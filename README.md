# Paxos playground

For the bounded Python → reactive-modules → Lean model of the current learning
implementation, see [formal/README.md](formal/README.md). It includes CSLib-based
specifications, repeatable checks, and an explicit account of proof limitations.

Python 3.11+, standard library only. Networking and configuration are implemented;
**Paxos is not**. Edit `paxos_lab/algorithm.py` to implement it yourself.

## Run locally

From this directory, start one command in each of three terminals:

```sh
python3 -m paxos_lab --node n1
python3 -m paxos_lab --node n2
python3 -m paxos_lab --node n3 --value '"hello"'
```

Each process logs its listening address. Until you implement the hooks, nodes
only listen; `--value` calls the empty `propose()` stub and produces no result.
Start the other nodes before the process with `--value`. Stop with Ctrl+C;
restart a process to submit another startup proposal. State is currently only
in memory; persistence is up to your implementation.

## Run over your VPN

1. Copy this project onto each host and use Python 3.11 or newer.
2. Replace the example IPs in `config/vpn.toml` with your hosts' VPN addresses.
3. Copy the same configuration to every host and allow the listed TCP ports
   between those hosts over the VPN.
4. Run the corresponding node on each host:

```sh
# Host A
python3 -m paxos_lab --config config/vpn.toml --node n1
# Host B
python3 -m paxos_lab --config config/vpn.toml --node n2
# Host C
python3 -m paxos_lab --config config/vpn.toml --node n3 --value '42'
```

Node count is independent of physical host count. For multiple processes on one
host, give their node entries the same VPN IP and different ports. Add more node
tables if needed; every process must use the same membership configuration.
IDs such as `n1` are stable strings, not process IDs.

By default, a node listens on its configured address. `--bind-host 0.0.0.0`
can override the listen address while leaving the configured destination address
unchanged. Use reachable VPN addresses in the config, not `0.0.0.0`.
This transport relies on your trusted VPN: there is no TLS or sender
authentication, and sender IDs can be forged by someone with network access.

## Your algorithm interface

`PaxosNode` receives a `Transport`, which provides:

| Interface | Meaning |
| --- | --- |
| `transport.node_id` | This node's ID |
| `transport.peers` | All configured IDs, including this node |
| `await transport.send(id, kind, payload)` | Send one message |
| `await transport.broadcast(kind, payload)` | Send to all nodes, including self; return failures by ID |
| `await transport.broadcast(kind, payload, include_self=False)` | Send to the other nodes |
| `await transport.receive()` | Receive a `Message`; the launcher calls this for you |

`kind` is any nonempty string you choose; `payload` is a JSON-compatible dict.
Use string keys and finite numbers, and avoid Python-only types such as sets.
Received messages have `sender`, `kind`, and `payload` attributes. For example,
this is a generic transport call, not a Paxos message specification:

```python
await self.transport.send("n2", "example", {"text": "hello"})
```

Implement these hooks in `algorithm.py`:

- `propose(value)`: invoked once if the command includes a JSON `--value`.
- `on_message(message)`: invoked for each received message, including self sends.
- `on_tick()`: invoked periodically; `--tick 0.5` sets the interval in seconds.

Hooks run serially. Keep them short: don't call `receive()` or wait for a protocol
reply inside a hook; store state and handle the reply in `on_message()`. Awaiting
`send()` or `broadcast()` is fine: reception runs independently of the hooks.
Timers may be delayed by a running hook. Unhandled hook exceptions stop the node
so implementation errors remain visible.

## Delivery behavior

- TCP carries length-prefixed JSON, one message per connection. Individual
  messages cannot be interleaved or partially delivered to the algorithm.
- Successful `send()` means the remote in-memory inbox accepted the message.
  It does **not** mean the algorithm processed it or persisted anything.
- Failed or timed-out delivery raises `DeliveryError`. Delivery can be uncertain
  if the acknowledgement was lost. There are no automatic retries.
- `broadcast()` attempts all recipients concurrently and returns a dict of
  `DeliveryError`s; one unreachable node doesn't prevent other sends. Inspect
  the result in your implementation. Invalid local messages raise immediately.
- There is no ordering guarantee across concurrent sends, no durable delivery,
  and no deduplication. Any algorithm-level retry and duplicate handling is yours.
- An oversized/malformed message or a full inbox is rejected. Frame size,
  inbox capacity, and connection timeout are configurable in `[network]`.
- Self sends use the same transport and inbox path as remote sends.

The transport doesn't define message types, ballots, roles, quorums, elections,
acceptance rules, or learning behavior. Those are left for your Paxos implementation.

## Verify the scaffolding

```sh
python3 -m unittest discover -s tests -v
```

The tests use actual loopback TCP connections with OS-assigned ports and exercise
delivery, partial broadcast failure, validation, queue limits, timeouts, and
shutdown. They don't test or implement Paxos. Add `--verbose` to a node command
to log rejected incoming connections when troubleshooting.
