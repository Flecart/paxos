# rmverify: executable Python + properties → Lean evidence

`rmverify` is a reusable verifier for a deliberately small typed Python language.
The library discovers state/input types, compiles to real reactive-module terms,
and generates Lean proofs. Application authors supply code, predicates, and
optional traces. There is no per-program compiler or handwritten Lean proof.

The examples include a counter, two-account transfer, Boolean register, and a
renamed-field program. `paxos_lab/algorithm.py` is unchanged and is not verified;
its containers, effects, and async behavior need future shared language support.

## Install and run

Requirements: Git, uv, a Rust/C++ build toolchain, and elan. From the repository root:

```sh
git submodule update --init --recursive
python3 formal/bootstrap.py
formal/.venv/bin/python -m rmverify examples.counter_spec:spec
formal/.venv/bin/python -m rmverify examples.programs:transfer
formal/.venv/bin/python -m rmverify examples.programs:register
formal/.venv/bin/python -m rmverify examples.programs:renamed
formal/.venv/bin/python formal/test_rmverify.py -v
```

`python3 formal/verify.py` remains a shortcut for the counter. The executable
counter itself runs with `python3 formal/counter.py -5 0 7 7 3 12`.

Bootstrap builds the pinned upstream `zrth` extension and installs the local
`formal/` package into `formal/.venv`. Upstream currently requires CPU PyTorch
and Python 3.12–3.13; bootstrap selects 3.13. Lean 4.30.0 is pinned and uses only
`Std`: no mathlib, CSLib, external proof oracle, or verification-branch dependency.
The package carries its shared Lean semantics, so the CLI also works outside this
repository when run with the installed environment.

## User interface

The implementation remains ordinary Python:

```python
class Counter:
    value: int

    def __init__(self) -> None:
        self.value = 0

    def offer(self, offered: int) -> None:
        if offered > self.value:
            self.value = offered
```

Use inspectable definitions in `.py` files and put the specification in an
importable Python module:

```python
from rmverify import Specification, Contract, Call, Trace, verify

def nonnegative(state: Counter) -> bool:
    return state.value >= 0

def monotone(before: Counter, after: Counter,
             result: None, offered: int) -> bool:
    return after.value >= before.value

spec = Specification(
    target=Counter,
    transitions=[Counter.offer],
    invariants=[nonnegative],
    contracts={Counter.offer: Contract(ensures=monotone)},
    checks=[Trace([Call("offer", offered=-5), Call("offer", offered=7)])],
)

# In application/test code:
# report = verify(spec)
# assert report.ok, report.diagnostics
```

Use `python -m rmverify your_module:spec`. Constructor and selected method code
are the verification inputs; there are no reserved state, argument, or method
names. Annotate state fields on the class or on assignments in `__init__`.

- Invariants receive one state.
- Contract `requires` predicates receive the before-state, then method arguments.
- Contract `ensures` predicates receive before-state, after-state, result, then
  method arguments. All predicates return `bool`. Bindings are positional; use
  the target class annotation for state snapshots and the method's return type
  for the result, including `None` for methods returning nothing.
- Preconditions qualify postconditions only. They **never exclude method calls
  from invariant reachability**. For example, the deliberately broken example's
  positive-input contract is proved, while its unconditional invariant is refuted.
- `strengthening=[predicate, ...]` supplies additional Python invariants. They
  are proved together with the requested invariants, never assumed. The
  `unstrengthened`/`strengthened` examples demonstrate `unknown` becoming `proved`.
- Checks are concrete traces, with exactly named, correctly typed arguments.
  They compare original Python state/results with mathematical RM execution and
  evaluate predicates. They are regression evidence, not universal proofs.

## Supported language and execution

The first release supports plain classes with at least one `int`/`bool` field,
a zero-argument constructor, and selected synchronous instance methods with
explicit scalar argument and return annotations. Returns may be `int`, `bool`,
or `None`. Fields and locals have separate binding namespaces; every field must
be initialized and every read must be definitely assigned.

Supported operations are assignments (including annotated and augmented forms),
locals, branches, early returns, integer `+`/`-`, unary signs, multiplication by
integer literals, comparisons, Boolean `and`/`or`/`not`, conditional expressions,
and two-argument `min`/`max`. Predicates use the same language and cannot mutate
state. Integers are unbounded. Large literals and coefficients are constructed
with small scalar affine RM terms, without truncation or a repeated-doubling
expression explosion. Boolean operands must actually be Boolean, not numeric
truthiness or implicit Boolean/integer arithmetic.

Loops, arbitrary calls, containers, async, exceptions, floats, division,
nonlinear multiplication, inheritance, special object behavior, descriptors,
behavior-changing decorators, dynamic attributes, and default/variadic arguments
are rejected before compilation. Unsupported source reports a diagnostic rather
than silently dropping behavior. Loaded functions must match their source; reload
modules after editing code in an interactive process.

An execution is construction followed by arbitrary calls to selected methods,
with arbitrary correctly typed arguments. Each method call is atomic. Contracts
are checked on reachable states, using established invariants when available.
Outside mutation, unselected calls, resource exhaustion, and concurrent accesses
are outside this execution model. Code requiring input restrictions must enforce
them itself if an invariant needs those restrictions.

## What Lean checks

The shared frontend extracts a typed **structured source tree**, retaining
sequencing, branching, and early returns. The compiler separately lowers it to
SSA-like expressions, creates upstream RM terms, and exports the actual ordered
RM atoms. Lean has an independent structured statement interpreter and an
ordered-wire interpreter. Both use mathematical integers and Boolean 0/1 values.

Every constructor, method, and predicate gets a translation theorem equating the
two interpretations for all well-typed inputs. These theorems include state and
return values. Graph corruption and predicate corruption are acceptance tests:
a safe but incorrect compiled program cannot pass translation checking.

The generated `source_model_eq` and predicate agreement theorems connect the two
models. Generic induction proves initialization and preservation of the
conjunction of invariants. `always_safe` covers every instant of an infinite
execution. `source_invariant` and `source_contract` explicitly lift the accepted
claims to the structured source semantics. No program-specific proof script is
maintained; automation uses shared reduction laws, case splitting, and `omega`.

The trust boundary is **source extraction, name/type binding, the specification
of the supported Python semantics, and Lean's kernel/standard axioms**. Checking
correspondence removes the compiler/exporter's correctness from the trust needed
for these source-semantic claims. It does not prove the parser correct, formalize
all CPython behavior, or establish equivalence with native Rust/PyTorch fixed-width
execution. Hashes establish evidence identity, not semantic correctness. The
original executable Python is differentially tested as additional evidence.

## Results and evidence

Each invocation creates a fresh evidence directory (default `.rmverify/check-*`)
and prints a JSON report. Use `--out PATH`, `--timeout SECONDS` (default 60 per
Lean check/SMT query), or `--depth N` (default 10 method calls for witness search).
Proofs are unbounded; the depth only limits counterexample search. The Python API
accepts the equivalent `directory`, `timeout`, and `depth` keyword arguments.

| Status | Meaning |
| --- | --- |
| `proved` | Translation and exact proof obligations passed Lean and axiom auditing. |
| `refuted` | Lean checked a reachable trace violating an invariant or contract. |
| `unknown` | Proof checking/search failed or timed out, without a checked refutation. |
| `unsupported` | The program/specification exceeds the accepted language. |
| `error` | Tooling, translation, stale-source, or concrete-check failure. |

A failed inductive proof is not a counterexample: its problematic state may be
unreachable. Add strengthening predicates when needed. Z3 only proposes traces;
its `sat`/`unsat` responses never become proofs. Refutations require kernel replay.
Only `propext`, `Classical.choice`, and `Quot.sound` are accepted axioms; admissions
and native-evaluator proof shortcuts are rejected. `report.ok` and the CLI's zero
exit status require all requested claims proved and all supplied checks passed.

Evidence includes source/tool/upstream hashes, the structured source trees, typed
RM graphs, generated Lean sources, proof logs, a report, and any counterexample
traces. Input changes during checking invalidate the run. Earlier reports are
historical evidence for their recorded hashes; rerun verification after edits.

## Updating upstream

The submodule tracks `main`, currently pinned to
`66bdb2d37d4c2fb925c103f8088b43653773d298`. Updates are explicit:

```sh
git submodule update --remote --checkout formal/reactive-modules
python3 formal/bootstrap.py
formal/.venv/bin/python formal/test_rmverify.py -v
git diff --submodule=log
git add formal/reactive-modules
```

Review and commit the new pin only after the checks pass. The counter-specific
compiler and handwritten proof runner have been replaced. Existing untracked
`native-evidence/`, `protocol-evidence/`, and old ignored caches are not inputs.
Future collections, helpers, and async support must extend shared semantics and
translation checks once; Paxos must not acquire a separate verification-only
implementation.
