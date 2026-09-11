import Semantics

/- Typed source execution. The frontend supplies variable projections and updates;
   operations below give Python's supported builtins their meaning. A fault keeps
   the frame at the point of failure, including earlier writes. -/
namespace RMVerify.TypedSource

inductive Fault where
  | missingKey
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

def Outcome.frame : Outcome Frame Result → Frame
  | .next frame => frame
  | .returned frame _ => frame
  | .fault frame _ => frame

def Outcome.fault? : Outcome Frame Result → Option Fault
  | .fault _ reason => some reason
  | _ => none

def Outcome.result? : Outcome Frame Result → Option Result
  | .returned _ value => some value
  | _ => none

def Outcome.bind (outcome : Outcome Frame Result) (next : Frame → Outcome Frame Result) :=
  match outcome with
  | .next frame => next frame
  | .returned frame result => .returned frame result
  | .fault frame reason => .fault frame reason

inductive Stmt (Frame Result : Type) : Type 1 where
  | skip
  | assign (put : Frame → α → Frame) (value : Expr Frame α)
  | seq (first rest : Stmt Frame Result)
  | branch (test : Expr Frame Bool) (yes no : Stmt Frame Result)
  | ret (value : Expr Frame Result)
  | each (items : Expr Frame (List α)) (body : α → Stmt Frame Result)

def eachM (body : α → Frame → Outcome Frame Result) : List α → Frame → Outcome Frame Result
  | [], frame => .next frame
  | a :: rest, frame => (body a frame).bind (eachM body rest)

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

@[simp] theorem setAdd_duplicate [DecidableEq K] (xs : List K) (key : K) (h : key ∈ xs) :
    setAdd xs key = xs := by simp [setAdd, h]

@[simp] theorem setAdd_length [DecidableEq K] (xs : List K) (key : K) :
    (setAdd xs key).length = if key ∈ xs then xs.length else xs.length + 1 := by
  by_cases h : key ∈ xs <;> simp [setAdd, h]

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

end RMVerify.TypedSource
