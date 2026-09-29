import Temporal
import Mathlib.Data.Finset.Card
import Mathlib.Data.Fintype.Card

/- Single-decree Paxos over `N` acceptors with majority quorums. Generalizes
   `RMVerify.Paxos` (three acceptors) to arbitrary `N`. Ballots and values are
   mathematical naturals. The network may delay, duplicate, or permanently
   withhold messages; promises, proposals and votes are retained histories. -/
namespace PaxosN

abbrev Ballot := Nat
abbrev Value := Nat
abbrev Vote := Nat × Nat

/-- A majority quorum: strictly more than half of the `N` acceptors. -/
def IsQuorum (N : Nat) (q : Finset (Fin N)) : Prop := N < 2 * q.card

variable {N : Nat}

theorem quorum_intersection {q r : Finset (Fin N)}
    (hq : IsQuorum N q) (hr : IsQuorum N r) : ∃ a, a ∈ q ∧ a ∈ r := by
  have hsum := Finset.card_union_add_card_inter q r
  have hle : (q ∪ r).card ≤ N := by
    simpa using Finset.card_le_univ (q ∪ r)
  have hpos : 0 < (q ∩ r).card := by
    unfold IsQuorum at hq hr; omega
  obtain ⟨a, ha⟩ := Finset.card_pos.mp hpos
  exact ⟨a, (Finset.mem_inter.mp ha).1, (Finset.mem_inter.mp ha).2⟩

theorem quorum_nonempty {q : Finset (Fin N)} (hq : IsQuorum N q) : ∃ a, a ∈ q := by
  obtain ⟨a, ha, _⟩ := quorum_intersection hq hq
  exact ⟨a, ha⟩

structure State (N : Nat) where
  promised : Fin N → Ballot
  accepted : Fin N → Option Vote
  promises : Fin N → Ballot → Option Vote → Prop
  proposals : Ballot → Value → Prop
  votes : Fin N → Ballot → Value → Prop

def initial (N : Nat) : State N where
  promised := fun _ => 0
  accepted := fun _ => none
  promises := fun _ _ _ => False
  proposals := fun _ _ => False
  votes := fun _ _ _ => False

def put (f : Fin N → α) (a : Fin N) (v : α) : Fin N → α :=
  fun i => if i = a then v else f i

def prepare (s : State N) (a : Fin N) (b : Ballot) : State N :=
  { s with promised := put s.promised a b
           promises := fun i c snap => s.promises i c snap ∨
             (i = a ∧ c = b ∧ snap = s.accepted a) }

def propose (s : State N) (b : Ballot) (v : Value) : State N :=
  { s with proposals := fun c w => s.proposals c w ∨ (c = b ∧ w = v) }

def cast (s : State N) (a : Fin N) (b : Ballot) (v : Value) : State N :=
  { s with promised := put s.promised a b
           accepted := put s.accepted a (some (b,v))
           votes := fun i c w => s.votes i c w ∨ (i = a ∧ c = b ∧ w = v) }

/-- Relational phase-2 value choice: if no quorum member reported a vote the
    proposer is free; otherwise it must adopt the value of a highest-ballot
    reported vote. -/
def SelectOK (q : Finset (Fin N)) (snap : Fin N → Option Vote) (v : Nat) : Prop :=
  (∀ a ∈ q, snap a = none) ∨
  ∃ a ∈ q, ∃ m, snap a = some m ∧ m.2 = v ∧ ∀ c ∈ q, ∀ m', snap c = some m' → m'.1 ≤ m.1

inductive Step (N : Nat) : State N → State N → Prop where
  | idle : Step N s s
  | prepare (a b) (higher : s.promised a < b) : Step N s (prepare s a b)
  | propose (b v) (q : Finset (Fin N)) (hq : IsQuorum N q) (snap : Fin N → Option Vote)
      (fresh : ∀ w, ¬ s.proposals b w)
      (promised : ∀ a ∈ q, s.promises a b (snap a))
      (choice : SelectOK q snap v) :
      Step N s (propose s b v)
  | cast (a b v) (sent : s.proposals b v) (allowed : s.promised a ≤ b) :
      Step N s (cast s a b v)

def Chosen (N : Nat) (s : State N) (b : Ballot) (v : Value) : Prop :=
  ∃ q, IsQuorum N q ∧ ∀ a ∈ q, s.votes a b v

def CannotVote (s : State N) (a : Fin N) (b : Ballot) : Prop :=
  b < s.promised a ∧ ∀ v, ¬ s.votes a b v

/-- Each lower ballot is blocked by a quorum unless it votes for this value. -/
def SafeAt (s : State N) (b : Ballot) (v : Value) : Prop :=
  ∀ c, c < b → ∃ q, IsQuorum N q ∧ ∀ a ∈ q, s.votes a c v ∨ CannotVote s a c

/-- A promise snapshot describes the last accepted vote below its ballot and
    remains accurate about earlier votes even after the acceptor advances. -/
def Snapshot (s : State N) (a : Fin N) (b : Ballot) (snap : Option Vote) : Prop :=
  b ≤ s.promised a ∧
  (∀ c v, s.votes a c v → c < b → ∃ m, snap = some m ∧ c ≤ m.1) ∧
  (∀ m, snap = some m → m.1 < b ∧ s.votes a m.1 m.2)

structure Invariant (s : State N) : Prop where
  origin : ∀ a, s.promised a = 0 ∨ (∃ snap, s.promises a (s.promised a) snap) ∨ ∃ v, s.proposals (s.promised a) v
  unique : ∀ b v w, s.proposals b v → s.proposals b w → v = w
  voted : ∀ a b v, s.votes a b v → s.proposals b v
  bounded : ∀ a b v, s.votes a b v → b ≤ s.promised a
  latest : ∀ a b v, s.votes a b v → ∃ m, s.accepted a = some m ∧ b ≤ m.1
  accepted_vote : ∀ a m, s.accepted a = some m → s.votes a m.1 m.2
  snapshots : ∀ a b snap, s.promises a b snap → Snapshot s a b snap
  safe : ∀ b v, s.proposals b v → SafeAt s b v

theorem initial_invariant : Invariant (initial N) := by
  constructor <;> simp [initial]

theorem safe_mono (s t : State N)
    (hv : ∀ a b v, s.votes a b v → t.votes a b v)
    (hc : ∀ a b, CannotVote s a b → CannotVote t a b)
    (h : SafeAt s b v) : SafeAt t b v := by
  intro c hcb
  obtain ⟨q, hq, hm⟩ := h c hcb
  exact ⟨q, hq, fun a ha => (hm a ha).elim (fun h => .inl (hv a c v h)) (fun h => .inr (hc a c h))⟩

theorem prepare_invariant (s : State N) (inv : Invariant s) (a : Fin N) (b : Ballot)
    (higher : s.promised a < b) : Invariant (prepare s a b) := by
  have mono : ∀ i, s.promised i ≤ (prepare s a b).promised i := by
    intro i; simp [prepare, put]; split <;> grind
  have cannot : ∀ i c, CannotVote s i c → CannotVote (prepare s a b) i c := by
    intro i c ⟨h, hn⟩
    exact ⟨Nat.lt_of_lt_of_le h (mono i), hn⟩
  refine ⟨?_, inv.unique, inv.voted, ?_, inv.latest, inv.accepted_vote, ?_, ?_⟩
  · intro i
    by_cases hi : i = a
    · subst i
      right; left
      exact ⟨s.accepted a, .inr ⟨rfl, by simp [prepare, put], rfl⟩⟩
    · have ho := inv.origin i
      simp only [prepare, put, if_neg hi]
      rcases ho with h | ⟨snap, h⟩ | h
      · exact .inl h
      · exact .inr (.inl ⟨snap, .inl h⟩)
      · exact .inr (.inr h)
  · intro i c v hv; exact Nat.le_trans (inv.bounded i c v hv) (mono i)
  · intro i c snap hp
    rcases hp with hp | ⟨rfl, rfl, rfl⟩
    · obtain ⟨hb, hmax, hsnap⟩ := inv.snapshots i c snap hp
      exact ⟨Nat.le_trans hb (mono i), hmax, hsnap⟩
    · refine ⟨?_, ?_, ?_⟩
      · simp [prepare, put]
      · intro c v hv _; exact inv.latest i c v hv
      · intro m hm
        have hv := inv.accepted_vote i m hm
        exact ⟨Nat.lt_of_le_of_lt (inv.bounded i m.1 m.2 hv) higher, hv⟩
  · intro c v hp; exact safe_mono s _ (fun _ _ _ h => h) cannot (inv.safe c v hp)

theorem cast_invariant (s : State N) (inv : Invariant s) (a : Fin N) (b : Ballot)
    (v : Value) (sent : s.proposals b v) (allowed : s.promised a ≤ b) :
    Invariant (cast s a b v) := by
  have mono : ∀ i, s.promised i ≤ (cast s a b v).promised i := by
    intro i; simp [cast, put]; split <;> grind
  have vm : ∀ i c w, s.votes i c w → (cast s a b v).votes i c w :=
    fun _ _ _ h => .inl h
  have cannot : ∀ i c, CannotVote s i c → CannotVote (cast s a b v) i c := by
    intro i c ⟨hc, hn⟩
    refine ⟨Nat.lt_of_lt_of_le hc (mono i), ?_⟩
    intro w hw
    rcases hw with hw | ⟨rfl, rfl, rfl⟩
    · exact hn w hw
    · exact Nat.not_lt_of_ge allowed hc
  refine ⟨?_, inv.unique, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · intro i
    by_cases hi : i = a
    · subst i; exact .inr (.inr ⟨v, by simpa [cast, put] using sent⟩)
    · simpa [cast, put, hi] using inv.origin i
  · intro i c w hv
    rcases hv with hv | ⟨rfl, rfl, rfl⟩
    · exact inv.voted i c w hv
    · exact sent
  · intro i c w hv
    rcases hv with hv | ⟨rfl, rfl, rfl⟩
    · exact Nat.le_trans (inv.bounded i c w hv) (mono i)
    · simp [cast, put]
  · intro i c w hv
    by_cases hi : i = a
    · subst i
      refine ⟨(b,v), by simp [cast, put], ?_⟩
      rcases hv with hv | ⟨_, rfl, _⟩
      · exact Nat.le_trans (inv.bounded a c w hv) allowed
      · exact Nat.le_refl _
    · have old : s.votes i c w := by rcases hv with h | h; exact h; exact False.elim (hi h.1)
      obtain ⟨m, hm, hb⟩ := inv.latest i c w old
      exact ⟨m, by simpa [cast, put, hi] using hm, hb⟩
  · intro i m hm
    by_cases hi : i = a
    · subst i
      have eq : (b,v) = m := by simpa [cast, put] using hm
      subst m; exact .inr ⟨rfl, rfl, rfl⟩
    · exact .inl (inv.accepted_vote i m (by simpa [cast, put, hi] using hm))
  · intro i c snap hp
    obtain ⟨hb, hmax, hsnap⟩ := inv.snapshots i c snap hp
    refine ⟨Nat.le_trans hb (mono i), ?_, ?_⟩
    · intro d w hv hd
      rcases hv with hv | ⟨rfl, rfl, rfl⟩
      · exact hmax d w hv hd
      · exact False.elim (Nat.not_lt_of_ge (Nat.le_trans hb allowed) hd)
    · intro m hm
      obtain ⟨hlt, hv⟩ := hsnap m hm
      exact ⟨hlt, .inl hv⟩
  · intro c w hp; exact safe_mono s _ vm cannot (inv.safe c w hp)

/-- A phase-1 quorum establishes safety for any value allowed by `SelectOK`. -/
theorem selection_safe (s : State N) (inv : Invariant s) (b : Ballot) (v : Value)
    (q : Finset (Fin N)) (hq : IsQuorum N q) (snap : Fin N → Option Vote)
    (promised : ∀ a ∈ q, s.promises a b (snap a))
    (choice : SelectOK q snap v) : SafeAt s b v := by
  have sn : ∀ a ∈ q, Snapshot s a b (snap a) :=
    fun a ha => inv.snapshots a b (snap a) (promised a ha)
  rcases choice with none_voted | ⟨a, ha, m, hm, hmv, hmax⟩
  · -- (a) no member reported a vote: `q` blocks every lower ballot.
    intro c hcb
    refine ⟨q, hq, fun i hi => .inr ⟨Nat.lt_of_lt_of_le hcb (sn i hi).1, ?_⟩⟩
    intro w hw
    obtain ⟨m, hm, _⟩ := (sn i hi).2.1 c w hw hcb
    rw [none_voted i hi] at hm
    cases hm
  · -- (b) the highest reported vote `m` at acceptor `a`.
    subst hmv
    obtain ⟨hmb, hvote⟩ := (sn a ha).2.2 m hm
    have hp : s.proposals m.1 m.2 := inv.voted a m.1 m.2 hvote
    intro c hcb
    by_cases hcm : c < m.1
    · exact inv.safe m.1 m.2 hp c hcm
    · refine ⟨q, hq, ?_⟩
      intro i hi
      by_cases existsVote : ∃ w, s.votes i c w
      · obtain ⟨w, hw⟩ := existsVote
        obtain ⟨m', hm', hle⟩ := (sn i hi).2.1 c w hw hcb
        have hle' := hmax i hi m' hm'
        have eq : c = m.1 := Nat.le_antisymm (Nat.le_trans hle hle') (Nat.le_of_not_gt hcm)
        subst c
        have eqv := inv.unique m.1 w m.2 (inv.voted i m.1 w hw) hp
        exact .inl (eqv ▸ hw)
      · exact .inr ⟨Nat.lt_of_lt_of_le hcb (sn i hi).1, fun w hw => existsVote ⟨w, hw⟩⟩

theorem propose_invariant (s : State N) (inv : Invariant s) (b : Ballot)
    (v : Value) (fresh : ∀ w, ¬ s.proposals b w) (safe : SafeAt s b v) :
    Invariant (propose s b v) := by
  refine ⟨?_, ?_, ?_, inv.bounded, inv.latest, inv.accepted_vote, inv.snapshots, ?_⟩
  · intro a
    rcases inv.origin a with h | h | ⟨w,h⟩
    · exact .inl h
    · exact .inr (.inl h)
    · exact .inr (.inr ⟨w,.inl h⟩)
  · intro c x y hx hy
    rcases hx with hx | ⟨rfl, rfl⟩
    · rcases hy with hy | ⟨rfl, rfl⟩
      · exact inv.unique c x y hx hy
      · exact False.elim (fresh x hx)
    · rcases hy with hy | ⟨_, rfl⟩
      · exact False.elim (fresh y hy)
      · rfl
  · intro a c w hv; exact .inl (inv.voted a c w hv)
  · intro c w hp
    rcases hp with hp | ⟨rfl, rfl⟩
    · exact inv.safe c w hp
    · exact safe

theorem step_invariant (s t : State N) (inv : Invariant s) (step : Step N s t) :
    Invariant t := by
  cases step with
  | idle => exact inv
  | prepare a b h => exact prepare_invariant s inv a b h
  | propose b v q hq snap fresh promised choice =>
    exact propose_invariant s inv b v fresh
      (selection_safe s inv b v q hq snap promised choice)
  | cast a b v hp ha => exact cast_invariant s inv a b v hp ha

def module (N : Nat) : RMVerify.Reactive.Module (State N) :=
  ⟨[⟨[], [], [], fun s => s = initial N, Step N⟩]⟩

theorem reachable_invariant (s : State N) (h : RMVerify.Reactive.Reachable (module N) s) :
    Invariant s := by
  induction h with
  | @initial s h =>
    have he : s = initial N := by simpa [module, RMVerify.Reactive.Module.initial] using h
    subst s; exact initial_invariant
  | @step s t _ h ih =>
    exact step_invariant s t ih (by simpa [module, RMVerify.Reactive.Module.step] using h)

/-- Safety is a consequence of the invariant and quorum intersection. -/
theorem agreement_of_invariant (s : State N) (inv : Invariant s)
    (b c : Ballot) (v w : Value) (hb : Chosen N s b v) (hc : Chosen N s c w) : v = w := by
  obtain ⟨q, hqq, hq⟩ := hb
  obtain ⟨r, hrq, hr⟩ := hc
  obtain ⟨x, hx⟩ := quorum_nonempty hqq
  obtain ⟨y, hy⟩ := quorum_nonempty hrq
  have pv := inv.voted x b v (hq x hx)
  have pw := inv.voted y c w (hr y hy)
  have lower : ∀ (b c : Ballot) (v w : Value), s.proposals b v → c < b →
      Chosen N s c w → v = w := by
    intro b c v w hp hlt ⟨r, hrq, hr⟩
    obtain ⟨q, hqq, hq⟩ := inv.safe b v hp c hlt
    obtain ⟨a, haq, har⟩ := quorum_intersection hqq hrq
    cases hq a haq with
    | inl hv => exact inv.unique c v w (inv.voted a c v hv) (inv.voted a c w (hr a har))
    | inr hn => exact False.elim (hn.2 w (hr a har))
  by_cases h : c < b
  · exact lower b c v w pv h ⟨r, hrq, hr⟩
  by_cases h' : b < c
  · exact (lower c b w v pw h' ⟨q, hqq, hq⟩).symm
  have he : b = c := Nat.le_antisymm (Nat.le_of_not_gt h) (Nat.le_of_not_gt h')
  subst c
  exact inv.unique b v w pv pw

/-- Agreement for every reachable execution, with no delivery/fairness premise. -/
theorem safety (s : State N) (h : RMVerify.Reactive.Reachable (module N) s)
    (b c : Ballot) (v w : Value) (hb : Chosen N s b v) (hc : Chosen N s c w) : v = w :=
  agreement_of_invariant s (reachable_invariant s h) b c v w hb hc

#print axioms safety

end PaxosN
