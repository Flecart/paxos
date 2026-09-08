import PaxosFormal.Network

namespace PaxosFormal

set_option maxRecDepth 1000
set_option maxHeartbeats 200000

attribute [local irreducible] initialWorld

/-- A generic two-state trace keeps temporal reasoning independent of RM data. -/
def settleTrace (first rest : α) : Nat → α
  | 0 => first
  | _ + 1 => rest

theorem settle_execution (first rest : α) (step : α → α → Prop)
    (start : step first rest) (loop : step rest rest) :
    Execution first step (settleTrace first rest) := by
  constructor
  · rfl
  · intro t
    cases t with
    | zero => exact start
    | succ t => exact loop

theorem settle_not_live (first rest : α) (p q : α → Prop)
    (requested : p rest) (notDone : ¬ q rest) :
    ¬ LeadsTo p q (settleTrace first rest) := by
  intro live
  obtain ⟨u, hu, done⟩ := live 1 requested
  cases u with
  | zero => omega
  | succ u => exact notDone done

theorem idle_transition (w : World) (scope : WithinScope w) : Transition w w :=
  ⟨.idle, rfl, scope, scope⟩

/-- A real RM-generated state: n1 has submitted A and is awaiting delivery. -/
@[irreducible] def waitingWorld : World := networkStep initialWorld (.propose 0 1)
def stalledTrace : Nat → World := settleTrace initialWorld waitingWorld

theorem waiting_eq : networkStep initialWorld (.propose 0 1) = waitingWorld := by
  unfold waitingWorld
  rfl

-- Keep concrete checks Boolean: synthesizing Decidable for a reducible World
-- proposition can unfold the entire generated RM before native evaluation.
private theorem scope_of_check (w : World)
    (h : (!w.outside && !w.invalid) = true) : WithinScope w := by
  simpa [WithinScope] using h

private theorem nonempty_of_check (xs : List Int)
    (h : (!xs.isEmpty) = true) : xs ≠ [] := by
  intro empty
  simp [empty] at h

theorem initial_in_scope : WithinScope initialWorld :=
  scope_of_check initialWorld (by native_decide)
theorem waiting_in_scope : WithinScope waitingWorld :=
  scope_of_check waitingWorld (by native_decide)
theorem waiting_has_submission : waitingWorld.submitted ≠ [] :=
  nonempty_of_check waitingWorld.submitted (by native_decide)
theorem waiting_has_no_choice : hasChoice waitingWorld = false := by native_decide

/-- With no fairness assumption, a successful enqueue may wait forever. -/
theorem stalled_is_execution : Execution initialWorld Transition stalledTrace :=
  settle_execution initialWorld waitingWorld Transition
    ⟨.propose 0 1, waiting_eq, initial_in_scope, waiting_in_scope⟩
    (idle_transition waitingWorld waiting_in_scope)

theorem stalled_not_live : ¬ ProposalLiveness stalledTrace :=
  settle_not_live initialWorld waitingWorld
    (fun w => w.submitted ≠ []) (fun w => hasChoice w = true)
    waiting_has_submission (fun h => Bool.false_ne_true (waiting_has_no_choice.symm.trans h))

/-- This refutes unconditional liveness, not fair-scheduler liveness. -/
theorem unconditional_proposal_liveness_is_false :
    ¬ (∀ trace, Execution initialWorld Transition trace → ProposalLiveness trace) := by
  intro h
  exact stalled_not_live (h stalledTrace stalled_is_execution)

end PaxosFormal
