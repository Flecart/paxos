import Semantics

namespace RMVerify.Reactive

/-- Infinite executions include stuttering only when the module permits it. -/
def Execution (m : Module State) (run : Nat → State) : Prop :=
  m.initial (run 0) ∧ ∀ n, m.step (run n) (run (n + 1))

def Eventually (p : State → Prop) (run : Nat → State) (start : Nat := 0) : Prop :=
  ∃ n, start ≤ n ∧ p (run n)

def Always (p : State → Prop) (run : Nat → State) : Prop := ∀ n, p (run n)

def LeadsTo (p q : State → Prop) (run : Nat → State) : Prop :=
  ∀ n, p (run n) → Eventually q run n

/-- A continuously enabled action must eventually occur. Fairness is a premise,
    never silently added to the transition relation. -/
def WeakFair (enabled : State → Prop) (action : State → State → Prop)
    (run : Nat → State) : Prop :=
  ∀ n, (∀ k, n ≤ k → enabled (run k)) →
    ∃ k, n ≤ k ∧ action (run k) (run (k + 1))

theorem execution_reachable (m : Module State) (run : Nat → State)
    (h : Execution m run) : ∀ n, Reachable m (run n) := by
  intro n
  induction n with
  | zero => exact .initial h.1
  | succ n ih => exact .step ih (h.2 n)

/-- A persistent obligation whose fair action establishes the target leads to it. -/
theorem fair_leads_to (run : Nat → State) (p q enabled : State → Prop)
    (action : State → State → Prop)
    (fair : WeakFair enabled action run)
    (persists : ∀ n, p (run n) → ¬ q (run n) → p (run (n + 1)))
    (enables : ∀ n, p (run n) → ¬ q (run n) → enabled (run n))
    (finishes : ∀ n, p (run n) → action (run n) (run (n + 1)) → q (run (n + 1))) :
    LeadsTo p q run := by
  intro n hp
  apply Classical.byContradiction
  intro absent
  have hq : ∀ k, n ≤ k → ¬ q (run k) := by
    intro k hk h; exact absent ⟨k, hk, h⟩
  have persistent : ∀ k, n ≤ k → p (run k) := by
    intro k hk
    have all : ∀ d, p (run (n + d)) := by
      intro d
      induction d with
      | zero => simpa using hp
      | succ d ih => exact persists (n + d) ih (hq (n + d) (by omega))
    have eq : n + (k - n) = k := by omega
    simpa [eq] using all (k - n)
  obtain ⟨k, hk, ha⟩ := fair n (fun k hk => enables k (persistent k hk) (hq k hk))
  exact hq (k + 1) (by omega) (finishes k (persistent k hk) ha)

/-- Fair progress may take arbitrarily many steps, but cannot strictly decrease
    a natural-number rank forever. No bounded-time conclusion is implied. -/
theorem eventually_of_rank (run : Nat → State) (goal : State → Prop)
    (rank : State → Nat)
    (progress : ∀ n, ¬ goal (run n) →
      ∃ k, n < k ∧ rank (run k) < rank (run n)) : Eventually goal run := by
  have h : ∀ r n, rank (run n) = r → Eventually goal run n := by
    intro r
    induction r using Nat.strongRecOn with
    | ind r ih =>
      intro n hr
      by_cases hg : goal (run n)
      · exact ⟨n, Nat.le_refl n, hg⟩
      · obtain ⟨k, hnk, hlt⟩ := progress n hg
        obtain ⟨j, hkj, hj⟩ := ih (rank (run k)) (by omega) k rfl
        exact ⟨j, by omega, hj⟩
  exact h (rank (run 0)) 0 rfl

/-- A fair action eventually establishes a goal if absence of that goal keeps
    it enabled after the specified starting time. -/
theorem eventually_fair (run : Nat → State) (goal enabled : State → Prop)
    (action : State → State → Prop) (start : Nat)
    (fair : WeakFair enabled action run)
    (enables : ∀ n, start ≤ n → ¬ goal (run n) → enabled (run n))
    (finishes : ∀ n, start ≤ n → action (run n) (run (n+1)) → goal (run (n+1))) :
    Eventually goal run start := by
  apply Classical.byContradiction
  intro absent
  have hg : ∀ n, start ≤ n → ¬ goal (run n) :=
    fun n hn h => absent ⟨n,hn,h⟩
  obtain ⟨n, hn, ha⟩ := fair start (fun n hn => enables n hn (hg n hn))
  exact hg (n+1) (by omega) (finishes n hn ha)

end RMVerify.Reactive
