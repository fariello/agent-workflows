# IPD: Untrack the four generated index manifests and reconcile stale-index semantics

- Date: 2026-09-06
- Kind: child
- Concern: The four generated manifests are still TRACKED at HEAD `7f80180e` (`git ls-files` lists `.aw/records/plans/INDEX.json`, `plans/INDEX.md`, `research/INDEX.json`, `research/INDEX.md`; `git check-ignore` reports none of them ignored). They are byte-deterministically regenerated from the artifact files, so every diff is derived, and the churn is measured: 328 commits in 14 days on `plans/INDEX.json` alone (item `ila6vl`), and 58 commits in the 4 days to 2026-09-06 touching the two JSON manifests. It stopped being only a churn tax on 2026-09-06, when a conflict in `plans/INDEX.json` was the SOLE reason lane `ueg5cf`'s merge-back aborted in run `run-20260906T162533Z-1552446`, stranding 2477 lines of correct, tested code and cascading two further Set items into `dependency-blocked`. `git merge-tree` confirmed the real code auto-merged cleanly. A tracked auto-regenerated file conflicts on any concurrent lane BY CONSTRUCTION.
- Scope: The tree state and the statements about it. IN: adding the four paths to the framework-owned `.aw/.gitignore`; `git rm --cached` them in the SAME commit; deciding and implementing the `check.stale-index` semantics for a now-untracked file at its two emitters and four doctor consumers; correcting the three documents that imply the manifests are committed. OUT: the commit-path-set removal (child 01, a declared dependency); any change to `aw index` regeneration itself; the broader repo-local-untracked question (backlog `hsixiz`).
- Scope-Paths: .aw/.gitignore, .aw/records/plans/INDEX.json, .aw/records/plans/INDEX.md, .aw/records/research/INDEX.json, .aw/records/research/INDEX.md, agent_workflows/plans_index.py, agent_workflows/research_index.py, agent_workflows/doctor.py, .aw/records/plans/README.md, .aw/records/research/README.md, CONTRIBUTING.md, tests/test_doctor.py
- Item-Dependencies: executed:4r0qp1
- Status: draft
- Set: idxuntrack
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: ila6vl
- Id: yvvf98

## Workflow history

- 2026-09-06 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-06 authored (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `ila6vl`. Carries the maintainer's 2026-08-31 decision to untrack plus the 2026-09-06 answer to the item's one remaining check (nothing outside the repo consumes the committed manifests), which removes the last precondition. Depends on child 01 because untracking before the commit-path removal would point a journalled finalize transaction at gitignored paths.

## Goal

Make the four generated index manifests gitignored, locally-regenerated views: present and checkable on disk, absent from git. Keep `check.stale-index` meaningful under the new regime with its semantics decided explicitly rather than by accident, and correct the documents that currently tell a reader the manifests are committed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: untrack

- [ ] E-01 Add the four manifest paths to the FRAMEWORK-OWNED `.aw/.gitignore` (never the user's root `.gitignore`), and `git rm --cached` all four in the SAME commit. Follow the existing precedent in that file, where `system/layout.json` and `system/layout.schema.json` are ignored with an explicit comment that tracking generated output is the drift the design exists to avoid; write a comparable comment naming byte-deterministic regeneration and the `ueg5cf` incident. Paths are relative to `.aw/`, so they are `records/plans/INDEX.json` and siblings. The same-commit requirement is not stylistic: a concurrent agent's `aw index` auto-refresh will re-stage them between two commits and the change will look like it did not take.
  - Depends on: none
  - Expected outcome: `git ls-files` lists none of the four; `git check-ignore` reports all four ignored; the four files still exist on disk unchanged.
  - Execution state: pending

### Task group 2: reconcile the consumers of the now-changed guarantee

- [ ] E-02 Decide and implement what `check.stale-index` MEANS for an untracked file, and record the choice with its reasoning. Its meaning shifts from "the committed view is current" to "the local view is current". Emitted at `plans_index.py:284,289` and `research_index.py:469,473` with the message "INDEX.json is missing or out of date", which conflates two now-different cases: MISSING (expected in a fresh clone, since nothing has generated one yet) and PRESENT-BUT-STALE (a real local problem). Implement the split: absence must not be reported as drift with the same severity as staleness. Verified precondition: `aw index plans --check` byte-compares against the file on DISK, not against git, so the check remains sound once absence is handled.
  - Depends on: E-01
  - Expected outcome: a fresh clone with no manifest does not report a hard drift; a present-but-stale manifest still does; both messages name `aw index <type>` as the fix.
  - Execution state: pending

- [ ] E-03 Update the four `doctor.py` consumers so E-02's semantics flow through the aggregation and its remediation hint. Locate by SYMBOL: the rule-matching at `:859` (`"stale-index" in rule or rule.startswith("doctor.index-")`), the comment at `:938`, the hint block at `:1049` ("aw index" / "aw index <type>"), and the two predicates at `:1382` and `:1460`. Confirm the doctor's exit-code aggregation does not turn an expected fresh-clone absence into a failure.
  - Depends on: E-02
  - Expected outcome: `aw doctor` reports a missing manifest as informational and a stale one as actionable, with the `aw index` hint intact in both.
  - Execution state: pending

- [ ] E-04 Correct the three documents that assert or imply the manifests are committed: `.aw/records/plans/README.md:87`, `.aw/records/research/README.md:30,44-45,49`, and `CONTRIBUTING.md:54-55`. State plainly that they are generated, gitignored, local views, regenerated with `aw index <type>`, and absent in a fresh clone until generated. Record the three accepted losses the maintainer already accepted on the item: no manifest in a fresh clone, no `INDEX.md` browsing on a git host, no manifest diffs in review. Write no em or en dashes in this user-facing prose.
  - Depends on: E-01
  - Expected outcome: no in-repo document tells a reader the manifests are committed.
  - Execution state: pending

- [ ] E-05 Prove the end-to-end outcome the item exists for, and pin it. Add or extend a test asserting the four paths are gitignored and untracked, so a future change cannot silently re-track them. Then demonstrate the original failure is fixed: construct the `ueg5cf` scenario (two branches whose only conflicting path is a generated manifest) and show the merge-back now succeeds or, if it still conflicts, that the reason names it as regenerable per the `mergemsg` fix in `998fd708`. Note honestly which of the two outcomes was observed.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a durable guard against re-tracking, plus pasted evidence about the concurrent-lane scenario that motivated the change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.aw/.gitignore` is framework-owned and is the correct home for this. It already ignores `records/*/untracked/`, `setup-repo-needed.md`, `records/history.jsonl`, `records/runs/`, `/inbox/`, and `system/layout.json`. The maintainer chose exactly this mechanism for `layout.json` on 2026-09-01 and cited `ila6vl` when doing so, so this child follows an established precedent rather than inventing one.
- `/inbox/` in that file carries a comment explaining why it is ANCHORED with a leading slash: a bare `inbox/` would match at any depth and swallow the tracked `records/comms/shared/inbox/`. Mind the same trap: write specific paths, not a bare `INDEX.json` pattern that would match any depth in any tree.
- No CI workflow references INDEX at all (`local-leaks.yml`, `secret-scan.yml`, `tests.yml`), so the item's scope point 8 needs no work beyond confirming it still holds at execution time.
- Suite bare (`python3 -m pytest`); prefer an isolated worktree; expect ~35 environment-related failures in any lane worktree (`agrlvw`) and compare node ids, not totals.

## Findings

| Id | Severity | Location (HEAD `7f80180e`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | git index | All four manifests still tracked and none gitignored. | `git ls-files` lists all four; `git check-ignore` reports none |
| F-2 | HIGH | run `run-20260906T162533Z-1552446` | A conflict in `plans/INDEX.json` was the SOLE cause of lane `ueg5cf`'s aborted merge-back, stranding 2477 lines and cascading 2 items to `dependency-blocked`. | `git merge-tree main aw/lane/ueg5cf` showed one CONFLICT, in that file; code and tests auto-merged |
| F-3 | MED | `plans_index.py:284,289`; `research_index.py:469,473` | The `stale-index` message conflates MISSING with OUT-OF-DATE, which become materially different cases once untracked. | message string "INDEX.json is missing or out of date" |
| F-4 | MED | `doctor.py:859,938,1049,1382,1460` | Four consumers plus a hint block key on the `stale-index` rule; the item's "four places" count is confirmed. | source read |
| F-5 | LOW | 3 documents | `plans/README.md:87`, `research/README.md:30,44-45,49`, `CONTRIBUTING.md:54-55` describe the manifests without noting they will be untracked. | source read |
| F-6 | INFO | maintainer, 2026-09-06 | The item's one remaining precondition ("does anything OUTSIDE this repo consume the committed manifests?") is answered: NO. This removes the last blocker to executing. | maintainer statement, recorded on `ila6vl` at graduation |

## Proposed changes (ordered, validatable)

1. E-01 untracks (gitignore plus `git rm --cached`, one commit).
2. E-02 then E-03 make the check and the doctor correct under the new regime, in that order because the doctor consumes the rule.
3. E-04 corrects the documents.
4. E-05 pins the outcome against regression and reports on the motivating scenario.

## Deferred / out of scope (with reason)

- The commit-path-set removal: child 01, declared as `Item-Dependencies: executed:4r0qp1`.
- The broader "should repo-local records be untracked" question: backlog `hsixiz`, which may subsume the direction this sets but is a much larger scope.
- Any change to `aw index` regeneration behavior or timing: not required, and widening here would obscure whether an untracking regression came from the ignore or from the generator.
- Retroactively purging manifest blobs from git history: not requested, not needed for the goal, and history rewriting on a shared repo is a separate maintainer decision.

## Scope check

- Over-scope: `tests/test_doctor.py` is in scope only for the cases E-02/E-03 change; do not refactor that module.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there at execution time and pasted; compare failing NODE IDS, not totals. Plus the git-state assertions in E-05 (`git ls-files`, `git check-ignore`) and a fresh-clone check that a missing manifest does not produce a hard failure.

## Spec / documentation sync

Three documents in E-04. No spec change: `ila6vl` is a maintainer decision recorded on the backlog item, not a spec requirement, and spec `kw5y2s` already cites it as settled precedent rather than depending on this change.

## Open questions

### OQ-01: Should a MISSING manifest be silent, informational, or a warning?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: E-02 must choose and record. The repository constrains but does not fully determine it: the `layout.json` precedent established that readers must tolerate absence, which rules out treating absence as an error, but leaves silent-versus-informational open. Decide from the doctor's aggregation behavior (an informational note must not change its exit code) and record the reasoning. Not escalated: it is an internal diagnostic severity with no public contract, and either choice satisfies the item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git ls-files | grep -E 'INDEX\.(json|md)$'` returning EMPTY, `git check-ignore -v` naming `.aw/.gitignore` for all four paths, `ls` proving the four files still exist on disk, and `git show --stat` of the single commit showing the `.gitignore` edit and the four deletions together.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw index plans --check` clean with the manifest present; then move the manifest aside and paste the output proving ABSENCE is not reported as a hard drift; then corrupt it and paste the output proving PRESENT-BUT-STALE still is. Three distinct pasted runs, and the recorded decision with its reasoning.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw doctor` output (and its exit code) for both the missing-manifest and stale-manifest cases, showing the `aw index` hint present in both and the exit code unchanged by a mere absence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the changed passages from all three documents, plus a grep proving no remaining in-repo statement implies the manifests are committed. Confirm no em or en dashes were introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new guard test passing, AND a mutation check (re-track one manifest, show the guard FAILS, revert, show it passes). Plus the `ueg5cf`-scenario demonstration with its actual observed outcome stated honestly, including which of the two acceptable outcomes occurred.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. E-01 is the one deliberate exception to one-concern-per-commit: the `.gitignore` edit and the four `git rm --cached` deletions MUST be a single commit, for the reason E-01 states. When reporting tests passed, paste the ACTUAL runner output.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved yvvf98 --by-human --message ...`) before execution, and its `Item-Dependencies: executed:4r0qp1` refuses dispatch until child 01 is executed. Do NOT hand-write a `Readiness:` field (`IPD-M107`). On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
