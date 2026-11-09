"""Guided setup. Release scripts can also run this module before Vita Tree is installed."""

from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from queue import Empty, Queue
import argparse
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
from threading import Thread
import time
import venv
import webbrowser


class InstallError(RuntimeError):
    pass


def data_directory() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
    return base / "vita-tree"


@contextmanager
def single_writer(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as lock:
        if os.name == "nt":
            import msvcrt

            if not lock.tell():
                lock.write(b"\0")
                lock.flush()
            lock.seek(0)
            acquire = lambda: msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            acquire = lambda: fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            acquire()
        except (BlockingIOError, PermissionError) as exc:
            raise RuntimeError("Setup is already running for this destination. Wait and retry.") from exc
        yield


def matches_release(python: Path, release: str, ai: bool) -> bool:
    if not python.is_file():
        return False
    check = "from importlib.metadata import version; from vita_tree.cli import main; print(version('vita-tree'))"
    if ai:
        check += "; version('vita-cv')"
    result = subprocess.run(
        [str(python), "-I", "-c", check], capture_output=True, text=True, timeout=15,
    )
    return result.returncode == 0 and result.stdout.strip() == release


def stop_install(process: subprocess.Popen) -> None:
    if process.poll() is None:
        if os.name == "nt":
            try:
                subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5,
                )
            finally:
                if process.poll() is None:
                    process.kill()
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
    process.wait()


@contextmanager
def installation(release: str | None, ai: bool):
    current = Path(sys.executable)
    if release is None or matches_release(current, release, ai):
        yield current, lambda: None
        return

    name = release + ("-ai" if ai else "")
    directory = data_directory() / "environments" / name
    python = directory / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    ready = directory / ".ready"
    with single_writer(directory.parent / f"{name}.lock"):
        if ready.is_file() and matches_release(python, release, ai):
            print(f"Using Vita Tree {release} already installed for this account.", flush=True)
            yield python, lambda: None
            return

        print(f"Installing Vita Tree {release} in an isolated environment…", flush=True)
        ready.unlink(missing_ok=True)
        venv.EnvBuilder(with_pip=True).create(directory)
        target = f"vita-tree{'[ai]' if ai else ''}=={release}"
        process = subprocess.Popen(
            [str(python), "-I", "-m", "pip", "--isolated", "install", "--no-input",
             "--disable-pip-version-check", "--index-url", "https://pypi.org/simple",
             "--timeout", "15", "--retries", "1", target],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env={**os.environ, "PIP_CONFIG_FILE": os.devnull},
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
        )
        deadline = time.monotonic() + 180

        def finish():
            if process.poll() is None:
                print("Finishing package installation…", flush=True)
            try:
                code = process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired as exc:
                raise InstallError("Package installation timed out. Check your connection and retry.") from exc
            if code or not matches_release(python, release, ai):
                raise InstallError(
                    f"Could not install Vita Tree {release} from PyPI. "
                    "Check your connection and the published version, then retry."
                )
            ready.touch()

        try:
            yield python, finish
        finally:
            stop_install(process)


def announce_url(stream, urls: Queue) -> None:
    for line in stream:
        if line.startswith("Dashboard running at "):
            urls.put(line.removeprefix("Dashboard running at ").strip())
        else:
            print(line, end="", flush=True)
    urls.put(None)


def launch(python: Path, repository: Path | None, port: int, no_browser: bool) -> int:
    mode = ["demo"] if repository is None else ["run", str(repository)]
    command = [str(python), "-I", "-u", "-m", "vita_tree", *mode, "--port", str(port), "--no-browser"]
    print("Starting the local dashboard…", flush=True)
    with subprocess.Popen(command, stdout=subprocess.PIPE, text=True, errors="replace") as process:
        urls: Queue = Queue()
        reader = Thread(target=announce_url, args=(process.stdout, urls), daemon=True)
        reader.start()
        try:
            try:
                url = urls.get(timeout=30)
            except Empty as exc:
                raise RuntimeError("The dashboard did not start in time. Retry setup.") from exc
            match = re.fullmatch(r"http://127\.0\.0\.1:(\d+)", url or "")
            if not match:
                raise RuntimeError("The dashboard did not start. Check the project path and port shown above.")
            connection = HTTPConnection("127.0.0.1", int(match[1]), timeout=5)
            try:
                connection.request("GET", "/")
                if connection.getresponse().status != 200:
                    raise RuntimeError("The dashboard page did not load. Retry setup.")
            finally:
                connection.close()
            print(f"Dashboard ready at {url}", flush=True)
            reopen = [str(python), "-m", "vita_tree", *mode, "--port", match[1]]
            if no_browser:
                reopen.append("--no-browser")
            print("Reopen with: " + (subprocess.list2cmdline(reopen) if os.name == "nt" else shlex.join(reopen)))
            if not no_browser:
                try:
                    webbrowser.open(url)
                except (OSError, webbrowser.Error):
                    pass  # The URL is already visible and works in any browser.
            return process.wait()
        finally:
            if process.poll() is None:
                process.terminate()
            reader.join(timeout=5)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--release", help="published version to install in an isolated environment")
    parser.add_argument("--check", action="store_true", help="check required tools and exit")
    parser.add_argument("--repository", type=Path, help="existing CV repository (default: sample)")
    parser.add_argument("--ai", action="store_true", help="include optional AI support in a release install")
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", default=0, type=int, help="localhost port (default: choose an available port)")


def choose_install(args: argparse.Namespace, ai: bool, tex: bool) -> tuple[Path, Path | None]:
    interactive = not args.non_interactive
    repository = args.repository
    for attempt in range(2):
        try:
            with installation(args.release, ai) as (python, finish):
                if interactive and attempt == 0:
                    if repository is None:
                        path = input("CV repository folder (press Enter to try the sample): ").strip()
                        repository = Path(path).expanduser() if path else None
                    if not tex and input("Show setup steps for PDF previews? [y/N] ").lower() == "y":
                        print("Install MiKTeX on Windows or TeX Live on macOS/Linux. Then use Check CV files.")
                finish()
            return python, repository
        except InstallError as exc:
            if not interactive or attempt:
                raise
            print(exc, file=sys.stderr)
            if input("Retry installation with the same choices? [y/N] ").lower() != "y":
                raise
    raise AssertionError("Installation attempts exhausted")


def run_setup(args: argparse.Namespace) -> int:
    if args.release is not None and not re.fullmatch(r"\d+\.\d+\.\d+", args.release):
        print("--release must be a published version such as 1.2.3.", file=sys.stderr)
        return 2

    if sys.version_info < (3, 10) or not shutil.which("git"):
        print("Install Python 3.10 or newer and Git, then rerun setup.", file=sys.stderr)
        return 1
    tex = any(shutil.which(engine) for engine in ("pdflatex", "xelatex", "lualatex"))
    if args.check:
        print(f"Python and Git are ready. TeX for PDFs: {'available' if tex else 'optional, unavailable'}.")
        return 0

    interactive = not args.non_interactive
    try:
        ai = args.ai or bool(
            args.release and interactive and input("Install optional AI support? [y/N] ").lower() == "y"
        )
        python, repository = choose_install(args, ai, tex)
        if ai:
            print("For AI, choose a provider or sign in under Job details & AI. You can skip this.")
        return launch(python, repository, args.port, args.no_browser)
    except (EOFError, KeyboardInterrupt):
        print("\nSetup canceled. Run the same command to try again.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"Vita Tree setup: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install Vita Tree and open a sample or your own LaTeX CV.")
    add_arguments(parser)
    return run_setup(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
