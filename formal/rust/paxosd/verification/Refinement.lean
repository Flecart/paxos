import UserVerification.Local

/- The deployment refines the abstract Paxos model, and its concrete
   invariant is inductive. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

/-! ## Frame lemmas -/

@[simp] theorem after_self (w : World) (i : Rid) (r : Opt Send × Node) :
    (w.after i r).node i = r.2 := by simp [World.after, Paxos.put]

theorem after_other (w : World) {i k : Rid} (r : Opt Send × Node) (h : k ≠ i) :
    (w.after i r).node k = w.node k := by simp [World.after, Paxos.put, h]

theorem after_node (w : World) (i k : Rid) (r : Opt Send × Node) :
    (w.after i r).node k = if k = i then r.2 else w.node k := by
  simp [World.after, Paxos.put]

@[simp] theorem after_net (w : World) (i : Rid) (r : Opt Send × Node) (p : Packet) :
    (w.after i r).net p ↔ w.net p ∨ (r.1 = .Some p.send ∧ p.src = i) := Iff.rfl

theorem net_grows (w : World) (i : Rid) (r : Opt Send × Node) (p : Packet) (h : w.net p) :
    (w.after i r).net p := .inl h

theorem sent_new (w : World) (i : Rid) (s : Send) (n : Node) :
    (w.after i (.Some s, n)).net ⟨i, s⟩ := .inr ⟨rfl, rfl⟩

theorem top_grows (w : World) (i : Rid) (r : Opt Send × Node) (g : Grows (w.node i) r.2) :
    top w ≤ top (w.after i r) := by
  have h : ∀ k, (w.node k).ballot.val ≤ ((w.after i r).node k).ballot.val := by
    intro k; rw [after_node]; split
    · subst k; exact g.ballot
    · exact le_refl _
  unfold top
  have := h 0; have := h 1; have := h 2
  omega

theorem world_ext {w w' : World} (hn : w.node = w'.node) (hp : ∀ p, w.net p ↔ w'.net p) :
    w = w' := by
  cases w; cases w'; simp only at hn; subst hn
  congr; funext p; exact propext (hp p)

theorem after_noop (w : World) (i : Rid) : w.after i (.None, w.node i) = w := by
  apply world_ext
  · funext k; rw [after_node]; split <;> simp_all
  · intro p; simp

theorem after_dup (w : World) (i : Rid) (s : Send) (h : w.net ⟨i, s⟩) :
    w.after i (.Some s, w.node i) = w := by
  apply world_ext
  · funext k; rw [after_node]; split <;> simp_all
  · intro p; simp only [after_net]
    constructor
    · rintro (hp | ⟨hs, hi⟩)
      · exact hp
      · cases p; simp only [Option.some.injEq] at hs hi
        cases hs; subst hi; exact h
    · exact .inl

/-! ## Monotonicity of the invariant -/

theorem abs_votes_grow (w : World) (i : Rid) (r : Opt Send × Node) {a b v}
    (h : (abs w).votes a b v) : (abs (w.after i r)).votes a b v := by
  obtain ⟨p, hp, rest⟩ := h; exact ⟨p, .inl hp, rest⟩

theorem NodeInv.mono {w w' : World} {k : Rid} (h : NodeInv w k) (hn : w'.node k = w.node k)
    (hnet : ∀ p, w.net p → w'.net p) (htop : top w ≤ top w') : NodeInv w' k := by
  obtain ⟨id, own, started, proposed, slots, pending, promised_top, seen_top, request, votes,
    undecided, decided⟩ := h
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> rw [hn]
  · exact id
  · exact own
  · intro hb; obtain ⟨a, b⟩ := started hb; exact ⟨a, hnet _ b⟩
  · intro v hv; obtain ⟨a, b⟩ := proposed v hv; exact ⟨a, hnet _ b⟩
  · intro j y hj; obtain ⟨p, a, b⟩ := slots j y hj; exact ⟨p, hnet _ a, b⟩
  · exact pending
  · omega
  · omega
  · intro v hv; obtain ⟨p, a, b⟩ := request v hv; exact ⟨p, hnet _ a, b⟩
  · intro j vt hj; obtain ⟨p, a, b⟩ := votes j vt hj; exact ⟨p, hnet _ a, b⟩
  · exact undecided
  · intro v hv
    obtain ⟨q, b, hq⟩ := decided v hv
    refine ⟨q, b, fun a ha => ?_⟩
    obtain ⟨p, hp, rest⟩ := hq a ha
    exact ⟨p, hnet _ hp, rest⟩

theorem PacketInv.mono (w : World) (i : Rid) (r : Opt Send × Node) (g : Grows (w.node i) r.2)
    (p : Packet) (h : PacketInv w p) : PacketInv (w.after i r) p := by
  have ballot : ∀ k, (w.node k).ballot.val ≤ ((w.after i r).node k).ballot.val := by
    intro k; rw [after_node]; split
    · subst k; exact g.ballot
    · exact le_refl _
  have promised : ∀ k, (w.node k).promised.val ≤ ((w.after i r).node k).promised.val := by
    intro k; rw [after_node]; split
    · subst k; exact g.promised
    · exact le_refl _
  unfold PacketInv at *
  cases hm : p.send.msg <;> simp only [hm] at h ⊢
  · exact h
  · exact ⟨h.1, h.2.1, le_trans h.2.2 (ballot _)⟩
  · exact h
  · obtain ⟨h0, h1, h2, h3, q, hq, hm⟩ := h
    refine ⟨h0, h1, le_trans h2 (ballot _), ?_, q, .inl hq, hm⟩
    intro e
    rw [after_node] at e ⊢
    split at e
    · rename_i hs; subst hs
      by_cases same : r.2.ballot = (w.node p.src).ballot
      · rw [same] at e; simpa using g.proposal same _ (h3 e)
      · exfalso
        have lt : (w.node p.src).ballot.val < r.2.ballot.val := by
          have := g.ballot
          have : (w.node p.src).ballot.val ≠ r.2.ballot.val :=
            fun v => same (UScalar.eq_of_val_eq v).symm
          omega
        rw [e] at h2; omega
    · rename_i hs; simpa [hs] using h3 e
  · exact le_trans h (promised _)
  · exact le_trans h (top_grows w i r g)

/-- Each handler case only needs to establish the updated replica's invariant
    and the invariant of the packet it emits. -/
theorem inv_after (w : World) (inv : Inv w) (i : Rid) (o : Opt Send) (n' : Node)
    (g : Grows (w.node i) n') (hnode : NodeInv (w.after i (o, n')) i)
    (hpkt : ∀ s, o = .Some s → PacketInv (w.after i (o, n')) ⟨i, s⟩) :
    Inv (w.after i (o, n')) := by
  refine ⟨fun k => ?_, fun p hp => ?_⟩
  · by_cases hk : k = i
    · subst hk; exact hnode
    · exact (inv.1 k).mono (after_other w _ hk) (net_grows w i _) (top_grows w i _ g)
  · rcases hp with hp | ⟨hs, hi⟩
    · exact PacketInv.mono w i (o, n') g p (inv.2 p hp)
    · cases p; simp only at hs hi; subst hi; exact hpkt _ hs

/-! ## Abstract state equality -/

theorem state_ext {s t : Paxos.State} (h1 : ∀ a, s.promised a = t.promised a)
    (h2 : ∀ a, s.accepted a = t.accepted a)
    (h3 : ∀ a b x, s.promises a b x ↔ t.promises a b x)
    (h4 : ∀ b v, s.proposals b v ↔ t.proposals b v)
    (h5 : ∀ a b v, s.votes a b v ↔ t.votes a b v) : s = t := by
  cases s; cases t
  simp only [Paxos.State.mk.injEq]
  refine ⟨funext h1, funext h2, ?_, ?_, ?_⟩
  · funext a b x; exact propext (h3 a b x)
  · funext b v; exact propext (h4 b v)
  · funext a b v; exact propext (h5 a b v)

/-- Messages that the abstract model does not record. -/
def Hidden : Msg → Prop
  | .Request _ => True
  | .Prepare _ => True
  | .Nack _ _ => True
  | _ => False

theorem abs_hidden (w : World) (i : Rid) (o : Opt Send) (n' : Node)
    (hp : n'.promised = (w.node i).promised) (ha : n'.accepted = (w.node i).accepted)
    (ho : ∀ s, o = .Some s → Hidden s.msg ∨ w.net ⟨i, s⟩) :
    abs (w.after i (o, n')) = abs w := by
  have visible : ∀ p, (w.after i (o, n')).net p → ¬ w.net p → Hidden p.send.msg := by
    intro p h hn
    rcases h with h | ⟨hs, hi⟩
    · exact absurd h hn
    · rcases ho _ hs with h | h
      · exact h
      · cases p; simp only at hi; subst hi; exact absurd h hn
  apply state_ext
  · intro a; simp only [abs, after_node]; split <;> simp_all
  · intro a; simp only [abs, after_node]; split <;> simp_all
  · intro a b x; simp only [abs]; constructor
    · rintro ⟨p, h, hsrc, y, z, hm, rest⟩
      by_cases old : w.net p
      · exact ⟨p, old, hsrc, y, z, hm, rest⟩
      · have := visible p h old; rw [hm] at this; cases this
    · rintro ⟨p, h, rest⟩; exact ⟨p, .inl h, rest⟩
  · intro b v; simp only [abs]; constructor
    · rintro ⟨p, h, vt, hm, rest⟩
      by_cases old : w.net p
      · exact ⟨p, old, vt, hm, rest⟩
      · have := visible p h old; rw [hm] at this; cases this
    · rintro ⟨p, h, rest⟩; exact ⟨p, .inl h, rest⟩
  · intro a b v; simp only [abs]; constructor
    · rintro ⟨p, h, hsrc, vt, hm, rest⟩
      by_cases old : w.net p
      · exact ⟨p, old, hsrc, vt, hm, rest⟩
      · have := visible p h old; rw [hm] at this; cases this
    · rintro ⟨p, h, rest⟩; exact ⟨p, .inl h, rest⟩

/-! ## Replica facts reused by several handlers -/

/-- A replica whose proposer and learner state is unchanged keeps its invariant,
    given bounds for its acceptor fields and provenance for a new client value. -/
theorem NodeInv.congr {w w' : World} {k : Rid} (h : NodeInv w k)
    (hnet : ∀ p, w.net p → w'.net p) (htop : top w ≤ top w')
    (hid : (w'.node k).id = (w.node k).id) (hb : (w'.node k).ballot = (w.node k).ballot)
    (hpr : (w'.node k).proposal = (w.node k).proposal)
    (h0 : (w'.node k).promise0 = (w.node k).promise0) (h1 : (w'.node k).promise1 = (w.node k).promise1)
    (h2 : (w'.node k).promise2 = (w.node k).promise2)
    (v0 : (w'.node k).vote0 = (w.node k).vote0) (v1 : (w'.node k).vote1 = (w.node k).vote1)
    (v2 : (w'.node k).vote2 = (w.node k).vote2) (hd : (w'.node k).decided = (w.node k).decided)
    (hv : (w.node k).value ≠ .None → (w'.node k).value ≠ .None)
    (hreq : ∀ v, (w'.node k).value = .Some v → ∃ p, w'.net p ∧ p.send.msg = .Request v)
    (hprom : (w'.node k).promised.val ≤ top w') (hseen : (w'.node k).max_seen.val ≤ top w') :
    NodeInv w' k := by
  have hm := h.mono (w' := { node := w.node, net := w'.net }) rfl hnet (le_refl (top w))
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, hprom, hseen, hreq, ?_, ?_, ?_⟩
  · rw [hid]; exact h.id
  · rw [hb]; exact h.own
  · intro hb'; rw [hb] at hb' ⊢
    exact ⟨hv (h.started hb').1, hnet _ (h.started hb').2⟩
  · intro v hp; rw [hpr] at hp; rw [hb]; exact hm.proposed v hp
  · intro j y hj
    have : pslot (w'.node k) j = pslot (w.node k) j := by simp [pslot, h0, h1, h2]
    rw [this] at hj; rw [hb]; exact hm.slots j y hj
  · rw [hpr, h0, h1, h2]; exact h.pending
  · intro j vt hj
    have : vslot (w'.node k) j = vslot (w.node k) j := by simp [vslot, v0, v1, v2]
    rw [this] at hj; exact hm.votes j vt hj
  · rw [hd, v0, v1, v2]; exact h.undecided
  · intro v hv'; rw [hd] at hv'
    obtain ⟨q, b, hq⟩ := h.decided v hv'
    exact ⟨q, b, fun a ha => by obtain ⟨p, hp, rest⟩ := hq a ha; exact ⟨p, hnet _ hp, rest⟩⟩

def quorum01 : Paxos.Quorum := ⟨0, 1, by decide⟩
def quorum02 : Paxos.Quorum := ⟨0, 2, by decide⟩
def quorum12 : Paxos.Quorum := ⟨1, 2, by decide⟩

theorem quorumS_spec (n : Node) (l r : Opt Vote)
    (h : quorumS n.promise0 n.promise1 n.promise2 = .Some (l, r)) :
    ∃ q : Paxos.Quorum, pslot n q.first = .Some l ∧ pslot n q.second = .Some r := by
  unfold quorumS at h
  split at h <;> simp only [Option.some.injEq, Prod.mk.injEq, reduceCtorEq] at h
  all_goals obtain ⟨rfl, rfl⟩ := h
  · exact ⟨quorum12, by simp_all [pslot, quorum12]⟩
  · exact ⟨quorum02, by simp_all [pslot, quorum02]⟩
  · exact ⟨quorum01, by simp_all [pslot, quorum01]⟩

theorem quorumS_of_two (n : Node) (q : Paxos.Quorum) (hl : pslot n q.first ≠ .None)
    (hr : pslot n q.second ≠ .None) : quorumS n.promise0 n.promise1 n.promise2 ≠ .None := by
  have d := q.distinct
  have := q.first.isLt; have := q.second.isLt
  have d' : q.first.val ≠ q.second.val := fun e => d (Fin.ext e)
  unfold pslot at hl hr
  cases h0 : n.promise0 <;> cases h1 : n.promise1 <;> cases h2 : n.promise2 <;>
    simp only [quorumS, ne_eq, reduceCtorEq, not_false_eq_true, not_true_eq_false] <;>
    (split_ifs at hl hr <;> simp_all <;> omega)

theorem same_eq_of (a b : Vote) (h : Same a b) : a = b := by
  obtain ⟨h1, h2⟩ := h; cases a; cases b; simp_all

theorem agreedS_cases (v0 v1 v2 : Opt Vote) (x : U64) (h : agreedS v0 v1 v2 = .Some x) :
    (∃ a, v0 = .Some a ∧ v1 = .Some a ∧ a.value = x) ∨
    (∃ a, v0 = .Some a ∧ v2 = .Some a ∧ a.value = x) ∨
    (∃ a, v1 = .Some a ∧ v2 = .Some a ∧ a.value = x) := by
  cases v0 <;> cases v1 <;> cases v2 <;> simp only [agreedS] at h <;> (repeat' split at h) <;>
    simp only [Option.some.injEq, reduceCtorEq] at h <;> subst h <;> rename_i hs <;>
    have e := same_eq_of _ _ hs <;> subst e <;> simp

theorem agreedS_spec (n : Node) (x : U64) (h : agreedS n.vote0 n.vote1 n.vote2 = .Some x) :
    ∃ (q : Paxos.Quorum) (vt : Vote), vslot n q.first = .Some vt ∧ vslot n q.second = .Some vt ∧
      vt.value = x := by
  rcases agreedS_cases _ _ _ x h with ⟨a, h0, h1, hx⟩ | ⟨a, h0, h2, hx⟩ | ⟨a, h1, h2, hx⟩
  · exact ⟨quorum01, a, by simp [vslot, quorum01, h0], by simp [vslot, quorum01, h1], hx⟩
  · exact ⟨quorum02, a, by simp [vslot, quorum02, h0], by simp [vslot, quorum02, h2], hx⟩
  · exact ⟨quorum12, a, by simp [vslot, quorum12, h1], by simp [vslot, quorum12, h2], hx⟩

theorem agreedS_of_two (n : Node) (q : Paxos.Quorum) (vt : Vote)
    (hl : vslot n q.first = .Some vt) (hr : vslot n q.second = .Some vt) :
    agreedS n.vote0 n.vote1 n.vote2 ≠ .None := by
  have d := q.distinct
  have := q.first.isLt; have := q.second.isLt
  have d' : q.first.val ≠ q.second.val := fun e => d (Fin.ext e)
  have self : Same vt vt := ⟨rfl, rfl⟩
  unfold vslot at hl hr
  cases h0 : n.vote0 <;> cases h1 : n.vote1 <;> cases h2 : n.vote2 <;>
    simp only [agreedS] <;> (split_ifs at hl hr <;> simp_all <;> (try omega)) <;>
    (split_ifs <;> simp_all)

theorem selectS_val (l r : Opt Vote) (v : U64) :
    (selectS l r v).val = Paxos.select (snap l) (snap r) v.val := by
  cases l <;> cases r <;> simp only [selectS, snap, Paxos.select]
  rename_i a b
  by_cases h : a.ballot < b.ballot
  · have : a.ballot.val < b.ballot.val := by rwa [UScalar.lt_equiv] at h
    simp [h, this]
  · have : ¬ a.ballot.val < b.ballot.val := by rwa [UScalar.lt_equiv] at h
    simp [h, this]

theorem selectS_cases (l r : Opt Vote) (v : U64) :
    selectS l r v = v ∨ (∃ a, l = .Some a ∧ selectS l r v = a.value) ∨
      (∃ b, r = .Some b ∧ selectS l r v = b.value) := by
  cases l <;> cases r <;> simp only [selectS] <;> (try split) <;> simp

end PaxosSystem
