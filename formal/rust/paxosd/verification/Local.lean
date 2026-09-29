import UserVerification.System

/- Replica-local facts about the extracted transition function. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

/-- What a replica never loses, whatever input it processes. -/
structure Grows (n n' : Node) : Prop where
  id : n'.id = n.id
  ballot : n.ballot.val ≤ n'.ballot.val
  promised : n.promised.val ≤ n'.promised.val
  seen : n.max_seen.val ≤ n'.max_seen.val
  value : ∀ v, n.value = .Some v → n'.value = .Some v
  proposal : n'.ballot = n.ballot → ∀ v, n.proposal = .Some v → n'.proposal = .Some v
  slot : n'.ballot = n.ballot → ∀ j, pslot n j ≠ .None → pslot n' j ≠ .None
  vote : ∀ j vt, vslot n j = .Some vt → ∃ vt', vslot n' j = .Some vt' ∧ vt.ballot.val ≤ vt'.ballot.val
  decided : ∀ v, n.decided = .Some v → n'.decided = .Some v

theorem Grows.refl (n : Node) : Grows n n :=
  ⟨rfl, le_refl _, le_refl _, le_refl _, fun _ h => h, fun _ _ h => h, fun _ _ h => h,
   fun _ vt h => ⟨vt, h, le_refl _⟩, fun _ h => h⟩

theorem higherS_val (a b : U64) : (higherS a b).val = max a.val b.val := by
  unfold higherS; split <;> (rename_i h; rw [UScalar.lt_equiv] at h) <;> omega

/-- The floor from which a fresh ballot is allocated. -/
def floorOf (n : Node) : Nat := max (max n.max_seen.val n.promised.val) n.ballot.val

theorem floor_val (n : Node) :
    (higherS (higherS n.max_seen n.promised) n.ballot).val = floorOf n := by
  simp [higherS_val, floorOf]

/-- Replica state after allocating ballot `b`. -/
def fresh (n : Node) (b : U64) : Node :=
  { n with ballot := b, proposal := .None, promise0 := .None, promise1 := .None, promise2 := .None }

theorem start_cases (n : Node) :
    (LIMIT ≤ floorOf n ∧ startS n = (.None, n)) ∨
    (floorOf n < LIMIT ∧
      (startS n).1 = .Some ⟨.All, .Prepare (startS n).2.ballot⟩ ∧
      (startS n).2.ballot.val = (floorOf n / 3 + 1) * 3 + n.id.val ∧
      (startS n).2 = fresh n (startS n).2.ballot) := by
  unfold startS
  simp only [floor_val]
  split
  · exact .inl ⟨by omega, rfl⟩
  · refine .inr ⟨by omega, rfl, ?_, rfl⟩
    rw [← floor_val]; exact nextS_val _ _ (by rw [floor_val]; omega)

theorem grows_of {n n' : Node} (h_id : n'.id = n.id) (h_b : n'.ballot = n.ballot)
    (h_p : n.promised.val ≤ n'.promised.val) (h_s : n.max_seen.val ≤ n'.max_seen.val)
    (h_v : ∀ v, n.value = .Some v → n'.value = .Some v) (h_pr : n'.proposal = n.proposal)
    (h_sl : ∀ j, pslot n j ≠ .None → pslot n' j ≠ .None)
    (h_vote : ∀ j vt, vslot n j = .Some vt → ∃ vt', vslot n' j = .Some vt' ∧ vt.ballot.val ≤ vt'.ballot.val)
    (h_d : ∀ v, n.decided = .Some v → n'.decided = .Some v) : Grows n n' :=
  ⟨h_id, by rw [h_b], h_p, h_s, h_v, fun _ v h => by rw [h_pr]; exact h, fun _ => h_sl, h_vote, h_d⟩

theorem start_grows (n : Node) : Grows n (startS n).2 := by
  rcases start_cases n with ⟨_, h⟩ | ⟨hl, _, hb, he⟩
  · rw [h]; exact Grows.refl n
  · have gt : n.ballot.val < (startS n).2.ballot.val := by
      rw [hb]; unfold floorOf; omega
    have ne : (startS n).2.ballot ≠ n.ballot := fun e => by rw [e] at gt; omega
    generalize (startS n).2.ballot = b at gt ne he
    rw [he]
    refine ⟨rfl, le_of_lt gt, le_refl _, le_refl _, fun _ h => h, fun e => absurd e ne,
      fun e => absurd e ne, fun _ vt h => ⟨vt, by simpa [vslot, fresh] using h, le_refl _⟩, fun _ h => h⟩

theorem tick_grows (n : Node) : Grows n (tickS n).2 := by
  unfold tickS
  split
  · cases n.value
    · exact Grows.refl n
    · exact start_grows n
  · split
    · exact start_grows n
    · cases n.proposal <;> exact Grows.refl n

theorem u8_zero_iff (x : U8) : x = 0#u8 ↔ x.val = 0 := by
  constructor
  · intro h; subst h; rfl
  · intro h; apply UScalar.eq_of_val_eq; simpa using h

theorem u8_one_iff (x : U8) : x = 1#u8 ↔ x.val = 1 := by
  constructor
  · intro h; subst h; rfl
  · intro h; apply UScalar.eq_of_val_eq; simpa using h

theorem pslot_record (n : Node) (src : U8) (acc : Opt Vote) (j : Rid) (hs : src.val < 3) :
    pslot (recordS n src acc) j = if j.val = src.val then .Some acc else pslot n j := by
  unfold pslot recordS
  simp only [u8_zero_iff, u8_one_iff]
  have := j.isLt
  split_ifs <;> simp_all <;> omega

theorem vslot_set (n : Node) (src : U8) (v : Vote) (j : Rid) (hs : src.val < 3) :
    vslot (setVote n src v) j = if j.val = src.val then .Some v else vslot n j := by
  unfold vslot setVote
  simp only [u8_zero_iff, u8_one_iff]
  have := j.isLt
  split_ifs <;> simp_all <;> omega

theorem voteAt_eq (n : Node) (j : Rid) : voteAt n (rid j) = vslot n j := by
  unfold voteAt vslot
  simp only [u8_zero_iff, u8_one_iff, rid_val]

theorem record_fields (n : Node) (src : U8) (acc : Opt Vote) :
    (recordS n src acc).ballot = n.ballot ∧ (recordS n src acc).proposal = n.proposal ∧
    (recordS n src acc).value = n.value ∧ (recordS n src acc).id = n.id ∧
    (recordS n src acc).promised = n.promised ∧ (recordS n src acc).accepted = n.accepted ∧
    (recordS n src acc).max_seen = n.max_seen ∧ (recordS n src acc).vote0 = n.vote0 ∧
    (recordS n src acc).vote1 = n.vote1 ∧ (recordS n src acc).vote2 = n.vote2 ∧
    (recordS n src acc).decided = n.decided := by
  unfold recordS; split_ifs <;> simp

theorem setVote_fields (n : Node) (src : U8) (v : Vote) :
    (setVote n src v).ballot = n.ballot ∧ (setVote n src v).proposal = n.proposal ∧
    (setVote n src v).value = n.value ∧ (setVote n src v).id = n.id ∧
    (setVote n src v).promised = n.promised ∧ (setVote n src v).accepted = n.accepted ∧
    (setVote n src v).max_seen = n.max_seen ∧ (setVote n src v).promise0 = n.promise0 ∧
    (setVote n src v).promise1 = n.promise1 ∧ (setVote n src v).promise2 = n.promise2 ∧
    (setVote n src v).decided = n.decided := by
  unfold setVote; split_ifs <;> simp

theorem record_grows (n : Node) (src : U8) (acc : Opt Vote) (hs : src.val < 3) :
    Grows n (recordS n src acc) := by
  obtain ⟨e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11⟩ := record_fields n src acc
  refine grows_of e4 e1 (by rw [e5]) (by rw [e7]) (fun v h => by rw [e3]; exact h) e2 ?_ ?_
    (fun v h => by rw [e11]; exact h)
  · intro j hj
    rw [pslot_record n src acc j hs]; split
    · simp
    · exact hj
  · intro j vt hj
    exact ⟨vt, by simpa [vslot, e8, e9, e10] using hj, le_refl _⟩

theorem promise_grows (n : Node) (src : U8) (b : U64) (acc : Opt Vote) (hs : src.val < 3) :
    Grows n (onPromiseS n src b acc).2 := by
  unfold onPromiseS
  by_cases h1 : b ≠ n.ballot
  · rw [if_pos h1]; exact Grows.refl n
  rw [if_neg h1]
  by_cases h2 : b = 0#u64
  · rw [if_pos h2]; exact Grows.refl n
  rw [if_neg h2]
  cases hp : n.proposal
  · have base := record_grows n src acc hs
    obtain ⟨e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11⟩ := record_fields n src acc
    cases hv : n.value
    · exact base
    · simp only []
      cases hq : quorumS (recordS n src acc).promise0 (recordS n src acc).promise1
          (recordS n src acc).promise2
      · exact base
      · simp only []
        refine ⟨by simp [e4], by simp [e1], by simp [e5], by simp [e7], by simp [e3], ?_, ?_, ?_,
          by simp [e11]⟩
        · intro _ v h; rw [hp] at h; cases h
        · intro _ j hj
          have := base.slot e1 j hj
          simpa [pslot] using this
        · intro j vt hj
          exact ⟨vt, by simpa [vslot, e8, e9, e10] using hj, le_refl _⟩
  · exact Grows.refl n

theorem setVote_grows (n : Node) (src : U8) (v : Vote) (hs : src.val < 3)
    (hn : newer (voteAt n src) v = true) : Grows n (setVote n src v) := by
  obtain ⟨e1, e2, e3, e4, e5, e6, e7, e8, e9, e10, e11⟩ := setVote_fields n src v
  refine grows_of e4 e1 (by rw [e5]) (by rw [e7]) (fun v h => by rw [e3]; exact h) e2 ?_ ?_
    (fun v h => by rw [e11]; exact h)
  · intro j hj; simpa [pslot, e8, e9, e10] using hj
  · intro j vt hj
    rw [vslot_set n src v j hs]
    split
    · rename_i hjs
      refine ⟨v, rfl, ?_⟩
      have hsrc : src = rid j := by apply UScalar.eq_of_val_eq; simp [hjs]
      rw [hsrc, voteAt_eq, hj] at hn
      simp only [newer, decide_eq_true_eq] at hn
      rw [UScalar.lt_equiv] at hn; omega
    · exact ⟨vt, hj, le_refl _⟩

theorem accepted_grows (n : Node) (src : U8) (v : Vote) (hs : src.val < 3) :
    Grows n (onAcceptedS n src v).2 := by
  have hm : Grows n (if newer (voteAt n src) v = true then setVote n src v else n) := by
    split
    · rename_i hn; exact setVote_grows n src v hs hn
    · exact Grows.refl n
  unfold onAcceptedS
  generalize (if newer (voteAt n src) v = true then setVote n src v else n) = m at hm ⊢
  cases hd : n.decided
  · exact ⟨hm.id, hm.ballot, hm.promised, hm.seen, hm.value, hm.proposal,
      fun e => hm.slot e, fun j vt h => by simpa [vslot] using hm.vote j vt h,
      fun _ h => by rw [hd] at h; cases h⟩
  · exact hm

theorem grows (n : Node) (inp : Input) : Grows n (handleS n inp).2 := by
  cases inp with
  | Submit v => exact Grows.refl n
  | Tick => exact tick_grows n
  | Deliver src msg =>
    unfold handleS deliverS
    by_cases hs : 3 ≤ src.val
    · simp only [hs, if_true]; exact Grows.refl n
    simp only [hs, if_false]
    have hs : src.val < 3 := by omega
    cases msg <;> dsimp only
    case Request v =>
      cases h : n.value
      · exact grows_of rfl rfl (le_refl _) (le_refl _) (fun _ e => by rw [h] at e; cases e) rfl
          (fun _ e => e) (fun _ vt e => ⟨vt, by simpa [vslot] using e, le_refl _⟩) (fun _ e => e)
      · exact Grows.refl n
    case Prepare b =>
      unfold onPrepareS; split
      · rename_i h; rw [UScalar.lt_equiv] at h
        exact grows_of rfl rfl (by simp; omega) (le_refl _) (fun _ e => e) rfl
          (fun _ e => e) (fun _ vt e => ⟨vt, by simpa [vslot] using e, le_refl _⟩) (fun _ e => e)
      · exact Grows.refl n
    case Promise b acc => exact promise_grows n src b acc hs
    case Accept v =>
      unfold onAcceptS; split
      · rename_i h; rw [UScalar.le_equiv] at h
        exact grows_of rfl rfl (by simp; omega) (le_refl _) (fun _ e => e) rfl
          (fun _ e => e) (fun _ vt e => ⟨vt, by simpa [vslot] using e, le_refl _⟩) (fun _ e => e)
      · exact Grows.refl n
    case Accepted v => exact accepted_grows n src v hs
    case Nack _ q =>
      split
      · rename_i h; rw [UScalar.lt_equiv] at h
        exact grows_of rfl rfl (le_refl _) (by simp; omega) (fun _ e => e) rfl
          (fun _ e => e) (fun _ vt e => ⟨vt, by simpa [vslot] using e, le_refl _⟩) (fun _ e => e)
      · exact Grows.refl n

end PaxosSystem
