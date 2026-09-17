---
name: write-verification-spec
description: Author and review Rust-to-Lean safety, liveness, and mathematical specifications in this repository, connect them to extracted code, run verification, and interpret checked evidence. Use for spec.toml, spec.json, and verification/*.lean work, including fairness assumptions and cryptographic reductions.
---

# Write verification specifications

Read [the interface guide](../../rust/SPECIFICATIONS.md) for the schema and exact
quantifiers. Use [delivery](../../rust/delivery/spec.toml) as the smallest complete
example; use [Paxos](../../rust/paxos/spec.json) for distributed refinement and
[Pedersen](../../rust/pedersen/README.md) for probability/security claims.
Repository commands below run from the root containing `formal/`.

## Author the claim before the proof

Translate the user's intended guarantee into an observable state/trace property.
Distinguish an invariant over reachable states, a conditional temporal claim, and
a relation between probability distributions. State the verification boundary:
protocol core, runtime, storage, cryptographic backend, and external inputs.
Do not strengthen environmental assumptions just to make a proof succeed.

Create a commented `spec.toml` (or `spec.json`) and `verification/Protocol.lean` in the Rust library. Import
its generated `LibraryName.Extraction` module in the adapter. Define transitions
using extracted calls, or prove their refinement into a model. An unrelated
model theorem is not implementation verification. Keep handwritten files outside
`proofs/`, which the snapshotter excludes as generated output.

Use `invariant` for unconditional reachable-state safety; its system fairness
predicates are intentionally ignored. Use `always`, `eventually`, or `leads_to`
with explicit `system.assumptions` for execution properties. Predicates and
assumptions are Lean terms, not English. Put readable intent in `description`.
Use `lean` for claims requiring other quantifiers, such as cryptographic security.
Formal premises of `lean` claims belong in the statement, not just metadata.

## Avoid plausible but misleading proofs

- Check initial states and every permitted transition. A disabled or always-failing
  handler can satisfy safety vacuously; verify enabled local progress as needed.
- For liveness, name the fair action and show why it stays enabled. Do not assume
  termination itself. Look for an idle execution when fairness is absent.
- With repeated requests, correlate responses to request identifiers; an old
  completion must not discharge a new obligation.
- Check whether assumptions can hold. Lean proves implications with contradictory
  premises too. Do not describe such a result as demonstrated progress.
- A bounded test, borrow-check success, or model-check result is not the Lean proof.
- Hiding requires an indistinguishability/distribution statement. Pedersen is not
  unconditionally binding: prove a reduction with an explicit hardness bound.
  Do not claim a toy group, canonical backend interpretation, or unchecked RNG
  is production cryptography.

## Run and inspect

```sh
python3 formal/rust_verify.py --explain-spec path/to/crate/spec.toml
python3 formal/rust_verify.py --check-spec path/to/crate/spec.toml
python3 formal/rust_verify.py path/to/crate
python3 formal/rust_verify.py --recheck .rmverify/rust/rust-RESULT
```

Inspect the generated statement as well as the status. Add handwritten lemmas
when automatic tactics stop; never use `sorry`, added axioms, or a weaker claim
to conceal failure. Read extraction/build/claim logs to distinguish unsupported
Rust from an unproved obligation. A `refuted` result requires a checked negation;
a failed proof is `unknown`.

For a new adapter, make one meaningful mutation that should break the property
and check that it cannot return `proved`. Report the exact scope, assumptions,
checked results, and outstanding proof obligations. Creating specs does not
itself authorize commits, pushes, deployments, or external messages.
