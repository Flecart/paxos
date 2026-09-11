# Collections, borrowing, and receiver checkpoint

This is a tested extension of the scalar pipeline, not completion of the full
Paxos preparation plan. Run commands from the repository root after bootstrap.

## 1. Collections and explicit faults

```sh
formal/.venv/bin/python -m rmverify examples.collections_spec:registry --timeout 60
```

The registry owns a dictionary of integer payloads and a set of IDs. Register
`(3, 7)`, then `(3, 99)`: the stored payload remains `7`, and the count stays one.
Lean proves that dictionary keys and set members agree in every reachable state,
and proves the payload/duplicate contract for arbitrary integer arguments.

In the printed evidence directory, open `Translation.lean`:

- `Registry.register_1` is the compiled typed function.
- `source1` is its extracted source program; `translation1` equates their complete
  outcomes, including locals, return values, and faults.
- `State`, `Action`, and `model` are the compiled machine.
- `source_model_eq` connects the source machine to that machine.
- `safe` combines the invariant with absence of faults. `Invariants.lean` proves
  it over unbounded reachability. `Contract0.lean` proves the registration contract.

The collection tests also attempt a missing dictionary lookup after a state
write. It becomes a fault state preserving the preceding write. Lean replays
that execution and refutes `no-fault`; it is not silently removed from the model.

## 2. Borrowing without changing Python behavior

The registry uses `entries = self.entries` and writes through `entries`. The
frontend treats this alias as an exclusive borrow through its last use.

```python
entries = self.entries
entries[key] = 7              # accepted
self.last = entries[key]
self.entries[key] = 8         # accepted after the last use of entries
```

This overlapping access is rejected with both source locations:

```python
entries = self.entries
self.last = len(self.entries) # conflicting access while entries is borrowed
entries[key] = 7
```

The tests also check shared borrows, annotation mismatches, rebinding, dictionary
iteration order, and conflicting mutation during iteration. These ownership
rules are conservative frontend checks. They do not yet have an independently
checked Lean certificate of the borrow analysis.

## 3. Duplicate delivery and the remaining network work

```sh
formal/.venv/bin/python -m rmverify examples.receiver_spec:receiver --timeout 60
formal/.venv/bin/python -m rmverify examples.receiver_spec:broken_receiver --timeout 60 --depth 2
```

The receiver core accepts arbitrary integer IDs, including repeated IDs. Its
invariant states `count == len(processed)`. Its contract states that an already
processed ID does not increment the count, while a new ID increments it once.

The broken receiver increments on every delivery. Concrete search proposes two
deliveries of the same ID. A generated Lean witness proves both reachability and
the violated invariant, and connects the refutation back to source execution.
The bound of two limits discovery only. It does not bound the correct receiver's
safety theorem. Replaying the evidence does not require the Python verifier.

`Network.lean` separately proves that an empty choice domain disables delivery,
stuttering remains possible, and a deterministic ghost observer can be added or
projected away without changing executable reachability. Tests exercise repeated
delivery and membership in the old-state domain. These are library lemmas:
Python `Choice(domain)`, collection-valued composition, and ghost bindings are
not connected yet. The receiver-core proof makes no no-fabrication claim.

## Checks and limits

```sh
formal/.venv/bin/python -m unittest formal.test_rmverify formal.test_composition formal.test_paper formal.test_collections -v
python3 PATH_TO_EVIDENCE/recheck.py
```

Mutation tests deliberately corrupt generated code, state encoding, fault
projection, input binding, invariant connection, and return projection. Lean must
reject the changed translation, even when the changed machine remains safe.
The suite also checks stale source, timeouts, axiom audits, Peterson rounds,
old/awaited reads, and existing negative examples.

Still missing: frozen records/options, general typed helpers, broader loop proof
automation, ownership transfers/certificates, and the complete composed Python
sender/network/receiver example. These are implementation and proof work, not a
demonstrated impossibility. Fully automatic invariant proving for arbitrary
Python is not a realistic guarantee; unsupported constructs must be rejected and
unclosed obligations must remain `unknown`.

The current `paxos_lab/algorithm.py` additionally uses async transport calls,
retry decorators, nested mutable containers, and `Any`. Directly verifying that
file is outside the planned fragment. A synchronous typed protocol core and an
explicit transport model would be needed, or the supported semantics would have
to be broadened substantially. This checkpoint does not modify that file.
