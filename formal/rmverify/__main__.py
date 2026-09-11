"""Run a Python specification: python -m rmverify package.module:spec."""
import argparse
from dataclasses import asdict
import importlib
import json
from .value_types import json_value

from . import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("specification", help="importable module:specification_variable")
    parser.add_argument("--out", default=".rmverify")
    parser.add_argument("--timeout",type=float,default=60)
    parser.add_argument("--depth",type=int,default=10)
    args = parser.parse_args()
    module, separator, name = args.specification.partition(":")
    if not separator: parser.error("specify module:variable")
    spec = getattr(importlib.import_module(module),name)
    report = verify(spec,directory=args.out,timeout=args.timeout,depth=args.depth)
    print(json.dumps(asdict(report),indent=2,default=json_value))
    raise SystemExit(0 if report.ok else 1)


if __name__ == "__main__":
    main()
