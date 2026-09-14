"""A finite-choice lossy/reordering/repeating network; no fairness assumption."""
from dataclasses import dataclass
from rmverify import Component, Composition, Choice, Await

@dataclass(frozen=True)
class Message:
    key: int
    payload: int

class Sender:
    serial: int
    outgoing: Message | None
    def __init__(self) -> None:
        self.serial = 0
        self.outgoing = None
    def send(self) -> None:
        self.outgoing = Message(self.serial, self.serial)
        self.serial += 1

class Network:
    pending: set[Message]
    delivered: Message | None
    def __init__(self) -> None:
        self.pending = set()
        self.delivered = None
    def collect(self, message: Message | None) -> None:
        if message is not None:
            self.pending.add(message)
    def deliver(self, selected: Message) -> None:
        self.delivered = selected
    def drop(self, selected: Message) -> None:
        self.pending.discard(selected)
    def delay(self) -> None:
        self.delivered = None

class Receiver:
    processed: set[int]
    count: int
    def __init__(self) -> None:
        self.processed = set()
        self.count = 0
    def receive(self, message: Message | None) -> None:
        if message is not None:
            if message.key not in self.processed:
                self.processed.add(message.key)
                self.count += 1

class BrokenReceiver:
    processed: set[int]
    count: int
    def __init__(self) -> None:
        self.processed = set()
        self.count = 0
    def receive(self, message: Message | None) -> None:
        if message is not None:
            self.processed.add(message.key)
            self.count += 1

class History:
    sent: set[Message]
    handled: set[int]
    repeated: bool
    def __init__(self) -> None:
        self.sent = set()
        self.handled = set()
        self.repeated = False
    def watch(self, outgoing: Message | None, delivered: Message | None, before: int, after: int) -> None:
        if outgoing is not None:
            self.sent.add(outgoing)
        if after > before:
            if delivered is not None:
                if delivered.key in self.handled:
                    self.repeated = True
                self.handled.add(delivered.key)

class State:
    serial: int
    outgoing: Message | None
    pending: set[Message]
    delivered: Message | None
    processed: set[int]
    count: int
    sent: set[Message]
    handled: set[int]
    repeated: bool

def consistent(s: State) -> bool:
    return s.count == len(s.processed)

def sender_range(s: State) -> bool:
    return s.serial >= 0 and (s.outgoing is None or (0 <= s.outgoing.key and s.outgoing.key < s.serial and s.outgoing.payload == s.outgoing.key))

def pending_range(s: State) -> bool:
    return all(0 <= m.key and m.key < s.serial and m.payload == m.key for m in s.pending)

def delivered_range(s: State) -> bool:
    return s.delivered is None or (0 <= s.delivered.key and s.delivered.key < s.serial and s.delivered.payload == s.delivered.key)

def no_fabrication(s: State) -> bool:
    return (s.delivered is None or s.delivered in s.sent) and all(m in s.sent for m in s.pending) and (s.outgoing is None or s.outgoing in s.sent)

def at_most_once(s: State) -> bool:
    return not s.repeated

def history_domains(s: State) -> bool:
    return all(k in s.processed for k in s.handled) and all(k in s.handled for k in s.processed)

def make(receiver):
    return Composition(State, [
        Component(Sender,[Sender.send],{'serial':'serial','outgoing':'outgoing'}),
        Component(Network,[Network.collect,Network.deliver,Network.drop,Network.delay],{'pending':'pending','delivered':'delivered'},inputs={'message':'outgoing','selected':Choice('pending')}),
        Component(receiver,[receiver.receive],{'processed':'processed','count':'count'},inputs={'message':Await('delivered')}),
        Component(History,[History.watch],{'sent':'sent','handled':'handled','repeated':'repeated'},
                  inputs={'outgoing':Await('outgoing'),'delivered':Await('delivered'),'before':'count','after':Await('count')},stutter=False,ghost=True),
    ], [consistent,delivered_range,no_fabrication,at_most_once], [sender_range,pending_range,history_domains])

spec = make(Receiver)
broken = make(BrokenReceiver)
