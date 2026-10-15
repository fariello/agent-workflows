# IPD: Verify and close the --source-anchors --agent crash fix and add bare-command and non-info severity tests

- Date: 2026-10-14
- Kind: child
- Concern: Backlog `g3ropl` (`Blocks-Release: next`, filed 2026-10-12 at `92a6f240d` while graduating `1vd74h`) reports that `aw check --source-anchors --agent` (and `aw check specs --source-anchors --agent`) crashed with `ValueError: Invalid aw.agent/v1 record: Exit code mismatch: exit=0 incompatible with negative outcome 'findings'` whenever `spec_citations.stale_spec_anchors` returned any finding, because `cli._run_check` hardcoded `exit_code = 0` beside `status = "findings"`. Sibling plan `fz3i3m` (`sbh1o1` Order 03, commit `44696b524`) already landed the `cli._run_check` fix as its `E-02` and added `aw check specs --source-anchors --agent` tests `test_e`/`test_f` in `tests/test_spec_citation_anchors.py`, but left `g3ropl` open because `fz3i3m` carried `- From-Backlog: 1vd74h` (`Work-Kind: chore`, no `Blocks-Release`). Moreover, `tests/test_spec_citation_anchors.py` still does not test (a) the bare `aw check --source-anchors --agent` command (without the positional `specs` noun, the primary command named in `g3ropl`'s Summary and workflow history) or its `--verbose` `evidence` records (`source_anchors` and `rules` statuses and severity counts, repaired in `fz3i3m` review PR-002), or (b) the `exit_code == 1` / `status = "findings"` arm of `cli._run_check` when `check.spec-anchor-stale` has a non-`info` severity.
- Scope: (1) Verify with pasted runner output on the current tree that commit `44696b524` (`fz3i3m` `E-02`) repaired `cli._run_check`'s `--source-anchors` branch, that both `aw check --source-anchors --agent` and `aw check specs --source-anchors --agent` succeed on the real tree, and that all existing tests in `tests/test_spec_citation_anchors.py` pass (`E-01`). (2) Add two behavioral tests (`test_g` and `test_h`) to `tests/test_spec_citation_anchors.py` over self-written fixtures (`temp_spec_repo`) covering bare `aw check --source-anchors --agent --verbose` with attributed and unattributed findings (`outcome: "conforms"`, `exit: 0`, and `evidence` statuses/counts) and the non-`info` severity arm (`outcome: "findings"`, `exit: 1`, and `evidence` statuses/counts), then run the module and the bare test suite (`E-02`), so `g3ropl` closes through its `From-Backlog: g3ropl` / `Blocks-Release: next` carrier. EXCLUDES any edit to `agent_workflows/cli.py` or `agent_workflows/spec_citations.py` unless `E-01` uncovers a regression, EXCLUDES changing the registered severity of `check.spec-anchor-stale` in `agent_workflows/check_engine.py`, and EXCLUDES any live-tree census assertion in tests.
- Scope-Paths: tests/test_spec_citation_anchors.py
- Item-Dependencies: executed:fz3i3m
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: g3ropl
- Blocks-Release: next
- Set: sbh1o1
- Order: 5
- Highest E allocated: 02
- Author: antigravity/Gemini-4-Argon-High
- Id: f0kolj

## Workflow history
- 2026-10-15 reviewed (aw set): plan-review applied revisions
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003
- 2026-10-14 to-review (aw set): Authored review-ready from backlog g3ropl at HEAD 89413ed93; verifies the fz3i3m crash fix in cli._run_check and adds bare-command verbose and non-info severity tests in tests/test_spec_citation_anchors.py

- 2026-10-14 draft (antigravity/Gemini-4-Argon-High): created.

## Goal

Graduate release-blocking backlog `g3ropl` by verifying with pasted runner output that `fz3i3m` (commit `44696b524`) fixed the `--source-anchors --agent` crash in `agent_workflows.cli._run_check`, and by adding behavioral tests in `tests/test_spec_citation_anchors.py` for the bare `aw check --source-anchors --agent --verbose` command (with findings) and for the non-`info` severity (`outcome: "findings"`, `exit: 1`) branch of `cli._run_check`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Verify the landed crash fix and record the baseline

- [ ] E-01 Confirm on the current tree that commit `44696b524` (`fz3i3m` `E-02`) is present in `agent_workflows/cli.py` (`_run_check`'s `if getattr(args, "source_anchors", False):` branch derives `rule_sev = ce.rule_spec("check.spec-anchor-stale").severity` and `exit_code = core.drift_exit_code(diagnostics)`, setting `status` and both `Evidence.status` fields to `"clean"` on zero findings, `"conforms"` when `exit_code == 0`, and `"findings"` otherwise). Run and paste: (1) `python3 -m agent_workflows check --source-anchors --agent` and `python3 -m agent_workflows check specs --source-anchors --agent` on the real tree (with exit codes and stderr; use the `python3 -m agent_workflows` spelling because the installed `aw` console script prints a one-line `aw: invoked in checkout ... re-running with ...` re-exec notice on stderr inside a lane worktree, which is not a defect; if `aw` is used instead, stderr must contain nothing beyond that notice); (2) `python3 -m pytest -o addopts="" -v tests/test_spec_citation_anchors.py` (every collected test passing, re-derived at execution; the existing `--source-anchors --agent` tests `test_e_*`/`test_f_*` are non-binding pointers); and (3) the pre-edit bare-suite baseline `python3 -m pytest` summary line and failing-test-id set for `E-02` to compare against.
  - Depends on: none
  - Expected outcome: both real-tree CLI commands exit 0 with a `result` record for which `agent_schema.validate_agent_record` returns `[]`, an `outcome` of `clean` or `conforms` (the live finding count is NOT a bar), and empty stderr (no `Traceback`/`ValueError`); every collected test in `tests/test_spec_citation_anchors.py` passes; bare-suite baseline summary line and failing-test-id set are recorded.
  - Execution state: pending

### Task group 2: Add behavioral coverage for bare command, verbose evidence, and non-info severity

- [ ] E-02 Add two behavioral tests to `tests/test_spec_citation_anchors.py` over self-written fixtures in `temp_spec_repo` (never asserting on the live tree census or inspecting source text): (g) `test_g_cli_bare_check_source_anchors_agent_verbose_findings_conforms_exit_zero`, driving bare `aw check --source-anchors --agent --verbose --dir <temp_spec_repo>` (no positional `specs` noun, matching `g3ropl`'s Summary command) via `subprocess.run` on a fixture file containing one stale attributed anchor and one unattributed anchor in separate comment blocks (separated by a blank line so the second block does not inherit the first block's `id6`), asserting `proc.returncode == 0`, no `Traceback` or `ValueError` in `proc.stderr`, every non-empty stdout line parses as JSON, and the `result` record has `outcome == "conforms"`, `exit == 0`, `target == "source-anchors"`, `findings == 2`, `findings_by_severity == {"error": 0, "warning": 0, "info": 2}`, both `evidence` entries (`source_anchors` and `rules`) carrying `status == "conforms"` with `rules["value"] == {"errors": 0, "warnings": 0, "info": 2}`, and two `check.spec-anchor-stale` diagnostics (one attributed, one unattributed) with `severity == "info"`, and `agent_schema.validate_agent_record(rec) == []`; and (h) `test_h_cli_check_source_anchors_agent_non_info_severity_reports_findings_exit_one`, using `monkeypatch.setitem(check_engine.RULE_REGISTRY, "check.spec-anchor-stale", check_engine.RULE_REGISTRY["check.spec-anchor-stale"]._replace(severity="error"))` and calling `cli.main(["check", "--source-anchors", "--agent", "--verbose", "--dir", str(temp_spec_repo)])` (capturing output via `capsys`) on a fixture with one stale anchor, asserting return value `1`, empty stderr, and an `aw.agent/v1` `result` record for which `agent_schema.validate_agent_record(rec) == []` (the exact predicate that raised the original `Exit code mismatch` `ValueError`) with `outcome == "findings"`, `exit == 1`, `target == "source-anchors"`, `findings == 1`, `findings_by_severity == {"error": 1, "warning": 0, "info": 0}`, and both `evidence` entries carrying `status == "findings"` with `rules["value"] == {"errors": 1, "warnings": 0, "info": 0}`. Then run `python3 -m pytest -o addopts="" -v tests/test_spec_citation_anchors.py` and the bare suite `python3 -m pytest`, comparing the summary line and failing-test-id set against the `E-01` baseline.
  - Depends on: E-01
  - Expected outcome: `tests/test_spec_citation_anchors.py` passes all collected tests (including `test_g` and `test_h`), and the bare suite `python3 -m pytest` shows no new failing test IDs relative to the `E-01` baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The test suite is run bare as `python3 -m pytest` (`AGENTS.md` repo-local development contract), where `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Narrowed runs that need per-test `-v` output clear the configured defaults explicitly with `-o addopts=""`.
- Tests must exercise observable behavior and outcomes (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", `GUIDING_PRINCIPLES.md` P16). `tests/test_spec_citation_anchors.py` states this posture in its module docstring: "behavioral assertions only, no code-structure pinning, no live-tree census counts".
- `agent_workflows.check_engine.RuleSpec` is a `NamedTuple`, so overriding a rule's registered severity in a test uses ` RULE_REGISTRY["check.spec-anchor-stale"]._replace(severity="error")` under `monkeypatch.setitem`.
- `agent_workflows.cli.main(argv)` accepts an explicit `argv` list and returns the integer exit code without `execve` re-exec or `sys.exit`, making in-process `monkeypatch` + `capsys` testing of `cli._run_check` clean and side-effect-free.
- Commits go through `aw commit <plan> -- <paths>` (`AGENTS.md` execution contract), and public output/records must pass `aw sanitize --agent` with no local machine paths.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at starting HEAD `89413ed93` in this lane.

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The production crash in `agent_workflows.cli._run_check` was already fixed by plan `fz3i3m` (`sbh1o1` Order 03) in commit `44696b524`. | `git show 44696b524 -- agent_workflows/cli.py` replaces `exit_code = 0` and `status = "clean" if len(findings) == 0 else "findings"` in `_run_check`'s `if getattr(args, "source_anchors", False):` branch with `rule_sev = ce.rule_spec("check.spec-anchor-stale").severity`, `exit_code = core.drift_exit_code(diagnostics)`, and `status = "clean"` (0 findings), `"conforms"` (`exit_code == 0`), or `"findings"` (`exit_code != 0`) on both `CommandResult` and its `source_anchors` and `rules` `Evidence` items. At HEAD `89413ed93`, both `aw check --source-anchors --agent` and `aw check specs --source-anchors --agent` exit 0 and emit a valid `aw.agent/v1` record. |
| F-02 | Why `g3ropl` remained `open`: `fz3i3m` carried `- From-Backlog: 1vd74h` (`Work-Kind: chore`, no `Blocks-Release`), so `runner_shared.process_backlog_close` did not touch `g3ropl`, and no manual `aw backlog set done g3ropl --evidence ...` commit was made after `fz3i3m` finalized. | `.aw/records/plans/executed/20261012-sbh1o1-03-fz3i3m-make-the-spec-anchor-detector-honest-enough-to-gate-fix-the.ipd.md` (`## Approval and execution gate` and review `PR-003`/`D-2`) notes that `g3ropl` was not `fz3i3m`'s `From-Backlog`. Because no artifact in the tree carries `- From-Backlog: g3ropl`, `runner_shared.backlog_item_already_complete(repo, "g3ropl")` returns `BACKLOG_NO_IPD_CARRIER`. |
| F-03 | `tests/test_spec_citation_anchors.py` does not yet test (a) the bare `aw check --source-anchors --agent` invocation (without the positional `specs` noun), (b) the `--verbose` `evidence` records (`source_anchors` and `rules` statuses and severity counts repaired by `fz3i3m` review `PR-002`), or (c) the `exit_code == 1` / `status = "findings"` arm of `cli._run_check` when `check.spec-anchor-stale` has non-`info` severity. | In `tests/test_spec_citation_anchors.py`, `test_e_cli_check_specs_source_anchors_agent_stale_anchor_conforms_exit_zero` and `test_f_cli_check_specs_source_anchors_agent_clean_reports_clean_exit_zero` both pass `["check", "specs", "--source-anchors", "--agent", "--dir", ...]` without `--verbose` (so `result.to_agent_record` emits compact `evidence: ["source_anchors", "rules"]` instead of the `Evidence.to_dict` dicts carrying `status` and `value`), and neither exercises `rule_sev != "info"`. |
| F-04 | Both new test cases (`test_g` and `test_h`) were verified in a scratch `tempfile.TemporaryDirectory()` against `agent_workflows.cli` at HEAD `89413ed93`. | Driving `cli.main(["check", "--source-anchors", "--agent", "--verbose", "--dir", str(repo)])` on a two-block fixture (one stale attributed anchor, one unattributed anchor separated by a blank line) returns `0` with `outcome == "conforms"`, `exit == 0`, `findings == 2`, `findings_by_severity == {"error": 0, "warning": 0, "info": 2}`, and both `evidence` dicts carrying `status == "conforms"`. Overriding `check_engine.RULE_REGISTRY["check.spec-anchor-stale"]` via `._replace(severity="error")` returns `1` with `outcome == "findings"`, `exit == 1`, `findings_by_severity == {"error": 2, "warning": 0, "info": 0}` on that two-block fixture (re-measured at review on the one-anchor `test_h` fixture: `{"error": 1, "warning": 0, "info": 0}`, `rules.value == {"errors": 1, "warnings": 0, "info": 0}`, empty stderr, `validate_agent_record` returns `[]`), and both `evidence` dicts carrying `status == "findings"`. |

## Proposed changes (ordered, validatable)

1. `E-01`: Verify the `fz3i3m` (`44696b524`) fix on the current tree (`aw check --source-anchors --agent`, `aw check specs --source-anchors --agent`, and `python3 -m pytest -o addopts="" -v tests/test_spec_citation_anchors.py`) and record the bare-suite baseline (`python3 -m pytest`).
2. `E-02`: Add `test_g_cli_bare_check_source_anchors_agent_verbose_findings_conforms_exit_zero` and `test_h_cli_check_source_anchors_agent_non_info_severity_reports_findings_exit_one` to `tests/test_spec_citation_anchors.py`, re-run the module with `-o addopts="" -v`, and run the bare suite `python3 -m pytest` to confirm no regressions.

## Deferred / out of scope (with reason)

- Editing `agent_workflows/cli.py` or `agent_workflows/spec_citations.py`: commit `44696b524` (`fz3i3m`) already landed the `cli._run_check` crash fix, table-row acceptance, and unattributed-anchor detection (F-01).
  - Carrier-Declined: already implemented in commit `44696b524` (executed plan `fz3i3m`); no production defect remains in `cli._run_check`.
- Changing the registered severity of `check.spec-anchor-stale` in `agent_workflows/check_engine.py` from `info` to `error`: maintainer ruling on 2026-10-12 chose to gate new stale spec pointers at the runner merge check (executed plan `mnwkqu`, Set `cihealth`) rather than promoting `check.spec-anchor-stale` in `aw check`.
  - Carrier-Declined: maintainer ruling 2026-10-12 (`l85xvi` superseded by `mnwkqu`); `test_h` exercises the non-`info` branch in-process via `monkeypatch` without changing the production registry.

## Scope check

- Over-scope: none. Only `tests/test_spec_citation_anchors.py` is declared in `Scope-Paths`, and `E-02` modifies it directly.
- Under-scope: none. Every surface named in backlog `g3ropl` (`aw check --source-anchors --agent`, `aw check specs --source-anchors --agent`, `cli._run_check` exit-code/outcome pairing with `agent_schema.assert_valid_agent_record`, and release-gate handoff for `Blocks-Release: next`) is verified in `E-01` and tested in `E-02`.

## Required tests / validation

- Real-tree CLI verification (`V-01`): `aw check --source-anchors --agent` and `aw check specs --source-anchors --agent` both exit 0 with valid `aw.agent/v1` JSONL output and empty stderr.
- Narrowed module run (`V-01`, `V-02`): `python3 -m pytest -o addopts="" -v tests/test_spec_citation_anchors.py` passes every collected test (count re-derived at execution); in `V-02` the two new tests (`test_g_*`, `test_h_*`, names non-binding) pin the bare-command `conforms`/exit 0 verbose evidence and the non-`info` `findings`/exit 1 arm.
- Bare test suite (`V-01`, `V-02`): `python3 -m pytest` summary line and failing-test-id set compared before and after `E-02` showing zero new failures.

## Spec / documentation sync

N/A: no specification or user-facing documentation changes. The `aw.agent/v1` envelope contract (`agent_schema.assert_valid_agent_record`) and `--source-anchors` CLI flag semantics are unchanged; this plan verifies the landed `fz3i3m` fix and adds behavioral test coverage in `tests/test_spec_citation_anchors.py`.

## Open questions

### OQ-01: Given that commit `44696b524` (plan `fz3i3m`) already fixed the crash in `agent_workflows/cli.py`, should this plan be a zero-edit verification plan or also close the remaining test gaps in `tests/test_spec_citation_anchors.py`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from repository evidence (F-01 through F-04): verify the landed `cli._run_check` fix AND add `test_g` and `test_h` in `tests/test_spec_citation_anchors.py`. Adding those two tests covers the exact bare `aw check --source-anchors --agent` command named in `g3ropl`'s Summary, the `--verbose` `Evidence.status` and `rules` counts fixed in `fz3i3m` PR-002, and the `exit_code == 1` / `status = "findings"` branch when `rule_sev != "info"`, while ensuring `tests/test_spec_citation_anchors.py` is genuinely modified during execution and `g3ropl` (`Blocks-Release: next`) closes cleanly via its `From-Backlog: g3ropl` carrier.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste (1) the stdout, stderr, and exit code of `python3 -m agent_workflows check --source-anchors --agent` and `python3 -m agent_workflows check specs --source-anchors --agent` on the real tree (produced by `agent_workflows.cli._run_check`), plus the `agent_schema.validate_agent_record` return value (`[]`) for each `result` record; (2) the per-test `-v` output and summary line of `python3 -m pytest -o addopts="" -v tests/test_spec_citation_anchors.py` showing every collected test `PASSED` (count re-derived at execution, not a bar); and (3) the pre-edit bare-suite `python3 -m pytest` summary line and failing-test-id set.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste (1) `git diff -- tests/test_spec_citation_anchors.py` showing the added `test_g_cli_bare_check_source_anchors_agent_verbose_findings_conforms_exit_zero` and `test_h_cli_check_source_anchors_agent_non_info_severity_reports_findings_exit_one` tests; (2) the per-test `-v` output and summary line of `python3 -m pytest -o addopts="" -v tests/test_spec_citation_anchors.py` showing every collected test `PASSED`, including the two new tests (names are non-binding pointers) that pin, respectively, bare `check --source-anchors --agent --verbose` returning `outcome: "conforms"` / `exit: 0` with `conforms` evidence statuses and `info` counts, and the non-`info` severity arm returning `outcome: "findings"` / `exit: 1` with `findings` evidence statuses and `errors: 1`, each `result` record passing `agent_schema.validate_agent_record` with `[]`; and (3) the post-edit bare-suite `python3 -m pytest` summary line and failing-test-id set compared against `V-01`, showing zero new failures.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved f0kolj --by-human`). Open questions: OQ-01 is resolved; none remain. Start execution with `aw ipd begin f0kolj`. `- Scope-Paths:` (`tests/test_spec_citation_anchors.py`) is a DECLARATION reconciled at finalize: if an out-of-scope edit (such as `agent_workflows/cli.py`) proves necessary, make it and justify it with `--scope-reason <path>=<why>`. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; never claim a pass you did not run, and run the full suite bare (`python3 -m pytest`). Commit only `tests/test_spec_citation_anchors.py` (plus this plan) through `aw commit f0kolj -- tests/test_spec_citation_anchors.py .aw/records/plans/pending/20261014-sbh1o1-05-f0kolj-verify-and-close-the-source-anchors-agent-crash-fix-and-add.ipd.md` (never `git add -A`, `-a`, or `--no-verify`), verify `git diff --cached --name-only` before committing, run `aw sanitize --agent` to confirm no local paths leaked into tracked artifacts, and never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns `finalize` after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` inside the runner; when executed by hand, run `aw ipd finalize f0kolj` once `aw ipd lint --phase pre-transition` conforms and `V-01`..`V-02` hold pasted evidence with `Result: pass`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`. Release gate: keep the inherited `- Blocks-Release: next`; once this plan is `executed`, backlog `g3ropl` closes `done` via the runner's `process_backlog_close` under the HANDOFF rule (or `aw backlog set done g3ropl --evidence <executed-plan-path>` when executed by hand).
