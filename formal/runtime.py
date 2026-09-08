"""Exact scalar RM interpreter and bounded asynchronous composition.

The interpreter does not delegate to the Python algorithm or use torch's fixed
width arithmetic. All integer operations use Python's mathematical integers.
"""
from collections import deque
from dataclasses import dataclass
import json
from pathlib import Path

from compile_rm import load_node

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "generated" / "manifest.json").read_text())
VALUES = MANIFEST["values"]
KINDS = MANIFEST["kinds"]
REVERSE_KINDS = {v: k for k, v in KINDS.items()}


def encode(value):
    for i, candidate in enumerate(VALUES):
        if type(value) is type(candidate) and value == candidate:
            return i
    raise ValueError(f"Value outside the declared domain: {value!r}")


def evaluate(block, state, inputs):
    wires = list(state) + list(inputs)
    for term in block["terms"]:
        a = [wires[i] for i in term["args"]]
        op = term["op"].removeprefix("LIA_")
        if op in ("Int", "Bool"):
            result = term["value"]
        elif op == "Id": result = a[0]
        elif op == "Add": result = a[0] + a[1]
        elif op == "Sub": result = a[0] - a[1]
        elif op == "Max": result = max(a)
        elif op == "Min": result = min(a)
        elif op == "Eq": result = int(a[0] == a[1])
        elif op == "Ne": result = int(a[0] != a[1])
        elif op == "Lt": result = int(a[0] < a[1])
        elif op == "Le": result = int(a[0] <= a[1])
        elif op == "Gt": result = int(a[0] > a[1])
        elif op == "Ge": result = int(a[0] >= a[1])
        elif op == "And": result = int(bool(a[0]) and bool(a[1]))
        elif op == "Or": result = int(bool(a[0]) or bool(a[1]))
        elif op == "Not": result = int(not a[0])
        elif op == "Ite": result = a[1] if a[0] else a[2]
        else: raise ValueError(f"Unimplemented operator: {op}")
        wires.append(result)
    return [wires[i] for i in block["outputs"]]


class RMNode:
    def __init__(self, artifact):
        self.artifact = artifact
        self.names = artifact["state"]
        self.__dict__.update(zip(self.names, evaluate(artifact["init"], [0] * len(self.names), [0] * 6)))

    def step(self, *inputs):
        output = evaluate(self.artifact["step"], [getattr(self, n) for n in self.names], inputs)
        self.__dict__.update(zip(self.names, output))


@dataclass(frozen=True)
class Envelope:
    sender: int
    recipient: int
    kind: int
    num: int
    value: int = 0
    prior_n: int = -1
    prior_v: int = 0

    def arguments(self):
        return (self.kind, self.sender, self.num, self.value, self.prior_n, self.prior_v)


class Network:
    def __init__(self, rm=False):
        artifact = json.loads((ROOT / "generated" / "rm.json").read_text()) if rm else None
        factory = (lambda: RMNode(artifact)) if rm else load_node()
        self.nodes = [factory() for _ in range(3)]
        self.pending = []
        self.inboxes = [deque() for _ in range(3)]
        self.outstanding = [0] * 3
        self.submitted = set()
        self.votes = {}
        self.declarations = []
        self.actions = []
        self.trace = []
        self.out_of_scope = False

    def dispatch(self, node_id, args):
        if not 0 <= node_id < 3:
            raise ValueError("Node outside the declared membership")
        node = self.nodes[node_id]
        if self.out_of_scope or node.status != 0:
            raise ValueError("Cannot step a halted or out-of-scope system")
        if (node.pc != 0) != (args[0] == 3):
            raise ValueError("Hook reentry or invalid resumption")
        if args[0] == 3 and self.outstanding[node_id]:
            raise ValueError("Cannot resume before the send has been enqueued remotely")
        before = [getattr(node, key) for key in MANIFEST["initial"]]
        node.step(*args)
        after = [getattr(node, key) for key in MANIFEST["initial"]]
        self.trace.append(dict(node=node_id, inputs=list(args), before=before, after=after))
        if args[0] == 1 and args[3] != 0:
            self.submitted.add(args[3])
        if node.status == 2:
            self.out_of_scope = True
            return
        if node.declared:
            self.declarations.append((node_id, node.declared_num, node.declared_value))
        if node.out_kind:
            recipients = range(3) if node.out_target == -1 else [node.out_target]
            for target in recipients:
                self.pending.append(Envelope(node_id, target, node.out_kind, node.out_num,
                                             node.out_value, node.out_prior_n, node.out_prior_v))
                self.outstanding[node_id] += 1
            if node.out_kind == KINDS["accepted"]:
                self.votes.setdefault((node.out_num, node.out_value), set()).add(node_id)
        total = len(self.pending) + sum(map(len, self.inboxes))
        if total > MANIFEST["queue_capacity"]:
            self.out_of_scope = True

    def act(self, action):
        self.actions.append(list(action))
        kind, *args = action
        if kind == "propose":
            node, value = args
            self.dispatch(node, (1, 0, 0, value, -1, 0))
        elif kind == "tick":
            self.dispatch(args[0], (2, 0, 0, 0, -1, 0))
        elif kind == "resume":
            self.dispatch(args[0], (3, 0, 0, 0, -1, 0))
        elif kind == "deliver":
            if not 0 <= args[0] < len(self.pending):
                raise ValueError("Invalid pending-message index")
            packet = self.pending.pop(args[0])
            self.inboxes[packet.recipient].append(packet)
            self.outstanding[packet.sender] -= 1
        elif kind == "receive":
            node = args[0]
            if not 0 <= node < 3 or not self.inboxes[node]:
                raise ValueError("Invalid receiver or empty inbox")
            self.dispatch(node, self.inboxes[node].popleft().arguments())
        elif kind == "idle":
            pass
        else:
            raise ValueError(action)

    def drain(self, max_actions=2000):
        for _ in range(max_actions):
            if self.out_of_scope:
                return
            if self.pending:
                self.act(("deliver", 0))
                continue
            ready = [i for i, n in enumerate(self.nodes) if n.status == 0 and n.pc and not self.outstanding[i]]
            if ready:
                self.act(("resume", ready[0]))
                continue
            ready = [i for i, n in enumerate(self.nodes) if n.status == 0 and not n.pc and self.inboxes[i]]
            if ready:
                self.act(("receive", ready[0]))
                continue
            return
        raise RuntimeError("Drain exceeded its explicit action limit")

    @property
    def chosen(self):
        return {v for (_, v), senders in self.votes.items() if len(senders) >= 2}

    def properties(self):
        return dict(agreement=len(self.chosen) <= 1,
                    validity=self.chosen <= self.submitted,
                    decision_accuracy=all(v in self.chosen for _, _, v in self.declarations),
                    decision_consistency=len({v for _, _, v in self.declarations}) <= 1,
                    choice_reached=bool(self.chosen),
                    all_nodes_declared=len({i for i, _, v in self.declarations if v in self.chosen}) == 3,
                    out_of_scope=self.out_of_scope)


def decode_node(node):
    """Recover algorithm-owned state, including dictionary presence and Counter order."""
    from collections import Counter
    numbers = range(MANIFEST["max_number"] + 1)
    counters = {}
    for n in numbers:
        if getattr(node, f"cand_has_{n}"):
            vals = sorted(range(1, len(VALUES)), key=lambda v: getattr(node, f"rank_{n}_{v}"))
            counters[n] = Counter({VALUES[v]: getattr(node, f"count_{n}_{v}") for v in vals
                                   if getattr(node, f"count_{n}_{v}") != 0})
    return dict(
                    num=node.num, promised_n=node.promised,
                    accepted_n=None if node.accepted_n == -1 else node.accepted_n,
                    accepted_value=VALUES[node.accepted], value=VALUES[node.own],
                    proposed_value={n: VALUES[getattr(node, f"pv_{n}")] for n in numbers if getattr(node, f"pv_has_{n}")},
                    promisers={n: {f"n{p+1}" for p in range(3) if getattr(node, f"prom_{n}_{p}")} for n in numbers if getattr(node, f"prom_has_{n}")},
                    acceptors={n: {f"n{p+1}" for p in range(3) if getattr(node, f"acc_{n}_{p}")} for n in numbers if getattr(node, f"acc_has_{n}")},
                    candidate_accepted=counters)
