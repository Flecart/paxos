"""Exercise the pinned solver, reconstruction audit, and diagnostic distinction."""
from pathlib import Path
import tempfile
import unittest
from rmverify import checking,lean_backend as lean,symbolic
from examples.programs import unstrengthened

class AutomationTests(unittest.TestCase):
    def test_reconstruction_and_counterexample_kinds(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            lean.prepare(directory);lean.build(directory,90)
            for trust,expected in [('false','proved'),('true','error')]:
                source=f'''import Veil
set_option veil.smt.trust {trust}
set_option veil.smt.timeout 5
theorem reconstructed (a b : Int) (ha : a ≥ 0) (hb : b ≥ 0) : a+b ≥ 0 := by veil_smt
#print axioms reconstructed
'''
                status,reason=lean.run(directory,'SMT'+trust,source,['reconstructed'],60)
                self.assertEqual(status,expected,reason)
            model=checking.prepare_model(unstrengthened)
            source,names=lean.definitions(model)
            status,reason=lean.run(directory,'Translation',source,['Verified.source_model_eq'],90,output=True)
            self.assertEqual(status,'proved',reason)
            queries=symbolic.search(directory,model,names,composition=False,typed=False,depth=2,timeout=30)
            self.assertEqual([(q['kind'],q['status']) for q in queries],[('counterexample_to_induction','candidate'),('bounded_symbolic_trace','no-candidate')])
            self.assertTrue(all(not q['checked_witness'] for q in queries))

if __name__=='__main__':unittest.main()
