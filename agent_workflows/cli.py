"""Command-line entry point for agent-workflows (`agent-workflows` / `aw` / `agentwf`).

This is the packaged CLI. In Batch A (IPD-2) it wires the `install` verb and `--version`
to the existing install engine (parity with the historical `install-workflows.py`); the
`setup`, `uninstall`, `list`, and `status` verbs plus the bare-command smart default are
scaffolded here and implemented in later batches (C-D). All subcommands route through
`main(argv)` so the deprecated root shim and tests can drive them from an argv list.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from . import __version__, engine


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-workflows",
        description="Install and manage the agent-workflows framework across your repos.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"agent-workflows {__version__}",
        help="Print the agent-workflows version and exit.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # install <dir> | all  (the idempotent workhorse; no separate `update` verb)
    p_install = sub.add_parser(
        "install",
        help="Install or update the framework in a repo (idempotent).",
    )
    p_install.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Repo directory to install into (default: current directory). "
        "'all' installs into every configured repo (Batch D).",
    )
    p_install.add_argument("--source", dest="source_root", default=None,
                           help="Path to the source .agents/workflows (dev/override).")
    p_install.add_argument("--dry-run", action="store_true", help="Show actions without writing.")
    p_install.add_argument("--no-backup", action="store_true",
                           help="Do not back up before overwrite/prune.")
    p_install.add_argument("--no-prune", action="store_true",
                           help="Do not remove stale framework files.")

    # Verbs scaffolded now, implemented in later batches (kept discoverable in --help).
    sub.add_parser("setup", help="Guided first-run setup wizard (Batch D).")
    sub.add_parser("uninstall", help="Remove the framework from a repo (Batch D).")
    sub.add_parser("list", help="List configured/discovered repos and currency (Batch D).")
    sub.add_parser("status", help="Show environment + currency summary (Batch D).")

    return parser


def _run_install(args: argparse.Namespace) -> int:
    """Adapt the CLI `install` args to the engine's namespace and run it.

    Batch A supports `install <dir>` (and default cwd). `install all` is a Batch D
    capability (needs config); we fail clearly rather than pretend.
    """

    from pathlib import Path

    if args.target == "all":
        print(
            "install all requires configured repos and lands in a later batch; "
            "for now run 'install <dir>' per repo.",
            file=sys.stderr,
        )
        return 2

    repo_root = Path(args.target).expanduser() if args.target else Path.cwd()

    # Build the engine's argparse.Namespace shape (parity with install-workflows.py).
    engine_args = argparse.Namespace(
        source_root=Path(args.source_root).expanduser() if args.source_root else None,
        repo_root=repo_root,
        dry_run=args.dry_run,
        no_backup=args.no_backup,
        no_prune=args.no_prune,
        version=False,
    )
    return engine.run(engine_args)


def _not_yet(command: str) -> int:
    print(
        f"'{command}' is scaffolded and lands in a later IPD-2 batch. "
        f"Available now: 'install <dir>' and '--version'.",
        file=sys.stderr,
    )
    return 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        # Smart default (setup-if-unconfigured / status) lands in Batch D. For now, help.
        parser.print_help()
        return 0

    if args.command == "install":
        return _run_install(args)

    if args.command in ("setup", "uninstall", "list", "status"):
        return _not_yet(args.command)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
