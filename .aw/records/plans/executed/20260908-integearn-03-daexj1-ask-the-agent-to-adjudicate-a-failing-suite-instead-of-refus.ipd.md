# IPD: Ask the agent to adjudicate a failing suite instead of refusing every lane on any red test

- Date: 2026-09-08
- Kind: child
- Concern: ONE pre-existing red test anywhere in the repository silently refuses lane integration for EVERY plan. With `--validate` defaulting FALSE, `integration_is_earned` falls back to the driver-run suite as its trust signal, and that signal is BINARY over the whole repository: `SuiteCheckResult.passing` is True only on an observed exit 0 (`oc_runipd.py:3610-3624`, verdict at `:3786-3796`). MEASURED HARM 2026-09-08: a single unrelated failure (`tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, caused by a REPLAN verdict on the live plan `32ij2j`) stranded ELEVEN lanes holding fully validated work, and because nothing reported it, plan `03ie04` was executed TWICE for the same fix at `$16.59` then `$32.83`. The lanes were recovered only by a hand audit of `git worktree list`.
- Scope: Replace the binary refusal with a bounded ESCALATION TO THE AGENT, per the maintainer's ruling of 2026-09-08: record the failing test NAMES, and when the suite is not clean, ask the agent that just did the work to adjudicate with three parsable verdicts (safe to ignore / retry / cannot fix) rather than deciding by a fragile programmatic rule. Also fill the revalidation stub so the suite runs where the merged code actually is. Adds NO new refusal that a human cannot see, and changes no verifier semantics.
- Scope-Paths: agent_workflows/run_evidence.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/orchestrate_isolation.py, tests/test_suite_adjudication.py, tests/test_novalnomerge_integration.py, .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md, tests/test_runner_shared.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: integearn
- Order: 3
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: daexj1
- From-Backlog: ciesaj
- Blocks-Release: next

## Workflow history
- 2026-09-21 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: daexj1 verified (set integearn, attempt 1). [Scope reconciliation - widened-scope tests/test_runner_shared.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw oc run); in-scope-unmodified agent_workflows/orchestrate_isolation.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified agent_workflows/run_evidence.py: declared-but-unmodified (auto-acknowledged by aw oc run); in-scope-unmodified tests/test_novalnomerge_integration.py: declared-but-unmodified (auto-acknowledged by aw oc run)]
- 2026-09-21 executed (opencode its_direct/pt3-claude-opus-5-1m-us): all 10 E-items performed, all 10 V-items verified with pasted evidence. BARE SUITE, baseline measured FIRST as the plan instructed: before any edit `1 failed, 7694 passed, 3 skipped, 2 xfailed in 110.30s`; after all work `1 failed, 7736 passed, 3 skipped, 2 xfailed in 102.08s`. DELTA +42 passed (exactly the new test file), SAME single failure, none new. THE PLAN'S AUTHORED BASELINE WAS STALE both ways and was not trusted: the `test_reporting_contract` failure it predicted (backlog `8kttqq`) PASSES here, and the one live failure is a DIFFERENT environmental defect, `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, proven environmental in both directions on the same tree (`env -u OPENCODE_CONFIG_CONTENT ... -> 43 passed`, bare -> 1 failed): it reads the `OPENCODE_CONFIG_CONTENT` inherited from the executing agent's own turn. Filed as backlog `se8vsp`.
  WHAT ACTUALLY CHANGED BEHAVIOR IS E-03/E-04, and that is the honest headline. The revalidation stub is GONE: `make_integration_validation_runner`'s body was `return True` on both hosts, so the merge-and-revalidate gate had NEVER checked anything despite its own docstring stating "per-lane green NEVER implies integrated green". It now materializes the real merge result (new `materialize_merge_result` / `release_merge_result`: `git merge-tree --write-tree` + `commit-tree` + a DETACHED worktree, creating no branch and moving no ref, asserted) and runs the suite THERE, so the measurement finally contains the work being integrated. Proven against a fixture whose lane file is absent from main: the measured tree contains it. A combined-red suite now REFUSES, which the old runner structurally could not. Four fail-closed paths (no checker, unresolvable base/head, unmaterializable merge, suite exception) each measured. COST MEASURED, not estimated, and recorded in the docstring per E-04: 107.04s per distinct merge result, of which the suite is 106.59s and this plan's machinery 0.45s; cached on the merged TREE id so the suite runs ONCE per distinct result (asserted as a COUNT: 1 for two lanes sharing a tree, 2 for different trees).
  TWO E-ITEMS WERE SATISFIED BY EQUIVALENT SHIPPED BEHAVIOR RATHER THAN BY NEW CODE, recorded as decisions D-1 and D-2 and flagged for human review rather than buried. This plan was authored 2026-09-08; a LATER plan, `h5pyqa` (`gatewire-01`), SHIPPED its central mechanism on 2026-09-20 under a maintainer ruling of that date, in a different vocabulary: daexj1 E-05/E-06 name three prose sentinels (`SAFE TO IGNORE.` / `RETRY TESTS.` / `UNABLE TO FIX.`) parsed from stdout, while what ships is a four-answer JSON vocabulary (`not-mine` / `fixed` / `mine` / `needs-human`) with 1049 lines of behavioral tests. I did NOT build the second parser, because daexj1's OWN E-09 forbids exactly that duplication, and I did NOT delete the shipped one to satisfy the plan's letter. Every expected outcome E-05/E-06/E-07 states was verified against the shipped behavior by ACTION (a non-clean suite escalates; the prompt carries expectation + observed failing ids + consequences and is recorded in the prompts directory; `not-mine` releases; `fixed` re-runs and the RE-RUN decides, which is STRICTER than `RETRY TESTS.`; `mine` refuses and preserves; an unparseable answer refuses; both loops bounded by the run's existing `--retry-budget`; every adjudication persisted beside `integration_signal`). E-01's capture was likewise already shipped, sited differently than prescribed; all four of its stated properties were re-measured here, including that `SuiteCheckResult.summary` is now NON-EMPTY (F-10's bug is fixed) and that raw output is still absent from the durable ledger record.
  AN INTERMEDIATE FAILURE IS DISCLOSED RATHER THAN HIDDEN. My first E-03 implementation broke 14 tests across `test_oc_runipd.py`, `test_agy_runipd_cli.py` and `test_runner_backlog_close_in_lane.py`, because it ran a post-merge suite for EVERY item, including `--validate`-ON items whose trust signal is the VERIFIER's verdict. `integration_is_earned`'s two modes are ALTERNATIVES, not a conjunction, so refusing a verifier-earned integration on a suite result would have made `--validate` stricter than the mode it is an alternative to. I FIXED THE IMPLEMENTATION, NOT THE TESTS: revalidation now runs for the suite-earned mode only, resolved identically to the dispatch seam (and pinned against it, because the two hosts freeze OPPOSITE-POLARITY keys: oc writes `validate`+`no_audit`, agy writes only `no_verify`). All 322 tests in those three files pass. Separately, `pytest` exit 5 ("no tests collected") is NOT read as a broken merge, because a tree with no tests cannot have been broken by merging; narrowed to exactly 5 so 1/124/127 all keep refusing.
  E-10 AMENDED SPEC `25kzda` FIRST, as ordered. Section 5.1 gains "The attributed suite-attribution exception", conditioned on CAPTURED EVIDENCE (answer, reason, THE FAILING IDS THE AGENT WAS SHOWN, session, re-run count/outcome), naming the id list as what makes it reviewable, and stating that `ipd_lifecycle.finalize_precheck` applies UNCHANGED and that no gate is removed. A pure 50-line insertion, ZERO deletions, so section 4.2's finding-code table is byte-identical and its byte-equality test passes (87 passed). Per OQ-02 (`resolved`), the wording honestly describes the NON-gated form the maintainer ruled for, including the limit that the agent has no pre-work baseline, so this mitigates sloppiness and not deception and attribution is the safeguard.
  SCOPE: `tests/test_runner_shared.py` was ADDED to `Scope-Paths` during execution because E-03 forced it: `test_the_validation_runner_is_NOT_the_shipped_constant_true_one` asserted the constant-True behavior this item removes, so it was UPDATED (with the reason written into the test) rather than deleted, and its protected property is unchanged. `agent_workflows/run_evidence.py`, `agent_workflows/orchestrate_isolation.py` and `tests/test_novalnomerge_integration.py` were declared but needed NO edit (see D-2 and D-3). THREE DEFECTS FOUND AND FILED: `g31sns` (`aw specs note` truncates a spec's inline workflow history by design while the sidecar it defers to is GITIGNORED, so committing its output would have permanently deleted five tracked amendment records from this very spec; I restored them by hand, which is why the diff has zero deletions), `se8vsp` (the environmental test-isolation failure above), `iv4n2c` (`reattempt_deferred_integrations` accepts a REQUIRED `validation_runner_for` injection it never calls). `aw sanitize --agent` clean, `findings: 0`. `aw ipd lint --phase pre-transition` conforming (advisory only). NOT PUSHED.
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> neutral (not negative). Specifically, the finding it escalated (PR-401) is now closed in review round 2 after the maintainer rejected its framing on 2026-09-08; its one remaining question is `Blocking: no`. Performed at HEAD `84111de2` at the maintainer's explicit instruction of 2026-09-10, who was shown that 10 of 15 `no-go` plans were held by stale bookkeeping and chose to have them hand-fixed with evidence recorded rather than re-reviewed. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-08 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS; PR-401..PR-407; PR-401 escalated to blocking OQ-02

- 2026-09-08 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-401..PR-407, six FIXED, PR-401 (BLOCKER) left OPEN and escalated to OQ-02 (`Blocking: yes`); Readiness `no-go` pending that answer. Reviewed at HEAD `2c727032`; `aw ipd lint` conformed at `--phase author` (one advisory `IPD-Z602` density note) and at `--phase review-finalize`. THE PLAN'S DIAGNOSIS AND DESIGN ARE SOUND and were re-verified rather than trusted: `SuiteCheckResult.passing` is True only on exit 0, `integration_is_earned`'s suite branch is the only correctness signal in the default path, both hosts' `full_validation_runner` bodies really are `return True`, and the eleven-lane incident is present in the durable records (all eleven ids found across `run-20260908T030747Z-1812636` and `run-20260908T030809Z-1812970`). WHAT REVIEW FOUND. FIRST and blocking: the design lets an agent clear a test IT broke, and the plan's own proposed remedy is UNBUILDABLE as described, because the suite runs exactly ONCE post-work (`oc_runipd.py:6656`, `agy_runipd.py:3720`) so no baseline exists and "which failures are new" is not computable without a second full suite run. OQ-02 was reclassified `Blocking: yes` with three costed options; this is a security-relevant policy call about how much authority an agent holds over its own work, and the maintainer already ruled once on this design. SECOND: the spec reconciliation the plan handed to the executor was performed at review and the answer is determinate, not a judgement, since `25kzda` forbids this in three places including the integration clause at `:897`; the spec path joined `Scope-Paths` and new E-10 performs a narrow, evidence-conditioned amendment. THIRD: `32ij2j`'s defect is ALREADY SHIPPED in the function this plan modifies, measured by driving the real `capture_command`, so `SuiteCheckResult.summary` is always empty in production and E-01 now fixes it. FOURTH: the sentinel precedent cited does not exist in code (it is unbuilt plan `m7gvuz`), and the nearest real agent-verdict reader FAILS OPEN in the same function, defaulting an unrecognized verdict to `verified`. FIFTH: the stated baseline was wrong in both its count and its named failure, and the named failure now passes because `32ij2j` was retired. Also corrected a dangling sibling id (`nzpixq` does not exist; Order 04 is `ys1dor`). No product code was modified by this review.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): REPLACES the rejected plan `32ij2j` (Set `integearn` Order 01, `- Status: reviewed`, `- Readiness: no-go`), whose diagnosis was sound and whose PRESCRIPTION was measured unimplementable on two independent counts. Authored after three maintainer rulings on 2026-09-08, each recorded below as a DECIDED question rather than left open. FIRST RULING, and it is a design change rather than a choice between the offered options: the maintainer rejected a hard programmatic gate outright as "very fragile" and directed that the runner instead ASK THE AGENT to adjudicate a failing suite, parsing for one of three sentinels (`SAFE TO IGNORE.`, `RETRY TESTS.`, `UNABLE TO FIX.`) and re-prompting when none is present. That inverts the design: the comparison stops being the authority and becomes the INPUT to a question. It also dissolves `32ij2j`'s fatal inversion, because an empty failing list no longer silently means "nothing broke"; a non-clean suite always escalates. SECOND RULING: run the suite AFTER combining the work, filling the revalidation stub. THIRD RULING: report a stranded run as NOT DONE in red from the run's OWN record (that half is sibling Order 04, `nzpixq`). WHY `32ij2j` COULD NOT BE SALVAGED IN PLACE: its E-01 parses `FAILED <nodeid>` out of `tool_event['stdout_excerpt']`, and I re-verified that `run_evidence.build_tool_event` (`:277`) NEVER WRITES that key, storing only `stdout_sha256` (`:299`, `:318`), `stderr_sha256`, lengths and a truncation flag, with `max_output_bytes` (`:446`) truncating BEFORE hashing so no text survives at all. Its E-04 derived the outcome from a filesystem audit, which re-renders a recovered run as COMPLETED and so rewrites history. Both are structural, so this is a new plan carrying `32ij2j`'s evidence forward rather than a revision of it. THE REVALIDATION STUB IS REAL AND STILL A STUB: `execute_merge_and_revalidate_gate` (`orchestrate_isolation.py:982`) calls `full_validation_runner` at `:1160`, and both hosts' builders return a closure whose entire body is `return True` (`oc_runipd.py:1999-2002`, `agy_runipd.py:1242`), with a docstring conceding "per-lane green never implies integrated green".
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop losing validated work to unrelated red tests, without pretending a program can safely judge which failures matter. The runner should gather the facts, notice that the suite is not clean, and put the judgement to the agent that just did the work, in a form it must answer in one of three machine-readable ways.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the failing test names available at all

- [x] E-01 Capture the failing test IDENTIFIERS while the output is still in memory, and persist ONLY those. Per the maintainer's ruling, save the names and not the raw text. `capture_command` (`run_evidence.py:435`) currently hands bytes to `build_tool_event` (`:277`), which hashes them (`:299`) and keeps only digests and lengths (`:318`), and `max_output_bytes` (`:446`) truncates BEFORE hashing so the text is gone. Extract the failing node ids at capture time and add them as a typed list field on the evidence record. WHY NAMES ARE SAFE WHERE OUTPUT IS NOT: a pytest node id is repository-relative (`tests/test_x.py::Class::test_y`) and contains no home directory, username or absolute path, so it does not engage the D92 local-leaks rule that forbids machine-identifying strings in durable artifacts. Run `aw sanitize --agent` over a record containing real captured ids to prove that rather than assert it.
  YOU ARE FIXING A LIVE SHIPPED BUG AT THE SAME SEAM, AND THE PLAN DID NOT KNOW IT (F-10). `run_suite_check` ALREADY reads the key `32ij2j` was faulted for inventing: `oc_runipd.py:3671-3672` does `stdout = str(tool_event.get("stdout_excerpt") or "")` and the same for `stderr_excerpt`, then parses the pytest summary out of those strings at `:3691`. Since `build_tool_event` never writes either key, both are ALWAYS the empty string, so `SuiteCheckResult.summary` is ALWAYS `""` in production. MEASURED at review by driving the real `capture_command` on a command that prints a pytest-shaped summary line: the returned event's keys are exactly `['actor','argv','cwd','end_time','env','exit_code','kind','parent','run_id','schema_version','seq','start_time','stderr_len','stderr_sha256','stdout_len','stdout_sha256','timestamp','truncated']`, `'stdout_excerpt' in event` is `False`, and the string the summary regex would search is `''`. So `32ij2j`'s defect was not merely proposed, it is ALREADY IN THE SHIPPED CODE at the function this plan modifies. Fix it here (the same capture change that yields the ids can yield the summary), and say in the code comment that the reason `reason` strings have been reading `no summary line parsed` is this, not a regex problem. Do NOT reintroduce raw output to fix it: derive both the ids and the summary at capture time and persist only those.
  - Depends on: none
  - Expected outcome: a suite run's evidence record carries the failing test ids as a list; raw output is still not persisted; the sanitizer reports clean on a record built from a real failing run; `SuiteCheckResult.summary` is non-empty on a real run, which it has never been.
  - Execution state: performed

- [x] E-02 Do NOT let a missing or empty list read as success, which is the exact inversion that sank `32ij2j`. Its E-03 compared failing sets as a SUBSET, and because the source string was always empty the parsed set was always empty, and the empty set is a subset of everything, so every lane would have earned integration including one that broke the whole suite. Under this plan the authority is the EXIT CODE, never the list: a non-zero suite exit escalates (E-04) whatever the list contains, and the list is only ever used to make the question specific. Encode that ordering explicitly so a later refactor cannot reintroduce the inversion, and pin it with a test that supplies a non-zero exit and an EMPTY list and asserts escalation rather than integration.
  - Depends on: E-01
  - Expected outcome: exit code decides whether to escalate; an empty failing list with a red exit still escalates; a test pins it.
  - Execution state: performed

### Task group 2: run the suite where the merged code actually is

- [x] E-03 Fill the revalidation stub so the suite runs against the COMBINED result, per the maintainer's second ruling. `execute_merge_and_revalidate_gate` (`orchestrate_isolation.py:982`) already exists for exactly this and already states the principle in its own docstring ("per-lane green never implies integrated green"), and it calls `full_validation_runner` at `:1160`. Both hosts currently supply a closure whose whole body is `return True` (`oc_runipd.py:1999-2002`, `agy_runipd.py:1242`), so the gate has never checked anything. Supply a real runner that executes the bare suite against the merged tree and returns its result plus the failing ids from E-01. THIS ALSO FIXES THE MEASUREMENT MISMATCH: `run_suite_check` runs in the PRIMARY checkout by deliberate design (`dh0uno`, because a lane resolves a different `.aw/state` where about 15 run-viewer tests fail for unrelated reasons), while `isolate_worktree` defaults TRUE so the work lives only on the lane branch. Testing post-merge is the one place the code under judgement is actually present.
  - Depends on: E-02
  - Expected outcome: the gate runs a real suite against the merged tree on both hosts; the `return True` stub is gone; the docstring's stated principle is now enforced rather than asserted.
  - Execution state: performed

- [x] E-04 State the COST honestly in the code and measure it. Post-merge revalidation means one extra full suite run per distinct base, which roughly doubles the gate's wall time; the bare suite is presently about 55 seconds here, so budget accordingly. Record the measured before and after wall time in a comment so a future reader can judge whether the tradeoff still holds, and make sure a multi-lane run does not re-run the suite once per lane when the base is unchanged (the gate is per combined base, not per lane).
  - Depends on: E-03
  - Expected outcome: measured wall-time cost recorded; the suite runs once per distinct base rather than once per lane.
  - Execution state: performed

### Task group 3: the escalation, which is this plan's substance

- [x] E-05 When the suite is not clean, ASK THE AGENT rather than refusing, in the maintainer's own shape. The prompt must state what was expected, show what was observed (the failing ids from E-01, and enough output to judge), and demand exactly one of three sentinels: `SAFE TO IGNORE.` followed by a brief explanation to record; `RETRY TESTS.` followed by what was changed; or `UNABLE TO FIX.` followed by an explanation. Keep the sentinels EXACT and terminal-punctuated as the maintainer wrote them, since they are a parsing contract, and match them anchored rather than by loose substring so a sentinel merely DISCUSSED in prose cannot be mistaken for a verdict.
  - Depends on: E-02
  - Expected outcome: a non-clean suite produces the adjudication prompt carrying expectation, observation and the three required verdicts; the prompt is recorded in the run's prompts directory like every other.
  - Execution state: performed

- [x] E-06 Act on each verdict, and bound the loop. `SAFE TO IGNORE.` records the explanation into the run record and proceeds to integration. `RETRY TESTS.` re-runs the suite and re-adjudicates. `UNABLE TO FIX.` refuses integration and preserves the lane exactly as today, which is the correct outcome for a genuinely broken change. If NO sentinel is parsed, re-prompt as the maintainer directed. BOUND BOTH LOOPS EXPLICITLY, because neither can be unbounded: a retry loop that never converges burns paid model turns indefinitely, and a re-prompt loop against a model that will not emit the sentinel does the same. Choose a small cap for each, state the number and why in a comment, and treat exhaustion as `UNABLE TO FIX.` so the failure mode is the SAFE one (lane preserved, nothing integrated).
  - Depends on: E-05
  - Expected outcome: all three verdicts behave as specified; a missing sentinel re-prompts; both loops are capped and exhaustion refuses rather than integrates.
  - Execution state: performed

- [x] E-07 Record the adjudication DURABLY, so a `SAFE TO IGNORE.` is auditable rather than invisible. Write the verdict, the agent's explanation, the failing ids it was shown, and how many retries occurred into the run's own state, next to the existing `integration_signal` / `integration_detail` fields both drivers already write. This matters because `SAFE TO IGNORE.` is the path that lets work land over a red suite: it must be possible to ask later WHO decided that and on what basis. Note the reporting half is the sibling's: this item only ensures the fact is recorded where a reader can find it.
  - Depends on: E-06
  - Expected outcome: every adjudication is recorded in run state with verdict, explanation, shown ids and retry count.
  - Execution state: performed

### Task group 4: amend the contract this design changes

- [x] E-10 Amend spec `25kzda` to carry the narrow, named exception this design requires, and do it BEFORE the escalation is wired. This item exists because the reconciliation was left as an open judgement for the executor while the answer is determinate: the spec DOES forbid an agent opinion from permitting integration, in three places (`:64`, `:825-830`, and decisively `:897`, quoted in `Spec / documentation sync`). Read that section first; it states exactly what the amendment must say and what it must not touch.
  WRITE THE EXCEPTION NARROWLY OR IT IS A HOLE RATHER THAN AN AMENDMENT. It must be conditioned on the adjudication being CAPTURED EVIDENCE (the verdict, the explanation, and the failing ids the agent was shown, all recorded per E-07), not free prose; it must name the failing-id list as part of what makes it reviewable; and it must state that `ipd_lifecycle.finalize_precheck` still applies unchanged afterwards, so the amendment adds an attributed exception rather than removing a gate. Do NOT weaken the general sentence at `:64` and do NOT edit section 4.2's finding-code table (byte-equality test).
  ORDER MATTERS FOR AN HONEST REASON, not a mechanical one. There is no contract test binding this spec text to code (unlike the flag-surface case elsewhere in this repository), so nothing will go red if you wire the escalation first. Amend first anyway: doing it afterwards means that between two of your own commits the runner is shipping behavior its governing spec forbids, and a reviewer reading the diff in order cannot tell whether the amendment was reasoned or retrofitted.
  IF OQ-02 IS UNANSWERED, STOP HERE AND SAY SO rather than writing the weaker exception. The amendment's text DEPENDS on OQ-02: with option (a) it describes an agent adjudicating pre-existing noise only, which is defensible; without it, it must honestly describe an agent that may clear its own breakage, which is a materially larger exception to ask an approved spec to admit. Writing the wrong one and amending again later leaves two contradictory amendment records on the same contract.
  - Depends on: none
  - Expected outcome: spec `25kzda` carries the narrow exception, conditioned on captured evidence and the unchanged finalize gate, with its stated reason; section 4.2 is byte-identical; the spec's workflow history records the amendment through the tooled path; the exception's wording matches OQ-02's answer.
  - Execution state: performed

### Task group 5: prove it

- [x] E-08 Test WITHOUT STUBBING the capture, which is the specific hole that let `32ij2j`'s defect through review. The existing tests fabricate the evidence key (`tests/test_novalnomerge_integration.py:262`, `:288`, `:312` stub `capture_command`), so they could not have noticed the field was never written. Drive a REAL command that genuinely fails and assert the ids were captured from its real output. Cover: a genuinely red suite yielding a NON-EMPTY id list; each of the three sentinels driving its correct action; a missing sentinel re-prompting then exhausting to a refusal; the E-02 inversion guard (red exit plus empty list still escalates); and a clean suite still integrating with NO prompt issued, so the escalation cannot become an unconditional tax.
  - Depends on: E-07
  - Expected outcome: all six cases pass against real captured output rather than fabricated fields.
  - Execution state: performed

- [x] E-09 Prove BOTH hosts share every symbol added, by OBJECT IDENTITY rather than by grep, per the anti-re-fork discipline this repository already enforces (`tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests`). The adjudication logic, the sentinel parser and the real validation runner must live in `runner_shared.py` and be reached by both drivers, because a second copy of a sentinel parser is exactly how the two hosts drift on what counts as a verdict. Confirm `agy_runipd` gained no new direct import from `oc_runipd`.
  - Depends on: E-08
  - Expected outcome: an identity assertion showing both hosts resolve to the same objects; no new cross-driver import.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `SuiteCheckResult` (`oc_runipd.py:3610-3624`) documents itself as an OBSERVED FACT rather than a claim, noting the executor's own `tests` field is "the agent's own prose about work it says it did" and that `passing` is True only on an observed exit 0. This plan keeps that honesty and adds a second, explicitly attributed signal (the agent's adjudication) rather than blurring the two.
- `integration_is_earned` (`oc_runipd.py:3786-3796`) already distinguishes verifier-earned from suite-earned integration and deliberately refuses to let a green suite override an explicit verifier verdict. That precedence must survive: this plan changes only the suite-signal branch.
- The revalidation gate exists, states the right principle, and has never enforced it: `full_validation_runner` is a `return True` closure on both hosts.
- `run_suite_check` runs in the PRIMARY checkout deliberately (`dh0uno`), because a lane resolves a different `.aw/state` and about 15 `test_run_viewer` tests fail there for unrelated reasons. Any change of measurement site must not reintroduce that noise, which is why post-merge (not in-lane) is the ruled answer.
- Both drivers already persist `integration_signal`, `integration_detail`, `preserved_branch`, `preserved_worktree` and `preserved_lane_id`. The facts are recorded; readers are what is missing.
- D92 forbids machine-identifying strings in durable artifacts, which is why E-01 persists node ids rather than output, and why the sanitizer is run as proof.
- THE SENTINEL PRECEDENT THIS PLAN CITED IS NOT SHIPPED CODE, and the correction matters because it changes which model you copy (F-12). The "orchestrator probe accepts only two exact sentinels" describes plan `m7gvuz` (`orchprobe-03`, `- Status: approved`, every E-item `Execution state: pending`); MEASURED at review, `ORCHESTRATOR: CONTAINS EXECUTIONS` and its sibling grep to ZERO files under `agent_workflows/`, and `tests/test_orchestrator_probe.py` does not exist. Cite it as a CONVERGENT DESIGN, not as precedent.
- THE REAL SHIPPED PRECEDENT TO COPY IS `lane_containment.parse_missing_input_token` (`:1571-1617`) with `MISSING_INPUT_VERDICT_REFUSED` (`:1489`): it parses an exact prefix-anchored token out of WORKER STDOUT, the emitter and parser share ONE constant so they cannot drift, and a malformed token yields an explicit `REJECT_MALFORMED_TOKEN` rather than being dropped. `run_selection_policy.is_confirmation_accepted` (`:673-690`) is the exact-phrase-only analogue for a human reply. Follow those.
- **THE NEAREST EXISTING AGENT-VERDICT READER FAILS OPEN, AND THIS PLAN MUST NOT COPY IT.** `oc_runipd.py:6622-6633` (agy twin at `:3682`) reads the verifier's JSON verdict with `str(v_data.get("verdict","")).upper()` and a LOOSE substring test (`"BLOCKED" in ... or "NOT CONFORMING" in ...`), then falls to `else: verify_disp = "verified"`, and its `except` clause also defaults to `"verified"` when `v_rc == 0`. So an unrecognized, misspelled, or malformed verdict is read as VERIFIED. That is the precise opposite of the discipline E-05/E-06 require, it sits in the same function this plan edits, and an executor pattern-matching on nearby code would reproduce it. Anchor the match, and make the unparsed case re-prompt and then REFUSE (E-06), never proceed.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The suite signal is binary over the whole repository: `passing` is True only on exit 0. | `oc_runipd.py:3610-3624`, verdict `:3786-3796` |
| F-2 | ONE unrelated red test stranded ELEVEN lanes of validated work, each refused with `integration_signal: suite-failed`. | measured across the run records 2026-09-08 (`29wvmj`, `4r0qp1`, `6sb3yu`, `7wei1o`, `8fhjjc`, `eqzd0h`, `h9cn0y`, `kgpptv`, `nna8yz`, `tm2cz8`, `03ie04`) |
| F-3 | The cost is duplicated paid work: `03ie04` ran twice for the same fix, `$16.59` then `$32.83`. | the two runs' recorded attempt costs |
| F-4 | `32ij2j`'s parse target does not exist: `build_tool_event` never writes `stdout_excerpt`; it stores digests and lengths only, and truncation happens BEFORE hashing. | `run_evidence.py:277`, `:299`, `:318`, `:446` |
| F-5 | That would have INVERTED the gate: an always-empty failing set is a subset of everything, so every lane would integrate. This plan makes the EXIT CODE the authority instead (E-02). | `32ij2j` review finding PR-016, re-verified at `e148f82c` |
| F-6 | The existing tests could not catch F-4 because they stub the capture and fabricate the field. | `tests/test_novalnomerge_integration.py:262`, `:288`, `:312` |
| F-7 | The revalidation gate is a live stub: `full_validation_runner` bodies are `return True` on both hosts, though the gate's docstring states "per-lane green never implies integrated green". | `orchestrate_isolation.py:982`, `:1160`; `oc_runipd.py:1999-2002`; `agy_runipd.py:1242` |
| F-8 | The measurement site does not contain the work: the suite runs in the primary checkout while `isolate_worktree` defaults TRUE, so the lane's commits are absent. | `dh0uno` rationale recorded in `run_suite_check`'s docstring |
| F-10 | **`32ij2j`'s DEFECT IS ALREADY SHIPPED IN THE FUNCTION THIS PLAN MODIFIES, and the plan faulted it as a proposal without noticing.** `run_suite_check` reads `tool_event.get("stdout_excerpt")` and `("stderr_excerpt")` at `oc_runipd.py:3671-3672` and parses the pytest summary from those strings at `:3691`. `build_tool_event` writes NEITHER key, so both are always `""` and `SuiteCheckResult.summary` is always `""` in production, which is why `reason` strings have been reading `no summary line parsed`. MEASURED at review by driving the real `capture_command`: the event's keys contain no `stdout_excerpt`, and the string the regex searches is `''`. So this is a live latent bug, not a hypothetical, and E-01's capture change is the fix. | driven `run_evidence.capture_command` at review; `oc_runipd.py:3671-3672`, `:3691`; `run_evidence.py:318` key list |
| F-11 | **THE SPEC DOES FORBID THIS DESIGN, so the amendment is determinate rather than a judgement to defer to the executor.** Three places: `25kzda:64` ("The agent's prose and exit status are never completion authority"); `:825-830` section 5.1's not-completion-evidence list, which includes "a verifier's opinion" and "an agent-authored summary or checklist without captured evidence"; and decisively `:897`, "Executor commits remain on the item's isolated branch until scope, commit-content, hook, dependency, and deterministic completion checks pass. Only then may the coordinator integrate the verified commit set." A `SAFE TO IGNORE.` reply permits integration WITHOUT the deterministic check having passed. New E-10 performs the narrow amendment; the spec path joined `Scope-Paths` at review. | `.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:64`, `:825-830`, `:897` |
| F-12 | **THE SENTINEL PRECEDENT THE PLAN CITES IS AN UNBUILT PLAN, NOT SHIPPED CODE.** "The orchestrator probe accepts only two exact sentinels" describes `m7gvuz` (`orchprobe-03`, `- Status: approved`, every E-item `Execution state: pending`); `ORCHESTRATOR: CONTAINS EXECUTIONS` greps to zero files under `agent_workflows/`, and `tests/test_orchestrator_probe.py` does not exist. The real shipped precedents are `lane_containment.parse_missing_input_token` (`:1571-1617`, one shared constant, explicit `REJECT_MALFORMED_TOKEN`) with `MISSING_INPUT_VERDICT_REFUSED` (`:1489`), and `run_selection_policy.is_confirmation_accepted` (`:673-690`, exact phrase only). | plan `m7gvuz:39-44`; measured zero-match grep; `lane_containment.py:1489`, `:1571-1617` |
| F-13 | **THE NEAREST EXISTING AGENT-VERDICT READER FAILS OPEN, IN THE SAME FUNCTION THIS PLAN EDITS.** `oc_runipd.py:6622-6633` (agy twin `:3682`) upper-cases the verifier's JSON verdict and tests `"BLOCKED" in ... or "NOT CONFORMING" in ...` by loose substring, then `else: verify_disp = "verified"`; its `except` also defaults to `"verified"` when `v_rc == 0`. An unrecognized or malformed verdict therefore reads as VERIFIED. An executor pattern-matching on adjacent code would reproduce exactly the failure mode E-05/E-06 forbid. | `oc_runipd.py:6622-6633`; `agy_runipd.py:3682` |
| F-14 | **OQ-02's PROPOSED CONSTRAINT IS NOT BUILDABLE FROM WHAT THIS PLAN PROVIDES.** It claims "E-01 gives the failing ids on both sides", but MEASURED at review there is only ONE side: `run_suite_check` is called exactly once per attempt, after the work, at `oc_runipd.py:6656` and `agy_runipd.py:3720`, guarded by `if integration_gate_relevant and not validate`. No baseline suite result exists in run state, so "which failures are NEW" is not computable without a SECOND suite run, which is unscoped cost on top of E-04's doubling. This is why OQ-02 was reclassified blocking. | `oc_runipd.py:6649-6656`; `agy_runipd.py:3720`; no baseline field in either driver's frozen state |
| F-15 | The sibling plan id was wrong: the plan names Order 04 as `nzpixq` twice, and no artifact with that id exists anywhere under `.aw/records/`. The real Order 04 is `ys1dor`. A dangling id in a deferral note means the reader cannot find the plan that owns the deferred half. | measured `find .aw/records -name "*nzpixq*"` empty; `.aw/records/plans/pending/20260908-integearn-04-ys1dor-...ipd.md` |
| F-9 | The failing test that caused all of this is itself unrelated to any lane: it failed because of a REPLAN verdict recorded on the then-live plan `32ij2j`. RESOLVED SINCE AUTHORING, which validates the diagnosis: `32ij2j` was retired to `superseded/`, no pending plan now carries a negative verdict, and the test PASSES at review. The incident it caused is unchanged, and the plan's premise (that an unrelated red test must be survivable) is unaffected. | `tests/test_plan_readiness.py:790-798`; measured `1 passed, 66 deselected` at review; `32ij2j` now `- Status: superseded` |

## Proposed changes (ordered, validatable)

0. Amend spec `25kzda` with the narrow, named exception this design requires, before wiring the escalation (E-10).
1. Capture and persist failing test ids only, fix the always-empty `summary` bug at the same seam, and prove the sanitizer stays clean (E-01).
2. Make the exit code the authority so an empty list can never mean success (E-02).
3. Fill the revalidation stub so the suite runs on the merged result (E-03).
4. Measure and record the added wall-time cost; one run per base (E-04).
5. Ask the agent to adjudicate with three exact sentinels (E-05).
6. Act on each verdict; cap both loops; exhaustion refuses (E-06).
7. Record every adjudication durably in run state (E-07).
8. Test against real captured output, never a stubbed field (E-08).
9. Prove both hosts share the new symbols by identity (E-09).

## Deferred / out of scope (with reason)

- THE END-OF-RUN AND CROSS-TREE REPORTING. A stranded run must stop printing a green COMPLETED, and `aw attention` must surface a stranded lane; those are sibling Order 04 (`ys1dor`, NOT `nzpixq` as authored: verified at review, no artifact with id `nzpixq` exists anywhere under `.aw/records/`, while `20260908-integearn-04-ys1dor-report-a-run-whose-work-never-landed-as-not-done-in-red-from.ipd.md` is the real Order 04) and backlog `nuanaw` respectively. This plan fixes the CAUSE; being told about it is separately owned.
- `32ij2j` ITSELF. It is superseded rather than revised, because both of its mechanisms are structurally unavailable (F-4, and its filesystem-derived outcome). It should be retired as superseded by this plan; that is a records act for the maintainer, and this plan does not perform it.
- CHANGING THE VERIFIER PATH. When `--validate` is ON, the verifier verdict governs and a green suite deliberately does not override it. Untouched.
- PERSISTING RAW SUITE OUTPUT. Ruled against: names only. A sanitized-excerpt design was offered and not chosen.
- IN-LANE MEASUREMENT. Offered and not chosen; it reintroduces the `dh0uno` noise and still proves only per-lane green.
- AUTO-FIXING THE CURRENT RED TEST. `tests/test_plan_readiness.py`'s failure belongs to whoever owns plan `32ij2j`'s REPLAN verdict. This plan makes such a failure survivable rather than fixing this instance.

## Scope check

- Over-scope: `orchestrate_isolation.py` is included because E-03 must replace the stub the gate calls; without it the ruled post-merge measurement has nowhere to run. The spec file was ADDED at review (E-10) because the design contradicts three clauses of an `approved` contract and the amendment is part of the deliverable rather than a follow-up (F-11).
- Under-scope: reporting is left to sibling `ys1dor` and to backlog `nuanaw`. No verifier semantics change. The environmentally-failing `test_reporting_contract` case is not fixed here (backlog `8kttqq` owns it) and must not be "fixed" by deleting an untracked directory.
- ONE ADJACENT BUG IS DELIBERATELY IN SCOPE: the always-empty `SuiteCheckResult.summary` (F-10). It is not scope creep, it is the same missing capture E-01 already has to add, in the same function, and leaving it would mean shipping a plan that faults `32ij2j` for a defect the code still contains.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line and MEASURE YOUR OWN BEFORE-BASELINE; judge on the DELTA. DO NOT TRUST THE AUTHORED BASELINE: it said `1 failed, 5858 passed` naming a `test_plan_readiness` failure, and BOTH halves are now wrong. Re-measured at review (HEAD `2c727032`): the suite reports `1 failed, 5865 passed, 3 skipped, 2 xfailed in 54.31s`, and `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` now PASSES (`1 passed, 66 deselected`) because plan `32ij2j` was retired to `superseded/`, which is exactly the fix F-9 predicted. The single current failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL and not yours: that test walks `REPO_ROOT.rglob("*")` skipping only `.git/`, `.aw/records/`, `.aw/worktrees/` and `tests/` and consults no `.gitignore`, so it trips over a gitignored local `opencode-recovery/` directory. It is already filed as backlog `8kttqq`. Exclude it from your delta, and do NOT delete another party's untracked directory to make it pass.
- `python3 -m pytest tests/test_suite_adjudication.py tests/test_novalnomerge_integration.py` for the focused surface.
- A REAL end-to-end: a lane whose work is fine, against a tree carrying one unrelated red test, must reach the adjudication prompt and integrate on `SAFE TO IGNORE.` — this is the exact scenario that stranded eleven lanes.
- The inverse: a lane that genuinely breaks tests must reach `UNABLE TO FIX.` and be preserved, proving the fix did not simply disable the gate.
- `aw sanitize --agent` over a record containing real captured ids.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

THE RECONCILIATION WAS DONE AT REVIEW, AND THE ANSWER IS YES, THIS IS A SPEC AMENDMENT. The plan left it as a judgement for the executor ("THE EXECUTOR MUST READ THAT SECTION AND RECONCILE. If the spec forbids ..."), which is not a question an executor should be answering mid-implementation about an `approved` contract. It was read at review and the spec does forbid it, in two places that must both be amended (F-11):
  * `25kzda:64`: "The agent's prose and exit status are never completion authority. Completion comes only from typed repository state, Git state, tool-authored lifecycle receipts, captured command evidence, declared dependency state, and deterministic checks."
  * `25kzda:825-830` section 5.1 "Deterministic authority boundary" lists what is NOT completion evidence, including "'done,' 'tests pass,' or similar agent prose", "an agent-authored summary or checklist without captured evidence", and (decisively for this design) "a verifier's opinion".
  * `25kzda:897` is the clause that binds INTEGRATION specifically: "Executor commits remain on the item's isolated branch until scope, commit-content, hook, dependency, and deterministic completion checks pass. Only then may the coordinator integrate the verified commit set". A `SAFE TO IGNORE.` reply is an agent opinion that permits integration WITHOUT the deterministic completion check having passed, so it contradicts this sentence directly.
THEREFORE: `.aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` IS declared in `- Scope-Paths:` (added at review), so the runner announces the edit before the run starts and the finalize scope gate reconciles it afterwards. The amendment is a NARROW, NAMED EXCEPTION, not a weakening of the boundary: state that a non-clean suite may be cleared for integration ONLY by an explicitly recorded agent adjudication that names the failing test ids it was shown, that the adjudication is itself captured evidence (E-07) rather than free prose, and that the deterministic finalize gate (`ipd_lifecycle.finalize_precheck`) still applies unchanged afterwards. Say WHY in the amendment, since a spec edit changes the contract every other plan is reviewed against: the alternative was measured and is worse, eleven lanes of validated work stranded by one unrelated red test and one plan paid for twice.
DO NOT TOUCH SECTION 4.2's FINDING-CODE TABLE. `run_evidence.RUN_FINDING_CODES` transcribes those cells verbatim under a byte-equality test, so editing a cell IS a code change and is outside this amendment.
IF OQ-02 IS ANSWERED AS OPTION (a), SAY SO IN THE AMENDMENT TOO, because a constraint that refuses `SAFE TO IGNORE.` for NEWLY broken tests is what makes the exception defensible in spec terms: the agent then adjudicates only pre-existing noise, and no agent clears its own breakage. An amendment written before OQ-02 is answered would have to describe the weaker, self-clearing form.
`AGENTS.md` needs no change; the runner behavior it describes is unaffected.

## Open questions

### OQ-01: How many retries, and how many re-prompts, before exhaustion?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE BY THE EXECUTOR, recorded so the numbers are deliberate rather than accidental. Both loops must be bounded (E-06) and exhaustion must be treated as `UNABLE TO FIX.`, so the failure mode is the safe one. RECOMMENDATION: small, since each iteration costs a paid model turn and the existing correction budget defaults to 2 for exactly that reason; one or two retries and two re-prompts is a reasonable start. State the chosen numbers and the reasoning in a comment so a later reader can tune them against observed behavior rather than guessing.

### OQ-02: Should `SAFE TO IGNORE.` be constrained to failures the agent did not cause?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-401
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08, AND THE QUESTION WAS RE-FRAMED FIRST BECAUSE BOTH THIS QUESTION AND THE REVIEW FINDING BEHIND IT WERE ARGUING THE WRONG THING. The answer is: KEEP ASKING THE AGENT, ADD NO HARD GATE ON ITS VERDICT, AND GIVE IT A PRE-WORK BASELINE AS INFORMATION so it can answer correctly. The baseline runs IN PARALLEL, in its OWN WORKTREE, PINNED TO THE ITEM'S OWN RECORDED BASE COMMIT.
  THE MAINTAINER REJECTED THE ABUSE FRAMING, and the rejection is correct and is recorded verbatim in substance because it should not be re-litigated: "You cannot build a pre-test that detects deception and every model we use is certainly smart enough to make tests pass. You cannot rigidly check for change, because we are asking models to change things ... a malicious, deceptive agent can easily circumvent the gate, but we're NOT worried about malicious agents, because malicious agents can rewrite the code that keeps the gate and do much more than just 'sneak' past a puny little gate. The raised issue in my mind is a red herring. We're mitigating sloppiness, not malice. Asking the agent is 100% the right move." The maintainer also noted, correctly, that rigid programmatic gates in this repository "keep biting us in time and money". So option (c) (narrow the verdict to non-integrating) and any hard refusal keyed on the verdict are REFUSED, and this question's original framing as an authority/abuse problem is withdrawn.
  WHAT SURVIVES THE RE-FRAMING, AND IS THE ACTUAL JUSTIFICATION: THE AGENT CANNOT ANSWER THE QUESTION ACCURATELY EVEN WHEN PERFECTLY HONEST. To say a failure is PRE-EXISTING it must know the test was already failing before it started, and it has no way to know that. Measured: `run_suite_check` is called exactly ONCE per attempt, AFTER the work, at `oc_runipd.py:6670` and `agy_runipd.py:3724`, and nothing persists a prior result anywhere (`suite_check` appears only at those two write sites plus the re-export at `agy_runipd.py:320`). So a well-meaning agent that broke something subtly, and genuinely believes the failure is unrelated, will answer `SAFE TO IGNORE.` in good faith and be WRONG. That is exactly the SLOPPINESS the maintainer wants mitigated, not malice, which is why the baseline survives while the gate does not.
  SO THE BASELINE IS CONTEXT, NOT A CHECK. It is handed to the agent so it can distinguish pre-existing noise from its own breakage. Nothing programmatic refuses a verdict on the strength of it. This is the distinction that made the maintainer accept it after rejecting the gate.
  THE PARALLEL DESIGN, WHICH THE MAINTAINER ASKED FOR AND WHICH REMOVES THE COST OBJECTION. (1) RUN IT CONCURRENTLY WITH THE AGENT TURN. The baseline is ~81 seconds (measured: `5859 passed, 3 skipped, 2 xfailed in 80.96s`) while an execute turn is minutes to hours, so starting it at dispatch and collecting it at turn end makes the added wall-clock essentially ZERO. It only costs anything for a turn shorter than the suite, which does not occur in practice. (2) PIN IT TO THE ITEM'S OWN BASE COMMIT, NOT TO MAIN. This answers the maintainer's own question about a human or another agent updating main mid-turn: pinned to the recorded base, the baseline remains the correct before-picture for THIS item regardless of what lands meanwhile. The base is already recorded (`item["preserved_base"]`, `oc_runipd.py:6900`; `wt_handle.base_commit`; `worktree_lease.allocate_worktree` takes `base_commit` at `:554` and resolves it at `:587`). Pinning to a COMMIT rather than a moving branch is what makes the answer trustworthy. (3) USE ITS OWN WORKTREE, which is REQUIRED and not merely tidy: running the suite in the primary checkout while an agent works there would read half-written files.
  ONE MEASURED TRAP THE IMPLEMENTOR MUST HANDLE, or the baseline will be wrong in a way that looks like real failures: THE SUITE BEHAVES DIFFERENTLY IN A LINKED WORKTREE. `run_suite_check`'s own docstring records why it insists on the primary checkout (`oc_runipd.py:3637-3646`): a linked worktree resolves `.aw/state` relative to cwd (backlog `dh0uno`), and `tests/test_run_viewer.py` gives `36 passed` in the primary checkout against `15 failed, 20 passed` in a lane, every failure being the state-resolution family. A naive worktree baseline therefore reports ~15 phantom failures. The baseline must either neutralize that state resolution or subtract the known-divergent set explicitly, and MUST NOT be compared naively against a primary-checkout post-run result, because the two are not measured under the same conditions. This is the single highest risk in the design and it is not optional.
  COST NAMED HONESTLY, since the maintainer's time-and-money objection applies: a second checkout of the repository plus a full suite run means real disk and CPU concurrent with the agent turn. Accepted on the basis that wall-clock is unaffected.
  SCOPE CONSEQUENCE, RESOLVED BY THE MAINTAINER IN THE SAME EXCHANGE: THE BASELINE IS SPLIT OUT INTO A NEW CHILD, `9lyg5h` (`integearn` Order 5), which declares `Item-Dependencies: executed:daexj1`. Asked directly whether the decision needed a replan or a breakup, the maintainer chose the split. THE MEASUREMENT BEHIND IT: this plan already carries TEN E-items across EIGHT files and already reads `Readiness: no-go`, so it was at or past a reviewable unit's capacity before the decision existed, and the baseline is a NEW CAPABILITY (a second checkout per item, commit-pinned, running a suite concurrently with the agent turn, plus neutralizing a measured ~15-test phantom-failure divergence) rather than a detail, in a plan that contains essentially no concurrency.
  THE SEAM IS CLEAN, WHICH IS WHY THIS PLAN NEEDS NO RE-CUTTING: this plan's value stands alone (asking the agent instead of silently refusing is what fixes the eleven-lane stranding), and the baseline only makes the agent's ANSWER more accurate. So THIS plan ships first and is unchanged by the ruling except for E-05, which must leave room for `9lyg5h` E-04 to add one context block to its prompt without reshaping it.
  CHECKED RATHER THAN ASSUMED, and it matters for this plan's own next step: this plan's `no-go` was NOT a size verdict. Its review round 1 records `Verdict: REVIEWED - OPEN QUESTIONS` with one advisory `IPD-Z602` density note and no structural error, and the blocking question was THIS one. With OQ-02 now resolved, this plan's readiness should be RE-EXAMINED rather than re-cut; that is a review action, not an authoring one.
  AND THE REFUSED HALF STAYS REFUSED: option (a) as originally written ("refuse `SAFE TO IGNORE.` for any id absent from the baseline") is REJECTED, so `9lyg5h` is authorized to supply INFORMATION only, and its E-05 exists specifically to prove no code path refuses on it.
## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a real evidence record built from a genuinely failing suite run, showing the failing ids present as a list and NO raw output field. Paste `aw sanitize --agent` over that record showing `findings: 0`. Paste the diff of `build_tool_event` showing where the ids are added and that hashing/truncation behavior is otherwise unchanged.
  - Observed evidence: VERIFIED, and with one SUBSTITUTION recorded as decision D-2 rather than smuggled: the failing-id capture E-01 asked for was ALREADY SHIPPED by a LATER plan, `h5pyqa` (`gatewire-01`, `- Status: executed`, 2026-09-20), and it is sited differently than E-01 prescribes. E-01 asked for extraction inside `run_evidence.capture_command` with a typed field on the LEDGER record; what ships is `capture_command` returning the output text on the mapping it hands back (`run_evidence.py:524-537`) with extraction in `oc_runipd.extract_suite_failures` (`:3955`) and the typed list persisted on the DURABLE RUN RECORD at `attempt["suite_check"]["failures"]` (`runner_shared.py:16084`). All four of E-01's stated properties were re-measured HERE rather than assumed.
DRIVEN AGAINST A REAL FAILING SUITE, capture UNSTUBBED. A temporary `test_probe.py` with one passing and two genuinely failing tests (one bare assertion, one raised `ValueError`) was run through the production path:
```
=== exit code (real) === 1
=== failing ids extracted from REAL output ===
    FAILED test_probe.py::test_genuinely_fails - assert 1 == 2
    FAILED test_probe.py::test_also_fails - ValueError: boom
```
PROPERTY 1, the ids are a typed list on the record the driver persists. `run_suite_check` on the same fixture:
```
{
  "suite_check": {
    "passing": false,
    "exit_code": 1,
    "summary": "2 failed, 1 passed in 1.84s",
    "failures": [
      "FAILED test_probe.py::test_also_fails - ValueError: boom",
      "FAILED test_probe.py::test_genuinely_fails - assert 1 == 2"
    ]
  }
}
```
PROPERTY 2, RAW OUTPUT IS STILL NOT PERSISTED. The LEDGER record built from that same real output carries digests and lengths only; measured key list:
```
['actor','argv','cwd','env','exit_code','kind','parent','run_id','schema_version','seq','stderr_len','stderr_sha256','stdout_len','stdout_sha256','timestamp','truncated']
raw output persisted in ledger record? False
```
`build_tool_event`'s hashing/truncation behavior is UNCHANGED by this plan: `git diff -- agent_workflows/run_evidence.py` is EMPTY (the file was declared in `Scope-Paths` and needed no edit, see D-2), so there is no diff to paste and that absence IS the evidence that hashing was not touched.
PROPERTY 3, THE F-10 BUG IS FIXED AND I CONFIRMED IT RATHER THAN INHERITING THE CLAIM. `SuiteCheckResult.summary` measured NON-EMPTY on a real run: `'2 failed, 1 passed in 1.84s'`. F-10 states it was ALWAYS `""` in production; it is not now. The repair is `h5pyqa`'s, in `capture_command`, and `run_suite_check`'s docstring (`oc_runipd.py:4049-4057`) records it.
PROPERTY 4, SANITIZER CLEAN over a record containing real captured ids:
```
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
EXIT: 0
```
`findings: 0`, exit 0. A node id is repository-relative (`tests/test_x.py::Class::test_y`) and carries no home path, which is now PINNED by `tests/test_suite_adjudication.py::TheFailingIdsComeFromREALCapturedOutput::test_a_node_id_carries_no_machine_identifying_string` rather than only argued.
AND THE HOLE THAT LET F-10 SHIP IS NOW CLOSED: six new cases in `TheFailingIdsComeFromREALCapturedOutput` drive the REAL `capture_command`, including `test_the_capture_was_NOT_stubbed_and_the_real_command_really_ran` and `test_the_DURABLE_record_still_carries_no_raw_output`. The pre-existing tests could not see F-10 because they stub the capture and fabricate the key (F-6).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the test that supplies a NON-ZERO exit with an EMPTY failing list and asserts ESCALATION, plus its passing result. Paste the code showing the exit code is consulted before the list is used. This is the anti-inversion guard and a passing suite alone does not satisfy it.
  - Observed evidence: VERIFIED. The anti-inversion guard is now pinned BEHAVIORALLY and STRUCTURALLY, in `tests/test_suite_adjudication.py::TheExitCodeIsTheAuthorityAndNotTheList` (6 cases, all passing).
THE REQUIRED CASE, a NON-ZERO exit with an EMPTY failing list, asserts ESCALATION. Measured live before writing the test:
```
red exit + EMPTY list -> earned: False | signal: suite-failed
  escalates (asks the agent)? True | the driver-run suite refused integration and the turn's session is resumable
green -> earned: True | asks a question? False
```
So an empty list with a red exit does NOT integrate (which is `32ij2j`'s inversion) and does NOT silently refuse either: it escalates. `test_a_RED_exit_with_an_EMPTY_failing_list_still_ESCALATES` and the harsher `test_a_RED_exit_with_an_EMPTY_list_and_an_EMPTY_summary_still_escalates` both pass.
THE CODE SHOWING THE EXIT CODE IS CONSULTED AND THE LIST IS NOT. `integration_is_earned` (`oc_runipd.py:4159`) branches ONLY on `suite_result.passing`, which `run_suite_check` sets from the observed exit code; the verdict never reads `failures`. Rather than assert that by reading, it is pinned over the AST in `test_the_verdict_reads_PASSING_and_never_the_failing_list`, which walks the function and asserts `"passing" in attrs` and `"failures" not in attrs`. That is the guard the plan asked for: the moment the verdict consults the list, an empty list acquires decision power and the inversion becomes reachable again, and this test goes red.
THE ORDERING IS PINNED IN BOTH DIRECTIONS, so it is not one-sided: `test_a_PASSING_exit_earns_integration_regardless_of_the_list` feeds a PASSING result carrying a nonsense non-empty `failures` tuple and asserts it still earns. Exit 0 decides; the list is decoration for the question.
AND THE SIGNAL-LESS CASES REFUSE FAIL-CLOSED: `test_a_TIMEOUT_and_an_UNRUNNABLE_suite_both_refuse_fail_closed` covers exit 124 and 127, neither of which carries any ids at all, and both escalate rather than integrate.
A PASSING SUITE ALONE DOES NOT SATISFY THIS ITEM, per the plan's own instruction, which is why the evidence above is the specific red-exit-empty-list case and its AST guard rather than a green run.
```
python3 -m pytest tests/test_suite_adjudication.py -o addopts="" -q
42 passed in 3.96s
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff` of both hosts' validation-runner builders showing `return True` replaced by a real run, and paste a gate execution log showing the suite actually ran against the MERGED tree (name the tree path and show the work present in it).
  - Observed evidence: VERIFIED, and this is the item that changed real behavior. THE STUB IS GONE.
BOTH HOSTS' BUILDERS, `git diff`:
```
+        # integearn-03 (`daexj1`) E-03: pass THIS host's `run_suite_check` so the gate's revalidation
+        # step measures the merge result instead of returning a constant True.
-            make_integration_validation_runner(state, run_dir, item),
+            make_integration_validation_runner(
+                state, run_dir, item, suite_check=run_suite_check
+            ),
```
(identical shape in `agy_runipd.py` with `dict(item)`, plus the `validation_runner_for` site on each host). The shared factory `make_integration_validation_runner` (`runner_shared.py:12601`) no longer contains `return True`; its body now materializes the merge result and runs the injected suite there. `tests/test_runner_shared.py::ReintegrationVerbTests::test_the_validation_runner_is_NOT_the_shipped_constant_true_one` was UPDATED rather than deleted: its old assertion `assertTrue(shipped(...))` pinned the constant-True behavior and is now `assertFalse(...)`, because with no checker injected the runner FAILS CLOSED. The reason for the change is written into the test.
THE SUITE RAN AGAINST A TREE THAT ACTUALLY CONTAINS THE WORK, which is the whole point and is what the primary checkout cannot do (isolation defaults ON). A real git fixture: `main` holds `test_base.py`, lane `aw/lane/xx1111` adds `test_lane_work.py`, and main does NOT have that file. Driving the real runner:
```
base: 4f7a15284751 head: dcaace1695a0
main tree contains the lane's file? False (must be False)

=== RESULT ===
runner verdict: True
suite ran in: .../run/revalidation/revalidate-7982efc7ce5d
that tree CONTAINS the lane's new file? True <-- THIS is the E-03 property
that tree also contains the base file? True

=== recorded on the item ===
{
  "passed": true,
  "tree": "7982efc7ce5d1fbfc9681d293a10b3e6863590d2",
  "reason": "green",
  "failures": [],
  "merged_files": ["test_lane_work.py"],
  "cached": false
}

ephemeral worktree cleaned up? True
```
The named tree path is `<run_dir>/revalidation/revalidate-<tree12>`, and the work is demonstrably present in it.
AND THE GATE CAN NOW SAY NO, which it structurally could not before. A red post-merge suite:
```
=== COMBINED-RED case ===
verdict (must be False): False
recorded: {"passed": false, "tree": "73ddc921b4be...", "reason": "combined RED", "failures": ["FAILED t::x"], ...}
```
WHY A TREE HAD TO BE MATERIALIZED AT ALL, since the plan assumed one existed: `execute_merge_and_revalidate_gate` is DIFF-BASED (it concatenates lane diffs and calls `full_validation_runner(combined_diff, merged_files)` at `orchestrate_isolation.py:1160`), and the real `git merge` happens only AFTER the gate passes. So at gate time NO merged tree exists on disk. New `materialize_merge_result` builds one with `git merge-tree --write-tree` + `git commit-tree` + a DETACHED `git worktree`, writing no ref and touching no working tree; `test_materializing_creates_NO_branch_and_moves_NO_ref` asserts `git show-ref`, `HEAD` and `git status --porcelain` are all byte-identical afterwards, which matters because this runs in a checkout other agents share.
THE `dh0uno` BLOCKER THE PLAN INHERITED IS STALE, and I re-measured rather than trusting either side. That backlog item is `- Status: done` (fixed in `6771e590`) and its OWN history retracts the claim: "NOTE the old acceptance claim that ~15 test_run_viewer failures ARE this bug was false". Measured in THIS lane, a real linked worktree (`git rev-parse --git-dir` = `.git/worktrees/daexj1_attempt2`): `python3 -m pytest tests/test_run_viewer.py` -> `91 passed`. Not 15 failed.
THE DOCSTRING'S PRINCIPLE IS NOW ENFORCED: `orchestrate_isolation.py:1159` says "Per-lane green NEVER implies integrated green!" and until this change the runner it called could only return True.
FOUR FAIL-CLOSED PATHS, each measured: no checker injected, unresolvable base/head, an unmaterializable (conflicting) merge, and an exception from the suite all return False. `test_materializing_a_CONFLICTING_merge_returns_None_and_not_a_guess` also proves the three-valued discipline (None is not empty and not a pass) against a genuine conflict fixture.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste measured gate wall time before and after, and paste evidence from a multi-lane run that the suite ran ONCE per distinct base rather than once per lane (a count, not an assertion).
  - Observed evidence: VERIFIED, with the cost MEASURED rather than estimated and recorded in the code as E-04 requires (`runner_shared.py`, `make_integration_validation_runner` docstring, section "THE COST, MEASURED RATHER THAN ESTIMATED (2026-09-21 ...)").
BEFORE: the gate's revalidation step cost ~0s, because its runner's entire body was `return True`. There is no wall time to measure for a function that returns a constant, and saying so is the honest before-number.
AFTER, measured at HEAD `64f5254c` on this repository, driving the REAL suite inside a REAL materialized merge result:
```
MATERIALIZE the merge result: 0.40s  (tree 7224bfe8d003, why='')
worktree: revalidate-7224bfe8d003 | contains agent_workflows? True
RELEASE the worktree:        0.06s
GIT OVERHEAD TOTAL:          0.45s  (the suite run itself dominates)

measuring the REAL suite inside the materialized merge result...

POST-MERGE SUITE RUN: 106.59s wall
  passing: False | exit: 1
  summary: 1 failed, 7694 passed, 3 skipped, 2 xfailed, 3 warnings in 105.50s (0:01:45)
  failures: 1
     FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
cleaned up: True
```
So: 107.04s total per distinct merge result, of which the SUITE is 106.59s and the machinery this plan adds is 0.45s. The bare suite in the primary checkout measured 110.30s in the same session, so a post-merge run costs about the same as the run the driver already performs; a serial run of N items with N distinct merge results roughly DOUBLES total suite time. That is stated plainly in the docstring rather than hidden. (Note the single failure in that measurement is the environmental one discussed in V-09 and filed as backlog `se8vsp`; it is not caused by this work and does not affect the timing.)
ONCE PER DISTINCT BASE, PROVEN AS A COUNT AND NOT AN ASSERTION, which is what the plan demanded. Two items sharing one merge result:
```
=== E-04 CACHE: same merge result twice ===
suite invocations for the SAME tree: 1 (must be 1, second was cached)
second call recorded cached flag: True
cache contents: {'73ddc921b4be': {'passed': False, 'reason': 'combined RED'}}
```
and `test_the_suite_runs_ONCE_per_distinct_merge_result` asserts `len(calls) == 1` across two separate runner invocations, while `test_a_DIFFERENT_merge_result_is_measured_SEPARATELY` asserts `len(calls) == 2` for two genuinely different merges, so the cache cannot answer for a tree it never measured.
THE CACHE KEY IS THE MERGED TREE ID, not the lane and not the base, and that choice is the honest one: the tree IS the identity of the thing tested, so two lanes merging to the same tree are one measurement and a lane whose merge differs gets its own. It is sited on `state` (`REVALIDATION_CACHE_KEY`) rather than in a module global, so its lifetime is the run's.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the actual adjudication prompt text as issued, showing the expectation, the observed failing ids, and all three required sentinels verbatim. Paste the prompt as recorded in the run's prompts directory.
  - Observed evidence: VERIFIED BY EQUIVALENCE, and the substitution is recorded as decision D-1 rather than presented as a literal match. E-05 specifies three exact prose sentinels parsed from worker stdout (`SAFE TO IGNORE.`, `RETRY TESTS.`, `UNABLE TO FIX.`). The mechanism that SHIPPED is `h5pyqa` (`gatewire-01`, executed 2026-09-20, under a maintainer ruling of that date): a four-answer JSON vocabulary written into the outcome file, `not-mine` / `fixed` / `mine` / `needs-human`. I did NOT build a second parser, because E-09's own anti-divergence requirement forbids exactly that ("a second copy of a sentinel parser is exactly how the two hosts drift on what counts as a verdict").
THE ACTUAL PROMPT AS ISSUED, `gate_answer_question` (`runner_shared.py:12053`), rendered with real failing ids:
```
Your work is committed on your lane, but integration is REFUSED because the full
test suite did not pass. This is a question, not an accusation: the suite covers the WHOLE repository
and other work lands in it, so a failure here is often nothing to do with your turn.

THE FULL TEST SUITE REPORTED:

FAILED tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today - AssertionError
FAILED tests/test_other.py::test_thing - assert 1 == 2

THE FILES YOUR TURN CHANGED:

  agent_workflows/runner_shared.py
  tests/test_suite_adjudication.py

Compare the two and answer by writing ONE object into the `integration_gate_answer` key of the outcome JSON
you already wrote. Change nothing else in that file unless you are answering `fixed`.

  "integration_gate_answer": {"answer": "<not-mine|fixed|mine|needs-human>", "reason": "<why, one line>"}

WHAT EACH ANSWER DOES, so you are choosing an outcome and not a label:

  not-mine
      ... YOUR LANE IS THEN INTEGRATED. ...
  fixed
      ... THE FULL TEST SUITE IS RE-RUN and the re-run decides, not your claim. ...
  mine
      ... INTEGRATION IS REFUSED and your lane and branch are PRESERVED ...
  needs-human
      ... INTEGRATION IS REFUSED and your lane is PRESERVED ... waiting on a DECISION rather than on work.

CHOOSE THE ANSWER THAT IS TRUE. ...
Your answer is recorded on the run record under your name and is reviewable, exactly like a `V-*`
evidence block. Claim `not-mine` only if you believe it.
```
E-05'S FOUR REQUIRED ELEMENTS, each checked mechanically rather than by eye:
```
  True  states the EXPECTATION (suite must pass)
  True  shows the OBSERVED failing ids
  True  offers all available verdicts
  True  states the CONSEQUENCE of each
  True  does NOT accuse
```
THE PROMPT IS RECORDED IN THE RUN'S PROMPTS DIRECTORY like every other: the wiring calls `write_prompt(run_dir, item, gate_prompt_text, attempt_no, suffix="gate-answer")` on both hosts (`runner_shared.py:16487` and `:16512`), so it lands beside the turn's other prompts with a `gate-answer` suffix.
MATCHING IS ANCHORED, NOT LOOSE SUBSTRING, which E-05 required: `validate_gate_answer` (`:11999`) tests `token not in GATE_ANSWERS` against a closed tuple. Proven by behavior in `test_an_UNKNOWN_token_refuses_and_is_named_in_the_record`, which feeds the literal string `SAFE TO IGNORE.` and asserts it REFUSES and is recorded as a violation: a sentinel merely discussed in prose cannot be mistaken for a verdict.
AND F-13's HAZARD IS NOT REPRODUCED. The plan warned that the nearest agent-verdict reader FAILS OPEN (`oc_runipd.py:6622-6633` upper-cases and loose-substring-tests, then `else: verify_disp = "verified"`). The adjudication path does the opposite: an unrecognized token, a missing reason, an absent file and an interrupted turn all refuse.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: four separate demonstrations with their outcomes: `SAFE TO IGNORE.` integrates and records the explanation; `RETRY TESTS.` re-runs and re-adjudicates; `UNABLE TO FIX.` preserves the lane; and a reply with NO sentinel re-prompts and then exhausts to a refusal. Paste the configured caps and show exhaustion refusing rather than integrating.
  - Observed evidence: VERIFIED. All four demonstrations below are automated cases in `tests/test_suite_adjudication.py::TheThreeVerdictsDriveTheirActions`, driven through the SHIPPED `perform_gate_answer` with a stubbed ask (no paid model turn, no real suite run), and each names the daexj1 sentinel it stands for per D-1.
1. `SAFE TO IGNORE.` == `not-mine` INTEGRATES AND RECORDS THE EXPLANATION. `test_SAFE_TO_IGNORE_integrates_and_records_the_explanation`: `result.release` is True and `record["reason"]` carries the agent's sentence ("the failure is in a file my diff never touched").
2. `RETRY TESTS.` == `fixed` RE-RUNS AND RE-ADJUDICATES, and is STRICTER than the plan asked. `test_RETRY_TESTS_re_runs_and_the_RERUN_decides_not_the_claim`: the suite is actually re-run (`len(runs) == 1`), `recheck_passed` is True, and release follows the OBSERVED RE-RUN rather than the claim. Its complement `test_a_RETRY_claim_whose_rerun_STAYS_RED_refuses` proves an unverified repair claim never releases (`recheck_passed` False, `release` False).
3. `UNABLE TO FIX.` == `mine` REFUSES AND PRESERVES THE LANE. `test_UNABLE_TO_FIX_refuses_and_the_lane_is_preserved`: `release` False, `record["refuses"]` True. Nothing is discarded; this is the correct outcome for a genuinely broken change.
4. NO SENTINEL RE-PROMPTS THEN EXHAUSTS TO A REFUSAL. `test_NO_VERDICT_refuses_rather_than_integrating`: the agent IS asked (one prompt issued), and an absent verdict lands on REFUSE with `record["usable"]` False. `test_an_UNKNOWN_token_refuses_and_is_named_in_the_record` covers the malformed case the same way.
BOTH LOOPS ARE CAPPED, and the configured cap is the run's OWN EXISTING `--retry-budget` rather than a new knob, which is the maintainer's 2026-09-20 ruling (share it, add no second knob). Verified structurally:
```
  retry loop bound comes from the run's existing budget: True   (retry_budget in perform_gate_answer)
  ask is bounded at ONE per attempt structurally (already_asked): True
```
The ask bound is STRUCTURAL rather than a counter: `gate_answer_is_warranted(..., already_asked=...)` refuses a second ask in the same attempt, and `test_it_is_bounded_at_exactly_one_ask_per_attempt` in the sibling file pins it.
EXHAUSTION REFUSES RATHER THAN INTEGRATING, which is the safe direction the plan demanded. `test_the_RETRY_loop_is_BOUNDED` asserts re-runs never exceed the budget (`len(runs) <= 2` with budget 2) and that an always-red repair claim ends with `release` False. `test_a_ZERO_budget_never_verifies_and_therefore_refuses` covers budget 0: a `fixed` claim that cannot be verified simply refuses, which is the correct reading of an operator who asked for no corrections.
OQ-01 (how many retries/re-prompts) is therefore ANSWERED BY THE SHIPPED DESIGN rather than by a number I invented: the budget is the run's own, its default is 2, and the reasoning is recorded in `perform_gate_answer`'s docstring.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the run-state fragment after a `SAFE TO IGNORE.` adjudication showing the verdict, the explanation, the shown ids and the retry count, sitting alongside the existing `integration_signal` field.
  - Observed evidence: VERIFIED. The adjudication is recorded DURABLY, in normalized form, at the same per-item seam that writes `integration_signal`, by BOTH hosts. The record after a `not-mine` (== `SAFE TO IGNORE.`) adjudication, produced by the shipped `gate_answer_record` (`runner_shared.py:12252`):
```
{
  "answer": "not-mine",
  "reason": "unrelated flake",
  "violation": "",
  "usable": true,
  "integrates": true,
  "refuses": false,
  "awaits_human_decision": false,
  "asked": true,
  "ask_reason": "suite failed",
  "session_id": "sess-1",
  "signal": "suite-failed",
  "failing_tests": [
    "FAILED t::x",
    "FAILED t::y"
  ],
  "recheck_attempts": 0,
  "recheck_budget": 2,
  "recheck_passed": null,
  "recheck_summary": ""
}
```
EVERY FIELD E-07 NAMED IS PRESENT: the verdict (`answer`), the agent's explanation (`reason`), THE FAILING IDS IT WAS SHOWN (`failing_tests`), and the retry count (`recheck_attempts`, with `recheck_budget`/`recheck_passed`/`recheck_summary` beside it). `session_id` additionally answers "WHO decided that", which E-07's stated purpose requires.
IT SITS ALONGSIDE `integration_signal`, as required. Location and shape are a documented contract: `state["queue"][i]["integration_gate_answer"]` in `<run_dir>/state.json`, written at the same seam as `item["integration_signal"]` (`runner_shared.py:16090-16092` writes the signal; `:16234-16235` writes `attempt[GATE_ANSWER_RECORD_KEY]` and `item[GATE_ANSWER_RECORD_KEY]`). `signal` is carried INSIDE the record too, so a reader holding only the adjudication knows which refusal it answered.
PINNED BY TESTS rather than only demonstrated: `test_every_adjudication_is_recorded_with_the_ids_it_was_SHOWN` asserts all six fields are present AND that `failing_tests` is non-empty, because without the ids a reviewer cannot check the answer against the failures it was given, which is exactly what makes a `not-mine` auditable rather than invisible.
THIS PLAN ALSO ADDS A SECOND DURABLE RECORD at the same level, for the revalidation E-03 introduced: `item["post_merge_revalidation"]` carries `passed`, the merged `tree` id, `reason`, `failures`, `merged_files`, `cached` and `skipped`. It is needed for the same reason: a refusal an operator cannot explain is indistinguishable from a bug, and `integration_failed_combined_red` alone does not say WHICH tree was tested or WHAT failed in it. The `skipped` flag deliberately distinguishes "measured and passed" from "not measured, and here is why", so a verifier-governed item is never presented as a suite measurement that never happened.
REPORTING IS EXPLICITLY NOT THIS ITEM'S JOB (it belongs to sibling `ys1dor` and backlog `nuanaw`); this item only ensures the fact is recorded where a reader can find it, which it is.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste all six cases with results, and paste proof the capture was NOT stubbed (show the real command run and its real output feeding the ids). Paste the ids captured from that real run.
  - Observed evidence: VERIFIED. `tests/test_suite_adjudication.py` is new and carries 42 passing cases:
```
python3 -m pytest tests/test_suite_adjudication.py -o addopts="" -q
42 passed in 3.96s
```
ALL SIX REQUIRED CASES ARE PRESENT AND PASSING:
1. A genuinely red suite yields a NON-EMPTY id list -> `TheFailingIdsComeFromREALCapturedOutput::test_a_genuinely_red_suite_yields_a_NON_EMPTY_id_list`, which also asserts a PASSING test never appears in the failing list.
2. Each verdict drives its correct action -> `TheThreeVerdictsDriveTheirActions` (9 cases; see V-06).
3. A missing sentinel re-prompts then exhausts to a refusal -> `test_NO_VERDICT_refuses_rather_than_integrating`, `test_an_UNKNOWN_token_refuses_and_is_named_in_the_record`, `test_the_RETRY_loop_is_BOUNDED`.
4. The E-02 inversion guard (red exit + empty list still escalates) -> `TheExitCodeIsTheAuthorityAndNotTheList` (6 cases; see V-02).
5. A clean suite still integrates with NO prompt issued -> `AGreenSuiteIsNeverTaxedWithAQuestion::test_a_clean_suite_integrates_with_NO_question_asked`, so the escalation cannot become an unconditional tax on every green run.
6. Both hosts share every symbol by identity -> `BothHostsShareEveryAdjudicationSymbol` (see V-09).
PROOF THE CAPTURE WAS NOT STUBBED, which is the specific hole this item exists to close (F-6: the pre-existing tests stub `capture_command` at `tests/test_novalnomerge_integration.py:293`, `:319`, `:343` and fabricate the very key production never wrote, so they could not have noticed F-4/F-10). The new cases drive a REAL subprocess. `test_the_capture_was_NOT_stubbed_and_the_real_command_really_ran` calls the production `run_evidence.capture_command` directly on a temporary `test_probe.py` that genuinely fails, and asserts the real exit code and that real output text came back:
```
=== exit code (real) === 1
=== failing ids extracted from REAL output ===
    FAILED test_probe.py::test_genuinely_fails - assert 1 == 2
    FAILED test_probe.py::test_also_fails - ValueError: boom
```
THE IDS CAPTURED FROM THAT REAL RUN are the two lines above; the fixture deliberately uses two DIFFERENT failure shapes (a bare assertion and a raised exception) because they render differently in pytest's short summary and a parser handling only one would look correct against a single-shape fixture. `test_the_ids_are_NOT_a_count_line` asserts every captured line contains `::`, since a count cannot be attributed to a diff.
THE OTHER DECLARED TEST SURFACE STILL PASSES: `python3 -m pytest tests/test_novalnomerge_integration.py tests/test_gate_answer_wiring.py -o addopts="" -q` was run as part of the focused set and is green (318 passed alongside `test_runner_shared.py` in the same invocation, then 322 passed for the three integration files after the two-mode fix).
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste an object-identity assertion (`oc.<symbol> is agy.<symbol>`) returning True for the adjudicator, the sentinel parser and the validation runner; paste a grep showing `agy_runipd` gained no new import from `oc_runipd`; paste the bare `python3 -m pytest` summary line compared to the stated baseline.
  - Observed evidence: VERIFIED BY OBJECT IDENTITY, not by grep, as required.
```
=== V-09 OBJECT IDENTITY ===
  gate_answer_is_warranted: shared-only, runner_shared.gate_answer_is_warranted present -> True
  perform_gate_answer: shared-only, runner_shared.perform_gate_answer present -> True
  validate_gate_answer: shared-only, runner_shared.validate_gate_answer present -> True
  gate_answer_question: shared-only, runner_shared.gate_answer_question present -> True
  gate_answer_record: shared-only, runner_shared.gate_answer_record present -> True
  oc.make_integration_validation_runner is agy.make_integration_validation_runner -> True
  materialize_merge_result: shared-only, runner_shared.materialize_merge_result present -> True
  release_merge_result: shared-only, runner_shared.release_merge_result present -> True
  oc.run_suite_check is agy.run_suite_check -> True
  oc.integration_is_earned is agy.integration_is_earned -> True
  oc.SuiteCheckResult is agy.SuiteCheckResult -> True
```
Every symbol this plan touches is ONE object. The adjudicator (`perform_gate_answer`), the verdict parser (`validate_gate_answer`) and the validation runner (`make_integration_validation_runner`, plus this plan's new `materialize_merge_result` / `release_merge_result`) all live in `runner_shared.py` and are reached by both drivers; `test_the_adjudication_logic_lives_in_the_SHARED_module` asserts `__module__ == "agent_workflows.runner_shared"` for each, so a later re-fork into a host driver fails the test.
NO NEW CROSS-DRIVER IMPORT:
```
=== V-09 no new cross-driver import ===
  adjudication/revalidation symbols imported from oc_runipd: NONE
```
`test_agy_gained_NO_new_direct_import_of_the_adjudication_seam` AST-walks `agy_runipd.py` and asserts none of the adjudication symbols arrive via `from ...oc_runipd import`. It is deliberately SCOPED to this plan's symbols: agy legitimately imports many names from oc for historical reasons, so a blanket "zero oc imports" assertion would fail for reasons unrelated to this change and would be a false guard. `test_the_shared_module_imports_NO_host_driver` re-asserts the existing rule in the other direction, which matters because this plan ADDS to that module.
BOTH HOSTS ACTUALLY WIRE THE NEW INJECTION, asserted over the AST so a host cannot silently keep the old call shape: `test_BOTH_hosts_pass_their_own_suite_checker_to_the_factory` finds every `make_integration_validation_runner(...)` call in each driver and requires `suite_check` among its keywords. Without that, a host's integration gate would fail closed on every lane.
THE BARE SUITE, COMPARED TO MY OWN MEASURED BASELINE. Baseline taken at turn start, BEFORE any edit:
```
1 failed, 7694 passed, 3 skipped, 2 xfailed, 3 warnings in 110.30s (0:01:50)
FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
```
After all work:
```
1 failed, 7736 passed, 3 skipped, 2 xfailed, 3 warnings in 102.08s (0:01:42)
FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
```
DELTA: +42 passed (exactly the new file), SAME single failure, no new failure. THE PLAN'S AUTHORED BASELINE WAS STALE AND I DID NOT TRUST IT, as it instructed: it predicted a `test_reporting_contract` failure (backlog `8kttqq`); that test passes here, and the one failure is a DIFFERENT environmental defect. I proved it environmental in both directions on the same tree and commit: `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` gives `43 passed`, while a bare run gives 1 failed. The test asserts a non-isolated turn gets NO denial policy, and it reads the `OPENCODE_CONFIG_CONTENT` inherited from MY OWN runner turn's environment. It is not caused by this work and is filed as backlog `se8vsp`.
INTERMEDIATE HONESTY, DISCLOSED RATHER THAN HIDDEN: my first E-03 implementation broke 14 tests across `test_oc_runipd.py`, `test_agy_runipd_cli.py` and `test_runner_backlog_close_in_lane.py`, because it ran a post-merge suite even for `--validate`-ON items whose trust signal is the VERIFIER's verdict. I FIXED the implementation rather than the tests (see V-03 and the two-mode section of the factory's docstring); all 322 tests in those three files now pass.
  - Result: pass
- [x] V-10 validates E-10
  - Required evidence: paste the spec diff. Quote the added exception in full and show, sentence by sentence, that it is conditioned on CAPTURED EVIDENCE (verdict, explanation, shown failing ids) rather than prose, and that it states `ipd_lifecycle.finalize_precheck` still applies unchanged. Paste `git diff --stat` for the spec proving only the intended section changed, and confirm section 4.2's finding-code table is BYTE-IDENTICAL (show the diff is empty for that region, and paste the byte-equality test passing). Paste the spec's appended workflow-history line and confirm `- Status:` was NOT hand-edited. STATE WHICH OQ-02 OPTION THE WORDING ASSUMES and quote the clause that reflects it; if OQ-02 was answered option (a), the exception must say the agent adjudicates pre-existing failures only. Paste the three spec lines this design contradicts (`:64`, `:825-830`, `:897` as they stood before) so a reader can see exactly what was amended and why.
  - Observed evidence: VERIFIED. The amendment is a PURE INSERTION with ZERO deletions:
```
git diff --stat -- .aw/records/specs/approved/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
 ...-01-aw-run-deterministic-run-and-verify.spec.md | 50 ++++++++++++++++++++++
 1 file changed, 50 insertions(+)

deletions: 0   insertions: 50
```
SECTION 4.2's FINDING-CODE TABLE IS BYTE-IDENTICAL, proven two ways. First, the diff contains ZERO removed lines anywhere in the file, so no cell could have changed. Second, the byte-equality test that transcribes those cells into `run_evidence.RUN_FINDING_CODES` passes:
```
python3 -m pytest tests/test_run_evidence_completion.py -o addopts="" -q
87 passed in 1.34s
```
`- Status:` WAS NOT HAND-EDITED. `git diff` shows no change to any metadata line (`- Status:`, `- Id:`, `- Date:` all absent from the diff); the spec remains `approved`. The workflow-history line was appended through the TOOLED path (`aw specs note`), and `aw specs check` reports `all specs conform.`
THE ADDED EXCEPTION, quoted and shown sentence by sentence to be conditioned on CAPTURED EVIDENCE rather than prose. It is titled "The attributed suite-attribution exception" and sits inside section 5.1, immediately after the not-completion-evidence list it qualifies.
  * IT IS SCOPED TO INTEGRATION ONLY: "The general boundary above is UNCHANGED: an agent's prose is still not completion evidence, and this exception permits INTEGRATION of a lane only, never a completion claim." So the general sentence at 5.1 (`:113`, "The agent's prose and exit status are never completion authority") is NOT weakened, which the plan explicitly forbade.
  * ITS CONDITIONS ARE CONJUNCTIVE AND NAMED: the suite did not pass; the signal is specifically the suite-failure signal ("a verifier that explicitly DECLINED is a stronger and more specific judgement and is never answerable by the agent it judged"); and only two answers may release, one on the answer alone and one "only on an OBSERVED PASSING RE-RUN of the full suite, never on the claim".
  * IT IS CONDITIONED ON CAPTURED EVIDENCE, and this is the load-bearing sentence: "The adjudication is admissible only when the run durably records, beside the item's integration signal: the answer token, the agent's stated reason, THE FAILING TEST IDENTIFIERS THE AGENT WAS SHOWN, the session that answered, and the number and outcome of any suite re-runs."
  * IT NAMES THE FAILING-ID LIST AS WHAT MAKES IT REVIEWABLE: "The failing-identifier list is load-bearing and not decoration: a count line ('1 failed') cannot be attributed to a diff, so without the identifiers a reviewer cannot afterwards check the answer against the failures it was given, and the record would be the 'agent-authored summary without captured evidence' this section already refuses."
  * IT REFUSES ANYTHING LESS: "An adjudication lacking any of those fields is not this exception and does not release anything."
  * IT STATES THE FINALIZE GATE STILL APPLIES UNCHANGED: "`ipd_lifecycle.finalize_precheck` applies UNCHANGED afterwards: a current begin receipt, the before-marking-executed lint requiring every `E-*` performed and every `V-*` passing with non-empty observed evidence, and the scope comparison." And it closes: "This exception adds an ATTRIBUTED, REVIEWABLE input to one integration decision; it removes no gate."
  * IT SAYS WHY, with the measured cost of the alternative: eleven lanes stranded and one plan paid twice on 2026-09-08; three lanes, eight cascaded `dependency-blocked` items and $55.02 for nothing on 2026-09-19.
WHICH OQ-02 OPTION THE WORDING ASSUMES, stated plainly as V-10 demands: NEITHER option (a) nor the self-clearing form as originally framed. OQ-02 is `- Status: resolved`, and the maintainer REJECTED a hard programmatic gate on the verdict (2026-09-08, reaffirmed 2026-09-20) and ruled that a pre-work baseline is INFORMATION ONLY. The amendment therefore describes that ruling honestly rather than claiming the stronger constraint, in its final paragraph: "The agent may answer 'not mine' in good faith about a failure it actually caused, because it has no baseline of the suite before its own work and so cannot know what was already red. The maintainer ruled ... that no programmatic gate may refuse the verdict on that basis: a pre-work baseline may be supplied to the agent as INFORMATION so it can answer more accurately, but nothing refuses on it. So this exception mitigates SLOPPINESS and not deception, and ATTRIBUTION is what makes it safe." This is the wording the plan said would be required if option (a) were NOT taken, and it is the accurate one. The baseline itself is sibling `9lyg5h`.
THE THREE CLAUSES THIS DESIGN CONTRADICTS, as they stand (line numbers RE-LOCATED, because the plan's `:64` / `:825-830` / `:897` had all shifted):
  * `:113` "The agent's prose and exit status are never completion authority. Completion comes only from typed repository state, Git state, tool-authored lifecycle receipts, captured command evidence, declared dependency state, and deterministic checks." (UNMODIFIED.)
  * `:930-939` section 5.1's not-completion-evidence list, including "an agent-authored summary or checklist without captured evidence" and "a verifier's opinion". (UNMODIFIED; the new subsection follows it and names captured evidence as its own precondition.)
  * `:1002` "Executor commits remain on the item's isolated branch until scope, commit-content, hook, dependency, and deterministic completion checks pass. Only then may the coordinator integrate the verified commit set." (UNMODIFIED; this is the clause the exception qualifies, and it does so by naming itself an attributed exception rather than by editing the sentence.)
ONE DEFECT FOUND AND REPAIRED WHILE DOING THIS, disclosed because it nearly destroyed another party's records: `aw specs note` TRUNCATES a spec's inline `## Workflow history` to the single newest record (deliberate, `specs.py:342`, deferring to a `.aw/records/history.jsonl` sidecar), but that sidecar is GITIGNORED (`.aw/.gitignore:11`) and held only 2 records on this machine while the spec's inline history held 5 spanning 2026-09-13 to 2026-09-20. Committing the tool's output would have deleted five amendment records from TRACKED history with no tracked copy anywhere. I restored all five by hand from `git show HEAD:<path>`, which is why the diff is a pure insertion, and filed backlog `g31sns`.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. IT IS NOT APPROVABLE YET: OQ-02 is `Blocking: yes` and `Status: open`, so `aw set approved` refuses (`plan_readiness.has_unresolved_blocking_question`), which is the correct fail-closed behavior. That is the ONE thing standing between this plan and execution; everything else review found was repaired in place.

WHY OQ-02 BLOCKS, in one paragraph, because it is the decision the maintainer must make. This design lets the agent that just did the work decide whether its own change may land over a red suite, and as written it accepts `SAFE TO IGNORE.` with no independent check, so an agent can clear a test IT broke. The plan offered a cheap-sounding constraint (refuse the verdict for NEWLY failing tests) and review measured that constraint UNBUILDABLE as described (F-14): the suite runs exactly once, after the work, so no baseline exists and "new" is not computable without a second full suite run. So the real choice is (a) add the baseline and pay another suite run, (b) ship the self-clearing hole and rely on the audit record, or (c) make `SAFE TO IGNORE.` non-integrating. OQ-02 states each with its cost.

A reviewer or maintainer should also know four things review established. FIRST, this plan supersedes `32ij2j` rather than revising it, and review found the superseded plan's defect is ALREADY SHIPPED in the function this plan modifies: `run_suite_check` reads `stdout_excerpt`, which is never written, so `SuiteCheckResult.summary` is always empty in production (F-10). E-01 now fixes that too. SECOND, the spec reconciliation the plan deferred to the executor was done at review and the answer is determinate: spec `25kzda` forbids this design in three places including the integration clause at `:897`, so the amendment is required, its path joined `Scope-Paths`, and new E-10 performs it (F-11). THIRD, the sentinel precedent the plan cited does not exist in shipped code (it is unbuilt plan `m7gvuz`), and the nearest real agent-verdict reader FAILS OPEN in the same function this plan edits, so an executor copying nearby code would reproduce exactly the hazard E-06 forbids (F-12, F-13). FOURTH, its central design remains a MAINTAINER RULING of 2026-09-08, not the author's preference, and nothing in this review disturbs that ruling; the blocking question is about one guardrail on it, not about the approach.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD, which is unusual here and serious: this plan changes the gate that decides whether ITS OWN work is integrated. Verify by behavior in a scratch repository, and if the change strands its own lane, recover it by hand rather than trusting the mechanism under test. Re-locate every citation BY SYMBOL: `oc_runipd.py` and `agy_runipd.py` are the most heavily edited files in the repository. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`.
