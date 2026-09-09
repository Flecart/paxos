"""Compile unchanged algorithm.py directly and compare against its real coroutines.

No Paxos lowering/generate.py or fixed algorithm hash. Transport is an explicit
request/reply interface; failed correctness is not failed translation.
"""
from __future__ import annotations

import argparse
import copy
from collections import Counter
from contextlib import redirect_stdout
from dataclasses import dataclass
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from paxos_lab.algorithm import PaxosNode
from paxos_lab.transport import Message, DeliveryError
from zrth.native_runtime import Object, Pending, Finished, Failed, InterfaceError
from zrth.verified_native import compile_native
from zrth.native_checks import Recorder


@dataclass
class Packet:
    method: str
    args: tuple
    keywords: dict

    def __await__(self):
        return (yield self)


class Port:
    node_id = "n1"
    peers = ("n1", "n2", "n3")

    async def send(self, *args, **keywords):
        return await Packet("send", args, keywords)

    async def broadcast(self, *args, **keywords):
        return await Packet("broadcast", args, keywords)


async def delay(seconds):
    return await Packet("sleep", (seconds,), {})


def canonical(value):
    if isinstance(value, Object): return ["record", canonical(value.fields)]
    if type(value) in (type(None), bool, int, str): return [type(value).__name__, value]
    if isinstance(value, dict): return [type(value).__name__, [[canonical(k), canonical(v)] for k,v in value.items()]]
    if isinstance(value, set): return ["set", sorted((canonical(v) for v in value), key=repr)]
    if isinstance(value, (tuple, list)): return [type(value).__name__, [canonical(v) for v in value]]
    if isinstance(value, Exception): return ["error", type(value).__name__, list(value.args)]
    raise TypeError(type(value))


def state(node):
    fields = node.fields if isinstance(node, Object) else vars(node)
    return canonical({k:v for k,v in fields.items() if k != "transport"})


def advance(coroutine, value=None, error=None):
    output = io.StringIO()
    with redirect_stdout(output):
        try:
            result = coroutine.throw(error) if error is not None else coroutine.send(value)
        except StopIteration as end: result = Finished(end.value)
        except Exception as failure: result = Failed(failure)
    return result, output.getvalue()


def compare_call(bundle, original, compiled, method, args, replies=(), recorder=None):
    source_args = copy.deepcopy(args)
    target_args = copy.deepcopy(args)
    if method == "on_message":
        source_args = (Message(*source_args[0]),)
        sender, kind, payload = target_args[0]
        target_args = (Object(".transport.Message", dict(sender=sender, kind=kind, payload=payload)),)
    task = bundle.task("PaxosNode." + method, compiled, *target_args)
    if recorder is not None: recorder.attach(task)
    coroutine = getattr(original, method)(*source_args)
    transcript = []
    try:
        with patch("backoff._async.asyncio.sleep", delay):
            source, printed = advance(coroutine)
            target = task.run(fuel=100000)
            logs = 0
            response_index = 0
            for _ in range(1000):
                assert target is not None, "execution budget exhausted; no successful-result claim"
                emitted = "".join(event[1] for event in task.events if event[0] == "print")
                assert printed == emitted[logs:], (method, "print mismatch", printed, emitted[logs:])
                logs = len(emitted)
                assert state(original) == state(compiled), (method, "state mismatch", state(original), state(compiled))
                if isinstance(source, Finished):
                    assert isinstance(target, Finished) and canonical(source.value) == canonical(target.value)
                    transcript.append({"return": canonical(source.value)})
                    return transcript
                if isinstance(source, Failed):
                    assert isinstance(target, Failed), (source, target)
                    name = target.error.name.rsplit(".",1)[-1] if isinstance(target.error, InterfaceError) else type(target.error).__name__
                    assert type(source.error).__name__ == name, (source, target)
                    if isinstance(source.error, (KeyError, DeliveryError)):
                        assert source.error.args == target.error.args, (source, target)
                    transcript.append({"error": name, "args": repr(source.error.args)})
                    return transcript
                assert isinstance(source, Packet) and isinstance(target, Pending), (source, target)
                assert source.method == target.interface.rsplit(".",1)[-1]
                if source.method == "sleep":
                    assert 0 <= source.args[0] <= target.args[1], (source.args, target.args)
                    reply, failure = None, False
                else:
                    assert canonical(source.args) == canonical(target.args), (source, target)
                    assert source.keywords == target.keywords
                    selected = replies[response_index] if response_index < len(replies) else ({} if source.method == "broadcast" else None)
                    response_index += 1
                    failure = selected == "delivery-error"
                    reply = None if failure else ({"n2": DeliveryError("returned failure")} if selected == "delivery-map" else selected)
                transcript.append({"request": source.method, "args": repr(target.args), "failed_reply": failure})
                source, printed = advance(coroutine, copy.deepcopy(reply), DeliveryError("injected") if failure else None)
                target_reply = copy.deepcopy(reply)
                if isinstance(target_reply, dict):
                    target_reply = {key: InterfaceError(".transport.DeliveryError", *value.args)
                                    if isinstance(value, DeliveryError) else value
                                    for key, value in target_reply.items()}
                target = task.resume(target, target_reply, InterfaceError(".transport.DeliveryError", "injected") if failure else None)
            raise AssertionError("trace budget exhausted; no successful-result claim")
    finally:
        coroutine.close()


def comparisons(bundle, recorder=None):
    reports = []
    cases = [
        ({}, [("propose", (None,), ()), ("propose", ("A",), ()), ("propose", ("B",), ()), ("on_tick", (), ())]),
        ({}, [("on_message", (("n2", kind, {"num": num, "value": value}),), ())
              for kind, num, value in [("propose",1,None),("propose",1,None),("reject",3,None),
                                      ("accept",4,"A"),("accept",5,"B"),("unknown",5,None),("propose",1,None)]]),
        ({"value":"A"}, [("on_message", ((peer,"promise",{"num":1,"value":{"accepted_n":0,"accepted_value":"A"}}),), ())
                          for peer in ("n1","n2","n3")]),
        ({"value":"A"}, [("on_message", (("n1","promise",{"num":1,"value":{"accepted_value":1}}),), ()),
                         ("on_message", (("n2","promise",{"num":2,"value":{"accepted_value":1}}),), ())]),
        ({"num":20,"value":"A"}, [("on_tick", (), ("delivery-error",)*25)]),
        ({}, [("propose", ("A",), ("delivery-error", "delivery-error", {}))]),
        ({}, [("on_message", (("n1","accepted",{"num":1,"value":"A"}),), ()),
              ("on_message", (("n2","accepted",{"num":1,"value":"A"}),), ())]),
        ({}, [("propose", ("A",), ("delivery-map", {}))]),
        ({"value":"A", "promisers": {1: {"n1"}}},
         [("on_message", (("n2", "promise", {"num":1, "value":{}}),), ("delivery-map", {}))]),
        ({"value":"A", "promisers": {1: {"n1"}}, "candidate_accepted": {1: Counter()}},
         [("on_message", (("n2", "promise", {"num":1, "value":{}}),), ())]),
        ({"num":3}, [("on_message", (("n2", "propose", {"num":1}),), ("delivery-error", None))]),
    ]
    for value in (None, True, False, -2**100, 2**100, "value", [], {"x":1}):
        cases.append(({}, [("on_message", (("n2","promise",{"num":0,"value":{"accepted_value":value}}),), ())]))
    for index, (initial, calls) in enumerate(cases):
        original = PaxosNode(Port())
        port = Object(".transport.Transport", dict(node_id="n1", peers=Port.peers))
        compiled = Object("PaxosNode")
        init = bundle.task("PaxosNode.__init__", compiled, port)
        if recorder is not None: recorder.attach(init)
        assert isinstance(init.run(), Finished)
        for name, value in initial.items():
            setattr(original, name, copy.deepcopy(value)); compiled.fields[name] = copy.deepcopy(value)
        assert state(original) == state(compiled)
        trace = []
        for method, args, replies in calls:
            trace += compare_call(bundle, original, compiled, method, args, replies, recorder)
        reports.append(dict(case=index, trace=trace))
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-lean", action="store_true")
    parser.add_argument("--out", type=Path, default=ROOT / "native-evidence")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "check-status.json").write_text(json.dumps({"run":"not-established"})+"\n")
    config = json.loads((ROOT / "native.json").read_text())
    bundle = compile_native(ROOT.parent / "paxos_lab/algorithm.py", config)
    bundle.write(args.out)
    recorder = Recorder(per_signature=1)
    reports = comparisons(bundle, recorder)
    print(f"Source compiled: {len(bundle.artifact['native_program']['instructions'])} instructions; "
          f"{len(reports)} original-Python/RM comparisons passed.", flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "python-comparisons.json").write_text(json.dumps(reports, indent=2) + "\n")
    if not args.skip_lean:
        print("Checking the translation certificate in Lean...", flush=True)
        bundle.certify(args.out)
        print(f"Kernel-replaying {len(recorder.samples)} instruction/reply samples...", flush=True)
        recorder.check(bundle, args.out)
    (args.out / "check-status.json").write_text(json.dumps(dict(run="checked" if not args.skip_lean else "python-comparisons-only",
        source_sha256=bundle.artifact["source_sha256"], scenarios=len(reports),
        instruction_and_reply_samples=len(recorder.samples), algorithm_correctness="not-asserted"), indent=2)+"\n")
    print(f"Unchanged algorithm.py: {len(bundle.artifact['native_program']['instructions'])} instructions, "
          f"{len(reports)} original-Python/RM comparison scenarios passed.")
    print("Translation: " + ("not checked (--skip-lean)" if args.skip_lean else "Lean checked; algorithm correctness not asserted"))


if __name__ == "__main__": main()
