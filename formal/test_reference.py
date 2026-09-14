"""Reproduce the external-model comparison without trusting a TLA parser."""
import hashlib
import json
from pathlib import Path
import unittest
from rmverify import verify
from rmverify import composition,lean_backend as lean
from examples.tla_lock_spec import spec

class ReferenceTests(unittest.TestCase):
    def test_pinned_tla_lock(self):
        root=Path(__file__).parent/'references'
        provenance=json.loads((root/'tlaplus/provenance.json').read_text())
        for name,digest in provenance['files'].items():
            self.assertEqual(hashlib.sha256((root/'tlaplus'/name).read_bytes()).hexdigest(),digest)
        report=verify(spec,timeout=180)
        self.assertTrue(report.ok,report)
        evidence=Path(report.evidence)
        _,names=composition.definitions(composition.prepare_model(spec))
        source='import Translation\nopen RMVerify RMVerify.Reactive Verified\nset_option maxHeartbeats 8000000\nset_option linter.all false\n'
        source+=(root/'LockModel.lean').read_text()
        source+='''
def encodeTLA (s : TLALock.State) : Verified.State := ⟨TLALock.code s.first, TLALock.code s.second, flag s.free⟩
theorem tla_initial (s : TLALock.State) : composed.initial (encodeTLA s) ↔ TLALock.initial s := by
  rcases s with ⟨a,b,free⟩
  cases a <;> cases b <;> cases free
  all_goals
'''
        source+='\n'.join('    '+line for line in lean.tactic(names+['encodeTLA','TLALock.initial','TLALock.code']).splitlines())+'\n'
        source+='''theorem tla_round (s t : TLALock.State) : composed.step (encodeTLA s) (encodeTLA t) ↔ TLALock.round s t := by
  rcases s with ⟨a,b,free⟩
  rcases t with ⟨a',b',free'⟩
  cases a <;> cases b <;> cases free
  all_goals
'''
        source+='\n'.join('    '+line for line in lean.tactic(names+['encodeTLA','TLALock.round','TLALock.next','TLALock.process','TLALock.code','TLALock.State.mk.injEq']).splitlines())+'\n'
        source+='''theorem tla_source_round (s t : TLALock.State) : sourceModule.step (encodeTLA s) (encodeTLA t) ↔ TLALock.round s t := by
  rw [source_module_eq]; exact tla_round s t
#print axioms tla_initial
#print axioms tla_round
#print axioms tla_source_round
'''
        status,reason=lean.run(evidence,'Reference',source,['tla_initial','tla_round','tla_source_round'],180)
        self.assertEqual(status,'proved',reason)
        (evidence/'reference-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
        artifact=json.loads((evidence/'artifact.json').read_text())
        lean.seal(evidence,artifact['sources'],180)

if __name__=='__main__':unittest.main()
