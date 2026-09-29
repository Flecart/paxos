import UserVerification.Refinement

/- Each input handled by the extracted code preserves the concrete invariant
   and is a single abstract Paxos step (or a stutter). -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

def Good (w w' : World) : Prop := Inv w' ∧ Paxos.Step (abs w) (abs w')

theorem abs_after (w : World) (i : Rid) (o : Opt Send) (n' : Node) :
    (∀ a, (abs (w.after i (o, n'))).promised a = Paxos.put (abs w).promised i n'.promised.val a) ∧
    (∀ a, (abs (w.after i (o, n'))).accepted a = Paxos.put (abs w).accepted i (snap n'.accepted) a) ∧
    (∀ a c x, (abs (w.after i (o, n'))).promises a c x ↔ (abs w).promises a c x ∨
      ∃ s, o = .Some s ∧ a = i ∧ ∃ y z, s.msg = .Promise y z ∧ y.val = c ∧ snap z = x) ∧
    (∀ c v, (abs (w.after i (o, n'))).proposals c v ↔ (abs w).proposals c v ∨
      ∃ s, o = .Some s ∧ ∃ vt : Vote, s.msg = .Accept vt ∧ vt.ballot.val = c ∧ vt.value.val = v) ∧
    (∀ a c v, (abs (w.after i (o, n'))).votes a c v ↔ (abs w).votes a c v ∨
      ∃ s, o = .Some s ∧ a = i ∧ ∃ vt : Vote, s.msg = .Accepted vt ∧ vt.ballot.val = c ∧
        vt.value.val = v) := by
  refine ⟨fun a => ?_, fun a => ?_, fun a c x => ?_, fun c v => ?_, fun a c v => ?_⟩
  · simp only [abs, after_node, Paxos.put]; split <;> rfl
  · simp only [abs, after_node, Paxos.put]; split <;> rfl
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

theorem good_noop (w : World) (inv : Inv w) (i : Rid) : Good w (w.after i (.None, w.node i)) := by
  rw [after_noop]; exact ⟨inv, .idle⟩

theorem good_dup (w : World) (inv : Inv w) (i : Rid) (s : Send) (h : w.net ⟨i, s⟩) :
    Good w (w.after i (.Some s, w.node i)) := by
  rw [after_dup w i s h]; exact ⟨inv, .idle⟩

/-- Replica state unchanged, and a new packet that the abstract model ignores. -/
theorem good_hidden (w : World) (inv : Inv w) (i : Rid) (s : Send) (hs : Hidden s.msg)
    (hpkt : PacketInv (w.after i (.Some s, w.node i)) ⟨i, s⟩) :
    Good w (w.after i (.Some s, w.node i)) := by
  refine ⟨inv_after w inv i _ _ (Grows.refl _) ?_ (fun s' e => by cases e; exact hpkt), ?_⟩
  · exact (inv.1 i).mono (after_self _ _ _) (net_grows w i _) (top_grows w i _ (Grows.refl _))
  · rw [abs_hidden w i _ _ rfl rfl (fun s' e => by cases e; exact .inl hs)]; exact .idle

theorem good_submit (w : World) (inv : Inv w) (i : Rid) (v : U64) :
    Good w (w.after i (handleS (w.node i) (.Submit v))) :=
  good_hidden w inv i _ trivial rfl

/-! ## Timer -/

theorem good_start (w : World) (inv : Inv w) (i : Rid) (hv : (w.node i).value ≠ .None) :
    Good w (w.after i (startS (w.node i))) := by
  have old := inv.1 i
  have g := start_grows (w.node i)
  rcases start_cases (w.node i) with ⟨_, h⟩ | ⟨hl, ho, hb, he⟩
  · rw [h]; exact good_noop w inv i
  generalize startS (w.node i) = r at ho hb he g
  obtain ⟨o, n'⟩ := r
  simp only at ho hb he g
  subst ho
  generalize n'.ballot = b at hb he ⊢
  subst he
  have hbv : b.val = (floorOf (w.node i) / 3 + 1) * 3 + i.val := by
    rw [hb, old.id, rid_val]
  have hlt := i.isLt
  have tg := top_grows w i (.Some ⟨.All, .Prepare b⟩, fresh (w.node i) b) g
  refine ⟨inv_after w inv i _ _ g ?_ ?_, ?_⟩
  · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [after_self, fresh]
    · exact old.id
    · right; omega
    · intro _; exact ⟨hv, sent_new _ _ _ _⟩
    · intro v h; cases h
    · intro j y h; simp only [pslot] at h; split_ifs at h <;> cases h
    · intro _; rfl
    · exact le_trans old.promised_top tg
    · exact le_trans old.seen_top tg
    · intro v h; obtain ⟨p, hp, hm⟩ := old.request v h; exact ⟨p, .inl hp, hm⟩
    · intro j vt h
      obtain ⟨p, hp, rest⟩ := old.votes j vt (by simpa [vslot] using h)
      exact ⟨p, .inl hp, rest⟩
    · exact old.undecided
    · intro v h
      obtain ⟨q, c, hq⟩ := old.decided v h
      exact ⟨q, c, fun a ha => abs_votes_grow w i _ (hq a ha)⟩
  · intro s e; cases e
    simp only [PacketInv, after_self, fresh]
    exact ⟨by omega, by omega, le_refl _⟩
  · rw [abs_hidden w i (.Some ⟨.All, .Prepare b⟩) (fresh (w.node i) b) rfl rfl
      (fun s e => by cases e; exact .inl trivial)]
    exact .idle

theorem good_tick (w : World) (inv : Inv w) (i : Rid) :
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

theorem deliver_rid (n : Node) (j : Rid) (msg : Msg) :
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
  unfold deliverS; rw [if_neg (by simp)]; cases msg <;> rfl

theorem owner_of (b : U64) (j : Rid) (h : b.val % 3 = j.val) : owner b = j := Fin.ext h

theorem good_request (w : World) (inv : Inv w) (i : Rid) (p : Packet) (hp : w.net p) (v : U64)
    (hm : p.send.msg = .Request v) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Request v))) := by
  have old := inv.1 i
  rw [deliver_rid]
  cases hv : (w.node i).value
  · simp only []
    have g : Grows (w.node i) { w.node i with value := .Some v } :=
      grows_of rfl rfl (le_refl _) (le_refl _) (fun _ e => by rw [hv] at e; cases e) rfl
        (fun _ e => e) (fun _ vt e => ⟨vt, by simpa [vslot] using e, le_refl _⟩) (fun _ e => e)
    have tg := top_grows w i (.None, { w.node i with value := .Some v }) g
    refine ⟨inv_after w inv i _ _ g ?_ (fun s e => by cases e), ?_⟩
    · apply old.congr (net_grows w i _) tg <;> simp only [after_self]
      · simp
      · intro x e; simp only [Option.some.injEq] at e; subst e; exact ⟨p, .inl hp, hm⟩
      · exact le_trans old.promised_top tg
      · exact le_trans old.seen_top tg
    · rw [abs_hidden w i .None { w.node i with value := .Some v } rfl rfl (fun s e => by cases e)]
      exact .idle
  · exact good_noop w inv i

theorem good_nack (w : World) (inv : Inv w) (i : Rid) (p : Packet) (hp : w.net p) (x q : U64)
    (hm : p.send.msg = .Nack x q) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Nack x q))) := by
  have old := inv.1 i
  have hq : q.val ≤ top w := by have := inv.2 p hp; simp only [PacketInv, hm] at this; exact this
  rw [deliver_rid]
  simp only []
  split
  · rename_i hlt; rw [UScalar.lt_equiv] at hlt
    have g : Grows (w.node i) { w.node i with max_seen := q } :=
      grows_of rfl rfl (le_refl _) (by simp; omega) (fun _ e => e) rfl
        (fun _ e => e) (fun _ vt e => ⟨vt, by simpa [vslot] using e, le_refl _⟩) (fun _ e => e)
    have tg := top_grows w i (.None, { w.node i with max_seen := q }) g
    refine ⟨inv_after w inv i _ _ g ?_ (fun s e => by cases e), ?_⟩
    · apply old.congr (net_grows w i _) tg <;> simp only [after_self]
      · exact id
      · intro x e; obtain ⟨p, hp, h⟩ := old.request x e; exact ⟨p, .inl hp, h⟩
      · exact le_trans old.promised_top tg
      · exact le_trans hq tg
    · rw [abs_hidden w i .None { w.node i with max_seen := q } rfl rfl (fun s e => by cases e)]
      exact .idle
  · exact good_noop w inv i

theorem good_prepare (w : World) (inv : Inv w) (i : Rid) (p : Packet) (hp : w.net p) (b : U64)
    (hm : p.send.msg = .Prepare b) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Prepare b))) := by
  have old := inv.1 i
  have pk := inv.2 p hp
  simp only [PacketInv, hm] at pk
  obtain ⟨_, hmod, hle⟩ := pk
  have hbt : b.val ≤ top w := le_trans hle (le_top w _)
  rw [deliver_rid]
  simp only [onPrepareS]
  split
  · rename_i hlt; rw [UScalar.lt_equiv] at hlt
    have g : Grows (w.node i) { w.node i with promised := b } :=
      grows_of rfl rfl (by simp; omega) (le_refl _) (fun _ e => e) rfl
        (fun _ e => e) (fun _ vt e => ⟨vt, by simpa [vslot] using e, le_refl _⟩) (fun _ e => e)
    have tg := top_grows w i (.Some ⟨.To (rid p.src), .Promise b (w.node i).accepted⟩,
      { w.node i with promised := b }) g
    refine ⟨inv_after w inv i _ _ g ?_ ?_, ?_⟩
    · apply old.congr (net_grows w i _) tg <;> simp only [after_self]
      · exact id
      · intro x e; obtain ⟨p, hp, h⟩ := old.request x e; exact ⟨p, .inl hp, h⟩
      · exact le_trans hbt tg
      · exact le_trans old.seen_top tg
    · intro s e; cases e; simp only [PacketInv, owner_of b p.src hmod]
    · obtain ⟨e1, e2, e3, e4, e5⟩ := abs_after w i (.Some ⟨.To (rid p.src), .Promise b (w.node i).accepted⟩)
        { w.node i with promised := b }
      have : abs (w.after i (.Some ⟨.To (rid p.src), .Promise b (w.node i).accepted⟩,
          { w.node i with promised := b })) = Paxos.prepare (abs w) i b.val := by
        apply state_ext
        · intro a; rw [e1]; rfl
        · intro a; rw [e2]; simp [Paxos.prepare, Paxos.put, abs]; intro h; subst h; rfl
        · intro a c x; rw [e3]; simp only [Paxos.prepare]
          apply or_congr_right
          constructor
          · rintro ⟨s, hs, rfl, y, z, hmsg, hy, hz⟩
            cases hs; simp only [Msg.Promise.injEq] at hmsg; obtain ⟨rfl, rfl⟩ := hmsg
            exact ⟨rfl, hy.symm, by rw [← hz]; rfl⟩
          · rintro ⟨rfl, rfl, rfl⟩
            exact ⟨_, rfl, rfl, b, (w.node a).accepted, rfl, rfl, rfl⟩
        · intro c v; rw [e4]; simp [Paxos.prepare]
        · intro a c v; rw [e5]; simp [Paxos.prepare]
      rw [this]
      exact .prepare i b.val (by simpa [abs] using hlt)
  · have hq : (w.node i).promised.val ≤ top w := old.promised_top
    exact good_hidden w inv i _ trivial (by
      simp only [PacketInv]; exact le_trans hq (top_grows w i _ (Grows.refl _)))

theorem good_accept (w : World) (inv : Inv w) (i : Rid) (p : Packet) (hp : w.net p) (vt : Vote)
    (hm : p.send.msg = .Accept vt) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Accept vt))) := by
  have old := inv.1 i
  have pk := inv.2 p hp
  simp only [PacketInv, hm] at pk
  obtain ⟨_, _, hle, _, _⟩ := pk
  have hbt : vt.ballot.val ≤ top w := le_trans hle (le_top w _)
  rw [deliver_rid]
  simp only [onAcceptS]
  split
  · rename_i hlt; rw [UScalar.le_equiv] at hlt
    let n' : Node := { w.node i with promised := vt.ballot, accepted := .Some vt }
    have g : Grows (w.node i) n' :=
      grows_of rfl rfl (by simp [n']; omega) (le_refl _) (fun _ e => e) rfl
        (fun _ e => e) (fun _ v e => ⟨v, by simpa [vslot, n'] using e, le_refl _⟩) (fun _ e => e)
    have tg := top_grows w i (.Some ⟨.All, .Accepted vt⟩, n') g
    refine ⟨inv_after w inv i _ _ g ?_ ?_, ?_⟩
    · apply old.congr (net_grows w i _) tg <;> simp only [after_self, n']
      · exact id
      · intro x e; obtain ⟨p, hp, h⟩ := old.request x e; exact ⟨p, .inl hp, h⟩
      · exact le_trans hbt tg
      · exact le_trans old.seen_top tg
    · intro s e; cases e; simp [PacketInv, n']
    · obtain ⟨e1, e2, e3, e4, e5⟩ := abs_after w i (.Some ⟨.All, .Accepted vt⟩) n'
      have : abs (w.after i (.Some ⟨.All, .Accepted vt⟩, n')) =
          Paxos.cast (abs w) i vt.ballot.val vt.value.val := by
        apply state_ext
        · intro a; rw [e1]; rfl
        · intro a; rw [e2]; rfl
        · intro a c x; rw [e3]; simp [Paxos.cast]
        · intro c v; rw [e4]; simp [Paxos.cast]
        · intro a c v; rw [e5]; simp only [Paxos.cast]
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

/-- Learner updates change only the vote slots and the decision. -/
theorem good_learner (w : World) (inv : Inv w) (i : Rid) (n' : Node) (g : Grows (w.node i) n')
    (b1 : n'.ballot = (w.node i).ballot) (b2 : n'.proposal = (w.node i).proposal)
    (b3 : n'.value = (w.node i).value) (b4 : n'.id = (w.node i).id)
    (b5 : n'.promised = (w.node i).promised) (b6 : n'.accepted = (w.node i).accepted)
    (b7 : n'.max_seen = (w.node i).max_seen) (b8 : n'.promise0 = (w.node i).promise0)
    (b9 : n'.promise1 = (w.node i).promise1) (b10 : n'.promise2 = (w.node i).promise2)
    (votes : ∀ j x, vslot n' j = .Some x → ∃ q, w.net q ∧ q.src = j ∧ q.send.msg = .Accepted x)
    (und : n'.decided = .None → agreedS n'.vote0 n'.vote1 n'.vote2 = .None)
    (dec : ∀ x, n'.decided = .Some x →
      ∃ (q : Paxos.Quorum) (c : Nat), ∀ a, Paxos.Member a q → (abs w).votes a c x.val) :
    Good w (w.after i (.None, n')) := by
  have old := inv.1 i
  have tg := top_grows w i (.None, n') g
  refine ⟨inv_after w inv i _ _ g ?_ (fun s e => by cases e), ?_⟩
  · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [after_self]
    · rw [b4]; exact old.id
    · rw [b1]; exact old.own
    · rw [b1, b3]; intro hb; exact ⟨(old.started hb).1, .inl (old.started hb).2⟩
    · rw [b1, b2]; intro v h; exact ⟨(old.proposed v h).1, .inl (old.proposed v h).2⟩
    · intro j y h
      have : pslot n' j = pslot (w.node i) j := by simp [pslot, b8, b9, b10]
      rw [this] at h; rw [b1]
      obtain ⟨q, hq, rest⟩ := old.slots j y h; exact ⟨q, .inl hq, rest⟩
    · rw [b2, b8, b9, b10]; exact old.pending
    · rw [b5]; exact le_trans old.promised_top tg
    · rw [b7]; exact le_trans old.seen_top tg
    · rw [b3]; intro v h; obtain ⟨q, hq, rest⟩ := old.request v h; exact ⟨q, .inl hq, rest⟩
    · intro j x h; obtain ⟨q, hq, rest⟩ := votes j x h; exact ⟨q, .inl hq, rest⟩
    · exact und
    · intro x h
      obtain ⟨q, c, hq⟩ := dec x h
      exact ⟨q, c, fun a ha => abs_votes_grow w i _ (hq a ha)⟩
  · rw [abs_hidden w i .None n' b5 b6 (fun s e => by cases e)]; exact .idle

theorem good_accepted (w : World) (inv : Inv w) (i : Rid) (p : Packet) (hp : w.net p) (vt : Vote)
    (hm : p.send.msg = .Accepted vt) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Accepted vt))) := by
  have old := inv.1 i
  rw [deliver_rid]
  have hs : (rid p.src).val < 3 := by simp
  have g := accepted_grows (w.node i) (rid p.src) vt hs
  simp only [onAcceptedS] at g ⊢
  generalize hmdef : (if newer (voteAt (w.node i) (rid p.src)) vt = true then
    setVote (w.node i) (rid p.src) vt else w.node i) = m at g ⊢
  obtain ⟨f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11⟩ :
      m.ballot = (w.node i).ballot ∧ m.proposal = (w.node i).proposal ∧
      m.value = (w.node i).value ∧ m.id = (w.node i).id ∧
      m.promised = (w.node i).promised ∧ m.accepted = (w.node i).accepted ∧
      m.max_seen = (w.node i).max_seen ∧ m.promise0 = (w.node i).promise0 ∧
      m.promise1 = (w.node i).promise1 ∧ m.promise2 = (w.node i).promise2 ∧
      m.decided = (w.node i).decided := by
    rw [← hmdef]; split
    · exact setVote_fields _ _ _
    · simp
  have mvotes : ∀ j x, vslot m j = .Some x → ∃ q, w.net q ∧ q.src = j ∧ q.send.msg = .Accepted x := by
    intro j x h
    rw [← hmdef] at h; split at h
    · rw [vslot_set _ _ _ _ hs] at h; split at h
      · rename_i hj; simp only [Option.some.injEq] at h; subst h
        exact ⟨p, hp, Fin.ext (by simpa using hj.symm), hm⟩
      · exact old.votes j x h
    · exact old.votes j x h
  cases hd : (w.node i).decided
  · simp only [hd] at g ⊢
    refine good_learner w inv i _ g f1 f2 f3 f4 f5 f6 f7 f8 f9 f10
      (fun j x h => mvotes j x (by simpa [vslot] using h)) (fun h => by simpa using h) ?_
    intro x h
    obtain ⟨q, y, h1, h2, hx⟩ := agreedS_spec m x (by simpa using h)
    refine ⟨q, y.ballot.val, fun a ha => ?_⟩
    have hy : vslot m a = .Some y := by rcases ha with rfl | rfl <;> assumption
    obtain ⟨pk, hpk, hsrc, hmsg⟩ := mvotes a y hy
    exact ⟨pk, hpk, hsrc, y, hmsg, rfl, by rw [hx]⟩
  · simp only [hd] at g ⊢
    refine good_learner w inv i _ g f1 f2 f3 f4 f5 f6 f7 f8 f9 f10 mvotes
      (fun h => by rw [f11, hd] at h; cases h) ?_
    intro x h; rw [f11] at h; exact old.decided x h

theorem put_same (f : Rid → α) (a : Rid) : Paxos.put f a (f a) = f := by
  funext i; by_cases hi : i = a <;> simp [Paxos.put, hi]

/-- A value reported in a promise snapshot was proposed, hence requested by a client. -/
theorem request_of_snapshot (w : World) (inv : Inv w) (ainv : Paxos.Invariant (abs w))
    (pk : Packet) (hpk : w.net pk) (c : U64) (a : Vote) (hm : pk.send.msg = .Promise c (.Some a)) :
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

theorem good_promise (w : World) (inv : Inv w) (ainv : Paxos.Invariant (abs w)) (i : Rid)
    (p : Packet) (hp : w.net p) (b : U64) (acc : Opt Vote) (hm : p.send.msg = .Promise b acc) :
    Good w (w.after i (deliverS (w.node i) (rid p.src) (.Promise b acc))) := by
  have old := inv.1 i
  have hs : (rid p.src).val < 3 := by simp
  have g := promise_grows (w.node i) (rid p.src) b acc hs
  rw [deliver_rid]
  simp only [onPromiseS] at g ⊢
  by_cases h1 : b ≠ (w.node i).ballot
  · rw [if_pos h1]; exact good_noop w inv i
  rw [if_neg h1] at g ⊢
  have h1 : b = (w.node i).ballot := not_not.mp h1
  by_cases h2 : b = 0#u64
  · rw [if_pos h2]; exact good_noop w inv i
  rw [if_neg h2] at g ⊢
  have hb0 : (w.node i).ballot.val ≠ 0 := by
    rw [← h1]; intro e; exact h2 (UScalar.eq_of_val_eq (by simpa using e))
  rcases hpr : (w.node i).proposal with _ | x
  rotate_left
  · exact good_noop w inv i
  simp only [hpr] at g ⊢
  have mslots : ∀ j y, pslot (recordS (w.node i) (rid p.src) acc) j = .Some y →
      ∃ q, w.net q ∧ q.src = j ∧ q.send.msg = .Promise (w.node i).ballot y := by
    intro j y h
    rw [pslot_record _ _ _ _ hs] at h
    split at h
    · rename_i hj; simp only [Option.some.injEq] at h; subst h
      exact ⟨p, hp, Fin.ext (by simpa using hj.symm), by rw [hm, h1]⟩
    · exact old.slots j y h
  obtain ⟨e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11⟩ := record_fields (w.node i) (rid p.src) acc
  generalize recordS (w.node i) (rid p.src) acc = m at *
  have own : (w.node i).ballot.val % 3 = i.val := old.own.resolve_left hb0
  rcases hv : (w.node i).value with _ | v
  · exact absurd hv (old.started hb0).1
  simp only [hv] at g ⊢
  have mvotes : ∀ j, vslot m j = vslot (w.node i) j := by intro j; simp [vslot, e8, e9, e10]
  rcases hq : quorumS m.promise0 m.promise1 m.promise2 with _ | ⟨l, r⟩
  · simp only [hq] at g ⊢
    have tg := top_grows w i (.None, m) g
    refine ⟨inv_after w inv i _ _ g ?_ (fun s e => by cases e), ?_⟩
    · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [after_self]
      · rw [e4]; exact old.id
      · rw [e1]; exact old.own
      · rw [e1, e3]; intro hb; exact ⟨(old.started hb).1, .inl (old.started hb).2⟩
      · rw [e2, hpr]; intro v h; cases h
      · intro j y h; rw [e1]; obtain ⟨q, hq', rest⟩ := mslots j y h; exact ⟨q, .inl hq', rest⟩
      · intro _; exact hq
      · rw [e5]; exact le_trans old.promised_top tg
      · rw [e7]; exact le_trans old.seen_top tg
      · rw [e3]; intro v h; obtain ⟨q, hq', rest⟩ := old.request v h; exact ⟨q, .inl hq', rest⟩
      · intro j x h; rw [mvotes] at h
        obtain ⟨q, hq', rest⟩ := old.votes j x h; exact ⟨q, .inl hq', rest⟩
      · rw [e11, e8, e9, e10]; exact old.undecided
      · rw [e11]; intro x h
        obtain ⟨q, c, hq'⟩ := old.decided x h
        exact ⟨q, c, fun a ha => abs_votes_grow w i _ (hq' a ha)⟩
    · rw [abs_hidden w i .None m e5 e6 (fun s e => by cases e)]; exact .idle
  simp only [hq] at g ⊢
  obtain ⟨q, hql, hqr⟩ := quorumS_spec m l r hq
  generalize hx : selectS l r v = x at g ⊢
  have tg := top_grows w i (.Some ⟨.All, .Accept ⟨b, x⟩⟩, { m with proposal := .Some x }) g
  refine ⟨inv_after w inv i _ _ g ?_ ?_, ?_⟩
  · refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [after_self]
    · rw [e4]; exact old.id
    · rw [e1]; exact old.own
    · rw [e1, e3]; intro hb; exact ⟨(old.started hb).1, .inl (old.started hb).2⟩
    · intro v' h; simp only [Option.some.injEq] at h; subst h
      rw [e1]; exact ⟨hb0, by rw [← h1]; exact sent_new _ _ _ _⟩
    · intro j y h
      have : pslot { m with proposal := .Some x } j = pslot m j := by simp [pslot]
      rw [this] at h; rw [e1]; obtain ⟨q, hq', rest⟩ := mslots j y h; exact ⟨q, .inl hq', rest⟩
    · intro h; cases h
    · have := old.promised_top; rw [← e5] at this; exact le_trans this tg
    · have := old.seen_top; rw [← e7] at this; exact le_trans this tg
    · rw [e3]; intro v h; obtain ⟨q, hq', rest⟩ := old.request v h; exact ⟨q, .inl hq', rest⟩
    · intro j y h
      have : vslot { m with proposal := .Some x } j = vslot m j := by simp [vslot]
      rw [this, mvotes] at h
      obtain ⟨q, hq', rest⟩ := old.votes j y h; exact ⟨q, .inl hq', rest⟩
    · rw [e11, e8, e9, e10]; exact old.undecided
    · rw [e11]; intro y h
      obtain ⟨q, c, hq'⟩ := old.decided y h
      exact ⟨q, c, fun a ha => abs_votes_grow w i _ (hq' a ha)⟩
  · intro s e; cases e
    simp only [PacketInv, after_self]
    refine ⟨by rw [h1]; exact hb0, by rw [h1]; exact own, by rw [e1, h1], by simp, ?_⟩
    rcases selectS_cases l r v with h | ⟨a, hl, h⟩ | ⟨a, hr, h⟩ <;> rw [hx] at h <;> subst h
    · obtain ⟨pk, hpk, hmm⟩ := old.request _ hv; exact ⟨pk, .inl hpk, hmm⟩
    · subst hl
      obtain ⟨pk, hpk, _, hmsg⟩ := mslots q.first _ hql
      obtain ⟨rq, hrq, hmr⟩ := request_of_snapshot w inv ainv pk hpk _ a hmsg
      exact ⟨rq, .inl hrq, hmr⟩
    · subst hr
      obtain ⟨pk, hpk, _, hmsg⟩ := mslots q.second _ hqr
      obtain ⟨rq, hrq, hmr⟩ := request_of_snapshot w inv ainv pk hpk _ a hmsg
      exact ⟨rq, .inl hrq, hmr⟩
  · have fresh : ∀ v', ¬ (abs w).proposals b.val v' := by
      rintro v' ⟨pk, hpk, vt, hmsg, hb, _⟩
      have pi := inv.2 pk hpk
      simp only [PacketInv, hmsg] at pi
      obtain ⟨_, hmod, _, hprop, _⟩ := pi
      have hsrc : pk.src = i := Fin.ext (by rw [← hmod, ← own, hb, h1])
      rw [hsrc] at hprop
      have heq : vt.ballot = (w.node i).ballot := UScalar.eq_of_val_eq (by rw [hb, h1])
      rw [hprop heq] at hpr; cases hpr
    have hl' : (abs w).promises q.first b.val (snap l) := by
      obtain ⟨pk, hpk, hsrc, hmsg⟩ := mslots q.first l hql
      exact ⟨pk, hpk, hsrc, _, l, hmsg, by rw [h1], rfl⟩
    have hr' : (abs w).promises q.second b.val (snap r) := by
      obtain ⟨pk, hpk, hsrc, hmsg⟩ := mslots q.second r hqr
      exact ⟨pk, hpk, hsrc, _, r, hmsg, by rw [h1], rfl⟩
    obtain ⟨a1, a2, a3, a4, a5⟩ := abs_after w i (.Some ⟨.All, .Accept ⟨b, x⟩⟩) { m with proposal := .Some x }
    have heq : abs (w.after i (.Some ⟨.All, .Accept ⟨b, x⟩⟩, { m with proposal := .Some x })) =
        Paxos.propose (abs w) b.val (Paxos.select (snap l) (snap r) v.val) := by
      apply state_ext
      · intro a; rw [a1]; simp only [e5]
        show Paxos.put (abs w).promised i ((abs w).promised i) a = _
        rw [put_same]; rfl
      · intro a; rw [a2]; simp only [e6]
        show Paxos.put (abs w).accepted i ((abs w).accepted i) a = _
        rw [put_same]; rfl
      · intro a c y; rw [a3]; simp [Paxos.propose]
      · intro c y; rw [a4]; simp only [Paxos.propose]
        apply or_congr_right
        rw [← selectS_val, hx]
        constructor
        · rintro ⟨s, hs, vt, hmsg, hb, hv'⟩
          cases hs; simp only [Msg.Accept.injEq] at hmsg; subst hmsg
          exact ⟨hb.symm, hv'.symm⟩
        · rintro ⟨rfl, rfl⟩; exact ⟨_, rfl, ⟨b, x⟩, rfl, rfl, rfl⟩
      · intro a c y; rw [a5]; simp [Paxos.propose]
    rw [heq]
    exact .propose b.val v.val q (snap l) (snap r) fresh hl' hr'

/-- Every permitted input preserves the invariant and refines one abstract step. -/
theorem good_step (w : World) (inv : Inv w) (ainv : Paxos.Invariant (abs w)) (i : Rid)
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
