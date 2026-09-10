"""FMSD99 Figure 2 as separate Python processes and a closed RM composition.

Each advance call is an atomic local operation. The RM composition chooses
independently whether each process advances or sleeps in a round.
"""
from rmverify import Component, Composition


class P1:
    pc: int
    x: bool

    def __init__(self, x: bool) -> None:
        self.pc = 0
        self.x = x

    def advance(self, pc2: int, x2: bool) -> None:
        if self.pc == 0:
            self.pc = 1
            self.x = x2
        elif self.pc == 1:
            if pc2 == 0 or self.x != x2:
                self.pc = 2
        elif self.pc == 2:
            self.pc = 0


class P2:
    pc: int
    x: bool

    def __init__(self, x: bool) -> None:
        self.pc = 0
        self.x = x

    def advance(self, pc1: int, x1: bool) -> None:
        if self.pc == 0:
            self.pc = 1
            self.x = not x1
        elif self.pc == 1:
            if pc1 == 0 or self.x == x1:
                self.pc = 2
        elif self.pc == 2:
            self.pc = 0


class State:
    """Property schema; each coordinate is owned by exactly one component."""
    pc1: int
    pc2: int
    x1: bool
    x2: bool


def mutual_exclusion(state: State) -> bool:
    return not (state.pc1 == 2 and state.pc2 == 2)


def control_locations(state: State) -> bool:
    return 0 <= state.pc1 <= 2 and 0 <= state.pc2 <= 2


def priority(state: State) -> bool:
    return ((state.pc1 != 2 or state.pc2 != 1 or state.x1 != state.x2)
            and (state.pc2 != 2 or state.pc1 != 1 or state.x1 == state.x2))


def paper_initial(state: State) -> bool:
    # The flag variables are arbitrary Booleans, as in the paper.
    return state.pc1 == 0 and state.pc2 == 0


def paper_round(before: State, after: State) -> bool:
    """Independent relational statement of the two atoms, including sleep."""
    first = ((after.pc1 == before.pc1 and after.x1 == before.x1)
             or (before.pc1 == 0 and after.pc1 == 1 and after.x1 == before.x2)
             or (before.pc1 == 1 and (before.pc2 == 0 or before.x1 != before.x2)
                 and after.pc1 == 2 and after.x1 == before.x1)
             or (before.pc1 == 2 and after.pc1 == 0 and after.x1 == before.x1))
    second = ((after.pc2 == before.pc2 and after.x2 == before.x2)
              or (before.pc2 == 0 and after.pc2 == 1 and after.x2 == (not before.x1))
              or (before.pc2 == 1 and (before.pc1 == 0 or before.x1 == before.x2)
                  and after.pc2 == 2 and after.x2 == before.x2)
              or (before.pc2 == 2 and after.pc2 == 0 and after.x2 == before.x2))
    return first and second


peterson = Composition(
    State,
    [Component(P1, [P1.advance], controls={"pc": "pc1", "x": "x1"},
               inputs={"pc2": "pc2", "x2": "x2"}, stutter=True),
     Component(P2, [P2.advance], controls={"pc": "pc2", "x": "x2"},
               inputs={"pc1": "pc1", "x1": "x1"}, stutter=True)],
    invariants=[mutual_exclusion], strengthening=[control_locations, priority],
    initial_relation=paper_initial, step_relation=paper_round,
)
