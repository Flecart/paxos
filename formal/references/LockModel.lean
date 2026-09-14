/- Independent transcription of tlaplus/Examples Lock.tla at the revision in
   tlaplus/provenance.json. Labels remain an enum, and lock=1 becomes free=true.
   No fairness assumption occurs in the upstream Spec. -/
namespace TLALock
inductive Label where
  | l0 | l1 | cs | l2
  deriving Repr, DecidableEq
structure State where
  first : Label
  second : Label
  free : Bool
  deriving Repr, DecidableEq

def initial (s : State) : Prop := s.first = .l0 ∧ s.second = .l0 ∧ s.free = true

def process (pc pc' : Label) (free free' : Bool) : Prop :=
  (pc = .l0 ∧ pc' = .l1 ∧ free' = free) ∨
  (pc = .l1 ∧ free = true ∧ pc' = .cs ∧ free' = false) ∨
  (pc = .cs ∧ pc' = .l2 ∧ free' = free) ∨
  (pc = .l2 ∧ pc' = .l0 ∧ free' = true)

def next (s t : State) : Prop :=
  (t.second = s.second ∧ process s.first t.first s.free t.free) ∨
  (t.first = s.first ∧ process s.second t.second s.free t.free)

/-- TLA+'s [Next]_vars explicitly permits stuttering. -/
def round (s t : State) : Prop := t = s ∨ next s t

def code : Label → Int
  | .l0 => 0 | .l1 => 1 | .cs => 2 | .l2 => 3
@[simp] theorem code_injective (a b : Label) : code a = code b ↔ a = b := by cases a <;> cases b <;> decide
@[simp] theorem code_l0 (a : Label) : code a = 0 ↔ a = .l0 := by cases a <;> decide
@[simp] theorem code_l1 (a : Label) : code a = 1 ↔ a = .l1 := by cases a <;> decide
@[simp] theorem code_cs (a : Label) : code a = 2 ↔ a = .cs := by cases a <;> decide
@[simp] theorem code_l2 (a : Label) : code a = 3 ↔ a = .l2 := by cases a <;> decide
end TLALock
