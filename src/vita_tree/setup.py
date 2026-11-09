"""Guided system prerequisites check and setup for Vita Tree."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import time

from .sample import default_demo_directory, prepare_demo_repository


class SetupLock:
    """Single-writer lock for target environment or repository directory."""

    def __init__(self, directory: Path):
        self.directory = directory.resolve()
        self.lock_file = self.directory / ".vita-tree-setup.lock"
        self._acquired = False

    def acquire(self, timeout: float = 2.0) -> bool:
        self.directory.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + timeout
        pid = str(os.getpid()).encode("utf-8")
        while time.monotonic() < deadline:
            try:
                fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, pid)
                os.close(fd)
                self._acquired = True
                return True
            except (FileExistsError, OSError):
                time.sleep(0.1)
        return False

    def release(self) -> None:
        if self._acquired:
            try:
                self.lock_file.unlink(missing_ok=True)
            except OSError:
                pass
            self._acquired = False

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(
                f"Another setup process is actively running for {self.directory}. "
                "Wait for it to complete or remove the lock if abandoned."
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()


def check_prerequisites() -> dict:
    """Inspect the host environment for required and optional capabilities."""
    py_ver = sys.version_info
    py_ok = py_ver >= (3, 10)
    py_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"

    git_path = shutil.which("git")
    git_ok = bool(git_path)

    engines = {e: bool(shutil.which(e)) for e in ("pdflatex", "xelatex", "lualatex")}
    tex_ok = any(engines.values())

    return {
        "python": {"ok": py_ok, "version": py_str},
        "git": {"ok": git_ok, "path": git_path},
        "tex": {"ok": tex_ok, "engines": engines},
        "ready_for_demo": py_ok and git_ok,
    }


def print_status(prereqs: dict) -> None:
    py = prereqs["python"]
    git = prereqs["git"]
    tex = prereqs["tex"]

    print("Vita Tree System Capability Check:")
    print(f"  Python: {py['version']} [{'OK' if py['ok'] else 'FAIL - Requires >= 3.10'}]")
    print(f"  Git:    {git['path'] if git['ok'] else 'Not found'} [{'OK' if git['ok'] else 'FAIL - Required for repository management'}]")

    tex_status = "Available (" + ", ".join(e for e, ok in tex["engines"].items() if ok) + ")" if tex["ok"] else "None found (optional; required for PDF compilation)"
    print(f"  TeX:    {tex_status}")

    if not py["ok"]:
        print("\nAction required: Upgrade Python to 3.10 or newer.")
    if not git["ok"]:
        print("\nAction required: Install Git and ensure it is available on PATH.")
    if not tex["ok"]:
        print("\nNote: TeX (MiKTeX on Windows, TeX Live on Linux/macOS) is only needed for compiling PDFs. Browsing and editing CVs works without TeX.")


def run_setup(
    check_only: bool = False,
    auto_demo: bool = False,
    non_interactive: bool = False,
    target: Path | None = None,
) -> int:
    """Execute guided setup or verification."""
    prereqs = check_prerequisites()
    print_status(prereqs)

    if check_only:
        return 0 if prereqs["ready_for_demo"] else 1

    if not prereqs["ready_for_demo"]:
        print("\nSetup cannot continue because required prerequisites are missing.", file=sys.stderr)
        return 1

    target_dir = target or default_demo_directory()
    try:
        with SetupLock(target_dir):
            if auto_demo or non_interactive:
                demo_repo = prepare_demo_repository(target_dir)
                print(f"\nSample CV repository ready at: {demo_repo}")
                print("Run 'vt demo' to launch the dashboard.")
                return 0

            # Interactive choice
            print("\nSetup Options:")
            print("  1. Prepare sample demo CV repository (recommended)")
            print("  2. Exit setup")
            choice = input("Select an option [1]: ").strip() or "1"

            if choice == "1":
                demo_repo = prepare_demo_repository(target_dir)
                print(f"\nSample CV repository ready at: {demo_repo}")
                print("To start exploring, run:")
                print("  vt demo")
                return 0
            else:
                print("Setup completed.")
                return 0
    except RuntimeError as err:
        print(f"\nSetup conflict: {err}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vita Tree guided setup and capability checker")
    parser.add_argument("--check", action="store_true", help="check prerequisites and exit")
    parser.add_argument("--demo", action="store_true", help="create demo repository")
    parser.add_argument("--non-interactive", action="store_true", help="run non-interactively")
    parser.add_argument("--target", type=Path, help="target directory for demo repository")
    args = parser.parse_args(argv)

    return run_setup(
        check_only=args.check,
        auto_demo=args.demo,
        non_interactive=args.non_interactive,
        target=args.target,
    )


if __name__ == "__main__":
    raise SystemExit(main())
