"""Strict typed extraction. This source/name/type boundary remains trusted."""
from dataclasses import dataclass
import ast
import inspect
import textwrap
from types import CodeType
from .value_types import resolve, mutable, parts, optional, record, union, Kind, matches
import sys


class Unsupported(ValueError):
    pass


def literal(value):
    return ("bool", value) if type(value) is bool else ("lit", int(value))


def source_literal(value, kind):
    if optional(kind):return ("none",parts(kind)[0]) if value is None else ("some",source_literal(value,parts(kind)[0]))
    if record(kind):return ("record",kind,tuple(source_literal(getattr(value,n),k) for n,k in kind.fields.items()),tuple(kind.fields))
    if mutable(kind):
        e=("empty",kind)
        if kind.startswith("dict["):
            for k,v in value.items():e=("dict_set",e,source_literal(k,parts(kind)[0]),source_literal(v,parts(kind)[1]))
        else:
            for v in sorted(value,key=repr):e=("set_add",e,source_literal(v,parts(kind)[0]))
        return e
    return literal(value)


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
    helpers: list = None
    loans: list = None
    accesses: list = None
    moves: list = None


class Helper(str):
    def __new__(cls, program):
        value = super().__new__(cls, program.function.__module__+'.'+program.function.__qualname__)
        value.program = program
        return value


def referenced_programs(programs):
    """Keep public indices stable and append resolved nonrecursive helpers."""
    result = list(programs)
    known = {p.function for p in result}
    for p in result:
        for helper in p.helpers or []:
            if helper.function not in known:
                known.add(helper.function); result.append(helper)
    return result


def definition_order(programs):
    result,seen = [],set()
    def visit(i):
        if i in seen: return
        seen.add(i)
        for helper in programs[i].helpers or []:
            visit(next(j for j,p in enumerate(programs) if p.function is helper.function))
        result.append(i)
    for i in range(len(programs)): visit(i)
    return result


def annotation(value, target=None, namespace=None):
    if target is not None and (value is target or value == target.__name__): return "state"
    try: return resolve(value, namespace or (vars(sys.modules[target.__module__]) if target else {}))
    except (ValueError, SyntaxError, TypeError) as error: raise Unsupported(str(error)) from error


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
                if n.target.attr in fields and annotation(fields[n.target.attr],namespace=vars(sys.modules[target.__module__])) != annotation(kind,namespace=vars(sys.modules[target.__module__])):
                    raise Unsupported("conflicting field annotations")
                fields[n.target.attr] = kind
    if not fields:
        raise Unsupported("annotate state fields on the class or in __init__")
    result = {name: annotation(kind,namespace=vars(sys.modules[target.__module__])) for name, kind in fields.items()}
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
    def __init__(self, function, fields, parameters, result, *, method=False, initialize=False, stack=()):
        self.function, self.fields, self.result = function, fields, result
        self.stack = (*stack,function)
        self.helpers = []
        self.loans, self.accesses = [], []
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
        self.readonly = {slot for name,(slot,k) in self.bindings.items() if slot is not None and mutable(k)}
        self.inputs = [] if initialize else list(self.slots)
        self.assigned = set() if initialize else set(range(len(self.slots)))
        self.expected = None
        self.quantified = set()
        self.borrows = {}
        self.writing = False
        self.refined = set()
        self.moves, self.moved = [], set()

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

    def coerce(self, expression, actual, expected, node):
        if expected and optional(expected):
            if actual == "none": return (("none", parts(expected)[0]) if expression == literal(0) else ("coerce_none",expected,expression)), expected
            if actual == parts(expected)[0]: return ("some", expression), expected
        return expression, actual

    def refinement(self, node, truth):
        if isinstance(node,ast.Compare) and len(node.ops)==1 and isinstance(node.comparators[0],ast.Constant) and node.comparators[0].value is None:
            if (isinstance(node.ops[0],ast.IsNot) and truth) or (isinstance(node.ops[0],ast.Is) and not truth):
                return {ast.dump(node.left)}
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.Not): return self.refinement(node.operand,not truth)
        if isinstance(node,ast.BoolOp) and ((isinstance(node.op,ast.And) and truth) or (isinstance(node.op,ast.Or) and not truth)):
            return set().union(*(self.refinement(n,truth) for n in node.values))
        return set()

    def expr(self, node, assigned):
        e,k = self.raw_expr(node,assigned)
        if optional(k) and ast.dump(node) in self.refined: return ("unwrap",e),parts(k)[0]
        return e,k

    def raw_expr(self, node, assigned):
        def binary(op, a, b, expected, result):
            left, lt = self.expr(a, assigned)
            right, rt = self.expr(b, assigned)
            if lt != rt or lt not in expected: self.fail(node, "operand type mismatch")
            return ("bin", op, left, right), result
        if isinstance(node, (ast.Dict, ast.Set)) and (not isinstance(node,ast.Dict) or node.keys):
            if isinstance(node,ast.Dict):
                if any(k is None for k in node.keys): self.fail(node,"dictionary unpacking is unsupported")
                pairs = [(self.expr(k,assigned),self.expr(v,assigned)) for k,v in zip(node.keys,node.values)]
                kt,vt = parts(self.expected) if self.expected and self.expected.startswith("dict[") else (pairs[0][0][1],pairs[0][1][1])
                ct = Kind(f"dict[{kt},{vt}]",[kt,vt])
                e = ("empty",ct)
                for (key,k),(value,v) in pairs:
                    key,k = self.coerce(key,k,kt,node); value,v = self.coerce(value,v,vt,node)
                    if (k,v)!=(kt,vt) or mutable(v) or mutable(k): self.fail(node,"heterogeneous or nested mutable dictionary")
                    e = ("dict_set",e,key,value)
            else:
                values = [self.expr(v,assigned) for v in node.elts]
                kt = parts(self.expected)[0] if self.expected and self.expected.startswith("set[") else values[0][1]
                if mutable(kt): self.fail(node,"mutable set elements are unsupported")
                ct = Kind(f"set[{kt}]",[kt]); e = ("empty",ct)
                for v,k in values:
                    v,k = self.coerce(v,k,kt,node)
                    if k != kt: self.fail(node,"heterogeneous set")
                    e = ("set_add",e,v)
            return e,ct
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            target = self.function.__globals__.get(node.func.id)
            if inspect.isclass(target) and hasattr(target,'__dataclass_fields__'):
                kt = annotation(target,namespace=self.function.__globals__)
                fields = list(kt.fields)
                if len(node.args)>len(fields): self.fail(node,"too many record constructor arguments")
                supplied = list(zip(fields,node.args)) + [(kw.arg,kw.value) for kw in node.keywords]
                labels = [n for n,_ in supplied]
                if len(set(labels))!=len(labels) or any(n not in fields for n in labels): self.fail(node,"unknown or duplicate record field")
                for n in fields:
                    if n not in labels:
                        if n not in kt.defaults: self.fail(node,"missing record constructor field")
                        supplied.append((n,ast.copy_location(ast.Constant(kt.defaults[n]),node)))
                values = []
                for n,arg in supplied:
                    expected = kt.fields[n]
                    e,k = self.expr(arg,assigned)
                    e,k = self.coerce(e,k,expected,arg)
                    if k != expected: self.fail(arg,"record constructor field type mismatch")
                    values.append(e)
                return ("record",kt,tuple(values),tuple(n for n,_ in supplied)),kt
        if isinstance(node,ast.Attribute) and not (isinstance(node.value,ast.Name) and node.value.id in self.objects):
            e,k = self.expr(node.value,assigned)
            if optional(k):
                e,k = ("unwrap",e),parts(k)[0]
            if not record(k) or node.attr not in k.fields: self.fail(node,"unknown immutable record field")
            return ("field",k,node.attr,e),k.fields[node.attr]
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

            return (node.func.id, ct, container, slot, body), "bool"
        if isinstance(node, ast.Subscript):
            container, ct = self.expr(node.value, assigned)
            key, kt = self.expr(node.slice, assigned)
            if ct.startswith("dict["): key,kt = self.coerce(key,kt,parts(ct)[0],node.slice)
            if not ct.startswith("dict[") or parts(ct)[0] != kt:
                self.fail(node, "dictionary key type mismatch")
            return ("lookup", container, key), parts(ct)[1]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "len" and len(node.args) == 1 and not node.keywords:
            self.builtin(node.func)
            value, vt = self.expr(node.args[0], assigned)
            if not mutable(vt): self.fail(node, "len requires a collection")
            return ("length", value), "int"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get" and len(node.args) in (1,2) and not node.keywords:
            container, ct = self.expr(node.func.value, assigned)
            key, kt = self.expr(node.args[0], assigned)
            if ct.startswith("dict["): key,kt = self.coerce(key,kt,parts(ct)[0],node.args[0])
            if not ct.startswith("dict[") or parts(ct)[0] != kt: self.fail(node,"get key type mismatch")
            vt = parts(ct)[1]
            if len(node.args) == 1: return ("get_optional",vt,container,key), union(vt,"none")
            default, dt = self.expr(node.args[1], assigned)
            if dt == "none": return ("get_optional_default",vt,container,key,default), union(vt,"none")
            default,dt = self.coerce(default,dt,vt,node.args[1])
            if dt != vt: self.fail(node,"get default type mismatch")
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
                    if mutable(ct): key,kt = self.coerce(key,kt,parts(ct)[0],left)
                    if not mutable(ct) or parts(ct)[0] != kt: self.fail(node, "membership type mismatch")
                    membership = ("contains", ct, container, key)
                    comparisons.append(("bin", "eq", membership, literal(False)) if isinstance(op, ast.NotIn) else membership)
                    continue
                if isinstance(op,(ast.Is,ast.IsNot)):
                    if not isinstance(right,ast.Constant) or right.value is not None: self.fail(node,"identity is supported only for None")
                    e,k = self.raw_expr(left,assigned)
                    if not optional(k): self.fail(node,"None comparison requires an optional value")
                    test = ("is_none",e)
                    comparisons.append(("bin","eq",test,literal(False)) if isinstance(op,ast.IsNot) else test)
                    continue
                if name in ("eq","ne"):
                    a,ak = self.expr(left,assigned); b,bk = self.expr(right,assigned)
                    a,ak = self.coerce(a,ak,bk,left); b,bk = self.coerce(b,bk,ak,right)
                    if ak != bk or mutable(ak): self.fail(node,"equality requires matching immutable types")
                    comparisons.append(("bin",name,a,b)); continue
                if name is None: self.fail(node, "unsupported comparison")
                comparisons.append(binary(name, left, right, ("int", "bool") if name in ("eq", "ne") else ("int",), "bool")[0])
            value = comparisons[0]
            for other in comparisons[1:]: value = ("bin", "and", value, other)
            return value, "bool"
        if isinstance(node, ast.BoolOp):
            saved = self.refined.copy()
            operands = []
            for v in node.values:
                operands.append(self.expr(v,assigned))
                self.refined |= self.refinement(v,isinstance(node.op,ast.And))
            self.refined = saved
            if any(t != "bool" for _, t in operands): self.fail(node, "Boolean operands required")
            value = operands[0][0]
            for other, _ in operands[1:]: value = ("bin", "and" if isinstance(node.op, ast.And) else "or", value, other)
            return value, "bool"
        if isinstance(node, ast.IfExp):
            cond, ct = self.expr(node.test, assigned)
            saved = self.refined.copy()
            self.refined |= self.refinement(node.test,True)
            yes, yt = self.expr(node.body, assigned)
            self.refined = saved | self.refinement(node.test,False)
            no, nt = self.expr(node.orelse, assigned)
            self.refined = saved
            if yt != nt:
                if yt == "none": yes,yt = self.coerce(yes,yt,union(nt,"none"),node.body)
                elif nt == "none": no,nt = self.coerce(no,nt,union(yt,"none"),node.orelse)
                yes,yt = self.coerce(yes,yt,nt,node.body)
                no,nt = self.coerce(no,nt,yt,node.orelse)
            if ct != "bool" or yt != nt: self.fail(node, "conditional type mismatch")
            return ("ite", cond, yes, no), yt
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("min", "max") and len(node.args) == 2 and not node.keywords:
            import builtins
            closure = inspect.getclosurevars(self.function)
            resolved = closure.nonlocals.get(node.func.id, closure.globals.get(node.func.id, closure.builtins.get(node.func.id)))
            if resolved is not getattr(builtins, node.func.id): self.fail(node, "shadowed builtin")
            comp, _ = binary("le" if node.func.id == "min" else "ge", *node.args, ("int",), "bool")
            return ("ite", comp, comp[2], comp[3]), "int"
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            function = self.function.__globals__.get(node.func.id)
            if inspect.isfunction(function):
                if function in self.stack: self.fail(node,"recursive helpers are unsupported")
                if node.keywords: self.fail(node,"helper arguments must be positional")
                params = parameters(function)
                kinds = [(p.name,annotation(p.annotation,namespace=function.__globals__)) for p in params]
                result = annotation(inspect.signature(function).return_annotation,namespace=function.__globals__)
                if mutable(result) or result == "none": self.fail(node,"expression helpers return immutable values")
                if len(kinds)!=len(node.args): self.fail(node,"helper argument count mismatch")
                arguments = []
                for arg,(_,expected) in zip(node.args,kinds):
                    e,k = self.expr(arg,assigned)
                    e,k = self.coerce(e,k,expected,arg)
                    if k != expected: self.fail(arg,"helper argument type mismatch")
                    arguments.append(e)
                helper = Parser(function,{},kinds,result,stack=self.stack).parse()
                self.helpers.append(helper)
                return ("helper",Helper(helper),tuple(arguments)),result
        self.fail(node, "unsupported expression")

    def check_borrow(self, node, slot, via=None, write=False):
        if write and slot in self.readonly: self.fail(node,"cannot mutate a shared input borrow")
        position = (node.lineno, node.col_offset)
        self.accesses.append(dict(owner=slot,via=via if via in self.borrows else None,write=write,position=position))
        for name, (owner, exclusive, end, start) in self.borrows.items():
            if owner == slot and name != via and position <= end and (exclusive or write):
                self.fail(node, f"conflicting {'write' if write else 'read'}: {name} borrows this collection at {self.file}:{self.line + start[0] - 1}:{self.column + start[1] + 1}")
        if via in self.borrows and write and not self.borrows[via][1]:
            self.fail(node, "cannot mutate through a shared borrow")

    def borrow(self, node, target, expression, kind):
        if not isinstance(target, ast.Name): self.fail(node, "mutable state cannot acquire a second owner")
        parents=[parent for parent in ast.walk(self.tree) if isinstance(parent,(ast.If,ast.For)) and node in list(ast.walk(parent))]
        if parents:
            parent=min(parents,key=lambda p:len(list(ast.walk(p))))
            arm=parent.body if any(node in list(ast.walk(n)) for n in parent.body) else parent.orelse
            scope={child for n in arm for child in ast.walk(n)}
            if any(isinstance(n,ast.Name) and n.id==target.id and isinstance(n.ctx,ast.Load) and n not in scope for n in ast.walk(self.tree)):
                self.fail(node,"borrowed reference escapes its branch or iteration lifetime")
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
        start = (node.end_lineno,node.end_col_offset)
        self.loans.append(dict(owner=slot,name=target.id,exclusive=exclusive,start=start,finish=max(start,end)))

    def builtin(self, node):
        import builtins
        closure = inspect.getclosurevars(self.function)
        resolved = closure.nonlocals.get(node.id, closure.globals.get(node.id, closure.builtins.get(node.id)))
        if resolved is not getattr(builtins, node.id): self.fail(node, "shadowed builtin")

    def method_call(self, call, assigned):
        if not (self.method and isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name) and call.func.value.id=="self"):
            return None
        owner = self.function.__globals__.get(self.function.__qualname__.split(".")[0])
        function = getattr(owner,call.func.attr,None)
        if not inspect.isfunction(function) or call.func.attr=="__init__": self.fail(call,"unknown helper method")
        if function in self.stack: self.fail(call,"recursive helpers are unsupported")
        if call.keywords: self.fail(call,"helper arguments must be positional")
        params=parameters(function)[1:]
        kinds=[(p.name,annotation(p.annotation,namespace=function.__globals__)) for p in params]
        result=annotation(inspect.signature(function).return_annotation,namespace=function.__globals__)
        if mutable(result): self.fail(call,"mutable helper results cannot escape their owner")
        if len(kinds)!=len(call.args): self.fail(call,"helper argument count mismatch")
        arguments=[]
        for arg,(_,expected) in zip(call.args,kinds):
            e,k=self.expr(arg,assigned);e,k=self.coerce(e,k,expected,arg)
            if k!=expected:self.fail(arg,"helper argument type mismatch")
            arguments.append(e)
        helper=Parser(function,self.fields,kinds,result,method=True,stack=self.stack).parse()
        reads,writes=set(),set()
        def effects(e):
            if not isinstance(e,tuple):return
            if e and e[0]=="var" and e[1]<len(self.fields):reads.add(e[1])
            if e and e[0]=="assign" and e[1]<len(self.fields):writes.add(e[1])
            if e and e[0]=="invoke":
                reads.update(range(len(self.fields)));writes.update(range(len(self.fields)))
            for child in e:effects(child)
        effects(helper.body)
        for n in reads|writes:
            if n not in assigned:self.fail(call,"helper reads state before initialization")
            if mutable(self.slots[n]):self.check_borrow(call,n,write=n in writes)
        self.refined=set()
        self.helpers.append(helper)
        name=f"_rm_result{len(self.slots)}"
        while any(isinstance(n,ast.Name) and n.id==name for n in ast.walk(self.tree)):name+="_"
        slot=None if result=="none" else self.add_slot(result,name)
        if slot is not None:self.bindings[name]=(slot,result);assigned.add(slot)
        args=tuple(("var",n) for n in range(len(self.fields)))+tuple(arguments)
        replacement=ast.copy_location(ast.Constant(None) if slot is None else ast.Name(id=name,ctx=ast.Load()),call)
        return ("invoke",Helper(helper),args,slot),replacement

    def block(self, nodes, assigned, *, scoped=False):
        prior_borrows=set(self.borrows)
        rows, assigned, stopped = [], set(assigned), False
        for node in nodes:
            if isinstance(node,(ast.Assign,ast.AnnAssign,ast.Expr,ast.Return)) and isinstance(node.value,ast.Call):
                invocation=self.method_call(node.value,assigned)
                if invocation is not None:
                    from copy import copy
                    call,replacement=invocation
                    rows.append(call)
                    if isinstance(node,ast.Expr):continue
                    node=copy(node);node.value=replacement
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
                    if ct.startswith("dict["):
                        key,kt = self.coerce(key,kt,parts(ct)[0],target.slice)
                        expression,kind = self.coerce(expression,kind,parts(ct)[1],value)
                    if not ct.startswith("dict[") or parts(ct) != [kt, kind]: self.fail(target, "dictionary assignment type mismatch")
                    self.refined = set()
                    # Python assignment evaluates the RHS before its target key;
                    # dictionary construction evaluates each key before its value.
                    stored = self.add_slot(kind, f"_rm_store{len(self.slots)}")
                    rows.append(("assign", stored, expression))
                    rows.append(("assign", container[1], ("dict_set", container, key, ("var", stored))))
                    continue
                self.expected = (annotation(ast.unparse(node.annotation),namespace=self.function.__globals__) if isinstance(node, ast.AnnAssign) else
                    self.fields.get(target.attr) if isinstance(target, ast.Attribute) else
                    self.bindings.get(target.id, (None, None))[1] if isinstance(target, ast.Name) else None)
                expression, kind = self.expr(value, assigned)
                expression, kind = self.coerce(expression,kind,self.expected,value)
                self.expected = None
                if isinstance(node, ast.AnnAssign) and annotation(ast.unparse(node.annotation),namespace=self.function.__globals__) != kind:
                    self.fail(node, "assignment annotation mismatch")
                if mutable(kind) and expression[0] == "var":
                    donor=expression[1]
                    if donor>=len(self.inputs) and donor>=len(self.fields) and isinstance(value,ast.Name) and value.id not in self.borrows:
                        self.check_borrow(node,donor,write=True)
                        self.moves.append(dict(donor=donor,position=(node.end_lineno,node.end_col_offset)))
                        self.moved.add(donor);assigned.remove(donor)
                    else:
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
                if slot in self.moved: self.fail(node,"use after ownership transfer")
                if kind != expected or slot is None: self.fail(node, "assignment changes variable type")
                if mutable(kind): self.check_borrow(target,slot,write=True)
                target_key = ast.dump(ast.Name(id=target.id,ctx=ast.Load())) if isinstance(target,ast.Name) else ast.dump(ast.Attribute(value=target.value,attr=target.attr,ctx=ast.Load()))
                self.refined = {key for key in self.refined if target_key not in key}
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
                key,kt = self.coerce(key,kt,parts(ct)[0],call.args[0])
                if parts(ct) != [kt]: self.fail(node, "set element type mismatch")
                rows.append(("assign", container[1], ("set_" + call.func.attr, container, key)))
            elif isinstance(node, ast.For):
                if node.orelse or not isinstance(node.target, ast.Name):
                    self.fail(node, "use a plain dictionary-key loop without else")
                container, ct = self.binding(node.iter, assigned)
                if not mutable(ct): self.fail(node,"iteration requires a finite collection")
                if node.target.id in self.bindings or node.target.id in self.objects:
                    self.fail(node, "loop variables must be fresh locals")
                slot = self.add_slot(parts(ct)[0], node.target.id)
                self.bindings[node.target.id] = (slot, parts(ct)[0])
                borrow_name = f"iteration at line {self.line + node.lineno - 1}"
                self.borrows[borrow_name] = (container[1], False,
                    (node.end_lineno,node.end_col_offset), (node.lineno,node.col_offset))
                self.loans.append(dict(owner=container[1],name=borrow_name,exclusive=False,
                    start=(node.lineno,node.col_offset),finish=(node.end_lineno,node.end_col_offset)))
                self.refined = set()  # A later iteration may follow a write.
                body, _, _ = self.block(node.body, assigned | {slot},scoped=True)
                self.refined = set()
                del self.borrows[borrow_name]
                dead = [(n,self.slots[n]) for n in range(slot,len(self.slots))]
                rows.append(("each", ct, container, slot, body,tuple(dead)))
            elif isinstance(node, ast.If):
                condition, kind = self.expr(node.test, assigned)
                if kind != "bool": self.fail(node, "condition must be Boolean")
                saved = self.refined.copy()
                self.refined |= self.refinement(node.test,True)
                yes, ya, yr = self.block(node.body, assigned,scoped=True)
                yes_refined = self.refined.copy()
                self.refined = saved | self.refinement(node.test,False)
                no, na, nr = self.block(node.orelse, assigned,scoped=True)
                self.refined = self.refined if yr and not nr else yes_refined if nr and not yr else self.refined & yes_refined
                assigned = na if yr and not nr else ya if nr and not yr else ya & na
                stopped = yr and nr
                rows.append(("branch", condition, yes, no))
            elif isinstance(node, ast.Return):
                expression, kind = (literal(0), "none") if node.value is None else self.expr(node.value, assigned)
                expression,kind = self.coerce(expression,kind,self.result,node)
                if kind != self.result: self.fail(node, "return type mismatch")
                if self.initialize and not set(range(len(self.fields))) <= assigned:
                    self.fail(node, "constructor returns before initializing every field")
                rows.append(("ret", expression))
                stopped = True
            else: self.fail(node, "unsupported statement")
        if scoped:
            for name in set(self.borrows)-prior_borrows:
                del self.borrows[name]
                self.bindings.pop(name,None)
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
        # Shared inputs may alias an owned field at an ordinary Python call.
        # Reject a potential overlapping write instead of silently copying it.
        for access in self.accesses:
            if access['write'] and access['owner'] < len(self.fields):
                for other in self.accesses:
                    slot=other['owner']
                    if len(self.fields) <= slot < len(self.inputs) and mutable(self.inputs[slot]) and self.inputs[slot] == self.inputs[access['owner']]:
                        self.fail(self.tree, f"shared input may alias mutated state at {self.line+access['position'][0]-1}; input access at {self.line+other['position'][0]-1}")
        return Program(self.function.__name__, body, self.inputs, self.slots, len(self.fields) if self.method else 0, self.result, self.function, self.initialize, self.slot_names,
                       self.file, self.line, ast.dump(self.tree, include_attributes=True), self.column, self.helpers, self.loans, self.accesses, self.moves)


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
    kinds = [(p.name, annotation(p.annotation,namespace=function.__globals__)) for p in params[1:]]
    if any(k == "none" for _, k in kinds): raise Unsupported("method input annotations need a value type")
    result = "none" if initialize else annotation(inspect.signature(function).return_annotation,namespace=function.__globals__)
    if mutable(result): raise Unsupported("borrowed or mutable method results cannot escape")
    parser = Parser(function, fields, kinds, result, method=True, initialize=initialize)
    if initialize_arguments is None:
        return parser.parse()
    if not initialize or set(initialize_arguments) != {name for name, _ in kinds}:
        raise Unsupported("initializer argument names differ from constructor signature")
    bindings = []
    for name, kind in kinds:
        value = initialize_arguments[name]
        if not matches(value,kind):
            raise Unsupported("initializer argument type mismatch")
        slot, _ = parser.bindings[name]
        parser.assigned.add(slot)
        bindings.append(("assign", slot, source_literal(value,kind)))
    program = parser.parse()
    # Bind a finite constructor call before interpreting its unchanged body.
    for binding in reversed(bindings):
        program.body = ("seq", binding, program.body)
    return program


def predicate_program(function, fields, target, expected):
    params = parameters(function)
    kinds = [annotation(p.annotation, target, function.__globals__) for p in params]
    if kinds != expected or annotation(inspect.signature(function).return_annotation,namespace=function.__globals__) != "bool":
        raise Unsupported(f"{function.__name__}: expected predicate parameters {expected} and bool result")
    return Parser(function, fields, [(p.name, k) for p, k in zip(params, kinds)], "bool").parse()


def domain_program(function, fields, target):
    params=parameters(function)
    if len(params)!=1 or annotation(params[0].annotation,target,function.__globals__)!="state":
        raise Unsupported("Choice domain takes the previous global state")
    result=annotation(inspect.signature(function).return_annotation,namespace=function.__globals__)
    if not mutable(result):raise Unsupported("Choice domain returns a finite dict or set")
    return Parser(function,fields,[(params[0].name,"state")],result).parse()
