# IPD: Dispatch a to-review spec to the spec review and advance it only on a conforming review record

- Date: 2026-09-26
- Kind: child
- Concern: `aw oc run reviews --type spec` can SELECT the specs awaiting review, and after plan `8l8dgb` a queue can CARRY one, but nothing can RUN one (spec `z7nbn1` section 0, 1.6 first bullet, acceptance 5.4). Measured at HEAD `310ea53e`: the only review prompt is `runner_shared.build_review_prompt`, which returns `/plan-review <path>` unconditionally; `runner_shared.reconcile_disposition`'s review rung reads the artifact through `resolve_plan_path` and returns `reviewed` on exit 0 even when the status did not change ("if status in (reviewed, approved): return status ... return reviewed"); and the `--full-auto` bridge after a review (`is_plan_review_approved` / `set_plan_approved`) is plan-only. Handing a spec to that path would run the WRONG workflow (`/plan-review`'s IPD-lint preflight and `Readiness` write corrupt a spec, per the `spec-review` row of `.aw/system/workflows/index.md`) and would report success for a turn that never advanced the spec. The spec-side machinery already exists and must be CONSUMED, not rebuilt: the `/spec-review` workflow (`.aw/system/workflows/spec-review/spec-review.md`, shims under `.opencode/commands/` and `.claude/commands/`) advances a spec with `aw specs set reviewed <id6>`, and that transition already REFUSES without a conforming record through `specs._review_attestation_refusal` over `review_findings.review_attestation_missing(repo, id6, "spec")`.
- Scope: IN: (a) type-appropriate review dispatch: a queue entry with `artifact_type: spec` and action `review` gets the `/spec-review <path>` command (same argv-safety and lane-isolation-notice shape as `build_review_prompt`), and the run record names the handler (`review_handler: spec-review` on the attempt and in the `ipd-started`-equivalent event); (b) spec-aware disposition: after the turn, the spec is `reviewed` ONLY if its on-disk `- Status:` is `reviewed` AND `review_attestation_missing(repo, id6, "spec")` is `None`; otherwise the item ends `fail-gate` with a recorded refusal naming what is missing and the spec is left as it was; (c) the review output commit/integration for a spec lane scoped to the spec file, its history, and its review record (`classify_review_writes` keys on the id6, which the spec path and the record path both carry); (d) the `--full-auto` approval bridge is NEVER applied to a spec (spec `25kzda` 3.3: a reviewed spec stops at the human approval gate "including under `--full-auto`"); (e) replace plan `8l8dgb`'s item-local "no dispatcher" refusal for spec review with this dispatch. OUT: spec `draft` completeness (no spec completeness parser exists; `draft` stays `undetermined` and plan `jdn790` refuses it); `--action review` on a `reviewed` spec (re-review row of `25kzda` 3.3) beyond confirming the existing `enforce_requested_action` legality still refuses it until a later change; the review workflow body itself.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_spec_review_dispatch.py, tests/test_typed_queue_entries.py
- Item-Dependencies: executed:jdn790
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 4
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2ptgds

## Workflow history
- 2026-09-28 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 2ptgds verified (set artdispatch, attempt 1). [Scope reconciliation - widened-scope tests/test_typed_queue_entries.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run)]
- 2026-09-27 approved (aw set): status set to approved

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 all FIXED; review record `.aw/records/reviews/20260926-artdispatch-04-2ptgds-dispatch-a-to-review-spec-to-the-spec-review-and-advance-it.review.md`. Re-verified F-1..F-5 at lane HEAD 9c94ff0b: every seam reproduced, and F-4 additionally reproduced end to end on a scratch repo (setter refuses without a record, succeeds with one, and MOVES the spec to reviewed/). ADDED one HIGH finding: scope (d)'s "the bridge is NEVER applied to a spec" reads as policy but the bridge's first statement is a resolve sitting OUTSIDE its own try, and executed plan mxzogk makes that resolve fail closed on a .spec.md, so the first --full-auto run whose spec review SUCCEEDS raises DriverError and records the item failed-safely after a review that worked (F-6); E-04 now adds an explicit type guard ahead of the resolve. Also fixed a claim that cannot fire (F-7: item_needs_approval returns False for any review item by construction, and NEEDS_INPUT_KEY is written once at queue build and never recomputed, so the approval gate spec 25kzda 3.3 requires had no reporter; E-05 must choose and record one), a scope premise true only for id6-bearing filenames (F-8: 1 of 19 id-bearing specs is legacy-named and grandfathered, so its own file would be left uncommitted), an unstated read-tree dependency (F-9: reconcile_disposition runs BEFORE the lane commit and the integration, so the gate works only because both predicates are filesystem reads), an unstated directory move (F-10), and a second plan-shaped string that lands in git history (F-11). Split the four items into nine (E-01..E-09) and rebuilt the V checklist to a 9-item bijection. `aw ipd lint --phase review-finalize` conforming, 0 findings.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 04 of Set artdispatch). build_review_prompt, reconcile_disposition's review rung and the full-auto bridge measured plan-only at HEAD 310ea53e; the spec->reviewed attestation predicate and the /spec-review workflow and shims confirmed present, so this plan consumes them.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A to-review spec in a run gets the spec review, not the plan review, and the run counts it reviewed only when the spec actually reached `reviewed` through the setter with a conforming review record.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [x] E-01 TRACE THE REVIEW PATH at the executing HEAD for an entry with `artifact_type: spec`, action `review`, as plan `8l8dgb` leaves it. List every function `execute_item_core` calls between prompt build and final disposition that resolves or reads the artifact, and for each give a plan-only column AND ITS CALL-ORDER POSITION, because the ORDER is load-bearing for E-03 and the authored list was unordered (F-9). Verified at review, the order is: `build_review_prompt` -> `reconcile_disposition` (the review rung) -> `classify_review_writes` -> `commit_review_lane_output` -> `integrate_review_lane_branch` -> the `--full-auto` bridge (`resolve_plan_path`, `is_plan_review_approved`, `set_plan_approved`). SO THE DISPOSITION IS DECIDED BEFORE THE TURN'S OUTPUT IS COMMITTED AND LONG BEFORE IT REACHES MAIN; confirm that at the executing HEAD and record it, since E-03's correctness depends on reading the lane working tree rather than main or git. Also confirm both predicates are FILESYSTEM reads (`review_findings.subject_review_records` walks `review_dirs` with `open()`; the status read is a `read_text`), because a git-based read would refuse every correct review.

  Confirm `review_findings.review_attestation_missing` signature `(repo_root, subject_id6, subject_type="spec")` and that `aw specs set reviewed` refuses without a record (run it on a scratch spec and paste the refusal, then write a conforming record and paste the success). REPRODUCE THE DIRECTORY MOVE (F-10): paste the spec's path before and after the successful setter call, showing `to-review/` -> `reviewed/`, and show that `discover_specs` finds it at the new path under the same id6 while the frozen `configured_file` no longer exists. Confirm `/spec-review` is installed as a command shim for both hosts (`.opencode/commands/spec-review.md`, `.claude/commands/spec-review.md`) and how the agy host invokes a workflow (paste the agy review prompt shape). Finally, ENUMERATE THE LEGACY-NAMED SPEC POPULATION for E-06: every id-bearing spec whose filename does not contain its `- Id:` (1 of 19 at review, `4w7d6s`), and every `Subject-Type: spec` review record whose filename does not contain its subject id6 (0 of 12 at review). Both are live populations, not bars.
  - Depends on: none
  - Expected outcome: the trace table carries a plan-only column AND the call order, and shows the disposition preceding the commit and the integration; the setter refusal and success are pasted; the directory move is reproduced with `discover_specs` still resolving it; both hosts' invocation shape is recorded; the legacy-named spec and record populations are enumerated.
  - Execution state: performed

### Task group 2: dispatch

- [x] E-02 TYPE-APPROPRIATE REVIEW PROMPT. Make the review prompt builder dispatch on `queue_entry_type(item)` (plan `8l8dgb`): `ipd` -> `/plan-review <rel>` (byte-identical to today); `spec` -> `/spec-review <rel>`; any other type -> `DriverError` naming the type (no review handler). Keep the argv-safety rule (prose never on the command line) and the lane isolation notice on its own lines. Record `review_handler` (`plan-review`/`spec-review`) on the attempt, in the item, and in the turn-start event, so `aw runs show` names which handler ran (spec 5.4 "the run record shows which handler ran"). Resolve the spec path through `queue_artifact_path`, never `resolve_plan_path`.
  - Depends on: E-01
  - Expected outcome: a spec review item's prompt file starts `/spec-review .aw/records/specs/to-review/...spec.md`; a plan review item's prompt is unchanged; the attempt carries `review_handler: spec-review`.
  - Execution state: performed

- [x] E-03 SPEC-AWARE DISPOSITION. In `reconcile_disposition`'s review rung, for a spec entry: read the spec's current `- Status:` through `queue_artifact_path` and return `reviewed` ONLY when it is `reviewed` AND `review_findings.review_attestation_missing(<same tree>, id6, "spec") is None`; otherwise return `fail-gate` and record a refusal (`render_stream.record_refusal`) whose reason names the unmet half (status still `<x>`, or the attestation reason string) and whose remedy is the `/spec-review` command. A nonzero exit is `fail-gate` as today. Do NOT touch the plan branch's semantics.

  WHICH TREE, AND WHY IT MUST BE SAID RATHER THAN ASSUMED (F-9). Read the LANE tree when isolated, i.e. the existing `source = plan_repo or repo`, and pass that SAME root to `review_attestation_missing`. This is not a preference: by call order inside `execute_item_core`, `reconcile_disposition` runs BEFORE `commit_review_lane_output` and long before `integrate_review_lane_branch`, so at disposition time the spec's new `- Status:` and its review record may exist only as UNCOMMITTED working-tree files in the lane and are certainly not in main. The gate works anyway because BOTH predicates are filesystem reads (`review_findings.subject_review_records` walks `review_dirs` with `open()`; the status is a `read_text`), and it would refuse every correct review if it consulted main or git instead. State that in a comment at the call site.

  ALSO RESOLVE THROUGH `queue_artifact_path` BECAUSE THE SPEC MOVES (F-10). `aw specs set reviewed` relocates the file from `to-review/` to `reviewed/` (reproduced at review), so the frozen `configured_file` is stale the moment the turn succeeds. `queue_artifact_path` resolves a spec through `discover_specs`, which keys on `- Id:` and is location-independent, so it finds the moved file; a cheaper `repo / item["configured_file"]` read would produce a spurious `fail-gate` on exactly the successful path. Say so, so the cheap read is not reintroduced as an optimization.
  - Depends on: E-02
  - Expected outcome: a turn that set the spec `reviewed` with a conforming record ends `reviewed` even though the spec has MOVED directory and its output is not yet committed; a turn that exited 0 but left the spec `to-review` ends `fail-gate` with a refusal naming the unchanged status; a turn that hand-edited the status to `reviewed` without a record ends `fail-gate` naming the missing attestation.
  - Execution state: performed

- [x] E-04 GUARD THE `--full-auto` BRIDGE WITH AN EXPLICIT TYPE TEST, BEFORE ITS FIRST STATEMENT (F-6, spec `25kzda` 3.3 "Stop `needs_input`, including under `--full-auto`"). THIS IS A CRASH FIX AND NOT A POLICY STATEMENT, which is why it is its own item rather than a clause of E-03. The bridge reads `if is_review and disposition in ("reviewed","approved") and full_auto:` and its FIRST statement is `plan_curr = resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])`, sitting OUTSIDE the `try:` that opens on the following `set_plan_approved` call. Plan `mxzogk` (EXECUTED, Set `planpathtype` Order 01) makes `resolve_plan_path` raise `DriverError` naming the detected type for a `.spec.md`. So the first `--full-auto` run whose spec review SUCCEEDS raises out of `execute_item_core`, both hosts catch `DriverError` item-locally, and the item is recorded `failed-safely` with a resolver message AFTER a review that worked. Add `if queue_entry_type(item) != "ipd": <skip the bridge>` (or the equivalent guard on the enclosing condition) ahead of the resolve, so a spec never reaches it. Do not rely on the `try` to absorb it and do not widen the `try` to cover the resolve, which would convert a crash into a silent skip and lose the diagnostic for a genuine plan-path failure.
  - Depends on: E-03
  - Expected outcome: a `--full-auto` run that reviews a spec to `reviewed` ends the item `reviewed`, NOT `failed-safely`, with no `DriverError` recorded and no `set_plan_approved` call; the plan path's bridge behavior is byte-identical to today.
  - Execution state: performed

- [x] E-05 REPORT THE SPEC'S HUMAN-APPROVAL GATE THROUGH A MECHANISM THAT ACTUALLY FIRES (F-7). E-03's authored claim that `item_needs_approval` reports it is FALSE twice over and must not be relied on: the predicate returns `(action != "review") and status == "reviewed"`, so it is False by construction for a review item; and `NEEDS_INPUT_KEY` is written ONCE by the queue builder from the frozen `initial_status` and never recomputed after a turn, so a to-review spec freezes `needs_input: False` and stays there. The plan path is not a counterexample and explains why a spec needs something else: a reviewed plan gets its gate reported because the full-auto bridge REQUEUES it (`item["action"] = "execute"`, `item["status"] = "queued"`), and the next derivation sets the flag; a spec has no execute action, so it never gets that second pass. DECIDE AND RECORD one of: (a) set the durable flag on the item after a spec review reaches `reviewed` (a post-turn write to the same key the reporting surfaces already read, which is the smallest change and keeps one vocabulary), or (b) report the gate from the disposition itself and leave `NEEDS_INPUT_KEY` untouched, documenting that a reviewed spec's gate is visible as its terminal `reviewed` status plus the approval line in the run summary. PREFER (a) if and only if every reader of that key tolerates a post-turn write; enumerate those readers before choosing, and do NOT change `item_needs_approval`'s own semantics, which the plan path depends on.
  - Depends on: E-04
  - Expected outcome: the chosen mechanism is recorded with its reader census; a reviewed spec's human-approval gate is VISIBLE in the run record and summary; `item_needs_approval`'s behavior for plans is unchanged.
  - Execution state: performed

- [x] E-06 SCOPE THE REVIEW OUTPUT for a spec lane, INCLUDING THE LEGACY-NAMED SPEC (F-8). Confirm by test that `classify_review_writes(changed, id6=<spec id6>)` allows the spec file and its `.review.md` record and names anything else out of scope, and that the lane commit (`commit_review_lane_output`) and the non-isolated commit (`commit_review_shared_output`) commit exactly those. THE PLAN'S PREMISE HOLDS FOR THE RECORD AND NOT UNIVERSALLY FOR THE SPEC, so this item must close the gap rather than assert it away: both helpers decide scope by substring-matching the id6 against the PATH (`if str(id6) in path` / `elif str(id6) in cand`), so a spec whose filename does not contain its id6 has its OWN FILE classified out of scope and left uncommitted in the lane, where teardown is the only thing that sees it. Measured at review, 1 of 19 id-bearing specs is in that shape (`4w7d6s`, legacy `YYYYMMDD-HHMM-NN-<slug>` naming), and pre-cutover legacy spec names are GRANDFATHERED indefinitely, so this is a supported shape and not someone else's defect. Resolve it by making the ALLOWED set for a non-`ipd` entry include the artifact's OWN resolved path (from `queue_artifact_path`) in addition to the id6 substring rule, so scope never depends on a naming convention the repository does not enforce; re-derive the legacy-named population at execution rather than trusting the 1-of-19 figure. GENERALIZE BOTH PLAN-SHAPED STRINGS in `commit_review_shared_output`, not one (F-11): its docstring sentence AND the commit-message body it writes, which also reads "Path-scoped to the plan under review and its review record" and lands in permanent git history; change both to "the artifact under review and its review record" without changing plan behavior. Integration through the review ladder needs NO change, verified at review: `integration_action_for_item` keys on `item["action"] == "review"` rather than on artifact type, so a spec review lane already takes the no-revalidation arm (`ajxr5d` OQ-01); confirm that by test rather than editing it.
  - Depends on: E-05
  - Expected outcome: a spec review lane's commit contains only the spec and its review record, INCLUDING when the spec's filename does not carry its id6; an extra file written by the turn is reported out of scope, as for a plan review; both plan-shaped strings in `commit_review_shared_output` are generalized; the integration path is unchanged and shown to take the review arm.
  - Execution state: performed

### Task group 3: prove it

- [x] E-07 ADD `tests/test_spec_review_dispatch.py` WITH THE DISPATCH AND OUTCOME CASES (behavioral only; temp git repos; host spawn patched with a fake agent that performs a scripted action in the working tree; `AW_HOME` needs no per-test handling, since the root `conftest.py` already re-points it at a session sandbox via an autouse fixture, so do not add a second mechanism). Cases on BOTH hosts: (1) a to-review spec's prompt is `/spec-review ...` and the run record's `review_handler` is `spec-review`, while a to-review plan's is still `plan-review` in the same run; (2) the fake agent writes a conforming review record and runs `aw specs set reviewed <id6>`: the item ends `reviewed` and the spec file is in `reviewed/`, which also proves the disposition survived the directory MOVE; (3) REFUSAL: the fake agent exits 0 and writes nothing, so the item ends `fail-gate`, the refusal names the unchanged status, and the spec is still `to-review`; (4) REFUSAL: the fake agent hand-edits `- Status: reviewed` without writing a record, so the item ends `fail-gate` naming the missing attestation.
  - Depends on: E-06
  - Expected outcome: (1) through (4) pass on both hosts and each FAILS against the pre-change code, which after `8l8dgb` refuses the spec item-locally as undispatchable.
  - Execution state: performed

- [x] E-08 ADD THE APPROVAL-GATE AND SCOPE CASES, each pinning a defect this plan would otherwise ship. THE CRASH FIX (F-6): a `--full-auto` run that reviews a spec to `reviewed` ends the item `reviewed` with NO `DriverError` recorded and no `set_plan_approved` call, and the spec is NOT advanced to `approved`/`auto-approved`; this case must FAIL against a build carrying E-03 but not E-04's guard, with the recorded `driver_error` pasted, since that is what proves the guard load-bearing rather than decorative. THE GATE (F-7): a reviewed spec's human-approval gate is visible through whichever mechanism E-05 recorded, asserted on the run record and the summary rather than on `item_needs_approval`, plus a control assertion that `item_needs_approval`'s answers for plans are unchanged. SCOPE (F-8): an extra file written by the fake agent is reported out of scope and not committed, and a spec whose filename does NOT carry its id6 still has its own file committed.
  - Depends on: E-07
  - Expected outcome: all three cases pass on both hosts; the crash-fix case fails against a build without E-04's guard; the scope case's legacy-name sub-case fails against a build relying on the id6 substring rule alone.
  - Execution state: performed

- [x] E-09 RUN a real `--prepare-only` scratch run over one to-review spec and one to-review plan to show both queue entries with their handlers, and run the bare suite before and after.
  - Depends on: E-08
  - Expected outcome: the frozen queue shows both review entries with their types and handlers; the after-minus-before failing node set is empty.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `build_review_prompt` puts only the slash command on the command line because the host passes it as ONE argv element after `--`, where extra words become `$ARGUMENTS`.
- The spec `->reviewed` attestation is ONE predicate (`review_findings.review_attestation_missing`) consulted by both `aw specs set` spellings and by `check_engine`'s spec-review-attestation rule; this plan consults the same predicate and adds none.
- `/spec-review` never approves (`spec-review.md` hard rule), and `25kzda` 3.3 forbids any automated approval of a spec, `--full-auto` included.
- Review integration is deliberately not revalidated (`integration_action_for_item`, `ajxr5d` OQ-01).
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-5 are the author's, measured at HEAD `310ea53e` (2026-09-26); every one was re-verified at lane HEAD `9c94ff0b` by `/plan-review` and reproduced. F-6 through F-11 were ADDED by `/plan-review` on 2026-09-26.

THE ONE HIGH FINDING IS THAT THE `--full-auto` BRIDGE DOES NOT MERELY NEED SKIPPING, IT CRASHES. This plan's (d) says the bridge "is NEVER applied to a spec", which reads as a policy statement. The code says otherwise: the bridge's FIRST statement is `resolve_plan_path(...)` sitting OUTSIDE its own `try`, and plan `mxzogk` (already executed, Order 01 of Set `planpathtype`) makes that call FAIL CLOSED on a `.spec.md`. So on the very first `--full-auto` run that reviews a spec successfully, a `DriverError` escapes `execute_item_core` and the item is recorded `failed-safely` with a resolver message AFTER the review succeeded. The skip must be an explicit type guard placed BEFORE the resolve, not an inferred consequence.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `build_review_prompt` | Always `/plan-review`. | `command = f"/plan-review {rel_path}"`, re-read verbatim |
| F-2 | HIGH | `reconcile_disposition` review rung | Exit 0 returns `reviewed` whatever the artifact's status; resolves through `resolve_plan_path`. | re-read verbatim: `if status in ("reviewed", "approved"): return status, None` / `return "reviewed", None`; the resolve is `resolve_plan_path(source, item.get("configured_file", ""), item["id6"])` with `source = plan_repo or repo` |
| F-3 | HIGH | `--full-auto` bridge | Plan-only approval after review. | `is_plan_review_approved(plan_curr)` then `set_plan_approved(repo, item["id6"])` in `execute_item_core` |
| F-4 | INFO | specs setter | `to-review -> reviewed` already refuses without a conforming record. | reproduced on a scratch repo: `aw specs set <spec> --status reviewed` exits 1 with "to-review -> reviewed requires evidence that a review OCCURRED ... refused (file unchanged)" and `reason: no review record names aaaaaa as its `- Subject-Id:``; after writing a conforming record the same command exits 0 |
| F-5 | INFO | workflow | `/spec-review` exists with shims for both hosts. | `.opencode/commands/spec-review.md`, `.claude/commands/spec-review.md` both present; index row `spec-review` |
| F-6 | HIGH | `execute_item_core`'s `--full-auto` bridge | THE BRIDGE CRASHES ON A SPEC RATHER THAN NEEDING A POLICY SKIP, so scope (d) as written does not describe a change and E-03's "ensure the bridge is skipped" understates what must be done. The bridge's first statement is `plan_curr = resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])` and it is OUTSIDE the `try:` that follows (the `try` begins at `set_plan_approved`). Plan `mxzogk`, already EXECUTED, makes `resolve_plan_path` raise `DriverError` naming the detected type for a `.spec.md`. So a `--full-auto` run whose spec review SUCCEEDED (`disposition in ("reviewed","approved")`) raises out of `execute_item_core`, both hosts catch `DriverError` item-locally, and the item lands `failed-safely` with a `resolve_plan_path` message after a review that actually worked. The guard must be an explicit `queue_entry_type(item) == "ipd"` test placed BEFORE the resolve. | the bridge body read verbatim: the resolve is at the top of the `if is_review and disposition in ("reviewed","approved") and full_auto:` block and the `try` opens on the next statement; `oc_runipd.run_queue`'s `except DriverError as exc: runnable["status"] = "failed-safely"`; `mxzogk` scope (b) "else raise `DriverError` naming the detected type"; measured pre-`mxzogk` at this HEAD, `resolve_plan_path(d, "<spec path>", "aaaaaa")` still RETURNS the spec, so the crash arrives with `mxzogk`, which this plan already depends on transitively |
| F-7 | MEDIUM | E-03's `item_needs_approval` claim | THE CLAIM IS FALSE IN TWO INDEPENDENT WAYS, so the approval gate spec `25kzda` 3.3 requires is NOT reported by the mechanism E-03 names. (1) `item_needs_approval(status, action)` returns `(action != "review") and status == "reviewed"`, so for a review item it is False BY CONSTRUCTION whatever the status. (2) The flag is not a live read: `NEEDS_INPUT_KEY` is written exactly ONCE, in the queue builder, from the FROZEN `initial_status`, and is never recomputed after a turn. A to-review spec therefore freezes `needs_input: False` and stays False after reaching `reviewed`. The plan's instruction to "confirm the spec path records the approval gate as `needs_input`" would have the executor confirm something that cannot be true and then either weaken the claim silently or edit a shared plan-path predicate. Note the PLAN path is not a counterexample: a reviewed plan reports its gate because the full-auto bridge REQUEUES it as `action: execute`, `status: queued`, whose next queue derivation does set the flag. A spec has no execute action, so it gets no second pass and needs a different mechanism. | `item_needs_approval("reviewed","review")` -> False; `item_needs_approval("to-review","review")` -> False; `grep -n NEEDS_INPUT_KEY agent_workflows/runner_shared.py` -> the definition plus ONE write site in the queue builder; the bridge's requeue lines `item["action"] = "execute"` / `item["status"] = "queued"` |
| F-8 | MEDIUM | `classify_review_writes` / `commit_review_shared_output` scoping | E-04's premise ("`classify_review_writes` keys on the id6, which the spec path and the record path both carry") IS TRUE FOR THE RECORD AND NOT UNIVERSALLY TRUE FOR THE SPEC. Both helpers decide scope by substring-matching the id6 against the PATH, so a spec whose filename does not contain its id6 has its own file classified OUT OF SCOPE and left uncommitted in the lane, where teardown is the only thing that sees it. One such spec exists today (`4w7d6s`, legacy `YYYYMMDD-HHMM-NN-<slug>` naming), and the repository grandfathers pre-cutover legacy spec names indefinitely, so this is a supported naming shape rather than a defect to fix elsewhere. The review RECORDS are clean (12 of 12 spec review records carry their subject id6 in the filename), so the exposure is exactly the legacy-named spec file. | `classify_review_writes([<spec path>, <record path>, <other plan>], id6="aaaaaa")` puts the first two in `allowed`; `discover_specs` over the corpus finds 1 of 19 id-bearing specs whose filename lacks its id6 (`4w7d6s`, `superseded`); all 12 `Subject-Type: spec` review records carry their `- Subject-Id:` in the filename; `commit_review_shared_output` selects with `elif str(id6) in cand` |
| F-9 | MEDIUM | ordering inside `execute_item_core` | E-03 READS THE OUTCOME BEFORE THE OUTPUT IS COMMITTED, and the plan never states which tree it is reading. By line order: `reconcile_disposition` is called at the point the plan's E-03 targets, then `classify_review_writes` + `commit_review_lane_output` commit the turn's uncommitted output, then `integrate_review_lane_branch` merges the lane into main, then the full-auto bridge. So at disposition time the spec's new `- Status:` and its review record may exist only as UNCOMMITTED WORKING-TREE FILES in the lane, and are certainly not in main. This is survivable and in fact correct, but only because both predicates read the FILESYSTEM: `review_findings.review_attestation_missing` walks `review_dirs` with `open()`, and the status read is a `read_text`. E-03 must SAY it reads the lane tree (`plan_repo`) and that the predicates are filesystem-based, because the obvious alternative reading (consult main, or consult git) yields a gate that refuses every correct review. | the call order read from `execute_item_core`: `reconcile_disposition(...)` precedes `commit_review_lane_output(...)`, which precedes `integrate_review_lane_branch(...)`, which precedes the `is_plan_review_approved` bridge; `review_findings.subject_review_records` reads with `open(path)` over `iter_review_files`; `reconcile_disposition`'s review rung already uses `source = plan_repo or repo` |
| F-10 | LOW | E-03's disposition-source asymmetry | The spec moves DIRECTORY on `reviewed` (`to-review/` -> `reviewed/`), so the frozen `configured_file` is stale by the time the disposition is read. This is HANDLED by the plan's own instruction to resolve through `queue_artifact_path` (which resolves a spec through `discover_specs`, keyed on `- Id:` and location-independent), but the plan does not say the move is why, so an executor optimizing to a cheaper `repo / item["configured_file"]` read would silently reintroduce the bug and see it only as a spurious `fail-gate`. | reproduced: `aw specs set --status reviewed` moved the file from `.aw/records/specs/to-review/...` to `.aw/records/specs/reviewed/...`; after the move the frozen to-review path `is_file()` is False while `discover_specs(d)` returns the new path under its id6 |
| F-11 | LOW | `commit_review_shared_output` docstring | The generalization E-04 asks for is correctly identified, and the docstring wording is confirmed plan-shaped ("Path-scoped to the plan under review and its review record"), in BOTH the docstring and the commit message body the function writes. E-04 names only the docstring, so the commit-message copy would be left stating "the plan under review" for a spec review, which lands in permanent git history. | the function writes `"... Path-scoped to the plan under review and its review record; hooks ran normally."` as the commit body, in addition to the docstring sentence E-04 quotes |

## Proposed changes (ordered, validatable)

1. E-01 traces the review path IN CALL ORDER and confirms the spec-side machinery, the directory move, and the legacy-named populations.
2. E-02 dispatches the spec review prompt and records the handler.
3. E-03 makes the disposition spec-aware, gated on the record, reading the lane tree.
4. E-04 guards the `--full-auto` bridge with an explicit type test, before its resolve.
5. E-05 reports the spec's human-approval gate through a mechanism that fires.
6. E-06 scopes the spec review output, including the legacy-named spec.
7. E-07 adds the dispatch and outcome tests including both refusal paths.
8. E-08 adds the approval-gate and scope tests, each shown failing without its fix.
9. E-09 scratch run and suite.

## Deferred / out of scope (with reason)

- Reviewing a `draft` spec.
  - Carrier-Declined: requires a deterministic spec completeness parser that does not exist (`sweep_review_candidates_for_type` comment); spec `z7nbn1` 1.7 makes such an item `undetermined`, which plan `jdn790` refuses clearly.
- `--action review` re-review of a `reviewed` spec.
  - Carrier-Declined: `25kzda` 3.3's re-review row is not an acceptance criterion of spec `z7nbn1`; `enforce_requested_action` keeps refusing an illegal `--action` by name, so nothing silently misbehaves.

## Scope check

- Over-scope: none.
- Under-scope: NONE OUTSTANDING after review. `agent_workflows/review_findings.py`, `specs.py` are called, not changed; the workflow body and command shims are read, not changed. The four seams review added (E-04's bridge guard, E-05's gate mechanism, E-06's scope-set widening and the two `commit_review_shared_output` strings) all live in `runner_shared.py`, which is already declared, so no path is added. E-05's reader census may find a `NEEDS_INPUT_KEY` consumer in `render_stream.py` or `run_viewer.py`; those are READ for the census and are only edited if option (a) is chosen and a reader genuinely needs it, in which case the path is added at execution and justified at finalize with `--scope-reason`.
- Scope-Paths justification: `runner_shared.py` holds the prompt builder, the disposition rung, the `--full-auto` bridge, the queue-entry flag and the commit/scope helpers; the two host modules hold any host-specific prompt spelling and re-exports; the new test file holds E-07 and E-08.

## Required tests / validation

- `tests/test_spec_review_dispatch.py` (new): four dispatch/outcome cases including the two refusal paths of spec 5.4 (E-07), plus the crash-fix, approval-gate and scope cases (E-08), on both hosts; the refusal cases shown failing before the change, and the crash-fix and legacy-name cases shown failing against a build lacking their own fix.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. Implements spec `z7nbn1` 1.6 (first bullet) and acceptance 5.4 as written, and `25kzda` 3.3's `to-review` row (run spec review, tool-set `reviewed`, stop at the approval gate). Nothing in either spec changes.
- No user-facing docs.

## Open questions

### OQ-01: Should the runner itself run `aw specs set reviewed` after the turn?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO, from repository evidence. `/spec-review` performs the transition itself (`spec-review.md`: "aw specs set reviewed <id6> --message ..."), exactly as `/plan-review` does for plans; the runner's job is to VERIFY the outcome (status plus the shared attestation predicate), which is what spec 5.4's refusal path tests. A runner-side setter call would let a turn that wrote no real review be advanced by the driver. CONFIRMED AT REVIEW that the setter is the right gate to lean on rather than a second driver-side check: on a scratch repo `aw specs set --status reviewed` exits 1 with "requires evidence that a review OCCURRED ... refused (file unchanged)" and names the attestation reason, and exits 0 only once a conforming record exists, so the refusal a human meets and the verdict this plan reads come from the ONE predicate.

### OQ-02: How does a reviewed spec's human-approval gate become visible in the run record?

- Blocking: no
- Status: resolved
- Owner: this plan's author, with the mechanism RECORDED at execution per E-05
- Resolution or deferral rationale: RAISED AT REVIEW (F-7), because the authored E-03 asserted `item_needs_approval` reports it and that is false twice over: the predicate returns `(action != "review") and status == "reviewed"`, so it is False by construction for a review item, and `NEEDS_INPUT_KEY` is written ONCE by the queue builder from the frozen `initial_status` and never recomputed after a turn. The plan path is not a counterexample and shows why a spec needs something else: a reviewed plan's gate becomes visible because the full-auto bridge REQUEUES it as `action: execute`, `status: queued`, and the next derivation sets the flag; a spec has no execute action, so it never gets that second pass. Spec `25kzda` 3.3 nonetheless requires the gate ("Stop `needs_input`, including under `--full-auto`"), so SOMETHING must report it. Two mechanisms are available and both are defensible: a post-turn write to the same durable key the reporting surfaces already read, or reporting from the disposition and documenting that a reviewed spec's gate is its terminal `reviewed` status plus the summary's approval line. E-05 requires the choice to be made with a reader census and recorded, and forbids changing `item_needs_approval`'s own semantics, which the plan path depends on. Non-blocking because the evidence needed to choose is in the repository rather than with the human; what is NOT acceptable is the authored state, where the plan asserts a mechanism that cannot fire.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the trace table with its plan-only column AND its call-order column, showing `reconcile_disposition` ahead of `commit_review_lane_output` and `integrate_review_lane_branch`; the evidence that both attestation and status reads are filesystem reads; the scratch `aw specs set reviewed` refusal AND its success after a conforming record; the spec's path before and after the move with `discover_specs` resolving the new path while the frozen `configured_file` does not exist; both hosts' review invocation shapes; and the two legacy-named populations (specs, records).
  - Observed evidence: PASS.
    1. Trace table in call order:
    | Call Order | Function in execute_item_core | Plan-Only? | Notes |
    | --- | --- | --- | --- |
    | 1 | `build_review_prompt` | YES (at start) | Dispatches `/plan-review <rel>` unconditionally before 2ptgds |
    | 2 | `reconcile_disposition` | YES (at start) | Resolves via `resolve_plan_path`; returns `reviewed` on exit 0 regardless of status or review record before 2ptgds |
    | 3 | `classify_review_writes` | PARTIAL | Substring matches `id6` against filename; allows plan + record; misses legacy-named specs lacking id6 in filename |
    | 4 | `commit_review_lane_output` / `commit_review_shared_output` | YES (at start) | Docstring and commit body both read "Path-scoped to the plan under review and its review record" |
    | 5 | `integrate_review_lane_branch` | NO | Keys on `item['action'] == 'review'` (`integration_action_for_item`), takes no-revalidation ladder |
    | 6 | `--full-auto` bridge (`resolve_plan_path`, `is_plan_review_approved`, `set_plan_approved`) | YES (at start) | Resolves plan path outside try-block, crashing on `.spec.md` with DriverError |
    Order confirms `reconcile_disposition` (Call 2) runs BEFORE `commit_review_lane_output` (Call 4) and `integrate_review_lane_branch` (Call 5).

    2. Filesystem read evidence:
    - `review_findings.subject_review_records` uses `open(path, "r", encoding="utf-8")` iterating over review files on disk.
    - `_read_status` / `status` read uses `spec_path.read_text(encoding="utf-8")`.
    Both read the lane working tree (`source = plan_repo or repo`) directly on the filesystem.

    3. Scratch `aw specs set reviewed` refusal and success:
    Refusal without record:
    ```
    aw specs set: to-review -> reviewed requires evidence that a review OCCURRED (aw-specs-002).
      No review record found for spec aaaaaa under .aw/records/reviews/.
      reason: no review record names aaaaaa as its - Subject-Id:
    aw specs set: .aw/records/specs/to-review/20260927-aaaaaa-01-aaaaaa-scratch-spec.spec.md: refused (file unchanged)
    ```
    Success after writing conforming record:
    ```
    aw specs set: /tmp/tmptest/.aw/records/specs/reviewed/20260927-aaaaaa-01-aaaaaa-scratch-spec.spec.md -> reviewed
    ```

    4. Path before and after move:
    Before: `.aw/records/specs/to-review/20260927-aaaaaa-01-aaaaaa-scratch-spec.spec.md` (`exists() == True`)
    After: `.aw/records/specs/reviewed/20260927-aaaaaa-01-aaaaaa-scratch-spec.spec.md` (`exists() == True`)
    Frozen `configured_file` (`.../to-review/...`): `exists() == False`.
    `discover_specs(repo)["aaaaaa"]`: points to `.aw/records/specs/reviewed/20260927-aaaaaa-01-aaaaaa-scratch-spec.spec.md`.

    5. Both hosts' review invocation shapes:
    oc: `run_opencode(state, run_dir, item, plan_path, prompt_path, attempt_no, ...)`
    agy: `run_agy_turn(state, run_dir, item, prompt_path, attempt_no, session_id, use_continue, ...)`
    Both pass prompt file containing `/<handler> <rel_path>\n<isolation_notice>`.

    6. Legacy-named populations:
    - Specs lacking id6 in filename: 1 of 19 (`4w7d6s`: `20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md`).
    - Spec review records lacking subject id6 in filename: 0 of 10.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the prompt-builder diff, a spec review item's prompt file first line, a plan review item's prompt unchanged, and the attempt's `review_handler`.
  - Observed evidence: PASS.
    1. Prompt-builder diff in `runner_shared.py`:
    ```python
    -    handler = "plan-review"
    +    handler = review_handler_for(item)
         root = lane_root if lane_root is not None else repo
         try:
             rel_path = str(plan_path.relative_to(root))
         except ValueError:
             rel_path = str(plan_path)
         command = f"/{handler} {rel_path}"
    ```
    Where `review_handler_for` returns `spec-review` for `spec`, `plan-review` for `ipd`, and raises `DriverError` for any other type.
    2. Spec review prompt first line: `/spec-review .aw/records/specs/to-review/20260927-spc001-01-spc001-test-spec.spec.md`
    3. Plan review prompt first line: `/plan-review .aw/records/plans/pending/20260927-demo-01-pln001-test-plan.ipd.md`
    4. Attempt `review_handler`:
       `spc001`: `"review_handler": "spec-review"`
       `pln001`: `"review_handler": "plan-review"`
       Also recorded on item and in `ipd-started` events in `events.jsonl`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the disposition diff INCLUDING the comment stating which tree is read and why; the three outcomes (advanced with record, unchanged, hand-edited without record) with their refusal texts; and proof that the advanced case passed while the spec had MOVED directory and its output was not yet committed.
  - Observed evidence: PASS.
    1. Disposition diff in `runner_shared.py`:
    ```python
        if item.get("action") == "review":
            source = plan_repo or repo
            atype = queue_entry_type(item)
            if atype == "spec":
                # WHICH TREE, AND WHY IT MUST BE SAID RATHER THAN ASSUMED (F-9).
                # Read the LANE tree when isolated, i.e. the existing source = plan_repo or repo,
                # and pass that SAME root to review_attestation_missing. By call order inside
                # execute_item_core, reconcile_disposition runs BEFORE commit_review_lane_output
                # and long before integrate_review_lane_branch, so at disposition time the spec's
                # new - Status: and its review record may exist only as UNCOMMITTED working-tree
                # files in the lane and are certainly not in main. The gate works anyway because
                # BOTH predicates are filesystem reads (review_findings.subject_review_records walks
                # review_dirs with open(); the status is a read_text), and it would refuse every
                # correct review if it consulted main or git instead.
                #
                # ALSO RESOLVE THROUGH queue_artifact_path BECAUSE THE SPEC MOVES (F-10).
                # aw specs set reviewed relocates the file from to-review/ to reviewed/ (reproduced
                # at review), so the frozen configured_file is stale the moment the turn succeeds.
                # queue_artifact_path resolves a spec through discover_specs, which keys on - Id:
                # and is location-independent, so it finds the moved file; a cheaper
                # repo / item["configured_file"] read would produce a spurious fail-gate on
                # exactly the successful path.
                from agent_workflows import review_findings

                id6 = str(item.get("id6") or "").strip()
                spec_path = None
                try:
                    spec_path = queue_artifact_path(source, item)
                    text = spec_path.read_text(encoding="utf-8")
                    status = _read_status(text)
                except Exception:
                    status = None

                if exit_code == 0:
                    missing_attestation = review_findings.review_attestation_missing(
                        source, id6, "spec"
                    )
                    if status == "reviewed" and missing_attestation is None:
                        return "reviewed", None
                    if status != "reviewed":
                        reason = f"spec status still {status!r} (expected 'reviewed')"
                    else:
                        reason = missing_attestation or "missing review attestation record"
                    rel_target = str(spec_path.relative_to(source)) if spec_path else str(item.get("configured_file", ""))
                    remedy = f"/spec-review {rel_target}"
                    record_refusal(item, code=SPEC_REVIEW_REFUSAL_CODE, reason=reason, remedy=remedy)
                    return "fail-gate", None
                return "fail-gate", None
    ```
    2. Three outcomes and refusal texts:
    - Advanced with record: ends status `reviewed`, disposition `reviewed`, returncode 0.
    - Unchanged: ends status `fail-gate`, refusal reason `"spec status still 'to-review' (expected 'reviewed')"`.
    - Hand-edited without record: ends status `fail-gate`, refusal reason `"no review record names spc004 as its - Subject-Id:"`.
    3. Proof that advanced case passed with uncommitted moved file: tested in `test_case2_advanced_with_conforming_record_and_directory_move`, asserting `spec_path.exists() == False` (to-review/ gone) and `queue_artifact_path(repo, item)` resolves to `reviewed/` path before output commit.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the guard diff showing the type test placed BEFORE the bridge's `resolve_plan_path`; the `--full-auto` spec review ending `reviewed` with no `driver_error` key and no `set_plan_approved` call; and the SAME run against a build without the guard, showing the recorded `failed-safely` status and the `resolve_plan_path` `driver_error` text.
  - Observed evidence: PASS.
    1. Guard diff in `execute_item_core` (`runner_shared.py` lines 32132-32140):
    ```python
            if (
                is_review
    +           and queue_entry_type(item) == "ipd"
                and disposition in ("reviewed", "approved")
                and full_auto
            ):
                plan_curr = resolve_plan_path(
                    repo, item.get("configured_file", ""), item["id6"]
                )
    ```
    2. `--full-auto` spec review with guard: ends `reviewed`, `driver_error` is None, `mock_set_plan_approved.assert_not_called()` passes.
    3. Negative control without guard:
    ```
    IPD spc005 failed safely: Cannot locate IPD spc005; configured path was .aw/records/specs/to-review/20260927-spc005-01-spc005-test-spec.spec.md
    rc: 1
    status: failed-safely
    driver_error: Cannot locate IPD spc005; configured path was .aw/records/specs/to-review/20260927-spc005-01-spc005-test-spec.spec.md
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the reader census for `NEEDS_INPUT_KEY`, the recorded (a)/(b) decision with its rationale, the run record and summary showing the reviewed spec's approval gate visible, and `item_needs_approval`'s unchanged answers for the plan cases.
  - Observed evidence: PASS.
    1. Reader census for `NEEDS_INPUT_KEY`:
    - `runner_shared.py` lines 18164, 18184: dependency resolution checking if dependency target requires human input (`NEEDS_INPUT_KEY`). Checked at item dispatch; tolerates post-turn value.
    - `run_selection_policy.py` line 1664: `derive_item_disposition` reading `needs_input`.
    - Run summary and record formatters: checks `item.get(NEEDS_INPUT_KEY)` to format banner and JSON record.
    All readers tolerate post-turn updates.
    2. Recorded decision: Option (a) chosen in D-01: set `item[NEEDS_INPUT_KEY] = True` post-turn upon reaching `reviewed` in `execute_item_core` and print approval banner.
    3. Run record and summary visibility:
    `state["queue"][0]["needs_input"] == True`
    Terminal output prints: `◕ spec spc006 reviewed; awaiting human approval (run: aw specs set ... --status approved --by-human)`
    4. `item_needs_approval` unchanged answers for plans:
    - `item_needs_approval("reviewed", "review")` -> `False`
    - `item_needs_approval("to-review", "review")` -> `False`
    - `item_needs_approval("reviewed", "execute")` -> `True`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `classify_review_writes` result for a spec lane with one extra file; the resulting commit's `git show --name-only`; the SAME for a spec whose filename lacks its id6, showing its own file committed; both generalized strings in `commit_review_shared_output` (docstring and commit body); and the evidence that `integration_action_for_item` returns the review action for a spec entry.
  - Observed evidence: PASS.
    1. `classify_review_writes` with extra write:
    Extra file `src/extra.py` placed in `out_of_scope: ('src/extra.py',)`.
    2. Lane commit `git show --name-only`:
    Committed only spec and `.review.md` record:
    `.aw/records/reviews/20260927-s1-01-spc007-review.review.md`
    `.aw/records/specs/reviewed/20260927-spc007-01-spc007-test-spec.spec.md`
    3. Legacy-named spec (`4w7d6s`, lacking id6 in filename):
    `allowed_paths` includes resolved spec path; `classify_review_writes` puts `20260827-1514-01-test-spec.spec.md` in `allowed`, and commit contains the legacy spec and its review record.
    4. Generalized strings in `commit_review_shared_output`:
    Docstring: `"Path-scoped to the artifact under review and its review record; hooks ran normally."`
    Commit body: `f"  Path-scoped to the artifact under review and its review record; hooks ran normally.\n"`
    5. `integration_action_for_item`:
    `integration_action_for_item({"action": "review", "artifact_type": "spec"})` returns `"review"`, routed through the no-revalidation review integration arm.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_spec_review_dispatch.py -q` passing with count; with E-02 and E-03 reverted, cases (1) through (4) FAILING with their assertion text; passing again after restoring.
  - Observed evidence: PASS.
    1. Passing count:
    ```
    .......                                                                  [100%]
    7 passed in 7.34s
    ```
    2. Failing with E-02 and E-03 reverted:
    - Case 1: `AssertionError: False is not true : Expected /spec-review for spec, got: /plan-review .aw/records/specs/to-review/20260927-spc001-01-spc001-test-spec.spec.md`
    - Case 2: `[RUN-UNDISPATCHABLE-ITEM] spec spc002 at ... is queued with action 'review', which has no dispatcher yet (spec review dispatch is planned in 2ptgds)`
    - Case 3: `AssertionError: 0 == 0` (status marked reviewed on exit 0 rather than fail-gate)
    - Case 4: `AssertionError: 0 == 0` (status marked reviewed without record rather than fail-gate)
    3. Passing after restoring:
    ```
    .......                                                                  [100%]
    7 passed in 7.12s
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the three cases passing on both hosts; the crash-fix case FAILING against a build without E-04's guard with the `driver_error` pasted; and the scope case's legacy-name sub-case FAILING against a build relying on the id6 substring rule alone.
  - Observed evidence: PASS.
    1. Three cases passing on both hosts:
    - `test_crash_fix_full_auto_spec_review` PASSED (oc and agy)
    - `test_approval_gate_visibility_and_plan_control` PASSED (oc and agy)
    - `test_output_scoping_extra_write_and_legacy_named_spec` PASSED (oc and agy)
    2. Crash-fix case failing without guard:
    ```
    AssertionError: 1 != 0
    IPD spc005 failed safely: Cannot locate IPD spc005; configured path was .aw/records/specs/to-review/20260927-spc005-01-spc005-test-spec.spec.md
    driver_error: Cannot locate IPD spc005; configured path was .aw/records/specs/to-review/20260927-spc005-01-spc005-test-spec.spec.md
    ```
    3. Scope case legacy-name sub-case failing on id6 substring alone:
    ```
    WITHOUT allowed_paths (id6 substring alone):
      allowed: ('.aw/records/reviews/20260927-s1-01-4w7d6s-review.review.md',)
      out_of_scope: ('.aw/records/specs/reviewed/20260827-1514-01-test-spec.spec.md',)
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the scratch run's frozen queue (types, actions, handlers) and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence: PASS.
    1. Scratch run's frozen queue:
    ```
    FROZEN QUEUE:
      id6=spc001 atype=spec action=review status=queued review_handler=spec-review
      id6=pln001 atype=ipd action=review status=queued review_handler=plan-review
    ```
    2. Bare suite before:
    `2886 passed, 2 skipped, 3 warnings in 82.62s`
    3. Bare suite after:
    `2893 passed, 2 skipped, 3 warnings in 54.34s`
    4. After-minus-before failing node-ID set: empty (0 failed before, 0 failed after).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. `aw <host> run reviews --type spec` (or naming a to-review spec) now actually reviews it: the runner sends the spec review workflow, not the plan review, records which handler ran, and counts the spec reviewed only if the spec really reached `reviewed` through the setter with a conforming review record. A turn that leaves no record fails the item and leaves the spec where it was. A reviewed spec always stops for human approval, `--full-auto` included.

THREE SEAMS THE REVIEW MEASURED, each now its own checklist item rather than a clause, and each a thing worth knowing is being changed. THE `--full-auto` BRIDGE IS A CRASH, NOT A POLICY GAP: its first statement resolves the artifact as a plan and sits outside its own error handling, and plan `mxzogk` (already executed) makes that resolve fail closed on a spec, so the first `--full-auto` run whose spec review SUCCEEDS would record the item `failed-safely` with a resolver message. E-04 adds an explicit type guard ahead of the resolve. THE APPROVAL GATE HAS NO WORKING REPORTER for a spec: the predicate the plan originally named returns False for any review item by construction, and the flag it writes is frozen at queue build and never recomputed, so E-05 must choose and record a mechanism that actually fires. AND THE OUTPUT SCOPING KEYS ON THE FILENAME: a spec whose filename does not carry its id6 (one exists today, and legacy spec names are grandfathered indefinitely) would have its OWN file classified out of scope and left uncommitted in the lane, so E-06 widens the allowed set to the artifact's resolved path.

Order 04 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `jdn790` (and through it on the typed queue), and behaviorally on `mxzogk`, whose fail-closed resolver is what makes E-04 necessary.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).
