"""Command-line entry point for agent-workflows (`agent-workflows` / `aw` / `agentwf`).

Verbs (spec OQ7): `install <dir>|all`, `setup`, `uninstall <dir>`, `list`, `status`.
There is intentionally NO `update` (install is idempotent) and NO `doctor` (its safety is
preflight-warn+confirm here; its readout is folded into `status`). Bare `aw` is a smart
default: run `setup` when unconfigured, else show `status` + hints.

The CLI (host-level, deterministic, multi-repo) COMPLEMENTS the LLM `/setup-repo` workflow
(in-agent, stack-tailored). After install/setup the CLI points the user at `/setup-repo`
for the judgment layer.

All output goes through `term.Term` for accessible, degrade-when-piped styling (AC-15).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import __version__, config, discovery, engine, versioning
from .term import Term


# --------------------------------------------------------------------------------------
# Argument parsing
# --------------------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    # A shared parent so --no-color works both before AND after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color (also honored via NO_COLOR).",
    )

    parser = argparse.ArgumentParser(
        prog="agent-workflows",
        description="Install and manage the agent-workflows framework across your repos.",
        parents=[common],
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"agent-workflows {__version__}",
        help="Print the agent-workflows version and exit.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p_install = sub.add_parser(
        "install",
        parents=[common],
        help="Install or update the framework in a repo (idempotent).",
    )
    p_install.add_argument(
        "targets",
        nargs="*",
        default=None,
        help="Repo dirs (default: cwd), or 'all' for every configured repo.",
    )
    p_install.add_argument(
        "--source",
        dest="source_root",
        default=None,
        help="Path to the source .agents/workflows (dev/override).",
    )
    p_install.add_argument(
        "--dry-run", action="store_true", help="Show actions without writing."
    )
    p_install.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not back up before overwrite/prune.",
    )
    p_install.add_argument(
        "--no-prune", action="store_true", help="Do not remove stale framework files."
    )
    p_install.add_argument(
        "-y", "--yes", action="store_true", help="Skip preflight confirmations."
    )

    p_setup = sub.add_parser(
        "setup", parents=[common], help="Guided first-run setup wizard."
    )
    p_setup.add_argument(
        "--root",
        dest="roots",
        action="append",
        default=None,
        help="A search root to discover repos under (repeatable). "
        "Non-interactive when supplied.",
    )
    p_setup.add_argument(
        "--recursive", action="store_true", help="Discover repos recursively."
    )
    p_setup.add_argument(
        "-y", "--yes", action="store_true", help="Install without per-repo prompts."
    )
    p_setup.add_argument(
        "--source", dest="source_root", default=None, help=argparse.SUPPRESS
    )

    p_uninstall = sub.add_parser(
        "uninstall",
        parents=[common],
        help="Remove the framework from a repo (asks first).",
    )
    p_uninstall.add_argument(
        "target", help="Repo directory to remove the framework from."
    )
    p_uninstall.add_argument(
        "-y", "--yes", action="store_true", help="Skip the confirmation prompt."
    )

    p_list = sub.add_parser(
        "list",
        parents=[common],
        help="List configured/discovered repos and their currency.",
    )
    p_list.add_argument(
        "--recursive", action="store_true", help="Discover repos recursively."
    )

    sub.add_parser(
        "status", parents=[common], help="Show environment + currency summary."
    )

    p_plans = sub.add_parser(
        "plans",
        parents=[common],
        help="Show a board of plan/IPD readiness Status, grouped by lifecycle.",
    )
    p_plans.add_argument(
        "dir",
        nargs="?",
        default=None,
        help="Repo root to read (default: current directory).",
    )
    p_plans.add_argument(
        "--pending",
        action="store_true",
        help="Only show plans in the pending/ directory.",
    )
    p_plans.add_argument(
        "--status",
        dest="status_filter",
        default=None,
        help="Only show one readiness status.",
    )
    p_plans.add_argument(
        "--write-index",
        action="store_true",
        help="(Re)generate .agents/plans/STATUS.md instead of printing.",
    )

    p_names = sub.add_parser(
        "plan-names",
        parents=[common],
        help="Check (or --apply) that plan/prompt filenames match YYYYMMDD-HHMM-NN-<slug>.md.",
    )
    p_names.add_argument(
        "dir", nargs="?", default=None, help="Repo root (default: current directory)."
    )
    p_names.add_argument(
        "--apply",
        action="store_true",
        help="Perform the staged git-mv renames (default: check).",
    )
    p_names.add_argument(
        "--area",
        action="append",
        default=None,
        help="Top-level .agents/ area to scan (repeatable).",
    )
    p_names.add_argument(
        "--all",
        dest="all_areas",
        action="store_true",
        help="Scan every top-level .agents/ area.",
    )
    p_names.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="fnmatch glob to exclude (repeatable).",
    )
    p_names.add_argument(
        "--no-default-excludes",
        action="store_true",
        help="Drop the built-in README.md exclude.",
    )
    p_names.add_argument(
        "--include-nested",
        action="store_true",
        help="Also rename eligible *.md nested deeper.",
    )
    p_names.add_argument(
        "--rename-non-numeric",
        action="store_true",
        help="Also rename files not starting with a date.",
    )
    p_names.add_argument(
        "--assume-dates",
        action="store_true",
        help="Accept derived dates for 'imported?' files.",
    )
    p_names.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json"],
        default="text",
        help="Output format.",
    )

    return parser


# --------------------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------------------


def _packaged_version() -> str:
    """The version this distribution ships (what installed repos are compared against)."""

    return __version__


def _confirm(term: Term, prompt: str, assume_yes: bool) -> bool:
    """Ask a yes/no question; auto-yes when assume_yes or non-interactive stdin."""

    if assume_yes:
        return True
    if not sys.stdin.isatty():
        # Non-interactive without --yes: refuse to change things silently.
        term.status(
            "warn", f"{prompt} (declining: non-interactive; pass --yes to proceed)"
        )
        return False
    try:
        answer = input(f"{prompt} [y/N] ").strip().lower()
    except EOFError:
        return False
    return answer in ("y", "yes")


def _has_uncommitted_changes(repo_root: Path) -> bool:
    """True if the git working tree has staged or unstaged changes (best-effort)."""

    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def _preflight_warnings(repo_root: Path, packaged: str) -> List[str]:
    """Return preflight WARN messages for a target (ex-`doctor`; D6).

    Warns on: not a git repo; a would-downgrade (installed is 'ahead' of the packaged
    version). The dirty/behind git state is owned by `engine.run_git_diagnostics` (single
    source of truth), which every interactive install path runs; it is NOT duplicated here.
    """

    warnings: List[str] = []
    if not (repo_root / ".git").exists():
        warnings.append(
            f"{repo_root} is not a git repository (install will still write files)."
        )
    installed = engine.read_installed_version(repo_root)
    if installed is not None:
        state = versioning.status(installed, packaged)
        if state == "ahead":
            warnings.append(
                f"{repo_root} has {installed}, which is AHEAD of this tool's {packaged}; "
                "installing would DOWNGRADE it."
            )
    return warnings


def _diagnostics_ok(repo_root: Path, args: argparse.Namespace) -> bool:
    """Run the shared engine git-diagnostics pre-flight for one repo before installing.

    Returns True to proceed, False to skip/abort this repo. Builds a minimal InstallPlan so
    the CLI runs the SAME pre-flight as engine.main()/install-workflows.py (entry-point
    parity, 1837-01). run_git_diagnostics is no-op-silent when the repo is clean+in-sync or
    non-interactive, and only prompts on real risk (tracked-dirty or behind).
    """

    import copy

    engine_args = copy.copy(args)
    engine_args.repo_root = repo_root
    engine_args.version = False
    engine_args.diff = False
    engine_args.undo = False
    # Different callers (install, install-all, setup) carry different arg shapes; ensure the
    # attributes build_install_plan reads are present with safe defaults.
    for attr, default in (
        ("dry_run", False),
        ("no_backup", False),
        ("no_prune", False),
        ("source_root", None),
        ("yes", False),
        ("no_color", False),
    ):
        if not hasattr(engine_args, attr):
            setattr(engine_args, attr, default)
    plan = engine.build_install_plan(engine_args)
    return engine.run_git_diagnostics(plan)


# --------------------------------------------------------------------------------------
# install
# --------------------------------------------------------------------------------------


def _install_one(
    repo_root: Path,
    source_root: Path,
    args: argparse.Namespace,
    term: Term,
) -> str:
    """Install into ONE repo through the single shared shell, then summarize and offer to commit.

    This is the ONE per-repo orchestration all entry points use (D85: `aw install <dir>`,
    `aw install all`, `aw setup`, and the engine `run()` path), so none can drift into
    staging-without-committing. It runs: install_into_repo (steps) -> print_summary -> a status line
    -> prompt_and_run_commit (auto-commits under --yes, prompts otherwise, and on decline prints the
    "left staged; commit with git commit -- ..." line so a repo is NEVER left SILENTLY dirty). It is
    SystemExit-isolated so a dir-conflict/git failure in one repo cannot abort a batch (R-4).

    Returns one of "ok", "nochange", or "failed" for the caller's tally.
    """

    import copy

    try:
        result = engine.install_into_repo(
            repo_root,
            source_root,
            dry_run=getattr(args, "dry_run", False),
            backup=not getattr(args, "no_backup", False),
            prune=not getattr(args, "no_prune", False),
            yes=getattr(args, "yes", False),
            no_color=getattr(args, "no_color", False),
        )
    except (
        Exception,
        SystemExit,
    ) as exc:  # isolate one repo's failure from a batch (R-4).
        term.status("fail", f"{repo_root}: {exc}")
        return "failed"

    workflows = engine.parse_manifest(source_root)
    engine_args = copy.copy(args)
    engine_args.repo_root = repo_root
    engine_args.version = False
    engine_args.diff = False
    engine_args.undo = False
    # The `setup` / `install all` arg namespaces do not carry the `install`-verb flags, but
    # build_install_plan reads them as hard attributes. Fill the same defaults install_into_repo
    # used above so the shared plan is well-formed for every entry point (behavior-preserving:
    # the single-repo `install` path already has these, so getattr returns its real values).
    engine_args.dry_run = getattr(args, "dry_run", False)
    engine_args.no_backup = getattr(args, "no_backup", False)
    engine_args.no_prune = getattr(args, "no_prune", False)
    plan = engine.build_install_plan(engine_args)

    engine.print_summary(
        plan=plan,
        workflows=workflows,
        migrated=result.get("migrated") or [],
        installed=result["installed"],
        skipped=result["skipped"],
        pruned=result["pruned"],
        agents_status=result["agents_status"],
        gitignore_status=result["gitignore_status"],
        backups_ignore_status=result["backups_ignore_status"],
        use_git=result["use_git"],
    )

    n = len(result["installed"])
    if n == 0:
        term.status(
            "ok",
            f"{repo_root}: already current at version {result['version']}; nothing to update.",
        )
        outcome = "nochange"
    else:
        term.status(
            "ok",
            f"{repo_root}: installed/updated {n} file(s); version {result['version']}.",
        )
        outcome = "ok"

    # Offer to commit (auto under --yes; prompt otherwise; on decline it prints how to commit, so
    # nothing is left SILENTLY staged). This is the step batch paths previously skipped (the bug).
    engine.prompt_and_run_commit(
        plan=plan,
        installed=result["installed"],
        pruned=result["pruned"],
        agents_status=result["agents_status"],
        backups_ignore_status=result["backups_ignore_status"],
        use_git=result["use_git"],
        artifacts=result.get("artifacts") or [],
    )
    return outcome


def _run_install(args: argparse.Namespace, term: Term) -> int:
    targets = args.targets if getattr(args, "targets", None) else []
    if "all" in targets:
        return _install_all(args, term)

    repo_roots = (
        [Path(t).expanduser().resolve() for t in targets] if targets else [Path.cwd()]
    )

    if not config.config_path().is_file() and not targets:
        term.status(
            "warn",
            "No config yet. Run 'aw setup' to configure your repos, or "
            "'aw install <dir>' for a one-off.",
        )

    try:
        source_root = engine.resolve_source_root(
            Path(args.source_root).expanduser() if args.source_root else None
        )
    except SystemExit as exc:
        term.status("fail", f"Resolve source root: {exc}")
        return 1

    packaged = _packaged_version()
    returncode = 0

    for repo_root in repo_roots:
        if len(repo_roots) > 1:
            term.line()
            term.heading(f"Target Repo: {repo_root}")

        for w in _preflight_warnings(repo_root, packaged):
            term.status("warn", w)
        # Git diagnostics pre-flight FIRST (dirty/behind handling, shared with the engine);
        # an abort here skips the repo before the install confirm.
        if not _diagnostics_ok(repo_root, args):
            term.status(
                "skip", f"{repo_root}: aborted at git pre-flight; nothing changed."
            )
            returncode = 1
            continue
        if not _confirm(term, f"Install agent-workflows into {repo_root}?", args.yes):
            term.status("skip", f"{repo_root}: aborted; nothing changed.")
            continue

        # Shared per-repo shell (install + summary + commit-offer, SystemExit-isolated).
        if _install_one(repo_root, source_root, args, term) == "failed":
            returncode = 1
    return returncode


def _install_all(args: argparse.Namespace, term: Term) -> int:
    """Install into every repo in the config allowlist, with per-repo isolation (R-3/R-4)."""

    cfg = config.load()
    repos = config.expanded_repos(cfg)
    if not repos:
        term.status(
            "warn", "No repos in your config yet. Run 'aw setup' to add search roots."
        )
        return 1

    try:
        source_root = engine.resolve_source_root(
            Path(args.source_root).expanduser()
            if getattr(args, "source_root", None)
            else None
        )
    except SystemExit as exc:
        term.status("fail", str(exc))
        return 1

    # "all" means every CONFIGURED repo (the allowlist), not every repo on disk. Make that
    # explicit so a user with many on-disk repos is not surprised by the count.
    if not _confirm(
        term,
        f"Install/update agent-workflows into {len(repos)} configured repo(s)?",
        args.yes,
    ):
        term.status("skip", "aborted; nothing changed.")
        return 1

    ok = 0
    failed = 0
    aborted = 0
    for repo in repos:
        if not repo.is_dir():
            term.status("skip", f"{repo}: not a directory")
            continue
        # Same git diagnostics pre-flight as the single-repo path (entry-point parity).
        # No-op-silent when clean/in-sync/non-interactive; an abort skips just this repo.
        if not _diagnostics_ok(repo, args):
            term.status("skip", f"{repo}: aborted at git pre-flight")
            aborted += 1
            continue
        # Shared per-repo shell: installs AND offers to commit (auto under --yes), SystemExit-isolated.
        # Before D85 this batch path staged files and never committed -> a fleet left silently dirty.
        outcome = _install_one(repo, source_root, args, term)
        if outcome == "failed":
            failed += 1
        else:
            ok += 1

    term.line()
    summary = f"{ok} installed, {failed} failed"
    if aborted:
        summary += f", {aborted} aborted"
    summary += f", {len(repos)} configured total"
    term.kv("Summary", summary)
    if ok:
        _teach(term)
    return 1 if failed else 0


def _teach(term: Term) -> None:
    term.line()
    term.status(
        "ok",
        "Next: run the LLM '/setup-repo' workflow in each repo for "
        "stack-tailored conformance (CI, .gitignore, lifecycle contract).",
    )


# --------------------------------------------------------------------------------------
# uninstall
# --------------------------------------------------------------------------------------


def _run_uninstall(args: argparse.Namespace, term: Term) -> int:
    repo_root = Path(args.target).expanduser().resolve()
    if not (repo_root / engine.WORKFLOWS_DIR).is_dir():
        term.status(
            "warn", f"{repo_root}: framework not installed (nothing to remove)."
        )
        return 1
    if not _confirm(
        term,
        f"Remove agent-workflows from {repo_root}? "
        "(framework + generated shims + AGENTS pointer)",
        args.yes,
    ):
        term.status("skip", "aborted; nothing changed.")
        return 1

    use_git = engine.git_available(repo_root)
    actions = engine.uninstall_repo(repo_root, use_git)
    for a in actions:
        term.status("ok", a)

    # Drop the repo from the config allowlist, if present.
    cfg = config.load()
    stored = [
        p for p in cfg.get("repos", []) if config.expand_path(p).resolve() != repo_root
    ]
    if len(stored) != len(cfg.get("repos", [])):
        cfg["repos"] = stored
        config.save(cfg)
        term.status("ok", f"removed {repo_root} from the config repo list.")

    term.status("warn", "Deletions are STAGED, not committed. Review and commit.")
    return 0


# --------------------------------------------------------------------------------------
# list / status
# --------------------------------------------------------------------------------------


def _repos_for_report(recursive: bool) -> List[Path]:
    """Config repos plus repos discovered under the config search roots (deduped)."""

    cfg = config.load()
    repos = list(config.expanded_repos(cfg))
    roots = config.expanded_search_roots(cfg)
    if roots:
        found = discovery.discover(
            roots, ignore=cfg.get("ignore", []), recursive=recursive
        )
        repos.extend(found.targets)
    seen = set()
    out = []
    for r in repos:
        rp = r.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out


def _run_list(args: argparse.Namespace, term: Term) -> int:
    packaged = _packaged_version()
    repos = _repos_for_report(args.recursive)
    if not repos:
        term.status("warn", "No configured or discovered repos. Run 'aw setup'.")
        return 0
    term.heading("Repositories")
    for repo in repos:
        installed = engine.read_installed_version(repo)
        state = versioning.status(installed, packaged)
        detail = installed if installed else "not installed"
        term.status(state, f"{repo}  ({detail})")
    return 0


def _run_status(term: Term) -> int:
    packaged = _packaged_version()
    term.heading("agent-workflows status")
    term.kv("Packaged version", packaged)
    term.kv("Python", sys.version.split()[0])
    term.kv("git", "present" if engine.git_available(Path.cwd()) else "not found")
    term.kv(
        "Config",
        str(config.config_path())
        + ("" if config.config_path().is_file() else "  (none yet; run 'aw setup')"),
    )
    cfg = config.load()
    term.kv("Search roots", ", ".join(cfg.get("search_roots", [])) or "(none)")
    term.kv("Repos configured", str(len(cfg.get("repos", []))))

    repos = _repos_for_report(recursive=False)
    if repos:
        counts = {}
        for repo in repos:
            state = versioning.status(engine.read_installed_version(repo), packaged)
            counts[state] = counts.get(state, 0) + 1
        term.line()
        term.heading("Currency")
        for state in ("current", "stale", "ahead", "dev", "not-installed", "unknown"):
            if counts.get(state):
                term.status(state, f"{counts[state]} repo(s)")
    return 0


# --------------------------------------------------------------------------------------
# setup wizard
# --------------------------------------------------------------------------------------


def _run_setup(args: argparse.Namespace, term: Term) -> int:
    cfg = config.load()
    interactive = args.roots is None and sys.stdin.isatty()

    if args.roots is None and config.is_configured() and not sys.stdin.isatty():
        # Non-interactive re-run of a configured tool: summarize, do not re-interview.
        term.status("ok", "Already configured.")
        return _run_status(term)

    # Gather search roots.
    roots: List[str] = []
    if args.roots:
        roots = list(args.roots)
    elif interactive:
        term.heading("agent-workflows setup")
        term.line(
            "Where do you keep your repositories? Enter one path per line "
            "(use ~ for home); blank to finish."
        )
        existing = cfg.get("search_roots", [])
        if existing:
            term.kv("Current roots", ", ".join(existing))
        while True:
            entry = input("  root> ").strip()  # KeyboardInterrupt/EOF handled in main()
            if not entry:
                break
            expanded = Path(entry).expanduser()
            stored = config._preserve_home(str(expanded))
            if not expanded.exists():
                term.status(
                    "warn",
                    f"{stored} does not exist yet; storing it anyway (roots are scanned "
                    "when you install).",
                )
            elif not expanded.is_dir():
                term.status("fail", f"{stored} is not a directory; skipped.")
                continue
            if stored in roots:
                term.status("skip", f"{stored} already added.")
                continue
            roots.append(stored)
            term.status("ok", f"Added {stored}.")
        if not roots:
            roots = existing
    else:
        term.status(
            "warn", "Non-interactive and no --root given; nothing to configure."
        )
        return 1

    if roots:
        # Merge (store ~-preserved via normalize on save).
        merged = list(dict.fromkeys(list(cfg.get("search_roots", [])) + roots))
        cfg["search_roots"] = merged

    # Discover repos under the roots.
    expanded_roots = [config.expand_path(r) for r in cfg.get("search_roots", [])]
    found = discovery.discover(
        expanded_roots, ignore=cfg.get("ignore", []), recursive=args.recursive
    )
    term.line()
    term.heading("Discovered repositories")
    if not found.targets:
        term.status("warn", "No git repos found under those roots.")
    for repo in found.targets:
        term.status("ok", str(repo))
    for repo, reason in sorted(found.skipped.items()):
        term.status("skip", f"{repo} ({reason})")
    for repo in found.ignored:
        term.status("ignored", str(repo))

    # Record discovered repos into the allowlist.
    if found.targets:
        cfg_repos = list(cfg.get("repos", []))
        for repo in found.targets:
            cfg_repos.append(str(repo))
        cfg["repos"] = list(dict.fromkeys(cfg_repos))

    saved = config.save(cfg)
    term.status("ok", f"Saved config to {saved}")

    # Install into discovered repos (with consent unless --yes).
    if found.targets and _confirm(
        term,
        f"Install agent-workflows into {len(found.targets)} repo(s) now?",
        args.yes,
    ):
        try:
            source_root = engine.resolve_source_root(
                Path(args.source_root).expanduser()
                if getattr(args, "source_root", None)
                else None
            )
        except SystemExit as exc:
            term.status("fail", str(exc))
            return 1
        for repo in found.targets:
            # Same git diagnostics pre-flight as the other install paths (parity).
            if not _diagnostics_ok(repo, args):
                term.status("skip", f"{repo}: aborted at git pre-flight")
                continue
            # Shared per-repo shell: installs AND offers to commit (auto under --yes),
            # SystemExit-isolated. Before D85 setup staged files and never committed.
            _install_one(repo, source_root, args, term)

    _orient(term)
    return 0


def _orient(term: Term) -> None:
    term.line()
    term.heading("You are set up")
    term.line("The workflows are agent instructions your AI coding tool runs. Try:")
    term.line(
        "  /release-review, /assess <concern>, /advise <persona>, /verify, /setup-repo"
    )
    term.line("Or from any agent: 'Read and execute .agents/workflows/index.md'.")
    _teach(term)


# --------------------------------------------------------------------------------------
# dispatch
# --------------------------------------------------------------------------------------


def _run_plans(args: argparse.Namespace, term: Term) -> int:
    from . import plans as plans_mod

    root = (
        Path(args.dir).expanduser().resolve()
        if getattr(args, "dir", None)
        else Path.cwd()
    )

    if not (root / ".agents" / "plans").is_dir():
        term.status("skip", f"No plans found (no .agents/plans/ under {root}).")
        return 0

    records = plans_mod.scan(root)

    if getattr(args, "pending", False):
        records = [r for r in records if r.disposition == "pending"]
    status_filter = getattr(args, "status_filter", None)
    if status_filter:
        want = plans_mod.normalize_status(status_filter)
        records = [r for r in records if r.status == want]

    if getattr(args, "write_index", False):
        index_path = root / ".agents" / "plans" / "STATUS.md"
        index_path.write_text(
            plans_mod.render_status_index(root, records), encoding="utf-8"
        )
        term.status(
            "ok",
            f"Wrote {index_path.relative_to(root).as_posix()} ({len(records)} entries).",
        )
        return 0

    if not records:
        term.status("skip", "No matching plans.")
        return 0

    by_disp = plans_mod.group(records)
    term.kv("Total", f"{len(records)} plan/prompt file(s)")
    for disp in plans_mod.DISPOSITION_DIRS:
        statuses = by_disp.get(disp)
        if not statuses:
            continue
        count = sum(len(v) for v in statuses.values())
        term.line()
        term.heading(f"{disp}/ ({count})")
        for status in sorted(statuses, key=plans_mod._status_sort_key):
            recs = statuses[status]
            term.line(f"  {term.colorize(status, 'bold')} ({len(recs)})")
            for rec in sorted(recs, key=lambda r: r.path.name):
                term.line(f"    {rec.path.relative_to(root).as_posix()}")
    return 0


def _load_normalizer():
    """Import the plan-name normalizer script (it lives under the bundled workflow tree).

    Resolves the `.agents/workflows/` root via `_compat.packaged_source_root()` (installed
    wheel) or the repo root (source checkout / editable install), then loads the standalone
    script by path (it is a script, not an importable package module). Returns the module or
    None if it cannot be located/loaded.
    """

    import importlib.util

    from . import _compat

    root = _compat.packaged_source_root()
    if root is None:
        # Source checkout: .agents/workflows lives at the repo root (two levels up from here).
        root = Path(__file__).resolve().parent.parent / ".agents" / "workflows"
    script = root / "setup-repo" / "tools" / "normalize_plan_names.py"
    if not script.is_file():
        return None
    spec = importlib.util.spec_from_file_location("aw_normalize_plan_names", script)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_plan_names(args: argparse.Namespace, term: Term) -> int:
    normalizer = _load_normalizer()
    if normalizer is None:
        term.status("fail", "Could not locate the plan-name normalizer script.")
        return 1

    root = Path(args.dir).expanduser() if getattr(args, "dir", None) else Path.cwd()
    passthrough = ["--repo", str(root), "--format", getattr(args, "fmt", "text")]
    if getattr(args, "apply", False):
        passthrough.append("--apply")
    if getattr(args, "all_areas", False):
        passthrough.append("--all")
    for area in getattr(args, "area", None) or []:
        passthrough += ["--area", area]
    for glob in getattr(args, "exclude", None) or []:
        passthrough += ["--exclude", glob]
    if getattr(args, "no_default_excludes", False):
        passthrough.append("--no-default-excludes")
    if getattr(args, "include_nested", False):
        passthrough.append("--include-nested")
    if getattr(args, "rename_non_numeric", False):
        passthrough.append("--rename-non-numeric")
    if getattr(args, "assume_dates", False):
        passthrough.append("--assume-dates")

    # Delegate to the script's own main(argv); it prints its report and returns its exit code.
    return normalizer.main(passthrough)


def _dispatch(argv: Optional[Sequence[str]]) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    term = Term(color=False if args.no_color else None)

    if args.command is None:
        # Smart default (D7): setup if unconfigured, else status + hints.
        if not config.is_configured():
            if sys.stdin.isatty():
                return _run_setup(
                    argparse.Namespace(
                        roots=None, recursive=False, yes=False, source_root=None
                    ),
                    term,
                )
            term.status("warn", "Not configured. Run 'aw setup' to get started.")
            return _run_status(term)
        _run_status(term)
        term.line()
        term.line(
            "Commands: install <dir>|all, setup, uninstall <dir>, list, status, plans, "
            "plan-names. See 'aw --help'."
        )
        return 0

    if args.command == "install":
        return _run_install(args, term)
    if args.command == "uninstall":
        return _run_uninstall(args, term)
    if args.command == "list":
        return _run_list(args, term)
    if args.command == "status":
        return _run_status(term)
    if args.command == "setup":
        return _run_setup(args, term)
    if args.command == "plans":
        return _run_plans(args, term)
    if args.command == "plan-names":
        return _run_plan_names(args, term)

    parser.print_help()
    return 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Catches CTRL-C / EOF at any prompt and exits cleanly (D-CLI-UX).

    Returns the conventional 130 for a user interrupt instead of dumping a traceback.
    MUST return (not sys.exit) so in-process callers/tests reading the int keep working;
    ``__main__`` turns the return value into the process exit code.
    """

    try:
        return _dispatch(argv)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
    except EOFError:
        print("\nCancelled (end of input).", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
