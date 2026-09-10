from counter import Counter
from rmverify import Specification, Contract, Call, Trace


def nonnegative(state: Counter) -> bool:
    return state.value >= 0


def monotone(before: Counter, after: Counter, result: None, offered: int) -> bool:
    return after.value >= before.value


spec = Specification(Counter, [Counter.step], invariants=[nonnegative],
                     contracts={Counter.step: Contract(ensures=monotone)},
                     checks=[Trace([Call("step", offered=n) for n in (-5, 0, 7, 7, 3, 10**100)])])
