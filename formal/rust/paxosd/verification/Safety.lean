import UserVerification.Steps

/- Safety of the deployed cluster: every reachable state of the three extracted
   replicas and their network satisfies agreement and validity. No fairness,
   timing, or delivery assumption is used. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

theorem initial_inv (w : World) (h : Initial w) : Inv w := by
  obtain ⟨hn, hnet⟩ := h
  have node : ∀ k, w.node k = initS (rid k) := by
    intro k; have := hn k; rw [new_eq] at this; simp only [ok.injEq] at this; exact this.symm
  refine ⟨fun k => ?_, fun p hp => absurd hp (hnet p)⟩
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp [node, initS, pslot, vslot, quorumS, agreedS]

theorem initial_abs (w : World) (h : Initial w) : abs w = Paxos.initial := by
  obtain ⟨hn, hnet⟩ := h
  have node : ∀ k, w.node k = initS (rid k) := by
    intro k; have := hn k; rw [new_eq] at this; simp only [ok.injEq] at this; exact this.symm
  apply state_ext <;> simp [abs, Paxos.initial, node, initS, snap, hnet]

/-- Joint induction: the concrete invariant holds and the interpretation is a
    reachable state of the abstract Paxos model. -/
theorem reachable_inv (w : World) (h : Reactive.Reachable module w) :
    Inv w ∧ Reactive.Reachable Paxos.module (abs w) := by
  induction h with
  | @initial w h =>
    have h : Initial w := by simpa [module, Reactive.Module.initial] using h
    refine ⟨initial_inv w h, .initial ?_⟩
    simpa [Paxos.module, Reactive.Module.initial] using initial_abs w h
  | @step w w' _ h ih =>
    have h : Step w w' := by simpa [module, Reactive.Module.step] using h
    obtain ⟨inv, areach⟩ := ih
    rcases (step_iff w w').mp h with rfl | ⟨i, inp, al, rfl⟩
    · exact ⟨inv, areach⟩
    · obtain ⟨inv', astep⟩ := good_step w inv (Paxos.reachable_invariant _ areach) i inp al
      exact ⟨inv', .step areach (by simpa [Paxos.module, Reactive.Module.step] using astep)⟩

/-- Refinement: every reachable deployment state interprets as a reachable
    state of the abstract single-decree Paxos model. -/
theorem refinement (w : World) (h : Reactive.Reachable module w) :
    Reactive.Reachable Paxos.module (abs w) := (reachable_inv w h).2

/-- A replica's decision is backed by a quorum of acceptor votes. -/
theorem decided_chosen (w : World) (h : Reactive.Reachable module w) (k : Rid) (v : U64)
    (hd : (w.node k).decided = .Some v) : ∃ b, Paxos.Chosen (abs w) b v.val := by
  obtain ⟨q, b, hq⟩ := ((reachable_inv w h).1.1 k).decided v hd
  exact ⟨b, q, hq⟩

/-- Agreement: no two replicas ever decide different values. -/
def Agreement (w : World) : Prop :=
  ∀ i j u v, (w.node i).decided = .Some u → (w.node j).decided = .Some v → u = v

theorem agreement : ∀ w, Reactive.Reachable module w → Agreement w := by
  intro w h i j u v hu hv
  obtain ⟨b, hb⟩ := decided_chosen w h i u hu
  obtain ⟨c, hc⟩ := decided_chosen w h j v hv
  exact UScalar.eq_of_val_eq (Paxos.safety _ (refinement w h) b c _ _ hb hc)

/-- Only a client submission produces a `Request` message. -/
theorem request_only_from_submit (n : Node) (inp : Input) (s : Send) (v : U64)
    (h : (handleS n inp).1 = .Some s) (hm : s.msg = .Request v) : inp = .Submit v := by
  cases inp with
  | Submit x => simp [handleS] at h; subst h; simp at hm; rw [hm]
  | Tick =>
    simp only [handleS, tickS] at h
    split at h
    · split at h
      · cases h
      · rcases start_cases n with ⟨_, e⟩ | ⟨_, e, _⟩ <;> rw [e] at h <;> cases h <;> cases hm
    · split at h
      · rcases start_cases n with ⟨_, e⟩ | ⟨_, e, _⟩ <;> rw [e] at h <;> cases h <;> cases hm
      · split at h <;> cases h <;> cases hm
  | Deliver src msg =>
    exfalso
    simp only [handleS, deliverS] at h
    split at h
    · cases h
    cases msg <;> simp only [onPrepareS, onPromiseS, onAcceptS, onAcceptedS] at h <;>
      (repeat' split at h) <;> (try simp only [Option.some.injEq, reduceCtorEq] at h) <;>
      (try subst h) <;> simp_all

/-- Validity: every decided value was submitted by a client. -/
def Validity (w : World) : Prop :=
  ∀ k v, (w.node k).decided = .Some v → ∃ p, w.net p ∧ p.send.msg = .Request v

theorem validity : ∀ w, Reactive.Reachable module w → Validity w := by
  intro w h k v hd
  obtain ⟨inv, areach⟩ := reachable_inv w h
  obtain ⟨b, q, hq⟩ := decided_chosen w h k v hd
  have ainv := Paxos.reachable_invariant _ areach
  obtain ⟨p, hp, vt, hmsg, _, hval⟩ := ainv.voted _ _ _ (hq q.first (.inl rfl))
  have pi := inv.2 p hp
  simp only [PacketInv, hmsg] at pi
  obtain ⟨_, _, _, _, r, hr, hreq⟩ := pi
  exact ⟨r, hr, (UScalar.eq_of_val_eq hval) ▸ hreq⟩

#print axioms agreement
#print axioms validity
#print axioms refinement
end PaxosSystem
