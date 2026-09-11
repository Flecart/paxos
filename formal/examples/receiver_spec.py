"""Receiver core under arbitrary repeated IDs; network composition is separate."""
from rmverify import Specification, Contract, Call, Trace


class Receiver:
    processed: set[int]
    count: int

    def __init__(self) -> None:
        self.processed = set()
        self.count = 0

    def deliver(self, key: int) -> None:
        if key not in self.processed:
            self.processed.add(key)
            self.count += 1


def consistent(s: Receiver) -> bool:
    return s.count == len(s.processed)


def duplicate_safe(before: Receiver, after: Receiver, result: None, key: int) -> bool:
    return (key in after.processed and
            after.count == before.count + (0 if key in before.processed else 1))


receiver = Specification(Receiver, [Receiver.deliver], invariants=[consistent],
    contracts={Receiver.deliver: Contract(ensures=duplicate_safe)},
    checks=[Trace([Call('deliver', key=3), Call('deliver', key=3), Call('deliver', key=1)])])


class BrokenReceiver:
    processed: set[int]
    count: int

    def __init__(self) -> None:
        self.processed = set()
        self.count = 0

    def deliver(self, key: int) -> None:
        self.processed.add(key)
        self.count += 1


def broken_consistent(s: BrokenReceiver) -> bool:
    return s.count == len(s.processed)


broken_receiver = Specification(BrokenReceiver, [BrokenReceiver.deliver], invariants=[broken_consistent])
