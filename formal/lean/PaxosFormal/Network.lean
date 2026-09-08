import PaxosFormal.Generated
import Cslib.Foundations.Semantics.LTS.OmegaExecution

namespace PaxosFormal

structure Message where
  sender : Nat
  target : Nat
  kind : Int
  number : Int
  value : Int := 0
  priorNumber : Int := -1
  priorValue : Int := 0
  deriving Repr, BEq, DecidableEq, Inhabited

structure Vote where
  node : Nat
  number : Int
  value : Int
  deriving Repr, BEq, DecidableEq, Inhabited

structure World where
  nodes : Array (Array Int)
  pending : List Message := []
  inboxes : Array (List Message) := #[[], [], []]
  outstanding : Array Nat := #[0, 0, 0]
  submitted : List Int := []
  votes : List Vote := []
  declarations : List Vote := []
  outside : Bool := false
  invalid : Bool := false
  deriving Repr, Inhabited

def initialWorld : World := { nodes := #[nodeInitial, nodeInitial, nodeInitial] }

inductive Action where
  | propose (node : Nat) (value : Int)
  | tick (node : Nat)
  | resume (node : Nat)
  | deliver (index : Nat)
  | receive (node : Nat)
  | idle
  deriving Repr, DecidableEq, Inhabited

def field (state : Array Int) (index : Nat) : Int := state[index]!

def dispatch (w : World) (node : Nat) (input : Array Int) : World := Id.run do
  if node ≥ 3 || w.outside || w.invalid then return { w with invalid := true }
  let before := w.nodes[node]!
  let event := input[0]!
  if before[statusIndex]! != 0 || ((before[pcIndex]! != 0) != (event == 3)) then
    return { w with invalid := true }
  if event == 3 && w.outstanding[node]! != 0 then return { w with invalid := true }
  let after := nodeStep before input
  let mut result := { w with nodes := w.nodes.set! node after }
  if event == 1 && input[3]! != 0 then
    result := { result with submitted := input[3]! :: result.submitted }
  if after[statusIndex]! == 2 then return { result with outside := true }
  if after[declaredIndex]! != 0 then
    result := { result with declarations :=
      ⟨node, after[declaredNumIndex]!, after[declaredValueIndex]!⟩ :: result.declarations }
  if after[outKindIndex]! != 0 then
    let targets := if after[outTargetIndex]! == -1 then [0, 1, 2]
                   else [after[outTargetIndex]!.toNat]
    for target in targets do
      let packet : Message := ⟨node, target, after[outKindIndex]!, after[outNumIndex]!,
                                after[outValueIndex]!, after[outPriorNIndex]!, after[outPriorVIndex]!⟩
      result := { result with
        pending := result.pending ++ [packet]
        outstanding := result.outstanding.set! node (result.outstanding[node]! + 1) }
    if after[outKindIndex]! == 13 then
      result := { result with votes :=
        ⟨node, after[outNumIndex]!, after[outValueIndex]!⟩ :: result.votes }
  let queued := result.pending.length + result.inboxes.foldl (fun total q => total + q.length) 0
  if queued > queueCapacity then result := { result with outside := true }
  return result

def networkStep (w : World) (action : Action) : World :=
  match action with
  | .propose node value => dispatch w node #[1, 0, 0, value, -1, 0]
  | .tick node => dispatch w node #[2, 0, 0, 0, -1, 0]
  | .resume node => dispatch w node #[3, 0, 0, 0, -1, 0]
  | .idle => w
  | .deliver index =>
    if let some packet := w.pending[index]? then
      { w with
        pending := w.pending.take index ++ w.pending.drop (index + 1)
        inboxes := w.inboxes.set! packet.target (w.inboxes[packet.target]! ++ [packet])
        outstanding := w.outstanding.set! packet.sender (w.outstanding[packet.sender]! - 1) }
    else { w with invalid := true }
  | .receive node =>
    match w.inboxes[node]! with
    | [] => { w with invalid := true }
    | packet :: rest =>
      dispatch { w with inboxes := w.inboxes.set! node rest } node
        #[packet.kind, packet.sender, packet.number, packet.value, packet.priorNumber, packet.priorValue]

def runActions (actions : List Action) : World := actions.foldl networkStep initialWorld

def majority (w : World) (number value : Int) : Bool :=
  ([0, 1, 2].filter (fun node =>
    w.votes.any (fun vote => vote.node == node && vote.number == number && vote.value == value))).length ≥ 2

def chosen (w : World) (value : Int) : Bool :=
  w.votes.any (fun vote => majority w vote.number value)

def agreement (w : World) : Bool :=
  w.votes.all (fun a => w.votes.all (fun b =>
    !(chosen w a.value && chosen w b.value) || a.value == b.value))

def validity (w : World) : Bool :=
  w.votes.all (fun vote => !chosen w vote.value || w.submitted.contains vote.value)

def decisionAccuracy (w : World) : Bool :=
  w.declarations.all (fun d => chosen w d.value)

def decisionConsistency (w : World) : Bool :=
  w.declarations.all (fun a => w.declarations.all (fun b => a.value == b.value))

def hasChoice (w : World) : Bool := w.votes.any (fun v => chosen w v.value)
def allRecognize (w : World) : Bool :=
  [0, 1, 2].all (fun node => w.declarations.any (fun d => d.node == node && chosen w d.value))

/-- Out-of-scope states are excluded from claims, never reclassified as success. -/
def WithinScope (w : World) : Prop := w.outside = false ∧ w.invalid = false
def networkLTS : Cslib.LTS World Action :=
  ⟨fun s action t => networkStep s action = t ∧ WithinScope s ∧ WithinScope t⟩
def Transition (s t : World) : Prop :=
  ∃ action, networkLTS.Tr s action t

def Safety : Prop := ∀ s, Reachable initialWorld Transition s →
  agreement s = true ∧ validity s = true ∧ decisionAccuracy s = true ∧ decisionConsistency s = true

def ProposalLiveness (trace : Nat → World) : Prop :=
  LeadsTo (fun w => w.submitted ≠ []) (fun w => hasChoice w = true) trace

def LearningLiveness (trace : Nat → World) : Prop :=
  LeadsTo (fun w => hasChoice w = true) (fun w => allRecognize w = true) trace

/-- Fairness profiles are supplied as explicit predicates, not hidden axioms. -/
def ConditionalLiveness (fair : (Nat → World) → Prop) : Prop :=
  ∀ trace, Execution initialWorld Transition trace → fair trace →
    ProposalLiveness trace ∧ LearningLiveness trace

def SchedulerExecution (trace : Nat → World) (actions : Nat → Action) : Prop :=
  Execution initialWorld Transition trace ∧
  ∀ t, networkStep (trace t) (actions t) = trace (t + 1)

def idleNode (w : World) (n : Nat) : Bool :=
  w.nodes[n]![statusIndex]! == 0 && w.nodes[n]![pcIndex]! == 0

/-- FIFO head transmission fairness and per-node servicing fairness. -/
def FairSchedule (trace : Nat → World) (actions : Nat → Action) : Prop :=
  WeakFairness (fun t => !(trace t).pending.isEmpty)
    (fun t => decide (actions t = .deliver 0)) ∧
  ∀ n, n < 3 →
    WeakFairness (fun t => idleNode (trace t) n && !(trace t).inboxes[n]!.isEmpty)
      (fun t => decide (actions t = .receive n)) ∧
    WeakFairness (fun t => (trace t).nodes[n]![statusIndex]! == 0 &&
                          (trace t).nodes[n]![pcIndex]! != 0 && (trace t).outstanding[n]! == 0)
      (fun t => decide (actions t = .resume n)) ∧
    WeakFairness (fun t => idleNode (trace t) n)
      (fun t => decide (actions t = .tick n))

def SingleProposer (actions : Nat → Action) : Prop :=
  ∃ n, n < 3 ∧ ∀ t m v, actions t = .propose m v → m = n

/-- Specification only: no proof or non-vacuity claim is made for this bounded profile. -/
def BenignLiveness : Prop :=
  ∀ trace actions, SchedulerExecution trace actions → FairSchedule trace actions →
    SingleProposer actions → ProposalLiveness trace ∧ LearningLiveness trace

end PaxosFormal
