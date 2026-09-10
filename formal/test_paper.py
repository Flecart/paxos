"""Paper relation checks and unbounded Lean proofs.

Run: formal/.venv/bin/python formal/test_paper.py -v
"""
from itertools import product
from pathlib import Path
import tempfile
import unittest

from examples.paper import EXAMPLES, control_locations, mutual_exclusion, priority
from rmverify import verify
from rmverify.checking import make_state, prepare_model, python_program
from rmverify.compiler import run_graph


def allowed_rounds(name, state, inputs):
    """Independent set-valued relations, rather than the implementation's branches.

    Selector inputs are quantified by the caller; this function has no knowledge
    of their encoding. It specifies every permitted update of the round.
    """
    if name == "not_gate":
        return {(not inputs[0],)}
    if name == "and_gate":
        return {(all(inputs),)}
    if name == "latch":
        set_, reset = inputs
        next_states = ({True} if set_ else set()) | ({False} if reset else set())
        return {(state[1], v) for v in (next_states or {state[1]})}
    pc1, pc2, x1, x2 = state
    first, second = {(pc1, x1)}, {(pc2, x2)}  # unconditional sleep commands
    if pc1 == 0: first.add((1, x2))
    if pc1 == 1 and (pc2 == 0 or x1 != x2): first.add((2, x1))
    if pc1 == 2: first.add((0, x1))
    if pc2 == 0: second.add((1, not x1))
    if pc2 == 1 and (pc1 == 0 or x1 == x2): second.add((2, x2))
    if pc2 == 2: second.add((0, x2))
    return {(a, b, x, y) for (a, x), (b, y) in product(first, second)}


def check_relations():
    """Exhaust all finite states/inputs, including unreachable protocol states."""
    boolean = (False, True)
    counts = {}
    for name, spec in EXAMPLES.items():
        model = prepare_model(spec)
        domains = [range(3) if kind == "int" else boolean for kind in model["fields"].values()]
        external = {"not_gate": 1, "and_gate": 2, "latch": 2, "peterson": 0}[name]
        selectors = {"not_gate": 0, "and_gate": 0, "latch": 1, "peterson": 2}[name]
        count = 0
        for state in product(*domains):
            for inputs in product(boolean, repeat=external):
                observed = set()
                for choices in product(boolean, repeat=selectors):
                    values = list(state + inputs + choices)
                    actual = python_program(model, 1, values)
                    assert actual == run_graph(model["graphs"][1], values), (name, values)
                    observed.add(tuple(actual[:-1]))
                    count += 1
                assert observed == allowed_rounds(name, state, inputs), (name, state, inputs, observed)
        counts[name] = count
        if name == "peterson":
            # Check all four paper initial flag valuations too. This is finite
            # regression evidence; the Lean initial-state theorem uses __init__.
            for x1, x2 in product(boolean, repeat=2):
                initial = make_state(model, [0, 0, x1, x2])
                assert all(p(initial) for p in (mutual_exclusion, control_locations, priority))
            initial = spec.target()
            reached = {tuple(getattr(initial, k) for k in model["fields"])}
            pending = list(reached)
            while pending:
                state = pending.pop()
                obj = make_state(model, state)
                assert all(p(obj) for p in (mutual_exclusion, control_locations, priority))
                for next_state in allowed_rounds(name, state, ()) - reached:
                    reached.add(next_state)
                    pending.append(next_state)
            counts["peterson_reachable"] = len(reached)
    return counts


class PaperTests(unittest.TestCase):
    def test_complete_round_relations(self):
        counts = check_relations()
        self.assertEqual({k: counts[k] for k in EXAMPLES},
                         {"not_gate": 4, "and_gate": 8, "latch": 32, "peterson": 144})

    def test_lean_proofs_without_traces(self):
        with tempfile.TemporaryDirectory(prefix="rmverify-paper-tests-") as directory:
            for name, spec in EXAMPLES.items():
                with self.subTest(example=name):
                    self.assertEqual(spec.checks, [])
                    report = verify(spec, directory=directory, timeout=120, depth=3)
                    self.assertTrue(report.ok, report)
                    self.assertEqual(report.checks, [])
                    evidence = Path(report.evidence)
                    self.assertIn("'Verified.source_model_eq'", (evidence / "Translation.log").read_text())
                    if spec.invariants:
                        self.assertIn("'source_invariant'", (evidence / "Invariants.log").read_text())
                    if spec.contracts:
                        self.assertIn("'source_contract'", (evidence / "Contract0.log").read_text())


if __name__ == "__main__":
    unittest.main()
