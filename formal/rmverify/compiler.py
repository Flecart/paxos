"""One source-to-RM compiler. Its output is untrusted until Lean checks it."""
import operator


def substitute(e, env):
    match e:
        case ("var", slot): return env[slot]
        case ("lit" | "bool", _): return e
        case ("bin", op, a, b): return ("bin", op, substitute(a, env), substitute(b, env))
        case ("ite", c, a, b): return ("ite", substitute(c, env), substitute(a, env), substitute(b, env))
    raise ValueError("invalid source expression")


def lower(program):
    # ponytail: continuation expansion can grow exponentially with branching;
    # use shared SSA nodes when larger handlers exhaust compilation/proof resources.
    # Continuations preserve early return and sequential assignments independently
    # of Lean's structured Outcome interpreter.
    def go(stmt, env, next_):
        match stmt:
            case ("skip",): return next_(env)
            case ("assign", slot, value):
                updated = list(env)
                updated[slot] = substitute(value, env)
                return next_(updated)
            case ("seq", first, rest): return go(first, env, lambda e: go(rest, e, next_))
            case ("branch", condition, yes, no):
                left, right = go(yes, env, next_), go(no, env, next_)
                cond = substitute(condition, env)
                return [a if a == b else ("ite", cond, a, b) for a, b in zip(left, right, strict=True)]
            case ("ret", value): return env[:program.fields] + [substitute(value, env)]
        raise ValueError("invalid source statement")
    env = [("var", i) if i < len(program.inputs) else ("lit", 0) for i in range(len(program.slots))]
    return go(program.body, env, lambda e: e[:program.fields] + [("lit", 0)])


def expression_sort(e, sorts):
    match e:
        case ("var", n) if type(n) is int and 0 <= n < len(sorts): return sorts[n]
        case ("lit", n) if type(n) is int: return "int"
        case ("bool", b) if type(b) is bool: return "bool"
        case ("bin", op, a, b):
            left, right = expression_sort(a, sorts), expression_sort(b, sorts)
            if left != right: raise ValueError("RM operand sort mismatch")
            if op in ("add", "sub", "mul") and left == "int": return "int"
            if op in ("lt", "le", "gt", "ge") and left == "int": return "bool"
            if op in ("eq", "ne"): return "bool"
            if op in ("and", "or") and left == "bool": return "bool"
        case ("ite", c, a, b):
            left, right = expression_sort(a, sorts), expression_sort(b, sorts)
            if expression_sort(c, sorts) == "bool" and left == right: return left
    raise ValueError(f"ill-typed or unsupported expression: {e}")


def evaluate(e, env):
    match e:
        case ("lit" | "bool", n): return n
        case ("var", i): return env[i]
        case ("ite", c, a, b): return evaluate(a if evaluate(c, env) else b, env)
        case ("bin", op, a, b):
            operations = dict(add=operator.add, sub=operator.sub, mul=operator.mul,
                              eq=operator.eq, ne=operator.ne, lt=operator.lt,
                              le=operator.le, gt=operator.gt, ge=operator.ge,
                              **{"and": lambda a,b: bool(a and b), "or": lambda a,b: bool(a or b)})
            return operations[op](evaluate(a, env), evaluate(b, env))
    raise ValueError("invalid expression")


def run_graph(graph, values):
    if len(values) != len(graph["inputs"]): raise ValueError("graph input arity")
    env = list(values)
    for e in graph["terms"]: env.append(evaluate(e, env))
    return [env[i] for i in graph["outputs"]]


def compile_program(program):
    import torch  # Load libtorch before the extension.
    import zrth as rm

    def sort(kind): return (rm.Bool if kind == "bool" else rm.Int)([1, 1])
    inputs = [rm.Var(sort(k)) for k in program.inputs]
    terms, cache = [], {}

    def term(op, reads, kind):
        output = rm.Wire(sort(kind))
        terms.append(rm.Term(op, [output], reads))
        return output

    def scaled(value, n):
        if -(2**63) <= n < 2**63:
            return term(rm.LIA.Linear(torch.tensor([[n]], dtype=torch.int64),
                                     torch.tensor([[0]], dtype=torch.int64)), [value], "int")
        high, low = divmod(n, 2**60)
        return term(rm.LIA.Add(), [scaled(scaled(value, high), 2**60), scaled(value, low)], "int")

    def constant(n):
        if -(2**63) <= n < 2**63:
            return term(rm.LIA.Int(torch.tensor([[n]], dtype=torch.int64)), [], "int")
        # Chunked affine terms avoid both int64 truncation and exponential
        # unfolding of a repeated-doubling DAG in the Lean kernel.
        high, low = divmod(n, 2**60)
        return term(rm.LIA.Add(), [scaled(constant(high), 2**60), constant(low)], "int")

    def coefficient(e):
        if e[0] == "lit": return e[1]
        if e[:2] == ("bin", "sub") and e[2] == ("lit", 0):
            n = coefficient(e[3])
            return None if n is None else -n
        return None

    def wire(e):
        if e in cache: return cache[e]
        kind = expression_sort(e, program.inputs)
        match e:
            case ("var", i): result = inputs[i]
            case ("lit", n): result = constant(n)
            case ("bool", b): result = term(rm.LIA.Bool(torch.tensor([[b]], dtype=torch.bool)), [], "bool")
            case ("ite", c, a, b): result = term(rm.LIA.Ite(), [wire(c), wire(a), wire(b)], kind)
            case ("bin", "mul", a, b):
                n, value = coefficient(a), b
                if n is None: n, value = coefficient(b), a
                if n is None: raise ValueError("nonlinear multiplication")
                result = scaled(wire(value), n)
            case ("bin", op, a, b) if op in ("eq", "ne") and expression_sort(a, program.inputs) == "bool":
                left, right = wire(a), wire(b)
                negated = term(rm.LIA.Not(), [right], "bool")
                result = term(rm.LIA.Ite(), [left, right, negated] if op == "eq" else [left, negated, right], "bool")
            case ("bin", op, a, b):
                constructor = {"add":"Add", "sub":"Sub", "eq":"Eq", "ne":"Ne", "lt":"Lt", "le":"Le", "gt":"Gt", "ge":"Ge", "and":"And", "or":"Or"}[op]
                result = term(getattr(rm.LIA, constructor)(), [wire(a), wire(b)], kind)
            case _: raise ValueError("unsupported lowered expression")
        cache[e] = result
        return result

    expressions = lower(program)
    outputs = []
    for e in expressions:
        output = rm.Var(sort(expression_sort(e, program.inputs)))
        source = wire(e)
        terms.append(rm.Term(rm.LIA.Id(), [rm.X(output)], [source]))
        outputs.append(output)
    initial = terms
    if not program.initialize:
        initial = [rm.Term(rm.LIA.Bool(torch.tensor([[False]], dtype=torch.bool)) if w.dtype == sort("bool") else rm.LIA.Int(torch.tensor([[0]], dtype=torch.int64)), [rm.X(w)], []) for w in outputs]
    module = rm.Module(init=initial, update=terms, vars=inputs + outputs)
    if set(module.ctrl) != set(outputs) or not set(module.extl) <= set(inputs):
        raise ValueError("unexpected RM interface")
    atoms = list(module.atoms)
    if any(type(t.itype).__name__ != "Differential_ZERO" for atom in atoms for t in atom.delay):
        raise ValueError("continuous dynamics are unsupported")
    # Read back the real ordered RM atoms, never the compiler's expression list.
    bindings = {w: i for i, w in enumerate(inputs)}
    rows, sorts = [], list(program.inputs)
    for atom in atoms:
        for t in (atom.init if program.initialize else atom.update):
            if len(t.write) != 1 or t.write[0] in bindings: raise ValueError("invalid RM controller")
            args = [("var", bindings[w]) for w in t.read]
            match t.itype, args:
                case rm.LIA.Int(n), []: expression = ("lit", int(n.item()))
                case rm.LIA.Bool(b), []: expression = ("bool", bool(b.item()))
                case rm.LIA.Linear(weight, bias), [a]:
                    if list(weight.shape) != [1, 1] or list(bias.shape) != [1, 1]:
                        raise ValueError("only scalar affine terms are supported")
                    expression = ("bin", "add", ("bin", "mul", ("lit", int(weight.item())), a), ("lit", int(bias.item())))
                case rm.LIA.Id(), [a]: expression = a
                case rm.LIA.Not(), [a]: expression = ("ite", a, ("bool", False), ("bool", True))
                case rm.LIA.Ite(), [c, a, b]: expression = ("ite", c, a, b)
                case op, [a, b]:
                    name = {"LIA_Add":"add", "LIA_Sub":"sub", "LIA_Eq":"eq", "LIA_Ne":"ne", "LIA_Lt":"lt", "LIA_Le":"le", "LIA_Gt":"gt", "LIA_Ge":"ge", "LIA_And":"and", "LIA_Or":"or"}.get(type(op).__name__)
                    if name is None: raise ValueError(f"unsupported RM operator {op}")
                    expression = ("bin", name, a, b)
                case _: raise ValueError(f"unsupported RM term {t}")
            kind = expression_sort(expression, sorts)
            if t.write[0].dtype != sort(kind): raise ValueError("RM output sort mismatch")
            bindings[t.write[0]] = len(sorts)
            rows.append(expression)
            sorts.append(kind)
    return dict(inputs=program.inputs, terms=rows,
                outputs=[bindings[rm.X(w)] for w in outputs],
                sorts=[expression_sort(e, program.inputs) for e in expressions])
