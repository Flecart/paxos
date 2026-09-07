"""Bounded JSON messages over TCP; no consensus decisions or automatic retries."""

import asyncio
from dataclasses import dataclass
import json
import logging
import struct
from typing import Any

from .config import ClusterConfig

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Message:
    sender: str
    kind: str
    payload: dict[str, Any]


class DeliveryError(Exception):
    """Delivery failed or its outcome is unknown; the message may have arrived."""


class Transport:
    def __init__(self, node_id: str, config: ClusterConfig, bind_host: str | None = None):
        if node_id not in config.nodes:
            raise ValueError(f"unknown node ID: {node_id}")
        self.node_id = node_id
        self.config = config
        self.bind_host = bind_host or config.nodes[node_id].host
        self._inbox: asyncio.Queue[Message] = asyncio.Queue(config.inbox_size)
        self._server: asyncio.Server | None = None
        self._handlers: set[asyncio.Task] = set()

    @property
    def peers(self) -> tuple[str, ...]:
        """All configured node IDs, including this node."""
        return tuple(self.config.nodes)

    async def __aenter__(self) -> "Transport":
        await self.start()
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()

    async def start(self) -> None:
        if self._server is not None:
            raise RuntimeError("transport is already started")
        self._server = await asyncio.start_server(
            self._accept, self.bind_host, self.config.nodes[self.node_id].port
        )

    async def close(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        handlers = tuple(self._handlers)
        for task in handlers:
            task.cancel()
        await asyncio.gather(*handlers, return_exceptions=True)

    async def receive(self) -> Message:
        """Wait for the next message. Cancel the caller to stop waiting."""
        return await self._inbox.get()

    def _encode(self, kind: str, payload: dict[str, Any]) -> bytes:
        if not isinstance(kind, str) or not kind:
            raise ValueError("message kind must be a nonempty string")
        if not isinstance(payload, dict):
            raise ValueError("payload must be a JSON object")
        body = json.dumps(
            {"sender": self.node_id, "kind": kind, "payload": payload},
            allow_nan=False, separators=(",", ":"),
        ).encode("utf-8")
        if len(body) > self.config.max_message_bytes:
            raise ValueError("message exceeds max_message_bytes")
        return struct.pack("!I", len(body)) + body

    async def send(self, recipient: str, kind: str, payload: dict[str, Any]) -> None:
        """Return when queued remotely, not when processed by the algorithm.

        Unknown recipients and invalid local messages raise ValueError/TypeError.
        Connection errors and timeouts raise DeliveryError. Never retries.
        """
        if self._server is None:
            raise RuntimeError("start the transport before sending")
        if recipient not in self.config.nodes:
            raise ValueError(f"unknown recipient: {recipient}")
        packet = self._encode(kind, payload)
        peer = self.config.nodes[recipient]
        writer = None
        try:
            async with asyncio.timeout(self.config.timeout):
                reader, writer = await asyncio.open_connection(peer.host, peer.port)
                writer.write(packet)
                await writer.drain()
                if await reader.readexactly(1) != b"\x01":
                    raise DeliveryError(f"{recipient} rejected the message")
        except (OSError, TimeoutError, asyncio.IncompleteReadError) as exc:
            raise DeliveryError(f"delivery to {recipient} failed: {exc}") from exc
        finally:
            if writer is not None:
                writer.close()

    async def broadcast(
        self, kind: str, payload: dict[str, Any], *, include_self: bool = True
    ) -> dict[str, DeliveryError]:
        """Send concurrently; return failures keyed by node ID.

        Self delivery uses the same TCP/inbox path. Invalid messages still raise.
        """
        self._encode(kind, payload)
        recipients = [p for p in self.peers if include_self or p != self.node_id]

        async def attempt(recipient: str) -> DeliveryError | None:
            try:
                await self.send(recipient, kind, payload)
            except DeliveryError as exc:
                return exc
            return None

        results = await asyncio.gather(*(attempt(p) for p in recipients))
        return {p: error for p, error in zip(recipients, results) if error is not None}

    def _accept(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        task = asyncio.create_task(self._handle(reader, writer))
        self._handlers.add(task)
        task.add_done_callback(self._handlers.discard)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            async with asyncio.timeout(self.config.timeout):
                size = struct.unpack("!I", await reader.readexactly(4))[0]
                if not 0 < size <= self.config.max_message_bytes:
                    raise ValueError("invalid frame size")
                body = await reader.readexactly(size)
                envelope = json.loads(body, parse_constant=self._reject_constant)
                if not isinstance(envelope, dict):
                    raise ValueError("envelope must be an object")
                sender = envelope.get("sender")
                kind = envelope.get("kind")
                payload = envelope.get("payload")
                if not isinstance(sender, str) or sender not in self.config.nodes:
                    raise ValueError("unknown sender")
                if not isinstance(kind, str) or not kind or not isinstance(payload, dict):
                    raise ValueError("invalid kind or payload")
                self._inbox.put_nowait(Message(sender, kind, payload))
                writer.write(b"\x01")
                await writer.drain()
        except (ValueError, RecursionError, OSError, TimeoutError,
                asyncio.IncompleteReadError, asyncio.QueueFull) as exc:
            log.debug("rejected incoming connection: %s", exc)
        finally:
            writer.close()

    @staticmethod
    def _reject_constant(value: str) -> None:
        raise ValueError(f"non-JSON number: {value}")
