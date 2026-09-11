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
    def test_stuck_process_loses_a_specified_round(self):
        from examples.peterson_stuck import peterson as stuck
        before, after = (0, 0, False, False), (1, 0, False, False)
        model = prepare_model(stuck)
        self.assertIn(before, initial_states(model))
        self.assertTrue(paper_round(state_object(before), state_object(after)))
        self.assertNotIn(after, successors(model, before))

    def test_peterson_rounds(self):
        model = prepare_model(peterson)
        self.assertEqual(len(model["atoms"]), 2)
        self.assertEqual([a["controls"] for a in model["atoms"]], [[0, 2], [1, 3]])
        self.assertEqual([a["awaits"] for a in model["atoms"]], [[], []])
        self.assertNotIn("run1", model["fields"])
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
            old_report = verify(pipeline("produced"), directory=directory, timeout=30)
            self.assertEqual(old_report.status, "refuted", old_report)
            self.assertEqual(old_report.properties['invariant:equal']['witness']['kind'], 'reachable_invariant')
            from examples.peterson_stuck import peterson as stuck
            stuck_report = verify(stuck, directory=directory, timeout=120)
            self.assertEqual(stuck_report.status, "refuted", stuck_report)
            self.assertEqual(stuck_report.properties['invariant:mutual_exclusion']['status'], 'proved')
            self.assertEqual(stuck_report.properties['relation:paper_round']['witness']['kind'], 'relation_mismatch')

    def test_corrupt_generated_wiring_cannot_pass(self):
        from rmverify import composition
        original = composition.definitions
        def corrupt(model):
            source, names = original(model)
            start = source.index("def atom1 :")
            end = source.index("def sourceAtom1 :", start)
            source = source[:start] + source[start:end].replace("t.«produced»", "s.«produced»") + source[end:]
            return source, names
        with tempfile.TemporaryDirectory(prefix="rmverify-wiring-") as directory:
            with patch.object(composition, 'definitions', corrupt):
                report = verify(pipeline(Await("produced")), directory=directory, timeout=30)
            self.assertTrue((Path(report.evidence)/'Translation.lean').exists(), report)
            self.assertNotEqual(report.translation, 'proved', report)

    def test_corrupt_initialization_cannot_pass(self):
        from rmverify import lean_backend
        original = lean_backend.compiled_definition
        def corrupt(program, i):
            lines, names = original(program, i)
            if program.initialize:
                lines[-1] = "  [17, 0]"
            return lines, names
        with tempfile.TemporaryDirectory(prefix="rmverify-corrupt-composition-") as directory:
            with patch.object(lean_backend, "compiled_definition", corrupt):
                report = verify(pipeline(Await("produced")), directory=directory, timeout=30)
            self.assertTrue((Path(report.evidence)/"Translation.lean").exists(), report)
            self.assertNotEqual(report.translation, "proved", report)
            self.assertFalse(report.ok)


if __name__ == "__main__":
    unittest.main()
