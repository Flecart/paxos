"""Your implementation goes here. No Paxos protocol is implemented yet."""

from typing import Any

from .transport import Message, Transport


class PaxosNode:
    def __init__(self, transport: Transport):
        self.transport = transport
        self.node_id = transport.node_id
        self.members = transport.peers
        # TODO: define your algorithm's state here.

    async def propose(self, value: Any) -> None:
        """Called for the optional --value argument."""
        # TODO: implement your proposal entry point.
        pass

    async def on_message(self, message: Message) -> None:
        """Inspect message.sender, message.kind, and message.payload."""
        # TODO: implement your protocol's message handling.
        pass

    async def on_tick(self) -> None:
        """Called periodically; you choose whether/how to use timers."""
        # TODO: optional algorithm timers/retries.
        pass
