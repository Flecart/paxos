# Direct pipeline measurements

Measured on 2026-09-11 with Python 3.13.9 on the same machine. Each row is one fresh evidence run with already installed toolchains/dependencies. Dependency installation time is excluded; reusable semantics compilation and proof checking are included. Other verification work was running concurrently, so these are descriptive measurements, not an isolated benchmark or a general speed claim.

The baseline used the pre-migration checkout and Lean 4.30.0; the direct implementation used Lean 4.32.0 and the pinned Veil interface. Both reported every requested property proved. The direct implementation checks additional read-dependency and Veil-correspondence obligations.

| Example | Pipeline | Wall time (s) | Translation.lean bytes | All top-level Lean bytes |
| --- | --- | ---: | ---: | ---: |
| examples.counter_spec:spec | Previous graph pipeline | 10.30 | 7,329 | 18,707 |
| examples.counter_spec:spec | Direct Lean pipeline | 12.29 | 8,532 | 23,728 |
| examples.peterson_v2:peterson | Previous graph pipeline | 96.08 | 40,093 | 54,106 |
| examples.peterson_v2:peterson | Direct Lean pipeline | 46.61 | 40,175 | 58,026 |

Byte counts measure generated/source text, not serialized kernel proof terms. The total includes reusable semantics and property files. No size-reduction claim follows from these results: direct definitions and additional obligations add overhead for small programs.

Reproduce the direct run:

```sh
formal/.venv/bin/python formal/benchmark.py --out formal/.rmverify/measurements
```

For an isolated old checkout, pass `--module-root /path/to/old-checkout/formal` and use a Python environment containing that revision’s dependencies. The historical external RM build dependencies are needed only for that optional baseline.

Raw measurements (including evidence paths) are in [direct-measurements.json](direct-measurements.json). Each evidence artifact records its actual source/tool hashes, dependency pins, accepted theorem audits, and standalone replay files.
