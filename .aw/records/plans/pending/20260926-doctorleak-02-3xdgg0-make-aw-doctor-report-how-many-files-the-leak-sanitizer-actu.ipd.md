# IPD: Make aw doctor report how many files the leak sanitizer actually scanned

- Date: 2026-09-26
- Kind: child
- Concern: `doctor.SanitizerProbeResult.scanned_files` is declared (default 0), serialized by `to_dict()`, and published in the `sanitizer` agent evidence (`"scanned_files": report.sanitizer.scanned_files`), but nothing ever assigns it, so `aw doctor --agent` always reports `scanned_files: 0` even when it found leaks. `leak_sanitizer.scan_working_tree` returns only findings, so `doctor.probe_sanitizer` has no count to set.
- Scope: IN: a counted variant `leak_sanitizer.scan_working_tree_counted`; `scan_working_tree` delegates to it; `doctor.probe_sanitizer` sets `scanned_files`; one outcome test. OUT: the other scanners (`scan_staged`, `scan_history`); other callers of `scan_working_tree`; rpqv4q's drift/except changes.
- Scope-Paths: agent_workflows/leak_sanitizer.py, agent_workflows/doctor.py, tests/test_doctor.py
- Item-Dependencies: executed:rpqv4q
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: c0ppo0
- Blocks-Release: next
- Set: doctorleak
- Order: 2
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3xdgg0

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog c0ppo0: add leak_sanitizer.scan_working_tree_counted and set doctor's scanned_files from it, with a 2-file/1-leak outcome test.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw doctor`'s sanitizer evidence states the true number of tracked files the scan read, so a reader can tell a clean scan of N files from a scan that read nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: count, wire, test

- [ ] E-01 In `agent_workflows/leak_sanitizer.py`, add `scan_working_tree_counted(repo_root: Path, *, include_warn: bool = False) -> tuple[list[Finding], int]` containing the current body of `scan_working_tree`, incrementing a counter each time a file's text is obtained and passed to `scan_text` (the on-disk read OR the `git show HEAD:<rel>` fallback). A path in `_ALLOWED_PATHS` is skipped and NOT counted; a path whose read and fallback both fail (`continue`) is NOT counted. Replace `scan_working_tree`'s body with `return scan_working_tree_counted(repo_root, include_warn=include_warn)[0]`, keeping its signature and return type, so its callers (`leak_sanitizer`'s own sanitizer entry point that calls `scan_working_tree(repo_root, include_warn=include_warn)`, `security_hardening.scan_artifact_for_leaks`, and the `local_leaks` re-export) are unchanged. State the counting rule in the new function's docstring: "files actually read and scanned; excludes `_ALLOWED_PATHS` and unreadable paths".
  - Depends on: none
  - Expected outcome: identical findings from both functions; the counted one also returns the read count.
  - Execution state: pending

- [ ] E-02 In `doctor.probe_sanitizer`, call `leak_sanitizer.scan_working_tree_counted(repo_root)` and set `res.scanned_files` from its count and `res.findings` from its findings. rpqv4q restructures this function first (only the scan call inside the `try`); keep that structure: unpack the tuple inside the `try`, build drift outside it. If rpqv4q has not landed, stop (see gate).
  - Depends on: E-01
  - Expected outcome: `aw doctor --agent` sanitizer evidence shows a nonzero `scanned_files` on any repo with tracked files.
  - Execution state: pending

- [ ] E-03 Add a test to `tests/test_doctor.py`: a fresh `tempfile.TemporaryDirectory` git repo (use the file's `_git` helper; do NOT reuse `DoctorTests.setUp`, whose installed fixture tracks many files) with exactly two committed files, one containing a home-directory path built at runtime from pieces (`"/home/" + "someuser" + "/x"`, never one literal, since `tests/test_doctor.py` is not in `_ALLOWED_PATHS` and a literal would itself be a leak finding; see rpqv4q E-02) and one clean. Assert `probe_sanitizer(repo).scanned_files == 2` and `len(probe_sanitizer(repo).findings) == 1`. Outcomes only. Then run the bare suite.
  - Depends on: E-02
  - Expected outcome: the test passes; against the pre-change doctor it fails with `0 != 2`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- rpqv4q (doctorleak-01, approved) changes the same function (`f.matched` -> `f.snippet`, narrow `try`); this plan depends on it to avoid a conflicting edit.
- `leak_sanitizer._ALLOWED_PATHS` exempts five self-referencing files from scanning; `tests/test_doctor.py` is not among them.
- `aw sanitize --agent` must stay clean after the test is added.
- Tests assert OUTCOMES only (maintainer rule): no source-text or docstring pins.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | LOW | `doctor.SanitizerProbeResult.scanned_files` | Never assigned anywhere. | `grep -n scanned_files agent_workflows/*.py tests/*.py` -> only the dataclass default, `to_dict`, and the evidence emitter |
| F-2 | INFO | `leak_sanitizer.scan_working_tree` | Returns `list[Finding]` only; callers: `leak_sanitizer`'s sanitizer entry (`findings = scan_working_tree(repo_root, include_warn=include_warn)`), `security_hardening.scan_artifact_for_leaks`, `doctor.probe_sanitizer`, and the `local_leaks` re-export. | grep |

## Proposed changes (ordered, validatable)

1. E-01: counted scanner; old one delegates.
2. E-02: doctor sets the count.
3. E-03: outcome test; bare suite.

## Deferred / out of scope (with reason)

- Counts for `scan_staged` and `scan_history`: doctor does not use them and no surface reports a count for them.
  - Carrier-Declined: no consumer.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_doctor.py -v -k scanned`; `aw sanitize --agent`; bare suite. Test rule: outcomes only.

## Spec / documentation sync

N/A: no spec documents the doctor evidence fields; the field already exists and now carries a real value.

## Open questions

### OQ-01: Count files read, or files listed by `git ls-files`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Files actually read and scanned. The field's purpose is to show what the scan covered; counting allowed or unreadable paths would overstate coverage.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the diff; paste `python3 -c 'from pathlib import Path; from agent_workflows import leak_sanitizer as L; a=L.scan_working_tree(Path(".")); b,n=L.scan_working_tree_counted(Path(".")); print(len(a)==len(b), n, n==len([p for p in L._tracked_files(Path(".")) if p not in L._ALLOWED_PATHS]))'` on this repo showing `True <n> True` (or, if unreadable paths exist, the difference explained).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the doctor diff; paste the `sanitizer` evidence object from `python3 -m agent_workflows doctor --agent` on this repo showing `scanned_files` nonzero.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the test run passing; revert the E-02 hunk IN THE WORKTREE and paste the test FAILING with `0 != 2`; restore. Paste `aw sanitize --agent` showing no finding in `tests/test_doctor.py`, and the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. One new public function in `leak_sanitizer` (the old one keeps its exact contract), one assignment in doctor, one test. `aw doctor`'s evidence field changes from a constant 0 to the real count.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if rpqv4q has not executed (its `f.matched` defect still present in `doctor.probe_sanitizer`), stop; the runner's `Item-Dependencies` ordering should prevent this.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `c0ppo0` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`.
