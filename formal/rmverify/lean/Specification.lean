import Temporal

namespace RMVerify.Spec
open Reactive

/-- Safety over all reachable states; scheduling assumptions cannot weaken it. -/
def Invariant (m : Module S) (p : S → Prop) : Prop :=
  ∀ s, Reactive.Reachable m s → p s

/-- Temporal properties explicitly quantify over executions and their environment. -/
def Always (m : Module S) (env : (Nat → S) → Prop) (p : S → Prop) : Prop :=
  ∀ run, Execution m run → env run → Reactive.Always p run

def Eventually (m : Module S) (env : (Nat → S) → Prop) (p : S → Prop) : Prop :=
  ∀ run, Execution m run → env run → Reactive.Eventually p run

def LeadsTo (m : Module S) (env : (Nat → S) → Prop) (p q : S → Prop) : Prop :=
  ∀ run, Execution m run → env run → Reactive.LeadsTo p q run

theorem invariant_always (m : Module S) (env : (Nat → S) → Prop) (p : S → Prop)
    (h : Invariant m p) : Always m env p := by
  intro run exec _ n
  exact h _ (execution_reachable m run exec n)

end RMVerify.Spec
