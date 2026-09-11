"""Lean evidence generation. Successful statuses require audited kernel proofs."""
from pathlib import Path
import os
import json
import hashlib
import time
import re
import shutil
import signal
import subprocess
from textwrap import indent


from .recheck import audit, lean_environment

SEMANTICS = Path(__file__).with_name("lean") / "Semantics.lean"
UNFOLD = "RMVerify.environment, RMVerify.update, RMVerify.Expr.eval, RMVerify.Op.eval, RMVerify.Stmt.exec, List.range_succ, Bool.eq_not, Bool.not_eq, Id.run, Bind.bind, Pure.pure"


def lean_list(values): return "[" + ", ".join(values) + "]"


def expr(e):
    match e:
        case ("lit" | "bool", n): return f"(.lit ({int(n)}))"
        case ("var", n): return f"(.var {n})"
        case ("bin", op, a, b): return f"(.bin .{op} {expr(a)} {expr(b)})"
        case ("ite", c, a, b): return f"(.ite {expr(c)} {expr(a)} {expr(b)})"
    raise ValueError("invalid expression")


def statement(s):
    match s:
        case ("skip",): return ".skip"
        case ("assign", n, e): return f"(.assign {n} {expr(e)})"
        case ("seq", a, b): return f"(.seq {statement(a)} {statement(b)})"
        case ("branch", c, a, b): return f"(.branch {expr(c)} {statement(a)} {statement(b)})"
        case ("ret", e): return f"(.ret {expr(e)})"
    raise ValueError("invalid statement")


def kind(k): return {"int":"Int", "bool":"Bool", "none":"Unit"}[k]


def encode(k, value): return f"flag {value}" if k == "bool" else "0" if k == "none" else value


def decode(k, value): return f"({value} != 0)" if k == "bool" else "()" if k == "none" else value


def arguments(kinds): return " ".join(f"(a{i} : {kind(k)})" for i, k in enumerate(kinds))


def actuals(kinds): return " ".join(f"a{i}" for i in range(len(kinds)))


def inputs(kinds): return lean_list(encode(k, f"a{i}") for i,k in enumerate(kinds))


def tactic(names, *, contextual=True):
    # No program-dependent proof scripts: reduction, cases, arithmetic, and logic.
    # A useful split must survive when simp makes no further change. Otherwise
    # repeat' rolls back that split and leaves conditional goals for omega.
    simplify = "simp_all (config := {failIfUnchanged := false})"
    initial = simplify if contextual else "simp (config := {failIfUnchanged := false})"
    location = "" if contextual else " at *"
    return (f"{initial} [{', '.join(names)}, {UNFOLD}]{location}\n"
            f"all_goals (repeat' (first | omega | split <;> {simplify} [{UNFOLD}]))\n"
            "all_goals first | omega | grind [RMVerify.flag]")


def prepare(directory):
    library = SEMANTICS.parent
    for name in ("Semantics.lean", "VeilAdapter.lean", "lean-toolchain", "lakefile.toml", "lake-manifest.json"):
        shutil.copyfile(library/name, directory/name)
    shutil.copyfile(Path(__file__).with_name("recheck.py"), directory/"recheck.py")
    # Reuse installed dependencies locally. The manifest still supports fresh
    # Lake builds after removing .lake when moving the evidence elsewhere.
    packages = library/".lake/packages"
    if packages.is_dir():
        (directory/".lake").mkdir(exist_ok=True)
        (directory/".lake/packages").symlink_to(packages, target_is_directory=True)


def seal(directory, sources, timeout):
    snapshot = directory/"sources"
    snapshot.mkdir(exist_ok=True)
    for path, digest in sources.items():
        content = Path(path).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise RuntimeError("source changed before evidence snapshot; evidence is stale")
        (snapshot/f"{digest}.py").write_bytes(content)
    manifest_path = directory/"recheck.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"obligations": []}
    manifest["version"] = 3
    manifest["timeout"] = timeout
    manifest["files"] = {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [*directory.glob("*.lean"), *directory.glob("*.json"),
                                   *directory.glob("*.toml"), directory/"lean-toolchain", directory/"recheck.py",
                                   *snapshot.glob("*.py")]
                         if p != manifest_path}
    manifest_path.write_text(json.dumps(manifest, indent=2)+"\n")


def command(directory, arguments, log, timeout):
    started = time.monotonic()
    with log.open("w") as stream:
        process = subprocess.Popen(arguments, cwd=directory,
            env=lean_environment(directory) if arguments[0] == "lean" else None,
            stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            return None
    metrics = directory/"timings.json"
    times = json.loads(metrics.read_text()) if metrics.exists() else {}
    times[log.stem] = time.monotonic() - started
    metrics.write_text(json.dumps(times, indent=2)+"\n")
    return process.returncode


def build(directory, timeout):
    if not (directory/".lake/packages/veil/.lake/build/lib/lean/Veil/Base.olean").exists():
        code = command(directory, ["lake", "--no-cache", "build"], directory/"build.log", timeout)
        if code is None: raise subprocess.TimeoutExpired("Lean dependency build", timeout)
        if code: raise RuntimeError("Lean dependency build failed; see build.log")
    (directory/".lake/build/lib/lean").mkdir(parents=True, exist_ok=True)
    for name, audits in (("Semantics", []), ("VeilAdapter", ["RMVerify.Reactive.veil_initial",
                          "RMVerify.Reactive.veil_round", "RMVerify.Reactive.veil_reachable"])):
        status, reason = run(directory, name, (directory/f"{name}.lean").read_text(), audits, timeout, output=True)
        if status == "unknown": raise subprocess.TimeoutExpired(reason, timeout)
        if status != "proved": raise RuntimeError(reason)


def run(directory, name, source, audits, timeout, *, output=False):
    (directory / f"{name}.lean").write_text(source)
    arguments = ["lean", "-j1", f"{name}.lean"]
    if output:
        arguments += ["-o", str(directory / ".lake/build/lib/lean" / f"{name}.olean")]
    log = directory / f"{name}.log"
    code = command(directory, arguments, log, timeout)
    if code is None: return "unknown", f"{name}: Lean timed out"
    text = log.read_text()
    if code:
        status = "unknown" if re.search(r"unsolved goals|could not prove|tactic.*failed|`grind` failed|maximum|heartbeat", text) else "error"
        return status, f"{name}: Lean did not accept the obligation; see {log}"
    try:
        audit(text, audits)
    except ValueError as error:
        return "error", f"{name}: {error}"
    manifest_path = directory/"recheck.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {"obligations": []}
    manifest["obligations"].append(dict(name=name, audits=audits, output=output))
    manifest_path.write_text(json.dumps(manifest, indent=2)+"\n")
    return "proved", ""


def native_expression(e, slots):
    match e:
        case ("lit", n): return f"({n} : Int)"
        case ("bool", b): return str(b).lower()
        case ("var", n): return f"v{n}"
        case ("ite", c, a, b):
            return f"(if {native_expression(c, slots)} then {native_expression(a, slots)} else {native_expression(b, slots)})"
        case ("bin", op, a, b):
            a, b = native_expression(a, slots), native_expression(b, slots)
            symbol = {"add":"+", "sub":"-", "mul":"*", "eq":"==", "ne":"!=",
                      "lt":"<", "le":"≤", "gt":">", "ge":"≥", "and":"&&", "or":"||"}[op]
            result = f"({a} {symbol} {b})"
            return f"(decide {result})" if op in ("lt", "le", "gt", "ge") else result
    raise ValueError("invalid source expression")


def compiled_definition(program, i):
    """Emit typed Lean lets/conditionals; no SSA terms or RM wire language."""
    name = f"«{program.function.__qualname__}_{i}»"
    output = f"«{program.function.__qualname__}_{i}.Output»"
    fields = program.slot_names[:program.fields]
    lines = [f"structure {output} where"]
    lines += [f"  «{n}» : {kind(k)}" for n,k in zip(fields, program.slots)]
    lines += [f"  «$return» : {kind(program.result)}", "  deriving Repr, DecidableEq"]
    def finish(value):
        return "⟨" + ", ".join([f"v{n}" for n in range(program.fields)] + [value]) + "⟩"
    def go(stmt):
        match stmt:
            case ("skip",): return []
            case ("assign", n, e): return [f"v{n} := {native_expression(e, program.slots)}"]
            case ("seq", a, b): return go(a) + go(b)
            case ("branch", c, a, b):
                yes, no = "\n".join(go(a)) or "pure ()", "\n".join(go(b)) or "pure ()"
                return [f"if {native_expression(c, program.slots)} then\n" + indent(yes, "  ") + "\nelse\n" + indent(no, "  ")]
            case ("ret", e): return ["return " + finish("()" if program.result == "none" else native_expression(e, program.slots))]
        raise ValueError("invalid source statement")
    binders = " ".join(f"(v{n} : {kind(k)})" for n,k in enumerate(program.inputs))
    defaults = {"int": "0", "bool": "false", "none": "()"}
    body = [f"let mut v{n} : {kind(k)} := " + (f"v{n}" if n < len(program.inputs) else defaults[k])
            for n,k in enumerate(program.slots)]
    body += go(program.body)
    if program.result == "none":
        body.append("return " + finish("()"))
    lines += [f"def {name} {binders} : {output} := Id.run do", indent("\n".join(body), "  ")]
    args = " ".join(decode(k, f"(env {n})") for n,k in enumerate(program.inputs))
    outputs = [encode(k, f"o.«{n}»") for n,k in zip(fields, program.slots)]
    outputs += [encode(program.result, "o.«$return»")]
    lines += [f"def compiled{i} (env : Env) : List Int :=", f"  let o := {name} {args}", "  " + lean_list(outputs)]
    return lines, [f"compiled{i}", name]


def program_definitions(model):
    lines = ["import VeilAdapter", "set_option veil.smt.trust false", "open RMVerify", "namespace Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000"]
    names = []
    for i,program in enumerate(model["programs"]):
        compiled, reductions = compiled_definition(program, i)
        lines += [f"def source{i} : Stmt := {statement(program.body)}", *compiled]
        names += [f"source{i}", *reductions]
        typed = " ∧ ".join([f"(env {j} = 0 ∨ env {j} = 1)" for j,k in enumerate(program.inputs) if k == "bool"] + ["True"])
        boolean_slots = [j for j,k in enumerate(program.inputs) if k == "bool"]
        hypotheses = [f"b{j}" for j in boolean_slots]
        lines += [f"theorem translation{i} (env : Env) (typed : {typed}) :",
                  f"    (source{i}.exec env).outputs {program.fields} = compiled{i} env := by"]
        if hypotheses:
            lines += ["  rcases typed with ⟨" + ", ".join(hypotheses + ["_"]) + "⟩",
                      "  " + " <;> ".join(f"rcases {h} with {h} | {h}" for h in hypotheses)]
        lines += ["  all_goals",
                  f"    simp only [{', '.join(hypotheses + [f'source{i}', 'Stmt.exec', 'Outcome.bind_next', 'Outcome.bind_returned', 'Outcome.bind_ite', 'Outcome.outputs_ite', 'Outcome.outputs_next', 'Outcome.outputs_returned'])}]",
                  "  all_goals", indent(tactic(reductions), "    "), f"#print axioms translation{i}"]
    return lines, names


def definitions(model):
    lines, names = program_definitions(model)
    lines += ["structure State where"]
    for i,k in enumerate(model["fields"].values()): lines.append(f"  «{list(model['fields'])[i]}» : {kind(k)}")
    lines += ["  deriving Repr, DecidableEq", "def encodeState (s : State) : List Int := " + lean_list(encode(k, f"s.«{list(model['fields'])[i]}»") for i,k in enumerate(model["fields"].values())),
              "def decodeState (values : List Int) : State := ⟨" + ", ".join(decode(k, f"environment values {i}") for i,k in enumerate(model["fields"].values())) + "⟩"]
    names += ["encodeState", "decodeState"]
    lines += ["inductive Action where"]
    for j,m in enumerate(model["methods"]): lines.append(f"  | m{j} {arguments(m['inputs'])}")
    lines.append("  deriving Repr, DecidableEq")
    for j,m in enumerate(model["methods"]):
        lines += [f"def output{j} (s : State) {arguments(m['inputs'])} : List Int := compiled{m['index']} (environment (encodeState s ++ {inputs(m['inputs'])}))",
                  f"def step{j} (s : State) {arguments(m['inputs'])} : State := decodeState (output{j} s {actuals(m['inputs'])})",
                  f"def result{j} (s : State) {arguments(m['inputs'])} : {kind(m['result'])} := " + decode(m['result'], f"environment (output{j} s {actuals(m['inputs'])}) {len(model['fields'])}")]
        names += [f"output{j}", f"step{j}", f"result{j}"]
    lines += ["def model : Model State Action where", "  initial := decodeState (compiled0 (environment []))", "  step s action := match action with"]
    for j,m in enumerate(model["methods"]): lines.append(f"    | .m{j} {actuals(m['inputs'])} => step{j} s {actuals(m['inputs'])}")
    names.append("model")
    for i,p in enumerate(model["invariants"]):
        lines.append(f"def inv{i} (s : State) : Prop := environment (compiled{p['index']} (environment (encodeState s))) 0 ≠ 0")
        names.append(f"inv{i}")
    lines += ["def safe (s : State) : Prop := " + " ∧ ".join([f"inv{i} s" for i in range(len(model['invariants']))] + ["True"])]
    names.append("safe")
    for j,c in enumerate(model["contracts"]):
        m = model["methods"][c["method"]]
        args = actuals(m["inputs"])
        before = f"encodeState s ++ {inputs(m['inputs'])}"
        req = "True" if c["requires"] is None else f"environment (compiled{c['requires']} (environment ({before}))) 0 ≠ 0"
        after = f"encodeState s ++ encodeState (step{c['method']} s {args})"
        if m["result"] != "none": after += f" ++ [{encode(m['result'], f'(result{c["method"]} s {args})')}]"
        after += f" ++ {inputs(m['inputs'])}"
        post = f"environment (compiled{c['ensures']} (environment ({after}))) 0 ≠ 0"
        lines += [f"def pre{j} (s : State) {arguments(m['inputs'])} : Prop := {req}",
                  f"def post{j} (s : State) {arguments(m['inputs'])} : Prop := {post}"]
        names += [f"pre{j}", f"post{j}"]
    lines.extend(source_bridges(model))
    lines.append("end Verified")
    return "\n".join(lines) + "\n", names



def state_cases(model, variables):
    kinds = list(model["fields"].values())
    lines = [f"rcases {v} with ⟨" + ", ".join(f"{v}{i}" for i in range(len(kinds))) + "⟩" for v in variables]
    cases = [f"cases {v}{i}" for v in variables for i,k in enumerate(kinds) if k == "bool"]
    if cases:
        lines.append(" <;> ".join(cases))
    return "\n".join(lines)


def finite_state_hint(model):
    literals = set()
    def visit(node):
        if not isinstance(node, tuple): return
        if node[0] == "lit": literals.add(node[1])
        for child in node[1:]: visit(child)
    for prop in model["invariants"]:
        visit(model["programs"][prop["index"]].body)
    integers = [i for i,k in enumerate(model["fields"].values()) if k == "int"]
    if not literals or not 0 < max(literals)-min(literals) <= 3: return [], []
    domain = list(range(min(literals), max(literals)+1))
    # ponytail: enumerate at most 64 integer valuations; retain symbolic proofs
    # when the proposed partition is larger. Every proposed bound is proved.
    return (integers, domain) if len(domain)**len(integers) <= 64 else ([], [])


def invariant_proof(model, names):
    lines = ["import Translation", "set_option veil.smt.trust false", "open RMVerify Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
             "theorem invariant : ∀ s, Reachable model s → safe s := by",
             "  apply invariant_of_induction", "  ·\n" + indent(tactic(names), "    "),
             "  · intro s action hs", indent(state_cases(model, ["s"]), "    ")]
    integers, domain = finite_state_hint(model)
    for i in integers:
        lines += ["    all_goals", "      try",
                  f"        have bounded : " + " ∨ ".join(f"s{i} = ({v} : Int)" for v in domain) + " := by",
                  indent(tactic(names), "          "),
                  "        rcases bounded with " + " | ".join("rfl" for _ in domain)]
    lines += ["    all_goals", "      cases action with"]
    for j, method in enumerate(model["methods"]):
        lines.append(f"      | m{j} {actuals(method['inputs'])} =>")
        booleans = [f"cases a{i}" for i,k in enumerate(method["inputs"]) if k == "bool"]
        if booleans: lines.append("          " + " <;> ".join(booleans))
        lines += ["          all_goals",
                  "            simp_all +decide [safe" + "".join(f", inv{i}" for i in range(len(model["invariants"]))) + "]",
                  "          all_goals", indent(tactic(names), "            ")]
    lines += [
             "theorem always_safe (states : Nat → State) (actions : Nat → Action)",
             "    (start : states 0 = model.initial)",
             "    (round : ∀ n, states (n+1) = model.step (states n) (actions n)) :",
             "    ∀ n, safe (states n) := invariant_always model safe invariant states actions start round",
             "theorem source_invariant : ∀ s, Reachable sourceModel s → sourceSafe s := by",
             "  simpa only [source_model_eq, sourceSafe, safe, " + ", ".join(f"inv_agreement{i}" for i in range(len(model["invariants"]))) + "] using invariant" if model["invariants"] else "  simpa only [source_model_eq, sourceSafe, safe] using invariant",
             "theorem veil_invariant : ∀ s, model.toModule.toVeil.reachable () s → safe s := by",
             "  intro s h",
             "  exact invariant s ((reachable_iff model s).mpr ((Reactive.veil_reachable model.toModule s).mp h))",
             "#print axioms veil_invariant",
             "#print axioms invariant", "#print axioms always_safe", "#print axioms source_invariant"]
    return "\n".join(lines) + "\n"


def contract_proof(model, names, index, have_invariant):
    c = model["contracts"][index]
    m = model["methods"][c["method"]]
    lines = ["import " + ("Invariants" if have_invariant else "Translation"), "set_option veil.smt.trust false", "open RMVerify Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
             f"theorem contract (s : State) {arguments(m['inputs'])} (reachable : Reachable model s)",
             f"    (pre : pre{index} s {actuals(m['inputs'])}) : post{index} s {actuals(m['inputs'])} := by"]
    if have_invariant: lines.append("  have hs := invariant s reachable")
    lines += [indent(state_cases(model, ["s"]), "  "), "  all_goals", indent(tactic(names), "    "), "#print axioms contract"]
    cargs = actuals(m["inputs"])
    lines += [f"theorem source_contract (s : State) {arguments(m['inputs'])} (reachable : Reachable sourceModel s)",
              f"    (pre : sourcePre{index} s {cargs}) : sourcePost{index} s {cargs} := by",
              f"  apply (post_agreement{index} s {cargs}).mpr",
              f"  apply contract s {cargs}",
              "  · simpa only [source_model_eq] using reachable",
              f"  · exact (pre_agreement{index} s {cargs}).mp pre",
              "#print axioms source_contract"]
    return "\n".join(lines) + "\n"


def value(v): return str(v).lower() if type(v) is bool else f"({v})"


def witness_proof(model, witness):
    lines = ["import Translation", "set_option veil.smt.trust false", "open RMVerify Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
             "def state0 : State := model.initial", "theorem reach0 : Reachable model state0 := .initial"]
    category,index = witness["target"]
    prefix = witness["calls"] if category == "invariant" else witness["calls"][:-1]
    for n,call in enumerate(prefix):
        j = next(j for j,m in enumerate(model["methods"]) if m["name"]==call["method"])
        args = " ".join(value(call["arguments"][name]) for name in model["methods"][j]["parameters"])
        lines += [f"def state{n+1} : State := model.step state{n} (.m{j} {args})",
                  f"theorem reach{n+1} : Reachable model state{n+1} := .step reach{n}"]
    n = len(prefix)
    if category == "invariant":
        lines += [f"theorem bad : ¬ inv{index} state{n} := by unfold inv{index}; decide",
                  f"theorem refutation : ¬ (∀ s, Reachable model s → inv{index} s) := by",
                  f"  intro h; exact bad (h state{n} reach{n})"]
    else:
        c = model["contracts"][index]
        m = model["methods"][c["method"]]
        call = witness["calls"][-1]
        args = " ".join(value(call["arguments"][name]) for name in m["parameters"])
        lines += [f"theorem allowed : pre{index} state{n} {args} := by unfold pre{index}; decide",
                  f"theorem bad : ¬ post{index} state{n} {args} := by unfold post{index}; decide",
                  f"theorem refutation : ¬ (∀ (s : State) {arguments(m['inputs'])}, Reachable model s → pre{index} s {actuals(m['inputs'])} → post{index} s {actuals(m['inputs'])}) := by",
                  f"  intro h; exact bad (h state{n} {args} reach{n} allowed)"]
    if category == "invariant":
        lines += [f"theorem source_refutation : ¬ (∀ s, Reachable sourceModel s → sourceInv{index} s) := by",
                  f"  simpa only [source_model_eq, inv_agreement{index}] using refutation"]
    else:
        lines += [f"theorem source_refutation : ¬ (∀ (s : State) {arguments(m['inputs'])}, Reachable sourceModel s → sourcePre{index} s {actuals(m['inputs'])} → sourcePost{index} s {actuals(m['inputs'])}) := by",
                  f"  simpa only [source_model_eq, pre_agreement{index}, post_agreement{index}] using refutation"]
    lines += ["#print axioms refutation", "#print axioms source_refutation"]
    return "\n".join(lines)+"\n"


def source_bridges(model):
    """Connect the public claims to source execution, using checked translations."""
    lines = []
    field_count = len(model["fields"])
    typed = "by simp [environment, encodeState]"
    for j,m in enumerate(model["methods"]):
        args, binders = actuals(m["inputs"]),arguments(m["inputs"])
        p = m["index"]
        lines += [f"def sourceOutput{j} (s : State) {binders} : List Int := (source{p}.exec (environment (encodeState s ++ {inputs(m['inputs'])}))).outputs {field_count}",
                  f"theorem output_agreement{j} (s : State) {binders} : sourceOutput{j} s {args} = output{j} s {args} := by",
                  f"  exact translation{p} _ ({typed})",
                  f"def sourceStep{j} (s : State) {binders} : State := decodeState (sourceOutput{j} s {args})",
                  f"def sourceResult{j} (s : State) {binders} : {kind(m['result'])} := " + decode(m['result'],f"environment (sourceOutput{j} s {args}) {field_count}"),
                  f"theorem step_agreement{j} (s : State) {binders} : sourceStep{j} s {args} = step{j} s {args} := by simp [sourceStep{j}, step{j}, output_agreement{j}]",
                  f"theorem result_agreement{j} (s : State) {binders} : sourceResult{j} s {args} = result{j} s {args} := by simp [sourceResult{j}, result{j}, output_agreement{j}]"]
    lines += ["def sourceModel : Model State Action where",
              f"  initial := decodeState ((source0.exec (environment [])).outputs {field_count})",
              "  step s action := match action with"]
    for j,m in enumerate(model["methods"]): lines.append(f"    | .m{j} {actuals(m['inputs'])} => sourceStep{j} s {actuals(m['inputs'])}")
    rewrite = ", ".join(["sourceModel","model","translation0 _ True.intro"]+[f"step_agreement{j}" for j in range(len(model["methods"]))])
    lines += ["theorem source_model_eq : sourceModel = model := by", f"  simp only [{rewrite}]", "#print axioms source_model_eq"]
    for j,p in enumerate(model["invariants"]):
        lines += [f"def sourceInv{j} (s : State) : Prop := environment ((source{p['index']}.exec (environment (encodeState s))).outputs 0) 0 ≠ 0",
                  f"theorem inv_agreement{j} (s : State) : sourceInv{j} s ↔ inv{j} s := by",
                  f"  unfold sourceInv{j} inv{j}; rw [translation{p['index']} _ ({typed})]",
                  f"#print axioms inv_agreement{j}"]
    lines += ["def sourceSafe (s : State) : Prop := " + " ∧ ".join([f"sourceInv{j} s" for j in range(len(model["invariants"]))]+["True"])]
    for j,c in enumerate(model["contracts"]):
        method = c["method"]
        m = model["methods"][method]
        args, binders = actuals(m["inputs"]),arguments(m["inputs"])
        before = f"encodeState s ++ {inputs(m['inputs'])}"
        req = "True" if c["requires"] is None else f"environment ((source{c['requires']}.exec (environment ({before}))).outputs 0) 0 ≠ 0"
        after = f"encodeState s ++ encodeState (sourceStep{method} s {args})"
        if m["result"] != "none": after += f" ++ [{encode(m['result'],f'(sourceResult{method} s {args})')}]"
        after += f" ++ {inputs(m['inputs'])}"
        post = f"environment ((source{c['ensures']}.exec (environment ({after}))).outputs 0) 0 ≠ 0"
        lines += [f"def sourcePre{j} (s : State) {binders} : Prop := {req}",
                  f"def sourcePost{j} (s : State) {binders} : Prop := {post}",
                  f"theorem pre_agreement{j} (s : State) {binders} : sourcePre{j} s {args} ↔ pre{j} s {args} := by"]
        if c["requires"] is None: lines.append("  rfl")
        else: lines.append(f"  unfold sourcePre{j} pre{j}; rw [translation{c['requires']} _ ({typed})]")
        lines += [f"theorem post_agreement{j} (s : State) {binders} : sourcePost{j} s {args} ↔ post{j} s {args} := by",
                  f"  unfold sourcePost{j} post{j}",
                  f"  simp only [step_agreement{method}, result_agreement{method}]",
                  f"  rw [translation{c['ensures']} _ ({typed})]",
                  f"#print axioms pre_agreement{j}",f"#print axioms post_agreement{j}"]
    return lines
