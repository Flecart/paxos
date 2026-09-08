import PaxosFormal

-- Expose the proof trust boundary instead of hiding native evaluation.
#print axioms PaxosFormal.executeList_correct
#print axioms PaxosFormal.execute_correct
#print axioms PaxosFormal.reachable_iff_cslib
#print axioms PaxosFormal.scheduler_iff_cslib
#print axioms PaxosFormal.single_checked
#print axioms PaxosFormal.key_error_checked
#print axioms PaxosFormal.cslib_unconditional_liveness_is_false
