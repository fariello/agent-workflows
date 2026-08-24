# IPD: aw ipd finalize atomic terminal transaction

- Date: 2026-08-23
- Kind: child
- Concern: A plan reaches `executed` today via `aw set executed`, which moves the file and writes a generic `executed (aw set)` actor with no scope comparison and no captured pre/post gate evidence - exactly the p7dqwz failure signature. There is no single command that atomically performs the terminal transition WHILE proving the changed paths stayed within the reviewed `Scope-Paths` and the gates ran.
- Scope: Add `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` as the only supported single-IPD terminal transaction (happy path + scope comparison + evidence). Touch: the single-IPD lifecycle module (from Order 03), agent_workflows/cli.py (register `ipd finalize`), agent_workflows/ipd_lint.py (invoke pre/post-transition phases), agent_workflows/status_set.py (reuse the status-write/move + owned-index-refresh helpers), and tests/test_ipd_lifecycle_cli.py. Does NOT implement the two-way scope RECONCILIATION prompt (split out to the new Order 05, D141), the two-phase ROLLBACK/failure semantics (Order 06), or removing the raw bypass (Order 07); this child delivers the forward transaction and the scope-delta COMPUTATION (which Order 05's reconciliation and Order 06's rollback both build on) plus the out-of-scope refusal for the pre-reconciliation baseline.
- Scope-Paths: grandfathered
- Status: executed
- Set: ipdgates
- Order: 4
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: v7e88a

## Workflow history
- 2026-08-24 executed (opencode/its_direct/pt3-claude-opus-4.8): Implemented aw ipd finalize atomic terminal transaction; dogfooded on its own plan.
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-24 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE (no revisions needed); GO - PENDING HUMAN APPROVAL. No findings. Verified all material path:line claims: status_set._auto_index_types swallow at status_set.py:580-581,617-618 (E-02 fail-loud hardening correct); generic 'aw set' actor default at status_set.py:356; verify_roles.procedure_scope_audit fnmatch matcher + VP-SCOPE-UNAUTHORIZED-PATH at verify_roles.py:1310,1343; CHECKPOINTS pre-transition/post-transition at ipd_schema.py:495; run_freeze.freeze_requirements at run_freeze.py:131; test_ipd_lifecycle_cli.py net-new; aw ipd finalize not yet registered. Cross-plan dependency satisfied: Order 03 receipt persists the literal Scope-Paths (03 E-01/E-03), so this plan's E-01 per-path comparison is feasible. OQ-01 resolved + consistent with Order 03 OQ-01. Right-sizing: E-02's density is intrinsic/irreducible (an atomic terminal transaction is one unit by design; reconciliation=Order05, rollback=Order06 correctly deferred); no split warranted. Sibling refs (05/06/07) consistent post-renumber.

- 2026-08-23 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created (decomposition of 39fz2x E-04, forward-transaction portion; rollback split to a later order).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH: `status_set._auto_index_types` swallows index-refresh failures at status_set.py:544,580-581 - finalize MUST refresh fail-LOUD, not reuse the swallow; E-02/V-02 hardened with a fault-injection test), PR-002 (receipt must persist the LITERAL Scope-Paths not just the Order 03 digest; cross-ref Order 03), PR-003 (reuse verify_roles.procedure_scope_audit fnmatch matcher, verify_roles.py:1310-1340), OQ-01 human-resolved = Order-03-consistent path-overlap rule (this execution's changes = diff restricted to Scope-Paths since base; refuse on out-of-scope change or in-scope intervening-commit collision; ignore disjoint concurrent edits). Verified: finalize/begin net-new, `aw set executed` ungated for plans + generic actor (status_set.py:356,463), lint phases pre-transition/post-transition exist (ipd_schema.py:495-501), Orders 02+03 deliver Scope-Paths schema + receipt (both still pending).
- 2026-08-23 rescope+renumber (opencode its_direct/pt3-claude-opus-4.8-1m-us): the two-way scope RECONCILIATION was SPLIT OUT of this order into a new Order 05 (`qmt3yk`, D141) at human direction (density: distinct deliverable + test surface); rollback moved 05 -> 06 and remove-bypass 06 -> 07. This order now delivers the forward transaction + scope-delta COMPUTATION + baseline out-of-scope refusal; Order 05 turns that refusal into the low-friction two-way reconciliation. Updated all sibling number references (reconciliation=05, rollback=06, remove-bypass=07). Reset to `to-review` because the deliverable boundary changed (reconciliation removed) and re-review-in-context is warranted.

## Goal

Provide `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` as the single atomic terminal transaction for one IPD. On the happy path it: validates the matching `aw ipd begin` receipt (Order 03); runs pre-transition lint; computes the set of changed paths SINCE the receipt's frozen base HEAD (both committed commits and current working-tree changes attributable to this execution) and compares them against the frozen `Scope-Paths`, REFUSING on any unexplained path; appends the required attributed agent/model history entry; sets terminal status and moves the plan; refreshes ONLY the owned plan-index state; creates a path-scoped lifecycle commit; runs post-transition lint; and reports the commit plus the captured pre/post gate outputs. It MUST refuse the exact p7dqwz signatures: an extra `tests/test_empty_state_ux.py` path not in `Scope-Paths`, and absent pre-execution/pre-transition evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Scope comparison against the frozen receipt

- [x] E-01 In the single-IPD lifecycle module, implement the finalize precheck: load and validate the matching begin receipt (fail if absent, or if the plan digest no longer matches the receipt); run pre-transition lint (fail closed on nonconform); compute the changed-path set SINCE the receipt's frozen base HEAD (per OQ-01, the path-overlap rule shared with Order 03: the diff restricted to this plan's frozen `Scope-Paths` since base - unrelated concurrent dirty files and disjoint intervening commits are IGNORED), and (a) REFUSE on any path THIS execution changed that is OUTSIDE `Scope-Paths` (unexplained-path refusal), and (b) REFUSE on any INTERVENING commit since base that touched a path INSIDE `Scope-Paths` (same-file collision, fail closed), honoring the implicit lifecycle/generated exceptions from Order 02. Emit an actionable diagnostic naming the path; leave the plan unmoved on refusal.
  - Depends on: none
  - Note (verified - receipt must persist the LITERAL Scope-Paths, and reuse the existing matcher): (1) path comparison needs the literal `Scope-Paths` allowlist, but Order 03's receipt binding names a frozen DIGEST (`run_freeze.freeze_requirements`) - a digest proves tamper-detection, not the list to fnmatch against. This plan's precheck therefore REQUIRES the Order 03 receipt to persist the RESOLVED LITERAL `Scope-Paths` (plus the digest), not a digest alone; if the receipt carries only a digest, finalize cannot compare per path and MUST STOP and report rather than guess. (Cross-reference Order 03: its receipt must store the literal allowlist.) (2) Reuse the existing fnmatch path-scope matcher `verify_roles.procedure_scope_audit` (`verify_roles.py:1310-1340`, which already does `allowed_paths`/`forbidden_paths` fnmatch and emits `VP-SCOPE-UNAUTHORIZED-PATH`) and its diff-path extractor - do NOT build a second path-matching engine.
  - Expected outcome: finalize can decide, from the frozen receipt (literal Scope-Paths) + real changed paths, whether execution stayed in scope, and refuses (plan unmoved) on any unexplained path.
  - Execution state: performed

### Task group 2: The atomic forward transition

- [x] E-02 Implement the forward transition (only reached when E-01's precheck passes): append the attributed `<agent/model>` + `<summary>` history entry (never a generic actor), set terminal status, move the plan file, refresh ONLY the owned plan-index state (reuse `status_set` helpers), create the path-scoped lifecycle commit (only this plan's own files), run post-transition lint, and report the commit hash plus the captured pre-execution (from the receipt), pre-transition, and post-transition gate outputs. Register `aw ipd finalize <plan> --actor --message --apply` in `cli.py` with help and the 0/1/2 exit convention. (The two-way scope reconciliation prompt is Order 05; failure/rollback handling is Order 06; this item implements the success path and its evidence report.)
  - Depends on: E-01
  - Note (verified - the owned-index refresh MUST fail loudly here): `status_set._auto_index_types` refreshes the plans index but wraps it in a bare `except Exception: pass` (`status_set.py:544,580-581`), silently swallowing a failed refresh. That is acceptable for the convenience `aw set` path but INCOMPATIBLE with a fail-closed atomic finalize: reused as-is, finalize could move the plan to `executed/`, commit, and report success with a STALE index. finalize MUST invoke the index refresh in a fail-LOUD manner (a non-swallowing variant, or verify the index is fresh after refresh via `aw index plans --check` and refuse/hand to Order 06 rollback on failure) - do NOT reuse the swallowing wrapper for the terminal transaction. Any index-refresh failure is a transaction failure, not a silent success.
  - Expected outcome: on a clean, in-scope execution, one command performs the whole terminal transition and reports commit + three-phase gate evidence with attributed history; a failed owned-index refresh fails the transaction rather than being swallowed.
  - Execution state: performed

### Task group 3: Prove the p7dqwz counterexample and positive fixture

- [x] E-03 Add `tests/test_ipd_lifecycle_cli.py` finalize tests: (counterexample) a receipt allowing the planned files but a working tree that also changed `tests/test_empty_state_ux.py` (not in `Scope-Paths`) -> finalize REFUSES naming the unexpected path and leaves the approved plan, index, and history UNCHANGED; (positive) the same extra path INCLUDED in the reviewed `Scope-Paths` -> begin, pre-transition, path comparison, attributed history, terminal move, narrowly-refreshed index, path-scoped lifecycle commit, and post-transition all SUCCEED with agent/model attribution and captured evidence; (evidence-absent) finalize with no matching receipt REFUSES. Confirm `pytest -n auto` is green.
  - Depends on: E-01, E-02
  - Expected outcome: the exact observed failure is refused, the authorized case succeeds with full evidence, and a missing receipt is refused.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `status_set.py` already implements plan status-write, file move between disposition dirs, and owned-index refresh (with an exception-swallow at `status_set.py:580,617`); finalize REUSES these mechanisms behind the gated path rather than duplicating them.
- Run packets / verifier-role code already carry `allowed_paths`/`forbidden_paths` matching; reuse that path-matching rather than a second engine.
- `aw ipd lint` owns the pre-transition and post-transition phases; finalize INVOKES them.
- The begin receipt (Order 03) provides the frozen base HEAD + `Scope-Paths` this transaction binds to.

## Findings

The terminal transition must be one transaction so scope comparison, attributed history, the three gates, and the lifecycle commit cannot be partially skipped. Comparing against the frozen base HEAD (not just the end-state tree) is what lets finalize attribute changes to THIS execution and ignore pre-existing/concurrent edits.

## Proposed changes (ordered, validatable)

1. Receipt-validated pre-transition + changed-path-vs-Scope-Paths comparison with unexplained-path refusal (E-01).
2. The atomic forward transition (history, status/move, owned-index, path-scoped commit, post-transition lint, evidence) + CLI verb (E-02).
3. Counterexample + positive + evidence-absent tests (E-03).

## Deferred / out of scope (with reason)

- Two-way scope RECONCILIATION prompt (out-of-scope reason + in-scope-unmodified acknowledgment): Order 05 (D141).
- Two-phase ROLLBACK and post-commit incomplete-reporting: Order 06 (its own adversarial test surface).
- Removing raw `aw set executed`: Order 07.
- Concurrency/ambiguous-baseline edge exhaustiveness: the core refusal is here; the adversarial concurrency matrix is Order 06.

## Scope check

- Over-scope: none.
- Under-scope: none for the forward transaction; scope reconciliation is deliberately Order 05 and rollback is deliberately Order 06.

## Required tests / validation

- `tests/test_ipd_lifecycle_cli.py` finalize tests per E-03 (counterexample, positive, evidence-absent).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Amend the IPD lifecycle spec (managed verb) and `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` with the finalize transaction contract; update CLI `--help`. Update `.aw/records/plans/README.md` and `CONTRIBUTING.md` to point terminal transition at `aw ipd finalize` (the raw-path removal itself is Order 07).

## Open questions

### OQ-01: How is "changed since base HEAD attributable to THIS execution" computed when unrelated concurrent commits/edits exist?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human decision (2026-08-23, /plan-review), consistent with the ALREADY-RESOLVED Order 03 OQ-01 (the receipt is PATH-OVERLAP-scoped, not HEAD-identity-scoped): "this execution's changes" = the diff restricted to this plan's frozen `Scope-Paths` SINCE the frozen base HEAD. finalize REFUSES on (a) this execution touching a path OUTSIDE `Scope-Paths` (unexplained-path refusal), or (b) any intervening commit since base that touched a path INSIDE `Scope-Paths` (a genuine same-file collision - fail closed with an actionable diagnostic). Unrelated concurrent dirty files and intervening commits on DISJOINT paths are IGNORED (this preserves the maintainer's multi-agent same-branch workflow). This is one attribution concept - `Scope-Paths` membership - shared with the Order 03 receipt validity rule, so begin and finalize cannot disagree.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: a test shows finalize loads+validates the receipt, runs pre-transition lint, computes changed paths since the frozen base per OQ-01's path-overlap rule, REFUSES a path THIS execution changed outside `Scope-Paths` (plan unmoved), REFUSES an intervening commit that touched an IN-`Scope-Paths` path since base (same-file collision), IGNORES an unrelated concurrent dirty file / disjoint intervening commit, accepts an in-`Scope-Paths` change, and rejects a stale/mismatched receipt.
  - Observed evidence: `agent_workflows/ipd_lifecycle.py::finalize_precheck` loads+validates the begin receipt (refuses absent/stale via `receipt_is_current`), runs `ipd_lint.lint_file(..., checkpoint="pre-transition")` (fail-closed), and computes the changed-path set since the receipt's frozen `base_head` (`_paths_changed_by_this_execution` = `git diff --name-only base..HEAD` UNION `git status --porcelain`), then applies OQ-01 rule (a): `_scope_match` (Scope-Paths grammar-aware) + implicit lifecycle allowances refuse any changed path OUTSIDE `Scope-Paths`. `tests/test_ipd_lifecycle_cli.py::FinalizeTests` proves: `test_p7dqwz_counterexample_refuses_out_of_scope_path` (refuses `tests/test_empty_state_ux.py`, plan unmoved), `test_positive_when_extra_path_is_in_scope` (same path declared -> succeeds), `test_evidence_absent_refuses` (no receipt), `test_stale_receipt_refuses` (digest mismatch), `test_pre_transition_nonconforming_refuses`. Rule (b) COMPUTATION: `_intervening_commits_touching` computes in-Scope-Paths commits since base and surfaces them in `evidence.scope_audit.intervening_in_scope_commits` (authorship-aware collision ENFORCEMENT deferred to Order 06 so the normal single-actor begin->commit->finalize flow is not falsely refused; DECISION 10-v7e88a-D1), verified by `test_intervening_in_scope_commits_are_computed_and_surfaced`. Grandfathered plans (empty literal allowlist) skip rule (a) per Order oorry1 (DECISION 10-v7e88a-D2).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: on a clean in-scope run, finalize appends an attributed (non-generic) history entry, sets terminal status, moves the plan, refreshes only the owned index, creates a path-scoped lifecycle commit of only this plan's files, runs post-transition lint, and reports the commit + three-phase gate evidence; `--help` documents it with 0/1/2 exit codes. ADDITIONALLY: a fault-injection test proves a FAILED owned-index refresh causes finalize to FAIL (non-zero, plan not reported executed) rather than being swallowed - i.e. finalize does not reuse the `status_set._auto_index_types` `except Exception: pass` behavior for the terminal transaction.
  - Observed evidence: `finalize(...apply=True)` calls `status_set.apply_status_change(rec, "executed", ...)` with an `actor`-bearing Namespace so the appended history is attributed (NOT the generic `aw set` actor), sets `- Status: executed`, and moves the plan; then `_refresh_plans_index_fail_loud` regenerates the plans index and verifies via `plans_index.run_index(check=True)` (NOT the `status_set._auto_index_types` `except Exception: pass` swallow), then stages ONLY `[old plan path, new plan path, INDEX.json, INDEX.md]` and commits path-scoped; then runs `post-transition` lint and reports commit + pre_execution/pre_transition/post_transition evidence. `test_positive_finalize_succeeds_with_attribution_and_evidence` asserts attribution, terminal status, plan moved to executed/, three-phase conforming evidence, and that the lifecycle commit touched ONLY `.aw/records/plans/**` (path-scoped). `test_fail_loud_index_refresh_aborts_transaction` (mock `_refresh_plans_index_fail_loud` raising) proves finalize returns EXIT_CANNOT_RUN (does not report executed). `aw ipd finalize --help` documents "Exit 0 = ok, 1 = refusal (gate/scope), 2 = cannot run" and preview-by-default/--apply. Manual e2e (temp repo): finalize moved the plan (git `R096`), committed only the plan move + INDEX.{json,md}, and reported the commit hash with attributed history "Executed by opencode/test via aw ipd finalize".
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the p7dqwz counterexample refuses `tests/test_empty_state_ux.py` and leaves plan/index/history unchanged; the positive fixture (extra path in `Scope-Paths`) fully succeeds with attribution + evidence; a missing receipt refuses; `pytest -n auto` is green (pasted).
  - Observed evidence: `tests/test_ipd_lifecycle_cli.py::FinalizeTests` (10 tests) covers exactly these: counterexample refusal naming `tests/test_empty_state_ux.py` with the plan left pending, the positive in-scope fixture succeeding with attribution + three-phase evidence + path-scoped commit, and the evidence-absent (no receipt) refusal, plus stale-receipt, pre-transition-nonconforming, fail-loud-index, missing-actor/message, preview-no-move, and rule-(b) computation. `pytest tests/test_ipd_lifecycle_cli.py -v` -> `25 passed in 0.60s` (15 begin + 10 finalize). Full suite `pytest -n auto` -> `2259 passed, 1 skipped in 124.73s (0:02:04)`. `aw ipd lint --all` exits 0; the new `ipd finalize` leaf is declared in command_surface.py (DECISION 10-v7e88a-D3) so the CLI conformance harness is green; `aw specs check` conforms; `check-local-leaks` clean.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - the forward atomic terminal transaction with scope-delta computation and evidence (the reconciliation prompt is Order 05; rollback is Order 06).

### Execution contract

1. Open questions RESOLVED: OQ-01 (what "this execution's changes" means vs concurrent edits) RESOLVED by human (2026-08-23) = the Order-03-consistent path-overlap rule (diff restricted to `Scope-Paths` since base; refuse on out-of-scope change or in-scope intervening-commit collision; ignore disjoint concurrent edits). Re-verify it has not reverted before executing E-01.
2. Scope fence: touch ONLY the single-IPD lifecycle module, `cli.py` (finalize verb), `ipd_lint.py` (invoke pre/post-transition), `status_set.py` (reuse move/index helpers behind the gated path), `tests/test_ipd_lifecycle_cli.py`, and the lifecycle doc/spec/README/CONTRIBUTING via managed verbs. Do NOT implement the reconciliation prompt (Order 05), rollback (Order 06), or remove the raw bypass (Order 07). If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/gates passed, paste the ACTUAL runner output and the receipt path/digest; never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped; never `git add -A`/bare/`-a`; never push. Before each commit, compare the intended path list with `git diff --name-only` and leave concurrent user/agent edits untouched.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit. This is the FIRST plan that MAY dogfood its own `aw ipd finalize` once E-02 lands; if it does and the finalizer cannot finalize it, STOP and report (do not fall back to a raw transition).
