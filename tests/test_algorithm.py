"""Behavioral checks for the learning implementation, not a Paxos solution.

Run: uv run python -m unittest discover -s tests -p test_algorithm.py -v

These checks assert the expected observable properties. Failures are deliberate
regression targets, not expectedFailure tests. The transport below only queues
messages; all protocol behavior comes from the real PaxosNode implementation.
"""

from collections import deque
from contextlib import redirect_stdout
import io
import unittest

from paxos_lab.algorithm import PaxosNode
from paxos_lab.transport import Message


class QueuedTransport:
    peers = ("n1", "n2", "n3")

    def __init__(self, node_id, network):
        self.node_id = node_id
        self.network = network

    async def send(self, recipient, kind, payload):
        message = Message(self.node_id, kind, dict(payload))
        self.network.pending.append((recipient, message))
        self.network.sent.append((recipient, message))

    async def broadcast(self, kind, payload, *, include_self=True):
        for recipient in self.peers:
            if include_self or recipient != self.node_id:
                await self.send(recipient, kind, payload)
        return {}


class Network:
    def __init__(self):
        self.pending = deque()
        self.sent = []
        self.nodes = {
            name: PaxosNode(QueuedTransport(name, self))
            for name in QueuedTransport.peers
        }

    async def deliver(self, batch):
        for recipient, message in batch:
            await self.nodes[recipient].on_message(message)

    async def drain(self):
        for _ in range(1000):
            if not self.pending:
                return
            await self.deliver([self.pending.popleft()])
        raise AssertionError("More than 1000 deliveries without reaching an idle network")


class AlgorithmChecks(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.output = io.StringIO()
        capture = redirect_stdout(self.output)
        capture.__enter__()
        self.addCleanup(capture.__exit__, None, None, None)
        self.network = Network()

    async def test_single_proposer_with_prompt_delivery(self):
        await self.network.nodes["n1"].propose("A")
        await self.network.drain()
        self.assert_only_one_value_has_acceptance_majorities(require_choice=True)

    def assert_only_one_value_has_acceptance_majorities(self, *, require_choice=False):
        # Observe actual acceptance replies, independently of local decision logs.
        votes = {}
        for _, message in self.network.sent:
            if message.kind == "accepted":
                key = (message.payload["num"], message.payload["value"])
                votes.setdefault(key, set()).add(message.sender)
        chosen = {
            value for (_, value), senders in votes.items()
            if len(senders) > len(QueuedTransport.peers) // 2
        }
        self.assertLessEqual(len(chosen), 1, f"Different values obtained majorities: {votes}")
        if require_choice:
            self.assertTrue(chosen, f"Scenario did not reach a first chosen value; acceptance replies: {votes}")

    async def test_chosen_value_survives_a_later_proposal(self):
        await self.network.nodes["n1"].propose("A")
        await self.network.drain()
        self.assert_only_one_value_has_acceptance_majorities(require_choice=True)
        await self.network.nodes["n2"].propose("B")
        await self.network.drain()
        self.assert_only_one_value_has_acceptance_majorities()

    async def test_delayed_acceptance_replies_do_not_allow_two_chosen_values(self):
        delayed = []

        async def deliver_except_acceptance_replies():
            for _ in range(1000):
                if not self.network.pending:
                    return
                recipient, message = self.network.pending.popleft()
                if message.kind == "accepted":
                    delayed.append((recipient, message))
                else:
                    await self.network.deliver([(recipient, message)])
            self.fail("Network failed to become idle within 1000 deliveries")

        await self.network.nodes["n1"].propose("A")
        await deliver_except_acceptance_replies()
        self.assert_only_one_value_has_acceptance_majorities(require_choice=True)
        await self.network.nodes["n2"].propose("B")
        await deliver_except_acceptance_replies()
        # Release all delayed replies: this schedule loses no messages.
        await self.network.deliver(delayed)
        await self.network.drain()
        self.assert_only_one_value_has_acceptance_majorities()

    async def test_retries_with_one_tick_message_delay(self):
        await self.network.nodes["n1"].propose("A")
        for _ in range(20):
            # Every message is delivered on the following simulated tick.
            # No loss, duplicate messages, unavailable peers, or wall-clock sleeps.
            batch = list(self.network.pending)
            self.network.pending.clear()
            for node in self.network.nodes.values():
                await node.on_tick()
            await self.network.deliver(batch)
        promises = [m for _, m in self.network.sent if m.kind == "promise"]
        self.assertTrue(
            promises,
            "20 ticks with reliable one-tick delivery produced zero promises",
        )

    async def test_concurrent_proposals_do_not_choose_different_values(self):
        await self.network.nodes["n1"].propose("A")
        await self.network.nodes["n2"].propose("B")
        batch = list(self.network.pending)
        self.network.pending.clear()
        # n2 sees B first; n1 and n3 see A first. All messages are delivered.
        batch.sort(key=lambda item: not (item[0] == "n2" and item[1].sender == "n2"))
        await self.network.deliver(batch)
        await self.network.drain()
        self.assert_only_one_value_has_acceptance_majorities()

    async def test_promises_from_different_numbers_do_not_form_a_majority(self):
        node = self.network.nodes["n1"]
        await node.propose("A")
        for sender, num in (("n2", 1), ("n3", 2)):
            await node.on_message(Message(sender, "promise", {
                "num": num, "value": {
                    "num": num, "accepted_n": None, "accepted_value": None,
                },
            }))
        accepts = [m for _, m in self.network.sent if m.kind == "accept"]
        self.assertFalse(
            accepts,
            "One promise for number 1 and one for number 2 triggered accept broadcasts",
        )

    async def test_conflicting_acceptance_reports_do_not_form_a_majority(self):
        node = self.network.nodes["n1"]
        await node.propose("A")
        await node.on_message(Message("n2", "accepted", {"num": 1, "value": "A"}))
        await node.on_message(Message("n3", "accepted", {"num": 2, "value": "B"}))
        self.assertNotIn(
            "accepted by majority", self.output.getvalue(),
            "Acceptance of A at number 1 and B at number 2 was reported as a majority",
        )


if __name__ == "__main__":
    unittest.main()
