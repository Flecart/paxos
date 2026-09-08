# Python → RM → Lean learning model

This directory formalizes the current `paxos_lab/algorithm.py` without repairing
its algorithm. It is a **source-specific, bounded translation**, not a general
Python compiler and not a proof that the implementation is correct.

## Run

From the repository root, the installed environment can be checked with:

```sh
python3 formal/verify.py
```

This repeats six abstraction-boundary tests, the original/Python/RM differential checks, the Z3 checks, exports
Lean from the RM artifact, runs `lake build`, and prints theorem axioms using
`Audit.lean`. To also rebuild the Python AST
and actual upstream RM, use `python3 formal/verify.py --recompile`. Compilation
and a cold Lean build take several minutes. `--skip-lean` runs the Python checks
without the Lean build.

On a fresh machine (requires uv, Rust/Cargo, a C/C++ compiler, and elan/Lean):

```sh
python3 formal/bootstrap.py
cd formal/lean
lake update
cd ../..
python3 formal/verify.py --recompile
```

Bootstrap uses uv to create an isolated Python 3.13 environment and installs the
CPU-only PyTorch dependency required by the upstream Rust/Python compiler.
Lake fetches CSLib and mathlib; their caches can require several GB. Neither the
root Python environment nor the original algorithm is rewritten.

## The compilation chain

```text
algorithm.py (hash-pinned, unchanged)
  → generate.py → generated/node.py (ordinary scalar Python)
  → upstream zrth.analyzer.convert_method → actual zrth.Module
  → compile_rm.py → generated/rm.json (the module's init/update wire DAG)
  → export_lean.py → Lean RM interpreter + three-node network + properties
```

`generated/node.py` is the requested analyzer-compatible Python: attributes,
assignments, conditionals, scalar arithmetic, and no sugar DSL. Dictionaries,
sets, and Counters are flattened with explicit presence flags and insertion
ranks. `generated/manifest.json` documents the fields, events, source regions,
continuation states, and failure states. This is deliberately specific to the
source hash in `config.json`. After you edit the algorithm, **review and update
the lowering**, then update the hash; changing the hash alone does not translate
your change.

The actual [reactive-modules compiler](https://github.com/Flecart/reactive-modules/tree/66bdb2d37d4c2fb925c103f8088b43653773d298)
is pinned to `66bdb2d37d4c2fb925c103f8088b43653773d298`. A small local builder
subclass works around that revision's nonexistent `LIA.Const` Boolean
constructor by calling its real `LIA.Bool` constructor. No upstream source is
edited. The export refuses unsupported RM operators. Python and Lean interpret
the exported DAG with mathematical integers, not floating point or machine-word
overflow. The DAG has 721 controlled state fields and 27,191 update terms.

The [CSLib dependency](https://github.com/leanprover/cslib/tree/d0c137a2e65bb13d906be55bcde4fecaa7972c0b)
is pinned to `d0c137a2e65bb13d906be55bcde4fecaa7972c0b`, compatible with Lean
4.30.0. The model directly reuses `Cslib.LTS`, `LTS.MTr`,
`LTS.OmegaExecution`, and `ωSequence.LeadsTo`. `PaxosFormal/CSLib.lean` proves
the reachability/execution bridges and uses CSLib's temporal composition lemma.
The project-specific part is the RM wire interpreter and network semantics.

## Scope and preservation

- Three nodes, each running the same proposer/acceptor/learner hooks.
- Numbers and Counter counts bounded at 31; 32 queued or in-flight messages.
- Values are `None`, `"A"`, `"B"`, and Python integers `0`, `1`, `2`.
  The encoded values are respectively `0, 1, 2, 3, 4, 5`; node IDs are `0, 1, 2`.
  Integer values are included because their equality with dictionary number
  keys is observable in the source. This is not a value-symmetry reduction.
- Successful, authentic, exactly-once delivery, with arbitrary transmission
  order and per-receiver FIFO processing. No TCP failures, malformed messages,
  restarts, timeouts, or backoff/retry failures are modeled.
- Client proposals and ticks are explicit events. A node executes hooks
  serially. Sends suspend at the actual `await`; receivers can process a packet
  before its sender resumes. A broadcast's three deliveries are separately
  schedulable. Repeated client calls model the hook API, not just CLI startup.
- Existing Counter behavior, ignored fields, number handling, rejection rules,
  decision-print versus stored-value distinction, and source exceptions remain.
  `status = 1` records an uncaught source exception and halts that node;
  `fault = 1/2` distinguishes `KeyError`/`IndexError`.
- `status = 2` or a queue overflow means **outside the abstraction**, never
  success or an algorithm exception. Statements exclude out-of-scope and invalid
  schedules. Unknown JSON values, unhashable values, and Boolean values are not
  covered. Ordinary diagnostic text is omitted; decision announcements are
  explicitly observed and checked.

The abstraction is reviewed and differentially tested, not backed by a theorem
about Python's complete language/async semantics. It makes no unbounded claim.
History monitors are mathematical lists; no exhaustive finite-state search is
claimed just because the node data and live queues have bounds.

## Safety and liveness statements

The RM graph drives `nodeStep`; `PaxosFormal/Network.lean` composes three such
nodes and defines the predicates over their histories. A value is **chosen**
when two distinct acceptors emitted acceptance replies for that value and the
same number. This is majority choice, not unanimous state equality. Choice
history is retained across later proposals.

| Statement | Meaning |
| --- | --- |
| Agreement | At most one value is ever chosen. |
| Validity | Every chosen value was submitted by a client. |
| Decision accuracy | Every printed majority decision names a chosen value. |
| Decision consistency | All printed decisions name the same value. |
| Proposal liveness | A submitted proposal leads to some chosen value. |
| Learning liveness | A chosen value leads to every node announcing a chosen value. |

`Safety` universally quantifies over reachable states and conjoins the four
safety predicates. `ProposalLiveness` and `LearningLiveness` use CSLib's
`LeadsTo`; they do not mistake a finite execution for an infinite proof.
The original has no separate learner callback, so the optional learning
statement observes its majority-decision print. An acceptor merely storing a
value is not counted as that announcement.

`FairSchedule` explicitly states weak fairness for FIFO head delivery and each
node's message handling, send resumption, and ticks. `SingleProposer` and
`BenignLiveness` expose a one-proposer environmental profile. They are
**specifications, not assumed theorems**. In particular, forced infinite ticks
can exhaust the finite number bound. Non-vacuity of that bounded fair profile
has not been proved; do not use an empty set of fair executions to claim
liveness. An unbounded model or a justified finite-prefix progress statement
is needed before drawing conclusions about an indefinitely running deployment.

## Evidence and remaining obligations

| Claim | Evidence/status |
| --- | --- |
| Original ↔ flattened Python ↔ RM on seven saved schedules | All local states, Counter order, sends, decision announcements, and exceptions match. Not exhaustive. |
| Saved schedules execute with the reported final predicates | Lean `native_decide` replays the actual RM/network. Finite witnesses only. |
| Scalar instruction execution follows its list relation | Lean induction theorem `executeList_correct`, connected to the actual Array interpreter by `execute_correct`. |
| CSLib reachability and scheduler bridges; temporal composition | Lean proofs. |
| Unconditional proposal liveness | Refuted in Lean: submit once, then let delivery wait forever. This schedule is unfair. |
| Non-None acceptance is immutable in one RM step | Z3: negation UNSAT, not a Lean theorem. |
| An acceptance reply matches recorded accepted value | Z3: negation UNSAT, not a Lean theorem. |
| Universal `Safety` | Open; no full inductive proof or exhaustive exploration supplied. |
| Liveness under a non-vacuous fair environment | Open. The unfair counterexample says nothing about this case. |
| End-to-end compiler/refinement correctness | Open beyond the stated interpreter theorem and differential checks. |

`generated/checks.json` and `trace_*.json` contain repeatable schedules and local
states, including a source-exception witness. `generated/smt_results.json`
keeps solver evidence separate from Lean proofs. None of the scenario results
constitutes a Paxos repair or a general correctness certificate.

The Lean files contain no `sorry` or handwritten algorithm-correctness axioms.
Concrete witnesses use `native_decide`, so their trust base includes Lean's
native evaluator and compiler, in addition to the kernel and library axioms.
On this Lean version, `Audit.lean` reports compiler-generated axioms named
`..._native.native_decide.ax_1_1` for those concrete checks. They are not
kernel-only reduction proofs. The ordinary relational and CSLib bridge proofs
are audited separately.
The RM exporter and source lowering are also part of the end-to-end trust
boundary. `nodeStep_is_exported_RM` is a definitional identity, **not** a proof
that the upstream Python compiler preserves all Python behavior.
