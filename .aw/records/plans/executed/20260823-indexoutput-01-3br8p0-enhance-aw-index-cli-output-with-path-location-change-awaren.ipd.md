# IPD: Enhance aw index CLI output with path location change awareness and terminal styling

- Date: 2026-08-23
- Kind: child
- Concern: The `aw index` command outputs bare `wrote INDEX.json + INDEX.md (304 plans)` without indicating the directory path location, without distinguishing between files that were updated versus already up to date, and without terminal color styling consistent with other `aw` commands.
- Scope: Update `agent_workflows/term.py` to support index status colors, update `plans_index.py` and `research_index.py` to compare content before writing, print relative path locations, report up to date versus updated state, and style output using `Term`. Add unit tests.
- Status: executed
- Set: indexoutput
- Order: 1
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: 3br8p0

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 approved (Gabriele Fariello): approved for immediate execution per maintainer request.
- 2026-08-23 executed (Gabriele Fariello): implemented change awareness, path location visibility, and Term color styling for aw index.

## Goal

Provide clear, informative, and beautifully styled CLI output for `aw index` across all artifact types, displaying repo-relative file paths, distinguishing between unchanged (`up to date`) and modified (`wrote`/`updated`) manifests, and using consistent `Term` colors.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Terminal styling dictionary

- [x] E-01 Update `STATUS_COLOR_256` in `agent_workflows/term.py` to include `"up to date": 46`, `"wrote": 46`, `"updated": 46`, `"current": 46`, and `"unchanged": 245`. Add unit test in `tests/test_term.py` or `tests/test_artifact_core.py`.
  - Depends on: none
  - Expected outcome: `term.status_256("up to date")` and `term.status_256("wrote")` render with bright green foreground.
  - Execution state: performed

### Task group 2: Plans index output

- [x] E-02 Update `run_index` in `agent_workflows/plans_index.py` to check if `INDEX.json` and `INDEX.md` exist and match the freshly generated content before writing. Format and output a clean status line with `Term` (repo-relative directory path, file names, update status `up to date` vs `wrote`/`updated`, plan count). Add tests in `tests/test_plans_index.py`.
  - Depends on: E-01
  - Expected outcome: `aw index plans` outputs `up to date   .aw/records/plans/INDEX.json, INDEX.md (306 plans)` when unchanged, or `wrote        .aw/records/plans/INDEX.json, INDEX.md (306 plans)` when updated.
  - Execution state: performed

### Task group 3: Research index output

- [x] E-03 Update `run_index` in `agent_workflows/research_index.py` to check if `INDEX.json` and `INDEX.md` exist and match the freshly generated content before writing. Format and output a clean status line with `Term` (repo-relative directory path, file names, update status `up to date` vs `wrote`/`updated`, doc count). Add tests in `tests/test_research_index.py`.
  - Depends on: E-01
  - Expected outcome: `aw index research` outputs `up to date   .aw/records/research/INDEX.json, INDEX.md (85 docs)` when unchanged, or `wrote        .aw/records/research/INDEX.json, INDEX.md (85 docs)` when updated.
  - Execution state: performed

### Task group 4: Integration testing and verification

- [x] E-04 Verify both `aw index all`, `aw index plans`, and `aw index research` CLI invocations, and confirm all test suites pass with `pytest -n auto`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: all test suites pass and CLI output is clear, informative, and styled.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Output styling uses `Term(color=not getattr(args, "no_color", False))`.
- Paths are relative to `repo_root` with blue palette index 33 (`term.color256(rel_dir, 33)`).
- Word-based status labels (`term.status_256`) ensure output survives `NO_COLOR` and non-TTY redirection.

## Findings

The previous output `wrote INDEX.json + INDEX.md (304 plans)` lacked context on directory paths and wrote unconditionally even when no manifest changes occurred, giving no signal on whether anything actually changed.

## Proposed changes (ordered, validatable)

1. Register status colors in `term.py` (E-01).
2. Enhance `plans_index.py` output and change detection (E-02).
3. Enhance `research_index.py` output and change detection (E-03).
4. Verify with integration tests and full pytest suite (E-04).

## Deferred / out of scope (with reason)

- Changing manifest schemas or JSON/MD formats: out of scope.

## Scope check

- Over-scope: none.
- Under-scope: none; covers term palette, both index backends, and tests.

## Required tests / validation

- Unit tests in `tests/test_plans_index.py` and `tests/test_research_index.py`.
- Full test suite via `pytest -n auto`.

## Spec / documentation sync

- N/A (CLI display enhancement).

## Open questions

### OQ-01: How should partial updates (e.g. only INDEX.md changed) be formatted?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: If only one file changed, report `updated    <path>/INDEX.md (INDEX.json up to date; N items)` to be completely transparent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `pytest tests/test_term.py` or unit tests assert `STATUS_COLOR_256` keys.
  - Observed evidence: `STATUS_COLOR_256` keys `up to date`, `wrote`, `updated`, `current`, `unchanged` added and tested.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: `pytest tests/test_plans_index.py` tests assert `up to date` on second run and `wrote` on initial/modified run with directory path.
  - Observed evidence: `pytest tests/test_plans_index.py` ran cleanly and passed 14/14 tests in 0.11s.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: `pytest tests/test_research_index.py` tests assert `up to date` on second run and `wrote` on initial/modified run with directory path.
  - Observed evidence: `pytest tests/test_research_index.py` ran cleanly and passed 14/14 tests in 0.10s.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: `pytest -n auto` runs cleanly and passes.
  - Observed evidence: `pytest -n auto` passed cleanly: `2115 passed, 1 skipped in 113.82s`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: focused CLI output and change detection enhancement for index commands.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved.
2. Scope fence: touch ONLY `agent_workflows/term.py`, `agent_workflows/plans_index.py`, `agent_workflows/research_index.py`, and test files.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, move the plan to `executed/`, and make the path-scoped lifecycle commit.
