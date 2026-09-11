"""Strict typed extraction. This source/name/type boundary remains trusted."""
from dataclasses import dataclass
import ast
import inspect
import textwrap
from types import CodeType
from .value_types import collection_type, mutable, parts


class Unsupported(ValueError):
    pass


def literal(value):
    return ("bool", value) if type(value) is bool else ("lit", int(value))


@dataclass
class Program:
    name: str
    body: tuple
    inputs: list[str]
    slots: list[str]
    fields: int
    result: str
    function: object
    initialize: bool = False
    slot_names: list[str] = None
    source_file: str = ""
    source_line: int = 0
    source_ast: str = ""
    source_column: int = 0


def annotation(value, target=None):
    if value is int or value == "int": return "int"
    if value is bool or value == "bool": return "bool"
    if value is None or value in ("None", "NoneType"): return "none"
    if target is not None and (value is target or value == target.__name__): return "state"
    collection = collection_type(value)
    if collection is not None: return collection
    raise Unsupported(f"unsupported or missing type annotation: {value!r}")


def fields_of(target, *, require_init=True):
    if not inspect.isclass(target) or target.__bases__ != (object,) or type(target) is not type:
        raise Unsupported("target must be a plain class without inheritance/metaclass behavior")
    tree = ast.parse(textwrap.dedent(inspect.getsource(target))).body[0]
    if tree.decorator_list:
        raise Unsupported("class decorators are unsupported")
    fields = dict(inspect.get_annotations(target))
    init = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
    if init is None and require_init:
        raise Unsupported("an explicit zero-argument __init__ is required")
    for n in ast.walk(init) if init is not None else ():
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Attribute):
            if isinstance(n.target.value, ast.Name) and n.target.value.id == "self":
                kind = ast.unparse(n.annotation)
                if n.target.attr in fields and annotation(fields[n.target.attr]) != annotation(kind):
                    raise Unsupported("conflicting field annotations")
                fields[n.target.attr] = kind
    if not fields:
        raise Unsupported("annotate state fields on the class or in __init__")
    result = {name: annotation(kind) for name, kind in fields.items()}
    if any(type(name) is not str or not name.isidentifier() or name.startswith("__") for name in result):
        raise Unsupported("state fields require ordinary Python identifiers")
    if any(kind == "none" for kind in result.values()):
        raise Unsupported("state fields must be int or bool")
    for name, value in vars(target).items():
        if name in fields:
            if type(value) is not (bool if result[name] == "bool" else int):
                raise Unsupported(f"unsupported descriptor/default for field {name}")
            continue
        if name in ("__module__", "__doc__", "__annotations__", "__dict__", "__weakref__", "__firstlineno__", "__static_attributes__"):
            continue
        if not inspect.isfunction(value):
            raise Unsupported(f"unsupported class member {name}")
        if name.startswith("__") and name != "__init__":
            raise Unsupported(f"special behavior {name} is unsupported")
    return result


class Parser:
    def __init__(self, function, fields, parameters, result, *, method=False, initialize=False):
        self.function, self.fields, self.result = function, fields, result
        self.file = inspect.getsourcefile(function)
        self.line = inspect.getsourcelines(function)[1]
        source = inspect.getsource(function)
        self.column = len(source.splitlines()[0]) - len(source.splitlines()[0].lstrip())
        self.tree = ast.parse(textwrap.dedent(source)).body[0]
        self.slots, self.bindings, self.objects = [], {}, {}
        self.slot_names = []
        self.method, self.initialize = method, initialize
        if method:
            self.objects["self"] = self.add_fields(fields)
        for name, kind in parameters:
            if kind == "state": self.objects[name] = self.add_fields(fields)
            elif kind == "none": self.bindings[name] = (None, "none")
            else: self.bindings[name] = (self.add_slot(kind, name), kind)
        self.inputs = [] if initialize else list(self.slots)
        self.assigned = set() if initialize else set(range(len(self.slots)))
        self.expected = None
        self.quantified = set()
        self.borrows = {}
        self.writing = False

    def add_slot(self, kind, name):
        self.slots.append(kind)
        self.slot_names.append(name)
        return len(self.slots) - 1

    def add_fields(self, fields):
        return {name: (self.add_slot(kind, name), kind) for name, kind in fields.items()}

    def fail(self, node, message):
        raise Unsupported(f"{self.file}:{self.line + node.lineno - 1}:{self.column + node.col_offset + 1}: {message}")

    def binding(self, node, assigned):
        if isinstance(node, ast.Name) and node.id in self.bindings:
            slot, kind = self.bindings[node.id]
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in self.objects and node.attr in self.objects[node.value.id]:
            slot, kind = self.objects[node.value.id][node.attr]
        else:
            self.fail(node, "unknown variable or field")
        if slot is not None and mutable(kind):
            via = node.id if isinstance(node, ast.Name) else None
            self.check_borrow(node, slot, via, self.writing)
        if slot is not None and slot not in assigned:
            self.fail(node, "read before definite assignment")
        return (literal(0) if slot is None else ("bound" if slot in self.quantified else "var", slot)), kind

    def expr(self, node, assigned):
        def binary(op, a, b, expected, result):
            left, lt = self.expr(a, assigned)
            right, rt = self.expr(b, assigned)
            if lt != rt or lt not in expected: self.fail(node, "operand type mismatch")
            return ("bin", op, left, right), result
        if isinstance(node, ast.Dict) and not node.keys:
            if self.expected and self.expected.startswith("dict["):
                return ("empty", self.expected), self.expected
            self.fail(node, "empty dictionary needs a field or local annotation")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("set", "dict") and not node.args and not node.keywords:
            self.builtin(node.func)
            if self.expected and self.expected.startswith(node.func.id + "["):
                return ("empty", self.expected), self.expected
            self.fail(node, "empty collection needs a field or local annotation")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("all", "any") and len(node.args) == 1 and not node.keywords:
            self.builtin(node.func)
            gen = node.args[0]
            if not isinstance(gen, ast.GeneratorExp) or len(gen.generators) != 1:
                self.fail(node, "all/any requires one finite generator")
            comp = gen.generators[0]
            if not isinstance(comp.target, ast.Name) or comp.ifs or comp.is_async:
                self.fail(node, "use a plain finite generator without filters")
            container, ct = self.expr(comp.iter, assigned)
            if not mutable(ct): self.fail(node, "quantifier requires a collection")
            if comp.target.id in self.bindings or comp.target.id in self.objects: self.fail(node, "generator variable shadows an existing local")
            slot = self.add_slot(parts(ct)[0], comp.target.id)
            self.bindings[comp.target.id] = (slot, parts(ct)[0])
            self.quantified.add(slot)
            body, bt = self.expr(gen.elt, assigned | {slot})
            del self.bindings[comp.target.id]
            self.quantified.remove(slot)
            if bt != "bool": self.fail(node, "quantifier body must be Boolean")
            if ct.startswith("set[") and any(isinstance(n, ast.Subscript) for n in ast.walk(gen.elt)):
                self.fail(node, "set predicates must be total; use get with an explicit default")
            return (node.func.id, ct, container, slot, body), "bool"
        if isinstance(node, ast.Subscript):
            container, ct = self.expr(node.value, assigned)
            key, kt = self.expr(node.slice, assigned)
            if not ct.startswith("dict[") or parts(ct)[0] != kt:
                self.fail(node, "dictionary key type mismatch")
            return ("lookup", container, key), parts(ct)[1]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len" and len(node.args) == 1 and not node.keywords:
            self.builtin(node.func)
            value, vt = self.expr(node.args[0], assigned)
            if not mutable(vt): self.fail(node, "len requires a collection")
            return ("length", value), "int"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and len(node.args) == 2 and not node.keywords:
            container, ct = self.expr(node.func.value, assigned)
            key, kt = self.expr(node.args[0], assigned)
            default, dt = self.expr(node.args[1], assigned)
            if not ct.startswith("dict[") or parts(ct) != [kt, dt]: self.fail(node, "get argument type mismatch")
            return ("get", container, key, default), dt
        if isinstance(node, ast.Constant):
            if type(node.value) in (int, bool): return literal(node.value), "bool" if type(node.value) is bool else "int"
            if node.value is None: return literal(0), "none"
        if isinstance(node, (ast.Name, ast.Attribute)):
            return self.binding(node, assigned)
        if isinstance(node, ast.UnaryOp):
            value, kind = self.expr(node.operand, assigned)
            if isinstance(node.op, ast.Not) and kind == "bool": return ("bin", "eq", value, literal(False)), "bool"
            if isinstance(node.op, (ast.USub, ast.UAdd)) and kind == "int":
                return (("bin", "sub", literal(0), value) if isinstance(node.op, ast.USub) else value), "int"
        if isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult):
            op = {ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul"}[type(node.op)]
            if op == "mul":
                def is_literal(n):
                    return isinstance(n, ast.Constant) and type(n.value) is int or isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.USub, ast.UAdd)) and isinstance(n.operand, ast.Constant) and type(n.operand.value) is int
                if not (is_literal(node.left) or is_literal(node.right)):
                    self.fail(node, "multiplication requires a literal operand")
            return binary(op, node.left, node.right, ("int",), "int")
        if isinstance(node, ast.Compare):
            comparisons = []
            for left, op, right in zip([node.left, *node.comparators], node.ops, node.comparators):
                name = {ast.Eq:"eq", ast.NotEq:"ne", ast.Lt:"lt", ast.LtE:"le", ast.Gt:"gt", ast.GtE:"ge"}.get(type(op))
                if isinstance(op, (ast.In, ast.NotIn)):
                    key, kt = self.expr(left, assigned)
                    container, ct = self.expr(right, assigned)
                    if not mutable(ct) or parts(ct)[0] != kt: self.fail(node, "membership type mismatch")
                    membership = ("contains", ct, container, key)
                    comparisons.append(("bin", "eq", membership, literal(False)) if isinstance(op, ast.NotIn) else membership)
                    continue
                if name is None: self.fail(node, "unsupported comparison")
                comparisons.append(binary(name, left, right, ("int", "bool") if name in ("eq", "ne") else ("int",), "bool")[0])
            value = comparisons[0]
            for other in comparisons[1:]: value = ("bin", "and", value, other)
            return value, "bool"
        if isinstance(node, ast.BoolOp):
            operands = [self.expr(v, assigned) for v in node.values]
            if any(t != "bool" for _, t in operands): self.fail(node, "Boolean operands required")
            value = operands[0][0]
            for other, _ in operands[1:]: value = ("bin", "and" if isinstance(node.op, ast.And) else "or", value, other)
            return value, "bool"
        if isinstance(node, ast.IfExp):
            cond, ct = self.expr(node.test, assigned)
            yes, yt = self.expr(node.body, assigned)
            no, nt = self.expr(node.orelse, assigned)
            if ct != "bool" or yt != nt: self.fail(node, "conditional type mismatch")
            return ("ite", cond, yes, no), yt
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("min", "max") and len(node.args) == 2 and not node.keywords:
            import builtins
            closure = inspect.getclosurevars(self.function)
            resolved = closure.nonlocals.get(node.func.id, closure.globals.get(node.func.id, closure.builtins.get(node.func.id)))
            if resolved is not getattr(builtins, node.func.id): self.fail(node, "shadowed builtin")
            comp, _ = binary("le" if node.func.id == "min" else "ge", *node.args, ("int",), "bool")
            return ("ite", comp, comp[2], comp[3]), "int"
        self.fail(node, "unsupported expression")

    def check_borrow(self, node, slot, via=None, write=False):
        position = (node.lineno, node.col_offset)
        for name, (owner, exclusive, end, start) in self.borrows.items():
            if owner == slot and name != via and position <= end and (exclusive or write):
                self.fail(node, f"conflicting {'write' if write else 'read'}: {name} borrows this collection at {self.file}:{self.line + start[0] - 1}:{self.column + start[1] + 1}")
        if via in self.borrows and write and not self.borrows[via][1]:
            self.fail(node, "cannot mutate through a shared borrow")

    def borrow(self, node, target, expression, kind):
        if not isinstance(target, ast.Name): self.fail(node, "mutable state cannot acquire a second owner")
        if any(isinstance(parent, (ast.If, ast.For, ast.While)) and node in list(ast.walk(parent)) for parent in ast.walk(self.tree)):
            self.fail(node, "conditional borrow creation is not yet supported")
        if target.id in self.bindings or target.id in self.objects: self.fail(node, "rebinding a mutable borrow or state parameter is unsupported")
        uses = [n for n in ast.walk(self.tree) if isinstance(n, ast.Name) and n.id == target.id and isinstance(n.ctx, ast.Load)]
        end = max(((n.lineno,n.col_offset) for n in uses), default=(node.lineno,node.col_offset))
        exclusive = any(
            isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store) and isinstance(n.value, ast.Name) and n.value.id == target.id or
            isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("add", "discard") and isinstance(n.func.value, ast.Name) and n.func.value.id == target.id
            for n in ast.walk(self.tree))
        slot = expression[1]
        self.check_borrow(node,slot,write=exclusive)
        self.bindings[target.id] = (slot,kind)
        self.borrows[target.id] = (slot,exclusive,end,(node.lineno,node.col_offset))

    def builtin(self, node):
        import builtins
        closure = inspect.getclosurevars(self.function)
        resolved = closure.nonlocals.get(node.id, closure.globals.get(node.id, closure.builtins.get(node.id)))
        if resolved is not getattr(builtins, node.id): self.fail(node, "shadowed builtin")

    def block(self, nodes, assigned):
        rows, assigned, stopped = [], set(assigned), False
        for node in nodes:
            if stopped: self.fail(node, "unreachable statements after return are unsupported")
            if isinstance(node, ast.Pass) or isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                rows.append(("skip",))
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                if isinstance(node, ast.Assign):
                    if len(node.targets) != 1: self.fail(node, "single-target assignment required")
                    target = node.targets[0]
                else: target = node.target
                if isinstance(target, ast.Name) and target.id in self.borrows:
                    self.fail(target, "rebinding a mutable borrow is unsupported")
                value = node.value
                if value is None: self.fail(node, "assignment needs a value")
                if isinstance(node, ast.AugAssign):
                    value = ast.copy_location(ast.BinOp(left=target, op=node.op, right=value), node)
                if isinstance(target, ast.Subscript):
                    if not self.method: self.fail(target, "properties cannot mutate collections")
                    self.writing = True
                    container, ct = self.binding(target.value, assigned)
                    self.writing = False
                    key, kt = self.expr(target.slice, assigned)
                    expression, kind = self.expr(value, assigned)
                    if not ct.startswith("dict[") or parts(ct) != [kt, kind]: self.fail(target, "dictionary assignment type mismatch")
                    rows.append(("assign", container[1], ("dict_set", container, key, expression)))
                    continue
                self.expected = (annotation(ast.unparse(node.annotation)) if isinstance(node, ast.AnnAssign) else
                    self.fields.get(target.attr) if isinstance(target, ast.Attribute) else
                    self.bindings.get(target.id, (None, None))[1] if isinstance(target, ast.Name) else None)
                expression, kind = self.expr(value, assigned)
                self.expected = None
                if isinstance(node, ast.AnnAssign) and annotation(ast.unparse(node.annotation)) != kind:
                    self.fail(node, "assignment annotation mismatch")
                if mutable(kind) and expression[0] == "var":
                    self.borrow(node,target,expression,kind)
                    rows.append(("skip",))
                    continue
                if kind == "none": self.fail(node, "None is only supported as a method result")
                if isinstance(target, ast.Name):
                    if target.id in self.objects: self.fail(node, "cannot rebind a state parameter")
                    if target.id not in self.bindings: self.bindings[target.id] = (self.add_slot(kind, target.id), kind)
                    slot, expected = self.bindings[target.id]
                elif self.method and isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self" and target.attr in self.fields:
                    slot, expected = self.objects["self"][target.attr]
                else: self.fail(node, "properties cannot mutate state; unknown assignment target")
                if kind != expected or slot is None: self.fail(node, "assignment changes variable type")
                if mutable(kind): self.check_borrow(target,slot,write=True)
                assigned.add(slot)
                rows.append(("assign", slot, expression))
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute):
                call = node.value
                if not self.method: self.fail(node, "properties cannot mutate collections")
                self.writing = True
                container, ct = self.binding(call.func.value, assigned)
                self.writing = False
                if not ct.startswith("set[") or call.func.attr not in ("add", "discard") or len(call.args) != 1 or call.keywords:
                    self.fail(node, "unsupported collection mutation")
                key, kt = self.expr(call.args[0], assigned)
                if parts(ct) != [kt]: self.fail(node, "set element type mismatch")
                rows.append(("assign", container[1], ("set_" + call.func.attr, container, key)))
            elif isinstance(node, ast.For):
                if node.orelse or not isinstance(node.target, ast.Name):
                    self.fail(node, "use a plain dictionary-key loop without else")
                container, ct = self.binding(node.iter, assigned)
                if not ct.startswith("dict["):
                    self.fail(node, "executable set iteration needs an order-independence proof and is not supported")
                if node.target.id in self.bindings or node.target.id in self.objects:
                    self.fail(node, "loop variables must be fresh locals")
                slot = self.add_slot(parts(ct)[0], node.target.id)
                self.bindings[node.target.id] = (slot, parts(ct)[0])
                borrow_name = f"iteration at line {self.line + node.lineno - 1}"
                self.borrows[borrow_name] = (container[1], False,
                    (node.end_lineno,node.end_col_offset), (node.lineno,node.col_offset))
                body, _, _ = self.block(node.body, assigned | {slot})
                del self.borrows[borrow_name]
                rows.append(("each", ct, container, slot, body))
            elif isinstance(node, ast.If):
                condition, kind = self.expr(node.test, assigned)
                if kind != "bool": self.fail(node, "condition must be Boolean")
                yes, ya, yr = self.block(node.body, assigned)
                no, na, nr = self.block(node.orelse, assigned)
                assigned = na if yr and not nr else ya if nr and not yr else ya & na
                stopped = yr and nr
                rows.append(("branch", condition, yes, no))
            elif isinstance(node, ast.Return):
                expression, kind = (literal(0), "none") if node.value is None else self.expr(node.value, assigned)
                if kind != self.result: self.fail(node, "return type mismatch")
                if self.initialize and not set(range(len(self.fields))) <= assigned:
                    self.fail(node, "constructor returns before initializing every field")
                rows.append(("ret", expression))
                stopped = True
            else: self.fail(node, "unsupported statement")
        result = ("skip",)
        for row in reversed(rows): result = ("seq", row, result)
        return result, assigned, stopped

    def parse(self):
        if not isinstance(self.tree, ast.FunctionDef) or self.tree.decorator_list:
            self.fail(self.tree, "async/decorated functions are unsupported")
        if (type(self.function.__name__) is not str or type(self.function.__qualname__) is not str or
                self.function.__name__ != self.tree.name or
                any(not part.isidentifier() and part != "<locals>" for part in self.function.__qualname__.split("."))):
            self.fail(self.tree, "function metadata must use Python identifiers matching its source")
        compiled = compile(ast.Module(body=[self.tree], type_ignores=[]), self.file, "exec", dont_inherit=True)
        candidate = next(c for c in compiled.co_consts if isinstance(c, CodeType))
        actual = self.function.__code__
        def constants(code):
            values = list(code.co_consts)
            if values and isinstance(values[0], str): values[0] = None  # docstring indentation
            return [(c.co_code, c.co_names, c.co_varnames, c.co_freevars, constants(c)) if isinstance(c, CodeType) else c for c in values]
        if any(getattr(candidate, k) != getattr(actual, k) for k in ("co_code", "co_names", "co_varnames", "co_freevars")) or constants(candidate) != constants(actual):
            self.fail(self.tree, "loaded function differs from its source; reload the module")
        body, assigned, returned = self.block(self.tree.body, self.assigned)
        if self.result != "none" and not returned: self.fail(self.tree, "all paths must return a value")
        if self.initialize and not set(range(len(self.fields))) <= assigned:
            self.fail(self.tree, "constructor must initialize every field")
        return Program(self.function.__name__, body, self.inputs, self.slots, len(self.fields) if self.method else 0, self.result, self.function, self.initialize, self.slot_names,
                       self.file, self.line, ast.dump(self.tree, include_attributes=True), self.column)


def parameters(function):
    result = list(inspect.signature(function).parameters.values())
    if any(p.kind not in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD) or p.default is not p.empty for p in result):
        raise Unsupported("use positional parameters without defaults, varargs or kwargs")
    return result


def method_program(function, fields, *, initialize=False, initialize_arguments=None):
    params = parameters(function)
    if not params or params[0].name != "self": raise Unsupported("instance methods require self")
    if initialize and initialize_arguments is None and len(params) != 1:
        raise Unsupported("constructor must take no arguments")
    kinds = [(p.name, annotation(p.annotation)) for p in params[1:]]
    if any(k not in ("int", "bool") for _, k in kinds): raise Unsupported("method inputs currently require immutable scalars")
    result = "none" if initialize else annotation(inspect.signature(function).return_annotation)
    if mutable(result): raise Unsupported("borrowed or mutable method results cannot escape")
    parser = Parser(function, fields, kinds, result, method=True, initialize=initialize)
    if initialize_arguments is None:
        return parser.parse()
    if not initialize or set(initialize_arguments) != {name for name, _ in kinds}:
        raise Unsupported("initializer argument names differ from constructor signature")
    bindings = []
    for name, kind in kinds:
        value = initialize_arguments[name]
        if type(value) is not (bool if kind == "bool" else int):
            raise Unsupported("initializer argument type mismatch")
        slot, _ = parser.bindings[name]
        parser.assigned.add(slot)
        bindings.append(("assign", slot, literal(value)))
    program = parser.parse()
    # Bind a finite constructor call before interpreting its unchanged body.
    for binding in reversed(bindings):
        program.body = ("seq", binding, program.body)
    return program


def predicate_program(function, fields, target, expected):
    params = parameters(function)
    kinds = [annotation(p.annotation, target) for p in params]
    if kinds != expected or annotation(inspect.signature(function).return_annotation) != "bool":
        raise Unsupported(f"{function.__name__}: expected predicate parameters {expected} and bool result")
    return Parser(function, fields, [(p.name, k) for p, k in zip(params, kinds)], "bool").parse()
