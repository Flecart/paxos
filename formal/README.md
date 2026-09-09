# RM-native protocol verification

This branch has one verification workflow: author a protocol using ordinary
reactive-modules primitives, declare its contract, and check the exported RM
model with Z3, Lean, or both. Start with [PROTOCOL.md](PROTOCOL.md).

The original `paxos_lab/algorithm.py` is unchanged. The separate
`protocol_paxos.py` is a manually authored, bug-preserving RM port, not an
automatic translation of arbitrary Python/asyncio. Differential tests compare
the port with the original coroutines.

## Setup

Requires uv, Rust/Cargo, a C/C++ compiler, and elan/Lean.

```sh
python3 formal/bootstrap.py
cd formal/.cache/reactive-modules/verification/lean
lake exe cache get
lake build ReactiveModules.Protocol
cd ../../../../..
```

Bootstrap creates an isolated Python 3.13 environment and installs the pinned
upstream checkout. It refuses to overwrite an upstream checkout with local
changes. Lean/CSLib dependency caches can require several GB.

## Check

From the Paxos repository root:

```sh
uv run --no-project --python formal/.venv/bin/python formal/check_protocol.py --backend both
uv run --no-project --python formal/.venv/bin/python -m pytest -q formal/test_protocol_paxos.py formal/.cache/reactive-modules/python/tests/test_protocol.py
```

A small contract-only example, with no hand-written Lean file:

```sh
uv run --no-project --python formal/.venv/bin/python -m zrth.protocol_check formal/.cache/reactive-modules/verification/examples/protocol_register.py --out formal/protocol-evidence/register
```

The checker generates proof obligations from the declared schema and properties.
Small invariant/step obligations get an automatic symbolic proof attempt.
Z3 counterexamples are independently replayed in Lean. Results are
`lean-proved`, `lean-refuted`, or `unknown`; selecting a backend is not a
guarantee that it can settle every property.

## Reading order

1. Upstream `verification/examples/protocol_register.py`: implementation and contract.
2. [PROTOCOL.md](PROTOCOL.md): scheduler, scope, and Paxos properties.
3. `protocol_paxos.py`: node transitions, network, then property definitions.
4. Upstream `verification/lean/ReactiveModules/Protocol.lean`: mathematical semantics.
5. Upstream `python/zrth/protocol.py`, `protocol_check.py`, and
   `protocol_proof.py`: export, evidence checking, and automatic proof attempts.

The previous generator/native demonstration routes and hand-written example
proofs have been removed from this branch. Recovery references are in
[UPSTREAM.md](UPSTREAM.md). Shared upstream compiler libraries remain internal
dependencies/regression targets; they are not additional documented workflows.
