# IPD: Refuse a finalize against a plan path the runner knows may be stale, instead of silently substituting it

- Date: 2026-09-30
- Kind: child
- Concern: THE FINALIZE STEP RE-RESOLVES THE PLAN PATH AND THEN SWALLOWS THE FAILURE INTO THE KNOWN-STALE VALUE IT WAS RE-RESOLVING TO REPLACE. In `runner_shared.execute_item_core`, both self-finalize arms read `current_plan_for_finalize = resolve_plan_path(...)` with `except DriverError: current_plan_for_finalize = plan_path`, where `plan_path` was captured AT TURN START from `queue_plan_path_for`. A self-finalizing plan MOVES out of `pending/` during its own turn, which is the reason the value needs re-resolving at all, so the fallback substitutes a path the runner already has evidence is wrong and hands it to `compute_scope_reconciliation`, `record_item_spec_edits`, `refreeze_stale_receipt_for_correction`, `driver_finalize` and `perform_carrier_verification`.
  THE HOLE IS NOT LATENT, WHICH IS THE ITEM'S FIRST QUESTION ANSWERED. The item asked whether `aw ipd finalize` already refuses a path that does not exist or does not match the id6. MEASURED at HEAD `2142a15d`: it does NOT, and the failure is worse than a refusal in both directions the fallback can take. (a) When the substituted path DOES NOT EXIST, `ipd_lifecycle.finalize_precheck` does an UNGUARDED `plan_path.read_text(...)` and raises `FileNotFoundError` (F-1), which is NOT a `DriverError`, so it escapes `execute_item_core`'s inner handlers, escapes both hosts' per-item `except DriverError` in `run_queue`, and reaches `main`'s outermost `except Exception` which prints one line and RE-RAISES; the whole run dies mid-item with the remaining queue untouched (F-2). (b) When the substituted path EXISTS but is the WRONG tree's copy (the lane default), the gate answers about that OTHER document: `_repo_relative` falls back to an ABSOLUTE path, so `finalize_precheck` compares the wrong file's front matter and returns a refusal whose finding describes the wrong plan (F-3).
  AND THE WORST CASE IS A FALSE SUCCESS, NOT A CRASH, WHICH IS WHAT ELEVATES THIS ABOVE TIDINESS. `driver_finalize`'s last step is `finalize_outcome`, whose idempotence tail asks `finalize_already_done`, which delegates to `ipd_lifecycle.plan_already_finalized`, whose predicate is `runner_shared.plan_bucket(plan_path) == "executed"`. `plan_bucket` is PURE PATH INSPECTION and does no IO by contract. So a stale `executed/`-shaped path makes a REAL refusal (`no begin receipt for <id6>`) return exit code 0 with the message "the terminal transition already succeeded", after which the arm sets `attempt["disposition"] = "executed"`, `attempt["finalized"] = True` and proceeds to integration (F-4, measured: `finalize_outcome(rc=1)` returns `0`).
  THE FALSE SUCCESS HAS TWO SHAPES AND ONLY ONE IS A GHOST PATH, which is the correction review made to this plan's own analysis and the reason E-04 is not a one-line existence check. SHAPE (i), the GHOST: an `executed/`-shaped path that does not exist on disk at all. SHAPE (ii), the WRONG TREE, which is the DOMINANT one because it is this runner's own default execution geometry: the substituted `plan_path` was resolved against MAIN and EXISTS there, while `finalize_repo` is the LANE, so the predicate answers `already=True` about a file in a tree the finalize is not finalizing. Measured on a real `git worktree` pair (F-10): the fallback value exists, `finalize_already_done(lane, mainpath) -> True`, and `finalize_outcome(lane, mainpath, rc=1) -> 0`. An existence check alone leaves shape (ii) WIDE OPEN, so E-04 requires CONTAINMENT as well as existence, and F-10 records the control that keeps the legitimate `finidem` case (a plan the LANE itself moved into its own `executed/`) still returning 0.
  WHY THIS WAS FILED SEPARATELY FROM `fzxfph`, and why that fence was right. `fzxfph` fixed the byte-identical twin on the VERIFY side, where the same shape was measured launching 23 verifier turns against a nonexistent path across three named runs. Its scope fence excluded this site by name, recorded it as F-13, required the executor to paste it UNCHANGED as V-03 evidence, and filed this item rather than widening. The consumer differs (`aw ipd finalize`, not a verifier launch) and so does the failure model, which the item said must be measured before deciding. It now has been, and the answer is that the finalize gates do NOT catch it.
- Scope: IN: (1) replace both `except DriverError: current_plan_for_finalize = plan_path` arms in `runner_shared.execute_item_core` with a RECORDED REFUSAL that leaves the plan unmoved, spends no finalize, and does not integrate, reusing the `record_refusal` + reason/remedy shape `fzxfph` established on the verify side but with its OWN code rather than a verify-specific one; (2) close the two ways a wrong path becomes a FALSE SUCCESS or a RUN-FATAL crash even when re-resolution succeeded, by making `finalize_already_done` require the plan file to be BOTH present on disk AND CONTAINED IN THE TREE BEING FINALIZED before it may convert a refusal into a no-op (F-10 measures that an existence check ALONE misses the dominant case, where the substituted path exists in the OTHER tree), and by making `finalize_precheck` refuse an unreadable plan file with its own exit-2 cannot-run instead of raising `FileNotFoundError`; (3) behavioral tests for all three, including the false-success direction in BOTH its wrong-tree and its ghost-path shapes, driven through the shipped predicates rather than asserted on source text. OUT: the verify-side site, which `fzxfph` already fixed and which this plan must leave byte-identical; the THREE OTHER `except DriverError: <x> = plan_path` prompt-building fallbacks in the same function (F-7 measures them as a different class with an advisory consumer); `plan_bucket` itself, which must stay IO-free (F-5); `ipd_lifecycle.plan_already_finalized`, whose `executed/`-bucket-without-reachable-commit tolerance is the measured `finidem` incident's own shape (F-5); the finalize retry classification and its budget; and any change to WHICH refusals are retryable.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/ipd_lifecycle.py, tests/test_finalize_stale_plan_path.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: rfhiu2
- Set: rfhiu2
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 1fzist
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed), PR-002, PR-003, PR-004 (MEDIUM, all fixed), PR-005, PR-006, PR-007 (LOW, all fixed). Typed record at `.aw/records/reviews/20260930-rfhiu2-01-1fzist-refuse-a-finalize-against-a-plan-path-the-runner-knows-may-b.review.md` with six `### Decisions` rows, none irreversible. Every finding the plan authored was RE-MEASURED at HEAD `62b18f47` rather than read, including a real `git worktree` pair, and all of them reproduce.
  THE DOMINANT REVISION CORRECTED THIS PLAN'S OWN FIX (PR-001, F-10). E-04 proposed an EXISTENCE check on `finalize_already_done`, and an existence check does not touch the false-success shape the runner actually produces: measured on a lane branched before the plan existed, with main's copy in `executed/`, the substituted path EXISTS, `finalize_already_done(lane, mainpath)` is `True`, and `finalize_outcome(lane, mainpath, 1, "refused")` returns `0`. As authored the plan would have shipped a guard that passes its own test, closes the minor ghost-path case, and leaves the default lane geometry open. E-04 now requires CONTAINMENT as well as existence, E-06 row (b) is split into both shapes on a real worktree, and V-04 demands the same-tree and non-normalized-spelling controls green BEFORE and AFTER, because a containment guard implemented against the wrong tree would refuse every legitimate idempotent finalize and strand lanes for hand merging.
  THREE SMALLER FIXES OF FACT OR MECHANISM. E-02's disposition is now mandated `fail-gate` rather than left open (PR-002): `partial`'s recorded non-retryable reason names another plan as its future owner, so a later widening would re-dispatch an item whose plan the runner cannot locate. E-05's caller list dropped the false `wtiso_gate` claim and gained F-12/F-13 (PR-003, PR-005), the latter recording that `ipd_lifecycle.finalize` already guards the missing-plan case one layer up, which is why E-05 reuses its wording and why V-05 now also demands the `finalize_with_contention_retry` route that guard does not cover. And E-02's refusal is now asserted at END OF TURN (PR-004, F-11), because `record_refusal` writes a single slot that `handle_turn_failure_retry` overwrites for every execute turn after both finalize arms.
  WHAT WAS DELIBERATELY NOT WIDENED, with the reason recorded in the plan rather than here: `record_refusal`'s single-slot design (D-3), `_repo_relative`'s absolute-path fallback (D-4), the verify-side site, and the three prompt-building fallbacks. OQ-01 stays `open` and NON-BLOCKING (D-5): the run corpus is gitignored and absent from this lane, and the item's second reclassification trigger is independently satisfied in-lane, so the count would change how urgent this looks and not what any E-item does. `aw ipd lint` reported `conforming` at `--phase author` before review and at `--phase review-finalize` after.

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `rfhiu2`. Every finding below was MEASURED by importing the shipped modules and driving the real predicates against temporary git repositories at HEAD `2142a15d`, not transcribed from the item.
  THE ITEM'S OWN RECLASSIFICATION TRIGGER FIRED, so this plan is filed `bug` where the item is `followup`, and the reason is the item's words rather than a preference. The item states: "If a scan of recorded runs shows it firing, or if the finalize gates are shown not to catch a stale path, RECLASSIFY it with the number attached." Suggested first step 1 has now been performed and the finalize gates are shown NOT to catch it (F-1 through F-4). The `Blocks-Release: next` gate follows from the repository's "every live bug gates the next release" rule rather than from a separate judgement; the item carries no gate to inherit, so this plan ORIGINATES one, which is what that rule requires of a `bug`. The number attached is not a latency measurement (this is a correctness defect, not a slow path): it is that a REAL refusal returns exit code 0 and the item is recorded `executed` and integrated (F-4, reproduced in three lines).
  THE ITEM'S SUGGESTED FIRST STEP 2 (SCAN RECORDED RUNS) COULD NOT BE PERFORMED HERE AND THAT IS STATED RATHER THAN QUIETLY DROPPED. `.aw/records/runs/` is GITIGNORED (`.aw/.gitignore` matches `records/runs/`) and is therefore ABSENT from this lane worktree entirely: `ls .aw/records/runs` in the lane returns zero entries, while the maintainer's main checkout holds 332. So the historical-occurrence count the item asks for is not obtainable from an isolated lane by construction, and going outside the lane to read it is prohibited. That is why the reclassification rests on the OTHER trigger the item names (the gates are shown not to catch it), which is fully measurable in-lane. F-8 records what a maintainer with the corpus can run to get the count, and OQ-01 carries the question.
  THE SCOPE GREW BEYOND THE ITEM'S THREE STEPS, DELIBERATELY AND MINIMALLY. The item proposed one fix (refuse at the fallback). Measuring the consumer turned up two INDEPENDENT holes that make a wrong path dangerous even when re-resolution SUCCEEDS: `finalize_already_done` keys on a path SHAPE and never checks existence (F-4), and `finalize_precheck` raises rather than refusing on a missing file (F-1). Fixing only the fallback would leave both reachable by any other route to a wrong path, and the second one is what converts a defect into a false claim of execution. Each is one guard clause with its own test, so the plan stays one focused pass.

## Goal

Make the finalize step refuse a plan path it cannot re-resolve, instead of silently proceeding against
the value it was re-resolving to replace, and make the two downstream gates that a wrong path slips
past fail closed rather than either crashing the whole run or reporting a refused finalize as success.

Nothing about WHICH plans may finalize changes. A turn whose plan re-resolves cleanly, which is every
turn on the happy path, behaves byte-identically.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: refuse the unresolvable plan instead of substituting a stale one

- [x] E-01 In `agent_workflows/runner_shared.py`, add a module-level refusal CODE constant for this fact plus a reason/remedy text function, sited beside the existing `FINALIZE_REFUSAL_CODE` rather than beside the `VERIFY_ABSENCE_*` block. Two reasons the placement matters: the `VERIFY_ABSENCE_CODES` tuple is documented as a CLOSED set over "every reason a VERDICT can be absent" and `verify_absence_text` RAISES on a code outside it, so adding a finalize fact there would either break that closure or require widening a set whose four members each describe a verifier turn; and `fzxfph`'s own in-tree comment instructs a follow-up to "reuse `VERIFY_ABSENCE_*`'s shape, not its verify-specific codes". Name the code for the fact (the plan could not be re-resolved before finalize), give the reason the same three properties the verify twin's has (say what did NOT happen, say that the runner deliberately did not fall back, say that nothing was merged), and give the remedy a concrete first command (`aw find plans <id6>`) plus the statement that the lane is PRESERVED, since the destructive wrong move here is re-running a plan whose lane already holds the work.
  - Depends on: none
  - Expected outcome: importing `runner_shared` exposes the new code and the text function; the text function returns a non-empty reason and a non-empty remedy for it (the `Refusal` contract requires both); `VERIFY_ABSENCE_CODES` is UNCHANGED and still has exactly four members; and `verify_absence_text` still raises `ValueError` when handed the new code, proving the two vocabularies stayed separate.
  - Execution state: performed

- [x] E-02 In `runner_shared.execute_item_core`, replace BOTH `except DriverError: current_plan_for_finalize = plan_path` arms (the lane arm, whose `try` calls `resolve_plan_path(finalize_repo, ...)`, and the non-lane arm, whose `try` calls `resolve_plan_path(repo, ...)`) with a refusal that performs the same five acts the verify-side twin performs: `record_refusal` with E-01's code, reason and remedy; set the disposition to a non-success terminal value; print the reason and remedy to stderr; save state; and SKIP the entire finalize body so no `driver_finalize`, no `record_item_spec_edits`, no `refreeze_stale_receipt_for_correction`, no `perform_carrier_verification` and no integration runs for that item. Use the `current_plan_for_finalize = None` / `if current_plan_for_finalize is not None:` guard shape the verify site already uses, so the two sites read the same way and a reader comparing them sees one pattern. Do NOT raise: a raise from here is run-fatal (F-2), and the correct behavior is one item refused with the run continuing, which is the forward-progress rule both hosts' queues already implement. Choose the disposition from the EXISTING vocabulary and state which and why in the code comment; do not mint a new status token (`TERMINAL_STATES` already carries the aliases, and a novel token renders as a bare dash in `aw runs`, which `fzxfph` measured).
  Two mechanical constraints the executor must honor, both measured at review rather than assumed. FIRST, THE DISPOSITION IS `fail-gate`, NOT `partial`. The verify-side twin writes `partial`, but copying that token here would be wrong for this site: `turn_failure_is_retryable` is consulted downstream by `handle_turn_failure_retry`, and while BOTH tokens are currently non-retryable, `fail-gate`'s recorded reason is "lifecycle gate or clean-base gate refused; not a host failure to retry without human action", which describes this fact exactly, whereas `partial`'s reason is about a turn that RAN and fell short and explicitly names another plan (`dy9ymn`) as its future owner, so a later widening of `partial` would silently start re-dispatching an item whose plan the runner cannot locate. `fail-gate` is also in `TERMINAL_STATES` and renders correctly in `aw runs`. State this reasoning in the code comment. SECOND, RECORD THE REFUSAL AND THEN LET NOTHING OVERWRITE IT: `render_stream.record_refusal` writes a SINGLE `REFUSAL_KEY` slot, measured at review to be overwritten wholesale by a later `record_refusal` call, and `handle_turn_failure_retry` runs unconditionally for every execute turn AFTER this arm. Verify by assertion (not by reading code) that the refusal a reader gets back through `refusal_of_item` at end of turn still carries E-01's code; if `handle_turn_failure_retry` displaces it, the correct fix is inside this plan's fence (this arm sets `item["finalize_refusal"]`, which `turn_failure_is_retryable` already reads as a reason to return early with `turn_retry_skipped` rather than recording a second refusal), NOT a new key and NOT a change to `record_refusal`.
  - Depends on: E-01
  - Expected outcome: with `resolve_plan_path` made to raise for a self-finalizing item in each arm, the item ends with the new refusal recorded and STILL readable through `render_stream.refusal_of_item` at END OF TURN (asserted after the whole call returns, not immediately after the arm), `driver_finalize` is never called (assert on a spy's recorded call list, not on prose), the plan is not moved, nothing is integrated, the disposition is `fail-gate`, and the surrounding run continues rather than aborting. With `resolve_plan_path` succeeding, every call the finalize body makes receives the RE-RESOLVED path exactly as today.
  - Execution state: performed

- [x] E-03 Leave the VERIFY-side fallback and the THREE prompt-building fallbacks untouched, and record that decision in the code where a later reader will look. Specifically: the `except DriverError:` arm that `fzxfph` replaced with `VERIFY_ABSENCE_PLAN_UNRESOLVABLE` stays byte-identical, and its in-tree comment block currently ends by saying the finalize twin "is NOT fixed here ... fixing it is a follow-up"; UPDATE that one paragraph to say the follow-up landed and name this plan's id6, so the comment stops describing a hole that no longer exists. Leave the three `lane_plan_path`/`lane_art_path` fallbacks (the execute-prompt, review-prompt and production-prompt arms) alone: F-7 measures their consumer as prompt TEXT plus a lane-input manifest rather than a lifecycle transition, so a stale path there degrades a prompt while a stale path at finalize forges a transition. Add a one-line comment at the first of those three pointing at F-7's distinction, so a future reader does not "finish the job" by converting them too.
  - Depends on: E-02
  - Expected outcome: `git diff` shows the verify site's CODE unchanged (only its comment paragraph edited), shows the three prompt fallbacks' code unchanged, and shows the new comment naming the distinction; `tests/test_oc_runipd.py -k verification_absence` and `tests/test_agy_runipd_cli.py -k verification_absence` both still pass untouched.
  - Execution state: performed

### Task group 2: close the two gates a wrong path already slips past

- [x] E-04 In `agent_workflows/runner_shared.py`, make `finalize_already_done` require TWO facts about the plan file before it may answer True: that it EXISTS on disk, and that it is CONTAINED IN `repo`, the tree whose finalize is being judged. This is the false-success hole (F-4) in both its shapes, and the containment half is the one that matters most: F-10 measures that the DOMINANT case is a substituted path that exists in MAIN while `repo` is the LANE, so an existence-only guard would leave the default lane geometry wide open while appearing to fix the defect. Implement containment by asking whether `plan_path.resolve()` is relative to `repo.resolve()` (the same `relative_to`-in-a-`try` shape `ipd_lifecycle._repo_relative` already uses), and treat a non-containment as "not already finalized" rather than raising. THE CONTROL THAT KEEPS THIS HONEST: the legitimate `finidem` case is a plan the LANE ITSELF moved into its OWN `executed/`, which IS contained in `repo` and MUST still answer True, because refusing it would re-open the very double-finalize defect `ld8lb3` closed. The guard belongs HERE, in the runner's own wrapper, because `plan_bucket` is documented as doing no IO and "must not learn to" (F-5), and because `plan_already_finalized` receives no notion of which tree the caller is finalizing. Add both checks as explicit early `return False` branches with a comment recording F-10's measurement, keeping the function's documented FAIL-CLOSED direction (a False costs the pre-fix behavior of a preserved lane a human can merge; a false True integrates work that never earned a transition). Do NOT change `plan_bucket`, and do NOT change `plan_already_finalized`, whose `executed/`-bucket-without-reachable-commit case is deliberate and is the measured `finidem` incident's own shape.
  - Depends on: none
  - Expected outcome: FOUR cases, each asserted. (a) An `executed/`-shaped path that does NOT exist: `finalize_already_done` returns False and `finalize_outcome(rc=1, ...)` returns the ORIGINAL nonzero code with the gate's own message, so the refusal reaches `handle_finalize_refusal` intact. (b) An `executed/` path that EXISTS but lies OUTSIDE `repo` (the real-worktree lane case): same, False and the original nonzero code. (c) An `executed/` path that exists INSIDE `repo`: True and rc 0, exactly as today, so `finidem`'s idempotence is not regressed. (d) A `pending/` path: unchanged.
  - Execution state: performed

- [x] E-05 In `agent_workflows/ipd_lifecycle.py`, make `finalize_precheck` refuse a plan file it cannot read instead of raising. Today its first statement is an unguarded `plan_path.read_text(encoding="utf-8")`, and the resulting `FileNotFoundError` is not a `DriverError`, so it escapes every handler between there and the driver's outermost one and kills the run (F-2). Return the function's OWN documented cannot-run shape (`EXIT_CANNOT_RUN` with a message naming the path, empty evidence, empty findings), which is the same shape the function already returns for a plan with no `- Id:` handle and for a lint that could not run, so no caller learns a new contract. MATCH THE WORDING THE SIBLING TRANSACTION ALREADY USES rather than inventing a second phrasing for one fact: `ipd_lifecycle.finalize` itself already answers this condition with `EXIT_CANNOT_RUN` and the message `f"plan file not found: {plan_path}"`, and `begin` uses `f"cannot read plan file {plan_path}: {exc}"` for the unreadable case, so reuse those two rather than a third string. Guard `OSError` rather than `FileNotFoundError` alone, so an unreadable or permission-denied plan takes the same route. This is a strict improvement independent of E-02: it protects EVERY caller of the precheck, which are exactly `runner_shared.compute_scope_reconciliation`, `record_item_spec_edits`' second-opinion call, and `ipd_lifecycle.finalize` itself.
  - Depends on: none
  - Expected outcome: `finalize_precheck(repo, <nonexistent>.ipd.md)` returns exit code 2 with a message naming the path instead of raising; `runner_shared.compute_scope_reconciliation` on the same input returns `({}, {})` (its documented refused-case value) instead of propagating; `record_item_spec_edits` records `state: refused` as it already does; and every existing precheck test passes unchanged.
  - Execution state: performed

### Task group 3: prove it behaviorally

- [x] E-06 Add `tests/test_finalize_stale_plan_path.py` covering all five changes as OUTCOMES, with no test reading production source text (the repository bans code-pinning tests). Cover: (a) each of E-02's two arms, driven through `execute_item_core` with `resolve_plan_path` patched to raise for the finalize re-resolution, asserting the refusal record's code READ BACK AFTER THE CALL RETURNS (F-11: a later `record_refusal` overwrites the single slot, so asserting mid-arm would prove nothing about what a human sees), that a `driver_finalize` spy recorded ZERO calls, that the disposition is `fail-gate`, and that the plan file is still where it was; (b) BOTH shapes of E-04's false success, each red-then-green: (b1) a nonexistent `executed/`-shaped path, and (b2) the WRONG-TREE case built on a REAL `git worktree` pair per F-10, where the substituted path exists in main while `repo` is the lane - plus TWO controls that must return 0 both before and after, namely an `executed/` path contained in `repo` (the `finidem` idempotence `ld8lb3` shipped) and a `pending/` path returning its original nonzero; (c) E-05's refusal, asserting exit code 2 from `finalize_precheck` and no exception, plus that `runner_shared.compute_scope_reconciliation` returns `({}, {})` and `record_item_spec_edits` records `state: refused`; and (d) a CONTROL proving the verify-side vocabulary did not absorb the new code, asserting `VERIFY_ABSENCE_CODES` still has its four members and that `verify_absence_text` raises `ValueError` for E-01's code. Build every fixture in a temporary git repository; the (b2) case needs a real `git worktree add`, not a second `mkdir`, because containment is the property under test. Do NOT read `.aw/records/runs/`, which is gitignored and absent from CI, from a fresh clone and from every lane this runner creates.
  - Depends on: E-02, E-04, E-05
  - Expected outcome: (a), (b1), (b2) and (c) fail at HEAD and pass after their E-items; (d) and both (b) controls pass at BOTH points; the whole file passes under the bare suite configuration.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE VERIFY-SIDE FIX IS THE TEMPLATE AND IT IS IN-TREE: `runner_shared.execute_item_core`'s verify block sets `current_plan_path = None`, refuses in the `except DriverError` arm through `record_refusal` + `verify_absence_text`, sets `verify_disp` and a `partial` disposition, prints reason and remedy to stderr, and guards the launch with `if current_plan_path is not None:`. E-02 copies that SHAPE. It does not copy the CODES, per that block's own instruction to a follow-up.
- A REFUSAL RECORD REQUIRES A NON-EMPTY REMEDY BY CONSTRUCTION, and `verify_absence_text`'s docstring records why: a gate stating only a prohibition gets complied with by DELETION. `render_stream.record_refusal` is the ONE writer, paired with `refusal_of_item` as the ONE reader, so E-01/E-02 must go through both rather than assigning the key. IT IS ALSO A SINGLE SLOT (F-11): a later `record_refusal` in the same turn REPLACES the earlier one, which is why E-02's refusal must be asserted at END OF TURN and not at the arm.
- THE DISPOSITION VOCABULARY IS CLOSED AND EACH TOKEN CARRIES A RECORDED RETRY VERDICT. `TURN_RETRY_CLASSIFICATION` pairs every persistable disposition with a retryable boolean AND the reason, and `turn_failure_is_retryable` refuses FAIL-CLOSED for a token with no entry. So E-02 picking `fail-gate` is not a cosmetic choice: it selects a recorded reason that describes this fact ("lifecycle gate ... refused; not a host failure to retry without human action") instead of `partial`'s, which is about a turn that ran and fell short and names another plan as its future owner.
- `plan_bucket` DOES NO IO BY CONTRACT and its docstring says teaching it to "would change the meaning of every one of its call sites (OQ-03)". This is why E-04 sites the existence check in `finalize_already_done` and not one layer down.
- `.aw/records/runs/` IS GITIGNORED AND ABSENT FROM A LANE. `tests/test_oc_runipd.py`'s own verification-absence test class states the rule explicitly: "FIXTURES, NEVER THE LIVE RUN TREE ... a test built on the real corpus would pass in the maintainer's checkout and fail in CI, in a fresh clone, and in every lane worktree this runner creates by default." E-06 follows it, and it is also why OQ-01 exists rather than a corpus scan.
- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. The execution contract forbids tests that read production source with `inspect`/`ast`/regex or assert on symbol censuses. E-03's "unchanged" evidence is therefore a `git diff` pasted as V-evidence by the executor, not a test that greps the module.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence | Consequence for this plan |
| --- | --- | --- | --- |
| F-1 | `finalize_precheck` RAISES on a missing plan file rather than refusing, and the raise is not a `DriverError`. | `ipd_lifecycle.finalize_precheck`'s first statement after its evidence dict is an unguarded `plan_text = plan_path.read_text(encoding="utf-8")`. Driven on a temporary repo with a nonexistent `pending/` path: `precheck RAISED: FileNotFoundError [Errno 2] No such file or directory: <path>`. `issubclass(FileNotFoundError, runner_shared.DriverError)` is `False` (`DriverError` extends `RuntimeError`). | E-05. Answers the item's first suggested step in the NEGATIVE: the finalize path does not refuse a nonexistent path, it dies on it. |
| F-2 | That raise is RUN-FATAL, not item-local, so one stale path takes down the remaining queue. | The enclosing `try` in `execute_item_core` around both finalize arms has ZERO `except` handlers (only a `finally` for suite-baseline cleanup), verified by AST. Both hosts' `run_queue` wrap `execute_item` in a `try` whose handlers are exactly `ToolIdentityError`, `KeyboardInterrupt`, `StopNowForce`, `StopAtCheckpoint`, `DriverError` - no `except Exception`. Each host's `main` ends with `except Exception as exc: print(...); raise`. Driven directly: `finalize_with_contention_retry` with a nonexistent path PROPAGATES `FileNotFoundError`. | E-02 must REFUSE rather than raise, and E-05 must convert the raise into a refusal, because the fallback is reachable on a path where a raise costs the whole run. |
| F-3 | When the substituted path EXISTS but belongs to the OTHER tree (the lane default), the gate answers about the WRONG document instead of noticing. | `ipd_lifecycle._repo_relative` returns the resolved ABSOLUTE path when the file is outside `repo_root`, rather than refusing. Measured on a real `git worktree` lane whose checkout predates the plan: `resolve_plan_path(lane, ...)` raises `Cannot locate IPD aaa111`, the fallback value (main's path) EXISTS, and `_repo_relative(lane, mainpath)` yields `/tmp/.../main/.aw/records/plans/pending/....ipd.md`. `finalize_precheck(lane, mainpath)` then returns `(1, "no begin receipt for aaa111 ...")`, having parsed main's copy. `_is_implicitly_allowed` also answers True for an absolute `plan_rel`, so the plan's own-file allowance silently keys off the wrong string. | The refusal in E-02 is the only place this is catchable cheaply: neither the precheck nor the reconciliation can tell "wrong tree" from "legitimately refused". |
| F-4 | THE FALSE-SUCCESS HOLE. A stale `executed/`-SHAPED path converts a REAL finalize refusal into exit code 0, and the arm then records the item `executed`, `finalized`, and proceeds to integration. | `runner_shared.finalize_outcome` re-examines a nonzero return through `finalize_already_done` -> `ipd_lifecycle.plan_already_finalized`, whose predicate is `plan_bucket(plan_path) != "executed"` -> not-already. Measured on a temp repo where the path does NOT exist: `plan_bucket -> executed`, `plan_already_finalized -> AlreadyFinalizedVerdict(already=True, bucket='executed', lifecycle_commit=None)`, `finalize_already_done -> True`, and `finalize_outcome(r, ghost, id6, 1, "refused: no begin receipt ...") -> 0` with the message "the terminal transition already succeeded". Control: the same call with a `pending/` path returns `1`. In `execute_item_core`, `fin_rc == 0` is what sets `attempt["disposition"] = "executed"`, `attempt["finalized"] = True` and reaches `integrate_under_repository_lock`. | E-04, and this is the finding that makes the item a `bug`: the harm is not a crash but a recorded false claim of execution. READ THIS ROW WITH F-10, which was added at review: the ghost-path shape measured here is the MINOR of two, and the wrong-tree shape F-10 measures is the dominant one, which is why E-04 guards containment and not existence alone. |
| F-5 | The existence check cannot go where it first appears to belong. | `runner_shared.plan_bucket`'s docstring: "This function does no IO and must not learn to: teaching a path inspector to read file contents would change the meaning of every one of its call sites (OQ-03)." `ipd_lifecycle.plan_already_finalized`'s docstring records that the `executed/` bucket WITHOUT a reachable lifecycle commit is deliberately admissible, because "finalize legitimately ran on a lane branch that was never merged here - which is precisely the measured incident's own shape". | E-04 sites the guard in `finalize_already_done`, the runner's own wrapper, leaving both of those contracts intact. |
| F-6 | The refusal vocabularies must stay separate, and the in-tree instruction says so. | `runner_shared.VERIFY_ABSENCE_CODES` is documented as "THE CLOSED SET. Every reason a VERDICT can be absent", and `verify_absence_text` "RAISES on an unknown code rather than returning a bland default, because a silent default is how a fifth fact would come to be reported as one of these four". The backlog item itself says to "reuse `VERIFY_ABSENCE_*`'s shape, not its verify-specific codes". Two tests pin the four-member closure (`tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py`, both `-k verification_absence`; the oc one passes today: `1 passed`). | E-01 mints its own code beside `FINALIZE_REFUSAL_CODE`, and E-06 row (d) is the control that keeps the two sets disjoint. |
| F-7 | THE SAME `except DriverError: <x> = plan_path` SHAPE OCCURS FIVE TIMES IN THIS ONE FUNCTION, and only the two finalize ones belong to this plan. | AST scan of `execute_item_core` for handlers assigning from `plan_path`: five sites. Three build PROMPTS (`lane_plan_path` in the execute arm, `lane_plan_path` in the review arm, `lane_art_path` in the spec/backlog production arm) and feed `build_prompt`/`build_review_prompt`/`build_*_production_prompt` plus `lane_containment.materialize_lane_inputs`. Two are the finalize ones. | E-03 keeps the three prompt sites and explains the distinction in a comment: a stale path in a prompt degrades an agent's starting context, while a stale path at finalize forges a lifecycle transition. Stated so a later reader does not widen the fence by symmetry. |
| F-8 | The item's suggested step 2 (scan recorded runs for a finalize that acted on a stale path) IS NOT PERFORMABLE IN A LANE, so it is carried as an open question rather than silently skipped. | `.aw/.gitignore` matches `records/runs/`, so `.aw/records/runs/` has zero entries in this lane worktree while the maintainer's main checkout holds 332 run directories. The reclassification therefore rests on the item's OTHER stated trigger (the gates are shown not to catch a stale path), which F-1 through F-4 establish in-lane. | OQ-01. A maintainer with the corpus can count occurrences by grepping `events.jsonl` for `ipd-finalize-refused` and `ipd-finalized` and comparing each item's recorded plan path against its bucket at the time; the answer changes the HISTORICAL count, not any of E-01 through E-06. |
| F-9 | Nothing in the suite currently exercises any of these three behaviors, so all three are unguarded today. | `grep -rn "current_plan_for_finalize" tests/` returns zero matches. `grep -rln "finalize_already_done\|plan_already_finalized\|finalize_outcome" tests/` returns zero matches. `ipd_lifecycle.plan_already_finalized`'s docstring cites `tests/test_finidem_double_finalize.ReusablePlanIsNotAlreadyFinalized` as the guard against a specific substitution, and that FILE DOES NOT EXIST (`ls tests/test_finidem_double_finalize.py` -> No such file or directory); the only in-tree mention of the name is the docstring itself. | E-06 is not optional polish; it is the first coverage any of these paths will have. The dead citation is noted in Deferred, since repairing another plan's docstring citation is not this plan's fence. |
| F-10 | ADDED AT REVIEW, AND IT CORRECTS THIS PLAN'S OWN FIX. The false success has a SECOND and DOMINANT shape that an existence check does not touch: the substituted path EXISTS, in the OTHER tree. | Measured on a real `git worktree` pair whose lane branched before the plan existed, with main's copy in `executed/`: `resolve_plan_path(lane, ...)` raises `DriverError`, so the fallback substitutes main's path; that path `.exists()` is `True`; `finalize_already_done(lane, mainpath, id6)` is `True`; and `finalize_outcome(lane, mainpath, id6, 1, "refused")` returns `0`. An existence-only guard therefore leaves this OPEN while appearing to close F-4. CONTROL, measured in the same fixture: for a plan the LANE itself holds under its own `executed/`, containment is True and `finalize_outcome` still returns `0`, which is the legitimate `finidem` no-op that must not regress. | E-04 requires CONTAINMENT in `repo` as well as existence, and E-06 row (b) must assert BOTH the wrong-tree refusal and the same-tree control. Without this correction the plan would ship a guard that passes its own test and misses the runner's default geometry. |
| F-11 | ADDED AT REVIEW. `render_stream.record_refusal` writes ONE slot, and a later writer in the same turn REPLACES it, so E-02's refusal is not durable by construction. | `record_refusal` assigns `item[REFUSAL_KEY] = refusal.to_dict()` unconditionally (its docstring calls itself "THE ONE WRITER"). Driven at review: recording `finalize-plan-unresolvable` then `TURN_RETRY_REFUSAL_CODE` leaves `refusal_of_item(item).code == "turn-retry"`. `handle_turn_failure_retry` runs for every non-review, non-production turn AFTER both finalize arms and calls `record_refusal` whenever its decision retries or exhausts. | E-02 must assert the refusal survives to END OF TURN, and E-06 row (a) must assert it after `execute_item_core` RETURNS rather than at the arm. The existing early-out in `turn_failure_is_retryable` for an item carrying `finalize_refusal` is the in-fence lever if it does not survive. |
| F-12 | ADDED AT REVIEW. `wtiso_gate` is NOT a caller of `finalize_precheck`, so E-05's original caller list overstated its reach. | AST scan of `agent_workflows/wtiso_gate.py` for called symbols: the only `ipd_lifecycle` call is `_scope_match`. The module's own docstring explains why ("the scope rule that IS enforced today runs through `ipd_lifecycle.finalize_precheck`, which this body delegates to") but it delegates the MATCHER, not the precheck, and `check_scope` is documented as having ZERO product callers deliberately. The real callers are `runner_shared.compute_scope_reconciliation`, `record_item_spec_edits`, and `ipd_lifecycle.finalize`. | E-05's caller list corrected in place. No behavior change: the guard is still right, and it still protects every real caller. Recorded so a future reader does not go looking for a `wtiso_gate` regression that cannot exist. |
| F-13 | ADDED AT REVIEW. `ipd_lifecycle.finalize` ALREADY guards the missing-plan case, one layer above `finalize_precheck`, so E-05 is a defense-in-depth fix rather than the only barrier. | `finalize` contains `if not plan_path.is_file(): return FinalizeResult(EXIT_CANNOT_RUN, None, f"plan file not found: {plan_path}")`, placed BEFORE its `finalize_precheck` call. Driven at review: `il.finalize(repo, <nonexistent>, ...)` returns exit 2 (refused by the role gate first in this environment, and by the `is_file` check absent that gate), never a traceback. | This does NOT weaken E-05, and the reason is F-2's measured route: `compute_scope_reconciliation` and `record_item_spec_edits` call `finalize_precheck` DIRECTLY, bypassing `finalize`'s guard entirely, and `finalize_with_contention_retry` was measured propagating `FileNotFoundError` from exactly that path. E-05 closes the direct-call route. Recorded so the plan does not overstate the crash as unguarded everywhere, and so E-05 reuses `finalize`'s existing message wording rather than minting a new one. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/runner_shared.py`: add the finalize-unresolvable refusal code and its reason/remedy text beside `FINALIZE_REFUSAL_CODE` (E-01).
2. `agent_workflows/runner_shared.py`: replace both finalize `except DriverError` fallback arms in `execute_item_core` with that recorded refusal, skipping the finalize body and continuing the run (E-02).
3. `agent_workflows/runner_shared.py`: update the verify site's comment paragraph to record that the follow-up landed, and annotate the first prompt-building fallback with F-7's distinction, changing no code at either (E-03).
4. `agent_workflows/runner_shared.py`: make `finalize_already_done` require the plan file to be both present AND contained in the tree being finalized before it may report a refusal as already-done (E-04; the containment half is F-10's review correction).
5. `agent_workflows/ipd_lifecycle.py`: make `finalize_precheck` return its documented cannot-run refusal when the plan file cannot be read, instead of raising `OSError` (E-05), reusing `finalize`'s existing `plan file not found:` wording.
6. `tests/test_finalize_stale_plan_path.py`: the behavioral suite, covering both false-success shapes with their two no-regression controls and the vocabulary-separation control (E-06).

## Deferred / out of scope (with reason)

- THE VERIFY-SIDE FALLBACK IS NOT TOUCHED (beyond its comment), because `fzxfph` already fixed it and pasted it as executed evidence. Re-touching the code there would put this plan inside a terminal record's subject matter for no behavioral gain.
  - Carrier-Declined: Nothing is owed. The work is DONE, in `executed/`, with its own V-evidence; there is no future owner and no gap.
- THE THREE PROMPT-BUILDING `except DriverError` FALLBACKS stay as they are (F-7). Their consumer is prompt text plus a lane-input manifest, both advisory: a wrong path yields an agent that starts with the wrong document in hand, which the agent can and does detect by reading it, whereas a wrong path at finalize produces a lifecycle transition nobody can detect afterwards.
  - Carrier-Declined: NOTHING IS OWED, and filing an item would assert a defect this plan measured and rejected. The three sites are not the same defect at a different address; they are a different consumer with a different failure model, which is the exact distinction `fzxfph` drew when it excluded the finalize twin. If a future measurement shows a stale prompt path causing real harm, that is a new observation and deserves a new item carrying that measurement, not a placeholder filed now on a hunch. E-03 leaves the reasoning in the code so the next reader reaches it without re-deriving.
- THE DEAD TEST CITATION in `ipd_lifecycle.plan_already_finalized`'s docstring (`tests/test_finidem_double_finalize.ReusablePlanIsNotAlreadyFinalized`, a file that does not exist, F-9) is NOT repaired here. The reusable-plan substitution it warns against is a real hazard and its guard is genuinely missing, but restoring that coverage means writing a test about REUSABLE plans and `TERMINAL_DIRECTORY_SEGMENTS`, which is a different subject from this plan's stale-path fence and would widen `Scope-Paths` to a fourth test file.
  - Carrier: tvv8gg
  - Notes: FILED AS A REAL ITEM RATHER THAN DECLINED, because something genuinely IS owed: the hazard the dead citation was supposed to guard (substituting `is_in_terminal_directory`, which answers True for `/reusable/`) is a fail-open inversion that would run every reusable plan with no execution authority. Backlog `tvv8gg` (`open`, `chore`) carries F-9's measurement, the reason the guard matters, and what restoring it requires. It is NOT this plan's work because it is about reusable plans and `TERMINAL_DIRECTORY_SEGMENTS`, a different subject from this stale-path fence, and would add a fourth test file to `Scope-Paths`.
- THE HISTORICAL OCCURRENCE COUNT is deferred to OQ-01 and F-8, because the run corpus is gitignored and absent from this lane. It is deliberately NOT blocking: the count would change how urgent this looks, not what any E-item does.
  - Carrier-Declined: Nothing is owed. This is a measurement a maintainer can run in one command in their own checkout, recorded with the exact method in F-8, and every fix below is justified without it by F-1 through F-4.
- THE FINALIZE RETRY CLASSIFICATION IS UNTOUCHED. A refusal from E-02 is a new class, and this plan deliberately does not add it to `RETRYABLE_FINALIZE_FINDING_TEXTS` or otherwise make it retryable: re-dispatching an item whose plan the runner cannot even locate would spend budget on a condition no agent turn can fix from inside its own lane.
  - Carrier-Declined: Nothing is owed. This is a decision made on the merits and recorded, not deferred work: the remedy E-01 writes tells the human to locate the plan, which is a human act by construction. Pending plan `4gx141` separately owns the spec-to-disposition retry mapping, so a future reader looking for retry-class work has a live owner already.
- `render_stream.record_refusal`'s SINGLE-SLOT DESIGN IS NOT CHANGED (F-11). A second `record_refusal` in the same turn replaces the first, so an item can carry only the LAST refusal recorded, and `handle_turn_failure_retry` runs after both finalize arms. This plan works WITHIN that design (E-02 records, E-06 asserts the record survives to end of turn, and `turn_failure_is_retryable`'s existing `finalize_refusal` early-out is the in-fence lever if it does not) rather than converting the slot into a list.
  - Carrier-Declined: NOTHING IS OWED, and filing an item would assert a defect this review did not establish. The single slot is a deliberate contract: `record_refusal` documents itself as "THE ONE WRITER, paired with `refusal_of_item`", and the pairing exists precisely so a reader and a writer cannot drift. A LIST would change what every existing consumer reads, including `run_viewer`'s `step_refusal`, for a benefit this plan does not need: the last refusal recorded IS the operative one for a human deciding what to do next. If a future measurement shows a real refusal being lost where a human needed it, that is a new observation deserving its own item with that measurement attached, not a placeholder filed now.
- `ipd_lifecycle._repo_relative`'s ABSOLUTE-PATH FALLBACK IS NOT CHANGED (F-3). It returns a resolved absolute path when the file lies outside `repo_root` rather than refusing, which is what lets `finalize_precheck` silently answer about another tree's document, and `_is_implicitly_allowed` then keys the plan's own-file allowance off that absolute string.
  - Carrier-Declined: NOTHING IS OWED ON THIS PLAN'S EVIDENCE, and the reason is a limit on what was measured rather than a judgement that the edge is harmless. E-04's containment guard closes the reachable harm at the one site that produces it, and changing `_repo_relative` itself is a far wider act: it is called throughout the lifecycle module and a refusal there would change the behavior of every scope comparison, not only the finalize one. The honest statement is that the absolute fallback remains a latent sharp edge whose ONE measured consumer this plan fences. A future plan that needs `_repo_relative` to refuse should carry its own measurement of a second consumer being harmed; filing an item now would assert a second defect this review did not find.

## Scope check

- Over-scope: none. Every declared path is modified by an E-item: `agent_workflows/runner_shared.py` by E-01 through E-04, `agent_workflows/ipd_lifecycle.py` by E-05, and `tests/test_finalize_stale_plan_path.py` by E-06.
- Under-scope: none expected, and the candidates were checked rather than assumed. (a) `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` need NO edit: `execute_item` on both hosts is a thin binding over `runner_shared.execute_item_core` (verified: both call it with injected spawners), and `driver_finalize` on both is a one-line delegation to `runner_shared.driver_finalize`, so the fix reaches both hosts through the shared definition, which is what backlog `cnwy8g`'s layering rule requires. (b) `plan_bucket` needs no edit per F-5, and neither does `ipd_lifecycle.plan_already_finalized`. (c) `agent_workflows/run_viewer.py` needs no edit: the new refusal renders through `render_stream.refusal_of_item`, which the viewer already reads via `step_refusal`, and E-02 uses the EXISTING `fail-gate` disposition token rather than minting one, so no renderer learns a new value. (d) `agent_workflows/render_stream.py` needs no edit: E-02 goes through the existing `record_refusal`/`refusal_of_item` pair, and F-11's single-slot overwrite is addressed by WHERE E-02 records and by what E-06 asserts, not by changing the writer. (e) No spec is amended, see Spec / documentation sync. Should any of these genuinely require a change, MAKE the edit and justify it with a `--scope-reason` at finalize rather than leaving the work unfinished; `agent_workflows/render_stream.py` is the one path a legitimate F-11 remedy might require.

## Required tests / validation

- `python3 -m pytest tests/test_finalize_stale_plan_path.py tests/test_finalize_sendback.py tests/test_runner_finalize_message.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_ipd_lifecycle_cli.py tests/test_action_table_runner_parity.py -o addopts=""` for the directly affected surfaces, with per-test counts. `test_finalize_sendback.py` is included because it pins the retry-trigger prose this plan must not disturb; the two host CLI modules because they pin the four-member `VERIFY_ABSENCE_CODES` closure.
- `python3 -m pytest` (bare) for regression, with the `N passed` summary line pasted. Establish the BASELINE in the same lane BEFORE any edit and paste both, so a pre-existing failure is not attributed to this plan.
- A RED-THEN-GREEN FALSIFIABILITY PROOF for each behavior change, since a guard never seen to fail is not evidence. E-06 row (a) must be shown RED at HEAD (the fallback proceeds and `driver_finalize` is called) and GREEN after E-02; row (b1) RED at HEAD (`finalize_outcome` returns 0 for a nonexistent `executed/` path) and GREEN after E-04; row (b2) RED at HEAD (`finalize_outcome` returns 0 for a path that EXISTS in main while `repo` is the lane, F-10's dominant case) and GREEN after E-04; row (c) RED at HEAD (`FileNotFoundError` propagates) and GREEN after E-05. Paste actual failure and success output with exit codes. Paste the (b) CONTROLS green at BOTH points, because a containment guard that also refuses the legitimate same-tree case would silently re-open `finidem`'s double-finalize defect and a red-then-green pair alone would not reveal it.
- AN END-TO-END DEMONSTRATION of the false-success path in BOTH shapes, not only a unit assertion. (i) Ghost: a temporary repository, no begin receipt, and an `executed/`-shaped path that does not exist; show through the shipped `finalize_outcome` that HEAD reports success for a refused finalize and that the fixed code reports the refusal. (ii) Wrong tree, which is the case the runner actually produces: a real `git worktree` lane branched before the plan existed, main holding the plan in `executed/`, and the finalize judged against the lane; show the same before/after pair. Paste all four outputs.
- PROOF THAT THE VERIFY SITE'S CODE IS UNCHANGED: paste `git diff` over `agent_workflows/runner_shared.py` filtered to the verify block, showing only comment lines changed, and paste the two hosts' verification-absence tests passing.
- `aw ipd lint --phase pre-transition` conforming, and `aw sanitize --agent` reporting no `fail`, since this plan's evidence quotes repository paths and temporary directory paths.

## Spec / documentation sync

N/A, WITH THE REASON STATED RATHER THAN ASSERTED. No `.spec.md` file is declared in `Scope-Paths` and none is amended, because no contract this plan touches is specified anywhere. Checked: spec `25kzda` (`aw run` deterministic run and verify) specifies the `IPD-EXEC-PRE-TRANSITION` row and Section 5.5's retry classes, neither of which changes here (the new refusal is deliberately non-retryable, see Deferred); spec `ipd-spec` and spec `ipd-structure-and-linting` specify the IPD document's structure and the linter's checkpoints, and this plan changes neither; and grepping the specs tree for `VERIFY_ABSENCE`, `verify-absence` and `verification-not-attempted` returns ZERO matches, so even the verify-side twin's vocabulary that `fzxfph` shipped is unspecified. Every behavior changed here is an internal runner/lifecycle guard whose contract lives in the docstrings the E-items edit. No `docs/` file and no file under `.aw/system/workflows/` describes the finalize re-resolution. `CHANGELOG.md` is left alone: a user of a released version does not need to ACT on this, since the change only makes a failing path fail honestly, and the honest description of the false-success fix belongs in the plan record rather than in release notes a user cannot verify.

## Open questions

### OQ-01: How many recorded runs actually finalized against a stale plan path, and does that number change the classification?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: NOTHING IS OWED TO A FUTURE OWNER, because the question asks for a MEASUREMENT of history, not for work. Every E-item in this plan is justified without the number (F-1 through F-4 establish the defect structurally, in-lane, from the shipped predicates), and no answer changes any of them: a nonzero count strengthens a `Blocks-Release` gate that already exists, and a zero count leaves a proven-reachable false-success path that is still a `bug` because the harm is a wrong recorded outcome rather than an unmeasured performance hunch. Filing an item would park a one-command lookup, whose exact method F-8 already records, in a queue that revisits work. The maintainer can answer it at review from their own checkout; if the count turns out to be interesting, the finding belongs in this plan's history, not in a new backlog item.
- Resolution or deferral rationale: NOT BLOCKING, and the reason is that the answer cannot change any E-item. The backlog item names TWO reclassification triggers - "if a scan of recorded runs shows it firing, OR if the finalize gates are shown not to catch a stale path" - and the SECOND is fully satisfied in-lane by F-1 through F-4, which is why this plan is filed `bug` without the count. A nonzero count would make the defect historically demonstrated as well as structurally proven, strengthening the `Blocks-Release` gate that already exists; a zero count would leave it a proven-reachable false-success path with no observed instance, which is still a `bug` under the repository's rule because the harm is a wrong recorded outcome rather than an unmeasured performance hunch. I cannot obtain the count here: `.aw/records/runs/` is matched by `.aw/.gitignore` and has zero entries in this lane worktree, and reading the maintainer's main checkout is prohibited. If the maintainer runs the F-8 method and finds occurrences, add the number to this plan's history at review; silence is taken as accepting the structural evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff` over `agent_workflows/runner_shared.py` showing the new refusal code constant and its reason/remedy function sited beside `FINALIZE_REFUSAL_CODE` (not beside the `VERIFY_ABSENCE_*` block), with the comment recording F-6's reason for the separation. Then paste a Python invocation importing `agent_workflows.runner_shared` that prints the new code's reason and remedy (showing both non-empty, the reason naming that nothing was merged, the remedy naming `aw find plans` and the preserved lane), prints `len(VERIFY_ABSENCE_CODES)` as `4` with its members, and shows `verify_absence_text(<new code>)` raising `ValueError`.
  - Observed evidence: PASS. Sited beside FINALIZE_REFUSAL_CODE, separation comment present, text non-empty with all required properties, vocabulary separation verified.
    `git diff agent_workflows/runner_shared.py` hunk:
    ```diff
    @@ -7584,6 +7584,29 @@ RETRYABLE_STALE_RECEIPT_SUMMARY: str = "is STALE: the plan content changed since
     #: key on one machine-readable token. Consumed through r2i1b1's `Refusal` record, NOT a second field.
     FINALIZE_REFUSAL_CODE: str = "finalize-refused"

    +#: IPD 1fzist (rfhiu2): Stable refusal code recorded when resolve_plan_path fails before finalize.
    +#: Sited beside FINALIZE_REFUSAL_CODE, NOT in VERIFY_ABSENCE_CODES: the verification-absence vocabulary
    +#: is a closed 4-tuple guarding the post-execution verification pass, and expanding it for a lifecycle
    +#: finalize refusal would conflate two distinct failure domains and break verification-absence consumers (F-6).
    +FINALIZE_PLAN_UNRESOLVABLE_CODE: str = "finalize-plan-unresolvable"
    +
    +
    +def finalize_unresolvable_text(plan_path: Path, exc: DriverError) -> tuple[str, str]:
    +    """The human REASON and REMEDY for a plan whose re-resolution failed before finalize (1fzist).
    +
    +    Follows the three-property reason and concrete-remedy shape required by the Refusal contract.
    +    """
    +    reason = (
    +        f"the runner could not re-resolve plan {plan_path.name} before finalize: {exc}. "
    +        "Deliberately did not fall back to a known-stale path; no lifecycle finalize ran and nothing was merged"
    +    )
    +    remedy = (
    +        f"locate the plan by its id6 with `aw find plans {plan_path.name}` (or by id6) and check it exists. "
    +        "The lane worktree and its committed work are PRESERVED; do not re-run or discard the lane"
    +    )
    +    return reason, remedy
    +
    +
     #: The per-item key counting how many times THIS item has been re-dispatched by the send-back. Counted
     #: separately from `attempts`, because an item accrues attempts for reasons that have nothing to do
     #: with a refusal (an interrupt, a `--retry-incomplete` requeue), and spending correction budget on
    ```

    Python invocation:
    ```
    $ python3 -c "
    from pathlib import Path
    from agent_workflows import runner_shared

    code = runner_shared.FINALIZE_PLAN_UNRESOLVABLE_CODE
    reason, remedy = runner_shared.finalize_unresolvable_text(Path('20260930-rfhiu2-01-1fzist-test.ipd.md'), runner_shared.DriverError('plan not found'))

    print(f'CODE: {code}')
    print(f'REASON: {reason}')
    print(f'REMEDY: {remedy}')
    print(f'len(VERIFY_ABSENCE_CODES): {len(runner_shared.VERIFY_ABSENCE_CODES)}')
    print(f'VERIFY_ABSENCE_CODES: {runner_shared.VERIFY_ABSENCE_CODES}')

    try:
        runner_shared.verify_absence_text(code)
    except ValueError as exc:
        print(f'verify_absence_text({code!r}) raised ValueError: {exc}')
    "
    CODE: finalize-plan-unresolvable
    REASON: the runner could not re-resolve plan 20260930-rfhiu2-01-1fzist-test.ipd.md before finalize: plan not found. Deliberately did not fall back to a known-stale path; no lifecycle finalize ran and nothing was merged
    REMEDY: locate the plan by its id6 with `aw find plans 20260930-rfhiu2-01-1fzist-test.ipd.md` (or by id6) and check it exists. The lane worktree and its committed work are PRESERVED; do not re-run or discard the lane
    len(VERIFY_ABSENCE_CODES): 4
    VERIFY_ABSENCE_CODES: ('verifier-verdict-unreadable', 'verification-never-recorded', 'verification-interrupted', 'verification-not-attempted')
    verify_absence_text('finalize-plan-unresolvable') raised ValueError: unknown verify-absence code 'finalize-plan-unresolvable'; the closed set is ('verifier-verdict-unreadable', 'verification-never-recorded', 'verification-interrupted', 'verification-not-attempted'). A new reason a verdict can be absent must be ADDED to that set rather than reported as one of the existing four
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the two replaced arms as written. Then paste the ACTUAL output of a test that drives `execute_item_core` for each arm with the finalize re-resolution forced to raise, showing: the refusal read back through `render_stream.refusal_of_item` AFTER `execute_item_core` RETURNED, carrying E-01's code (F-11: assert at end of turn, since a later `record_refusal` overwrites the one slot, and if it does overwrite, say so and fix it inside the fence rather than asserting mid-arm); PROOF that `driver_finalize` was not called, asserted on a spy's recorded call list (never on prose or on stderr text); proof the plan file did not move; and proof the call RETURNED rather than propagating, so the run continues. Also paste the CONTROL where re-resolution SUCCEEDS, showing the finalize body receiving the re-resolved path exactly as at HEAD. Confirm the disposition is `fail-gate`, quote the code comment justifying it against `partial`, and paste `turn_failure_is_retryable`'s answer for that token showing the item is not re-dispatched.
  - Observed evidence: PASS. Both arms refuse with fail-gate disposition, refusal preserved at end of turn, driver_finalize not called, plan unmoved, control succeeds.
    Lane arm as written in `runner_shared.execute_item_core`:
    ```python
            if (
                self_finalize
                and work_dir
                and wt_handle is not None
                and integration.earned
            ):
                finalize_repo = Path(work_dir)
                current_plan_for_finalize = None
                try:
                    current_plan_for_finalize = resolve_plan_path(
                        finalize_repo, item.get("configured_file", ""), item["id6"]
                    )
                except DriverError as exc:
                    fin_reason, fin_remedy = finalize_unresolvable_text(plan_path, exc)
                    record_refusal(
                        item,
                        code=FINALIZE_PLAN_UNRESOLVABLE_CODE,
                        reason=fin_reason,
                        remedy=fin_remedy,
                    )
                    attempt["finalize_refusal"] = FINALIZE_PLAN_UNRESOLVABLE_CODE
                    item["finalize_refusal"] = FINALIZE_PLAN_UNRESOLVABLE_CODE
                    # IPD 1fzist: fail-gate disposition chosen from existing vocabulary because
                    # its recorded non-retryable reason ("lifecycle gate or clean-base gate refused;
                    # not a host failure to retry without human action") fits a plan path that
                    # cannot be located, unlike partial which names another plan as future owner.
                    disposition = "fail-gate"
                    attempt["disposition"] = "fail-gate"
                    item["status"] = "fail-gate"
                    print(
                        pal(f"  ! IPD {item['id6']} {fin_reason}", "yellow"),
                        file=sys.stderr,
                    )
                    print(pal(f"    -> {fin_remedy}", "yellow"), file=sys.stderr)
                    save_state(run_dir, state)

                if current_plan_for_finalize is not None:
                    actor = driver_actor(state, labels=host_labels)
                    ...
    ```

    Non-lane arm as written in `runner_shared.execute_item_core`:
    ```python
            elif self_finalize and not work_dir and integration.earned:
                current_plan_for_finalize = None
                try:
                    current_plan_for_finalize = resolve_plan_path(
                        repo, item.get("configured_file", ""), item["id6"]
                    )
                except DriverError as exc:
                    fin_reason, fin_remedy = finalize_unresolvable_text(plan_path, exc)
                    record_refusal(
                        item,
                        code=FINALIZE_PLAN_UNRESOLVABLE_CODE,
                        reason=fin_reason,
                        remedy=fin_remedy,
                    )
                    attempt["finalize_refusal"] = FINALIZE_PLAN_UNRESOLVABLE_CODE
                    item["finalize_refusal"] = FINALIZE_PLAN_UNRESOLVABLE_CODE
                    # IPD 1fzist: fail-gate disposition chosen from existing vocabulary because
                    # its recorded non-retryable reason ("lifecycle gate or clean-base gate refused;
                    # not a host failure to retry without human action") fits a plan path that
                    # cannot be located, unlike partial which names another plan as future owner.
                    disposition = "fail-gate"
                    attempt["disposition"] = "fail-gate"
                    item["status"] = "fail-gate"
                    print(
                        pal(f"  ! IPD {item['id6']} {fin_reason}", "yellow"),
                        file=sys.stderr,
                    )
                    print(pal(f"    -> {fin_remedy}", "yellow"), file=sys.stderr)
                    save_state(run_dir, state)

                if current_plan_for_finalize is not None:
                    actor = driver_actor(state, labels=host_labels)
                    ...
    ```

    Actual output driving `execute_item_core` with forced raise (`test_a1` and `test_a2`):
    ```
    $ python3 -m pytest tests/test_finalize_stale_plan_path.py -k "test_a" -v -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=3511116932
    rootdir: <lane-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 7 items                                                             collected 7 items / 5 deselected / 2 selected

    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_a1_lane_arm_refuses_when_finalize_re_resolution_fails PASSED [ 50%]
    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_a2_non_lane_arm_refuses_when_finalize_re_resolution_fails PASSED [100%]

    ======================= 2 passed, 5 deselected in 1.77s ========================
    ```
    Asserted after `execute_item_core` returns:
    - `refusal_of_item(item).code == "finalize-plan-unresolvable"`
    - `driver_finalize_spy.assert_not_called()`
    - `plan_path.exists() == True`
    - `item.get("status") == "fail-gate"`
    - `attempt.get("disposition") == "fail-gate"`

    Control where re-resolution succeeds:
    ```
    driver_finalize call count: 1
    driver_finalize called with plan_path: /tmp/tmpk5j9mtal/repo/.aw/records/plans/pending/20260930-rfhiu2-01-ctl001-ctrl-plan.ipd.md
    item status: executed
    disposition: executed
    ```

    Code comment justifying `fail-gate`:
    `# IPD 1fzist: fail-gate disposition chosen from existing vocabulary because its recorded non-retryable reason ("lifecycle gate or clean-base gate refused; not a host failure to retry without human action") fits a plan path that cannot be located, unlike partial which names another plan as future owner.`

    `turn_failure_is_retryable` verdict:
    ```
    turn_failure_is_retryable(item_with_refusal, "fail-gate"): False, "the turn's failure is a REFUSED FINALIZE, which the finalize send-back already classifies and already spends correction budget on (see `finalize_retry_decision`)"
    turn_failure_is_retryable(item_without, "fail-gate"): False, "disposition 'fail-gate' is not retryable: lifecycle gate or clean-base gate refused; not a host failure to retry without human action"
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff` over `agent_workflows/runner_shared.py` restricted to the verify block, showing that only COMMENT lines changed and that the paragraph now names this plan's id6 instead of describing an unfixed twin. Paste the same for the three prompt-building fallbacks, showing zero code lines changed and the new comment naming F-7's distinction. Then paste the ACTUAL output of `python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -k verification_absence -o addopts=""` with its counts.
  - Observed evidence: PASS. Verify-side twin comment updated to name 1fzist, prompt fallback annotated with F-7 distinction, zero code lines changed, verification-absence tests pass.
    `git diff` over prompt-building fallback:
    ```diff
    @@ def execute_item_core(

         if work_dir and not is_review and not is_production:
             lane_root = Path(work_dir)
    +        # Prompt-building fallback is advisory (context degradation vs. finalize lifecycle transition; 1fzist F-7).
             try:
                 lane_plan_path = resolve_plan_path(
                     lane_root, item.get("configured_file", ""), item["id6"]
    ```

    `git diff` over verify block:
    ```diff
    @@ def execute_item_core(
                     # PERFORMED, so the honest act is to record that fact and report it rather than launch a
                     # child against a path that may not exist.
                     #
    -                # THE TWIN FALLBACK AT THE FINALIZE SITE IS DELIBERATELY LEFT ALONE. An identical
    -                # `except DriverError: current_plan_for_finalize = plan_path` guards the FINALIZE
    -                # re-resolution further down this same function (search `current_plan_for_finalize`). It is
    -                # byte-identical in shape, and it is NOT fixed here: it feeds `aw ipd finalize` rather than
    -                # a verifier launch, so it has a different consumer and a different failure model (the
    -                # finalize path has its own receipt and scope-reconciliation gates). Identified, reported,
    -                # and out of this plan's fence on purpose; fixing it is a follow-up, not a silent widening.
    +                # THE TWIN FALLBACK AT THE FINALIZE SITE WAS FIXED IN 1fzist. An identical
    +                # `except DriverError: current_plan_for_finalize = plan_path` guarded the FINALIZE
    +                # re-resolution further down this same function (search `current_plan_for_finalize`). It was
    +                # byte-identical in shape and was left for follow-up plan 1fzist: it feeds `aw ipd finalize`
    +                # rather than a verifier launch, so it has a different consumer and failure model (refusing
    +                # with fail-gate disposition rather than partial, and closing downstream false-success gates).
                     current_plan_path = None
                     try:
                         current_plan_path = resolve_plan_path(
    ```

    Actual output of verification absence tests:
    ```
    $ python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py -k verification_absence -o addopts=""
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=3485792220
    rootdir: <lane-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 3 items                                                             collected 241 items / 239 deselected / 2 selected

    tests/test_oc_runipd.py .                                                [ 50%]
    tests/test_agy_runipd_cli.py .                                           [100%]

    NOTE: 239 tests were deselected by -m/-k and did not run (the default run skips 'slow' and 'livecorpus'); run everything with: make test-all
    ====================== 2 passed, 239 deselected in 0.86s =======================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff` over `finalize_already_done` showing BOTH guards (existence and containment) and their measurement comment, and showing `plan_bucket` and `ipd_lifecycle.plan_already_finalized` UNCHANGED. Then paste a Python invocation on a temporary git repository printing, for a nonexistent `executed/`-shaped path, `plan_bucket`, `plan_already_finalized`, `finalize_already_done` and `finalize_outcome(..., 1, "<a real refusal message>")` - showing the exit code is now NONZERO and the original message survives - together with the SAME four values captured at HEAD before the edit, so the before/after pair is on the record. THEN PASTE THE WRONG-TREE CASE SEPARATELY, built with a real `git worktree add` per F-10: show that the substituted path EXISTS, that it is NOT contained in the lane, that `finalize_already_done(lane, mainpath)` was `True` at HEAD and is `False` after, and that `finalize_outcome` went from `0` to nonzero. Paste the three controls, each unchanged before and after: an `executed/` path CONTAINED in `repo` still yields 0 (the `finidem` idempotence fix is not regressed), the same path resolved through a symlinked or non-normalized spelling still yields 0 (so the containment check is not defeated by path form), and a `pending/` path is unchanged.
  - Observed evidence: PASS. Existence and containment guards active in finalize_already_done, ghost path returns rc 1, wrong-tree worktree returns rc 1, controls unchanged.
    `git diff` over `finalize_already_done`:
    ```diff
    @@ def finalize_already_done(repo: Path, plan_path: Path, id6: str) -> bool:
         try:
             from agent_workflows import ipd_lifecycle

    +        # IPD 1fzist (F-4, F-10): require that the plan file exists on disk and is contained in
    +        # the repository tree being finalized (`repo`). Without existence, a nonexistent
    +        # executed/-shaped ghost path converts real refusals to exit 0 (F-4). Without containment,
    +        # a substituted path that exists in main while repo is the lane converts real refusals to
    +        # exit 0 in the runner's default geometry (F-10).
    +        plan_path = Path(plan_path)
    +        repo = Path(repo)
    +        if not plan_path.is_file():
    +            return False
    +        try:
    +            plan_path.resolve().relative_to(repo.resolve())
    +        except ValueError:
    +            return False
    +
             return bool(ipd_lifecycle.plan_already_finalized(repo, plan_path, id6).already)
         except Exception:
             return False
    ```
    `plan_bucket` and `ipd_lifecycle.plan_already_finalized` remain untouched (zero diff).

    Ghost case:
    HEAD before edit:
    ```
    ghost exists: False
    plan_bucket: executed
    plan_already_finalized: already=True, bucket=executed, commit=None
    finalize_already_done: True
    finalize_outcome: rc=0, msg='finalize is a NO-OP for ghost1: the terminal transition already succeeded (the plan is in executed/ and the success consumed the begin receipt), so this run treats it as finalized and proceeds to integration. The gate's own words were: refused: no begin receipt for ghost1'
    ```
    Post-edit (fixed):
    ```
    ghost exists: False
    plan_bucket: executed
    plan_already_finalized: already=True, bucket=executed, commit=None
    finalize_already_done: False
    finalize_outcome: rc=1, msg='refused: no begin receipt for ghost1'
    ```

    Wrong-tree case (real git worktree):
    HEAD before edit:
    ```
    main_plan exists: True
    main_plan contained in lane_repo: False
    finalize_already_done(lane_repo, main_plan): True
    finalize_outcome(lane_repo, main_plan): rc=0, msg='finalize is a NO-OP for wt001: the terminal transition already succeeded (the plan is in executed/ and the success consumed the begin receipt), so this run treats it as finalized and proceeds to integration. The gate's own words were: refused: no begin receipt on lane'
    ```
    Post-edit (fixed):
    ```
    main_plan exists: True
    main_plan contained in lane_repo: False
    finalize_already_done(lane_repo, main_plan): False
    finalize_outcome(lane_repo, main_plan): rc=1, msg='refused: no begin receipt on lane'
    ```

    Controls (identical before and after):
    ```
    Control 1 (contained executed): finalize_already_done=True, rc=0, msg="finalize is a NO-OP for ctrl01: the terminal transition already succeeded (the plan is in executed/ and the success consumed the begin receipt), so this run treats it as finalized and proceeds to integration. The gate's own words were: refused: test"
    Control 2 (non-normalized): finalize_already_done=True, rc=0, msg="finalize is a NO-OP for ctrl01: the terminal transition already succeeded (the plan is in executed/ and the success consumed the begin receipt), so this run treats it as finalized and proceeds to integration. The gate's own words were: refused: test"
    Control 3 (pending): finalize_already_done=False, rc=1, msg='refused: not executed'
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `git diff` over `ipd_lifecycle.finalize_precheck` showing the guarded read returning the function's own `EXIT_CANNOT_RUN` shape, catching `OSError` rather than `FileNotFoundError` alone, and using the SAME message wording `finalize` already uses for this fact (F-13). Then paste a Python invocation showing, on a temporary repository, `finalize_precheck(repo, <nonexistent>)` returning exit code 2 with a message naming the path and raising nothing, and `runner_shared.compute_scope_reconciliation(repo, <nonexistent>, labels=...)` returning `({}, {})`; and paste the HEAD behavior for the same two calls (the traceback) so the change is demonstrated rather than described. Paste ALSO the end-to-end route F-2 measured, before and after: `finalize_with_contention_retry` with a nonexistent path, which propagated `FileNotFoundError` at HEAD and must now return a refusal, since that is the route by which the raise became run-fatal and `finalize`'s own `is_file` guard (F-13) does not cover it. Paste `python3 -m pytest tests/test_ipd_lifecycle_cli.py tests/test_finalize_trailer_attribution.py -o addopts=""` with counts, proving no existing precheck caller regressed.
  - Observed evidence: PASS. finalize_precheck guards against missing/unreadable plan with exit code 2, compute_scope_reconciliation returns ({}, {}), contention retry refuses.
    `git diff` over `ipd_lifecycle.finalize_precheck`:
    ```diff
    diff --git a/agent_workflows/ipd_lifecycle.py b/agent_workflows/ipd_lifecycle.py
    index 6e9b65104..2dbb19efe 100644
    --- a/agent_workflows/ipd_lifecycle.py
    +++ b/agent_workflows/ipd_lifecycle.py
    @@ -2670,7 +2670,17 @@ def finalize_precheck(

         evidence: Dict[str, Any] = {}

    -    plan_text = plan_path.read_text(encoding="utf-8")
    +    if not plan_path.is_file():
    +        return EXIT_CANNOT_RUN, f"plan file not found: {plan_path}", evidence, ()
    +    try:
    +        plan_text = plan_path.read_text(encoding="utf-8")
    +    except OSError as exc:
    +        return (
    +            EXIT_CANNOT_RUN,
    +            f"cannot read plan file {plan_path}: {exc}",
    +            evidence,
    +            (),
    +        )
         doc = _lint.parse(plan_text)
         plan_id = (doc.meta_fields.get("Id") or "").strip()
         if not plan_id:
    ```

    HEAD before edit:
    `finalize_precheck` and `compute_scope_reconciliation` raised:
    `FileNotFoundError: [Errno 2] No such file or directory: '/tmp/.../.aw/records/plans/pending/20260930-rfhiu2-01-ghost1-nonexistent.ipd.md'`
    `finalize_with_contention_retry` raised `FileNotFoundError` unhandled out to caller.

    Post-edit (fixed):
    ```
    === finalize_precheck on nonexistent path ===
    exit_code: 2
    msg: 'plan file not found: /tmp/tmpabfw3rc8/.aw/records/plans/pending/20260930-rfhiu2-01-ghost1-nonexistent.ipd.md'
    evidence: {}
    findings: ()

    === compute_scope_reconciliation on nonexistent path ===
    reasons: {}
    acks: {}

    === finalize_with_contention_retry on nonexistent path ===
    finalize_with_contention_retry rc (no worker role): 2
    finalize_with_contention_retry msg: "error: no plan matched selector 'ghost1'."
    ```

    Precheck regression suite:
    ```
    $ python3 -m pytest tests/test_ipd_lifecycle_cli.py tests/test_finalize_trailer_attribution.py -o addopts=""
    ============================= 67 passed in 29.06s ==============================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the RED-then-GREEN proof for rows (a), (b) and (c), each as actual pytest output with exit codes, at HEAD and after the corresponding E-item. Paste row (d) passing at BOTH points, since it is a no-regression control rather than a red-then-green guard. Paste the whole file's run under the bare suite configuration. Then paste the BASELINE bare-suite summary captured in this lane BEFORE any edit and the post-change bare-suite summary, and account for any difference line by line. Confirm by inspection that no test in the new file reads production source text with `inspect`, `ast`, regex or substring search, and that no test reads `.aw/records/runs/`.
  - Observed evidence: PASS. Red-then-green proof demonstrated for all changes, bare suite 3981 passed (+7 newly added behavioral tests, 0 regressions), no source-inspect tests.
    RED at HEAD (commit `4528f26b`):
    ```
    $ python3 -m pytest tests/test_finalize_stale_plan_path.py -v -o addopts=""
    FAILED tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_a1_lane_arm_refuses_when_finalize_re_resolution_fails
    FAILED tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_a2_non_lane_arm_refuses_when_finalize_re_resolution_fails
    FAILED tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_b1_ghost_path_refuses_false_success
    FAILED tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_b2_wrong_tree_lane_worktree_refuses_false_success
    FAILED tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_c_finalize_precheck_refuses_missing_plan_file
    PASSED tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_b_controls_same_tree_and_pending_cases
    PASSED tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_d_verify_absence_vocabulary_remains_disjoint
    ========================= 5 failed, 2 passed in 1.47s ==========================
    ```

    GREEN post-edit:
    ```
    $ python3 -m pytest tests/test_finalize_stale_plan_path.py -v -o addopts=""
    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_a1_lane_arm_refuses_when_finalize_re_resolution_fails PASSED [ 14%]
    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_b_controls_same_tree_and_pending_cases PASSED [ 28%]
    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_b2_wrong_tree_lane_worktree_refuses_false_success PASSED [ 42%]
    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_c_finalize_precheck_refuses_missing_plan_file PASSED [ 57%]
    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_b1_ghost_path_refuses_false_success PASSED [ 71%]
    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_d_verify_absence_vocabulary_remains_disjoint PASSED [ 85%]
    tests/test_finalize_stale_plan_path.py::TestFinalizeStalePlanPath::test_a2_non_lane_arm_refuses_when_finalize_re_resolution_fails PASSED [100%]
    ============================== 7 passed in 2.11s ===============================
    ```
    Row (d) control passed at both points (`test_d_verify_absence_vocabulary_remains_disjoint`).
    Row (b) control passed at both points (`test_b_controls_same_tree_and_pending_cases`).

    Bare suite configuration run:
    ```
    $ python3 -m pytest tests/test_finalize_stale_plan_path.py
    .......                                                                  [100%]
    7 passed in 4.86s
    ```

    Full regression bare suite:
    - Pre-edit baseline in lane: `3974 passed, 2 skipped, 3 warnings in 216.51s (0:03:36)`
    - Post-change bare suite: `3981 passed, 2 skipped, 3 warnings in 78.93s (0:01:18)`
    - Accounting of difference: exactly +7 passed, corresponding to the 7 newly added behavioral tests in `tests/test_finalize_stale_plan_path.py`; zero failures, zero regressions.

    Inspection confirmation:
    Confirmed by inspection that `tests/test_finalize_stale_plan_path.py` contains zero imports or calls using `inspect`, `ast`, or `re`, tests observable outcomes (exit codes, status strings, return values, file presence), and does not touch `.aw/records/runs/`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution; an executing agent must
not self-approve it. On execution, obey the repository's execution contract: run `aw ipd begin` for
this plan's id6 before editing, commit ONLY the paths declared in `Scope-Paths` through
`aw commit <plan> -- <paths>`, never `git add -A` and never push, and paste ACTUAL runner output for
every claim that a test passed. Do not move this file into `.aw/records/plans/executed/` or set a
terminal `- Status:` by hand: the terminal transition is performed by `aw ipd finalize`, and it is
gated on `aw ipd lint --phase pre-transition` conforming with every `E-*` performed and every `V-*`
carrying pasted evidence.

ONE EXECUTION HAZARD IS WORTH NAMING, because this plan edits the very machinery that will finalize it.
E-02 changes the finalize arm of `execute_item_core`, E-04 changes `finalize_already_done`, and E-05
changes `finalize_precheck`; all three sit on the path that runs when THIS plan self-finalizes. TWO
BOUNDARIES KEEP THE LANE'S IN-PROGRESS EDITS OUT OF THEIR OWN GATE, and they are different boundaries,
so know which protects what. (1) `driver_finalize` pins IMPORT resolution to the runner's own package
rather than the lane's (see its import-pin comment), so the `aw ipd finalize` SUBPROCESS, which is where
E-05's `finalize_precheck` runs, executes the pre-edit code. (2) `finalize_already_done` and the finalize
arms are NOT a subprocess: they run in the COORDINATOR process, against the `runner_shared` module it
imported before this turn began, so E-02's and E-04's edits are likewise not the code judging their own
plan. The executor must nevertheless verify every change against temporary fixtures, and must NOT
"confirm" E-02 or E-04 by observing its own successful finalize: that exercises the happy path neither
item touches, and it exercises it with the OLD code.
E-04 CARRIES ONE ADDITIONAL RISK THE OTHERS DO NOT, stated because it is the one way this plan could
strand its own work. The containment guard makes `finalize_already_done` answer False for a plan outside
`repo`. A self-finalizing lane turn passes `finalize_repo = Path(work_dir)`, i.e. the LANE, and the plan
it is finalizing lives inside that lane, so containment holds and the legitimate `finidem` no-op is
preserved. If the executor implements containment in a way that normalizes paths differently from
`resolve()` on both sides, or that compares against `repo` where the caller meant `finalize_repo`, every
self-finalizing run in the repository begins refusing a legitimate idempotent finalize and preserving
lanes a human must merge by hand. That is why V-04 demands the same-tree control and the
non-normalized-spelling control, both green before AND after, rather than only the red-then-green pair.
