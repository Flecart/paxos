# Direct Python-to-Lean verification: implementation and research notes

This delivery targets verifier primitives: immutable values, flat collections,
borrowing, finite environmental choices, and complete-round message delivery.
It does not modify or verify `paxos_lab/algorithm.py`.

## Code map and artifact walkthrough

| Code | Responsibility |
| --- | --- |
| `rmverify/frontend.py`, `value_types.py` | Source validation, types, effects, borrows, helper resolution |
| `rmverify/typed_backend.py` | Typed source terms, native functions, correspondence and local property obligations |
| `rmverify/typed_composition.py` | Typed atoms, finite choices, wiring, ghost projection, complete-round witnesses |
| `rmverify/lean/Semantics.lean` | Canonical relational RM, reachability and induction; scalar source fragment |
| `rmverify/lean/TypedSource.lean` | Rich source execution, explicit outcomes, collection operations and permutation lemmas |
| `rmverify/lean/Borrowing.lean` | Access/loan and affine-use certificate predicates and theorems |
| `rmverify/lean/Network.lean`, `VeilAdapter.lean` | Observer execution preservation and Veil round correspondence |
| `rmverify/symbolic.py`, `lean_backend.py`, `recheck.py` | Diagnostic search, checked proof execution, audits and standalone replay |

After verifying `examples.delivery_spec:spec`, open the emitted
`Translation.lean`. `State` contains the Python fields and private fault fields;
`Sender.send_1` and the other named functions contain the compiled computation.
`atom0`, `atom1`, and the remaining atoms state ownership, inputs, initialization,
and transition relations. `composed` is the compiled RM machine. `sourceModule`
is constructed from interpreted source, and `source_module_eq` equates them.

`safe` conjoins requested predicates, strengthening, and absence of faults.
`Invariants.lean` proves this predicate on all reachable states, and
`always_safe` lifts it to every finite position in an arbitrary infinite round
sequence. `ghost_projection` and `ghost_extension` are in `Translation.lean`.
Broken examples add witness files proving an initial state, each actual round,
and the final violation. The reusable semantics files are fixed library inputs
for one evidence version; changing them changes the evidence identity.

## Representation and proof boundary

The implementation remains ordinary Python. A separate specification selects
methods, properties, optional strengthening, initialization choices, and wiring.
The frontend validates parsed source, resolves names, infers local types and
collection access effects, and retains source locations. Its structured terms
represent supported Python statements and expressions; they are not an RM graph.

`TypedSource.lean` interprets that source fragment. The compiler separately emits
named Lean functions and typed state structures. Each function receives a
correspondence theorem equating complete outcomes: updated state, return value,
and runtime fault. Composition adds checked adapters for connections and output
projections. Generated definitions cannot authorize a proof before these checks
pass. Simplifying total expressions and guarded optional values changes only the
native emitter; the original source interpreter checks the simplification.

The trusted boundary includes source extraction, name/type/effect resolution,
the interpretation of the supported Python fragment, and Lean's kernel with the
allowlisted standard axioms. This is not a formalization of the CPython parser,
heap, interpreter, or resource exhaustion. Differential execution is regression
evidence, never a substitute for a theorem. Outside mutation and concurrent
access during a selected atomic method are outside this execution model.

## Values, collection order, and faults

The supported values are mathematical integers, booleans, optional immutable
values, and plain frozen dataclasses with immutable fields. Record types are
nominal: two separately loaded Python classes are distinct even if their source
names agree. Extraction checks dataclass source and generated behavior, including
equality and hashing.

Dictionaries use ordered association lists. Overwriting a key retains its
position. Sets use duplicate-eliminating finite lists internally; their internal
enumeration is not a prescribed Python iteration order. Membership and size are
available for both; dictionary lookup/get/update and set add/discard are explicit
library operations. Mutable nesting and arbitrary object graphs remain outside
the agreed fragment.

Dictionary loops retain insertion order. Set predicates carry totality and
permutation certificates. Executable set loops carry a checked commutation
condition and a library theorem extending it to arbitrary permutations. The
condition compares full outcomes after discarding inaccessible loop-local
slots. It is sufficient, not a complete decision procedure for order independence.
A loop without an accepted certificate cannot receive `proved`.

Dictionary assignment evaluates its value before the target key; dictionary
construction evaluates each key before its value. Explicit `None` results and
`get` defaults still evaluate their subexpressions. Exact-fault regression
theorems check these distinctions, including writes made before failure. Witness
state keys preserve dictionary insertion order.

Missing dictionary entries and dereferencing absent optional records produce
explicit faults, retaining earlier writes. Faults are represented in machine
state rather than removed from reachability. A no-fault obligation is mandatory;
it can be checked independently of a failing user invariant.

## Ownership and helper calls

Aliases of state collections are borrows. Static checking permits shared reads or
exclusive mutation over inferred lifetimes. Branch/iteration-local borrows cannot
escape their scope. Mutable inputs are shared borrows, and cannot be mutated or
stored as another state owner. A freshly owned local collection can transfer to
state; subsequent use of the donor is rejected.

Lean checks finite access/loan certificates and affine-use certificates. These
check extracted permission facts; they do not claim to derive a Rust borrow
checker from CPython heap semantics. Diagnostics retain both conflicting source
locations. No permissions annotation language is added.

Nonrecursive free helpers are checked as pure computations. Effectful method
helper calls are accepted as statements or as the immediate value of an
assignment/return; arbitrary expression nesting of effectful calls is rejected. Method helpers can
mutate their owner's state. Their calls have source semantics that merge callee
writes back into the caller, including writes preceding a fault. Helper returns
resume the caller; they do not return from the public transition. Borrow checking
accounts for inferred helper reads and writes.

## RM rounds, choices, and instrumentation

`Semantics.lean` supplies the common relational RM and invariant induction.
Each atom owns disjoint coordinates. Ordinary connections read the old snapshot;
`Await` connections read the candidate new snapshot. Await dependencies must be
acyclic. Independent atom stuttering and simultaneous advancement remain part of
a round. Typed compositions own a separate fault coordinate per atom.

Single-class specifications quantify over all well-typed method arguments.
Compositions bind every input explicitly. Finite control alternatives and finite
`Choice` domains do not bound the integer state space or execution length.

`Choice(domain)` selects from a finite old-state collection, a pure domain
function, or a finite literal domain. Empty domains disable that alternative.
Stuttering or another unconditional alternative supplies nonblocking behavior.
Typed relation predicates compare fault-free endpoints. Their equivalence
theorems quantify over arbitrary such states, while the separate no-fault theorem
connects this scope to executions. A relation mismatch can therefore be
unreachable and is reported separately from a reachable safety violation.

The generated checks include ownership, permitted reads, await order, source
agreement, nonempty initialization, and nonblocking rounds.

A ghost component is a deterministic observer with one initializer and one
transition. Executable components cannot read its fields or use them in choice
domains. The generated observer correspondence identifies the full machine with
a deterministic lift of its executable projection. Lean proves both directions:
projecting an instrumented run yields an executable run, and every executable run
can be extended with ghost history. This is an execution-preservation statement,
not merely a check that ghost fields are absent from one predicate.

The delivery example separates sender, network, receiver, and history observer.
The sender numbers immutable messages; the network collects, delays, drops, and
selects previously collected messages, including repeated selection and arbitrary
reordering. Receiver consistency and observer history express duplicate safety
and no fabrication. Fairness, eventual delivery, crashes/restarts, and real sockets
are not modeled.

## Automation, counterexamples, and evidence

Lean reduction, standard lemmas, arithmetic automation, and `grind` run first.
Veil's SMT fallback explicitly disables trust and requests proof reconstruction.
The final theorem dependency audit permits only `propext`, `Classical.choice`,
and `Quot.sound`. A solver answer, reconstruction failure, admission, stale source,
or timeout cannot authorize `proved`.

Veil diagnostic queries distinguish counterexamples to induction from bounded
symbolic traces. Their raw models remain candidates. Python enumeration and Z3
also propose witnesses; a refutation requires a separate Lean proof of the actual
initial state, every complete round, and the final violation. Search limits bound
witness discovery, not successful invariant theorems.

Evidence format version 4 includes source snapshots, extracted source semantics, generated RM
functions, correspondence and property theorems, witnesses, dependency pins,
checksums, timing measurements, and axiom audits. Standalone replay uses the
pinned Lean dependencies and a copied standard-library Python script; it does not
import or rerun the Python verifier.

## Checked duplicate trace

The broken receiver's automatically discovered witness has four complete rounds.
The source correspondence, round reachability, and final violations are all
checked in Lean; the receiver's separate no-fault theorem still passes.

| Round | Sender serial | Pending IDs | Delivered ID | Processed IDs | Count | Repeated flag |
| ---: | ---: | --- | --- | --- | ---: | --- |
| Initial | 0 | {} | None | {} | 0 | false |
| 1 | 1 | {} | None | {} | 0 | false |
| 2 | 1 | {0} | None | {} | 0 | false |
| 3 | 1 | {0} | 0 | {0} | 1 | false |
| 4 | 1 | {0} | 0 | {0} | 2 | true |

This refutes count consistency and at-most-once processing. It does not refute
unviolated predicates. The generator proves invariant clauses jointly with their
strengthening; failure of that joint induction can leave other clauses unknown.
Only independently closed obligations or checked violations receive a stronger
status. General invariant synthesis and complete proof search remain outside the
agreed scope.

## Independent reference model

The repository contains the requested TLA+ examples at revision
`ceeaa904140e3e03781cb2a79cd6c6d8b8b08e10`, with their MIT license and file hashes.
`Lock.tla` is useful as a small independent relational reference. Its two program
counters have four labels, and each step advances one selected process or
stutters. The Python translation has a separate round predicate. A second Lean
transcription retains an enum for the TLA+ labels and checks correspondence under
an explicit state encoding. The manual TLA+-to-Lean transcription remains part of
the reference-comparison boundary; there is no claim of a verified TLA+ parser.

This reference has different scheduling from the independently advancing RM
Peterson atoms. `LockHS.tla` also adds scheduling behavior, so it is not silently
treated as a passive history observer. The Paxos reference's set of messages ever
sent informs the network history model. Its README explicitly notes that its
candidate invariant is not inductive. No Paxos protocol theorem is inferred from
these primitive and reference checks.

## Validation measurements

Measured on 2026-09-14 with Python 3.13.9 and pinned Lean 4.32.0. Each run
creates fresh evidence with dependencies already built. Library compilation,
source correspondence, property proofs, and audits are included. Other checks
ran concurrently: these are descriptive samples, not isolated performance claims.
The historical graph measurements below were recorded on 2026-09-11 with Lean
4.30.0; the toolchain and obligation differences prevent attributing timing changes
solely to compilation architecture.

| Example | Pipeline | Result | Wall time, s | Translation.lean bytes | All top-level Lean bytes |
| --- | --- | --- | ---: | ---: | ---: |
| examples.counter_spec:spec | Historical graph | proved | 10.30 | 7,329 | 18,707 |
| examples.peterson_v2:peterson | Historical graph | proved | 96.08 | 40,093 | 54,106 |
| examples.counter_spec:spec | Direct, version 4 | proved | 17.96 | 8,867 | 42,683 |
| examples.peterson_v2:peterson | Direct, version 4 | proved | 77.48 | 40,490 | 77,144 |
| examples.registry_spec:spec | Direct, version 4 | proved | 145.54 | 26,326 | 63,614 |
| examples.delivery_spec:spec | Direct, version 4 | proved | 163.21 | 141,941 | 179,823 |

`Translation.lean` includes native definitions and correspondence/certificate
proof scripts. The total counts shipped reusable library sources as well as
generated files; not every library is compiled for every scalar example.
`recheck.json` identifies the actual accepted obligations. These are text-size
measurements, not serialized kernel proof-term sizes. Additional checks and
semantics increase the source footprint; no general size-reduction claim follows.
Raw timings, hashes, pins, and local evidence paths are in
[full-measurements.json](full-measurements.json).

Reproduce the measurements from the repository root:

```sh
formal/.venv/bin/python formal/benchmark.py --out formal/.rmverify/full-measurements --timeout 180 --spec examples.counter_spec:spec --spec examples.peterson_v2:peterson --spec examples.registry_spec:spec --spec examples.delivery_spec:spec
```

The installation check uses a separate source copy and Python environment with
no `reactive-modules` directory. Only `rmverify` and pinned `z3-solver` are installed
in that environment; the pinned Lean package cache is reused. This checks the
verifier's independence from the old RM submodule, not a dependency-free cold
installation. A cold Veil build additionally needs clang/libc++ headers and its
pinned Lake dependencies.

Final validation passed:

| Check | Result |
| --- | --- |
| Existing scalar, composition, paper, collection and negative fixtures | 35 tests passed |
| Records/options, helpers, borrowing/transfers, collection order, delivery and TLA+ comparison | 19 tests passed |
| Real Veil reconstruction, rejection of trust-enabled results, and diagnostic witness kinds | 1 test passed |
| Network evidence replay without the Python verifier | 7 accepted obligations rechecked |
| Broken-network evidence replay without the Python verifier | 9 accepted obligations rechecked |
| Isolated installation without the RM submodule | Counter and registry proved; final registry rerun proved |

The 35-test suite took 1,095.96 seconds, the 19-test suite 1,122.67 seconds,
and the automation test 22.62 seconds; these runs overlapped. Negative fixtures
pass their tests by receiving the expected checked refutation, rejection, or
unknown result. The correct delivery example proves all requested invariants and
strengthening over unbounded reachability. The broken receiver receives checked
refutations for count consistency and at-most-once processing.

The reference test proves initial-state and complete-round equivalence with the
independent Lean transcription of `Lock.tla`, as well as the source-level round
correspondence. It also verifies the vendored reference hashes. This comparison
does not prove correctness of a TLA+ parser or of the Paxos reference itself.

```sh
formal/.venv/bin/python -m unittest formal.test_rmverify formal.test_composition formal.test_paper formal.test_collections formal.test_values formal.test_primitives formal.test_delivery formal.test_reference formal.test_automation -v
python3 PATH_TO_EVIDENCE/recheck.py
```

Evidence directories are generated outputs and remain untracked. The CLI prints
their paths; the measurement JSON records the measured local bundles. Every
bundle contains the pinned sources and standalone replay script. Published reports
from earlier pipelines remain historical evidence for their recorded versions.
