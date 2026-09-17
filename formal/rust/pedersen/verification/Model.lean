import Mathlib.Algebra.Module.Basic
import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Tactic.Abel

namespace Pedersen
noncomputable section
open scoped BigOperators

/-- Exact probability on a finite uniform random tape. Events need not be decidable
    computationally; classical decidability is used only in the specification. -/
def probability {Ω : Type} [Fintype Ω] (event : Ω → Prop) : ℚ := by
  classical
  exact (∑ ω, if event ω then 1 else 0) / Fintype.card Ω

theorem probability_true {Ω : Type} [Fintype Ω] [Nonempty Ω] :
    probability (fun _ : Ω => True) = 1 := by
  simp [probability, Fintype.card_ne_zero]

theorem probability_mono {Ω : Type} [Fintype Ω] (p q : Ω → Prop)
    (h : ∀ ω, p ω → q ω) : probability p ≤ probability q := by
  classical
  apply div_le_div_of_nonneg_right _ (Nat.cast_nonneg _)
  apply Finset.sum_le_sum
  intro ω _
  by_cases hp : p ω
  · simp [hp, h ω hp]
  · simp [hp]; split_ifs <;> norm_num

theorem probability_permutation {Ω : Type} [Fintype Ω] (e : Ω ≃ Ω) (p : Ω → Prop) :
    probability (fun ω => p (e ω)) = probability p := by
  classical
  unfold probability
  congr 1
  exact e.sum_comp (fun ω => if p ω then (1 : ℚ) else 0)

variable {F G : Type} [Field F] [AddCommGroup G] [Module F G]

def commit (g h : G) (m r : F) : G := m • g + r • h

/-- Equality of entire output distributions under uniform finite-field blinding. -/
theorem perfect_hiding [Fintype F] (g h : G)
    (generator : Function.Surjective (fun r : F => r • h)) (m₀ m₁ : F) (c : G) :
    probability (fun r : F => commit g h m₀ r = c) =
    probability (fun r : F => commit g h m₁ r = c) := by
  obtain ⟨d, hd⟩ := generator ((m₀ - m₁) • g)
  have shift : commit g h m₀ = (commit g h m₁) ∘ (Equiv.addRight d) := by
    funext r
    simp only [commit, Function.comp_apply, Equiv.coe_addRight, add_smul, hd, sub_smul]
    abel
  rw [shift]
  exact probability_permutation (Equiv.addRight d) (fun r => commit g h m₁ r = c)

structure Opening (F : Type) where
  message : F
  blind : F
  otherMessage : F
  otherBlind : F

def BindingWin (g h : G) (o : Opening F) : Prop :=
  o.message ≠ o.otherMessage ∧
  commit g h o.message o.blind = commit g h o.otherMessage o.otherBlind

def extractLog (o : Opening F) : F :=
  (o.message - o.otherMessage) / (o.otherBlind - o.blind)

theorem binding_reduction (g h : G)
    (generator : Function.Injective (fun x : F => x • g)) (o : Opening F)
    (win : BindingWin g h o) : (extractLog o) • g = h := by
  have eq : (o.message - o.otherMessage) • g = (o.otherBlind - o.blind) • h := by
    simp only [sub_smul]
    apply sub_eq_sub_iff_add_eq_add.mpr
    simpa [commit, add_comm] using win.2
  have nonzero : o.otherBlind - o.blind ≠ 0 := by
    intro hz
    have hm : (o.message - o.otherMessage) • g = (0 : F) • g := by
      simpa [hz] using eq
    exact win.1 (sub_eq_zero.mp (generator hm))
  calc
    (extractLog o) • g = (o.otherBlind - o.blind)⁻¹ • ((o.message - o.otherMessage) • g) := by
      simp [extractLog, div_eq_mul_inv, smul_smul, mul_comm]
    _ = (o.otherBlind - o.blind)⁻¹ • ((o.otherBlind - o.blind) • h) := by rw [eq]
    _ = h := inv_smul_smul₀ nonzero h

/-- Pointwise reduction on the same finite random tape, including randomized setup. -/
theorem binding_probability {Ω : Type} [Fintype Ω] (g : G)
    (generator : Function.Injective (fun x : F => x • g))
    (challenge : Ω → G) (attack : Ω → Opening F) :
    probability (fun ω => BindingWin g (challenge ω) (attack ω)) ≤
    probability (fun ω => extractLog (attack ω) • g = challenge ω) :=
  probability_mono _ _ (fun ω hω => binding_reduction g (challenge ω) generator (attack ω) hω)

end
end Pedersen
