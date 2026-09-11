"""Intentional mutation: safety holds, but paper-round equivalence fails.

Run: python -m rmverify examples.peterson_stuck:peterson --timeout 120
V2 currently reports the failed equivalence as unknown, not refuted.
"""
from dataclasses import replace

from .peterson_v2 import peterson as working_peterson


class StuckP1:
    pc: int
    x: bool

    def __init__(self, x: bool) -> None:
        self.pc = 0
        self.x = x

    def advance(self, pc2: int, x2: bool) -> None:
        if self.pc == 0:
            self.pc = 0  # Deliberate mutation: never requests entry.
            self.x = x2
        elif self.pc == 1:
            if pc2 == 0 or self.x != x2:
                self.pc = 2
        elif self.pc == 2:
            self.pc = 0


peterson = replace(working_peterson, components=[
    replace(working_peterson.components[0], target=StuckP1,
            transitions=[StuckP1.advance]),
    working_peterson.components[1],
])
