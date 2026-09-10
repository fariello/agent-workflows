# IPD: Untrack the four generated index manifests and reconcile stale-index semantics

- Date: 2026-09-06
- Kind: child
- Concern: The four generated manifests are still TRACKED at HEAD `7f80180e` (`git ls-files` lists `.aw/records/plans/INDEX.json`, `plans/INDEX.md`, `research/INDEX.json`, `research/INDEX.md`; `git check-ignore` reports none of them ignored). They are byte-deterministically regenerated from the artifact files, so every diff is derived, and the churn is measured: 328 commits in 14 days on `plans/INDEX.json` alone (item `ila6vl`), and 58 commits in the 4 days to 2026-09-06 touching the two JSON manifests. It stopped being only a churn tax on 2026-09-06, when a conflict in `plans/INDEX.json` was the SOLE reason lane `ueg5cf`'s merge-back aborted in run `run-20260906T162533Z-1552446`, stranding 2477 lines of correct, tested code and cascading two further Set items into `dependency-blocked`. `git merge-tree` confirmed the real code auto-merged cleanly. A tracked auto-regenerated file conflicts on any concurrent lane BY CONSTRUCTION.
- Scope: The tree state, the mechanism that reproduces it in every managed repo, and the statements about it. IN: adding the four paths to the framework-owned `.aw/.gitignore`; `git rm --cached` them in the SAME commit; extending the INSTALLER's `.aw/.gitignore` template and its back-fill list so a fresh install and every already-managed repo inherit the ignore (F-7, carried from child 01's review as PR-008); registering `stale-index` in `check_engine.RULE_REGISTRY` and splitting MISSING from PRESENT-BUT-STALE at the two emitters; reconciling the doctor consumers; correcting the FOUR documents that assert or imply the manifests are committed (the three named plus the shipped installer TEMPLATE, F-8). OUT: the commit-path-set removal (child 01, a declared dependency); any change to `aw index` regeneration itself; the broader repo-local-untracked question (backlog `hsixiz`).
- Scope-Paths: .aw/.gitignore, .aw/records/plans/INDEX.json, .aw/records/plans/INDEX.md, .aw/records/research/INDEX.json, .aw/records/research/INDEX.md, agent_workflows/plans_index.py, agent_workflows/research_index.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, agent_workflows/engine.py, .aw/records/plans/README.md, .aw/records/research/README.md, CONTRIBUTING.md, .aw/system/workflows/templates/agents-docs-research-README.md, tests/test_plans_index.py, tests/test_research_index.py, tests/test_doctor_remediations.py, tests/test_engine_install.py
- Item-Dependencies: executed:4r0qp1
- Status: executed
- Readiness: go-pending-approval
- Set: idxuntrack
- Order: 2
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: ila6vl
- Id: yvvf98

## Workflow history
- 2026-09-10 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Completed the deferred untracking half: E-01/E-04/E-05/E-06 performed, V-01/V-04/V-05/V-06 verified with pasted evidence, V-07's declared PARTIAL closed. Manifests now gitignored here and in the installer for every managed repo. Lane suite 5930 passed, 3 skipped, 2 xfailed, 0 failed. [Scope reconciliation - out-of-scope .pre-commit-config.yaml: NOT THIS EXECUTION. Another agent's commit bcd9755f (29wvmj, executed-transition gate fix), false-attributed by the documented commit-cohesion heuristic because that commit also touched CONTRIBUTING.md, which this plan declares. Verified via git log: this lane never touched the file.; out-of-scope agent_workflows/hooks/executed_transition_gate.py: NOT THIS EXECUTION. Same commit bcd9755f (29wvmj) as above, attributed only through its co-located CONTRIBUTING.md edit. This lane's three commits (6d828fdf, 38023f17, 0bc46618) do not touch it.; out-of-scope agent_workflows/research_contract.py: NOT THIS EXECUTION. Another agent's commit 6f628533 (awmetastore research adoption), which also regenerated records/research/INDEX.{json,md} that this plan declares, hence the cohesion match. Untouched by this lane.; out-of-scope tests/test_ci_check_parity.py: THIS PLAN's work, but from the EARLIER 2026-09-08 turn (commit 338a4db4, E-08), not from today's commits. It is genuinely in scope for the plan and was omitted from Scope-Paths at authoring time; E-08 names it explicitly as one of the four real test surfaces the rule rename breaks.; out-of-scope tests/test_executed_transition_gate.py: NOT THIS EXECUTION. Commit bcd9755f (29wvmj) again, the test file accompanying that hook fix.; out-of-scope tests/test_orchestrator_retirement.py: NOT THIS EXECUTION. Another agent's commit 31169afd (orchretire re-measurement); cohesion-matched because an earlier commit in the same range, 674f2c68, was idxuntrack child 01's own work on declared paths. Untouched by this lane.; out-of-scope tests/test_research_contract.py: NOT THIS EXECUTION. Commit 6f628533 (awmetastore) again, the test file accompanying that research-contract change.]
- 2026-09-09 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): completed the DEFERRED half. E-01/E-04/E-05/E-06 performed and V-01/V-04/V-05/V-06 verified with pasted evidence, plus a mutation check whose four failing guards include the outcome assertion, and both halves of the merge demonstration matching the review's measurement. The blocking dependency was re-verified PER SYMBOL rather than from its status field: `ipd_lifecycle.py:2591` is now `owned_paths = [plan_rel, dest_rel]`, `git_commit_helper` carries the check-ignore guard, `status_set._index_paths_for_types` is gone, so the measured hazard behind DEFERRED 02-yvvf98-Q1 no longer exists. Also CLOSED V-07's declared PARTIAL (606 plans / 110 research docs scanned while the manifests are genuinely gitignored, so they do not regenerate empty). Three commits on lane `aw/lane/yvvf98`: `6d828fdf` (E-01), `38023f17` (E-06 + the E-05 guard test), `0bc46618` (E-04). Full bare suite in the lane: 5930 passed, 3 skipped, 2 xfailed, 0 failed. Two new records: DECISION 02-yvvf98-D4 (a path-scoped commit silently undoes `git rm --cached`) and DECISION 02-yvvf98-D5 (the merge-back needs the dirty primary-checkout manifests discarded first, or the merge aborts).
- 2026-09-08 partially executed (opencode/its_direct/pt3-claude-opus-5-1m-us, run run-20260908T030809Z-1812970): E-02/E-03/E-07/E-08 performed and V-02/V-03/V-07/V-08 verified with pasted evidence and two mutation checks (commit `338a4db4` on lane `aw/lane/yvvf98`). E-01/E-04/E-05/E-06 and V-01/V-04/V-05/V-06 DEFERRED: the declared `Item-Dependencies: executed:4r0qp1` is UNMET (child 01 is still `pending`, its work unmerged on `aw/lane/4r0qp1`, its code verifiably absent from this base). Untracking on this base would point `ipd_lifecycle.finalize`'s `owned_paths` at gitignored paths; reproduced that `offer_commit` returns `error` with NO commit for a path-set containing an ignored path, losing the artifact's own commit. Plan stays in `pending/` and is NOT executed. Two deviations recorded: severity had to be stamped at the emitter (registration alone left absence failing the gate) and the doctor's remediation title had to stop conflating the two split cases. See DECISION 02-yvvf98-D1..D3 and DEFERRED 02-yvvf98-Q1..Q2.
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

- [x] E-01 Add the four manifest paths to the FRAMEWORK-OWNED `.aw/.gitignore` (never the user's root `.gitignore`), and `git rm --cached` all four in the SAME commit. Follow the existing precedent in that file, where `system/layout.json` and `system/layout.schema.json` are ignored with an explicit comment that tracking generated output is the drift the design exists to avoid; write a comparable comment naming byte-deterministic regeneration and the `ueg5cf` incident. Paths are relative to `.aw/`, so they are `records/plans/INDEX.json` and siblings. The same-commit requirement is not stylistic: a concurrent agent's `aw index` auto-refresh will re-stage them between two commits and the change will look like it did not take.
  - Depends on: none
  - Expected outcome: `git ls-files` lists none of the four; `git check-ignore` reports all four ignored; the four files still exist on disk unchanged.
  - Execution state: performed
  - Execution note: performed 2026-09-09 in commit `6d828fdf` on lane `aw/lane/yvvf98`, after the dependency cleared. Dependency re-verified PER SYMBOL rather than trusting the status field: `ipd_lifecycle.py:2591` now reads `owned_paths = [plan_rel, dest_rel]` (the two manifest entries child 01 removed), `git_commit_helper` carries the `check-ignore` guard (`grep -c` -> 2, was 0), and `status_set._index_paths_for_types` no longer exists (`grep -c` -> 0). The measured hazard in DEFERRED 02-yvvf98-Q1 is therefore gone. ONE DEVIATION IN COMMIT MECHANICS, recorded because it silently defeats this specific E-item (DECISION 02-yvvf98-D4): a path-scoped `git commit -- <paths>` RE-READS each path from the working tree, so it re-added all four manifests and undid the `git rm --cached`, producing a commit touching only `.gitignore` (measured: first attempt `16206fce`, 1 file instead of 5). Redone as a bare `git commit` over an index verified to hold exactly the five intended paths.

- [x] E-06 Extend the INSTALLER so the ignore reaches every managed repo, not just this checkout (F-7; carried from child 01's review as PR-008). Two edits in `engine.py`, both required because they serve different populations: add the four `records/.../INDEX.{json,md}` patterns to `_AW_GITIGNORE_TEMPLATE` (`:4274-4308`), which a FRESH install writes verbatim; and add them to the `_ensure_aw_gitignore` back-fill list (`:5323-5370`), which is the only path that reaches an ALREADY-INSTALLED repo. Follow the existing `system/layout.json` pattern for both, and use the same anchored-literal discipline the `/inbox/` comment in that file warns about: write the four specific paths, never a bare `INDEX.json` that would match at any depth. Note the template and this repo's `.aw/.gitignore` are byte-identical today (verified), so E-01 and this item must produce the SAME four lines or the next install will diff against the repo.
  - Depends on: E-01
  - Expected outcome: a fresh `aw install` into a clean repo gitignores all four paths; re-running the installer on a repo that predates this change back-fills them; the template and this repo's file agree.
  - Execution state: performed
  - Execution note: performed 2026-09-09 in commit `38023f17`. Both edits made in `engine.py`: the four patterns added to `_AW_GITIGNORE_TEMPLATE` (fresh installs) and to the `_ensure_aw_gitignore` back-fill list (already-installed repos), the latter line-anchored with `re.escape` exactly as the adjacent `system/layout.*` loop does. The four lines are byte-identical to E-01's, so `engine._AW_GITIGNORE_TEMPLATE == Path('.aw/.gitignore').read_text()` still returns `True`.

### Task group 2: reconcile the consumers of the now-changed guarantee

- [x] E-02 Register `stale-index` in `check_engine.RULE_REGISTRY` and split MISSING from PRESENT-BUT-STALE at the two emitters. The mechanism is settled by an almost exact precedent, so implement it rather than re-deriving it (see OQ-01, resolved): `stale-index` is currently UNREGISTERED, so `rule_spec` returns `_DEFAULT_RULESPEC` with `severity="error"` (verified live), and `artifact_core.drift_exit_code:405-415` fails the gate for anything not `info`. Emit TWO distinct rules from `plans_index.py:281-291` and `research_index.py:467-475`, replacing the single conflated "INDEX.json is missing or out of date": a MISSING case and a STALE case, each with its own registry entry and its own message. Follow `check.system-layout-missing`/`check.system-layout-drift` (`check_engine.py:294-309`), which solved the identical problem for the gitignored `layout.json`: a generated, gitignored artifact whose absence must not fail a fresh clone. Copy its two design choices explicitly: the `warning`-not-`error` reasoning (the artifact is GENERATED and the remedy is mechanical, so the CLASS differs even where loudness does not), and if you make absence non-failing you MUST use `info`, because `warning` still exits nonzero. Keep both messages naming `aw index <type>` as the fix.
  - Depends on: E-01
  - Expected outcome: a fresh clone with no manifest does not fail the gate; a present-but-stale manifest still does; both rules are REGISTERED rather than falling through to the conservative default; both messages name the fix.
  - Execution state: performed

- [x] E-03 Reconcile the `doctor.py` consumers with E-02's new rule ids. All five sites match on the SUBSTRING `"stale-index"` (`:859` remediation, `:938` comment, `:1049` priority comment, `:1382` and `:1460` count predicates), so if E-02's new ids both CONTAIN that substring they keep matching unchanged, and if they do not, all five break silently. Decide which and state it: prefer ids that preserve the substring (e.g. `stale-index-missing` / `stale-index-stale`) so the existing matching holds, and verify rather than assume. Then confirm the count predicates at `:1382`/`:1460` do not report an expected fresh-clone absence as a finding, and that the remediation hint (`aw index <type>`) is produced for BOTH cases.
  - Depends on: E-02
  - Expected outcome: `aw doctor` reports a missing manifest as non-failing and a stale one as actionable, with the `aw index` hint intact in both and no silently-broken substring match.
  - Execution state: performed

- [x] E-07 Reconcile the OTHER consumer of the same emitters, which the authored plan missed (F-9): `check_engine.check_content` calls `plans_index.check_drift` (`:629`) and `research_index.check_drift` (`:727`), so E-02's new rules flow into `aw check plans`/`aw check research`/`aw check all`, not only into `aw index --check` and `aw doctor`. Verify the two new rule ids are enriched correctly through `enrich_drift` (`:322-343`) and that `aw check` behaves as intended for both cases. Also confirm the regeneration scan is unaffected: the manifests are excluded from `_scan_plans`/`_scan_docs` by NAME (`plans_index._EXCLUDE_NAMES:49`, `research_index:74`) BEFORE `is_ignored_path` is consulted, which is why gitignoring them does not make the generator skip its own inputs. State that as verified, because if it were false the manifests would regenerate empty.
  - Depends on: E-02
  - Expected outcome: `aw check plans` and `aw check research` report the missing and stale cases with the intended severities, and the generator still sees every artifact.
  - Execution state: performed

- [x] E-04 Correct the FOUR documents that assert or imply the manifests are committed. Three are the ones already named: `.aw/records/plans/README.md:85-96`, `.aw/records/research/README.md:48-50`, `CONTRIBUTING.md:52-56`. The fourth is the shipped INSTALLER TEMPLATE `.aw/system/workflows/templates/agents-docs-research-README.md:50` (F-8), which carries the same sentence verbatim ("both are COMMITTED so a fresh clone and a weak agent have them without running the tool") and is written into every managed repo by `engine.ensure_docs_readmes` (`:5134-5175`); leaving it would re-seed the false claim into every new install. Note the research README's claim is the strongest of the four: it states the reason for committing them, so it needs rewriting rather than a caveat. State plainly that they are generated, gitignored, local views, regenerated with `aw index <type>`, and absent in a fresh clone until generated. Record the three accepted losses the maintainer already accepted: no manifest in a fresh clone, no `INDEX.md` browsing on a git host, no manifest diffs in review. Also record the two consequences this review measured, because a reader will otherwise hit them as surprises: a NEW WORKTREE has no manifest until `aw index` runs there (measured: `git worktree add` produced no manifest), and switching branches no longer changes the manifest (it is now one local file shared across branches). Write no em or en dashes in this user-facing prose.
  - Depends on: E-01
  - Expected outcome: no in-repo document and no shipped template tells a reader the manifests are committed; the worktree and branch-switch consequences are stated.
  - Execution state: performed
  - Execution note: performed 2026-09-09 in commit `0bc46618`. All four documents corrected, with the research README rewritten rather than caveated as the item requires (it stated the REASON for committing). The three accepted losses and the two measured F-12 consequences are stated in each. Em/en dash check run on the diff's added lines only: none.

- [x] E-05 Prove the end-to-end outcome the item exists for, and pin it. Add a test asserting the four paths are gitignored and untracked so a future change cannot silently re-track them; follow the EXISTING precedent `tests/test_engine_install.py` (its `IGNORE_PATTERNS` + `check-ignore` helpers already do exactly this for `layout.json`, including a template-carries-the-pattern test and a fresh-install test) rather than writing a new harness. Then demonstrate the motivating failure is fixed. This review already measured it, so the expected result is known and the executor is confirming, not exploring: with the manifest TRACKED, two branches whose only differing path is the manifest produce `CONFLICT (content)` and the merge fails; with it UNTRACKED and `git rm --cached`ed on both branches, the same merge succeeds ("Merge made by the 'ort' strategy", only `code.py` in the stat) and the manifest survives on disk. Reproduce both halves and paste them. If the untracked half still conflicts, that is a DIFFERENT outcome than measured and must be reported, not explained away.
  - Depends on: E-01, E-02, E-03, E-04, E-06, E-07
  - Expected outcome: a durable guard against re-tracking that reuses the layout.json test precedent, plus a pasted before/after merge demonstration.
  - Execution state: performed
  - Execution note: performed 2026-09-09; the guard test landed in commit `38023f17` alongside E-06 (the same file, `tests/test_engine_install.py`, and the guard asserts E-06's installer behavior, so splitting them would have committed a test of unlanded code). `ManifestIndexGitignoreTests` mirrors the adjacent `LayoutArtifactsGitignoreTests` as instructed rather than adding a harness. Both halves of the merge demonstration reproduced in scratch repos and pasted under V-05; the outcome MATCHED the review's measurement in both directions.

- [x] E-08 Retarget the test surfaces this change actually breaks, which the authored plan mis-scoped (F-10). `tests/test_doctor.py` contains ZERO `stale-index` references (verified: `grep -c` returns 0), so it is the wrong file and must be removed from scope. The real surfaces are: `tests/test_plans_index.py:233-237` and `tests/test_research_index.py:203-207`, which assert `d.rule == "stale-index"` EXACTLY and will fail the moment E-02 renames the rule; `tests/test_doctor_remediations.py:54-56,231-233`, which construct `Drift(..., "stale-index", ...)` literals; and `tests/test_ci_check_parity.py:92-115`, whose clean-tree case deliberately regenerates the index first with the comment "mirrors the committed state CI runs against", a comment that becomes false. Update each to the new rule ids and semantics, and keep every existing guarantee: do not delete a case to make it pass. Baseline measured at review time on the main checkout for these five modules: 78 passed.
  - Depends on: E-02, E-03, E-07
  - Expected outcome: the four affected test modules pass against the new rule ids, still fail if staleness stops being detected, and `test_ci_check_parity`'s stale comment no longer claims a committed baseline.
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: paste `git ls-files | grep -E 'INDEX\.(json|md)$'` returning EMPTY, `git check-ignore -v` naming `.aw/.gitignore` for all four paths, `ls` proving the four files still exist on disk, and `git show --stat` of the single commit showing the `.gitignore` edit and the four deletions together.
  - Observed evidence: All four required artifacts, in order. `git ls-files` returns EMPTY (grep exits 1, which IS the empty result):

    ```text
    === V-01 (a) ls-files must be EMPTY:
    [exit=1 -> 1 means empty, correct]

    === V-01 (b) check-ignore -v all four:
    .aw/.gitignore:45:records/plans/INDEX.json	.aw/records/plans/INDEX.json
    .aw/.gitignore:46:records/plans/INDEX.md	.aw/records/plans/INDEX.md
    .aw/.gitignore:47:records/research/INDEX.json	.aw/records/research/INDEX.json
    .aw/.gitignore:48:records/research/INDEX.md	.aw/records/research/INDEX.md

    === V-01 (c) files still exist on disk:
    -rw-r--r-- 1 179078 .aw/records/plans/INDEX.json
    -rw-r--r-- 1  10289 .aw/records/plans/INDEX.md
    -rw-r--r-- 1  65051 .aw/records/research/INDEX.json
    -rw-r--r-- 1  15141 .aw/records/research/INDEX.md

    === V-01 (d) single commit, gitignore edit + four deletions together:
    6d828fdf refactor(records): gitignore the four generated INDEX manifests (yvvf98 E-01)
     .aw/.gitignore                  |   14 +
     .aw/records/plans/INDEX.json    | 6062 ---------------------------------------
     .aw/records/plans/INDEX.md      |  204 --
     .aw/records/research/INDEX.json | 2055 -------------
     .aw/records/research/INDEX.md   |   71 -
     5 files changed, 14 insertions(+), 8392 deletions(-)
    ```

    Attribution confirmed to be the FRAMEWORK-OWNED file: every rule resolves to `.aw/.gitignore`, never the user's root `.gitignore`. The four files are unchanged on disk (`git rm --cached` only, never `git rm`).

    THE SAME-COMMIT REQUIREMENT WAS NEARLY LOST, and the mechanism is worth recording because it defeats this E-item silently (DECISION 02-yvvf98-D4). The execution contract's usual `git commit -m msg -- <paths>` RE-READS each named path from the WORKING TREE, so naming the four manifests re-added them and undid the staged `git rm --cached`. The first attempt therefore committed ONE file, not five:

    ```text
    16206fce refactor(records): gitignore the four generated INDEX manifests (yvvf98 E-01)
     .aw/.gitignore | 14 ++++++++++++++
     1 file changed, 14 insertions(+)
    ```

    Caught by checking `git ls-files` immediately after committing (it still listed all four), then redone as `git reset --soft HEAD~1`, re-`git rm --cached`, verify the index holds exactly the five intended paths and nothing else, bare `git commit`. This is the one deliberate exception the plan's own execution contract grants E-01; the index was verified before committing, which is the safeguard path-scoping normally provides.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `aw index plans --check` clean with the manifest present; then move the manifest aside and paste the output AND ITS EXIT CODE proving absence does not fail the gate; then corrupt it and paste the output and exit code proving present-but-stale still does. Three distinct pasted runs with exit codes, since the exit code is the whole point. Plus `python3 -c` output of `check_engine.rule_spec(<new-missing-id>)` and `rule_spec(<new-stale-id>)` showing BOTH are registered with the intended severities and neither falls through to the `error` default.
  - Observed evidence: Three pasted runs with exit codes, run as `python3 -m agent_workflows` (NOT the `aw` shim, which resolves to the INSTALLED package and would not exercise this worktree; that shadowing cost one misleading measurement before it was caught):

    ```text
    === CASE 1: PRESENT and current ===
    plans index --check: clean
    exit=0

    === CASE 2: MISSING -> must NOT fail ===
    INDEX.json: check.stale-index-missing: INDEX.json has not been generated; run 'aw index plans'
    exit=0

    === CASE 3: PRESENT but STALE -> must fail ===
    INDEX.json: check.stale-index-stale: INDEX.json is out of date; run 'aw index plans'
    exit=1
    ```

    Both rules REGISTERED, neither falling through to the conservative `error` default:

    ```text
    check.stale-index-missing -> RuleSpec(severity='info', assurance='repository', determinism='deterministic', invariant='')
       registered? True
    check.stale-index-stale -> RuleSpec(severity='warning', assurance='repository', determinism='deterministic', invariant='')
       registered? True
    ```

    The same three cases isolated in a SCRATCH tree, for BOTH surfaces, so no unrelated repository finding can mask the exit code:

    ```text
    --- research: EMPTY root, no manifest generated (fresh-clone shape)
        check.stale-index-missing severity= 'info'
        check.stale-index-missing severity= 'info'
        drift_exit_code = 0
    --- research: after generation
        findings: [] exit= 0
    --- research: manifest CORRUPTED (present but stale)
        check.stale-index-stale severity= 'warning'
        drift_exit_code = 1
    --- plans: EMPTY root, no manifest generated (fresh-clone shape)
        check.stale-index-missing severity= 'info'
        check.stale-index-missing severity= 'info'
        drift_exit_code = 0
    --- plans: after generation
        findings: [] exit= 0
    --- plans: manifest CORRUPTED (present but stale)
        check.stale-index-stale severity= 'warning'
        drift_exit_code = 1
    ```

    DEVIATION FROM THE PLAN'S STATED MECHANISM, recorded because it changes what E-02 had to do (DECISION 02-yvvf98-D2). Registering the two rules was NOT sufficient: a missing manifest still exited 1. The cause was MEASURED, not inferred: both emitters return RAW `Drift`s and nothing on either consumer path enriches them, so `severity` was `""` and `drift_exit_code` fails on anything that is not `info`:

    ```text
    raw drift from emitter:
      rule= check.stale-index-missing severity= ''
    drift_exit_code(raw)      = 1
    drift_exit_code(enriched) = 0
    ```

    Fixed by stamping severity AT THE EMITTER via `check_engine.enrich_drift` (keeping `RULE_REGISTRY` the single source of severity for every consumer, which is what the plan's own convention note asserts), and by replacing the hardcoded `return 1` in `plans_index.run_index` and `return 1 if drift else 0` in BOTH `research_index.run_index` branches with `_core.drift_exit_code(drift)`. Without that second half the human-readable branch and `--agent` returned DIFFERENT exit codes for the same tree.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `aw doctor` output (and its exit code) for both the missing-manifest and stale-manifest cases, showing the `aw index` hint present in both and the exit code unaffected by a mere absence. ALSO paste a grep of the five `doctor.py` sites proving each still matches the new rule ids (or was updated), since all five match on the substring `"stale-index"` and would break silently otherwise.
  - Observed evidence: `aw doctor` (as `python3 -m agent_workflows doctor`) for both cases, showing the two now-DISTINCT titles with the `aw index` hint intact in each:

    ```text
    === MISSING case: title + hint ===
    doctor exit(missing)=1
        Issue: Manifest index has not been generated yet
        Fix: run 'aw index' to regenerate the manifest index.
      88. Manifest index has not been generated yet (1 file)

    === STALE case: title + hint ===
    doctor exit(stale)=1
        Issue: Manifest index is out of date
        Fix: run 'aw index' to regenerate the manifest index.
      88. Manifest index is out of date (1 file)
    ```

    HONEST LIMIT on that exit code, stated rather than glossed. `aw doctor` exits 1 in BOTH cases, but NOT because of the manifest: this repository already reports 344 unrelated pre-existing findings ("Artifact Integrity & Schema Contracts (344 finding(s))") and exits 1 even with the manifests present and current. So the repo-level exit code CANNOT isolate this change, and the plan's "exit code unaffected by a mere absence" has to be verified on the finding itself:

    ```text
    check.stale-index-missing: severity='info' exit_if_only_finding=0 title='Manifest index has not been generated yet' cmd='aw index plans'
    check.stale-index-stale: severity='warning' exit_if_only_finding=1 title='Manifest index is out of date' cmd='aw index plans'
    ```

    All five `doctor.py` sites still match, because both new ids deliberately CONTAIN the substring `stale-index` (the plan's preferred option, chosen for exactly this reason):

    ```text
    861:    # and both new ids CONTAIN `stale-index`, so this match (and the four other `"stale-index" in
    869:    if "stale-index" in rule or rule.startswith("doctor.index-"):
    1397:        or "stale-index" in d.rule
    1475:        or "stale-index" in d.rule
    ```

    (`:938` and `:1049` are the two COMMENT sites; `:861` is the new explanatory comment.) Remediation resolved for every id form, proving no site broke and the legacy id still resolves:

    ```text
    check.stale-index-missing    -> title='Manifest index has not been generated yet' cmd='aw index plans'
    check.stale-index-stale      -> title='Manifest index is out of date' cmd='aw index plans'
    stale-index                  -> title='Manifest index is missing or out of date' cmd='aw index plans'
    doctor.index-foo             -> title='Manifest index is missing or out of date' cmd='aw index plans'
    ```

    Also verified the count predicates at `:1397`/`:1475` cannot DOUBLE-count: each is a single boolean `or`, so a `check.`-prefixed id containing `stale-index` matches exactly once.

    ONE CHANGE BEYOND THE PLAN'S LITERAL TEXT (DECISION 02-yvvf98-D3): the remediation TITLE was "Manifest index is missing or out of date", which re-conflated precisely what E-02 split. E-03's expected outcome requires the doctor to report the two cases distinguishably, so the title now branches while the remedy command stays shared.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the changed passages from all FOUR documents including the installer template, plus a grep over the repo proving no remaining statement (in a document OR a shipped template) implies the manifests are committed. Show the worktree and branch-switch consequences are stated. Confirm no em or en dashes were introduced.
  - Observed evidence: The FALSE SENTENCE that propagated is gone from both copies. Before, present verbatim in `.aw/records/research/README.md:50` AND in the shipped template `.aw/system/workflows/templates/agents-docs-research-README.md:50`:

    ```text
    frontmatter; both are COMMITTED so a fresh clone and a weak agent have them without running the tool.
    ```

    After (both files, identical replacement, since `ensure_docs_readmes` writes the template into every managed repo and the two must not diverge):

    ```text
    frontmatter. Both are GENERATED, GITIGNORED, LOCAL views: they are not committed, they are absent in a
    fresh clone until you generate them, and you refresh them with `aw research index`. A missing manifest
    is therefore a normal state, reported at `info` severity by `check.stale-index-missing` rather than
    failing a check; a manifest that is present but out of date is a real finding
    (`check.stale-index-stale`).
    ...
    Three consequences were accepted deliberately when this changed. A fresh clone has no manifest until
    you run the tool. `INDEX.md` can no longer be browsed on a git host. Manifest diffs no longer appear
    in review. Two more will surprise you if nobody says them: a NEW WORKTREE contains no manifest until
    `aw research index` runs there, and switching branches no longer changes the manifest, because it is
    now one local file shared across every branch.
    ```

    `.aw/records/plans/README.md`, added to the manifest section:

    ```text
    - Both manifests are GENERATED, GITIGNORED, LOCAL views. They are not committed, a fresh clone has
      none until you generate them, and you refresh them with `aw index plans`. A MISSING manifest is a
      normal state, reported at `info` severity (`check.stale-index-missing`) rather than failing a check;
      a manifest that is PRESENT but out of date is a real finding (`check.stale-index-stale`).
      ... Accepted losses, decided deliberately: no manifest in a fresh clone, no `INDEX.md` browsing on a
      git host, no manifest diffs in review. Two consequences worth stating so they do not surprise you: a
      NEW WORKTREE has no manifest until `aw index plans` runs there, and switching branches no longer
      changes the manifest, since it is now one local file shared across every branch.
    ```

    `CONTRIBUTING.md`, in the "Regenerating Derivative Artifacts" list:

    ```text
    - **Plans Manifest (`.aw/records/plans/INDEX.json`, `INDEX.md`)**: `aw index plans`. GENERATED,
      GITIGNORED, LOCAL: not committed, absent in a fresh clone until you generate it, and absent in a new
      worktree until you generate it there. A missing manifest is reported at `info` severity, not as a
      failure; a present-but-stale one is a real finding.
    - **Research Manifest (`.aw/records/research/INDEX.json`, `INDEX.md`)**: `aw research index`. Same
      regime: generated, gitignored, local, never committed.
    ```

    Repo-wide grep for any REMAINING claim that the manifests are committed. Every surviving hit is a historical RECORD, not a live instruction, and each is correctly left alone:

    ```text
    walkthroughs/...hey7r7-execution.walkthrough.md:22  - a 2026-08-23 commit message, immutable history
    reviews/...ueg5cf...review.md:73                    - describes owned_paths BEFORE child 01 changed it
    specs/20260730-2152-01-...spec.md:237               - OQ3's original ASSUMPTION, explicitly "To confirm"
    backlog/done/...vvc7c1...md:54                      - closed item's own finding text
    backlog/blocked/...adgtqb...md                      - the item tracking THIS half-landed Set
    backlog/graduated/...ila6vl...md                     - the parent item, recording the decision itself
    ```

    NO PROSE DOCUMENT AND NO SHIPPED TEMPLATE now tells a reader the manifests are committed: the four E-04 files were the only live claims, and `ARCHITECTURE.md:63` / `README.md:331` were checked and merely NAME the files in a directory tree without asserting trackedness, so they needed no edit.

    ONE DELIBERATE NON-EDIT, stated rather than silently skipped: spec `20260730-2152-01` OQ3 records the ORIGINAL assumption ("commit `INDEX.json` and `INDEX.md` ... To confirm") in an open-questions section of an `implemented` spec. It is the historical question this plan ANSWERS, not a live contract claim, and rewriting a resolved open question would erase the record of what was asked. This plan's spec-sync section already rules no spec change is needed here.

    Em/en dash check on the ADDED lines of all four documents:

    ```text
    $ git diff -- <the four docs> | grep '^+' | grep -nP '[\x{2014}\x{2013}]'
    no em/en dashes in added lines
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new guard test passing, AND a mutation check (re-track one manifest, show the guard FAILS, revert, show it passes). Plus BOTH halves of the merge demonstration: the tracked case showing `CONFLICT (content)` and a failed merge, and the untracked case showing the merge succeeding with only the real code file in the stat and the manifest still present on disk. State the observed outcome honestly; if the untracked half conflicts, report it rather than explaining it away.
  - Observed evidence: The new guard class passing, then the whole module (10 new + 18 pre-existing, nothing weakened or deleted):

    ```text
    $ python3 -m pytest tests/test_engine_install.py -o addopts="" -q -k ManifestIndex
    ..........                                                               [100%]
    10 passed, 18 deselected in 14.16s

    $ python3 -m pytest tests/test_engine_install.py -o addopts="" -q
    ............................                                             [100%]
    28 passed in 42.68s
    ```

    MUTATION CHECK, the re-tracking regression this guard exists to catch: one manifest pattern dropped from `_AW_GITIGNORE_TEMPLATE`, exactly as a careless future edit would. FOUR independent guards fail, including the OUTCOME assertion rather than only the pattern-presence ones:

    ```text
    mutation applied: dropped records/plans/INDEX.json from _AW_GITIGNORE_TEMPLATE
    E    AssertionError: '\nrecords/plans/INDEX.json\n' not found in "# agent-workflows: ...
    tests/test_engine_install.py:468: AssertionError
    FAILED tests/test_engine_install.py::ManifestIndexGitignoreTests::test_fresh_install_ignores_all_four_manifests
    FAILED tests/test_engine_install.py::ManifestIndexGitignoreTests::test_template_and_this_repos_own_gitignore_agree
    FAILED tests/test_engine_install.py::ManifestIndexGitignoreTests::test_manifests_are_untracked_after_install
    FAILED tests/test_engine_install.py::ManifestIndexGitignoreTests::test_template_carries_all_four_patterns
    4 failed, 6 passed, 18 deselected in 17.34s
    === RESTORE ===
    10 passed, 18 deselected in 19.35s
    ```

    `test_manifests_are_untracked_after_install` failing is the important one: it asserts on `git ls-files` after a real `git add -A`, so the guard pins the OUTCOME (nothing tracked) and not merely the presence of a string in a template.

    MERGE DEMONSTRATION HALF 1, manifest TRACKED, two branches whose only differing path is the manifest. Matches the review's measurement exactly:

    ```text
    === HALF 1: manifest TRACKED.
    --- git merge lane-a:
    Auto-merging sub/INDEX.json
    CONFLICT (content): Merge conflict in sub/INDEX.json
    Automatic merge failed; fix conflicts and then commit the result.
    merge exit=1
    --- status:
    M  code.py
    UU sub/INDEX.json
    ```

    The real code file merged CLEANLY (`M code.py`) while the generated manifest alone (`UU`) failed the merge. That is the `ueg5cf` failure reproduced in miniature.

    MERGE DEMONSTRATION HALF 2, same scenario with the manifest gitignored and `git rm --cached`ed (the E-01 change), and with genuinely DIVERGED branches so a real merge is exercised rather than a fast-forward:

    ```text
    --- diverged; manifest differs on disk from lane's regeneration; merge:
    Merge made by the 'ort' strategy.
     code.py | 2 +-
     1 file changed, 1 insertion(+), 1 deletion(-)
    merge exit=0
    --- merge stat (only the real code file expected):
    3a67796 Merge branch 'lane-a'
     code.py | 2 +-
     1 file changed, 1 insertion(+), 1 deletion(-)
    --- manifest survives on disk:
    {"n":2}
    --- tracked set:
    .gitignore code.py other.py
    ```

    Observed outcome MATCHES the review's measurement in both directions: `Merge made by the 'ort' strategy`, only `code.py` in the stat, the manifest still present on disk with the local regeneration intact, and absent from the tracked set. The untracked half did NOT conflict.

    ONE FALSE START, recorded because it would have made the half-2 evidence vacuous: the first attempt produced `Fast-forward` rather than a merge, because main had no commit of its own. A fast-forward proves nothing about conflict resolution, so the scenario was rebuilt with a divergent commit on main. Pasted above is the divergent run.

    A THIRD, UNPLANNED MEASUREMENT that the executor of the merge-back needs, found while building half 2 and not predicted by the plan: a merge that DELETES a tracked path ABORTS if that path is dirty in the receiving tree.

    ```text
    error: Your local changes to the following files would be overwritten by merge:
    	sub/INDEX.json
    Please commit your changes or stash them before you merge.
    Aborting
    ```

    This matters concretely here: `.aw/records/plans/INDEX.{json,md}` are DIRTY in the primary checkout right now (a co-worker's `aw index` refresh), and this lane's E-01 commit deletes them. So merging this lane requires discarding the local manifest modification first, which is safe precisely because the file is generated and gitignored afterwards, but it is not automatic and a naive merge attempt will simply abort.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste a FRESH install into a scratch repo showing all four paths gitignored afterwards (`git check-ignore -v` naming the installed `.aw/.gitignore`), AND a back-fill exercise: a scratch repo carrying a pre-change `.aw/.gitignore`, re-run the installer, show the four patterns appended without clobbering the existing content. Plus a byte-comparison proving `engine._AW_GITIGNORE_TEMPLATE` and this repo's `.aw/.gitignore` still agree after E-01 and E-06.
  - Observed evidence: FRESH INSTALL into a scratch git repo, driven through the shared `engine.install_into_repo` chokepoint (the same one every entry point reaches), then the four manifests materialized as `aw index` would create them:

    ```text
    install target_layout: aw
    --- git check-ignore -v (must name the INSTALLED .aw/.gitignore):
    .aw/.gitignore:45:records/plans/INDEX.json	.aw/records/plans/INDEX.json
    .aw/.gitignore:46:records/plans/INDEX.md	.aw/records/plans/INDEX.md
    .aw/.gitignore:47:records/research/INDEX.json	.aw/records/research/INDEX.json
    .aw/.gitignore:48:records/research/INDEX.md	.aw/records/research/INDEX.md
    --- git status --porcelain (must show no INDEX):
    0
    [0 = none visible]
    ```

    BACK-FILL EXERCISE, which is the ONLY path that reaches an already-installed repo and the one a template-only edit silently fails. The scratch repo was regressed to a pre-change `.aw/.gitignore` (four manifest lines removed) plus a sentinel user line, so a clobber would be visible:

    ```text
    pre-change .aw/.gitignore restored; four manifest lines removed; sentinel line added
    --- BEFORE back-fill, are they ignored?
    NOT ignored (correct: pre-change state)
    --- run the back-fill:
    back-fill done
    --- AFTER back-fill, check-ignore -v:
    .aw/.gitignore:46:records/plans/INDEX.json	.aw/records/plans/INDEX.json
    .aw/.gitignore:47:records/plans/INDEX.md	.aw/records/plans/INDEX.md
    .aw/.gitignore:48:records/research/INDEX.json	.aw/records/research/INDEX.json
    .aw/.gitignore:49:records/research/INDEX.md	.aw/records/research/INDEX.md
    --- pre-existing content preserved (no clobber)?
    1        <- the sentinel `my-own-preexisting-line` survived
    1        <- `records/*/untracked/` survived
    --- exactly one copy of each appended pattern?
    records/plans/INDEX.json -> 1
    records/plans/INDEX.md -> 1
    records/research/INDEX.json -> 1
    records/research/INDEX.md -> 1
    ```

    Note the line numbers differ between the two exercises (45-48 fresh, 46-49 back-filled) because the back-fill APPENDS after the sentinel line. That is the expected difference between writing the template verbatim and appending to an existing file, and it is why both paths had to be exercised separately.

    BYTE-COMPARISON after both E-01 and E-06, which is the F-7 precondition (if these diverged, the next `aw install` would re-diff this repo against its own template):

    ```text
    template == repo .aw/.gitignore: True
    ```

    Idempotence and no-duplication are additionally pinned by test rather than by this one-shot run: `test_backfill_is_idempotent` (3 repeated calls) and `test_reinstall_does_not_duplicate_the_patterns` both pass, and `test_tracked_comms_inbox_lane_is_still_not_ignored` plus the new `test_unrelated_index_json_at_another_depth_is_not_ignored` fence the anchoring so `docs/INDEX.json` stays visible to git.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `aw check plans` and `aw check research` output plus exit codes for both the missing and stale cases, showing the intended severities flow through `enrich_drift`. Plus proof the generator is unaffected: paste `aw index plans` regenerating a manifest with the full plan count while the manifest itself is gitignored, demonstrating the name-exclusion still admits every artifact.
  - Observed evidence: The new rules flow through `check_engine.check_content`, which is the `aw check plans` / `aw check research` / `aw check all` path (`:629`, `:727`), with severity and recovery correctly enriched. The manifest finding's own exit contribution is isolated from the repository's unrelated findings:

    ```text
    PRESENT+current:
        check.stale-index-stale severity= 'warning' recovery= 'aw index plans'
        stale-index-only exit_code = 1
    MISSING:
        check.stale-index-missing severity= 'info' recovery= 'aw index plans'
        stale-index-only exit_code = 0
    STALE:
        check.stale-index-stale severity= 'warning' recovery= 'aw index plans'
        stale-index-only exit_code = 1
    ```

    The "PRESENT+current" row reporting `stale` is NOT a defect in this change: the manifest COMMITTED at base `9b413533` is genuinely stale against a rebuild, which is live confirmation of this plan's own churn thesis. Recorded as DEFERRED 02-yvvf98-Q2; I left the tracked file byte-identical rather than adding one more manifest commit to a contended file.

    Generator UNAFFECTED, which the plan asks to be stated as verified because the manifests would regenerate EMPTY if it were false. Exclusion is by NAME (`_EXCLUDE_NAMES`), applied BEFORE `is_ignored_path` is consulted:

    ```text
    plans entries scanned: 557
    research entries scanned: 105
    plans _EXCLUDE_NAMES: ['INDEX.json', 'INDEX.md', 'README.md', 'STATUS.md']
    ```

    PARTIAL AT THE TIME OF THE 2026-09-08 TURN, and the gap is named rather than papered over: the plan asks for this count "while the manifest itself is gitignored". The manifests were NOT yet gitignored because E-01 was deferred (DEFERRED 02-yvvf98-Q1). What was proven then is that the exclusion is by name and therefore INDEPENDENT of ignore state, which is the property that makes gitignoring safe.

    GAP NOW CLOSED (2026-09-09, after E-01 landed in `6d828fdf`). Re-confirmed exactly as this V-item asked, with the manifests genuinely gitignored this time:

    ```text
    === V-07 re-confirmation: generator counts WHILE the manifests ARE gitignored
    manifests ARE gitignored: yes
    plans entries scanned: 606
    plans _EXCLUDE_NAMES: ['INDEX.json', 'INDEX.md', 'README.md', 'STATUS.md']
    research entries scanned: 110
    generated manifest entry count (NOT empty => name-exclusion still admits every artifact): 606
    ```

    The manifests regenerate with the FULL artifact count while being gitignored, so the name-exclusion running BEFORE `is_ignored_path` is confirmed by measurement and not only by reading. Had that ordering been wrong, these manifests would have regenerated EMPTY, which is the failure this V-item exists to rule out.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the full passing output of `python3 -m pytest tests/test_plans_index.py tests/test_research_index.py tests/test_doctor_remediations.py tests/test_ci_check_parity.py tests/test_engine_install.py -o addopts="" -q`, with the before/after counts stated (78 passed at review baseline for these five modules). Plus a MUTATION CHECK: make a manifest stale, show the retargeted assertion FAILS if staleness detection is removed, then restore. Confirm `tests/test_doctor.py` was dropped from scope and state why.
  - Observed evidence: Full passing output of the five modules:

    ```text
    $ python3 -m pytest tests/test_plans_index.py tests/test_research_index.py tests/test_doctor_remediations.py tests/test_ci_check_parity.py tests/test_engine_install.py -o addopts="" -q
    ........................................................................ [ 81%]
    ................                                                         [100%]
    88 passed in 31.12s
    ```

    Before/after counts: 78 passed at the review baseline for these five modules, re-measured at 78 on THIS worktree before any edit; 88 after. The +10 is 2 new tests (`test_missing_index_is_informational_not_failing`, one per surface) plus 8 subTest cases from the parametrized remediation test. No test was deleted, skipped, or weakened.

    MUTATION CHECK 1, staleness detection removed (a present-but-differing manifest treated as matching). The retargeted assertion FAILS, so it is real evidence rather than a test that cannot fail:

    ```text
    mutation applied
    E       AssertionError: False is not true
    tests/test_plans_index.py:240: AssertionError
    FAILED tests/test_plans_index.py::CheckDriftTests::test_stale_index_flagged
    1 failed, 15 passed in 0.26s
    === RESTORE ===
    16 passed in 0.20s
    ```

    MUTATION CHECK 2, missing-severity reverted from `info` to the failing `warning`. Both new guards FAIL, so the non-failing-absence property (the whole point of the split) is genuinely pinned:

    ```text
    mutation applied
    FAILED tests/test_plans_index.py::CheckDriftTests::test_missing_index_is_informational_not_failing
    FAILED tests/test_research_index.py::CheckDriftTests::test_missing_index_is_informational_not_failing
    2 failed, 39 passed in 0.59s
    === RESTORE ===
    41 passed in 0.55s
    ```

    `tests/test_doctor.py` confirmed DROPPED from scope for the reason F-10 gives, re-verified rather than trusted: `grep -c "stale-index" tests/test_doctor.py` -> `0`. It never referenced this rule, so listing it was an authoring error and not a deliberate widening. I ran it anyway (35 passed alongside `test_ci_check_parity` and `test_engine_install`) to confirm the rename did not reach it indirectly.

    `tests/test_ci_check_parity.py`: the clean-tree comment claiming the index "mirrors the committed state CI runs against" is corrected, since there is no committed baseline to mirror once the manifests are generated local views. `tests/test_engine_install.py` is deliberately UNCHANGED: its `IGNORE_PATTERNS` work belongs to the deferred E-05/E-06.

    WHOLE SUITE, run BARE per the execution contract:

    ```text
    $ python3 -m pytest
    33 failed, 5626 passed, 3 skipped, 2 xfailed in 51.90s
    ```

    Baseline measured in THIS SAME worktree with my changes stashed:

    ```text
    33 failed, 5624 passed, 3 skipped, 2 xfailed in 54.41s
    ```

    Compared by failing NODE ID as the plan requires, not by total: `diff` of the two sorted `FAILED` lists is EMPTY. Zero new failures and zero pre-existing failures accidentally fixed. The 33 are the known environment class: this lane runs with `AW_EXECUTION_ROLE=worker` (which `test_worker_role_refusal` asserts against directly) plus the `agrlvw` run-viewer data class the plan itself predicts.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Size note: 8 E-leaves in 2 groups, within the count thresholds; grown from 5 by the review's re-sweep (installer reach, template document, `aw check` consumer, test retargeting).
- Cohesion rationale: E-01 and E-06 both write the SAME four gitignore lines, to two places that must not diverge (the repo file and the installer template are byte-identical today), so they are deliberately adjacent and sequenced rather than merged: E-01's commit has a hard same-commit constraint with `git rm --cached` that E-06's edit does not share. E-02/E-03/E-07 are one rule definition plus its two consumer surfaces, split because each consumer has its own test surface and failure mode (the doctor's five substring matches, `aw check`'s enrichment path). E-04 and E-08 are single-concern.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit. E-01 is the one deliberate exception to one-concern-per-commit: the `.gitignore` edit and the four `git rm --cached` deletions MUST be a single commit, for the reason E-01 states. When reporting tests passed, paste the ACTUAL runner output.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved yvvf98 --by-human --message ...`) before execution, and its `Item-Dependencies: executed:4r0qp1` refuses dispatch until child 01 is executed. Do NOT hand-write a `Readiness:` field (`IPD-M107`). On completion, transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
