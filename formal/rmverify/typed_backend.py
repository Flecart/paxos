"""Typed collection definitions and source correspondence on the shared RM library."""
from textwrap import indent
import re
import json
from . import lean_backend as lean
from .frontend import definition_order
from .value_types import mutable, parts, optional, record, record_types, probes


def kind(k):
    if record(k): return f"«{k[7:]}»"
    if optional(k): return f"(Option ({kind(parts(k)[0])}))"
    if k.startswith("set["): return f"(List ({kind(parts(k)[0])}))"
    if k.startswith("dict["):
        a,b = parts(k)
        return f"(List ({kind(a)} × {kind(b)}))"
    return lean.kind(k)


def arguments(kinds):
    return " ".join(f"(a{i} : {kind(k)})" for i,k in enumerate(kinds))


def packed_type(kinds):
    """Type the argument tuple before Lean elaborates nested helper calls."""
    if not kinds: return "Int"  # The zero-argument expression uses a dummy 0.
    if len(kinds) == 1: return kind(kinds[0])
    return f"({kind(kinds[0])} × {packed_type(kinds[1:])})"


def default(k):
    if optional(k): return "none"
    if record(k): return "⟨" + ", ".join(default(a) for a in k.fields.values()) + "⟩"
    return "[]" if mutable(k) else {"int":"0", "bool":"false", "none":"()"}[k]


def value(v,k):
    if optional(k): return "none" if v is None else f"(some ({value(v,parts(k)[0])}))"
    if record(k): return "({" + ", ".join(f"«{n}» := {value(getattr(v,n),a)}" for n,a in k.fields.items()) + f"}} : {kind(k)})"
    if k.startswith("set["): return "[" + ", ".join(value(x,parts(k)[0]) for x in sorted(v,key=repr)) + "]"
    if k.startswith("dict["): return "[" + ", ".join(f"({value(x,parts(k)[0])}, {value(y,parts(k)[1])})" for x,y in v.items()) + "]"
    return lean.value(v)


def operation(e):
    """Builtin meanings shared by the two emitters, not arbitrary Python calls."""
    match e:
        case ("coerce_none", k, a): return [a], f"fun _ => .ok ({default(k)} : {kind(k)})"
        case ("get_optional_default", k, a, b, c): return [a,("pair",b,c)], "fun a b => .ok (" + ("(dictGet a b.1).join" if optional(k) else "dictGet a b.1") + ")"
        case ("some", a): return [a], "fun a => .ok (some a)"
        case ("is_none", a): return [a], "fun a => .ok a.isNone"
        case ("unwrap", a): return [a], "optionGet"
        case ("get_optional", k, a, b): return [a,b], "fun a b => .ok (" + ("(dictGet a b).join" if optional(k) else "dictGet a b") + ")"
        case ("field", k, name, a): return [a], f"fun (a : {kind(k)}) => .ok a.«{name}»"
        case ("record", k, values, labels):
            def pack(xs): return xs[0] if len(xs)==1 else ("pair",xs[0],pack(xs[1:]))
            projections = []
            for i in range(len(values)):
                projections.append('a'+'.2'*i+('.1' if i<len(values)-1 else ''))
            fields = ', '.join(f'«{n}» := {projections[labels.index(n)]}' for n in k.fields)
            return [pack(values)], f"fun a => .ok ({{{fields}}} : {kind(k)})"
        case ("keys", a): return [a], "fun a => .ok (List.map Prod.fst a)"
        case ("length", a): return [a], "fun a => .ok (Int.ofNat (List.length a))"
        case ("lookup", a, b): return [a,b], "dictLookup"
        case ("contains", k, a, b):
            return [a,b], f"fun (a : {kind(k)}) (b : {kind(parts(k)[0])}) => .ok (decide (b ∈ " + ("a.map Prod.fst" if k.startswith("dict[") else "a") + "))"
        case ("set_add", a, b): return [a,b], "fun a b => .ok (setAdd a b)"
        case ("set_discard", a, b): return [a,b], "fun a b => .ok (setDiscard a b)"
        case ("pair", a, b): return [a,b], "fun a b => .ok (a, b)"
        case ("dict_set", a, b, c): return [a,("pair",b,c)], "fun a b => .ok (dictSet a b.1 b.2)"
        case ("get", a, b, c): return [a,("pair",b,c)], "fun a b => .ok ((dictGet a b.1).getD b.2)"
        case ("bin", op, a, b):
            symbol = {"add":"+", "sub":"-", "mul":"*", "eq":"=", "ne":"≠", "lt":"<", "le":"≤", "gt":">", "ge":"≥"}[op]
            value = f"(a {symbol} b)"
            if op in ("eq", "ne", "lt", "le", "gt", "ge"): value = f"decide {value}"
            return [a,b], f"fun a b => .ok ({value})"
    raise ValueError(f"unsupported typed expression {e}")


def total_expression(e, frame="f", depth=0):
    """Erase Except plumbing only for statically total builtin expressions.

    The source emitter is unchanged; translation theorems check this reduction.
    Helpers and potentially failing operations keep their explicit outcomes.
    """
    match e:
        case ("lit",n):return f"({n} : Int)"
        case ("bool",b):return str(b).lower()
        case ("var",n):return f"{frame}.v{n}"
        case ("bound",n):return f"q{n}"
        case ("native",n):return n
        case ("unwrap",("some",a)):return total_expression(a,frame,depth+1)
        case ("none",k):return f"(none : Option ({kind(k)}))"
        case ("empty",k):return f"([] : {kind(k)})"
        case ("helper",_,_) | ("lookup",_,_) | ("unwrap",_):return None
        # Keep tuple operands in typed Except bindings. Eager polymorphic
        # constructor applications can make Lean infer the operands as types.
        case ("pair",_,_):return None
        case ("bin","and" | "or" as op,a,b):
            av,bv=total_expression(a,frame,depth+1),total_expression(b,frame,depth+1)
            if av is not None and bv is not None:return f"({av} {'&&' if op=='and' else '||'} {bv})"
            return total_expression(("ite",a,b,("bool",False)) if op=='and' else ("ite",a,("bool",True),b),frame,depth)
        case ("ite",c,a,b):
            optional_arg=None; none_branch,some_branch=a,b
            if c[0]=='is_none':optional_arg=c[1]
            elif c[0:2]==('bin','eq') and c[2][0]=='is_none' and c[3]==('bool',False):
                optional_arg=c[2][1]; none_branch,some_branch=b,a
            if optional_arg is not None:
                variable=f'present{depth}'
                def substitute(e):
                    if e==optional_arg:return ('some',('native',variable))
                    return tuple(substitute(x) for x in e) if isinstance(e,tuple) else e
                arg=total_expression(optional_arg,frame,depth+1)
                yes=total_expression(none_branch,frame,depth+1)
                no=total_expression(substitute(some_branch),frame,depth+1)
                if all(v is not None for v in (arg,yes,no)):
                    return f'(match {arg} with | none => {yes} | some {variable} => {no})'
            c,a,b=[total_expression(x,frame,depth+1) for x in (c,a,b)]
            return None if any(x is None for x in (c,a,b)) else f"(if {c} then {a} else {b})"
        case ("all" | "any" as op,ct,container,slot,body):
            domain=total_expression(("keys",container) if ct.startswith('dict[') else container,frame,depth+1)
            body=total_expression(body,frame,depth+1)
            return None if domain is None or body is None else f"({domain}).{op} (fun q{slot} => {body})"
    args,op=operation(e)
    values=[total_expression(a,frame,depth+1) for a in args]
    if any(v is None for v in values):return None
    assert '=> .ok' in op
    return '('+op.replace('=> .ok','=>')+') '+' '.join(f'({v})' for v in values)


def expression(e, *, source, frame="f"):
    if not source:
        total=total_expression(e,frame)
        if total is not None:return f"(Except.ok ({total}))"
    match e:
        case ("lit", n): return f"(.value ({n} : Int))" if source else f"(.ok ({n} : Int))"
        case ("bool", b): return f"(.{'value' if source else 'ok'} {str(b).lower()})"
        case ("none", k): return f"(.{'value' if source else 'ok'} (none : Option ({kind(k)})))"
        case ("empty", k): return f"(.{'value' if source else 'ok'} ([] : {kind(k)}))"
        case ("bound", n): return f"(.value q{n})" if source else f"(Except.ok q{n})"
        case ("all" | "any" as op, ct, container, slot, body):
            domain = ("keys", container) if ct.startswith("dict[") else container
            domain = expression(domain,source=source,frame=frame)
            body = expression(body,source=source,frame=frame)
            return f"(.{op} {domain} (fun q{slot} => {body}))" if source else f"({domain} >>= fun xs => {op}M (fun q{slot} => {body}) xs)"
        case ("helper", helper, args):
            p = helper.program
            def packed(values): return values[0] if len(values)==1 else ("pair",values[0],packed(values[1:]))
            projections = ['a'+'.2'*i+('.1' if i<len(args)-1 else '') for i in range(len(args))]
            frame_value_ = source_frame_value(p,projections)
            callee = f"«source:{helper}».exec" if source else f"«compiled:{helper}»"
            op = f"fun (a : {packed_type(p.inputs)}) => ({callee} ({frame_value_})).toExcept ({default(p.result)})"
            arg = expression(packed(args) if args else ("lit",0),source=source,frame=frame)
            return f"(.call₁ ({op}) {arg})" if source else f"({arg} >>= ({op}))"
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


def invocation(helper,args,slot,source):
    p=helper.program
    def pack(xs):return xs[0] if len(xs)==1 else ("pair",xs[0],pack(xs[1:]))
    projections=['a'+'.2'*i+('.1' if i<len(args)-1 else '') for i in range(len(args))]
    frame=source_frame_value(p,projections)
    # The frame argument type is inferred from the named helper function.
    callee=f"«source:{helper}».exec" if source else f"«compiled:{helper}»"
    op=f"fun (a : {packed_type(p.inputs)}) => Except.ok ({frame})"
    arg=expression(pack(args),source=source)
    arg=f"(.call₁ ({op}) {arg})" if source else f"({arg} >>= ({op}))"
    merge="fun f c => {f with "+", ".join(f"v{n} := c.v{n}" for n in range(p.fields))+"}"
    save="fun f _ => f" if slot is None else f"fun f v => {{f with v{slot} := v}}"
    return arg,callee,merge,save,default(p.result)


def source_statement(s, result):
    match s:
        case ("invoke", helper, args, slot):
            arg,callee,merge,save,fallback=invocation(helper,args,slot,True)
            return f"(.invoke {arg} ({callee}) ({merge}) ({save}) ({fallback}))"
        case ("skip",): return ".skip"
        case ("assign", n, e): return f"(.assign (fun f v => {{f with v{n} := v}}) {expression(e,source=True)})"
        case ("seq", a, b): return f"(.seq {source_statement(a,result)} {source_statement(b,result)})"
        case ("branch", c, a, b): return f"(.branch {expression(c,source=True)} {source_statement(a,result)} {source_statement(b,result)})"
        case ("each", ct, container, slot, body, dead):
            domain = expression(("keys",container) if ct.startswith("dict[") else container,source=True)
            assign = f"(.assign (fun f v => {{f with v{slot} := v}}) (.value q{slot}))"
            clear = "fun f => {f with " + ", ".join(f"v{n} := {default(k)}" for n,k in dead) + "}"
            return f"(.each {domain} (fun q{slot} => .scope ({clear}) (.seq {assign} {source_statement(body,result)})))"
        case ("ret", e): return f"(.ret {expression(('coerce_none','none',e) if result == 'none' else e,source=True)})"
    raise ValueError("unsupported typed statement")


def compiled_definition(p, i):
    def go(s, finish):
        match s:
            case ("invoke", helper, args, slot):
                arg,callee,merge,save,fallback=invocation(helper,args,slot,False)
                update=lambda value: f"let f := ({save}) (({merge}) f c) ({value})\n"+finish
                return f"match {arg} with\n| .error reason => .fault f reason\n| .ok args =>\n  match {callee} args with\n  | .fault c reason => .fault (({merge}) f c) reason\n  | .next c =>\n"+indent(update(fallback),"    ")+"\n  | .returned c result =>\n"+indent(update("result"),"    ")
            case ("skip",): return finish
            case ("seq", a, b): return go(a, go(b, finish))
            case ("assign", n, e):
                return f"match {expression(e,source=False)} with\n| .error reason => .fault f reason\n| .ok value =>\n" + indent(f"let f := {{f with v{n} := value}}\n{finish}","  ")
            case ("each", ct, container, slot, body, dead):
                domain = expression(("keys",container) if ct.startswith("dict[") else container,source=False)
                loop_body = f"let f := {{f with v{slot} := q{slot}}}\n" + go(body,".next f")
                clear = "fun f => {f with " + ", ".join(f"v{n} := {default(k)}" for n,k in dead) + "}"
                loop_body = "("+loop_body+f" : Outcome Frame{i} {kind(p.result)}).mapFrame ("+clear+")"
                loop = f"(eachM (fun q{slot} f =>\n" + indent(loop_body,"  ") + f") items f).bind (fun f =>\n" + indent(finish,"  ") + ")"
                return f"match {domain} with\n| .error reason => .fault f reason\n| .ok items =>\n" + indent(loop,"  ")
            case ("ret", e):
                value = expression(("coerce_none","none",e) if p.result == "none" else e,source=False)
                return f"match {value} with\n| .error reason => .fault f reason\n| .ok value => .returned f value"
            case ("branch", c, a, b):
                branches = "if value then\n" + indent(go(a,finish),"  ") + "\nelse\n" + indent(go(b,finish),"  ")
                return f"match {expression(c,source=False)} with\n| .error reason => .fault f reason\n| .ok value =>\n" + indent(branches,"  ")
        raise ValueError("unsupported typed statement")
    name = f"«{p.function.__qualname__}_{i}»"
    lines = [f"def {name} (f : Frame{i}) : Outcome Frame{i} {kind(p.result)} :=", indent(go(p.body,".next f"),"  "),
             f"def compiled{i} := {name}"]
    return lines, [name, f"compiled{i}"]


REDUCE = "TypedSource.Expr.eval, TypedSource.Stmt.exec, TypedSource.Outcome.bind, Bind.bind, Pure.pure, Except.bind, Except.pure, dictLookup, optionGet, TypedSource.Outcome.toExcept, TypedSource.Outcome.mapFrame, Except.toOption, Option.getD"


def tactic(names, *, contextual=True):
    initial="simp_all" if contextual else "simp"
    location="" if contextual else " at *"
    return (f"{initial} (config := {{failIfUnchanged := false}}) [{', '.join(names)}, {REDUCE}]{location}\n"
            f"all_goals subst_vars\nall_goals repeat' (first | omega | split at * <;> subst_vars <;> simp_all (config := {{failIfUnchanged := false}}) [{REDUCE}])\n"
            "all_goals first | omega | grind (splits := 64) [dictSet_length_of_mem, dictSet_keys, setAdd_mem, setDiscard_mem, setAdd_length, setAdd_duplicate, allM_ok_true, List.all_eq_true]")


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


def set_quantifiers(p):
    result = []
    def visit(e):
        if not isinstance(e,tuple): return
        if e and e[0] in ("all","any") and e[1].startswith("set["): result.append(e)
        for child in e: visit(child)
    visit(p.body)
    return result


def quantifier_certificates(p,i,names):
    lines = []
    for j,(op,ct,_,slot,body) in enumerate(set_quantifiers(p)):
        bound = set()
        def visit(e):
            if not isinstance(e,tuple): return
            if e and e[0] == 'bound': bound.add(e[1])
            for x in e: visit(x)
        visit(body); bound.add(slot)
        other = sorted(bound-{slot})
        binders = ' '.join(f'(q{x} : {kind(p.slots[x])})' for x in other)
        args = ' '.join(f'q{x}' for x in other)
        body_expr = expression(body,source=True)
        total = f'set_total{i}_{j}'
        lines += [f'theorem {total} (f : Frame{i}) {binders} (q{slot} : {kind(p.slots[slot])}) :',
                  f'    ∃ b, ({body_expr} : TypedSource.Expr Frame{i} Bool).eval f = .ok b := by',
                  indent(tactic(names),'  '), f'#print axioms {total}',
                  f'theorem set_order{i}_{j} (f : Frame{i}) {binders} (xs ys : List ({kind(p.slots[slot])})) (perm : xs.Perm ys) :',
                  f'    {op}M (fun q{slot} => ({body_expr} : TypedSource.Expr Frame{i} Bool).eval f) xs =',
                  f'    {op}M (fun q{slot} => ({body_expr} : TypedSource.Expr Frame{i} Bool).eval f) ys := by',
                  f'  exact {op}M_total_order_independent _ xs ys perm (fun q{slot} => {total} f {args} q{slot})',
                  f'#print axioms set_order{i}_{j}']
    return lines


def borrow_certificate(p,i):
    loans = []
    for loan in p.loans or []:
        start,finish = loan['start'],loan['finish']
        loans.append(f"⟨{loan['owner']}, {json.dumps(loan['name'],ensure_ascii=False)}, {str(loan['exclusive']).lower()}, ({start[0]},{start[1]}), ({finish[0]},{finish[1]})⟩")
    accesses = []
    for access in p.accesses or []:
        via = 'none' if access['via'] is None else 'some '+json.dumps(access['via'],ensure_ascii=False)
        at = access['position']
        accesses.append(f"⟨{access['owner']}, {via}, {str(access['write']).lower()}, ({at[0]},{at[1]})⟩")
    moves = [f"⟨{m['donor']}, ({m['position'][0]}, {m['position'][1]})⟩" for m in p.moves or []]
    return [f"def loans{i} : List Borrowing.Loan := ["+', '.join(loans)+']',
            f"def accesses{i} : List Borrowing.Access := ["+', '.join(accesses)+']',
            f"theorem ownership{i} : Borrowing.valid {len(p.slots)} loans{i} accesses{i} := by",
            f"  simp [Borrowing.valid, Borrowing.Loan.permits, Borrowing.Loan.active, Borrowing.before, Borrowing.atMost, loans{i}, accesses{i}]",
            f"#print axioms ownership{i}",
            f"def moves{i} : List Borrowing.Move := ["+', '.join(moves)+']',
            f"theorem affine{i} : Borrowing.affine moves{i} accesses{i} := by simp [Borrowing.affine, Borrowing.before, moves{i}, accesses{i}]",
            f"#print axioms affine{i}"]


def extra_audits(model):
    return (["Verified.safe_agreement"] + [f"Verified.{n}{i}_{j}" for i,p in enumerate(model["programs"]) for j,_ in enumerate(set_loops(p)) for n in ("set_loop_commutes","set_loop_order")] +
            [f"Verified.{n}{i}" for i in range(len(model["programs"])) for n in ("ownership","affine")] +
            [f"Verified.{n}{i}_{j}" for i,p in enumerate(model["programs"]) for j,_ in enumerate(set_quantifiers(p)) for n in ("set_total","set_order")] +
            [f"Verified.stateOf_agreement{i}" for i,p in enumerate(model["programs"]) if p.fields] +
            [f"Verified.result_agreement{j}" for j in range(len(model["contracts"]))])


def program_definitions(model):
    lines = ["import VeilAdapter", "import TypedSource", "import Borrowing", "set_option veil.smt.trust false", "open RMVerify", "open RMVerify.TypedSource", "namespace Verified",
             "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000", "set_option linter.all false"]
    for k in record_types([k for p in model["programs"] for k in [*p.slots,p.result]]):
        lines += [f"structure {kind(k)} where"] + [f"  «{n}» : {kind(a)}" for n,a in k.fields.items()] + ["  deriving Repr, DecidableEq"]
    names, aliased = [], set()
    indices = {p.function: i for i,p in enumerate(model["programs"])}
    for i in definition_order(model["programs"]):
        p = model["programs"][i]
        lines += [f"structure Frame{i} where"] + [f"  v{n} : {kind(k)}" for n,k in enumerate(p.slots)] + ["  deriving Repr, DecidableEq"]
        for n in range(len(p.slots)):
            lines += [f"@[simp] theorem frame{i}_v{n}_ite (p : Prop) [Decidable p] (a b : Frame{i}) : (if p then a else b).v{n} = if p then a.v{n} else b.v{n} := by split <;> rfl"]
        src = source_statement(p.body,p.result)
        lines += [f"def source{i} : TypedSource.Stmt Frame{i} {kind(p.result)} := {src}"]
        compiled, reductions = compiled_definition(p,i)
        lines += compiled
        names += [f"source{i}", *reductions]
        lines += [f"theorem translation{i} (f : Frame{i}) : source{i}.exec f = compiled{i} f := by"]
        for n,k in enumerate(p.inputs):
            if optional(k):lines += [f"  all_goals cases h{n} : f.v{n}"]
        # Reuse checked helper correspondence instead of expanding both helper
        # bodies at every call. The caller's own source and code remain checked.
        support = []
        for helper in p.helpers or []:
            name = helper.function.__module__+'.'+helper.function.__qualname__
            support += [f"«source:{name}»", f"«compiled:{name}»", f"translation{indices[helper.function]}"]
        lines += ["  all_goals",indent(tactic([f"source{i}",*reductions] + support),"    "), f"#print axioms translation{i}"]
        helper_name = p.function.__module__+'.'+p.function.__qualname__
        if helper_name not in aliased:
            lines += [f"def «source:{helper_name}» := source{i}", f"def «compiled:{helper_name}» := compiled{i}"]
            names += [f"«source:{helper_name}»",f"«compiled:{helper_name}»"]
            aliased.add(helper_name)
        lines += quantifier_certificates(p,i,names)
        lines += borrow_certificate(p,i)
        lines += loop_certificates(p,i,names)
    return lines, names


def definitions(model):
    lines, names = program_definitions(model)
    fields = list(model["fields"])
    lines += ["structure State where"] + [f"  «{n}» : {kind(k)}" for n,k in model["fields"].items()] + ["  «$fault» : Option Fault", "  deriving Repr, DecidableEq"]
    lines += ["inductive Action where"]
    for j,m in enumerate(model["methods"]): lines.append(f"  | m{j} {arguments(m['inputs'])}")
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
            lines += [f"def {prefix}step{j} (s : State) {arguments(m['inputs'])} : State :=",
                      f"  if s.«$fault».isSome then s else {projection}{m['index']} ({run(m['index'],frame)})"]
            names.append(f"{prefix}step{j}")
        name = "sourceModel" if source else "model"
        lines += [f"def {name} : Model State Action where", f"  initial := {projection}0 ({run(0,initial)})", "  step s selected := match selected with"]
        for j,m in enumerate(model["methods"]): lines.append(f"    | .m{j} {lean.actuals(m['inputs'])} => {prefix}step{j} s {lean.actuals(m['inputs'])}")
        names.append(name)
    lines += ["theorem source_model_eq : sourceModel = model := by", "  simp only [sourceModel, model, " + ", ".join([f"sourcestep{j}, step{j}" for j in range(len(model["methods"]))] + [f"translation{i}" for i in range(len(model["programs"]))]+[f"stateOf_agreement{i}" for i,p in enumerate(model["programs"]) if p.fields]) + "]", "#print axioms source_model_eq"]
    for j,m in enumerate(model["methods"]):
        args,binders = lean.actuals(m["inputs"]),arguments(m["inputs"])
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
        binders,args = arguments(m["inputs"]),lean.actuals(m["inputs"])
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
           "  · intro s selected hs", "    rcases hs with ⟨hfault, hs⟩", "    cases selected with"]
    for j,m in enumerate(model["methods"]):
        lines.append(f"    | m{j} {lean.actuals(m['inputs'])} =>")
        lines += [indent(line,"      ") for line in branch_hint(model,m)]
        lines += ["      all_goals", indent(tactic(names),"        ")]
    lines += ["theorem no_fault (s : State) (h : Reachable model s) : s.«$fault» = none := (invariant s h).1",
           "theorem source_invariant : ∀ s, Reachable sourceModel s → sourceSafe s := by simpa only [source_model_eq, safe_agreement] using invariant",
           "theorem always_safe (states : Nat → State) (selections : Nat → Action)", "    (start : states 0 = model.initial)", "    (round : ∀ n, states (n+1) = model.step (states n) (selections n)) :", "    ∀ n, safe (states n) := invariant_always model safe invariant states selections start round",
           "theorem veil_invariant : ∀ s, model.toModule.toVeil.reachable () s → safe s := by", "  intro s h", "  exact invariant s ((reachable_iff model s).mpr ((Reactive.veil_reachable model.toModule s).mp h))",
           "#print axioms invariant", "#print axioms no_fault", "#print axioms source_invariant", "#print axioms always_safe", "#print axioms veil_invariant"]
    return "\n".join(lines)+"\n"


def contract_proof(model,names,index,have_invariant):
    c=model["contracts"][index]
    m=model["methods"][c["method"]]
    binders,args=arguments(m["inputs"]),lean.actuals(m["inputs"])
    lines=["import " + ("Invariants" if have_invariant else "Translation"), "set_option veil.smt.trust false",
           "open RMVerify RMVerify.TypedSource Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
           f"theorem contract (s : State) {binders} (reachable : Reachable model s)",
           f"    (pre : pre{index} s {args}) : post{index} s {args} := by"]
    if have_invariant: lines += ["  have hs := invariant s reachable", "  clear reachable"]
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
            witnesses['no-fault'] = dict(kind='reachable_fault', calls=calls, fault=error.reason, state=error.fields)
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
                domains = [probes(k)[:3] if k != 'int' else [-1,0,1] for k in m['inputs']]
                for args in product(*domains):
                    trace = calls + [dict(method=m['name'], arguments=dict(zip(m['parameters'], args)))]
                    try:
                        output = execute(model['programs'][m['index']], state + list(args))
                        result = output[:-1]
                    except ExecutionFault as error:
                        fault(error, trace)
                        continue
                    for ci,c in enumerate(model['contracts']):
                        if model['methods'][c['method']] is not m or c['identifier'] not in unresolved or c['identifier'] in witnesses:continue
                        try:pre = c['requires'] is None or execute(model['programs'][c['requires']],state+list(args))[0]
                        except ExecutionFault:pre=False
                        if not pre:continue
                        values=state+result+([] if m['result']=='none' else [output[-1]])+list(args)
                        try:post=execute(model['programs'][c['ensures']],values)[0]
                        except ExecutionFault:post=False
                        if not post:witnesses[c['identifier']]=dict(kind='reachable_contract',contract=ci,calls=calls,arguments=dict(zip(m['parameters'],args)))
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
        args = ' '.join(value(call['arguments'][p],k) for p,k in zip(m['parameters'],m['inputs']))
        lines += [f'def state{n+1} : State := model.step state{n} (.m{j} {args})',
                  f'theorem reach{n+1} : Reachable model state{n+1} := .step reach{n}']
    n = len(witness['calls'])
    if witness['kind'] == 'reachable_contract':
        j=witness['contract']; c=model['contracts'][j]; m=model['methods'][c['method']]
        args=' '.join(value(witness['arguments'][p],k) for p,k in zip(m['parameters'],m['inputs']))
        proof=tactic(names+[f'state{i}' for i in range(n+1)]+['dictGet','dictSet','setAdd','setDiscard','allM','anyM','eachM'])
        binders,variables=arguments(m['inputs']),lean.actuals(m['inputs'])
        lines += [f'theorem preWitness : pre{j} state{n} {args} := by',indent(proof,'  '),
                  f'theorem bad : ¬ post{j} state{n} {args} := by',indent(proof,'  '),
                  f'theorem refutation : ¬ (∀ (s : State) {binders}, Reachable model s → pre{j} s {variables} → post{j} s {variables}) := by',
                  f'  intro h; exact bad (h state{n} {args} reach{n} preWitness)',
                  f'theorem source_refutation : ¬ (∀ (s : State) {binders}, Reachable sourceModel s → sourcePre{j} s {variables} → sourcePost{j} s {variables}) := by',
                  f'  simpa only [source_model_eq, pre_agreement{j}, post_agreement{j}] using refutation',
                  '#print axioms refutation','#print axioms source_refutation']
        return '\n'.join(lines)+'\n'
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


def set_loops(p):
    result=[]
    def visit(e):
        if not isinstance(e,tuple):return
        if e and e[0]=="each" and e[1].startswith("set["):result.append(e)
        for x in e:visit(x)
    visit(p.body)
    return result


def loop_certificates(p,i,names):
    lines=[]
    for j,(_,ct,container,slot,body,dead) in enumerate(set_loops(p)):
        clear="fun f => {f with "+", ".join(f"v{n} := {default(k)}" for n,k in dead)+"}"
        stmt=f"(.scope ({clear}) (.seq (.assign (fun f v => {{f with v{slot} := v}}) (.value q{slot})) {source_statement(body,p.result)}))"
        lines += [f"def loopBody{i}_{j} (q{slot} : {kind(parts(ct)[0])}) (f : Frame{i}) : Outcome Frame{i} {kind(p.result)} := ({stmt} : TypedSource.Stmt Frame{i} {kind(p.result)}).exec f",
                  f"theorem set_loop_commutes{i}_{j} (a b : {kind(parts(ct)[0])}) (f : Frame{i}) :",
                  f"    (loopBody{i}_{j} a f).bind (loopBody{i}_{j} b) = (loopBody{i}_{j} b f).bind (loopBody{i}_{j} a) := by",
                  indent(tactic(names+[f"loopBody{i}_{j}"]),"  "), f"#print axioms set_loop_commutes{i}_{j}",
                  f"theorem set_loop_order{i}_{j} (xs ys : List ({kind(parts(ct)[0])})) (perm : xs.Perm ys) (f : Frame{i}) :",
                  f"    eachM loopBody{i}_{j} xs f = eachM loopBody{i}_{j} ys f := eachM_perm _ set_loop_commutes{i}_{j} perm f",
                  f"#print axioms set_loop_order{i}_{j}"]
    return lines


def no_fault_proof(model,names):
    lines=['import Translation','set_option veil.smt.trust false','open RMVerify RMVerify.TypedSource Verified','set_option linter.all false','set_option maxHeartbeats 2000000',
           'theorem no_fault : ∀ s, Reachable model s → s.«$fault» = none := by',
           '  apply invariant_of_induction','  ·',indent(tactic(names),'    '),
           '  · intro s selected hfault','    cases selected with']
    for j,m in enumerate(model['methods']):
        lines += [f"    | m{j} {lean.actuals(m['inputs'])} =>"]
        lines += [indent(line,'      ') for line in branch_hint(model,m)]
        lines += ['      all_goals',indent(tactic(names),'        ')]
    lines += ['theorem source_no_fault : ∀ s, Reachable sourceModel s → s.«$fault» = none := by simpa only [source_model_eq] using no_fault','#print axioms no_fault','#print axioms source_no_fault']
    return '\n'.join(lines)+'\n'
