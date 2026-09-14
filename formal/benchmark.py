"""Measure fresh evidence generation; optionally import an isolated old checkout."""
import argparse
import importlib
import json
from pathlib import Path
import platform
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module-root', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=120)
    parser.add_argument('--spec', action='append', help='Repeat to measure other specifications')
    parser.add_argument('--depth', type=int, default=4)
    args = parser.parse_args()
    sys.path.insert(0, str(args.module_root.resolve()))
    from rmverify import verify
    rows = []
    for path in args.spec or ('examples.counter_spec:spec', 'examples.peterson_v2:peterson'):
        module, name = path.split(':')
        spec = getattr(importlib.import_module(module), name)
        started = time.monotonic()
        report = verify(spec, directory=args.out/'evidence', timeout=args.timeout, depth=args.depth)
        evidence = Path(report.evidence)
        artifact=json.loads((evidence/'artifact.json').read_text()) if (evidence/'artifact.json').exists() else {}
        rows.append(dict(artifact_sha256=artifact.get('sha256'), lean_toolchain=(evidence/'lean-toolchain').read_text().strip() if (evidence/'lean-toolchain').exists() else None, specification=path, status=report.status, translation=report.translation,
                         seconds=time.monotonic()-started,
                         lean_bytes=sum(p.stat().st_size for p in evidence.glob('*.lean')),
                         translation_bytes=(evidence/'Translation.lean').stat().st_size
                                           if (evidence/'Translation.lean').exists() else None,
                         evidence=str(evidence)))
        print(json.dumps(rows[-1]), flush=True)
    (args.out/'measurements.json').write_text(json.dumps(
        dict(python=platform.python_version(), measurements=rows), indent=2)+'\n')
    raise SystemExit(0 if all(r['status'] == 'proved' for r in rows) else 1)


if __name__ == '__main__':
    main()
