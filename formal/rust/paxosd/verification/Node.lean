import DeployablePaxos.Extraction

/- Pure characterisation of the extracted replica state machine.
   Every extracted function is proved equal to `ok` of a total Lean function,
   so the Rust code never panics and all later reasoning uses these equations. -/
namespace PaxosNode
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos
set_option Aeneas.Deprecated.progressWarning false

abbrev Opt := core.option.Option

def LIMIT : Nat := 4611686018427387904

def higherS (a b : U64) : U64 := if a < b then b else a

def nextS (floor : U64) (id : U8) : U64 :=
  ⟨BitVec.ofNat 64 ((floor.val / 3 + 1) * 3 + id.val)⟩

def selectS (l r : Opt Vote) (offered : U64) : U64 :=
  match l, r with
  | .None, .None => offered
  | .None, .Some b => b.value
  | .Some a, .None => a.value
  | .Some a, .Some b => if a.ballot < b.ballot then b.value else a.value

def Same (a b : Vote) : Prop := a.ballot = b.ballot ∧ a.value = b.value

instance (a b : Vote) : Decidable (Same a b) := by unfold Same; infer_instance

def agreedS (v0 v1 v2 : Opt Vote) : Opt U64 :=
  match v0, v1, v2 with
  | .None, .None, _ => .None
  | .None, .Some _, .None => .None
  | .None, .Some b, .Some c => if Same b c then .Some b.value else .None
  | .Some _, .None, .None => .None
  | .Some a, .None, .Some c => if Same a c then .Some a.value else .None
  | .Some a, .Some b, .None => if Same a b then .Some a.value else .None
  | .Some a, .Some b, .Some c =>
    if Same a b then .Some a.value
    else if Same a c then .Some a.value
    else if Same b c then .Some b.value else .None

def quorumS (p0 p1 p2 : Opt (Opt Vote)) : Opt (Opt Vote × Opt Vote) :=
  match p0, p1, p2 with
  | .None, .None, _ => .None
  | .None, .Some _, .None => .None
  | .None, .Some b, .Some c => .Some (b, c)
  | .Some _, .None, .None => .None
  | .Some a, .None, .Some c => .Some (a, c)
  | .Some a, .Some b, _ => .Some (a, b)

def startS (n : Node) : Opt Send × Node :=
  let floor := higherS (higherS n.max_seen n.promised) n.ballot
  if LIMIT ≤ floor.val then (.None, n)
  else
    let b := nextS floor n.id
    (.Some ⟨.All, .Prepare b⟩,
      { n with ballot := b, proposal := .None, promise0 := .None,
               promise1 := .None, promise2 := .None })

def tickS (n : Node) : Opt Send × Node :=
  if n.ballot = 0#u64 then
    match n.value with
    | .None => (.None, n)
    | .Some _ => startS n
  else if n.ballot < n.max_seen then startS n
  else
    match n.proposal with
    | .None => (.Some ⟨.All, .Prepare n.ballot⟩, n)
    | .Some v => (.Some ⟨.All, .Accept ⟨n.ballot, v⟩⟩, n)

def onPrepareS (n : Node) (src : U8) (b : U64) : Opt Send × Node :=
  if n.promised < b then (.Some ⟨.To src, .Promise b n.accepted⟩, { n with promised := b })
  else (.Some ⟨.To src, .Nack b n.promised⟩, n)

def onAcceptS (n : Node) (src : U8) (v : Vote) : Opt Send × Node :=
  if n.promised ≤ v.ballot then
    (.Some ⟨.All, .Accepted v⟩, { n with promised := v.ballot, accepted := .Some v })
  else (.Some ⟨.To src, .Nack v.ballot n.promised⟩, n)

def recordS (n : Node) (src : U8) (acc : Opt Vote) : Node :=
  if src = 0#u8 then { n with promise0 := .Some acc }
  else if src = 1#u8 then { n with promise1 := .Some acc }
  else { n with promise2 := .Some acc }

def onPromiseS (n : Node) (src : U8) (b : U64) (acc : Opt Vote) : Opt Send × Node :=
  if b ≠ n.ballot then (.None, n)
  else if b = 0#u64 then (.None, n)
  else match n.proposal with
    | .Some _ => (.None, n)
    | .None =>
      let m := recordS n src acc
      match n.value with
      | .None => (.None, m)
      | .Some v =>
        match quorumS m.promise0 m.promise1 m.promise2 with
        | .None => (.None, m)
        | .Some (l, r) =>
          (.Some ⟨.All, .Accept ⟨b, selectS l r v⟩⟩, { m with proposal := .Some (selectS l r v) })

def voteAt (n : Node) (src : U8) : Opt Vote :=
  if src = 0#u8 then n.vote0 else if src = 1#u8 then n.vote1 else n.vote2

def setVote (n : Node) (src : U8) (v : Vote) : Node :=
  if src = 0#u8 then { n with vote0 := .Some v }
  else if src = 1#u8 then { n with vote1 := .Some v }
  else { n with vote2 := .Some v }

def newer (cur : Opt Vote) (v : Vote) : Bool :=
  match cur with
  | .None => true
  | .Some old => decide (old.ballot < v.ballot)

def onAcceptedS (n : Node) (src : U8) (v : Vote) : Opt Send × Node :=
  let m := if newer (voteAt n src) v then setVote n src v else n
  match n.decided with
  | .None => (.None, { m with decided := agreedS m.vote0 m.vote1 m.vote2 })
  | .Some _ => (.None, m)

def deliverS (n : Node) (src : U8) (msg : Msg) : Opt Send × Node :=
  if 3 ≤ src.val then (.None, n)
  else match msg with
    | .Request v =>
      match n.value with
      | .None => (.None, { n with value := .Some v })
      | .Some _ => (.None, n)
    | .Prepare b => onPrepareS n src b
    | .Promise b acc => onPromiseS n src b acc
    | .Accept v => onAcceptS n src v
    | .Accepted v => onAcceptedS n src v
    | .Nack _ p => if n.max_seen < p then (.None, { n with max_seen := p }) else (.None, n)

def handleS (n : Node) : Input → Opt Send × Node
  | .Submit v => (.Some ⟨.All, .Request v⟩, n)
  | .Deliver src msg => deliverS n src msg
  | .Tick => tickS n

def initS (id : U8) : Node :=
  { id, promised := 0#u64, accepted := .None, value := .None, ballot := 0#u64,
    max_seen := 0#u64, proposal := .None, promise0 := .None, promise1 := .None,
    promise2 := .None, vote0 := .None, vote1 := .None, vote2 := .None, decided := .None }

/-! ## Extracted functions equal the pure specification -/

theorem new_eq (id : U8) : Node.new id = ok (initS id) := rfl

theorem higher_eq (a b : U64) : higher a b = ok (higherS a b) := by
  unfold higher higherS; split <;> rfl

theorem nextS_val (floor : U64) (id : U8) (h : floor.val < LIMIT) :
    (nextS floor id).val = (floor.val / 3 + 1) * 3 + id.val := by
  have hid : id.bv.toNat < 2 ^ 8 := id.bv.isLt
  show (BitVec.ofNat 64 ((floor.val / 3 + 1) * 3 + id.bv.toNat)).toNat = _
  rw [BitVec.toNat_ofNat]; apply Nat.mod_eq_of_lt
  unfold LIMIT at h; show _ < 2 ^ 64; omega

theorem next_ballot_eq (floor : U64) (id : U8) (h : floor.val < LIMIT) :
    next_ballot floor id = ok (nextS floor id) := by
  have spec : next_ballot floor id ⦃ b => b.val = (floor.val / 3 + 1) * 3 + id.val ⦄ := by
    unfold next_ballot; unfold LIMIT at h; step*
  obtain ⟨b, hb, hv⟩ := (WP.spec_equiv_exists _ _).mp spec
  rw [hb]; congr 1
  apply UScalar.eq_of_val_eq; rw [hv, nextS_val floor id h]

theorem select_eq (l r : Opt Vote) (offered : U64) :
    select l r offered = ok (selectS l r offered) := by
  cases l <;> cases r <;> simp [select, selectS]
  split <;> rfl

theorem same_eq (a b : Vote) : same a b = ok (decide (Same a b)) := by
  unfold same Same; by_cases h : a.ballot = b.ballot <;> simp [h]

theorem agreed_eq (v0 v1 v2 : Opt Vote) : agreed v0 v1 v2 = ok (agreedS v0 v1 v2) := by
  cases v0 <;> cases v1 <;> cases v2 <;> simp only [agreed, agreedS, same_eq, bind_tc_ok] <;>
    (repeat' split) <;> simp_all

theorem quorum_eq (p0 p1 p2 : Opt (Opt Vote)) : quorum p0 p1 p2 = ok (quorumS p0 p1 p2) := by
  cases p0 <;> cases p1 <;> cases p2 <;> rfl

theorem start_eq (n : Node) : Node.start n = ok (startS n) := by
  unfold Node.start startS
  simp only [higher_eq, bind_tc_ok, BALLOT_LIMIT]
  generalize higherS (higherS n.max_seen n.promised) n.ballot = f
  by_cases h : LIMIT ≤ f.val
  · have : (4611686018427387904#u64 : U64) ≤ f := by
      rw [UScalar.le_equiv]; simpa [LIMIT] using h
    simp [this, h]
  · have : ¬ (4611686018427387904#u64 : U64) ≤ f := by
      rw [UScalar.le_equiv]; simpa [LIMIT] using h
    simp only [ge_iff_le, this, if_false, h]
    rw [next_ballot_eq _ _ (by omega)]
    rfl

theorem tick_eq (n : Node) : Node.tick n = ok (tickS n) := by
  unfold Node.tick tickS
  split
  · cases n.value <;> simp [start_eq]
  · split
    · exact start_eq n
    · cases n.proposal <;> rfl

theorem on_prepare_eq (n : Node) (src : U8) (b : U64) :
    Node.on_prepare n src b = ok (onPrepareS n src b) := by
  unfold Node.on_prepare onPrepareS; split <;> rfl

theorem on_accept_eq (n : Node) (src : U8) (v : Vote) :
    Node.on_accept n src v = ok (onAcceptS n src v) := by
  unfold Node.on_accept onAcceptS; split <;> rfl

theorem on_promise_eq (n : Node) (src : U8) (b : U64) (acc : Opt Vote) :
    Node.on_promise n src b acc = ok (onPromiseS n src b acc) := by
  unfold Node.on_promise onPromiseS recordS
  by_cases h1 : b = n.ballot
  · subst h1
    by_cases h2 : n.ballot = 0#u64
    · simp [h2]
    · cases hp : n.proposal
      · cases hv : n.value <;> by_cases s0 : src = 0#u8 <;> by_cases s1 : src = 1#u8 <;>
          cases h0 : n.promise0 <;> cases h1 : n.promise1 <;> cases h2' : n.promise2 <;>
          simp [h2, hp, hv, s0, s1, h0, h1, h2', quorum_eq, select_eq, quorumS]
      · simp [h2, hp]
  · have : (b != n.ballot) = true := by simpa using h1
    simp [this, h1]

theorem on_accepted_eq (n : Node) (src : U8) (v : Vote) :
    Node.on_accepted n src v = ok (onAcceptedS n src v) := by
  unfold Node.on_accepted onAcceptedS voteAt setVote newer
  by_cases s0 : src = 0#u8 <;> by_cases s1 : src = 1#u8 <;>
    cases h0 : n.vote0 <;> cases h1 : n.vote1 <;> cases h2 : n.vote2 <;> cases hd : n.decided <;>
    simp [s0, s1, h0, h1, h2, hd, agreed_eq] <;> (repeat' split) <;>
    first | rfl | (simp_all; done) | (cases n; simp_all; done)

theorem deliver_eq (n : Node) (src : U8) (msg : Msg) :
    Node.deliver n src msg = ok (deliverS n src msg) := by
  unfold Node.deliver deliverS
  by_cases h : 3 ≤ src.val
  · have : src ≥ NODES := by simp [NODES, UScalar.le_equiv]; exact h
    simp [this, h]
  · have : ¬ src ≥ NODES := by simp [NODES, UScalar.le_equiv]; omega
    simp only [this, h, if_false]
    cases msg with
    | Request v => cases n.value <;> rfl
    | Prepare b => exact on_prepare_eq n src b
    | Promise b acc => exact on_promise_eq n src b acc
    | Accept v => exact on_accept_eq n src v
    | Accepted v => exact on_accepted_eq n src v
    | Nack _ p => simp only []; split <;> rfl

/-- The extracted transition function is total: it returns `ok` for every
    replica state and every input, including malformed sender identifiers. -/
theorem handle_eq (n : Node) (input : Input) :
    Node.handle n input = ok (handleS n input) := by
  cases input with
  | Submit v => rfl
  | Deliver src msg => exact deliver_eq n src msg
  | Tick => exact tick_eq n

theorem no_panic : ∀ (n : Node) (input : Input), ∃ r, Node.handle n input = ok r :=
  fun n input => ⟨_, handle_eq n input⟩

#print axioms handle_eq
end PaxosNode
