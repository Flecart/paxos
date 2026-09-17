# Writing specifications for Rust programs

The verifier accepts `(Rust library / .rs / ZIP, specification.json or specification.toml)`. The driver
is protocol-independent: it extracts Rust using Hax/Charon/Aeneas, elaborates the
specification into Lean propositions, checks proofs, and saves replayable evidence.
Adding a protocol does not require editing the driver or registering a profile.

Start with the complete [delivery example](delivery/spec.toml), then inspect
[Paxos](paxos/spec.json) for distributed agreement and
[Pedersen](pedersen/spec.json) for distributional and algebraic properties.

For coding agents, read the repository-local
[write-verification-spec skill](../skills/write-verification-spec/SKILL.md).
Point an agent at that file, or install its folder into your agent's skill
directory. The verifier does not change global agent configuration.

```sh
# Preview each claim and its assumptions in readable form.
python3 formal/rust_verify.py --explain-spec formal/rust/delivery/spec.toml
# Inspect the exact propositions without extracting or compiling anything.
python3 formal/rust_verify.py --check-spec formal/rust/delivery/spec.toml
# Extract the submitted implementation and check those propositions.
python3 formal/rust_verify.py formal/rust/delivery
```

## Human-friendly authoring

Prefer TOML when writing by hand: comments and multiline strings make intent and
proof assumptions easier to review. JSON remains supported with the same schema.
A crate directory automatically uses its single `spec.toml` or `spec.json`; if both
exist, select one explicitly. A ZIP or standalone Rust file needs an explicit spec
path. `--explain-spec` previews intent, assumptions, and exact generated statements;
`--check-spec` outputs machine-readable elaboration. Neither runs Lean or establishes
that predicates are well-typed.

```toml
version = 1
imports = ["UserVerification.Protocol"]

[system]
module = "Delivery.module"
# Without fair delivery, an infinite idle execution is possible.
assumptions = ["Delivery.Fair"]

[[claims]]
name = "eventual_delivery"
kind = "eventually"
description = "Every fair execution eventually delivers the message."
predicate = "Delivery.Done"
proof = "Delivery.eventually_done"
```

Choose `invariant` for a predicate on every reachable state, `eventually` for
completion, and `leads_to` for each request eventually receiving a response.
Predicates and supporting lemmas still require Lean definitions; the interface
reduces repetitive specification syntax, not the need to define precise semantics.
English descriptions are documentation, never silently translated into theorems.

## Files you author

```text
my-protocol/
  Cargo.toml
  src/lib.rs                    executable implementation
  spec.json                     readable claims and environment assumptions
  verification/Protocol.lean    state interpretation, predicates, lemmas, proofs
```

Files under `verification/` become Lean modules under `UserVerification`.
For example, `verification/Protocol.lean` is imported as
`UserVerification.Protocol`. Handwritten files are copied to each evidence bundle;
regenerating extracted code never overwrites them. They should import the
extracted library's `Extraction` module, not its generated umbrella module (which
imports the handwritten proofs and would create a cycle).

## Version 1

```json
{
  "version": 1,
  "title": "Reliable delivery latch",
  "description": "The environment schedules delivery events.",
  "imports": ["UserVerification.Protocol"],
  "system": {
    "module": "Delivery.module",
    "assumptions": ["Delivery.Fair"]
  },
  "claims": [
    {
      "name": "valid_state",
      "kind": "invariant",
      "predicate": "Delivery.Valid",
      "proof": "Delivery.safe"
    },
    {
      "name": "pending_completes",
      "kind": "leads_to",
      "from": "Delivery.Waiting",
      "to": "Delivery.Done",
      "proof": "Delivery.progress"
    }
  ]
}
```

The compiler rejects unknown fields, duplicate claim names, missing expressions,
unknown kinds, and ambiguous combinations of property fields. Lean subsequently
checks expression types. `title`, `description`, and each claim's `description`
are explanatory metadata, never proof premises.

| Field | Meaning |
| --- | --- |
| `version` | `1`; omitted only for compatibility with existing custom requests |
| `imports` | Additional Lean module names |
| `support` | Optional shared library modules, such as `Paxos`; `Semantics`, `Temporal`, and `Specification` are always supplied |
| `system.module` | Lean expression of type `RMVerify.Reactive.Module S` |
| `system.assumptions` | Explicit list of Lean predicates of type `(Nat → S) → Prop`; use `[]` if there are none |
| `claims` | Nonempty list of uniquely named properties |
| `proof` | Optional Lean proof term, often a theorem name or `by ...` |
| `refutation` | Optional Lean proof of the negation of the generated proposition |

A `system` is required for temporal and invariant claims. Pure `lean` claims do
not need it. Existing `{"profile":"paxos","claims":["safety","liveness"]}`
requests load an ordinary JSON template from `profiles/`; this is compatibility
convenience, not a special verification path. The explicit `paxos/spec.json`
workflow is preferred for new work.

## Property meanings

Let `M` be the selected module, `run : Nat → S` an infinite execution, and `E run`
the conjunction of all listed environment predicates.

| Kind | Property fields | Exact meaning |
| --- | --- | --- |
| `invariant` | `predicate` | Every reachable state satisfies the predicate |
| `always` | `predicate` | For every execution satisfying `E`, the predicate holds at every index |
| `eventually` | `predicate` | For every execution satisfying `E`, the predicate holds at some index, possibly zero |
| `leads_to` | `from`, `to` | At every index where `from` holds, `to` holds at that index or a later one |
| `lean` | `statement` | The supplied Lean proposition, unchanged |

**An invariant does not use scheduling assumptions.** It covers all reachable
states, including executions outside the fair environment. Use `always` when
the property intentionally depends on execution assumptions. `lean` claims also
do not implicitly receive system assumptions: write all premises in their
proposition. The report lists the assumptions applied to each structured claim.

The definitions are in [Specification.lean](../rmverify/lean/Specification.lean).
The engine neither invents assumptions nor infers the intended property from a
function name. Predicate fields contain Lean expressions or names, not strings
parsed as English or Rust. This small interface removes repetitive temporal
quantifiers; it does not eliminate the need to define meaning precisely.

For example, `leads_to` elaborates to:

```lean
∀ run, RMVerify.Reactive.Execution M run → E run →
  ∀ n, pending (run n) →
    ∃ k, n ≤ k ∧ completed (run k)
```

For repeated requests, include a request identifier in the state and predicate.
Otherwise an old completion could satisfy a new request's property. Timing is
logical execution steps; eventuality supplies no wall-clock or step bound.

## Connecting the implementation

The protocol's Lean adapter must connect its transitions to the **extracted
Rust functions**. The delivery example defines a step by a successful extracted
function call. Paxos proves that its composed extracted calls refine an abstract
model. Pedersen supplies an explicit algebraic interpretation of its backend
trait, then proves equations for the extracted commitment functions.

A `True` theorem or a theorem about an unrelated model can be checked by Lean,
but says nothing about the submitted program. The driver reports `extracted`;
it does not infer implementation refinement from a property name or a successful
build. Include a correspondence/refinement claim and inspect its statement when
using an abstract model. If primitives or runtime behavior are assumed, display
those assumptions in the spec description and put the actual formal premises in
the definitions/statements.

Rust ownership helps control aliasing, but it does not establish message
provenance, unique identifiers, crash recovery, or scheduler fairness.

## Proving safety and liveness

For an invariant, prove it holds initially and is preserved by every permitted
step. `Reactive.invariant_of_induction` supplies the induction principle. A
stronger auxiliary invariant may be necessary; the requested claim should still
state the externally meaningful guarantee.

For liveness, identify why a pending obligation remains enabled, which action
establishes its target, and what requires that action eventually to occur.
`Reactive.WeakFair` says a continuously enabled action eventually occurs.
`fair_leads_to`, `eventually_fair`, and `eventually_of_rank` provide reusable proof
rules. Fairness is written in the environment, never silently added by the tool.
Do not assume the desired eventual result as an environment predicate.

Infinite stuttering may violate liveness while preserving safety. The delivery
example proves that progress without fairness is false. Check environment
satisfiability separately where it is uncertain: inconsistent assumptions make
conditional temporal claims vacuously true. The driver cannot generally decide
whether arbitrary Lean assumptions are satisfiable. A module with no infinite
executions also makes universal temporal claims vacuous; establish a valid
execution witness when this is in doubt.

Hiding, binding, and other cryptographic properties need different quantifiers.
Use `lean` to express distributions and reductions rather than disguising them
as temporal invariants. See the [Pedersen explanation](pedersen/README.md).

## Proof assistance and results

Without a supplied proof, the engine tries a small sequence of Lean tactics.
This is convenient for elementary obligations, not a complete verifier. Add
lemmas under `verification/` when automation stops. If a positive proof fails,
the engine tries the supplied refutation or a small automatic negation proof.

- `proved`: the exact proposition compiled and passed the transitive axiom audit.
- `refuted`: its negation compiled and passed that audit.
- `unknown`: neither proof was established, including compilation failure or timeout.
- `unsupported`: extraction rejected the implementation.
- `error`: input, setup, or tooling failed.

Only standard Lean axioms (`propext`, `Classical.choice`, `Quot.sound`) are
accepted. `sorry` and custom axioms cannot authorize a successful claim.
A source mutation that invalidates a handwritten proof usually returns `unknown`,
not `refuted`: failing to prove something is not proving its negation.

Each report records exact propositions, claim kinds, and structured assumptions.
The evidence contains source snapshots, handwritten and generated Lean, logs,
version pins, hashes, and the replay runner. Replay rechecks accepted claims;
it does not independently verify the extraction compiler. See [the usage guide](README.md).

This is a local tool for trusted source and proof inputs. Rust build scripts and
Lean metaprograms execute code; an upload service would require isolation.
