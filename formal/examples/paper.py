"""Executable specializations of FMSD99, Figures 1–2.

Each tick is one round. Constructors choose concrete initial valuations;
choice/run inputs expose update nondeterminism to the environment.
"""
from rmverify import Contract, Specification


class NotGate:
    out: bool

    def __init__(self) -> None:
        self.out = True

    def tick(self, signal: bool) -> None:
        self.out = not signal


def negates(before: NotGate, after: NotGate, result: None, signal: bool) -> bool:
    return after.out == (not signal)


not_gate = Specification(NotGate, [NotGate.tick],
                         contracts={NotGate.tick: Contract(ensures=negates)})


class AndGate:
    out: bool

    def __init__(self) -> None:
        self.out = False

    def tick(self, left: bool, right: bool) -> None:
        self.out = left and right


def conjunction(before: AndGate, after: AndGate, result: None,
                left: bool, right: bool) -> bool:
    return after.out == (left and right)


and_gate = Specification(AndGate, [AndGate.tick],
                         contracts={AndGate.tick: Contract(ensures=conjunction)})


class Latch:
    out: bool
    state: bool

    def __init__(self) -> None:
        self.out = False
        self.state = False

    def tick(self, set_: bool, reset: bool, choose_set: bool) -> None:
        self.out = self.state
        if set_ and reset:
            self.state = choose_set
        elif set_:
            self.state = True
        elif reset:
            self.state = False


def latch_round(before: Latch, after: Latch, result: None,
                set_: bool, reset: bool, choose_set: bool) -> bool:
    # A relational contract: output lags state by one round. With both inputs
    # high either state is legal; choose_set is deliberately not constrained.
    return (after.out == before.state
            and (set_ or reset or after.state == before.state)
            and (not set_ or reset or after.state)
            and (not reset or set_ or not after.state))


latch = Specification(Latch, [Latch.tick],
                      contracts={Latch.tick: Contract(ensures=latch_round)})


class Peterson:
    # 0 = outside, 1 = requesting, 2 = inside the critical section.
    pc1: int
    pc2: int
    x1: bool
    x2: bool

    def __init__(self) -> None:
        self.pc1 = 0
        self.pc2 = 0
        self.x1 = False
        self.x2 = False

    def tick(self, run1: bool, run2: bool) -> None:
        # Every guard and flag assignment reads the latched state. In
        # particular, process 2 must not see process 1's writes this round.
        pc1 = self.pc1
        pc2 = self.pc2
        x1 = self.x1
        x2 = self.x2
        if run1:
            if pc1 == 0:
                self.pc1 = 1
                self.x1 = x2
            elif pc1 == 1:
                if pc2 == 0 or x1 != x2:
                    self.pc1 = 2
            else:
                self.pc1 = 0
        if run2:
            if pc2 == 0:
                self.pc2 = 1
                self.x2 = not x1
            elif pc2 == 1:
                if pc1 == 0 or x1 == x2:
                    self.pc2 = 2
            else:
                self.pc2 = 0


def mutual_exclusion(state: Peterson) -> bool:
    return not (state.pc1 == 2 and state.pc2 == 2)


def control_locations(state: Peterson) -> bool:
    return 0 <= state.pc1 <= 2 and 0 <= state.pc2 <= 2


def priority(state: Peterson) -> bool:
    return ((state.pc1 != 2 or state.pc2 != 1 or state.x1 != state.x2)
            and (state.pc2 != 2 or state.pc1 != 1 or state.x1 == state.x2))


peterson = Specification(Peterson, [Peterson.tick], invariants=[mutual_exclusion],
                         strengthening=[control_locations, priority])

# No concrete traces are needed to request any of the proofs above.
EXAMPLES = {"not_gate": not_gate, "and_gate": and_gate,
            "latch": latch, "peterson": peterson}
