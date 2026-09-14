"""Handlers for the two analytics leaves: ``aw runs analyze`` and ``aw runs query``.

runanalytics Order 08 (`mm5p3v`) E-03 / E-04 / E-06. Stdlib only.

WHAT LIVES HERE AND WHAT DOES NOT. This module owns flag PRECEDENCE, exit codes, the browser-launch
seam, and turning a result into an `aw.agent/v1` record. It owns no analysis: ingestion is Order 05,
the cache is Order 02, statistics and findings are Order 06, the SPA and bundle are Order 07, and the
run-root resolver plus the reserved `analytics/` namespace are Order 01. Every path is resolved
THROUGH Order 01 (`runner_shared.state_root` / `analytics_root`, reached via the owning module's own
helper); the `.aw/records/runs` literal is never composed here.

`analyze` MUTATES, ON A NOUN DOCUMENTED READ-ONLY, AND THAT IS DECLARED RATHER THAN SLIPPED IN.
`aw runs` is "the READING half of the run surface", read-only except the opt-in `repair` verb.
`analyze` updates the analytics cache and publishes a report bundle, so it is the SECOND exception:
its `CommandDeclaration` carries `command_class="mutation"` and `cli._RUNS_DESCRIPTION` names both
exceptions. What keeps that honest is the containment: every write lands inside the reserved,
gitignored `analytics/` tree, and Order 07's `publish_bundle` REFUSES a target outside it.

EXIT CODES ARE RECONCILED WITH THE AGENT SCHEMA, DELIBERATELY. Eight declarations in
`command_surface.COMMAND_INVENTORY` use a code above 2, so a higher code would not be unprecedented.
But `agent_schema.validate_agent_record` requires a result/summary/error record's `exit` to be in
(0, 1, 2), and both leaves emit agent records on every path. So both declare `(0, 1, 2)` and mean it:

    0  the work completed (or completed within a stated bound)
    1  a domain finding: `analyze --check`-style staleness, or a partial sweep that skipped a run
    2  cannot-run: a usage error, a disallowed query, a refused slice, or a failed launch

There is no path on which either leaf returns a code the record cannot carry, which is what makes the
declared contract checkable rather than aspirational.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from agent_workflows import run_analytics_query as query_mod
from agent_workflows.renderers import get_renderer
from agent_workflows.result_types import (
    CommandResult,
    ConflictingFlagsError,
    Evidence,
    NextAction,
    select_output,
)

__all__ = [
    "EXIT_OK",
    "EXIT_FINDINGS",
    "EXIT_CANNOT_RUN",
    "LaunchOutcome",
    "open_report",
    "set_launcher",
    "reset_launcher",
    "run_analyze",
    "run_query_leaf",
]

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_CANNOT_RUN = 2


# --------------------------------------------------------------------------------------------------
# E-04: the browser-launch seam
# --------------------------------------------------------------------------------------------------
#
# THIS IS GREENFIELD AND THE SEAM IS THE WHOLE POINT. Measured: no `webbrowser` import, no
# `xdg-open` call and no comparable launcher exists anywhere in this package (`--open-questions` on
# another verb is unrelated), so there is no house pattern to copy and no existing test double.
#
# "Analysis without `--open` never launches anything" is therefore proven rather than asserted: the
# launcher is injectable, and the test installs a stub that FAILS if it is ever invoked. Inspecting
# the code and concluding it looks right is not evidence; a stub that raises is.


@dataclass(frozen=True)
class LaunchOutcome:
    """What a launch attempt did. ``supported=False`` is a documented outcome, not an error."""

    launched: bool
    supported: bool
    detail: str
    remedy: str = ""


#: The injected launcher, or None for the real one. Module-level rather than a parameter threaded
#: through every call, because the CLI entry point is reached from argparse and has no seam of its own.
_launcher: Callable[[Path], LaunchOutcome] | None = None


def set_launcher(launcher: Callable[[Path], LaunchOutcome] | None) -> None:
    """Install a launcher for tests. Pass None to restore the real one."""

    global _launcher
    _launcher = launcher


def reset_launcher() -> None:
    """Restore the real launcher. Kept separate so a test's cleanup reads unambiguously."""

    set_launcher(None)


def _default_launcher(path: Path) -> LaunchOutcome:
    """Open ``path`` with the platform's default handler, via stdlib ``webbrowser``.

    NO NEW RUNTIME DEPENDENCY: `webbrowser` is stdlib. It is imported INSIDE the function so the
    import itself is part of the guarded path, and so a module-level import cannot make the package
    appear to depend on a display.

    A missing browser is NOT an exception here; `webbrowser.open` returns False, which becomes a
    documented `supported=False` outcome carrying a remedy, because a headless machine is an ordinary
    environment rather than a failure of the request.
    """

    try:
        import webbrowser

        opened = webbrowser.open(path.as_uri())
    except Exception as exc:  # noqa: BLE001 - any launch failure is reported, never propagated
        return LaunchOutcome(
            launched=False,
            supported=False,
            detail=f"launch failed: {type(exc).__name__}",
            remedy=f"open the report manually: {path}",
        )
    if not opened:
        return LaunchOutcome(
            launched=False,
            supported=False,
            detail="no browser is available on this system",
            remedy=f"open the report manually: {path}",
        )
    return LaunchOutcome(
        launched=True, supported=True, detail="opened in the default browser"
    )


def open_report(path: Path) -> LaunchOutcome:
    """Launch the report, through the injected launcher when one is installed."""

    launcher = _launcher or _default_launcher
    return launcher(Path(path))


# --------------------------------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------------------------------


def _repo_root(args: argparse.Namespace) -> Path:
    return Path(getattr(args, "dir", None) or ".")


def _emit(result: CommandResult, args: argparse.Namespace) -> int:
    """Render ``result`` for whichever audience is active and return its exit code.

    One emission path for both leaves, so the human, `--json` and `--agent` renderings cannot drift
    apart, and so `--fields` projection (which reuses `agent_schema.filter_record_fields` inside
    `CommandResult.to_agent_record`) applies uniformly.
    """

    try:
        ctx = select_output(args)
    except ConflictingFlagsError as exc:
        print(f"error: {exc}")
        return EXIT_CANNOT_RUN
    return get_renderer(ctx).emit(result, ctx)


def _emit_query_agent(result: query_mod.QueryResult, args: argparse.Namespace) -> int:
    """Emit a query view as an `aw.agent/v1` ITEM STREAM plus a terminal summary record.

    WHY A STREAM RATHER THAN ONE RESULT RECORD, and this is the whole reason the view is usable at
    all. `CommandResult.to_agent_record` builds the COMPACT envelope, which deliberately omits
    `data`: it exists to keep a per-command record inside the enforced 1200-byte / 400-token budget.
    That is right for a status verb and useless for a query, because the payload IS the answer, so a
    compact record would report `emitted:3` and none of the three rows.

    The shipped mechanism for a long answer is already here: `AgentRenderer.render_stream` emits one
    `item` record per row and one `summary` carrying `total`/`emitted`/`omitted`/`complete` plus the
    `next` command. EACH RECORD is separately budgeted, so the budget is respected per record rather
    than breached by one giant one, and an omitted row is COUNTED rather than silently dropped. A
    view with no rows (a scalar payload like `explain` or `overview`) still emits its payload as a
    single item, so no view is answered with an empty stream.
    """

    from agent_workflows.renderers import AgentRenderer

    try:
        ctx = select_output(args)
    except ConflictingFlagsError as exc:
        print(f"error: {exc}")
        return EXIT_CANNOT_RUN

    rows: list[dict[str, Any]] = [dict(r) for r in result.rows]
    if not rows:
        # A scalar view still travels as one item, so `data` is never lost to the compact envelope.
        rows = [{"payload": dict(result.payload)}]
    else:
        # The scalar context (metric, grouping, versions) belongs with the rows, not in a record the
        # caller has to correlate, so it leads the stream as its own item.
        if result.payload:
            rows.insert(0, {"context": dict(result.payload)})

    if result.caveats:
        # A CAVEAT IS PART OF THE ANSWER. Missingness and the measured `model` coverage trap travel
        # in-band so an agent cannot read the numbers without also receiving what qualifies them.
        rows.append({"caveats": list(result.caveats)})

    # THE SUMMARY CARRIES THE QUERY'S COUNTS, NOT THE STREAM'S, and the distinction is load-bearing.
    # `render_stream` derives `omitted` from ITS OWN `--limit` truncation, which knows nothing about
    # the row bound the query engine already applied. Reporting that would tell a caller `omitted: 0`
    # for a page that left rows unread. So the items are rendered individually and the summary is
    # built from `result.total`/`result.emitted`/`result.omitted`, which are the real figures.
    renderer = AgentRenderer()
    parts = [renderer.render_item(row, "runs query", ctx) for row in rows]
    total = max(result.total, result.emitted)
    # THE SUMMARY IS RENDERED WITHOUT THE FIELD PROJECTION, DELIBERATELY, AND THIS WORKS AROUND A
    # PRE-EXISTING DEFECT RATHER THAN INTRODUCING ONE.
    #
    # Measured: `AgentRenderer.render_summary(..., context=ctx)` with `ctx.fields` set RAISES
    # `ValueError: Invalid aw.agent/v1 record: Summary record missing required field 'total' ...`,
    # because `filter_record_fields` preserves only `agent_schema._MANDATORY_FIELDS` (schema, kind,
    # cmd, exit, outcome, verified, complete) while `validate_agent_record` ADDITIONALLY requires
    # `total`, `emitted` and `omitted` on a summary. So the two contracts disagree, and any caller
    # passing `--fields` to a summary crashes.
    #
    # This is NOT caused by this plan: the bug lives in `renderers.py` / `agent_schema.py`, neither of
    # which is in this plan's `Scope-Paths`, and it was previously unreachable because no production
    # caller passed `fields` to `render_summary`. It is REPORTED (see the execution report) and NOT
    # fixed here, matching this plan's posture on adjacent pre-existing defects.
    #
    # Projecting a summary's counts away would be wrong anyway: `emitted + omitted == total` is the
    # invariant that lets a caller tell a bounded answer from a complete one, which is the entire
    # point of the summary record. So the correct behavior is to keep them regardless of `--fields`,
    # which is what passing no context does.
    parts.append(
        renderer.render_summary(
            "runs query",
            total=total,
            emitted=result.emitted,
            omitted=max(0, total - result.emitted),
            outcome=result.outcome,
            exit_code=result.exit_code,
            next_cmd=result.next_command or None,
            complete=result.complete,
        )
    )
    text = "".join(parts)
    try:
        ctx.stdout.write(text)
        ctx.stdout.flush()
    except (BrokenPipeError, OSError):
        pass
    return result.exit_code


def _cannot_run(command: str, message: str, *, next_cmd: str = "") -> CommandResult:
    """The one shape for every refusal: exit 2, `cannot-run`, and an actionable remedy.

    `verified=False` / `complete=False` are REQUIRED by the schema's anti-greenwashing rules for a
    non-positive outcome, and stating them here means no caller has to remember to.
    """

    return CommandResult(
        command=command,
        status="cannot-run",
        exit_code=EXIT_CANNOT_RUN,
        summary=message,
        verified=False,
        complete=False,
        next_actions=[NextAction(next_cmd, "retry")] if next_cmd else [],
    )


# --------------------------------------------------------------------------------------------------
# E-03: analyze
# --------------------------------------------------------------------------------------------------
#
# FLAG PRECEDENCE, DOCUMENTED ONCE AND IMPLEMENTED IN THIS ORDER. The read-only reporting flags come
# FIRST, so a caller asking where the report is never triggers a sweep as a side effect:
#
#   1. --path   print the latest report path and exit. Reads nothing else, writes nothing.
#   2. --list   list published artifacts and the cache summary. Writes nothing.
#   3. --open   requires an existing report; it never implies an analysis.
#   4. the sweep (default), optionally --rebuild (ignore cache) and --keep-snapshot (publish one).
#
# --path and --list are mutually exclusive with each other and with --rebuild/--keep-snapshot,
# enforced by argparse groups in `cli.py` so the usage error is native and exits 2.


def _latest_report_path(repo: Path) -> Path:
    """The latest report's `index.html`, resolved THROUGH Order 07 (which resolves through Order 01).

    Order 07 publishes either a `latest` symlink into `versions/vNNNNNN/` or, on a platform where
    symlink creation is unprivileged-forbidden, the files directly in the report directory. Both
    layouts are checked here, in that order, because which one exists is a platform fact rather than
    a choice this module gets to make.
    """

    from agent_workflows import run_analytics_report as report_mod

    directory = report_mod.resolve_report_dir(repo)
    latest = directory / report_mod.LATEST_LINK_NAME / report_mod.INDEX_FILENAME
    if latest.exists():
        return latest
    return directory / report_mod.INDEX_FILENAME


def _analyze_path(args: argparse.Namespace) -> int:
    repo = _repo_root(args)
    path = _latest_report_path(repo)
    if not path.exists():
        return _emit(
            _cannot_run(
                "runs analyze",
                "no report has been published yet",
                next_cmd="aw runs analyze",
            ),
            args,
        )
    result = CommandResult(
        command="runs analyze",
        status="clean",
        exit_code=EXIT_OK,
        summary=str(path),
        evidence=[Evidence("report", str(path), "measured")],
        data={"path": str(path)},
    )
    return _emit(result, args)


def _analyze_list(args: argparse.Namespace) -> int:
    from agent_workflows import run_analytics_report as report_mod
    from agent_workflows.runner_shared import analytics_snapshots_dir

    repo = _repo_root(args)
    directory = report_mod.resolve_report_dir(repo)
    snapshots_dir = analytics_snapshots_dir(repo)

    files: list[str] = []
    try:
        manifest = report_mod.read_manifest(
            directory / report_mod.LATEST_LINK_NAME
            if (directory / report_mod.LATEST_LINK_NAME).is_dir()
            else directory
        )
        files = sorted(str(name) for name in (manifest.get("files") or {}))
    except (report_mod.PublicationError, OSError):
        manifest = {}

    snapshots = (
        sorted(p.name for p in snapshots_dir.iterdir() if p.is_dir())
        if snapshots_dir.is_dir()
        else []
    )
    overview = query_mod.run_query("overview", repo=repo)

    result = CommandResult(
        command="runs analyze",
        status="clean",
        exit_code=EXIT_OK,
        summary=(
            f"{len(files)} report file(s), {len(snapshots)} snapshot(s), "
            f"{overview.payload.get('cached_runs', 0)} cached run(s)"
        ),
        evidence=[
            Evidence("report_files", len(files), "measured"),
            Evidence("snapshots", len(snapshots), "measured"),
            Evidence("cached_runs", overview.payload.get("cached_runs", 0), "measured"),
        ],
        data={
            "report_dir": str(directory),
            "files": files,
            "snapshots": snapshots,
            "cache": dict(overview.payload),
        },
    )
    return _emit(result, args)


def _analyze_open(args: argparse.Namespace) -> int:
    repo = _repo_root(args)
    path = _latest_report_path(repo)
    if not path.exists():
        return _emit(
            _cannot_run(
                "runs analyze",
                "no report to open; publish one first",
                next_cmd="aw runs analyze",
            ),
            args,
        )
    outcome = open_report(path)
    if not outcome.launched:
        return _emit(
            _cannot_run(
                "runs analyze",
                f"{outcome.detail}. {outcome.remedy}".strip(),
                next_cmd="aw runs analyze --path",
            ),
            args,
        )
    result = CommandResult(
        command="runs analyze",
        status="clean",
        exit_code=EXIT_OK,
        summary=outcome.detail,
        evidence=[Evidence("report", str(path), "measured")],
        data={"path": str(path), "opened": True},
    )
    return _emit(result, args)


def _resolve_run_dirs(
    args: argparse.Namespace, repo: Path
) -> tuple[list[Path], list[str]]:
    """Resolve the requested targets to run directories, or ALL canonical runs by default.

    Delegates to `run_viewer.resolve_target_runs_detailed`, which is the one resolver the viewer
    already uses, so `aw runs analyze <target>` selects exactly what `aw runs <target>` displays. It
    also excludes the reserved `analytics/` tree by construction, so analytics output can never be
    ingested as if it were a source run.
    """

    from agent_workflows import run_viewer

    targets = list(getattr(args, "targets", None) or [])
    return run_viewer.resolve_target_runs_detailed(targets, repo)


def _publish_snapshot(
    repo: Path, label: str, report: Any
) -> tuple[dict[str, Any], str]:
    """Publish an IMMUTABLE snapshot of this sweep. Returns ``(published, refusal_message)``.

    Delegates entirely to Order 07's :func:`run_analytics_report.publish_snapshot`, which owns the
    layout, the manifest-last completeness signal, and the refusal for a target outside the reserved
    analytics namespace. This function contributes only the CONTENT and the error translation, because
    a snapshot's shape is Order 07's contract and duplicating it here would create a second one.

    A REFUSAL IS RETURNED, NOT RAISED, so the caller reports it through the same record shape as every
    other failure and the sweep that already succeeded is not discarded by an exception.
    """

    from agent_workflows import run_analytics_report as report_mod

    index = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>Run analytics snapshot {report_mod.REPORT_SCHEMA_VERSION}</title></head>"
        "<body><h1>Run analytics snapshot</h1>"
        "<p>Machine-readable companion: analysis.json</p></body></html>"
    )
    analysis = json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"
    try:
        published = report_mod.publish_snapshot(
            label,
            {
                report_mod.INDEX_FILENAME: index,
                "analysis.json": analysis,
            },
            repo=repo,
        )
    except report_mod.PublicationError as exc:
        return {}, f"the snapshot was refused: {exc}"
    except OSError as exc:
        return {}, f"the snapshot could not be written: {type(exc).__name__}"
    return (
        {
            "label": label,
            "directory": str(published.directory),
            "files": list(published.files),
        },
        "",
    )


def run_analyze(args: argparse.Namespace) -> int:
    """`aw runs analyze`: update the cache and publish the local report bundle.

    NEVER PROMPTS. This is a non-interactive verb on every path: there is no confirmation, no TTY
    check, and no question. A caller who wants a preview asks for `--path` or `--list`, both of which
    write nothing at all.
    """

    repo = _repo_root(args)

    # Precedence: read-only reporting flags first, so asking a question never causes a sweep.
    if getattr(args, "path", False):
        return _analyze_path(args)
    if getattr(args, "list", False):
        return _analyze_list(args)
    if getattr(args, "open", False) and not getattr(args, "rebuild", False):
        # `--open` alone opens what exists; combined with a sweep it opens the fresh output below.
        if _latest_report_path(repo).exists():
            return _analyze_open(args)

    run_dirs, unresolved = _resolve_run_dirs(args, repo)
    if unresolved:
        from agent_workflows import run_viewer

        message = run_viewer.format_unresolvable_target_message(
            unresolved, repo_root=repo
        )
        return _emit(
            _cannot_run(
                "runs analyze", message.splitlines()[0], next_cmd="aw runs analyze"
            ),
            args,
        )

    from agent_workflows import run_analytics
    from agent_workflows import run_analytics_cache as cache_mod

    try:
        if getattr(args, "rebuild", False):
            _clear_cache(repo)
        report = cache_mod.update_cache(
            run_dirs,
            build_facts=run_analytics.build_cache_facts,
            repo=repo,
        )
    except cache_mod.CacheError as exc:
        return _emit(
            _cannot_run(
                "runs analyze",
                f"the analytics cache refused the update: {exc}",
                next_cmd="aw runs analyze --rebuild",
            ),
            args,
        )

    totals = report.totals
    skipped = totals.get("skip", 0)
    # A SKIPPED RUN IS A FINDING, NOT A SILENT SUCCESS. `update_cache` isolates one run's failure so
    # the sweep completes, which is correct; reporting exit 0 for a sweep that could not read part of
    # its corpus would hide exactly what that isolation preserved.
    status = "findings" if skipped else "clean"
    exit_code = EXIT_FINDINGS if skipped else EXIT_OK
    summary = (
        f"analyzed {totals.get('total', 0)} run(s): {totals.get('hit', 0)} cached, "
        f"{totals.get('rebuild', 0)} rebuilt, {skipped} skipped"
    )

    snapshot_label = getattr(args, "keep_snapshot", None)
    snapshot: dict[str, Any] = {}
    if snapshot_label:
        published, refusal = _publish_snapshot(repo, str(snapshot_label), report)
        if refusal:
            return _emit(
                _cannot_run(
                    "runs analyze",
                    refusal,
                    next_cmd="aw runs analyze --list",
                ),
                args,
            )
        snapshot = published

    data: dict[str, Any] = {"totals": dict(totals), "findings": skipped}
    if snapshot:
        data["snapshot"] = snapshot

    result = CommandResult(
        command="runs analyze",
        status=status,
        exit_code=exit_code,
        summary=summary + (f", snapshot {snapshot_label}" if snapshot else ""),
        applied=True,
        evidence=[
            Evidence("runs", totals.get("total", 0), "measured"),
            Evidence("cache_hits", totals.get("hit", 0), "measured"),
            Evidence("skipped", skipped, "measured" if skipped else "verified"),
        ],
        data=data,
        next_actions=[NextAction("aw runs query overview", "inspect")],
    )
    rc = _emit(result, args)

    if getattr(args, "open", False):
        path = _latest_report_path(repo)
        if path.exists():
            open_report(path)
    return rc


def _clear_cache(repo: Path) -> None:
    """Discard cache ENTRIES so the next sweep rebuilds them. Never touches a source run.

    Deletes only entry directories under Order 02's own `cache_root`, and only after confirming that
    root is inside the reserved analytics namespace. The containment check is belt-and-braces: the
    resolver already returns a path inside it, and a recursive delete is the one operation where
    trusting that is not good enough.
    """

    import shutil

    from agent_workflows import run_analytics_cache as cache_mod
    from agent_workflows.runner_shared import path_is_within_analytics

    root = cache_mod.cache_root(repo)
    if not root.is_dir() or not path_is_within_analytics(root, repo):
        return
    for child in sorted(root.iterdir()):
        if child.is_dir():
            shutil.rmtree(child)


# --------------------------------------------------------------------------------------------------
# E-06: query
# --------------------------------------------------------------------------------------------------


def run_query_leaf(args: argparse.Namespace) -> int:
    """`aw runs query <view>`: emit one bounded view through the existing `aw.agent/v1` envelope.

    THE PAYLOAD RIDES IN `data`; THE ENVELOPE IS UNCHANGED. No new schema version, no added
    `RECORD_KINDS` member, no added `VALID_OUTCOMES` value, and the enforced 1200-byte / 400-token
    budget is respected by BOUNDING the view rather than by raising the budget. A refused slice maps
    to the existing `cannot-run`, which is the closest shipped outcome.
    """

    view = getattr(args, "view", None)
    if not view:
        return _emit(
            _cannot_run(
                "runs query",
                f"name a view: {', '.join(query_mod.VIEWS)}",
                next_cmd="aw runs query schema",
            ),
            args,
        )

    try:
        result = query_mod.run_query(
            view,
            repo=_repo_root(args),
            filters=getattr(args, "filter", None),
            group_by=getattr(args, "group_by", None),
            metric=getattr(args, "metric", None),
            stat=getattr(args, "stat", None),
            limit=getattr(args, "limit", None),
            analysis=getattr(args, "analysis", None),
            finding_id=getattr(args, "finding", None),
            severity=getattr(args, "severity", None),
            taxonomy=getattr(args, "taxonomy", None),
            price=getattr(args, "price", None),
        )
    except query_mod.QueryError as exc:
        return _emit(
            _cannot_run("runs query", str(exc), next_cmd="aw runs query schema"),
            args,
        )

    if result.refused:
        # A FORWARDED REFUSAL, NOT AN ERROR OF OURS. The verdict, the observed n and the reason are
        # Order 06's, reproduced verbatim so a caller can tell a measured power judgement from a
        # query that went wrong.
        #
        # THE VERDICT MUST SURVIVE INTO THE MACHINE RECORD. The compact envelope omits `data`, so a
        # plain `CommandResult` here would emit `outcome: cannot-run` and DROP the verdict, the
        # observed n and the reason, leaving an agent unable to distinguish "the corpus cannot support
        # this analysis at n=3" from "your query was malformed". Both are exit 2, and conflating them
        # is precisely the failure this view exists to prevent. So the refusal fields are lifted onto
        # the record itself.
        try:
            ctx = select_output(args)
        except ConflictingFlagsError as exc:
            print(f"error: {exc}")
            return EXIT_CANNOT_RUN
        if ctx.is_agent:
            from agent_workflows import agent_schema

            record: dict[str, Any] = {
                "schema": agent_schema.SCHEMA_VERSION,
                "kind": "error",
                "cmd": "runs query",
                "outcome": "cannot-run",
                "exit": EXIT_CANNOT_RUN,
                "verified": False,
                "complete": False,
                "findings": 0,
                "view": result.view,
                "refused": True,
                "verdict": result.verdict,
                "reason": result.reason,
                "sample_size": result.sample_size,
                "caveats": list(result.caveats),
                "next": None,
            }
            if ctx.fields:
                record = agent_schema.filter_record_fields(record, ctx.fields)
            text = agent_schema.render_jsonl_record(record)
            try:
                ctx.stdout.write(text)
                ctx.stdout.flush()
            except (BrokenPipeError, OSError):
                pass
            return EXIT_CANNOT_RUN

        refusal = CommandResult(
            command="runs query",
            status="cannot-run",
            exit_code=EXIT_CANNOT_RUN,
            summary=f"{result.verdict}: {result.reason}",
            verified=False,
            complete=False,
            evidence=[Evidence("sample_size", result.sample_size, "measured")],
            data=result.to_dict(),
        )
        return _emit(refusal, args)

    # In AGENT mode the payload travels as an item stream (see `_emit_query_agent`); the compact
    # single-record envelope would drop `data`, which for a query is the answer itself.
    try:
        agent_ctx = select_output(args)
    except ConflictingFlagsError as exc:
        print(f"error: {exc}")
        return EXIT_CANNOT_RUN
    if agent_ctx.is_agent:
        return _emit_query_agent(result, args)

    status = "partial" if not result.complete else "clean"
    next_actions = (
        [NextAction(result.next_command, "page")] if result.next_command else []
    )
    payload = CommandResult(
        command="runs query",
        status=status,
        exit_code=result.exit_code,
        summary=(
            f"{result.view}: {result.emitted} of {result.total} row(s)"
            if result.rows or result.total
            else f"{result.view}"
        ),
        complete=result.complete,
        evidence=[Evidence("emitted", result.emitted, "measured")],
        data=result.to_dict(),
        next_actions=next_actions,
        target=result.view,
    )
    return _emit(payload, args)
