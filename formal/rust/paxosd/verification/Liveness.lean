import UserVerification.Progress
import Specification

/- Liveness of the deployed cluster: under partial-synchrony-style assumptions
   (eventually a single leader starts ballots, and messages among a live
   majority are eventually delivered), every replica in that majority decides. -/
namespace PaxosSystem
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos PaxosNode RMVerify

/-- Replica `i` processes input `inp` in this step. -/
def Does (i : Rid) (inp : Input) (w w' : World) : Prop := w' = w.after i (handleS (w.node i) inp)

def Delivers (i : Rid) (p : Packet) : World → World → Prop := Does i (.Deliver (rid p.src) p.send.msg)

def Ticks (i : Rid) : World → World → Prop := Does i .Tick

/-- Environment assumptions from time `T` on, for a leader `L` in a live majority `Q`.
    * a client value has reached a replica of `Q`;
    * no other replica starts a ballot (leader election has stabilised: the
      runtime only fires the other replicas' timers when they suspect `L`);
    * ballots are far from the 2^62 allocation bound;
    * `L`'s timer keeps firing;
    * every packet sent between members of `Q` that stays in the network is
      eventually delivered (retransmission over fair-lossy links).
    Delays are unbounded but finite; replicas outside `Q` may be crashed. -/
structure Fair (run : Nat → World) (L : Rid) (Q : Paxos.Quorum) (T : Nat) : Prop where
  leader : Paxos.Member L Q
  request : ∃ p v, (run T).net p ∧ Paxos.Member p.src Q ∧ p.send.msg = .Request v
  stable : ∀ n, T ≤ n → ∀ j, j ≠ L → ((run (n+1)).node j).ballot = ((run n).node j).ballot
  headroom : top (run T) + 5 < LIMIT
  tick : Reactive.WeakFair (fun _ => True) (Ticks L) run
  deliver : ∀ i p, Paxos.Member i Q → Paxos.Member p.src Q →
    Reactive.WeakFair (fun w => w.net p ∧ Addressed p i) (Delivers i p) run

theorem top_le_max (w : World) (L : Rid) (M : Nat)
    (h : ∀ j, j ≠ L → (w.node j).ballot.val ≤ M) : top w ≤ max (w.node L).ballot.val M := by
  unfold top
  fin_cases L
  · have := h 1 (by decide); have := h 2 (by decide); simp at *; omega
  · have := h 0 (by decide); have := h 2 (by decide); simp at *; omega
  · have := h 0 (by decide); have := h 1 (by decide); simp at *; omega

theorem after_sent {w : World} {i : Rid} {r : Opt Send × Node} {s : Send} (h : r.1 = .Some s) :
    (w.after i r).net ⟨i, s⟩ := .inr ⟨h, rfl⟩

section
variable {run : Nat → World} (exec : Reactive.Execution module run)
  {L : Rid} {Q : Paxos.Quorum} {T : Nat} (live : Fair run L Q T)
include exec live

theorem deliver_ev (i : Rid) (p : Packet) (hi : Paxos.Member i Q) (hs : Paxos.Member p.src Q)
    (n : Nat) (hp : (run n).net p) (ha : Addressed p i) :
    ∃ k, n ≤ k ∧ run (k+1) = (run k).after i
      (handleS ((run k).node i) (.Deliver (rid p.src) p.send.msg)) :=
  live.deliver i p hi hs n (fun k hk => ⟨run_net exec n k hk p hp, ha⟩)

theorem tick_ev (n : Nat) :
    ∃ k, n ≤ k ∧ run (k+1) = (run k).after L (handleS ((run k).node L) .Tick) :=
  live.tick n (fun _ _ => trivial)

theorem others_const (n : Nat) (hn : T ≤ n) (j : Rid) (hj : j ≠ L) :
    ((run n).node j).ballot = ((run T).node j).ballot := by
  induction n, hn using Nat.le_induction with
  | base => rfl
  | succ n hn ih => rw [live.stable n hn j hj, ih]

theorem top_now (n : Nat) (hn : T ≤ n) :
    top (run n) ≤ max ((run n).node L).ballot.val (top (run T)) :=
  top_le_max _ L _ (fun j hj => by rw [others_const exec live n hn j hj]; exact le_top _ _)

theorem leader_bound (n : Nat) (hn : T ≤ n) :
    ((run n).node L).ballot.val ≤ top (run T) + 5 := by
  induction n, hn using Nat.le_induction with
  | base => have := le_top (run T) L; omega
  | succ n hn ih =>
    by_cases e : ((run (n+1)).node L).ballot = ((run n).node L).ballot
    · rw [e]; exact ih
    rcases run_step exec n with e' | ⟨i, inp, _, e'⟩
    · rw [e'] at e; exact absurd rfl e
    by_cases hi : i = L
    · subst hi
      rw [e', after_self] at e ⊢
      obtain ⟨cond, hb⟩ := ballot_moves _ inp e
      have inv := (run_inv exec n).1.1 i
      have hid : ((run n).node i).id.val < 3 := by rw [inv.id, rid_val]; exact i.isLt
      have tn := top_now exec live n hn
      have := inv.promised_top; have := inv.seen_top
      have fl : floorOf ((run n).node i) ≤ top (run T) := by
        unfold floorOf; omega
      rw [hb]; omega
    · rw [e', after_node, if_neg (fun h => hi h.symm)] at e; exact absurd rfl e

theorem top_bound (n : Nat) (hn : T ≤ n) : top (run n) ≤ top (run T) + 5 := by
  have := top_now exec live n hn; have := leader_bound exec live n hn; omega

theorem floor_ok (n : Nat) (hn : T ≤ n) : floorOf ((run n).node L) < LIMIT := by
  have inv := (run_inv exec n).1.1 L
  have := top_bound exec live n hn; have := live.headroom
  have := inv.promised_top; have := inv.seen_top; have := le_top (run n) L
  unfold floorOf; omega

theorem ballot_stable : ∃ n1, T ≤ n1 ∧ ∀ n, n1 ≤ n →
    ((run n).node L).ballot = ((run n1).node L).ballot := by
  obtain ⟨n1, h1, h2⟩ := eventually_const (fun n => ((run n).node L).ballot.val) T (top (run T) + 5)
    (fun n _ => (step_grows exec n L).ballot) (fun n hn => leader_bound exec live n hn)
  exact ⟨n1, h1, fun n hn => UScalar.eq_of_val_eq (h2 n hn)⟩

theorem value_arrives : ∃ tv, T ≤ tv ∧ ∀ n, tv ≤ n → ((run n).node L).value ≠ .None := by
  obtain ⟨p, v, hp, hs, hm⟩ := live.request
  have pi := (run_inv exec T).1.2 p hp
  simp only [PacketInv, hm] at pi
  obtain ⟨k, hk, e⟩ := deliver_ev exec live L p live.leader hs T hp (.inl pi)
  refine ⟨k+1, by omega, fun n hn => ?_⟩
  have got : ((run (k+1)).node L).value ≠ .None := by
    rw [e, after_self, hm]; exact request_sets _ _ _
  intro hnone
  cases hv : ((run (k+1)).node L).value with
  | none => exact got hv
  | some x =>
    have := (run_grows exec (k+1) n hn L).value x hv
    rw [hnone] at this; cases this

/-- The core liveness argument, after the leader's ballot has stabilised at `b`. -/
theorem decides : ∃ t, T ≤ t ∧ ∀ c, Paxos.Member c Q → ((run t).node c).decided ≠ .None := by
  obtain ⟨n1, hT1, hstab⟩ := ballot_stable exec live
  obtain ⟨tv, hTv, hval⟩ := value_arrives exec live
  let n2 := max n1 tv
  have h12 : n1 ≤ n2 := le_max_left _ _
  have hT2 : T ≤ n2 := le_trans hT1 h12
  obtain ⟨b, hbdef⟩ : ∃ b, ((run n1).node L).ballot = b := ⟨_, rfl⟩
  have hb : ∀ n, n2 ≤ n → ((run n).node L).ballot = b :=
    fun n hn => (hstab n (le_trans h12 hn)).trans hbdef
  have hv : ∀ n, n2 ≤ n → ((run n).node L).value ≠ .None :=
    fun n hn => hval n (le_trans (le_max_right _ _) hn)
  have inv : ∀ n, Inv (run n) := fun n => (run_inv exec n).1
  have ainv : ∀ n, Paxos.Invariant (abs (run n)) := fun n => Paxos.reachable_invariant _ (run_inv exec n).2
  -- The leader's ballot is not zero: otherwise its fair timer would start one.
  have b0 : b.val ≠ 0 := by
    intro hz
    obtain ⟨k, hk, e⟩ := tick_ev exec live n2
    have moved := tick_moves ((run k).node L) (floor_ok exec live k (le_trans hT2 hk))
      (.inl ⟨by rw [hb k hk]; exact hz, hv k hk⟩)
    rw [← after_self (run k) L (handleS ((run k).node L) .Tick), ← e, hb k hk, hb (k+1) (by omega)] at moved
    exact moved rfl
  have b0' : b ≠ 0#u64 := fun e => b0 (by rw [e]; rfl)
  -- It has seen no higher ballot: otherwise its fair timer would restart.
  have seen : ∀ n, n2 ≤ n → ((run n).node L).max_seen.val ≤ b.val := by
    intro n hn
    by_contra hgt
    obtain ⟨k, hk, e⟩ := tick_ev exec live n
    have mono := (run_grows exec n k hk L).seen
    have moved := tick_moves ((run k).node L) (floor_ok exec live k (by omega))
      (.inr ⟨by rw [hb k (by omega)]; exact b0, by rw [hb k (by omega)]; omega⟩)
    rw [← after_self (run k) L (handleS ((run k).node L) .Tick), ← e, hb k (by omega),
      hb (k+1) (by omega)] at moved
    exact moved rfl
  have own : b.val % 3 = L.val := by
    have := (inv n2).1 L |>.own; rw [hb n2 le_rfl] at this; exact this.resolve_left b0
  let P : Packet := ⟨L, ⟨.All, .Prepare b⟩⟩
  have hP : (run n2).net P := by
    have := ((inv n2).1 L).started (by rw [hb n2 le_rfl]; exact b0)
    rw [hb n2 le_rfl] at this; exact this.2
  have hPn : ∀ n, n2 ≤ n → (run n).net P := fun n hn => run_net exec n2 n hn P hP
  -- Every acceptor of the quorum stays at or below `b`: a higher promise would
  -- answer the retransmitted prepare with a nack that raises `max_seen`.
  have promised : ∀ a, Paxos.Member a Q → ∀ n, n2 ≤ n → ((run n).node a).promised.val ≤ b.val := by
    intro a ha n hn
    by_contra hgt
    obtain ⟨k, hk, e⟩ := deliver_ev exec live a P ha live.leader n (hPn n hn) (.inl rfl)
    have mono := (run_grows exec n k hk a).promised
    have out := prepare_output ((run k).node a) L b
    rw [if_neg (by omega)] at out
    have hN := after_sent (w := run k) (i := a) out
    rw [← e] at hN
    obtain ⟨k', hk', e'⟩ := deliver_ev exec live L _ live.leader ha (k+1) hN (.inr rfl)
    have raised := nack_raises ((run k').node L) a b ((run k).node a).promised
    rw [← after_self (run k') L (handleS ((run k').node L) _), ← e'] at raised
    have := seen (k'+1) (by omega)
    omega
  -- The leader eventually proposes.
  have proposes : ∃ n3, n2 ≤ n3 ∧ ((run n3).node L).proposal ≠ .None := by
    by_contra hno
    push Not at hno
    have sent : ∀ a, Paxos.Member a Q → ∃ t y, n2 ≤ t ∧ (run t).net ⟨a, ⟨.To (rid L), .Promise b y⟩⟩ := by
      intro a ha
      obtain ⟨k, hk, e⟩ := deliver_ev exec live a P ha live.leader n2 hP (.inl rfl)
      have hle := promised a ha k hk
      by_cases hlt : ((run k).node a).promised.val < b.val
      · have out := prepare_output ((run k).node a) L b
        rw [if_pos hlt] at out
        have hN := after_sent (w := run k) (i := a) out
        rw [← e] at hN
        exact ⟨k+1, _, by omega, hN⟩
      · have heq : (abs (run k)).promised a = b.val :=
          Nat.le_antisymm hle (Nat.le_of_not_lt hlt)
        rcases (ainv k).origin a with h0 | ⟨snap, hs⟩ | ⟨v, hv'⟩
        · rw [heq] at h0; exact absurd h0 b0
        · rw [heq] at hs
          obtain ⟨pk, hpk, hsrc, x, y, hmsg, hx, _⟩ := hs
          have pi := (inv k).2 pk hpk
          simp only [PacketInv, hmsg] at pi
          have xb : x = b := UScalar.eq_of_val_eq hx
          rw [xb] at hmsg pi
          rw [owner_of b L own] at pi
          refine ⟨k, y, hk, ?_⟩
          have : pk = ⟨a, ⟨.To (rid L), .Promise b y⟩⟩ := by
            obtain ⟨src, ⟨dst, msg⟩⟩ := pk; simp only at hsrc pi hmsg; subst hsrc pi hmsg; rfl
          rw [← this]; exact hpk
        · rw [heq] at hv'
          obtain ⟨pk, hpk, vt, hmsg, hvb, _⟩ := hv'
          have pi := (inv k).2 pk hpk
          simp only [PacketInv, hmsg] at pi
          obtain ⟨_, hmod, _, hprop, _⟩ := pi
          have hsrc : pk.src = L := Fin.ext (by rw [← hmod, hvb, own])
          rw [hsrc] at hprop
          have := hprop (UScalar.eq_of_val_eq (by rw [hvb, hb k hk]))
          have h2 := hno k hk; rw [this] at h2; cases h2
    have slot : ∀ a, Paxos.Member a Q → ∃ d, n2 ≤ d ∧ ∀ n, d ≤ n → pslot ((run n).node L) a ≠ .None := by
      intro a ha
      obtain ⟨t, y, ht, hpk⟩ := sent a ha
      obtain ⟨d, hd, e⟩ := deliver_ev exec live L _ live.leader ha t hpk (.inr rfl)
      refine ⟨d+1, by omega, fun n hn => ?_⟩
      have hrec := promise_records ((run d).node L) a b y (hb d (by omega)) b0' (by
        have := hno d (by omega); simpa using this)
      rw [← after_self (run d) L (handleS ((run d).node L) _), ← e] at hrec
      exact (run_grows exec (d+1) n hn L).slot (by rw [hb n (by omega), hb (d+1) (by omega)]) a hrec
    obtain ⟨d1, hd1, s1⟩ := slot Q.first (.inl rfl)
    obtain ⟨d2, hd2, s2⟩ := slot Q.second (.inr rfl)
    let n := max d1 d2
    have hpend := ((inv n).1 L).pending (by have := hno n (by omega); simpa using this)
    exact quorumS_of_two _ Q (s1 n (le_max_left _ _)) (s2 n (le_max_right _ _)) hpend
  obtain ⟨n3, h23, hprop⟩ := proposes
  obtain ⟨x, hx⟩ : ∃ x, ((run n3).node L).proposal = .Some x := by
    cases h : ((run n3).node L).proposal with
    | none => exact absurd h hprop
    | some x => exact ⟨x, rfl⟩
  let A : Packet := ⟨L, ⟨.All, .Accept ⟨b, x⟩⟩⟩
  have hA : (run n3).net A := by
    have := (((inv n3).1 L).proposed x hx).2; rw [hb n3 h23] at this; exact this
  -- Both quorum acceptors accept the proposal.
  have accepted : ∀ a, Paxos.Member a Q → ∃ t, n3 ≤ t ∧ (run t).net ⟨a, ⟨.All, .Accepted ⟨b, x⟩⟩⟩ := by
    intro a ha
    obtain ⟨k, hk, e⟩ := deliver_ev exec live a A ha live.leader n3 hA (.inl rfl)
    have out := accept_output ((run k).node a) L ⟨b, x⟩
    rw [if_pos (promised a ha k (by omega))] at out
    have hN := after_sent (w := run k) (i := a) out
    rw [← e] at hN
    exact ⟨k+1, by omega, hN⟩
  -- Any vote from a quorum acceptor at ballot `b` or higher is exactly the proposal.
  have pinned : ∀ c a, Paxos.Member a Q → ∀ n, n3 ≤ n → ∀ vt,
      vslot ((run n).node c) a = .Some vt → b.val ≤ vt.ballot.val → vt = ⟨b, x⟩ := by
    intro c a ha n hn vt hs hge
    obtain ⟨pk, hpk, hsrc, hmsg⟩ := ((inv n).1 c).votes a vt hs
    have pi := (inv n).2 pk hpk
    simp only [PacketInv, hmsg] at pi
    rw [hsrc] at pi
    have := promised a ha n (by omega)
    have vb : vt.ballot = b := UScalar.eq_of_val_eq (by omega)
    have hvote : (abs (run n)).votes a b.val vt.value.val := ⟨pk, hpk, hsrc, vt, hmsg, by rw [vb], rfl⟩
    have p1 := (ainv n).voted _ _ _ hvote
    have p2 : (abs (run n)).proposals b.val x.val :=
      ⟨A, run_net exec n3 n hn A hA, ⟨b, x⟩, rfl, rfl, rfl⟩
    have := UScalar.eq_of_val_eq ((ainv n).unique _ _ _ p1 p2)
    cases vt; simp_all
  -- Every learner of the quorum eventually decides.
  have learns : ∀ c, Paxos.Member c Q → ∃ t, T ≤ t ∧ ∀ n, t ≤ n → ((run n).node c).decided ≠ .None := by
    intro c hc
    have heard : ∀ a, Paxos.Member a Q → ∃ d, n3 ≤ d ∧ ∀ n, d ≤ n → vslot ((run n).node c) a = .Some ⟨b, x⟩ := by
      intro a ha
      obtain ⟨t, ht, hpk⟩ := accepted a ha
      obtain ⟨d, hd, e⟩ := deliver_ev exec live c _ hc ha t hpk (.inl rfl)
      refine ⟨d+1, by omega, fun n hn => ?_⟩
      obtain ⟨v1, h1, l1⟩ := accepted_records ((run d).node c) a ⟨b, x⟩
      rw [← after_self (run d) c (handleS ((run d).node c) _), ← e] at h1
      obtain ⟨v2, h2, l2⟩ := (run_grows exec (d+1) n hn c).vote a v1 h1
      rw [h2, pinned c a ha n (by omega) v2 h2 (le_trans l1 l2)]
    obtain ⟨d1, hd1, s1⟩ := heard Q.first (.inl rfl)
    obtain ⟨d2, hd2, s2⟩ := heard Q.second (.inr rfl)
    let n := max d1 d2
    refine ⟨n, by omega, fun m hm => ?_⟩
    have got : ((run n).node c).decided ≠ .None := by
      intro hnone
      exact agreedS_of_two _ Q _ (s1 n (le_max_left _ _)) (s2 n (le_max_right _ _))
        (((inv n).1 c).undecided hnone)
    intro hnone
    cases hd : ((run n).node c).decided with
    | none => exact got hd
    | some y =>
      have := (run_grows exec n m hm c).decided y hd
      rw [hnone] at this; cases this
  obtain ⟨t1, ht1, l1⟩ := learns Q.first (.inl rfl)
  obtain ⟨t2, ht2, l2⟩ := learns Q.second (.inr rfl)
  refine ⟨max t1 t2, by omega, fun c hc => ?_⟩
  rcases hc with rfl | rfl
  · exact l1 _ (le_max_left _ _)
  · exact l2 _ (le_max_right _ _)

end

/-- Liveness: in every execution of the extracted replicas satisfying the
    environment assumptions, every replica of the live majority decides. -/
theorem liveness (run : Nat → World) (exec : Reactive.Execution module run)
    (L : Rid) (Q : Paxos.Quorum) (T : Nat) (live : Fair run L Q T) :
    Reactive.Eventually (fun w => ∀ c, Paxos.Member c Q → (w.node c).decided ≠ .None) run T :=
  decides exec live

/-- Without environment assumptions, an idle execution is legal and never decides. -/
theorem idle_never_decides (w : World) (h : Initial w) :
    Reactive.Execution module (fun _ => w) ∧
    ¬ Reactive.Eventually (fun w => ∃ c, (w.node c).decided ≠ .None) (fun _ => w) := by
  refine ⟨⟨by simpa [module, Reactive.Module.initial] using h,
    fun _ => by simpa [module, Reactive.Module.step] using (Step.idle (w := w))⟩, ?_⟩
  rintro ⟨n, _, c, hc⟩
  have := h.1 c; rw [new_eq] at this; simp only [ok.injEq] at this
  rw [← this] at hc; exact hc rfl

/-- Some execution suffix satisfies the environment assumptions. -/
def Live (run : Nat → World) : Prop := ∃ L Q T, Fair run L Q T

/-- Every replica of some majority has decided. -/
def QuorumDecided (w : World) : Prop :=
  ∃ q : Paxos.Quorum, ∀ c, Paxos.Member c q → (w.node c).decided ≠ .None

theorem eventually_quorum_decided : RMVerify.Spec.Eventually module Live QuorumDecided := by
  intro run exec ⟨L, Q, T, live⟩
  obtain ⟨n, _, h⟩ := liveness run exec L Q T live
  exact ⟨n, Nat.zero_le _, Q, h⟩

#print axioms liveness
#print axioms eventually_quorum_decided
end PaxosSystem
