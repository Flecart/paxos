import Mathlib.Data.Finset.Basic

/- Finite conjunctions of eventually-permanent properties. -/
namespace PaxosSystem

/-- If each member of a finite set eventually satisfies a property forever,
    then eventually all of them satisfy it simultaneously, forever. -/
theorem eventually_forall {ι : Type} [DecidableEq ι] (s : Finset ι) (P : ι → Nat → Prop)
    (h : ∀ a ∈ s, ∃ t, ∀ n, t ≤ n → P a n) : ∃ t, ∀ n, t ≤ n → ∀ a ∈ s, P a n := by
  induction s using Finset.induction_on with
  | empty => exact ⟨0, fun _ _ a ha => absurd ha (Finset.notMem_empty a)⟩
  | insert x s hx ih =>
    obtain ⟨t1, h1⟩ := h x (Finset.mem_insert_self x s)
    obtain ⟨t2, h2⟩ := ih (fun a ha => h a (Finset.mem_insert_of_mem ha))
    refine ⟨max t1 t2, fun n hn a ha => ?_⟩
    rcases Finset.mem_insert.mp ha with rfl | ha
    · exact h1 n (le_trans (le_max_left _ _) hn)
    · exact h2 n (le_trans (le_max_right _ _) hn) a ha

end PaxosSystem
