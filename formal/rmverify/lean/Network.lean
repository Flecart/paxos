import Semantics

namespace RMVerify.Reactive

/-- Choices are evaluated on the previous state. An empty domain disables the
    action, but does not disable the separately specified stuttering alternative. -/
def choiceStep (domain : State → List Input) (action : State → Input → State)
    (s t : State) : Prop := ∃ input ∈ domain s, t = action s input

def choiceOrStutter (domain : State → List Input) (action : State → Input → State)
    (s t : State) : Prop := t = s ∨ choiceStep domain action s t

theorem empty_choice (domain : State → List Input) (action : State → Input → State)
    (s t : State) (empty : domain s = []) : ¬ choiceStep domain action s t := by
  simp [choiceStep, empty]

theorem choice_nonblocking (domain : State → List Input) (action : State → Input → State)
    (s : State) : ∃ t, choiceOrStutter domain action s t := ⟨s, Or.inl rfl⟩

/-- Relational observer lift of complete rounds. The executable relation is
    independent of the observer; this construction alone makes no ownership claim. -/
def observed (m : Module State) (initialGhost : State → Ghost)
    (observe : State → Ghost → State → Ghost) : Module (State × Ghost) :=
  ⟨[⟨[], [], [],
    fun s => m.initial s.1 ∧ s.2 = initialGhost s.1,
    fun s t => m.step s.1 t.1 ∧ t.2 = observe s.1 s.2 t.1⟩]⟩

theorem observed_projects (m : Module State) (initialGhost : State → Ghost)
    (observe : State → Ghost → State → Ghost) (s : State × Ghost)
    (h : Reachable (observed m initialGhost observe) s) : Reachable m s.1 := by
  induction h with
  | initial h =>
    simp only [observed, Module.initial, List.mem_singleton, forall_eq] at h
    exact .initial h.1
  | step _ h ih =>
    simp only [observed, Module.step, List.mem_singleton, forall_eq] at h
    exact .step ih h.1

theorem observed_extends (m : Module State) (initialGhost : State → Ghost)
    (observe : State → Ghost → State → Ghost) (s : State) (h : Reachable m s) :
    ∃ g, Reachable (observed m initialGhost observe) (s, g) := by
  induction h with
  | @initial s h =>
    refine ⟨initialGhost s, .initial ?_⟩
    simpa [observed, Module.initial] using h
  | @step s t _ round ih =>
    obtain ⟨g, hg⟩ := ih
    refine ⟨observe s g t, .step hg ?_⟩
    simpa [observed, Module.step] using round

theorem observed_reachable_iff (m : Module State) (initialGhost : State → Ghost)
    (observe : State → Ghost → State → Ghost) (s : State) :
    (∃ g, Reachable (observed m initialGhost observe) (s, g)) ↔ Reachable m s := by
  constructor
  · rintro ⟨g, h⟩; exact observed_projects m initialGhost observe (s,g) h
  · exact observed_extends m initialGhost observe s

end RMVerify.Reactive
