import VerifiedPedersen.Extraction
import UserVerification.Model

open Aeneas.Std
namespace Pedersen
noncomputable section
variable {F G : Type} [Field F] [AddCommGroup G] [Module F G]

/-- Mathematical interpretation of the Rust backend interface. Concrete curve
    implementations must separately prove they realize these operations. -/
def backend [DecidableEq G] : verified_pedersen.Group G F where
  scale g x := .ok (x • g)
  add g h := .ok (g + h)
  same g h := .ok (decide (g = h))

structure BackendLaws [DecidableEq G] (ops : verified_pedersen.Group G F) : Prop where
  scale : ∀ g x, ops.scale g x = .ok (x • g)
  add : ∀ g h, ops.add g h = .ok (g + h)
  same : ∀ g h, ops.same g h = .ok (decide (g = h))

theorem commit_refines [DecidableEq G] (ops : verified_pedersen.Group G F)
    (laws : BackendLaws ops) (g h : G) (m r : F) :
    verified_pedersen.commit ops g h m r = .ok (commit g h m r) := by
  simp [verified_pedersen.commit, laws.scale, laws.add, commit]

theorem verify_refines [DecidableEq G] (ops : verified_pedersen.Group G F)
    (laws : BackendLaws ops) (g h c : G) (m r : F) :
    verified_pedersen.verify ops g h m r c = .ok (decide (commit g h m r = c)) := by
  simp [verified_pedersen.verify, commit_refines ops laws, laws.same]

theorem rust_commit [DecidableEq G] (g h : G) (m r : F) :
    verified_pedersen.commit backend g h m r = .ok (commit g h m r) := by
  rfl

theorem rust_verify [DecidableEq G] (g h c : G) (m r : F) :
    verified_pedersen.verify backend g h m r c = .ok (decide (commit g h m r = c)) := by
  rfl

theorem correctness [DecidableEq G] (g h : G) (m r : F) :
    verified_pedersen.verify backend g h m r (commit g h m r) = .ok true := by
  simp [rust_verify]

theorem correctness_refines [DecidableEq G] (ops : verified_pedersen.Group G F)
    (laws : BackendLaws ops) (g h : G) (m r : F) :
    verified_pedersen.verify ops g h m r (commit g h m r) = .ok true := by
  simp [verify_refines ops laws]

theorem rust_perfect_hiding [Fintype F] [DecidableEq G]
    (ops : verified_pedersen.Group G F) (laws : BackendLaws ops) (g h : G)
    (generator : Function.Surjective (fun r : F => r • h)) (m₀ m₁ : F) (c : G) :
    probability (fun r : F => verified_pedersen.commit ops g h m₀ r = .ok c) =
    probability (fun r : F => verified_pedersen.commit ops g h m₁ r = .ok c) := by
  simpa [commit_refines ops laws] using perfect_hiding g h generator m₀ m₁ c

def RustBindingWin [DecidableEq G] (ops : verified_pedersen.Group G F)
    (g h : G) (o : Opening F) : Prop :=
  o.message ≠ o.otherMessage ∧ ∃ c,
    verified_pedersen.verify ops g h o.message o.blind c = .ok true ∧
    verified_pedersen.verify ops g h o.otherMessage o.otherBlind c = .ok true

theorem rust_binding_reduction [DecidableEq G] (ops : verified_pedersen.Group G F)
    (laws : BackendLaws ops) (g h : G)
    (generator : Function.Injective (fun x : F => x • g)) (o : Opening F)
    (win : RustBindingWin ops g h o) : extractLog o • g = h := by
  obtain ⟨distinct,c,left,right⟩ := win
  have hl : commit g h o.message o.blind = c := by
    simpa [verify_refines ops laws] using left
  have hr : commit g h o.otherMessage o.otherBlind = c := by
    simpa [verify_refines ops laws] using right
  exact binding_reduction g h generator o ⟨distinct, hl.trans hr.symm⟩

theorem rust_binding_bound [DecidableEq G] (ops : verified_pedersen.Group G F)
    (laws : BackendLaws ops) {Ω : Type} [Fintype Ω] [Nonempty Ω] (g : G)
    (generator : Function.Injective (fun x : F => x • g))
    (challenge : Ω → G) (attack : Ω → Opening F) (ε : ℚ)
    (hard : probability (fun ω => extractLog (attack ω) • g = challenge ω) ≤ ε) :
    probability (fun ω => RustBindingWin ops g (challenge ω) (attack ω)) ≤ ε :=
  le_trans (probability_mono _ _
    (fun ω hω => rust_binding_reduction ops laws g (challenge ω) generator (attack ω) hω)) hard

end
end Pedersen

#print axioms Pedersen.commit_refines
#print axioms Pedersen.rust_perfect_hiding
#print axioms Pedersen.rust_binding_bound
