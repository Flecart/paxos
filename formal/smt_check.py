"""SMT obligations over actual exported RM terms, not a second algorithm model.

These are solver results, NOT Lean proofs. The report labels that boundary.
"""
import json
from pathlib import Path
import z3

ROOT = Path(__file__).resolve().parent


def symbolic_step(artifact):
    names = artifact["state"] + artifact["inputs"]
    wires = [z3.Int(name) for name in names]
    initial = dict(zip(names, wires))
    for term in artifact["step"]["terms"]:
        a = [wires[i] for i in term["args"]]
        op = term["op"].removeprefix("LIA_")
        if op == "Int": result = z3.IntVal(term["value"])
        elif op == "Bool": result = z3.BoolVal(bool(term["value"]))
        elif op == "Id": result = a[0]
        elif op == "Add": result = a[0] + a[1]
        elif op == "Sub": result = a[0] - a[1]
        elif op == "Max": result = z3.If(a[0] >= a[1], a[0], a[1])
        elif op == "Min": result = z3.If(a[0] <= a[1], a[0], a[1])
        elif op == "Eq": result = a[0] == a[1]
        elif op == "Ne": result = a[0] != a[1]
        elif op == "Lt": result = a[0] < a[1]
        elif op == "Le": result = a[0] <= a[1]
        elif op == "Gt": result = a[0] > a[1]
        elif op == "Ge": result = a[0] >= a[1]
        elif op == "And": result = z3.And(*a)
        elif op == "Or": result = z3.Or(*a)
        elif op == "Not": result = z3.Not(a[0])
        elif op == "Ite": result = z3.If(*a)
        else: raise ValueError(op)
        wires.append(z3.simplify(result))
    after = {name: wires[i] for name, i in zip(artifact["state"], artifact["step"]["outputs"])}
    return initial, after


def main():
    artifact = json.loads((ROOT / "generated" / "rm.json").read_text())
    before, after = symbolic_step(artifact)
    obligations = {
        "non_none_acceptance_is_immutable": z3.Implies(before["accepted"] != 0, after["accepted"] == before["accepted"]),
        "acceptance_reply_matches_recorded_value": z3.Implies(after["out_kind"] == 13, after["accepted"] == after["out_value"]),
    }
    results = {}
    for name, proposition in obligations.items():
        solver = z3.Solver()
        solver.set(timeout=30000)
        solver.add(z3.Not(proposition))
        status = str(solver.check())
        results[name] = {"negation": status, "evidence": "Z3 only; not a Lean theorem"}
        if status == "sat":
            results[name]["counterexample"] = str(solver.model())
        print(name, status)
    (ROOT / "generated" / "smt_results.json").write_text(json.dumps(results, indent=2) + "\n")
    if any(result["negation"] != "unsat" for result in results.values()):
        raise SystemExit("An RM invariant is false or unresolved; inspect smt_results.json")


if __name__ == "__main__":
    main()
