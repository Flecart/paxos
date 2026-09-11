"""The flat collection subset; no evaluation of annotation strings."""
import ast
from typing import get_args, get_origin


def collection_type(value):
    origin = get_origin(value)
    if origin in (dict, set):
        args = ["int" if a is int else "bool" if a is bool else None for a in get_args(value)]
        if None not in args and len(args) == (2 if origin is dict else 1):
            return origin.__name__ + "[" + ",".join(args) + "]"
    if isinstance(value, str):
        try:
            node = ast.parse(value, mode="eval").body
        except SyntaxError:
            return None
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in ("dict", "set"):
            args = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            if len(args) == (2 if node.value.id == "dict" else 1) and all(isinstance(a, ast.Name) and a.id in ("int", "bool") for a in args):
                return node.value.id + "[" + ",".join(a.id for a in args) + "]"
    return None


def parts(kind):
    return kind[kind.index("[")+1:-1].split(",")


def mutable(kind):
    return kind.startswith(("dict[", "set["))


def matches(value, kind):
    if not mutable(kind):
        return type(value) is {"int": int, "bool": bool, "none": type(None)}[kind]
    args = parts(kind)
    if kind.startswith("dict["):
        return type(value) is dict and all(matches(k, args[0]) and matches(v, args[1]) for k,v in value.items())
    return type(value) is set and all(matches(v, args[0]) for v in value)


def probes(kind):
    if kind == "bool": return [False, True]
    if kind == "int": return [-10**100, -1, 0, 1, 10**100]
    args = parts(kind)
    keys = [False, True] if args[0] == "bool" else [0, 1]
    if kind.startswith("set["): return [set(), {keys[0]}, set(keys)]
    values = [False, True] if args[1] == "bool" else [7, -1]
    return [{}, {keys[0]: values[0]}, dict(zip(keys, values))]


def json_value(value):
    if isinstance(value, set): return {"set": sorted(value)}
    raise TypeError(f"cannot serialize {type(value).__name__}")
