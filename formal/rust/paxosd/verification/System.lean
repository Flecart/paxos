import UserVerification.Node
import Paxos

/- Closed-world semantics of a three-replica deployment. The state is the three
   real replica states and the set of every packet ever sent. A step runs the
   extracted `Node.handle` on one replica for a client submission, a timer tick,
   or the delivery of a previously sent packet addressed to it. Packets are
   never removed, so delivery may be delayed, duplicated, reordered or omitted.
   A crash followed by restart from durable storage leaves the state unchanged
   (the runtime stores the new state before sending), so it is a stutter step. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

abbrev Rid := Fin 3

def rid (i : Rid) : U8 := ⟨BitVec.ofNat 8 i.val⟩

@[simp] theorem rid_val (i : Rid) : (rid i).val = i.val := by
  show (BitVec.ofNat 8 i.val).toNat = i.val
  have := i.isLt; simp [BitVec.toNat_ofNat]; omega

theorem rid_inj {i j : Rid} (h : rid i = rid j) : i = j := by
  apply Fin.ext; have := congrArg UScalar.val h; simpa using this

theorem rid_eq_iff (i : Rid) (x : U8) : rid i = x ↔ i.val = x.val := by
  constructor
  · intro h; subst h; simp
  · intro h; apply UScalar.eq_of_val_eq; simp [h]

structure Packet where
  src : Rid
  send : Send

def Addressed (p : Packet) (i : Rid) : Prop :=
  p.send.to = .All ∨ p.send.to = .To (rid i)

structure World where
  node : Rid → Node
  net : Packet → Prop

def emit (net : Packet → Prop) (i : Rid) (o : Opt Send) : Packet → Prop :=
  fun p => net p ∨ (o = .Some p.send ∧ p.src = i)

def World.after (w : World) (i : Rid) (r : Opt Send × Node) : World :=
  ⟨Paxos.put w.node i r.2, emit w.net i r.1⟩

/-- Inputs the environment may present to replica `i`. -/
def Allowed (w : World) (i : Rid) : Input → Prop
  | .Submit _ => True
  | .Tick => True
  | .Deliver src msg => ∃ p, w.net p ∧ Addressed p i ∧ src = rid p.src ∧ msg = p.send.msg

inductive Step : World → World → Prop where
  | idle : Step w w
  | submit (i : Rid) (v : U64) (r) (exec : Node.handle (w.node i) (.Submit v) = ok r) :
      Step w (w.after i r)
  | tick (i : Rid) (r) (exec : Node.handle (w.node i) .Tick = ok r) : Step w (w.after i r)
  | deliver (i : Rid) (p : Packet) (r) (sent : w.net p) (dest : Addressed p i)
      (exec : Node.handle (w.node i) (.Deliver (rid p.src) p.send.msg) = ok r) :
      Step w (w.after i r)

def Initial (w : World) : Prop :=
  (∀ i, Node.new (rid i) = ok (w.node i)) ∧ ∀ p, ¬ w.net p

def module : Reactive.Module World := ⟨[⟨[], [], [], Initial, Step⟩]⟩

theorem step_iff (w w' : World) :
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

def pslot (n : Node) (j : Rid) : Opt (Opt Vote) :=
  if j.val = 0 then n.promise0 else if j.val = 1 then n.promise1 else n.promise2

def vslot (n : Node) (j : Rid) : Opt Vote :=
  if j.val = 0 then n.vote0 else if j.val = 1 then n.vote1 else n.vote2

def top (w : World) : Nat :=
  max (max (w.node 0).ballot.val (w.node 1).ballot.val) (w.node 2).ballot.val

theorem le_top (w : World) (k : Rid) : (w.node k).ballot.val ≤ top w := by
  unfold top
  fin_cases k <;> simp <;> omega

def owner (b : U64) : Rid := ⟨b.val % 3, Nat.mod_lt _ (by decide)⟩

/-! ## Interpretation as the abstract Paxos model -/

def snap : Opt Vote → Option Paxos.Vote
  | .None => none
  | .Some v => some (v.ballot.val, v.value.val)

def abs (w : World) : Paxos.State where
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
def PacketInv (w : World) (p : Packet) : Prop :=
  match p.send.msg with
  | .Request _ => p.send.to = .All
  | .Prepare b => b.val ≠ 0 ∧ b.val % 3 = p.src.val ∧ b.val ≤ (w.node p.src).ballot.val
  | .Promise b _ => p.send.to = .To (rid (owner b))
  | .Accept vt => vt.ballot.val ≠ 0 ∧ vt.ballot.val % 3 = p.src.val ∧
      vt.ballot.val ≤ (w.node p.src).ballot.val ∧
      (vt.ballot = (w.node p.src).ballot → (w.node p.src).proposal = .Some vt.value) ∧
      ∃ q, w.net q ∧ q.send.msg = .Request vt.value
  | .Accepted vt => vt.ballot.val ≤ (w.node p.src).promised.val
  | .Nack _ q => q.val ≤ top w

/-- Facts about each replica. -/
structure NodeInv (w : World) (k : Rid) : Prop where
  id : (w.node k).id = rid k
  own : (w.node k).ballot.val = 0 ∨ (w.node k).ballot.val % 3 = k.val
  started : (w.node k).ballot.val ≠ 0 →
    (w.node k).value ≠ .None ∧ w.net ⟨k, ⟨.All, .Prepare (w.node k).ballot⟩⟩
  proposed : ∀ v, (w.node k).proposal = .Some v →
    (w.node k).ballot.val ≠ 0 ∧ w.net ⟨k, ⟨.All, .Accept ⟨(w.node k).ballot, v⟩⟩⟩
  slots : ∀ j y, pslot (w.node k) j = .Some y →
    ∃ p, w.net p ∧ p.src = j ∧ p.send.msg = .Promise (w.node k).ballot y
  pending : (w.node k).proposal = .None →
    quorumS (w.node k).promise0 (w.node k).promise1 (w.node k).promise2 = .None
  promised_top : (w.node k).promised.val ≤ top w
  seen_top : (w.node k).max_seen.val ≤ top w
  request : ∀ v, (w.node k).value = .Some v → ∃ p, w.net p ∧ p.send.msg = .Request v
  votes : ∀ j vt, vslot (w.node k) j = .Some vt →
    ∃ p, w.net p ∧ p.src = j ∧ p.send.msg = .Accepted vt
  undecided : (w.node k).decided = .None →
    agreedS (w.node k).vote0 (w.node k).vote1 (w.node k).vote2 = .None
  decided : ∀ v, (w.node k).decided = .Some v →
    ∃ (q : Paxos.Quorum) (b : Nat), ∀ a, Paxos.Member a q → (abs w).votes a b v.val

def Inv (w : World) : Prop := (∀ k, NodeInv w k) ∧ ∀ p, w.net p → PacketInv w p

end PaxosSystem
