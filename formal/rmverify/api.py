"""Public specification and result types; application code needs no decorators."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Contract:
    requires: object = None
    ensures: object = None


@dataclass(init=False)
class Call:
    method: str
    arguments: dict

    def __init__(self, method, /, **arguments):
        self.method = method.__name__ if callable(method) else method
        self.arguments = arguments


@dataclass
class Trace:
    calls: list[Call]


@dataclass
class Specification:
    target: type
    transitions: list
    invariants: list = field(default_factory=list)
    contracts: dict = field(default_factory=dict)
    checks: list[Trace] = field(default_factory=list)
    strengthening: list = field(default_factory=list)


@dataclass
class Report:
    status: str
    properties: dict = field(default_factory=dict)
    checks: list = field(default_factory=list)
    translation: str = "not-run"
    evidence: str = ""
    diagnostics: list[str] = field(default_factory=list)

    @property
    def ok(self):
        return (self.status == self.translation == "proved"
                and all(p["status"] == "proved" for p in self.properties.values())
                and all(c["status"] == "passed" for c in self.checks))


def verify(spec, *, directory=None, timeout=60, depth=10):
    from .checking import verify as run
    return run(spec, directory=directory, timeout=timeout, depth=depth)
