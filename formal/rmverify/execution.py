"""Execute the validated source tree for regression checks and witness proposals.

Only Lean correspondence and replay authorize proof/refutation statuses.
"""
import operator


def expression(e, env):
    match e:
        case ("lit" | "bool", n): return n
        case ("var", i): return env[i]
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
    env = list(values) + [False if k == "bool" else 0 for k in program.slots[len(values):]]
    def go(stmt, env, next_):
        match stmt:
            case ("skip",): return next_(env)
            case ("assign", slot, value):
                updated = list(env)
                updated[slot] = evaluate(value, env)
                return next_(updated)
            case ("seq", first, rest): return go(first, env, lambda e: go(rest, e, next_))
            case ("branch", condition, yes, no):
                return [choose(evaluate(condition, env), a, b)
                        for a,b in zip(go(yes, env, next_), go(no, env, next_), strict=True)]
            case ("ret", value): return env[:program.fields] + [evaluate(value, env)]
        raise ValueError("invalid source statement")
    return go(program.body, env, lambda e: e[:program.fields] + [0])
