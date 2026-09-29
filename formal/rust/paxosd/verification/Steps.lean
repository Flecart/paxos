import UserVerification.Refinement

/- Each input handled by the extracted code preserves the concrete invariant
   and is a single abstract Paxos step (or a stutter). -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

set_option linter.unusedSectionVars false

variable {N : Nat} [Cluster N]

def Good (w w' : World N) : Prop := Inv w' ∧ PaxosN.Step N (abs w) (abs w')

theorem abs_after (w : World N) (i : Fin N) (o : Opt Send) (n' : Node) :
    (∀ a, (abs (w.after i (o, n'))).promised a = PaxosN.put (abs w).promised i n'.promised.val a) ∧
    (∀ a, (abs (w.after i (o, n'))).accepted a = PaxosN.put (abs w).accepted i (snap n'.accepted) a) ∧
    (∀ a c x, (abs (w.after i (o, n'))).promises a c x ↔ (abs w).promises a c x ∨
      ∃ s, o = .Some s ∧ a = i ∧ ∃ y z, s.msg = .Promise y z ∧ y.val = c ∧ snap z = x) ∧
    (∀ c v, (abs (w.after i (o, n'))).proposals c v ↔ (abs w).proposals c v ∨
      ∃ s, o = .Some s ∧ ∃ vt : Vote, s.msg = .Accept vt ∧ vt.ballot.val = c ∧ vt.value.val = v) ∧
    (∀ a c v, (abs (w.after i (o, n'))).votes a c v ↔ (abs w).votes a c v ∨
      ∃ s, o = .Some s ∧ a = i ∧ ∃ vt : Vote, s.msg = .Accepted vt ∧ vt.ballot.val = c ∧
        vt.value.val = v) := by
  refine ⟨fun a => ?_, fun a => ?_, fun a c x => ?_, fun c v => ?_, fun a c v => ?_⟩
  · simp only [abs, after_node, PaxosN.put]; split <;> rfl
  · simp only [abs, after_node, PaxosN.put]; split <;> rfl
  · simp only [abs, after_net]; constructor
    · rintro ⟨p, hp | ⟨hs, hi⟩, rest⟩
      · exact .inl ⟨p, hp, rest⟩
      · obtain ⟨hsrc, rest⟩ := rest; exact .inr ⟨p.send, hs, hi ▸ hsrc.symm, rest⟩
    · rintro (⟨p, hp, rest⟩ | ⟨s, hs, rfl, rest⟩)
      · exact ⟨p, .inl hp, rest⟩
      · exact ⟨⟨a, s⟩, .inr ⟨hs, rfl⟩, rfl, rest⟩
  · simp only [abs, after_net]; constructor
    · rintro ⟨p, hp | ⟨hs, _⟩, rest⟩
      · exact .inl ⟨p, hp, rest⟩
      · exact .inr ⟨p.send, hs, rest⟩
    · rintro (⟨p, hp, rest⟩ | ⟨s, hs, rest⟩)
      · exact ⟨p, .inl hp, rest⟩
      · exact ⟨⟨i, s⟩, .inr ⟨hs, rfl⟩, rest⟩
  · simp only [abs, after_net]; constructor
    · rintro ⟨p, hp | ⟨hs, hi⟩, rest⟩
      · exact .inl ⟨p, hp, rest⟩
      · obtain ⟨hsrc, rest⟩ := rest; exact .inr ⟨p.send, hs, hi ▸ hsrc.symm, rest⟩
    · rintro (⟨p, hp, rest⟩ | ⟨s, hs, rfl, rest⟩)
      · exact ⟨p, .inl hp, rest⟩
      · exact ⟨⟨a, s⟩, .inr ⟨hs, rfl⟩, rfl, rest⟩

theorem good_noop (w : World N) (inv : Inv w) (i : Fin N) :
    Good w (w.after i (.None, w.node i)) := by
  rw [after_noop]; exact ⟨inv, .idle⟩

theorem good_dup (w : World N) (inv : Inv w) (i : Fin N) (s : Send) (h : w.net ⟨i, s⟩) :
    Good w (w.after i (.Some s, w.node i)) := by
  rw [after_dup w i s h]; exact ⟨inv, .idle⟩

/-- Replica state unchanged, and a new packet that the abstract model ignores. -/
theorem good_hidden (w : World N) (inv : Inv w) (i : Fin N) (s : Send) (hs : Hidden s.msg)
    (hpkt : PacketInv (w.after i (.Some s, w.node i)) ⟨i, s⟩) :
    Good w (w.after i (.Some s, w.node i)) := by
  refine ⟨inv_after w inv i _ _ (Grows.refl _) ?_ (fun s' e => by cases e; exact hpkt), ?_⟩
  · exact (inv.1 i).mono (after_self _ _ _) (net_grows w i _) (top_grows w i _ (Grows.refl _))
  · rw [abs_hidden w i _ _ rfl rfl (fun s' e => by cases e; exact .inl hs)]; exact .idle

theorem good_submit (w : World N) (inv : Inv w) (i : Fin N) (v : U64) :
    Good w (w.after i (handleS (w.node i) (.Submit v))) :=
  good_hidden w inv i _ trivial rfl

/-! ## Timer -/

theorem own_mod (f : Nat) (i : Fin N) : ((f / N + 1) * N + i.val) % N = i.val := by
  rw [Nat.add_comm, Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt i.isLt]

theorem majority_zero (n : U8) : ¬ Majority 0 n := by unfold Majority; omega

theorem good_start (w : World N) (inv : Inv w) (i : Fin N) (hv : (w.node i).value ≠ .None) :
    Good w (w.after i (startS (w.node i))) := by
  have old := inv.1 i
  have g := start_grows (w.node i)
  rcases start_cases (w.node i) with ⟨_, h⟩ | ⟨hpos, _, ho, hb, he⟩
  · rw [h]; exact good_noop w inv i
  have hgt := start_ballot_gt _ hpos hb
  have hfl : (w.node i).ballot.val ≤ floorOf (w.node i) := by unfold floorOf; omega
  generalize startS (w.node i) = r at ho hb he g hgt
  obtain ⟨o, n'⟩ := r
  simp only at ho hb he g hgt
  subst ho
  generalize n'.ballot = b at hb he hgt ⊢
  subst he
  have hbv : b.val = (floorOf (w.node i) / N + 1) * N + i.val := by
    rw [hb, old.size, old.id, rid_val, u8_val]
  have tg := top_grows w i (.Some ⟨.All, .Prepare b⟩, fresh (w.node i) b) g
  have hnew : ∀ (j : Fin N) p, pslot (w.node i) j = .Some p → p.ballot.val < b.val := by
    intro j p h; have := (old.slot_le j p h).2; omega
  refine ⟨inv_after w inv i _ _ g ?_ ?_, ?_⟩
  · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
      simp only [after_self, fresh]
    · exact old.id
    · exact old.size
    · exact old.plen
    · exact old.vlen
    · right; rw [hbv]; exact own_mod _ i
    · intro _; exact ⟨hv, sent_new _ _ _ _⟩
    · intro v h; cases h
    · intro j p h
      exact ⟨(old.slot_le j p h).1, le_of_lt (hnew j p (by simpa [pslot] using h))⟩
    · intro j p h e
      have := hnew j p (by simpa [pslot] using h); rw [e] at this; omega
    · intro _
      rw [count_promises_zero (w.node i) old.plen b (fun j p h e => by
        have := hnew j p h; rw [e] at this; omega)]
      exact majority_zero _
    · exact le_trans old.promised_top tg
    · exact le_trans old.seen_top tg
    · intro v h; obtain ⟨p, hp, hm⟩ := old.request v h; exact ⟨p, .inl hp, hm⟩
    · intro j vt h
      obtain ⟨p, hp, rest⟩ := old.votes j vt (by simpa [vslot] using h)
      exact ⟨p, .inl hp, rest⟩
    · exact old.undecided
    · intro v h
      obtain ⟨q, c, hq, hm⟩ := old.decided v h
      exact ⟨q, c, hq, fun a ha => abs_votes_grow w i _ (hm a ha)⟩
  · intro s e; cases e
    simp only [PacketInv, after_self, fresh]
    exact ⟨by omega, by rw [hbv]; exact own_mod _ i, le_refl _⟩
  · rw [abs_hidden w i (.Some ⟨.All, .Prepare b⟩) (fresh (w.node i) b) rfl rfl
      (fun s e => by cases e; exact .inl trivial)]
    exact .idle

theorem good_tick (w : World N) (inv : Inv w) (i : Fin N) :
    Good w (w.after i (handleS (w.node i) .Tick)) := by
  have old := inv.1 i
  simp only [handleS, tickS]
  split
  · cases hv : (w.node i).value
    · exact good_noop w inv i
    · exact good_start w inv i (by simp [hv])
  · rename_i hb
    have hb' : (w.node i).ballot.val ≠ 0 := fun e => hb (UScalar.eq_of_val_eq (by simpa using e))
    split
    · exact good_start w inv i (old.started hb').1
    · cases hp : (w.node i).proposal
      · exact good_dup w inv i _ (old.started hb').2
      · exact good_dup w inv i _ (old.proposed _ hp).2

/-! ## Message delivery -/

theorem deliver_rid (n : Node) (hn : n.n = u8 N) (j : Fin N) (msg : Msg) :
    deliverS n (rid j) msg =
      match msg with
      | .Request v =>
        match n.value with
        | .None => (.None, { n with value := .Some v })
        | .Some _ => (.None, n)
      | .Prepare b => onPrepareS n (rid j) b
      | .Promise b acc => onPromiseS n (rid j) b acc
      | .Accept v => onAcceptS n (rid j) v
      | .Accepted v => onAcceptedS n (rid j) v
      | .Nack _ q => if n.max_seen < q then (.None, { n with max_seen := q }) else (.None, n) := by
  unfold deliverS
  rw [if_neg (by rw [hn, u8_val, rid_val]; exact Nat.not_le.mpr j.isLt)]
  cases msg <;> rfl

theorem owner_of (b : U64) (j : Fin N) (h : b.val % N = j.val) : owner (N := N) b = j := Fin.ext h

theorem good_request (w : World N) (inv : Inv w) (i : Fin N) (p : Packet N) (hp : w.net p)
    (v : U64) (hm : p.send.msg = .Request v) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Request v))) := by
  have old := inv.1 i
  rw [deliver_rid _ old.size]
  cases hv : (w.node i).value
  · simp only []
    have g : Grows (w.node i) { w.node i with value := .Some v } :=
      grows_of rfl rfl rfl (le_refl _) (le_refl _) (fun _ e => by rw [hv] at e; cases e) rfl
        rfl rfl (fun _ e => e)
    have tg := top_grows w i (.None, { w.node i with value := .Some v }) g
    refine ⟨inv_after w inv i _ _ g ?_ (fun s e => by cases e), ?_⟩
    · apply old.congr (net_grows w i _) <;> simp only [after_self]
      · simp
      · intro x e; simp only [Option.some.injEq] at e; subst e; exact ⟨p, .inl hp, hm⟩
      · exact le_trans old.promised_top tg
      · exact le_trans old.seen_top tg
    · rw [abs_hidden w i .None { w.node i with value := .Some v } rfl rfl (fun s e => by cases e)]
      exact .idle
  · exact good_noop w inv i

theorem good_nack (w : World N) (inv : Inv w) (i : Fin N) (p : Packet N) (hp : w.net p)
    (x q : U64) (hm : p.send.msg = .Nack x q) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Nack x q))) := by
  have old := inv.1 i
  have hq : q.val ≤ top w := by have := inv.2 p hp; simp only [PacketInv, hm] at this; exact this
  rw [deliver_rid _ old.size]
  simp only []
  split
  · rename_i hlt; rw [UScalar.lt_equiv] at hlt
    have g : Grows (w.node i) { w.node i with max_seen := q } :=
      grows_of rfl rfl rfl (le_refl _) (by simp; omega) (fun _ e => e) rfl rfl rfl (fun _ e => e)
    have tg := top_grows w i (.None, { w.node i with max_seen := q }) g
    refine ⟨inv_after w inv i _ _ g ?_ (fun s e => by cases e), ?_⟩
    · apply old.congr (net_grows w i _) <;> simp only [after_self]
      · exact id
      · intro x e; obtain ⟨p, hp, h⟩ := old.request x e; exact ⟨p, .inl hp, h⟩
      · exact le_trans old.promised_top tg
      · exact le_trans hq tg
    · rw [abs_hidden w i .None { w.node i with max_seen := q } rfl rfl (fun s e => by cases e)]
      exact .idle
  · exact good_noop w inv i

theorem good_prepare (w : World N) (inv : Inv w) (i : Fin N) (p : Packet N) (hp : w.net p)
    (b : U64) (hm : p.send.msg = .Prepare b) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Prepare b))) := by
  have old := inv.1 i
  have pk := inv.2 p hp
  simp only [PacketInv, hm] at pk
  obtain ⟨_, hmod, hle⟩ := pk
  have hbt : b.val ≤ top w := le_trans hle (le_top w _)
  rw [deliver_rid _ old.size]
  simp only [onPrepareS]
  split
  · rename_i hlt; rw [UScalar.lt_equiv] at hlt
    have g : Grows (w.node i) { w.node i with promised := b } :=
      grows_of rfl rfl rfl (by simp; omega) (le_refl _) (fun _ e => e) rfl rfl rfl (fun _ e => e)
    have tg := top_grows w i (.Some ⟨.To (rid p.src), .Promise b (w.node i).accepted⟩,
      { w.node i with promised := b }) g
    refine ⟨inv_after w inv i _ _ g ?_ ?_, ?_⟩
    · apply old.congr (net_grows w i _) <;> simp only [after_self]
      · exact id
      · intro x e; obtain ⟨p, hp, h⟩ := old.request x e; exact ⟨p, .inl hp, h⟩
      · exact le_trans hbt tg
      · exact le_trans old.seen_top tg
    · intro s e; cases e; simp only [PacketInv, owner_of b p.src hmod]
    · obtain ⟨e1, e2, e3, e4, e5⟩ := abs_after w i
        (.Some ⟨.To (rid p.src), .Promise b (w.node i).accepted⟩) { w.node i with promised := b }
      have : abs (w.after i (.Some ⟨.To (rid p.src), .Promise b (w.node i).accepted⟩,
          { w.node i with promised := b })) = PaxosN.prepare (abs w) i b.val := by
        apply state_ext
        · intro a; rw [e1]; rfl
        · intro a; rw [e2]; simp [PaxosN.prepare, PaxosN.put, abs]; intro h; subst h; rfl
        · intro a c x; rw [e3]; simp only [PaxosN.prepare]
          apply or_congr_right
          constructor
          · rintro ⟨s, hs, rfl, y, z, hmsg, hy, hz⟩
            cases hs; simp only [Msg.Promise.injEq] at hmsg; obtain ⟨rfl, rfl⟩ := hmsg
            exact ⟨rfl, hy.symm, by rw [← hz]; rfl⟩
          · rintro ⟨rfl, rfl, rfl⟩
            exact ⟨_, rfl, rfl, b, (w.node a).accepted, rfl, rfl, rfl⟩
        · intro c v; rw [e4]; simp [PaxosN.prepare]
        · intro a c v; rw [e5]; simp [PaxosN.prepare]
      rw [this]
      exact .prepare i b.val (by simpa [abs] using hlt)
  · have hq : (w.node i).promised.val ≤ top w := old.promised_top
    exact good_hidden w inv i _ trivial (by
      simp only [PacketInv]; exact le_trans hq (top_grows w i _ (Grows.refl _)))

theorem good_accept (w : World N) (inv : Inv w) (i : Fin N) (p : Packet N) (hp : w.net p)
    (vt : Vote) (hm : p.send.msg = .Accept vt) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Accept vt))) := by
  have old := inv.1 i
  have pk := inv.2 p hp
  simp only [PacketInv, hm] at pk
  obtain ⟨_, _, hle, _, _⟩ := pk
  have hbt : vt.ballot.val ≤ top w := le_trans hle (le_top w _)
  rw [deliver_rid _ old.size]
  simp only [onAcceptS]
  split
  · rename_i hlt; rw [UScalar.le_equiv] at hlt
    let n' : Node := { w.node i with promised := vt.ballot, accepted := .Some vt }
    have g : Grows (w.node i) n' :=
      grows_of rfl rfl rfl (by simp [n']; omega) (le_refl _) (fun _ e => e) rfl rfl rfl
        (fun _ e => e)
    have tg := top_grows w i (.Some ⟨.All, .Accepted vt⟩, n') g
    refine ⟨inv_after w inv i _ _ g ?_ ?_, ?_⟩
    · apply old.congr (net_grows w i _) <;> simp only [after_self]
      · exact id
      · intro x e; obtain ⟨p, hp, h⟩ := old.request x e; exact ⟨p, .inl hp, h⟩
      · exact le_trans hbt tg
      · exact le_trans old.seen_top tg
    · intro s e; cases e; simp [PacketInv]
    · obtain ⟨e1, e2, e3, e4, e5⟩ := abs_after w i (.Some ⟨.All, .Accepted vt⟩) n'
      have : abs (w.after i (.Some ⟨.All, .Accepted vt⟩, n')) =
          PaxosN.cast (abs w) i vt.ballot.val vt.value.val := by
        apply state_ext
        · intro a; rw [e1]; rfl
        · intro a; rw [e2]; rfl
        · intro a c x; rw [e3]; simp [PaxosN.cast]
        · intro c v; rw [e4]; simp [PaxosN.cast]
        · intro a c v; rw [e5]; simp only [PaxosN.cast]
          apply or_congr_right
          constructor
          · rintro ⟨s, hs, rfl, v', hmsg, hb, hv⟩
            cases hs; simp only [Msg.Accepted.injEq] at hmsg; subst hmsg
            exact ⟨rfl, hb.symm, hv.symm⟩
          · rintro ⟨rfl, rfl, rfl⟩
            exact ⟨_, rfl, rfl, vt, rfl, rfl, rfl⟩
      rw [this]
      exact .cast i vt.ballot.val vt.value.val ⟨p, hp, vt, hm, rfl, rfl⟩ (by simpa [abs] using hlt)
  · have hq : (w.node i).promised.val ≤ top w := old.promised_top
    exact good_hidden w inv i _ trivial (by
      simp only [PacketInv]; exact le_trans hq (top_grows w i _ (Grows.refl _)))

/-- Learner updates change only the vote vector and the decision. -/
theorem good_learner (w : World N) (inv : Inv w) (i : Fin N) (n' : Node)
    (g : Grows (w.node i) n')
    (b1 : n'.ballot = (w.node i).ballot) (b2 : n'.proposal = (w.node i).proposal)
    (b3 : n'.value = (w.node i).value) (b4 : n'.id = (w.node i).id)
    (b5 : n'.promised = (w.node i).promised) (b6 : n'.accepted = (w.node i).accepted)
    (b7 : n'.max_seen = (w.node i).max_seen) (b8 : n'.promises = (w.node i).promises)
    (b9 : n'.n = (w.node i).n) (vlen : (items n'.votes).length = N)
    (votes : ∀ (j : Fin N) x, vslot n' j = .Some x →
      ∃ q, w.net q ∧ q.src = j ∧ q.send.msg = .Accepted x)
    (und : n'.decided = .None → ∀ v, ¬ Majority (countVotesS (items n'.votes) v) n'.n)
    (dec : ∀ x, n'.decided = .Some x →
      ∃ (q : Finset (Fin N)) (c : Nat), PaxosN.IsQuorum N q ∧ ∀ a ∈ q, (abs w).votes a c x.val) :
    Good w (w.after i (.None, n')) := by
  have old := inv.1 i
  have tg := top_grows w i (.None, n') g
  have eps : ∀ j : Fin N, pslot n' j = pslot (w.node i) j := by intro j; simp [pslot, b8]
  refine ⟨inv_after w inv i _ _ g ?_ (fun s e => by cases e), ?_⟩
  · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
      simp only [after_self]
    · rw [b4]; exact old.id
    · rw [b9]; exact old.size
    · rw [b8]; exact old.plen
    · exact vlen
    · rw [b1]; exact old.own
    · rw [b1, b3]; intro hb; exact ⟨(old.started hb).1, .inl (old.started hb).2⟩
    · rw [b1, b2]; intro v h; exact ⟨(old.proposed v h).1, .inl (old.proposed v h).2⟩
    · intro j y h; rw [eps] at h; rw [b1]; exact old.slot_le j y h
    · intro j y h hy; rw [eps] at h; rw [b1] at hy
      obtain ⟨q, hq, rest⟩ := old.slots j y h hy; exact ⟨q, .inl hq, rest⟩
    · rw [b2, b8, b1, b9]; exact old.pending
    · rw [b5]; exact le_trans old.promised_top tg
    · rw [b7]; exact le_trans old.seen_top tg
    · rw [b3]; intro v h; obtain ⟨q, hq, rest⟩ := old.request v h; exact ⟨q, .inl hq, rest⟩
    · intro j x h; obtain ⟨q, hq, rest⟩ := votes j x h; exact ⟨q, .inl hq, rest⟩
    · exact und
    · intro x h
      obtain ⟨q, c, hq, hm⟩ := dec x h
      exact ⟨q, c, hq, fun a ha => abs_votes_grow w i _ (hm a ha)⟩
  · rw [abs_hidden w i .None n' b5 b6 (fun s e => by cases e)]; exact .idle

theorem majority_mono {a b : Nat} (n : U8) (h : a ≤ b) (hb : ¬ Majority b n) : ¬ Majority a n := by
  unfold Majority at *; omega

theorem good_accepted (w : World N) (inv : Inv w) (i : Fin N) (p : Packet N) (hp : w.net p)
    (vt : Vote) (hm : p.send.msg = .Accepted vt) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Accepted vt))) := by
  have old := inv.1 i
  have hs : (rid p.src).val < (items (w.node i).votes).length := by
    rw [old.vlen, rid_val]; exact p.src.isLt
  have g := accepted_grows (w.node i) (rid p.src) vt
  rw [deliver_rid _ old.size]
  simp only []
  rw [accepted_eq _ _ _ hs] at g ⊢
  have llen : (items (learnS (w.node i) (rid p.src) vt)).length = N := by
    rw [learn_length]; exact old.vlen
  have mvotes : ∀ (j : Fin N) x, slot (learnS (w.node i) (rid p.src) vt) j.val = .Some x →
      ∃ q, w.net q ∧ q.src = j ∧ q.send.msg = .Accepted x := by
    intro j x h
    rw [learn_slot _ _ _ hs] at h
    split at h
    · rename_i hj; simp only [Option.some.injEq] at h; subst h
      exact ⟨p, hp, Fin.ext (by rw [hj.2, rid_val]), hm⟩
    · exact old.votes j x h
  have lle : ∀ v', v' ≠ vt → countVotesS (items (learnS (w.node i) (rid p.src) vt)) v' ≤
      countVotesS (items (w.node i).votes) v' := fun v' hv => count_learn_le _ _ _ _ hv hs
  generalize learnS (w.node i) (rid p.src) vt = L at g llen mvotes lle ⊢
  cases hd : (w.node i).decided
  · simp only [hd] at g ⊢
    by_cases hmaj : Majority (countVotesS (items L) vt) (w.node i).n
    · rw [if_pos hmaj] at g ⊢
      refine good_learner w inv i _ g rfl rfl rfl rfl rfl rfl rfl rfl rfl llen
        (fun j x h => mvotes j x h) (fun h => by cases h) ?_
      intro x h
      simp only [Option.some.injEq] at h; subst h
      have hq : PaxosN.IsQuorum N (voters (N := N) { w.node i with votes := L } vt) := by
        have := (majority_iff _).mp (by rw [← old.size]; exact hmaj)
        rw [count_votes_card { w.node i with votes := L } llen] at this
        exact this
      refine ⟨_, vt.ballot.val, hq, fun a ha => ?_⟩
      obtain ⟨y, hy, hyb, hyv⟩ := (mem_voters _ vt a).mp ha
      obtain ⟨pk, hpk, hsrc, hmsg⟩ := mvotes a y hy
      exact ⟨pk, hpk, hsrc, y, hmsg, by rw [hyb], by rw [hyv]⟩
    · rw [if_neg hmaj] at g ⊢
      refine good_learner w inv i _ g rfl rfl rfl rfl rfl rfl rfl rfl rfl llen
        (fun j x h => mvotes j x h) ?_ (fun x h => by cases h)
      intro _ v'
      by_cases hv : v' = vt
      · subst hv; exact hmaj
      · exact majority_mono _ (lle v' hv) (old.undecided hd v')
  · simp only [hd] at g ⊢
    refine good_learner w inv i _ g rfl rfl rfl rfl rfl rfl rfl rfl rfl llen
      (fun j x h => mvotes j x h) (fun h => by cases h) ?_
    intro x h; exact old.decided x (by rw [hd]; exact h)

theorem put_same {α : Type} (f : Fin N → α) (a : Fin N) : PaxosN.put f a (f a) = f := by
  funext i; by_cases hi : i = a <;> simp [PaxosN.put, hi]

/-- A value reported in a promise snapshot was proposed, hence requested by a client. -/
theorem request_of_snapshot (w : World N) (inv : Inv w) (ainv : PaxosN.Invariant (abs w))
    (pk : Packet N) (hpk : w.net pk) (c : U64) (a : Vote)
    (hm : pk.send.msg = .Promise c (.Some a)) :
    ∃ q, w.net q ∧ q.send.msg = .Request a.value := by
  have hpr : (abs w).promises pk.src c.val (some (a.ballot.val, a.value.val)) :=
    ⟨pk, hpk, rfl, c, .Some a, hm, rfl, rfl⟩
  obtain ⟨_, _, hsnap⟩ := ainv.snapshots _ _ _ hpr
  obtain ⟨_, hv⟩ := hsnap _ rfl
  obtain ⟨p', hp', vt, hmsg, _, hval⟩ := ainv.voted _ _ _ hv
  have pi := inv.2 p' hp'
  simp only [PacketInv, hmsg] at pi
  obtain ⟨_, _, _, _, q, hq, hr⟩ := pi
  have : vt.value = a.value := UScalar.eq_of_val_eq hval
  exact ⟨q, hq, this ▸ hr⟩

/-- The abstract snapshot carried by the promise a replica recorded for acceptor `j`. -/
def snapAt (n : Node) (j : Fin N) : Option PaxosN.Vote :=
  match pslot n j with
  | .Some p => snap p.accepted
  | .None => none

theorem getElem?_of_slot {α : Type} (s : RVec (Opt α)) (j : Nat) (x : α)
    (h : slot s j = .Some x) : (items s)[j]? = some (.Some x) := by
  unfold slot at h
  cases e : (items s)[j]? with
  | none => rw [e] at h; cases h
  | some y => rw [e] at h; simp only [Option.getD_some] at h; rw [h]

/-- Phase 2 start: a majority of promises for the current ballot has been
    recorded, and the replica proposes `x` (chosen as `SelectOK` requires). -/
theorem good_propose (w : World N) (inv : Inv w) (i : Fin N) (ps : RVec (Opt Promise)) (x : U64)
    (hpr : (w.node i).proposal = .None) (hb0 : (w.node i).ballot.val ≠ 0)
    (base : Grows (w.node i) { w.node i with promises := ps })
    (mslot_le : ∀ (j : Fin N) pr, slot ps j.val = .Some pr →
      0 < pr.ballot.val ∧ pr.ballot.val ≤ (w.node i).ballot.val)
    (mslots : ∀ (j : Fin N) pr, slot ps j.val = .Some pr → pr.ballot = (w.node i).ballot →
      ∃ q, w.net q ∧ q.src = j ∧ q.send.msg = .Promise pr.ballot pr.accepted)
    (hmaj : Majority (countPromisesS (items ps) (w.node i).ballot) (w.node i).n)
    (hsel : PaxosN.SelectOK (promisers (N := N) { w.node i with promises := ps } (w.node i).ballot)
      (snapAt { w.node i with promises := ps }) x.val)
    (hreq : ∃ q, w.net q ∧ q.send.msg = .Request x) :
    Good w (w.after i (.Some ⟨.All, .Accept ⟨(w.node i).ballot, x⟩⟩,
      { w.node i with proposal := .Some x, promises := ps })) := by
  have old := inv.1 i
  have own : (w.node i).ballot.val % N = i.val := old.own.resolve_left hb0
  have plen : (items ps).length = N := base.plen.trans old.plen
  have g : Grows (w.node i) { w.node i with proposal := .Some x, promises := ps } :=
    ⟨rfl, rfl, base.plen, rfl, le_refl _, le_refl _, le_refl _, fun _ h => h,
      fun _ v h => (by rw [hpr] at h; cases h), base.slot, base.vote, fun _ h => h⟩
  have tg := top_grows w i (.Some ⟨.All, .Accept ⟨(w.node i).ballot, x⟩⟩,
    { w.node i with proposal := .Some x, promises := ps }) g
  refine ⟨inv_after w inv i _ _ g ?_ ?_, ?_⟩
  · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
      simp only [after_self]
    · exact old.id
    · exact old.size
    · exact plen
    · exact old.vlen
    · exact old.own
    · intro hb; exact ⟨(old.started hb).1, .inl (old.started hb).2⟩
    · intro v' h; simp only [Option.some.injEq] at h; subst h; exact ⟨hb0, sent_new _ _ _ _⟩
    · intro j y h; exact mslot_le j y h
    · intro j y h hy; obtain ⟨q, hq, rest⟩ := mslots j y h hy; exact ⟨q, .inl hq, rest⟩
    · intro h; cases h
    · exact le_trans old.promised_top tg
    · exact le_trans old.seen_top tg
    · intro v h; obtain ⟨q, hq, rest⟩ := old.request v h; exact ⟨q, .inl hq, rest⟩
    · intro j y h; obtain ⟨q, hq, rest⟩ := old.votes j y h; exact ⟨q, .inl hq, rest⟩
    · exact old.undecided
    · intro y h
      obtain ⟨q, c, hq, hm'⟩ := old.decided y h
      exact ⟨q, c, hq, fun a ha => abs_votes_grow w i _ (hm' a ha)⟩
  · intro s e; cases e
    simp only [PacketInv, after_self]
    obtain ⟨q, hq, hmq⟩ := hreq
    exact ⟨hb0, own, le_refl _, by simp, q, .inl hq, hmq⟩
  · have fresh : ∀ v', ¬ (abs w).proposals (w.node i).ballot.val v' := by
      rintro v' ⟨pk, hpk, vt, hmsg, hb, _⟩
      have pi := inv.2 pk hpk
      simp only [PacketInv, hmsg] at pi
      obtain ⟨_, hmod, _, hprop, _⟩ := pi
      have hsrc : pk.src = i := Fin.ext (by rw [← hmod, ← own, hb])
      rw [hsrc] at hprop
      have heq : vt.ballot = (w.node i).ballot := UScalar.eq_of_val_eq hb
      rw [hprop heq] at hpr; cases hpr
    have hq : PaxosN.IsQuorum N
        (promisers (N := N) { w.node i with promises := ps } (w.node i).ballot) := by
      have := (majority_iff _).mp (by rw [← old.size]; exact hmaj)
      rw [count_promises_card { w.node i with promises := ps } plen] at this
      exact this
    have hprom : ∀ a ∈ promisers (N := N) { w.node i with promises := ps } (w.node i).ballot,
        (abs w).promises a (w.node i).ballot.val (snapAt { w.node i with promises := ps } a) := by
      intro a ha
      obtain ⟨pr, hpr', hb⟩ := (mem_promisers _ _ a).mp ha
      obtain ⟨pk, hpk, hsrc, hmsg⟩ := mslots a pr hpr' hb
      exact ⟨pk, hpk, hsrc, pr.ballot, pr.accepted, hmsg, by rw [hb], by simp [snapAt, hpr']⟩
    obtain ⟨a1, a2, a3, a4, a5⟩ := abs_after w i (.Some ⟨.All, .Accept ⟨(w.node i).ballot, x⟩⟩)
      { w.node i with proposal := .Some x, promises := ps }
    have heq : abs (w.after i (.Some ⟨.All, .Accept ⟨(w.node i).ballot, x⟩⟩,
        { w.node i with proposal := .Some x, promises := ps })) =
        PaxosN.propose (abs w) (w.node i).ballot.val x.val := by
      apply state_ext
      · intro a; rw [a1]
        show PaxosN.put (abs w).promised i ((abs w).promised i) a = _
        rw [put_same]; rfl
      · intro a; rw [a2]
        show PaxosN.put (abs w).accepted i ((abs w).accepted i) a = _
        rw [put_same]; rfl
      · intro a c y; rw [a3]; simp [PaxosN.propose]
      · intro c y; rw [a4]; simp only [PaxosN.propose]
        apply or_congr_right
        constructor
        · rintro ⟨s, hs, vt, hmsg, hb, hv'⟩
          cases hs; simp only [Msg.Accept.injEq] at hmsg; subst hmsg
          exact ⟨hb.symm, hv'.symm⟩
        · rintro ⟨rfl, rfl⟩; exact ⟨_, rfl, ⟨_, x⟩, rfl, rfl, rfl⟩
      · intro a c y; rw [a5]; simp [PaxosN.propose]
    rw [heq]
    exact .propose _ _ _ hq _ fresh hprom hsel

/-- The value a replica proposes after a promise majority: the value of the
    highest reported vote, or its own client value. -/
def chooseS (ps : List (Opt Promise)) (b : U64) (v : U64) : U64 :=
  match highestS ps b with
  | .None => v
  | .Some m => m.value

/-- `onPromiseS` for a promise for the current ballot at a replica with no
    proposal yet and a client value. -/
theorem promise_eq (n : Node) (src : U8) (acc : Opt Vote) (v : U64)
    (hb0 : n.ballot ≠ 0#u64) (hpr : n.proposal = .None) (hv : n.value = .Some v)
    (hs : src.val < (items n.promises).length) :
    onPromiseS n src n.ballot acc =
      if Majority (countPromisesS (items (setAt n.promises src.val (.Some ⟨n.ballot, acc⟩)))
          n.ballot) n.n then
        (.Some ⟨.All, .Accept ⟨n.ballot, chooseS (items (setAt n.promises src.val
            (.Some ⟨n.ballot, acc⟩))) n.ballot v⟩⟩,
          { n with proposal := .Some (chooseS (items (setAt n.promises src.val
            (.Some ⟨n.ballot, acc⟩))) n.ballot v),
                   promises := setAt n.promises src.val (.Some ⟨n.ballot, acc⟩) })
      else (.None, { n with promises := setAt n.promises src.val (.Some ⟨n.ballot, acc⟩) }) := by
  cases n
  simp only at hb0 hpr hv hs ⊢
  subst hpr hv
  unfold onPromiseS
  rw [if_neg (by simp), if_neg hb0]
  simp only []
  rw [if_neg (by omega)]
  split
  · unfold chooseS; split <;> (rename_i heq; rw [heq])
  · rfl

theorem good_promise (w : World N) (inv : Inv w) (ainv : PaxosN.Invariant (abs w)) (i : Fin N)
    (p : Packet N) (hp : w.net p) (b : U64) (acc : Opt Vote) (hm : p.send.msg = .Promise b acc) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Promise b acc))) := by
  have old := inv.1 i
  have hs : (rid p.src).val < (items (w.node i).promises).length := by
    rw [old.plen, rid_val]; exact p.src.isLt
  rw [deliver_rid _ old.size]
  simp only []
  by_cases h1 : b ≠ (w.node i).ballot
  · unfold onPromiseS; rw [if_pos h1]; exact good_noop w inv i
  have h1 : b = (w.node i).ballot := not_not.mp h1
  subst h1
  by_cases h2 : (w.node i).ballot = 0#u64
  · unfold onPromiseS; rw [if_neg (by simp), if_pos h2]; exact good_noop w inv i
  have hb0 : (w.node i).ballot.val ≠ 0 := fun e => h2 (UScalar.eq_of_val_eq (by simpa using e))
  cases hpr : (w.node i).proposal with
  | some x =>
    unfold onPromiseS; rw [if_neg (by simp), if_neg h2]; simp only [hpr]
    exact good_noop w inv i
  | none =>
  obtain ⟨v, hv⟩ : ∃ v, (w.node i).value = .Some v := by
    cases h : (w.node i).value
    · exact absurd h (old.started hb0).1
    · exact ⟨_, rfl⟩
  rw [promise_eq _ _ _ v h2 hpr hv hs]
  have base := record_grows (w.node i) (rid p.src) acc hs
  have mslot : ∀ j : Fin N, slot (setAt (w.node i).promises (rid p.src).val
      (.Some ⟨(w.node i).ballot, acc⟩)) j.val =
      if j = p.src then .Some ⟨(w.node i).ballot, acc⟩ else pslot (w.node i) j := by
    intro j; rw [slot_setAt _ _ _ _ hs, rid_val]; simp only [Fin.val_inj]; rfl
  have mslot_le : ∀ (j : Fin N) pr, slot (setAt (w.node i).promises (rid p.src).val
      (.Some ⟨(w.node i).ballot, acc⟩)) j.val = .Some pr →
      0 < pr.ballot.val ∧ pr.ballot.val ≤ (w.node i).ballot.val := by
    intro j pr h; rw [mslot] at h; split at h
    · simp only [Option.some.injEq] at h; subst h; exact ⟨by simp only []; omega, le_refl _⟩
    · exact old.slot_le j pr h
  have mslots : ∀ (j : Fin N) pr, slot (setAt (w.node i).promises (rid p.src).val
      (.Some ⟨(w.node i).ballot, acc⟩)) j.val = .Some pr → pr.ballot = (w.node i).ballot →
      ∃ q, w.net q ∧ q.src = j ∧ q.send.msg = .Promise pr.ballot pr.accepted := by
    intro j pr h hb; rw [mslot] at h; split at h
    · rename_i hj; simp only [Option.some.injEq] at h; subst h; subst hj; exact ⟨p, hp, rfl, hm⟩
    · exact old.slots j pr h hb
  generalize setAt (w.node i).promises (rid p.src).val (.Some ⟨(w.node i).ballot, acc⟩) = ps
    at base mslot_le mslots ⊢
  have plen : (items ps).length = N := base.plen.trans old.plen
  by_cases hmaj : Majority (countPromisesS (items ps) (w.node i).ballot) (w.node i).n
  · rw [if_pos hmaj]
    rcases hh : highestS (items ps) (w.node i).ballot with _ | mm
    · simp only [chooseS, hh]
      refine good_propose w inv i ps v hpr hb0 base mslot_le mslots hmaj (.inl ?_) (old.request v hv)
      intro a ha
      obtain ⟨pr, hpr', hb⟩ := (mem_promisers _ _ a).mp ha
      have := highestS_none _ _ hh a.val pr (getElem?_of_slot _ _ _ hpr') hb
      simp [snapAt, hpr', this, snap]
    · simp only [chooseS, hh]
      obtain ⟨⟨idx, hidx⟩, hmax⟩ := highestS_some _ _ _ hh
      have hlt : idx < (items ps).length := by
        by_contra hc; rw [List.getElem?_eq_none (by omega)] at hidx; cases hidx
      let a : Fin N := ⟨idx, plen ▸ hlt⟩
      have hslot : pslot { w.node i with promises := ps } a =
          .Some ⟨(w.node i).ballot, .Some mm⟩ := by
        show slot ps idx = _; simp [slot, hidx]
      obtain ⟨pk, hpk, _, hmsg⟩ := mslots a _ hslot rfl
      obtain ⟨rq, hrq, hmr⟩ := request_of_snapshot w inv ainv pk hpk _ mm hmsg
      refine good_propose w inv i ps mm.value hpr hb0 base mslot_le mslots hmaj
        (.inr ⟨a, (mem_promisers _ _ a).mpr ⟨_, hslot, rfl⟩, (mm.ballot.val, mm.value.val),
          by simp [snapAt, hslot, snap], rfl, ?_⟩) ⟨rq, hrq, hmr⟩
      intro c hc m' hm'
      obtain ⟨pr, hpr', hb⟩ := (mem_promisers _ _ c).mp hc
      simp only [snapAt, hpr'] at hm'
      cases hacc : pr.accepted with
      | none => rw [hacc] at hm'; cases hm'
      | some y =>
        rw [hacc] at hm'; simp only [snap, Option.some.injEq] at hm'; subst hm'
        exact hmax c.val pr y (getElem?_of_slot _ _ _ hpr') hb hacc
  · rw [if_neg hmaj]
    have tg := top_grows w i (.None, { w.node i with promises := ps }) base
    refine ⟨inv_after w inv i _ _ base ?_ (fun s e => by cases e), ?_⟩
    · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
        simp only [after_self]
      · exact old.id
      · exact old.size
      · exact plen
      · exact old.vlen
      · exact old.own
      · intro hb; exact ⟨(old.started hb).1, .inl (old.started hb).2⟩
      · intro v h; rw [hpr] at h; cases h
      · exact mslot_le
      · intro j y h hy; obtain ⟨q, hq, rest⟩ := mslots j y h hy; exact ⟨q, .inl hq, rest⟩
      · intro _; exact hmaj
      · exact le_trans old.promised_top tg
      · exact le_trans old.seen_top tg
      · intro v h; obtain ⟨q, hq, rest⟩ := old.request v h; exact ⟨q, .inl hq, rest⟩
      · intro j x h; obtain ⟨q, hq, rest⟩ := old.votes j x h; exact ⟨q, .inl hq, rest⟩
      · exact old.undecided
      · intro y h
        obtain ⟨q, c, hq, hm'⟩ := old.decided y h
        exact ⟨q, c, hq, fun a ha => abs_votes_grow w i _ (hm' a ha)⟩
    · rw [abs_hidden w i .None { w.node i with promises := ps } rfl rfl (fun s e => by cases e)]
      exact .idle

/-- Every permitted input preserves the invariant and refines one abstract step. -/
theorem good_step (w : World N) (inv : Inv w) (ainv : PaxosN.Invariant (abs w)) (i : Fin N)
    (inp : Input) (al : Allowed w i inp) : Good w (w.after i (handleS (w.node i) inp)) := by
  cases inp with
  | Submit v => exact good_submit w inv i v
  | Tick => exact good_tick w inv i
  | Deliver src msg =>
    obtain ⟨p, hp, _, rfl, rfl⟩ := al
    simp only [handleS]
    cases hm : p.send.msg with
    | Request v => exact good_request w inv i p hp v hm
    | Prepare b => exact good_prepare w inv i p hp b hm
    | Promise b acc => exact good_promise w inv ainv i p hp b acc hm
    | Accept vt => exact good_accept w inv i p hp vt hm
    | Accepted vt => exact good_accepted w inv i p hp vt hm
    | Nack x q => exact good_nack w inv i p hp x q hm

end PaxosSystem
