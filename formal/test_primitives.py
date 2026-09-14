import importlib.util
from pathlib import Path
import tempfile
import unittest
from rmverify import verify
from rmverify.frontend import Unsupported
from rmverify.checking import prepare_model
from examples import primitives_spec

class PrimitiveTests(unittest.TestCase):
    def test_effects_moves_optional_scalars_and_shared_inputs(self):
        report=verify(primitives_spec.store,timeout=120)
        self.assertTrue(report.ok,report)
        table=primitives_spec.Store()
        table.update(3)
        self.assertEqual((table.entries,table.total),({3:7},7))
        audit=(Path(report.evidence)/'Translation.log').read_text()
        self.assertIn('affine',audit)

    def test_set_iteration_has_a_permutation_proof(self):
        report=verify(primitives_spec.summation,timeout=120)
        self.assertTrue(report.ok,report)
        self.assertIn('set_loop_order',(Path(report.evidence)/'Translation.log').read_text())
        s=primitives_spec.Sum();s.accumulate();s.accumulate()
        self.assertEqual(s.total,6)

    def load(self,source):
        path=Path(self.temp.name)/'fixture.py';path.write_text(source)
        spec=importlib.util.spec_from_file_location('primitive_fixture',path)
        module=importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name]=module
        exec(compile(source,str(path),'exec'),module.__dict__)
        return module.spec

    def setUp(self):self.temp=tempfile.TemporaryDirectory()
    def tearDown(self):self.temp.cleanup()

    def test_conflicts_and_use_after_transfer_are_rejected(self):
        base='''from rmverify import Specification
class S:
    ids:set[int]
    def __init__(self)->None:self.ids=set()
    def step(self,other:set[int])->None:
BODY
def safe(s:S)->bool:return True
spec=Specification(S,[S.step],[safe])
'''
        bodies=[('        owned:set[int]=set()\n        self.ids=owned\n        owned.add(1)','definite assignment'),
                ('        other.add(1)','shared input borrow'),
                ('        self.ids.add(1)\n        found:bool=1 in other','may alias'),
                ('        alias=self.ids\n        self.ids.add(1)\n        alias.add(2)','conflicting'),
                ('        if True:\n            alias=self.ids\n        alias.add(1)','escapes')]
        for body,message in bodies:
            with self.subTest(body=body),self.assertRaisesRegex(Unsupported,message):prepare_model(self.load(base.replace('BODY',body)))

    def test_set_iteration_rejects_observable_order(self):
        spec=self.load('''from rmverify import Specification
class S:
    ids:set[int]
    last:int
    def __init__(self)->None:
        self.ids={1,2}
        self.last=0
    def step(self)->None:
        for element in self.ids:
            self.last=element
def safe(s:S)->bool:return True
spec=Specification(S,[S.step],[safe])
''')
        report=verify(spec,timeout=60)
        self.assertNotEqual(report.translation,'proved',report)
        self.assertIn('set_loop_commutes',(Path(report.evidence)/'Translation.log').read_text())

    def test_dictionary_evaluation_order_and_exact_fault(self):
        spec=self.load('''from dataclasses import dataclass
from rmverify import Specification
@dataclass(frozen=True)
class Message:
    value:int
class S:
    entries:dict[int,int]
    indices:dict[int,int]
    message:Message|None
    marker:int
    def __init__(self)->None:
        self.entries={}
        self.indices={}
        self.message=None
        self.marker=0
    def assign(self)->None:
        self.marker=1
        self.entries[self.indices[0]]=self.message.value
    def construct(self)->None:
        self.marker=1
        self.entries={self.indices[0]:self.message.value}
    def optional_result(self)->Message|None:
        return None if self.message.value>0 else None
    def unit_result(self)->None:
        return None if self.message.value>0 else None
    def get_default(self)->int|None:
        return self.entries.get(0,None if self.message.value>0 else None)
def safe(s:S)->bool:return True
spec=Specification(S,[S.assign,S.construct,S.optional_result,S.unit_result,S.get_default],[safe])
''')
        from rmverify import lean_backend as lean
        report=verify(spec,timeout=90,depth=1)
        self.assertEqual(report.properties['no-fault']['status'],'refuted',report)
        proof='''import Translation
open RMVerify RMVerify.TypedSource Verified
theorem assignment_order : (model.step model.initial .m0).«$fault» = some .missingValue := by decide
theorem construction_order : (model.step model.initial .m1).«$fault» = some .missingKey := by decide
theorem optional_evaluation : (model.step model.initial .m2).«$fault» = some .missingValue := by decide
theorem unit_evaluation : (model.step model.initial .m3).«$fault» = some .missingValue := by decide
theorem default_evaluation : (model.step model.initial .m4).«$fault» = some .missingValue := by decide
theorem partial_write : (model.step model.initial .m0).marker = 1 := by decide
#print axioms assignment_order
#print axioms construction_order
#print axioms partial_write
#print axioms optional_evaluation
#print axioms unit_evaluation
#print axioms default_evaluation
'''
        status,reason=lean.run(Path(report.evidence),'EvaluationOrder',proof,['assignment_order','construction_order','partial_write','optional_evaluation','unit_evaluation','default_evaluation'],60)
        self.assertEqual(status,'proved',reason)

    def test_optional_keys_and_ordered_witness_data(self):
        spec=self.load('''from rmverify import Specification
class S:
    values:dict[int|None,int]
    last:int|None
    def __init__(self)->None:
        self.values={None:7,1:9}
        self.last=None
    def step(self)->None:
        self.values[None]=7
        self.last=self.values.get(None)
def safe(s:S)->bool:return len(s.values)==2 and None in s.values
spec=Specification(S,[S.step],[safe])
''')
        report=verify(spec,timeout=120)
        self.assertTrue(report.ok,report)
        from rmverify.typed_composition import state_key
        self.assertNotEqual(state_key([{1:7,2:9}]),state_key([{2:9,1:7}]))
        self.assertIn('dict',state_key([{None:7,1:9}]))

if __name__=='__main__':unittest.main()
