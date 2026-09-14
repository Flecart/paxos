"""Translation of pinned tlaplus/Examples Lock.tla, with labels 0,1,2,3.

One selected process action per round matches [Next]_vars, including stutter.
This is not the two-independently-advancing-atom Peterson round model.
"""
from rmverify import Component, Composition

class Lock:
    first: int
    second: int
    lock: int
    def __init__(self) -> None:
        self.first = 0
        self.second = 0
        self.lock = 1
    def first_step(self) -> None:
        if self.first == 0:
            self.first = 1
        elif self.first == 1:
            if self.lock == 1:
                self.lock = 0
                self.first = 2
        elif self.first == 2:
            self.first = 3
        elif self.first == 3:
            self.lock = 1
            self.first = 0
    def second_step(self) -> None:
        if self.second == 0:
            self.second = 1
        elif self.second == 1:
            if self.lock == 1:
                self.lock = 0
                self.second = 2
        elif self.second == 2:
            self.second = 3
        elif self.second == 3:
            self.lock = 1
            self.second = 0

def type_ok(s: Lock) -> bool:
    return 0 <= s.first and s.first <= 3 and 0 <= s.second and s.second <= 3 and (s.lock == 0 or s.lock == 1)

def mutex(s: Lock) -> bool:
    return not (s.first >= 2 and s.second >= 2)

def held(s: Lock) -> bool:
    return (s.first < 2 and s.second < 2) or s.lock == 0

def initial(s: Lock) -> bool:
    return s.first == 0 and s.second == 0 and s.lock == 1

def next_round(s: Lock, t: Lock) -> bool:
    return (t.first == s.first and t.second == s.second and t.lock == s.lock) or (
        t.second == s.second and (
            (s.first == 0 and t.first == 1 and t.lock == s.lock) or
            (s.first == 1 and s.lock == 1 and t.first == 2 and t.lock == 0) or
            (s.first == 2 and t.first == 3 and t.lock == s.lock) or
            (s.first == 3 and t.first == 0 and t.lock == 1))) or (
        t.first == s.first and (
            (s.second == 0 and t.second == 1 and t.lock == s.lock) or
            (s.second == 1 and s.lock == 1 and t.second == 2 and t.lock == 0) or
            (s.second == 2 and t.second == 3 and t.lock == s.lock) or
            (s.second == 3 and t.second == 0 and t.lock == 1)))

spec = Composition(Lock,[Component(Lock,[Lock.first_step,Lock.second_step],{'first':'first','second':'second','lock':'lock'})],
                   [mutex], [type_ok,held], initial_relation=initial,step_relation=next_round)
