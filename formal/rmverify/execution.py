"""Execute the validated source tree for regression checks and witness proposals.

Only Lean correspondence and replay authorize proof/refutation statuses.
"""
import operator
from copy import deepcopy
from .value_types import mutable, default_value


class ExecutionFault(KeyError):
    def __init__(self, fields, reason="missingKey"):
        super().__init__(reason)
        self.reason = reason
        self.fields = deepcopy(fields)


def expression(e, env):
    match e:
        case ("helper", helper, args): return execute(helper.program,[expression(a,env) for a in args])[0]
        case ("coerce_none", k, a):
            expression(a,env)
            return 0 if k=="none" else None
        case ("get_optional_default", _, a, b, c):
            container=expression(a,env);key=expression(b,env)
            expression(c,env)
            return container.get(key)
        case ("none", _): return None
        case ("some", a): return expression(a,env)
        case ("is_none", a): return expression(a,env) is None
        case ("unwrap", a):
            v = expression(a,env)
            if v is None: raise AttributeError('None record access')
            return v
        case ("get_optional", _,a,b): return expression(a,env).get(expression(b,env))
        case ("record", k, values, labels): return k.record(**dict(zip(labels,(expression(v,env) for v in values))))
        case ("field", _,name,a): return getattr(expression(a,env),name)
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
            key = expression(b, env)
            value = expression(c, env)
            result[key] = value
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
    env = deepcopy(list(values)) + [default_value(k) for k in program.slots[len(values):]]
    def eval_at(value, env):
        try: return evaluate(value, env)
        except ExecutionFault as error:
            raise ExecutionFault(env[:program.fields],error.reason) from error
        except (KeyError,AttributeError) as error:
            raise ExecutionFault(env[:program.fields], "missingKey" if isinstance(error,KeyError) else "missingValue") from error
    def go(stmt, env, next_):
        match stmt:
            case ("invoke", helper, args, slot):
                values=[eval_at(arg,env) for arg in args]
                updated=list(env)
                try: result=execute(helper.program,values)
                except ExecutionFault as error:
                    updated[:helper.program.fields]=error.fields
                    raise ExecutionFault(updated[:program.fields],error.reason) from error
                updated[:helper.program.fields]=result[:-1]
                if slot is not None:updated[slot]=result[-1]
                return next_(updated)
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
            case ("each", _, container, slot, body, dead):
                items = list(eval_at(container,env))
                def loop(index, current):
                    if index == len(items): return next_(current)
                    updated = list(current)
                    updated[slot] = items[index]
                    def resume(e):
                        for n,k in dead: e[n] = default_value(k)
                        return loop(index+1,e)
                    return go(body,updated,resume)
                return loop(0,env)
            case ("ret", value): return env[:program.fields] + [eval_at(value, env)]
        raise ValueError("invalid source statement")
    return go(program.body, env, lambda e: e[:program.fields] + [0])
