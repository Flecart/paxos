"""Execute the validated source tree for regression checks and witness proposals.

Only Lean correspondence and replay authorize proof/refutation statuses.
"""
import operator
from copy import deepcopy
from .value_types import mutable


class ExecutionFault(KeyError):
    def __init__(self, fields):
        super().__init__("missingKey")
        self.fields = deepcopy(fields)


def expression(e, env):
    match e:
        case ("lit" | "bool", n): return n
        case ("var" | "bound", i): return env[i]
        case ("empty", k): return {} if k.startswith("dict[") else set()
        case ("all" | "any" as op, _, container, slot, body):
            def values():
                for item in expression(container, env):
                    local = list(env)
                    local[slot] = item
                    yield expression(body, local)
            return (all if op == "all" else any)(values())
        case ("length", a): return len(expression(a, env))
        case ("lookup", a, b): return expression(a, env)[expression(b, env)]
        case ("contains", _, a, b): return expression(b, env) in expression(a, env)
        case ("get", a, b, c): return expression(a, env).get(expression(b, env), expression(c, env))
        case ("dict_set", a, b, c):
            result = dict(expression(a, env))
            result[expression(b, env)] = expression(c, env)
            return result
        case ("set_add" | "set_discard" as op, a, b):
            result = set(expression(a, env))
            (result.add if op == "set_add" else result.discard)(expression(b, env))
            return result
        case ("bin", "and", a, b): return expression(a, env) and expression(b, env)
        case ("bin", "or", a, b): return expression(a, env) or expression(b, env)
        case ("ite", c, a, b): return expression(a if expression(c, env) else b, env)
        case ("bin", op, a, b):
            operations = dict(add=operator.add, sub=operator.sub, mul=operator.mul,
                eq=operator.eq, ne=operator.ne, lt=operator.lt, le=operator.le,
                gt=operator.gt, ge=operator.ge,
                **{"and": lambda a,b: bool(a and b), "or": lambda a,b: bool(a or b)})
            return operations[op](expression(a, env), expression(b, env))
    raise ValueError("invalid source expression")


def execute(program, values, *, evaluate=expression, choose=lambda c,a,b: a if c else b):
    if len(values) != len(program.inputs):
        raise ValueError("source input arity mismatch")
    env = deepcopy(list(values)) + [{} if k.startswith("dict[") else set() if k.startswith("set[") else False if k == "bool" else 0 for k in program.slots[len(values):]]
    def eval_at(value, env):
        try: return evaluate(value, env)
        except KeyError as error:
            raise ExecutionFault(env[:program.fields]) from error
    def go(stmt, env, next_):
        match stmt:
            case ("skip",): return next_(env)
            case ("assign", slot, value):
                updated = list(env)
                updated[slot] = eval_at(value, env)
                return next_(updated)
            case ("seq", first, rest): return go(first, env, lambda e: go(rest, e, next_))
            case ("branch", condition, yes, no):
                if evaluate is expression:
                    return go(yes if eval_at(condition, env) else no, env, next_)
                return [choose(eval_at(condition, env), a, b)
                        for a,b in zip(go(yes, env, next_), go(no, env, next_), strict=True)]
            case ("each", _, container, slot, body):
                items = list(eval_at(container,env))
                def loop(index, current):
                    if index == len(items): return next_(current)
                    updated = list(current)
                    updated[slot] = items[index]
                    return go(body,updated,lambda e: loop(index+1,e))
                return loop(0,env)
            case ("ret", value): return env[:program.fields] + [eval_at(value, env)]
        raise ValueError("invalid source statement")
    return go(program.body, env, lambda e: e[:program.fields] + [0])
