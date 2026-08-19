# IPD: attention hides ? for history-less trees + aw doctor source-repo awareness and summary

- Date: 2026-08-19
- Kind: child
- Concern: Two board-UX defects. (1) The attention board shows a `?` unknown-age marker on items that legitimately have no last-activity date (research at intake, seeded actions), which reads as noise. (2) `aw doctor` run in the FRAMEWORK SOURCE checkout falsely reports `doctor.version-not-installed` (a source repo has no baked `.aw/VERSION` by design) and its output has no summary line, so the reader is not told whether the findings are actionable.
- Scope: `agent_workflows/attention.py` (`_age_marker`) + `agent_workflows/doctor.py` (`_version_drift` + `run` summary); tests. No change to the scan, the contract classes, or machine/JSON output shape.
- Status: reviewed
- Set: awdoctorfix
- Order: 3
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: qa1k8z

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - suppress the `?` age marker for trees with no history lifecycle, and make `aw doctor` source-repo-aware (no false version-not-installed) with an informative summary line.
- 2026-08-19 reviewed (opencode): self-review - verified _age_marker single call site + tree values, doctor._version_drift source-checkout guard (pyproject contains agent-workflows + no baked VERSION), the summary line does not change --agent/exit codes, and E/V bijection. Awaiting explicit human approval before execution.

## Goal

Stop the attention board and `aw doctor` from misinforming the reader: hide the `?` unknown-age marker on trees that have no history lifecycle, make `aw doctor` recognize a framework SOURCE checkout (so it stops falsely reporting `version-not-installed`), and give `aw doctor` a summary line that states the finding count by category and flags untracked-only findings as informational.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: quiet the ? marker

- [ ] E-01 In `agent_workflows/attention.py`, give `_age_marker` a second parameter `tree: str = ""` and return `""` (not `"?"`) for a `None` last_history_at when the tree has no history lifecycle - specifically the trees `{"actions", "research"}` (research is commonly at `intake` with no history; actions carry status, not a workflow-history block). For trees that DO keep history (plans/specs/backlog/releases), an unknown date still yields `?` (a genuine "no recorded activity" signal). Update the single call site in `render_board` to pass `it.tree`.
  - Depends on: none
  - Expected outcome: a research/intake or action item with `last_history_at=None` renders NO `?`; a backlog item with `last_history_at=None` still renders `?`.
  - Execution state: pending

### Task group 2: aw doctor source-repo awareness + summary

- [ ] E-02 In `agent_workflows/doctor.py` `_version_drift`, detect a FRAMEWORK SOURCE checkout and skip the version probe there (no false `version-not-installed`). A source checkout is: no installed `.aw/VERSION` / `.agents/VERSION` AND a `pyproject.toml` at `repo_root` whose text contains `agent-workflows` (or an `agent_workflows/` package dir at root). In that case return `[]`. Otherwise keep the existing behavior (flag stale/unknown/not-installed on a real installed target).
  - Depends on: none
  - Expected outcome: `aw doctor` in this source repo emits NO `doctor.version-*` drift; an installed target with a missing/stale VERSION still gets `doctor.version-not-installed`/`-stale`.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/doctor.py` `run`, add an informative SUMMARY: after listing findings (human, non-agent branch), print a final line `aw doctor: N finding(s) (git: G, names: M, version: V).` counting by rule prefix, and clarify that untracked files are informational (e.g. append ` - untracked files are informational, not errors` when the only findings are `doctor.git-untracked`). The `--agent` and exit-code behavior are unchanged (still 0 clean / 1 findings). When there are zero findings keep the existing `aw doctor: no findings.` line.
  - Depends on: none
  - Expected outcome: `aw doctor` prints a trailing summary line stating the finding count by category; a repo whose only findings are untracked files says they are informational; exit code unchanged.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add `tests/test_doctor_and_marker.py` (`DoctorAndMarkerTests`): (a) `_age_marker(None, "research")=="" ` and `_age_marker(None, "backlog")=="?"` and `_age_marker(<60d-old>, "backlog")=="!"`; (b) `_version_drift` returns `[]` in a fixture that looks like a source checkout (a `pyproject.toml` containing `agent-workflows`, no VERSION) and still flags an installed-target fixture (a `.aw/VERSION` mismatching packaged); (c) `doctor.run` prints a summary line and, when the only findings are untracked, the informational note. Run the FULL serial suite and paste the tail. Update `tests/test_doctor.py` if its clean-repo fixture now trips the source-repo skip (it should not: that fixture writes a matching `.aw/VERSION`, so it is treated as installed).
  - Depends on: E-01,E-02,E-03
  - Expected outcome: the new module passes; test_doctor still green; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `_age_marker` (attention.py) has ONE call site in `render_board`; adding a `tree` param is safe.
- `doctor._version_drift` compares an installed `.aw/VERSION` to `versioning.resolve_version(source_root)`; a source checkout has no installed VERSION, so `versioning.status(None, ...)` returns `not-installed` - a false positive that a source-repo guard removes.
- The framework source repo is identifiable by `pyproject.toml` (contains `agent-workflows`) + an `agent_workflows/` package dir at root, with no baked `.aw/VERSION`.
- `doctor.run`'s human branch is the only surface that gains the summary; `--agent`/exit codes are the stable machine contract.

## Findings

`?` on history-less trees and a false `version-not-installed` in the source repo are both "the tool is technically right but the reader is misinformed" defects. This IPD scopes them to `_age_marker` + `_version_drift`/`run` and adds a summary so `aw doctor` output is self-explaining.

## Proposed changes (ordered, validatable)

1. `_age_marker(lha, tree)` returns `''` for history-less trees on unknown date.
2. `_version_drift` skips a framework source checkout.
3. `doctor.run` prints a category summary + an informational note for untracked-only findings.
4. Tests.

## Deferred / out of scope (with reason)

- Making `aw doctor` refuse to run in a source repo entirely: no - the git/names probes are still useful there; only the version probe is source-inappropriate.
- Sorting the board by priority (awdoctorfix-01 OQ-01): still deferred.

## Scope check

- Over-scope: none (attention.py `_age_marker` + doctor.py + tests).
- Under-scope: none for the stated concern.

## Required tests / validation

`tests/test_doctor_and_marker.py` + `tests/test_doctor.py` still green; full serial suite green.

## Spec / documentation sync

N/A: no spec governs these cosmetics; the summary line is self-documenting.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No open questions; both fixes are well-defined.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `_age_marker(None, "research")` and `_age_marker(None, "actions")` return `""`; `_age_marker(None, "backlog")` returns `"?"`; a colored board of a research-intake item shows no `?`. Shown by the new test.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `_version_drift` returns `[]` for a source-checkout fixture (pyproject with agent-workflows, no VERSION) and a non-empty drift for an installed-target fixture with a mismatched `.aw/VERSION`; live `aw doctor` in this repo shows no `doctor.version-*` line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `aw doctor` output ends with a `aw doctor: N finding(s) ...` summary; an untracked-only repo shows the informational note; exit code still 0/1. Paste the live output.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest tests/test_doctor_and_marker.py tests/test_doctor.py -p no:xdist -q` green; full serial suite `python3 -m pytest -p no:xdist` tail pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files changed by this plan, path-scoped, never push. Run the full serial suite and paste the actual runner output as V evidence. On completion, lint `--phase pre-transition` while still approved, then flip Status to executed, add an executed workflow-history line, `git mv` to `.aw/records/plans/executed/`, and lint `--phase post-transition`. Do not mark executed until every V item is verified with concrete evidence.
