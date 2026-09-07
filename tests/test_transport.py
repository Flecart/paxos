import asyncio
from contextlib import AsyncExitStack
import json
from pathlib import Path
import struct
import tempfile
import unittest

from paxos_lab.config import ClusterConfig, Peer
from paxos_lab.transport import DeliveryError, Transport


class ConfigTests(unittest.TestCase):
    def test_examples(self):
        for name in ("local", "vpn"):
            config = ClusterConfig.load(Path(__file__).resolve().parents[1] / "config" / f"{name}.toml")
            self.assertEqual(tuple(config.nodes), ("n1", "n2", "n3"))

    def test_invalid_config(self):
        cases = ["", '[nodes.n1]\nhost="x"\nport=true',
                 '[nodes.n1]\nhost="x"\nport=0',
                 '[network]\ntimeout=nan\n[nodes.n1]\nhost="x"\nport=12',
                 '[network]\ninbox_size=0\n[nodes.n1]\nhost="x"\nport=12',
                 '[nodes.n1]\nhost="x"\nport=12\n[nodes.n2]\nhost="x"\nport=12']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cluster.toml"
            for content in cases:
                with self.subTest(content=content):
                    path.write_text(content)
                    with self.assertRaises(ValueError):
                        ClusterConfig.load(path)


class TransportTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # OS-assigned ports avoid collisions. Patch endpoints after listeners bind.
        self.config = ClusterConfig(
            nodes={f"n{i}": Peer("127.0.0.1", 0) for i in range(1, 4)},
            timeout=0.5, max_message_bytes=4096, inbox_size=4,
        )
        self.stack = AsyncExitStack()
        self.addAsyncCleanup(self.stack.aclose)
        self.nodes = {}
        for node_id in self.config.nodes:
            transport = await self.stack.enter_async_context(Transport(node_id, self.config))
            port = transport._server.sockets[0].getsockname()[1]
            self.config.nodes[node_id] = Peer("127.0.0.1", port)
            self.nodes[node_id] = transport

    async def receive(self, node_id):
        return await asyncio.wait_for(self.nodes[node_id].receive(), 1)

    async def test_send_and_self_delivery(self):
        payload = {"text": "ciao 🌍", "nested": [1, True, None]}
        for target in ("n1", "n2"):
            await self.nodes["n1"].send(target, "example", payload)
            message = await self.receive(target)
            self.assertEqual((message.sender, message.kind, message.payload),
                             ("n1", "example", payload))
            self.assertIsNot(message.payload, payload)

    async def test_broadcast_partial_failure(self):
        await self.nodes["n3"].close()
        failures = await self.nodes["n1"].broadcast("example", {})
        self.assertEqual(set(failures), {"n3"})
        for node_id in ("n1", "n2"):
            self.assertEqual((await self.receive(node_id)).kind, "example")

    async def test_broadcast_excludes_self(self):
        self.assertEqual(await self.nodes["n1"].broadcast("example", {}, include_self=False), {})
        for node_id in ("n2", "n3"):
            await self.receive(node_id)
        self.assertTrue(self.nodes["n1"]._inbox.empty())

    async def test_local_validation(self):
        for target, kind, payload in [("missing", "x", {}), ("n2", "", {}),
                                      ("n2", "x", []), ("n2", "x", {"x": float("nan")}),
                                      ("n2", "x", {"x": "a" * 5000})]:
            with self.subTest(target=target, kind=kind), self.assertRaises(ValueError):
                await self.nodes["n1"].send(target, kind, payload)

    async def test_full_inbox_rejects_without_hanging(self):
        for i in range(4):
            await self.nodes["n1"].send("n2", "example", {"i": i})
        with self.assertRaises(DeliveryError):
            await self.nodes["n1"].send("n2", "example", {})
        await self.receive("n2")
        await self.nodes["n1"].send("n2", "example", {})

    async def test_malformed_frames_do_not_break_listener(self):
        peer = self.config.nodes["n2"]
        bodies = [b"not json", b"[]", b'{"sender":[]}',
                  json.dumps({"sender": "unknown", "kind": "x", "payload": {}}).encode()]
        packets = [struct.pack("!I", len(body)) + body for body in bodies]
        packets += [struct.pack("!I", 5000)]
        for packet in packets:
            reader, writer = await asyncio.open_connection(peer.host, peer.port)
            writer.write(packet)
            await writer.drain()
            self.assertEqual(await asyncio.wait_for(reader.read(), 1), b"")
            writer.close()
            await writer.wait_closed()
        await self.nodes["n1"].send("n2", "still-alive", {})
        self.assertEqual((await self.receive("n2")).kind, "still-alive")

    async def test_slow_connection_times_out(self):
        peer = self.config.nodes["n2"]
        reader, writer = await asyncio.open_connection(peer.host, peer.port)
        writer.write(b"\x00")
        await writer.drain()
        self.assertEqual(await asyncio.wait_for(reader.read(), 2), b"")
        writer.close()
        await writer.wait_closed()

    async def test_shutdown_closes_incomplete_connections(self):
        peer = self.config.nodes["n2"]
        reader, writer = await asyncio.open_connection(peer.host, peer.port)
        await self.nodes["n2"].close()
        self.assertEqual(await asyncio.wait_for(reader.read(), 1), b"")
        writer.close()
        await writer.wait_closed()
        self.assertFalse(self.nodes["n2"]._handlers)


if __name__ == "__main__":
    unittest.main()
