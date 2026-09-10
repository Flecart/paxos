"""Build the Git submodule in an isolated Python environment."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT / "reactive-modules"
PYTHON = ROOT / ".venv" / "bin" / "python"


def main():
    def run(*args, **kwargs):
        subprocess.run(args, check=True, **kwargs)

    if not (REPO / "python" / "Cargo.toml").exists():
        raise SystemExit("Run git submodule update --init --recursive first")
    if not PYTHON.exists():
        run("uv", "venv", str(ROOT / ".venv"), "--python", "3.13")
    run("uv", "pip", "install", "--python", str(PYTHON), "torch==2.9.0",
        "--index-url", "https://download.pytorch.org/whl/cpu")
    run("uv", "pip", "install", "--python", str(PYTHON), "maturin==1.9.0")
    env = dict(os.environ, VIRTUAL_ENV=str(ROOT / ".venv"),
               PATH=str(PYTHON.parent) + os.pathsep + os.environ.get("PATH", ""),
               LIBTORCH_USE_PYTORCH="1", CARGO_BUILD_JOBS="2")
    run(str(PYTHON), "-m", "maturin", "develop", "--locked", cwd=REPO / "python", env=env)
    run("uv", "pip", "install", "--python", str(PYTHON), "--no-deps", "-e", str(ROOT))
    run("lake", "--version", cwd=ROOT / "rmverify" / "lean")


if __name__ == "__main__":
    main()
