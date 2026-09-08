"""Differential checks: original coroutines -> flattened Python -> actual RM."""
import asyncio
from contextlib import redirect_stdout
import copy
import io
import hashlib
import json
from pathlib import Path
import random
import sys

from runtime import Network, MANIFEST, VALUES, KINDS, REVERSE_KINDS, decode_node

ROOT = Path(__file__).resolve().parent
SCENARIOS = ("single", "later", "integer", "concurrent", "ticks", "key_error", "interleaved")
sys.path.insert(0, str(ROOT.parent))
from paxos_lab.algorithm import PaxosNode
from paxos_lab.transport import Message


class Capture:
    peers = ("n1", "n2", "n3")

    def __init__(self, node_id):
        self.node_id = f"n{node_id+1}"
        self.sent = None
        self.waiter = None

    async def send(self, recipient, kind, payload):
        self.sent = (int(recipient[1:]) - 1, kind, copy.deepcopy(payload))
        self.waiter = asyncio.get_running_loop().create_future()
        await self.waiter

    async def broadcast(self, kind, payload, include_self=True):
        assert include_self
        self.sent = (-1, kind, copy.deepcopy(payload))
        self.waiter = asyncio.get_running_loop().create_future()
        await self.waiter
        return {}


def payload(args):
    event, sender, number, value, prior_n, prior_v = args
    if event == KINDS["promise"]:
        return {"num": number, "value": {"num": number,
                "accepted_n": None if prior_n == -1 else prior_n,
                "accepted_value": VALUES[prior_v]}}
    if event in (KINDS["accept"], KINDS["accepted"]):
        return {"num": number, "value": VALUES[value]}
    return {"num": number}


async def compare_original(trace):
    transports = [Capture(i) for i in range(3)]
    nodes = [PaxosNode(t) for t in transports]
    tasks = [None] * 3
    try:
        for index, row in enumerate(trace):
            node_id = row["node"]
            args = row["inputs"]
            event = args[0]
            node, transport = nodes[node_id], transports[node_id]
            transport.sent = None
            if event == 3:
                transport.waiter.set_result(None)
            else:
                assert tasks[node_id] is None or tasks[node_id].done()
                if event == 1:
                    coro = node.propose(VALUES[args[3]])
                elif event == 2:
                    coro = node.on_tick()
                else:
                    coro = node.on_message(Message(f"n{args[1]+1}", REVERSE_KINDS[event], payload(args)))
                tasks[node_id] = asyncio.create_task(coro)
            printed = io.StringIO()
            with redirect_stdout(printed):
                await asyncio.sleep(0)
            state = type("Snapshot", (), dict(zip(MANIFEST["initial"], row["after"])))()
            expected = decode_node(state)
            decisions = [line for line in printed.getvalue().splitlines() if " accepted by majority, num " in line]
            expected_decisions = ([f"value {VALUES[state.declared_value]} accepted by majority, num {state.declared_num}"]
                                  if state.declared else [])
            assert decisions == expected_decisions, (decisions, expected_decisions)
            actual = {key: getattr(node, key) for key in expected}
            assert actual == expected, f"Original/Python divergence at local step {index}, {args}: " + str({k: (actual[k], expected[k]) for k in actual if actual[k] != expected[k]})
            # Counter equality ignores insertion order; check it separately.
            assert {n: list(c.items()) for n,c in actual["candidate_accepted"].items()} == {n: list(c.items()) for n,c in expected["candidate_accepted"].items()}
            exception = tasks[node_id].exception() if tasks[node_id].done() else None
            expected_exception = {1: KeyError, 2: IndexError}.get(state.fault)
            if state.status == 1:
                assert type(exception) is expected_exception, (exception, state.fault)
            else:
                assert exception is None, repr(exception)
            if state.out_kind:
                out_args = (state.out_kind, node_id, state.out_num, state.out_value, state.out_prior_n, state.out_prior_v)
                assert transport.sent == (state.out_target, REVERSE_KINDS[state.out_kind], payload(out_args)), (transport.sent, out_args)
            else:
                assert transport.sent is None
    finally:
        for task in tasks:
            if task is not None and not task.done():
                task.cancel()
        await asyncio.gather(*(t for t in tasks if t is not None), return_exceptions=True)


def scenario(name):
    n = Network()
    if name == "single":
        n.act(("propose", 0, 1))
        n.drain()
    elif name == "later":
        n.act(("propose", 0, 1))
        n.drain()
        n.act(("propose", 1, 2))
        n.drain()
    elif name == "integer":
        n.act(("propose", 0, 4))
        n.drain()
        n.act(("propose", 1, 5))
        n.drain()
    elif name == "key_error":
        n.act(("propose", 0, 5))
        n.drain()
        n.act(("propose", 1, 1))
        n.drain()
        n.act(("propose", 1, 1))
        n.drain()
    elif name == "concurrent":
        n.act(("propose", 0, 1))
        n.act(("propose", 1, 2))
        n.drain()
    elif name == "interleaved":
        n.act(("propose", 0, 1))
        n.act(("propose", 1, 2))
        rng = random.Random(20260908)
        for _ in range(500):
            ready = [("deliver", i) for i in range(len(n.pending))]
            ready += [("resume", i) for i, node in enumerate(n.nodes)
                      if node.status == 0 and node.pc and not n.outstanding[i]]
            ready += [("receive", i) for i, node in enumerate(n.nodes)
                      if node.status == 0 and not node.pc and n.inboxes[i]]
            if not ready or n.out_of_scope:
                break
            n.act(rng.choice(ready))
    elif name == "ticks":
        n.act(("propose", 0, 1))
        n.drain()
        for _ in range(22):
            for i in range(3):
                n.act(("tick", i))
            n.drain()
    else:
        raise ValueError(name)
    return n


def replay_rm(reference):
    rm = Network(rm=True)
    for action in reference.actions:
        rm.act(action)
    assert rm.trace == reference.trace, "Python/RM state or output divergence"
    assert rm.properties() == reference.properties()


async def check():
    actual_hash = hashlib.sha256((ROOT.parent / "paxos_lab" / "algorithm.py").read_bytes()).hexdigest()
    assert actual_hash == MANIFEST["source_sha256"], "Source changed; review and regenerate the translation"
    artifact = json.loads((ROOT / "generated" / "rm.json").read_text())
    assert artifact["python_sha256"] == hashlib.sha256((ROOT / "generated" / "node.py").read_bytes()).hexdigest(), "RM artifact is stale; run compile_rm.py"
    results = {}
    for name in SCENARIOS:
        n = scenario(name)
        assert not n.out_of_scope, name
        with redirect_stdout(io.StringIO()):
            await compare_original(n.trace)
        replay_rm(n)
        results[name] = dict(local_steps=len(n.trace), properties=n.properties(),
                             node_status=[x.status for x in n.nodes])
        (ROOT / "generated" / f"trace_{name}.json").write_text(json.dumps(dict(
            rm_sha256=hashlib.sha256((ROOT / "generated" / "rm.json").read_bytes()).hexdigest(),
            actions=n.actions, steps=n.trace, properties=n.properties()), separators=(",", ":")) + "\n")
        print(f"{name}: {len(n.trace)} local steps matched original/Python/RM; {n.properties()}")
    (ROOT / "generated" / "checks.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    asyncio.run(check())
