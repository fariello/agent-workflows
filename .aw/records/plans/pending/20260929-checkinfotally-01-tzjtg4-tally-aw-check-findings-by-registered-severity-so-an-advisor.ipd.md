# IPD: Tally aw check findings by registered severity so an advisory is not reported as an error

- Date: 2026-09-29
- Kind: child
- Concern: `aw check`'s human `Evidence` block renders an `errors` / `warnings` split computed from the RULE NAME rather than from the finding's registered severity. `cli._run_check` computes `err_cnt = sum(1 for d in drift if not d.rule.startswith("warn"))` and `warn_cnt` by the same prefix test, and NO rule id in `check_engine.RULE_REGISTRY` begins with `warn` (all 52 are `check.*`), so `warn_cnt` is ALWAYS 0 and every finding is counted as an error whatever its registered severity. Measured at base commit `54eb0f87`: `aw check plans` reports 15 findings whose registered severities are 12 `error`, 1 `warning`, 2 `info`, and renders `errors 15   warnings 0`. On a CLEAN tree the contradiction is starker still, because `drift_exit_code` correctly exempts `info`: `aw check specs`, `aw check research`, and `aw check prompts` each render `CONFORMS` beside `errors 1` while exiting 0. The enriched severity is already in hand three lines above the tally (`enriched = ce.enrich_drift(d, ...)` in the same loop) and simply is not read.
- Scope: IN: (a) replacing the two rule-name-prefix counters in `cli._run_check` with a tally over the ENRICHED severity, and adding `info` as its own bucket so an advisory is neither called an error nor silently folded into warnings; (b) a new behavior test module pinning the three-way split, the `CONFORMS`-beside-zero-errors property, and the count-conservation invariant, because F-04 measured that NOTHING in `tests/` asserts on this row today. OUT: any change to a rule's registered severity (the registry is correct; this is a reporting defect); any change to `artifact_core.drift_exit_code`, which already keys on severity and is the reason the exit code is right while the display is wrong (F-05); the `aw check` diagnostics list and its per-finding rendering, whose volume is a separate reporting concern owned by backlog `ct1n04`; `agent_workflows/renderers.py` and `term.format_evidence_grid`, which need no change because they iterate the Evidence dict generically (F-06); and the compact `--agent` record, which lists evidence KEYS only and so is unaffected (F-07).
- Scope-Paths: agent_workflows/cli.py, tests/test_check_severity_tally.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: zosk0a
- Blocks-Release: next
- Set: checkinfotally
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: tzjtg4

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog zosk0a. Authoring measurement CONFIRMED the item's diagnosis and its fix sketch exactly, and added three things the item does not state: a DUPLICATE open backlog item (`xqm16x`) describes the same defect and must be closed by this plan or it outlives its own fix (F-03); the row has NO test caller at all (F-04); and the item's own headline number (428 errors on `aw check plans`) is a LIVE tree count that has since moved to 15, so no validation may compare against it (F-02). See F-01 through F-07.
- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make `aw check`'s at-a-glance triage line tell the truth. After this plan the `errors` / `warnings` / `info` counts come from each finding's registered severity, a clean run no longer renders `CONFORMS` beside `errors 1`, and a behavior test keeps the split from regressing to a rule-name guess.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Confirm the premise before changing anything

- [ ] E-01 Re-measure the defect at the execution base, so the fix is not built on a stale premise. Run `python3 -m agent_workflows check specs` and confirm the output renders `CONFORMS` on the status line while the Evidence grid reads `errors 1   warnings 0`, and that the command exits 0. Then confirm the prefix test is still the live implementation and still matches nothing in the registry: `git grep -n 'startswith("warn")' -- agent_workflows/` and `python3 -c "from agent_workflows import check_engine as ce; print([r for r in ce.RULE_REGISTRY if r.startswith(chr(119)+chr(97)+chr(114)+chr(110))])"`.
  - Depends on: none
  - Expected outcome: the self-contradicting render is reproduced (`CONFORMS` beside a nonzero `errors`, exit 0), the two counters are the only `startswith("warn")` callers in the package, and the list of `warn`-prefixed rule ids is EMPTY, which is what makes `warn_cnt` unconditionally 0. STOP AND REPORT if any rule id does begin with `warn`: the counters would then be partially meaningful and this plan's premise would need revising.
  - Execution state: pending

### Task group 2: Tally by severity

- [ ] E-02 In `cli._run_check`, replace the two rule-name-prefix counters with a tally over the ENRICHED severity, and render `info` as its own bucket. The severity is already computed in the loop immediately above (the `enriched = ce.enrich_drift(d, recovery=fix or "")` line that feeds `diagnostics` and `findings`), so collect each finding's severity in that SAME pass rather than adding a second enrichment loop; use the same `enriched.severity or "error"` fallback the adjacent `Diagnostic(...)` construction already uses, so an un-enriched legacy `Drift` stays counted as an error exactly as it is today. Then build the `Evidence(key="rules", ...)` value as a three-key dict `{"errors": ..., "warnings": ..., "info": ...}`. Do NOT change the Evidence `key`, its `status` expression (`"clean" if exit_code == 0 else "findings"`), its position in the `evidence` list, or the `inventory` row above it.
  - Depends on: E-01
  - Expected outcome: the row reports the registered severity split. Every finding lands in exactly one bucket and the three counts sum to `len(drift)`, so no finding can be dropped by the change.
  - Execution state: pending
- [ ] E-03 Make the unknown-severity case explicit rather than accidental, so a severity outside the three-value enum cannot silently vanish from the row. Confirm what the code does with a severity that is neither `error`, `warning`, nor `info`, and ensure such a finding is counted in the `errors` bucket (the conservative direction, matching `rule_spec`'s `_DEFAULT_RULESPEC` fallback to `error` for an unregistered rule id and `drift_exit_code`'s treatment of any non-`info` severity as failing). Add a brief comment at the tally naming this choice and why it is conservative. If the implementation chosen in E-02 already guarantees it by construction, say so and record it; do NOT add a second code path for a case the first already covers.
  - Depends on: E-02
  - Expected outcome: no finding can be omitted from the rendered row. A hypothetical out-of-enum severity inflates `errors` (alarming, recoverable) rather than disappearing (silent, misleading), and the reasoning is recorded where the next reader will see it.
  - Execution state: pending

### Task group 3: Pin it

- [ ] E-04 Add `tests/test_check_severity_tally.py`, a BEHAVIOR test that drives the real `aw check` CLI over purpose-built fixture repositories and asserts on the rendered/structured output. It must cover: (1) THE THREE-WAY SPLIT, a tree provoking findings of known mixed severity, asserting the `rules` evidence row reports each severity in its own bucket and NOT every finding as an error; (2) THE CLEAN-RUN CONTRADICTION, a tree whose only finding is `info`-severity, asserting the command exits 0 AND that its human output does not claim a nonzero `errors` count beside a conforming status, which is the exact user-visible symptom backlog `zosk0a` reports; (3) COUNT CONSERVATION, that `errors + warnings + info` equals the total number of findings, which is the invariant that makes the change provably lossless; (4) EXIT-CODE INDEPENDENCE, that the fix did not disturb the exit code, since `drift_exit_code` is deliberately untouched (F-05). Prefer the structured `--json` surface for the counts (`data.policy_findings` carries each finding's severity, so the assertion can be derived from the same run rather than hardcoded) and use the human surface for the `CONFORMS`-beside-`errors` assertion, since that rendering IS the defect. Follow the existing pattern in `tests/test_agent_checked_count.py`: `tests.support.init_repo` plus `tests.support.run_cli`. Assert on real command output, exit codes, and side effects ONLY; do NOT read `cli.py` source with `inspect`, `ast`, regex, or substring search, do NOT assert on caller counts or symbol censuses, and do NOT assert that the `startswith("warn")` string is absent (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16).
  - Depends on: E-02
  - Expected outcome: a new test module that FAILS against the base tally and PASSES after E-02, exercising the CLI rather than inspecting it. This is the durable guard: F-04 measured that no test anywhere asserts on this row, so without it the row is free to regress to a rule-name guess.
  - Execution state: pending

### Task group 4: Verify and close the duplicate

- [ ] E-05 Verify the fix tree-wide, then close the DUPLICATE backlog item so it does not outlive its own fix. Run `git grep -n 'startswith("warn")'` over the whole repo and enumerate every remaining hit with a disposition. Run the suite BARE as `python3 -m pytest`. Run `python3 -m agent_workflows check all` and read the rendered row against the same run's `--json` severities. Run `aw sanitize --agent; echo rc=$?`. Then close backlog `xqm16x` (F-03), which describes THIS defect in more detail than `zosk0a` does and is fixed by the same two lines: it carries `- Blocks-Release: next`, so per AGENTS.md its close must be legitimate rather than forced, and the correct route is `--evidence` citing this executed plan. Do this AFTER `aw ipd finalize` has moved this plan to `executed/`, not before.
  - Depends on: E-03, E-04
  - Expected outcome: no live counter keys on a rule-name prefix; suite green; the rendered row agrees with the registered severities on a full-tree run; sanitizer exit 0; and `xqm16x` is closed against real evidence rather than left open pointing at fixed code.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL or by a quoted content string; the line numbers in the Findings table are at base commit `54eb0f87` and are approximate by the time this executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Severity is the single authority for how serious a finding is, and it lives in ONE place: `check_engine.RULE_REGISTRY` via `check_engine.rule_spec`, stamped onto each `Drift` by `check_engine.enrich_drift`. `artifact_core.drift_exit_code` already reads it. This plan makes the DISPLAY read the same source rather than introducing a second notion of seriousness.
- An unregistered rule id falls back to `_DEFAULT_RULESPEC` at `error`, deliberately, so a rule nobody registered fails loudly rather than passing quietly. E-03 keeps the display consistent with that bias.
- Tests must exercise behavior and assert on real outputs; tests that read production source text or count symbols are forbidden (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"; GUIDING_PRINCIPLES P16). This is why E-04 drives the CLI instead of grepping `cli.py`.
- `tests/test_agent_checked_count.py` is the closest precedent for this shape (a small focused module asserting a single evidence-row property through `tests.support.run_cli` over a fixture repo) and is not `slow`-marked, so it runs in the default suite. E-04 follows it.
- Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md "HOW TO RUN THE SUITE").
- Commit through `aw commit tzjtg4 -- <paths>`; never `git add -A`, never `-a`, never push.

## Findings

| # | Location (base `54eb0f87`) | Finding |
| --- | --- | --- |
| F-01 | `agent_workflows/cli.py`, `_run_check`, the `err_cnt` / `warn_cnt` computation feeding the `Evidence(key="rules", ...)` row (~:12667-12675) | CONFIRMED EXACTLY AS BACKLOG `zosk0a` STATES. `err_cnt = sum(1 for d in drift if not d.rule.startswith("warn"))` and `warn_cnt = sum(1 for d in drift if d.rule.startswith("warn"))`. Measured: `RULE_REGISTRY` holds 52 rules, 33 `error`, 12 `warning`, 7 `info`, and ZERO whose id begins with `warn`, so `warn_cnt` is unconditionally 0 and `err_cnt` is unconditionally `len(drift)`. Measured per target: `check plans` renders `errors 15  warnings 0` over findings whose real severities are 12/1/2 (error/warning/info); `check specs`, `check research`, and `check prompts` each render `CONFORMS ... errors 1  warnings 0` while exiting 0, the single `info` finding being `check.collisions-not-checked` or `check.ipd-lint-diagnostic`; `check backlog` renders `errors 3` over 2 error plus 1 info. The needed data is three lines above: the same loop already computes `enriched = ce.enrich_drift(d, recovery=fix or "")` and passes `enriched.severity or "error"` into the `Diagnostic`. This is a ONE-SITE defect: `git grep` finds `err_cnt`/`warn_cnt` nowhere else in the package. |
| F-02 | backlog `zosk0a` workflow-history line, "already renders 'errors 428'" | THE ITEM'S HEADLINE NUMBER HAS MOVED AND MUST NOT BE ASSERTED AGAINST. At its filing (HEAD `93b7aabb`) `aw check plans` reported 428 findings of which 76 were info; at base `54eb0f87` the same command reports 15, of which 2 are info. The defect is UNCHANGED (still 100 percent of findings counted as errors); what moved is the live artifact tree, and `check.scope-drift` in particular tracks in-flight begin receipts including other agents' (this is exactly what backlog `ct1n04` measured, 340 to 354 of 402 to 416 findings). CONSEQUENCE FOR THIS PLAN: no `V-*` may compare a count against any number written in this plan or in the backlog item. Every validation asserts a RELATION measured within one run (the rendered row versus that same run's `--json` severities) or a SHAPE (`CONFORMS` beside `errors 0`), never an absolute. |
| F-03 | `.aw/records/backlog/open/20260920-xqm16x-01-xqm16x-check-summary-counts-warnings-as-errors.backlog.md` | A DUPLICATE OPEN ITEM DESCRIBES THE SAME DEFECT, and `zosk0a` does not mention it. `xqm16x` ("aw check's errors/warnings tally keys on the rule NAME prefix instead of the finding's severity") is the same two lines, the same root cause, the same fix sketch, and it is the RICHER record: it quotes the code, states that no registry id starts with `warn`, names the advisory rules, and argues the user-perceptible impact that makes this `bug` rather than `chore`. Both are `open`, `medium`, `Work-Kind: bug`, `Blocks-Release: next`, filed a day apart by different sweeps (`lintreach k9awrq` and `id6integ sk7ggr`), each noting `cli.py` was outside its plan's fence. They differ only in emphasis: `xqm16x` leads on warnings being miscounted, `zosk0a` on info being miscounted, and ONE severity-based tally fixes both. This plan graduates `zosk0a` (its assigned item) and takes `xqm16x`'s detail as corroborating evidence; E-05 closes `xqm16x` on the same executed-plan evidence, because leaving a release-gating item open against fixed code is a false gate. NOT merged into one item and not closed at authoring: this turn is authoring-only, and an item must not be closed before its carrier ships. |
| F-04 | `tests/` tree | THE ROW HAS NO TEST CALLER AT ALL. `git grep -n '"errors"' tests/` and a search for a `warnings` evidence key both return NOTHING, so no test anywhere asserts on the `rules` evidence row, in either surface. The defect has therefore been shipping unguarded, and a severity-correct tally would be equally unguarded without E-04. This is the most durable part of the plan and the reason it is not a two-line commit. |
| F-05 | `agent_workflows/artifact_core.py`, `drift_exit_code` (~:679-689) | THE GATE IS ALREADY CORRECT, which bounds this plan to reporting. `return 1 if any(getattr(d, "severity", "") != "info" for d in drift) else 0` reads severity properly and exempts exactly `info`. That is WHY a clean run can render `CONFORMS` beside `errors 1`: two code paths answer "how serious is this?" and only one asks the registry. This plan changes the display to agree with the gate and must NOT touch the gate; a diff touching `drift_exit_code` would convert a reporting fix into a gating change. Note also that a legacy 3-field `Drift` carries `severity=""`, which is non-`info` and so fails the gate; E-02's `or "error"` fallback keeps the display consistent with that. |
| F-06 | `agent_workflows/renderers.py`, `HumanRenderer.render` Evidence block; `agent_workflows/term.py`, `format_evidence_grid` | NO RENDERER CHANGE IS NEEDED for the new `info` bucket. The renderer collects `[(k, v) for k, v in e.value.items() if not isinstance(v, (dict, list))]` and hands them to `format_evidence_grid`, which joins every pair generically (`"  " + "   ".join(f"{k}  {v}")`). A third scalar key therefore renders as `errors  N   warnings  N   info  N` with no edit, which is why `renderers.py` and `term.py` are OUT of `- Scope-Paths:`. Recorded so a reviewer does not expect renderer edits, and so an executor does not add them. |
| F-07 | `agent_workflows/result_types.py`, `Evidence.to_dict` and `CommandResult.to_agent_record` | THE MACHINE SURFACES ARE SAFE IN BOTH DIRECTIONS. `--json` serializes `Evidence.value` verbatim, so the new `info` key appears automatically and the existing two keys keep their names (additive, not breaking). The compact `--agent` record projects evidence to its KEYS only (measured: `"evidence": ["inventory", "rules"]`), so it is unaffected entirely. Together with F-06 this is why the fix is confined to `cli.py`. |

## Proposed changes (ordered, validatable)

1. E-01 re-measure the self-contradicting render and confirm no registry id begins with `warn` (guards the premise).
2. E-02 tally the `rules` evidence row from the enriched severity and add an `info` bucket (the actual fix).
3. E-03 make the out-of-enum severity case explicit and conservative, so no finding can vanish from the row.
4. E-04 add the behavior test module pinning the split, the clean-run property, count conservation, and exit-code independence.
5. E-05 tree-wide grep with per-hit disposition, bare suite, full-tree agreement check, sanitizer, and close duplicate backlog `xqm16x`.

## Deferred / out of scope (with reason)

- The VOLUME of the `aw check plans` diagnostics list, where a single `info` advisory is invisible inside hundreds of enumerated rows. This is a real and adjacent reporting problem (an operator who cannot find the advisory is not helped much by a correct count of it), but it is a different change to a different surface: it needs grouping or collapsing in the renderer, not a tally fix, and its candidate directions are already worked out in the carrier below, whose summary records that `aw check plans` reported 416 findings of which 354 were `check.scope-drift`.
  - Carrier: ct1n04
- Any change to a rule's registered severity in `RULE_REGISTRY`. The registry is the authority this plan starts trusting; re-litigating individual severities inside a display fix would confound the two and make the diff unreviewable.
  - Carrier-Declined: no work is owed. The registry is correct as written, and each entry's severity carries its own recorded rationale.
- Any change to `artifact_core.drift_exit_code` (F-05). It already keys on severity and is why the exit code is right today.
  - Carrier-Declined: no work is owed; the gate is correct and this plan's whole purpose is to make the display agree with it.
- Merging duplicate backlog items `zosk0a` and `xqm16x` into one record (F-03). Both are closed out legitimately instead: `zosk0a` graduates to this plan, and `xqm16x` closes on this plan's executed evidence (E-05). Rewriting one item to point at the other adds no information once both are closed against the same carrier.
  - Carrier-Declined: resolved by E-05 rather than deferred.

## Scope check

- Over-scope: two additions beyond the backlog item's literal text, each justified. `tests/test_check_severity_tally.py` (E-04) is added because F-04 measured that NO test asserts on this row, so the item's fix sketch alone would land unguarded. Closing backlog `xqm16x` (E-05) is added because F-03 found a duplicate release-gating item fixed by the same two lines; leaving it open against fixed code would be a false gate, and it is a records close rather than a code change. E-03 is not over-scope: it is the correctness edge of E-02's own change.
- Under-scope: the plan deliberately does NOT address the diagnostics-list volume that makes an advisory hard to find even once counted correctly (carried by `ct1n04`), and does not touch `drift_exit_code` or any registered severity. It also does not add a `--agent` surface for the split, since the compact record carries evidence keys only (F-07) and inventing a new projection is beyond a reporting fix.

## Required tests / validation

One new behavior test module, `tests/test_check_severity_tally.py` (E-04), is the durable verification. It drives the real `aw check` CLI over fixture repositories and asserts four properties: the three-way severity split, the clean-run case that does not render `CONFORMS` beside a nonzero `errors`, count conservation across the three buckets, and exit-code independence. It must fail against the base tally and pass after E-02; demonstrating that failure is part of V-04, because a test that passes both before and after proves nothing.

Beyond it: E-01's reproduction of the contradicting render, E-03's out-of-enum reasoning, E-05's tree-wide grep with a disposition per hit, a full-tree `check all` whose rendered row is read against the same run's `--json` severities, a bare `python3 -m pytest`, and `aw sanitize --agent`.

HOW THE ASSERTIONS AVOID THE STALE-NUMBER TRAP (F-02). Every check on the live tree asserts a RELATION measured inside a single run, never an absolute count: the rendered `errors`/`warnings`/`info` values are compared against the severities in that SAME invocation's `data.policy_findings`. The live count moves with other agents' in-flight receipts, so a hardcoded expectation would be flaky by construction. The fixture-repo tests in E-04 own the deterministic assertions.

HONEST LIMITS ON WHAT THIS VERIFICATION PROVES. First, a correct count does not make an advisory easy to FIND in a long report; that is `ct1n04`'s concern and this plan does not improve it. Second, count conservation proves no finding is dropped, not that every rule's severity is the RIGHT severity; this plan trusts the registry by design. Third, the fixture repos in E-04 provoke a chosen subset of rules, so they pin the tally mechanism rather than all 52 registrations; E-05's full-tree agreement check is what exercises the real corpus, and it is a one-time measurement, not a gate.

## Spec / documentation sync

No `.spec.md` is amended and no doc is edited, so `- Scope-Paths:` declares neither. Checked at authoring: `docs/cli-output-contract.md` and `docs/cli-human-guide.md` contain no occurrence of `warnings` and do not specify or illustrate the `rules` evidence row, so no documented contract describes the behavior being corrected. The change is additive on the machine surface (a third key in an existing Evidence dict, F-07) and corrective on the human surface, so there is no contract to restate. If an executor finds a doc or spec that DOES pin the two-key shape, that is a scope finding to report at finalize with `--scope-reason`, not a silent edit.

## Open questions

### OQ-01: Does `info` get its own bucket, or fold into `warnings`?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: ITS OWN BUCKET. Backlog `zosk0a` asks for exactly this ("render info findings in their own bucket"), and `xqm16x`'s fix sketch leaves it open ("decide whether info gets its own column or folds into warnings"), so the assigned item is the tiebreaker. It is also the only option consistent with the rest of the system: `drift_exit_code` treats `info` as categorically different from `warning` (it exempts `info` and fails on `warning`), so folding them would rebuild in the display the very conflation this plan removes, and an operator reading `warnings 3` could not tell whether the command could have failed. F-06 confirms the cost is zero: the renderer grid takes a third scalar key with no edit. F-07 confirms the machine surfaces are additive-safe.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the actual output of `python3 -m agent_workflows check specs` followed by `echo rc=$?`, showing a CONFORMS status line, an Evidence grid with a nonzero `errors` and `warnings 0`, and `rc=0`. Paste the output of `git grep -n 'startswith("warn")' -- agent_workflows/` (expect exactly the two counter lines in `cli.py`) and the `warn`-prefixed-rule-id list (expect `[]`). Judge the SHAPE only: do NOT compare the `N specs checked` count or the `errors` value against any number in this plan or in backlog `zosk0a`, per F-02.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- agent_workflows/cli.py`. It must show the two `startswith("warn")` counters REPLACED by a severity-based tally and the `Evidence(key="rules", ...)` value carrying three keys. Confirm in one sentence that the severity comes from the enrichment ALREADY performed in the adjacent loop rather than a second enrichment pass, and that the Evidence `key`, its `status` expression, and its position are unchanged. Then paste `python3 -m agent_workflows check specs` showing CONFORMS beside `errors 0` with the finding now counted under `info`, and `echo rc=$?` showing `rc=0` (the exit code must not move). A diff touching `artifact_core.drift_exit_code`, `RULE_REGISTRY`, `renderers.py`, or `term.py` is a FAILED V-02, not a passed one (F-05, F-06).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: state in one or two sentences what the implementation does with a severity outside `{error, warning, info}`, and show it: either paste the diff hunk plus comment that routes it to `errors`, or, if E-02's construction already guarantees it, paste the few lines that do so and explain why no extra branch is needed. Then demonstrate the conservation property directly on a mixed set, for example by tallying `check plans --json`'s `data.policy_findings` severities and showing the three bucket values sum to the total finding count in that SAME run. A claim that no out-of-enum severity can occur is NOT sufficient evidence on its own: show the code path that handles it if one does.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: THE TEST MUST BE SHOWN TO FAIL FIRST. Paste (1) the new test module's contents; (2) the output of running it against the UNFIXED tally, demonstrating a real failure, obtained by stashing the fix (`git stash push agent_workflows/cli.py`), running `python3 -m pytest tests/test_check_severity_tally.py -o addopts=""`, and restoring; (3) the same command PASSING with the fix in place, with its per-test counts. Name which of the four properties each test covers (three-way split, clean-run contradiction, count conservation, exit-code independence). State explicitly that the module asserts on command output, exit codes, and structured fields only, and reads no production source text (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"). A test that passes in step (2) is a FAILED V-04: it is not pinning this defect.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the FULL output of `git grep -n 'startswith("warn")'` and ENUMERATE every remaining hit with a disposition; expect hits ONLY in historical records that must not be rewritten (this plan, backlog `zosk0a`, backlog `xqm16x`, and any review record quoting them), and NO hit under `agent_workflows/`. A hit in live package code is a FAILED V-05. Paste the final summary line of a BARE `python3 -m pytest`, naming any failure as pre-existing or new (do not absorb a pre-existing failure silently). Paste the `rules` Evidence row from `python3 -m agent_workflows check all` beside the severity tally derived from that SAME run's `--json` `data.policy_findings`, and state that they agree; per F-02 compare the two measurements against EACH OTHER, never against a number written here. Paste `aw sanitize --agent; echo rc=$?` ending `rc=0`. Finally, paste the `aw backlog set done xqm16x --evidence <this executed plan path>` invocation and its output, and confirm it was run AFTER `aw ipd finalize` moved this plan to `executed/`; if the close refused, paste the refusal and report it rather than forcing it with `--blocks-release -`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and needs explicit human approval before execution.

WHAT A HUMAN IS APPROVING: a two-line fix in `cli._run_check` that counts findings by their registered severity instead of by a rule-name prefix, plus an `info` bucket in the same Evidence row, plus one new behavior test module, plus closing a duplicate backlog item. No rule's severity changes, no gate changes, no renderer changes, no spec is amended, and no existing test is modified.

THREE THINGS THE APPROVER SHOULD KNOW, all measured at authoring rather than assumed. FIRST, there is a DUPLICATE open item: `xqm16x` describes this same defect in more detail than `zosk0a` does, both carry `- Blocks-Release: next`, and one severity-based tally fixes both, so E-05 closes `xqm16x` on this plan's executed evidence (F-03). If the maintainer would rather close it by hand, say so and E-05 drops that step. SECOND, the item's headline number (428 errors) is a LIVE tree count that has since moved to 15; the defect is unchanged, but no validation in this plan may assert an absolute count, and every live-tree check compares two measurements from the SAME run instead (F-02). THIRD, this row has never had a test (F-04), which is why a two-line fix carries a test module.

WHAT THIS DELIBERATELY DOES NOT FIX, so the approver is not surprised later. A correct count still sits inside a diagnostics list that can run to hundreds of rows, where an `info` advisory remains hard to find; that is backlog `ct1n04`'s concern, it needs renderer grouping rather than a tally fix, and folding it in would turn a reporting correction into a rendering redesign.

GENUINE STOP CONDITIONS: E-01 finds a rule id that DOES begin with `warn` (the counters would be partially meaningful and the premise would need revising), a doc or spec is found to pin the two-key Evidence shape (report it rather than silently editing, per the spec-sync section), or a co-worker's concurrent edit to `cli.py` cannot be safely combined. None is a scope question; each is a condition under which proceeding would write something false.

HONESTY RULE (hard MUST): paste the ACTUAL command output for every `V-*`; never claim a check passed that was not run. V-04 specifically requires demonstrating the new test FAILING before the fix. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the two paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, make the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path). In particular do NOT edit `renderers.py` or `term.py` to "add the info column": F-06 measured that the grid renders a third scalar key with no change, and editing them would be unnecessary churn in a shared rendering path.

Commit ONLY the paths in `- Scope-Paths:` through `aw commit tzjtg4 -- <paths>`; never `git add -A`, never `-a`, never push. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize tzjtg4 --actor <agent/model> --message <summary> --apply` (the runner owns it when it executes this plan in a lane). This plan inherits `- Blocks-Release: next` from backlog `zosk0a`; AFTER EXECUTION, and not before, set that item `done` with `--evidence` citing this executed plan, and close `xqm16x` the same way (E-05). The ORDER is load-bearing: while this plan sits in `pending/`, closing either item fails closed because the gate is handed to a carrier that has not shipped, so both stay open until `aw ipd finalize` has moved this plan to `executed/`.
