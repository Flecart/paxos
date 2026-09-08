"""Your implementation goes here. No Paxos protocol is implemented yet."""

import asyncio
from typing import Any
from unittest import case
import backoff

from .transport import Message, Transport, DeliveryError
from collections import Counter

class PaxosNode:
    def __init__(self, transport: Transport):
        self.transport = transport
        self.node_id = transport.node_id
        self.members = transport.peers
        # TODO: define your algorithm's state here.
        
        # max number atm received.
        self.num = 0
        self.promised_n: int = -1
        self.accepted_n: int | None = None
        self.accepted_value: Any = None
        
        self.promisers: dict[int, set[str]] = {}
        self.candidate_accepted: dict[int, Counter] = dict()
        self.acceptors: dict[int, set[str]] = {}
        self.proposed_value: dict[int, Any] = {}
        self.value = None
        
    @backoff.on_exception(backoff.expo, DeliveryError, max_tries=5)
    async def propose(self, value: Any) -> None:
        """Called for the optional --value argument."""
        
        if value is None:
            return
        if self.value is not None and self.value != value:
            print(f"already proposed value {self.value}, ignoring new proposal {value}")
            return

        self.value = value
        
        failures = await self.transport.broadcast("propose", {"num": self.num + 1}, include_self=True)
        self.num += 1
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
        if kind == "propose":
            self.num = max(self.num, num)
            if num > self.promised_n:
                self.promised_n = num
                failures = await self.transport.send(
                    sender,
                    "promise",
                    {"num": self.promised_n, "value": {
                        "num": self.promised_n,
                        "accepted_n": self.accepted_n,
                        "accepted_value": self.accepted_value,
                    }},
                )
            else:
                failures = await self.transport.send(sender, "reject", {"num": self.num})
        elif kind == "reject":
            self.num = max(self.num, num)
        elif kind == "accept":
            self.num = max(self.num, num)
            proposed_value = payload.get("value", None)
            if self.accepted_value is None or self.accepted_value == proposed_value:
                print(f"accepting value {proposed_value} from {sender} with num {num}")
                # self.accepted_value[num] = proposed_value
                self.proposed_value[num] = proposed_value
                self.accepted_value = proposed_value
                self.accepted_n = num
                failures = await self.transport.send(sender, "accepted", {"num": num, "value": self.proposed_value[num]})
            else:
                print(f"conflicting values: {self.proposed_value} vs {payload.get('value', None)}")
                await self.transport.send(sender, "reject", {"num": self.num})
        elif kind == "promise":
            num_to_send = num
            value_to_send = self.value
            
            accepted_n = payload.get("value", {}).get("accepted_n", -1)
            accepted_value = payload.get("value", {}).get("accepted_value", None)
            if accepted_value is not None:
                if accepted_value not in self.candidate_accepted:
                    self.candidate_accepted[num_to_send] = Counter()
                self.candidate_accepted[num_to_send][(accepted_value)] += 1
            
            if num_to_send not in self.promisers:
                self.promisers[num_to_send] = set()
            self.promisers[num_to_send].add(sender)
            if len(self.promisers[num_to_send]) > len(self.members) // 2:
                # find majority of accepted values if any.
                
                if self.candidate_accepted:
                    value_to_send, count = self.candidate_accepted[num_to_send].most_common(1)[0]
                self.proposed_value[num_to_send] = value_to_send
                
                failures = await self.transport.broadcast(
                    "accept",
                    {"num": num_to_send, "value": value_to_send},
                    include_self=True,
                )

        elif kind == "accepted":
            self.num = max(self.num, num)
            if self.num not in self.acceptors:
                self.acceptors[num] = set()
            self.acceptors[num].add(sender)
            if len(self.acceptors[num]) > len(self.members) // 2 and self.accepted_value is None:
                print(f"value {self.proposed_value[num]} accepted by majority, num {num}")
                self.accepted_value = payload.get("value", None)
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
        
        if self.num // 20 and self.accepted_value is None:
            await self.propose(self.value) # leader election failed probably, let's retry
        # if self.num // 10 and self.accepted_value is not None:
        #     # broadcast learn message to all nodes
        #     for peer in self.members:
        #         if peer not in self.node_knows:
        #             failures = await self.transport.send(peer, "learn", {"num": self.num, "value": self.accepted_value})
        #             if failures:
        #                 print(f"failures in broadcasting learn message: {failures}")
        #                 raise DeliveryError(f"failed to deliver learn message to {failures}")
            
        # async with self.lock:
        self.num += 1