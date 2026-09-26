# IPD: Verify a finished carrier with an agent instead of failing on it, and fail only on abandoned carriers

- Date: 2026-09-26
- Kind: child
- Concern: A pending plan can hand deferred work to another plan or backlog item (`- Carrier: <id6>`). When that carrier FINISHES, `check.ipd-uncarried-obligation` calls the handed-off work unowned and reports an ERROR, both in CI (`aw check plans`, fail-closed, which turned main red twice on 2026-09-26: 8ud1is -> 0yrtne, a6xbso -> 8apjpp, both times the carrier HAD done the work) and at a plan's own pre-transition finalize gate. Nothing re-checks the OTHER plans that named a carrier at the moment it finishes, and the runner's retry instructions do not tell the agent how to resolve this case. The checker cannot tell 'finished and did it' from 'finished without doing it', so a judgement is needed, and the maintainer ruled that an agent makes it.
- Scope: IN: split the terminal verdict into FINISHED (executed, done) vs ABANDONED (superseded, not-executed, parked); in `aw check` a FINISHED carrier becomes a non-failing 'needs verification' finding while ABANDONED stays an error; a reverse lookup of pending plans that name a given carrier; in a run, after a plan finalizes, the driver gives the SAME agent (same lane, same session) a verification turn for each affected row with instructions to record `Carrier-Evidence` if the work was done or otherwise fix the row (re-point to a live owner, or do the work) and justify any out-of-lane edit; a 'no'/unresolved answer is sent back through the existing correction budget; the finalize-refusal retry path recognizes a FINISHED-carrier refusal as retryable with the same instructions; outcome tests; one CHANGELOG line. OUT: auto-editing other plans without an agent; aw attention surfacing.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/runner_shared.py, tests/test_carrier_reverse_lookup.py, tests/test_carrier_finished_verification.py, tests/test_check_engine.py, CHANGELOG.md
- Item-Dependencies: executed:xz59ai
- Status: reviewed
- Work-Kind: chore
- Priority: medium
- From-Backlog: zi2uzu
- Set: carrierwarn
- Order: 1
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: cnzrxb

## Workflow history
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED; 6 decisions recorded
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 all FIXED, none deferred, none open; 6 decisions D-1..D-6 recorded. Reviewed at HEAD 21b22c3b. `aw ipd lint --phase author --agent` reported `clean`/`findings: 0` before revision; the lane-input copy was byte-identical to the tracked file and the tree was clean, so no pre-review snapshot. THE PROBLEM IS REAL AND BOTH CITED INCIDENTS VERIFIED (`b20b7a74` re-pointed 8ud1is off executed carrier 0yrtne, `e0581df0` re-pointed a6xbso off executed 8apjpp; each carrier HAD done the work), and the maintainer's finished-vs-abandoned ruling is the right shape. SIX SUBSTANTIVE CORRECTIONS, each measured, three of which would each have made the plan fail its own stated outcome. (1) `warning` SEVERITY STILL EXITS 1: `artifact_core.drift_exit_code` exempts ONLY `info`, measured, and the constant directly above the code E-01 edits says so verbatim ("a `warning` here would exit 1 ... and fail CI"). E-01's stated outcome, `aw check plans` exit 0 on a finished carrier, was therefore false as written; corrected to `info`, with the CI-red consequence and the honest cost stated. (2) ONE DRIFT PER PLAN, ONE RULE, ONE SEVERITY: `evaluate_durable_carrier` emits a single Drift whose severity is `carrier_severity_for_plan`, so a plan carrying BOTH a finished and an abandoned row cannot report two rules (driven: 2 failures collapsed into one `error` Drift). E-01 now owns splitting the emitter and partitioning failures, and a new E-08 pins the mixed-row case, which was the plan's largest unstated gap. (3) THE E-03/E-04 RETRY REUSE CANNOT FIRE, TWICE OVER: `finalize_refusal_is_retryable` locates findings by the literal `IPD-` prefix, and a `check.*` rule never carries it (driven: finding_lines `[]`, retryable False), and `finalize_retry_decision` keys on a FINALIZE REFUSAL message while E-03's case has NO refusal (finalize SUCCEEDED), so passing a synthetic string returns LEAVE-ALONE silently (driven). Both are now stated, E-04 is re-scoped to the one thing it can honestly do, and E-03 owns an explicit budget rather than pretending to reuse one. (4) A DIRECT COLLISION WITH PENDING PLAN `xz59ai`, which is `reviewed` and rewrites the SAME `_resolve_carrier` terminal branch on the OPPOSITE premise (keep the refusal, improve the message); declared `- Item-Dependencies: executed:xz59ai` and reconciled in a new F-9 so the two do not silently undo each other. (5) `tests/test_check_engine.py` IS UNDECLARED but holds the existing carrier tests this changes the verdicts of; added to Scope-Paths. (6) The claimed corpus size is wrong (47 pending plans, not ~65) and ZERO rows are in the finished or abandoned state today, so E-02's timing target and E-05's fixtures must be re-derived; recorded in F-10 with the measurement. Full record: `.aw/records/reviews/20260926-carrierwarn-01-cnzrxb-warn-at-transition-time-when-a-terminal-carrier-leaves-anoth.review.md`.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): REDESIGNED per maintainer ruling 2026-09-26 (asked via question tool): a carrier that FINISHED is not an automatic error; an agent verifies it in the run (yes = record proof, no = fix it or send back), CI does not fail on a finished carrier but still fails on an abandoned one. Replaces the warn-only design.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog zi2uzu: warn at finalize, rollup and backlog done/parked when another pending plan names the transitioning artifact as a Carrier.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

A carrier that FINISHED no longer turns CI red or strands a plan. Instead an agent checks whether the finished carrier actually did the handed-off work: if yes it records the proof (`Carrier-Evidence`), if not it fixes the row (hands it to a live owner or does the work) with a justified out-of-lane edit, and only an unresolved 'no' fails. A carrier that was ABANDONED (superseded, not-executed, parked) still fails, because then the work truly has no owner.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Tell finished from abandoned

- [ ] E-01 In `check_engine`, split `_CARRIER_TERMINAL_STATUSES` (the frozenset beside the comment "A carrier target's status that means the obligation is ALREADY HIDDEN") into `_CARRIER_FINISHED_STATUSES = {"executed", "done"}` and `_CARRIER_ABANDONED_STATUSES = {"superseded", "not-executed", "parked"}`. Make `_resolve_carrier` return a new verdict `"finished"` when every owner is finished (and none live), and keep `"terminal"` (detail text renamed to abandoned) when any owner is abandoned and none live or finished. Thread it through `evaluate_carrier_obligation` so a `finished` carrier yields a `CloseVerdict` under a new rule `check.ipd-carrier-finished-unverified` whose detail says: `carrier <id6> finished (<status>); an agent must confirm it did this work and record Carrier-Evidence, or re-point the row`.
  - Depends on: none
  - Expected outcome: `aw check plans` exits 0 on a tree whose only carrier problem is a FINISHED carrier, and still exits 1 on an ABANDONED one.
  - THE SEVERITY MUST BE `info`, NOT `warning`, OR THIS ITEM'S OWN EXPECTED OUTCOME IS FALSE. Measured at review: `artifact_core.drift_exit_code` returns 1 for `error`, `warning` AND `warn`, and 0 ONLY for `info`. The authority is not an inference: the comment on `_CARRIER_LEGACY_SEVERITY`, which sits a few lines above the frozenset this item edits, states it verbatim ("`artifact_core.drift_exit_code` exempts ONLY `info`, so a `warning` here would exit 1 ... and fail CI"), and cites `check.stale-index-missing` as the precedent ("`info`, the ONLY non-failing severity"). Register the new rule in `RULE_REGISTRY` beside `check.ipd-uncarried-obligation` at `info`. STATE THE COST HONESTLY in the CHANGELOG line (E-07) rather than papering over it: `info` means the finding does NOT fail CI and, per the render path, is easy for a human to skim past; that is the price of the maintainer's ruling that CI must not go red on a finished carrier, and the compensating control is the agent turn in E-03, not the severity.
  - EMITTING TWO RULES REQUIRES CHANGING THE EMITTER, which the plan did not say and which is the larger half of this item. Measured at review: `evaluate_durable_carrier` returns AT MOST ONE Drift per plan, with ONE hardcoded `_CARRIER_RULE` and ONE severity from `carrier_severity_for_plan`, and it joins up to five failing reasons into one detail. Driven on a plan carrying one finished row and one wholly uncarried row: ONE Drift, rule `check.ipd-uncarried-obligation`, severity `error`, both reasons concatenated. So a per-row verdict change alone cannot produce a non-failing finished finding: partition `failures` by the verdict's rule and emit ONE Drift PER RULE (at most two), each with its own severity and its own five-reason cap. E-08 pins the mixed case.
  - `ipd_lint._merge_durable_carrier` already routes `severity == "info"` to `advisories` and everything else to blocking `diagnostics`, so choosing `info` gives the advisory-not-error behavior this item wants at the pre-transition gate FOR FREE, with no edit to `ipd_lint.py`. Verify that rather than assuming it, and if no edit proves necessary, say so at finalize and `--scope-ack` the declared path.
  - Execution state: pending

- [ ] E-02 Add `check_engine.find_obligations_carried_by(repo_root, id6, *, include_untracked=False) -> List[CarriedObligation]` (`plan_path, plan_id6, locator, line_no, row_text`). Iterate pending plans the way `check_durable_carrier` does (via `_iter_type_files(repo_root, "plans")` filtered on a `pending` path part); substring pre-filter on `id6` before parsing; obligations from `_deferred_section_obligations` + `_question_obligations`; keep rows whose `parse_carrier_ids` good tokens include `id6` and that carry no `Carrier-Evidence`/`Carrier-Declined`. Never raises (return `[]`). Reuse only the existing parsers.
  - Depends on: none
  - Expected outcome: one pure reverse lookup; measured cost re-derived at execution (see the timing note below).
  - RE-DERIVE THE CORPUS SIZE; DO NOT CARRY THE AUTHORED NUMBER. The item cited "~65 pending plans"; measured at review there are 47, and the population moves as lanes land. Treat the timing in E-07 as a re-derived measurement of whatever the tree then holds, and do not assert a threshold this plan cannot control.
  - NOTE `_question_obligations` NOW TAKES AN OPTIONAL `plan_text` KEYWORD (`def _question_obligations(open_questions, *, plan_text: Optional[str] = None)`), added by `vtkfq8`'s scaffold-placeholder skip and passed by `evaluate_durable_carrier` as `plan_text=plan_text`. It is keyword-only and defaulted, so a bare call still works, but OMITTING it changes behavior: an untouched scaffold placeholder question would then be reported as an obligation this lookup asks an agent about. Pass `plan_text=` and read the current signature before calling it.
  - Execution state: pending

### Task group 2: Verify with an agent in the run

- [ ] E-03 In `runner_shared.execute_item_core`, after a SUCCESSFUL finalize of plan B at BOTH finalize call sites (the two `_call_driver_finalize` calls, one inside the `finalize_repo = Path(work_dir)` isolated arm and one in the main-repo arm; locate them by that distinction, not by line number), call `find_obligations_carried_by(<lane or repo>, B)`. If rows exist and the attempt has a session id, dispatch ONE follow-up turn to the same agent in the same lane using a new builder `build_carrier_verification_prompt(b_id6, rows)` that says, in plain words: 'Plan <B> just finished. These pending plans named it as the owner of work they deferred: <plan, row, text>. For each: if <B> did this work, add `- Carrier-Evidence: <path of executed B>` under the row; if it did not, re-point `- Carrier:` to a live backlog item or plan (file one with `aw backlog new` if needed) or do the work. These edits are outside your plan's scope: commit them with `aw commit --no-plan -m <why>` naming each path, and state the reason. Report yes/no per row.' Then re-run `find_obligations_carried_by` on the lane and record the outcome per row.
  - Depends on: E-01, E-02
  - Expected outcome: finishing a carrier in a run leaves no other plan pointing at it unresolved, or the run says exactly which row it could not resolve.
  - USE THE ESTABLISHED FOLLOW-UP-TURN PRIMITIVE, WHICH EXISTS AND IS NOT `spawn_executor`. `runner_shared.resume_via_launcher` takes the host's own `raw_launcher` as a NAME and is already used by exactly two follow-up turns (the defect re-ask and the gate answer), each reading `attempt.get("session_id")` and passing `work_dir` plus a host-specific kwarg (`resume_session=<id>` on OpenCode, `session_id=<id>` + `use_continue=False` on Antigravity). Its docstring records WHY a third direct launcher call is forbidden: a test pins each host's launcher to EXACTLY TWO callers so no launch path can inherit the wrong frozen profile. So this item MUST route through `resume_via_launcher` and MUST branch on `host_labels == OC_HOST_LABELS` for the kwarg, exactly as both existing sites do. A plain `spawn_executor` call would also be wrong for a second measured reason: an isolated turn is ALWAYS a fresh session by design (`lanesess xd9sll`, four lanes lost), and `resume_session` is the one documented exception.
  - THE SEND-BACK PATH NAMED IN THIS ITEM CANNOT FIRE; THIS ITEM OWNS ITS OWN BOUND INSTEAD. Measured at review: `finalize_retry_decision(item, state, msg)` returns RETRY only when `finalize_refusal_is_retryable(msg)` is True, and that predicate requires either the literal summary `pre-transition gate did NOT conform` with every finding line prefixed `IPD-`, or the stale-receipt summary. Driven with `"carrier-verification-unresolved: ..."`: `retry=False, exhausted=False, reason=''`, i.e. LEAVE-ALONE, silently. And the deeper problem is that the premise does not hold at all: in THIS case finalize SUCCEEDED, so there is no refusal message and no refusal to classify. Therefore do NOT reuse `finalize_retry_decision`. Spend AT MOST ONE verification turn per attempt, bounded structurally by a per-attempt flag in the shape `attempt["defect_reasked"]` already uses (the defect re-ask's own docstring says "THIS FUNCTION NEVER LOOPS; boundedness is structural, not a counter"), and on an unresolved answer RECORD it (`record_refusal` with a new code plus a remedy naming the row) and let the run continue. Recording an asked-and-unanswered outcome is the precedent the defect re-ask sets verbatim: that outcome "is RECORDED rather than retried, because 'the agent was asked and did not answer' is itself a finding a human should see".
  - DO NOT BLOCK INTEGRATION ON AN UNRESOLVED ROW, and be deliberate about this because the item as authored implied a non-integration. The unresolved row is in ANOTHER plan, and plan B itself is finalized and verified; withholding B's integration would strand correct, validated work over a third party's row, which is the lane-stranding outcome the runner's whole send-back design exists to stop. Record the refusal, report it, integrate B. If the maintainer wants integration blocked, that is a policy change to raise explicitly rather than a side effect of this item.
  - THE OUT-OF-LANE EDIT IS SAFE AT THE INTEGRATION GATE AND NEEDS NO SCOPE PLEA, measured: `integrate_lane_branch` calls `execute_merge_and_revalidate_gate` WITHOUT `declared_scope`, so the gate's scope-fence arm (which would refuse an out-of-fence merged file) is not armed, and the lane commit rides the normal merge-and-revalidate path. What DOES see it is finalize's scope reconciliation, and it is already past: this turn runs AFTER `_call_driver_finalize` returned 0. Keep the edit in its OWN commit (`aw commit --no-plan`) so commit-boundary cohesion cannot attribute another plan's paths to B on a later finalize.
  - Execution state: pending

- [ ] E-04 PROVE, RATHER THAN PATCH, THAT A PLAN IS NO LONGER STUCK ON A FINISHED CARRIER IN ITS OWN DEFERRED SECTION. E-01's `info` severity routes the finished finding into `ipd_lint`'s `advisories`, which cannot move the disposition, so the pre-transition gate should no longer refuse for this cause at all and NOTHING needs adding to the retryable set. Demonstrate it: build a scratch plan whose own row names a finished carrier, run `aw ipd lint --phase pre-transition`, and show the finding reported as an advisory with a `conforming` disposition. Record the result in Findings. Only if a refusing path genuinely survives may the classifier be touched, and then it must be done the way the next bullet describes.
  - Depends on: E-01
  - Expected outcome: a plan never gets stuck on a finished carrier in its own Deferred section, shown by a conforming pre-transition lint rather than by a widened retry allowlist.
  - THE AUTHORED MECHANISM WOULD NOT HAVE WORKED, so do not fall back to it without re-reading it. `finalize_refusal_is_retryable` locates finding lines by `line.strip().startswith("IPD-")`, and `aw ipd finalize` prints findings as `  <rule> <detail>`, so a `check.ipd-carrier-finished-unverified` line begins `check.` and is INVISIBLE to that scanner. Driven at review on a realistic carrier refusal message: `finding_lines` is `[]` and the predicate returns False, and it returns False precisely BECAUSE an empty finding list is the documented fail-closed direction ("The summary alone ... tells us only that the gate refused and NOT which class"). Adding the rule to `RETRYABLE_FINALIZE_FINDING_TEXTS` alone therefore changes nothing; it would also require widening the line locator, which is pinned by a test on purpose so a wording change breaks loudly. Widening a fail-closed allowlist is a real risk and must not be done as a side effect of a message change.
  - Execution state: pending

### Task group 3: Outcome tests

- [ ] E-05 `tests/test_carrier_reverse_lookup.py` (scratch git repo, `tests/support.ready_plan_text` fixtures): (a) plan A defers to executed plan B -> `aw check plans` exit 0 with a `check.ipd-carrier-finished-unverified` finding naming A's row; (b) plan A defers to superseded plan B -> exit 1 with `check.ipd-uncarried-obligation`; (c) the same row with `- Carrier-Evidence:` -> no finding; (d) `find_obligations_carried_by(repo, B)` returns A's row, and `[]` for an id6 nobody names.
  - Depends on: E-01, E-02
  - Expected outcome: four outcome tests.
  - BUILD THE FIXTURES; DO NOT LOOK FOR A LIVE EXAMPLE. Measured at review over all 47 pending plans: 9 carrier rows resolve to a LIVE owner and ZERO resolve to a finished or an abandoned one, so neither case (a) nor case (b) exists in the tree today. That is expected (the two incidents were fixed by hand in `b20b7a74` and `e0581df0`) and it is why these must be scratch fixtures. It also means the live `check plans` run in E-07 will show NO finding of the new rule, which is a pass and not a failure to reproduce.
  - THE SCRATCH REPO MUST SET THE CARRIER CUTOVER, or (b) may not report at `error` at all. `carrier_severity_for_plan` reads `resolve_cutover_date(repo_root, "carrier_obligations")` and falls back to the `CARRIER_CUTOVER_DATE` constant, comparing against the plan's OWN `- Date:`, and a pre-cutover plan is downgraded to `info` (non-failing). So give each fixture plan a post-cutover `- Date:` and write `.aw/config/project.json` with `cutovers.carrier_obligations`, as the existing carrier-severity test in `tests/test_check_engine.py` already does. Otherwise (b)'s expected exit 1 can pass or fail for a reason unrelated to this change.
  - Execution state: pending

- [ ] E-06 `tests/test_carrier_finished_verification.py`: drive `execute_item_core` with an injected host runner double (no real model; the suite forbids real spawns) on a scratch repo where pending plan A defers to plan B: (a) the double answers the verification turn by adding `Carrier-Evidence` -> B integrates, A's row resolved, no refusal; (b) the double changes nothing -> item B carries the unresolved-verification refusal record AND STILL INTEGRATES (per E-03's ruling that another plan's row must not strand B's verified work), with the refusal readable on the item; (c) no plan names B -> no verification turn is dispatched (the double's call count is unchanged).
  - Depends on: E-03
  - Expected outcome: three outcome tests of what the run does, not of prompt wording.
  - ADD A FOURTH CASE, the one that guards the launch-path invariant E-03 rides on: assert the verification turn goes through the SAME injected `raw_launcher` the executor and verifier use, and that it is dispatched with the attempt's session (OpenCode `resume_session`, Antigravity `session_id` + `use_continue=False`). Without it, a later refactor could turn this into a third direct launcher caller, which the existing two-caller test pins against and which would silently inherit the wrong launch profile.
  - CASE (b) MUST NOT BE WRITTEN AGAINST `budget 0`. The authored wording spent the finalize retry budget, which E-03 measured cannot fire here; assert instead that the per-attempt flag prevents a SECOND verification turn in the same attempt (drive it twice and show one dispatch), which is the structural bound E-03 actually adopts.
  - Execution state: pending

- [ ] E-08 PIN THE MIXED-ROW CASE in `tests/test_check_engine.py`, which is the one E-01's emitter split exists for and which no other item covers: a single pending plan carrying BOTH a row whose carrier FINISHED and a row that is wholly UNCARRIED must produce TWO findings, `check.ipd-carrier-finished-unverified` at `info` and `check.ipd-uncarried-obligation` at `error`, and `aw check plans` must exit 1 (the abandoned/uncarried half still fails). Assert the rules and severities, not the wording. Measured at review against the CURRENT code, this returns ONE Drift, rule `check.ipd-uncarried-obligation`, severity `error`, with both reasons concatenated into one detail, so this test FAILS before E-01 and is the proof the emitter was actually split.
  - Depends on: E-01
  - Expected outcome: two findings with the two severities; the test fails against the pre-change emitter.
  - ALSO RE-RUN THE EXISTING CARRIER TESTS in `tests/test_check_engine.py` and reconcile them: they are the only tests that currently assert this rule's verdicts, so E-01 changes some of their expectations. Update them deliberately, naming each changed expectation in V-08, rather than discovering the breakage in E-07's bare suite.
  - Execution state: pending

### Task group 4: Record and verify

- [ ] E-07 Add one `- Changed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md`, plain words, no em or en dashes: when a plan or backlog item that other plans handed work to is finished, a run now asks the agent to confirm the work was done and records the proof, and `aw check plans` no longer fails on a finished owner (it still fails when the owner was abandoned). Then run the bare suite, `python3 -m agent_workflows check plans --agent`, `aw sanitize --agent`, and time `find_obligations_carried_by` warm on this repository.
  - Depends on: E-05, E-06, E-08, E-09
  - Expected outcome: 0 failed; timing recorded.
  - SAY IN THE CHANGELOG LINE THAT THE FINDING NO LONGER FAILS THE BUILD, since that is the user-visible consequence of E-01's `info` tier and a reader who is told only "no longer fails on a finished owner" will not know the finding is now easy to miss. One plain sentence, no em or en dashes.
  - EXPECT ZERO LIVE FINDINGS OF THE NEW RULE on this repository and do not treat that as a failure: measured at review, no pending plan currently names a finished or abandoned carrier. Paste the live `check plans` output and say so explicitly.
  - Execution state: pending

- [ ] E-09 RECONCILE WITH PENDING PLAN `xz59ai`, which edits the SAME `_resolve_carrier` terminal branch on the OPPOSITE premise and is already `reviewed` (F-9). Read the executed `xz59ai` first. Its shipped behavior is: a FINISHED carrier still refuses (`legitimate=False`, `error`) and the refusal prints a pasteable `- Carrier-Evidence: <path>` plus a warning against `Carrier-Declined`. This plan makes the same case non-failing. The two are NOT incompatible in substance and the combination is the better outcome, so PRESERVE the remedy text while changing the verdict tier: the `info` finding this plan emits MUST still carry `xz59ai`'s pasteable Carrier-Evidence line, so an agent or human reading it gets the exact fix. Verify `xz59ai`'s own tests (its Carrier-Evidence suggestion cases in `tests/test_check_engine.py`) still pass, and if any expectation genuinely must change, name it in V-09 with the reason.
  - Depends on: E-01
  - Expected outcome: the finished-carrier finding is non-failing AND still prints the pasteable remedy; `xz59ai`'s tests pass or their changes are justified individually.
  - THIS IS WHY `- Item-Dependencies: executed:xz59ai` IS DECLARED. Both plans rewrite the branch that turns a terminal carrier into a verdict. Executing this one first would leave `xz59ai` editing a function whose shape it was reviewed against no longer matching, and `xz59ai` is the narrower, already-reviewed change. The runner enforces the edge; a human executing by hand must check it.
  - Execution state: pending

## Project conventions discovered (Step 0)

- One evaluator, many surfaces: `evaluate_durable_carrier` serves both `aw check` and `aw ipd lint --phase pre-transition`; `_resolve_carrier`, `_deferred_section_obligations`, `_question_obligations`, `parse_carrier_ids` are the only carrier parsers; reuse them. That evaluator emits AT MOST ONE Drift per plan with one rule and one severity (F-6), so emitting a second rule is an emitter change and not a verdict change.
- `info` is the ONLY non-failing severity (`artifact_core.drift_exit_code`), and `ipd_lint._merge_durable_carrier` routes exactly `severity == "info"` to `advisories` and everything else to blocking diagnostics. So the severity choice alone decides both the CI exit code and whether the pre-transition gate refuses (F-5).
- The runner's send-back loop is for REFUSED finalizes only: `finalize_retry_decision` requires `finalize_refusal_is_retryable(fin_msg)`, which recognizes two summaries and locates findings by the `IPD-` prefix. It cannot be reused for a case where finalize SUCCEEDED, and passing it an unrecognized string yields a silent LEAVE-ALONE (F-7, F-8).
- A follow-up turn in the same session has ONE established primitive, `resume_via_launcher`, with exactly two existing callers (defect re-ask, gate answer), each reading `attempt["session_id"]`, passing `work_dir`, and branching on `host_labels == OC_HOST_LABELS` for the host's kwarg (`resume_session` vs `session_id` + `use_continue=False`). A test pins each host's launcher to two callers, so a third direct call is forbidden; and an isolated lane turn is otherwise ALWAYS a fresh session (`lanesess xd9sll`).
- Boundedness for a follow-up turn is STRUCTURAL here, not a counter: the defect re-ask sets a per-attempt flag and never loops, and records an asked-and-unanswered outcome rather than retrying it.
- The integration gate's scope fence is NOT armed on this path: `integrate_lane_branch` calls `execute_merge_and_revalidate_gate` without `declared_scope`, so an out-of-lane edit committed on the lane rides the normal merge-and-revalidate gate. Finalize's scope reconciliation is already past by then.
- The suite refuses real model spawns (`_assert_probe_spawn_is_permitted` precedent); tests inject runner doubles.
- Out-of-lane edits are allowed when justified (AGENTS.md execution contract; finalize `--scope-reason`).
- Tests: outcome only (maintainer standing rule).

## Findings

F-1 through F-4 were measured by the author. F-5 through F-10 were measured at `/plan-review`
(2026-09-26, HEAD `21b22c3b`), each by DRIVING the predicate, the CLI, or the runner helper rather than
by reading the code. Citations are by SYMBOL, since an offset expires before this plan executes.

| # | Location | Finding |
| --- | --- | --- |
| F-1 | backlog `zi2uzu` claim that aw check reports a clean tree in the window | FALSE: `check_durable_carrier` sweeps all pending plans on every `aw check plans`, fail-closed in CI; that is what turned main red on 2026-09-26 (fixed by hand in b20b7a74 and e0581df0). CONFIRMED at review: `b20b7a74` re-pointed `8ud1is` off executed carrier `0yrtne` and `e0581df0` re-pointed `a6xbso` off executed `8apjpp`, and in both commit messages the carrier HAD done the work. |
| F-2 | `_resolve_carrier` | Treats executed/done the same as superseded/not-executed/parked. The two real incidents were both FINISHED carriers that had done the work; the rule cannot distinguish that from a finished carrier that dropped it, which is why an agent must judge (maintainer ruling 2026-09-26). |
| F-3 | runner finalize path | After plan B finalizes, nothing looks at plans that named B; the only detection is the next `aw check plans` (CI) or the other plan's own pre-transition lint. |
| F-4 | design history | The first version of this plan only printed a warning at the transition. Rejected by the maintainer: warnings in unattended runs and in CI are not read, so they fix nothing. |
| F-5 | E-01's proposed `warn`/`warning` severity, and `artifact_core.drift_exit_code` | **A `warning` SEVERITY STILL EXITS 1, SO E-01's OWN EXPECTED OUTCOME WAS FALSE AS WRITTEN.** `drift_exit_code` returns `1 if any(severity != "info")`, measured for all four spellings: `error` -> 1, `warning` -> 1, `warn` -> 1, `info` -> 0. The authority is in this very code region: the `_CARRIER_LEGACY_SEVERITY` comment, a few lines above the frozenset E-01 edits, states "`artifact_core.drift_exit_code` exempts ONLY `info`, so a `warning` here would exit 1 ... and fail CI", citing `check.stale-index-missing` ("`info`, the ONLY non-failing severity"). The rule tier must be `info`. |
| F-6 | `evaluate_durable_carrier` | **ONE DRIFT PER PLAN, ONE RULE, ONE SEVERITY, so the two-rule split needs an emitter change the plan never mentioned.** The function emits at most one Drift carrying the hardcoded `_CARRIER_RULE` and a single severity from `carrier_severity_for_plan`, joining up to five reasons into one detail. Driven on a plan with one finished-carrier row and one uncarried row: ONE Drift, `check.ipd-uncarried-obligation`, `error`, both reasons concatenated. Without partitioning failures by rule, a per-row verdict change cannot produce a non-failing finished finding at all. |
| F-7 | `finalize_refusal_is_retryable`, and `aw ipd finalize`'s finding render | **E-04's MECHANISM CANNOT FIRE: A `check.*` FINDING IS INVISIBLE TO THE RETRY CLASSIFIER.** The predicate collects finding lines with `line.strip().startswith("IPD-")`, while `ipd_lifecycle`'s finalize renderer prints `  {d.rule} {d.detail}`, so a `check.ipd-carrier-finished-unverified` line begins `check.`. Driven on a realistic carrier refusal message: `finding_lines == []` and the predicate returns False, by its own documented fail-closed rule. Adding the rule to `RETRYABLE_FINALIZE_FINDING_TEXTS` alone changes nothing, and widening the line locator would loosen a deliberately fail-closed allowlist that a test pins. |
| F-8 | `finalize_retry_decision`, and E-03's send-back | **E-03's SEND-BACK IS A SILENT NO-OP, AND ITS PREMISE DOES NOT HOLD.** `finalize_retry_decision` returns RETRY only for a classified finalize REFUSAL; driven with `"carrier-verification-unresolved: ..."` it returns `retry=False, exhausted=False, reason=''` (LEAVE-ALONE, no error). More fundamentally, in this case finalize SUCCEEDED, so there is no refusal message to classify and no refusal arm to enter. The item needs its own structural bound (the `attempt["defect_reasked"]` pattern) rather than a budget it cannot reach. |
| F-9 | pending plan `xz59ai` (`reviewed`, Set `carrierauth`) | **A DIRECT COLLISION ON THE SAME BRANCH, ON THE OPPOSITE PREMISE.** `xz59ai` rewrites `_resolve_carrier`'s terminal verdict and `evaluate_carrier_obligation`'s `raw_carrier` branch to KEEP the refusal (`legitimate=False`, `error`) while printing a pasteable `- Carrier-Evidence: <path>`; this plan makes the same case non-failing. Both declare `agent_workflows/check_engine.py` and both are pending. The substance is complementary (a non-failing finding that still prints the exact fix is better than either alone), so this plan now declares `- Item-Dependencies: executed:xz59ai` and E-09 preserves its remedy text. Left undeclared, whichever ran second would silently undo the other's reviewed behavior. |
| F-10 | the corpus claims in E-02 and E-05 | The stated "~65 pending plans" is wrong (47 measured) and, more importantly, ZERO carrier rows currently resolve to a finished or abandoned owner: over all 47 pending plans, 9 rows resolve to a LIVE owner and none to a terminal one. So E-05 must build fixtures rather than find examples, and the live `check plans` in E-07 will legitimately show no finding of the new rule. Also measured: `_question_obligations` now takes a keyword-only `plan_text` that `evaluate_durable_carrier` passes, added by `vtkfq8`; omitting it would re-report scaffold placeholder questions. |

## Proposed changes (ordered, validatable)

1. E-01 finished vs abandoned verdicts, at `info` so it is genuinely non-failing (F-5), with the emitter split so two rules can coexist on one plan (F-6).
2. E-02 reverse lookup.
3. E-03 agent verification turn after finalize in runs, through `resume_via_launcher`, with its own structural bound and no integration block (F-8); E-04 proves the plan's own row no longer refuses instead of widening the retry allowlist (F-7).
4. E-05, E-06, E-08 outcome tests (including the mixed finished-plus-uncarried plan, which is what proves the emitter split); E-09 reconciles with `xz59ai` and preserves its pasteable remedy (F-9).
5. E-07 CHANGELOG, suite, live check, timing.

## Deferred / out of scope (with reason)

- Surfacing unverified finished carriers in `aw attention`.
  - Carrier-Declined: the run resolves them at finish and `aw check plans` still reports them; a third surface adds nothing.
- Resolving finished carriers outside a run (a human running `aw ipd finalize` by hand).
  - Carrier-Declined: `aw check plans` reports the row as needing verification and the human is the verifier; no agent is present to ask.

## Scope check

- Over-scope: none; the rule split, the lookup, and the run turn are one concern (who confirms handed-off work was done).
- Under-scope: four gaps closed at review. The emitter split that makes a two-rule outcome possible at all was unstated (F-6), now the larger half of E-01 and pinned by new E-08; the mixed finished-plus-uncarried plan had no test; the collision with pending `xz59ai` was undeclared (F-9), now a declared dependency plus new E-09; and `tests/test_check_engine.py`, which holds the existing carrier tests whose verdicts this change alters, was undeclared and is now in `- Scope-Paths:`.
- Two mechanisms named by the plan were measured NOT to work and the items were re-scoped rather than deleted: E-04's retry-allowlist route is invisible to the classifier (F-7) and E-03's send-back is a silent no-op on a successful finalize (F-8). Both items retain their goal with an achievable mechanism.
- `agent_workflows/ipd_lint.py` stays declared but may need NO edit: `info` already routes to advisories. If it is unmodified at finalize, `--scope-ack` it.

## Required tests / validation

Outcome tests only (maintainer standing rule): `tests/test_carrier_reverse_lookup.py` (what `aw check plans` reports and its exit code for finished, abandoned, and evidenced carriers) and `tests/test_carrier_finished_verification.py` (what a run does: integrates with or without a recorded refusal, dispatches nothing, and dispatches through the injected launcher with the attempt's session), with an injected runner double and no real model. Plus `tests/test_check_engine.py` for the MIXED plan (E-08): one plan with a finished row and an uncarried row must yield two rules at two severities and exit 1, which fails against the current single-Drift emitter. Every carrier fixture carries a post-cutover `- Date:` and a `.aw/config/project.json` `cutovers.carrier_obligations`, or the severity tier is decided by grandfathering instead of by this change. Run the suite BARE: `python3 -m pytest`.

## Spec / documentation sync

No `.spec.md` is amended. The durable-carrier contract (plan `rnkqrc`) changes in one respect: a FINISHED carrier is now a non-failing finding pending agent verification. That is recorded in this plan and the CHANGELOG; if a spec states the old rule, the executor must list it here and add it to Scope-Paths before editing it.

## Open questions

### OQ-01: Should a finished carrier fail CI, or wait for an agent?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-26 BY THE MAINTAINER when asked directly: verify with an agent in the run; CI does not fail on a finished carrier (it reports it) but still fails on an abandoned one. IMPLEMENTATION CONSEQUENCE ADDED AT REVIEW, not a re-opening: "does not fail" forces the `info` tier, because `warning` also exits 1 (F-5). `info` is the tier the repository reserves for detect-and-nudge findings, so the finished-carrier finding becomes genuinely advisory at BOTH surfaces, including the pre-transition gate. That is consistent with the ruling (the agent turn in E-03, not the severity, is the control that makes the work get checked) and the cost is stated in the CHANGELOG rather than hidden.

### OQ-02: When no run is present, is an advisory-only finished-carrier finding enough?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: YES, on the maintainer's own ruling and on the deferral already recorded here. The ruling moved the judgement into the run, and the plan's second deferral says a human running `aw ipd finalize` by hand IS the verifier. Recorded because the combination has a real consequence a reader should see stated: outside a run, a finished carrier now produces a non-failing `info` finding and NOTHING blocks, where today it blocks. That is the deliberate trade the ruling makes (the previous behavior turned CI red twice for carriers that had done the work), and E-09 reduces the cost by keeping `xz59ai`'s pasteable remedy in the finding text so the cheap fix stays visible. If the maintainer later wants a stronger non-run control, the natural place is `aw attention`, which this plan deliberately declines.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m agent_workflows check plans --agent` on the E-05 (a) and (b) scratch trees, showing exit 0 with the new finding for (a) and exit 1 with `check.ipd-uncarried-obligation` for (b). Paste the EXIT CODE of each explicitly, plus the `RULE_REGISTRY` entry showing the new rule at `info`, and state that `warning` was measured to exit 1 so `info` is required (F-5). Also paste `aw ipd lint --phase pre-transition` on the (a) tree showing the finding as an ADVISORY with a `conforming` disposition.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -c "from pathlib import Path; from agent_workflows import check_engine as ce; print(ce.find_obligations_carried_by(Path('.'), '<id6 some pending plan here names as Carrier>')); print(ce.find_obligations_carried_by(Path('.'), 'zzzzzz'))"` showing that plan's row, then `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste E-06 tests (a), (b) and the launcher-path case passing (node ids), and the item's recorded refusal from test (b) with its code and remedy. Show that test (b)'s item STILL INTEGRATED (the refusal is recorded, not blocking), which is the behavior change this review required. Paste the dispatch kwargs proving the turn went through `resume_via_launcher` with the attempt's session, and paste the twice-driven case showing exactly ONE verification turn per attempt.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw ipd lint --phase pre-transition` on a scratch plan whose OWN row names a finished carrier, showing the finding as an advisory and the disposition `conforming`, and paste `git diff` over `RETRYABLE_FINALIZE_FINDING_TEXTS` and `finalize_refusal_is_retryable` showing them UNCHANGED. If either was changed, justify it here and paste the measurement that a refusing path genuinely survived, because F-7 measured the authored route to be inert and widening a fail-closed allowlist needs its own reason.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_carrier_reverse_lookup.py -o addopts="" -v` showing 4 passed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest tests/test_carrier_finished_verification.py -o addopts="" -v` showing 3 passed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `git diff CHANGELOG.md`, `git diff CHANGELOG.md | grep -P '[\x{2013}\x{2014}]'` printing nothing, the final summary line of a BARE `python3 -m pytest` with 0 failed, `python3 -m agent_workflows check plans --agent` with its exit code, `aw sanitize --agent` exit 0, and three warm timings of the reverse lookup with the pending-plan COUNT they were measured over. Do NOT assert `check plans` exits 0 on the real tree: at review it exited 1 on a PRE-EXISTING `check.ipd-uncarried-obligation` (an uncarried row in plan `2yqt0a`) that this plan does not address, so name any surviving finding as pre-existing with its rule and plan, or show it gone with the reason.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the mixed-plan test FAILING against the pre-change emitter (the single `check.ipd-uncarried-obligation` `error` Drift with both reasons concatenated) and PASSING after, with both rules and both severities shown and the `aw check plans` exit code 1. Then list every existing `tests/test_check_engine.py` carrier expectation you changed, with the reason for each.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste one full finished-carrier finding detail showing it STILL contains `xz59ai`'s pasteable `- Carrier-Evidence: <path>` line, and paste `xz59ai`'s own carrier tests passing. Name any of its expectations you changed with the reason. Also confirm `xz59ai` is in `executed/` before this plan's changes were made (`aw find plans xz59ai`), since the declared dependency requires it.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern, who confirms that handed-off work was done when its owner finishes: the checker distinguishes finished from abandoned, and the run asks the agent.

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: (1) `aw check plans` stops failing when a named owner FINISHED and still fails when it was ABANDONED; (2) a run spends one extra agent turn after finishing a plan that other plans named as an owner, and that turn may edit those other plans with a stated reason; (3) an unresolved answer is RECORDED on the item as a refusal and reported, and the finished plan still integrates.

THREE THINGS A HUMAN SHOULD LOOK AT DELIBERATELY, all added at review. FIRST, "STOPS FAILING" MEANS `info`, WHICH ALSO MEANS THE PRE-TRANSITION GATE STOPS BLOCKING AND THE FINDING IS EASY TO SKIM PAST. `warning` still exits 1 (measured; the constant beside this code says so), so the only non-failing tier is `info`, the tier used for detect-and-nudge. So outside a run, a finished carrier now produces an advisory and nothing stops, where today it stops. That is the deliberate trade in the maintainer's ruling, since the old behavior turned main red twice for carriers that HAD done the work (OQ-02, F-5). SECOND, POINT (3) CHANGED AT REVIEW: the plan said an unresolved answer sends the item back through the existing retry budget, and that was measured to be a silent no-op (finalize SUCCEEDED, so there is no refusal to classify, and the predicate returns LEAVE-ALONE on an unrecognized string). It is now a recorded refusal plus one structurally bounded turn, and it deliberately does NOT block the finished plan's integration, because the unresolved row belongs to a DIFFERENT plan and stranding verified work over a third party's row is the outcome the runner's design exists to prevent (F-7, F-8). THIRD, THIS COLLIDES WITH PENDING PLAN `xz59ai`, which is already `reviewed` and rewrites the SAME branch on the opposite premise (keep the refusal, print a pasteable fix). The two are complementary in substance, so this plan now declares `- Item-Dependencies: executed:xz59ai` and E-09 preserves its remedy text inside the new advisory. Approving this means approving that ordering (F-9).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the files in `- Scope-Paths:`. `agent_workflows/ipd_lint.py` may need NO edit (`info` already routes to advisories) and takes a `--scope-ack` if unmodified. If the work requires another file, make the edit and JUSTIFY it at finalize (`--scope-reason`).

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a test passed that was not run. Run the suite BARE (`python3 -m pytest`), no `-n0`, no extra `-q`, no `-p no:randomly`. Two claims here are specifically easy to fake and must be DRIVEN, not described: V-01's EXIT CODES for the finished and abandoned trees (an assertion on the finding alone does not prove the tier), and V-08's mixed-plan test shown FAILING against the current single-Drift emitter, which is the only proof the emitter was really split rather than the verdict merely renamed.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if `xz59ai` has NOT executed when this plan starts, stop rather than rewriting the branch under it (the runner enforces the declared edge; a hand executor must check). If making the finished finding non-failing would ALSO make an ABANDONED or wholly uncarried row non-failing (the single-Drift emitter makes this the default failure mode), stop rather than shipping it: that would disable the fail-closed rule the maintainer explicitly kept. And do not widen `finalize_refusal_is_retryable`'s finding locator to make E-04 work; if a refusing path survives, report it.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit cnzrxb -- <paths>`; never `git add -A`, never `-a`, never push. The one deliberate exception is E-03's runtime behavior, which instructs the AGENT IN A RUN to commit another plan's row with `aw commit --no-plan`; that is the feature, not a contract breach, and it must stay in its own commit. The runner owns finalize in a lane. Backlog `zi2uzu` carries no `- Blocks-Release:`; after execution set it `done` with `--evidence` citing the executed plan.
