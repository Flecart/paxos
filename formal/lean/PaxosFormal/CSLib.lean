import PaxosFormal.Liveness

namespace PaxosFormal

attribute [local irreducible] initialWorld

/-- The actual Array-based interpreter satisfies the instruction-list relation. -/
theorem execute_correct (program : Array Instr) (s : Array Int) :
    Executes program.toList s (execute program s) := by
  simpa only [execute, Array.foldl_toList] using executeList_correct program.toList s

/-- The network's finite reachability is exactly CSLib labelled reachability. -/
theorem reachable_iff_cslib (s : World) :
    Reachable initialWorld Transition s ↔ ∃ actions, networkLTS.MTr initialWorld actions s := by
  constructor
  · intro h
    induction h with
    | initial => exact ⟨[], .refl⟩
    | next _ step ih =>
      obtain ⟨actions, ha⟩ := ih
      obtain ⟨action, hs⟩ := step
      exact ⟨actions ++ [action], Cslib.LTS.MTr.stepR networkLTS ha hs⟩
  · rintro ⟨actions, h⟩
    have extend : ∀ {a b : World} {labels : List Action}, networkLTS.MTr a labels b →
        Reachable initialWorld Transition a → Reachable initialWorld Transition b := by
      intro a b labels path
      induction path with
      | refl => exact id
      | stepL h _ ih => exact fun start => ih (.next start ⟨_, h⟩)
    exact extend h .initial

/-- Scheduler executions use CSLib's infinite labelled-execution component. -/
theorem scheduler_iff_cslib (trace : Nat → World) (actions : Nat → Action) :
    SchedulerExecution trace actions ↔
      trace 0 = initialWorld ∧ networkLTS.OmegaExecution ⟨trace⟩ ⟨actions⟩ := by
  constructor
  · rintro ⟨⟨initial, steps⟩, scheduled⟩
    refine ⟨initial, ?_⟩
    intro t
    obtain ⟨_, _, before, after⟩ := steps t
    exact ⟨scheduled t, before, after⟩
  · rintro ⟨initial, steps⟩
    exact ⟨⟨initial, fun t => ⟨actions t, steps t⟩⟩, fun t => (steps t).1⟩

/-- CSLib temporal composition combines the two requested liveness statements. -/
theorem proposal_to_learning (trace : Nat → World)
    (proposal : ProposalLiveness trace) (learning : LearningLiveness trace) :
    LeadsTo (fun w => w.submitted ≠ []) (fun w => allRecognize w = true) trace :=
  Cslib.ωSequence.leadsTo_trans proposal learning

/-- Lift a two-state trace into CSLib's infinite-execution relation. -/
theorem settle_omega (lts : Cslib.LTS α β) (first rest : α) (start idle : β)
    (firstStep : lts.Tr first start rest) (loop : lts.Tr rest idle rest) :
    lts.OmegaExecution ⟨settleTrace first rest⟩ ⟨settleTrace start idle⟩ := by
  intro t
  cases t with
  | zero => exact firstStep
  | succ t => exact loop

theorem cslib_idle (w : World) (scope : WithinScope w) : networkLTS.Tr w .idle w :=
  ⟨rfl, scope, scope⟩

/-- The checked no-fairness counterexample also refutes the CSLib statement. -/
theorem cslib_unconditional_liveness_is_false :
    ¬ (∀ trace actions, trace 0 = initialWorld →
      networkLTS.OmegaExecution ⟨trace⟩ ⟨actions⟩ → ProposalLiveness trace) := by
  intro claimed
  exact stalled_not_live (claimed stalledTrace (settleTrace (.propose 0 1) .idle)
    stalled_is_execution.1
    (settle_omega networkLTS initialWorld waitingWorld (.propose 0 1) .idle
      ⟨waiting_eq, initial_in_scope, waiting_in_scope⟩
      (cslib_idle waitingWorld waiting_in_scope)))

end PaxosFormal
