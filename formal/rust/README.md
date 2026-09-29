# Rust → Lean verification

This pipeline extracts a supported Rust library through **Hax → Charon →
Aeneas**, builds Lean definitions, and checks explicit propositions with Lean.
The included three-acceptor, single-decree Paxos library has safety and
conditional liveness proofs connected to its extracted functions.

The [specification interface](SPECIFICATIONS.md) supports `invariant`, `always`,
`eventually`, `leads_to`, and arbitrary Lean propositions. New protocols supply
their own `spec.toml` or `spec.json` and `verification/*.lean`; no driver changes are needed.
The [agent skill](../skills/write-verification-spec/SKILL.md) teaches this workflow.
Examples include [delivery](delivery/spec.toml), [Paxos](paxos/spec.json),
[deployable Paxos](paxosd/README.md), and [Pedersen commitments](pedersen/README.md).

[`paxosd`](paxosd/README.md) is the deployable version. It verifies a complete replica state
machine (ballot allocation, preemption retry, learner) composed into an N-replica
deployment with a lossy network and crash/restart. It proves agreement and validity
without assumptions, and liveness under a stable-leader, fair-delivery environment,
and it ships a std-only UDP runtime with durable storage.

## Run

Prerequisites: Python 3.11+, Rust/rustup, Lean's elan installer, Git, a C toolchain,
and `tar` with zstd support. Automatic binary installation currently supports
Linux x86_64. Initial setup needs internet access and several GB of disk space;
the first Lean dependency build can take many minutes. Later runs share a pinned
local dependency cache.
Allow several GB of free RAM as well. The driver builds extracted definitions
before handwritten proof modules to reduce simultaneous Lean memory use;
`extracted-build.log` and `build.log` distinguish those stages.

```sh
python3 formal/rust_verify.py --install
python3 formal/rust_verify.py formal/rust/paxos formal/rust/requests-paxos.json
```

For the general interface, inspect and run a specification directly:

```sh
python3 formal/rust_verify.py --explain-spec formal/rust/delivery/spec.toml
python3 formal/rust_verify.py --check-spec formal/rust/paxos/spec.json
python3 formal/rust_verify.py formal/rust/paxos
python3 formal/rust_verify.py formal/rust/pedersen formal/rust/pedersen/spec.json
```

The input pair is `(crate directory | .rs file | .zip, statements.json or statements.toml)`:

```sh
python3 formal/rust_verify.py protocol.zip statements.json --timeout 600
```

ZIP archives can contain the crate at their root or inside one enclosing folder.
Submit a library crate; binary-only packages and virtual workspaces are rejected.
If a crate also has binaries, only its library is verified. A small recorded
wrapper passes `--lib` to Charon because this pinned Hax version does not forward
that Cargo option on its Aeneas route; otherwise binary output can overwrite the
library extraction.
A standalone `.rs` file is wrapped as a library named `user-protocol`. The CLI
snapshots the input before extraction; generated code never overwrites the
submitted implementation. Cargo build scripts and Lean metaprograms execute
code: this is a **local developer tool for trusted inputs**, not an isolated
service for arbitrary uploads. Archive traversal and symlink checks do not
replace process isolation.

The built-in request is:

```json
{"profile": "paxos", "claims": ["safety", "liveness"]}
```

It expects the `verified-paxos` library API. It is not a source-hash whitelist:
modified implementations are extracted again and must satisfy the same checked
refinement obligations.

Results are JSON. Exit code zero means every requested claim was proved.

| Status | Meaning |
| --- | --- |
| `proved` | The exact requested Lean proposition passed compilation and axiom audit |
| `refuted` | Lean checked the negation of the requested proposition |
| `unknown` | Proof/refutation search failed, a refinement failed, or the proof timed out |
| `unsupported` | The Rust extractor rejected the input |
| `error` | Input/setup/tooling failed |

A failed proof is not a counterexample. Bounded execution and Rust unit tests
are not used to authorize `proved`. Each report points to extraction/build/
claim logs, the statement, and the checked theorem. `--timeout` is a per-stage
limit, not a wall-clock limit for the entire command.

## What is proved for Paxos

`paxos/src/lib.rs` implements acceptor prepare/accept, quorum value selection,
a proposer that issues at most once per instance, and a learner checking two
matching votes from distinct acceptors. The library uses `u64` ballots and
values, without unchecked arithmetic. `examples/demo.rs` runs these components
with an in-process transport demonstration:

```sh
cargo test --manifest-path formal/rust/paxos/Cargo.toml
cargo run --manifest-path formal/rust/paxos/Cargo.toml --example demo -- 42
```

The proof has three layers:

1. `rmverify/lean/Paxos.lean`: the message-history model, its inductive invariant,
   quorum intersection, agreement, and conditional eventual choice. The proof
   covers unbounded execution length and mathematical ballots/values, without a
   finite-state search bound. It also proves that an infinite idle execution is
   legal and never decides without progress assumptions.
2. `rust/paxos/verification/Protocol.lean`: equations/contracts for the actual extracted Rust
   functions; their operational composition with ghost message histories;
   refinement into the Paxos model; and the final implementation-backed claims.
   Local progress proves successful returns under enabled-action conditions,
   including proposer and learner computation.
3. Generated `Request*.lean`: the particular claims requested by the user,
   with transitive axiom audits. `sorryAx` and additional axioms are rejected.

**Safety** means two successful learner certificates in any reachable protocol
state return the same value. Historical votes remain in the model, so agreement
is not limited to current acceptor registers. Safety does not assume delivery or
fairness.

**Liveness** proves eventual **choice by a quorum**, together with successful
local computations under their enabling conditions. It assumes a positive
representable ballot, an eventually stable responsive quorum whose promises
never exceed that ballot after stabilization, and weak fairness of that ballot's
prepare, propose, and accept actions. Delays may be arbitrarily long but finite
on the actions covered by fairness. It does not prove that every client receives
a response, wall-clock bounds, leader election, or unconditional termination.

The three acceptors are non-Byzantine. Messages must be authentic, and the runtime
must deliver only previously emitted messages. Ballots must be globally unique
across proposer instances. Each component's mutable state must remain exclusively
owned and serialized. Duplicate and delayed delivery are allowed; ignoring a
message forever is allowed by safety, and constrained by the liveness premises.
Ghost histories retain sent messages, allowing the environment to model repeated
delivery; they are not mutable application data used to make protocol decisions.

**Verification scope:** this is the Rust protocol library composed through its
stated interface. For the full replica with ballot allocation, retry, and a runtime,
see [`paxosd`](paxosd/README.md). It does not verify the old Python `PaxosNode`, sockets, the
executable demo's transport, persistent storage, crash/restart recovery, ballot
allocation, or code outside the extracted library. The compiler/extraction
boundary remains trusted; this is not a verified Rust compiler. Ordinary Rust
borrow checking is not being claimed as a protocol proof.

## Other statements and handwritten proofs

For an input `identity.rs` containing:

```rust
pub fn identity(x: u64) -> u64 { x }
```

use:

```json
{
  "claims": [
    {
      "name": "identity",
      "statement": "∀ x : Aeneas.Std.U64, user_protocol.identity x = Aeneas.Std.RustM.ok x",
      "proof": "by intro x; rfl"
    }
  ]
}
```

Statements are formal Lean propositions, not automatically interpreted natural
language. Omit `proof` to try a small set of Lean tactics. An optional
`refutation` supplies a proof of the negated statement. An optional `imports`
list selects additional Lean modules. Put reusable handwritten proofs under
`verification/` in the input crate; they are copied into the Lean module namespace
`UserVerification` (for example, import `UserVerification.Safety`). These files
remain separate from regenerated definitions. A failed positive proof triggers a small
negation-proof attempt for claims; only a checked, audited negation
produces `refuted`.

Complex specifications require lemmas and domain knowledge. The engine does not
promise to automatically decide arbitrary safety or liveness properties.

## Evidence and replay

Every run writes a separate directory under `.rmverify/rust/` containing the
source snapshot, request, extracted Lean, proof files, logs, dependency pins,
report, hashes, and a copy of the replay command.

```sh
python3 formal/rust_verify.py --recheck .rmverify/rust/rust-EXAMPLE
# Within an exported evidence bundle:
python3 rust_verify.py --recheck .
```

Replay checks content hashes, builds the Lean package, and rechecks each accepted
proof/refutation and its axioms. Unknown claims remain unknown. Replay does not
re-extract Rust; extraction is checked operationally when the original run is
created and remains part of the trust boundary. A copied bundle may require
network access to fetch the pinned Lean dependencies if its local cache link is
unavailable. Source snapshots and handwritten statements should be versioned;
cache contents and generated proof projects need not be committed.

Tool versions are pinned in the installer, `paxos/hax.toml`, and
`lean-lake-manifest.json`. Hax verifies Charon/Aeneas binary checksums; the
installer verifies the Hax archive checksum. The Rust pipeline uses Lean 4.31.0
for upstream compatibility; the existing Python pipeline stays on Lean 4.32.0.
The shared reactive-module sources are checked by both.

## Regression checks

```sh
python3 -m unittest formal.test_rust_pipeline -v
RMVERIFY_RUST_INTEGRATION=1 python3 -m unittest formal.test_rust_pipeline -v
```

The integration checks exercise the structured temporal interface, Pedersen security,
directory and ZIP inputs, a standalone Rust file,
proof replay, a deliberately incorrect highest-ballot selector, an always-rejecting proposer, a checked false
statement, and rejection of `sorry`. The unit tests also check archive traversal,
symlinks, malformed requests, and axiom-audit failure.
