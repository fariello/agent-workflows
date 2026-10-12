# IPD: aw runs empty-state --agent emits an aw.agent/v1 summary record

- Date: 2026-10-12
- Kind: child
- Concern: `aw runs --agent` and its declared leaf twin `aw runs list --agent` print the bare payload `{"runs": []}` (optionally with `excluded_runs`) when no run survives resolution and filtering. That line carries no `schema`, `kind`, `outcome` or `exit`, so it is not an `aw.agent/v1` record: a JSONL caller reading the terminal record finds none, and the Section 4 exit-parity rule of `docs/cli-output-contract.md` has nothing to apply to (backlog `l5dq92`, `Blocks-Release: next`). The exit code (0) is CORRECT per Section 11.1 (a standing question with a clean empty answer); only the envelope is wrong.
- Scope: Change ONLY the `--agent` arm of the empty-state branch of `run_viewer.run_viewer_cli` (the block guarded by `if not summaries and not issues_only:`) so it emits one validated `kind: "summary"` record with `outcome: "clean"`, `exit: 0` and zero counts, carrying any `excluded_runs` and the active filters. Both spellings (`aw runs`, `aw runs list`) reach that one branch, so one edit decides both. Keep `runs list` declared `agent_record_kind="summary"` (no `command_surface` change). Leave the `--json` empty payload and the exit code unchanged. Update the one existing test that pins the bare agent line, add behavioral tests for both spellings, add a sentence to `docs/cli-output-contract.md` Section 3.1, and a CHANGELOG line. The non-empty `--agent` stream and the bare flag-conflict refusals are OUT of scope and filed as backlog `4d3ynu`.
- Scope-Paths: agent_workflows/run_viewer.py, tests/test_run_viewer.py, tests/test_runs_empty_agent_record.py, docs/cli-output-contract.md, CHANGELOG.md, .aw/records/plans/pending/20261012-l5dq92-01-t76qdk-aw-runs-empty-state-agent-emits-an-aw-agent-v1-summary-recor.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: l5dq92
- Blocks-Release: next
- Set: l5dq92
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: t76qdk
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed.
- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): authored from backlog l5dq92; empty-state branch, dispatch, declaration, schema validator and the pinning test measured at authoring HEAD 4dc9b2f82. Out-of-scope sibling defects filed as backlog 4d3ynu.

## Goal

An empty `aw runs --agent` / `aw runs list --agent` answer is a conforming `aw.agent/v1` `summary` record (`outcome: clean`, `exit: 0`, `total/emitted/omitted: 0`) that `agent_schema.validate_agent_record` accepts and whose embedded `exit` equals the process exit code, so automation reading the terminal record gets a real verdict instead of a bare dict.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: emit the record

- [ ] E-01 In `agent_workflows/run_viewer.py` `run_viewer_cli`, split the empty-state machine arm (currently `if is_agent or is_json:` building `payload: dict[str, Any] = {"runs": []}` then `print(json.dumps(payload, indent=2 if is_json else None))`) into two arms. (a) `if is_json:` keeps the existing bare payload byte-for-byte (`{"runs": []}` pretty-printed, plus `excluded_runs` when `excluded_data` is non-empty), because `--json` outranks `--agent` (contract Section 1) and the non-empty `--json` path is the same bare `{"runs": [...]}` dict, so changing only the empty case would break `data["runs"]` consumers (OQ-02). (b) `elif is_agent:` builds and prints, via `_agent_schema.render_jsonl_record` (which runs `assert_valid_agent_record`), exactly one record: `schema: _agent_schema.SCHEMA_VERSION`, `kind: "summary"`, `cmd: "runs"` (the value the sibling `_unresolvable_target_refusal` record in the same module already uses, OQ-03), `outcome: "clean"`, `exit: 0`, `total: 0`, `emitted: 0`, `omitted: 0`, `complete: True`, `verified: True`, `findings: 0`, `filters`: a dict of only the filters actually supplied (keys among `set`, `ipd`, `status`, `failed`, `active`, `last`, `since`, `targets`; booleans `failed`/`active` only when True; `last` as the NORMALIZED `last_n` int, so `--latest` reads `1`; string values passed through `_agent_schema.redact_home_paths`, and `targets` as `[_agent_schema.redact_home_paths(t) for t in raw_targets]`, element by element, because `redact_home_paths` returns a non-string such as a list UNCHANGED, as the sibling `_unresolvable_target_refusal` already does), `excluded_runs: excluded_data` only when non-empty, and `next`: `"aw runs"` when `filters` is non-empty (the broadening query, contract Section 11.1) else `None`. Print with `end=""` (the renderer already appends the newline) and `return 0`. Update the comment above the branch to cite `l5dq92`. Do not touch any other branch.
  - Depends on: none
  - Expected outcome: `aw runs --agent` and `aw runs list --agent` in an empty repository print one line that `validate_agent_record` accepts with `exit: 0`; `--json` output is unchanged; exit code stays 0.
  - Execution state: pending

### Task group 2: tests

- [ ] E-02 In `tests/test_run_viewer.py` `test_total_exclusion_distinguishable_from_empty_repo_across_all_surfaces`, replace ONLY the two agent-surface assertions that pin the bare shape (`self.assertEqual(out_ag_empty.strip(), '{"runs": []}')` and `self.assertEqual(data_ag_total["runs"], [])`) with assertions on the new record: the empty-repo record has `kind == "summary"`, `outcome == "clean"`, `exit == 0`, `total == 0` and no `excluded_runs` key; the total-exclusion record has `kind == "summary"`, `total == 0` and the existing three-run `excluded_runs` assertions unchanged (so the test still proves the two cases are distinguishable). Leave the human and `--json` sections of that test untouched.
  - Depends on: E-01
  - Expected outcome: the edited test passes post-fix and fails against pre-fix `run_viewer.py`.
  - Execution state: pending

- [ ] E-03 Create `tests/test_runs_empty_agent_record.py` driving the REAL `cli.main` (pattern: `tests/test_run_viewer.py::_run_viewer`, `cli.main(["runs", "--dir", str(root), *argv])`, and the leaf spelling `cli.main(["runs", "list", "--dir", str(root), *argv])`) in a `tempfile.TemporaryDirectory()` holding no runs. Cases, parametrized over both spellings: (a) `--agent` prints exactly one non-blank line; `json.loads` of it passes `agent_schema.validate_agent_record` with an empty error list; `kind == "summary"`, `outcome == "clean"`, `total == emitted == omitted == 0`, `complete is True`, `next is None`, `filters == {}`; and the record's `exit` equals the returned rc, which is 0. (b) `--agent --status nosuchstatus`: same validity and parity, `filters == {"status": "nosuchstatus"}`, `next == "aw runs"`. (c) `--json` output parses to exactly `{"runs": []}` (the unchanged contract, OQ-02). (d) both spellings produce byte-identical `--agent` output. No source reading, `inspect` or `ast` (GUIDING_PRINCIPLES P16).
  - Depends on: E-01
  - Expected outcome: new file passes post-fix; cases (a), (b) and (d) fail against pre-fix `run_viewer.py`.
  - Execution state: pending

### Task group 3: docs and user-facing note

- [ ] E-04 In `docs/cli-output-contract.md` Section 3.1, after the paragraph beginning "Commands in the run-execution family", add one paragraph stating: the `aw runs` viewer's read paths (bare `aw runs` and its identical leaf `aw runs list`) return exit `0` or `2`, and its opt-in mutating `aw runs repair` may also return `1`, so the viewer stays inside the three-state vocabulary and is not part of either wider table below; its unresolvable-target refusal already emits a conforming `kind: "error"` record, and its empty result emits a conforming `kind: "summary"` record with `outcome: "clean"` and `exit: 0` under `--agent` (Section 11.1), while `--json` keeps the bare `{"runs": [...]}` payload. Its non-empty `--agent` stream is not yet enveloped (tracked as backlog `4d3ynu`). User-facing prose: no em or en dashes.
  - Depends on: E-01
  - Expected outcome: Section 3.1 states the viewer's exit range (including `repair`'s `1`) and empty-state record honestly, scoped so it does not claim the whole family is reconciled.
  - Execution state: pending

- [ ] E-05 Add one `- Fixed:` line to the pending 2.0.0 section of `CHANGELOG.md`: when `aw runs --agent` or `aw runs list --agent` finds no matching runs it now prints a standard `aw.agent/v1` summary record (clean, exit 0, zero counts, plus any excluded runs and active filters) instead of a bare `{"runs": []}` object; `--json` output and exit codes are unchanged. No em or en dashes.
  - Depends on: E-01
  - Expected outcome: CHANGELOG carries the line; a dash check on it finds nothing.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Machine records are validated at emit time: `agent_schema.render_jsonl_record` calls `assert_valid_agent_record`, and the sibling refusal in the same module (`run_viewer._unresolvable_target_refusal`) builds its record by hand then calls `_agent_schema.assert_valid_agent_record` before printing. Reusing the validator is what makes exit parity enforced rather than hoped for.
- `kind: "summary"` requires `total`, `emitted`, `omitted`, `complete` with `emitted + omitted == total` (`agent_schema.validate_agent_record`, `elif kind == "summary":` arm). A probe record with the E-01 field set returned `[]` from `validate_agent_record` at authoring.
- Precedence is `--json` > `--agent` > human (`docs/cli-output-contract.md` Section 1); later branches of `run_viewer_cli` already test `if is_json:` before `if is_agent:`.
- Both spellings share one renderer: `cli.main` routes `runs_cmd == "list"` and the bare root to `run_viewer.run_viewer_cli` (`if runs_cmd and runs_cmd != "list":` / `return run_viewer.run_viewer_cli(args)`).
- Tests drive the real `cli.main` (`tests/test_run_viewer.py::_run_viewer`); no source-reading tests (GUIDING_PRINCIPLES P16). Suite runs bare: `python3 -m pytest` (AGENTS.md repo-local development contract).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The empty-state machine arm prints a bare dict for both `--agent` and `--json`. | `run_viewer.run_viewer_cli`: `if not summaries and not issues_only:` / `if is_agent or is_json:` / `payload: dict[str, Any] = {"runs": []}` / `print(json.dumps(payload, indent=2 if is_json else None))` / `return 0`. Measured: `python3 -m agent_workflows runs list --agent` printed `{"runs": []}`; `runs --agent --status zzz` printed `{"runs": []}`; `runs list --json` printed the same object pretty-printed. |
| F-02 | Both spellings reach the same branch, so one edit decides both (the backlog item's point (1)). | `cli.main`: `if runs_cmd and runs_cmd != "list":` routes other leaves to `run_cli`; everything else `return run_viewer.run_viewer_cli(args)`. `command_surface` comment: "The bare viewer's contract is carried by `runs list`, its identical alias, which IS a leaf." |
| F-03 | `runs list` is declared `agent_record_kind="summary"`; a `summary` record matches that declaration, so no declaration change is needed (point (2)). | `command_surface.COMMAND_INVENTORY` entry `command="runs list"`, `agent_record_kind="summary"`, `empty_error_renderer="shared_empty_result"`, `exit_contract=(0, 1, 2)`. Contract Section 11.1 permits "a structured `result` (or `summary`) record". |
| F-04 | The viewer's exits are already inside the three-state vocabulary, so the Section 3.1 wider-vocabulary reconciliation the item names (point (3)) reduces to stating that fact for this verb. | `run_viewer.EXIT_UNRESOLVABLE_TARGET: int = 2`; every `return` in `run_viewer_cli` is `0`, `2`, or a `repair_run` code, and `repair_run` returns `0`, `1` (`return 1, (`) or `2`, so `aw runs repair` can exit 1; the declaration says `exit_contract=(0, 1, 2)`. Section 3.1 currently says the family "emit bare JSON dictionaries ... rather than `aw.agent/v1` records". |
| F-05 | Exactly one existing test pins the bare agent line. | `tests/test_run_viewer.py::FilterExclusionReportingTests::test_total_exclusion_distinguishable_from_empty_repo_across_all_surfaces`: `self.assertEqual(out_ag_empty.strip(), '{"runs": []}')` and `self.assertEqual(data_ag_total["runs"], [])`. Grep of `tests/` for `'{"runs": []}'` / `"runs": []` finds no other agent-surface pin (`tests/test_aw_upgrade_test.py` hits are the unrelated upgrade-rehearsal payload). |
| F-06 | No conformance sweep covers either spelling, so the new test file is the only gate. | `tests/test_agent_surface_conformance.py::compute_conformance_universe` keeps only `agent_record_kind == "result"`; `tests/conformance_matrix.py` has no `runs list` exemption. |
| F-07 | Sibling defects on the same surface exist but need a separate public-contract decision. | Non-empty `--agent` path prints `json.dumps(asdict(s), ...)` per run and a bare `{"kind": "excluded_runs", ...}` line; flag-conflict refusals print `json.dumps({"error": err_msg, "exit_code": 2})`. Filed as backlog `4d3ynu` (`Blocks-Release: next`). |

## Proposed changes (ordered, validatable)

1. E-01: split the empty-state arm; `--agent` emits a validated `summary` record, `--json` unchanged.
2. E-02 / E-03: update the one pinning test; add two-spelling behavioral tests asserting validity and exit parity.
3. E-04 / E-05: Section 3.1 sentence; CHANGELOG line.

Alternatives considered and rejected: (i) emit `kind: "result"` and re-declare `runs list` as `result`: would pull the leaf into the `result` conformance UNIVERSE, whose sweep would then drive the NON-empty path too and fail on the bare per-run lines (F-07), so it couples this fix to `4d3ynu`; `summary` matches the existing declaration and Section 11.1 allows it. (ii) Also envelope the `--json` empty payload: makes `--json` shape depend on whether runs exist, breaking `data["runs"]` readers (`tests/test_runs_subdir_root.py` reads `c_json_data["runs"][0]`), with no record-protocol requirement on `--json` here.

## Deferred / out of scope (with reason)

- Non-empty `--agent` stream (`--latest-only`, `--summary-only`, `--issues`, per-run lines, the bare `excluded_runs` line) and the bare `{"error": ..., "exit_code": 2}` flag-conflict / `--since` refusals: filed as backlog `4d3ynu`; choosing an item-record shape for `RunSummary` is a separate public-contract change for every `aw runs` consumer.
- Adding `runs list` to the agent conformance UNIVERSE: blocked on `4d3ynu` for the reason in alternative (i).
- `--issues` empty output under `--agent` (prints nothing at exit 0): reached by a different branch (`issues_only` excludes this one); belongs with `4d3ynu`'s stream decision.

## Scope check

- Over-scope: none. Every `Scope-Paths` entry is the fix site, its pinning test, the new test, the contract doc the item names, the CHANGELOG, or this plan.
- Under-scope: none known. `command_surface.py` needs no edit (F-03); no spec governs this envelope (the contract doc is the authority and is in scope).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_runs_empty_agent_record.py -v`: all cases pass post-fix; cases (a), (b), (d) shown failing against pre-fix `run_viewer.py` (before committing the fix: `cp agent_workflows/run_viewer.py /tmp/opencode/run_viewer.fixed.py`, then `git show HEAD:agent_workflows/run_viewer.py > agent_workflows/run_viewer.py`, run, then `cp /tmp/opencode/run_viewer.fixed.py agent_workflows/run_viewer.py` and confirm `git diff --stat -- agent_workflows/run_viewer.py` matches V-01; never stash).
- `python3 -m pytest -o addopts="" tests/test_run_viewer.py tests/test_runs_subdir_root.py tests/test_runs_flag_position_parity.py tests/test_runs_repo_alias.py tests/test_cli_agent_protocol_doc.py tests/test_empty_result_convention_doc.py -q`: pass.
- Live: `python3 -m agent_workflows runs list --agent --dir <empty tempdir>` output piped through `python3 -c 'import json,sys; from agent_workflows import agent_schema as s; print(s.validate_agent_record(json.loads(sys.stdin.read())))'` prints `[]`.
- Full suite bare: `python3 -m pytest`, summary line pasted; any FAILED node id is re-run at the pre-change base commit to show it is pre-existing and unrelated.

## Spec / documentation sync

- `docs/cli-output-contract.md` Section 3.1: one paragraph (E-04). WHY: the item names Section 3.1's family scope-out as something this work must decide; the decision (F-04) is that the viewer already lives in the three-state vocabulary, and the doc should say so rather than lump it with the bare-dict verbs.
- `CHANGELOG.md`: one Fixed line (E-05).
- No `.spec.md` is touched: no spec governs the `aw runs` agent envelope.

## Open questions

### OQ-01: `summary` or `result` record kind for the empty state?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `summary`. Repository evidence: `runs list` is already declared `agent_record_kind="summary"` (F-03), contract Section 11.1 explicitly allows "`result` (or `summary`)", and choosing `result` would force a declaration change that drags the unfixed non-empty path into the conformance sweep (alternative (i)). The validator accepts the E-01 field set (`validate_agent_record` returned `[]` at authoring).

### OQ-02: Does `--json` change too?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `--json` is the explicit-format surface (Section 1), its non-empty shape is the bare `{"runs": [...]}` dict that existing tests and callers index (`tests/test_runs_subdir_root.py`), and the backlog item's defect is the missing `aw.agent/v1` envelope, which is an `--agent` protocol. Changing only the empty `--json` case would make the shape depend on the result count. Any `--json` envelope belongs with `4d3ynu`.

### OQ-03: What `cmd` value does the record carry?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: `"runs"`, matching the record `run_viewer._unresolvable_target_refusal` already emits from the same viewer for both spellings, so one viewer reports one `cmd` and both spellings stay byte-identical (E-03 (d)).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- agent_workflows/run_viewer.py` showing only the split empty-state arm and its comment; paste the live output of `python3 -m agent_workflows runs list --agent --dir <empty tempdir>` and `python3 -m agent_workflows runs --agent --dir <empty tempdir>` (code path `run_viewer.run_viewer_cli` empty-state branch, created by E-01), each followed by `echo $?` showing 0, and the `validate_agent_record` pipe printing `[]`; paste `python3 -m agent_workflows runs list --json --dir <empty tempdir>` still printing `{"runs": []}` pretty-printed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- tests/test_run_viewer.py` showing only the two agent-surface assertions replaced; paste the passing line of `python3 -m pytest -o addopts="" "tests/test_run_viewer.py::FilterExclusionReportingTests::test_total_exclusion_distinguishable_from_empty_repo_across_all_surfaces" -v`, and the same test FAILING against pre-fix `run_viewer.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_runs_empty_agent_record.py -v` showing every case passing post-fix, and the run against pre-fix `run_viewer.py` showing cases (a), (b), (d) failing while (c) passes; paste `rg -n "inspect|import ast|read_text" tests/test_runs_empty_agent_record.py` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff -- docs/cli-output-contract.md` showing the one added paragraph; paste `rg -n "[\u2013\u2014]" docs/cli-output-contract.md` output restricted to the added lines (none); paste the passing summary of `python3 -m pytest -o addopts="" tests/test_cli_agent_protocol_doc.py tests/test_empty_result_convention_doc.py -q`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff -- CHANGELOG.md` showing the one `- Fixed:` line under the 2.0.0 (pending) section, a dash check on that line finding no em or en dash, and the full suite bare `python3 -m pytest` summary line with its FAILED node-id list; for every failing node id, paste its run at the pre-change base commit (for example in a scratch `git worktree add` of that commit) showing it fails there too, and state that none is in a file this plan touches. A failure that passes at the base is caused by this change and makes the result `failed`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Reviewers should push hardest on OQ-02 (keeping `--json` bare) and on F-04 (that stating the viewer's exit range is a sufficient answer to the Section 3.1 reconciliation the backlog item names).

Execution contract: OQ-01 through OQ-03 are resolved; no open question remains. Scope fence: `- Scope-Paths:` declares every path this plan may change; an edit outside it must be justified at finalize via `--scope-reason`. Commit only the paths in `Scope-Paths` through `aw commit t76qdk -- <paths>`, never `git add -A`, never push. Verify the staged set with `git diff --cached --name-only` before committing. Every test claim MUST be backed by the ACTUAL pasted runner output; never claim a run you did not perform. Run the suite bare as `python3 -m pytest` and paste its actual summary line. Lifecycle: in a managed lane the runner owns `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd begin t76qdk`, fill every `V-*` with pasted output, confirm `aw ipd lint --phase pre-transition` conforms, then `aw ipd finalize t76qdk`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`. Backlog `l5dq92` is not set `done` by authoring; it closes via the From-Backlog handoff once this plan is executed, carrying `Blocks-Release: next`.
