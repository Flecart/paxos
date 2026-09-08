"""Build the pinned upstream compiler in an isolated environment."""
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT / ".cache" / "reactive-modules"
PYTHON = ROOT / ".venv" / "bin" / "python"


def run(*args, cwd=ROOT, env=None):
    subprocess.run(args, cwd=cwd, env=env, check=True)


def main():
    config = json.loads((ROOT / "config.json").read_text())
    if not (REPO / ".git").exists():
        REPO.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "https://github.com/Flecart/reactive-modules.git", str(REPO))
    run("git", "checkout", "--detach", config["rm_commit"], cwd=REPO)
    if not PYTHON.exists():
        run("uv", "venv", str(ROOT / ".venv"), "--python", "3.13")
    run("uv", "pip", "install", "--python", str(PYTHON), "torch==2.9.0",
        "--index-url", "https://download.pytorch.org/whl/cpu")
    run("uv", "pip", "install", "--python", str(PYTHON), "-r", str(ROOT / "requirements.txt"))
    env = dict(os.environ)
    env.update(VIRTUAL_ENV=str(ROOT / ".venv"),
               PATH=str(PYTHON.parent) + os.pathsep + env.get("PATH", ""),
               LIBTORCH_USE_PYTORCH="1", CARGO_BUILD_JOBS="2")
    torch_lib = subprocess.check_output(
        [str(PYTHON), "-c", "import torch,pathlib; print(pathlib.Path(torch.__file__).parent/'lib')"], text=True).strip()
    env["LD_LIBRARY_PATH"] = torch_lib + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    run(str(PYTHON), "-m", "maturin", "develop", cwd=REPO / "python", env=env)


if __name__ == "__main__":
    main()
