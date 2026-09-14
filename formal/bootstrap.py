"""Install the Python verifier; the upstream reference submodule is not needed."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "bin" / "python"


def main():
    if not PYTHON.exists():
        subprocess.run(["uv", "venv", str(ROOT / ".venv"), "--python", "3.13"], check=True)
    subprocess.run(["uv", "pip", "install", "--python", str(PYTHON), "-e", str(ROOT)], check=True)
    subprocess.run(["lake", "--no-cache", "build", "+Veil"], cwd=ROOT / "rmverify" / "lean", check=True)
    subprocess.run(["lake", "--no-cache", "build"], cwd=ROOT / "rmverify" / "lean", check=True)


if __name__ == "__main__":
    main()
