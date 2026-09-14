import Semantics

/- Typed source execution. The frontend supplies variable projections and updates;
   operations below give Python's supported builtins their meaning. A fault keeps
   the frame at the point of failure, including earlier writes. -/
namespace RMVerify.TypedSource

inductive Fault where
  | missingKey
  | missingValue
  deriving Repr, DecidableEq

inductive Expr (Frame : Type) : Type → Type 1 where
  | value (v : α) : Expr Frame α
  | read (get : Frame → α) : Expr Frame α
  | call₁ (op : α → Except Fault β) (arg : Expr Frame α) : Expr Frame β
  | call₂ (op : α → β → Except Fault γ) (a : Expr Frame α) (b : Expr Frame β) : Expr Frame γ
  | cond (test : Expr Frame Bool) (yes no : Expr Frame α) : Expr Frame α
  | all (items : Expr Frame (List α)) (body : α → Expr Frame Bool) : Expr Frame Bool
  | any (items : Expr Frame (List α)) (body : α → Expr Frame Bool) : Expr Frame Bool

def allM (p : α → Except Fault Bool) : List α → Except Fault Bool
  | [] => .ok true
  | a :: rest => do if ← p a then allM p rest else return false

def anyM (p : α → Except Fault Bool) : List α → Except Fault Bool
  | [] => .ok false
  | a :: rest => do if ← p a then return true else anyM p rest


@[simp] theorem ok_ite (p : Prop) [Decidable p] (a b : α) :
    (if p then Except.ok a else Except.ok b : Except Fault α) = .ok (if p then a else b) := by
  split <;> rfl

@[simp] theorem allM_nil (p : α → Except Fault Bool) : allM p [] = .ok true := rfl
@[simp] theorem anyM_nil (p : α → Except Fault Bool) : anyM p [] = .ok false := rfl

def Expr.eval (frame : Frame) : Expr Frame α → Except Fault α
  | .value v => .ok v
  | .read get => .ok (get frame)
  | .call₁ op a => do op (← a.eval frame)
  | .call₂ op a b => do op (← a.eval frame) (← b.eval frame)
  | .cond c a b => do if ← c.eval frame then a.eval frame else b.eval frame
  | .all items body => do allM (fun a => (body a).eval frame) (← items.eval frame)
  | .any items body => do anyM (fun a => (body a).eval frame) (← items.eval frame)

inductive Outcome (Frame Result : Type) where
  | next (frame : Frame)
  | returned (frame : Frame) (value : Result)
  | fault (frame : Frame) (reason : Fault)
  deriving Repr, DecidableEq

@[simp] def Outcome.frame : Outcome Frame Result → Frame
  | .next frame => frame
  | .returned frame _ => frame
  | .fault frame _ => frame

@[simp] def Outcome.fault? : Outcome Frame Result → Option Fault
  | .fault _ reason => some reason
  | _ => none

@[simp] theorem Outcome.frame_ite (p : Prop) [Decidable p] (a b : Outcome F R) :
    (if p then a else b).frame = if p then a.frame else b.frame := by split <;> rfl
@[simp] theorem Outcome.fault_ite (p : Prop) [Decidable p] (a b : Outcome F R) :
    (if p then a else b).fault? = if p then a.fault? else b.fault? := by split <;> rfl

def Outcome.result? : Outcome Frame Result → Option Result
  | .returned _ value => some value
  | _ => none

def Outcome.toExcept (outcome : Outcome Frame Result) (fallback : Result) : Except Fault Result :=
  match outcome with
  | .next _ => .ok fallback
  | .returned _ value => .ok value
  | .fault _ reason => .error reason

def Outcome.bind (outcome : Outcome Frame Result) (next : Frame → Outcome Frame Result) :=
  match outcome with
  | .next frame => next frame
  | .returned frame result => .returned frame result
  | .fault frame reason => .fault frame reason

@[simp] theorem Outcome.bind_ite (p : Prop) [Decidable p] (a b : Outcome F R)
    (next : F → Outcome F R) :
    (if p then a else b).bind next = if p then a.bind next else b.bind next := by
  split <;> rfl

def Outcome.mapFrame (clear : Frame → Frame) : Outcome Frame Result → Outcome Frame Result
  | .next f => .next (clear f)
  | .returned f v => .returned (clear f) v
  | .fault f e => .fault (clear f) e

inductive Stmt (Frame Result : Type) : Type 1 where
  | skip
  | assign (put : Frame → α → Frame) (value : Expr Frame α)
  | seq (first rest : Stmt Frame Result)
  | branch (test : Expr Frame Bool) (yes no : Stmt Frame Result)
  | ret (value : Expr Frame Result)
  | each (items : Expr Frame (List α)) (body : α → Stmt Frame Result)
  | scope (clear : Frame → Frame) (body : Stmt Frame Result)
  | invoke (arguments : Expr Frame Callee) (callee : Callee → Outcome Callee Value)
      (merge : Frame → Callee → Frame) (save : Frame → Value → Frame) (fallback : Value)

def eachM (body : α → Frame → Outcome Frame Result) : List α → Frame → Outcome Frame Result
  | [], frame => .next frame
  | a :: rest, frame => (body a frame).bind (eachM body rest)

@[simp] theorem eachM_pure (step : α → Frame → Frame) (xs : List α) (f : Frame) :
    (eachM (fun a f => .next (step a f)) xs f : Outcome Frame Result) =
      .next (xs.foldl (fun f a => step a f) f) := by
  induction xs generalizing f with
  | nil => rfl
  | cons a xs ih => simpa [eachM, Outcome.bind, List.foldl] using ih (step a f)

def Stmt.exec (frame : Frame) : Stmt Frame Result → Outcome Frame Result
  | .skip => .next frame
  | .assign put value => match value.eval frame with
    | .ok v => .next (put frame v)
    | .error reason => .fault frame reason
  | .seq a b => (a.exec frame).bind (fun frame' => b.exec frame')
  | .branch test yes no => match test.eval frame with
    | .ok b => if b then yes.exec frame else no.exec frame
    | .error reason => .fault frame reason
  | .ret value => match value.eval frame with
    | .ok v => .returned frame v
    | .error reason => .fault frame reason
  | .invoke arguments callee merge save fallback => match arguments.eval frame with
    | .error reason => .fault frame reason
    | .ok args => match callee args with
      | .next updated => .next (save (merge frame updated) fallback)
      | .returned updated result => .next (save (merge frame updated) result)
      | .fault updated reason => .fault (merge frame updated) reason
  | .scope clear body => (body.exec frame).mapFrame clear
  | .each items body => match items.eval frame with
    | .ok xs => eachM (fun a frame' => (body a).exec frame') xs frame
    | .error reason => .fault frame reason

/-- Ordered association lists retain Python dictionary insertion order.
    Overwriting a key changes its value in place. -/
def dictSet [DecidableEq K] (xs : List (K × V)) (key : K) (value : V) : List (K × V) :=
  match xs with
  | [] => [(key, value)]
  | (k, v) :: rest => if k = key then (k, value) :: rest else (k, v) :: dictSet rest key value

def dictGet [DecidableEq K] (xs : List (K × V)) (key : K) : Option V :=
  match xs with
  | [] => none
  | (k, v) :: rest => if k = key then some v else dictGet rest key

def optionGet (value : Option α) : Except Fault α :=
  match value with
  | none => .error .missingValue
  | some v => .ok v

def dictLookup [DecidableEq K] (xs : List (K × V)) (key : K) : Except Fault V :=
  match dictGet xs key with
  | none => .error .missingKey
  | some v => .ok v

def setAdd [DecidableEq K] (xs : List K) (key : K) : List K :=
  if key ∈ xs then xs else xs ++ [key]

def setDiscard [DecidableEq K] (xs : List K) (key : K) : List K :=
  xs.filter (fun k => decide (k ≠ key))

@[simp] theorem dictGet_set_same [DecidableEq K] (xs : List (K × V)) (key : K) (value : V) :
    dictGet (dictSet xs key value) key = some value := by
  induction xs with
  | nil => simp [dictSet, dictGet]
  | cons x xs ih => rcases x with ⟨k, v⟩; by_cases h : k = key <;> simp [dictSet, dictGet, h, ih]

@[simp] theorem dictSet_keys [DecidableEq K] (xs : List (K × V)) (key : K) (value : V) :
    (dictSet xs key value).map Prod.fst = setAdd (xs.map Prod.fst) key := by
  induction xs with
  | nil => simp [dictSet, setAdd]
  | cons x xs ih =>
    rcases x with ⟨k, v⟩
    by_cases h : k = key
    · subst k; simp [dictSet, setAdd]
    · by_cases hm : key ∈ xs.map Prod.fst <;> simp_all [dictSet, setAdd, eq_comm]

@[simp] theorem setAdd_mem [DecidableEq K] (xs : List K) (key x : K) :
    x ∈ setAdd xs key ↔ x ∈ xs ∨ x = key := by
  by_cases h : key ∈ xs <;> simp_all [setAdd]

@[simp] theorem setDiscard_mem [DecidableEq K] (xs : List K) (key x : K) :
    x ∈ setDiscard xs key ↔ x ∈ xs ∧ x ≠ key := by simp [setDiscard]

@[simp] theorem setAdd_duplicate [DecidableEq K] (xs : List K) (key : K) (h : key ∈ xs) :
    setAdd xs key = xs := by simp [setAdd, h]

@[simp] theorem setAdd_length [DecidableEq K] (xs : List K) (key : K) :
    (setAdd xs key).length = if key ∈ xs then xs.length else xs.length + 1 := by
  by_cases h : key ∈ xs <;> simp [setAdd, h]

@[simp] theorem dictSet_length [DecidableEq K] (xs : List (K × V)) (key : K) (value : V) :
    (dictSet xs key value).length = if key ∈ xs.map Prod.fst then xs.length else xs.length + 1 := by
  induction xs with
  | nil => simp [dictSet]
  | cons pair xs ih =>
    rcases pair with ⟨k,v⟩
    by_cases h : k = key
    · subst k; simp [dictSet]
    · by_cases mem : key ∈ xs.map Prod.fst <;> simp_all [dictSet, List.mem_cons, Ne.symm h]

@[simp] theorem dictSet_length_of_mem [DecidableEq K] (xs : List (K × V)) (key : K) (value : V)
    (h : key ∈ xs.map Prod.fst) : (dictSet xs key value).length = xs.length := by
  induction xs with
  | nil => simp at h
  | cons x xs ih =>
    rcases x with ⟨k, v⟩
    by_cases hk : k = key
    · simp [dictSet, hk]
    · have hrest : key ∈ xs.map Prod.fst := by
        simpa [List.mem_cons, Ne.symm hk] using h
      simp [dictSet, hk, ih hrest]

@[simp] theorem allM_pure (p : α → Bool) (xs : List α) :
    allM (fun x => .ok (p x)) xs = .ok (xs.all p) := by
  induction xs with
  | nil => rfl
  | cons x xs ih => cases h : p x <;> simp [allM, h, ih, Bind.bind, Pure.pure, Except.bind, Except.pure]

@[simp] theorem anyM_pure (p : α → Bool) (xs : List α) :
    anyM (fun x => .ok (p x)) xs = .ok (xs.any p) := by
  induction xs with
  | nil => rfl
  | cons x xs ih => cases h : p x <;> simp [anyM, h, ih, Bind.bind, Pure.pure, Except.bind, Except.pure]

theorem allM_order_independent (p : α → Bool) (xs ys : List α) (h : xs.Perm ys) :
    allM (fun x => .ok (p x)) xs = allM (fun x => .ok (p x)) ys := by
  simp only [allM_pure, h.all_eq]

theorem anyM_order_independent (p : α → Bool) (xs ys : List α) (h : xs.Perm ys) :
    anyM (fun x => .ok (p x)) xs = anyM (fun x => .ok (p x)) ys := by
  simp only [anyM_pure, h.any_eq]


theorem allM_total_order_independent (p : α → Except Fault Bool) (xs ys : List α)
    (perm : xs.Perm ys) (total : ∀ x, ∃ b, p x = .ok b) : allM p xs = allM p ys := by
  let q := fun x => (p x).toOption.getD false
  have hp : p = fun x => .ok (q x) := by
    funext x
    obtain ⟨b, hb⟩ := total x
    simp [q, hb, Except.toOption, Option.getD]
  rw [hp]
  exact allM_order_independent q xs ys perm

theorem anyM_total_order_independent (p : α → Except Fault Bool) (xs ys : List α)
    (perm : xs.Perm ys) (total : ∀ x, ∃ b, p x = .ok b) : anyM p xs = anyM p ys := by
  let q := fun x => (p x).toOption.getD false
  have hp : p = fun x => .ok (q x) := by
    funext x
    obtain ⟨b, hb⟩ := total x
    simp [q, hb, Except.toOption, Option.getD]
  rw [hp]
  exact anyM_order_independent q xs ys perm

@[simp] theorem bind_assoc (x : Outcome F R) (f g : F → Outcome F R) :
    (x.bind f).bind g = x.bind (fun s => (f s).bind g) := by cases x <;> rfl

theorem eachM_perm (body : α → F → Outcome F R)
    (commute : ∀ a b f, (body a f).bind (body b) = (body b f).bind (body a))
    {xs ys : List α} (perm : xs.Perm ys) : ∀ f, eachM body xs f = eachM body ys f := by
  induction perm with
  | nil => intro f; rfl
  | cons a _ ih =>
    intro f
    simp only [eachM]
    cases body a f <;> simp_all [Outcome.bind]
  | swap a b xs =>
    intro f
    simpa only [eachM, bind_assoc] using congrArg (fun o => o.bind (eachM body xs)) (commute b a f)
  | trans _ _ ih₁ ih₂ => intro f; exact (ih₁ f).trans (ih₂ f)

@[simp] theorem dictGet_eq_none [DecidableEq K] (xs : List (K × V)) (key : K) :
    dictGet xs key = none ↔ key ∉ xs.map Prod.fst := by
  induction xs with
  | nil => simp [dictGet]
  | cons x xs ih =>
    rcases x with ⟨k,v⟩
    by_cases h : k = key <;> simp_all [dictGet,eq_comm]

@[simp] theorem dictGet_set [DecidableEq K] (xs : List (K × V)) (key query : K) (value : V) :
    dictGet (dictSet xs key value) query = if query = key then some value else dictGet xs query := by
  induction xs with
  | nil => by_cases h : query = key <;> simp_all [dictGet,dictSet,eq_comm]
  | cons x xs ih =>
    rcases x with ⟨k,v⟩
    by_cases h : k = key <;> by_cases hq : query = key <;> by_cases hk : k = query <;> simp_all [dictGet,dictSet]

@[simp] theorem allM_ok_true (p : α → Except Fault Bool) (xs : List α) :
    allM p xs = .ok true ↔ ∀ x ∈ xs, p x = .ok true := by
  induction xs with
  | nil => simp [allM]
  | cons x xs ih =>
    cases h : p x with
    | error e => simp [allM,h,Bind.bind,Except.bind]
    | ok b => cases b <;> simp [allM,h,Bind.bind,Except.bind,Pure.pure,Except.pure,ih]

end RMVerify.TypedSource
