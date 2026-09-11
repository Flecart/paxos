"""Small typed collection examples; ordinary Python, separate properties."""
from rmverify import Specification, Contract, Call, Trace


class Store:
    entries: dict[int, int]
    ids: set[int]
    last: int

    def __init__(self) -> None:
        self.entries = {}
        self.ids = set()
        self.last = 0

    def register(self, key: int) -> None:
        self.entries[key] = 7
        self.ids.add(key)
        self.last = self.entries[key]

    def forget(self, key: int) -> None:
        self.ids.discard(key)


def nonnegative(s: Store) -> bool:
    return s.last >= 0 and len(s.entries) >= 0 and len(s.ids) >= 0


def registration(before: Store, after: Store, result: None, key: int) -> bool:
    return after.entries[key] == 7 and (key not in before.entries or len(after.entries) == len(before.entries))


spec = Specification(Store, [Store.register, Store.forget], invariants=[nonnegative], contracts={Store.register: Contract(ensures=registration)},
    checks=[Trace([Call("register", key=3), Call("register", key=3), Call("register", key=1), Call("forget", key=8)])])


class Registry:
    entries: dict[int, int]
    ids: set[int]

    def __init__(self) -> None:
        self.entries = {}
        self.ids = set()

    def register(self, key: int, payload: int) -> None:
        entries = self.entries
        if key not in entries:
            entries[key] = payload
        self.ids.add(key)


def domains_agree(s: Registry) -> bool:
    return all(k in s.ids for k in s.entries) and all(k in s.entries for k in s.ids)


def retains_payload(before: Registry, after: Registry, result: None, key: int, payload: int) -> bool:
    return (key in after.entries and
            after.entries.get(key, 0) == (before.entries.get(key, 0) if key in before.entries else payload) and
            (key not in before.entries or len(after.entries) == len(before.entries)))


registry = Specification(Registry, [Registry.register], invariants=[domains_agree],
    contracts={Registry.register: Contract(ensures=retains_payload)},
    checks=[Trace([Call("register", key=3, payload=7), Call("register", key=3, payload=99),
                   Call("register", key=1, payload=-8)])])
