# IPD: a terminal plan's leaked begin receipt must not drive the commit-scope gate

- Date: 2026-08-29
- Kind: child
- Concern: `check_scope_drift` treats ANY begin receipt on disk as an in-flight execution. Four receipts currently belong to plans already in `executed/`, so the shared commit-invariant aggregator reports 72 findings on this checkout, 27 of them from those terminal plans (only TWO of the four contribute; see F2). The opt-in `precommit-scope-gate` hook delegates to that aggregator, so installing it today would refuse every commit by every session in this repo. The SAME rule is also reached by `aw check plans` (F6), so the defect is not confined to the hook.
- Scope: Make `check_scope_drift` ignore a receipt that cannot describe an in-flight execution: one whose plan is in a TERMINAL lifecycle directory, and one whose frozen base is no longer reachable from HEAD. Adds the liveness predicate and its tests only. Does NOT change the ownership/attribution rule (backlog `077yqc`), does NOT install the hook, does NOT touch the receipt-leak source in the runner, and does NOT delete or rewrite any receipt on disk (a terminal plan's receipt can still be transactionally live for finalize resume; see F7).
- Scope-Paths: agent_workflows/check_engine.py, tests/test_check_engine_receipt_liveness.py
- Item-Dependencies: none
- Status: executed
- Set: gatestale
- Order: 1
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: rygds7
- Blocks-Release: next

## Workflow history
- 2026-08-30 executed (opencode its_direct/pt3-claude-opus-5-1m-us): Narrowed check.scope-drift to trust only a LIVE begin receipt: added _receipt_is_live (rejects a plan in a terminal lifecycle dir, reusing plans.TERMINAL, and a base_head not an ancestor of HEAD), failing SAFE with the cost documented; disposition is the first path component so a <disposition>/YYYYMM/ shard still classifies terminal. Measured same-session on BOTH consumer surfaces: check_commit_invariants 222 -> 143 and aw check plans --agent 238 -> 159, terminal plans v58bvy 45 -> 0 and 8zgybk 34 -> 0 with all five in-flight plans unchanged (no over-skip). 18 new tests in their own temp repos, falsifiable in three directions (pre-fix, rule-disabled, parent.name). Existing consumers 31 passed unchanged; fast and full suites show zero net-new failures vs a pre-change baseline measured in the same session (full 19 failed/3239 passed -> 19 failed/3257 passed, +18 = the new tests). No receipt was deleted or rewritten (F7). [Scope reconciliation - in-scope-unmodified agent_workflows/check_engine.py: modified in commit 45f8156, before the receipt refresh; carries E-01/E-02 (_receipt_is_live + _plan_disposition) and E-04 (both docstrings + RULE_REGISTRY comment); in-scope-unmodified tests/test_check_engine_receipt_liveness.py: modified in commit 45f8156, before the receipt refresh; created by E-03 (18 tests, cases a-g)]
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010. Independent review of a plan authored by another session in this same repo. Every material claim was re-measured rather than trusted, and four of the plan's own numbers were wrong. PR-001 (FIXED, HIGH): the headline measurement was stale and mis-attributed - the aggregator reports 72 findings not 74, and only TWO of the four terminal receipts actually emit findings (v58bvy 22, 8zgybk 5); qmt3yk and v7e88a emit ZERO because both are grandfathered, so _frozen_scope_paths returns [] and the PRE-EXISTING empty-allowlist skip already drops them. Crediting them to this fix would have made V-01's evidence literally unachievable. Corrected to 72 -> 45 with the per-plan breakdown. PR-002 (FIXED, HIGH): the plan framed this as hook-only, but check_scope_drift is ALSO reached via check_content(plans) at check_engine.py:471-476, which is what CI runs FAIL-CLOSED at tests.yml:140-142; measured aw check plans --agent exit 1 with 77 findings, 72 of them scope-drift. Added as F6; V-01 now measures both surfaces. PR-003 (FIXED, HIGH): added F7, the finding that BOUNDS the fix - v58bvy is in executed/ while its finalize journal is phase committed-incomplete, the documented resume state that re-runs finalize on a plan already in executed/ (ipd_lifecycle.py:1287-1300), so a terminal plan's receipt is NOT necessarily garbage. The plan is now explicit that terminal-directory licenses ignoring the receipt for scope ADVICE only, and deleting a receipt is forbidden as a correctness constraint rather than as tidiness. PR-004 (FIXED, HIGH): E-01 said to test the plan's directory, which would have been implemented as parent.name and silently broken the first time aw archive plans shards a terminal plan into <disposition>/YYYYMM/ (plans_archive.py:60-61); pinned to the first path component per plans_index.py:99 and added E-03 case (f) plus a falsifiability requirement against the parent.name form. PR-005 (FIXED, MEDIUM): E-01 re-listed the three terminal dir names, a fourth copy of a vocabulary centralized at plans.TERMINAL (plans.py:26) and already reused by plans_archive and ipd_lint; constrained to reuse it (verified no import cycle). PR-006 (FIXED, HIGH): the recorded test baseline could not be met as written - re-measured 2876 passed fast and 4 failed/3203 passed full, and test_run_viewer::test_run_viewer_cli_issues_flag, listed as a known failure, actually PASSES now; replaced with re-measured numbers, a measure-your-own-baseline rule, and the correct 4-failure known-unrelated set. PR-007 (FIXED, MEDIUM): the docstring update was required in Spec/documentation sync but assigned to no E-item, so nothing would have executed it; added E-04 + V-04, extended to the check_commit_invariants docstring which already claimed an ACTIVE receipt the code never verified. PR-008 (FIXED, MEDIUM): resolved OQ-02 from evidence instead of leaving it open - the advisory as conceived would be factually WRONG per F7, so a correct one must read the finalize journal and belongs outside the commit gate. PR-009 (FIXED, MEDIUM): E-03 lacked an aggregator-level case and a no-live-state rule (an active defect class here, i79rgh); added cases (f)/(g) and the isolation requirement. PR-010 (FIXED, LOW): corrected oc_runipd.py:2216 to :2219 and completed the gate's execution contract with the resolved-questions statement and the hard-MUST paste-the-actual-output honesty rule. Verified clean: aw ipd lint conforming at author and review-finalize; E/V bijection 4/4; tests_phase4_hooks + test_event_derived_lifecycle 31 passed unchanged; the simulated fix reproduces the corrected 72 -> 45 exactly.

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): authored after measuring that the SHIPPED `precommit-scope-gate` hook cannot be safely enabled. Scope was deliberately NARROWED at authoring time: the companion contract-wording fix was dropped because plan `uyd3lw` is CURRENTLY EXECUTING with `agent_workflows/engine.py` and `AGENTS.md` in its declared Scope-Paths, and this plan must not touch another in-flight plan's files.

## Goal

Make the scope-drift rule believe only receipts that can still describe work in progress. A begin receipt is execution AUTHORITY for one in-flight plan; once that plan reaches a terminal directory that authority is spent, but the rule still reads the receipt and compares the whole working tree against a frozen base no live execution owns. Fixing this is a precondition for ever enabling the pre-commit hook, the mechanical half of the anti-clobbering protection, and it also removes 27 false findings from `aw check plans`, which CI already runs fail-closed (F6).

Precise about what "spent" means: the receipt may still be needed by an unfinished finalize transaction even when the plan sits in `executed/` (F7). The claim is narrow and deliberate: a terminal plan's receipt must not drive a SCOPE ADVISORY about the current working tree. It is not a claim that the receipt is dead, and nothing here deletes one.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: only trust a live receipt

- [x] E-01 In `agent_workflows/check_engine.py`, add a small pure predicate (e.g. `_receipt_is_live(repo_root, plan_path, receipt)`) that returns False when the receipt cannot describe an in-flight execution, and use it in `check_scope_drift` immediately after the existing `if not receipt: continue` (check_engine.py:985-987). It must reject two cases: (1) TERMINAL PLAN, the plan file resides in a terminal lifecycle directory, determined from the plan's own path rather than by re-parsing status text; (2) UNREACHABLE BASE, `base_head` is not an ancestor of HEAD, so the frozen baseline no longer describes this history. Keep the existing `unversioned`/empty-base skip. Do not change the comparison itself. Two REQUIRED implementation constraints, both derived from repository evidence: (a) reuse the shared terminal vocabulary `plans.TERMINAL` (plans.py:26, the single source of truth, imported without a cycle) rather than re-listing the three directory names, exactly as `plans_archive.TERMINAL_DIRS` and `ipd_lint._is_terminal_dir` already do; (b) derive the disposition as the FIRST path component under the plans dir, not the file's immediate parent, because `aw archive plans` shards a terminal plan into `<disposition>/YYYYMM/` (plans_archive.py:60-61, `_at_disposition_root` :45-47) and a `parent.name` test would silently stop matching a sharded plan (verified: `.aw/records/plans/executed/202608/x.ipd.md` has `parent.name == '202608'`). Reuse `plans_index.scan_plans`'s established derivation (plans_index.py:99 `rel.split("/", 1)[0]`) rather than inventing a third one.
  - Depends on: none
  - Expected outcome: `check_commit_invariants` on this checkout drops from 72 findings to 45, with all 27 findings attributable to terminal plans (`v58bvy` 22, `8zgybk` 5) gone and every in-flight plan's findings unchanged (`58ha43` 31, `7p9n2v` 11, `qcqhj7` 3). A plan in a `<terminal>/YYYYMM/` shard is skipped too.
  - Execution state: performed

- [x] E-02 Make the predicate fail SAFE rather than fail OPEN. If liveness cannot be determined (git unavailable, unreadable path, `merge-base` error), treat the receipt as NOT live and skip it, because a false refusal blocks a legitimate commit while a missed advisory is recoverable, and this gate is explicitly documented as best-effort local FEEDBACK rather than an authority boundary (`hooks/precommit_scope_gate.py:17-19`). Record the choice in a comment citing that docstring so the asymmetry is not later "corrected". State plainly in the same comment what this direction COSTS: an environment where git cannot run silently disables the rule entirely rather than reporting that it could not run, which is acceptable only because the authoritative boundary is CI (`.github/workflows/tests.yml:140-142`) and NOT this local rule.
  - Depends on: E-01
  - Expected outcome: an induced git/OS error in the liveness check yields a skip, not a finding and not a traceback; the aggregator's per-rule exception isolation (check_engine.py:1056-1059) is not relied upon for this path.
  - Execution state: performed

### Task group 2: prove it, in both directions

- [x] E-03 Add `tests/test_check_engine_receipt_liveness.py` covering, in a temp git repo (mirror the existing fixture at `tests/test_event_derived_lifecycle.py:196-241`, including its `.gitignore` for `.aw/state/`, so the new module does not fork a second repo-builder): (a) a receipt whose plan is in `executed/` produces NO scope-drift finding even with an out-of-scope dirty path present; (b) a receipt whose plan is in `pending/` STILL produces the finding for the same dirty path, proving the rule was narrowed and not disabled; (c) a receipt whose `base_head` is not an ancestor of HEAD is skipped; (d) each terminal directory (`executed/`, `superseded/`, `not-executed/`) is rejected and `pending/`/`reusable/` are not; (e) a liveness-check error results in a skip (E-02); (f) a plan in a SHARD (`executed/YYYYMM/`) is also skipped, and a `pending/` plan is not, pinning E-01's first-path-component derivation against the `parent.name` regression; (g) the assertions run through `check_commit_invariants` (the aggregator the hook actually calls) at least once, not only through `check_scope_drift`, so the fix is proven on the surface that gates commits. Each assertion must be shown to FAIL against the pre-fix predicate where applicable. Every test asserts against its OWN temp repo; no test may read the live checkout (an ACTIVE defect class here, `i79rgh` E-01).
  - Depends on: E-01, E-02
  - Expected outcome: the module passes; case (a) FAILS against pre-fix code (that is the bug); case (b) FAILS if the receipt check is removed rather than narrowed; case (f) FAILS against a `parent.name`-based implementation.
  - Execution state: performed

### Task group 3: leave the next reader the reason

- [x] E-04 Update `check_scope_drift`'s docstring (check_engine.py:960-971) to state that only a LIVE receipt is considered and why, and update the `check.scope-drift` line in `check_commit_invariants`'s docstring (check_engine.py:1041-1043), which currently says "for a plan with an ACTIVE begin receipt" while the code accepted any receipt. Both must name the two rejected cases and point at the fail-safe rationale, so the next reader does not restore the old behavior believing it was the intent. The plan already required this docstring work in `## Spec / documentation sync` but assigned it to no `E-*`; this item is that assignment.
  - Depends on: E-01
  - Expected outcome: both docstrings describe the implemented behavior; no code path changes; the `RULE_REGISTRY` comment for `check.scope-drift` (check_engine.py:157-161) is consistent with them.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The gate is already built and is OPT-IN, not installed. `agent_workflows/hooks/precommit_scope_gate.py` delegates to the ONE shared aggregator `check_engine.check_commit_invariants` (check_engine.py:1029), which composes `check_status_untooled`, `check_release_gate_consistency`, and `check_scope_drift`. Verified `.pre-commit-config.yaml` contains no `precommit-scope-gate` entry. So this plan must NOT add a hook; the mechanical layer exists and merely cannot be trusted yet.
- The rule has TWO consumers, not one (F6). Besides the hook, `check_content(repo, "plans")` calls it at check_engine.py:471-476, and that is what `aw check plans --agent` runs, fail-closed in CI at `.github/workflows/tests.yml:140-142`. Both consumers get the fix from the single shared rule, which is the point of the no-fork design; the executor must therefore measure both.
- The defect is a missing liveness test, not a missing feature. `check_scope_drift` (check_engine.py:960) skips only when there is no receipt at all or the base is empty/`unversioned` (check_engine.py:985-991). It never asks whether the plan is still in flight.
- Measured on this checkout: 8 receipts under `.aw/state/ipd-lifecycle/`, of which FOUR (`8zgybk`, `qmt3yk`, `v58bvy`, `v7e88a`) belong to plans already in `executed/`. `check_commit_invariants(".")` returns 72 findings; 27 come from terminal plans (`v58bvy` 22, `8zgybk` 5) and 45 from in-flight ones (`58ha43` 31, `7p9n2v` 11, `qcqhj7` 3). The other two terminal receipts are grandfathered and already skipped (F2). Every receipt's `base_head` is currently an ancestor of HEAD, INCLUDING on both live lane branches (`aw/lane/qcqhj7`, `aw/lane/rchpms`), so the terminal-plan case is the one with live evidence and the unreachable-base case is purely defensive.
- Terminal disposition is the FIRST path component under the plans dir, not the file's parent directory. `aw archive plans` moves a terminal plan into a `<disposition>/YYYYMM/` shard (plans_archive.py:60-61); `plans_index.scan_plans` therefore derives disposition as `rel.split("/", 1)[0]` (plans_index.py:99) and documents that a sharded plan keeps its top-level disposition. An implementation testing the immediate parent would pass today (no shards exist yet: `find .aw/records/plans -mindepth 2 -maxdepth 2 -type d` is empty) and silently regress the first time anything is archived. E-01 pins the correct derivation and E-03 case (f) tests it.
- The shared terminal vocabulary already exists in exactly one place, `plans.TERMINAL` (plans.py:26), and is reused by `plans_archive.TERMINAL_DIRS` (:32) and `ipd_lint._is_terminal_dir` (:940-941). `check_engine` already imports `plans` transitively with no cycle (verified by direct import). Re-listing the three names in `check_engine` would create a fourth copy of a vocabulary this repo deliberately centralizes.
- The leak has a known source, and it is NOT in scope here. `finalize` DOES consume the receipt, but only on the clean-complete path (`receipt_path_for(...).unlink()`, ipd_lifecycle.py:1647-1651). Under worktree isolation the runner COPIES the receipt into the lane (`sync_receipt_into_worktree`, oc_runipd.py:488-494, called at :2219), so an in-lane finalize consumes the LANE's copy and the main-tree original is left behind. `8zgybk` was finalized exactly that way (`f5f733f`), which explains its leaked receipt. Fixing the leak is a runner change in files owned by in-flight plans, so this plan hardens the CONSUMER instead, which is correct regardless: the gate must not trust a stale receipt even if leaks are later eliminated.
- A leaked receipt and a LIVE-but-terminal receipt are different things, and only the second one bounds this fix (F7). `v58bvy`'s receipt survives for a documented transactional reason, not a bug: its finalize journal is `committed-incomplete`, the state whose recovery path re-runs the same finalize against a plan already sitting in `executed/` (ipd_lifecycle.py:1287-1300). That is precisely why this plan hardens a read-only advisory and touches no receipt: the same fact ("plan is in a terminal directory") licenses ignoring the receipt for SCOPE ADVICE while forbidding treating it as garbage. `8zgybk` has no journal at all (its lane-side journal died with the worktree), so the two leaked-receipt cases in this tree have different causes, and neither one licenses deletion.
- Terminal-vs-active is already encoded in the DIRECTORY, per the repository's filesystem-encoded-state principle: `pending/` and `reusable/` are non-terminal; `executed/`, `superseded/`, and `not-executed/` are terminal. Deriving liveness from the path is therefore consistent with how the rest of the toolkit reads disposition, and avoids re-parsing status text that may legitimately lag.
- The hook's own docstring states the honest limit: "git hooks are LOCAL, not cloned by default, and skippable with `--no-verify`. This is OPT-IN best-effort FEEDBACK, not an authority boundary; the authoritative boundary is phase-5 CI running the same engine." That is the basis for E-02's fail-safe direction.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `check_engine.py:985-991` | `check_scope_drift` accepts any receipt with a non-empty base as an in-flight execution. No check that the plan is still active. | source |
| F2 | HIGH | this checkout | 4 of 8 receipts belong to plans in `executed/`; the aggregator reports 72 findings, 27 of them from terminal plans. CORRECTED at review: only TWO of the four terminal receipts actually emit findings (`v58bvy` 22, `8zgybk` 5). `qmt3yk` and `v7e88a` emit ZERO for an unrelated reason: both are `grandfathered`, so `_frozen_scope_paths` returns `[]` and the pre-existing empty-allowlist skip (check_engine.py:991-992) already drops them. Counting them as this fix's beneficiaries would have overstated the fix and made V-01's evidence unachievable. | measured via `check_commit_invariants(Path('.'))`; `_frozen_scope_paths` returns `[]` for both grandfathered plans |
| F3 | HIGH | `hooks/precommit_scope_gate.py` + F2 | Because the hook delegates to that aggregator and fails closed on any finding, installing it today would refuse EVERY commit in this repo, including the live runners'. The mechanical anti-clobbering protection is therefore unusable. | hook `check()` returns exit 1 whenever drift is non-empty (precommit_scope_gate.py:38-51) |
| F4 | MED | `oc_runipd.py:488-494`, `:2219` vs `ipd_lifecycle.py:1647-1651` | The leak source: `finalize` unlinks the receipt it can see, but a lane-side finalize sees only the COPY synced into the worktree, so the main-tree receipt survives. `8zgybk` (`f5f733f`) is an instance. NOTE the call site is `oc_runipd.py:2219`, not `:2216`. | source + the leaked receipt for a plan in `executed/` |
| F5 | MED | `check_engine.py:1041-1043` | The rule reuses `_paths_changed_by_this_execution`, the same helper backlog `077yqc` reports has NO ownership filter. So a stale receipt does not merely produce noise: it attributes ANOTHER agent's uncommitted work to a finished plan. Narrowing liveness reduces the blast radius; it does not fix attribution. Concretely: all 22 `v58bvy` findings are OTHER agents' files (`run_cli.py`, `oc_runipd.py`, `test_run_viewer.py`, ...), none of them `v58bvy`'s. | `077yqc`; helper at ipd_lifecycle.py:791-814; the 22 detail lines, none inside `v58bvy`'s declared Scope-Paths |
| F6 | HIGH | `check_engine.py:471-476`, `.github/workflows/tests.yml:140-142` | ADDED at review. The plan framed this as a hook-only problem, but `check_scope_drift` is ALSO reached through `check_content(repo, "plans")`, which is what `aw check plans --agent` runs, and CI runs that command FAIL-CLOSED. Measured now: `aw check plans --agent` exits 1 with 77 findings, 72 of them `check.scope-drift`. The receipts are gitignored so CI's own checkout is clean today, which is the only reason `main` is green; a repo that ever tracks or reconstructs state would red CI. This widens the fix's value and means V-01 must measure BOTH surfaces. | `python3 -m agent_workflows check plans --agent` -> `"exit":1,"findings":77`; `.aw/state/` ignored at `.gitignore:60` with `git ls-files .aw/state` empty |
| F7 | HIGH | `.aw/state/runtime/transactions/ipd_finalize_v58bvy.json` | ADDED at review, and it CONSTRAINS the fix. A terminal-directory plan's receipt is NOT always garbage: `v58bvy` is in `executed/` AND its finalize journal is `phase: committed-incomplete`, the documented resume state in which the SAME `aw ipd finalize` command must run again (ipd_lifecycle.py:1287-1300) on a plan that already lives in `executed/`. The receipt is consumed only on the clean-complete path (`:1647-1651`). So `terminal directory` proves the receipt must not drive the SCOPE-DRIFT ADVISORY; it does NOT prove the receipt is dead. This is exactly why the fix must harden only the read-only consumer and must not delete receipts, and why E-01 must not be generalized later into "terminal plan implies delete the receipt". | journal `phase == "committed-incomplete"`, `lifecycle_commit bead376`, plan in `executed/`, receipt still present |

## Proposed changes (ordered, validatable)

1. Add the liveness predicate and apply it in `check_scope_drift`, reusing `plans.TERMINAL` and the first-path-component disposition derivation (E-01).
2. Make it fail safe, with the rationale and its cost cited in a comment (E-02).
3. Prove the rule was narrowed rather than disabled, in both directions, on both consumer surfaces, and against the shard regression (E-03).
4. Correct both docstrings so the narrowed contract is the one a reader finds (E-04).

## Deferred / out of scope (with reason)

- The CONTRACT wording fix (naming the shared-index race in the installed agent contract). Its files are `agent_workflows/engine.py` and `AGENTS.md`, which are the declared Scope-Paths of plan `uyd3lw`, CURRENTLY EXECUTING in a live runner. Editing them would collide with an in-flight plan, so this is deferred to its own plan once `uyd3lw` completes. This is the single most important scoping decision in this plan.
- Ownership-aware attribution (backlog `077yqc`, open, release-blocking). Distinct defect: `077yqc` is about WHOSE changes a rule may attribute; this plan is about WHETHER a receipt is still live. Both are needed before the hook is safe to enable; they are independent and separately verifiable.
- Fixing the receipt LEAK in the runner (F4). Its files (`oc_runipd.py`, `ipd_lifecycle.py`) are in the declared Scope-Paths of in-flight plans `y0gg8o`/`af7i6p`/`z2isfg`. Also, hardening the consumer is the more durable fix: the gate must tolerate a stale receipt regardless of how carefully leaks are prevented.
- INSTALLING the `precommit-scope-gate` hook. Explicitly not done here. With `077yqc` unfixed the gate would still misattribute concurrent work, so enabling it now would trade one clobbering failure for another. Installation belongs to a later plan that can demonstrate a clean run on a busy shared checkout.
- Any change to `check_status_untooled` or `check_release_gate_consistency`, the aggregator's other two rules. Neither is receipt-driven and neither contributed to the measured findings (confirmed: all 72 findings carry rule `check.scope-drift`).
- A stale-receipt ADVISORY (OQ-02). Deferred with a resolved rationale rather than left open: it would be wrong as naively conceived, because a terminal plan's receipt can be transactionally live (F7), so a correct advisory must read the finalize journal and belongs outside the commit gate.
- DELETING or rewriting any receipt, and any generalization of E-01 into receipt cleanup. F7 makes this a correctness constraint, not just caution: `v58bvy`'s receipt is required by the documented `committed-incomplete` resume path even though its plan is in `executed/`. This plan's whole claim is that a terminal plan's receipt must not drive the ADVISORY, never that it is garbage.
- Making the rule report that it could not run (the honest alternative to E-02's silent skip). Rejected here because emitting a finding on a git failure would fail the commit closed on an unrelated environment problem, the opposite of this plan's purpose; the cost is instead documented in the comment E-02 requires.

## Scope check

- Over-scope: none. `check_engine.py` carries F1/F2/F5/F6 and the E-04 docstrings; the test module is new and required by E-03. No other file is touched, which is deliberate given the concurrent runners. Note that `check_engine.py` is ALSO in executed plan `v58bvy`'s declared Scope-Paths, but `v58bvy` is terminal, so there is no live ownership conflict; no PENDING plan declares `check_engine.py` (verified by grep across `pending/`), so this plan holds that file uncontested.
- Under-scope: the contract fix, `077yqc`, the runner-side leak, hook installation, and the stale-receipt advisory (OQ-02) are each named under Deferred with the reason and, where relevant, the in-flight plan that owns the files.

## Required tests / validation

- The new `tests/test_check_engine_receipt_liveness.py` must pass, with case (a) shown to FAIL pre-fix, case (b) shown to fail under a naive removal of the receipt check, and case (f) shown to fail against a `parent.name`-based disposition test. All three directions are mandatory: a change that merely stops reporting has deleted a safety property rather than corrected it, and one that works only on unsharded paths is a latent regression.
- `tests/test_phase4_hooks.py` and `tests/test_event_derived_lifecycle.py` are the existing consumers of `check_scope_drift`/`check_commit_invariants` and must pass UNCHANGED. Both were confirmed green at review time (`31 passed`), so any failure there is caused by this change.
- `python3 -m pytest` and `python3 -m pytest -m ""` for the full suite. Invoke them BARE: `-n auto` is already in `addopts` (pyproject.toml:122) and adding a redundant `-n`/`-q` is the specific misuse plan `uyd3lw` exists to stop. RE-MEASURED BASELINE at review time, same session, which SUPERSEDES the authoring numbers: fast subset `2876 passed, 3 skipped, 4 xfailed`; full `4 failed, 3203 passed, 3 skipped, 4 xfailed`. The 4 known-unrelated failures, which must NOT be claimed as caused or fixed, are all undeclared-CLI-parser-leaf failures from concurrent `run_cli` work: `test_command_surface_declarations::test_zero_undeclared_parser_leaves`, `test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, and `test_cli_conformance_matrix::UndeclaredLeafGuardTests` (x2). CORRECTED at review: `tests/test_run_viewer.py::test_run_viewer_cli_issues_flag` was listed as a known failure but PASSES now (`34 passed`); it is live-state-dependent (`i79rgh` owns that fix), so treat it as FLAKY-BY-STATE rather than expected-failing, and if it fails, attribute it there instead of claiming a regression. Because the tree changes under concurrent sessions, RE-MEASURE the baseline in your own session before changing anything and compare against THAT, not against these numbers.
- A measured before/after on this checkout, on BOTH consumer surfaces (F6): `check_commit_invariants(Path("."))` drops from 72 to 45, and `python3 -m agent_workflows check plans --agent` drops its `check.scope-drift` findings from 72 to 45 (total findings 77 -> 50, the 5 non-drift findings unchanged). The terminal plans `v58bvy` and `8zgybk` contribute zero afterward; `qmt3yk` and `v7e88a` contributed zero BEFORE the fix as well (grandfathered, F2) and must not be credited to it. Because concurrent sessions change the tree, the executor must record both numbers from the SAME session and state the tree state, rather than comparing against this document's numbers.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- No spec change. Spec `25kzda` names "Declared Scope-Paths contain every item change" as a host-independent safety guarantee re-derived from the frozen baseline (section 5.2, guarantee 7) and states in the same section that "pre-existing dirty paths are never absorbed into an item delta"; a receipt for a finished plan has no item delta to re-derive, so skipping it serves that guarantee rather than weakening it. Section 6.1 requires honest limits, which E-02's comment supplies. This plan makes an existing local gate's precondition true rather than altering specified behavior.
- No user-facing docs describe `check_scope_drift` (verified: no match in `docs/`, `README.md`, `CONTRIBUTING.md`, `AGENTS.md`, or `.aw/records/specs/`), so no doc updates. The docstring work is now E-04 rather than an unowned requirement, and covers BOTH `check_scope_drift` and the `check_commit_invariants` line that already claimed an "ACTIVE begin receipt" the code did not verify.

## Open questions

### OQ-01: Should liveness be derived from the plan's directory or from its `Status:` field?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: DIRECTORY, and specifically the FIRST PATH COMPONENT under the plans dir. The repository encodes disposition in the path by design (filesystem-encoded-state), the lifecycle setters move files as the authoritative act, and `aw runs -L` already reports directory-vs-status discrepancies as a real and observed condition, so status text can lag the move. This tree contains a live instance of exactly that lag: `v58bvy` sits in `executed/` while its finalize journal is still `committed-incomplete`, so a status-text reading is the less reliable of the two. Using the directory also avoids re-parsing and cannot disagree with where `finalize` actually put the file. REFINED at review: "directory" must mean the first component under the plans dir, not the immediate parent, because `aw archive plans` shards terminal plans into `<disposition>/YYYYMM/` (plans_archive.py:60-61) and `plans_index.py:99` already establishes that derivation. The predicate should additionally tolerate a plan file that cannot be located at all by treating the receipt as not live, which E-02's fail-safe rule already covers.

### OQ-02: Should a stale receipt be reported as its own advisory rather than silently skipped?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from repository evidence: not in this plan, and a future advisory must NOT be written as "leaked receipt". Two reasons, both measured. First, the noise argument stands: emitting a new finding class from a commit-scoped gate would make the hook refuse on a repo that already carries stale receipts, defeating this plan's purpose, and the aggregator's consumers fail closed (`precommit_scope_gate.check` returns 1 on any drift; CI's `aw check plans` exits 1 on any finding). Second, and decisive, F7 shows the advisory as originally imagined would be FACTUALLY WRONG: `v58bvy`'s receipt is in a terminal directory yet is transactionally LIVE (`phase: committed-incomplete`), so calling it leaked would report a healthy recovery state as an anomaly. A correct advisory must therefore consult the finalize journal, not just the plan's directory, which is a strictly larger piece of work than this plan and belongs in an `aw doctor`-style surface outside the commit gate. Recorded so the silence here is a deliberate, evidence-backed choice, and so the follow-up is not implemented naively.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the predicate's source and the `check_scope_drift` call site. Paste a before/after count from the SAME session with the tree state noted, for BOTH consumer surfaces (F6): `check_commit_invariants(Path("."))` and `python3 -m agent_workflows check plans --agent`. The after-state must show `v58bvy` and `8zgybk` contributing zero findings and the in-flight plans' per-plan counts UNCHANGED (paste the per-plan breakdown, not just the total, since a total alone cannot distinguish the intended skip from an accidental over-skip). Also paste proof of the two implementation constraints: that the terminal vocabulary comes from `plans.TERMINAL` rather than a fourth hardcoded list, and that the disposition is the first path component (a one-line demonstration that a `<terminal>/YYYYMM/` path is classified terminal).
  - Observed evidence: measured in-session on BOTH consumer surfaces with the import path pinned to the lane copy: `check_commit_invariants(<main>)` 222 -> 143 findings, and `aw check plans --dir <main> --agent` 238 -> 159 (its `check.scope-drift` 222 -> 143, the 16 unrelated `check.lifecycle-transition-invalid` untouched). Terminal plans `v58bvy` 45 -> 0 and `8zgybk` 34 -> 0; all five in-flight plans UNCHANGED to the finding (qcqhj7 30, rchpms 29, 58ha43 29, 2c122z 28, 1o4eif 27), so there is no over-skip. `qmt3yk`/`v7e88a` were 0 BEFORE as well (grandfathered per F2) and are not credited. Predicate reuses `plans.TERMINAL` (no hardcoded `"executed"` literal) and derives disposition as the first path component, so `executed/202608/x.ipd.md` classifies terminal where `parent.name` would read `'202608'`. Full transcripts below.
    TREE STATE: executed in lane worktree `.aw/worktrees/rygds7` (branch `aw/lane/rygds7`, HEAD `ce1ae8e`), measured against the MAIN checkout as `repo_root` because receipts are gitignored runtime state that exists only there (`ls .aw/state` in the lane -> "No such file or directory"; DECISION 02-rygds7-D2). 14 receipts present; 11 lane worktrees concurrently in flight, so the working tree is dirty with other agents' files throughout. Counts differ from this document's authoring-time numbers (72 -> 45) because far more lanes are now active; the plan explicitly instructs re-measurement (DECISION 02-rygds7-D1). Import path pinned before measuring: `agent_workflows.__file__` == the LANE copy (DECISION 02-rygds7-D5 records a near-miss where a script run from /tmp silently measured the unmodified main-checkout module).

    PREDICATE SOURCE + CALL SITE (`check_engine.py`): `_plan_disposition` (first-path-component derivation) and `_receipt_is_live` (terminal + unreachable-base rejection, fail-safe `except`). Call site, immediately after the existing `if not receipt: continue` as E-01 requires:
    ```
            receipt = _life.read_receipt(repo_root, plan_id)
            if not receipt:
                continue  # no active execution -> nothing to reconcile
            if not _receipt_is_live(repo_root, p, receipt):
                continue  # spent authority (terminal plan / unreachable base) -> not an in-flight scope
            base_head = str(receipt.get("base_head") or "").strip()
    ```

    SURFACE 1, `check_commit_invariants(<main>)`, same session, fix toggled by restoring my own single file:
    ```
    ============ BEFORE ============          ============ AFTER =============
    TOTAL: 222  {'check.scope-drift': 222}    TOTAL: 143  {'check.scope-drift': 143}
      34  [executed ] ...8zgybk...              (absent)
      45  [executed ] ...v58bvy...              (absent)
      30  [pending  ] ...qcqhj7...              30  [pending  ] ...qcqhj7...
      29  [pending  ] ...rchpms...              29  [pending  ] ...rchpms...
      29  [pending  ] ...58ha43...              29  [pending  ] ...58ha43...
      28  [pending  ] ...2c122z...              28  [pending  ] ...2c122z...
      27  [pending  ] ...1o4eif...              27  [pending  ] ...1o4eif...
      terminal v58bvy: 45   8zgybk: 34         terminal v58bvy: 0   8zgybk: 0
      terminal qmt3yk:  0   v7e88a:  0         terminal qmt3yk: 0   v7e88a: 0
    ```
    NO OVER-SKIP: all five in-flight plans keep their counts to the finding (30/29/29/28/27 before and after); exactly the 79 findings belonging to the two terminal plans disappear. As F2 predicted, `qmt3yk` and `v7e88a` contributed ZERO both before and after (both grandfathered, `_frozen_scope_paths == []`, already dropped by the pre-existing empty-allowlist skip), so they are NOT credited to this fix.

    SURFACE 2, `python3 -m agent_workflows check plans --dir <main> --agent` (the command CI runs fail-closed; note `--dir`, not a positional path - DECISION 02-rygds7-D3 records catching a misinvocation here):
    ```
    --- before ---                            --- after ---
      exit: 1  total findings: 238              exit: 1  total findings: 159
        16  check.lifecycle-transition-invalid    16  check.lifecycle-transition-invalid
       222  check.scope-drift                    143  check.scope-drift
    ```
    The 16 unrelated `check.lifecycle-transition-invalid` findings are untouched, which is the signature of a NARROWED rule rather than a disabled one.

    CONSTRAINT (a), shared vocabulary not a fourth list:
    ```
    references _plans.TERMINAL: True
    hardcodes "executed" literal: False
    plans.TERMINAL is: ('executed', 'superseded', 'not-executed')
    ```
    CONSTRAINT (b), disposition is the FIRST path component (a `parent.name` test would read the shard):
    ```
    executed/202608/x.ipd.md     -> disposition='executed'     terminal=True   (parent.name='202608')
    executed/x.ipd.md            -> disposition='executed'     terminal=True   (parent.name='executed')
    superseded/202601/x.ipd.md   -> disposition='superseded'   terminal=True   (parent.name='202601')
    pending/202608/x.ipd.md      -> disposition='pending'      terminal=False  (parent.name='202608')
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the induced-error case showing a SKIP rather than a finding or a traceback, and paste the comment citing `precommit_scope_gate.py:17-19`'s best-effort-feedback limit as the basis for failing safe AND stating the cost (a git-less environment silently disables the rule). Confirm by inspection that the fail-safe path is inside the predicate and does not depend on the aggregator's blanket `except Exception` (check_engine.py:1056-1059), since that isolation would also swallow a genuine bug.
  - Observed evidence: induced `OSError` on `merge-base` yields a SKIP (healthy baseline 1 finding -> 0 findings with the error, no traceback) and `_receipt_is_live` returns False; the fail-safe `except` is INSIDE the predicate (proven by calling `check_scope_drift` directly, which has no handler of its own, so the aggregator's blanket `except Exception` was never in the path), and its comment cites `precommit_scope_gate.py:17-19`'s best-effort-feedback limit AND states the cost (a git-less environment silently disables the rule). Full transcripts below.
    INDUCED ERROR -> SKIP, in a temp repo, with `_git_capture` patched to raise `OSError` on `merge-base`:
    ```
    healthy baseline (rule works here): 1 finding(s)
    with git merge-base raising OSError -> 0 finding(s): SKIPPED, no traceback
    _receipt_is_live(...) returns: False
    ```
    The healthy baseline is shown first so the skip is provably the induced error's effect and not an arrangement that never flagged. No traceback was raised; the call returned normally.

    THE COMMENT (in `_receipt_is_live`'s docstring), citing the hook's own honest limit AND the cost:
    ```
    FAIL SAFE, NOT FAIL OPEN (E-02): when liveness cannot be determined (git unavailable, unreadable
    path, ``merge-base`` error) the receipt is treated as NOT live and skipped. The asymmetry is
    deliberate and must not later be "corrected": a false refusal blocks a legitimate commit, while a
    missed advisory is recoverable, and this rule is explicitly documented as best-effort local
    FEEDBACK rather than an authority boundary (``hooks/precommit_scope_gate.py:17-19``: "git hooks
    are LOCAL, not cloned by default, and skippable with ``--no-verify``. This is OPT-IN best-effort
    FEEDBACK, not an authority boundary; the authoritative boundary is phase-5 CI running the same
    engine."). WHAT THIS DIRECTION COSTS, stated plainly: an environment where git cannot run
    silently disables this rule entirely rather than reporting that it could not run. That is
    acceptable ONLY because the authoritative boundary is CI (``.github/workflows/tests.yml`` runs
    ``aw check`` fail-closed) and NOT this local rule.
    ```

    FAIL-SAFE IS INSIDE THE PREDICATE, not the aggregator. The predicate carries its own handler:
    ```
        except Exception:
            # Fail safe (see the docstring): an undeterminable liveness is treated as NOT live. This
            # local `except` is deliberate and must NOT be left to the aggregator's blanket
            # `except Exception` in `check_commit_invariants`, which would also swallow a genuine bug in
            # the comparison below.
            return False
        return True
    ```
    Proof it does not lean on the aggregator: the 0-finding result above came from calling `ce.check_scope_drift(d)` DIRECTLY, which has no try/except of its own, so `check_commit_invariants`' blanket handler (check_engine.py, "A single rule's failure must not take down the whole pre-commit gate") was never in the call path. Test `test_e_failsafe_is_inside_the_predicate_not_the_aggregator` pins this permanently.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the new module passing with all seven cases (a)-(g). Then paste FALSIFIABILITY in all three directions: case (a) FAILS against the pre-fix predicate, case (b) FAILS when the receipt check is removed instead of narrowed, and case (f) FAILS against a `parent.name`-based disposition test. Paste `tests/test_phase4_hooks.py` and `tests/test_event_derived_lifecycle.py` passing unchanged (review-time baseline `31 passed`), plus the BARE fast and full suite results measured in your own session, with your own re-measured pre-change baseline shown alongside and the 4 known-unrelated CLI-parser-leaf failures named and not claimed. Also state explicitly that the new module reads no live repository state.
  - Observed evidence: the new 18-test module passes covering all cases (a)-(g); falsifiable in all three required directions: case (a) FAILS pre-fix (14 failed), case (b) FAILS when the rule is disabled rather than narrowed (7 failed), case (f) FAILS against a `parent.name` derivation (2 failed), with all sabotage reverted and the file verified byte-identical afterward. Existing consumers pass unchanged at `31 passed`, matching the review-time baseline. Bare suites measured pre- AND post-change in this session: fast 15 failed/2912 passed -> 15 failed/2930 passed; full 19 failed/3239 passed -> 19 failed/3257 passed, i.e. IDENTICAL failure sets and +18 = exactly the new tests. The 4 CLI-parser-leaf failures plus 15 lane-only `test_run_viewer.py` failures are named and NOT claimed. The module reads no live repository state (own temp git repo per test; no `Path(".")`/`Path.cwd()`). Full transcripts below.
    NEW MODULE PASSING, all cases (a)-(g) across 18 tests:
    ```
    $ python3 -m pytest tests/test_check_engine_receipt_liveness.py -p no:randomly -v
    12 workers [18 items]
    ..................                                                       [100%]
    ============================== 18 passed in 1.90s ==============================
    ```
    Case map: (a) `test_a_executed_plan_receipt_is_ignored`; (b) `test_b_pending_plan_still_flags_the_same_dirty_path` + `test_b_narrowing_is_the_only_difference`; (c) `test_c_base_head_not_ancestor_of_head_is_skipped`, `test_c_orphan_branch_commit_is_not_an_ancestor`, `test_c_empty_base_head_is_skipped`; (d) `test_d_every_terminal_dir_rejected_and_non_terminal_kept` (all three terminal dirs plus pending/reusable) + `test_d_terminal_vocabulary_is_the_shared_one`; (e) `test_e_liveness_error_results_in_a_skip`, `test_e_failsafe_is_inside_the_predicate_not_the_aggregator`, `test_e_missing_plan_location_is_not_live`; (f) `test_f_sharded_terminal_plan_is_skipped`, `test_f_sharded_pending_plan_is_not_skipped`, `test_f_disposition_is_the_first_path_component`; (g) `test_g_aggregator_terminal_plan_is_clean`, `test_g_aggregator_pending_plan_still_refuses`, `test_g_hook_exit_code_flips_with_liveness` (this last drives the REAL `precommit_scope_gate.check`, asserting exit 1 for a live plan and exit 0 once the same plan becomes terminal). Plus `test_ignoring_a_terminal_receipt_does_not_delete_it`, guarding F7's constraint that the rule is read-only.

    FALSIFIABILITY 1 of 3, case (a) FAILS against the PRE-FIX predicate (change reverted, tests kept):
    ```
    14 failed, 4 passed in 3.25s
    FAILED ...::test_a_executed_plan_receipt_is_ignored          <- the bug itself
    FAILED ...::test_g_aggregator_terminal_plan_is_clean
    FAILED ...::test_f_sharded_terminal_plan_is_skipped
    FAILED ...::test_d_every_terminal_dir_rejected_and_non_terminal_kept
    FAILED ...::test_c_base_head_not_ancestor_of_head_is_skipped
    (+ 9 more)
    ```
    FALSIFIABILITY 2 of 3, case (b) FAILS when the receipt check is DISABLED rather than narrowed (sabotage: `if True: continue` in place of the liveness call):
    ```
    7 failed, 11 passed in 3.83s
    E  AssertionError: [] is not true : pending is NOT terminal and must be enforced
    FAILED ...::test_b_pending_plan_still_flags_the_same_dirty_path
    FAILED ...::test_b_narrowing_is_the_only_difference
    FAILED ...::test_g_aggregator_pending_plan_still_refuses
    FAILED ...::test_f_sharded_pending_plan_is_not_skipped
    FAILED ...::test_g_hook_exit_code_flips_with_liveness
    ```
    FALSIFIABILITY 3 of 3, case (f) FAILS against a `parent.name`-based derivation (sabotage: `return plan_path.parent.name`):
    ```
    2 failed, 16 passed in 3.32s
    E  "changed path 'other/' is outside the plan's declared Scope-Paths"
    FAILED ...::test_f_sharded_terminal_plan_is_skipped
    FAILED ...::test_f_disposition_is_the_first_path_component
    ```
    All sabotage was reverted and the restored file verified byte-identical (`diff` clean) to the measured implementation before proceeding.

    EXISTING CONSUMERS UNCHANGED, matching the review-time baseline of `31 passed` exactly:
    ```
    $ python3 -m pytest tests/test_phase4_hooks.py tests/test_event_derived_lifecycle.py
    ...............................                                          [100%]
    31 passed in 2.41s
    ```

    BARE SUITES (no redundant `-n`/`-q`; `-n auto --dist=worksteal` is already in `addopts`), each measured BOTH pre-change and post-change IN THIS SESSION. Pre-change runs were taken with the tree verified clean (`git status --porcelain` empty) and, for the full suite, with the new test module moved aside:
    ```
    FAST  (bare `python3 -m pytest`)
      pre-change : 15 failed, 2912 passed, 3 skipped, 4 xfailed
      post-change: 15 failed, 2930 passed, 3 skipped, 4 xfailed     (+18 = exactly the new tests)

    FULL  (bare `python3 -m pytest -m ""`)
      pre-change : 19 failed, 3239 passed, 3 skipped, 4 xfailed
      post-change: 19 failed, 3257 passed, 3 skipped, 4 xfailed     (+18 = exactly the new tests)
    ```
    IDENTICAL failure sets before and after; zero net-new failures. NOT CLAIMED as caused or fixed by this change: the 4 known-unrelated CLI-parser-leaf failures from concurrent `run_cli` work - `tests/test_command_surface_declarations.py::CommandSurfaceDeclarationsTests::test_zero_undeclared_parser_leaves`, `tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description`, `tests/test_cli_conformance_matrix.py::UndeclaredLeafGuardTests::test_no_undeclared_parser_leaves`, and `...::test_every_declared_leaf_gets_a_full_scenario_row_set` - plus 15 `tests/test_run_viewer.py` failures. The plan expected the run_viewer module to pass and warned it was flaky-by-state; measured cause is that it reads the LIVE cwd (`run_viewer.discover_run_dirs(Path("."))`) and a lane worktree has no `.aw/records/runs/`, so the whole module fails in ANY lane. `i79rgh` owns that defect; `tests/test_run_viewer.py` is outside this plan's Scope-Paths and was not touched (DECISION 02-rygds7-D4).

    THE NEW MODULE READS NO LIVE REPOSITORY STATE: every test builds its own `tempfile.TemporaryDirectory` git repo in `setUp` (mirroring `tests/test_event_derived_lifecycle.py`'s fixture, including the `.gitignore` for `.aw/state/`) and asserts only against that temp root. There is no reference to the live checkout, no `Path(".")`, and no `Path.cwd()` anywhere in the module, so it cannot exhibit the `i79rgh` live-state defect class.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste both revised docstrings. `check_scope_drift`'s must name the two rejected cases; `check_commit_invariants`'s `check.scope-drift` bullet must no longer claim an "ACTIVE begin receipt" that the code does not verify. Confirm no behavioral line changed in this item (a diff limited to docstring/comment lines).
  - Observed evidence: both docstrings revised and pasted below: `check_scope_drift` now names both rejected cases (terminal directory incl. `<disposition>/YYYYMM/` shards, and base-not-ancestor-of-HEAD) plus the fail-safe rationale, and `check_commit_invariants`'s bullet no longer claims an "ACTIVE begin receipt" (now a LIVE receipt, verified); the `RULE_REGISTRY` comment was made consistent too. E-04 changed no behavioral line: all 7 removed lines in the file diff classify as comment or docstring prose, and the only added executable lines belong to E-01/E-02. Full transcripts below.
    REVISED DOCSTRING 1, `check_scope_drift`, naming BOTH rejected cases and the fail-safe rationale:
    ```
        For each plan that has a LIVE begin receipt, compare the paths this execution changed since the
        frozen base against the plan's declared Scope-Paths, REUSING the finalize scope helpers
        ...
        LIVE is checked by ``_receipt_is_live`` and is narrower than "a receipt exists" (IPD rygds7): a
        receipt is IGNORED when (1) its plan sits in a TERMINAL lifecycle directory
        (executed/superseded/not-executed, read from the plan's path so a ``<disposition>/YYYYMM/`` shard
        still counts), or (2) its frozen ``base_head`` is NOT an ancestor of HEAD, so the baseline no
        longer describes this history. Both cases are receipts that cannot describe work in progress, and
        comparing the whole working tree against them attributed other agents' uncommitted files to a
        finished plan. Liveness FAILS SAFE (undeterminable -> skip); see ``_receipt_is_live`` for the
        rationale and its cost. Ignoring a terminal plan's receipt here is an ADVISORY decision only and
        is NOT a claim that the receipt is dead - it may still be required by an unfinished finalize
        transaction, and nothing here deletes one.
    ```
    REVISED DOCSTRING 2, `check_commit_invariants`; the phrase "ACTIVE begin receipt" is GONE, replaced by a LIVE claim the code actually verifies:
    ```
        * ``check.scope-drift`` (``check_scope_drift``) - for a plan with a LIVE begin receipt, a
          changed path outside its declared ``Scope-Paths`` (findings 5.3: enforce the staged-paths-
          within-declared-scope INVARIANT, not the command syntax). LIVE is verified, not assumed (IPD
          rygds7): a receipt is IGNORED when its plan is in a TERMINAL lifecycle directory or when its
          frozen ``base_head`` is not an ancestor of HEAD, since neither can describe an in-flight
          execution. That liveness test fails SAFE (undeterminable -> skip), consistent with this being
          best-effort local feedback; see ``_receipt_is_live``.
    ```
    ALSO made consistent, as the E-04 expected outcome requires, the `RULE_REGISTRY` comment for `check.scope-drift`:
    ```
        # Declared-file-scope drift (agentadhere Phase 3, IPD wqj1ne E-02; catalog I-01). A plan with a
        # LIVE begin receipt whose changed paths since the frozen base fall outside its Scope-Paths. LIVE
        # excludes a receipt whose plan is in a terminal lifecycle dir or whose base is unreachable from
        # HEAD (IPD rygds7; see `_receipt_is_live`).
    ```
    NO BEHAVIORAL LINE CHANGED BY E-04. Classifying every REMOVED line in the whole file diff shows all 7 are prose or comment; no executable line was deleted or edited:
    ```
    ALL REMOVED LINES (7) - every one must be prose/comment:
      [comment        ] # Declared-file-scope drift (agentadhere Phase 3, IPD wqj1ne E-02; catalog I-01). A plan
      [comment        ] # active begin receipt whose changed paths since the frozen base fall outside its Scope-
      [docstring-prose] For each plan that has an ACTIVE begin receipt (an in-flight execution with a frozen bas
      [docstring-prose] Scope-Paths), compare the paths this execution changed since the frozen base against the
      [docstring-prose] declared Scope-Paths, REUSING the finalize scope helpers
      [docstring-prose] * ``check.scope-drift`` (``check_scope_drift``) - for a plan with an ACTIVE begin receip
      [docstring-prose] within-declared-scope INVARIANT, not the command syntax).
    ```
    The only ADDED executable lines in the file belong to E-01/E-02 (the two new functions plus the 2-line call site), confirming E-04 contributed documentation only.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: all open questions are resolved (OQ-01 and OQ-02 both `resolved`); commit ONLY the two files in Scope-Paths, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`/bare/`-a`, and never push. HONESTY RULE, hard MUST: every claim that a test or command passed must be accompanied by the ACTUAL pasted runner output; never assert a result you did not run, and never restate this document's measured numbers as if you had observed them.

SHARED-CHECKOUT WARNING, unusually acute for this plan: multiple runners are executing concurrently (two live lane worktrees at review time, `aw/lane/qcqhj7` and `aw/lane/rchpms`, plus in-flight plans declaring `agent_workflows/engine.py`, `AGENTS.md`, `oc_runipd.py`, `agy_runipd.py`, `ipd_lifecycle.py`, and `cli.py`). This plan touches NONE of those, deliberately. Before every commit AND every retry, run `git diff --cached --name-only` and unstage anything not in this plan's Scope-Paths: the git index is SHARED mutable state, so a co-worker's `git add` can land between your check and your commit, which was observed this session. A verification result older than the commit attempt is worthless; re-verify immediately before each attempt. Expect the working tree to be dirty with other agents' files throughout; that is normal here and is not yours to clean, stage, or revert.

Do not "fix" the leaked receipts on disk as a convenience, and do not delete a receipt whose plan is terminal. They are the evidence F2/F4/F7 rest on, they belong to other plans' executions, deleting them would destroy the before/after measurement V-01 requires, and at least one of them (`v58bvy`) is still required by an unfinished finalize transaction (F7). This prohibition is a correctness constraint, not tidiness.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand, and this plan is moved to `.aw/records/plans/executed/` only by that command.
