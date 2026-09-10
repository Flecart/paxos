"""Lean evidence generation. Successful statuses require audited kernel proofs."""
from pathlib import Path
import os
import re
import shutil
import signal
import subprocess
from textwrap import indent

from .compiler import substitute

SEMANTICS = Path(__file__).with_name("lean") / "Semantics.lean"
UNFOLD = "RMVerify.environment, RMVerify.update, RMVerify.Expr.eval, RMVerify.Op.eval, RMVerify.Stmt.exec, List.range_succ"


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
    shutil.copyfile(SEMANTICS, directory / "Semantics.lean")
    (directory / "lean-toolchain").write_text(Path(__file__).with_name("lean").joinpath("lean-toolchain").read_text())
    (directory / "lakefile.toml").write_text('name = "rmverifyEvidence"\ndefaultTargets = ["Semantics"]\n[[lean_lib]]\nname = "Semantics"\n')


def command(directory, arguments, log, timeout):
    with log.open("w") as stream:
        process = subprocess.Popen(arguments, cwd=directory, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            return None
    return process.returncode


def build(directory, timeout):
    code = command(directory, ["lake", "build", "Semantics"], directory / "build.log", timeout)
    if code is None: raise subprocess.TimeoutExpired("Lean semantics build", timeout)
    if code: raise RuntimeError("Lean semantics build failed; see build.log")


def run(directory, name, source, audits, timeout, *, output=False):
    (directory / f"{name}.lean").write_text(source)
    arguments = ["lake", "env", "lean", "-j1", f"{name}.lean"]
    if output:
        arguments += ["-o", str(directory / ".lake/build/lib/lean" / f"{name}.olean")]
    log = directory / f"{name}.log"
    code = command(directory, arguments, log, timeout)
    if code is None: return "unknown", f"{name}: Lean timed out"
    text = log.read_text()
    if code:
        status = "unknown" if re.search(r"unsolved goals|could not prove|tactic.*failed|`grind` failed|maximum|heartbeat", text) else "error"
        return status, f"{name}: Lean did not accept the obligation; see {log}"
    for theorem in audits:
        if f"'{theorem}' does not depend on any axioms" in text: continue
        match = re.search(rf"'{re.escape(theorem)}' depends on axioms:\s*\[([^\]]*)\]", text, re.S)
        if match is None or not {n.strip() for n in match[1].split(",") if n.strip()} <= {"propext", "Classical.choice", "Quot.sound"}:
            return "error", f"{name}: missing or unapproved axiom audit for {theorem}"
    return "proved", ""


def graph_definitions(graph, i):
    # Normalize the wire environment once, with a kernel-checked rfl lemma.
    # ponytail: expansion can grow with DAG sharing; use staged evaluation if
    # larger graphs exhaust compilation/proof resources.
    wires = [("var", j) for j in range(len(graph["inputs"]))]
    for term in graph["terms"]: wires.append(substitute(term, wires))
    outputs = lean_list(f"({expr(wires[j])} : Expr).eval env" for j in graph["outputs"])
    return [f"def graph{i} : Graph := ⟨{len(graph['inputs'])}, {lean_list(map(expr, graph['terms']))}, {lean_list(map(str, graph['outputs']))}⟩",
            f"theorem graph_eval{i} (env : Env) : graph{i}.run env = {outputs} := by rfl"]


def program_definitions(model):
    lines = ["import Semantics", "open RMVerify", "namespace Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000"]
    names = []
    for i,(program, graph) in enumerate(zip(model["programs"], model["graphs"])):
        lines += [f"def source{i} : Stmt := {statement(program.body)}", *graph_definitions(graph, i)]
        names += [f"source{i}", f"graph_eval{i}"]
        typed = " ∧ ".join([f"(env {j} = 0 ∨ env {j} = 1)" for j,k in enumerate(program.inputs) if k == "bool"] + ["True"])
        lines += [f"theorem translation{i} (env : Env) (typed : {typed}) :",
                  f"    (source{i}.exec env).outputs {program.fields} = graph{i}.run env := by",
                  # Eliminate statement continuations before simplifying values;
                  # otherwise simp repeatedly evaluates the unbound suffix body.
                  f"    simp only [source{i}, Stmt.exec, Outcome.bind_next, Outcome.bind_returned, Outcome.bind_ite, Outcome.outputs_ite, Outcome.outputs_next, Outcome.outputs_returned]",
                  "    all_goals", indent(tactic([f"graph_eval{i}"]), "      "), f"#print axioms translation{i}"]
    return lines, names


def definitions(model):
    lines, names = program_definitions(model)
    lines += ["structure State where"]
    for i,k in enumerate(model["fields"].values()): lines.append(f"  f{i} : {kind(k)}")
    lines += ["  deriving Repr, DecidableEq", "def encodeState (s : State) : List Int := " + lean_list(encode(k, f"s.f{i}") for i,k in enumerate(model["fields"].values())),
              "def decodeState (values : List Int) : State := ⟨" + ", ".join(decode(k, f"environment values {i}") for i,k in enumerate(model["fields"].values())) + "⟩"]
    names += ["encodeState", "decodeState"]
    lines += ["inductive Action where"]
    for j,m in enumerate(model["methods"]): lines.append(f"  | m{j} {arguments(m['inputs'])}")
    lines.append("  deriving Repr, DecidableEq")
    for j,m in enumerate(model["methods"]):
        lines += [f"def output{j} (s : State) {arguments(m['inputs'])} : List Int := graph{m['index']}.run (environment (encodeState s ++ {inputs(m['inputs'])}))",
                  f"def step{j} (s : State) {arguments(m['inputs'])} : State := decodeState (output{j} s {actuals(m['inputs'])})",
                  f"def result{j} (s : State) {arguments(m['inputs'])} : {kind(m['result'])} := " + decode(m['result'], f"environment (output{j} s {actuals(m['inputs'])}) {len(model['fields'])}")]
        names += [f"output{j}", f"step{j}", f"result{j}"]
    lines += ["def model : Model State Action where", "  initial := decodeState (graph0.run (environment []))", "  step s action := match action with"]
    for j,m in enumerate(model["methods"]): lines.append(f"    | .m{j} {actuals(m['inputs'])} => step{j} s {actuals(m['inputs'])}")
    names.append("model")
    for i,p in enumerate(model["invariants"]):
        lines.append(f"def inv{i} (s : State) : Prop := environment (graph{p['index']}.run (environment (encodeState s))) 0 ≠ 0")
        names.append(f"inv{i}")
    lines += ["def safe (s : State) : Prop := " + " ∧ ".join([f"inv{i} s" for i in range(len(model['invariants']))] + ["True"])]
    names.append("safe")
    for j,c in enumerate(model["contracts"]):
        m = model["methods"][c["method"]]
        args = actuals(m["inputs"])
        before = f"encodeState s ++ {inputs(m['inputs'])}"
        req = "True" if c["requires"] is None else f"environment (graph{c['requires']}.run (environment ({before}))) 0 ≠ 0"
        after = f"encodeState s ++ encodeState (step{c['method']} s {args})"
        if m["result"] != "none": after += f" ++ [{encode(m['result'], f'(result{c["method"]} s {args})')}]"
        after += f" ++ {inputs(m['inputs'])}"
        post = f"environment (graph{c['ensures']}.run (environment ({after}))) 0 ≠ 0"
        lines += [f"def pre{j} (s : State) {arguments(m['inputs'])} : Prop := {req}",
                  f"def post{j} (s : State) {arguments(m['inputs'])} : Prop := {post}"]
        names += [f"pre{j}", f"post{j}"]
    lines.extend(source_bridges(model))
    lines.append("end Verified")
    return "\n".join(lines) + "\n", names


def invariant_proof(model, names):
    lines = ["import Translation", "open RMVerify Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
             "theorem invariant : ∀ s, Reachable model s → safe s := by",
             "  apply invariant_of_induction", "  ·\n" + indent(tactic(names), "    "),
             "  · intro s action hs", "    cases s", "    cases action", "    all_goals", indent(tactic(names), "      "),
             "theorem always_safe (states : Nat → State) (actions : Nat → Action)",
             "    (start : states 0 = model.initial)",
             "    (round : ∀ n, states (n+1) = model.step (states n) (actions n)) :",
             "    ∀ n, safe (states n) := invariant_always model safe invariant states actions start round",
             "theorem source_invariant : ∀ s, Reachable sourceModel s → sourceSafe s := by",
             "  simpa only [source_model_eq, sourceSafe, safe, " + ", ".join(f"inv_agreement{i}" for i in range(len(model["invariants"]))) + "] using invariant" if model["invariants"] else "  simpa only [source_model_eq, sourceSafe, safe] using invariant",
             "#print axioms invariant", "#print axioms always_safe", "#print axioms source_invariant"]
    return "\n".join(lines) + "\n"


def contract_proof(model, names, index, have_invariant):
    c = model["contracts"][index]
    m = model["methods"][c["method"]]
    lines = ["import " + ("Invariants" if have_invariant else "Translation"), "open RMVerify Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
             f"theorem contract (s : State) {arguments(m['inputs'])} (reachable : Reachable model s)",
             f"    (pre : pre{index} s {actuals(m['inputs'])}) : post{index} s {actuals(m['inputs'])} := by"]
    if have_invariant: lines.append("  have hs := invariant s reachable")
    lines += ["  cases s", indent(tactic(names), "  "), "#print axioms contract"]
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
    lines = ["import Translation", "open RMVerify Verified", "set_option linter.all false", "set_option maxRecDepth 100000", "set_option maxHeartbeats 1000000",
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
