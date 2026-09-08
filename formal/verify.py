"""Repeat the saved checks and Lean build; optionally rebuild the upstream RM."""
import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recompile", action="store_true", help="regenerate Python and re-run the pinned upstream analyzer")
    parser.add_argument("--skip-lean", action="store_true", help="run Python/RM and SMT checks only")
    args = parser.parse_args()
    python = ROOT / ".venv" / "bin" / "python"
    if not python.exists():
        raise SystemExit("Run python3 formal/bootstrap.py first")
    scripts = (["generate.py", "compile_rm.py"] if args.recompile else [])
    scripts += ["test_model.py", "check.py", "smt_check.py", "export_lean.py"]
    for script in scripts:
        subprocess.run([str(python), str(ROOT / script)], check=True)
    if not args.skip_lean:
        subprocess.run(["lake", "build"], cwd=ROOT / "lean", check=True)
        subprocess.run(["lake", "env", "lean", "Audit.lean"], cwd=ROOT / "lean", check=True)
    print("Checks completed. See formal/README.md for proof scope and open obligations.", flush=True)


if __name__ == "__main__":
    main()
