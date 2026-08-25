# IPD: aw install ensures records runs directory is gitignored

- Date: 2026-08-24
- Kind: child
- Concern: The ipdrunner IPD driver writes per-run durable state under `.aw/records/runs/<run-id>/` (queue state.json, session JSONL logs, prompts, outcomes, driver.lock). This is box-local, ephemeral working material that must never be committed. It was manually added to `.aw/.gitignore` in this repo, but a fresh `aw install` does not guarantee it, so any new repo shows ipdrunner run dirs as untracked noise. Backlog item 8t5ghs (release-blocker for 2.0.0 / f33nrj).
- Scope: Make `aw install` (the per-repo installer that lays down the framework-owned `.aw/` tree including `.aw/.gitignore`) guarantee `records/runs/` is present in `.aw/.gitignore`, idempotently, alongside the existing ignored lanes. This covers both a fresh install (via the gitignore template) and an already-installed repo (via the back-fill path). Add an install test asserting a fresh install produces a `.aw/.gitignore` that ignores `records/runs/`.
- Scope-Paths: agent_workflows/engine.py, tests/test_installer.py
- Status: approved
- Set: 8t5ghsgi
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: s2ufeo
- Approval: 2026-08-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-25 approved (aw set): status set to approved
- 2026-08-25 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (include co-located history.jsonl back-fill per Fix Bar + test it), OQ-01 marked resolved
- 2026-08-24 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; single-child plan for backlog item 8t5ghs (install must gitignore records/runs/). NOTE: release-blocker intent (`Blocks-Release: next`, gates 2.0.0 / f33nrj) is DEFERRED from front matter until the vwios6ipd Set makes plans able to carry the field without failing `aw ipd lint` (IPD-M103). Interim intent is tracked on backlog item 8t5ghs and the f33nrj release record; re-mark via `aw ipd set --blocks-release next` once that Set lands.

## Goal

Guarantee that every repo where `aw install` runs has `records/runs/` in its `.aw/.gitignore`, so ipdrunner durable run state is never committed, without requiring anyone to add the entry by hand.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fresh-install template

- [x] E-01 In `agent_workflows/engine.py`, add `records/runs/` to `_AW_GITIGNORE_TEMPLATE` (`engine.py:4055-4067`) alongside the existing `records/*/untracked/`, `setup-repo-needed.md`, and `records/history.jsonl` entries, so a fresh install writes it.
  - Depends on: none
  - Expected outcome: a brand-new `.aw/.gitignore` written by install contains `records/runs/`.
  - Execution note: commit b78501b; added a `records/runs/` line (with an `awrunsignore` comment) to `_AW_GITIGNORE_TEMPLATE` alongside `records/*/untracked/`, `setup-repo-needed.md`, and `records/history.jsonl`.
  - Execution state: performed

### Task group 2: Idempotent back-fill for existing installs

- [x] E-02 In `agent_workflows/engine.py`, extend `_ensure_aw_gitignore` (`engine.py:4737-4756`) to back-fill `records/runs/` when the file exists but lacks the line, mirroring the existing `if "<entry>" not in text: additions.append(...)` pattern used for `records/*/untracked/` and `setup-repo-needed.md` (add one more `if "records/runs/" not in text: additions.append("records/runs/")` clause). Do not duplicate the line if already present. ALSO close the co-located pre-existing gap in the SAME `additions` block: `records/history.jsonl` is in the template but missing from the back-fill list, so a repo installed before that lane existed never gains it - add the matching `if "records/history.jsonl" not in text: additions.append("records/history.jsonl")` clause. This is one adjacent line, zero added risk, and closes the latent bug F-02 names rather than leaving it; both back-fills share the existing single write path.
  - Depends on: none
  - Expected outcome: re-running install (or the ensure path) on a repo whose `.aw/.gitignore` predates this change adds `records/runs/` (and, if missing, `records/history.jsonl`) exactly once each; running again is a no-op.
  - Execution note: commit b78501b; `_ensure_aw_gitignore` gained two back-fill clauses mirroring the existing `if "<entry>" not in text: additions.append(...)` pattern: `records/runs/` (awrunsignore) and the co-located `records/history.jsonl` (closing F-02, which was in the template but missing from the back-fill list). Both share the single existing write path; deduped by the `not in text` guard.
  - Execution state: performed

### Task group 3: Install test

- [x] E-03 In `tests/test_installer.py`, add a test asserting a fresh install produces a `.aw/.gitignore` whose contents include `records/runs/`, and (idempotency) that a second `_ensure_aw_gitignore` pass does not duplicate the line. Add a back-fill fixture: write a pre-existing `.aw/.gitignore` missing BOTH `records/runs/` and `records/history.jsonl`, run `_ensure_aw_gitignore`, and assert each is added exactly once (guarding the E-02 co-located history.jsonl back-fill too) and a second pass is a no-op.
  - Depends on: E-01, E-02
  - Expected outcome: passing test proving the fresh-install guarantee, the `records/runs/` + `records/history.jsonl` back-fill, and idempotency.
  - Execution note: commit b78501b; added `tests/test_installer.py::AwGitignoreRunsLaneTests` - template-contains-records-runs, fresh-install-presence + idempotency, and the pre-existing-gitignore back-fill (both `records/runs/` and `records/history.jsonl` added exactly once, second pass a no-op). NOTE: test_installer.py carries `pytestmark = pytest.mark.slow`, so these run under `pytest -m ""` / `make test-all` (not the default `-m "not slow"` selection).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `.aw/.gitignore` is defined by `AW_GITIGNORE_PATH` (`engine.py:4054`) and `_AW_GITIGNORE_TEMPLATE` (`engine.py:4055-4067`); the fresh-install write registers it at `engine.py:4683`.
- `_ensure_aw_gitignore` (`engine.py:4737-4756`) writes the full template when absent and back-fills a hardcoded subset (`records/*/untracked/`, `setup-repo-needed.md`) when present. Note: `records/history.jsonl` is in the template but NOT the back-fill list (a pre-existing inconsistency).
- Install tests live in `tests/test_installer.py` (also `tests/test_doctor_and_marker.py` covers the setup marker + gitignore). Run with `python3 -m pytest tests/test_installer.py`.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Toolkit user | Fresh `aw install` does not add `records/runs/` to `.aw/.gitignore`, so ipdrunner run dirs show as untracked noise and risk being committed. |
| F-02 | Med | Maintainer | `_ensure_aw_gitignore` back-fill list is a hardcoded subset that already omits `records/history.jsonl`; a new lane must be added in both the template and the back-fill list to be guaranteed everywhere. |

## Proposed changes (ordered, validatable)

1. Add `records/runs/` to `_AW_GITIGNORE_TEMPLATE`.
2. Add a `records/runs/` back-fill clause to `_ensure_aw_gitignore`.
3. Add an install test asserting fresh-install presence and idempotency.

## Deferred / out of scope (with reason)

- The `records/history.jsonl` back-fill divergence is now INCLUDED in E-02 (it is trivially co-located - one adjacent line in the same `additions` block, zero added risk - so the Fix Bar favors closing it here rather than deferring). No broader template/back-fill audit beyond these two lanes is in scope.
- No change to what ipdrunner writes or where; only the ignore guarantee.

## Scope check

- Over-scope: none. Two files only.
- Under-scope: none. Covers fresh install, existing-install back-fill, and a regression test, which is the complete guarantee the backlog item requires.

## Required tests / validation

- `python3 -m pytest tests/test_installer.py` green, including the new fresh-install + idempotency test.
- Manual: run `aw install` in a scratch repo and confirm `.aw/.gitignore` contains `records/runs/`; run again and confirm no duplicate line.
- `pre-commit run --files agent_workflows/engine.py tests/test_installer.py`.

## Spec / documentation sync

- If the `.aw/` layout docs or the installer README enumerate ignored lanes, add `records/runs/` for parity. Otherwise N/A. Verify during execution.

## Open questions

### OQ-01: Should the entry be `records/runs/` (trailing slash, directory) to match the sibling `records/*/untracked/` style?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED. Use `records/runs/` (trailing slash, directory form) to match the existing directory-ignore style (`records/*/untracked/`) and the manual entry already present in this repo's `.aw/.gitignore` (verified: `.aw/.gitignore:15`). Non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: snippet of `_AW_GITIGNORE_TEMPLATE` showing `records/runs/`; pasted contents of a freshly installed `.aw/.gitignore` (from the test or a scratch install) containing the line.
  - Observed evidence: (commit b78501b) `_AW_GITIGNORE_TEMPLATE` now ends with a comment + `records/runs/`. Scratch `engine._ensure_aw_gitignore(<fresh tmp>)` wrote a `.aw/.gitignore` whose tail is: `# The ipdrunner IPD-driver per-run durable state ... never committed (awrunsignore).` then `records/runs/`. `AwGitignoreRunsLaneTests.test_template_contains_records_runs` and `test_fresh_install_gitignores_records_runs_and_is_idempotent` pass.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted test/manual output showing a pre-existing gitignore missing `records/runs/` and `records/history.jsonl` gains each exactly once, and a second pass is a no-op (no duplicate lines).
  - Observed evidence: (commit b78501b) `AwGitignoreRunsLaneTests.test_backfill_adds_runs_and_history_once_on_preexisting` passes: seeding a `.aw/.gitignore` with only `records/*/untracked/` + `setup-repo-needed.md`, one `_ensure_aw_gitignore` pass yields `text.count('records/runs/') == 1` and `text.count('records/history.jsonl') == 1`, and a second pass leaves both counts at 1 (no-op). Manual smoke confirmed the same counts (backfill runs once: True | history once: True; backfill idempotent: True).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_installer.py` output with the new test passing.
  - Observed evidence: (commit b78501b) `python3 -m pytest tests/test_installer.py -m "" -k AwGitignoreRunsLane` -> `3 passed`; full `python3 -m pytest tests/test_installer.py -m ""` -> `148 passed` (no regression; the `-m ""` is required because test_installer.py is `pytestmark = pytest.mark.slow` and the default selection is `-m "not slow"`). Whole default suite `python3 -m pytest tests/` -> 2221 passed, 1 skipped. `pre-commit run --files agent_workflows/engine.py tests/test_installer.py` -> all hooks Passed.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one small, cohesive concern (guarantee `records/runs/` is gitignored by install) across the template, the back-fill path, and a regression test.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and resolved (`records/runs/` directory form). No blocking open question remains.
2. Scope fence: touch ONLY `agent_workflows/engine.py` and `tests/test_installer.py`. Do NOT alter unrelated install behavior or the ipdrunner tool. If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 -m pytest tests/test_installer.py` and any scratch-install output); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
