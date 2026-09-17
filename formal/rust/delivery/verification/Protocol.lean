import VerifiedDelivery.Extraction
import Specification

namespace Delivery
open Aeneas.Std RMVerify.Reactive

def module : Module U8 :=
  ⟨[⟨[],[],[],fun s => s = 0#u8,
    fun s t => ∃ event, verified_delivery.step s event = .ok t⟩]⟩
def Valid (s : U8) : Prop := s.val ≤ 1
def Done (s : U8) : Prop := s = 1#u8
def Waiting (s : U8) : Prop := s = 0#u8
def DeliveryTaken (s t : U8) : Prop := verified_delivery.step s true = .ok t
def Fair := WeakFair (fun s => ¬ Done s) DeliveryTaken

theorem safe : RMVerify.Spec.Invariant module Valid := by
  apply invariant_of_induction
  · intro s hs
    have h : s = 0#u8 := by simpa [module, Module.initial] using hs
    subst s; simp [Valid]
  · intro s t hs ht
    obtain ⟨event,he⟩ : ∃ event, verified_delivery.step s event = .ok t := by
      simpa [module, Module.step] using ht
    cases event <;> simp [verified_delivery.step] at he <;> subst t
    · exact hs
    · simp [Valid]

theorem always_valid : RMVerify.Spec.Always module Fair Valid :=
  RMVerify.Spec.invariant_always module Fair Valid safe

theorem progress : RMVerify.Spec.LeadsTo module Fair Waiting Done := by
  intro run _ fair n _
  apply eventually_fair run Done (fun s => ¬ Done s) DeliveryTaken n fair
  · exact fun _ _ h => h
  · intro k _ h
    have ht : 1#u8 = run (k+1) := by
      simpa [DeliveryTaken, verified_delivery.step] using h
    exact ht.symm

theorem eventually_done : RMVerify.Spec.Eventually module Fair Done := by
  intro run exec fair
  apply progress run exec fair 0
  simpa [Waiting, module, Module.initial] using exec.1

theorem no_unconditional_progress : ¬ RMVerify.Spec.Eventually module (fun _ => True) Done := by
  intro h
  have exec : Execution module (fun _ => 0#u8) := by
    constructor
    · simp [module, Module.initial]
    · intro n
      change ∀ a ∈ module.atoms, a.step (0#u8) (0#u8)
      simp only [module, List.mem_singleton, forall_eq]
      exact ⟨false, rfl⟩
  obtain ⟨n,_,hn⟩ := h _ exec trivial
  have impossible : (0 : Nat) = 1 := congrArg (fun x : U8 => x.val) hn
  omega

end Delivery
