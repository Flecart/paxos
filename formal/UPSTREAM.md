# Reactive-modules frontend contribution

## RM-native protocol branch

The project now pins `f4857be9477596e75e930c95ccab8e72bffe6a45` on
`feat/rm-protocol-modules`. This adds `zrth.protocol`, ordered-atom RM export,
selectable Z3/Lean checking, typed property obligations, kernel-checked numerical
wire certificates, and an independently proved register. See [PROTOCOL.md](PROTOCOL.md).
The original native compiler and its previous branch are retained unchanged.

## Direct native-source check

The native compiler increment was introduced at upstream contribution commit
`91289f99b76f27abaf8ead91dc149b096dc85b69` on `feat/verified-python-handlers`.

Run this from the Paxos project root:

```sh
uv run --no-project --python formal/.venv/bin/python formal/check_native.py
```

The unchanged `algorithm.py` now goes through the reusable
`zrth.verified_native.compile_native` frontend. Its native dictionaries, sets,
Counter, mutable fields, nested awaits, async helper call frames, early returns,
exceptions, formatting, and supported retry decorators are accepted. There is
no Paxos-specific lowering and no source-hash whitelist on this path.

The current file elaborates to 642 instructions. Actual RM graphs select those
instructions; the reusable Lean object machine defines their value, heap,
control-flow, async, exception and retry behavior. Lean checks the graph/page
certificates and whole-machine compiled/source equivalence for all finite action
sequences. The command additionally compares original Python coroutines and the
compiled runtime at suspension/return/failure boundaries and replays saved
instruction samples in Lean's kernel.

This is **not** a claim that Paxos is correct. Its errors remain errors. The
frontend's AST elaboration and CPython correspondence remain trusted; the runtime
adapter is differentially tested. Transport/retry timing use explicit interfaces
from `native.json`, not silently assumed TCP behavior. Inputs use the declared
acyclic integer-JSON/object profile, not arbitrary Python objects. See
[NATIVE.md](.cache/reactive-modules/verification/NATIVE.md) for exact scope.

Evidence is under ignored `formal/native-evidence/`. Each source edit is compiled
afresh, and failed/stale checks clear their success status. Use `--skip-lean` only
for a clearly labeled Python-comparison run. To author a property, use the native
compiler CLI with `--proof` and `--theorem`; specifications are not inferred from
the implementation.

`generate.py` remains for the older bounded Paxos model and its existing proofs,
but is no longer required by the direct-source check. The historical increments
below explain how the reusable compiler developed.

## Checked-library first release

The new [feat/verified-python-handlers contribution](https://github.com/Flecart/reactive-modules/tree/feat/verified-python-handlers) provides a reusable
`zrth.verified.compile_module` interface, a Lean-proved canonical lowering, and
checked contracts for a register and a communicating retry channel. A deliberately
incorrect register is preserved and refuted. No per-algorithm generator is used.

Run from this repository:

```sh
uv run --no-project --python formal/.venv/bin/python formal/verify_libraries.py
```

Fresh installations should first run `python3 formal/bootstrap.py`, then fetch
Lean caches with `lake exe cache get` from
`formal/.cache/reactive-modules/verification/lean`. The full upstream API, supported
subset and exact trust boundary are documented in
[verification/README.md](.cache/reactive-modules/verification/README.md).

Evidence is regenerated under `formal/.cache/reactive-modules/verification/bundles`.
The parser/schema elaborator and Python runtime correspondence remain explicit
trust assumptions; the source-AST-to-RM connection is checked in Lean. These new
proofs do not use `native_decide` or algorithm-correctness axioms.

The original `algorithm.py` is unchanged. The direct native-source path above is
newer than this immutable-handler increment; the legacy generator is needed only
for the old bounded model.

## Compiler increment: helpers and fixed-tuple iteration

The contribution now also supports same-module nonrecursive typed helpers,
positional/keyword calls, nested tuple unpacking, literal tuple indexing, `len`,
and `for` loops over nonempty homogeneous fixed tuples. Nested loops, early
returns, and `for ... else` preserve their Python control flow; calls in Boolean
and conditional expressions stay inside their short-circuiting branches.

Calls and loops remain explicit in the Lean source model. The generic lowering
proof covers isolated helper-local state, helper return boundaries, and iteration
over a snapshot of the input tuple. Fixed tuple length is part of the source
schema, not a silently chosen execution bound. This synchronous entrypoint does
not support dynamically growing dictionaries, sets, lists, or async handlers.

The new `verification/examples/fold_register.py` uses a helper in a loop;
`verification/proofs/fold_register.lean` proves that its compiled graph never
decreases the stored value and covers all offered values. The saved runner above
also runs the new control-flow regressions and these proofs. The original Paxos
algorithm is not rewritten or repaired by this increment.

## Unbounded heap and async-effect foundation

Upstream now includes `zrth.effects`: integer dictionary/set objects with stable
references, aliasing, copies, insertion-order-aware dictionary access, and
explicit errors. A real Python coroutine runner exposes each awaitable request
and guards suspension tokens against replay and cross-task use. It supports
manual interleaving of tasks sharing a heap; it is not a network adapter.

`ReactiveModules.Heap` and `ReactiveModules.Effects` contain 18 checked model
theorems. The saved runner additionally compares 272 requests against native
Python containers in Lean, including values beyond machine integer width.
These are model proofs and sampled runtime correspondence, **not a proof of
container or async compilation**. Both lowering statuses in the standalone
foundation artifact remain explicitly `not-established`. The compiler connection
below has its own evidence and supported subset.

Run the new example from this project:

```sh
uv run --no-project --python formal/.venv/bin/python formal/.cache/reactive-modules/verification/examples/async_containers.py
```

It prints `(10, 20, 1)`, demonstrating an independent dictionary copy and set
deduplication across genuine suspension points. See upstream
[verification/EFFECTS.md](.cache/reactive-modules/verification/EFFECTS.md) for
supported operations, exact integer schemas, trust boundaries, and next steps.

## Connected async compiler

`zrth.verified.compile_coroutine` now directly compiles typed `async def` source
using top-level `await Request(...)` into actual RM segment graphs. All 18
integer dictionary/set operations use the explicit unbounded heap service.
Frames retain local values across awaits. Lean checks each graph's translation,
frame interfaces, and composition with the heap/resumption model, for arbitrary
finite ticket sequences. No Paxos-specific generator is used by this path.

Run from this project:

```sh
uv run --no-project --python formal/.venv/bin/python -m zrth.verified \
  formal/.cache/reactive-modules/verification/examples/compiled_async.py \
  --coroutine --entrypoint step --out /tmp/compiled-async \
  --proof formal/.cache/reactive-modules/verification/proofs/compiled_async.lean \
  --theorem AsyncDictionary.round_trip
```

This proves the compiled example returns its stored value for all integer
keys/values, assuming its three requests are served from an empty heap.
`formal/verify_libraries.py` includes this proof and saved async regressions.
Parsing and async/frame elaboration remain trusted; Python runtime agreement is
differentially tested, not a CPython theorem. The native Rust/tensor runtime is
not the certified interpreter. See upstream
[ASYNC.md](.cache/reactive-modules/verification/ASYNC.md).

This smaller explicit-Request entrypoint still rejects native `d[key]` syntax,
awaits in branches/loops, and async helpers. Use the native-source frontend above
for those constructs. `algorithm.py` and its existing bugs remain unchanged.

## Earlier strict-scalar contribution

Development branch:
[Flecart/reactive-modules:feat/strict-python-frontend](https://github.com/Flecart/reactive-modules/tree/feat/strict-python-frontend).
The exact revision consumed here is recorded in `config.json` and the generated
RM manifest. The contribution is pushed on a branch; it is not merged into main.

The compiler changes are in `python/zrth/analyzer.py`, `strict.py`, and
`builder.py`, with algorithm-independent tests in `python/tests/test_strict.py`
and `test_builder.py`. They add:

- Opt-in `convert_method(..., strict=True)`, validating source syntax before
  early-return normalization.
- Explicit errors for unsupported effects, control flow, calls, async code,
  and mutation, rather than silently skipping them.
- Source filename, line, and column in diagnostics.
- Annotated assignments and checks against conflating locals with state fields,
  shadowed builtin calls, non-Boolean conditions, non-scalar shapes, and integer
  literal truncation.
- The LIA Boolean-constant fix previously implemented as a local workaround.

The default permissive behavior remains available to upstream's delegated gym
environments. Strict mode defines a supported subset; it is not a theorem that
the compiler preserves all Python behavior. Sort declarations remain explicit.

## Run the upstream regression tests

The bootstrap environment has the editable upstream package. Install its test
runner if necessary, then run from the Paxos repository root:

```sh
uv pip install --python formal/.venv/bin/python pytest
formal/.venv/bin/python -m pytest -q formal/.cache/reactive-modules/python/tests
```

To omit the unrelated reinforcement-learning training tests, append:

```sh
--ignore=formal/.cache/reactive-modules/python/tests/gym/test_training.py
```

The Python changes do not require rebuilding the Rust extension in an existing
editable checkout. A fresh environment should use `python3 formal/bootstrap.py`.

## Further work beyond the current native profile

The handwritten lowering has **not** been moved into upstream or renamed to
appear generic. It remains visible as `generate.py` for historical bounded proofs;
the direct-source compiler is a separate, reusable implementation.

1. Mechanize more of the currently trusted AST-to-instruction elaboration.
2. Extend the declared Python/value profile, including additional container
   APIs, cyclic graphs, general exception handlers, and asyncio facilities.
3. Compose native actors with explicit network contracts and author safety and
   liveness statements for that unbounded model; do not transfer the old bounded
   results merely by changing their labels.
4. Retire the historical generator only when its separately scoped property
   suite has an appropriate replacement.

Each compiler feature should first have tests unrelated to Paxos. Unsupported
source must remain a compilation error until its semantics is implemented.
