"""Z3 proposes reachable witnesses; only Lean replay may label them refutations."""
import z3


def expression(e, env):
    match e:
        case ("lit", n): return z3.IntVal(n)
        case ("bool", b): return z3.BoolVal(b)
        case ("var", i): return env[i]
        case ("ite", c, a, b): return z3.If(expression(c,env),expression(a,env),expression(b,env))
        case ("bin", op, a, b):
            a, b = expression(a,env), expression(b,env)
            return {"add":lambda:a+b,"sub":lambda:a-b,"mul":lambda:a*b,"eq":lambda:a==b,"ne":lambda:a!=b,
                    "lt":lambda:a<b,"le":lambda:a<=b,"gt":lambda:a>b,"ge":lambda:a>=b,
                    "and":lambda:z3.And(a,b),"or":lambda:z3.Or(a,b)}[op]()
    raise ValueError("invalid solver expression")


def run(program, values):
    from .execution import execute
    return execute(program, values, evaluate=expression, choose=z3.If)


def concrete(model, values):
    result = [model.eval(value,model_completion=True) for value in values]
    return [z3.is_true(value) if z3.is_bool(value) else value.as_long() for value in result]


def counterexamples(model, depth, timeout, wanted):
    solver = z3.Solver()
    solver.set(timeout=max(1,int(timeout*1000)))
    programs, methods = model["programs"],model["methods"]
    states = [run(programs[0],[])[:-1]]
    selectors, arguments, found = [], [], {}

    def trace(solution, final=None):
        calls = []
        for selector, choices in zip(selectors,arguments):
            j = solution.eval(selector,model_completion=True).as_long()
            m = methods[j]
            calls.append(dict(method=m["name"],arguments=dict(zip(m["parameters"],concrete(solution,choices[j])))))
        if final is not None:
            j, args = final
            calls.append(dict(method=methods[j]["name"],arguments=dict(zip(methods[j]["parameters"],concrete(solution,args)))))
        return calls

    def query(identifier, condition, target, final=None):
        if identifier not in wanted or identifier in found: return
        solver.push()
        solver.add(condition)
        if solver.check() == z3.sat:
            solution = solver.model()
            found[identifier] = dict(target=target,calls=trace(solution,final))
        solver.pop()

    for k in range(depth+1):
        state = states[-1]
        for i,p in enumerate(model["invariants"]):
            query(p["identifier"], z3.Not(run(programs[p["index"]],state)[0]),["invariant",i])
        if k == depth or set(found) == wanted: break
        choices = [[(z3.Bool if kind=="bool" else z3.Int)(f"input_{k}_{j}_{n}") for n,kind in enumerate(m["inputs"])] for j,m in enumerate(methods)]
        outputs = [run(programs[m["index"]],state+args) for m,args in zip(methods,choices)]
        for i,c in enumerate(model["contracts"]):
            j = c["method"]
            args, m, output = choices[j],methods[j],outputs[j]
            pre = z3.BoolVal(True) if c["requires"] is None else run(programs[c["requires"]],state+args)[0]
            post_args = state+output[:-1]+([] if m["result"]=="none" else output[-1:])+args
            post = run(programs[c["ensures"]],post_args)[0]
            query(c["identifier"],z3.And(pre,z3.Not(post)),["contract",i],(j,args))
        selector = z3.Int(f"method_{k}")
        solver.add(selector>=0,selector<len(methods))
        next_state = []
        for n in range(len(model["fields"])):
            value = outputs[-1][n]
            for j in reversed(range(len(methods)-1)):
                value = z3.If(selector==j,outputs[j][n],value)
            next_state.append(value)
        states.append(next_state)
        selectors.append(selector)
        arguments.append(choices)
    return found


def composition_relation(model, before, after=None):
    """A complete round, with shared old state and candidate awaited values."""
    atoms = []
    for atom in model["atoms"]:
        controls = atom["controls"]
        alternatives = []
        if after is None:
            for initial in atom["initial"]:
                output = run(model["programs"][initial["index"]], [])[:-1]
                alternatives.append(z3.And(*[before[j] == v for j,v in zip(controls, output, strict=True)]))
        else:
            if atom["stutter"]:
                alternatives.append(z3.And(*[after[j] == before[j] for j in controls]))
            for action in atom["actions"]:
                values = [before[j] for j in controls]
                values += [(after if p["awaited"] else before)[p["variable"]] for p in action["ports"]]
                output = run(model["programs"][action["index"]], values)[:-1]
                alternatives.append(z3.And(*[after[j] == v for j,v in zip(controls, output, strict=True)]))
        atoms.append(z3.Or(*alternatives))
    return z3.And(*atoms)


def composition_counterexamples(model, depth, timeout, wanted):
    """Propose reachable invariant violations and distinct relation mismatches."""
    solver = z3.Solver()
    solver.set(timeout=max(1, int(timeout*1000)))
    found = {}
    def state(name):
        return [(z3.Bool if k == "bool" else z3.Int)(f"{name}_{i}")
                for i,k in enumerate(model["fields"].values())]
    # Relation equivalence ranges over all valuations, not just reachable ones.
    before, after = state("before"), state("after")
    for relation in model["relations"]:
        identifier = relation["identifier"]
        if identifier not in wanted:
            continue
        initial = relation["name"] == "initial"
        actual = composition_relation(model, before, None if initial else after)
        specified = run(model["programs"][relation["index"]], before if initial else before+after)[0]
        solver.push()
        solver.add(z3.Xor(actual, specified))
        if solver.check() == z3.sat:
            solution = solver.model()
            found[identifier] = dict(kind="relation_mismatch", relation=relation["name"],
                states=[concrete(solution, before)] + ([] if initial else [concrete(solution, after)]))
        solver.pop()
    states = [state("state0")]
    solver.add(composition_relation(model, states[0]))
    for n in range(depth+1):
        for i, prop in enumerate(model["invariants"]):
            identifier = prop["identifier"]
            if identifier not in wanted or identifier in found:
                continue
            solver.push()
            solver.add(z3.Not(run(model["programs"][prop["index"]], states[-1])[0]))
            if solver.check() == z3.sat:
                solution = solver.model()
                found[identifier] = dict(kind="reachable_invariant", invariant=i,
                    states=[concrete(solution, s) for s in states])
            solver.pop()
        if n == depth or wanted <= found.keys():
            break
        states.append(state(f"state{n+1}"))
        solver.add(composition_relation(model, states[-2], states[-1]))
    return found
