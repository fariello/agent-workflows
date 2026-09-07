# IPD: Untrack the four generated index manifests and reconcile stale-index semantics

- Date: 2026-09-06
- Kind: child
- Concern: The four generated manifests are still TRACKED at HEAD `7f80180e` (`git ls-files` lists `.aw/records/plans/INDEX.json`, `plans/INDEX.md`, `research/INDEX.json`, `research/INDEX.md`; `git check-ignore` reports none of them ignored). They are byte-deterministically regenerated from the artifact files, so every diff is derived, and the churn is measured: 328 commits in 14 days on `plans/INDEX.json` alone (item `ila6vl`), and 58 commits in the 4 days to 2026-09-06 touching the two JSON manifests. It stopped being only a churn tax on 2026-09-06, when a conflict in `plans/INDEX.json` was the SOLE reason lane `ueg5cf`'s merge-back aborted in run `run-20260906T162533Z-1552446`, stranding 2477 lines of correct, tested code and cascading two further Set items into `dependency-blocked`. `git merge-tree` confirmed the real code auto-merged cleanly. A tracked auto-regenerated file conflicts on any concurrent lane BY CONSTRUCTION.
- Scope: The tree state, the mechanism that reproduces it in every managed repo, and the statements about it. IN: adding the four paths to the framework-owned `.aw/.gitignore`; `git rm --cached` them in the SAME commit; extending the INSTALLER's `.aw/.gitignore` template and its back-fill list so a fresh install and every already-managed repo inherit the ignore (F-7, carried from child 01's review as PR-008); registering `stale-index` in `check_engine.RULE_REGISTRY` and splitting MISSING from PRESENT-BUT-STALE at the two emitters; reconciling the doctor consumers; correcting the FOUR documents that assert or imply the manifests are committed (the three named plus the shipped installer TEMPLATE, F-8). OUT: the commit-path-set removal (child 01, a declared dependency); any change to `aw index` regeneration itself; the broader repo-local-untracked question (backlog `hsixiz`).
- Scope-Paths: .aw/.gitignore, .aw/records/plans/INDEX.json, .aw/records/plans/INDEX.md, .aw/records/research/INDEX.json, .aw/records/research/INDEX.md, agent_workflows/plans_index.py, agent_workflows/research_index.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, agent_workflows/engine.py, .aw/records/plans/README.md, .aw/records/research/README.md, CONTRIBUTING.md, .aw/system/workflows/templates/agents-docs-research-README.md, tests/test_plans_index.py, tests/test_research_index.py, tests/test_doctor_remediations.py, tests/test_engine_install.py
- Item-Dependencies: executed:4r0qp1
- Status: approved
- Readiness: go-pending-approval
- Set: idxuntrack
- Order: 2
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: ila6vl
- Id: yvvf98
- Approval: 2026-09-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-07 approved (aw set): status set to approved
- 2026-09-06 reviewed (aw set): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 (8 fixed, PR-009 deferred). Carried child 01's PR-008 as F-7: the change would not have reached any managed repo (installer template + back-fill unscoped). Resolved OQ-01 from the layout.json registry precedent. Reproduced the ueg5cf merge failure and its fix.
- 2026-09-06 to-review (aw set): Authored and ready for critique: aw ipd lint conforming, E-01..E-05 with a V-* bijection, every V-item demanding pasted evidence including two mutation checks, and the one genuinely open question (OQ-01, missing-manifest severity) left open with its decision criteria stated rather than pre-empted.

- 2026-09-06 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-06 authored (opencode/its_direct/pt3-claude-opus-5-1m-us): graduated from backlog `ila6vl`. Carries the maintainer's 2026-08-31 decision to untrack plus the 2026-09-06 answer to the item's one remaining check (nothing outside the repo consumes the committed manifests), which removes the last precondition. Depends on child 01 because untracking before the commit-path removal would point a journalled finalize transaction at gitignored paths.

## Goal

Make the four generated index manifests gitignored, locally-regenerated views: present and checkable on disk, absent from git. Keep `check.stale-index` meaningful under the new regime with its semantics decided explicitly rather than by accident, and correct the documents that currently tell a reader the manifests are committed.

Make the change reach EVERY managed repo, not just this checkout. The repo's `.aw/.gitignore` is byte-identical to `engine._AW_GITIGNORE_TEMPLATE`, so editing only the file would leave every fresh `aw install` and every already-installed repo still tracking the manifests, and the `ueg5cf` failure class would remain live everywhere but here (F-7).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: untrack

- [ ] E-01 Add the four manifest paths to the FRAMEWORK-OWNED `.aw/.gitignore` (never the user's root `.gitignore`), and `git rm --cached` all four in the SAME commit. Follow the existing precedent in that file, where `system/layout.json` and `system/layout.schema.json` are ignored with an explicit comment that tracking generated output is the drift the design exists to avoid; write a comparable comment naming byte-deterministic regeneration and the `ueg5cf` incident. Paths are relative to `.aw/`, so they are `records/plans/INDEX.json` and siblings. The same-commit requirement is not stylistic: a concurrent agent's `aw index` auto-refresh will re-stage them between two commits and the change will look like it did not take.
  - Depends on: none
  - Expected outcome: `git ls-files` lists none of the four; `git check-ignore` reports all four ignored; the four files still exist on disk unchanged.
  - Execution state: pending

- [ ] E-06 Extend the INSTALLER so the ignore reaches every managed repo, not just this checkout (F-7; carried from child 01's review as PR-008). Two edits in `engine.py`, both required because they serve different populations: add the four `records/.../INDEX.{json,md}` patterns to `_AW_GITIGNORE_TEMPLATE` (`:4274-4308`), which a FRESH install writes verbatim; and add them to the `_ensure_aw_gitignore` back-fill list (`:5323-5370`), which is the only path that reaches an ALREADY-INSTALLED repo. Follow the existing `system/layout.json` pattern for both, and use the same anchored-literal discipline the `/inbox/` comment in that file warns about: write the four specific paths, never a bare `INDEX.json` that would match at any depth. Note the template and this repo's `.aw/.gitignore` are byte-identical today (verified), so E-01 and this item must produce the SAME four lines or the next install will diff against the repo.
  - Depends on: E-01
  - Expected outcome: a fresh `aw install` into a clean repo gitignores all four paths; re-running the installer on a repo that predates this change back-fills them; the template and this repo's file agree.
  - Execution state: pending

### Task group 2: reconcile the consumers of the now-changed guarantee

- [ ] E-02 Register `stale-index` in `check_engine.RULE_REGISTRY` and split MISSING from PRESENT-BUT-STALE at the two emitters. The mechanism is settled by an almost exact precedent, so implement it rather than re-deriving it (see OQ-01, resolved): `stale-index` is currently UNREGISTERED, so `rule_spec` returns `_DEFAULT_RULESPEC` with `severity="error"` (verified live), and `artifact_core.drift_exit_code:405-415` fails the gate for anything not `info`. Emit TWO distinct rules from `plans_index.py:281-291` and `research_index.py:467-475`, replacing the single conflated "INDEX.json is missing or out of date": a MISSING case and a STALE case, each with its own registry entry and its own message. Follow `check.system-layout-missing`/`check.system-layout-drift` (`check_engine.py:294-309`), which solved the identical problem for the gitignored `layout.json`: a generated, gitignored artifact whose absence must not fail a fresh clone. Copy its two design choices explicitly: the `warning`-not-`error` reasoning (the artifact is GENERATED and the remedy is mechanical, so the CLASS differs even where loudness does not), and if you make absence non-failing you MUST use `info`, because `warning` still exits nonzero. Keep both messages naming `aw index <type>` as the fix.
  - Depends on: E-01
  - Expected outcome: a fresh clone with no manifest does not fail the gate; a present-but-stale manifest still does; both rules are REGISTERED rather than falling through to the conservative default; both messages name the fix.
  - Execution state: pending

- [ ] E-03 Reconcile the `doctor.py` consumers with E-02's new rule ids. All five sites match on the SUBSTRING `"stale-index"` (`:859` remediation, `:938` comment, `:1049` priority comment, `:1382` and `:1460` count predicates), so if E-02's new ids both CONTAIN that substring they keep matching unchanged, and if they do not, all five break silently. Decide which and state it: prefer ids that preserve the substring (e.g. `stale-index-missing` / `stale-index-stale`) so the existing matching holds, and verify rather than assume. Then confirm the count predicates at `:1382`/`:1460` do not report an expected fresh-clone absence as a finding, and that the remediation hint (`aw index <type>`) is produced for BOTH cases.
  - Depends on: E-02
  - Expected outcome: `aw doctor` reports a missing manifest as non-failing and a stale one as actionable, with the `aw index` hint intact in both and no silently-broken substring match.
  - Execution state: pending

- [ ] E-07 Reconcile the OTHER consumer of the same emitters, which the authored plan missed (F-9): `check_engine.check_content` calls `plans_index.check_drift` (`:629`) and `research_index.check_drift` (`:727`), so E-02's new rules flow into `aw check plans`/`aw check research`/`aw check all`, not only into `aw index --check` and `aw doctor`. Verify the two new rule ids are enriched correctly through `enrich_drift` (`:322-343`) and that `aw check` behaves as intended for both cases. Also confirm the regeneration scan is unaffected: the manifests are excluded from `_scan_plans`/`_scan_docs` by NAME (`plans_index._EXCLUDE_NAMES:49`, `research_index:74`) BEFORE `is_ignored_path` is consulted, which is why gitignoring them does not make the generator skip its own inputs. State that as verified, because if it were false the manifests would regenerate empty.
  - Depends on: E-02
  - Expected outcome: `aw check plans` and `aw check research` report the missing and stale cases with the intended severities, and the generator still sees every artifact.
  - Execution state: pending

- [ ] E-04 Correct the FOUR documents that assert or imply the manifests are committed. Three are the ones already named: `.aw/records/plans/README.md:85-96`, `.aw/records/research/README.md:48-50`, `CONTRIBUTING.md:52-56`. The fourth is the shipped INSTALLER TEMPLATE `.aw/system/workflows/templates/agents-docs-research-README.md:50` (F-8), which carries the same sentence verbatim ("both are COMMITTED so a fresh clone and a weak agent have them without running the tool") and is written into every managed repo by `engine.ensure_docs_readmes` (`:5134-5175`); leaving it would re-seed the false claim into every new install. Note the research README's claim is the strongest of the four: it states the reason for committing them, so it needs rewriting rather than a caveat. State plainly that they are generated, gitignored, local views, regenerated with `aw index <type>`, and absent in a fresh clone until generated. Record the three accepted losses the maintainer already accepted: no manifest in a fresh clone, no `INDEX.md` browsing on a git host, no manifest diffs in review. Also record the two consequences this review measured, because a reader will otherwise hit them as surprises: a NEW WORKTREE has no manifest until `aw index` runs there (measured: `git worktree add` produced no manifest), and switching branches no longer changes the manifest (it is now one local file shared across branches). Write no em or en dashes in this user-facing prose.
  - Depends on: E-01
  - Expected outcome: no in-repo document and no shipped template tells a reader the manifests are committed; the worktree and branch-switch consequences are stated.
  - Execution state: pending

- [ ] E-05 Prove the end-to-end outcome the item exists for, and pin it. Add a test asserting the four paths are gitignored and untracked so a future change cannot silently re-track them; follow the EXISTING precedent `tests/test_engine_install.py` (its `IGNORE_PATTERNS` + `check-ignore` helpers already do exactly this for `layout.json`, including a template-carries-the-pattern test and a fresh-install test) rather than writing a new harness. Then demonstrate the motivating failure is fixed. This review already measured it, so the expected result is known and the executor is confirming, not exploring: with the manifest TRACKED, two branches whose only differing path is the manifest produce `CONFLICT (content)` and the merge fails; with it UNTRACKED and `git rm --cached`ed on both branches, the same merge succeeds ("Merge made by the 'ort' strategy", only `code.py` in the stat) and the manifest survives on disk. Reproduce both halves and paste them. If the untracked half still conflicts, that is a DIFFERENT outcome than measured and must be reported, not explained away.
  - Depends on: E-01, E-02, E-03, E-04, E-06, E-07
  - Expected outcome: a durable guard against re-tracking that reuses the layout.json test precedent, plus a pasted before/after merge demonstration.
  - Execution state: pending

- [ ] E-08 Retarget the test surfaces this change actually breaks, which the authored plan mis-scoped (F-10). `tests/test_doctor.py` contains ZERO `stale-index` references (verified: `grep -c` returns 0), so it is the wrong file and must be removed from scope. The real surfaces are: `tests/test_plans_index.py:233-237` and `tests/test_research_index.py:203-207`, which assert `d.rule == "stale-index"` EXACTLY and will fail the moment E-02 renames the rule; `tests/test_doctor_remediations.py:54-56,231-233`, which construct `Drift(..., "stale-index", ...)` literals; and `tests/test_ci_check_parity.py:92-115`, whose clean-tree case deliberately regenerates the index first with the comment "mirrors the committed state CI runs against", a comment that becomes false. Update each to the new rule ids and semantics, and keep every existing guarantee: do not delete a case to make it pass. Baseline measured at review time on the main checkout for these five modules: 78 passed.
  - Depends on: E-02, E-03, E-07
  - Expected outcome: the four affected test modules pass against the new rule ids, still fail if staleness stops being detected, and `test_ci_check_parity`'s stale comment no longer claims a committed baseline.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.aw/.gitignore` is framework-owned and is the correct home for this. It already ignores `records/*/untracked/`, `setup-repo-needed.md`, `records/history.jsonl`, `records/runs/`, `/inbox/`, and `system/layout.json`. The maintainer chose exactly this mechanism for `layout.json` on 2026-09-01 and cited `ila6vl` when doing so, so this child follows an established precedent rather than inventing one.
- `/inbox/` in that file carries a comment explaining why it is ANCHORED with a leading slash: a bare `inbox/` would match at any depth and swallow the tracked `records/comms/shared/inbox/`. Mind the same trap: write specific paths, not a bare `INDEX.json` pattern that would match any depth in any tree.
- No CI workflow references INDEX at all (`local-leaks.yml`, `secret-scan.yml`, `tests.yml`), so the item's scope point 8 needs no work beyond confirming it still holds at execution time.
- Suite bare (`python3 -m pytest`); prefer an isolated worktree; expect ~35 environment-related failures in any lane worktree (`agrlvw`) and compare node ids, not totals.
- Drift SEVERITY is a registry concern, not a per-emitter one. `check_engine.RULE_REGISTRY` maps a rule id to a `RuleSpec`, `enrich_drift` stamps it onto the `Drift`, and `artifact_core.drift_exit_code` fails the gate for anything that is not `info`. An UNREGISTERED rule silently gets `_DEFAULT_RULESPEC` (`error`), which is deliberate ("fail toward visible") and is exactly the state `stale-index` is in today. So changing how loudly a check speaks means registering a rule, never editing a message string.
- `.aw/.gitignore` is generated from `engine._AW_GITIGNORE_TEMPLATE` and back-filled by `_ensure_aw_gitignore`. Any change to the repo's copy that is not mirrored into BOTH will be re-diffed by the next install and will never reach another repo. The same holds for the `README` stubs under `.aw/system/workflows/templates/`, which `ensure_docs_readmes` writes into managed repos.
- The generated manifests are excluded from their own generator's scan BY NAME (`plans_index._EXCLUDE_NAMES`, `research_index`'s `INDEX_MD` check), which runs BEFORE the `is_ignored_path` filter. That ordering is what makes gitignoring them safe: an ignored path IS reported by `git ls-files --others --ignored`, so it does enter `get_ignored_dirs`, and a generator that relied on the ignore filter alone would have started skipping real inputs.

## Findings

| Id | Severity | Location (HEAD `7f80180e`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | git index | All four manifests still tracked and none gitignored. | `git ls-files` lists all four; `git check-ignore` reports none |
| F-2 | HIGH | run `run-20260906T162533Z-1552446` | A conflict in `plans/INDEX.json` was the SOLE cause of lane `ueg5cf`'s aborted merge-back, stranding 2477 lines and cascading 2 items to `dependency-blocked`. | `git merge-tree main aw/lane/ueg5cf` showed one CONFLICT, in that file; code and tests auto-merged |
| F-3 | MED | `plans_index.py:284,289`; `research_index.py:469,473` | The `stale-index` message conflates MISSING with OUT-OF-DATE, which become materially different cases once untracked. | message string "INDEX.json is missing or out of date" |
| F-4 | MED | `doctor.py:859,938,1049,1382,1460` | Four consumers plus a hint block key on the `stale-index` rule; the item's "four places" count is confirmed. | source read |
| F-5 | LOW | 3 documents | `plans/README.md:87`, `research/README.md:30,44-45,49`, `CONTRIBUTING.md:54-55` describe the manifests without noting they will be untracked. | source read |
| F-6 | INFO | maintainer, 2026-09-06 | The item's one remaining precondition ("does anything OUTSIDE this repo consume the committed manifests?") is answered: NO. This removes the last blocker to executing. | maintainer statement, recorded on `ila6vl` at graduation |
| F-7 | HIGH | `engine.py:4274-4308,5323-5370` | The change would NOT reach any other repo. This repo's `.aw/.gitignore` is BYTE-IDENTICAL to `engine._AW_GITIGNORE_TEMPLATE`, which a fresh `aw install` writes verbatim, and `_ensure_aw_gitignore` is the only path that back-fills an already-installed repo. Editing the file alone leaves every managed repo tracking the manifests, so the `ueg5cf` failure class stays live everywhere but here. Carried from child 01's review as PR-008. Addressed by new E-06. | `engine._AW_GITIGNORE_TEMPLATE == Path('.aw/.gitignore').read_text()` -> `True` |
| F-8 | HIGH | `.aw/system/workflows/templates/agents-docs-research-README.md:50` | A FOURTH document asserts the manifests are committed, and it is the one that propagates: the shipped installer template carries the same sentence verbatim ("both are COMMITTED so a fresh clone and a weak agent have them without running the tool") and `engine.ensure_docs_readmes` (`:5134-5175`) writes it into every managed repo. Correcting only the three in-repo documents re-seeds the false claim on every new install. Folded into E-04. | template line read; `diff` against `.aw/records/research/README.md` shows the sentence identical in both |
| F-9 | MED | `check_engine.py:629,727` | A THIRD consumer class of the two emitters was unscoped: `check_content` calls `plans_index.check_drift` and `research_index.check_drift`, so the rule also flows through `aw check plans`/`aw check research`/`aw check all`, not only `aw index --check` and `aw doctor`. A rename or severity change silently changes `aw check` behavior. Added as E-07. | source read |
| F-10 | MED | `tests/test_doctor.py`; `tests/test_plans_index.py:233-237`; `tests/test_research_index.py:203-207`; `tests/test_doctor_remediations.py:54-56,231-233`; `tests/test_ci_check_parity.py:92-115` | The scoped test file is the wrong one and four real surfaces were unscoped. `tests/test_doctor.py` has ZERO `stale-index` references. The tests that actually break assert `d.rule == "stale-index"` EXACTLY (plans_index, research_index), construct that literal (doctor_remediations), or carry a clean-tree comment claiming the index "mirrors the committed state CI runs against" (ci_check_parity). Added as E-08. | `grep -c stale-index tests/test_doctor.py` -> `0`; the five modules pass at review baseline (78) |
| F-11 | MED | `check_engine.py:294-309`; `artifact_core.py:405-415` | The plan left OQ-01 (missing-manifest severity) open, but the repository ALREADY DECIDED this for the identical case. `check.system-layout-missing`/`check.system-layout-drift` split exactly this problem for the gitignored, generated `layout.json`, with a recorded rationale for `warning`-not-`error`. Critically, `stale-index` is UNREGISTERED, so it currently gets `_DEFAULT_RULESPEC` severity `error`, and `drift_exit_code` fails on anything not `info`, so "informational" must mean `info` or absence still fails a fresh clone. OQ-01 resolved from this; E-02 rewritten around the mechanism. | `rule_spec('stale-index')` -> `severity='error'`; `rule_spec('check.system-layout-missing')` -> `severity='warning'` |
| F-12 | LOW | measured this review | Two consequences of untracking that no document mentions and a user will hit: a NEW WORKTREE contains no manifest until `aw index` runs there (measured: `git worktree add` produced a tree with no manifest at all), and switching branches no longer changes the manifest, since it becomes one local file shared across every branch. Neither is a defect; both are surprises worth stating. Folded into E-04. | `git worktree add` then `ls` shows no manifest; branch switch left the manifest content unchanged |

## Proposed changes (ordered, validatable)

1. E-01 untracks this repo (gitignore plus `git rm --cached`, one commit).
2. E-06 puts the same four lines into the installer template and its back-fill list, so the change reaches fresh installs and already-managed repos rather than only this checkout.
3. E-02 registers the two new rules and splits missing from stale; E-03 then E-07 reconcile the consumers (doctor, then `aw check`), in that order because both consume the rule E-02 defines.
4. E-04 corrects all four documents including the shipped template.
5. E-08 retargets the four test modules the rule rename actually breaks.
6. E-05 pins the outcome against re-tracking and reproduces both halves of the motivating merge scenario.

## Deferred / out of scope (with reason)

- The commit-path-set removal: child 01, declared as `Item-Dependencies: executed:4r0qp1`.
- The broader "should repo-local records be untracked" question: backlog `hsixiz`, which may subsume the direction this sets but is a much larger scope.
- Any change to `aw index` regeneration behavior or timing: not required, and widening here would obscure whether an untracking regression came from the ignore or from the generator.
- Retroactively purging manifest blobs from git history: not requested, not needed for the goal, and history rewriting on a shared repo is a separate maintainer decision.
- Auto-generating a manifest on demand when one is absent (so a fresh clone or a new worktree never sees the `info` case): out of scope, and deliberately so. It would change `aw index` regeneration TIMING, which this plan already excludes, and it would hide the very condition E-02 exists to report. F-12's worktree consequence is documented in E-04 rather than engineered away.
- Registering severities for the OTHER unregistered rules this review noticed in passing (`name-metadata-mismatch`, `dangling-citation`, and the rest of the two emitters' rule vocabulary all fall through to the `error` default): out of scope. Only `stale-index` changes meaning here, and a broader registry audit is its own item with its own blast radius.

## Scope check

- Over-scope: none. `tests/test_doctor.py` was REMOVED from scope: it contains zero `stale-index` references (F-10), so listing it was an error rather than a deliberate widening.
- Under-scope: none remaining. The authored plan was under-scoped on four counts, all corrected above: the installer template and back-fill (F-7, the change would not have reached any other repo), the shipped README template (F-8, would have re-seeded the false claim on every install), the `aw check` consumer path (F-9), and the four real test surfaces (F-10).

## Required tests / validation

`python3 -m pytest` bare, in an isolated worktree, baseline measured there at execution time and pasted; compare failing NODE IDS, not totals (expect ~35 environment-related failures in any lane worktree per `agrlvw`, and a concurrent co-worker commit can move the total). Baseline measured at review time on the main checkout for the directly implicated modules: `tests/test_plans_index.py tests/test_research_index.py tests/test_doctor.py tests/test_doctor_remediations.py tests/test_ci_check_parity.py` -> 78 passed.

Beyond the suite: the git-state assertions in E-05 (`git ls-files`, `git check-ignore`), the two installer exercises in E-06 (fresh install AND back-fill, which are different code paths), the exit-code evidence in V-02/V-07 (the exit code is the substance of the missing-versus-stale split, not a detail), and the both-halves merge reproduction in E-05.

CAUTION for the executor on worktree choice: this review measured that a NEW WORKTREE has no manifest at all until `aw index` runs there (F-12). If you validate in an isolated worktree AFTER E-01 lands, the manifest will legitimately be absent, which is the `info` case, not a failure. Generate it before drawing conclusions about staleness.

## Spec / documentation sync

FOUR documents in E-04, one of which is a shipped installer template that propagates into every managed repo (F-8).

No spec change: `ila6vl` is a maintainer decision recorded on the backlog item, not a spec requirement, and spec `kw5y2s` already cites it as settled precedent rather than depending on this change. Note the closely related `kw5y2s` Section 2.3 already rules the generated `layout.json` gitignored, which is the precedent E-02 follows for severity; this change is consistent with that spec rather than altering it.

## Open questions

### OQ-01: Should a MISSING manifest be silent, informational, or a warning?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW from repository evidence, because the repository had already decided the identical question and the plan's framing understated how completely. Emit MISSING at `info` severity and PRESENT-BUT-STALE at `warning`, both as REGISTERED rules. The basis is `check.system-layout-missing`/`check.system-layout-drift` (`check_engine.py:294-309`), which split exactly this case for the gitignored, generated `layout.json`, and whose own comment records the reasoning: a generated artifact whose remedy is mechanical is a `warning` rather than an `error` because the CLASS differs even when the loudness does not. The plan's "silent versus informational" framing missed the mechanism that decides it: `stale-index` is currently UNREGISTERED, so `rule_spec` hands it `_DEFAULT_RULESPEC` severity `error` (verified live), and `artifact_core.drift_exit_code:405-415` fails the gate for anything that is not `info`. So `warning` for absence would STILL fail every fresh clone, which is the outcome the plan wanted to avoid; only `info` is actually non-failing. That makes this a mechanism question with one correct answer, not a taste question with two acceptable ones. Not escalated: internal diagnostic severity, no public contract, and the precedent is the maintainer's own.

### OQ-02: Should the installer template change (E-06) land in this child, or as a follow-on?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW: land it HERE. This child is the one that makes the manifests gitignored, and F-7 shows the repo file and the installer template are byte-identical today, so the two must change together or the very next `aw install` re-diffs this repo against its own template. Splitting them would also leave the Set's stated goal unmet everywhere except this checkout while the plan claimed success. The alternative considered was a third child; rejected because the edit is two small additions in one file, it shares E-01's exact four lines, and deferring it creates a window in which the toolkit ships a fix that does not apply to its own users.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git ls-files | grep -E 'INDEX\.(json|md)$'` returning EMPTY, `git check-ignore -v` naming `.aw/.gitignore` for all four paths, `ls` proving the four files still exist on disk, and `git show --stat` of the single commit showing the `.gitignore` edit and the four deletions together.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw index plans --check` clean with the manifest present; then move the manifest aside and paste the output AND ITS EXIT CODE proving absence does not fail the gate; then corrupt it and paste the output and exit code proving present-but-stale still does. Three distinct pasted runs with exit codes, since the exit code is the whole point. Plus `python3 -c` output of `check_engine.rule_spec(<new-missing-id>)` and `rule_spec(<new-stale-id>)` showing BOTH are registered with the intended severities and neither falls through to the `error` default.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw doctor` output (and its exit code) for both the missing-manifest and stale-manifest cases, showing the `aw index` hint present in both and the exit code unaffected by a mere absence. ALSO paste a grep of the five `doctor.py` sites proving each still matches the new rule ids (or was updated), since all five match on the substring `"stale-index"` and would break silently otherwise.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the changed passages from all FOUR documents including the installer template, plus a grep over the repo proving no remaining statement (in a document OR a shipped template) implies the manifests are committed. Show the worktree and branch-switch consequences are stated. Confirm no em or en dashes were introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new guard test passing, AND a mutation check (re-track one manifest, show the guard FAILS, revert, show it passes). Plus BOTH halves of the merge demonstration: the tracked case showing `CONFLICT (content)` and a failed merge, and the untracked case showing the merge succeeding with only the real code file in the stat and the manifest still present on disk. State the observed outcome honestly; if the untracked half conflicts, report it rather than explaining it away.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste a FRESH install into a scratch repo showing all four paths gitignored afterwards (`git check-ignore -v` naming the installed `.aw/.gitignore`), AND a back-fill exercise: a scratch repo carrying a pre-change `.aw/.gitignore`, re-run the installer, show the four patterns appended without clobbering the existing content. Plus a byte-comparison proving `engine._AW_GITIGNORE_TEMPLATE` and this repo's `.aw/.gitignore` still agree after E-01 and E-06.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `aw check plans` and `aw check research` output plus exit codes for both the missing and stale cases, showing the intended severities flow through `enrich_drift`. Plus proof the generator is unaffected: paste `aw index plans` regenerating a manifest with the full plan count while the manifest itself is gitignored, demonstrating the name-exclusion still admits every artifact.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the full passing output of `python3 -m pytest tests/test_plans_index.py tests/test_research_index.py tests/test_doctor_remediations.py tests/test_ci_check_parity.py tests/test_engine_install.py -o addopts="" -q`, with the before/after counts stated (78 passed at review baseline for these five modules). Plus a MUTATION CHECK: make a manifest stale, show the retargeted assertion FAILS if staleness detection is removed, then restore. Confirm `tests/test_doctor.py` was dropped from scope and state why.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Size note: 8 E-leaves in 2 groups, within the count thresholds; grown from 5 by the review's re-sweep (installer reach, template document, `aw check` consumer, test retargeting).
- Cohesion rationale: E-01 and E-06 both write the SAME four gitignore lines, to two places that must not diverge (the repo file and the installer template are byte-identical today), so they are deliberately adjacent and sequenced rather than merged: E-01's commit has a hard same-commit constraint with `git rm --cached` that E-06's edit does not share. E-02/E-03/E-07 are one rule definition plus its two consumer surfaces, split because each consumer has its own test surface and failure mode (the doctor's five substring matches, `aw check`'s enrichment path). E-04 and E-08 are single-concern.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. E-01 is the one deliberate exception to one-concern-per-commit: the `.gitignore` edit and the four `git rm --cached` deletions MUST be a single commit, for the reason E-01 states. When reporting tests passed, paste the ACTUAL runner output.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved yvvf98 --by-human --message ...`) before execution, and its `Item-Dependencies: executed:4r0qp1` refuses dispatch until child 01 is executed. Do NOT hand-write a `Readiness:` field (`IPD-M107`). On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
