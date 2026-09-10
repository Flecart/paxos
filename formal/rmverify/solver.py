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


def graph(g, values):
    env = list(values)
    for e in g["terms"]: env.append(expression(e,env))
    return [env[i] for i in g["outputs"]]


def concrete(model, values):
    result = [model.eval(value,model_completion=True) for value in values]
    return [z3.is_true(value) if z3.is_bool(value) else value.as_long() for value in result]


def counterexamples(model, depth, timeout, wanted):
    solver = z3.Solver()
    solver.set(timeout=max(1,int(timeout*1000)))
    graphs, methods = model["graphs"],model["methods"]
    states = [graph(graphs[0],[])[:-1]]
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
            query(p["identifier"], z3.Not(graph(graphs[p["index"]],state)[0]),["invariant",i])
        if k == depth or set(found) == wanted: break
        choices = [[(z3.Bool if kind=="bool" else z3.Int)(f"input_{k}_{j}_{n}") for n,kind in enumerate(m["inputs"])] for j,m in enumerate(methods)]
        outputs = [graph(graphs[m["index"]],state+args) for m,args in zip(methods,choices)]
        for i,c in enumerate(model["contracts"]):
            j = c["method"]
            args, m, output = choices[j],methods[j],outputs[j]
            pre = z3.BoolVal(True) if c["requires"] is None else graph(graphs[c["requires"]],state+args)[0]
            post_args = state+output[:-1]+([] if m["result"]=="none" else output[-1:])+args
            post = graph(graphs[c["ensures"]],post_args)[0]
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
