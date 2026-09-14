"""Small executable exercises for helpers, borrows, moves, and set order."""
from rmverify import Specification, Contract, Trace, Call

class Store:
    entries: dict[int,int]
    total: int
    def __init__(self) -> None:
        self.entries = {}
        self.total = 0
    def save(self, key: int) -> int:
        owned: dict[int,int] = {}
        owned[key] = 7
        self.entries = owned
        return self.entries[key]
    def update(self, key: int) -> None:
        amount = self.save(key)
        self.total += amount
    def read(self, supplied: dict[int,int]) -> int:
        borrowed = supplied
        return borrowed.get(0, 0)
    def guarded(self, offered: int | None) -> int:
        if offered is None:
            return 0
        return offered + 1
    def branch_borrow(self, enabled: bool) -> None:
        if enabled:
            exclusive = self.entries
            exclusive[0] = 7

def nonnegative(s: Store) -> bool:
    return s.total >= 0

store = Specification(Store,[Store.update,Store.read,Store.guarded,Store.branch_borrow],[nonnegative],
                      checks=[Trace([Call('update',key=3),Call('update',key=3),Call('read',supplied={0:9}),Call('guarded',offered=None),Call('guarded',offered=3),Call('branch_borrow',enabled=True)])])

class Sum:
    values: set[int]
    total: int
    def __init__(self) -> None:
        self.values = {1,2}
        self.total = 0
    def accumulate(self) -> None:
        for element in self.values:
            self.total += element

def arithmetic(s: Sum) -> bool:
    return s.total == s.total

summation = Specification(Sum,[Sum.accumulate],[arithmetic],checks=[Trace([Call('accumulate'),Call('accumulate')])])
