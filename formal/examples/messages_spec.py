"""Immutable records, optional messages, record keys, and pure typed helpers."""
from dataclasses import dataclass
from rmverify import Specification, Contract, Call, Trace


@dataclass(frozen=True)
class Message:
    key: int
    payload: int


@dataclass(frozen=True)
class Envelope:
    message: Message | None
    delivered: bool


def make_message(key: int, payload: int) -> Message:
    return Message(key, payload)


def payload_or_zero(envelope: Envelope) -> int:
    if envelope.message is None:
        return 0
    return envelope.message.payload


class MessageStore:
    table: dict[Message, int]
    envelope: Envelope
    total: int

    def __init__(self) -> None:
        self.table = {}
        self.envelope = Envelope(None, False)
        self.total = 0

    def put(self, key: int, payload: int) -> Message:
        message = make_message(key, payload)
        self.table[message] = payload
        self.envelope = Envelope(message, True)
        self.total = payload_or_zero(self.envelope)
        return message

    def clear(self) -> None:
        self.envelope = Envelope(None, False)


def consistent(s: MessageStore) -> bool:
    return s.envelope.message is None or s.total == s.envelope.message.payload


def stored(before: MessageStore, after: MessageStore, result: Message, key: int, payload: int) -> bool:
    return result == make_message(key, payload) and after.table[result] == payload


spec = Specification(MessageStore, [MessageStore.put, MessageStore.clear], invariants=[consistent],
    contracts={MessageStore.put: Contract(ensures=stored)},
    checks=[Trace([Call('put', key=3, payload=7), Call('put', key=3, payload=7), Call('clear')])])
