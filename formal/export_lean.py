"""Generate Lean only from the exported RM graph and recorded schedules."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "lean" / "PaxosFormal"


def array(items):
    return "#[" + ", ".join(map(str, items)) + "]"


def export():
    raw = (ROOT / "generated" / "rm.json").read_bytes()
    artifact = json.loads(raw)
    manifest = json.loads((ROOT / "generated" / "manifest.json").read_text())
    if artifact["source_sha256"] != hashlib.sha256((ROOT.parent / "paxos_lab" / "algorithm.py").read_bytes()).hexdigest():
        raise SystemExit("Original algorithm changed; review and regenerate the translation")
    if artifact["python_sha256"] != hashlib.sha256((ROOT / "generated" / "node.py").read_bytes()).hexdigest():
        raise SystemExit("RM artifact is stale; recompile before exporting Lean")
    rows = ["import PaxosFormal.Semantics", "namespace PaxosFormal", "set_option maxRecDepth 100000",
            f'def rmHash : String := "{hashlib.sha256(raw).hexdigest()}"',
            f"def stateSize : Nat := {len(artifact['state'])}",
            f"def queueCapacity : Nat := {manifest['queue_capacity']}"]
    aliases = {"status": "status", "pc": "pc", "declared": "declared", "declared_num": "declaredNum",
               "declared_value": "declaredValue", "out_kind": "outKind", "out_target": "outTarget",
               "out_num": "outNum", "out_value": "outValue", "out_prior_n": "outPriorN", "out_prior_v": "outPriorV"}
    for name, alias in aliases.items():
        rows.append(f"def {alias}Index : Nat := {artifact['state'].index(name)}")
    for phase in ("init", "step"):
        terms = artifact[phase]["terms"]
        chunks = []
        for i in range(0, len(terms), 128):
            name = f"{phase}Chunk{i // 128}"
            chunks.append(name)
            entries = []
            for term in terms[i:i+128]:
                name_op = term["op"].removeprefix("LIA_")
                op = f".const ({term['value']})" if name_op in ("Int", "Bool") else "." + name_op.lower()
                entries.append(f"⟨{op}, {array(term['args'])}⟩")
            rows.append(f"def {name} : Array Instr := " + array(entries))
        rows.append(f"def {phase}Program : Array Instr := " + " ++ ".join(chunks))
        rows.append(f"def {phase}Outputs : Array Nat := " + array(artifact[phase]["outputs"]))
    rows += ["def nodeInitial : Array Int := runBlock initProgram initOutputs (Array.replicate stateSize 0) (Array.replicate 6 0)",
             "def nodeStep (s inputs : Array Int) : Array Int := runBlock stepProgram stepOutputs s inputs",
             "/-- The generated transition is the actual exported RM wire interpreter. -/",
             "theorem nodeStep_is_exported_RM (s inputs : Array Int) :",
             "  nodeStep s inputs = runBlock stepProgram stepOutputs s inputs := rfl",
             "end PaxosFormal"]
    (OUT / "Generated.lean").write_text("\n".join(rows) + "\n")
    witnesses = ["import PaxosFormal.Network", "namespace PaxosFormal", "set_option maxRecDepth 100000", "set_option maxHeartbeats 0"]
    for name in ("single", "later", "integer", "concurrent", "ticks", "key_error", "interleaved"):
        path = ROOT / "generated" / f"trace_{name}.json"
        if not path.exists():
            continue
        trace = json.loads(path.read_text())
        if trace.get("rm_sha256") != hashlib.sha256(raw).hexdigest():
            raise SystemExit(f"{path.name} is stale; run check.py before exporting Lean")
        actions = ["." + kind + " " + " ".join(map(str, args)) for kind, *args in trace["actions"]]
        witnesses.append(f"def {name}Actions : List Action := [" + ", ".join(actions) + "]")
        witnesses.append(f"def {name}Result := runActions {name}Actions")
        # Explicitly finite-trace evidence, not a claim about all schedules.
        prop = trace["properties"]
        checks = [f"!{name}Result.outside", f"!{name}Result.invalid"]
        for py, lean in (("agreement", "agreement"), ("validity", "validity"),
                         ("decision_accuracy", "decisionAccuracy"), ("decision_consistency", "decisionConsistency"),
                         ("choice_reached", "hasChoice"), ("all_nodes_declared", "allRecognize")):
            check = f"{lean} {name}Result"
            checks.append(f"({check})" if prop[py] else f"(!({check}))")
        if name == "key_error":
            checks.append(f"({name}Result.nodes[1]![statusIndex]! == 1)")
        witnesses.append(f"theorem {name}_checked : (" + " && ".join(checks) + ") = true := by\n  native_decide")
    witnesses += ["end PaxosFormal"]
    (OUT / "Witnesses.lean").write_text("\n".join(witnesses) + "\n")
    (ROOT / "lean" / "PaxosFormal.lean").write_text("import PaxosFormal.Witnesses\nimport PaxosFormal.CSLib\n")
    print(f"Generated Lean from RM sha256={hashlib.sha256(raw).hexdigest()}")


if __name__ == "__main__":
    export()
