"""Typed collection definitions and source correspondence on the shared RM library."""
from textwrap import indent
import re
from . import lean_backend as lean
from .value_types import mutable, parts


def kind(k):
    if k.startswith("set["): return f"List {kind(parts(k)[0])}"
    if k.startswith("dict["):
        a,b = parts(k)
        return f"List ({kind(a)} × {kind(b)})"
    return lean.kind(k)


def default(k):
    return "[]" if mutable(k) else {"int":"0", "bool":"false", "none":"()"}[k]


def operation(e):
    """Builtin meanings shared by the two emitters, not arbitrary Python calls."""
    match e:
        case ("keys", a): return [a], "fun a => .ok (a.map Prod.fst)"
        case ("length", a): return [a], "fun a => .ok (Int.ofNat a.length)"
        case ("lookup", a, b): return [a,b], "dictLookup"
        case ("contains", k, a, b):
            return [a,b], "fun a b => .ok (decide (b ∈ " + ("a.map Prod.fst" if k.startswith("dict[") else "a") + "))"
        case ("set_add", a, b): return [a,b], "fun a b => .ok (setAdd a b)"
        case ("set_discard", a, b): return [a,b], "fun a b => .ok (setDiscard a b)"
        case ("pair", a, b): return [a,b], "fun a b => .ok (a, b)"
        case ("dict_set", a, b, c): return [a,("pair",b,c)], "fun a b => .ok (dictSet a b.1 b.2)"
        case ("get", a, b, c): return [a,("pair",b,c)], "fun a b => .ok ((dictGet a b.1).getD b.2)"
        case ("bin", op, a, b):
            symbol = {"add":"+", "sub":"-", "mul":"*", "eq":"==", "ne":"!=", "lt":"<", "le":"≤", "gt":">", "ge":"≥"}[op]
            value = f"(a {symbol} b)"
            if op in ("lt", "le", "gt", "ge"): value = f"decide {value}"
            return [a,b], f"fun a b => .ok ({value})"
    raise ValueError(f"unsupported typed expression {e}")


def expression(e, *, source, frame="f"):
    match e:
        case ("lit", n): return f"(.value ({n} : Int))" if source else f"(.ok ({n} : Int))"
        case ("bool", b): return f"(.{'value' if source else 'ok'} {str(b).lower()})"
        case ("empty", k): return f"(.{'value' if source else 'ok'} ([] : {kind(k)}))"
        case ("bound", n): return f"(.value q{n})" if source else f"(Except.ok q{n})"
        case ("all" | "any" as op, ct, container, slot, body):
            domain = ("keys", container) if ct.startswith("dict[") else container
            domain = expression(domain,source=source,frame=frame)
            body = expression(body,source=source,frame=frame)
            return f"(.{op} {domain} (fun q{slot} => {body}))" if source else f"({domain} >>= fun xs => {op}M (fun q{slot} => {body}) xs)"
        case ("var", n): return f"(.read (fun f => f.v{n}))" if source else f"(.ok {frame}.v{n})"
        case ("bin", "and", a, b): return expression(("ite",a,b,("bool",False)),source=source,frame=frame)
        case ("bin", "or", a, b): return expression(("ite",a,("bool",True),b),source=source,frame=frame)
        case ("ite", c, a, b):
            c,a,b = [expression(x,source=source,frame=frame) for x in (c,a,b)]
            return f"(.cond {c} {a} {b})" if source else f"({c} >>= fun c => if c then {a} else {b})"
    args, op = operation(e)
    values = [expression(a,source=source,frame=frame) for a in args]
    if source: return f"(.call{'₁' if len(args)==1 else '₂'} ({op}) {' '.join(values)})"
    result = f"(({op}) {' '.join('x'+str(i) for i in range(len(args)))})"
    for i,v in reversed(list(enumerate(values))): result = f"({v} >>= fun x{i} => {result})"
    return result


def source_statement(s, result):
    match s:
        case ("skip",): return ".skip"
        case ("assign", n, e): return f"(.assign (fun f v => {{f with v{n} := v}}) {expression(e,source=True)})"
        case ("seq", a, b): return f"(.seq {source_statement(a,result)} {source_statement(b,result)})"
        case ("branch", c, a, b): return f"(.branch {expression(c,source=True)} {source_statement(a,result)} {source_statement(b,result)})"
        case ("each", _, container, slot, body):
            domain = expression(("keys",container),source=True)
            assign = f"(.assign (fun f v => {{f with v{slot} := v}}) (.value q{slot}))"
            return f"(.each {domain} (fun q{slot} => .seq {assign} {source_statement(body,result)}))"
        case ("ret", e): return f"(.ret {'(.value ())' if result == 'none' else expression(e,source=True)})"
    raise ValueError("unsupported typed statement")


def compiled_definition(p, i):
    def go(s, finish):
        match s:
            case ("skip",): return finish
            case ("seq", a, b): return go(a, go(b, finish))
            case ("assign", n, e):
                return f"match {expression(e,source=False)} with\n| .error reason => .fault f reason\n| .ok value =>\n" + indent(f"let f := {{f with v{n} := value}}\n{finish}","  ")
            case ("each", _, container, slot, body):
                domain = expression(("keys",container),source=False)
                loop_body = f"let f := {{f with v{slot} := q{slot}}}\n" + go(body,".next f")
                loop = f"(eachM (fun q{slot} f =>\n" + indent(loop_body,"  ") + f") items f).bind (fun f =>\n" + indent(finish,"  ") + ")"
                return f"match {domain} with\n| .error reason => .fault f reason\n| .ok items =>\n" + indent(loop,"  ")
            case ("ret", e):
                value = "(.ok () : Except Fault Unit)" if p.result == "none" else expression(e,source=False)
                return f"match {value} with\n| .error reason => .fault f reason\n| .ok value => .returned f value"
            case ("branch", c, a, b):
                branches = "if value then\n" + indent(go(a,finish),"  ") + "\nelse\n" + indent(go(b,finish),"  ")
                return f"match {expression(c,source=False)} with\n| .error reason => .fault f reason\n| .ok value =>\n" + indent(branches,"  ")
        raise ValueError("unsupported typed statement")
    name = f"«{p.function.__qualname__}_{i}»"
    lines = [f"def {name} (f : Frame{i}) : Outcome Frame{i} {kind(p.result)} :=", indent(go(p.body,".next f"),"  "),
             f"def compiled{i} := {name}"]
    return lines, [name, f"compiled{i}"]


REDUCE = "TypedSource.Expr.eval, TypedSource.Stmt.exec, TypedSource.Outcome.bind, Bind.bind, Pure.pure, Except.bind, Except.pure, dictLookup"


def tactic(names):
    return (f"simp_all (config := {{failIfUnchanged := false}}) [{', '.join(names)}, {REDUCE}]\n"
            f"all_goals repeat' (first | omega | split <;> simp_all (config := {{failIfUnchanged := false}}) [{REDUCE}])\n"
            "all_goals first | omega | grind [dictSet_length_of_mem, dictSet_keys, setAdd_mem, List.all_eq_true]")


def frame_value(p, inputs):
    values = list(inputs) + [default(k) for k in p.slots[len(inputs):]]
    return "⟨" + ", ".join(values) + "⟩"


def source_frame_value(p, inputs):
    # Source bindings use named fields independently of the compiled adapter.
    return "{" + ", ".join(f"v{n} := {inputs[n] if n < len(inputs) else default(k)}"
                            for n,k in enumerate(p.slots)) + "}"


def state_projection(p, i, fields):
    values = ", ".join(f"f.v{n}" for n in range(len(fields)))
    return [f"def stateOf{i} : Outcome Frame{i} {kind(p.result)} → State",
            f"  | .next f => ⟨{values}, none⟩", f"  | .returned f _ => ⟨{values}, none⟩",
            f"  | .fault f reason => ⟨{values}, some reason⟩"]


def extra_audits(model):
    return (["Verified.safe_agreement"] +
            [f"Verified.stateOf_agreement{i}" for i,p in enumerate(model["programs"]) if p.fields] +
            [f"Verified.result_agreement{j}" for j in range(len(model["contracts"]))])


def definitions(model):
    lines = ["import VeilAdapter", "import TypedSource", "set_option veil.smt.trust false", "open RMVerify", "open RMVerify.TypedSource", "namespace Verified",
             "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000", "set_option linter.all false"]
    names = []
    for i,p in enumerate(model["programs"]):
        lines += [f"structure Frame{i} where"] + [f"  v{n} : {kind(k)}" for n,k in enumerate(p.slots)] + ["  deriving Repr, DecidableEq"]
        src = source_statement(p.body,p.result)
        lines += [f"def source{i} : TypedSource.Stmt Frame{i} {kind(p.result)} := {src}"]
        compiled, reductions = compiled_definition(p,i)
        lines += compiled
        names += [f"source{i}", *reductions]
        lines += [f"theorem translation{i} (f : Frame{i}) : source{i}.exec f = compiled{i} f := by", indent(tactic([f"source{i}",*reductions]),"  "), f"#print axioms translation{i}"]
    fields = list(model["fields"])
    lines += ["structure State where"] + [f"  «{n}» : {kind(k)}" for n,k in model["fields"].items()] + ["  «$fault» : Option Fault", "  deriving Repr, DecidableEq"]
    lines += ["inductive Action where"]
    for j,m in enumerate(model["methods"]): lines.append(f"  | m{j} {lean.arguments(m['inputs'])}")
    lines += ["  deriving Repr, DecidableEq"]
    # Every outcome, including faults, becomes a state. Fault states are absorbing.
    for i,p in enumerate(model["programs"]):
        if p.fields:
            lines += state_projection(p,i,fields)
            projected = [f"«{n}» := o.frame.v{j}" for j,n in enumerate(fields)] + ["«$fault» := o.fault?"]
            lines += [f"def sourceStateOf{i} (o : Outcome Frame{i} {kind(p.result)}) : State := {{" + ", ".join(projected) + "}",
                      f"theorem stateOf_agreement{i} : sourceStateOf{i} = stateOf{i} := by",
                      "  funext o; cases o <;> rfl", f"#print axioms stateOf_agreement{i}"]
            names.append(f"stateOf{i}")
    for source in (False,True):
        prefix = "source" if source else ""
        builder = source_frame_value if source else frame_value
        projection = "sourceStateOf" if source else "stateOf"
        initial = builder(model["programs"][0], [])
        run = lambda i,frame: f"source{i}.exec ({frame})" if source else f"compiled{i} ({frame})"
        for j,m in enumerate(model["methods"]):
            frame = builder(model["programs"][m["index"]], [f"s.«{n}»" for n in fields] + [f"a{n}" for n in range(len(m["inputs"]))])
            lines += [f"def {prefix}step{j} (s : State) {lean.arguments(m['inputs'])} : State :=",
                      f"  if s.«$fault».isSome then s else {projection}{m['index']} ({run(m['index'],frame)})"]
            names.append(f"{prefix}step{j}")
        name = "sourceModel" if source else "model"
        lines += [f"def {name} : Model State Action where", f"  initial := {projection}0 ({run(0,initial)})", "  step s action := match action with"]
        for j,m in enumerate(model["methods"]): lines.append(f"    | .m{j} {lean.actuals(m['inputs'])} => {prefix}step{j} s {lean.actuals(m['inputs'])}")
        names.append(name)
    lines += ["theorem source_model_eq : sourceModel = model := by", "  simp only [sourceModel, model, " + ", ".join([f"sourcestep{j}, step{j}" for j in range(len(model["methods"]))] + [f"translation{i}" for i in range(len(model["programs"]))]+[f"stateOf_agreement{i}" for i,p in enumerate(model["programs"]) if p.fields]) + "]", "#print axioms source_model_eq"]
    for j,m in enumerate(model["methods"]):
        args,binders = lean.actuals(m["inputs"]),lean.arguments(m["inputs"])
        lines += [f"theorem step_agreement{j} (s : State) {binders} : sourcestep{j} s {args} = step{j} s {args} := by",
                  f"  change sourceModel.step s (.m{j} {args}) = model.step s (.m{j} {args})",
                  "  rw [source_model_eq]"]
    for j,prop in enumerate(model["invariants"]):
        i=prop["index"]
        frame=frame_value(model["programs"][i],[f"s.«{n}»" for n in fields])
        sf=source_frame_value(model["programs"][i],[f"s.«{n}»" for n in fields])
        lines += [f"def inv{j} (s : State) : Prop := ∃ f, compiled{i} ({frame}) = .returned f true",
                  f"def sourceInv{j} (s : State) : Prop := ∃ f, source{i}.exec ({sf}) = .returned f true",
                  f"theorem inv_agreement{j} (s : State) : sourceInv{j} s ↔ inv{j} s := by simp only [sourceInv{j}, inv{j}, translation{i}]",
                  f"#print axioms inv_agreement{j}"]
        names += [f"inv{j}"]
    lines += ["def safe (s : State) : Prop := s.«$fault» = none ∧ " + " ∧ ".join([f"inv{j} s" for j in range(len(model["invariants"]))]+["True"])]
    lines += ["def sourceSafe (s : State) : Prop := s.«$fault» = none ∧ " + " ∧ ".join([f"sourceInv{j} s" for j in range(len(model["invariants"]))]+["True"]),
              "theorem safe_agreement (s : State) : sourceSafe s ↔ safe s := by",
              "  simp only [sourceSafe, safe" + "".join(f", inv_agreement{j}" for j in range(len(model["invariants"]))) + "]",
              "#print axioms safe_agreement"]
    names.append("safe")
    for j,c in enumerate(model["contracts"]):
        m = model["methods"][c["method"]]
        binders,args = lean.arguments(m["inputs"]),lean.actuals(m["inputs"])
        fields_before = [f"s.«{n}»" for n in fields]
        fields_after = [f"(step{c['method']} s {args}).«{n}»" for n in fields]
        method_args = [f"a{n}" for n in range(len(m["inputs"]))]
        mf = frame_value(model["programs"][m["index"]],fields_before+method_args)
        lines += [f"def result{j} (s : State) {binders} : {kind(m['result'])} :=",
                  f"  match compiled{m['index']} ({mf}) with",
                  "  | .returned _ value => value", f"  | _ => {default(m['result'])}"]
        smf = source_frame_value(model["programs"][m["index"]],fields_before+method_args)
        lines += [f"def sourceResult{j} (s : State) {binders} : {kind(m['result'])} := (source{m['index']}.exec ({smf})).result?.getD ({default(m['result'])})",
                  f"theorem result_agreement{j} (s : State) {binders} : sourceResult{j} s {args} = result{j} s {args} := by",
                  f"  unfold sourceResult{j} result{j}", f"  rw [translation{m['index']}]",
                  f"  all_goals cases compiled{m['index']} ({smf}) <;> rfl", f"#print axioms result_agreement{j}"]
        names.append(f"result{j}")
        for which,index,values in (("pre",c["requires"],fields_before+method_args),
            ("post",c["ensures"],fields_before+fields_after+([] if m["result"] == "none" else [f"result{j} s {args}"])+method_args)):
            frame = frame_value(model["programs"][index],values) if index is not None else None
            native = f"∃ f, compiled{index} ({frame}) = .returned f true" if index is not None else "True"
            source_values = [v.replace(f"step{c['method']} ",f"sourcestep{c['method']} ").replace(f"result{j} ",f"sourceResult{j} ") for v in values]
            sf = source_frame_value(model["programs"][index],source_values) if index is not None else None
            source = f"∃ f, source{index}.exec ({sf}) = .returned f true" if index is not None else "True"
            source_name = "sourcePre" if which == "pre" else "sourcePost"
            lines += [f"def {which}{j} (s : State) {binders} : Prop := {native}",
                      f"def {source_name}{j} (s : State) {binders} : Prop := {source}",
                      f"theorem {which}_agreement{j} (s : State) {binders} : {source_name}{j} s {args} ↔ {which}{j} s {args} := by",
                      (f"  simp only [{source_name}{j}, {which}{j}, step_agreement{c['method']}, result_agreement{j}, translation{index}]" if index is not None else "  rfl"),
                      f"#print axioms {which}_agreement{j}"]
            names.append(f"{which}{j}")
    lines += ["end Verified"]
    return re.sub(r"(?<!\w)\.ok\b", "Except.ok", "\n".join(lines)+"\n"), names


def branch_hint(model, method):
    def first_branch(stmt):
        if stmt[0] == "branch": return stmt[1]
        if stmt[0] == "seq": return first_branch(stmt[1]) or first_branch(stmt[2])
        return None
    p=model["programs"][method["index"]]
    condition=first_branch(p.body)
    if condition is None: return []
    # Exhaustive cases, never a path assumption. Prior writes can make this
    # initial-frame hint unhelpful, but cannot make it exclude an execution.
    frame=frame_value(p,[f"s.«{n}»" for n in model["fields"]]+[f"a{n}" for n in range(len(method["inputs"]))])
    guard=expression(condition,source=False,frame=f"({frame} : Frame{method['index']})")
    guard=re.sub(r"(?<!\w)\.ok\b","Except.ok",guard)
    return [f"by_cases guard : (({guard} : Except Fault Bool).toOption.getD false) = true",
            f"all_goals simp [{REDUCE}, Except.toOption, Option.getD] at guard"]


def invariant_proof(model,names):
    lines=["import Translation", "set_option veil.smt.trust false", "open RMVerify RMVerify.TypedSource Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
           "theorem invariant : ∀ s, Reachable model s → safe s := by", "  apply invariant_of_induction", "  ·", indent(tactic(names),"    "),
           "  · intro s action hs", "    rcases hs with ⟨hfault, hs⟩", "    cases action with"]
    for j,m in enumerate(model["methods"]):
        lines.append(f"    | m{j} {lean.actuals(m['inputs'])} =>")
        lines += [indent(line,"      ") for line in branch_hint(model,m)]
        lines += ["      all_goals", indent(tactic(names),"        ")]
    lines += ["theorem no_fault (s : State) (h : Reachable model s) : s.«$fault» = none := (invariant s h).1",
           "theorem source_invariant : ∀ s, Reachable sourceModel s → sourceSafe s := by simpa only [source_model_eq, safe_agreement] using invariant",
           "theorem always_safe (states : Nat → State) (actions : Nat → Action)", "    (start : states 0 = model.initial)", "    (round : ∀ n, states (n+1) = model.step (states n) (actions n)) :", "    ∀ n, safe (states n) := invariant_always model safe invariant states actions start round",
           "theorem veil_invariant : ∀ s, model.toModule.toVeil.reachable () s → safe s := by", "  intro s h", "  exact invariant s ((reachable_iff model s).mpr ((Reactive.veil_reachable model.toModule s).mp h))",
           "#print axioms invariant", "#print axioms no_fault", "#print axioms source_invariant", "#print axioms always_safe", "#print axioms veil_invariant"]
    return "\n".join(lines)+"\n"


def contract_proof(model,names,index,have_invariant):
    c=model["contracts"][index]
    m=model["methods"][c["method"]]
    binders,args=lean.arguments(m["inputs"]),lean.actuals(m["inputs"])
    lines=["import " + ("Invariants" if have_invariant else "Translation"), "set_option veil.smt.trust false",
           "open RMVerify RMVerify.TypedSource Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
           f"theorem contract (s : State) {binders} (reachable : Reachable model s)",
           f"    (pre : pre{index} s {args}) : post{index} s {args} := by"]
    if have_invariant: lines.append("  have hs := invariant s reachable")
    lines += [indent(line,"  ") for line in branch_hint(model,m)]
    lines += ["  all_goals", indent(tactic(names),"    "),
              f"theorem source_contract (s : State) {binders} (reachable : Reachable sourceModel s)",
              f"    (pre : sourcePre{index} s {args}) : sourcePost{index} s {args} := by",
              f"  apply (post_agreement{index} s {args}).mpr",
              f"  apply contract s {args}", "  · simpa only [source_model_eq] using reachable",
              f"  · exact (pre_agreement{index} s {args}).mp pre", "#print axioms contract", "#print axioms source_contract"]
    return "\n".join(lines)+"\n"


def counterexamples(model, depth, unresolved):
    """Concrete proposals only; each refutation is separately replayed in Lean."""
    from itertools import product
    from .execution import execute, ExecutionFault
    witnesses = {}
    def examine(state, calls):
        for j,p in enumerate(model['invariants']):
            key = p['identifier']
            if key not in unresolved or key in witnesses: continue
            try: valid = execute(model['programs'][p['index']], state)[0]
            except ExecutionFault: valid = False
            if not valid:
                witnesses[key] = dict(kind='reachable_invariant', invariant=j, calls=calls, state=state)
    def fault(error, calls):
        if 'no-fault' in unresolved and 'no-fault' not in witnesses:
            witnesses['no-fault'] = dict(kind='reachable_fault', calls=calls, fault='missingKey', state=error.fields)
    try: initial = execute(model['programs'][0], [])[:-1]
    except ExecutionFault as error:
        fault(error, [])
        return witnesses
    examine(initial, [])
    pending = [(initial, [])]
    seen = {repr(initial)}
    for _ in range(depth):
        following = []
        for state, calls in pending:
            for m in model['methods']:
                domains = [[False, True] if k == 'bool' else [-1, 0, 1] for k in m['inputs']]
                for args in product(*domains):
                    trace = calls + [dict(method=m['name'], arguments=dict(zip(m['parameters'], args)))]
                    try: result = execute(model['programs'][m['index']], state + list(args))[:-1]
                    except ExecutionFault as error:
                        fault(error, trace)
                        continue
                    examine(result, trace)
                    key = repr(result)
                    # ponytail: at most 256 concrete states; the cap bounds
                    # witness discovery only, never the scope of a theorem.
                    if key not in seen and len(seen) < 256:
                        seen.add(key)
                        following.append((result, trace))
        pending = following
        if not pending: break
    return witnesses


def witness_proof(model, witness, names):
    lines = ['import Translation', 'set_option veil.smt.trust false', 'open RMVerify RMVerify.TypedSource Verified', 'set_option linter.all false',
             'def state0 : State := model.initial', 'theorem reach0 : Reachable model state0 := .initial']
    for n,call in enumerate(witness['calls']):
        j,m = next((j,m) for j,m in enumerate(model['methods']) if m['name'] == call['method'])
        args = ' '.join(lean.value(call['arguments'][p]) for p in m['parameters'])
        lines += [f'def state{n+1} : State := model.step state{n} (.m{j} {args})',
                  f'theorem reach{n+1} : Reachable model state{n+1} := .step reach{n}']
    n = len(witness['calls'])
    if witness['kind'] == 'reachable_fault':
        claim = 's.«$fault» = none'
        source_claim = claim
        rewrite = 'source_model_eq'
    else:
        j = witness['invariant']
        claim, source_claim = f'inv{j} s', f'sourceInv{j} s'
        rewrite = f'source_model_eq, inv_agreement{j}'
    bad = claim.replace('s.«$fault»',f'state{n}.«$fault»') if witness['kind'] == 'reachable_fault' else f"inv{witness['invariant']} state{n}"
    lines += [f'theorem bad : ¬ ({bad}) := by',
              indent('decide' if witness['kind'] == 'reachable_fault' else
                     tactic(names + [f'state{i}' for i in range(n+1)] +
                            ['dictGet', 'dictSet', 'setAdd', 'setDiscard', 'allM', 'anyM', 'eachM']), '  '),
              f'theorem refutation : ¬ (∀ s, Reachable model s → {claim}) := by',
              f'  intro h; exact bad (h state{n} reach{n})',
              f'theorem source_refutation : ¬ (∀ s, Reachable sourceModel s → {source_claim}) := by',
              f'  simpa only [{rewrite}] using refutation',
              '#print axioms refutation', '#print axioms source_refutation']
    return '\n'.join(lines)+'\n'
