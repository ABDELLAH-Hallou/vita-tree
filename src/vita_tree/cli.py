"""Command-line interface for vita-tree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .server import resolve_repository, serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vt",
        description="Browse Git branches and preview their LaTeX documents.",
    )
    parser.add_argument("--version", action="version", version="vita-tree 0.1.0")
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
            )
        except (OSError, RuntimeError) as error:
            print(f"vt: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
