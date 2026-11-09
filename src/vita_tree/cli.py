"""Command-line interface for vita-tree."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from . import __version__
from .server import resolve_repository, serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vt",
        description="Browse Git branches and preview their LaTeX documents.",
    )
    parser.add_argument("--version", action="version", version=f"vita-tree {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run", help="start the branch dashboard")
    run.add_argument(
        "repository",
        nargs="?",
        default=".",
        help="Git repository to inspect (default: current directory)",
    )
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", default=8765, type=int)
    run.add_argument(
        "--file",
        dest="document_path",
        default="main.tex",
        help="document path inside each branch (default: main.tex)",
    )
    run.add_argument("--no-browser", action="store_true")
    run.add_argument("--vita-source", type=Path, help="Path to a local vita-cv checkout (optional)")
    run.add_argument("--log-dir", type=Path, help="Folder for rotating structured logs (default: user application data)")
    run.add_argument("--log-level", choices=("debug", "info", "warning", "error"), default="info")

    demo = commands.add_parser("demo", help="create or open a sample CV repository and launch the dashboard")
    demo.add_argument(
        "--path",
        type=Path,
        help="custom folder for the demo repository (default: isolated per-user demo folder)",
    )
    demo.add_argument("--host", default="127.0.0.1")
    demo.add_argument("--port", default=8765, type=int)
    demo.add_argument("--no-browser", action="store_true")
    demo.add_argument("--vita-source", type=Path, help="Path to a local vita-cv checkout (optional)")
    demo.add_argument("--log-dir", type=Path, help="Folder for rotating structured logs (default: user application data)")
    demo.add_argument("--log-level", choices=("debug", "info", "warning", "error"), default="info")

    setup_cmd = commands.add_parser("setup", help="check prerequisites and configure guided setup")
    setup_cmd.add_argument("--check", action="store_true", help="check system prerequisites and exit")
    setup_cmd.add_argument("--demo", action="store_true", help="automatically prepare sample demo after check")
    setup_cmd.add_argument("--non-interactive", action="store_true", help="run without interactive prompts")
    setup_cmd.add_argument("--target", type=Path, help="target directory for demo repository")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        try:
            repository = resolve_repository(Path(args.repository))
            serve(
                repository,
                host=args.host,
                port=args.port,
                document_path=args.document_path,
                open_browser=not args.no_browser,
                vita_source=args.vita_source.resolve() if args.vita_source else None,
                log_dir=args.log_dir.resolve() if args.log_dir else None,
                log_level=args.log_level,
            )
        except (OSError, RuntimeError) as error:
            print(f"vt: {error}", file=sys.stderr)
            return 1
    elif args.command == "demo":
        try:
            from .sample import prepare_demo_repository
            repository = prepare_demo_repository(args.path)
            print(f"Sample CV repository: {repository}")
            print(f"Starting Vita Tree demo dashboard at http://{args.host}:{args.port}")
            serve(
                repository,
                host=args.host,
                port=args.port,
                document_path="main.tex",
                open_browser=not args.no_browser,
                vita_source=args.vita_source.resolve() if args.vita_source else None,
                log_dir=args.log_dir.resolve() if args.log_dir else None,
                log_level=args.log_level,
            )
        except (OSError, RuntimeError) as error:
            print(f"vt demo: {error}", file=sys.stderr)
            return 1
    elif args.command == "setup":
        from .setup import run_setup
        return run_setup(
            check_only=args.check,
            auto_demo=args.demo,
            non_interactive=args.non_interactive,
            target=args.target,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
