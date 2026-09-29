import UserVerification.Local

/- The deployment refines the abstract Paxos model, and its concrete
   invariant is inductive. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

variable {N : Nat}

/-! ## Frame lemmas -/

@[simp] theorem after_self (w : World N) (i : Fin N) (r : Opt Send × Node) :
    (w.after i r).node i = r.2 := by simp [World.after, PaxosN.put]

theorem after_other (w : World N) {i k : Fin N} (r : Opt Send × Node) (h : k ≠ i) :
    (w.after i r).node k = w.node k := by simp [World.after, PaxosN.put, h]

theorem after_node (w : World N) (i k : Fin N) (r : Opt Send × Node) :
    (w.after i r).node k = if k = i then r.2 else w.node k := by
  simp [World.after, PaxosN.put]

@[simp] theorem after_net (w : World N) (i : Fin N) (r : Opt Send × Node) (p : Packet N) :
    (w.after i r).net p ↔ w.net p ∨ (r.1 = .Some p.send ∧ p.src = i) := Iff.rfl

theorem net_grows (w : World N) (i : Fin N) (r : Opt Send × Node) (p : Packet N) (h : w.net p) :
    (w.after i r).net p := .inl h

theorem sent_new (w : World N) (i : Fin N) (s : Send) (n : Node) :
    (w.after i (.Some s, n)).net ⟨i, s⟩ := .inr ⟨rfl, rfl⟩

theorem top_grows (w : World N) (i : Fin N) (r : Opt Send × Node) (g : Grows (w.node i) r.2) :
    top w ≤ top (w.after i r) := by
  have h : ∀ k, (w.node k).ballot.val ≤ ((w.after i r).node k).ballot.val := by
    intro k; rw [after_node]; split
    · subst k; exact g.ballot
    · exact le_refl _
  exact Finset.sup_mono_fun (fun k _ => h k)

theorem world_ext {w w' : World N} (hn : w.node = w'.node) (hp : ∀ p, w.net p ↔ w'.net p) :
    w = w' := by
  cases w; cases w'; simp only at hn; subst hn
  congr; funext p; exact propext (hp p)

theorem after_noop (w : World N) (i : Fin N) : w.after i (.None, w.node i) = w := by
  apply world_ext
  · funext k; rw [after_node]; split <;> simp_all
  · intro p; simp

theorem after_dup (w : World N) (i : Fin N) (s : Send) (h : w.net ⟨i, s⟩) :
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

theorem abs_votes_grow (w : World N) (i : Fin N) (r : Opt Send × Node) {a b v}
    (h : (abs w).votes a b v) : (abs (w.after i r)).votes a b v := by
  obtain ⟨p, hp, rest⟩ := h; exact ⟨p, .inl hp, rest⟩

theorem NodeInv.mono {w w' : World N} {k : Fin N} (h : NodeInv w k) (hn : w'.node k = w.node k)
    (hnet : ∀ p, w.net p → w'.net p) (htop : top w ≤ top w') : NodeInv w' k := by
  obtain ⟨id, size, plen, vlen, own, started, proposed, slot_le, slots, pending, promised_top,
    seen_top, request, votes, undecided, decided⟩ := h
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> rw [hn]
  · exact id
  · exact size
  · exact plen
  · exact vlen
  · exact own
  · intro hb; obtain ⟨a, b⟩ := started hb; exact ⟨a, hnet _ b⟩
  · intro v hv; obtain ⟨a, b⟩ := proposed v hv; exact ⟨a, hnet _ b⟩
  · exact slot_le
  · intro j y hj hb; obtain ⟨p, a, b⟩ := slots j y hj hb; exact ⟨p, hnet _ a, b⟩
  · exact pending
  · omega
  · omega
  · intro v hv; obtain ⟨p, a, b⟩ := request v hv; exact ⟨p, hnet _ a, b⟩
  · intro j vt hj; obtain ⟨p, a, b⟩ := votes j vt hj; exact ⟨p, hnet _ a, b⟩
  · exact undecided
  · intro v hv
    obtain ⟨q, b, hq, hm⟩ := decided v hv
    refine ⟨q, b, hq, fun a ha => ?_⟩
    obtain ⟨p, hp, rest⟩ := hm a ha
    exact ⟨p, hnet _ hp, rest⟩

theorem PacketInv.mono [Cluster N] (w : World N) (i : Fin N) (r : Opt Send × Node)
    (g : Grows (w.node i) r.2) (p : Packet N) (h : PacketInv w p) :
    PacketInv (w.after i r) p := by
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
theorem inv_after [Cluster N] (w : World N) (inv : Inv w) (i : Fin N) (o : Opt Send) (n' : Node)
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

theorem state_ext {s t : PaxosN.State N} (h1 : ∀ a, s.promised a = t.promised a)
    (h2 : ∀ a, s.accepted a = t.accepted a)
    (h3 : ∀ a b x, s.promises a b x ↔ t.promises a b x)
    (h4 : ∀ b v, s.proposals b v ↔ t.proposals b v)
    (h5 : ∀ a b v, s.votes a b v ↔ t.votes a b v) : s = t := by
  cases s; cases t
  simp only [PaxosN.State.mk.injEq]
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

theorem abs_hidden (w : World N) (i : Fin N) (o : Opt Send) (n' : Node)
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
theorem NodeInv.congr {w w' : World N} {k : Fin N} (h : NodeInv w k)
    (hnet : ∀ p, w.net p → w'.net p)
    (hid : (w'.node k).id = (w.node k).id) (hn : (w'.node k).n = (w.node k).n)
    (hb : (w'.node k).ballot = (w.node k).ballot)
    (hpr : (w'.node k).proposal = (w.node k).proposal)
    (hps : (w'.node k).promises = (w.node k).promises)
    (hvs : (w'.node k).votes = (w.node k).votes) (hd : (w'.node k).decided = (w.node k).decided)
    (hv : (w.node k).value ≠ .None → (w'.node k).value ≠ .None)
    (hreq : ∀ v, (w'.node k).value = .Some v → ∃ p, w'.net p ∧ p.send.msg = .Request v)
    (hprom : (w'.node k).promised.val ≤ top w') (hseen : (w'.node k).max_seen.val ≤ top w') :
    NodeInv w' k := by
  have hm := h.mono (w' := { node := w.node, net := w'.net }) rfl hnet (le_refl (top w))
  have eps : ∀ j : Fin N, pslot (w'.node k) j = pslot (w.node k) j := by
    intro j; simp [pslot, hps]
  have evs : ∀ j : Fin N, vslot (w'.node k) j = vslot (w.node k) j := by
    intro j; simp [vslot, hvs]
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, hprom, hseen, hreq, ?_, ?_, ?_⟩
  · rw [hid]; exact h.id
  · rw [hn]; exact h.size
  · rw [hps]; exact h.plen
  · rw [hvs]; exact h.vlen
  · rw [hb]; exact h.own
  · intro hb'; rw [hb] at hb' ⊢
    exact ⟨hv (h.started hb').1, hnet _ (h.started hb').2⟩
  · intro v hp; rw [hpr] at hp; rw [hb]; exact hm.proposed v hp
  · intro j y hj; rw [eps] at hj; rw [hb]; exact h.slot_le j y hj
  · intro j y hj hy; rw [eps] at hj; rw [hb] at hy; exact hm.slots j y hj hy
  · rw [hpr, hps, hb, hn]; exact h.pending
  · intro j vt hj; rw [evs] at hj; exact hm.votes j vt hj
  · rw [hd, hvs, hn]; exact h.undecided
  · intro v hv'; rw [hd] at hv'
    obtain ⟨q, b, hq, hm⟩ := h.decided v hv'
    exact ⟨q, b, hq, fun a ha => by obtain ⟨p, hp, rest⟩ := hm a ha; exact ⟨p, hnet _ hp, rest⟩⟩

/-! ## Counting and quorums -/

theorem slot_eq_getElem {α : Type} (s : RVec (Opt α)) (j : Nat) (h : j < (items s).length) :
    slot s j = (items s)[j] := by
  simp [slot, List.getElem?_eq_getElem h]

theorem slot_none_of_ge {α : Type} (s : RVec (Opt α)) (j : Nat) (h : (items s).length ≤ j) :
    slot s j = .None := by
  simp [slot, List.getElem?_eq_none h]

theorem promiseHit_iff (b : U64) (x : Opt Promise) :
    promiseHit b x = true ↔ ∃ p, x = .Some p ∧ p.ballot = b := by
  cases x <;> simp [promiseHit]

theorem voteHit_iff (v : Vote) (x : Opt Vote) :
    voteHit v x = true ↔ ∃ y, x = .Some y ∧ y.ballot = v.ballot ∧ y.value = v.value := by
  cases x <;> simp [voteHit]

theorem count_promises_card (n : Node) (hlen : (items n.promises).length = N) (b : U64) :
    countPromisesS (items n.promises) b = (promisers (N := N) n b).card := by
  unfold countPromisesS promisers
  rw [countP_eq_card _ _ N hlen]
  congr 1
  apply Finset.filter_congr
  intro j _
  simp only [pslot]; rw [slot_eq_getElem _ _ (by omega)]

theorem count_votes_card (n : Node) (hlen : (items n.votes).length = N) (v : Vote) :
    countVotesS (items n.votes) v = (voters (N := N) n v).card := by
  unfold countVotesS voters
  rw [countP_eq_card _ _ N hlen]
  congr 1
  apply Finset.filter_congr
  intro j _
  simp only [vslot]; rw [slot_eq_getElem _ _ (by omega)]

theorem majority_iff [Cluster N] (c : Nat) : Majority c (u8 N) ↔ N < 2 * c := by
  unfold Majority; rw [u8_val]; omega

theorem mem_promisers (n : Node) (b : U64) (j : Fin N) :
    j ∈ promisers n b ↔ ∃ p, pslot n j = .Some p ∧ p.ballot = b := by
  simp [promisers, promiseHit_iff]

theorem mem_voters (n : Node) (v : Vote) (j : Fin N) :
    j ∈ voters n v ↔ ∃ y, vslot n j = .Some y ∧ y.ballot = v.ballot ∧ y.value = v.value := by
  simp [voters, voteHit_iff]

/-- Nothing counts for a ballot above every recorded promise. -/
theorem count_promises_zero (n : Node) (hlen : (items n.promises).length = N) (b : U64)
    (h : ∀ (j : Fin N) p, pslot n j = .Some p → p.ballot ≠ b) :
    countPromisesS (items n.promises) b = 0 := by
  rw [count_promises_card n hlen, Finset.card_eq_zero, Finset.eq_empty_iff_forall_notMem]
  intro j hj
  obtain ⟨p, hp, hb⟩ := (mem_promisers n b j).mp hj
  exact h j p hp hb

/-- Replacing an entry by a vote other than `v'` does not raise the count of `v'`. -/
theorem count_votes_set_le (l : List (Opt Vote)) (i : Nat) (v v' : Vote) (hne : v' ≠ v)
    (hi : i < l.length) : countVotesS (l.set i (.Some v)) v' ≤ countVotesS l v' := by
  unfold countVotesS
  rw [List.countP_set hi]
  have : voteHit v' (.Some v) = false := by
    simp only [voteHit, decide_eq_false_iff_not]
    intro ⟨h1, h2⟩; apply hne; cases v; cases v'; simp_all
  rw [this]; simp only [Bool.false_eq_true, if_false, Nat.add_zero]; omega

theorem count_learn_le (n : Node) (src : U8) (v v' : Vote) (hne : v' ≠ v)
    (hs : src.val < (items n.votes).length) :
    countVotesS (items (learnS n src v)) v' ≤ countVotesS (items n.votes) v' := by
  unfold learnS; split
  · rw [items_setAt]; exact count_votes_set_le _ _ _ _ hne hs
  · exact le_refl _

end PaxosSystem
