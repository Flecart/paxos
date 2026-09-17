# Pedersen commitments: a parametric Rust scheme with Lean proofs

```sh
cargo test --manifest-path formal/rust/pedersen/Cargo.toml
python3 formal/rust_verify.py --check-spec formal/rust/pedersen/spec.json
python3 formal/rust_verify.py formal/rust/pedersen formal/rust/pedersen/spec.json
```

This example exercises the same general verifier as Paxos. It is a commitment
primitive, not a consensus algorithm. Its properties compare distributions and
adversarial openings, so its specification uses the general `lean` claim form.

The [Rust implementation](src/lib.rs) uses an abstract group trait to compute

```text
commit(G, H, message, blinding) = message • G + blinding • H
```

Here `•` is scalar multiplication, and `+` is the group operation. This is the
additive notation used for elliptic-curve Pedersen commitments. Verification
recomputes this expression and compares it to the submitted commitment.

## What the proof says

[Model.lean](verification/Model.lean) uses Mathlib's fields, modules, finite sums, and permutations.
`probability event` is the exact rational fraction of a finite uniform random
tape satisfying that event. Its normalization and monotonicity are proved in Lean. Scalars form a field `F`; the additive group `G` is
an `F`-module. Specialize this to `F = ZMod q` for a prime `q` and a cyclic group
of order `q`. Generator conditions are explicit injectivity/surjectivity of the
scalar-multiplication maps. No concrete curve is silently assumed.
[Security.lean](verification/Security.lean) connects these results to the extracted
Rust functions under the backend contracts.

| Claim | Checked meaning |
| --- | --- |
| `refinement` | The extracted Rust commitment computes the mathematical expression, under the backend-operation contracts |
| `correctness` | An honest opening is accepted by the extracted Rust verification function |
| `perfect_hiding` | The distributions of extracted Rust commitments for any two messages are exactly equal when blinding is uniform and `H` generates the group |
| `binding_reduction` | Two accepted openings with distinct messages yield a discrete logarithm of `H` relative to `G` |
| `binding_bound` | The probability of producing such openings is at most the supplied bound on the reduction's discrete-log success probability |

**Hiding proof.** Changing the message can be compensated by a fixed translation
of the blinding scalar. Translation permutes a finite field and therefore
preserves its uniform distribution. The proof establishes equality of the whole
commitment distributions, not merely the existence of alternative openings.
This is single-commitment hiding with fresh independent uniform randomness;
reuse or biased randomness is outside the statement.

**Binding proof.** If two accepted openings satisfy

```text
m • G + r • H = m' • G + r' • H, with m ≠ m',
```

then `r' - r` is nonzero and the reduction computes

```text
x = (m - m') / (r' - r), so x • G = H.
```

The probability theorem uses the same nonempty finite uniform random tape for the adversary
and reduction. The challenge `H` may depend on that tape, so randomized setup
can be represented. The theorem covers finite-randomness experiments at each
fixed parameter choice; it does not model arbitrary countably infinite samplers. Every binding success is a discrete-log success; an explicit
bound on the latter transfers to the former. There is no added cryptographic
axiom: the hardness bound is a visible theorem premise.

Pedersen is perfectly hiding and **computationally**, not perfectly, binding.
An unbounded attacker can compute discrete logarithms and find alternate
openings. The proof therefore deliberately does not assert that alternate
openings never exist. The reduction takes an attack's two openings and performs
a fixed number of field operations. This example does not formalize PPT machines,
operation costs, or an asymptotic negligibility framework; it proves the exact
algebraic reduction and quantitative probability implication. Supplying a
concrete hardness theorem/assumption remains a cryptographic instantiation task.

This separation follows the standard commitment-security formulation; compare
[Metere and Dong, Automated Cryptographic Analysis of the Pedersen Commitment
Scheme](https://arxiv.org/abs/1705.05897), which formalizes correctness, perfect
hiding, and computational binding in EasyCrypt. We reuse Mathlib and the Rust
extractor here; that paper's EasyCrypt proofs are not being imported into Lean.

## Backend and deployment boundary

`BackendLaws` states that `scale`, `add`, and `same` return the mathematical
operations successfully. The extracted Rust algorithm is checked for every
backend satisfying those laws. A mathematical backend interpretation is supplied;
a production Rust curve implementation is not supplied or verified.

The caller must supply sound public parameters, canonical scalar/group values,
and fresh uniform blinding. Setup must not give the committer the discrete log
of `H` relative to `G` if computational binding is required. The library does
not implement random-number generation, point validation, serialization,
constant-time arithmetic, erasure, or a network protocol.

The tiny group in the Rust unit test is explicitly insecure and only checks
execution of the equations. No security claim is made for that test group.
The integration regression replaces the blinding scalar with the message in
the Rust source and checks that the extracted-code proof fails.

Read the generated propositions and their premises in `spec.json` or use
`--check-spec`; the word “proved” always refers to those exact statements.
