# Deployable N-replica Paxos

A single-decree Paxos service with a machine-checked safety and liveness proof of
the exact replica code that runs. It decides one `u64` value, like a write-once
register. A cluster has any fixed number N of replicas (1 to 255), any strict
majority is a quorum, and everything uses only `std`. The proofs hold for every N.

- `src/lib.rs` is the replica: acceptor, proposer (ballot allocation, retry after
  preemption) and learner in one deterministic, I/O-free `Node::handle`. It is
  extracted to Lean with Hax/Charon/Aeneas and verified.
- `src/bin/paxosd/` is the runtime: UDP transport, HMAC authentication, durable
  storage, retransmission, a leader timer and a client CLI. It is **not verified**
  and is kept small so it can be reviewed against the contract below.

## Run a cluster

The cluster size N (1 to 255) is the number of addresses given to `--peers`;
every replica gets the same list, `--id` is its index in that list, and any
strict majority of the N replicas is a quorum. Three replicas:

```sh
cargo build --release --manifest-path formal/rust/paxosd/Cargo.toml
P=127.0.0.1:7000,127.0.0.1:7001,127.0.0.1:7002
KEY=change-me-to-a-long-shared-secret
BIN=formal/rust/paxosd/target/release/paxosd
for i in 0 1 2; do $BIN serve --id $i --peers $P --data /tmp/paxos-$i --key $KEY & done
$BIN propose --node 127.0.0.1:7002 42     # prints "decided 42"
$BIN propose --node 127.0.0.1:7000 7      # prints "decided 42": single decree
$BIN status  --node 127.0.0.1:7001
```

For five replicas, list five addresses in `P` and start `--id 0` to `--id 4`;
the cluster then tolerates two failed replicas. The cluster size is part of each
replica's durable state, so it cannot be changed for an existing data directory.

To watch the verified state machine itself, `cargo run --example trace` prints
every input, emitted message, and replica state for a normal decision and a
failover in which the new leader must re-propose the earlier value.

Options: `--tick-ms` (default 50) sets the protocol timer and heartbeats, and
`--suspect-ms` (default 600) sets how long a replica waits before assuming a
lower-numbered replica has failed. Kill and restart any replica at any time; it
resumes from `--data`. Deleting a replica's data directory while the cluster is
running is **not** a supported recovery procedure: it erases promises and can
break safety.

## Verify

```sh
python3 formal/rust_verify.py --install          # once
python3 formal/rust_verify.py formal/rust/paxosd # about 2 minutes
cargo test --manifest-path formal/rust/paxosd/Cargo.toml
```

`spec.json` lists the checked claims. The driver extracts `src/lib.rs` again and
checks every proposition, and the axiom audit rejects anything beyond `propext`,
`Classical.choice` and `Quot.sound`. Nothing uses `sorry`, and no bounded
search is involved. Every claim except `no_panic` is stated for all cluster
sizes: `∀ (N : Nat) [Cluster N], …`, where `Cluster N` means 0 < N < 256.

| Claim | Meaning | Assumptions |
| --- | --- | --- |
| `no_panic` | `Node::handle` returns normally for **every** state and input | none |
| `refinement` | every reachable deployment state maps to a reachable state of the abstract majority-quorum Paxos model (`verification/Model.lean`) | none |
| `agreement` | no two replicas ever decide different values | none (invariant) |
| `validity` | every decided value was submitted by a client | none (invariant) |
| `liveness` | every replica of the live majority `Q` decides | `Fair run L Q T`, below |
| `eventual_decision` | the same, as a `Spec.Eventually` claim | `Live` = some `Fair` |
| `fairness_needed` | an idle execution is legal and never decides | none |

### The model

`verification/System.lean` defines the deployment. Its state is the N real
`Node` values plus the set of **every packet ever sent**. A step applies the
extracted `Node::handle` at one replica to one of these inputs:

- a client `Submit`;
- a timer `Tick`;
- the delivery of any previously sent packet addressed to that replica.

Because packets stay in the set, the network may delay, duplicate, reorder or
never deliver them. A crash followed by a restart from storage is a stutter,
since the runtime makes state durable before it sends.

Safety (`agreement`, `validity`) holds in every reachable state with **no**
timing, delivery or leader assumption.

Liveness assumes, from some time `T`, a leader `L` in a majority `Q` with:

1. a client value has reached a member of `Q`;
2. no replica other than `L` starts a new ballot, meaning the runtime's leader
   timer has stabilised (Ω);
3. ballots at `T` are below 2^62 − 2N;
4. `L`'s timer keeps firing;
5. each packet sent between members of `Q` is eventually delivered (weak fairness).

Delays are unbounded, and every replica outside `Q` may be crashed forever.

The previous core proof (`formal/rust/paxos`) *assumed* that the quorum's promises
never exceed the leader's ballot. Here that fact is **derived** instead:

1. The leader's ballot is monotone. After `T` it is bounded, because only a
   higher ballot owned by another replica can trigger a restart.
2. So the ballot stabilises at some `b`.
3. If a quorum acceptor had promised more than `b`, its nack to the
   retransmitted prepare would raise the leader's `max_seen` and force a
   restart, which contradicts stability.
4. Therefore the promises of all of `Q` reach the leader, which counts a
   majority and proposes. Every member of `Q` accepts, and every learner in `Q`
   counts a majority of matching votes.

### Runtime contract

This is how the unverified runtime realises each model assumption:

| Model assumption | Runtime mechanism (`src/bin/paxosd`) |
| --- | --- |
| inputs to a replica are serialised | a single-threaded event loop per process |
| a restart resumes the last state before any send | state and outbox are fsync'd and atomically renamed **before** each send |
| delivery of a packet only to its addressee, with the true sender | HMAC-SHA-256 over sender, destination and message; addressee checked |
| a packet may be delivered many times | replays are accepted; the model already allows them |
| every packet between live replicas is eventually delivered | the durable outbox is retransmitted forever, with backoff up to 2 s |
| eventually a single ballot starter | only a replica that has not heard from any lower id (of the N) for `--suspect-ms` fires `Tick` |
| a fixed set of N replicas | `--peers` fixes N; the stored state records N and a replica refuses to start from a state of another cluster size |

The leader timer is a heuristic. If lower-numbered replicas keep flapping,
leaders can compete indefinitely. Safety is never affected, but assumption 2
then fails and decisions stall until the network settles.

### Trusted and not covered

- The runtime code, the Rust compiler, and Charon/Aeneas extraction.
- The Lean kernel.
- Durable storage honouring `fsync`, and each replica keeping its data directory.
- Cluster membership is fixed at N replicas (no reconfiguration), and there is
  one decision per cluster; it is not a replicated log or Multi-Paxos.
- The outbox is capped at 100,000 packets (oldest dropped). Reaching it takes
  pathological ballot churn and weakens only liveness.
- Clients are unauthenticated: anyone who can reach the port may propose.
- Satisfiability of the liveness assumptions is not proved in Lean.
  `fairness_needed` shows they are not trivially implied, and the randomized
  simulation in `src/tests.rs` runs schedules that satisfy them and decides.

## Proof layout

| File | Content |
| --- | --- |
| `Node.lean` | extracted functions, including the counting and max loops over the slot vectors, equal a pure specification (gives `no_panic`) |
| `Model.lean` | abstract Paxos over `Fin N` with majority quorums; agreement via quorum intersection |
| `System.lean` | world, steps, interpretation `abs`, concrete invariant |
| `Local.lean` | what a replica never loses under any input |
| `Refinement.lean`, `Steps.lean` | each handler preserves the invariant and is one abstract `prepare`/`propose`/`cast` or a stutter |
| `Safety.lean` | induction over reachable worlds; agreement, validity, refinement |
| `Progress.lean`, `Liveness.lean`, `Eventually.lean` | input effects, stabilisation, and the liveness argument |

Agreement itself is not re-proved: it follows from the abstract model's
quorum-intersection proof through `refinement`.

A mutation check in `formal/test_rust_pipeline.py` makes the proposer ignore
reported votes (`Some(_) => offered`); the result is not proved. In the earlier
3-replica version the same bug also failed the propose-refinement step when the
pure specification was changed to match, and a leader that never restarts after
a nack failed the liveness proof while safety still checked.

## Tests

- `src/tests.rs`: scenarios plus 300 randomized adversarial schedules. Each
  schedule uses a cluster of 1, 2, 3, 4, 5 or 7 replicas and mixes delay,
  duplication, loss, conflicting clients and competing leaders, followed by a
  stabilised fair phase with a crashed minority. Every schedule checks agreement
  and validity, and every one decides.
- `src/bin/paxosd/*`: SHA-256/HMAC test vectors, codec round-trips and
  truncation, and storage corruption detection.
- `tests/cluster.rs`: real processes over UDP, with 3 and 5 replicas. It covers
  decide-and-restart, failover without the preferred leaders, a late joiner
  catching up, concurrent conflicting proposals, and crash/restart of every
  replica while a decision is in flight.
