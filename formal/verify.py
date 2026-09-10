"""Compatibility entry point: verify the counter through the reusable library."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    python = ROOT / ".venv" / "bin" / "python"
    if not python.exists():
        raise SystemExit("Run python3 formal/bootstrap.py first")
    raise SystemExit(subprocess.call([str(python), "-m", "rmverify", "examples.counter_spec:spec",
                                     "--out", str(ROOT / ".rmverify"), *sys.argv[1:]], cwd=ROOT))
