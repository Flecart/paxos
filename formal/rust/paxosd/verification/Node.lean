import DeployablePaxos.Extraction
import Mathlib.Data.Finset.Card
import Mathlib.Data.Fintype.Card
import Mathlib.Data.Fintype.Fin

/- Pure characterisation of the extracted replica state machine for a cluster
   of `n` replicas. Every extracted function is proved equal to `ok` of a total
   Lean function, so the Rust code never panics, and all later reasoning uses
   these equations. The loops (`count_promises`, `highest`, `count_votes`,
   `Node::new`) are characterised by list functions. -/
namespace PaxosNode
open CoreModels Aeneas Aeneas.Std RustM deployable_paxos
set_option Aeneas.Deprecated.progressWarning false
set_option linter.unusedSimpArgs false
set_option linter.style.multiGoal false
set_option linter.unnecessarySeqFocus false

abbrev Opt := core.option.Option
abbrev RVec (α : Type) := CoreModels.alloc.vec.Vec α

/-- Elements of an extracted vector. -/
def items {α : Type} (s : RVec α) : List α := (s : Aeneas.Std.Slice α).val

theorem items_length_le {α : Type} (s : RVec α) : (items s).length ≤ Usize.max :=
  (s : Aeneas.Std.Slice α).property

/-- Entry `i`, or `None` outside the vector. -/
def slot {α : Type} (s : RVec (Opt α)) (i : Nat) : Opt α := ((items s)[i]?).getD .None

/-- The vector with entry `i` replaced (unchanged outside the vector). -/
def setAt {α : Type} (s : RVec α) (i : Nat) (x : α) : RVec α :=
  (⟨(items s).set i x, by simpa using items_length_le s⟩ : Aeneas.Std.Slice α)

/-- A vector of `k` copies of `x`. -/
def replicate {α : Type} (k : Nat) (x : α) (h : k ≤ Usize.max) : RVec α :=
  (⟨List.replicate k x, by simpa using h⟩ : Aeneas.Std.Slice α)

def LIMIT : Nat := 4611686018427387904

def higherS (a b : U64) : U64 := if a < b then b else a

def nextS (floor : U64) (id n : U8) : U64 :=
  ⟨BitVec.ofNat 64 ((floor.val / n.val + 1) * n.val + id.val)⟩

/-- Strict majority of a cluster of `n`. -/
def Majority (c : Nat) (n : U8) : Prop := n.val / 2 < c

instance (c : Nat) (n : U8) : Decidable (Majority c n) := by unfold Majority; infer_instance

def promiseHit (b : U64) : Opt Promise → Bool
  | .Some p => decide (p.ballot = b)
  | .None => false

def countPromisesS (ps : List (Opt Promise)) (b : U64) : Nat := ps.countP (promiseHit b)

/-- One iteration of the `highest` loop. -/
def bestStep (b : U64) (best : Opt Vote) : Opt Promise → Opt Vote
  | .Some p =>
    if p.ballot = b then
      match p.accepted with
      | .None => best
      | .Some v =>
        match best with
        | .None => .Some v
        | .Some m => if m.ballot < v.ballot then .Some v else .Some m
    else best
  | .None => best

def highestS (ps : List (Opt Promise)) (b : U64) : Opt Vote := ps.foldl (bestStep b) .None

def voteHit (v : Vote) : Opt Vote → Bool
  | .Some x => decide (x.ballot = v.ballot ∧ x.value = v.value)
  | .None => false

def countVotesS (vs : List (Opt Vote)) (v : Vote) : Nat := vs.countP (voteHit v)

def startS (n : Node) : Opt Send × Node :=
  if n.n = 0#u8 then (.None, n)
  else
    let floor := higherS (higherS n.max_seen n.promised) n.ballot
    if LIMIT ≤ floor.val then (.None, n)
    else
      let b := nextS floor n.id n.n
      (.Some ⟨.All, .Prepare b⟩, { n with ballot := b, proposal := .None })

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

def onPromiseS (n : Node) (src : U8) (b : U64) (acc : Opt Vote) : Opt Send × Node :=
  if b ≠ n.ballot then (.None, n)
  else if b = 0#u64 then (.None, n)
  else match n.proposal with
    | .Some _ => (.None, n)
    | .None =>
      if (items n.promises).length ≤ src.val then (.None, n)
      else
        let ps := setAt n.promises src.val (.Some ⟨b, acc⟩)
        match n.value with
        | .None => (.None, { n with promises := ps })
        | .Some v =>
          if Majority (countPromisesS (items ps) b) n.n then
            match highestS (items ps) b with
            | .None => (.Some ⟨.All, .Accept ⟨b, v⟩⟩, { n with proposal := .Some v, promises := ps })
            | .Some m =>
              (.Some ⟨.All, .Accept ⟨b, m.value⟩⟩, { n with proposal := .Some m.value, promises := ps })
          else (.None, { n with promises := ps })

def newer (cur : Opt Vote) (v : Vote) : Bool :=
  match cur with
  | .None => true
  | .Some old => decide (old.ballot < v.ballot)

def onAcceptedS (n : Node) (src : U8) (v : Vote) : Opt Send × Node :=
  if (items n.votes).length ≤ src.val then (.None, n)
  else
    let vs := if newer (slot n.votes src.val) v then setAt n.votes src.val (.Some v) else n.votes
    match n.decided with
    | .None =>
      if Majority (countVotesS (items vs) v) n.n then
        (.None, { n with votes := vs, decided := .Some v.value })
      else (.None, { n with votes := vs })
    | .Some _ => (.None, { n with votes := vs })

def deliverS (n : Node) (src : U8) (msg : Msg) : Opt Send × Node :=
  if n.n.val ≤ src.val then (.None, n)
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

theorem u8_le_usize (n : U8) : n.val ≤ Usize.max := by
  scalar_tac

def initS (id n : U8) : Node :=
  { id, n, promised := 0#u64, accepted := .None, value := .None, ballot := 0#u64,
    max_seen := 0#u64, proposal := .None,
    promises := replicate n.val .None (u8_le_usize n),
    votes := replicate n.val .None (u8_le_usize n), decided := .None }

/-! ## Helper lemmas about vectors and loops -/

theorem items_setAt' {α : Type} (s : RVec α) (i : Nat) (x : α) :
    items (setAt s i x) = (items s).set i x := rfl
theorem items_replicate' {α : Type} (k : Nat) (x : α) (h : k ≤ Usize.max) :
    items (replicate k x h) = List.replicate k x := rfl

theorem usize_le_u64 : Usize.max ≤ U64.max := by
  rcases Usize.bounds_eq with h | h <;> rw [h] <;> simp [U32.max_eq, U64.max_eq]

theorem vec_len_eq {α : Type} (s : RVec α) :
    CoreModels.alloc.vec.Vec.len s = ok (Slice.len (s : Slice α)) := rfl

theorem index_eq {α : Type} (s : RVec α) (i : Usize) (h : i.val < (items s).length) :
    alloc.vec.Vec.Insts.CoreOpsIndexIndex.index
      (core.Usize.Insts.CoreSliceIndexSliceIndexSliceT α) s i = ok ((items s)[i.val]) := by
  have hi : i < Slice.len (s : Slice α) := by rw [UScalar.lt_equiv]; simpa [items] using h
  simp [alloc.vec.Vec.Insts.CoreOpsIndexIndex.index, core.Slice.Insts.CoreOpsIndexIndex.index,
    rust_primitives.sequence.seq_to_slice, core.Usize.Insts.CoreSliceIndexSliceIndexSliceT.get,
    rust_primitives.slice.slice_length, rust_primitives.slice.slice_index,
    CoreModels.alloc.vec.Vec.Insts.CoreOpsDerefDerefSlice.deref, CoreModels.alloc.vec.Vec.as_slice]
  simp only [items] at h
  simp [h, items, Slice.index_usize, Slice.getElem?_Usize_eq, List.getElem?_eq_getElem h]

theorem index_mut_eq {α : Type} (s : RVec α) (i : Usize) (h : i.val < (items s).length) :
    alloc.vec.Vec.Insts.CoreOpsIndexIndexMut.index_mut
      (core.Usize.Insts.CoreSliceIndexSliceIndexSliceT α) s i =
      ok ((items s)[i.val], fun x => setAt s i.val x) := by
  simp only [items] at h
  simp [alloc.vec.Vec.Insts.CoreOpsIndexIndexMut.index_mut, core.Slice.Insts.CoreOpsIndexIndexMut.index_mut,
    rust_primitives.sequence.seq_to_slice_mut, core.Usize.Insts.CoreSliceIndexSliceIndexSliceT.get_unchecked_mut,
    rust_primitives.slice.slice_index_mut, Slice.index_mut_usize,
    Slice.index_usize, Slice.getElem?_Usize_eq, List.getElem?_eq_getElem h, bind_tc_ok]
  exact ⟨rfl, rfl⟩

theorem count_promises_spec (ps : RVec (Opt Promise)) (b : U64) :
    count_promises ps b ⦃ c => c.val = countPromisesS (items ps) b ⦄ := by
  unfold count_promises count_promises_loop
  have hlen := items_length_le ps
  apply loop.spec_decr_nat (fun (x : Usize × U64) => (items ps).length - x.1.val)
    (fun x => x.1.val ≤ (items ps).length ∧ x.2.val = countPromisesS ((items ps).take x.1.val) b)
  · rintro ⟨i, c⟩ ⟨hi, hc⟩
    simp only at hi hc
    unfold count_promises_loop.body
    have hcle : c.val ≤ i.val := by
      rw [hc]; exact le_trans List.countP_le_length (by simp)
    by_cases hlt : i.val < (items ps).length
    · have hlt' : i < Slice.len (ps : Slice _) := by rw [UScalar.lt_equiv]; simpa [items] using hlt
      have take_succ : countPromisesS ((items ps).take (i.val + 1)) b =
          countPromisesS ((items ps).take i.val) b + (if promiseHit b (items ps)[i.val] then 1 else 0) := by
        rw [List.take_add_one, List.getElem?_eq_getElem hlt]
        simp only [countPromisesS, List.countP_append, Option.toList_some, List.countP_singleton]
        cases promiseHit b (items ps)[i.val] <;> rfl
      simp only [vec_len_eq, bind_tc_ok, hlt', if_true, index_eq ps i hlt]
      have h64 : c.val + 1 ≤ U64.max := by
        have := usize_le_u64
        omega
      cases hx : (items ps)[i.val] with
      | none =>
        step*
        refine ⟨by omega, ?_, by omega⟩
        rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [promiseHit]; omega
      | some p =>
        by_cases e : p.ballot = b
        · simp only [e, if_true]
          step*
          refine ⟨by omega, ?_, by omega⟩
          rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [promiseHit, e]; omega
        · simp only [e, if_false]
          step*
          refine ⟨by omega, ?_, by omega⟩
          rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [promiseHit, e]; omega
    · have hge : ¬ i < Slice.len (ps : Slice _) := by rw [UScalar.lt_equiv]; simpa [items] using hlt
      simp only [vec_len_eq, bind_tc_ok, hge, if_false]
      have : i.val = (items ps).length := by omega
      simp [WP.spec_ok, hc, this]
  · simp [countPromisesS]

theorem count_votes_spec (vs : RVec (Opt Vote)) (v : Vote) :
    count_votes vs v ⦃ c => c.val = countVotesS (items vs) v ⦄ := by
  unfold count_votes count_votes_loop
  have hlen := items_length_le vs
  apply loop.spec_decr_nat (fun (x : Vote × Usize × U64) => (items vs).length - x.2.1.val)
    (fun x => x.1 = v ∧ x.2.1.val ≤ (items vs).length ∧
      x.2.2.val = countVotesS ((items vs).take x.2.1.val) v)
  · rintro ⟨v', i, c⟩ ⟨rfl, hi, hc⟩
    simp only at hi hc
    unfold count_votes_loop.body
    have hcle : c.val ≤ i.val := by
      rw [hc]; exact le_trans List.countP_le_length (by simp)
    by_cases hlt : i.val < (items vs).length
    · have hlt' : i < Slice.len (vs : Slice _) := by rw [UScalar.lt_equiv]; simpa [items] using hlt
      have take_succ : countVotesS ((items vs).take (i.val + 1)) v' =
          countVotesS ((items vs).take i.val) v' + (if voteHit v' (items vs)[i.val] then 1 else 0) := by
        rw [List.take_add_one, List.getElem?_eq_getElem hlt]
        simp only [countVotesS, List.countP_append, Option.toList_some, List.countP_singleton]
        cases voteHit v' (items vs)[i.val] <;> rfl
      simp only [vec_len_eq, bind_tc_ok, hlt', if_true, index_eq vs i hlt]
      have h64 : c.val + 1 ≤ U64.max := by
        have := usize_le_u64
        omega
      cases hx : (items vs)[i.val] with
      | none =>
        step*
        refine ⟨by omega, ?_, by omega⟩
        rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [voteHit]; omega
      | some x =>
        by_cases e1 : x.ballot = v'.ballot <;> by_cases e2 : x.value = v'.value <;>
          simp only [e1, e2, if_true, if_false] <;> step* <;>
          refine ⟨by omega, ?_, by omega⟩ <;>
          rw [show i2.val = i.val + 1 by omega, take_succ, hx] <;> simp [voteHit, e1, e2] <;> omega
    · have hge : ¬ i < Slice.len (vs : Slice _) := by rw [UScalar.lt_equiv]; simpa [items] using hlt
      simp only [vec_len_eq, bind_tc_ok, hge, if_false]
      have : i.val = (items vs).length := by omega
      simp [WP.spec_ok, hc, this]
  · simp [countVotesS]

theorem highest_spec (ps : RVec (Opt Promise)) (b : U64) :
    highest ps b ⦃ r => r = highestS (items ps) b ⦄ := by
  unfold highest highest_loop
  have hlen := items_length_le ps
  apply loop.spec_decr_nat (fun (x : Usize × Opt Vote) => (items ps).length - x.1.val)
    (fun x => x.1.val ≤ (items ps).length ∧
      x.2 = ((items ps).take x.1.val).foldl (bestStep b) .None)
  · rintro ⟨i, best⟩ ⟨hi, hc⟩
    simp only at hi hc
    unfold highest_loop.body
    by_cases hlt : i.val < (items ps).length
    · have hlt' : i < Slice.len (ps : Slice _) := by rw [UScalar.lt_equiv]; simpa [items] using hlt
      have take_succ : ((items ps).take (i.val + 1)).foldl (bestStep b) .None =
          bestStep b best (items ps)[i.val] := by
        rw [List.take_add_one, List.getElem?_eq_getElem hlt, List.foldl_append, ← hc]; rfl
      simp only [vec_len_eq, bind_tc_ok, hlt', if_true, index_eq ps i hlt]
      cases hx : (items ps)[i.val] with
      | none =>
        step*
        refine ⟨by omega, ?_, by omega⟩
        rw [show i2.val = i.val + 1 by omega, take_succ, hx]; rfl
      | some p =>
        by_cases e : p.ballot = b
        · cases ha : p.accepted with
          | none =>
            simp only [e, ha, if_true]
            step*
            refine ⟨by omega, ?_, by omega⟩
            rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [bestStep, e, ha]
          | some v =>
            cases hb : best with
            | none =>
              simp only [e, ha, if_true]
              step*
              refine ⟨by omega, ?_, by omega⟩
              rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [bestStep, e, ha, hb]
            | some m =>
              by_cases lt : m.ballot < v.ballot
              · have lt' : v.ballot > m.ballot := lt
                simp only [e, ha, if_true, lt', ↓reduceIte]
                step*
                refine ⟨by omega, ?_, by omega⟩
                rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [bestStep, e, ha, hb, lt]
              · have lt' : ¬ v.ballot > m.ballot := lt
                simp only [e, ha, if_true, lt', ↓reduceIte]
                step*
                refine ⟨by omega, ?_, by omega⟩
                rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [bestStep, e, ha, hb, lt]
        · simp only [e, if_false]
          step*
          refine ⟨by omega, ?_, by omega⟩
          rw [show i2.val = i.val + 1 by omega, take_succ, hx]; simp [bestStep, e]
    · have hge : ¬ i < Slice.len (ps : Slice _) := by rw [UScalar.lt_equiv]; simpa [items] using hlt
      simp only [vec_len_eq, bind_tc_ok, hge, if_false]
      have : i.val = (items ps).length := by omega
      simp [WP.spec_ok, hc, this, highestS]
  · simp

theorem push_eq {α : Type} (s : RVec α) (x : α) (h : (items s).length + 1 ≤ Usize.max) :
    CoreModels.alloc.vec.Vec.push s x = ok (show RVec α from (⟨items s ++ [x], by simpa using h⟩ : Slice α)) := by
  simp only [items] at h
  simp [CoreModels.alloc.vec.Vec.push, rust_primitives.sequence.seq_push, items, h]


theorem new_spec (n : U8) :
    Node.new_loop n (⟨[], by simp⟩ : Slice _) (⟨[], by simp⟩ : Slice _) 0#u8 ⦃ r =>
      items r.1 = List.replicate n.val .None ∧ items r.2 = List.replicate n.val .None ⦄ := by
  unfold Node.new_loop
  have hn := u8_le_usize n
  apply loop.spec_decr_nat (fun (x : RVec (Opt Promise) × RVec (Opt Vote) × U8) => n.val - x.2.2.val)
    (fun x => x.2.2.val ≤ n.val ∧ items x.1 = List.replicate x.2.2.val .None ∧
      items x.2.1 = List.replicate x.2.2.val .None)
  · rintro ⟨ps, vs, i⟩ ⟨hi, hp, hv⟩
    simp only at hi hp hv
    unfold Node.new_loop.body
    by_cases hlt : i < n
    · have hlt2 : i.val < n.val := hlt
      have h1 : (items ps).length + 1 ≤ Usize.max := by rw [hp]; simp; omega
      have h2 : (items vs).length + 1 ≤ Usize.max := by rw [hv]; simp; omega
      simp only [hlt, if_true, push_eq ps _ h1, push_eq vs _ h2, bind_tc_ok]
      step*
      refine ⟨by omega, ?_, ?_, by omega⟩ <;>
        simp only [items, show i1.val = i.val + 1 by omega, List.replicate_succ'] <;>
        simp only [items] at hp hv <;> simp [hp, hv]
    · simp only [hlt, if_false]
      have : i.val = n.val := by have : ¬ i.val < n.val := hlt; omega
      simp [WP.spec_ok, hp, hv, this]
  · simp [items]
/-! ## Extracted functions equal the pure specification -/

theorem new_eq (id n : U8) : Node.new id n = ok (initS id n) := by
  obtain ⟨r, hr, h1, h2⟩ := (WP.spec_equiv_exists _ _).mp (new_spec n)
  unfold Node.new
  simp only [CoreModels.alloc.vec.Vec.new, rust_primitives.sequence.seq_empty, bind_tc_ok]
  have e1 : Slice.new (Opt Promise) = ⟨[], by simp⟩ := rfl
  have e2 : Slice.new (Opt Vote) = ⟨[], by simp⟩ := rfl
  rw [e1, e2, hr]
  rcases r with ⟨p, v⟩
  have hp : p = replicate n.val .None (u8_le_usize n) := Subtype.ext h1
  have hv : v = replicate n.val .None (u8_le_usize n) := Subtype.ext h2
  subst hp hv
  rfl

theorem count_promises_eq (ps : RVec (Opt Promise)) (b : U64) :
    ∃ c : U64, count_promises ps b = ok c ∧ c.val = countPromisesS (items ps) b :=
  (WP.spec_equiv_exists _ _).mp (count_promises_spec ps b)

theorem highest_eq (ps : RVec (Opt Promise)) (b : U64) :
    highest ps b = ok (highestS (items ps) b) := by
  obtain ⟨r, hr, rfl⟩ := (WP.spec_equiv_exists _ _).mp (highest_spec ps b)
  exact hr

theorem count_votes_eq (vs : RVec (Opt Vote)) (v : Vote) :
    ∃ c : U64, count_votes vs v = ok c ∧ c.val = countVotesS (items vs) v :=
  (WP.spec_equiv_exists _ _).mp (count_votes_spec vs v)

noncomputable def cvS (vs : RVec (Opt Vote)) (v : Vote) : U64 := Classical.choose (count_votes_eq vs v)

theorem count_votes_rw (vs : RVec (Opt Vote)) (v : Vote) : count_votes vs v = ok (cvS vs v) :=
  (Classical.choose_spec (count_votes_eq vs v)).1

theorem cvS_val (vs : RVec (Opt Vote)) (v : Vote) : (cvS vs v).val = countVotesS (items vs) v :=
  (Classical.choose_spec (count_votes_eq vs v)).2

noncomputable def cpS (ps : RVec (Opt Promise)) (b : U64) : U64 :=
  Classical.choose (count_promises_eq ps b)

theorem count_promises_rw (ps : RVec (Opt Promise)) (b : U64) :
    count_promises ps b = ok (cpS ps b) :=
  (Classical.choose_spec (count_promises_eq ps b)).1

theorem cpS_val (ps : RVec (Opt Promise)) (b : U64) : (cpS ps b).val = countPromisesS (items ps) b :=
  (Classical.choose_spec (count_promises_eq ps b)).2

theorem higher_eq (a b : U64) : higher a b = ok (higherS a b) := by
  unfold higher higherS; split <;> rfl

theorem nextS_val' (floor : U64) (id n : U8) (h : floor.val < LIMIT) (hn : 0 < n.val) :
    (nextS floor id n).val = (floor.val / n.val + 1) * n.val + id.val := by
  have hid : id.val < 256 := by scalar_tac
  have hn' : n.val < 256 := by scalar_tac
  have hb : (floor.val / n.val + 1) * n.val ≤ floor.val + n.val := by
    rw [Nat.add_mul, Nat.one_mul]; have := Nat.div_mul_le_self floor.val n.val; omega
  unfold nextS
  simp only [UScalar.val, BitVec.toNat_ofNat] at *
  apply Nat.mod_eq_of_lt
  unfold LIMIT at h; omega

theorem next_ballot_eq (floor : U64) (id n : U8) (h : floor.val < LIMIT) (hn : 0 < n.val) :
    next_ballot floor id n = ok (nextS floor id n) := by
  have hid : id.val < 256 := by scalar_tac
  have hn' : n.val < 256 := by scalar_tac
  have hb : (floor.val / n.val + 1) * n.val ≤ floor.val + n.val := by
    rw [Nat.add_mul, Nat.one_mul]; have := Nat.div_mul_le_self floor.val n.val; omega
  have spec : next_ballot floor id n ⦃ b => b.val = (floor.val / n.val + 1) * n.val + id.val ⦄ := by
    unfold next_ballot; unfold LIMIT at h; step*
  obtain ⟨b, hb, hv⟩ := (WP.spec_equiv_exists _ _).mp spec
  rw [hb]; congr 1
  apply UScalar.eq_of_val_eq; rw [hv, nextS_val' floor id n h hn]

theorem majority_eq (c : U64) (n : U8) : majority c n = ok (decide (Majority c.val n)) := by
  have spec : majority c n ⦃ r => r = decide (Majority c.val n) ⦄ := by
    unfold majority Majority; step*
  obtain ⟨r, hr, rfl⟩ := (WP.spec_equiv_exists _ _).mp spec
  exact hr

theorem start_eq (n : Node) : Node.start n = ok (startS n) := by
  unfold Node.start startS
  by_cases hn : n.n = 0#u8
  · simp [hn]
  have hn0 : 0 < n.n.val := by
    have : n.n.val ≠ 0 := fun h => hn (UScalar.eq_of_val_eq (by simpa using h))
    omega
  simp only [hn, if_false, higher_eq, bind_tc_ok, BALLOT_LIMIT]
  generalize higherS (higherS n.max_seen n.promised) n.ballot = f
  by_cases h : LIMIT ≤ f.val
  · have : (4611686018427387904#u64 : U64) ≤ f := by
      rw [UScalar.le_equiv]; simpa [LIMIT] using h
    simp [this, h]
  · have : ¬ (4611686018427387904#u64 : U64) ≤ f := by
      rw [UScalar.le_equiv]; simpa [LIMIT] using h
    simp only [ge_iff_le, this, if_false, h]
    rw [next_ballot_eq _ _ _ (by omega) hn0]
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
  unfold Node.on_promise onPromiseS
  by_cases h1 : b = n.ballot
  · subst h1
    by_cases h2 : n.ballot = 0#u64
    · simp [h2]
    · cases hp : n.proposal
      · simp only [h2, hp, bne_self_eq_false, Bool.false_eq_true, if_false, ne_eq, not_true_eq_false,
          lift, vec_len_eq, bind_tc_ok]
        have hc : (UScalar.cast .Usize src).val = src.val := by simp
        by_cases hl : (items n.promises).length ≤ src.val
        · have : UScalar.cast .Usize src ≥ Slice.len (n.promises : Slice _) := by
            rw [ge_iff_le, UScalar.le_equiv, hc, Slice.len_val]; exact hl
          simp [this, hl]
        · have hlt : (UScalar.cast .Usize src).val < (items n.promises).length := by omega
          have : ¬ UScalar.cast .Usize src ≥ Slice.len (n.promises : Slice _) := by
            rw [ge_iff_le, UScalar.le_equiv, hc, Slice.len_val]; exact hl
          simp only [this, hl, if_false, index_mut_eq _ _ hlt, bind_tc_ok, hc]
          cases hv : n.value <;>
            simp [count_promises_rw, cpS_val, majority_eq, highest_eq, hv] <;> (repeat' split) <;> first | rfl | simp_all
      · simp [h2, hp]
  · have : (b != n.ballot) = true := by simpa using h1
    simp [this, h1]

theorem on_accepted_eq (n : Node) (src : U8) (v : Vote) :
    Node.on_accepted n src v = ok (onAcceptedS n src v) := by
  unfold Node.on_accepted onAcceptedS
  simp only [lift, vec_len_eq, bind_tc_ok]
  have hc : (UScalar.cast .Usize src).val = src.val := by simp
  by_cases hl : (items n.votes).length ≤ src.val
  · have : UScalar.cast .Usize src ≥ Slice.len (n.votes : Slice _) := by
      rw [ge_iff_le, UScalar.le_equiv, hc, Slice.len_val]; exact hl
    simp [this, hl]
  · have hlt : (UScalar.cast .Usize src).val < (items n.votes).length := by omega
    have : ¬ UScalar.cast .Usize src ≥ Slice.len (n.votes : Slice _) := by
      rw [ge_iff_le, UScalar.le_equiv, hc, Slice.len_val]; exact hl
    have hslot : slot n.votes src.val = (items n.votes)[src.val] := by
      simp [slot, List.getElem?_eq_getElem (hc ▸ hlt)]
    simp only [this, hl, if_false, index_eq _ _ hlt, index_mut_eq _ _ hlt, bind_tc_ok, hslot, hc]
    cases ho : (items n.votes)[src.val] <;> cases hd : n.decided <;>
      simp [newer, count_votes_rw, cvS_val, majority_eq] <;> (repeat' split) <;> first | rfl | simp_all

theorem deliver_eq (n : Node) (src : U8) (msg : Msg) :
    Node.deliver n src msg = ok (deliverS n src msg) := by
  unfold Node.deliver deliverS
  by_cases h : n.n.val ≤ src.val
  · have : src ≥ n.n := by simp [UScalar.le_equiv]; exact h
    simp [this, h]
  · have : ¬ src ≥ n.n := by simp [UScalar.le_equiv]; omega
    simp only [this, h, if_false]
    cases msg with
    | Request v => cases n.value <;> rfl
    | Prepare b => exact on_prepare_eq n src b
    | Promise b acc => exact on_promise_eq n src b acc
    | Accept v => exact on_accept_eq n src v
    | Accepted v => exact on_accepted_eq n src v
    | Nack _ p => simp only []; split <;> rfl

/-- The extracted transition function is total: it returns `ok` for every
    replica state and every input, including malformed sender identifiers,
    vectors of the wrong length, an empty cluster, and exhausted ballots. -/
theorem handle_eq (n : Node) (input : Input) :
    Node.handle n input = ok (handleS n input) := by
  cases input with
  | Submit v => rfl
  | Deliver src msg => exact deliver_eq n src msg
  | Tick => exact tick_eq n

theorem no_panic : ∀ (n : Node) (input : Input), ∃ r, Node.handle n input = ok r :=
  fun n input => ⟨_, handle_eq n input⟩

/-! ## Facts about the pure list functions -/

theorem nextS_val (floor : U64) (id n : U8) (h : floor.val < LIMIT) (hn : 0 < n.val) :
    (nextS floor id n).val = (floor.val / n.val + 1) * n.val + id.val := by
  exact nextS_val' floor id n h hn

theorem items_setAt {α : Type} (s : RVec α) (i : Nat) (x : α) :
    items (setAt s i x) = (items s).set i x := by
  rfl

theorem items_replicate {α : Type} (k : Nat) (x : α) (h : k ≤ Usize.max) :
    items (replicate k x h) = List.replicate k x := by
  rfl

theorem slot_setAt {α : Type} (s : RVec (Opt α)) (i j : Nat) (x : Opt α)
    (hi : i < (items s).length) :
    slot (setAt s i x) j = if j = i then x else slot s j := by
  unfold slot
  rw [items_setAt', List.getElem?_set]
  by_cases h : j = i
  · subst h; simp [hi]
  · simp [h, Ne.symm h]

theorem bestStep_cases (b : U64) (acc : Opt Vote) (x : Opt Promise) :
    (bestStep b acc x = acc ∨ ∃ v, x = .Some ⟨b, .Some v⟩ ∧ bestStep b acc x = .Some v) ∧
    (∀ m0, acc = .Some m0 → ∃ m1, bestStep b acc x = .Some m1 ∧ m0.ballot.val ≤ m1.ballot.val) ∧
    (∀ p m', x = .Some p → p.ballot = b → p.accepted = .Some m' →
      ∃ m1, bestStep b acc x = .Some m1 ∧ m'.ballot.val ≤ m1.ballot.val) := by
  rcases x with _ | ⟨pb, pa⟩
  · refine ⟨Or.inl rfl, fun m0 h0 => ⟨m0, h0, le_refl _⟩, ?_⟩
    intro p m' hx; simp at hx
  · by_cases e : pb = b
    · subst e
      rcases pa with _ | v
      · refine ⟨Or.inl (by simp [bestStep]), fun m0 h0 => ⟨m0, by simp [bestStep, h0], le_refl _⟩, ?_⟩
        intro p m' hx hb ha; cases hx; simp at ha
      · rcases acc with _ | m
        · refine ⟨Or.inr ⟨v, rfl, by simp [bestStep]⟩, fun m0 h0 => by simp at h0, ?_⟩
          intro p m' hx hb ha; cases hx; simp at ha; subst ha; exact ⟨_, by simp [bestStep], le_refl _⟩
        · by_cases lt : m.ballot < v.ballot
          · have lt' : m.ballot.val < v.ballot.val := lt
            refine ⟨Or.inr ⟨v, rfl, by simp [bestStep, lt]⟩, fun m0 h0 => ?_, ?_⟩
            · simp at h0; subst h0; exact ⟨v, by simp [bestStep, lt], by omega⟩
            · intro p m' hx hb ha; cases hx; simp at ha; subst ha
              exact ⟨_, by simp [bestStep, lt], le_refl _⟩
          · have lt' : ¬ m.ballot.val < v.ballot.val := lt
            refine ⟨Or.inl (by simp [bestStep, lt]), fun m0 h0 => ?_, ?_⟩
            · simp at h0; subst h0; exact ⟨_, by simp [bestStep, lt], le_refl _⟩
            · intro p m' hx hb ha; cases hx; simp at ha; subst ha
              exact ⟨m, by simp [bestStep, lt], by omega⟩
    · refine ⟨Or.inl (by simp [bestStep, e]), fun m0 h0 => ⟨m0, by simp [bestStep, e, h0], le_refl _⟩, ?_⟩
      intro p m' hx hb; cases hx; exact absurd hb e

theorem highestS_none_gen (ps : List (Opt Promise)) (b : U64) (acc : Opt Vote)
    (h : ps.foldl (bestStep b) acc = .None) :
    acc = .None ∧ ∀ (i : Nat) (p : Promise), ps[i]? = some (core.option.Option.Some p) →
      p.ballot = b → p.accepted = core.option.Option.None := by
  induction ps generalizing acc with
  | nil => simp_all
  | cons x xs ih =>
    rw [List.foldl_cons] at h
    obtain ⟨hacc, hrest⟩ := ih _ h
    obtain ⟨c1, c2, c3⟩ := bestStep_cases b acc x
    refine ⟨?_, ?_⟩
    · rcases acc with _ | m0
      · rfl
      · obtain ⟨m1, hm1, -⟩ := c2 m0 rfl
        rw [hm1] at hacc; cases hacc
    · intro i p hi hb
      cases i with
      | zero =>
        simp at hi
        cases hpa : p.accepted with
        | none => rfl
        | some m' =>
          obtain ⟨m1, hm1, -⟩ := c3 p m' hi hb hpa
          rw [hm1] at hacc; cases hacc
      | succ i => exact hrest i p (by simpa using hi) hb

theorem highestS_some_gen (ps : List (Opt Promise)) (b : U64) (acc : Opt Vote) (m : Vote)
    (h : ps.foldl (bestStep b) acc = .Some m) :
    (acc = .Some m ∨ ∃ i : Nat, ps[i]? = some (core.option.Option.Some
        ({ ballot := b, accepted := core.option.Option.Some m } : Promise))) ∧
    (∀ m0, acc = .Some m0 → m0.ballot.val ≤ m.ballot.val) ∧
    ∀ (i : Nat) (p : Promise) (m' : Vote), ps[i]? = some (core.option.Option.Some p) → p.ballot = b →
      p.accepted = core.option.Option.Some m' → m'.ballot.val ≤ m.ballot.val := by
  induction ps generalizing acc with
  | nil =>
    simp only [List.foldl_nil] at h
    subst h
    refine ⟨Or.inl rfl, ?_, ?_⟩
    · intro m0 h0; cases h0; exact le_refl _
    · intro i p m' hi; simp at hi
  | cons x xs ih =>
    rw [List.foldl_cons] at h
    obtain ⟨h1, h2, h3⟩ := ih _ h
    obtain ⟨c1, c2, c3⟩ := bestStep_cases b acc x
    refine ⟨?_, ?_, ?_⟩
    · rcases h1 with h1 | ⟨i, hi⟩
      · rcases c1 with c1 | ⟨v, hx, hv⟩
        · exact Or.inl (c1 ▸ h1)
        · rw [hv] at h1; cases h1
          exact Or.inr ⟨0, by simp [hx]⟩
      · exact Or.inr ⟨i + 1, by simpa using hi⟩
    · intro m0 h0
      obtain ⟨m1, hm1, hle⟩ := c2 m0 h0
      have := h2 m1 hm1; omega
    · intro i p m' hi hb ha
      cases i with
      | zero =>
        simp at hi
        obtain ⟨m1, hm1, hle⟩ := c3 p m' hi hb ha
        have := h2 m1 hm1; omega
      | succ i => exact h3 i p m' (by simpa using hi) hb ha

/-- Counting a predicate over a list of length `N` is the cardinality of the
    corresponding set of indices. -/
theorem countP_eq_card {α : Type} (l : List α) (p : α → Bool) (N : Nat) (hN : l.length = N) :
    l.countP p = (Finset.univ.filter (fun i : Fin N => p (l[i.val]'(by omega)) = true)).card := by
  induction l generalizing N with
  | nil => subst hN; simp
  | cons a l ih =>
    cases N with
    | zero => simp at hN
    | succ k =>
      rw [Fin.card_filter_univ_succ', List.countP_cons]
      simp only [List.getElem_cons_zero, Fin.val_succ, List.getElem_cons_succ, Fin.val_zero]
      rw [ih k (by simpa using hN)]
      exact Nat.add_comm _ _

/-- The `highest` loop reports no vote only if no promise for `b` carries one. -/
theorem highestS_none (ps : List (Opt Promise)) (b : U64) (h : highestS ps b = .None) :
    ∀ (i : Nat) (p : Promise), ps[i]? = some (core.option.Option.Some p) → p.ballot = b → p.accepted = core.option.Option.None := by
  exact (highestS_none_gen ps b .None h).2

/-- Otherwise it reports a vote carried by some promise for `b`, of maximal ballot. -/
theorem highestS_some (ps : List (Opt Promise)) (b : U64) (m : Vote)
    (h : highestS ps b = .Some m) :
    (∃ i : Nat, ps[i]? = some (core.option.Option.Some ({ ballot := b, accepted := core.option.Option.Some m } : Promise))) ∧
    ∀ (i : Nat) (p : Promise) (m' : Vote), ps[i]? = some (core.option.Option.Some p) → p.ballot = b →
      p.accepted = core.option.Option.Some m' → m'.ballot.val ≤ m.ballot.val := by
  obtain ⟨h1, -, h3⟩ := highestS_some_gen ps b .None m h
  exact ⟨h1.resolve_left (by simp), h3⟩

#print axioms handle_eq
end PaxosNode
