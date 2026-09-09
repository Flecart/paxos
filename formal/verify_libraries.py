"""Run reusable upstream compiler/library proofs, independently of the legacy Paxos model."""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "bin" / "python"
UPSTREAM = ROOT / ".cache" / "reactive-modules"


def main():
    if not PYTHON.exists() or not (UPSTREAM / "verification/check.py").exists():
        raise SystemExit("Run python3 formal/bootstrap.py to install the pinned upstream verification package")
    expected = json.loads((ROOT / "config.json").read_text())["rm_commit"]
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=UPSTREAM, text=True).strip()
    if actual != expected:
        raise SystemExit("Upstream revision differs from config.json; bootstrap the pinned revision")
    changed = subprocess.check_output(["git", "status", "--porcelain", "--", "python/zrth", "verification"], cwd=UPSTREAM, text=True)
    if changed:
        raise SystemExit("Upstream verification sources have uncommitted changes; run its check.py directly during development")
    subprocess.run([str(PYTHON), str(UPSTREAM / "verification/check.py"), *sys.argv[1:]], check=True)


if __name__ == "__main__":
    main()
