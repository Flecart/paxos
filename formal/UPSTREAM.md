# Upstream protocol contribution

The dependency is pinned by `formal/config.json` to the
`feat/rm-protocol-modules` branch of Flecart/reactive-modules.

The public workflow on this branch is `zrth.protocol` plus
`python -m zrth.protocol_check`. It provides named interfaces, actual RM atom
export, contracts, simulation, automatic small symbolic safety proofs, and
kernel-checked numerical witnesses. See upstream `verification/PROTOCOL.md`.

## Recovering previous work

No Git history was rewritten.

- Paxos commit `59cf19d2467a86a83962a216b45542f470c8fba9` contains the previous
  native/legacy runners, generated artifacts, and legacy Lean certificate.
- Paxos checkpoint `c4def90` also retains the previous compiler integration.
- Reactive Modules branch `feat/verified-python-handlers` at `91289f9` retains
  the older compiler demonstrations and hand-written example proofs.
- Reactive Modules commit `f4857be9477596e75e930c95ccab8e72bffe6a45` retains the
  first RM-native protocol increment and its hand-written register proof.

The cleanup removes competing examples and entrypoints, not the reusable
upstream compiler implementation. Compiler regression fixtures live under
`python/tests/fixtures/compiler/`, outside the protocol examples directory.
