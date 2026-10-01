import subprocess
import sys
from pathlib import Path


def _find_tool(name: str) -> list[str]:
    """Return the command list to invoke *name*.

    Resolution order:
    1. .venv/Scripts/<name> (Windows) or .venv/bin/<name> (Unix) — direct
       executable inside the local virtual environment.
    2. sys.executable -m <name> — module invocation via the running Python.
    """
    # Locate the project root relative to this script (scripts/ -> project root).
    project_root = Path(__file__).resolve().parent.parent
    venv_bin = project_root / ".venv" / ("Scripts" if sys.platform == "win32" else "bin")

    # On Windows the executable may have a .exe extension.
    candidates = [venv_bin / name]
    if sys.platform == "win32":
        candidates.insert(0, venv_bin / f"{name}.exe")

    for candidate in candidates:
        if candidate.is_file():
            return [str(candidate)]

    # Fallback: run as a Python module.
    return [sys.executable, "-m", name]


def run(cmd: list[str]) -> None:
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, check=False)
    if res.returncode != 0:
        print(f"VERIFY FAIL: {' '.join(cmd)}")
        sys.exit(1)


def main() -> None:
    run([*_find_tool("ruff"), "check", "."])
    run(_find_tool("pytest"))
    print("\nVERIFY PASS")


if __name__ == "__main__":
    main()
