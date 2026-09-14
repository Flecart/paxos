"""PaxosSafetyModel: a separate synchronous, single-decree Paxos model.

Three acceptors (0, 1, 2), two-member quorums, unbounded nonnegative ballots,
and integer values. Message histories permit arbitrary delayed/repeated receipt.
This is not an extraction or verification of paxos_lab.algorithm.PaxosNode.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class BallotValue:
    ballot: int
    value: int


@dataclass(frozen=True)
class AcceptorState:
    promised: int
    accepted: BallotValue | None


def promise(state: AcceptorState, ballot: int) -> AcceptorState:
    if ballot >= 0 and ballot > state.promised:
        return AcceptorState(ballot, state.accepted)
    return state


def accept(state: AcceptorState, ballot: int, value: int) -> AcceptorState:
    if ballot >= 0 and ballot >= state.promised:
        return AcceptorState(ballot, BallotValue(ballot, value))
    return state


class PaxosAcceptorModel:
    """Local acceptor rules; proposal uniqueness is a protocol obligation."""
    state: AcceptorState

    def __init__(self) -> None:
        self.state = AcceptorState(-1, None)

    def prepare(self, ballot: int) -> None:
        self.state = promise(self.state, ballot)

    def receive_accept(self, ballot: int, value: int) -> None:
        self.state = accept(self.state, ballot, value)


@dataclass(frozen=True)
class PromiseKey:
    acceptor: int
    ballot: int


@dataclass(frozen=True)
class Vote:
    acceptor: int
    ballot: int
    value: int


def safe_value(first: AcceptorState, second: AcceptorState, offered: int) -> int:
    """Adopt the value at the highest accepted ballot in the prepare quorum."""
    if first.accepted is not None:
        if second.accepted is not None:
            if second.accepted.ballot > first.accepted.ballot:
                return second.accepted.value
        return first.accepted.value
    if second.accepted is not None:
        return second.accepted.value
    return offered


class PaxosSafetyModel:
    """One protocol action per atomic call, following Paxos.tla's scheduling.

    Histories only grow. A message need never be received, and may be received
    again. There are no explicit leaders, sockets, crashes, or fairness rules.
    """
    acceptors: dict[int, AcceptorState]
    prepares: set[int]
    promises: dict[PromiseKey, AcceptorState]
    proposals: dict[int, int]
    votes: set[Vote]
    chosen: set[int]

    def __init__(self) -> None:
        self.acceptors = {
            0: AcceptorState(-1, None),
            1: AcceptorState(-1, None),
            2: AcceptorState(-1, None),
        }
        self.prepares = set()
        self.promises = {}
        self.proposals = {}
        self.votes = set()
        self.chosen = set()

    def phase1a(self, ballot: int) -> None:
        if ballot >= 0:
            self.prepares.add(ballot)

    def phase1b(self, acceptor: int, ballot: int) -> None:
        if acceptor in self.acceptors and ballot in self.prepares:
            before = self.acceptors[acceptor]
            if ballot > before.promised:
                after = promise(before, ballot)
                self.acceptors[acceptor] = after
                self.promises[PromiseKey(acceptor, ballot)] = after

    def phase2a(self, ballot: int, offered: int, first: int, second: int) -> None:
        if first != second and ballot not in self.proposals:
            left = PromiseKey(first, ballot)
            right = PromiseKey(second, ballot)
            if left in self.promises and right in self.promises:
                value = safe_value(self.promises[left], self.promises[right], offered)
                self.proposals[ballot] = value

    def phase2b(self, acceptor: int, ballot: int) -> None:
        if acceptor in self.acceptors and ballot in self.proposals:
            before = self.acceptors[acceptor]
            if ballot >= before.promised:
                value = self.proposals[ballot]
                self.acceptors[acceptor] = accept(before, ballot, value)
                self.votes.add(Vote(acceptor, ballot, value))

    def learn(self, ballot: int, value: int, first: int, second: int) -> None:
        if first != second:
            if Vote(first, ballot, value) in self.votes and Vote(second, ballot, value) in self.votes:
                self.chosen.add(value)

    def idle(self) -> None:
        pass
