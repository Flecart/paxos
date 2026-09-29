import UserVerification.System

/- Replica-local facts about the extracted transition function. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

/-- What a replica never loses, whatever input it processes. Vector entries are
    indexed by acceptor number (`slot`, out-of-range entries read `None`). -/
structure Grows (n n' : Node) : Prop where
  id : n'.id = n.id
  size : n'.n = n.n
  plen : (items n'.promises).length = (items n.promises).length
  vlen : (items n'.votes).length = (items n.votes).length
  ballot : n.ballot.val ≤ n'.ballot.val
  promised : n.promised.val ≤ n'.promised.val
  seen : n.max_seen.val ≤ n'.max_seen.val
  value : ∀ v, n.value = .Some v → n'.value = .Some v
  proposal : n'.ballot = n.ballot → ∀ v, n.proposal = .Some v → n'.proposal = .Some v
  /-- A promise recorded for the current ballot stays while the ballot is unchanged. -/
  slot : n'.ballot = n.ballot → ∀ j p, PaxosNode.slot n.promises j = .Some p →
    p.ballot = n.ballot → ∃ p', PaxosNode.slot n'.promises j = .Some p' ∧ p'.ballot = n.ballot
  /-- A recorded vote is only replaced by one with a ballot at least as high. -/
  vote : ∀ j vt, PaxosNode.slot n.votes j = .Some vt →
    ∃ vt', PaxosNode.slot n'.votes j = .Some vt' ∧ vt.ballot.val ≤ vt'.ballot.val
  decided : ∀ v, n.decided = .Some v → n'.decided = .Some v

theorem Grows.refl (n : Node) : Grows n n :=
  ⟨rfl, rfl, rfl, rfl, le_refl _, le_refl _, le_refl _, fun _ h => h, fun _ _ h => h,
   fun _ _ p h hb => ⟨p, h, hb⟩, fun _ vt h => ⟨vt, h, le_refl _⟩, fun _ h => h⟩

theorem higherS_val (a b : U64) : (higherS a b).val = max a.val b.val := by
  unfold higherS; split <;> (rename_i h; rw [UScalar.lt_equiv] at h) <;> omega

/-- The floor from which a fresh ballot is allocated. -/
def floorOf (n : Node) : Nat := max (max n.max_seen.val n.promised.val) n.ballot.val

theorem floor_val (n : Node) :
    (higherS (higherS n.max_seen n.promised) n.ballot).val = floorOf n := by
  simp [higherS_val, floorOf]

/-- Replica state after allocating ballot `b`. Recorded promises are kept; they
    are for lower ballots and no longer count. -/
def fresh (n : Node) (b : U64) : Node := { n with ballot := b, proposal := .None }

theorem u8_zero_iff (x : U8) : x = 0#u8 ↔ x.val = 0 := by
  constructor
  · intro h; subst h; rfl
  · intro h; apply UScalar.eq_of_val_eq; simpa using h

theorem start_cases (n : Node) :
    ((n.n.val = 0 ∨ LIMIT ≤ floorOf n) ∧ startS n = (.None, n)) ∨
    (0 < n.n.val ∧ floorOf n < LIMIT ∧
      (startS n).1 = .Some ⟨.All, .Prepare (startS n).2.ballot⟩ ∧
      (startS n).2.ballot.val = (floorOf n / n.n.val + 1) * n.n.val + n.id.val ∧
      (startS n).2 = fresh n (startS n).2.ballot) := by
  unfold startS
  split
  · rename_i h; exact .inl ⟨.inl ((u8_zero_iff _).mp h), rfl⟩
  · rename_i h0
    have hpos : 0 < n.n.val := by
      rcases Nat.eq_zero_or_pos n.n.val with e | e
      · exact absurd ((u8_zero_iff _).mpr e) h0
      · exact e
    simp only [floor_val]
    split
    · exact .inl ⟨.inr (by omega), rfl⟩
    · refine .inr ⟨hpos, by omega, rfl, ?_, rfl⟩
      rw [← floor_val]; exact nextS_val _ _ _ (by rw [floor_val]; omega) hpos

/-- A freshly allocated ballot exceeds the floor. -/
theorem floor_lt_next (f k i : Nat) (hk : 0 < k) : f < (f / k + 1) * k + i := by
  have := Nat.lt_div_mul_add (a := f) hk
  rw [Nat.succ_mul]; omega

theorem start_ballot_gt (n : Node) (hpos : 0 < n.n.val)
    (hb : (startS n).2.ballot.val = (floorOf n / n.n.val + 1) * n.n.val + n.id.val) :
    floorOf n < (startS n).2.ballot.val := by
  rw [hb]; exact floor_lt_next _ _ _ hpos

theorem start_grows (n : Node) : Grows n (startS n).2 := by
  rcases start_cases n with ⟨_, h⟩ | ⟨hpos, _, _, hb, he⟩
  · rw [h]; exact Grows.refl n
  · have gt : n.ballot.val < (startS n).2.ballot.val := by
      have := start_ballot_gt n hpos hb
      have : n.ballot.val ≤ floorOf n := by unfold floorOf; omega
      omega
    have ne : (startS n).2.ballot ≠ n.ballot := fun e => by rw [e] at gt; omega
    generalize (startS n).2.ballot = b at gt ne he
    rw [he]
    exact ⟨rfl, rfl, rfl, rfl, le_of_lt gt, le_refl _, le_refl _, fun _ h => h,
      fun e => absurd e ne, fun e => absurd e ne, fun _ vt h => ⟨vt, h, le_refl _⟩, fun _ h => h⟩

theorem tick_grows (n : Node) : Grows n (tickS n).2 := by
  unfold tickS
  split
  · cases n.value
    · exact Grows.refl n
    · exact start_grows n
  · split
    · exact start_grows n
    · cases n.proposal <;> exact Grows.refl n

/-- Growth for an update that keeps the proposer state and the vectors. -/
theorem grows_of {n n' : Node} (h_id : n'.id = n.id) (h_n : n'.n = n.n)
    (h_b : n'.ballot = n.ballot)
    (h_p : n.promised.val ≤ n'.promised.val) (h_s : n.max_seen.val ≤ n'.max_seen.val)
    (h_v : ∀ v, n.value = .Some v → n'.value = .Some v) (h_pr : n'.proposal = n.proposal)
    (h_ps : n'.promises = n.promises) (h_vs : n'.votes = n.votes)
    (h_d : ∀ v, n.decided = .Some v → n'.decided = .Some v) : Grows n n' :=
  ⟨h_id, h_n, by rw [h_ps], by rw [h_vs], by rw [h_b], h_p, h_s, h_v,
   fun _ v h => by rw [h_pr]; exact h, fun _ j p h hb => ⟨p, by rw [h_ps]; exact h, hb⟩,
   fun _ vt h => ⟨vt, by rw [h_vs]; exact h, le_refl _⟩, h_d⟩

theorem length_setAt {α : Type} (s : RVec α) (i : Nat) (x : α) :
    (items (setAt s i x)).length = (items s).length := by
  rw [items_setAt, List.length_set]

/-- Recording a promise for the current ballot. -/
theorem record_grows (n : Node) (src : U8) (acc : Opt Vote)
    (hs : src.val < (items n.promises).length) :
    Grows n { n with promises := setAt n.promises src.val (.Some ⟨n.ballot, acc⟩) } := by
  refine ⟨rfl, rfl, length_setAt _ _ _, rfl, le_refl _, le_refl _, le_refl _, fun _ h => h,
    fun _ _ h => h, ?_, fun _ vt h => ⟨vt, h, le_refl _⟩, fun _ h => h⟩
  intro _ j p hj hb
  simp only
  rw [slot_setAt _ _ _ _ hs]
  split
  · exact ⟨_, rfl, rfl⟩
  · exact ⟨p, hj, hb⟩

theorem promise_grows (n : Node) (src : U8) (b : U64) (acc : Opt Vote) :
    Grows n (onPromiseS n src b acc).2 := by
  unfold onPromiseS
  by_cases h1 : b ≠ n.ballot
  · rw [if_pos h1]; exact Grows.refl n
  rw [if_neg h1]
  have h1 : b = n.ballot := not_not.mp h1
  subst h1
  by_cases h2 : n.ballot = 0#u64
  · rw [if_pos h2]; exact Grows.refl n
  rw [if_neg h2]
  cases hp : n.proposal
  · simp only []
    split
    · exact Grows.refl n
    rename_i hs
    have hs : src.val < (items n.promises).length := by omega
    have base := record_grows n src acc hs
    generalize setAt n.promises src.val (.Some ⟨n.ballot, acc⟩) = ps at base ⊢
    have gp : ∀ x : Opt U64, Grows n { n with proposal := x, promises := ps } := fun x =>
      ⟨rfl, rfl, base.plen, rfl, le_refl _, le_refl _, le_refl _, fun _ h => h,
        fun _ v h => (by rw [hp] at h; cases h), base.slot, base.vote, fun _ h => h⟩
    split
    · exact gp _
    · split
      · split
        · exact gp _
        · exact gp _
      · exact gp _
  · exact Grows.refl n

theorem newer_le (vt v : Vote) (h : newer (.Some vt) v = true) : vt.ballot.val ≤ v.ballot.val := by
  simp only [newer, decide_eq_true_eq] at h
  rw [UScalar.lt_equiv] at h; omega

/-- The learner's vote vector after announcing `v` from `src`. -/
def learnS (n : Node) (src : U8) (v : Vote) : RVec (Opt Vote) :=
  if newer (slot n.votes src.val) v then setAt n.votes src.val (.Some v) else n.votes

theorem learn_length (n : Node) (src : U8) (v : Vote) :
    (items (learnS n src v)).length = (items n.votes).length := by
  unfold learnS; split
  · exact length_setAt _ _ _
  · rfl

theorem learn_slot (n : Node) (src : U8) (v : Vote) (hs : src.val < (items n.votes).length)
    (j : Nat) : slot (learnS n src v) j =
      if newer (slot n.votes src.val) v ∧ j = src.val then .Some v else slot n.votes j := by
  unfold learnS; split
  · rename_i hn; rw [slot_setAt _ _ _ _ hs]; simp [hn]
  · rename_i hn; simp [hn]

theorem learn_vote (n : Node) (src : U8) (v : Vote) (hs : src.val < (items n.votes).length) :
    ∀ j vt, slot n.votes j = .Some vt →
      ∃ vt', slot (learnS n src v) j = .Some vt' ∧ vt.ballot.val ≤ vt'.ballot.val := by
  intro j vt h
  rw [learn_slot n src v hs]
  split
  · rename_i hc
    obtain ⟨hn, rfl⟩ := hc
    rw [h] at hn
    exact ⟨v, rfl, newer_le vt v hn⟩
  · exact ⟨vt, h, le_refl _⟩

theorem accepted_eq (n : Node) (src : U8) (v : Vote) (hs : src.val < (items n.votes).length) :
    onAcceptedS n src v =
      match n.decided with
      | .None =>
        if Majority (countVotesS (items (learnS n src v)) v) n.n then
          (.None, { n with votes := learnS n src v, decided := .Some v.value })
        else (.None, { n with votes := learnS n src v })
      | .Some _ => (.None, { n with votes := learnS n src v }) := by
  unfold onAcceptedS learnS
  rw [if_neg (by omega)]
  rfl

theorem accepted_grows (n : Node) (src : U8) (v : Vote) :
    Grows n (onAcceptedS n src v).2 := by
  by_cases hs : (items n.votes).length ≤ src.val
  · unfold onAcceptedS; rw [if_pos hs]; exact Grows.refl n
  have hs : src.val < (items n.votes).length := by omega
  rw [accepted_eq n src v hs]
  have gv : ∀ d, (∀ x, n.decided = .Some x → d = .Some x) →
      Grows n { n with votes := learnS n src v, decided := d } := fun d hd =>
    ⟨rfl, rfl, rfl, learn_length n src v, le_refl _, le_refl _, le_refl _, fun _ h => h,
      fun _ _ h => h, fun _ _ p h hb => ⟨p, h, hb⟩, learn_vote n src v hs, hd⟩
  cases hd : n.decided
  · simp only []
    split
    · exact gv _ (fun _ h => by rw [hd] at h; cases h)
    · exact gv _ (fun _ h => by rw [hd] at h; cases h)
  · exact gv _ (fun _ h => by rw [hd] at h; exact h)

theorem grows (n : Node) (inp : Input) : Grows n (handleS n inp).2 := by
  cases inp with
  | Submit v => exact Grows.refl n
  | Tick => exact tick_grows n
  | Deliver src msg =>
    show Grows n (deliverS n src msg).2
    unfold deliverS
    by_cases hs : n.n.val ≤ src.val
    · rw [if_pos hs]; exact Grows.refl n
    rw [if_neg hs]
    cases msg <;> try dsimp only
    case Request v =>
      cases h : n.value
      · exact grows_of rfl rfl rfl (le_refl _) (le_refl _) (fun _ e => by rw [h] at e; cases e) rfl
          rfl rfl (fun _ e => e)
      · exact Grows.refl n
    case Prepare b =>
      unfold onPrepareS; split
      · rename_i h; rw [UScalar.lt_equiv] at h
        exact grows_of rfl rfl rfl (by simp; omega) (le_refl _) (fun _ e => e) rfl rfl rfl
          (fun _ e => e)
      · exact Grows.refl n
    case Promise b acc => exact promise_grows n src b acc
    case Accept v =>
      unfold onAcceptS; split
      · rename_i h; rw [UScalar.le_equiv] at h
        exact grows_of rfl rfl rfl (by simp; omega) (le_refl _) (fun _ e => e) rfl rfl rfl
          (fun _ e => e)
      · exact Grows.refl n
    case Accepted v => exact accepted_grows n src v
    case Nack _ q =>
      split
      · rename_i h; rw [UScalar.lt_equiv] at h
        exact grows_of rfl rfl rfl (le_refl _) (by simp; omega) (fun _ e => e) rfl rfl rfl
          (fun _ e => e)
      · exact Grows.refl n

end PaxosSystem
