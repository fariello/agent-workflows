#!/usr/bin/env python3
"""laneraceplan-01 (`kl18sz`): a records-only front-matter backfill survives its own run.

THE DEFECT, MEASURED RATHER THAN ARGUED. A plan whose job is to edit front matter across the whole
`pending/` population contends by construction with every execute item in its own run, so the more
successful the run the more conflicts it causes and the more likely it is to be stranded. Item
`8u6770` in run `run-20260922T024054Z-2245533` ended `merge-refused` with a real git conflict in 13
files, every one a `.aw/records/plans/*.ipd.md` and none of them code.

RE-MEASURED AT EXECUTION (2026-09-23) AND THE MEASUREMENT GREW. The plan records `aw/lane/8u6770` as
absent from all lane branches, which is true of the BRANCH REFS; the lane's commits survive as
DANGLING OBJECTS here and its finalize tip `0abc01d9` is still resolvable, so the real replay was
reconstructed from it rather than from the 4-path substitute the plan sanctioned. `git merge-tree
--write-tree main 0abc01d9` reports 34 conflicting paths (30 already in `executed/`, 4 still in
`pending/`), all 34 classify as this one shape, and on all 34 the target's `- Status:` had changed.

THE SHAPE IS A LIFECYCLE RACE, NOT A DISAGREEMENT. The lane adds two adjacent front-matter lines
(`- Work-Kind:`, `- Priority:`) plus one history line; main moved the same plan `pending/` ->
`executed/` and rewrote its `- Status:`. The lane's own appended history line reads "status unchanged
(no lifecycle transition)", so it never intended to touch `- Status:` at all.

THE TRAP IS A RESOLVER'S, NOT A SILENT MERGE'S, and the distinction is load-bearing because an
earlier draft of the plan overstated it. Git always conflicts loudly in this shape (pinned by
`test_git_really_does_conflict_loudly_in_this_shape`), so no data is lost by git. The hazard is a
human or agent typing "keep the lane's version" at the prompt, which would assert that 30 plans
sitting in `executed/` are merely `approved`.

THE TWO CONTROLS ARE THE POINT OF THIS FILE, and they are why one would not suffice:

* THE ANTI-REVERT CONTROL asserts that no code path can leave a plan present in a TERMINAL directory
  on the target carrying a non-terminal `- Status:` from the incoming branch. It is demonstrated
  FAILING when re-derivation is deliberately widened to include `- Status:`
  (`test_the_anti_revert_control_FAILS_when_rederivation_is_widened_to_status`).
* THE ALLOW-LIST CONTROL asserts the mechanism can never write a GATE or ATTESTATION key.
  `- Status:` is not the only dangerous field: `- Readiness:` is an attestation only `/plan-review`
  may write and the auto-approve predicate reads FIRST, so an integration able to write it would be
  strictly worse than the conflict it resolves.

REAL GIT, NOT MOCKS, for every end-to-end case: the defect is about what git actually does with
adjacent lines of a renamed file, so a fixture asserting the author's belief about that would pass
against broken code. The PURE classifier arms are unit-tested directly, which is why the classifier
takes texts rather than reading files.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from agent_workflows import agy_runipd, oc_runipd, runner_shared, worktree_lease

PLAN_NAME = "20260901-race-01-aaa111-a-plan.ipd.md"
PENDING = f".aw/records/plans/pending/{PLAN_NAME}"
EXECUTED = f".aw/records/plans/executed/{PLAN_NAME}"

BASE_PLAN = """# IPD: a plan

- Date: 2026-09-01
- Kind: child
- Scope-Paths: agent_workflows/x.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: race
- Order: 1
- Id: aaa111
- From-Backlog: bbb222

## Workflow history
- 2026-09-01 draft (author): created.

## Goal

body text that neither side edits
"""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def _run_checked_for(repo: Path):
    def _rc(argv, cwd=None, env=None):
        proc = subprocess.run(
            argv,
            cwd=str(cwd or repo),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return proc.stdout.strip()

    return _rc


def _init(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "T")
    # The hooks are LOCAL and irrelevant to the mechanism under test; a scratch repo has none.
    _git(repo, "config", "commit.gpgsign", "false")


def _write(repo: Path, rel: str, text: str) -> None:
    dest = repo / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")


@pytest.fixture()
def race_repo(tmp_path: Path) -> tuple[Path, str]:
    """The measured shape: lane backfills two fields; main executes the same plan.

    Returns ``(repo, base_commit)``. The lane branch is `lane`; main holds the plan in `executed/`
    with `- Status: executed` and its own extra history line.
    """
    repo = tmp_path / "repo"
    _init(repo)
    _write(repo, PENDING, BASE_PLAN)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()

    _git(repo, "checkout", "-qb", "lane")
    lane_text = BASE_PLAN.replace(
        "- Status: approved\n",
        "- Status: approved\n- Work-Kind: bug\n- Priority: medium\n",
    ).replace(
        "## Workflow history\n",
        "## Workflow history\n- 2026-09-20 approved (aw set): inherited Priority/Work-Kind from"
        " bbb222; status unchanged (no lifecycle transition).\n",
    )
    _write(repo, PENDING, lane_text)
    _git(repo, "commit", "-qam", "lane: backfill Priority/Work-Kind")

    _git(repo, "checkout", "-q", "main")
    (repo / ".aw/records/plans/executed").mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", PENDING, EXECUTED)
    main_text = BASE_PLAN.replace(
        "- Status: approved\n", "- Status: executed\n"
    ).replace(
        "## Workflow history\n",
        "## Workflow history\n- 2026-09-21 executed (aw oc run): finalized.\n",
    )
    _write(repo, EXECUTED, main_text)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "main: execute the plan")
    return repo, base


def _classify_live(repo: Path, base: str) -> list:
    """Drive a real conflicting merge and classify its conflict set (merge left in progress)."""
    _git(repo, "merge", "--ff-only", "lane")
    _git(repo, "merge", "--no-ff", "--no-edit", "-m", "m", "lane")
    conflicted = runner_shared.conflicted_paths(repo)
    return runner_shared.classify_conflict_set_for_rederivation(
        repo, paths=conflicted, branch="lane", base_commit=base
    )


# --------------------------------------------------------------------------------------------------
# The premise: git's own behavior in this shape (measured, not assumed)
# --------------------------------------------------------------------------------------------------


def test_git_really_does_conflict_loudly_in_this_shape(
    race_repo: tuple[Path, str],
) -> None:
    """THE PLAN'S CORRECTED CLAIM: git never silently un-executes; it conflicts.

    An earlier draft called the hazard a SILENT merge revert. Measurement disproved it, and this test
    pins the corrected premise so the file's whole rationale stays checkable: a stale side that edits
    a plan main has moved produces a LOUD conflict, so the risk lives in the resolution step.
    """
    repo, _base = race_repo
    proc = _git(repo, "merge", "--no-ff", "--no-edit", "-m", "m", "lane")
    assert proc.returncode != 0
    assert "CONFLICT" in proc.stdout
    assert runner_shared.conflicted_paths(repo) == [EXECUTED]


# --------------------------------------------------------------------------------------------------
# E-01: the classifier, including every negative arm
# --------------------------------------------------------------------------------------------------


def test_the_allow_list_is_exactly_the_two_measured_keys() -> None:
    """The allow-list is an ALLOW-list of exactly what the measured case needs, and no more."""
    assert runner_shared.REDERIVABLE_FRONT_MATTER_KEYS == frozenset(
        ("Work-Kind", "Priority")
    )


def test_a_real_conflict_of_this_shape_classifies_as_a_match(
    race_repo: tuple[Path, str],
) -> None:
    repo, base = race_repo
    verdicts = _classify_live(repo, base)
    assert [v.verdict for v in verdicts] == [runner_shared.REDERIVE_SHAPE_MATCH]
    verdict = verdicts[0]
    assert dict(verdict.added_keys) == {"Work-Kind": "bug", "Priority": "medium"}
    assert verdict.target_status == "executed"
    assert verdict.incoming_status == "approved"
    assert verdict.target_is_terminal is True
    assert len(verdict.history_lines) == 1
    rederivable, why = runner_shared.classify_records_only_conflict_set(verdicts)
    assert rederivable, why


def _classify_text(
    *, path: str = EXECUTED, base=BASE_PLAN, target=None, incoming=None, **kw
):
    return runner_shared.classify_records_only_front_matter_conflict(
        path=path,
        base_text=base,
        target_text=target,
        incoming_text=incoming,
        **kw,
    )


def test_a_code_path_is_proved_NOT_this_shape() -> None:
    verdict = _classify_text(
        path="agent_workflows/runner_shared.py",
        target="x = 1\n",
        incoming="x = 2\n",
    )
    assert verdict.verdict == runner_shared.REDERIVE_SHAPE_NOT
    assert ".aw/records/" in verdict.reason


def test_a_status_versus_status_disagreement_is_proved_NOT_this_shape() -> None:
    """The incoming side ASSERTING a transition is a real disagreement, never a race."""
    incoming = BASE_PLAN.replace("- Status: approved\n", "- Status: not-executed\n")
    target = BASE_PLAN.replace("- Status: approved\n", "- Status: executed\n")
    verdict = _classify_text(target=target, incoming=incoming)
    assert verdict.verdict == runner_shared.REDERIVE_SHAPE_NOT
    assert "Status" in verdict.reason


@pytest.mark.parametrize(
    "key,value",
    [
        # THE SHARPEST CASE FIRST: a forged attestation the auto-approve predicate reads BEFORE the
        # workflow history, so an integration able to write it could promote a plan to approved.
        ("Readiness", "go"),
        ("Approval", "2026-09-22, recorded via aw ipd set"),
        ("Blocks-Release", "next"),
        ("Item-Dependencies", "executed:zzz999"),
        ("Highest E allocated", "07"),
    ],
)
def test_a_gate_or_attestation_key_is_never_this_shape(key: str, value: str) -> None:
    """THE ALLOW-LIST CONTROL: adding a lifecycle/gate/attestation key is NOT re-derivable.

    A deny-list of one key (`- Status:`) would admit every one of these. Each is refused because it
    would let an automated integration write a field whose forgery this repository treats as serious.
    """
    base = BASE_PLAN.replace(f"- {key}: ", "- Unrelated-Key: ")
    incoming = base.replace(
        "- Status: approved\n", f"- Status: approved\n- {key}: {value}\n"
    )
    target = base.replace("- Status: approved\n", "- Status: executed\n")
    verdict = _classify_text(base=base, target=target, incoming=incoming)
    assert verdict.verdict == runner_shared.REDERIVE_SHAPE_NOT
    assert key in verdict.reason
    assert "allow-list" in verdict.reason


@pytest.mark.parametrize("suffix", [".backlog.md", ".spec.md", ".release.md"])
def test_an_unmeasured_record_type_returns_UNKNOWN_not_a_plan_verdict(
    suffix: str,
) -> None:
    """F-10: `.aw/records/` is broader than plans, and the other types have their own vocabularies.

    UNKNOWN rather than NOT_THIS_SHAPE, because nothing here has measured what "orthogonal" means for
    a backlog or spec status enum. An unproven type keeps today's refusal, which is correct and cheap.
    """
    path = f".aw/records/backlog/open/20260901-ccc333-01-ccc333-x{suffix}"
    incoming = BASE_PLAN.replace(
        "- Status: approved\n", "- Status: approved\n- Work-Kind: bug\n"
    )
    target = BASE_PLAN.replace("- Status: approved\n", "- Status: done\n")
    verdict = _classify_text(path=path, target=target, incoming=incoming)
    assert verdict.verdict == runner_shared.REDERIVE_SHAPE_UNKNOWN
    assert "UNMEASURED" in verdict.reason


def test_a_missing_merge_stage_returns_UNKNOWN_never_an_assumed_empty_file() -> None:
    verdict = _classify_text(target=None, incoming=BASE_PLAN)
    assert verdict.verdict == runner_shared.REDERIVE_SHAPE_UNKNOWN
    assert "target" in verdict.reason


def test_a_body_prose_rewrite_is_NOT_this_shape() -> None:
    """A body change that is not history INSERTION would be silently dropped by re-derivation."""
    incoming = BASE_PLAN.replace(
        "- Status: approved\n", "- Status: approved\n- Work-Kind: bug\n"
    ).replace("body text that neither side edits", "body text the LANE rewrote")
    target = BASE_PLAN.replace("- Status: approved\n", "- Status: executed\n")
    verdict = _classify_text(target=target, incoming=incoming)
    assert verdict.verdict == runner_shared.REDERIVE_SHAPE_NOT
    assert "insertion only" in verdict.reason


def test_a_target_that_did_not_transition_is_NOT_this_shape() -> None:
    """Without a target transition the conflict is an ordinary stale edit, outside this carve-out."""
    incoming = BASE_PLAN.replace(
        "- Status: approved\n", "- Status: approved\n- Work-Kind: bug\n"
    )
    target = BASE_PLAN.replace("- Kind: child\n", "- Kind: orchestrator\n")
    verdict = _classify_text(path=PENDING, target=target, incoming=incoming)
    assert verdict.verdict == runner_shared.REDERIVE_SHAPE_NOT
    assert "lifecycle race" in verdict.reason


def test_a_value_disagreement_on_an_allow_listed_key_is_NOT_this_shape() -> None:
    """Both sides setting `- Priority:` differently is a real disagreement about the value."""
    incoming = BASE_PLAN.replace(
        "- Status: approved\n", "- Status: approved\n- Priority: medium\n"
    )
    target = BASE_PLAN.replace(
        "- Status: approved\n", "- Status: executed\n- Priority: high\n"
    )
    verdict = _classify_text(target=target, incoming=incoming)
    assert verdict.verdict == runner_shared.REDERIVE_SHAPE_NOT
    assert "DIFFERENT value" in verdict.reason


# --------------------------------------------------------------------------------------------------
# E-02: the refusal message names the stale side and the safe resolution
# --------------------------------------------------------------------------------------------------


def test_the_refusal_names_the_stale_snapshot_and_the_safe_resolution(
    race_repo: tuple[Path, str],
) -> None:
    repo, base = race_repo
    verdicts = _classify_live(repo, base)
    text = runner_shared.format_records_only_conflict_refusal_reason(verdicts)
    assert "STALE LIFECYCLE SNAPSHOT" in text
    assert "REVERT 1 real execution(s)" in text
    assert "SAFE RESOLUTION" in text
    assert "keep the TARGET's `- Status:`" in text
    assert "keep BOTH history lines" in text
    assert "TERMINAL directory" in text


def test_the_shape_specific_refusal_is_empty_when_nothing_matched() -> None:
    """It ADDS detail to a recognized shape and invents none for an unrecognized one."""
    verdict = runner_shared.RecordsOnlyConflictVerdict(
        "mod.py", runner_shared.REDERIVE_SHAPE_NOT, "code"
    )
    assert runner_shared.format_records_only_conflict_refusal_reason([verdict]) == ""


def test_the_E02_refusal_CHANGES_NO_CONTRACT_only_the_message() -> None:
    """E-02 must not alter the refusal's KIND or its TERMINALITY; only the wording improves.

    Stated as a property of the shipped constants rather than of one fixture: a conflict that is not
    re-derived still returns `merge-refused`, and that kind is still terminal on its first attempt, so
    spec `25kzda` 2.1's prohibition is untouched by the better message.
    """
    assert runner_shared.INTEGRATION_REFUSAL_CONFLICT == "merge-refused"
    assert (
        runner_shared.classify_integration_refusal(
            runner_shared.INTEGRATION_REFUSAL_CONFLICT
        )
        is False
    )
    decision = runner_shared.decide_integration_deferral(
        integ_kind=runner_shared.INTEGRATION_REFUSAL_CONFLICT,
        attempts_used=1,
        limit=10,
    )
    assert decision.deferred is False
    assert decision.status == runner_shared.INTEGRATION_REFUSAL_CONFLICT


# --------------------------------------------------------------------------------------------------
# E-03: re-derivation, and its distinct reported outcome
# --------------------------------------------------------------------------------------------------


def test_rederivation_keeps_the_target_status_and_adds_both_keys(
    race_repo: tuple[Path, str],
) -> None:
    repo, base = race_repo
    verdicts = _classify_live(repo, base)
    target_text = runner_shared.read_merge_stage(repo, 2, EXECUTED)
    assert target_text is not None
    out = runner_shared.rederive_front_matter(
        target_text=target_text, verdict=verdicts[0]
    )
    assert "- Status: executed\n" in out
    assert "- Status: approved\n" not in out
    assert "- Work-Kind: bug\n" in out
    assert "- Priority: medium\n" in out
    # BOTH history lines survive: the lane's and the target's own.
    assert "status unchanged (no lifecycle transition)" in out
    assert "2026-09-21 executed (aw oc run): finalized." in out


def test_the_integration_reports_a_DISTINCT_recomputed_outcome(
    race_repo: tuple[Path, str],
) -> None:
    """F-11: neither a plain `integrated` nor the measured-and-refused `merge-refused`."""
    repo, base = race_repo
    handle = worktree_lease.WorktreeHandle(
        lane_id="aaa111", path=repo, branch="lane", base_commit=base
    )
    integrated, reason, kind = runner_shared.integrate_lane_branch(
        repo,
        handle,
        "aaa111",
        lambda _diff, _files: True,
        host_label="aw oc run",
        run_checked=_run_checked_for(repo),
        action_kind="execute",
    )
    assert integrated is True
    assert kind == runner_shared.INTEGRATION_REDERIVED == "merge-rederived"
    assert kind != runner_shared.INTEGRATION_REFUSAL_CONFLICT
    assert kind != "integrated"
    assert "RECOMPUTED rather than merged" in reason

    landed = (repo / EXECUTED).read_text(encoding="utf-8")
    assert "- Status: executed\n" in landed
    assert "- Work-Kind: bug\n" in landed
    assert "- Priority: medium\n" in landed
    # NO plan changed lifecycle directory as a result of this step.
    assert not (repo / PENDING).exists()
    assert _git(repo, "status", "--short").stdout.strip() == ""


def test_the_recomputed_kind_is_not_deferrable_because_it_is_not_a_refusal() -> None:
    """The ladder is asked only about refusals; a success kind must not be classified deferrable."""
    assert (
        runner_shared.classify_integration_refusal(runner_shared.INTEGRATION_REDERIVED)
        is False
    )


# --------------------------------------------------------------------------------------------------
# E-04: all-or-nothing
# --------------------------------------------------------------------------------------------------


def test_a_mixed_conflict_set_refuses_ENTIRELY_and_writes_nothing(
    tmp_path: Path,
) -> None:
    """One records file plus one code file: refuse everything, write nothing, leave main untouched."""
    repo = tmp_path / "repo"
    _init(repo)
    _write(repo, PENDING, BASE_PLAN)
    _write(repo, "mod.py", "x = 1\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "base")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()

    _git(repo, "checkout", "-qb", "lane")
    _write(
        repo,
        PENDING,
        BASE_PLAN.replace(
            "- Status: approved\n",
            "- Status: approved\n- Work-Kind: bug\n- Priority: medium\n",
        ),
    )
    _write(repo, "mod.py", "x = 2  # lane\n")
    _git(repo, "commit", "-qam", "lane: records + code")

    _git(repo, "checkout", "-q", "main")
    (repo / ".aw/records/plans/executed").mkdir(parents=True, exist_ok=True)
    _git(repo, "mv", PENDING, EXECUTED)
    _write(
        repo,
        EXECUTED,
        BASE_PLAN.replace("- Status: approved\n", "- Status: executed\n"),
    )
    _write(repo, "mod.py", "x = 3  # main\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "main: execute + code")

    before_head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    digests = {
        rel: hashlib.sha256((repo / rel).read_bytes()).hexdigest()
        for rel in (EXECUTED, "mod.py")
    }

    handle = worktree_lease.WorktreeHandle(
        lane_id="aaa111", path=repo, branch="lane", base_commit=base
    )
    integrated, reason, kind = runner_shared.integrate_lane_branch(
        repo,
        handle,
        "aaa111",
        lambda _diff, _files: True,
        host_label="aw oc run",
        run_checked=_run_checked_for(repo),
        action_kind="execute",
    )
    assert integrated is False
    assert kind == runner_shared.INTEGRATION_REFUSAL_CONFLICT
    assert "refuses rather than half-applying" in reason
    # NOTHING WRITTEN, on either path.
    assert _git(repo, "rev-parse", "HEAD").stdout.strip() == before_head
    assert _git(repo, "status", "--short").stdout.strip() == ""
    for rel, digest in digests.items():
        assert hashlib.sha256((repo / rel).read_bytes()).hexdigest() == digest


def test_an_empty_conflict_set_is_not_rederivable() -> None:
    """Vacuous truth is not a proof: an unenumerated conflict is an unknown, not a match."""
    rederivable, why = runner_shared.classify_records_only_conflict_set([])
    assert rederivable is False
    assert "nothing is proven" in why


def test_apply_RECHECKS_the_set_gate_rather_than_trusting_its_caller(
    tmp_path: Path,
) -> None:
    """The writer re-asks the all-or-nothing question, so a forgetful caller cannot half-apply."""
    repo = tmp_path / "repo"
    _init(repo)
    mixed = [
        runner_shared.RecordsOnlyConflictVerdict(
            EXECUTED, runner_shared.REDERIVE_SHAPE_MATCH, "ok"
        ),
        runner_shared.RecordsOnlyConflictVerdict(
            "mod.py", runner_shared.REDERIVE_SHAPE_NOT, "code"
        ),
    ]
    applied, why = runner_shared.apply_records_only_rederivation(repo, mixed)
    assert applied is False
    assert "refusing to re-derive" in why


# --------------------------------------------------------------------------------------------------
# THE ANTI-REVERT CONTROL, demonstrated FAILING when re-derivation is widened to `- Status:`
# --------------------------------------------------------------------------------------------------


def test_the_anti_revert_control_holds_on_the_shipped_allow_list(
    race_repo: tuple[Path, str],
) -> None:
    """THE CONTROL: no plan in a terminal directory on the target may acquire a non-terminal status.

    Stated over the MECHANISM rather than over one fixture: the re-derived text for a conflict whose
    target sits in a terminal directory must carry the target's own terminal `- Status:`.
    """
    repo, base = race_repo
    verdicts = _classify_live(repo, base)
    for verdict in verdicts:
        target_text = runner_shared.read_merge_stage(repo, 2, verdict.path)
        assert target_text is not None
        out = runner_shared.rederive_front_matter(
            target_text=target_text, verdict=verdict
        )
        if verdict.target_is_terminal:
            assert f"- Status: {verdict.target_status}\n" in out
            assert f"- Status: {verdict.incoming_status}\n" not in out


def test_the_anti_revert_control_FAILS_when_rederivation_is_widened_to_status() -> None:
    """Widen the allow-list to `- Status:` and the mechanism STILL refuses, in TWO independent places.

    THE DEMONSTRATION THE PLAN DEMANDS, and measuring it found the defence is DOUBLE rather than
    single, which is worth pinning because a future reader might otherwise delete one layer believing
    the other was the only one.

    LAYER ONE, THE CLASSIFIER'S CLASH RULE (condition 7). On the realistic fixture - the target
    carries `- Status: executed` and the incoming side would add `- Status: approved` - widening the
    allow-list is NOT enough to produce a match: the two sides hold the key with different values, so
    the verdict is `not-this-shape` regardless of the allow-list. Asserted first, because it means the
    widening cannot even reach the writer on the shape that actually occurred.

    LAYER TWO, THE WRITER'S OWN ALLOW-LIST (the load-bearing one). Constructed below on the ONLY shape
    that evades layer one, a target with no `- Status:` line at all, so the classifier legitimately
    matches with the widened list. There the WRITER refuses, and that refusal is what actually
    protects a permanent record: the classifier takes an injected allow-list so a test can widen it,
    while the writer accepts only the shipped constant, so no test double and no future caller can
    widen what reaches a record.
    """
    # LAYER ONE, on the real shape.
    realistic = _classify_text(
        base=BASE_PLAN.replace("- Status: approved\n", ""),
        target=BASE_PLAN.replace("- Status: approved\n", "- Status: executed\n"),
        incoming=BASE_PLAN,
        allow_list=frozenset(("Status", "Work-Kind", "Priority")),
    )
    assert realistic.verdict == runner_shared.REDERIVE_SHAPE_NOT
    assert "DIFFERENT value" in realistic.reason

    # LAYER TWO: the one shape that evades layer one, so the writer is the thing under test.
    statusless = BASE_PLAN.replace("- Status: approved\n", "")
    widened = _classify_text(
        path=EXECUTED,
        base=statusless,
        target=statusless,
        incoming=BASE_PLAN,
        target_path=EXECUTED,
        incoming_path=PENDING,
        allow_list=frozenset(("Status", "Work-Kind", "Priority")),
    )
    assert widened.verdict == runner_shared.REDERIVE_SHAPE_MATCH
    assert ("Status", "approved") in widened.added_keys
    with pytest.raises(runner_shared.DriverError) as excinfo:
        runner_shared.rederive_front_matter(target_text=statusless, verdict=widened)
    assert "refusing to write non-allow-listed front-matter key 'Status'" in str(
        excinfo.value
    )


@pytest.mark.parametrize("key", ["Status", "Readiness", "Approval", "Blocks-Release"])
def test_the_writer_refuses_every_gate_or_attestation_key_even_if_classified(
    key: str,
) -> None:
    """The writer's own allow-list check, per dangerous key, independent of the classifier."""
    verdict = runner_shared.RecordsOnlyConflictVerdict(
        EXECUTED,
        runner_shared.REDERIVE_SHAPE_MATCH,
        "forged verdict",
        added_keys=((key, "forged"),),
    )
    with pytest.raises(runner_shared.DriverError) as excinfo:
        runner_shared.rederive_front_matter(target_text=BASE_PLAN, verdict=verdict)
    assert key in str(excinfo.value)


def test_the_writer_refuses_a_path_it_did_not_positively_classify() -> None:
    for state in (
        runner_shared.REDERIVE_SHAPE_NOT,
        runner_shared.REDERIVE_SHAPE_UNKNOWN,
    ):
        verdict = runner_shared.RecordsOnlyConflictVerdict(EXECUTED, state, "why")
        with pytest.raises(runner_shared.DriverError):
            runner_shared.rederive_front_matter(target_text=BASE_PLAN, verdict=verdict)


# --------------------------------------------------------------------------------------------------
# Anti-re-fork: ONE definition reaches both hosts
# --------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "classify_records_only_front_matter_conflict",
        "classify_records_only_conflict_set",
        "format_records_only_conflict_refusal_reason",
        "rederive_front_matter",
        "integrate_lane_branch",
    ],
)
def test_the_seam_is_shared_by_both_runners(name: str) -> None:
    """The integration seam is shared, so this reaches both hosts with no per-host edit.

    `integrate_lane_branch` is included because each host binds a thin WRAPPER around the shared body;
    the wrapper is the host's own object, so identity is asserted on the shared module's attribute
    being the one the wrappers call.
    """
    shared = getattr(runner_shared, name)
    assert shared.__module__ == "agent_workflows.runner_shared"
    if name != "integrate_lane_branch":
        assert getattr(oc_runipd, name, shared) is shared
        assert getattr(agy_runipd, name, shared) is shared
