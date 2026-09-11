"""Small end-to-end collection and borrow checks. Run with formal/.venv/bin/python."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from rmverify import Specification, Contract, verify
from rmverify.checking import prepare_model, differential
from rmverify.frontend import Unsupported
from rmverify import typed_backend, lean_backend
from examples.collections_spec import spec, registry
from examples.receiver_spec import receiver, broken_receiver


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def load(self, body, predicate='s.last >= 0', *, field='last', result='None'):
        path = self.root/'fixture.py'
        path.write_text('''class Example:
    entries: dict[int, int]
    last: int
    def __init__(self) -> None:
        self.entries = {}
        self.last = 0
    def step(self, key: int) -> None:
''' + '\n'.join('        '+line for line in body.splitlines()) + f'''

def safe(s: Example) -> bool:
    return {predicate}
''')
        path.write_text(path.read_text().replace('def step(self, key: int) -> None:', f'def step(self, key: int) -> {result}:'))
        if field != 'last': path.write_text(path.read_text().replace('last',field))
        entry = importlib.util.spec_from_file_location('collection_fixture',path)
        module = importlib.util.module_from_spec(entry)
        sys.modules[entry.name] = module
        exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
        return Specification(module.Example,[module.Example.step],invariants=[module.safe])

    def test_collection_proof_and_replay(self):
        report = verify(spec,directory=self.root,timeout=60,depth=2)
        self.assertTrue(report.ok,report)
        import subprocess
        replay = subprocess.run([sys.executable,str(Path(report.evidence)/'recheck.py')],capture_output=True,text=True)
        self.assertEqual(replay.returncode,0,replay.stdout+replay.stderr)
        obj = spec.target()
        obj.register(3)
        obj.register(1)
        obj.register(3)
        self.assertEqual(list(obj.entries.items()),[(3,7),(1,7)])
        self.assertEqual(obj.ids,{1,3})

    def test_registry_domains_payload_and_duplicates(self):
        report = verify(registry,directory=self.root,timeout=60,depth=1)
        self.assertTrue(report.ok,report)
        obj = registry.target()
        obj.register(3,7)
        obj.register(3,99)
        self.assertEqual(obj.entries,{3:7})
        self.assertEqual(obj.ids,{3})

    def test_duplicate_receiver_and_checked_violation(self):
        report = verify(receiver,directory=self.root,timeout=60,depth=2)
        self.assertTrue(report.ok,report)
        report = verify(broken_receiver,directory=self.root,timeout=60,depth=2)
        self.assertEqual(report.translation,'proved',report)
        self.assertEqual(report.status,'refuted',report)
        claim = report.properties['invariant:broken_consistent']
        self.assertEqual(claim['status'],'refuted',report)
        witness = claim['witness']
        self.assertEqual(witness['kind'],'reachable_invariant')
        self.assertEqual(len(witness['calls']),2)
        obj = broken_receiver.target()
        for call in witness['calls']: getattr(obj,call['method'])(**call['arguments'])
        self.assertEqual(obj.count,2)
        self.assertEqual(len(obj.processed),1)
        import subprocess
        result = subprocess.run([sys.executable,str(Path(report.evidence)/'recheck.py')],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_exclusive_and_shared_borrows(self):
        accepted = self.load('entries = self.entries\nentries[key] = 7\nself.last = entries[key]\nself.entries[key] = 8')
        report = verify(accepted,directory=self.root,timeout=60,depth=1)
        self.assertTrue(report.ok,report)
        shared = self.load('a = self.entries\nb = self.entries\nself.last = len(a) + len(b)')
        self.assertGreater(differential(prepare_model(shared)),0)
        for body in (
            'entries = self.entries\nself.last = len(self.entries)\nentries[key] = 7',
            'entries = self.entries\nself.entries[key] = 7\nself.last = len(entries)',
            'a = self.entries\nb = self.entries\na[key] = 1\nb[key] = 2',
        ):
            with self.subTest(body=body), self.assertRaisesRegex(Unsupported,'conflicting.*borrows'):
                prepare_model(self.load(body))

    def test_get_and_early_return(self):
        spec = self.load('if key < 0:\n    return\nself.entries[key] = 7\nself.last = self.entries.get(key, 0)')
        report = verify(spec,directory=self.root,timeout=60,depth=1)
        self.assertTrue(report.ok,report)

    def test_fault_field_is_not_reserved(self):
        spec = self.load('self.entries[key] = 7\nself.last = self.entries[key]',field='fault')
        report = verify(spec,directory=self.root,timeout=60,depth=1)
        self.assertTrue(report.ok,report)
        text = (Path(report.evidence)/'Translation.lean').read_text()
        self.assertIn('«fault» : Int',text)
        self.assertIn('«$fault» : Option Fault',text)

    def test_conflict_locations_include_method_indentation(self):
        with self.assertRaises(Unsupported) as raised:
            prepare_model(self.load('entries = self.entries\nself.last = len(self.entries)\nentries[key] = 7'))
        self.assertIn(':9:25:',str(raised.exception))
        self.assertIn(':8:9',str(raised.exception))

    def test_borrow_rebinding_and_annotation_mismatch(self):
        for body in (
            'entries = self.entries\nself.last = len(entries)\nentries = {}',
            'entries: set[int] = self.entries',
            'self = self.entries',
            'for self in self.entries:\n    pass',
        ):
            with self.subTest(body=body), self.assertRaises(Unsupported):
                prepare_model(self.load(body))

    def test_short_circuit_and_quantifiers(self):
        guarded = self.load('if key in self.entries:\n    self.last = self.entries[key]',
            'all(s.entries[k] >= 0 for k in s.entries)')
        model = prepare_model(guarded)
        self.assertGreater(differential(model),0)
        total = self.load('self.entries[key] = 7', 'all(k == k for k in s.entries)')
        report = verify(total,directory=self.root,timeout=60,depth=1)
        self.assertTrue(report.ok,report)
        short = self.load('if False and self.entries[key] > 0:\n    self.last = -1')
        self.assertGreater(differential(prepare_model(short)),0)

    def test_missing_lookup_is_not_proved(self):
        broken = self.load('self.last = 1\nself.last = self.entries[key]')
        report = verify(broken,directory=self.root,timeout=60,depth=1)
        self.assertEqual(report.translation,'proved',report)
        self.assertFalse(report.ok,report)
        self.assertEqual(report.properties['no-fault']['status'],'refuted',report)
        self.assertEqual(report.properties['no-fault']['witness']['state'],[{},1])
        source = (Path(report.evidence)/'Translation.lean').read_text()
        self.assertIn('some reason',source)
        faulty_predicate = self.load('self.entries[key] = 7', 's.entries[0] >= 0')
        report = verify(faulty_predicate,directory=self.root,timeout=60,depth=1)
        self.assertEqual(report.translation,'proved',report)
        claim = report.properties['invariant:safe']
        self.assertEqual(claim['status'],'refuted',report)
        self.assertEqual(claim['witness']['calls'],[])


    def test_ordered_dictionary_iteration(self):
        spec = self.load('self.entries[key] = 7\nself.last = 0\nfor k in self.entries:\n    self.last = self.last + 1')
        report = verify(spec,directory=self.root,timeout=60,depth=1)
        self.assertEqual(report.translation,'proved',report)
        self.assertGreater(differential(prepare_model(spec)),0)
        for body in (
            'for k in self.entries:\n    self.entries[k] = 7',
            'entries = self.entries\nfor k in entries:\n    entries[k] = 7',
        ):
            with self.assertRaisesRegex(Unsupported,'conflicting.*iteration'):
                prepare_model(self.load(body))

    def test_lean_collection_fault_and_network_primitives(self):
        lean_backend.prepare(self.root)
        lean_backend.build(self.root,60,typed=True)
        network_audits = ["RMVerify.Reactive."+n for n in ("empty_choice", "choice_nonblocking", "observed_projects", "observed_extends", "observed_reachable_iff")]
        source = (self.root/'Network.lean').read_text() + "\n" + "\n".join("#print axioms "+n for n in network_audits)
        status,reason = lean_backend.run(self.root,'Network',source,network_audits,60,output=True)
        self.assertEqual(status,'proved',reason)
        source = """import TypedSource
import Network
open RMVerify.TypedSource RMVerify.Reactive
structure Frame where
  entries : List (Int × Int)
  value : Int
  deriving Repr, DecidableEq

def failing : Stmt Frame Unit :=
  .seq (.assign (fun f v => {f with value := v}) (.value 1))
    (.assign (fun f v => {f with value := v})
      (.call₂ dictLookup (.read Frame.entries) (.value 99)))
theorem keeps_prior_write : failing.exec ⟨[], 0⟩ = .fault ⟨[], 1⟩ .missingKey := by rfl

def orderedLoop : Stmt Frame Unit := .each (.value [3, 1])
  (fun k => .assign (fun f v => {f with value := v}) (.value k))
theorem ordered_iteration : orderedLoop.exec ⟨[], 0⟩ = .next ⟨[], 1⟩ := by rfl

theorem dictionary_overwrite_order : dictSet [(3, 7), (1, 9)] 3 8 = [(3, 8), (1, 9)] := by decide
theorem duplicate_set : setAdd [3, 1] 3 = [3, 1] := by decide
theorem missing_get : dictLookup ([] : List (Int × Int)) 9 = .error .missingKey := by rfl

def available (s : List Int × Int) := s.1
def deliver (s : List Int × Int) (key : Int) := (s.1,key)
theorem no_fabrication (s t : List Int × Int) (h : choiceStep available deliver s t) : t.2 ∈ s.1 := by
  obtain ⟨key, hk, rfl⟩ := h
  exact hk
theorem repeated_delivery : choiceStep available deliver ([3],3) ([3],3) := by
  exact ⟨3, by decide, rfl⟩
"""
        audits = ['keeps_prior_write','ordered_iteration','dictionary_overwrite_order','duplicate_set','missing_get','no_fabrication','repeated_delivery',
                  'RMVerify.TypedSource.allM_order_independent','RMVerify.TypedSource.anyM_order_independent']
        source += "\n" + "\n".join('#print axioms '+n for n in audits)
        status,reason = lean_backend.run(self.root,'Primitives',source,audits,60)
        self.assertEqual(status,'proved',reason)

    def test_adapter_mutations_are_rejected(self):
        original_projection = typed_backend.state_projection
        original_frame = typed_backend.frame_value
        original_definitions = typed_backend.definitions
        def fault_projection(p,i,fields):
            return [line.replace('some reason','none') for line in original_projection(p,i,fields)]
        def input_frame(p,inputs):
            return original_frame(p,[v.replace('a0','(a0 + 1)') for v in inputs])
        def dropped_invariant(model):
            source,names = original_definitions(model)
            source = source.replace('def safe (s : State) : Prop := s.«$fault» = none ∧ inv0 s ∧ True',
                                    'def safe (s : State) : Prop := s.«$fault» = none ∧ True')
            return source,names
        for name,corrupt in [('state_projection',fault_projection),('frame_value',input_frame),('definitions',dropped_invariant)]:
            with self.subTest(adapter=name), patch.object(typed_backend,name,corrupt):
                report = verify(spec,directory=self.root,timeout=60,depth=1)
                self.assertTrue((Path(report.evidence)/'Translation.lean').exists(),report)
                self.assertNotEqual(report.translation,'proved',report)

    def test_return_adapter_correspondence(self):
        spec = self.load('self.entries[key] = 7\nreturn key',result='int')
        # Keep the predicate in the same source module for extraction and hashing.
        module = sys.modules[spec.target.__module__]
        path = Path(module.__file__)
        path.write_text(path.read_text()+"\ndef returned(before: Example, after: Example, result: int, key: int) -> bool:\n    return result == key\n")
        exec(compile(path.read_text(),str(path),'exec'),module.__dict__)
        spec = Specification(module.Example,[module.Example.step],contracts={module.Example.step: Contract(ensures=module.returned)})
        report = verify(spec,directory=self.root,timeout=60,depth=1)
        self.assertTrue(report.ok,report)
        original = typed_backend.definitions
        def corrupt(model):
            source,names = original(model)
            return source.replace('| .returned _ value => value','| .returned _ value => 7'),names
        with patch.object(typed_backend,'definitions',corrupt):
            report = verify(spec,directory=self.root,timeout=60,depth=1)
        self.assertTrue((Path(report.evidence)/'Translation.lean').exists(),report)
        self.assertNotEqual(report.translation,'proved',report)

    def test_mutated_collection_code_is_rejected(self):
        original = typed_backend.compiled_definition
        def corrupt(p,i):
            lines,names = original(p,i)
            if p.function is spec.transitions[0]:
                lines = [line.replace('(7 : Int)','(8 : Int)') for line in lines]
            return lines,names
        with patch.object(typed_backend,'compiled_definition',corrupt):
            report = verify(spec,directory=self.root,timeout=60,depth=1)
        self.assertTrue((Path(report.evidence)/"Translation.lean").exists(),report)
        self.assertNotEqual(report.translation,'proved',report)


if __name__ == '__main__': unittest.main()
