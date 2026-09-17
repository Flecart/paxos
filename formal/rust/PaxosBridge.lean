import VerifiedPaxos.Extraction
import Paxos

/- This adapter gives the composed operational semantics of the extracted Rust
   components. Histories are ghost state: the environment can deliver only
   previously emitted authenticated messages. The runtime must preserve this
   interface and globally unique proposer ballots. No socket/runtime proof is
   asserted by this module. -/
namespace PaxosBridge
open CoreModels Aeneas Aeneas.Std
open RustM
open RMVerify

abbrev ROption := core.option.Option
abbrev RVote := verified_paxos.Vote
abbrev RPromise := verified_paxos.Promise
abbrev RAcceptor := verified_paxos.Acceptor
abbrev RProposer := verified_paxos.Proposer

def vote (v : RVote) : Paxos.Vote := (v.ballot.val, v.value.val)

def snapshot : ROption RVote → Option Paxos.Vote
  | .None => none
  | .Some v => some (vote v)

def selected (l r : ROption RVote) (offered : U64) : U64 :=
  match l,r with
  | .None, .None => offered
  | .Some a, .None => a.value
  | .None, .Some b => b.value
  | .Some a, .Some b => if a.ballot.val < b.ballot.val then b.value else a.value

theorem initial_eq : verified_paxos.Acceptor.new = ok
    ({ promised := 0#u64, accepted := .None } : RAcceptor) := by
  rfl

theorem proposer_initial_eq (b : U64) : verified_paxos.Proposer.new b = ok
    ({ ballot := b, issued := .None } : RProposer) := by
  rfl

theorem retransmit_eq (p : RProposer) :
    verified_paxos.Proposer.retransmit p = ok p.issued := by
  rfl

theorem select_eq (l r : ROption RVote) (offered : U64) :
    verified_paxos.select l r offered = ok (selected l r offered) := by
  cases l <;> cases r <;> simp [verified_paxos.select, selected, UScalar.lt_equiv]
  split_ifs <;> rfl

theorem selected_eq (l r : ROption RVote) (offered : U64) :
    (selected l r offered).val = Paxos.select (snapshot l) (snapshot r) offered.val := by
  cases l <;> cases r <;> simp [selected, snapshot, vote, Paxos.select]
  split <;> rfl

theorem prepare_eq (s : RAcceptor) (b : U64) :
    verified_paxos.Acceptor.prepare s b = ok
      (if s.promised.val < b.val then
        (.Some { ballot := b, accepted := s.accepted }, { s with promised := b })
       else (.None, s)) := by
  simp only [verified_paxos.Acceptor.prepare, UScalar.lt_equiv]
  split_ifs <;> rfl

theorem accept_eq (s : RAcceptor) (v : RVote) :
    verified_paxos.Acceptor.accept s v = ok
      (if s.promised.val ≤ v.ballot.val then
        (true, { promised := v.ballot, accepted := .Some v }) else (false, s)) := by
  simp only [verified_paxos.Acceptor.accept, UScalar.le_equiv]
  split_ifs <;> rfl

theorem issue_success (p : RProposer) (i j : U8) (l r : RPromise) (offered : U64)
    (v : RVote) (p' : RProposer)
    (h : verified_paxos.Proposer.issue p i l j r offered = ok (.Some v,p')) :
    i.val < 3 ∧ j.val < 3 ∧ i ≠ j ∧ l.ballot = p.ballot ∧ r.ballot = p.ballot ∧
    p.issued = .None ∧ v.ballot = p.ballot ∧ v.value = selected l.accepted r.accepted offered ∧
    p' = { p with issued := .Some v } := by
  simp only [verified_paxos.Proposer.issue, select_eq] at h
  split_ifs at h <;> simp_all [UScalar.le_equiv]
  split at h <;> simp_all
  all_goals grind [UScalar.eq_equiv]

theorem issue_enabled (p : RProposer) (i j : U8) (l r : RPromise) (offered : U64)
    (hi : i.val < 3) (hj : j.val < 3) (hne : i ≠ j)
    (hl : l.ballot = p.ballot) (hr : r.ballot = p.ballot) (fresh : p.issued = .None) :
    verified_paxos.Proposer.issue p i l j r offered =
      ok (.Some {ballot:=p.ballot,value:=selected l.accepted r.accepted offered},
          {p with issued:=.Some {ballot:=p.ballot,value:=selected l.accepted r.accepted offered}}) := by
  simp [verified_paxos.Proposer.issue, select_eq, UScalar.le_equiv, Nat.not_le.mpr hi, Nat.not_le.mpr hj, hne, hl, hr, fresh]

theorem learn_enabled (i j : U8) (l r : RVote)
    (hi : i.val < 3) (hj : j.val < 3) (hne : i ≠ j)
    (hb : l.ballot = r.ballot) (hv : l.value = r.value) :
    verified_paxos.learn i l j r = ok (.Some l.value) := by
  simp [verified_paxos.learn, UScalar.lt_equiv, hi, hj, hne, hb, hv]

theorem learn_success (i j : U8) (l r : RVote) (v : U64)
    (h : verified_paxos.learn i l j r = ok (.Some v)) :
    i.val < 3 ∧ j.val < 3 ∧ i ≠ j ∧ l.ballot = r.ballot ∧ l.value = r.value ∧ v = l.value := by
  simp only [verified_paxos.learn] at h
  split_ifs at h <;> simp_all [UScalar.lt_equiv]

def Matches (s : Paxos.State) (a : Paxos.Node) (r : RAcceptor) : Prop :=
  s.promised a = r.promised.val ∧ s.accepted a = snapshot r.accepted

def prepared (s : Paxos.State) (a : Paxos.Node) (reply : RPromise) (next : RAcceptor) : Paxos.State :=
  { s with promised := Paxos.put s.promised a next.promised.val
           accepted := Paxos.put s.accepted a (snapshot next.accepted)
           promises := fun i b snap => s.promises i b snap ∨
             (i = a ∧ b = reply.ballot.val ∧ snap = snapshot reply.accepted) }

def accepted (s : Paxos.State) (a : Paxos.Node) (v : RVote) (next : RAcceptor) : Paxos.State :=
  { s with promised := Paxos.put s.promised a next.promised.val
           accepted := Paxos.put s.accepted a (snapshot next.accepted)
           votes := fun i b w => s.votes i b w ∨
             (i = a ∧ b = v.ballot.val ∧ w = v.value.val) }

/-- Operational composition of Rust functions, with authenticated message
    histories and exclusive ownership of each globally unique proposer ballot. -/
inductive Step : Paxos.State → Paxos.State → Prop where
  | idle : Step s s
  | prepare (a r b reply next) (repr : Matches s a r)
      (exec : verified_paxos.Acceptor.prepare r b = ok (.Some reply,next)) :
      Step s (prepared s a reply next)
  | issue (q : Paxos.Quorum) (p : RProposer) (i j : U8) (l r : RPromise) (offered : U64)
      (v : RVote) (next : RProposer)
      (ids : i.val = q.first.val ∧ j.val = q.second.val)
      (owner : p.issued = .None → ∀ w, ¬ s.proposals p.ballot.val w)
      (left : s.promises q.first l.ballot.val (snapshot l.accepted))
      (right : s.promises q.second r.ballot.val (snapshot r.accepted))
      (exec : verified_paxos.Proposer.issue p i l j r offered = ok (.Some v,next)) :
      Step s (Paxos.propose s v.ballot.val v.value.val)
  | accept (a r v next) (repr : Matches s a r)
      (sent : s.proposals v.ballot.val v.value.val)
      (exec : verified_paxos.Acceptor.accept r v = ok (true,next)) :
      Step s (accepted s a v next)

theorem put_same (f : Paxos.Node → α) (a : Paxos.Node) : Paxos.put f a (f a) = f := by
  funext i; by_cases hi : i = a <;> simp [Paxos.put, hi]

theorem step_refines (h : Step s t) : Paxos.Step s t := by
  cases h with
  | idle => exact .idle
  | prepare a r b reply next hm he =>
    rw [prepare_eq] at he
    split at he
    · next hlt =>
      have eq : reply = { ballot := b, accepted := r.accepted } ∧ next = { r with promised := b } := by
        simpa using he.symm
      obtain ⟨rfl,rfl⟩ := eq
      have hs : prepared s a {ballot:=b,accepted:=r.accepted} {r with promised:=b} = Paxos.prepare s a b.val := by
        simp [prepared, Paxos.prepare, ← hm.2, put_same]
      rw [hs]
      exact .prepare a b.val (by simpa [hm.1] using hlt)
    · simp at he
  | issue q p i j l r offered v next ids owner hl hr he =>
    obtain ⟨_,_,_,hleft,hright,hfresh,hballot,hvalue,_⟩ := issue_success p i j l r offered v next he
    rw [hballot,hvalue, selected_eq]
    apply Paxos.Step.propose p.ballot.val offered.val q (snapshot l.accepted) (snapshot r.accepted)
    · exact owner hfresh
    · simpa [hleft] using hl
    · simpa [hright] using hr
  | accept a r v next hm sent he =>
    rw [accept_eq] at he
    split at he
    · next hle =>
      have eq : next = {promised:=v.ballot,accepted:=.Some v} := by simpa using he.symm
      subst next
      change Paxos.Step s (Paxos.cast s a v.ballot.val v.value.val)
      exact .cast a v.ballot.val v.value.val sent (by simpa [hm.1] using hle)
    · simp at he

def module : Reactive.Module Paxos.State :=
  ⟨[⟨[],[],[],fun s => s = Paxos.initial, Step⟩]⟩

theorem reachable_refines (s : Paxos.State) (h : Reactive.Reachable module s) :
    Reactive.Reachable Paxos.module s := by
  induction h with
  | @initial s h =>
    apply Reactive.Reachable.initial
    simpa [module, Paxos.module, Reactive.Module.initial] using h
  | @step s t _ h ih =>
    apply Reactive.Reachable.step ih
    have hs : Step s t := by simpa [module, Reactive.Module.step] using h
    simpa [Paxos.module, Reactive.Module.step] using step_refines hs

theorem execution_refines (run : Nat → Paxos.State) (h : Reactive.Execution module run) :
    Reactive.Execution Paxos.module run := by
  refine ⟨?_, ?_⟩
  · simpa [module, Paxos.module, Reactive.Module.initial] using h.1
  · intro n
    have hs : Step (run n) (run (n+1)) := by simpa [module, Reactive.Module.step] using h.2 n
    simpa [Paxos.module, Reactive.Module.step] using step_refines hs

def Learned (s : Paxos.State) (value : U64) : Prop :=
  ∃ (q : Paxos.Quorum) (i j : U8) (l r : RVote),
    i.val = q.first.val ∧ j.val = q.second.val ∧
    s.votes q.first l.ballot.val l.value.val ∧ s.votes q.second r.ballot.val r.value.val ∧
    verified_paxos.learn i l j r = ok (.Some value)

theorem learned_chosen (h : Learned s v) : ∃ b, Paxos.Chosen s b v.val := by
  obtain ⟨q,i,j,l,r,_,_,hl,hr,he⟩ := h
  obtain ⟨_,_,_,hb,hv,rfl⟩ := learn_success i j l r v he
  refine ⟨l.ballot.val,q,?_⟩
  intro a ha
  rcases ha with rfl | rfl
  · exact hl
  · simpa [← hb, ← hv] using hr

def SafetyClaim : Prop := ∀ s, Reactive.Reachable module s →
  ∀ v w, Learned s v → Learned s w → v = w

/-- Successful local computation is proved as well as conditional network
    progress, so a handler that always rejects cannot get a vacuous live result. -/
def LocalProgress : Prop :=
  (∀ (r : RAcceptor) (b : U64), r.promised.val < b.val →
    ∃ reply next, verified_paxos.Acceptor.prepare r b = ok (.Some reply,next)) ∧
  (∀ (r : RAcceptor) (v : RVote), r.promised.val ≤ v.ballot.val →
    ∃ next, verified_paxos.Acceptor.accept r v = ok (true,next)) ∧
  (∀ (p : RProposer) (i j : U8) (l r : RPromise) (offered : U64),
    i.val < 3 → j.val < 3 → i ≠ j → l.ballot = p.ballot → r.ballot = p.ballot → p.issued = .None →
    ∃ v next, verified_paxos.Proposer.issue p i l j r offered = ok (.Some v,next)) ∧
  (∀ (i j : U8) (l r : RVote), i.val < 3 → j.val < 3 → i ≠ j →
    l.ballot = r.ballot → l.value = r.value → verified_paxos.learn i l j r = ok (.Some l.value))

theorem local_progress : LocalProgress := by
  refine ⟨?_,?_,?_,?_⟩
  · intro r b h; simp [prepare_eq,h]
  · intro r v h; simp [accept_eq,h]
  · intro p i j l r offered hi hj hn hl hr hf
    exact ⟨_,_,issue_enabled p i j l r offered hi hj hn hl hr hf⟩
  · exact learn_enabled

def LivenessClaim : Prop := LocalProgress ∧ ∀ run, Reactive.Execution module run →
  ∀ (b : U64) q start, Paxos.Live run b.val q start →
    Reactive.Eventually (fun s => ∃ v, Paxos.Chosen s b.val v) run start

theorem safety : SafetyClaim := by
  intro s hs v w hv hw
  obtain ⟨b,hb⟩ := learned_chosen hv
  obtain ⟨c,hc⟩ := learned_chosen hw
  apply UScalar.eq_of_val_eq
  exact Paxos.safety s (reachable_refines s hs) b c v.val w.val hb hc

theorem liveness : LivenessClaim := by
  refine ⟨local_progress, ?_⟩
  intro run hr b q start live
  exact Paxos.liveness run (execution_refines run hr) b.val q start live

#print axioms initial_eq
#print axioms proposer_initial_eq
#print axioms safety
#print axioms liveness
#print axioms retransmit_eq
#print axioms select_eq
#print axioms prepare_eq
#print axioms accept_eq
#print axioms issue_success
#print axioms learn_success
end PaxosBridge
