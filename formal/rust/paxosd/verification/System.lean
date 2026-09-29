import UserVerification.Node
import UserVerification.Model

/- Closed-world semantics of an `N`-replica deployment. The state is the `N`
   real replica states and the set of every packet ever sent. A step runs the
   extracted `Node.handle` on one replica for a client submission, a timer tick,
   or the delivery of a previously sent packet addressed to it. Packets are
   never removed, so delivery may be delayed, duplicated, reordered or omitted.
   A crash followed by restart from durable storage leaves the state unchanged
   (the runtime stores the new state before sending), so it is a stutter step. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

/-- Admissible cluster sizes: at least one replica, and every replica id as
    well as the size itself fit in a `u8` (the Rust code supports `1 ≤ n ≤ 255`). -/
class Cluster (N : Nat) : Prop where
  pos : 0 < N
  small : N < 256

/-- The `u8` encoding of a natural number (used for the cluster size `N`). -/
def u8 (x : Nat) : U8 := ⟨BitVec.ofNat 8 x⟩

@[simp] theorem u8_val (N : Nat) [c : Cluster N] : (u8 N).val = N := by
  show (BitVec.ofNat 8 N).toNat = N
  have := c.small; simp [BitVec.toNat_ofNat]; omega

/-- The wire identifier of replica `i`. -/
def rid {N : Nat} (i : Fin N) : U8 := ⟨BitVec.ofNat 8 i.val⟩

variable {N : Nat}

@[simp] theorem rid_val [c : Cluster N] (i : Fin N) : (rid i).val = i.val := by
  show (BitVec.ofNat 8 i.val).toNat = i.val
  have := i.isLt; have := c.small; simp [BitVec.toNat_ofNat]; omega

theorem rid_inj [Cluster N] {i j : Fin N} (h : rid i = rid j) : i = j := by
  apply Fin.ext; have := congrArg UScalar.val h; simpa using this

theorem rid_eq_iff [Cluster N] (i : Fin N) (x : U8) : rid i = x ↔ i.val = x.val := by
  constructor
  · intro h; subst h; simp
  · intro h; apply UScalar.eq_of_val_eq; simp [h]

/-- A packet: the sending replica and what it sent. -/
structure Packet (N : Nat) where
  src : Fin N
  send : Send

/-- Packet `p` is offered to replica `i`. -/
def Addressed (p : Packet N) (i : Fin N) : Prop :=
  p.send.to = .All ∨ p.send.to = .To (rid i)

/-- A deployment: the state of each replica and the set of every packet ever sent. -/
structure World (N : Nat) where
  node : Fin N → Node
  net : Packet N → Prop

def emit (net : Packet N → Prop) (i : Fin N) (o : Opt Send) : Packet N → Prop :=
  fun p => net p ∨ (o = .Some p.send ∧ p.src = i)

/-- Replica `i` takes the result `r` of one call to `handle`: its state becomes
    `r.2` and the emitted message (if any) is added to the network. -/
def World.after (w : World N) (i : Fin N) (r : Opt Send × Node) : World N :=
  ⟨PaxosN.put w.node i r.2, emit w.net i r.1⟩

/-- Inputs the environment may present to replica `i`. -/
def Allowed (w : World N) (i : Fin N) : Input → Prop
  | .Submit _ => True
  | .Tick => True
  | .Deliver src msg => ∃ p, w.net p ∧ Addressed p i ∧ src = rid p.src ∧ msg = p.send.msg

/-- One step of the deployment: a stutter (e.g. crash and restart), or one
    replica running the extracted `Node.handle` on a permitted input. -/
inductive Step : World N → World N → Prop where
  | idle : Step w w
  | submit (i : Fin N) (v : U64) (r) (exec : Node.handle (w.node i) (.Submit v) = ok r) :
      Step w (w.after i r)
  | tick (i : Fin N) (r) (exec : Node.handle (w.node i) .Tick = ok r) : Step w (w.after i r)
  | deliver (i : Fin N) (p : Packet N) (r) (sent : w.net p) (dest : Addressed p i)
      (exec : Node.handle (w.node i) (.Deliver (rid p.src) p.send.msg) = ok r) :
      Step w (w.after i r)

/-- Every replica `i` was created by `Node::new(i, N)`, and nothing was sent. -/
def Initial (w : World N) : Prop :=
  (∀ i, Node.new (rid i) (u8 N) = ok (w.node i)) ∧ ∀ p, ¬ w.net p

def module (N : Nat) : Reactive.Module (World N) := ⟨[⟨[], [], [], Initial, Step⟩]⟩

theorem step_iff (w w' : World N) :
    Step w w' ↔ w' = w ∨ ∃ i inp, Allowed w i inp ∧ w' = w.after i (handleS (w.node i) inp) := by
  constructor
  · intro h
    cases h with
    | idle => exact .inl rfl
    | submit i v r exec =>
      rw [handle_eq] at exec; cases exec; exact .inr ⟨i, .Submit v, trivial, rfl⟩
    | tick i r exec =>
      rw [handle_eq] at exec; cases exec; exact .inr ⟨i, .Tick, trivial, rfl⟩
    | deliver i p r sent dest exec =>
      rw [handle_eq] at exec; cases exec
      exact .inr ⟨i, .Deliver (rid p.src) p.send.msg, ⟨p, sent, dest, rfl, rfl⟩, rfl⟩
  · rintro (rfl | ⟨i, inp, al, rfl⟩)
    · exact .idle
    · cases inp with
      | Submit v => exact .submit i v _ (handle_eq _ _)
      | Tick => exact .tick i _ (handle_eq _ _)
      | Deliver src msg =>
        obtain ⟨p, sent, dest, rfl, rfl⟩ := al
        exact .deliver i p _ sent dest (handle_eq _ _)

/-! ## Views of replica state -/

/-- The promise recorded by a replica for acceptor `j`. -/
def pslot (n : Node) (j : Fin N) : Opt Promise := slot n.promises j.val

/-- The vote recorded by a replica's learner for acceptor `j`. -/
def vslot (n : Node) (j : Fin N) : Opt Vote := slot n.votes j.val

/-- The highest ballot of any replica. -/
def top (w : World N) : Nat := Finset.univ.sup (fun k => (w.node k).ballot.val)

theorem le_top (w : World N) (k : Fin N) : (w.node k).ballot.val ≤ top w :=
  Finset.le_sup (f := fun k => (w.node k).ballot.val) (Finset.mem_univ k)

/-- The replica owning ballot `b`. -/
def owner [c : Cluster N] (b : U64) : Fin N := ⟨b.val % N, Nat.mod_lt _ c.pos⟩

/-- The acceptors whose recorded promise is for ballot `b`. -/
def promisers (n : Node) (b : U64) : Finset (Fin N) :=
  Finset.univ.filter (fun j => promiseHit b (pslot n j) = true)

/-- The acceptors whose announced vote is exactly `v`. -/
def voters (n : Node) (v : Vote) : Finset (Fin N) :=
  Finset.univ.filter (fun j => voteHit v (vslot n j) = true)

/-! ## Interpretation as the abstract Paxos model -/

def snap : Opt Vote → Option PaxosN.Vote
  | .None => none
  | .Some v => some (v.ballot.val, v.value.val)

/-- Promises, proposals and votes of the abstract model are the `Promise`,
    `Accept` and `Accepted` packets ever sent; acceptor state is read off the
    replicas. -/
def abs (w : World N) : PaxosN.State N where
  promised a := (w.node a).promised.val
  accepted a := snap (w.node a).accepted
  promises a b s := ∃ p, w.net p ∧ p.src = a ∧
    ∃ x y, p.send.msg = .Promise x y ∧ x.val = b ∧ snap y = s
  proposals b v := ∃ p, w.net p ∧ ∃ vt : Vote, p.send.msg = .Accept vt ∧
    vt.ballot.val = b ∧ vt.value.val = v
  votes a b v := ∃ p, w.net p ∧ p.src = a ∧ ∃ vt : Vote, p.send.msg = .Accepted vt ∧
    vt.ballot.val = b ∧ vt.value.val = v

/-! ## Concrete invariant -/

/-- Facts about each packet ever sent, relative to the current replica states. -/
def PacketInv [Cluster N] (w : World N) (p : Packet N) : Prop :=
  match p.send.msg with
  | .Request _ => p.send.to = .All
  | .Prepare b => b.val ≠ 0 ∧ b.val % N = p.src.val ∧ b.val ≤ (w.node p.src).ballot.val
  | .Promise b _ => p.send.to = .To (rid (owner (N := N) b))
  | .Accept vt => vt.ballot.val ≠ 0 ∧ vt.ballot.val % N = p.src.val ∧
      vt.ballot.val ≤ (w.node p.src).ballot.val ∧
      (vt.ballot = (w.node p.src).ballot → (w.node p.src).proposal = .Some vt.value) ∧
      ∃ q, w.net q ∧ q.send.msg = .Request vt.value
  | .Accepted vt => vt.ballot.val ≤ (w.node p.src).promised.val
  | .Nack _ q => q.val ≤ top w

/-- Facts about each replica. -/
structure NodeInv (w : World N) (k : Fin N) : Prop where
  id : (w.node k).id = rid k
  /-- The cluster-size field is `N`. -/
  size : (w.node k).n = u8 N
  /-- Both vectors have one entry per replica. -/
  plen : (items (w.node k).promises).length = N
  vlen : (items (w.node k).votes).length = N
  own : (w.node k).ballot.val = 0 ∨ (w.node k).ballot.val % N = k.val
  started : (w.node k).ballot.val ≠ 0 →
    (w.node k).value ≠ .None ∧ w.net ⟨k, ⟨.All, .Prepare (w.node k).ballot⟩⟩
  proposed : ∀ v, (w.node k).proposal = .Some v →
    (w.node k).ballot.val ≠ 0 ∧ w.net ⟨k, ⟨.All, .Accept ⟨(w.node k).ballot, v⟩⟩⟩
  /-- Recorded promises are for nonzero ballots not above the current one. -/
  slot_le : ∀ (j : Fin N) p, pslot (w.node k) j = .Some p →
    0 < p.ballot.val ∧ p.ballot.val ≤ (w.node k).ballot.val
  /-- A recorded promise for the current ballot was sent by that acceptor. -/
  slots : ∀ (j : Fin N) p, pslot (w.node k) j = .Some p → p.ballot = (w.node k).ballot →
    ∃ q, w.net q ∧ q.src = j ∧ q.send.msg = .Promise p.ballot p.accepted
  /-- Without a proposal, no majority has promised the current ballot. -/
  pending : (w.node k).proposal = .None →
    ¬ Majority (countPromisesS (items (w.node k).promises) (w.node k).ballot) (w.node k).n
  promised_top : (w.node k).promised.val ≤ top w
  seen_top : (w.node k).max_seen.val ≤ top w
  request : ∀ v, (w.node k).value = .Some v → ∃ p, w.net p ∧ p.send.msg = .Request v
  votes : ∀ (j : Fin N) vt, vslot (w.node k) j = .Some vt →
    ∃ p, w.net p ∧ p.src = j ∧ p.send.msg = .Accepted vt
  /-- Without a decision, no vote is announced by a majority. -/
  undecided : (w.node k).decided = .None →
    ∀ v, ¬ Majority (countVotesS (items (w.node k).votes) v) (w.node k).n
  /-- A decision is backed by a quorum of abstract votes. -/
  decided : ∀ v, (w.node k).decided = .Some v →
    ∃ (q : Finset (Fin N)) (b : Nat), PaxosN.IsQuorum N q ∧ ∀ a ∈ q, (abs w).votes a b v.val

/-- The concrete invariant of the deployment. -/
def Inv [Cluster N] (w : World N) : Prop := (∀ k, NodeInv w k) ∧ ∀ p, w.net p → PacketInv w p

end PaxosSystem
