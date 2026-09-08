import Std
import Cslib.Foundations.Data.OmegaSequence.Temporal

namespace PaxosFormal

/-- Scalar subset of the pinned RM operation language. Boolean wires are 0/1. -/
inductive Op where
  | const (value : Int)
  | id | add | sub | max | min | eq | ne | lt | le | gt | ge | and | or | not | ite
  deriving Repr, DecidableEq, Inhabited

structure Instr where
  op : Op
  args : Array Nat
  deriving Repr, Inhabited

def flag (p : Bool) : Int := if p then 1 else 0

def evalOp (op : Op) (a : Array Int) : Int :=
  match op with
  | .const v => v
  | .id => a[0]!
  | .add => a[0]! + a[1]!
  | .sub => a[0]! - a[1]!
  | .max => max a[0]! a[1]!
  | .min => min a[0]! a[1]!
  | .eq => flag (a[0]! == a[1]!)
  | .ne => flag (a[0]! != a[1]!)
  | .lt => flag (a[0]! < a[1]!)
  | .le => flag (a[0]! ≤ a[1]!)
  | .gt => flag (a[0]! > a[1]!)
  | .ge => flag (a[0]! ≥ a[1]!)
  | .and => flag (a[0]! != 0 && a[1]! != 0)
  | .or => flag (a[0]! != 0 || a[1]! != 0)
  | .not => flag (a[0]! == 0)
  | .ite => if a[0]! != 0 then a[1]! else a[2]!

def execute (program : Array Instr) (inputs : Array Int) : Array Int :=
  program.foldl (fun wires instruction =>
    wires.push (evalOp instruction.op (instruction.args.map (fun i => wires[i]!)))) inputs

def runBlock (program : Array Instr) (outputs : Array Nat)
    (state inputs : Array Int) : Array Int :=
  let wires := execute program (state ++ inputs)
  outputs.map (fun i => wires[i]!)

/-- Relational RM semantics: each instruction appends its assigned output wire. -/
inductive Executes : List Instr → Array Int → Array Int → Prop
  | nil (s) : Executes [] s s
  | cons (i : Instr) (rest : List Instr) (s final : Array Int)
      (h : Executes rest (s.push (evalOp i.op (i.args.map (fun n => s[n]!)))) final) :
      Executes (i :: rest) s final

theorem executeList_correct (program : List Instr) (s : Array Int) :
    Executes program s (program.foldl (fun w i =>
      w.push (evalOp i.op (i.args.map (fun n => w[n]!)))) s) := by
  induction program generalizing s with
  | nil => exact Executes.nil s
  | cons i rest ih => exact Executes.cons i rest s _ (ih _)

/-- A finite prefix is evidence only for the states in that prefix. -/
inductive Reachable (init : σ) (step : σ → σ → Prop) : σ → Prop
  | initial : Reachable init step init
  | next {s t} : Reachable init step s → step s t → Reachable init step t

def Execution (init : σ) (step : σ → σ → Prop) (trace : Nat → σ) : Prop :=
  trace 0 = init ∧ ∀ t, step (trace t) (trace (t + 1))

def Always (p : σ → Prop) (trace : Nat → σ) : Prop := ∀ t, p (trace t)
def Eventually (p : σ → Prop) (trace : Nat → σ) : Prop := ∃ t, p (trace t)
def LeadsTo (p q : σ → Prop) (trace : Nat → σ) : Prop :=
  Cslib.ωSequence.LeadsTo ⟨trace⟩ p q

/-- Fairness is a hypothesis on schedules, never an axiom that progress holds. -/
def WeakFairness (enabled taken : Nat → Bool) : Prop :=
  ∀ t, (∀ u, t ≤ u → enabled u = true) → ∃ u, t ≤ u ∧ taken u = true

end PaxosFormal
