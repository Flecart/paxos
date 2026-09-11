# rmverify: Python → Lean RM definitions → checked theorem

`rmverify` checks a small typed Python fragment. Implementations remain ordinary
Python; separate `Specification` and `Composition` objects select transitions,
properties, strengthening, and component connections. The current direct pipeline
supports the existing scalar examples and a first single-class collection subset. It does **not** verify
`paxos_lab/algorithm.py`.

The old SSA/`zrth`/ordered-wire compiler and its Lean interpreter have been removed.
The frontend validates a structured source tree. The backend emits typed Lean
functions with native integer/Boolean operations, `do` blocks, mutable locals, named output
records, and Python field names. Lean independently interprets the extracted
source and proves agreement on state and return values. Generated definitions are
untrusted until those correspondence proofs pass. Additional checked equations validate
state/input projections, invariant connections, and collection-method return
adapters; regression tests deliberately corrupt these adapters.

## Install and run

Requirements: Python 3.12–3.13, uv, Git, elan, and Node/npm (for Veil's upstream widget build). No Rust, Torch, Maturin, or
initialization of `formal/reactive-modules` is required.

```sh
python3 formal/bootstrap.py
formal/.venv/bin/python -m rmverify examples.counter_spec:spec
formal/.venv/bin/python -m rmverify examples.collections_spec:spec --timeout 60
formal/.venv/bin/python -m rmverify examples.collections_spec:registry --timeout 60
formal/.venv/bin/python -m rmverify examples.receiver_spec:receiver --timeout 60
formal/.venv/bin/python -m rmverify examples.receiver_spec:broken_receiver --timeout 60 --depth 2
formal/.venv/bin/python -m rmverify examples.programs:transfer
formal/.venv/bin/python -m rmverify examples.programs:register
formal/.venv/bin/python -m rmverify examples.programs:renamed
formal/.venv/bin/python -m rmverify examples.peterson_v2:peterson --timeout 120
formal/.venv/bin/python -m rmverify examples.peterson_stuck:peterson --timeout 120
```

Bootstrap installs the local Python package and builds the Lean library. Lean
4.32.0, Veil, and all its transitive Lake dependencies are pinned in
[`rmverify/lean/lake-manifest.json`](rmverify/lean/lake-manifest.json). The first
build downloads those dependencies. The Python dependency is pinned Z3, used only
to propose witnesses. The upstream RM submodule remains pinned for historical
reference and comparison; it is not an installation or verification input.

`python3 formal/verify.py` remains the counter shortcut. The counter itself runs
with `python3 formal/counter.py -5 0 7 7 3 12`.

## Annotation policy

| Information | Where it comes from |
| --- | --- |
| State, argument, and return types | Ordinary Python annotations |
| Local types and source field access | Inferred during validated extraction |
| Selected public transitions | Separate specification |
| Component ownership and connections | `Component.controls` and `inputs` |
| Old versus current-round inputs | String binding versus `Await(variable)` |
| Correctness properties | Explicit Boolean predicates |
| Strengthening | Optional predicates, proved together with the invariant |
| Constructor choices | Explicit finite domains; Boolean parameters default to both values |

```python
from counter import Counter
from rmverify import Specification, Contract, Call, Trace

def nonnegative(state: Counter) -> bool:
    return state.value >= 0

def monotone(before: Counter, after: Counter,
             result: None, offered: int) -> bool:
    return after.value >= before.value

spec = Specification(
    target=Counter,
    transitions=[Counter.step],
    invariants=[nonnegative],
    contracts={Counter.step: Contract(ensures=monotone)},
    checks=[Trace([Call("step", offered=-5), Call("step", offered=7)])],
)
```

Use inspectable definitions in `.py` files. Invariants receive one state.
Preconditions receive the old state and method arguments. Postconditions receive
old state, new state, result, and method arguments. Preconditions qualify
postconditions only: they do not remove calls from invariant reachability.
`strengthening` predicates are proved, never assumed. The unstrengthened example
remains `unknown` if induction fails without a reachable counterexample.

The scalar fragment supports `int`/`bool` fields, annotated synchronous methods,
locals, assignment, branches, early return, `+`/`-`, literal multiplication,
comparisons, Boolean operators, conditional expressions, and binary `min`/`max`.
Integers are mathematical, unbounded integers. Conditions must be Boolean.
Unsupported code, missing annotations, dynamic class behavior, and stale loaded
functions are rejected. Field/parameter names are not reserved verification APIs.

## Collection and borrowing checkpoint

`examples/collections_spec.py` exercises a dictionary and a set, repeated
registration, lookup immediately after insertion, and discard of an absent ID.
The storage contract asserts that registration stores `7` and that overwriting
an existing key does not increase the dictionary's length. The `registry`
specification uses arbitrary integer payloads: it checks agreement between the
key domain and ID set, preserves the first payload on duplicate registration,
and checks that duplicate registration does not increase the count. It exercises
an exclusive local borrow. Frozen message records and the network remain outside
this checkpoint.

The single-class frontend accepts flat `dict[K, V]` and `set[K]`, with `int` or
`bool` keys/elements/values. It supports empty construction, membership, `len`,
dictionary lookup/assignment, `get(key, default)`, and set `add`/`discard`.
Single-generator `all`/`any` predicates are supported without filters. Plain
`for key in dictionary` loops preserve insertion order; mutation of that dictionary
while iterating is rejected. Ordinary executable set iteration is rejected.
Set quantifiers must be total: potentially failing subscripts in their bodies
are rejected. The Lean library proves that total Boolean quantifiers are invariant
under permutation of the set's internal enumeration.

`TypedSource.lean` provides the typed source interpreter, ordered dictionary
operations, set operations, and explicit outcomes. Generated typed frames hold
collections directly rather than encoding them into integer slots. Variable
projections/updates and the whitelist of builtin operations remain part of source
extraction's trust boundary. Lean checks equality between interpreted source and
the generated functions, including state changes and faults. Loop correspondence
can pass even when invariant automation cannot close the safety proof; that
property remains `unknown`.

A failed lookup produces `missingKey` and preserves writes made before it failed.
The generated machine retains that fault in an absorbing state. Every collection
verification requires the separate `no-fault` property, including specifications
that request only contracts. Concrete search can propose a `reachable_fault`
witness; only a successful Lean replay permits a refutation. This search explores
at most 256 concrete states with small scalar arguments. That limit never bounds
the scope of a successful safety theorem. Collection search also proposes reachable invariant violations. Collection contract
counterexample discovery is not implemented yet.

Mutable aliases are checked conservatively without runtime annotations. A local
alias of a collection is a borrow lasting through its last syntactic use. Multiple
shared borrows or one exclusive borrow are accepted; conflicting reads/writes
identify both source locations. Borrow creation inside branches/loops, borrow
rebinding, mutable returns, state-to-state ownership transfers, and mutable method
arguments are rejected. These are frontend checks, not a formalization of Python's
whole heap or a complete Rust borrow checker. Accepted code still has ordinary
Python aliasing behavior.

`examples/receiver_spec.py` adds a receiver core under arbitrary repeated IDs.
It checks count/set consistency and that duplicate delivery does not increment
its count. The broken receiver increments on every delivery; search discovers
two deliveries of one ID and Lean checks the resulting reachable violation.
This single-class example does not yet establish network no-fabrication.

See the [step-by-step walkthrough](reports/collections-checkpoint.md) for the
small examples, generated definitions, mutation tests, and remaining boundaries.

Run the small end-to-end checks with:

```sh
formal/.venv/bin/python formal/test_collections.py -v
```

`Network.lean` separately proves old-state finite-choice facts and that a
deterministic observer can be added to/projected away from complete RM rounds.
These are **library primitives only**: `Choice(domain)` and ghost components are
not connected to Python `Composition` yet. Collection-valued composition is
explicitly rejected rather than sent through scalar wiring.

## RM and Veil semantics

Composed processes are independent atoms. Each may stutter independently, and
several may advance simultaneously in one round. Plain input bindings read the
old snapshot even if the producer advances; `Await` reads the candidate new
snapshot. Duplicate owners, missing bindings, wrong types, and await cycles are
frontend errors. Lean checks ownership/await ordering and atom read dependencies,
source/definition agreement, nonempty initialization, and nonblocking rounds.

The two-component Peterson example covers all four initial flag valuations and
proves equality with its separately specified round relation. The combined
Peterson example in `examples/paper.py` is a **historical specialization** with
external run selectors and one concrete constructor state.

Single-class reachability has a proved equivalence with a one-atom relational RM.
Its invariant induction uses the same RM induction theorem as composition.
[`VeilAdapter.lean`](rmverify/lean/VeilAdapter.lean) maps each **complete round**
to Veil's transition interface and proves initial, round, and reachable-state
correspondence. Generated invariant theorems also cover that Veil representation.
`veil.smt.trust` is explicitly false. The current automation uses Lean reduction,
standard-library lemmas, `omega`, and `grind`; witness proposals currently use Z3.
Veil SMT reconstruction and Veil symbolic trace discovery are not connected yet.
For small integer intervals suggested by property literals, automation may prove
a bound from the induction hypothesis and enumerate those cases. A failed bound
proof falls back to symbolic checking; guessed bounds never restrict executions.

## Results and evidence

```sh
formal/.venv/bin/python -m rmverify module:spec --out .rmverify --timeout 120 --depth 10
formal/.venv/bin/python formal/test_rmverify.py -v
formal/.venv/bin/python formal/test_composition.py -v
formal/.venv/bin/python formal/test_paper.py -v
```

| Status | Meaning |
| --- | --- |
| `proved` | Lean accepted correspondence and all claims with approved axiom dependencies. |
| `refuted` | Lean replayed an invariant/contract violation, runtime fault, or relation mismatch. |
| `unknown` | Proof/search did not establish either result, including timeouts. |
| `unsupported` | The program/specification is outside the supported fragment. |
| `error` | Tooling, correspondence, stale inputs, or concrete checks failed. |

`report.ok` and the CLI's zero exit status require every requested claim proved.
A failed inductive step is not a reachable counterexample. Composition witnesses
use distinct `reachable_invariant` and `relation_mismatch` kinds. Relation
equivalence ranges over all valuations, so a mismatch need not be reachable.
`peterson_stuck` retains proved safety while receiving a checked missing-round
counterexample. Search depth bounds discovery only; successful invariants cover
unbounded executions.

Evidence version **3** contains:

- `artifact.json`: source/specification identity, extracted source semantics,
  field and atom metadata, dependency versions, and a content hash; no RM graph.
- `sources/`: content-addressed copies of the actual Python source files.
- `Translation.lean`: generated typed definitions and source correspondence.
- `Semantics.lean`, `TypedSource.lean`, `Network.lean`, `VeilAdapter.lean`, and pinned
  Lake files: reusable semantics and the complete-round Veil adapter. Only the
  modules listed in `recheck.json` were compiled for that evidence bundle.
- Property/witness `.lean` files and `.log` files, including final axiom audits.
- `timings.json`, `report.json`, and `recheck.json`: timings, statuses, and exact
  accepted obligations plus hashes for standalone replay.

To recheck accepted obligations without importing/running the Python verifier:

```sh
python3 PATH_TO_EVIDENCE/recheck.py
```

Only Python's standard library and the pinned Lean dependencies are needed for
replay. When moving evidence to another machine, discard `.lake` (a build cache
which may contain a local dependency symlink); Lake reconstructs it from the
included manifest. Replay checks hashes and axiom audits and does not upgrade
unknown claims. Only `propext`, `Classical.choice`, and `Quot.sound` are accepted.
A solver response, admission, timeout, or stale evidence cannot authorize `proved`.

The trust boundary remains source extraction, name/type resolution, the specified
semantics of the supported Python fragment, and Lean's kernel/standard axioms.
Correspondence does not formalize the Python parser or all CPython execution.
Differential probes are regression evidence. Outside mutation, unselected calls,
resource exhaustion, and concurrent access are outside this atomic-call model.

## Reports and remaining migration

See the [measured comparison](reports/direct-pipeline.md) for proof-source sizes,
wall times, methodology, and reproduction commands.

The published `reports/fmsd99.*` and `reports/peterson-v2.*` files are historical
graph-pipeline evidence for their recorded hashes. The report generators now emit
`fmsd99-direct.html` and `peterson-direct.html` without replacing those records:

```sh
formal/.venv/bin/python formal/paper_report.py
formal/.venv/bin/python formal/composition_report.py
```

The requested Paxos preparation is **not complete**. Frozen dataclass records,
optional messages, general typed helpers, nonempty collection literals, full
ownership transfer, collection-valued composition, Python `Choice(domain)` and
ghost bindings, the frozen-message registry, and the duplicate-safe network proofs remain. General
loop/invariant proof automation is also incomplete; adding syntax does not make
its safety properties automatically provable. The network lemmas above establish
useful foundations, not verification of a Python network or Paxos.
