"""Run: formal/.venv/bin/python formal/test_composition.py -v"""
from copy import deepcopy
from itertools import product
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from examples.peterson_v2 import P1, P2, State, paper_round, peterson
from rmverify import Await, Component, Composition, verify
from rmverify.composition import initial_states, prepare_model, successors
from rmverify.frontend import Unsupported


class Increment:
    value: int

    def __init__(self) -> None:
        self.value = 0

    def advance(self) -> None:
        self.value += 1


class Copy:
    value: int

    def __init__(self) -> None:
        self.value = 0

    def advance(self, value: int) -> None:
        self.value = value


class Pair:
    produced: int
    copied: int


def equal(state: Pair) -> bool:
    return state.produced == state.copied


def pipeline(binding):
    # Deliberately declare the consumer first. Await dependencies determine order.
    return Composition(Pair,
        [Component(Copy, [Copy.advance], {"value": "copied"}, {"value": binding}, stutter=False),
         Component(Increment, [Increment.advance], {"value": "produced"}, stutter=False)],
        invariants=[equal])


def state_object(values):
    state = State()
    for name, value in zip(State.__annotations__, values, strict=True):
        setattr(state, name, value)
    return state


class CompositionTests(unittest.TestCase):
    def test_peterson_native_rounds(self):
        model = prepare_model(peterson)
        self.assertEqual(len(model["atoms"]), 2)
        self.assertEqual([a["controls"] for a in model["atoms"]], [[0, 2], [1, 3]])
        self.assertEqual([a["awaits"] for a in model["atoms"]], [[], []])
        self.assertNotIn("run1", model["native_module"])
        self.assertEqual(initial_states(model), {(0, 0, a, b) for a,b in product((False,True), repeat=2)})
        states = list(product(range(3), range(3), (False,True), (False,True)))
        for s in states:
            p1, p2 = P1(s[2]), P2(s[3])
            p1.pc, p2.pc = s[0], s[1]
            p1.advance(s[1], s[3])
            p2.advance(s[0], s[2])  # reads the old snapshot, including old x1
            expected = {(a,b,x,y) for (a,x),(b,y) in product(
                {(s[0],s[2]), (p1.pc,p1.x)}, {(s[1],s[3]), (p2.pc,p2.x)})}
            self.assertEqual(successors(model, s), expected)
            self.assertEqual(expected, {t for t in states if paper_round(state_object(s), state_object(t))})
        self.assertIn((1,1,False,True), successors(model, (0,0,False,False)))

    def test_await_and_old_reads(self):
        awaited = prepare_model(pipeline(Await("produced")))
        self.assertEqual([a["component"] for a in awaited["atoms"]], [1,0])
        self.assertEqual(successors(awaited, (0,0)), {(1,1)})
        old = prepare_model(pipeline("produced"))
        self.assertEqual(successors(old, (0,0)), {(1,0)})

    def test_invalid_compositions_fail_closed(self):
        duplicate = deepcopy(peterson)
        duplicate.components[1].controls = {"pc": "pc1", "x": "x2"}
        missing = deepcopy(peterson)
        del missing.components[0].inputs["pc2"]
        wrong_type = deepcopy(peterson)
        wrong_type.components[0].inputs["pc2"] = "x2"
        cyclic = Composition(Pair,
            [Component(Copy, [Copy.advance], {"value":"produced"}, {"value":Await("copied")}),
             Component(Copy, [Copy.advance], {"value":"copied"}, {"value":Await("produced")})],
            invariants=[equal])
        for spec in (duplicate, missing, wrong_type, cyclic):
            with self.subTest(spec=spec), self.assertRaises(Unsupported):
                prepare_model(spec)

    def test_lean_composition_and_relation_proofs(self):
        with tempfile.TemporaryDirectory(prefix="rmverify-composition-tests-") as directory:
            for spec in (peterson, pipeline(Await("produced"))):
                report = verify(spec, directory=directory, timeout=120)
                self.assertTrue(report.ok, report)
                evidence = Path(report.evidence)
                self.assertIn("'Verified.composition_correspondence'", (evidence/"Translation.log").read_text())
                self.assertIn("'source_invariant'", (evidence/"Invariants.log").read_text())
            # An old-value read breaks this invariant; it must never be proved.
            self.assertFalse(verify(pipeline("produced"), directory=directory, timeout=30).ok)

    def test_corrupt_native_initialization_cannot_pass(self):
        from rmverify.compiler import compile_composition

        def corrupt(model):
            graphs, module = compile_composition(model)
            graph = graphs[0]
            graph["terms"][graph["outputs"][0]-len(graph["inputs"])] = ("lit", 17)
            return graphs, module

        with tempfile.TemporaryDirectory(prefix="rmverify-corrupt-composition-") as directory:
            with patch("rmverify.composition.compile_composition", corrupt):
                report = verify(pipeline(Await("produced")), directory=directory, timeout=30)
            self.assertNotEqual(report.translation, "proved", report)
            self.assertFalse(report.ok)


if __name__ == "__main__":
    unittest.main()
