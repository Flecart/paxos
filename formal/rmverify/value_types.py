"""Validated Python value types; no evaluation of annotation strings."""
import ast
import dataclasses
import inspect
import sys
import textwrap
import types
import typing


class Kind(str):
    def __new__(cls, name, args=(), record=None, fields=None):
        value = super().__new__(cls, name)
        value.args, value.record, value.fields = tuple(args), record, fields
        return value

    def __eq__(self, other):
        if isinstance(other,Kind):
            return str.__eq__(self,other) and self.record is other.record and self.args==other.args
        return str.__eq__(self,other)

    def __ne__(self,other):return not self==other
    __hash__=str.__hash__


def parts(kind):
    return list(kind.args) if isinstance(kind, Kind) else kind[kind.index('[')+1:-1].split(',')


def mutable(kind):
    return kind.startswith(('dict[', 'set['))


def optional(kind):
    return kind.startswith('option[')


def record(kind):
    return getattr(kind, 'record', None)


def typed(kind):
    return kind not in ('int', 'bool', 'none')


def resolve(value, namespace=None, stack=()):
    namespace = namespace or {}
    if isinstance(value,Kind): return value
    if isinstance(value, str):
        def syntax(n):
            if isinstance(n, ast.Constant) and n.value is None: return type(None)
            if isinstance(n, ast.Name):
                builtins = dict(int=int, bool=bool, dict=dict, set=set, NoneType=type(None))
                if n.id in builtins: return builtins[n.id]
                if n.id in namespace: return namespace[n.id]
            if isinstance(n, ast.Attribute):
                base = syntax(n.value)
                if isinstance(base, types.ModuleType) and n.attr in vars(base): return vars(base)[n.attr]
            if isinstance(n, ast.BinOp) and isinstance(n.op, ast.BitOr):
                return union(resolve(syntax(n.left), namespace, stack), resolve(syntax(n.right), namespace, stack))
            if isinstance(n, ast.Subscript):
                base = syntax(n.value)
                nodes = n.slice.elts if isinstance(n.slice, ast.Tuple) else [n.slice]
                args = [resolve(syntax(a), namespace, stack) for a in nodes]
                if base in (dict, set): return collection(base, args)
                if base is typing.Optional and len(args) == 1: return union(args[0], 'none')
            raise ValueError('unsupported type annotation')
        value = syntax(ast.parse(value, mode='eval').body)
    if isinstance(value, Kind): return value
    if value is int: return 'int'
    if value is bool: return 'bool'
    if value is None or value is type(None): return 'none'
    origin = typing.get_origin(value)
    if origin in (dict, set): return collection(origin, [resolve(a,namespace,stack) for a in typing.get_args(value)])
    if origin in (typing.Union, types.UnionType):
        args = [resolve(a,namespace,stack) for a in typing.get_args(value)]
        if len(args) == 2: return union(*args)
    if inspect.isclass(value) and dataclasses.is_dataclass(value): return frozen_record(value, stack)
    raise ValueError(f'unsupported or missing type annotation: {value!r}')


def union(a,b):
    if a == 'none': a,b = b,a
    if b == 'none' and optional(a): return a
    if b != 'none' or a == 'none' or mutable(a):
        raise ValueError('only optional immutable values are supported')
    return Kind(f'option[{a}]', [a])


def collection(base, args):
    if len(args) != (2 if base is dict else 1) or any(mutable(a) or a == 'none' for a in args):
        raise ValueError('collections must be flat and contain immutable supported values')
    return Kind(base.__name__+'['+','.join(args)+']', args)


def frozen_record(target, stack):
    if target in stack: raise ValueError('recursive records are unsupported')
    if type(target) is not type or target.__bases__ != (object,):
        raise ValueError('records require a plain frozen dataclass')
    tree = ast.parse(textwrap.dedent(inspect.getsource(target))).body[0]
    if target.__name__ != tree.name or any(not part.isidentifier() and part != '<locals>' for part in target.__qualname__.split('.')) or any(not part.isidentifier() for part in target.__module__.split('.')):
        raise ValueError('record names must match their source and use Python identifiers')
    if target.__getattribute__ is not object.__getattribute__ or '__getattr__' in vars(target):
        raise ValueError('custom record attribute access is unsupported')
    namespace = vars(sys.modules[target.__module__])
    if len(tree.decorator_list) != 1:
        raise ValueError('records require exactly @dataclass(frozen=True)')
    decorator = tree.decorator_list[0]
    if not (isinstance(decorator,ast.Call) and isinstance(decorator.func,ast.Name)
            and namespace.get(decorator.func.id) is dataclasses.dataclass and not decorator.args
            and len(decorator.keywords) == 1 and decorator.keywords[0].arg == 'frozen'
            and isinstance(decorator.keywords[0].value,ast.Constant) and decorator.keywords[0].value.value is True):
        raise ValueError('records require exactly @dataclass(frozen=True)')
    fields, defaults = {}, {}
    for node in tree.body:
        if isinstance(node,ast.Pass) or isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str): continue
        if not isinstance(node,ast.AnnAssign) or not isinstance(node.target,ast.Name):
            raise ValueError('record bodies contain annotated fields only')
        name = node.target.id
        if name.startswith('__'): raise ValueError('record fields require ordinary identifiers')
        k = resolve(ast.unparse(node.annotation),namespace,(*stack,target))
        if mutable(k) or k == 'none': raise ValueError('record fields must be immutable')
        fields[name] = k
        if node.value is not None:
            try: default = ast.literal_eval(node.value)
            except (ValueError,TypeError): raise ValueError('record defaults must be immutable literals')
            if not matches(default,k): raise ValueError('record default type mismatch')
            defaults[name] = default
    if not fields: raise ValueError('records need at least one field')
    actual = {n:resolve(a,namespace,(*stack,target)) for n,a in inspect.get_annotations(target).items()}
    if actual != fields: raise ValueError('loaded record annotations differ from source')
    absent = object()
    for name in fields:
        declared,loaded = defaults.get(name,absent),vars(target).get(name,absent)
        if (declared is absent) != (loaded is absent) or declared is not absent and (type(loaded) is not type(declared) or loaded != declared):
            raise ValueError('record field descriptors/defaults differ from source')
    # Validate generated behavior, including monkey-patched methods. The stdlib
    # dataclass generator is part of the explicitly documented Python boundary.
    reference = dataclasses.make_dataclass(target.__name__, [(n,int,defaults[n]) if n in defaults else (n,int) for n in fields], frozen=True)
    for name in ('__init__','__eq__','__hash__','__setattr__','__delattr__'):
        f,g = getattr(target,name),getattr(reference,name)
        if not inspect.isfunction(f) or any(getattr(f.__code__,a) != getattr(g.__code__,a)
                for a in ('co_code','co_names','co_varnames','co_consts','co_freevars')) or f.__defaults__ != g.__defaults__:
            raise ValueError(f'loaded record {name} differs from frozen dataclass behavior')
        closure = inspect.getclosurevars(f)
        standard = inspect.getclosurevars(g)
        if {**closure.builtins,**closure.globals} != {**standard.builtins,**standard.globals}:
            raise ValueError('modified frozen dataclass builtin binding')
        if any(v is not (target if n == 'cls' else object if 'object' in n else dataclasses.FrozenInstanceError)
               for n,v in closure.nonlocals.items()):
            raise ValueError('modified frozen dataclass closure')
    result = Kind('record:'+target.__module__+'.'+target.__qualname__, record=target, fields=fields)
    result.defaults = defaults
    return result


def record_types(kinds):
    result = {}
    def visit(k):
        for a in getattr(k,'args',()): visit(a)
        if record(k) and str(k) in result and result[str(k)].record is not k.record:
            raise ValueError("distinct loaded record classes share a source name; reload the module")
        if record(k) and str(k) not in result:
            for a in k.fields.values(): visit(a)
            result[str(k)] = k
    for k in kinds: visit(k)
    return list(result.values())


def matches(value, kind):
    if optional(kind): return value is None or matches(value,parts(kind)[0])
    if record(kind): return type(value) is kind.record and all(matches(getattr(value,n),k) for n,k in kind.fields.items())
    if not mutable(kind): return type(value) is {'int':int,'bool':bool,'none':type(None)}[kind]
    args = parts(kind)
    if kind.startswith('dict['): return type(value) is dict and all(matches(k,args[0]) and matches(v,args[1]) for k,v in value.items())
    return type(value) is set and all(matches(v,args[0]) for v in value)


def default_value(kind):
    if optional(kind) or kind == 'none': return None
    if record(kind): return kind.record(*(default_value(k) for k in kind.fields.values()))
    if kind.startswith('dict['): return {}
    if kind.startswith('set['): return set()
    return False if kind == 'bool' else 0


def probes(kind):
    if kind == 'bool': return [False, True]
    if kind == 'int': return [-10**100, -1, 0, 1, 10**100]
    if optional(kind): return [None, *probes(parts(kind)[0])[:2]]
    if record(kind):
        return [kind.record(*(probes(k)[i % len(probes(k))] for k in kind.fields.values())) for i in (0,1,2)]
    args = parts(kind)
    keys = probes(args[0])[:2] if typed(args[0]) else [False,True] if args[0] == 'bool' else [0,1]
    if kind.startswith('set['): return [set(), {keys[0]}, set(keys)]
    values = probes(args[1])[:2] if typed(args[1]) else [False,True] if args[1] == 'bool' else [7,-1]
    return [{}, {keys[0]:values[0]}, dict(zip(keys,values))]


def json_value(value):
    if isinstance(value,set): return {'set':sorted(value,key=repr)}
    if dataclasses.is_dataclass(value): return {'record':type(value).__module__+'.'+type(value).__qualname__, 'fields':vars(value)}
    raise TypeError(f'cannot serialize {type(value).__name__}')


def data(value):
    """JSON evidence supports immutable record keys without lossy stringification."""
    if dataclasses.is_dataclass(value) and not isinstance(value,type):
        fields = {f.name:data(getattr(value,f.name)) for f in dataclasses.fields(value)}
        if getattr(type(value),'__dataclass_params__').frozen and type(value).__module__ != 'rmverify.api':
            return {'record':type(value).__module__+'.'+type(value).__qualname__, 'fields':fields}
        return fields
    if isinstance(value,dict):
        if any(not isinstance(k,str) for k in value):
            return {'dict':[[data(k),data(v)] for k,v in value.items()]}
        return {k:data(v) for k,v in value.items()}
    if isinstance(value,set): return {'set':[data(v) for v in sorted(value,key=repr)]}
    if isinstance(value,(list,tuple)): return [data(v) for v in value]
    return value
