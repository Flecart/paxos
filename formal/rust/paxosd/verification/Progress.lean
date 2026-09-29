import UserVerification.Safety

/- Replica-level effects and execution-level monotonicity used by liveness. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

set_option linter.unusedSectionVars false

variable {N : Nat}

/-! ## Effects of individual inputs -/

theorem deliver_keeps_ballot (n : Node) (src : U8) (msg : Msg) :
    (deliverS n src msg).2.ballot = n.ballot := by
  unfold deliverS
  split
  · rfl
  cases msg <;> simp only [onPrepareS, onPromiseS, onAcceptS, onAcceptedS] <;>
    (repeat' split) <;> rfl

/-- Only the timer changes a replica's ballot, and then to a fresh owned ballot
    just above everything the replica has seen. -/
theorem ballot_moves (n : Node) (inp : Input) (h : (handleS n inp).2.ballot ≠ n.ballot) :
    (n.ballot.val = 0 ∨ n.ballot.val < n.max_seen.val) ∧
    (handleS n inp).2.ballot.val = (floorOf n / n.n.val + 1) * n.n.val + n.id.val := by
  cases inp with
  | Submit v => exact absurd rfl h
  | Deliver src msg => exact absurd (deliver_keeps_ballot n src msg) h
  | Tick =>
    simp only [handleS, tickS] at h ⊢
    have st : (startS n).2.ballot ≠ n.ballot →
        (startS n).2.ballot.val = (floorOf n / n.n.val + 1) * n.n.val + n.id.val := by
      intro hs
      rcases start_cases n with ⟨_, e⟩ | ⟨_, _, _, hb, _⟩
      · rw [e] at hs; exact absurd rfl hs
      · exact hb
    by_cases h0 : n.ballot = 0#u64
    · rw [if_pos h0] at h ⊢
      have : n.ballot.val = 0 := by rw [h0]; rfl
      cases hv : n.value
      · simp only [hv] at h; exact absurd rfl h
      · simp only [hv] at h ⊢; exact ⟨.inl this, st h⟩
    · rw [if_neg h0] at h ⊢
      by_cases hlt : n.ballot < n.max_seen
      · rw [if_pos hlt] at h ⊢; rw [UScalar.lt_equiv] at hlt; exact ⟨.inr hlt, st h⟩
      · rw [if_neg hlt] at h; cases hp : n.proposal <;> rw [hp] at h <;> exact absurd rfl h

/-- A timer tick with a pending attempt to (re)start does allocate a new ballot. -/
theorem tick_moves (n : Node) (hn : 0 < n.n.val) (hf : floorOf n < LIMIT)
    (h : (n.ballot.val = 0 ∧ n.value ≠ .None) ∨ (n.ballot.val ≠ 0 ∧ n.ballot.val < n.max_seen.val)) :
    (handleS n .Tick).2.ballot ≠ n.ballot := by
  have st : (startS n).2.ballot ≠ n.ballot := by
    rcases start_cases n with ⟨hl, _⟩ | ⟨hpos, _, _, hb, _⟩
    · omega
    · intro e
      have gt := start_ballot_gt n hpos hb
      rw [e] at gt; unfold floorOf at gt; omega
  simp only [handleS, tickS]
  split
  · rename_i h0
    have : n.ballot.val = 0 := by rw [h0]; rfl
    rcases h with ⟨_, hv⟩ | ⟨h1, _⟩
    · cases hn : n.value
      · exact absurd hn hv
      · exact st
    · exact absurd this h1
  · rename_i h0
    have h0' : n.ballot.val ≠ 0 := fun e => h0 (UScalar.eq_of_val_eq (by simpa using e))
    rcases h with ⟨h1, _⟩ | ⟨_, hlt⟩
    · exact absurd h1 h0'
    · rw [if_pos (by rw [UScalar.lt_equiv]; exact hlt)]; exact st

section Local
variable [Cluster N]

theorem prepare_output (n : Node) (hn : n.n = u8 N) (j : Fin N) (b : U64) :
    (handleS n (.Deliver (rid j) (.Prepare b))).1 =
      if n.promised.val < b.val then .Some ⟨.To (rid j), .Promise b n.accepted⟩
      else .Some ⟨.To (rid j), .Nack b n.promised⟩ := by
  simp only [handleS]; rw [deliver_rid n hn]
  simp only [onPrepareS, UScalar.lt_equiv]
  split <;> rfl

theorem accept_output (n : Node) (hn : n.n = u8 N) (j : Fin N) (vt : Vote) :
    (handleS n (.Deliver (rid j) (.Accept vt))).1 =
      if n.promised.val ≤ vt.ballot.val then .Some ⟨.All, .Accepted vt⟩
      else .Some ⟨.To (rid j), .Nack vt.ballot n.promised⟩ := by
  simp only [handleS]; rw [deliver_rid n hn]
  simp only [onAcceptS, UScalar.le_equiv]
  split <;> rfl

theorem nack_raises (n : Node) (hn : n.n = u8 N) (j : Fin N) (x q : U64) :
    q.val ≤ (handleS n (.Deliver (rid j) (.Nack x q))).2.max_seen.val := by
  simp only [handleS]; rw [deliver_rid n hn]
  simp only []
  split
  · simp
  · rename_i h; rw [UScalar.lt_equiv] at h; simp only; omega

theorem request_sets (n : Node) (hn : n.n = u8 N) (j : Fin N) (v : U64) :
    (handleS n (.Deliver (rid j) (.Request v))).2.value ≠ .None := by
  simp only [handleS]; rw [deliver_rid n hn]
  simp only []
  split
  · simp
  · rename_i h; rw [h]; simp

/-- Delivering a promise for the current ballot, before any proposal, records
    an entry tagged with that ballot. -/
theorem promise_records (n : Node) (hn : n.n = u8 N) (hlen : (items n.promises).length = N)
    (j : Fin N) (b : U64) (y : Opt Vote) (hb : n.ballot = b)
    (h0 : b ≠ 0#u64) (hp : n.proposal = .None) :
    ∃ p, pslot (handleS n (.Deliver (rid j) (.Promise b y))).2 j = .Some p ∧ p.ballot = b := by
  have hs : (rid j).val < (items n.promises).length := by rw [hlen, rid_val]; exact j.isLt
  have hrec : ∀ m : Node, m.promises = setAt n.promises (rid j).val (.Some ⟨n.ballot, y⟩) →
      ∃ p, pslot m j = .Some p ∧ p.ballot = b := by
    intro m hm
    refine ⟨⟨n.ballot, y⟩, ?_, hb⟩
    simp only [pslot]; rw [hm, slot_setAt _ _ _ _ hs, if_pos (by rw [rid_val])]
  simp only [handleS]; rw [deliver_rid n hn]
  simp only [onPromiseS]
  subst hb
  rw [if_neg (fun h => h rfl), if_neg h0]
  simp only [hp]
  rw [if_neg (by omega)]
  split
  · exact hrec _ rfl
  split
  · split <;> exact hrec _ rfl
  · exact hrec _ rfl

theorem accepted_records (n : Node) (hn : n.n = u8 N) (hlen : (items n.votes).length = N)
    (j : Fin N) (vt : Vote) :
    ∃ vt', vslot (handleS n (.Deliver (rid j) (.Accepted vt))).2 j = .Some vt' ∧
      vt.ballot.val ≤ vt'.ballot.val := by
  have hs : (rid j).val < (items n.votes).length := by rw [hlen, rid_val]; exact j.isLt
  have hm : ∀ m : Node, m.votes = learnS n (rid j) vt →
      ∃ vt', vslot m j = .Some vt' ∧ vt.ballot.val ≤ vt'.ballot.val := by
    intro m hm
    simp only [vslot]; rw [hm, learn_slot _ _ _ hs]
    have hj : j.val = (rid j).val := by rw [rid_val]
    split
    · exact ⟨vt, rfl, le_refl _⟩
    · rename_i hc
      have hn' : newer (slot n.votes (rid j).val) vt = false := by
        cases h : newer (slot n.votes (rid j).val) vt
        · rfl
        · exact absurd ⟨h, hj⟩ hc
      rw [hj]
      cases hsl : slot n.votes (rid j).val with
      | none => rw [hsl] at hn'; simp [newer] at hn'
      | some old =>
        rw [hsl] at hn'
        simp only [newer, decide_eq_false_iff_not, UScalar.lt_equiv, not_lt] at hn'
        exact ⟨old, rfl, hn'⟩
  simp only [handleS]; rw [deliver_rid n hn]
  simp only []
  rw [accepted_eq _ _ _ hs]
  split
  · split
    · exact hm _ rfl
    · exact hm _ rfl
  · exact hm _ rfl

end Local

/-! ## Monotonicity along executions -/

theorem Grows.trans {a b c : Node} (h1 : Grows a b) (h2 : Grows b c) : Grows a c := by
  have eqb : c.ballot = a.ballot → b.ballot = a.ballot := by
    intro e; apply UScalar.eq_of_val_eq
    have := h1.ballot; have := h2.ballot; rw [e] at *; omega
  refine ⟨h2.id.trans h1.id, h2.size.trans h1.size, h2.plen.trans h1.plen, h2.vlen.trans h1.vlen,
    le_trans h1.ballot h2.ballot, le_trans h1.promised h2.promised,
    le_trans h1.seen h2.seen, fun v h => h2.value v (h1.value v h), ?_, ?_, ?_,
    fun v h => h2.decided v (h1.decided v h)⟩
  · intro e v h
    have e1 := eqb e
    exact h2.proposal (e.trans e1.symm) v (h1.proposal e1 v h)
  · intro e j p h hb
    have e1 := eqb e
    obtain ⟨p1, hp1, hb1⟩ := h1.slot e1 j p h hb
    obtain ⟨p2, hp2, hb2⟩ := h2.slot (e.trans e1.symm) j p1 hp1 (hb1.trans e1.symm)
    exact ⟨p2, hp2, hb2.trans e1⟩
  · intro j vt h
    obtain ⟨v1, h1', l1⟩ := h1.vote j vt h
    obtain ⟨v2, h2', l2⟩ := h2.vote j v1 h1'
    exact ⟨v2, h2', le_trans l1 l2⟩

section Execution
variable [Cluster N] {run : Nat → World N} (exec : Reactive.Execution (module N) run)
include exec

theorem run_step (n : Nat) : run (n+1) = run n ∨
    ∃ i inp, Allowed (run n) i inp ∧ run (n+1) = (run n).after i (handleS ((run n).node i) inp) :=
  (step_iff _ _).mp (by simpa [module, Reactive.Module.step] using exec.2 n)

theorem run_inv (n : Nat) : Inv (run n) ∧ Reactive.Reachable (PaxosN.module N) (abs (run n)) :=
  reachable_inv _ (Reactive.execution_reachable (module N) run exec n)

theorem step_grows (n : Nat) (k : Fin N) : Grows ((run n).node k) ((run (n+1)).node k) := by
  rcases run_step exec n with e | ⟨i, inp, _, e⟩
  · rw [e]; exact Grows.refl _
  · rw [e, after_node]; split
    · rename_i h; subst h; exact grows _ _
    · exact Grows.refl _

theorem step_net (n : Nat) (p : Packet N) (h : (run n).net p) : (run (n+1)).net p := by
  rcases run_step exec n with e | ⟨i, inp, _, e⟩
  · rw [e]; exact h
  · rw [e]; exact .inl h

theorem run_grows (n m : Nat) (h : n ≤ m) (k : Fin N) :
    Grows ((run n).node k) ((run m).node k) := by
  induction m, h using Nat.le_induction with
  | base => exact Grows.refl _
  | succ m _ ih => exact ih.trans (step_grows exec m k)

theorem run_net (n m : Nat) (h : n ≤ m) (p : Packet N) (hp : (run n).net p) : (run m).net p := by
  induction m, h using Nat.le_induction with
  | base => exact hp
  | succ m _ ih => exact step_net exec m p ih

end Execution

/-- A monotone natural sequence bounded after `T` is eventually constant. -/
theorem eventually_const (f : Nat → Nat) (T K : Nat) (mono : ∀ n, T ≤ n → f n ≤ f (n+1))
    (bound : ∀ n, T ≤ n → f n ≤ K) : ∃ n1, T ≤ n1 ∧ ∀ n, n1 ≤ n → f n = f n1 := by
  have mono' : ∀ n m, T ≤ n → n ≤ m → f n ≤ f m := by
    intro n m hn hm
    induction m, hm using Nat.le_induction with
    | base => exact le_refl _
    | succ m hm ih => exact le_trans ih (mono m (le_trans hn hm))
  suffices h : ∀ d t, T ≤ t → K - f t ≤ d → ∃ n1, t ≤ n1 ∧ ∀ n, n1 ≤ n → f n = f n1 by
    obtain ⟨n1, h1, h2⟩ := h _ T le_rfl le_rfl; exact ⟨n1, h1, h2⟩
  intro d
  induction d with
  | zero =>
    intro t ht hd
    refine ⟨t, le_rfl, fun n hn => ?_⟩
    have := mono' t n ht hn; have := bound n (le_trans ht hn); have := bound t ht; omega
  | succ d ih =>
    intro t ht hd
    by_cases hc : ∀ n, t ≤ n → f n = f t
    · exact ⟨t, le_rfl, hc⟩
    · push Not at hc
      obtain ⟨m, hm, hne⟩ := hc
      have hlt : f t < f m := lt_of_le_of_ne (mono' t m ht hm) (Ne.symm hne)
      obtain ⟨n1, h1, h2⟩ := ih m (le_trans ht hm) (by have := bound m (le_trans ht hm); omega)
      exact ⟨n1, le_trans hm h1, h2⟩

end PaxosSystem
