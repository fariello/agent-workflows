# IPD: Point the spec, backlog, and plan generators at the writing standard

- Date: 2026-10-25
- Kind: child
- Concern: Spec `ecmw83` R-06 requires the skeletons that `aw ipd scaffold`, `aw specs new`, and `aw backlog new` write, and the `assess` IPD templates, to name the writing standard, because the skeleton is what an author reads while writing. Maintainer commit `0cbfcc706` shipped the standard at `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install). None of the generators names it: `ipd_authoring.build_skeleton`, `specs._render_new_spec`, and `backlog._render_item` write no such line. `assess/templates/ipd.md` and `assess/templates/orchestrator-ipd.md` are byte-identical copies of `build_skeleton` output (`tests/test_ipd_templates.py::TemplateParityTests`), so they change with the scaffold.
- Scope: Define the pointer line once, emit it after the metadata block of every new plan (child and orchestrator), spec, and backlog item, regenerate the two `assess` templates, and test that each verb writes the line, that the written file still passes its own lint or check, and that the line survives a status transition. EXCLUDES runner prompts (Order 05), workflow bodies (Order 06), existing artifacts (Orders 07 to 09 sweep them), and the checked-in fixtures under `tests/fixtures/` (none is compared byte for byte with the scaffold).
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/ipd_authoring.py, agent_workflows/specs.py, agent_workflows/backlog.py, .aw/system/workflows/assess/templates/ipd.md, .aw/system/workflows/assess/templates/orchestrator-ipd.md, tests/test_generators_writing_standard_pointer.py, CHANGELOG.md
- Item-Dependencies: executed:g4719s
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
- Work-Kind: feature
- Priority: high
- From-Backlog: qph7c5
- From-Spec: ecmw83
- Set: writestd
- Order: 4
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: yz4jdm

## Workflow history
- 2026-11-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: yz4jdm verified (set writestd, attempt 1).
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-06 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 fixed
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; re-scoped to the standard shipped by 0cbfcc706 (g4719s OQ-02 answer); PR-001..PR-009 FIXED; review record .aw/records/reviews/20261025-writestd-04-yz4jdm-point-the-spec-backlog-and-plan-generators-at-the-writing-st.review.md
- 2026-10-26 to-review (aw set): authored review-ready from spec ecmw83 / backlog qph7c5

- 2026-10-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every newly created spec, backlog item, and plan tell its author where the shipped writing standard is, in a line that stays in the artifact through later status changes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Pointer form for every generator: one line, placed after the last metadata bullet and one blank line, and followed by one blank line before `## Workflow history`. The line is `artifact_core.writing_standard_pointer(<noun>)`, where `<noun>` is `plan`, `spec`, or `backlog item`.

### Task group 1: generators

- [x] E-01 (spec `ecmw83` R-06) In `agent_workflows/artifact_core.py`, add a public function `writing_standard_pointer(noun: str) -> str` that returns exactly: `f"> Write and proofread this {noun} per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams)."`. Name both layouts because a generated record is not a workflow body: a path relative to the record would not resolve, and the byte-pinned templates have no target repository to resolve a layout from. In `ipd_authoring.build_skeleton`, emit `writing_standard_pointer("plan")` and a blank line after the `- Id:` line's trailing blank line, before the first H2, for both kinds. Do not add the line to `ipd_authoring._AUTHORING_PLACEHOLDERS`: it is permanent guidance, as the comment at `ipd_authoring._SECTION_BODY` explains. Then regenerate `assess/templates/ipd.md` and `assess/templates/orchestrator-ipd.md` by writing `build_skeleton` output with the exact arguments `tests/test_ipd_templates.py::TemplateParityTests` uses (`CHILD_TITLE`, `ORCH_TITLE`, `AUTHOR`, `WHEN`, `set_name="<set-id>"`, order 1 and 0, `plan_id="tmp1d6"`).
  - Depends on: none
  - Expected outcome: a scaffolded child and orchestrator plan carry the line above `## Workflow history` and lint conforming; both templates equal the generator output.
  - Execution state: performed

- [x] E-02 (spec `ecmw83` R-06) In `specs._render_new_spec`, emit `artifact_core.writing_standard_pointer("spec")` and a blank line after the metadata block (after the optional `- Scope:` line and its following blank line), before `## Workflow history`.
  - Depends on: E-01
  - Expected outcome: a new spec carries the line above `## Workflow history`, and `specs.validate_spec` returns no drift for it.
  - Execution state: performed

- [x] E-03 (spec `ecmw83` R-06) In `backlog._render_item`, in the branch for a new item (`source_text is None`) only, emit `artifact_core.writing_standard_pointer("backlog item")` and a blank line before `## Workflow history`. Do not change the `source_text` branch: it already re-emits the prose between the bullets and `## Workflow history` (rendrop `2yqt0a` E-07), which is what keeps the line through `aw backlog set`.
  - Depends on: E-01
  - Expected outcome: a new backlog item carries the line above `## Workflow history`, and `backlog.validate_item` returns no drift for it.
  - Execution state: performed

### Task group 2: test, changelog, and gate

- [x] E-04 (spec `ecmw83` R-06, `ecmw83` AC-04) Create `tests/test_generators_writing_standard_pointer.py` with `pytestmark = pytest.mark.core`. Create a temporary git repository with `.aw/records/` and drive the real CLI (`python -m agent_workflows`) with `--apply`: `ipd scaffold` for one child and one orchestrator, `specs new --title`, and `backlog new --summary --set --work-kind --priority`. For each written file, assert: the line naming `.aw/system/workflows/technical-writing/technical-writing.md` appears exactly once, before `## Workflow history`; the file passes its own check (`ipd lint --phase author`, `specs check`, `backlog check`, exit 0); and after one status transition (`ipd set to-review`, `specs set --status to-review`, `backlog set --status parked`, each with `--message`), the line is still present exactly once. Add one line under the topmost pending heading of `CHANGELOG.md` (`## 2.0.0 (pending)` at review; re-read at execution), next to the existing "technical writing standard" entry: new plans, specs, and backlog items now name the writing standard. Use no em or en dash (CHANGELOG is user-facing).
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the test passes, and it fails when the pointer is removed from any one generator.
  - Execution state: performed

- [x] E-05 Run the new test with the existing generator and template tests (`tests/test_ipd_templates.py`, `tests/test_ipd_authoring.py`, `tests/test_ipd_schema.py`, `tests/test_authoring_coverage_guidance.py`, `tests/test_scaffold_history_clock.py`, `tests/test_specs_verbs.py`, `tests/test_backlog.py`), then the bare routine gate `python3 -m pytest`, then commit through `aw commit yz4jdm -- <paths>`.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: every listed test and the bare suite pass, and the commit holds only Scope-Paths files.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `ipd_authoring._AUTHORING_PLACEHOLDERS` marks stub text; permanent guidance must not be listed there (comment in `ipd_authoring._SECTION_BODY` under `S.H_PROJECT_CONVENTIONS`).
- `tests/test_ipd_templates.py::TemplateParityTests` requires both `assess` templates to equal `build_skeleton` output byte for byte, so regenerating them is mandatory, not optional. `tests/test_ipd_schema.py` reads the child template for heading-order checks only.
- `ipd_authoring`, `specs`, and `backlog` all import `artifact_core` already, so one function there gives the three generators one wording without a new import edge.
- `backlog._render_item` is also called by `set_records` (question promotion, `source_text=None`). Those items gain the line too, which is harmless and keeps one render path.
- Tests exercise behavior (GUIDING_PRINCIPLES P16): E-04 drives the real verbs and asserts on written files, exit codes, and a transition, not on generator source.

## Findings

- The orchestrator H2 order (`ipd_schema.ORCHESTRATOR_H2_ORDER`) has no "Project conventions discovered (Step 0)" heading, so a bullet in that section cannot reach an orchestrator plan or `orchestrator-ipd.md`. A line after the metadata block reaches both kinds.
- Review-time probes in a temporary repository (recorded in the review record, Step R1): a `>` pointer line between the metadata block and `## Workflow history` lints `conforming` at `author`, `review-finalize`, and `pre-execution` for both kinds; it survives `aw ipd set`, `aw specs set`, and `aw backlog set`; `validate_spec` and `validate_item` report no drift; and `aw check all` on an installed repository reports the same rule set with and without the line.
- `specs._render_new_spec` writes metadata and history only, so the line is the only body text above the history.

## Proposed changes (ordered, validatable)

1. Shared pointer, plan scaffold, and templates (E-01).
2. Spec and backlog generators (E-02, E-03).
3. Test and changelog (E-04); gate and commit (E-05).

## Deferred / out of scope (with reason)

- Existing specs, backlog items, and plans: the sweep Orders 07 to 09 proofread them; adding the line to them here would rewrite live artifacts outside this plan's purpose.
  - Carrier: 8fvkmp

## Scope check

- Over-scope: none.
- Under-scope: none. `agent_workflows/artifact_core.py` is added for the shared wording.

## Required tests / validation

`tests/test_generators_writing_standard_pointer.py` (new), `tests/test_ipd_templates.py`, `tests/test_ipd_authoring.py`, `tests/test_ipd_schema.py`, `tests/test_authoring_coverage_guidance.py`, `tests/test_scaffold_history_clock.py`, `tests/test_specs_verbs.py`, `tests/test_backlog.py`, and the bare suite.

## Spec / documentation sync

No spec edit: spec `ecmw83` R-06 and AC-04 specify this behavior, and the amended R-01 (Order 01 `g4719s` E-01) names the shipped path this line uses. `docs/technical-artifact-writing.md` describes delivery and stays accurate; the CHANGELOG line (E-04) records the change.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff agent_workflows/artifact_core.py agent_workflows/ipd_authoring.py`, `git diff --stat .aw/system/workflows/assess/templates/` showing both templates changed, and, in a temporary repository, the first 20 lines of an `aw ipd scaffold --apply` child and orchestrator plan showing the line above `## Workflow history`, with `aw ipd lint --phase author` on each reporting conforming.
  - Observed evidence:
    `git diff HEAD~1 -- agent_workflows/artifact_core.py agent_workflows/ipd_authoring.py`:
    ```diff
    diff --git a/agent_workflows/artifact_core.py b/agent_workflows/artifact_core.py
    index e1df73534..3e79b23bd 100644
    --- a/agent_workflows/artifact_core.py
    +++ b/agent_workflows/artifact_core.py
    @@ -253,6 +253,21 @@ def utc_history_date() -> str:
         return datetime.datetime.now(datetime.timezone.utc).date().strftime("%Y-%m-%d")


    +# --------------------------------------------------------------------------------------
    +# Technical writing standard pointer (spec ecmw83 R-06; IPD yz4jdm E-01)
    +# --------------------------------------------------------------------------------------
    +
    +
    +def writing_standard_pointer(noun: str) -> str:
    +    """Return the pointer line directing authors to the technical writing standard."""
    +    return (
    +        f"> Write and proofread this {noun} per the technical writing standard, "
    +        "`.aw/system/workflows/technical-writing/technical-writing.md` "
    +        "(`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), "
    +        "including requirement 12 (diagrams)."
    +    )
    +
    +
     # --------------------------------------------------------------------------------------
     # The ONE lifecycle-commit subject grammar (IPD `zexed1` E-02)
     # --------------------------------------------------------------------------------------
    diff --git a/agent_workflows/ipd_authoring.py b/agent_workflows/ipd_authoring.py
    index 53698bb7c..47c51adc7 100644
    --- a/agent_workflows/ipd_authoring.py
    +++ b/agent_workflows/ipd_authoring.py
    @@ -323,6 +323,8 @@ def build_skeleton(
         lines.append(f"- Author: {author}")
         lines.append(f"- Id: {plan_id}")
         lines.append("")
    +    lines.append(_core.writing_standard_pointer("plan"))
    +    lines.append("")
         for h in order_seq:
             lines.append(f"## {h}")
             lines.append("")
    ```
    `git diff --stat HEAD~1 -- .aw/system/workflows/assess/templates/`:
    ```
     .aw/system/workflows/assess/templates/ipd.md              | 2 ++
     .aw/system/workflows/assess/templates/orchestrator-ipd.md | 2 ++
     2 files changed, 4 insertions(+)
    ```
    Temporary repository scaffold and lint run:
    ```
    $ aw ipd scaffold --kind child --title "Example child" --set exset --order 1 --author testauthor --priority high --work-kind feature --apply
    wrote <tmp>/.aw/records/plans/pending/20261107-exset-01-ycxuc4-example-child.ipd.md

    $ head -n 20 20261107-exset-01-ycxuc4-example-child.ipd.md
    # IPD: Example child

    - Date: 2026-11-07
    - Kind: child
    - Concern: TODO.
    - Scope: TODO.
    - Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
    - Item-Dependencies: unresolved
    - Status: draft
    - Work-Kind: feature
    - Priority: high
    - Set: exset
    - Order: 1
    - Highest E allocated: 01
    - Author: testauthor
    - Id: ycxuc4

    > Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

    ## Workflow history

    $ aw ipd lint 20261107-exset-01-ycxuc4-example-child.ipd.md --phase author
    -    ○  draft        plan        20261107-exset-01-ycxuc4  [high]  advisory

    $ aw ipd scaffold --kind orchestrator --title "Example orchestrator" --set exset --order 0 --author testauthor --priority high --work-kind feature --apply
    wrote <tmp>/.aw/records/plans/pending/20261107-exset-00-u1u3sp-example-orchestrator.ipd.md

    $ head -n 20 20261107-exset-00-u1u3sp-example-orchestrator.ipd.md
    # IPD: Example orchestrator

    - Date: 2026-11-07
    - Kind: orchestrator
    - Concern: TODO.
    - Scope: TODO.
    - Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
    - Item-Dependencies: unresolved
    - Status: draft
    - Work-Kind: feature
    - Priority: high
    - Set: exset
    - Order: 0
    - Highest E allocated: 01
    - Author: testauthor
    - Id: u1u3sp

    > Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

    ## Workflow history

    $ aw ipd lint 20261107-exset-00-u1u3sp-example-orchestrator.ipd.md --phase author
    -    ○  draft        plan        20261107-exset-00-u1u3sp  [high]  advisory
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/specs.py` and, in a temporary repository, the full text of an `aw specs new --title t --apply` spec and the `aw specs check` result for it.
  - Observed evidence:
    `git diff HEAD~1 -- agent_workflows/specs.py`:
    ```diff
    diff --git a/agent_workflows/specs.py b/agent_workflows/specs.py
    index 14e13aa28..0fc7e6178 100644
    --- a/agent_workflows/specs.py
    +++ b/agent_workflows/specs.py
    @@ -1026,6 +1026,8 @@ def _render_new_spec(
             lines.append(f"- Scope: {summary}")
         hdate = history_date_iso or date_iso
         lines += [
    +        "",
    +        core.writing_standard_pointer("spec"),
             "",
             "## Workflow history",
             "",
    ```
    Temporary repository spec creation and check:
    ```
    $ aw specs new --title t --apply
    aw specs new: wrote <tmp>/.aw/records/specs/draft/20261107-9gyxmh-01-9gyxmh-t.spec.md

    $ cat 20261107-9gyxmh-01-9gyxmh-t.spec.md
    # Spec: t

    - Date: 2026-11-07
    - Status: draft
    - Id: 9gyxmh
    - Author: aw specs new

    > Write and proofread this spec per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

    ## Workflow history

    - 2026-11-07 created (aw specs): t

    $ aw specs check
    aw specs check: all specs conform. 1 specs checked.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff agent_workflows/backlog.py` and, in a temporary repository, the full text of an `aw backlog new --apply` item and the `aw backlog check` result for it.
  - Observed evidence:
    `git diff HEAD~1 -- agent_workflows/backlog.py`:
    ```diff
    diff --git a/agent_workflows/backlog.py b/agent_workflows/backlog.py
    index 1a21f0637..b1da0d3c0 100644
    --- a/agent_workflows/backlog.py
    +++ b/agent_workflows/backlog.py
    @@ -851,6 +851,8 @@ def _render_item(
             today = core.utc_history_date()
             msg = (message or "").strip() or item.summary
             lines.append("")
    +        lines.append(core.writing_standard_pointer("backlog item"))
    +        lines.append("")
             lines.append("## Workflow history")
             lines.append(f"- {today} created (aw backlog): {msg}")
             lines.append("")
    ```
    Temporary repository backlog item creation and check:
    ```
    $ aw backlog new --summary "example backlog item" --set exset --work-kind feature --priority high --apply
    aw backlog new: wrote <tmp>/.aw/records/backlog/open/20261107-exset-01-vji2bk-example-backlog-item.backlog.md

    $ cat 20261107-exset-01-vji2bk-example-backlog-item.backlog.md
    - Id: vji2bk
    - Status: open
    - Set: exset
    - Priority: high
    - Work-Kind: feature
    - Summary: example backlog item

    > Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

    ## Workflow history
    - 2026-11-07 created (aw backlog): example backlog item

    $ aw backlog check
    aw backlog check: all backlog items conform. 1 backlog items checked.
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_generators_writing_standard_pointer.py` with every test PASSED; then the same run after temporarily removing the pointer from `specs._render_new_spec`, showing FAILED, and the restored PASSED run; and `git diff CHANGELOG.md` showing one added line under the pending heading.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v tests/test_generators_writing_standard_pointer.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3476106200
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/yz4jdm
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_generators_writing_standard_pointer.py::test_specs_new_writing_standard_pointer PASSED [ 25%]
    tests/test_generators_writing_standard_pointer.py::test_ipd_scaffold_child_writing_standard_pointer PASSED [ 50%]
    tests/test_generators_writing_standard_pointer.py::test_backlog_new_writing_standard_pointer PASSED [ 75%]
    tests/test_generators_writing_standard_pointer.py::test_ipd_scaffold_orchestrator_writing_standard_pointer PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 4 passed in 4.81s ===============================
    ```
    After temporarily removing the pointer from `specs._render_new_spec`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=4168511505
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/yz4jdm
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_generators_writing_standard_pointer.py::test_ipd_scaffold_orchestrator_writing_standard_pointer PASSED [ 25%]
    tests/test_generators_writing_standard_pointer.py::test_ipd_scaffold_child_writing_standard_pointer PASSED [ 50%]
    tests/test_generators_writing_standard_pointer.py::test_specs_new_writing_standard_pointer FAILED [ 75%]
    tests/test_generators_writing_standard_pointer.py::test_backlog_new_writing_standard_pointer PASSED [100%]

    =================================== FAILURES ===================================
    ___________________ test_specs_new_writing_standard_pointer ____________________

    repo = PosixPath('/tmp/pytest-of-<user>/pytest-22874/test_specs_new_writing_standar0/repo')

        def test_specs_new_writing_standard_pointer(repo: Path) -> None:
            """Assert specs new emits the writing standard pointer and retains it through to-review."""
            res = run_cli(
                "specs",
                "new",
                "--dir",
                str(repo),
                "--title",
                "Test Spec",
                "--apply",
                cwd=repo,
            )
            assert res.returncode == 0, f"specs new failed: {res.stdout}\n{res.stderr}"

            spec_file = next((repo / ".aw" / "records" / "specs").rglob("*.spec.md"))
    >       _assert_pointer_before_history(spec_file.read_text(encoding="utf-8"), "new spec")

    tests/test_generators_writing_standard_pointer.py:144:
    _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    text = '# Spec: Test Spec\n\n- Date: 2026-11-07\n- Status: draft\n- Id: rmr6z1\n- Author: aw specs new\n\n## Workflow history\n\n- 2026-11-07 created (aw specs): Test Spec\n'
    label = 'new spec'

        def _assert_pointer_before_history(text: str, label: str) -> None:
            """Assert the writing standard pointer appears exactly once and before workflow history."""
    >       assert (
                text.count(POINTER_SNIPPET) == 1
            ), f"Expected exactly one pointer in {label}, found {text.count(POINTER_SNIPPET)}"
    E       AssertionError: Expected exactly one pointer in new spec, found 0
    E       assert 0 == 1
    E        +  where 0 = <built-in method count of str object at 0x7ec43c930fa0>('.aw/system/workflows/technical-writing/technical-writing.md')
    E        +    where <built-in method count of str object at 0x7ec43c930fa0> = '# Spec: Test Spec\n\n- Date: 2026-11-07\n- Status: draft\n- Id: rmr6z1\n- Author: aw specs new\n\n## Workflow history\n\n- 2026-11-07 created (aw specs): Test Spec\n'.count

    tests/test_generators_writing_standard_pointer.py:18: AssertionError
    ============================== SLOW TESTS REPORT ===============================
    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    =========================== short test summary info ============================
    FAILED tests/test_generators_writing_standard_pointer.py::test_specs_new_writing_standard_pointer
    ========================= 1 failed, 3 passed in 5.49s ==========================
    ```
    Restored PASSED run:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- ~/venv/p3.14/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=459081559
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/yz4jdm
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_generators_writing_standard_pointer.py::test_specs_new_writing_standard_pointer PASSED [ 25%]
    tests/test_generators_writing_standard_pointer.py::test_ipd_scaffold_orchestrator_writing_standard_pointer PASSED [ 50%]
    tests/test_generators_writing_standard_pointer.py::test_backlog_new_writing_standard_pointer PASSED [ 75%]
    tests/test_generators_writing_standard_pointer.py::test_ipd_scaffold_child_writing_standard_pointer PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 4 passed in 5.07s ===============================
    ```
    `git diff HEAD~1 -- CHANGELOG.md`:
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 409df24ee..284d9f8e3 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -105,6 +105,7 @@ Major storage-layout boundary. The logical model (D126-D129) was superseded by t
     - Fixed: recorded answers in open questions now preserve the original question text, record only the reasons you gave rather than adopting an option's argument, and no longer repeat unchecked factual premises from project records.
     - Added: a technical writing standard for all technical text (backlog items, specs, plans, research, prompts, reviews, walkthroughs, documentation, commit messages, code comments, and reports). `aw install` now installs it at `.aw/system/workflows/technical-writing/technical-writing.md`, the managed AGENTS.md block tells agents to read and follow it, and the spec, spec-review, plan-review, and research-prompt workflows apply it where the writing happens (see `docs/technical-artifact-writing.md`).
     - Changed: the technical writing standard at `.aw/system/workflows/technical-writing/technical-writing.md` now includes a diagram requirement and a proofreading procedure.
    +- Added: new plans, specs, and backlog items now name the writing standard.
     - Fixed: plain-text requests to use /askme (such as "use /askme" or "ask that again") are now recognized as commands rather than answers, including when submitted as custom answers in an interactive question tool. The workflow rewrites the most recent question asked even if askme was already applied in the session, and supersedes any earlier instruction for terse wording.
     - Added: every commit and merge created by `aw` now keeps the user as author and records `AW Agent (<model>) <local+aw@domain>` as committer (or `local+tag-aw@domain` when already tagged), stamps `AW-Runner` (`aw oc run`, `aw agy run`, or `aw commit`) alongside `AW-Run` and `AW-Item` when known, exports the agent committer identity and `AW_RUNNER` into runner agent turns, and preserves commit signing by supplying `user.signingkey` from the author identity when `commit.gpgsign` is enabled with no explicit key (see `docs/commit-identity.md`).
     - Fixed: aw rename and aw group now also rewrite citations that name a record by its filename without the type suffix, and skip with a warning when another record shares that name.
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the summary line of `python3 -m pytest -o addopts="" tests/test_generators_writing_standard_pointer.py tests/test_ipd_templates.py tests/test_ipd_authoring.py tests/test_ipd_schema.py tests/test_authoring_coverage_guidance.py tests/test_scaffold_history_clock.py tests/test_specs_verbs.py tests/test_backlog.py`, the summary line of bare `python3 -m pytest`, and the `aw commit` output listing the committed paths.
  - Observed evidence:
    Summary line of generator and template tests (`python3 -m pytest -o addopts="" ...`):
    ```
    ============================= 152 passed in 24.28s =============================
    ```
    Summary line of bare `python3 -m pytest`:
    ```
    1865 passed, 11 warnings in 61.53s (0:01:01)
    ```
    (under `aw suite`: `1865 passed, 11 warnings in 38.20s`)
    `aw commit` output:
    ```
    aw commit: committed 8 path(s): e6bebbfaa9a380d59228b0cef5d0e7f70a4a8c58
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), only after spec `ecmw83` is approved (it is `to-review` at review time; the orchestrator `8fvkmp` gate carries the same condition), and only after Order 01 `g4719s` is `executed` (its edge enforces this; it adds requirement 12, which the pointer names). Every open question is resolved. Before editing, read `.aw/system/workflows/technical-writing/technical-writing.md`. Scope fence: the paths in `- Scope-Paths:` are a declaration, not a stop condition; a needed file outside the fence is edited and justified (`aw ipd finalize` requires `--scope-reason PATH=WHY` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). Commit only through `aw commit yz4jdm -- <paths>`, never `git add -A`, never push. You MUST paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. Lifecycle: after every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize yz4jdm` itself.
