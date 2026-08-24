# IPD: Support age duration grammar and set cohesive archiving sweep

- Date: 2026-08-23
- Kind: child
- Concern: The `aw archive` command uses a hardcoded 14-day threshold, evaluates research documents individually (which can fragment multi-document sets), ignores un-sharded flat reference documents, lacks an `--age`/`-a` argument accepting duration formats (`1h`, `5d`, `10w`, `4m`, `1y`), and has minimal help text without usage examples.
- Scope: Add a duration parser (`parse_age_duration`), wire `-a, --age` into `aw archive` in `cli.py`, implement set-cohesive sweep logic in `research_archive.py` and `plans_archive.py` (evaluating sets as a whole based on the most recently created/edited member), improve CLI help text with examples, and add comprehensive unit and CLI tests.
- Status: approved
- Approval: Human requested feature implementation (2026-08-23)
- Set: archiveage
- Order: 1
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: kjdtf5

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 approved (Gabriele Fariello): approved for immediate execution per human request.

## Goal

Provide flexible, duration-based archiving via `aw archive [type] [--age/-a <duration>] [--apply]`, supporting units `1h`, `5d`, `10w`, `4m`, `1y` and preserving set cohesion across research and plans (sweeping a multi-member set only if its newest member meets the age threshold).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Age duration parser

- [ ] E-01 Create `agent_workflows/duration.py` with `parse_age_duration(val: str | int | float | None, default_days: float = 14.0) -> float` supporting units `h` (hours), `d` (days), `w` (weeks), `m` (months, 30 days), `y` (years, 365 days), and raw integers/floats. Raise clean `ValueError` on invalid syntax. Add unit tests in `tests/test_duration.py`.
  - Depends on: none
  - Expected outcome: duration strings like `1h`, `5d`, `10w`, `4m`, `1y` parse deterministically to fractional days; invalid inputs raise descriptive errors.
  - Execution state: pending

### Task group 2: Set-cohesive sweeping in research and plans

- [ ] E-02 Update `agent_workflows/research_archive.py` to accept `--age`/`-a` (via `parse_age_duration`) and implement set-cohesion in `sweep_candidates`: group research documents by `set_id` (fallback to standalone id6), compute the age of the newest member in each set, and sweep all un-archived members of a set if and only if the newest member is older than the threshold. Update sweep candidate reporting to display set context. Add tests in `tests/test_research_archive.py`.
  - Depends on: E-01
  - Expected outcome: `aw archive research --age <val>` sweeps un-archived docs and keeps sets together.
  - Execution state: pending

- [ ] E-03 Update `agent_workflows/plans_archive.py` to accept `--age`/`-a` and enforce set-cohesion for terminal-root plans grouped by `- Set: <set-id>`. Add tests in `tests/test_plans_archive.py`.
  - Depends on: E-01
  - Expected outcome: `aw archive plans --age <val>` sweeps terminal plans older than threshold and preserves set cohesion.
  - Execution state: pending

### Task group 3: CLI integration, rich help text, and examples

- [ ] E-04 In `agent_workflows/cli.py`, register `-a, --age` on `p_archive`, update parser descriptions, and add comprehensive help text and examples illustrating targeted vs sweep archival, `--age` duration formats, and set cohesion. Add CLI integration tests in `tests/test_research_archive.py` and `tests/test_plans_archive.py`.
  - Depends on: E-02, E-03
  - Expected outcome: `aw archive --help` provides rich, clear usage instructions and examples.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `research_archive.py` uses `_all_docs` and `_age_days` based on frontmatter `created` / `parsed.date`.
- `plans_archive.py` uses `_plan_date` and `_at_disposition_root`.
- The CLI uses `argparse` sub-parsers with shared `common` options.

## Findings

The current research sweep only checked hot docs (`intake`/`active`) and evaluated each document in isolation. Supporting `--age` with set cohesion allows whole multi-document research and plan sets to be archived together once the newest member matures past the threshold.

## Proposed changes (ordered, validatable)

1. Implement `agent_workflows/duration.py` with `parse_age_duration` and test suite (E-01).
2. Update `research_archive.py` to support `--age` and set-cohesive grouping (E-02).
3. Update `plans_archive.py` to support `--age` and set-cohesive grouping (E-03).
4. Update `cli.py` arguments, descriptions, and examples (E-04).

## Deferred / out of scope (with reason)

- Automatic cron/daemon background archiving: out of scope (archiving is always explicitly user-invoked).

## Scope check

- Over-scope: none.
- Under-scope: none; covers parser, both artifact backends, CLI options, help text, and tests.

## Required tests / validation

- Unit tests in `tests/test_duration.py`.
- Sweep and set-cohesion tests in `tests/test_research_archive.py` and `tests/test_plans_archive.py`.
- CLI `--help` output verification.
- Full test suite pass with `pytest -n auto`.

## Spec / documentation sync

- CLI help strings updated.

## Open questions

### OQ-01: How are fractional days represented for hour units?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: `1h` is represented as `1.0 / 24.0` days (floating point days), and `_age_days` can return floating point or float comparison is used.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `pytest tests/test_duration.py` passes with full coverage of valid units (`h`, `d`, `w`, `m`, `y`), plain integers, and error handling.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `pytest tests/test_research_archive.py` passes with tests for `--age`, set-cohesive sweeps (younger member prevents set sweep, all aged members sweep together), and unsharded docs.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `pytest tests/test_plans_archive.py` passes with tests for `--age` and set-cohesive sweeps on plans.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `aw archive --help` displays `-a/--age` with duration formats and clear examples.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one cohesive feature spanning parser, archive backends, CLI flags, and help docs.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved.
2. Scope fence: touch ONLY `agent_workflows/duration.py`, `agent_workflows/research_archive.py`, `agent_workflows/plans_archive.py`, `agent_workflows/cli.py`, and test files.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, move the plan, and commit.
