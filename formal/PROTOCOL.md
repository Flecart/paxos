# Direct RM Paxos protocol module

This branch contains only the RM-native verification workflow. Your
`paxos_lab/algorithm.py` is unchanged. `protocol_paxos.py` is a separate, manually
authored symbolic RM port of its current logic, including its bugs. Changing the
original does **not** automatically change this model: review the port and rerun
the saved differential checks. Source hashes record provenance, not equivalence.

## Run

```sh
uv run --no-project --python formal/.venv/bin/python formal/check_protocol.py --backend z3 --out formal/protocol-evidence/z3
uv run --no-project --python formal/.venv/bin/python formal/check_protocol.py --backend lean --lean-timeout 600 --out formal/protocol-evidence/lean
uv run --no-project --python formal/.venv/bin/python -m pytest -q formal/test_protocol_paxos.py formal/.cache/reactive-modules/python/tests/test_protocol.py
```

Backend choices are `z3`, `lean`, and `both`. Options: `--profile small` (default)
or `compatibility`, `--depth 16`, `--timeout 30` seconds per solver query,
`--lean-timeout 600` seconds per Lean check, and `--out formal/protocol-evidence`.
Timeouts return unknown. Small safety obligations get an automatic proof attempt,
without a separate Lean proof file. The large Paxos safety obligations exceed
the current symbolic expansion budget and return `unknown`; selecting Lean does
not silently prove them. Z3 induction results and bounded searches are separately
labeled. The retired verification routes are recoverable through Git; see
[UPSTREAM.md](UPSTREAM.md).

For a fresh environment use `python3 formal/bootstrap.py`, then build/fetch the
existing Lean dependencies as described in README.md. Bootstrap checks out the
pinned upstream revision; do not run it over uncommitted upstream work.

## Actual modeled transitions

All mutable state is in one discrete RM module: three nodes, packet slots,
delivery/inbox status, FIFO ranks, source faults, explicit bound failures,
proposal/vote history, and decision observations. No Python network simulator is
called during RM execution. Named construction helpers avoid positional argument
lists; the protocol infrastructure also exports genuinely composed RM atoms.

Inputs are ordered `(action, node, value, slot)`:

| Action | Code | Behavior |
| --- | --- | --- |
| idle | 0 | Stutter |
| propose | 1 | Invoke a free node's proposal hook with an encoded value |
| tick | 2 | Invoke a free node's timer hook |
| resume | 3 | Resume after all packets of that send have reached inboxes |
| deliver | 4 | Move the selected pending **slot** into its recipient's FIFO |
| receive | 5 | Invoke a free node with its internally selected FIFO head |

Nodes are 0/1/2, corresponding to n1/n2/n3. Values are encoded as
`0=None, 1="A", 2="B", 3=0, 4=1, 5=2`. Packet slots are stable storage indices,
not positions in a compacted pending list. Broadcasts enqueue three independently
deliverable messages. A recipient can process its delivery before the sender
resumes. Only one hook per node runs at once.

Invalid scheduler selections stutter protocol state and set `invalid=1`; the next
valid action clears that diagnostic. Input-domain violations are rejected by the
simulation API. The small profile has max number/count 3 and six total queued
packets; compatibility uses 31 and 32. Crossing a bound sets `out_of_scope=1`
and makes the entire system terminal. No wraparound or silent successful drop
is modeled. Reliable sends exclude loss, duplication, crashes, returned failures,
DeliveryError and backoff retries. The timer's nested proposal suspension remains
modeled, including the two increments after its send completes.

## Properties

`PropertySpec` objects near the end of `protocol_paxos.py` are machine-readable
formulas, translated to both backends. The evidence artifact lists their field
bindings and the generated `ProtocolArtifact.lean` gives their exact Lean types.

Safety is conditional on remaining in scope:

- Agreement: at most one value has a historical majority of actual acceptance
  sends for some proposal number.
- Validity: every such chosen value was submitted by a client.
- Decision accuracy: an announced value was chosen when announced.
- Decision consistency: announcements never disagree.
- Fault freedom: no node has raised a modeled source exception.
- Local step relations: non-None acceptance is immutable; acceptance replies
  match the stored value. One-step induction can expose unreachable malformed
  states; that is not automatically a reachable algorithm counterexample.

Unconditional proposal liveness means a submitted proposal eventually leads to
some chosen value on **every** infinite execution. A supplied proposal-then-idle
lasso is a refutation witness. This says nothing against fairness-dependent Paxos
liveness: no fairness is assumed and positive fair liveness is deliberately open.

The small-profile initialization/update execution certificates and this complete
proposal-then-idle refutation have passed Lean's kernel check. The final witness
depends only on `propext` and `Quot.sound`, not `native_decide` or an SMT axiom.
This is **not a proof of Paxos safety**: its positive safety obligations remain
open. In the saved three-second-query Z3 run, the three local acceptance
immutability relations were `solver-unsat` under induction; bounded global
searches timed out and were reported `unknown`.

The reusable API, Lean semantics, certificate method, and trust boundary are
documented upstream in `verification/PROTOCOL.md`. This is a bounded formal model
and simulation interface, not a TCP adapter or a universal Python compiler proof.
