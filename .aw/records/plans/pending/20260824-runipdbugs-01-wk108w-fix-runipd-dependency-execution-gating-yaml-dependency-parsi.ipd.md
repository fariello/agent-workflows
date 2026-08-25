# IPD: Fix runipd dependency execution gating, YAML dependency parsing, and directory fsync portability

- Date: 2026-08-24
- Kind: child
- Concern: bugs
- Scope: tools/ipdrunner/runipd.py
- Scope-Paths: tools/ipdrunner/runipd.py, tools/ipdrunner/test_runipd.py
- Status: to-review
- Set: runipdbugs
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: wk108w

## Workflow history

- 2026-08-24 to-review (Antigravity): created from /assess bugs analysis of tools/ipdrunner/runipd.py.

## Goal

Fix correctness defects and edge-case bugs in the OpenCode IPD driver (`tools/ipdrunner/runipd.py`):
1. Fix `dependency_status` to require `EXECUTION_SUCCESS_STATES` (`executed` or `substantially-complete`) for items whose action is `execute`, preventing unexecuted prerequisites from unblocking downstream implementation turns.
2. Fix `_read_deps` to properly clean brackets, quotes, and punctuation so YAML array syntax (e.g. `[a1b2c3, d4e5f6]`) and parenthesized notes parse dependencies correctly without dropping them.
3. Fix `atomic_write_json` directory fsync error handling to prevent spurious crashes on platforms or filesystems that reject directory descriptor sync.
4. Clean surrounding quotes in `_read_set` parsing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Dependency execution gating and status separation

- [ ] E-01 Separate execution dependency satisfaction from overall run success statuses in `dependency_status`.
  - Depends on: none
  - Expected outcome: Execution tasks (`action == 'execute'`) require prerequisites to be in `{'executed', 'substantially-complete'}`, while review tasks (`action == 'review'`) accept reviewed or approved plans.
  - Execution state: pending

### Task group 2: Frontmatter metadata parser hardening

- [ ] E-02 Harden `_read_deps` and `_read_set` against bracketed lists, quoted strings, and inline annotations.
  - Depends on: none
  - Expected outcome: YAML arrays like `[a1b2c3, d4e5f6]` and quoted sets like `"demo"` are correctly parsed into cleaned tokens.
  - Execution state: pending

### Task group 3: Atomic write directory fsync portability

- [ ] E-03 Guard directory file descriptor opening and fsyncing with `contextlib.suppress(OSError)` in `atomic_write_json`.
  - Depends on: none
  - Expected outcome: Atomic file writes succeed even on non-POSIX platforms or network filesystems where directory fsync is unsupported.
  - Execution state: pending

### Task group 4: Regression and unit testing

- [ ] E-04 Add unit tests covering dependency execution gating, YAML dependency parsing, and directory fsync suppression.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: All new and existing tests pass under `pytest tools/ipdrunner/test_runipd.py`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Project: Agent Workflows (`agent-workflows`) toolkit.
- Language: Python 3.10+ with strict typing and no third-party runtime dependencies in `tools/ipdrunner/runipd.py`.
- Style: ruff formatting, pre-commit hygiene hooks, leak sanitizer conformance.
- Plan lifecycle: `.aw/records/plans/pending/` with bijective `E-*` and `V-*` items verified with actual runner output.

## Findings

| ID | Location | Severity | Remediation Risk | Description |
|---|---|---|---|---|
| F-01 | `tools/ipdrunner/runipd.py:1068-1087` | High | Low | `dependency_status` checks `by_id[dep]["status"] in SUCCESS_STATES` (`{"executed", "reviewed", "approved"}`). An execution item will execute prematurely if its dependency was merely reviewed or approved but never executed. |
| F-02 | `tools/ipdrunner/runipd.py:512-521` | Medium | Low | `_read_deps` splits on whitespace/commas and tests `ID6_RE.fullmatch` without stripping brackets or quotes. YAML array notation (`[id6, id6]`) silently discards all dependencies. |
| F-03 | `tools/ipdrunner/runipd.py:451-455` | Low | Low | `atomic_write_json` calls `os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)` and `os.fsync(dir_fd)` unconditionally. If directory fsync is rejected by the OS or filesystem, the write crashes despite file replacement succeeding. |
| F-04 | `tools/ipdrunner/runipd.py:500-505` | Low | Low | `_read_set` does not strip enclosing quotes (`"..."` or `'...'`) from quoted set headers. |

## Proposed changes (ordered, validatable)

1. Introduce `EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}` in `runipd.py`.
2. Update `dependency_status` so that `action == "execute"` items strictly require prerequisites in `EXECUTION_SUCCESS_STATES`.
3. Update `_read_deps` to strip `[]"'(),;` from tokens before validating `ID6_RE.fullmatch`.
4. Update `_read_set` to strip surrounding quotes from set names.
5. Wrap directory fsync in `atomic_write_json` in `with contextlib.suppress(OSError):`.
6. Add unit tests in `tools/ipdrunner/test_runipd.py` for all 4 fixes.

## Deferred / out of scope (with reason)

- Out of scope: Changes to `opencode` binary or external MCP tools (handled by client-side watchdog and timeouts).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Unit tests in `tools/ipdrunner/test_runipd.py` asserting:
  1. An execution item is blocked when its dependency is only in `reviewed` or `approved` state.
  2. YAML bracketed and quoted dependencies parse into valid ID6 lists.
  3. `atomic_write_json` succeeds when directory fsync raises `OSError`.
- `pre-commit run --files tools/ipdrunner/runipd.py tools/ipdrunner/test_runipd.py`
- `python3 -m pytest tools/ipdrunner/test_runipd.py -v`

## Spec / documentation sync

- N/A with reason: Internal driver bug fix; CLI syntax and external contracts remain identical.

## Open questions

### OQ-01: Should review turns also gate on prerequisite reviews?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: For review items, prerequisites in `{"executed", "reviewed", "approved", "substantially-complete"}` are accepted so review chains can proceed after upstream review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Test demonstrating dependency blocking for `execute` action when prerequisite is in `reviewed` or `approved` status.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Test asserting `_read_deps` parses `[5ahblp, pr2nd0]` and quoted tokens correctly.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test asserting `atomic_write_json` writes file atomically even if directory fsync throws `OSError`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Full pytest output demonstrating all tests passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored following the `/assess bugs` workflow. It resides in `.aw/records/plans/pending/` with status `to-review`. It requires review and human approval before execution.
