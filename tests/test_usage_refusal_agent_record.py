"""Behavioral sweep and edge-case verification for usage refusal records under --agent and --json.

awcliux 0z7ds3 E-05.
Asserts that usage refusals arising during argument parsing or early required-flag checks
emit an aw.agent/v1 cannot-run error record on stdout under --agent and a structured JSON
object under --json, without altering human stderr text or exit codes.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys

from pathlib import Path

import pytest

from agent_workflows import agent_schema, cli


def _capture_cli(argv: list[str]) -> tuple[int, str, str]:
    """Execute cli.main in-process capturing stdout, stderr, and exit code."""
    out, err = io.StringIO(), io.StringIO()
    code = None
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = cli.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code if code is not None else 0, out.getvalue(), err.getvalue()


def _discover_required_arg_leaves() -> list[str]:
    """Extract every canonical leaf parser that carries at least one required argument."""
    parser = cli._build_parser()
    leaf_map: dict[str, argparse.ArgumentParser] = {}

    def walk(p: argparse.ArgumentParser, prefix: str = "") -> None:
        subparsers_actions = [
            a for a in p._actions if isinstance(a, argparse._SubParsersAction)
        ]
        if not subparsers_actions:
            leaf = prefix.strip()
            if leaf:
                leaf_map[leaf] = p
            return
        for sa in subparsers_actions:
            seen: list[tuple[str, argparse.ArgumentParser]] = []
            for choice, subp in sa.choices.items():
                if any(subp is prior for _, prior in seen):
                    continue
                seen.append((choice, subp))
                walk(subp, f"{prefix} {choice}".strip())

    walk(parser)

    def has_required_arg(p: argparse.ArgumentParser) -> bool:
        for action in p._actions:
            if action.option_strings:
                if action.required:
                    return True
            else:
                if action.nargs not in ("?", "*", argparse.REMAINDER):
                    return True
        return False

    required = [name for name, p in leaf_map.items() if has_required_arg(p)]
    return sorted(required)


# Named, reasoned exclusion set for leaves whose handler-free refusal is impossible.
# Measured at 0 leaves for this surface: all 68 required-argument leaves refuse cleanly.
EXCLUDED_LEAVES: set[str] = set()

REQUIRED_LEAVES: list[str] = [
    leaf for leaf in _discover_required_arg_leaves() if leaf not in EXCLUDED_LEAVES
]


def test_exclusion_set_size_and_members() -> None:
    """Explicit visibility of the exclusion set size and members."""
    assert len(EXCLUDED_LEAVES) == 0
    assert len(REQUIRED_LEAVES) == 68


@pytest.mark.parametrize("leaf", REQUIRED_LEAVES)
def test_required_arg_leaf_agent_mode(leaf: str) -> None:
    """Case 1: Every required-arg leaf emits a valid cannot-run record under --agent."""
    rc, out, err = _capture_cli(leaf.split() + ["--agent"])
    assert rc == 2
    assert out.strip() != "", f"Empty stdout for leaf '{leaf}'"

    lines = [line for line in out.strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])

    val_errs = agent_schema.validate_agent_record(rec)
    assert val_errs == [], f"Schema validation failed for leaf '{leaf}': {val_errs}"

    assert rec["kind"] == "error"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == f"aw {leaf} --help"

    # Leak checks: no machine-identifying absolute paths
    assert "/home/" not in out, f"Unsanitized /home/ path in stdout: {out!r}"
    assert "/tmp/" not in out, f"Unsanitized /tmp/ path in stdout: {out!r}"


@pytest.mark.parametrize("leaf", REQUIRED_LEAVES)
def test_required_arg_leaf_json_mode(leaf: str) -> None:
    """Case 2: Every required-arg leaf emits a cannot-run JSON object under --json."""
    rc, out, err = _capture_cli(leaf.split() + ["--json"])
    assert rc == 2
    assert out.strip() != "", f"Empty stdout for leaf '{leaf}' under --json"

    data = json.loads(out)
    assert isinstance(data, dict)
    assert data["status"] == "cannot-run"
    assert data["exit_code"] == 2
    assert "next_actions" in data
    assert any(a.get("command") == f"aw {leaf} --help" for a in data["next_actions"])


def test_human_control_ipd_scaffold() -> None:
    """Case 3: Human invocation keeps stdout empty and preserves stderr diagnostic."""
    rc, out, err = _capture_cli(["ipd", "scaffold"])
    assert rc == 2
    assert out == ""
    assert "the following arguments are required:" in err
    assert "Next  aw ipd scaffold --help" in err


def test_conflicting_flags_ipd_scaffold() -> None:
    """Case 4: Combining --agent and --json emits no machine line on stdout."""
    rc, out, err = _capture_cli(["ipd", "scaffold", "--agent", "--json"])
    assert rc == 2
    assert out == ""


def test_flag_after_double_dash_forwarding() -> None:
    """Case 5: A token after bare -- on a forwarding command is not treated as mode."""
    rc, out, err = _capture_cli(["test", "--", "--agent"])
    assert "aw.agent/v1" not in out


def test_unknown_command_agent_mode() -> None:
    """Case 6: Top-level unknown command emits cmd: aw and next: aw --help."""
    rc, out, err = _capture_cli(["nosuch", "--agent"])
    assert rc == 2
    lines = [line for line in out.strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["cmd"] == "aw"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == "aw --help"


@pytest.mark.parametrize(
    "leaf_tokens, leaf_name",
    [
        (["backlog", "new"], "backlog new"),
        (["specs", "new"], "specs new"),
        (["prompts", "new"], "prompts new"),
    ],
)
def test_e04_missing_required_handler_leaves(
    leaf_tokens: list[str], leaf_name: str
) -> None:
    """Case 7: Missing-required handler refusals emit a valid record and keep human stdout empty."""
    # Machine mode: --agent
    rc_agent, out_agent, err_agent = _capture_cli(leaf_tokens + ["--agent"])
    assert rc_agent == 2
    lines = [line for line in out_agent.strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["kind"] == "error"
    assert rec["cmd"] == leaf_name
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == f"aw {leaf_name} --help"

    # Human mode: no flags
    rc_human, out_human, err_human = _capture_cli(leaf_tokens)
    assert rc_human == 2
    assert out_human == ""
    assert err_human.strip() != ""


def test_global_flag_position() -> None:
    """Case 8: Global flag before leaf is captured accurately across command structures."""
    for argv, expected_leaf in [
        (["--agent", "ipd", "scaffold"], "ipd scaffold"),
        (["--agent", "ipd", "set"], "ipd set"),
    ]:
        rc, out, err = _capture_cli(argv)
        assert rc == 2
        lines = [line for line in out.strip().splitlines() if line.strip()]
        rec = json.loads(lines[-1])
        assert agent_schema.validate_agent_record(rec) == []
        assert rec["kind"] == "error"
        assert rec["cmd"] == expected_leaf
        assert rec["outcome"] == "cannot-run"
        assert rec["exit"] == 2
        assert rec["next"] == f"aw {expected_leaf} --help"


def test_invalid_choice_on_family() -> None:
    """Case 9: Invalid choice on a subcommand family emits family cmd and next."""
    rc, out, err = _capture_cli(["ipd", "nosuch", "--agent"])
    assert rc == 2
    lines = [line for line in out.strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["cmd"] == "ipd"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == "aw ipd --help"


def test_representative_subprocess() -> None:
    """Subprocess proof of the real console entry point."""
    res = subprocess.run(
        [sys.executable, "-m", "agent_workflows", "ipd", "scaffold", "--agent"],
        capture_output=True,
        timeout=15,
    )
    assert res.returncode == 2
    lines = [line for line in res.stdout.decode().strip().splitlines() if line.strip()]
    rec = json.loads(lines[-1])
    assert agent_schema.validate_agent_record(rec) == []
    assert rec["cmd"] == "ipd scaffold"
    assert rec["outcome"] == "cannot-run"
    assert rec["exit"] == 2
    assert rec["next"] == "aw ipd scaffold --help"


# ---------------------------------------------------------------------------
# IPD xvv7n4: Comprehensive coverage of remaining early usage refusal arms
# across backlog.run_new (11 arms), specs.run_new (5 arms), prompts.run_new
# (5 arms), and ipd_authoring.run_scaffold (13 arms), under --agent, --json,
# and human mode.
# ---------------------------------------------------------------------------


class RefusalCase:
    def __init__(
        self,
        case_id: str,
        cmd: str,
        argv: list[str] | None = None,
        invoker=None,
    ):
        self.case_id = case_id
        self.cmd = cmd
        self.argv = argv
        self.invoker = invoker

    def run(self, mode: str, repo_path: Path, monkeypatch) -> tuple[int, str, str]:
        if self.invoker is not None:
            return self.invoker(mode, repo_path, monkeypatch)
        assert self.argv is not None
        cmd_args = list(self.argv)
        if mode == "agent":
            cmd_args.append("--agent")
        elif mode == "json":
            cmd_args.append("--json")
        return _capture_cli(cmd_args)


def _invoke_backlog_unreachable_status(
    mode: str, repo_path: Path, monkeypatch
) -> tuple[int, str, str]:
    from agent_workflows import backlog

    ns = argparse.Namespace(
        dir=str(repo_path),
        status="bogus",
        set="demo",
        priority="low",
        work_kind="bug",
        summary="Valid summary",
        agent=(mode == "agent"),
        json=(mode == "json"),
        apply=False,
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = backlog.run_new(ns)
        except SystemExit as exc:
            rc = exc.code
    return rc if rc is not None else 0, out.getvalue(), err.getvalue()


def _invoke_specs_unreachable_containment(
    mode: str, repo_path: Path, monkeypatch
) -> tuple[int, str, str]:
    from agent_workflows import record_placement, specs

    monkeypatch.setattr(
        record_placement,
        "resolve_creation_path",
        lambda *args, **kwargs: (repo_path / "outside" / "escape.spec.md"),
    )
    ns = argparse.Namespace(
        dir=str(repo_path),
        title="Valid Title",
        slug="valid-slug",
        agent=(mode == "agent"),
        json=(mode == "json"),
        apply=False,
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = specs.run_new(ns)
        except SystemExit as exc:
            rc = exc.code
    return rc if rc is not None else 0, out.getvalue(), err.getvalue()


def _invoke_scaffold_missing_set(
    mode: str, repo_path: Path, monkeypatch
) -> tuple[int, str, str]:
    from agent_workflows import ipd_authoring

    ns = argparse.Namespace(
        kind="child",
        title="Valid Title",
        set=None,
        order=1,
        author="Tester",
        priority="low",
        work_kind="bug",
        agent=(mode == "agent"),
        json=(mode == "json"),
        apply=False,
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = ipd_authoring.run_scaffold(ns)
        except SystemExit as exc:
            rc = exc.code
    return rc if rc is not None else 0, out.getvalue(), err.getvalue()


def _invoke_scaffold_missing_order(
    mode: str, repo_path: Path, monkeypatch
) -> tuple[int, str, str]:
    from agent_workflows import ipd_authoring

    ns = argparse.Namespace(
        kind="child",
        title="Valid Title",
        set="demo",
        order=None,
        author="Tester",
        priority="low",
        work_kind="bug",
        agent=(mode == "agent"),
        json=(mode == "json"),
        apply=False,
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = ipd_authoring.run_scaffold(ns)
        except SystemExit as exc:
            rc = exc.code
    return rc if rc is not None else 0, out.getvalue(), err.getvalue()


ALL_REFUSAL_CASES: list[RefusalCase] = [
    # backlog.run_new (11 arms)
    RefusalCase(
        "backlog_setid_length",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--set",
            "a" * 25,
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--summary",
            "valid summary",
        ],
    ),
    RefusalCase(
        "backlog_invalid_priority",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--priority",
            "bogus",
            "--work-kind",
            "bug",
            "--summary",
            "valid summary",
        ],
    ),
    RefusalCase(
        "backlog_invalid_work_kind",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--priority",
            "low",
            "--work-kind",
            "bogus",
            "--summary",
            "valid summary",
        ],
    ),
    RefusalCase(
        "backlog_invalid_summary",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--summary",
            "bad\nsummary",
        ],
    ),
    RefusalCase(
        "backlog_invalid_gate_ref",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--summary",
            "valid summary",
            "--gate-ref",
            "bad\nref",
        ],
    ),
    RefusalCase(
        "backlog_blocked_missing_gate",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--status",
            "blocked",
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--summary",
            "valid summary",
        ],
    ),
    RefusalCase(
        "backlog_blocked_invalid_gate",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--status",
            "blocked",
            "--gate-kind",
            "bogus",
            "--gate-ref",
            "todo",
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--summary",
            "valid summary",
        ],
    ),
    RefusalCase(
        "backlog_invalid_release_exempt",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--summary",
            "valid summary",
            "--release-exempt-kind",
            "bogus",
            "--release-exempt-ref",
            "todo",
        ],
    ),
    RefusalCase(
        "backlog_unknown_blocks_release",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--summary",
            "valid summary",
            "--blocks-release",
            "nonexistent-rel",
        ],
    ),
    RefusalCase(
        "backlog_invalid_message",
        "backlog new",
        argv=[
            "backlog",
            "new",
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--summary",
            "valid summary",
            "--message",
            "bad\nmessage",
        ],
    ),
    RefusalCase(
        "backlog_unreachable_status",
        "backlog new",
        invoker=_invoke_backlog_unreachable_status,
    ),
    # specs.run_new (5 arms)
    RefusalCase(
        "specs_invalid_title",
        "specs new",
        argv=["specs", "new", "--title", "bad\ntitle", "--slug", "spec-slug"],
    ),
    RefusalCase(
        "specs_invalid_summary",
        "specs new",
        argv=[
            "specs",
            "new",
            "--title",
            "Valid Title",
            "--slug",
            "spec-slug",
            "--summary",
            "bad\nsummary",
        ],
    ),
    RefusalCase(
        "specs_lexical_date",
        "specs new",
        argv=[
            "specs",
            "new",
            "--title",
            "Valid Title",
            "--slug",
            "spec-slug",
            "--date",
            "invalid-date",
        ],
    ),
    RefusalCase(
        "specs_calendar_date",
        "specs new",
        argv=[
            "specs",
            "new",
            "--title",
            "Valid Title",
            "--slug",
            "spec-slug",
            "--date",
            "9999-99-99",
        ],
    ),
    RefusalCase(
        "specs_unreachable_containment",
        "specs new",
        invoker=_invoke_specs_unreachable_containment,
    ),
    # prompts.run_new (5 arms)
    RefusalCase(
        "prompts_empty_kebab_slug",
        "prompts new",
        argv=["prompts", "new", "--slug=---", "--kind", "research"],
    ),
    RefusalCase(
        "prompts_unrecognized_kind",
        "prompts new",
        argv=["prompts", "new", "--slug", "valid-slug", "--kind", "bogus"],
    ),
    RefusalCase(
        "prompts_invalid_date",
        "prompts new",
        argv=[
            "prompts",
            "new",
            "--slug",
            "valid-slug",
            "--kind",
            "research",
            "--date",
            "invalid-date",
        ],
    ),
    RefusalCase(
        "prompts_invalid_time",
        "prompts new",
        argv=[
            "prompts",
            "new",
            "--slug",
            "valid-slug",
            "--kind",
            "research",
            "--time",
            "99",
        ],
    ),
    RefusalCase(
        "prompts_set_id_err",
        "prompts new",
        argv=[
            "prompts",
            "new",
            "--slug",
            "valid-slug",
            "--kind",
            "research",
            "--set",
            "a" * 25,
        ],
    ),
    # ipd_authoring.run_scaffold (13 arms)
    RefusalCase(
        "scaffold_invalid_kind",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "bogus",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "1",
            "--author",
            "Tester",
            "--priority",
            "low",
            "--work-kind",
            "bug",
        ],
    ),
    RefusalCase(
        "scaffold_empty_title",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "",
            "--set",
            "demo",
            "--order",
            "1",
            "--author",
            "Tester",
            "--priority",
            "low",
            "--work-kind",
            "bug",
        ],
    ),
    RefusalCase(
        "scaffold_setid_length",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Title",
            "--set",
            "a" * 25,
            "--order",
            "1",
            "--author",
            "Tester",
            "--priority",
            "low",
            "--work-kind",
            "bug",
        ],
    ),
    RefusalCase(
        "scaffold_orchestrator_order",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "orchestrator",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "1",
            "--author",
            "Tester",
            "--priority",
            "low",
            "--work-kind",
            "bug",
        ],
    ),
    RefusalCase(
        "scaffold_child_order",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "0",
            "--author",
            "Tester",
            "--priority",
            "low",
            "--work-kind",
            "bug",
        ],
    ),
    RefusalCase(
        "scaffold_missing_author",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "1",
            "--priority",
            "low",
            "--work-kind",
            "bug",
        ],
    ),
    RefusalCase(
        "scaffold_unknown_from_backlog",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "1",
            "--author",
            "Tester",
            "--from-backlog",
            "zz99zz",
            "--priority",
            "low",
            "--work-kind",
            "bug",
        ],
    ),
    RefusalCase(
        "scaffold_missing_priority_kind",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "1",
            "--author",
            "Tester",
        ],
    ),
    RefusalCase(
        "scaffold_invalid_priority",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "1",
            "--author",
            "Tester",
            "--priority",
            "bogus",
            "--work-kind",
            "bug",
        ],
    ),
    RefusalCase(
        "scaffold_invalid_work_kind",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "1",
            "--author",
            "Tester",
            "--priority",
            "low",
            "--work-kind",
            "bogus",
        ],
    ),
    RefusalCase(
        "scaffold_nonconforming_path",
        "ipd scaffold",
        argv=[
            "ipd",
            "scaffold",
            "--kind",
            "child",
            "--title",
            "Title",
            "--set",
            "demo",
            "--order",
            "1",
            "--author",
            "Tester",
            "--priority",
            "low",
            "--work-kind",
            "bug",
            "--path",
            "invalid_name.md",
        ],
    ),
    RefusalCase(
        "scaffold_unreachable_missing_set",
        "ipd scaffold",
        invoker=_invoke_scaffold_missing_set,
    ),
    RefusalCase(
        "scaffold_unreachable_missing_order",
        "ipd scaffold",
        invoker=_invoke_scaffold_missing_order,
    ),
]


@pytest.fixture
def clean_scratch_repo(tmp_path: Path, monkeypatch) -> Path:
    (tmp_path / ".aw" / "records" / "backlog").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".aw" / "records" / "specs" / "draft").mkdir(
        parents=True, exist_ok=True
    )
    (tmp_path / ".aw" / "records" / "prompts" / "pending").mkdir(
        parents=True, exist_ok=True
    )
    (tmp_path / ".aw" / "records" / "plans" / "pending").mkdir(
        parents=True, exist_ok=True
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AW_IPD_AUTHOR", raising=False)
    return tmp_path


@pytest.mark.parametrize(
    "case", ALL_REFUSAL_CASES, ids=[c.case_id for c in ALL_REFUSAL_CASES]
)
@pytest.mark.parametrize("mode", ["agent", "json", "human"])
def test_handler_usage_refusal_across_modes(
    case: RefusalCase, mode: str, clean_scratch_repo: Path, monkeypatch
) -> None:
    rc, out, err = case.run(mode, clean_scratch_repo, monkeypatch)
    assert rc == 2
    assert (
        str(clean_scratch_repo) not in out
    ), f"Leak: scratch repo path found in stdout: {out!r}"
    assert "/home/" not in out, f"Leak: /home/ path found in stdout: {out!r}"
    assert "/tmp/" not in out, f"Leak: /tmp/ path found in stdout: {out!r}"

    if mode == "agent":
        lines = [line for line in out.strip().splitlines() if line.strip()]
        assert (
            len(lines) == 1
        ), f"Expected exactly one stdout line under --agent, got: {out!r}"
        rec = json.loads(lines[0])
        val_errs = agent_schema.validate_agent_record(rec)
        assert (
            val_errs == []
        ), f"Schema validation failed for {case.case_id}: {val_errs}"
        assert rec["kind"] == "error"
        assert rec["cmd"] == case.cmd
        assert rec["outcome"] == "cannot-run"
        assert rec["exit"] == 2
        assert rec["next"] == f"aw {case.cmd} --help"
        assert err.strip() != ""
    elif mode == "json":
        data = json.loads(out)
        assert isinstance(data, dict)
        assert data["status"] == "cannot-run"
        assert data["exit_code"] == 2
        assert "next_actions" in data
        assert any(
            a.get("command") == f"aw {case.cmd} --help" for a in data["next_actions"]
        )
        assert err.strip() != ""
    else:  # human
        if case.cmd == "ipd scaffold":
            assert out.startswith("error: ")
        else:
            assert out == ""
            assert err.strip() != ""


@pytest.mark.parametrize("mode", ["agent", "json"])
def test_scaffold_success_normalized_author_single_record(
    mode: str, clean_scratch_repo: Path, monkeypatch
) -> None:
    argv = [
        "ipd",
        "scaffold",
        "--kind",
        "child",
        "--title",
        "Test Title",
        "--set",
        "demo",
        "--order",
        "1",
        "--author",
        "Tester (model=test)",
        "--priority",
        "low",
        "--work-kind",
        "bug",
    ]
    if mode == "agent":
        argv.append("--agent")
    else:
        argv.append("--json")

    rc, out, err = _capture_cli(argv)
    assert rc == 0

    if mode == "agent":
        assert (
            str(clean_scratch_repo) not in out
        ), f"Leak: scratch repo path found in stdout: {out!r}"
        assert "/home/" not in out, f"Leak: /home/ path found in stdout: {out!r}"
        assert "/tmp/" not in out, f"Leak: /tmp/ path found in stdout: {out!r}"
        lines = [line for line in out.strip().splitlines() if line.strip()]
        assert (
            len(lines) == 1
        ), f"Expected exactly one stdout line under --agent, got: {out!r}"
        rec = json.loads(lines[0])
        val_errs = agent_schema.validate_agent_record(rec)
        assert val_errs == [], f"Schema validation failed on success: {val_errs}"
        assert rec["kind"] == "result"
        assert rec["outcome"] == "clean"
        assert rec["cmd"] == "ipd scaffold"
        assert rec["exit"] == 0
    else:
        data = json.loads(out)
        assert isinstance(data, dict)
        assert data["status"] == "clean"
        assert data["exit_code"] == 0

    assert "note: normalized --author" in err
