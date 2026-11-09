"""Command-line interface for vita-tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .server import resolve_repository, serve


def _server_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--vita-source", type=Path, help="Path to a local vita-cv checkout (optional)")
    parser.add_argument("--log-dir", type=Path, help="Folder for rotating structured logs (default: user application data)")
    parser.add_argument("--log-level", choices=("debug", "info", "warning", "error"), default="info")


def build_parser() -> argparse.ArgumentParser:
    from .setup import add_arguments

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
    run.add_argument(
        "--file",
        dest="document_path",
        default="main.tex",
        help="document path inside each branch (default: main.tex)",
    )
    _server_arguments(run)

    demo = commands.add_parser("demo", help="open the bundled sample CV in an isolated Git repository")
    demo.add_argument("--path", type=Path, help="new location for the sample repository (optional)")
    demo.set_defaults(document_path="main.tex")
    _server_arguments(demo)
    add_arguments(commands.add_parser("setup", help="open a sample or your own CV with guided setup"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "setup":
        from .setup import run_setup

        return run_setup(args)

    try:
        if args.command == "demo":
            from .sample import prepare_demo_repository

            repository = prepare_demo_repository(args.path)
        else:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
