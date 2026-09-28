import subprocess
import sys


def run(cmd: str) -> None:
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, check=False)
    if res.returncode != 0:
        print(f"VERIFY FAIL: {cmd}")
        sys.exit(1)


def main() -> None:
    run("ruff check .")
    run("pytest")
    print("\nVERIFY PASS")


if __name__ == "__main__":
    main()