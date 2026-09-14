import Semantics

namespace RMVerify.Borrowing

abbrev Position := Nat × Nat

def before (a b : Position) : Bool := a.1 < b.1 || (a.1 == b.1 && a.2 < b.2)
def atMost (a b : Position) : Bool := before a b || a == b

structure Loan where
  owner : Nat
  name : String
  exclusive : Bool
  start : Position
  finish : Position
  deriving Repr, DecidableEq

structure Access where
  owner : Nat
  via : Option String
  write : Bool
  position : Position
  deriving Repr, DecidableEq

def Loan.active (loan : Loan) (position : Position) : Bool :=
  before loan.start position && atMost position loan.finish

def Loan.permits (loan : Loan) (access : Access) : Prop :=
  loan.owner = access.owner → loan.active access.position = true →
    access.via = some loan.name ∨ (loan.exclusive = false ∧ access.write = false)

instance (loan : Loan) (access : Access) : Decidable (loan.permits access) := inferInstanceAs
  (Decidable (loan.owner = access.owner → loan.active access.position = true →
    access.via = some loan.name ∨ (loan.exclusive = false ∧ access.write = false)))

def valid (slots : Nat) (loans : List Loan) (accesses : List Access) : Prop :=
  (loans.map Loan.name).Nodup ∧
  (∀ loan ∈ loans, loan.owner < slots ∧ atMost loan.start loan.finish = true) ∧
  (∀ access ∈ accesses, access.owner < slots ∧
    (∀ loan ∈ loans, loan.permits access) ∧
    (∀ name, access.via = some name → ∃ loan ∈ loans,
      loan.name = name ∧ loan.owner = access.owner ∧ loan.active access.position = true ∧
      (access.write = true → loan.exclusive = true)))

/-- Every source access respects every live loan. -/
theorem no_conflict (slots : Nat) (loans : List Loan) (accesses : List Access)
    (certificate : valid slots loans accesses) (access : Access) (ha : access ∈ accesses)
    (loan : Loan) (hl : loan ∈ loans) : loan.permits access := (certificate.2.2 access ha).2.1 loan hl

structure Move where
  donor : Nat
  position : Position

def affine (moves : List Move) (accesses : List Access) : Prop :=
  (moves.map Move.donor).Nodup ∧ ∀ m ∈ moves, ∀ a ∈ accesses,
    before m.position a.position = true → a.owner ≠ m.donor

theorem no_use_after_move (moves : List Move) (accesses : List Access)
    (h : affine moves accesses) (m : Move) (hm : m ∈ moves)
    (a : Access) (ha : a ∈ accesses) (later : before m.position a.position = true) :
    a.owner ≠ m.donor := h.2 m hm a ha later

end RMVerify.Borrowing
