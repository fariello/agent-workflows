# IPD: untrack .aw/records/history.jsonl (accidental local sidecar) and gitignore it

- Date: 2026-08-20
- Kind: child
- Concern: repo hygiene / P5 externalize-local-state. `.aw/records/history.jsonl` (the per-repo append-only workflow-history sidecar) is accidentally git-TRACKED, so every `aw` status write dirties the tree and can leak local operational detail into the public repo.
- Scope: `git rm --cached` the tracked sidecar (keep on disk); add `records/history.jsonl` to the framework-owned `.aw/.gitignore` AND its source template `_AW_GITIGNORE_TEMPLATE` (engine.py) so fresh installs ignore it too; update the installer template tests. Does NOT touch `.aw/config/project.json` (that is a portable, MAY-be-tracked project policy, a different class) or the record_history writer/reader behavior.
- Status: to-review
- Set: awhistignore
- Order: 1
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: pprchd

## Workflow history

- 2026-08-20 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.

## Goal

Stop tracking `.aw/records/history.jsonl` and make the framework ignore it going forward, so the per-machine append-only history log behaves like the local sidecar it is (no working-tree churn, no operational-detail leakage, no cross-machine merge noise) - matching how `config/local.json` is already handled, and honoring GUIDING_PRINCIPLES P5 (externalize local state).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: untrack the sidecar + fix the live gitignore

- [ ] E-01 Remove `.aw/records/history.jsonl` from git tracking WITHOUT deleting it on disk (`git rm --cached .aw/records/history.jsonl`), and add the line `records/history.jsonl` to the live framework-owned `.aw/.gitignore` (the pattern is relative to `.aw/`, matching the existing `records/*/untracked/` style), with a one-line comment explaining it is the per-machine append-only history sidecar (never committed). Commit the removal + the gitignore edit path-scoped. After this, `git ls-files .aw/records/history.jsonl` is EMPTY and `git check-ignore .aw/records/history.jsonl` matches.
  - Depends on: none
  - Expected outcome: the sidecar is untracked-and-ignored; the file still exists on disk; `git status` no longer shows it as modified.
  - Execution state: pending

### Task group 2: fix the install-time template + document the intent

- [ ] E-02 Add the same `records/history.jsonl` line (with its comment) to the source template `_AW_GITIGNORE_TEMPLATE` in `agent_workflows/engine.py` (near the const `AW_GITIGNORE_PATH = ".aw/.gitignore"`; the template currently lists only `records/*/untracked/` and `setup-repo-needed.md`), so `_ensure_aw_gitignore` writes it into every fresh/updated install. Keep the pattern relative to `.aw/`. Cross-reference the record-history sidecar spec (`.aw/records/specs/20260818-1525-02-*.spec.md`) note that the sidecar is a local repo file; if the spec is silent on tracking, add a one-line clarification there that it is local-only (not committed) to keep single-source-of-truth.
  - Depends on: none
  - Expected outcome: `_AW_GITIGNORE_TEMPLATE` contains `records/history.jsonl`; a fresh install's `.aw/.gitignore` ignores the sidecar; the spec states the local-only/not-tracked intent.
  - Execution state: pending

### Task group 3: tests

- [ ] E-03 Update the installer/template assertions that pin the `.aw/.gitignore` content (`tests/test_setup_artifacts.py` around the `records/*/untracked/` + `setup-repo-needed.md` assertions at ~:79-113 and :269; and any parallel assertion in `tests/test_untracked_lane_both_layouts.py:61`) to also assert `records/history.jsonl` is present in the emitted template/live file. Add a focused test asserting a freshly installed repo's `.aw/.gitignore` ignores `records/history.jsonl` (i.e. `git check-ignore` / pattern-match semantics, or template-content assertion consistent with the existing style). Run the FULL serial suite (`python3 -m pytest -p no:xdist`) and paste the tail.
  - Depends on: E-02
  - Expected outcome: template/installer tests assert the new line and pass; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `record_history.py:19` `SIDECAR_RELPATH = ".aw/records/history.jsonl"`; `history_path()` (`:25-27`) resolves it REPO-relative (no `~`/`$HOME`) - so "global sidecar" means one-file-per-repo across all record trees, NOT a home-dir file. Written append-only on every status transition (`specs.py:127`, `backlog.py:386` -> `record_history.append`).
- The sidecar was first tracked ACCIDENTALLY: `git log --diff-filter=A -- .aw/records/history.jsonl` -> single commit `19f11bc` "feat(shims): implement /aw slash-command dispatcher" - the history lines were swept into an unrelated feature commit, not a deliberate track-this decision. The feature that created the sidecar (`awhistory` Set) neither committed nor ignored it.
- Framework-owned gitignore: `engine.py` `AW_GITIGNORE_PATH = ".aw/.gitignore"`, `_AW_GITIGNORE_TEMPLATE` (currently `records/*/untracked/` + `setup-repo-needed.md`), re-emitted by `_ensure_aw_gitignore`; the template is in the install manifest. Template patterns are relative to `.aw/`.
- `config/project.json` is a DIFFERENT class: spec `20260810-1447-01:63,106` classifies it as the portable, MAY-be-tracked project policy (counterpart to the gitignored `config/local.json`). It is only incidentally uncommitted; it MUST NOT be gitignored. Out of scope here.
- Nothing requires the sidecar git-tracked: readers (`read_all`/`read_for`) read it off disk (tracked or not); no test asserts `git ls-files`; not in packaging.

## Findings

| ID | Severity | Evidence | Finding |
|----|----------|----------|---------|
| HY-001 | Medium | `git ls-files .aw/records/history.jsonl` (tracked); first added `19f11bc`; `_AW_GITIGNORE_TEMPLATE` engine.py (omits it) | The per-repo append-only history sidecar is accidentally tracked and not ignored, so every `aw` status write dirties the tree, produces commit noise / cross-machine merge risk, and can leak local operational detail (actors/timestamps) into the public repo. Violates P5. |
| HY-002 | Low | `git status` ` M .aw/records/history.jsonl` (uncommitted append from `aw backlog set oijafw`) | Concretely observed: a routine `aw backlog set` left the tracked sidecar dirty, confirming perpetual churn. |

## Proposed changes (ordered, validatable)

1. `git rm --cached` the sidecar + add `records/history.jsonl` to the live `.aw/.gitignore` (E-01).
2. Add the same line to `_AW_GITIGNORE_TEMPLATE` so fresh installs ignore it; note the local-only intent in the sidecar spec (E-02).
3. Update template/installer tests + full serial suite (E-03).

## Deferred / out of scope (with reason)

- `.aw/config/project.json`: NOT touched - it is a portable, MAY-be-tracked project policy (spec `20260810-1447-01:63,106`), not a local sidecar; gitignoring it would be wrong. Its current uncommitted state is incidental.
- `.agents/**/.gitignore` untracked litter: pre-migration stale-tool leftovers, addressed separately by the consent-gated `is_stale_tool_litter` sweep (`uninstall --deep`); not this plan.
- Retroactively scrubbing the already-committed history.jsonl lines from git history: not needed (the content is this repo's own benign workflow log); out of scope.

## Scope check

- Over-scope: none - each change targets HY-001 directly.
- Under-scope: none - covers the live file, the install template (fresh repos), the spec note, and tests.

## Required tests / validation

`git ls-files .aw/records/history.jsonl` empty AND `git check-ignore .aw/records/history.jsonl` matches AND the file still exists on disk; `_AW_GITIGNORE_TEMPLATE` contains `records/history.jsonl`; a fresh install's `.aw/.gitignore` ignores the sidecar; template/installer tests updated + green; full serial suite green.

## Spec / documentation sync

Add a one-line note to the record-history sidecar spec (`.aw/records/specs/20260818-1525-02-*.spec.md`) that the sidecar is a LOCAL repo file, not committed (gitignored by the framework), keeping the tracking intent single-sourced (E-02).

## Open questions

### OQ-01: Should the already-committed history.jsonl lines be scrubbed from git history?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No. The committed content is this repo's own benign workflow log (no secrets; the leak-sanitizer passes on it). `git rm --cached` stops future tracking; a history rewrite is disproportionate. Out of scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `git ls-files .aw/records/history.jsonl` returns EMPTY (untracked); `git check-ignore .aw/records/history.jsonl` prints the file (ignored); the file still EXISTS on disk (`test -f`); `git status --short` no longer lists it. Live `.aw/.gitignore` contains a `records/history.jsonl` line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `_AW_GITIGNORE_TEMPLATE` in `agent_workflows/engine.py` contains `records/history.jsonl`; installing into a fresh temp repo writes a `.aw/.gitignore` that ignores `records/history.jsonl`; the sidecar spec `20260818-1525-02-*` states the local-only/not-committed intent.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `tests/test_setup_artifacts.py` (and any parallel template test) assert `records/history.jsonl` in the template/live gitignore and pass; `python3 -m pytest -p no:xdist` full serial suite tail pasted, green.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST be human-approved (Status: approved) before execution; it is not auto-run. Execution contract: commit only files changed by the plan, path-scoped, never push; run the full serial suite and paste the ACTUAL runner output as V evidence; do NOT delete history.jsonl from disk (untrack only); do NOT gitignore config/project.json; on completion lint --phase pre-transition while approved, then flip to executed + executed history line + remove the Approval line + git mv to executed/ + post-transition lint. Do not mark executed until every V item is verified with concrete evidence.
