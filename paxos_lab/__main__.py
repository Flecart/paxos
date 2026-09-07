import argparse
import asyncio
import json
import logging
import math

from .algorithm import PaxosNode
from .config import ClusterConfig
from .transport import Transport


async def run(args: argparse.Namespace) -> None:
    config = ClusterConfig.load(args.config)
    async with Transport(args.node, config, args.bind_host) as transport:
        logging.info("node %s listening on %s:%s; members=%s", args.node,
                     transport.bind_host, config.nodes[args.node].port, transport.peers)
        node = PaxosNode(transport)
        if args.value is not None:
            await node.propose(json.loads(args.value))
        # All algorithm hooks execute serially, so algorithm state needs no locks.
        loop = asyncio.get_running_loop()
        next_tick = loop.time() + args.tick
        while True:
            remaining = next_tick - loop.time()
            if remaining <= 0:
                await node.on_tick()
                next_tick = loop.time() + args.tick
                continue
            try:
                message = await asyncio.wait_for(transport.receive(), remaining)
            except TimeoutError:
                continue
            await node.on_message(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one node of your Paxos implementation")
    parser.add_argument("--config", default="config/local.toml")
    parser.add_argument("--node", required=True, help="node ID from the configuration")
    parser.add_argument("--bind-host", help="override the local listen address")
    parser.add_argument("--value", help='optional JSON proposal, e.g. '\
                        "'\"hello\"' or '42'")
    parser.add_argument("--tick", type=float, default=0.5, help="timer interval in seconds")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    if not math.isfinite(args.tick) or args.tick <= 0:
        parser.error("--tick must be finite and positive")
    if args.value is not None:
        try:
            json.loads(args.value)
        except ValueError as exc:
            parser.error(f"invalid JSON --value: {exc}")
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        pass
    except (ValueError, OSError) as exc:
        parser.exit(1, f"error: {exc}\n")


if __name__ == "__main__":
    main()
