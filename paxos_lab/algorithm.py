"""Your implementation goes here. No Paxos protocol is implemented yet."""

import asyncio
from typing import Any
from unittest import case
import backoff

from .transport import Message, Transport, DeliveryError


class PaxosNode:
    def __init__(self, transport: Transport):
        self.transport = transport
        self.node_id = transport.node_id
        self.members = transport.peers
        # TODO: define your algorithm's state here.
        
        # max number atm received.
        self.num: int = 0
        self.proposed_value: dict[int, Any] = {}
        self.accepted_value: int | None = None
        self.node_knows = set()
        self.value: Any = None
        self.num_promises: int = 0
        self.lock = asyncio.Lock()
        self.acceptors: dict[int, set[str]] = {}
        self.promisers: dict[int, set[str]] = {}

    @backoff.on_exception(backoff.expo, DeliveryError, max_tries=5)
    async def propose(self, value: Any) -> None:
        """Called for the optional --value argument."""
        
        if value is None:
            return
        
        async with self.lock:
            self.num_promises = 0
            self.proposed_value[self.num + 1] = value
            self.value = value
        failures = await self.transport.broadcast(
            "propose",
            {"value": value,
             "num": self.num + 1},
            include_self=True,
        )
        if failures:
            raise DeliveryError(f"failed to deliver propose message to {failures}")

        print(f"propose {value} with num {self.num} to {self.members}, failures: {failures}")
        
    @backoff.on_exception(backoff.expo, DeliveryError, max_tries=5)
    async def on_message(self, message: Message) -> None:
        """Inspect message.sender, message.kind, and message.payload."""
        # TODO: implement your protocol's message handling.
        sender = message.sender
        kind: str = message.kind
        payload = message.payload
        num = payload.get("num", -1)
        if num < self.num:
            print(f"ignore {kind} from {sender} with num {num}, current num is {self.num}")
            await self.transport.send(sender, "reject", {"num": self.num})
            return
        
        failures = None
        
        # now we should switch all the types I guess.
        async with self.lock:
            if kind == "propose":
                if num > self.num:
                    self.num = num
                    self.proposed_value[self.num] = payload.get("value", None)
                    failures = await self.transport.broadcast(
                        "promise",
                        {"num": self.num, "value": self.proposed_value[self.num]},
                        include_self=True,
                    )
                # do nothing if num = num, we give precedence to the node that proposed first.
                
            elif kind == "reject":
                self.num = max(self.num, num)
            elif kind == "accept":
                self.num = max(self.num, num)
                proposed_value = payload.get("value", None)
                if self.proposed_value.get(self.num) == proposed_value:
                    if self.accepted_value is None or self.accepted_value == proposed_value:
                        print(f"accepting value {proposed_value} from {sender} with num {num}")
                        # self.accepted_value[self.num] = proposed_value
                        self.accepted_value = proposed_value
                        failures = await self.transport.send(sender, "accepted", {"num": self.num, "value": self.proposed_value[self.num]})
                    else:
                        print(f"rejecting value {proposed_value} from {sender} with num {num}, already accepted {self.accepted_value}")
                        failures = await self.transport.send(sender, "reject", {"num": self.num})
                else:
                    print(f"conflicting values: {self.proposed_value} vs {payload.get('value', None)}")
                    await self.transport.send(sender, "reject", {"num": self.num})
            elif kind == "promise":
                self.num = max(self.num, num)
                self.num_promises += 1
                if self.num not in self.promisers:
                    self.promisers[self.num] = set()
                self.promisers[self.num].add(sender)
                if len(self.promisers[self.num]) > len(self.members) // 2:
                    # we have a majority of promises, so we can send accept messages
                    failures = await self.transport.broadcast(
                        "accept",
                        {"num": self.num, "value": self.proposed_value[self.num]},
                        include_self=True,
                    )

            elif kind == "accepted":
                self.num = max(self.num, num)
                if self.num not in self.acceptors:
                    self.acceptors[self.num] = set()
                self.acceptors[self.num].add(sender)
                if len(self.acceptors[self.num]) > len(self.members) // 2 and self.accepted_value is None:
                    print(f"value {self.proposed_value[self.num]} accepted by majority, num {self.num}")
                    self.accepted_value = payload.get("value", None)
            elif kind == "learn":
                self.num = max(self.num, num)
                self.accepted_value = payload.get("value", None)
                failures = await self.transport.send(sender, "ack", {"num": self.num, "value": self.accepted_value})
            elif kind == "ack":
                self.num = max(self.num, num)
                self.node_knows.add(sender)
            else:
                print(f"unknown message kind {kind} from {sender} with num {num}")
                return

        if failures is not None and failures:
            print(f"failures in handling {kind} from {sender} with num {num}: {failures}")
            raise DeliveryError(f"failed to deliver {kind} message to {failures}")
        
        return

    @backoff.on_exception(backoff.expo, DeliveryError, max_tries=5)
    async def on_tick(self) -> None:
        """Called periodically; you choose whether/how to use timers."""
        # TODO: optional algorithm timers/retries.
        
        if self.num // 2 and self.accepted_value is None:
            await self.propose(self.value)
        if self.num // 10 and self.accepted_value is not None:
            # broadcast learn message to all nodes
            for peer in self.members:
                if peer not in self.node_knows:
                    failures = await self.transport.send(peer, "learn", {"num": self.num, "value": self.accepted_value})
                    if failures:
                        print(f"failures in broadcasting learn message: {failures}")
                        raise DeliveryError(f"failed to deliver learn message to {failures}")
            
        async with self.lock:
            self.num += 1