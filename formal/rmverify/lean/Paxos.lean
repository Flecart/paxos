import Temporal

/- Single-decree Paxos with retained authenticated messages. Ballots and values
   are mathematical naturals. The Rust refinement restricts them to u64.
   The network may delay, duplicate, or permanently withhold messages. -/
namespace RMVerify.Paxos

abbrev Node := Fin 3
abbrev Ballot := Nat
abbrev Value := Nat
abbrev Vote := Ballot × Value

structure Quorum where
  first : Node
  second : Node
  distinct : first ≠ second

def Member (a : Node) (q : Quorum) : Prop := a = q.first ∨ a = q.second

theorem quorum_intersection (q r : Quorum) : ∃ a, Member a q ∧ Member a r := by
  have hq := q.distinct
  have hr := r.distinct
  have q0 := q.first.isLt
  have q1 := q.second.isLt
  have r0 := r.first.isLt
  have r1 := r.second.isLt
  by_cases h : q.first = r.first
  · exact ⟨q.first, .inl rfl, .inl h⟩
  by_cases h' : q.first = r.second
  · exact ⟨q.first, .inl rfl, .inr h'⟩
  by_cases h'' : q.second = r.first
  · exact ⟨q.second, .inr rfl, .inl h''⟩
  have he : q.second = r.second := by
    apply Fin.ext
    have d0 : q.first.val ≠ q.second.val := fun e => hq (Fin.ext e)
    have d1 : r.first.val ≠ r.second.val := fun e => hr (Fin.ext e)
    have d2 : q.first.val ≠ r.first.val := fun e => h (Fin.ext e)
    have d3 : q.first.val ≠ r.second.val := fun e => h' (Fin.ext e)
    have d4 : q.second.val ≠ r.first.val := fun e => h'' (Fin.ext e)
    omega
  exact ⟨q.second, .inr rfl, .inr he⟩

structure State where
  promised : Node → Ballot
  accepted : Node → Option Vote
  promises : Node → Ballot → Option Vote → Prop
  proposals : Ballot → Value → Prop
  votes : Node → Ballot → Value → Prop

def initial : State where
  promised := fun _ => 0
  accepted := fun _ => none
  promises := fun _ _ _ => False
  proposals := fun _ _ => False
  votes := fun _ _ _ => False

def put (f : Node → α) (a : Node) (v : α) : Node → α :=
  fun i => if i = a then v else f i

def prepare (s : State) (a : Node) (b : Ballot) : State :=
  { s with promised := put s.promised a b
           promises := fun i c snap => s.promises i c snap ∨
             (i = a ∧ c = b ∧ snap = s.accepted a) }

def propose (s : State) (b : Ballot) (v : Value) : State :=
  { s with proposals := fun c w => s.proposals c w ∨ (c = b ∧ w = v) }

def cast (s : State) (a : Node) (b : Ballot) (v : Value) : State :=
  { s with promised := put s.promised a b
           accepted := put s.accepted a (some (b,v))
           votes := fun i c w => s.votes i c w ∨ (i = a ∧ c = b ∧ w = v) }

def select (left right : Option Vote) (offered : Value) : Value :=
  match left, right with
  | some a, some b => if a.1 < b.1 then b.2 else a.2
  | some a, none => a.2
  | none, some b => b.2
  | none, none => offered

inductive Step : State → State → Prop where
  | idle : Step s s
  | prepare (a b) (higher : s.promised a < b) : Step s (prepare s a b)
  | propose (b offered) (q : Quorum) (left right)
      (fresh : ∀ v, ¬ s.proposals b v)
      (hl : s.promises q.first b left) (hr : s.promises q.second b right) :
      Step s (propose s b (select left right offered))
  | cast (a b v) (sent : s.proposals b v) (allowed : s.promised a ≤ b) :
      Step s (cast s a b v)

def Chosen (s : State) (b : Ballot) (v : Value) : Prop :=
  ∃ q, ∀ a, Member a q → s.votes a b v

def CannotVote (s : State) (a : Node) (b : Ballot) : Prop :=
  b < s.promised a ∧ ∀ v, ¬ s.votes a b v

/-- Each lower ballot is blocked by a quorum unless it votes for this value. -/
def SafeAt (s : State) (b : Ballot) (v : Value) : Prop :=
  ∀ c, c < b → ∃ q, ∀ a, Member a q → s.votes a c v ∨ CannotVote s a c

/-- A promise snapshot describes the last accepted vote below its ballot and
    remains accurate about earlier votes even after the acceptor advances. -/
def Snapshot (s : State) (a : Node) (b : Ballot) (snap : Option Vote) : Prop :=
  b ≤ s.promised a ∧
  (∀ c v, s.votes a c v → c < b → ∃ m, snap = some m ∧ c ≤ m.1) ∧
  (∀ m, snap = some m → m.1 < b ∧ s.votes a m.1 m.2)

structure Invariant (s : State) : Prop where
  origin : ∀ a, s.promised a = 0 ∨ (∃ snap, s.promises a (s.promised a) snap) ∨ ∃ v, s.proposals (s.promised a) v
  unique : ∀ b v w, s.proposals b v → s.proposals b w → v = w
  voted : ∀ a b v, s.votes a b v → s.proposals b v
  bounded : ∀ a b v, s.votes a b v → b ≤ s.promised a
  latest : ∀ a b v, s.votes a b v → ∃ m, s.accepted a = some m ∧ b ≤ m.1
  accepted_vote : ∀ a m, s.accepted a = some m → s.votes a m.1 m.2
  snapshots : ∀ a b snap, s.promises a b snap → Snapshot s a b snap
  safe : ∀ b v, s.proposals b v → SafeAt s b v

theorem initial_invariant : Invariant initial := by
  constructor <;> simp [initial]


theorem safe_mono (s t : State)
    (hv : ∀ a b v, s.votes a b v → t.votes a b v)
    (hc : ∀ a b, CannotVote s a b → CannotVote t a b)
    (h : SafeAt s b v) : SafeAt t b v := by
  intro c hcb
  obtain ⟨q, hq⟩ := h c hcb
  exact ⟨q, fun a ha => (hq a ha).elim (fun h => .inl (hv a c v h)) (fun h => .inr (hc a c h))⟩

theorem prepare_invariant (s : State) (inv : Invariant s) (a : Node) (b : Ballot)
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

theorem cast_invariant (s : State) (inv : Invariant s) (a : Node) (b : Ballot)
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

/-- A phase-1 quorum establishes safety by selecting its highest accepted vote. -/
theorem selection_safe (s : State) (inv : Invariant s) (b : Ballot)
    (offered : Value) (q : Quorum) (left right : Option Vote)
    (hl : s.promises q.first b left) (hr : s.promises q.second b right) :
    SafeAt s b (select left right offered) := by
  have sl := inv.snapshots q.first b left hl
  have sr := inv.snapshots q.second b right hr
  have build (m : Vote) (hv : s.votes q.first m.1 m.2 ∨ s.votes q.second m.1 m.2)
      (bounds : ∀ a, Member a q → ∀ c w, s.votes a c w → c < b → c ≤ m.1) :
      SafeAt s b m.2 := by
    have hp : s.proposals m.1 m.2 := hv.elim (inv.voted _ _ _) (inv.voted _ _ _)
    intro c hcb
    by_cases hcm : c < m.1
    · exact inv.safe m.1 m.2 hp c hcm
    · refine ⟨q, ?_⟩
      intro a ha
      by_cases existsVote : ∃ w, s.votes a c w
      · obtain ⟨w, hw⟩ := existsVote
        have hle := bounds a ha c w hw hcb
        have eq : c = m.1 := Nat.le_antisymm hle (Nat.le_of_not_gt hcm)
        subst c
        have eqv := inv.unique m.1 w m.2 (inv.voted a m.1 w hw) hp
        exact .inl (eqv ▸ hw)
      · refine .inr ⟨?_, fun w hw => existsVote ⟨w,hw⟩⟩
        rcases ha with rfl | rfl
        · exact Nat.lt_of_lt_of_le hcb sl.1
        · exact Nat.lt_of_lt_of_le hcb sr.1
  cases left with
  | none =>
    cases right with
    | none =>
      intro c hcb
      refine ⟨q, ?_⟩
      intro a ha
      apply Or.inr
      rcases ha with rfl | rfl
      · refine ⟨Nat.lt_of_lt_of_le hcb sl.1, ?_⟩
        intro w hw; obtain ⟨m, hm, _⟩ := sl.2.1 c w hw hcb; cases hm
      · refine ⟨Nat.lt_of_lt_of_le hcb sr.1, ?_⟩
        intro w hw; obtain ⟨m, hm, _⟩ := sr.2.1 c w hw hcb; cases hm
    | some r =>
      apply build r (.inr (sr.2.2 r rfl).2)
      intro a ha c w hw hcb
      rcases ha with rfl | rfl
      · obtain ⟨m, hm, _⟩ := sl.2.1 c w hw hcb; cases hm
      · obtain ⟨m, hm, hle⟩ := sr.2.1 c w hw hcb; cases hm; exact hle
  | some l =>
    cases right with
    | none =>
      apply build l (.inl (sl.2.2 l rfl).2)
      intro a ha c w hw hcb
      rcases ha with rfl | rfl
      · obtain ⟨m, hm, hle⟩ := sl.2.1 c w hw hcb; cases hm; exact hle
      · obtain ⟨m, hm, _⟩ := sr.2.1 c w hw hcb; cases hm
    | some r =>
      simp only [select]
      split
      · next hlt =>
        apply build r (.inr (sr.2.2 r rfl).2)
        intro a ha c w hw hcb
        rcases ha with rfl | rfl
        · obtain ⟨m, hm, hle⟩ := sl.2.1 c w hw hcb; cases hm
          exact Nat.le_trans hle (Nat.le_of_lt hlt)
        · obtain ⟨m, hm, hle⟩ := sr.2.1 c w hw hcb; cases hm; exact hle
      · next hlt =>
        apply build l (.inl (sl.2.2 l rfl).2)
        intro a ha c w hw hcb
        rcases ha with rfl | rfl
        · obtain ⟨m, hm, hle⟩ := sl.2.1 c w hw hcb; cases hm; exact hle
        · obtain ⟨m, hm, hle⟩ := sr.2.1 c w hw hcb; cases hm
          exact Nat.le_trans hle (Nat.le_of_not_gt hlt)

theorem propose_invariant (s : State) (inv : Invariant s) (b : Ballot)
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

theorem step_invariant (s t : State) (inv : Invariant s) (step : Step s t) : Invariant t := by
  cases step with
  | idle => exact inv
  | prepare a b h => exact prepare_invariant s inv a b h
  | propose b offered q left right fresh hl hr =>
    exact propose_invariant s inv b _ fresh (selection_safe s inv b offered q left right hl hr)
  | cast a b v hp ha => exact cast_invariant s inv a b v hp ha

def module : Reactive.Module State :=
  ⟨[⟨[], [], [], fun s => s = initial, Step⟩]⟩

theorem reachable_invariant (s : State) (h : Reactive.Reachable module s) : Invariant s := by
  induction h with
  | @initial s h =>
    have he : s = initial := by simpa [module, Reactive.Module.initial] using h
    subst s; exact initial_invariant
  | @step s t _ h ih =>
    exact step_invariant s t ih (by simpa [module, Reactive.Module.step] using h)

/-- Safety is a consequence of the invariant and quorum intersection. -/
theorem agreement_of_invariant (s : State) (inv : Invariant s)
    (b c : Ballot) (v w : Value) (hb : Chosen s b v) (hc : Chosen s c w) : v = w := by
  obtain ⟨q, hq⟩ := hb
  obtain ⟨r, hr⟩ := hc
  have pv := inv.voted q.first b v (hq q.first (.inl rfl))
  have pw := inv.voted r.first c w (hr r.first (.inl rfl))
  have lower : ∀ (b c : Ballot) (v w : Value), s.proposals b v → c < b → Chosen s c w → v = w := by
    intro b c v w hp hlt ⟨r, hr⟩
    obtain ⟨q, hq⟩ := inv.safe b v hp c hlt
    obtain ⟨a, haq, har⟩ := quorum_intersection q r
    cases hq a haq with
    | inl hv => exact inv.unique c v w (inv.voted a c v hv) (inv.voted a c w (hr a har))
    | inr hn => exact False.elim (hn.2 w (hr a har))
  by_cases h : c < b
  · exact lower b c v w pv h ⟨r, hr⟩
  by_cases h' : b < c
  · exact (lower c b w v pw h' ⟨q, hq⟩).symm
  have he : b = c := Nat.le_antisymm (Nat.le_of_not_gt h) (Nat.le_of_not_gt h')
  subst c
  exact inv.unique b v w pv pw

/-- Agreement for every reachable execution, with no delivery/fairness premise. -/
theorem safety (s : State) (h : Reactive.Reachable module s)
    (b c : Ballot) (v w : Value) (hb : Chosen s b v) (hc : Chosen s c w) : v = w :=
  agreement_of_invariant s (reachable_invariant s h) b c v w hb hc

def HasProposal (s : State) (b : Ballot) : Prop := ∃ v, s.proposals b v

def HasPromise (s : State) (a : Node) (b : Ballot) : Prop := ∃ snap, s.promises a b snap

def PrepareEnabled (a : Node) (b : Ballot) (s : State) : Prop := s.promised a < b

def PrepareTaken (a : Node) (b : Ballot) (s t : State) : Prop :=
  s.promised a < b ∧ t = prepare s a b

def ProposeEnabled (b : Ballot) (s : State) : Prop :=
  (∀ v, ¬ s.proposals b v) ∧ ∃ q : Quorum, HasPromise s q.first b ∧ HasPromise s q.second b

def ProposeTaken (b : Ballot) (s t : State) : Prop :=
  ∃ (offered : Value) (q : Quorum) (left right : Option Vote), (∀ v, ¬ s.proposals b v) ∧
    s.promises q.first b left ∧ s.promises q.second b right ∧
    t = propose s b (select left right offered)

def CastEnabled (a : Node) (b : Ballot) (s : State) : Prop :=
  HasProposal s b ∧ s.promised a ≤ b

def CastTaken (a : Node) (b : Ballot) (s t : State) : Prop :=
  ∃ v, s.proposals b v ∧ s.promised a ≤ b ∧ t = cast s a b v

def HistoriesGrow (s t : State) : Prop :=
  (∀ a b snap, s.promises a b snap → t.promises a b snap) ∧
  (∀ b v, s.proposals b v → t.proposals b v) ∧
  (∀ a b v, s.votes a b v → t.votes a b v)

theorem histories_grow (h : Step s t) : HistoriesGrow s t := by
  cases h <;> simp only [HistoriesGrow, prepare, propose, cast] <;> grind

theorem run_histories (run : Nat → State) (exec : Reactive.Execution module run)
    (n k : Nat) (hnk : n ≤ k) : HistoriesGrow (run n) (run k) := by
  have all : ∀ d, HistoriesGrow (run n) (run (n+d)) := by
    intro d
    induction d with
    | zero => exact ⟨fun _ _ _ h => h, fun _ _ h => h, fun _ _ _ h => h⟩
    | succ d ih =>
      have step : Step (run (n+d)) (run (n+d+1)) := by
        simpa [module, Reactive.Module.step] using exec.2 (n+d)
      obtain ⟨hp, hv, ha⟩ := histories_grow step
      exact ⟨fun a b x h => hp a b x (ih.1 a b x h),
        fun b v h => hv b v (ih.2.1 b v h),
        fun a b v h => ha a b v (ih.2.2 a b v h)⟩
  have eq : n + (k-n) = k := by omega
  simpa [eq] using all (k-n)

/-- Stable-leader assumptions: one positive ballot is never preempted at a
    responsive quorum after `start`; its prepare, propose, and accept actions
    are weakly fair. This does not assume a decision or successful completion. -/
structure Live (run : Nat → State) (b : Ballot) (q : Quorum) (start : Nat) : Prop where
  positive : 0 < b
  stable : ∀ n, start ≤ n → ∀ a, Member a q → (run n).promised a ≤ b
  prepareFair : ∀ a, Member a q → Reactive.WeakFair (PrepareEnabled a b) (PrepareTaken a b) run
  proposeFair : Reactive.WeakFair (ProposeEnabled b) (ProposeTaken b) run
  castFair : ∀ a, Member a q → Reactive.WeakFair (CastEnabled a b) (CastTaken a b) run

/-- Conditional termination of single-decree Paxos, with arbitrary finite
    delays and a stable responsive quorum. No bound on the number of steps. -/
theorem liveness (run : Nat → State) (exec : Reactive.Execution module run)
    (b : Ballot) (q : Quorum) (start : Nat) (live : Live run b q start) :
    Reactive.Eventually (fun s => ∃ v, Chosen s b v) run start := by
  have inv : ∀ n, Invariant (run n) := fun n =>
    reachable_invariant _ (Reactive.execution_reachable module run exec n)
  have promise_progress : ∀ a, Member a q →
      Reactive.Eventually (fun s => HasPromise s a b ∨ HasProposal s b) run start := by
    intro a ha
    apply Reactive.eventually_fair run _ (PrepareEnabled a b) (PrepareTaken a b) start
      (live.prepareFair a ha)
    · intro n hn absent
      have bound := live.stable n hn a ha
      have ne : (run n).promised a ≠ b := by
        intro eq
        rcases (inv n).origin a with hz | hp | hv
        · have : b = 0 := eq.symm.trans hz
          exact Nat.ne_of_gt live.positive this
        · exact absent (.inl (eq ▸ hp))
        · exact absent (.inr (eq ▸ hv))
      exact Nat.lt_of_le_of_ne bound ne
    · intro n _ ⟨_, ht⟩
      rw [ht]
      exact .inl ⟨(run n).accepted a, .inr ⟨rfl,rfl,rfl⟩⟩
  obtain ⟨l, hsl, hl⟩ := promise_progress q.first (.inl rfl)
  obtain ⟨r, hsr, hr⟩ := promise_progress q.second (.inr rfl)
  let ready := max l r
  have hready : start ≤ ready := Nat.le_trans hsl (Nat.le_max_left _ _)
  have ready_at : ∀ n, ready ≤ n → HasProposal (run n) b ∨
      (HasPromise (run n) q.first b ∧ HasPromise (run n) q.second b) := by
    intro n hn
    have lg := run_histories run exec l n (Nat.le_trans (Nat.le_max_left _ _) hn)
    have rg := run_histories run exec r n (Nat.le_trans (Nat.le_max_right _ _) hn)
    rcases hl with ⟨ls, hls⟩ | ⟨v,hv⟩
    · rcases hr with ⟨rs, hrs⟩ | ⟨v,hv⟩
      · exact .inr ⟨⟨ls,lg.1 _ _ _ hls⟩,⟨rs,rg.1 _ _ _ hrs⟩⟩
      · exact .inl ⟨v,rg.2.1 _ _ hv⟩
    · exact .inl ⟨v,lg.2.1 _ _ hv⟩
  have proposed : Reactive.Eventually (fun s => HasProposal s b) run ready := by
    apply Reactive.eventually_fair run _ (ProposeEnabled b) (ProposeTaken b) ready live.proposeFair
    · intro n hn absent
      refine ⟨fun v hv => absent ⟨v,hv⟩, ?_⟩
      rcases ready_at n hn with h | h
      · exact False.elim (absent h)
      · exact ⟨q,h⟩
    · intro n _ ⟨offered, quorum, left, right, _, _, _, ht⟩
      rw [ht]; exact ⟨select left right offered, .inr ⟨rfl,rfl⟩⟩
  obtain ⟨p, hrp, v, hp⟩ := proposed
  have votes_progress : ∀ a, Member a q →
      Reactive.Eventually (fun s => s.votes a b v) run p := by
    intro a ha
    apply Reactive.eventually_fair run _ (CastEnabled a b) (CastTaken a b) p (live.castFair a ha)
    · intro n hn _
      exact ⟨⟨v,(run_histories run exec p n hn).2.1 _ _ hp⟩,
        live.stable n (Nat.le_trans hready (Nat.le_trans hrp hn)) a ha⟩
    · intro n hn ⟨w, hw, _, ht⟩
      have eq := (inv n).unique b w v hw ((run_histories run exec p n hn).2.1 _ _ hp)
      subst w; rw [ht]; exact .inr ⟨rfl,rfl,rfl⟩
  obtain ⟨x,hpx,hx⟩ := votes_progress q.first (.inl rfl)
  obtain ⟨y,hpy,hy⟩ := votes_progress q.second (.inr rfl)
  refine ⟨max x y, Nat.le_trans hready (Nat.le_trans hrp (Nat.le_trans hpx (Nat.le_max_left _ _))), v, q, ?_⟩
  intro a ha
  rcases ha with rfl | rfl
  · exact (run_histories run exec x (max x y) (Nat.le_max_left _ _)).2.2 _ _ _ hx
  · exact (run_histories run exec y (max x y) (Nat.le_max_right _ _)).2.2 _ _ _ hy

/-- Without progress assumptions, a legal infinite idle execution never decides. -/
theorem idle_execution : Reactive.Execution module (fun _ => initial) := by
  constructor
  · simp [module, Reactive.Module.initial]
  · intro n
    simpa [module, Reactive.Module.step] using (Step.idle (s := initial))

theorem idle_never_decides :
    ¬ Reactive.Eventually (fun s => ∃ b v, Chosen s b v) (fun _ => initial) := by
  rintro ⟨n,_,b,v,q,hq⟩
  exact hq q.first (.inl rfl)

#print axioms safety
#print axioms liveness
end RMVerify.Paxos
