import Semantics
import Veil.Base
import Veil.Core.Tools.ModelChecker.TransitionSystem

set_option veil.smt.trust false

namespace RMVerify.Reactive

/-- Each Veil transition is a complete RM round, including independent stutter. -/
def Module.toVeil (m : Module State) : Veil.RelationalTransitionSystem Unit State Unit where
  assumptions _ := True
  init _ := m.initial
  tr _ s _ t := m.step s t

theorem veil_initial (m : Module State) (s : State) :
    m.toVeil.init () s ↔ m.initial s := Iff.rfl

theorem veil_round (m : Module State) (s t : State) :
    m.toVeil.next () s t ↔ m.step s t := by
  simp [Module.toVeil, Veil.RelationalTransitionSystem.next]

theorem veil_reachable (m : Module State) (s : State) :
    m.toVeil.reachable () s ↔ Reachable m s := by
  constructor
  · intro h
    induction h with
    | init s _ h => exact .initial h
    | step s t _ h ih => exact .step ih ((veil_round m s t).mp h)
  · intro h
    induction h with
    | initial h => exact .init _ True.intro h
    | @step s t _ h ih => exact .step s t ih ((veil_round m s t).mpr h)

#print axioms veil_initial
#print axioms veil_round
#print axioms veil_reachable
end RMVerify.Reactive
