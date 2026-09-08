# IPD: Ask the agent to adjudicate a failing suite instead of refusing every lane on any red test

- Date: 2026-09-08
- Kind: child
- Concern: ONE pre-existing red test anywhere in the repository silently refuses lane integration for EVERY plan. With `--validate` defaulting FALSE, `integration_is_earned` falls back to the driver-run suite as its trust signal, and that signal is BINARY over the whole repository: `SuiteCheckResult.passing` is True only on an observed exit 0 (`oc_runipd.py:3610-3624`, verdict at `:3786-3796`). MEASURED HARM 2026-09-08: a single unrelated failure (`tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, caused by a REPLAN verdict on the live plan `32ij2j`) stranded ELEVEN lanes holding fully validated work, and because nothing reported it, plan `03ie04` was executed TWICE for the same fix at `$16.59` then `$32.83`. The lanes were recovered only by a hand audit of `git worktree list`.
- Scope: Replace the binary refusal with a bounded ESCALATION TO THE AGENT, per the maintainer's ruling of 2026-09-08: record the failing test NAMES, and when the suite is not clean, ask the agent that just did the work to adjudicate with three parsable verdicts (safe to ignore / retry / cannot fix) rather than deciding by a fragile programmatic rule. Also fill the revalidation stub so the suite runs where the merged code actually is. Adds NO new refusal that a human cannot see, and changes no verifier semantics.
- Scope-Paths: agent_workflows/run_evidence.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/orchestrate_isolation.py, tests/test_suite_adjudication.py, tests/test_novalnomerge_integration.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: integearn
- Order: 3
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: daexj1
- From-Backlog: ciesaj
- Blocks-Release: next

## Workflow history
- 2026-09-08 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS; PR-401..PR-407; PR-401 escalated to blocking OQ-02

- 2026-09-08 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-401..PR-407, six FIXED, PR-401 (BLOCKER) left OPEN and escalated to OQ-02 (`Blocking: yes`); Readiness `no-go` pending that answer. Reviewed at HEAD `2c727032`; `aw ipd lint` conformed at `--phase author` (one advisory `IPD-Z602` density note) and at `--phase review-finalize`. THE PLAN'S DIAGNOSIS AND DESIGN ARE SOUND and were re-verified rather than trusted: `SuiteCheckResult.passing` is True only on exit 0, `integration_is_earned`'s suite branch is the only correctness signal in the default path, both hosts' `full_validation_runner` bodies really are `return True`, and the eleven-lane incident is present in the durable records (all eleven ids found across `run-20260908T030747Z-1812636` and `run-20260908T030809Z-1812970`). WHAT REVIEW FOUND. FIRST and blocking: the design lets an agent clear a test IT broke, and the plan's own proposed remedy is UNBUILDABLE as described, because the suite runs exactly ONCE post-work (`oc_runipd.py:6656`, `agy_runipd.py:3720`) so no baseline exists and "which failures are new" is not computable without a second full suite run. OQ-02 was reclassified `Blocking: yes` with three costed options; this is a security-relevant policy call about how much authority an agent holds over its own work, and the maintainer already ruled once on this design. SECOND: the spec reconciliation the plan handed to the executor was performed at review and the answer is determinate, not a judgement, since `25kzda` forbids this in three places including the integration clause at `:897`; the spec path joined `Scope-Paths` and new E-10 performs a narrow, evidence-conditioned amendment. THIRD: `32ij2j`'s defect is ALREADY SHIPPED in the function this plan modifies, measured by driving the real `capture_command`, so `SuiteCheckResult.summary` is always empty in production and E-01 now fixes it. FOURTH: the sentinel precedent cited does not exist in code (it is unbuilt plan `m7gvuz`), and the nearest real agent-verdict reader FAILS OPEN in the same function, defaulting an unrecognized verdict to `verified`. FIFTH: the stated baseline was wrong in both its count and its named failure, and the named failure now passes because `32ij2j` was retired. Also corrected a dangling sibling id (`nzpixq` does not exist; Order 04 is `ys1dor`). No product code was modified by this review.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): REPLACES the rejected plan `32ij2j` (Set `integearn` Order 01, `- Status: reviewed`, `- Readiness: no-go`), whose diagnosis was sound and whose PRESCRIPTION was measured unimplementable on two independent counts. Authored after three maintainer rulings on 2026-09-08, each recorded below as a DECIDED question rather than left open. FIRST RULING, and it is a design change rather than a choice between the offered options: the maintainer rejected a hard programmatic gate outright as "very fragile" and directed that the runner instead ASK THE AGENT to adjudicate a failing suite, parsing for one of three sentinels (`SAFE TO IGNORE.`, `RETRY TESTS.`, `UNABLE TO FIX.`) and re-prompting when none is present. That inverts the design: the comparison stops being the authority and becomes the INPUT to a question. It also dissolves `32ij2j`'s fatal inversion, because an empty failing list no longer silently means "nothing broke"; a non-clean suite always escalates. SECOND RULING: run the suite AFTER combining the work, filling the revalidation stub. THIRD RULING: report a stranded run as NOT DONE in red from the run's OWN record (that half is sibling Order 04, `nzpixq`). WHY `32ij2j` COULD NOT BE SALVAGED IN PLACE: its E-01 parses `FAILED <nodeid>` out of `tool_event['stdout_excerpt']`, and I re-verified that `run_evidence.build_tool_event` (`:277`) NEVER WRITES that key, storing only `stdout_sha256` (`:299`, `:318`), `stderr_sha256`, lengths and a truncation flag, with `max_output_bytes` (`:446`) truncating BEFORE hashing so no text survives at all. Its E-04 derived the outcome from a filesystem audit, which re-renders a recovered run as COMPLETED and so rewrites history. Both are structural, so this is a new plan carrying `32ij2j`'s evidence forward rather than a revision of it. THE REVALIDATION STUB IS REAL AND STILL A STUB: `execute_merge_and_revalidate_gate` (`orchestrate_isolation.py:982`) calls `full_validation_runner` at `:1160`, and both hosts' builders return a closure whose entire body is `return True` (`oc_runipd.py:1999-2002`, `agy_runipd.py:1242`), with a docstring conceding "per-lane green never implies integrated green".
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop losing validated work to unrelated red tests, without pretending a program can safely judge which failures matter. The runner should gather the facts, notice that the suite is not clean, and put the judgement to the agent that just did the work, in a form it must answer in one of three machine-readable ways.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the failing test names available at all

- [ ] E-01 Capture the failing test IDENTIFIERS while the output is still in memory, and persist ONLY those. Per the maintainer's ruling, save the names and not the raw text. `capture_command` (`run_evidence.py:435`) currently hands bytes to `build_tool_event` (`:277`), which hashes them (`:299`) and keeps only digests and lengths (`:318`), and `max_output_bytes` (`:446`) truncates BEFORE hashing so the text is gone. Extract the failing node ids at capture time and add them as a typed list field on the evidence record. WHY NAMES ARE SAFE WHERE OUTPUT IS NOT: a pytest node id is repository-relative (`tests/test_x.py::Class::test_y`) and contains no home directory, username or absolute path, so it does not engage the D92 local-leaks rule that forbids machine-identifying strings in durable artifacts. Run `aw sanitize --agent` over a record containing real captured ids to prove that rather than assert it.
  YOU ARE FIXING A LIVE SHIPPED BUG AT THE SAME SEAM, AND THE PLAN DID NOT KNOW IT (F-10). `run_suite_check` ALREADY reads the key `32ij2j` was faulted for inventing: `oc_runipd.py:3671-3672` does `stdout = str(tool_event.get("stdout_excerpt") or "")` and the same for `stderr_excerpt`, then parses the pytest summary out of those strings at `:3691`. Since `build_tool_event` never writes either key, both are ALWAYS the empty string, so `SuiteCheckResult.summary` is ALWAYS `""` in production. MEASURED at review by driving the real `capture_command` on a command that prints a pytest-shaped summary line: the returned event's keys are exactly `['actor','argv','cwd','end_time','env','exit_code','kind','parent','run_id','schema_version','seq','start_time','stderr_len','stderr_sha256','stdout_len','stdout_sha256','timestamp','truncated']`, `'stdout_excerpt' in event` is `False`, and the string the summary regex would search is `''`. So `32ij2j`'s defect was not merely proposed, it is ALREADY IN THE SHIPPED CODE at the function this plan modifies. Fix it here (the same capture change that yields the ids can yield the summary), and say in the code comment that the reason `reason` strings have been reading `no summary line parsed` is this, not a regex problem. Do NOT reintroduce raw output to fix it: derive both the ids and the summary at capture time and persist only those.
  - Depends on: none
  - Expected outcome: a suite run's evidence record carries the failing test ids as a list; raw output is still not persisted; the sanitizer reports clean on a record built from a real failing run; `SuiteCheckResult.summary` is non-empty on a real run, which it has never been.
  - Execution state: pending

- [ ] E-02 Do NOT let a missing or empty list read as success, which is the exact inversion that sank `32ij2j`. Its E-03 compared failing sets as a SUBSET, and because the source string was always empty the parsed set was always empty, and the empty set is a subset of everything, so every lane would have earned integration including one that broke the whole suite. Under this plan the authority is the EXIT CODE, never the list: a non-zero suite exit escalates (E-04) whatever the list contains, and the list is only ever used to make the question specific. Encode that ordering explicitly so a later refactor cannot reintroduce the inversion, and pin it with a test that supplies a non-zero exit and an EMPTY list and asserts escalation rather than integration.
  - Depends on: E-01
  - Expected outcome: exit code decides whether to escalate; an empty failing list with a red exit still escalates; a test pins it.
  - Execution state: pending

### Task group 2: run the suite where the merged code actually is

- [ ] E-03 Fill the revalidation stub so the suite runs against the COMBINED result, per the maintainer's second ruling. `execute_merge_and_revalidate_gate` (`orchestrate_isolation.py:982`) already exists for exactly this and already states the principle in its own docstring ("per-lane green never implies integrated green"), and it calls `full_validation_runner` at `:1160`. Both hosts currently supply a closure whose whole body is `return True` (`oc_runipd.py:1999-2002`, `agy_runipd.py:1242`), so the gate has never checked anything. Supply a real runner that executes the bare suite against the merged tree and returns its result plus the failing ids from E-01. THIS ALSO FIXES THE MEASUREMENT MISMATCH: `run_suite_check` runs in the PRIMARY checkout by deliberate design (`dh0uno`, because a lane resolves a different `.aw/state` where about 15 run-viewer tests fail for unrelated reasons), while `isolate_worktree` defaults TRUE so the work lives only on the lane branch. Testing post-merge is the one place the code under judgement is actually present.
  - Depends on: E-02
  - Expected outcome: the gate runs a real suite against the merged tree on both hosts; the `return True` stub is gone; the docstring's stated principle is now enforced rather than asserted.
  - Execution state: pending

- [ ] E-04 State the COST honestly in the code and measure it. Post-merge revalidation means one extra full suite run per distinct base, which roughly doubles the gate's wall time; the bare suite is presently about 55 seconds here, so budget accordingly. Record the measured before and after wall time in a comment so a future reader can judge whether the tradeoff still holds, and make sure a multi-lane run does not re-run the suite once per lane when the base is unchanged (the gate is per combined base, not per lane).
  - Depends on: E-03
  - Expected outcome: measured wall-time cost recorded; the suite runs once per distinct base rather than once per lane.
  - Execution state: pending

### Task group 3: the escalation, which is this plan's substance

- [ ] E-05 When the suite is not clean, ASK THE AGENT rather than refusing, in the maintainer's own shape. The prompt must state what was expected, show what was observed (the failing ids from E-01, and enough output to judge), and demand exactly one of three sentinels: `SAFE TO IGNORE.` followed by a brief explanation to record; `RETRY TESTS.` followed by what was changed; or `UNABLE TO FIX.` followed by an explanation. Keep the sentinels EXACT and terminal-punctuated as the maintainer wrote them, since they are a parsing contract, and match them anchored rather than by loose substring so a sentinel merely DISCUSSED in prose cannot be mistaken for a verdict.
  - Depends on: E-02
  - Expected outcome: a non-clean suite produces the adjudication prompt carrying expectation, observation and the three required verdicts; the prompt is recorded in the run's prompts directory like every other.
  - Execution state: pending

- [ ] E-06 Act on each verdict, and bound the loop. `SAFE TO IGNORE.` records the explanation into the run record and proceeds to integration. `RETRY TESTS.` re-runs the suite and re-adjudicates. `UNABLE TO FIX.` refuses integration and preserves the lane exactly as today, which is the correct outcome for a genuinely broken change. If NO sentinel is parsed, re-prompt as the maintainer directed. BOUND BOTH LOOPS EXPLICITLY, because neither can be unbounded: a retry loop that never converges burns paid model turns indefinitely, and a re-prompt loop against a model that will not emit the sentinel does the same. Choose a small cap for each, state the number and why in a comment, and treat exhaustion as `UNABLE TO FIX.` so the failure mode is the SAFE one (lane preserved, nothing integrated).
  - Depends on: E-05
  - Expected outcome: all three verdicts behave as specified; a missing sentinel re-prompts; both loops are capped and exhaustion refuses rather than integrates.
  - Execution state: pending

- [ ] E-07 Record the adjudication DURABLY, so a `SAFE TO IGNORE.` is auditable rather than invisible. Write the verdict, the agent's explanation, the failing ids it was shown, and how many retries occurred into the run's own state, next to the existing `integration_signal` / `integration_detail` fields both drivers already write. This matters because `SAFE TO IGNORE.` is the path that lets work land over a red suite: it must be possible to ask later WHO decided that and on what basis. Note the reporting half is the sibling's: this item only ensures the fact is recorded where a reader can find it.
  - Depends on: E-06
  - Expected outcome: every adjudication is recorded in run state with verdict, explanation, shown ids and retry count.
  - Execution state: pending

### Task group 4: amend the contract this design changes

- [ ] E-10 Amend spec `25kzda` to carry the narrow, named exception this design requires, and do it BEFORE the escalation is wired. This item exists because the reconciliation was left as an open judgement for the executor while the answer is determinate: the spec DOES forbid an agent opinion from permitting integration, in three places (`:64`, `:825-830`, and decisively `:897`, quoted in `Spec / documentation sync`). Read that section first; it states exactly what the amendment must say and what it must not touch.
  WRITE THE EXCEPTION NARROWLY OR IT IS A HOLE RATHER THAN AN AMENDMENT. It must be conditioned on the adjudication being CAPTURED EVIDENCE (the verdict, the explanation, and the failing ids the agent was shown, all recorded per E-07), not free prose; it must name the failing-id list as part of what makes it reviewable; and it must state that `ipd_lifecycle.finalize_precheck` still applies unchanged afterwards, so the amendment adds an attributed exception rather than removing a gate. Do NOT weaken the general sentence at `:64` and do NOT edit section 4.2's finding-code table (byte-equality test).
  ORDER MATTERS FOR AN HONEST REASON, not a mechanical one. There is no contract test binding this spec text to code (unlike the flag-surface case elsewhere in this repository), so nothing will go red if you wire the escalation first. Amend first anyway: doing it afterwards means that between two of your own commits the runner is shipping behavior its governing spec forbids, and a reviewer reading the diff in order cannot tell whether the amendment was reasoned or retrofitted.
  IF OQ-02 IS UNANSWERED, STOP HERE AND SAY SO rather than writing the weaker exception. The amendment's text DEPENDS on OQ-02: with option (a) it describes an agent adjudicating pre-existing noise only, which is defensible; without it, it must honestly describe an agent that may clear its own breakage, which is a materially larger exception to ask an approved spec to admit. Writing the wrong one and amending again later leaves two contradictory amendment records on the same contract.
  - Depends on: none
  - Expected outcome: spec `25kzda` carries the narrow exception, conditioned on captured evidence and the unchanged finalize gate, with its stated reason; section 4.2 is byte-identical; the spec's workflow history records the amendment through the tooled path; the exception's wording matches OQ-02's answer.
  - Execution state: pending

### Task group 5: prove it

- [ ] E-08 Test WITHOUT STUBBING the capture, which is the specific hole that let `32ij2j`'s defect through review. The existing tests fabricate the evidence key (`tests/test_novalnomerge_integration.py:262`, `:288`, `:312` stub `capture_command`), so they could not have noticed the field was never written. Drive a REAL command that genuinely fails and assert the ids were captured from its real output. Cover: a genuinely red suite yielding a NON-EMPTY id list; each of the three sentinels driving its correct action; a missing sentinel re-prompting then exhausting to a refusal; the E-02 inversion guard (red exit plus empty list still escalates); and a clean suite still integrating with NO prompt issued, so the escalation cannot become an unconditional tax.
  - Depends on: E-07
  - Expected outcome: all six cases pass against real captured output rather than fabricated fields.
  - Execution state: pending

- [ ] E-09 Prove BOTH hosts share every symbol added, by OBJECT IDENTITY rather than by grep, per the anti-re-fork discipline this repository already enforces (`tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests`). The adjudication logic, the sentinel parser and the real validation runner must live in `runner_shared.py` and be reached by both drivers, because a second copy of a sentinel parser is exactly how the two hosts drift on what counts as a verdict. Confirm `agy_runipd` gained no new direct import from `oc_runipd`.
  - Depends on: E-08
  - Expected outcome: an identity assertion showing both hosts resolve to the same objects; no new cross-driver import.
  - Execution state: pending

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
| F-11 | **THE SPEC DOES FORBID THIS DESIGN, so the amendment is determinate rather than a judgement to defer to the executor.** Three places: `25kzda:64` ("The agent's prose and exit status are never completion authority"); `:825-830` section 5.1's not-completion-evidence list, which includes "a verifier's opinion" and "an agent-authored summary or checklist without captured evidence"; and decisively `:897`, "Executor commits remain on the item's isolated branch until scope, commit-content, hook, dependency, and deterministic completion checks pass. Only then may the coordinator integrate the verified commit set." A `SAFE TO IGNORE.` reply permits integration WITHOUT the deterministic check having passed. New E-10 performs the narrow amendment; the spec path joined `Scope-Paths` at review. | `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md:64`, `:825-830`, `:897` |
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
THEREFORE: `.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md` IS declared in `- Scope-Paths:` (added at review), so the runner announces the edit before the run starts and the finalize scope gate reconciles it afterwards. The amendment is a NARROW, NAMED EXCEPTION, not a weakening of the boundary: state that a non-clean suite may be cleared for integration ONLY by an explicitly recorded agent adjudication that names the failing test ids it was shown, that the adjudication is itself captured evidence (E-07) rather than free prose, and that the deterministic finalize gate (`ipd_lifecycle.finalize_precheck`) still applies unchanged afterwards. Say WHY in the amendment, since a spec edit changes the contract every other plan is reviewed against: the alternative was measured and is worse, eleven lanes of validated work stranded by one unrelated red test and one plan paid for twice.
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

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-401
- Resolution or deferral rationale: RECLASSIFIED AS BLOCKING AT REVIEW, and the plan's own proposed remedy was measured UNBUILDABLE AS DESCRIBED, which is why this can no longer be a note for later.
  WHAT IS AT STAKE. As specified, the subject of the judgement is the agent that just did the work, the question is whether its own change may land, and the answer `SAFE TO IGNORE.` is accepted as sufficient with no independent check. So an agent whose change breaks a test can clear its own breakage and the runner integrates to main. That is not a hypothetical framing: the whole reason this plan exists is that the suite is the ONLY correctness signal in the `--validate: false` default path (`integration_is_earned`'s suite branch), so removing its veto without a substitute leaves nothing between a broken change and main. Spec `25kzda:830` independently lists "a verifier's opinion" among the things that are NOT completion evidence, which is the same objection stated as contract (F-11).
  THE PLAN'S PROPOSED FIX CANNOT BE BUILT FROM WHAT THIS PLAN PROVIDES. It says "E-01 gives the failing ids on both sides", but there IS no other side: MEASURED at review, `run_suite_check` is called exactly ONCE per attempt, AFTER the work, at `oc_runipd.py:6656` and `agy_runipd.py:3720`, inside `if integration_gate_relevant and not validate`. No baseline suite result exists anywhere in run state, so "which failures are NEW" is not computable. Delivering that constraint requires a SECOND suite run (a pre-work baseline, or a post-merge-versus-pre-merge pair), which is a real cost decision on top of E-04's already-doubled gate time and is not in this plan's scope as written.
  THE THREE HONEST OPTIONS, each with its cost. (a) ADD THE BASELINE: capture a suite result before the work (or reuse the merge base's), diff the id sets, and refuse `SAFE TO IGNORE.` for any id absent from the baseline, requiring `RETRY TESTS.` or `UNABLE TO FIX.`. This delivers exactly the maintainer's design (the agent adjudicates PRE-EXISTING noise, which is the measured problem) while removing the self-clearing case; cost is another full suite run per base, so roughly triple the original gate time rather than double. (b) SHIP WITHOUT IT AND ACCEPT THE HOLE, relying on the durable record (E-07) plus human review after the fact; cost is that a self-cleared breakage reaches main and is discovered later, and the eleven-lane incident shows how long "later" can be. (c) NARROW THE VERDICT: keep `SAFE TO IGNORE.` but make it non-integrating (record it, still preserve the lane, and let a human release it), which removes the abuse entirely at the cost of not solving the stranding this plan exists to solve, so it is not recommended.
  WHY THIS BLOCKS rather than being resolvable by the executor: it is a security-relevant policy choice about how much authority an agent has over its own work, and option (a) changes the plan's cost profile materially. `plan-review` forbids inventing a decision that requires the human, and the maintainer already ruled once on this design, so the amendment is theirs to make. An executor who hits this mid-implementation would have to either invent the baseline (unscoped work) or ship the hole silently.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a real evidence record built from a genuinely failing suite run, showing the failing ids present as a list and NO raw output field. Paste `aw sanitize --agent` over that record showing `findings: 0`. Paste the diff of `build_tool_event` showing where the ids are added and that hashing/truncation behavior is otherwise unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test that supplies a NON-ZERO exit with an EMPTY failing list and asserts ESCALATION, plus its passing result. Paste the code showing the exit code is consulted before the list is used. This is the anti-inversion guard and a passing suite alone does not satisfy it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `git diff` of both hosts' validation-runner builders showing `return True` replaced by a real run, and paste a gate execution log showing the suite actually ran against the MERGED tree (name the tree path and show the work present in it).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste measured gate wall time before and after, and paste evidence from a multi-lane run that the suite ran ONCE per distinct base rather than once per lane (a count, not an assertion).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the actual adjudication prompt text as issued, showing the expectation, the observed failing ids, and all three required sentinels verbatim. Paste the prompt as recorded in the run's prompts directory.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: four separate demonstrations with their outcomes: `SAFE TO IGNORE.` integrates and records the explanation; `RETRY TESTS.` re-runs and re-adjudicates; `UNABLE TO FIX.` preserves the lane; and a reply with NO sentinel re-prompts and then exhausts to a refusal. Paste the configured caps and show exhaustion refusing rather than integrating.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the run-state fragment after a `SAFE TO IGNORE.` adjudication showing the verdict, the explanation, the shown ids and the retry count, sitting alongside the existing `integration_signal` field.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste all six cases with results, and paste proof the capture was NOT stubbed (show the real command run and its real output feeding the ids). Paste the ids captured from that real run.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste an object-identity assertion (`oc.<symbol> is agy.<symbol>`) returning True for the adjudicator, the sentinel parser and the validation runner; paste a grep showing `agy_runipd` gained no new import from `oc_runipd`; paste the bare `python3 -m pytest` summary line compared to the stated baseline.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste the spec diff. Quote the added exception in full and show, sentence by sentence, that it is conditioned on CAPTURED EVIDENCE (verdict, explanation, shown failing ids) rather than prose, and that it states `ipd_lifecycle.finalize_precheck` still applies unchanged. Paste `git diff --stat` for the spec proving only the intended section changed, and confirm section 4.2's finding-code table is BYTE-IDENTICAL (show the diff is empty for that region, and paste the byte-equality test passing). Paste the spec's appended workflow-history line and confirm `- Status:` was NOT hand-edited. STATE WHICH OQ-02 OPTION THE WORDING ASSUMES and quote the clause that reflects it; if OQ-02 was answered option (a), the exception must say the agent adjudicates pre-existing failures only. Paste the three spec lines this design contradicts (`:64`, `:825-830`, `:897` as they stood before) so a reader can see exactly what was amended and why.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. IT IS NOT APPROVABLE YET: OQ-02 is `Blocking: yes` and `Status: open`, so `aw set approved` refuses (`plan_readiness.has_unresolved_blocking_question`), which is the correct fail-closed behavior. That is the ONE thing standing between this plan and execution; everything else review found was repaired in place.

WHY OQ-02 BLOCKS, in one paragraph, because it is the decision the maintainer must make. This design lets the agent that just did the work decide whether its own change may land over a red suite, and as written it accepts `SAFE TO IGNORE.` with no independent check, so an agent can clear a test IT broke. The plan offered a cheap-sounding constraint (refuse the verdict for NEWLY failing tests) and review measured that constraint UNBUILDABLE as described (F-14): the suite runs exactly once, after the work, so no baseline exists and "new" is not computable without a second full suite run. So the real choice is (a) add the baseline and pay another suite run, (b) ship the self-clearing hole and rely on the audit record, or (c) make `SAFE TO IGNORE.` non-integrating. OQ-02 states each with its cost.

A reviewer or maintainer should also know four things review established. FIRST, this plan supersedes `32ij2j` rather than revising it, and review found the superseded plan's defect is ALREADY SHIPPED in the function this plan modifies: `run_suite_check` reads `stdout_excerpt`, which is never written, so `SuiteCheckResult.summary` is always empty in production (F-10). E-01 now fixes that too. SECOND, the spec reconciliation the plan deferred to the executor was done at review and the answer is determinate: spec `25kzda` forbids this design in three places including the integration clause at `:897`, so the amendment is required, its path joined `Scope-Paths`, and new E-10 performs it (F-11). THIRD, the sentinel precedent the plan cited does not exist in shipped code (it is unbuilt plan `m7gvuz`), and the nearest real agent-verdict reader FAILS OPEN in the same function this plan edits, so an executor copying nearby code would reproduce exactly the hazard E-06 forbids (F-12, F-13). FOURTH, its central design remains a MAINTAINER RULING of 2026-09-08, not the author's preference, and nothing in this review disturbs that ruling; the blocking question is about one guardrail on it, not about the approach.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD, which is unusual here and serious: this plan changes the gate that decides whether ITS OWN work is integrated. Verify by behavior in a scratch repository, and if the change strands its own lane, recover it by hand rather than trusting the mechanism under test. Re-locate every citation BY SYMBOL: `oc_runipd.py` and `agy_runipd.py` are the most heavily edited files in the repository. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`.
