import Std

namespace RMVerify
abbrev Env := Nat → Int

def flag (b : Bool) : Int := if b then 1 else 0

@[simp] theorem flag_false : flag false = 0 := rfl
@[simp] theorem flag_true : flag true = 1 := rfl

-- Keep Boolean encodings symbolic instead of expanding a conditional for
-- every nested Boolean operator during invariant simplification.
@[simp] theorem flag_eq_zero (b : Bool) : flag b = 0 ↔ b = false := by
  cases b <;> decide

@[simp] theorem flag_eq_one (b : Bool) : flag b = 1 ↔ b = true := by
  cases b <;> decide

@[simp] theorem flag_eq_flag (a b : Bool) : flag a = flag b ↔ a = b := by
  cases a <;> cases b <;> decide

@[simp] theorem flag_test (b : Bool) : (flag b != 0) = b := by
  cases b <;> rfl

@[simp] theorem flag_valid (b : Bool) : flag b = 0 ∨ flag b = 1 := by
  cases b <;> decide

def update (env : Env) (i : Nat) (v : Int) : Env :=
  fun j => if j = i then v else env j

def environment (xs : List Int) : Env := fun i => xs[i]?.getD 0

inductive Op where
  | add | sub | mul | eq | ne | lt | le | gt | ge | and | or
  deriving Repr, DecidableEq

def Op.eval : Op → Int → Int → Int
  | .add, a, b => a + b
  | .sub, a, b => a - b
  | .mul, a, b => a * b
  | .eq, a, b => flag (a == b)
  | .ne, a, b => flag (a != b)
  | .lt, a, b => flag (a < b)
  | .le, a, b => flag (a ≤ b)
  | .gt, a, b => flag (a > b)
  | .ge, a, b => flag (a ≥ b)
  | .and, a, b => flag (a != 0 && b != 0)
  | .or, a, b => flag (a != 0 || b != 0)

inductive Expr where
  | lit (value : Int)
  | var (slot : Nat)
  | bin (op : Op) (left right : Expr)
  | ite (condition yes no : Expr)
  deriving Repr

def Expr.eval (env : Env) : Expr → Int
  | .lit n => n
  | .var n => env n
  | .bin op a b => op.eval (a.eval env) (b.eval env)
  | .ite c a b => if c.eval env != 0 then a.eval env else b.eval env

/-- Structured statements retain the source's sequencing and early returns. -/
inductive Stmt where
  | skip
  | assign (slot : Nat) (value : Expr)
  | seq (first rest : Stmt)
  | branch (condition : Expr) (yes no : Stmt)
  | ret (value : Expr)
  deriving Repr

inductive Outcome where
  | next (env : Env)
  | returned (env : Env) (value : Int)

def Outcome.bind (outcome : Outcome) (next : Env → Outcome) : Outcome :=
  match outcome with
  | .next env => next env
  | .returned env value => .returned env value

def Stmt.exec (env : Env) : Stmt → Outcome
  | .skip => .next env
  | .assign n e => .next (update env n (e.eval env))
  | .seq a b => (a.exec env).bind (fun env' => b.exec env')
  | .branch c a b => if c.eval env != 0 then a.exec env else b.exec env
  | .ret e => .returned env (e.eval env)

def Outcome.outputs (fields : Nat) : Outcome → List Int
  | .next env => (List.range fields).map env ++ [0]
  | .returned env result => (List.range fields).map env ++ [result]

@[simp] theorem Outcome.bind_next (env : Env) (f : Env → Outcome) :
    (Outcome.next env).bind f = f env := rfl

@[simp] theorem Outcome.bind_returned (env : Env) (v : Int) (f : Env → Outcome) :
    (Outcome.returned env v).bind f = .returned env v := rfl

@[simp] theorem Outcome.outputs_next (env : Env) (n : Nat) :
    (Outcome.next env).outputs n = (List.range n).map env ++ [0] := rfl

@[simp] theorem Outcome.outputs_returned (env : Env) (v : Int) (n : Nat) :
    (Outcome.returned env v).outputs n = (List.range n).map env ++ [v] := rfl

@[simp] theorem Outcome.bind_ite (p : Prop) [Decidable p] (a b : Outcome) (f : Env → Outcome) :
    (if p then a else b).bind f = if p then a.bind f else b.bind f := by
  by_cases h : p <;> simp [h]

@[simp] theorem Outcome.outputs_ite (p : Prop) [Decidable p] (a b : Outcome) (n : Nat) :
    (if p then a else b).outputs n = if p then a.outputs n else b.outputs n := by
  by_cases h : p <;> simp [h]

/-- Independent ordered-wire execution; it does not call the source interpreter. -/
def execute (cursor : Nat) (terms : List Expr) (env : Env) : Env :=
  match terms with
  | [] => env
  | term :: rest => execute (cursor + 1) rest (update env cursor (term.eval env))

structure Graph where
  inputs : Nat
  terms : List Expr
  outputs : List Nat

def Graph.run (g : Graph) (env : Env) : List Int :=
  g.outputs.map (execute g.inputs g.terms env)

structure Model (State Action : Type) where
  initial : State
  step : State → Action → State

inductive Reachable (m : Model State Action) : State → Prop where
  | initial : Reachable m m.initial
  | step : Reachable m s → Reachable m (m.step s action)

theorem invariant_of_induction (m : Model State Action) (p : State → Prop)
    (initial : p m.initial)
    (preserved : ∀ s action, p s → p (m.step s action)) :
    ∀ s, Reachable m s → p s := by
  intro s h
  induction h with
  | initial => exact initial
  | step _ ih => exact preserved _ _ ih

theorem invariant_always (m : Model State Action) (p : State → Prop)
    (safe : ∀ s, Reachable m s → p s)
    (states : Nat → State) (actions : Nat → Action)
    (start : states 0 = m.initial)
    (round : ∀ n, states (n+1) = m.step (states n) (actions n)) :
    ∀ n, p (states n) := by
  intro n
  apply safe
  induction n with
  | zero => rw [start]; exact .initial
  | succ n ih => rw [round]; exact .step ih

end RMVerify

namespace RMVerify.Reactive

/-- A relational atom constrains only its controlled coordinates. Input ports
    select either the old valuation (reads) or the candidate new one (awaits). -/
structure Atom (State : Type) where
  controls : List Nat
  reads : List Nat
  awaits : List Nat
  initial : State → Prop
  step : State → State → Prop

structure Module (State : Type) where
  atoms : List (Atom State)

def Module.parallel (a b : Module State) : Module State := ⟨a.atoms ++ b.atoms⟩

def Module.initial (m : Module State) (s : State) : Prop :=
  ∀ a ∈ m.atoms, a.initial s

def Module.step (m : Module State) (s t : State) : Prop :=
  ∀ a ∈ m.atoms, a.step s t

theorem initial_parallel (a b : Module State) (s : State) :
    (a.parallel b).initial s ↔ a.initial s ∧ b.initial s := by
  simp only [Module.initial, Module.parallel, List.mem_append]
  constructor
  · intro h; exact ⟨fun x hx => h x (.inl hx), fun x hx => h x (.inr hx)⟩
  · rintro ⟨ha, hb⟩ x (hx | hx)
    · exact ha x hx
    · exact hb x hx

theorem step_parallel (a b : Module State) (s t : State) :
    (a.parallel b).step s t ↔ a.step s t ∧ b.step s t := by
  simp only [Module.step, Module.parallel, List.mem_append]
  constructor
  · intro h; exact ⟨fun x hx => h x (.inl hx), fun x hx => h x (.inr hx)⟩
  · rintro ⟨ha, hb⟩ x (hx | hx)
    · exact ha x hx
    · exact hb x hx

def ordered (ready : List Nat) : List (Atom State) → Bool
  | [] => true
  | a :: rest => a.awaits.all ready.contains && ordered (ready ++ a.controls) rest

/-- Closed composition: exactly one owner per coordinate and an acyclic
    await order. Old-value reads need no ordering restriction. -/
def Module.wellFormed (m : Module State) (variables : Nat) : Bool :=
  let owned := m.atoms.flatMap Atom.controls
  owned.length == variables && owned.eraseDups.length == variables &&
  owned.all (fun v => v < variables) &&
  m.atoms.all (fun a => a.reads.all (fun v => v < variables)) && ordered [] m.atoms

inductive Reachable (m : Module State) : State → Prop where
  | initial : m.initial s → Reachable m s
  | step : Reachable m s → m.step s t → Reachable m t

theorem invariant_of_induction (m : Module State) (p : State → Prop)
    (initial : ∀ s, m.initial s → p s)
    (preserved : ∀ s t, p s → m.step s t → p t) :
    ∀ s, Reachable m s → p s := by
  intro s h
  induction h with
  | initial h => exact initial _ h
  | step _ h ih => exact preserved _ _ ih h

theorem invariant_always (m : Module State) (p : State → Prop)
    (safe : ∀ s, Reachable m s → p s) (states : Nat → State)
    (start : m.initial (states 0))
    (round : ∀ n, m.step (states n) (states (n+1))) :
    ∀ n, p (states n) := by
  intro n
  apply safe
  induction n with
  | zero => exact .initial start
  | succ n ih => exact .step ih (round n)

end RMVerify.Reactive
