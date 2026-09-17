# Rust-to-Lean verification: delivery report

18 September 2026 · Branch `formal/counter-lean`

[Client presentation (PowerPoint)](rust-verification-delivery.pptx) ·
[PDF presentation](rust-verification-delivery.pdf) ·
[Specification guide](../rust/SPECIFICATIONS.md)

## Delivered result

The Rust verification pipeline now supports protocol-independent specifications.
The driver has no Paxos-specific proof dispatch: each example provides its own
claims and handwritten proof adapter. The former Paxos profile remains as a
small data-only compatibility definition.

Users can author commented TOML or JSON, select `invariant`, `always`,
`eventually`, `leads_to`, or a general Lean proposition, and preview the exact
claims and their assumptions before extraction. A crate directory automatically
finds its single `spec.toml` or `spec.json`. ZIP and standalone Rust inputs accept
an explicit specification path. Error messages identify invalid fields and
claims; compilation diagnostics point to Lean errors and retained logs.

The engine snapshots inputs, extracts supported Rust through Hax/Charon/Aeneas,
compiles specifications into propositions over reactive-module executions,
checks supplied or automatically attempted proofs, audits their axioms, and
saves evidence for replay. Successful claims are checked together; failed batches
fall back to individual checks so partial results remain useful.

This is a general proof pipeline, not a decision procedure for arbitrary Rust
or an English-to-proof system. Predicates, semantic adapters, and nontrivial
proofs still require Lean. The authoring interface removes repetitive temporal
syntax without hiding those obligations.

## Checked examples

| Example | Claims | Result and scope |
| --- | ---: | --- |
| [Paxos](../rust/paxos/spec.json) | 4 | Agreement, enabled local progress, conditional eventual quorum choice, and refinement into the protocol model |
| [Delivery](../rust/delivery/spec.toml) | 5 | Invariant, always, eventually, leads-to, and a theorem that fairness-free eventual delivery is false |
| [Pedersen](../rust/pedersen/spec.json) | 5 | Extracted-code refinement, honest-opening correctness, perfect hiding, binding reduction, and a transferred probability bound |

All **14 example claims** passed Lean checking and the transitive axiom audit.
The same pipeline also returned **refuted** for unconditional eventual delivery,
using a checked proof of its negation.

Paxos safety concerns successful learner certificates in every reachable state.
Liveness requires a stable responsive quorum and weak fairness. Its model uses
three non-Byzantine acceptors, authentic retained messages, unique ballots, and
serialized owned state. It proves eventual quorum choice, not eventual client
receipt or a time bound. Sockets, recovery and leader election are outside scope.

Pedersen hiding is equality of commitment distributions with fresh uniform
finite-field blinding and a generating `H`. Binding is an algebraic reduction:
two accepted openings with different messages yield the discrete logarithm of
`H` relative to `G`. An explicit bound on that reduction's success probability
bounds the binding-break probability. These are parametric theorems over lawful
backend operations, not a verification of a concrete curve, RNG, parameter setup,
constant-time implementation or asymptotic/PPT security framework. See the
[security scope](../rust/pedersen/README.md) for the exact premises.

## Validation performed

The final complete Rust pipeline suite passed: **12 tests, no failures or skips,
450.597 seconds** on this workstation.

```sh
RMVERIFY_RUST_INTEGRATION=1 python3 -m unittest formal.test_rust_pipeline -v
```

The suite covers:

- All three examples and all five claim forms.
- Rechecking accepted proofs and a checked refutation from saved evidence.
- Crate, ZIP (including a crate with a binary), and standalone Rust inputs.
- TOML/JSON equivalence, spec discovery, visible assumptions and input validation.
- Archive traversal/symlink rejection and snapshot recursion protection.
- Rejection of `sorry`, nonstandard axioms and missing audit output.
- An incorrect Paxos highest-ballot selector that cannot pass verification.
- An always-rejecting Paxos proposer whose progress proof fails.
- A Pedersen implementation that uses the message instead of the blinding scalar,
  causing the extracted-code refinement proof to fail.

Rust tests passed for Paxos and Pedersen (one executable test each); the delivery
crate built and its test/doc-test commands passed with zero Rust tests. Delivery
behavior is covered by the Lean integration test. The shared specification module
also compiled on Lean 4.31.0 and 4.32.0. The new agent skill passed its validator.

Two proof-authoring errors found during integration were corrected before the
final passing run: a simplifier loop in delivery and a binder syntax error in
the new Paxos wrapper. The initial broad legacy Python suite was interrupted;
this report does not claim a full regression run of that separate pipeline.

## Human and agent workflow

```sh
# Preview the claim and its explicit premises; this does not run Lean.
python3 formal/rust_verify.py --explain-spec formal/rust/delivery/spec.toml
# Verify the crate; its specification is discovered automatically.
python3 formal/rust_verify.py formal/rust/delivery
# Recheck the evidence directory printed in the result.
python3 formal/rust_verify.py --recheck <evidence-directory>
```

Use [the specification guide](../rust/SPECIFICATIONS.md) for semantics and examples.
The [agent skill](../skills/write-verification-spec/SKILL.md) teaches agents to
connect claims to extracted code, distinguish safety from conditional progress,
check vacuity, and report proof failures without weakening the requested claim.
It is repository-local; no global agent configuration was changed.

The statuses have intentionally different meanings:

| Status | Meaning |
| --- | --- |
| `proved` | Lean checked the proposition and its permitted axioms |
| `refuted` | Lean checked the proposition's negation |
| `unknown` | Neither was established, or compilation/proof execution timed out |
| `unsupported` | Rust extraction failed |
| `error` | Invalid input, setup or tooling error |

## Trust boundary and next work

The Rust compiler and extraction chain remain trusted. Lean proofs use only the
audited standard axioms `propext`, `Classical.choice`, and `Quot.sound`. Replay
checks hashes and accepted proofs; it does not re-extract Rust or prove compiler
correctness. Runtime behavior must satisfy the model's explicit interface.

This is a local tool for trusted source/proof inputs. A hosted upload service
would require isolation for Cargo build scripts and Lean metaprograms.

The next useful increments are a verified runtime adapter for Paxos, a concrete
cryptographic backend satisfying `BackendLaws`, and CI integration retaining
proof evidence per revision. General protocol compositionality and automated
game-theoretic reasoning remain future work, not delivered guarantees.

## Presentation source

The PowerPoint is editable and reproducible:

```sh
uv run --with python-pptx==1.0.2 python formal/reports/build_presentation.py
```

Its speaker notes give technical context and source references. The PDF is a
companion export for review and sharing.
