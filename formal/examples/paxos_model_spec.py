"""Separate verification entrypoints for the new Paxos model, not PaxosNode."""
from rmverify import Call, Contract, Specification, Trace
from examples.paxos_model import AcceptorState, BallotValue, PaxosAcceptorModel, PaxosSafetyModel


def valid_acceptor(state: AcceptorState) -> bool:
    return state.promised >= -1 and (
        state.accepted is None or
        (0 <= state.accepted.ballot and state.accepted.ballot <= state.promised)
    )


def acceptor_safe(s: PaxosAcceptorModel) -> bool:
    return valid_acceptor(s.state)


def prepare_rule(before: PaxosAcceptorModel, after: PaxosAcceptorModel,
                 result: None, ballot: int) -> bool:
    return after.state.promised == max(before.state.promised, ballot) and after.state.accepted == before.state.accepted


def accept_rule(before: PaxosAcceptorModel, after: PaxosAcceptorModel,
                result: None, ballot: int, value: int) -> bool:
    return after.state.promised >= before.state.promised and (
        (after.state == before.state) if ballot < 0 or ballot < before.state.promised else
        after.state == AcceptorState(ballot, BallotValue(ballot, value))
    )


acceptor = Specification(
    PaxosAcceptorModel,
    [PaxosAcceptorModel.prepare, PaxosAcceptorModel.receive_accept],
    [acceptor_safe],
    contracts={
        PaxosAcceptorModel.prepare: Contract(ensures=prepare_rule),
        PaxosAcceptorModel.receive_accept: Contract(ensures=accept_rule),
    },
    checks=[Trace([
        Call('receive_accept', ballot=0, value=7),
        Call('prepare', ballot=2),
        Call('receive_accept', ballot=1, value=8),
        Call('receive_accept', ballot=2, value=7),
        Call('receive_accept', ballot=2, value=7),
    ])],
)


def agreement(s: PaxosSafetyModel) -> bool:
    return len(s.chosen) <= 1


def acceptors_valid(s: PaxosSafetyModel) -> bool:
    return all(valid_acceptor(s.acceptors[a]) for a in s.acceptors)


transitions = [PaxosSafetyModel.phase1a, PaxosSafetyModel.phase1b,
               PaxosSafetyModel.phase2a, PaxosSafetyModel.phase2b,
               PaxosSafetyModel.learn, PaxosSafetyModel.idle]

# Calls and witness-search depth are regression bounds, not theorem assumptions.
adoption_trace = Trace([
    Call('phase1a', ballot=0),
    Call('phase1b', acceptor=0, ballot=0),
    Call('phase1b', acceptor=1, ballot=0),
    Call('phase2a', ballot=0, offered=7, first=0, second=1),
    Call('phase2b', acceptor=0, ballot=0),
    Call('phase2b', acceptor=1, ballot=0),
    Call('learn', ballot=0, value=7, first=0, second=1),
    Call('phase1a', ballot=1),
    Call('phase1b', acceptor=1, ballot=1),
    Call('phase1b', acceptor=2, ballot=1),
    Call('phase2a', ballot=1, offered=9, first=1, second=2),
    Call('phase2b', acceptor=1, ballot=1),
    Call('phase2b', acceptor=2, ballot=1),
    Call('learn', ballot=1, value=7, first=1, second=2),
])

spec = Specification(PaxosSafetyModel, transitions, [agreement],
                     strengthening=[acceptors_valid], checks=[adoption_trace])
