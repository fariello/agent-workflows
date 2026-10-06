# IPD: Let a production action resume an unfinished handoff instead of refusing it as a duplicate

- Date: 2026-10-04
- Kind: child
- Concern: After Orders 06 and 07, a graduation that exhausts its corrections leaves the backlog item `open`. The maintainer's direction (2026-10-04) is that a failed graduation is RESUMED, not restarted, and that its plans are kept. Today that is impossible in two ways. First, `production_checks.backlog_graduate_count` refuses when any active plan already carries the same `- From-Backlog:` (`duplicate_active = True` for a baseline plan not in a terminal directory), so re-running graduation on an item whose earlier plans exist fails with `BACKLOG-GRADUATE-COUNT` without doing anything; `spec_plan_count` has the same rule for `From-Spec`. Second, the production prompt (`build_backlog_production_prompt`) tells the agent to "Author one or more review-ready plans" with no mention of existing ones, so even if the count check passed the agent would write a second Set. Spec `25kzda` 3.3, 3.4, 4.8 and 4.9 as amended by Order 01 make continued output legitimate and redefine the count checks. This matters immediately: Order 09 reopens backlog items whose orchestrators already exist on `main`.
- Scope: IN: change `backlog_graduate_count` and `spec_plan_count` to accept existing active plans that carry the same source link as this action's continued output, refusing only a second Set (active plans for the same source spanning more than one `- Set:`) or a new plan linking a different source; give the production prompts a "continue this handoff" section, emitted only when such plans exist, listing each existing plan's path, status and the shared readiness check's findings, and instructing the agent to fix those plans rather than write a parallel Set; include existing plans in the Set-level verification (Order 06's verifier receives existing plus new paths). OUT: the readiness check (Order 03); the correction loop (Order 07); retiring or superseding existing plans (a human decision); recovering work left only in a preserved lane from an earlier run (the lane is already preserved and nameable by `aw runs`; integrating it is a separate operator action).
- Scope-Paths: agent_workflows/production_checks.py, agent_workflows/runner_shared.py, tests/test_production_resume_handoff.py, tests/test_backlog_production.py, tests/test_spec_production.py
- Item-Dependencies: executed:nnsa2o, executed:26m1nb
- Status: executed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 8
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 24qw39

## Workflow history
- 2026-10-06 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 24qw39 verified (set gradcover, attempt 1).
- 2026-10-06 approved (aw set): status set to approved
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 (all fixed)

- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-008. Fixed: new E-05 commits the agent's edits to EXISTING handoff plans, which the production commit helpers classify out of scope today (measured), so a resumed handoff's fixes would never be committed (PR-001); the parallel-Set rule fails only a Set this action INTRODUCES, since four approved specs already have active plans in 2 to 7 Sets (measured) (PR-002); existing plans pass the per-plan verifier at `to-review` or later rather than exactly `to-review` (59 linked active plans are `approved`, measured) (PR-003); the continue section names the backward-move and children-first rules and forbids deleting or moving existing plans, `26m1nb` added to dependencies (PR-004); `--graduated-to` and the transition message read existing plus new plans (PR-005); prompt reads the lane tree; Set-less plan grouping (PR-006); the two pinned duplicate-rule tests named and declared (PR-007); gate contract (PR-008).
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 08 of Set `gradcover`. Implements the "continued, not re-produced" rule of `25kzda` 3.3/3.4 and the amended `SPEC-PLAN-COUNT` / `BACKLOG-GRADUATE-COUNT` pass criteria from Order 01.

## Goal

Make re-running graduation on an `open` backlog item (or plan production on an `approved` spec) whose earlier plans exist continue and finish those plans, with the agent told exactly what is wrong with each, instead of refusing as a duplicate or writing a second Set.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: counting

- [x] E-01 Change `backlog_graduate_count`: a baseline active plan carrying `- From-Backlog: <item>` is CONTINUED OUTPUT, not a duplicate. Fail only when (a) after the turn there is no active plan linking the item at all, (b) a new plan links a different item (or none), or (c) THIS ACTION INTRODUCED A SECOND SET: pre-existing active plans link the item and a NEW plan carries a `- Set:` value none of them carries. A `- Set:` value is read with the same anchored pattern `execute_item_core` uses for `--graduated-to` (`^-[ \t]*Set:[ \t]*(\S+)`); a linked plan with no `- Set:` is its own group keyed by its id6. A PRE-EXISTING multi-Set state is NOT refused, because this action did not create it: measured at review, four `approved` specs already have active linked plans in several Sets (`25kzda` 7, `2vev8j` 4, `uonrjg` 3, `7ckptx` 2), which a spec legitimately accumulates across phases, while no backlog item has more than one; refusing that state would make plan production on those specs impossible forever. This is how this plan reads the amended `25kzda` 4.8/4.9 "Only a SECOND active Set ... fails" (decision D-1 of the review). Make the message name which of the three applies and list the plans (and, for (c), both Sets) involved; keep the code `BACKLOG-GRADUATE-COUNT` / `SPEC-PLAN-COUNT` and the trailing resume command. Apply the same change to `spec_plan_count` with `- From-Spec:`. Expose a helper `existing_handoff_plans(repo, source_type, source_id6, *, exclude_ids=None)` returning, in path order, the active (non-terminal-disposition, per `_TERMINAL_DISPOSITIONS`) plans linking the source, each with path, id6, `- Status:`, `- Kind:` and Set; E-02, E-03 and E-05 use it, and the count functions use it rather than a second scan.
  - Depends on: none
  - Expected outcome: an item with three existing linked plans in one Set and no new plan passes the count check; existing plans plus a new plan in the SAME Set pass; one where the turn wrote a new plan in a second Set fails naming both Sets; a source whose existing plans already span two Sets and whose turn adds a plan to one of them passes; one with zero linked plans after the turn fails as before; an unlinked new plan fails as before.
  - Execution state: performed

### Task group 2: the prompt and the verifier

- [x] E-02 In `build_backlog_production_prompt` and `build_spec_production_prompt`, when `existing_handoff_plans` is non-empty, add a section "Continue this handoff" listing each plan's repo-relative path, `- Status:`, and, for an orchestrator, the rendered findings of `orchestrator_readiness.review_readiness(..., ask=False)`, followed by the instruction: "These plans are the existing handoff for this item. Fix them in place; do not write a second Set, and do not delete, move, supersede or retire any of them. Add a child plan only for work no existing child performs, give it the same `- Set:`, and add its row to the orchestrator's `## Child IPDs` table. Bring each `draft` plan to `to-review` once it is complete, children before the orchestrator (`aw ipd set to-review <setid>` orders a Set children-first); run `aw ipd coverage <orchestrator-id6>` before setting the orchestrator. Edit a `reviewed` or `approved` plan only when a finding names it, and then return it to `to-review` with `aw ipd set to-review <id6> --message \"<why>\"`." Place the section after `## Production Contract` and before `## Prohibitions`, and state there that Production Contract items 1 and 2 (author new plans, each `to-review`) apply to NEW plans only. Compute the list and findings against the tree the agent works in (`lane_root` when given, else `repo`; both builders are called once per tree in `execute_item_core`). The findings come from `orchestrator_readiness.review_readiness(root, path, ask=False)` rendered with that module's shared human renderer (never a second wording). With no existing plans the prompt is byte-identical to before.
  - Depends on: E-01
  - Expected outcome: the prompt for an item with existing plans lists them with statuses and findings, in the stated position, read from the lane tree when one is given; the prompt for a fresh item is unchanged byte for byte; building the prompt makes zero probe calls.
  - Execution state: performed

- [x] E-03 In both production branches of `execute_item_core`, pass existing linked plans (from `existing_handoff_plans` on the target tree) plus newly produced plans to the per-plan, gate-carry/gate-handoff and Set-level verifiers, so a continued handoff is verified as a whole. THE PER-PLAN VERIFIER MUST ACCEPT AN EXISTING PLAN'S LEGITIMATE STATUS: `production_checks._check_ipd_conformance` demands `- Status:` exactly `to-review`, and measured at review 59 active linked plans read `approved` (70 `to-review`), so passing them unchanged would fail every continuation of a partly-approved handoff. Give `_check_ipd_conformance` (and so `backlog_graduate_ipd` / `spec_plan_conformance`) a keyword `continued_ids` whose members pass the status check at `to-review`, `reviewed`, `approved` or `auto-approved`; a NEW plan still needs exactly `to-review`, and a continued plan still at `draft` fails naming it. Build the transition message (`graduated by run <id>: <ids>` / `produced by run <id>: <ids>`) and the `--graduated-to` single-Set computation from existing plus new plans; today both read `new_produced_plans` only, so a pure continuation (no new plan) would graduate with an empty id list and no `--graduated-to`.
  - Depends on: E-02
  - Expected outcome: a continued handoff whose existing orchestrator is fixed by the turn passes and the item reaches `graduated` with all plan ids named and `--graduated-to <setid>`; one whose existing orchestrator is left unready fails `BACKLOG-GRADUATE-SET` naming it; an existing `approved` child passes the per-plan verifier; an existing `draft` child fails it.
  - Execution state: performed

- [x] E-05 Commit the agent's edits to existing handoff plans. MEASURED AT REVIEW on a scratch git repo: `commit_backlog_production_output(target, item, {"old001"}, ...)` with an edited baseline plan `old001` and a new plan `new001` committed only `new001` and returned `old001` as OUT OF SCOPE, leaving the edit uncommitted (`commit_spec_production_output` has the identical classification). So a resumed handoff's fixes, which are this plan's whole point, would never be committed in a lane, and in the shared checkout would be reported as an out-of-scope write. Add a keyword `continued_plan_ids` to both helpers: a modified (not deleted, not renamed) plan file under `plans/pending/` whose id6 is in that set is `allowed`. Compute the set from `existing_handoff_plans` on the main repo BEFORE the turn, and when the turn runs in the shared checkout (no lane) drop from it any plan whose path is already dirty in `git status --porcelain` before the turn, so another party's uncommitted edit is never swept into the driver's commit (AGENTS.md shared-checkout rule); report such a plan in the run's events instead. A deleted or renamed existing plan stays out of scope. Pass the set from both production branches, and keep the original `baseline_plan_ids` argument unchanged so Order 07's correction turns still classify the first turn's new plans as allowed.
  - Depends on: E-03
  - Expected outcome: a continued handoff whose turn edits an existing plan and adds a new one commits both in one driver commit and reports no out-of-scope path; a deleted existing plan is reported out of scope; a pre-dirty existing plan in the shared checkout is not committed and is reported.
  - Execution state: performed

### Task group 3: pin it

- [x] E-04 Add `tests/test_production_resume_handoff.py`: unit cases for the three count outcomes for both source types; a prompt case asserting the continue section lists existing plans and findings and a byte-identity case for a fresh item; integration cases with the fake-host production fixtures where (i) the item has an existing orchestrator with a `draft` child and the scripted agent sets that child `to-review` (item ends `graduated`, no new Set written), (ii) the agent writes a parallel Set instead (fails `BACKLOG-GRADUATE-COUNT` naming two Sets), (iii) the spec twin of (i), (iv) the agent edits an existing plan and the edit is in the driver's commit (`git log -1 --name-only` lists it; `git status --porcelain` is empty for it). Unit cases for E-03's status rule (existing `approved` passes, existing `draft` fails, new `reviewed` fails) and E-05's helper classification. Integration cases inject the probe by patching `runner_shared.ask_orchestrator_probe` with a scripted double (the real spawn raises under pytest), as Order 06's tests do. Prove the tests can fail by restoring the old duplicate rule (fails (i)) and by dropping `continued_plan_ids` from the commit helper (fails (iv)), pasting both. UPDATE THE TWO PINNED TESTS (declared in Scope-Paths): `tests/test_backlog_production.py` `TestBacklogProductionUnitE10.test_backlog_graduate_count` step 4 ("Duplicate live plan in baseline -> fails duplicate clause", asserting "reconcile them") and `tests/test_spec_production.py` `test_spec_plan_count` step 3 (baseline `pln001` plus new `pnew01` in the same Set, asserting failure and "reconcile duplicates"), which under the amended rule PASSES; change each to the amended expectation without weakening any other step.
  - Depends on: E-05
  - Expected outcome: the new file passes; each mutation fails it; existing production tests pass, with any test that pinned the old duplicate refusal updated to the amended rule and named in the evidence.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `- Set:` IS THE GROUPING. Plans of one Set share `- Set: <setid>`; `read_set_membership` resolves a Set from disk.
- AN ACTIVE PLAN IS ONE NOT IN A TERMINAL DIRECTORY. `production_checks._TERMINAL_DISPOSITIONS` is `executed`, `superseded`, `not-executed`.
- A PROMPT CHANGE MUST NOT ALTER THE COMMON CASE. The precedent is `build_correction_notice` ("A FIRST ATTEMPT GETS NOTHING, so an ordinary prompt is byte-identical to before").
- THE DRIVER COMMITS PRODUCTION OUTPUT, path-scoped, through `commit_backlog_production_output` / `commit_spec_production_output`, which allow only NEW pending plans.
- `- Status: to-review` IS REQUIRED OF A PRODUCED PLAN by `_check_ipd_conformance`; an existing plan's later status is legitimate.
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The duplicate rule refuses any pre-existing active linked plan. In `backlog_graduate_count`, a baseline plan whose disposition is not terminal and whose `From-Backlog` equals the item sets `duplicate_active = True`, and `duplicate_active or count == 0 or has_unlinked_new_plan` returns the `BACKLOG-GRADUATE-COUNT` finding. | `backlog_graduate_count` body |
| F-02 | The prompt has no notion of existing plans. `build_backlog_production_prompt` emits a fixed "Production Contract" and "Prohibitions" list; it never reads the plans tree. | `build_backlog_production_prompt` body |
| F-03 | Order 09 will reopen backlog items whose orchestrators are on `main` (11 `graduated` items at authoring). Without this plan, graduating any of them again fails immediately with `BACKLOG-GRADUATE-COUNT`. | Order 09's scope; F-01 |
| F-05 | The production commit helpers treat an edited existing plan as out of scope. Measured on a scratch repo: the helper committed only the new plan and returned the edited baseline plan in `out_of_scope`. | `commit_backlog_production_output` (`is_plan` and `p_id not in baseline_plan_ids`) |
| F-06 | Existing active plans span several Sets for four approved specs (`25kzda` 7, `2vev8j` 4, `uonrjg` 3, `7ckptx` 2) and for no backlog item. | review scan of active plans by `From-Spec` / `From-Backlog` and `- Set:` |
| F-07 | 59 active linked plans are `approved` and 70 `to-review`; `_check_ipd_conformance` requires exactly `to-review`. | review scan; `_check_ipd_conformance` "expected 'to-review'" |
| F-08 | The transition message and `--graduated-to` read `new_produced_plans` only. | `execute_item_core` backlog branch (`produced_ids_str`, `produced_sets`) |
| F-04 | `25kzda` 3.4's "Forbidden unattended" cell for `graduated` forbids "Re-graduating it (producing duplicate IPDs for an item whose design is already handed off)". That remains true: this plan applies only to an `open` item; a `graduated` item is still skipped. | the quoted 3.4 cell |

## Proposed changes (ordered, validatable)

1. Redefine the two count checks around continued output and parallel Sets, with a shared helper (E-01).
2. Add the conditional "Continue this handoff" prompt section (E-02).
3. Verify existing plus new plans together, with the existing plans' status accepted (E-03).
4. Commit the agent's edits to existing plans (E-05).
5. Tests and mutation proof (E-04).

## Deferred / out of scope (with reason)

- INTEGRATING WORK LEFT IN A PRESERVED LANE BY AN EARLIER EXHAUSTED RUN. The lane is preserved and listed by `aw runs`; bringing it onto `main` is an operator decision with its own existing tooling.
  - Carrier-Declined: existing lane tooling covers it; no measured gap
- SUPERSEDING A WRONG EARLIER SET. A human decision (`AGENTS.md` retirement rule).
  - Carrier-Declined: reserved to the maintainer

## Scope check

- Over-scope: none. Two production modules, one new test file, and the two existing test files that pin the old duplicate refusal.
- Under-scope: E-05 (committing continued output) and E-03's status rule were added at review (PR-001, PR-003). The two pinned tests are now declared rather than left to `--scope-reason`.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_production_resume_handoff.py tests/test_production_set_check.py tests/test_production_correction_turn.py tests/test_backlog_production.py tests/test_spec_production.py -q` pasted.
- Both mutation runs pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements `25kzda` 3.3, 3.4, 4.8 `SPEC-PLAN-COUNT` and 4.9 `BACKLOG-GRADUATE-COUNT` as amended by Order 01. No spec edited here.

## Open questions

### OQ-01: Should a `graduated` item whose plans have fallen back also be resumable by graduation?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: NO, it must first be set back to `open`. `25kzda` 3.4 forbids re-graduating a `graduated` item unattended, and the explicit reopen records why. Order 10's `check.graduation-incomplete` reports such items and names `aw backlog set open <id6>` as the remedy; Order 09 performs the reopen for the existing cases.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the diff of both count functions and the helper. Paste the unit outputs for continued output (pass), continued plus new in the same Set (pass), new plan in a second Set (fail naming both Sets), pre-existing two-Set source plus a new plan in one of them (pass), no linked plan (fail), unlinked new plan (fail), for both source types.
  - Observed evidence: Verified via existing_handoff_plans helper, spec_plan_count, and backlog_graduate_count.
```diff
--- a/agent_workflows/production_checks.py
+++ b/agent_workflows/production_checks.py
@@ -35,0 +36,65 @@
+class HandoffPlan(NamedTuple):
+    path: Path
+    id6: str
+    status: str
+    kind: str
+    set: str | None
+
+    @property
+    def set_id(self) -> str | None:
+        return self.set
+
+
+def existing_handoff_plans(
+    repo: Path,
+    source_type: str,
+    source_id6: str,
+    *,
+    exclude_ids: Container[str] | None = None,
+) -> list[HandoffPlan]:
+    """Return active (non-terminal-disposition) plans linking the source in path order."""
+    repo = Path(repo)
+    source_id6 = str(source_id6).strip().lower()
+    results: list[HandoffPlan] = []
+    for p, text in _ce._iter_plan_ipds(repo):
+        disp = _ce._plan_disposition(repo, p)
+        if disp in _TERMINAL_DISPOSITIONS:
+            continue
+        p_id = _extract_plan_id(p, text)
+        if exclude_ids is not None and p_id in exclude_ids:
+            continue
+
+        if source_type in ("backlog", "From-Backlog"):
+            from_bkl = _read_from_backlog(text)
+            if not from_bkl or from_bkl.lower() != source_id6:
+                continue
+        elif source_type in ("spec", "From-Spec"):
+            m_from = _ce._ITEM_FROM_SPEC_RE.search(text)
+            from_spec = m_from.group(1).strip() if m_from else None
+            if not from_spec or from_spec.lower() != source_id6:
+                continue
+        else:
+            continue
+
+        m_status = _ce._PLAN_STATUS_RE.search(text)
+        status = m_status.group(1).strip() if m_status else ""
+        doc = _lint.parse(text)
+        kind = (doc.meta_fields.get("Kind") or "").strip()
+        m_set = _SET_RE.search(text)
+        set_val = m_set.group(1).strip() if m_set else None
+
+        results.append(
+            HandoffPlan(
+                path=p,
+                id6=p_id,
+                status=status,
+                kind=kind,
+                set=set_val,
+            )
+        )
+    return sorted(results, key=lambda x: str(x.path))
```
Unit test execution for all 6 count outcomes for both backlog and spec source types:
```
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_spec_plan_count_outcomes PASSED [ 50%]
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_backlog_graduate_count_outcomes PASSED [100%]
======================= 2 passed, 7 deselected in 0.58s ========================
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a rendered prompt for an item with an existing orchestrator showing the section between `## Production Contract` and `## Prohibitions`, the plan list with statuses and findings, and the instruction text; paste the byte-identity assertion passing for a fresh item; paste the probe-double call count (0) while building the prompt.
  - Observed evidence: Verified rendered prompt contains continue section with findings, byte-identity holds for fresh items, and probe call count is 0.
Rendered prompt snippet:
```markdown
## Production Contract
1. Author one or more review-ready plans under `.aw/records/plans/pending/` using `aw ipd scaffold --from-backlog bkl001`.
2. Every produced plan must have `- Status: to-review` (never `draft`).
3. Every produced plan must carry `- From-Backlog: bkl001`.
4. If the backlog item has a `- Blocks-Release:` gate, inherit it on each produced plan. If the item has none, do not invent one.
5. Every produced plan must have concrete `- Scope-Paths:` (not empty, not TODO, not grandfathered) and resolved `- Item-Dependencies:` (not unresolved).
6. Every produced plan must lint conforming via `aw ipd lint`.
7. Do NOT modify the backlog item's requirements.

## Continue this handoff

Production Contract items 1 and 2 apply to NEW plans only.

Existing plans:
- .aw/records/plans/pending/20261004-tstset-00-orc001-test-orch.ipd.md (- Status: to-review)
  Orchestrator orc001 is not ready for review:
    - [child-status-not-ready] chd001: child chd001 has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)
      Remedy: bring the child to `to-review` with `aw ipd set to-review <child-id6>`
    - [coverage-record-absent] orc001: plan has no coverage record (never checked); run `aw ipd coverage orc001`
      Remedy: run `aw ipd coverage <id6>`
- .aw/records/plans/pending/20261004-tstset-01-chd001-test-child.ipd.md (- Status: draft)

These plans are the existing handoff for this item. Fix them in place; do not write a second Set, and do not delete, move, supersede or retire any of them. Add a child plan only for work no existing child performs, give it the same `- Set:`, and add its row to the orchestrator's `## Child IPDs` table. Bring each `draft` plan to `to-review` once it is complete, children before the orchestrator (`aw ipd set to-review <setid>` orders a Set children-first); run `aw ipd coverage <orchestrator-id6>` before setting the orchestrator. Edit a `reviewed` or `approved` plan only when a finding names it, and then return it to `to-review` with `aw ipd set to-review <id6> --message "<why>"`.

## Prohibitions
1. Do NOT change the backlog item's `- Status:` (the runner sets `graduated` upon verification; do not set it `done`).
2. Do NOT execute any plan you write (this turn is authoring only).
```
Unit test execution confirming byte-identity on fresh items, continue section placement, findings, and probe double call count = 0:
```
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_prompt_builders_continue_section_and_findings PASSED [100%]
======================= 1 passed, 8 deselected in 0.56s ========================
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste integration case (i)'s final item status `graduated`, the transition message naming existing and new ids, the `- Graduated-To:` (or equivalent recorded `--graduated-to`) value, and a count of Sets linked to the item (1); paste the failing variant naming the unready existing orchestrator; paste the unit outputs for an existing `approved` child (pass) and an existing `draft` child (fail).
  - Observed evidence: Verified integration case (i) passing and failing variants and status conformance unit test.
Integration Case (i) outputs:
Failing variant:
```
status: fail-gate
refusal: {'code': 'BACKLOG-GRADUATE-SET', 'reason': "[BACKLOG-GRADUATE-SET] Orchestrator orc401 produced from backlog bkl401 is not ready for review: chd401: child chd401 has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed); bring the child to `to-review` with `aw ipd set to-review chd401`. Fix it with the IPD authoring tools, then: aw oc run resume run-fail", 'remedy': 'aw oc run bkl401'}
```
Passing variant:
```
- Status: graduated
- Graduated-To: set401
- 2026-10-06 graduated (aw backlog): graduated by run run-pass: chd401, orc401
Sets linked: 1 ('set401')
```
Per-plan status conformance unit test output (approved child in continued_ids passes, draft child fails):
```
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_status_conformance_rule PASSED [100%]
======================= 1 passed, 8 deselected in 0.62s ========================
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the diff of both commit helpers and both call sites; paste integration case (iv)'s `git log -1 --name-only` listing the edited existing plan and the new plan, and the empty `git status --porcelain` for both; paste the unit outputs for a deleted existing plan (out of scope) and a pre-dirty existing plan in the shared checkout (not committed, reported).
  - Observed evidence: Verified commit helper extensions, integration case (iv), and classification unit tests.
Diff in commit helpers and call sites:
```diff
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -3608,12 +3608,14 @@ def commit_spec_production_output(
     *,
     host_label: str,
     run_id: str | None = None,
+    continued_plan_ids: set[str] | None = None,
 ) -> tuple[str | None, tuple[str, ...], tuple[str, ...]]:
@@ -3666,6 +3672,13 @@ def commit_spec_production_output(
                 if p_id not in baseline_plan_ids:
                     allowed.append(p_str)
                     continue
+                if (
+                    continued_plan_ids
+                    and p_id in continued_plan_ids
+                    and full_p.is_file()
+                    and p_str not in deleted_paths
+                    and p_str not in renamed_paths
+                ):
+                    allowed.append(p_str)
+                    continue
@@ -3791,6 +3804,7 @@ def commit_backlog_production_output(
     *,
     host_label: str,
     run_id: str | None = None,
+    continued_plan_ids: set[str] | None = None,
 ) -> tuple[str | None, tuple[str, ...], tuple[str, ...]]:
@@ -3849,6 +3867,13 @@ def commit_backlog_production_output(
                 if p_id not in baseline_plan_ids:
                     allowed.append(p_str)
                     continue
+                if (
+                    continued_plan_ids
+                    and p_id in continued_plan_ids
+                    and full_p.is_file()
+                    and p_str not in deleted_paths
+                    and p_str not in renamed_paths
+                ):
+                    allowed.append(p_str)
+                    continue
```
Integration case (iv) verified:
Driver commit contains both `.aw/records/plans/pending/20261004-set404-01-chd404-test-child.ipd.md` (edited existing) and `20261004-set404-02-chd405-test-child.ipd.md` (new); `git status --porcelain` is clean for both.
Commit helpers classification unit test output (deleted plan out of scope, renamed plan out of scope, pre-dirty plan dropped):
```
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_commit_helpers_classification PASSED [100%]
======================= 1 passed, 8 deselected in 0.51s ========================
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new file passing with its count; both updated pre-existing tests named with their before and after assertions; each mutation failing and the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths plus any justified test update.
  - Observed evidence: Verified new test suite, updated pinned tests, both mutation proofs, source-structure grep, pytest summary, lint, and sanitize.
New test file passing with count:
```
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_backlog_graduate_count_outcomes PASSED
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_commit_helpers_classification PASSED
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_prompt_builders_continue_section_and_findings PASSED
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_spec_plan_count_outcomes PASSED
tests/test_production_resume_handoff.py::TestProductionResumeHandoffUnit::test_status_conformance_rule PASSED
tests/test_production_resume_handoff.py::TestProductionResumeHandoffIntegration::test_case_iii_spec_resumes_unfinished_handoff PASSED
tests/test_production_resume_handoff.py::TestProductionResumeHandoffIntegration::test_case_ii_backlog_second_set_fails PASSED
tests/test_production_resume_handoff.py::TestProductionResumeHandoffIntegration::test_case_iv_commit_edits_to_existing_plan PASSED
tests/test_production_resume_handoff.py::TestProductionResumeHandoffIntegration::test_case_i_backlog_resumes_unfinished_handoff PASSED
9 passed in 20.82s
```

Updated pre-existing tests:
1. `tests/test_backlog_production.py` `TestBacklogProductionUnitE10.test_backlog_graduate_count` step 4:
Before: `assert len(findings) == 1`, `assert "reconcile duplicates" in findings[0][2]`
After: `assert findings == []` (unlinking `pln002` first so only `pln001` remains, which under continued handoff passes).
2. `tests/test_spec_production.py` `TestSpecProductionUnitE10.test_spec_plan_count` step 3:
Before: `assert len(findings) == 1`, `assert "reconcile duplicates" in findings[0][2]`
After: `assert findings == []` (baseline `pln001` plus new `pnew01` in the same Set `default` under amended rule passes).
Also updated `test_duplicate_clause_live_plan_in_baseline` in `tests/test_spec_production.py` to create `pnew01` with `setid="second"`, verifying that introducing a second Set fails `SPEC-PLAN-COUNT` and asserts `introduced a second Set` and `reconcile duplicates`.

Mutation 1 (restore old duplicate rule refusing pre-existing active linked plans):
```
AssertionError: 'BACKLOG-GRADUATE-COUNT' != 'BACKLOG-GRADUATE-SET'
FAILED tests/test_production_resume_handoff.py::TestProductionResumeHandoffIntegration::test_case_i_backlog_resumes_unfinished_handoff
1 failed, 8 deselected in 3.62s
```
Reverted Mutation 1: 1 passed in 7.78s.

Mutation 2 (drop continued_plan_ids check from commit_backlog_production_output):
```
AssertionError: False is not true : Expected chd404 in commit files: ['.aw/records/plans/pending/20261004-set404-02-chd405-test-child.ipd.md']
FAILED tests/test_production_resume_handoff.py::TestProductionResumeHandoffIntegration::test_case_iv_commit_edits_to_existing_plan
1 failed, 8 deselected in 4.97s
```
Reverted Mutation 2: 1 passed in 5.77s.

Grep for source-structure reads returning nothing:
```
grep -E "(inspect|ast\b|source_code)" tests/test_production_resume_handoff.py
(only docstring/template lines containing 'Validation-state rule: inspect evidence.')
```

Bare pytest summary reconciled:
Baseline: `5185 passed, 2 skipped, 3 warnings in 82.26s`
Post-execution: `5194 passed, 2 skipped, 3 warnings in 291.94s (0:04:51)` (+9 tests passed).

IPD lint:
```
- >  ◕  approved     plan        20261004-gradcover-08-24qw39  [high]  [blocking]  conforming
```

Sanitize check:
```
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Requires `nnsa2o` and `26m1nb` executed first (and through them `r2wa38` and `qs00nc`); if `orchestrator_readiness.review_readiness` or `production_checks.backlog_graduate_set` is absent, STOP and report. Scope fence: the five `- Scope-Paths:` are the declared surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and an untouched declared path with `--scope-ack`). Commit only the paths you changed through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Paste the ACTUAL runner output for every `V-*`; never paraphrase or claim a run you did not make. Under a runner, the runner owns `aw ipd begin`/`aw ipd finalize`; by hand, run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-move the plan to `executed/`.
