# PaxosSafetyModel: a separate verification model

The new implementation is [`paxos_model.py`](../examples/paxos_model.py), with
properties in [`paxos_model_spec.py`](../examples/paxos_model_spec.py).
It does not import, modify, or establish a refinement of `paxos_lab/algorithm.py`.

| Model | Purpose | Execution |
| --- | --- | --- |
| `paxos_lab.algorithm.PaxosNode` | Existing application | Async transport and retries; unverified |
| `PaxosAcceptorModel` | Check local promise/accept rules | Arbitrary typed prepare/accept calls |
| `PaxosSafetyModel` | Check single-decree Paxos safety | One protocol action per step, retained message histories |

There are three acceptors, numbered 0, 1, and 2. Every pair is a quorum.
Ballots range over all nonnegative integers; values range over all integers.
Neither the ballot count nor execution length is bounded by the model.
Invalid IDs, negative ballots, and deliveries without matching sent messages
stutter. The single-class specification universally quantifies method inputs.

## Protocol representation

The pinned reference is
[`Paxos.tla`](../references/tlaplus/specifications/Paxos/Paxos.tla), revision
`ceeaa904140e3e03781cb2a79cd6c6d8b8b08e10`. The mapping below is a manual
design comparison, **not a checked translation or refinement theorem**.

| TLA+ concept | Python representation |
| --- | --- |
| `maxBal`, `maxVBal`, `maxVal` | `acceptors: dict[int, AcceptorState]` |
| Phase 1a messages | `prepares: set[int]` |
| Phase 1b messages | `promises: dict[PromiseKey, AcceptorState]` |
| Phase 2a messages | `proposals: dict[int, int]` |
| Phase 2b messages | `votes: set[Vote]` |
| Value chosen by a quorum | `learn` adds to `chosen: set[int]` |

Frozen records carry accepted ballot/value pairs and immutable promise snapshots.
`phase1b` raises one acceptor's promise and retains its accepted value in a
snapshot. `phase2a` requires snapshots from two distinct acceptors at the same
ballot. It takes the value with the highest accepted ballot, or the offered
value if neither acceptor has voted. The proposal dictionary prevents issuing
two values at one ballot. `phase2b` votes only for a sent proposal whose ballot
is at least the acceptor's promise.

Messages are retained permanently. Repeating receipt is allowed; never
receiving a message models loss for safety purposes. No FIFO order or fairness
is imposed. A learner can use old votes even after acceptors advance, so
agreement concerns the entire execution, not just current accepted values.
`chosen` never controls a protocol phase. Its observational nature is visible
in the source, but a separate learner-projection theorem is not supplied.

This uses the TLA+ reference's action scheduling. It does not compose three
independently advancing acceptor atoms with a live network. The separate
`delivery_spec` example demonstrates `Composition`, `Choice`, and `Await`.

## Verification and reproduction

```sh
formal/.venv/bin/python -m rmverify examples.paxos_model_spec:acceptor --timeout 120 --depth 2
formal/.venv/bin/python -m rmverify examples.paxos_model_spec:spec --timeout 180 --depth 2
formal/.venv/bin/python -m unittest formal.test_paxos_model -v
```

Results from the September 14, 2026 run:

| Obligation | Result |
| --- | --- |
| Local acceptor source correspondence | **proved** |
| Local acceptor invariant, both contracts, and no-fault | **proved** |
| Complete protocol source correspondence | **proved** (131 seconds) |
| Global agreement and joint acceptor strengthening | **unknown** (180-second proof timeout) |
| Global no-fault | **unknown** (separate 180-second proof timeout) |
| Supplied 14-call, two-ballot Python/source trace | **passed** |

The acceptor CLI exits successfully; the protocol CLI deliberately exits 1
because its requested safety properties are not all proved. The protocol's
Lean tests require source correspondence and honest result reporting; they do
not count `unknown` as a Paxos safety proof. Veil diagnostic queries also returned
unknown, and depth-2 source search supplied no checked reachable refutation.

The generated protocol RM is in
[`Translation.lean`](../../.rmverify/paxos-model/check-1nzpch0m/Translation.lean):
look for `State`, the `PaxosSafetyModel.phase*` functions, and `model`.
The local proofs are in
[`Invariants.lean`](../../.rmverify/check-1e86__c8/Invariants.lean)
and the adjacent `Contract0.lean` and `Contract1.lean` files.
These evidence directories are local, ignored build outputs; the commands
above regenerate them with source hashes, dependency pins, and axiom audits.

The local acceptor specification proves:

- The promised ballot is at least -1, and any accepted ballot is nonnegative
  and no greater than the promised ballot.
- Prepare raises the promise to the maximum of the old promise and the request,
  while retaining the accepted vote.
- Accept rejects stale/negative ballots without changing state; otherwise it
  records the requested ballot/value and never decreases the promise.
- All reachable calls are fault-free, with checked source correspondence.

The local acceptor intentionally relies on the surrounding protocol to prevent
conflicting proposals at the same ballot. Its contract does not claim local
non-equivocation under arbitrary malicious inputs.

Global agreement is written as `len(s.chosen) <= 1`. The current additional
predicate checks the local acceptor invariant throughout the acceptor map.
These predicates alone do not characterize reachable message histories:
an arbitrary state could already contain fabricated conflicting quorum votes.
Consequently they are insufficient for an inductive agreement proof. Closing
that proof needs invariants relating sent proposals, promise snapshots,
historical votes, and intersecting quorums across ballots. A bounded search
that finds no violation cannot supply that argument.
Closing the global no-fault obligation is a separate proof-automation task:
the current whole-step reduction exhausts its budget on the collection/helper
branches. The local acceptor no-fault theorem does not establish the global
dictionary and optional-value obligations.

The regression tests cover all nine pairs of old/new two-member quorums,
both delivery orders for the first quorum, duplicates, stale requests,
fabrication attempts, duplicate quorum members, proposal uniqueness, and a
three-ballot scenario where the highest accepted ballot determines the value.
The supplied multiballot trace also runs against Python and the extracted
source interpreter. These executions are regression evidence, not an
unbounded Paxos theorem.

Each verifier report identifies its generated `Translation.lean`, source
snapshots, audits, and accepted theorem files. Recheck accepted obligations
with `python3 PATH_TO_EVIDENCE/recheck.py`; replay preserves unknown statuses.

The model also exercised two generator changes. Helper argument tuples now
carry explicit Lean types and retain typed `Except` bindings during evaluation;
this avoids a Lean elaboration failure after dictionary lookups. Caller
correspondence proofs reuse previously checked helper correspondence theorems,
instead of expanding the helper implementation on both sides of every call.
The source interpreter, fault semantics, and permitted axioms are unchanged.
A regression corrupts the generated promise helper while preserving its local
ballot invariant and checks that source correspondence rejects the change.

Validation of this change passed 20 selected unit tests covering the new model,
records, helpers, borrowing, collection order, faults, and corruption rejection.
The existing composed delivery example also retains all its proved properties.
Standalone replay passed for the acceptor's nine accepted obligations and the
protocol's six accepted obligations; the latter preserves its unknown safety
statuses.
The complete 64-test suite is documented in the main README; it was not rerun
in full for this change.
