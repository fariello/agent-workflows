# IPD: Transition cold archival shards from weekly to monthly YYYYMM format

- Date: 2026-08-23
- Kind: child
- Concern: Archival shards currently use weekly ISO buckets (YYYYMM-Www), which creates artificial directory fragmentation (4-5 folders per month, many with only 1-2 files) and forces humans to think in ISO calendar weeks. Monthly buckets (YYYYMM, e.g. 202606, 202607, 202608) align with natural human mental models, match the YYYYMMDD date prefix format in filenames, and keep cold storage tidy.
- Scope: Update core shard calculation and validation in `agent_workflows/artifact_core.py`, update consumers in `plans_archive.py`, `research_archive.py`, `engine.py`, and `cli.py`, migrate existing on-disk weekly shards to monthly `YYYYMM/` shards, fix frontmatter creation placeholder dates on two research files, update test suites, and regenerate manifests.
- Status: executed
- Set: shardmonth
- Order: 1
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: nhbgcc

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 approved (Gabriele Fariello): approved for immediate execution per maintainer directive.
- 2026-08-23 executed (Gabriele Fariello): transitioned cold archival shards across research and plans from weekly (YYYYMM-Www) to monthly (YYYYMM).

## Goal

Transition all cold archival shards across research and plans from weekly buckets (`YYYYMM-Www`) to monthly buckets (`YYYYMM`), aligning with human mental models and the repository's `YYYYMMDD` grammar without breaking indexing, querying, or citations.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Shard math and core validation

- [x] E-01 Update `agent_workflows/artifact_core.py` to define `SHARD_DIR_RE = re.compile(r"\A(?P<yyyymm>\d{6})\Z")`, update `shard_dirname(yyyymm: str, week: int = 0) -> str` to return `yyyymm[:6]`, update `is_valid_shard_dirname` to accept monthly `YYYYMM` (and legacy weekly for backward-compatibility tolerance), and update `shard_for_date(yyyymmdd: str) -> str` to return `yyyymmdd.replace("-", "")[:6]`. Update re-exports in `agent_workflows/research_contract.py`.
  - Depends on: none
  - Expected outcome: `shard_for_date("20260701")` returns `"202607"`, and `is_valid_shard_dirname("202607")` returns True.
  - Execution state: performed

### Task group 2: On-disk migration and data cleanup

- [x] E-02 Migrate existing on-disk weekly shards to monthly shards via `git mv`: move `.aw/records/research/archive/202607-W28/*` to `.aw/records/research/archive/202607/`, and `.aw/records/research/reference/202608-W32/*` and `.aw/records/research/reference/202608-W33/*` to `.aw/records/research/reference/202608/`. Remove empty weekly directories. Correct frontmatter `created: 20260101` placeholders in `20260726-skills-00-vdz4ui-codex-cli-gpt-5.findings.md` (`created: 20260726`) and `20260807-codexfit-00-qcxc6c-codex-cli-gpt-5.findings.md` (`created: 20260807`).
  - Depends on: E-01
  - Expected outcome: all existing sharded research sits in `202607/` and `202608/` monthly folders with accurate frontmatter.
  - Execution state: performed

### Task group 3: Consumer updates and docstrings

- [x] E-03 Update consumers in `agent_workflows/plans_archive.py`, `agent_workflows/research_archive.py`, `agent_workflows/plans_index.py`, `agent_workflows/engine.py`, and `agent_workflows/cli.py` to reference monthly `YYYYMM` shards in docstrings, error messages, and scaffolding.
  - Depends on: E-01
  - Expected outcome: all tools, docstrings, and CLI strings reflect monthly `YYYYMM` shards.
  - Execution state: performed

### Task group 4: Test suites and index regeneration

- [x] E-04 Update unit tests in `tests/test_artifact_core.py`, `tests/test_research_contract.py`, `tests/test_research_archive.py`, `tests/test_plans_archive.py`, and related suites to assert monthly shard paths (e.g. `202607`). Regenerate `INDEX.json` and `INDEX.md` via `aw index research` and `aw index plans`. Verify full suite passes with `pytest -n auto`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: all tests pass, indices reflect the new monthly layout, and `aw check` conforms.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `shard_for_date` is exported from `artifact_core.py` and re-exported by `research_contract.py`.
- `plans_archive.py` and `research_archive.py` use `_core.shard_for_date` and `R.shard_for_date`.
- Manifest generation (`plans_index.py`, `research_index.py`) uses recursive scans and is invariant to subdirectory depth/naming.
- Shards exist under `reference/` and `archive/` in research, and under `executed/`, `superseded/`, `not-executed/` in plans.

## Findings

The weekly shard scheme (`YYYYMM-Www`) was an over-optimization for high-frequency repositories, creating unnecessary cognitive load and directory clutter. Switching to monthly `YYYYMM` creates clean, predictable buckets matching the project's `YYYYMMDD` grammar.

## Proposed changes (ordered, validatable)

1. Update `artifact_core.py` and `research_contract.py` shard functions (E-01).
2. Migrate existing on-disk shards and fix metadata placeholders (E-02).
3. Update module docstrings, help strings, and scaffolding in `plans_archive.py`, `research_archive.py`, `engine.py`, `cli.py` (E-03).
4. Update unit tests, regenerate indexes, and run `pytest -n auto` (E-04).

## Deferred / out of scope (with reason)

- Changing artifact filename grammar (`YYYYMMDD-...`): out of scope (filenames remain unchanged).

## Scope check

- Over-scope: none.
- Under-scope: none; covers core math, disk migration, consumer modules, and test suites.

## Required tests / validation

- Unit tests in `tests/test_artifact_core.py`, `tests/test_research_contract.py`, `tests/test_research_archive.py`, `tests/test_plans_archive.py`.
- Full test suite via `pytest -n auto`.
- `aw check research index` and `aw check plans index` clean.

## Spec / documentation sync

- Update READMEs and docstrings referencing `YYYYMM-Www` to `YYYYMM`.

## Open questions

### OQ-01: Should legacy `YYYYMM-Www` directory names still be tolerated by `is_valid_shard_dirname`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: YES, `is_valid_shard_dirname` accepts both `\d{6}` and legacy `\d{6}-W\d{2}` during transition so any external consumer repos migrating asynchronously do not fail closed abruptly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `pytest tests/test_artifact_core.py tests/test_research_contract.py` passes with updated monthly shard assertions.
  - Observed evidence: `pytest tests/test_artifact_core.py tests/test_research_contract.py` ran cleanly (21 passed in 0.17s) confirming `shard_for_date("20260701") == "202607"`, `is_valid_shard_dirname("202607") is True`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: `git status` shows tracked moves from `YYYYMM-Www` to `YYYYMM/`, and `20260726-skills-00-vdz4ui` and `20260807-codexfit-00-qcxc6c` carry correct `created:` dates.
  - Observed evidence: `git status` confirms tracked moves to `archive/202607/` and `reference/202608/`; `created:` dates updated to `20260726` and `20260807`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: `pytest tests/test_plans_archive.py tests/test_research_archive.py` passes with monthly shard paths.
  - Observed evidence: `pytest tests/test_plans_archive.py tests/test_research_archive.py` ran cleanly (19 passed in 0.38s).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: `aw index research --check` and `aw check plans index` pass cleanly, and `pytest -n auto` is green.
  - Observed evidence: `aw check research index` and `aw check plans index` both report `✓ CONFORMS` (0 errors, 0 warnings); `pytest -n auto` passed: `2113 passed, 1 skipped in 151.32s`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: cohesive migration across shard date math, disk layout, consumers, and tests.

### Execution contract

1. Open questions RESOLVED: OQ-01 resolved.
2. Scope fence: touch ONLY `agent_workflows/artifact_core.py`, `agent_workflows/research_contract.py`, `agent_workflows/plans_archive.py`, `agent_workflows/research_archive.py`, `agent_workflows/engine.py`, `agent_workflows/cli.py`, sharded research files, indexes, and tests.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, move the plan to `executed/`, and make the path-scoped lifecycle commit.
