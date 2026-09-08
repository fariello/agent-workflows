# IPD: Ask the agent to adjudicate a failing suite instead of refusing every lane on any red test

- Date: 2026-09-08
- Kind: child
- Concern: ONE pre-existing red test anywhere in the repository silently refuses lane integration for EVERY plan. With `--validate` defaulting FALSE, `integration_is_earned` falls back to the driver-run suite as its trust signal, and that signal is BINARY over the whole repository: `SuiteCheckResult.passing` is True only on an observed exit 0 (`oc_runipd.py:3610-3624`, verdict at `:3786-3796`). MEASURED HARM 2026-09-08: a single unrelated failure (`tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, caused by a REPLAN verdict on the live plan `32ij2j`) stranded ELEVEN lanes holding fully validated work, and because nothing reported it, plan `03ie04` was executed TWICE for the same fix at `$16.59` then `$32.83`. The lanes were recovered only by a hand audit of `git worktree list`.
- Scope: Replace the binary refusal with a bounded ESCALATION TO THE AGENT, per the maintainer's ruling of 2026-09-08: record the failing test NAMES, and when the suite is not clean, ask the agent that just did the work to adjudicate with three parsable verdicts (safe to ignore / retry / cannot fix) rather than deciding by a fragile programmatic rule. Also fill the revalidation stub so the suite runs where the merged code actually is. Adds NO new refusal that a human cannot see, and changes no verifier semantics.
- Scope-Paths: agent_workflows/run_evidence.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/orchestrate_isolation.py, tests/test_suite_adjudication.py, tests/test_novalnomerge_integration.py
- Item-Dependencies: none
- Status: to-review
- Set: integearn
- Order: 3
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: daexj1
- From-Backlog: ciesaj
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): REPLACES the rejected plan `32ij2j` (Set `integearn` Order 01, `- Status: reviewed`, `- Readiness: no-go`), whose diagnosis was sound and whose PRESCRIPTION was measured unimplementable on two independent counts. Authored after three maintainer rulings on 2026-09-08, each recorded below as a DECIDED question rather than left open. FIRST RULING, and it is a design change rather than a choice between the offered options: the maintainer rejected a hard programmatic gate outright as "very fragile" and directed that the runner instead ASK THE AGENT to adjudicate a failing suite, parsing for one of three sentinels (`SAFE TO IGNORE.`, `RETRY TESTS.`, `UNABLE TO FIX.`) and re-prompting when none is present. That inverts the design: the comparison stops being the authority and becomes the INPUT to a question. It also dissolves `32ij2j`'s fatal inversion, because an empty failing list no longer silently means "nothing broke"; a non-clean suite always escalates. SECOND RULING: run the suite AFTER combining the work, filling the revalidation stub. THIRD RULING: report a stranded run as NOT DONE in red from the run's OWN record (that half is sibling Order 04, `nzpixq`). WHY `32ij2j` COULD NOT BE SALVAGED IN PLACE: its E-01 parses `FAILED <nodeid>` out of `tool_event['stdout_excerpt']`, and I re-verified that `run_evidence.build_tool_event` (`:277`) NEVER WRITES that key, storing only `stdout_sha256` (`:299`, `:318`), `stderr_sha256`, lengths and a truncation flag, with `max_output_bytes` (`:446`) truncating BEFORE hashing so no text survives at all. Its E-04 derived the outcome from a filesystem audit, which re-renders a recovered run as COMPLETED and so rewrites history. Both are structural, so this is a new plan carrying `32ij2j`'s evidence forward rather than a revision of it. THE REVALIDATION STUB IS REAL AND STILL A STUB: `execute_merge_and_revalidate_gate` (`orchestrate_isolation.py:982`) calls `full_validation_runner` at `:1160`, and both hosts' builders return a closure whose entire body is `return True` (`oc_runipd.py:1999-2002`, `agy_runipd.py:1242`), with a docstring conceding "per-lane green never implies integrated green".
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop losing validated work to unrelated red tests, without pretending a program can safely judge which failures matter. The runner should gather the facts, notice that the suite is not clean, and put the judgement to the agent that just did the work, in a form it must answer in one of three machine-readable ways.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: make the failing test names available at all

- [ ] E-01 Capture the failing test IDENTIFIERS while the output is still in memory, and persist ONLY those. Per the maintainer's ruling, save the names and not the raw text. `capture_command` (`run_evidence.py:435`) currently hands bytes to `build_tool_event` (`:277`), which hashes them (`:299`) and keeps only digests and lengths (`:318`), and `max_output_bytes` (`:446`) truncates BEFORE hashing so the text is gone. Extract the failing node ids at capture time and add them as a typed list field on the evidence record. WHY NAMES ARE SAFE WHERE OUTPUT IS NOT: a pytest node id is repository-relative (`tests/test_x.py::Class::test_y`) and contains no home directory, username or absolute path, so it does not engage the D92 local-leaks rule that forbids machine-identifying strings in durable artifacts. Run `aw sanitize --agent` over a record containing real captured ids to prove that rather than assert it.
  - Depends on: none
  - Expected outcome: a suite run's evidence record carries the failing test ids as a list; raw output is still not persisted; the sanitizer reports clean on a record built from a real failing run.
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

### Task group 4: prove it

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
- Sentinel-parsing precedent exists in this codebase (the orchestrator probe accepts only two exact sentinels and fails closed on anything else); follow that strictness rather than a loose substring match.

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
| F-9 | The failing test that caused all of this is itself unrelated to any lane: it fails because of a REPLAN verdict recorded on the live plan `32ij2j`. | `tests/test_plan_readiness.py:798`; reproduced on `main` before and after the recovery |

## Proposed changes (ordered, validatable)

1. Capture and persist failing test ids only, and prove the sanitizer stays clean (E-01).
2. Make the exit code the authority so an empty list can never mean success (E-02).
3. Fill the revalidation stub so the suite runs on the merged result (E-03).
4. Measure and record the added wall-time cost; one run per base (E-04).
5. Ask the agent to adjudicate with three exact sentinels (E-05).
6. Act on each verdict; cap both loops; exhaustion refuses (E-06).
7. Record every adjudication durably in run state (E-07).
8. Test against real captured output, never a stubbed field (E-08).
9. Prove both hosts share the new symbols by identity (E-09).

## Deferred / out of scope (with reason)

- THE END-OF-RUN AND CROSS-TREE REPORTING. A stranded run must stop printing a green COMPLETED, and `aw attention` must surface a stranded lane; those are sibling Order 04 (`nzpixq`) and backlog `nuanaw` respectively. This plan fixes the CAUSE; being told about it is separately owned.
- `32ij2j` ITSELF. It is superseded rather than revised, because both of its mechanisms are structurally unavailable (F-4, and its filesystem-derived outcome). It should be retired as superseded by this plan; that is a records act for the maintainer, and this plan does not perform it.
- CHANGING THE VERIFIER PATH. When `--validate` is ON, the verifier verdict governs and a green suite deliberately does not override it. Untouched.
- PERSISTING RAW SUITE OUTPUT. Ruled against: names only. A sanitized-excerpt design was offered and not chosen.
- IN-LANE MEASUREMENT. Offered and not chosen; it reintroduces the `dh0uno` noise and still proves only per-lane green.
- AUTO-FIXING THE CURRENT RED TEST. `tests/test_plan_readiness.py`'s failure belongs to whoever owns plan `32ij2j`'s REPLAN verdict. This plan makes such a failure survivable rather than fixing this instance.

## Scope check

- Over-scope: `orchestrate_isolation.py` is included because E-03 must replace the stub the gate calls; without it the ruled post-merge measurement has nowhere to run.
- Under-scope: reporting is left to the sibling and to `nuanaw`. No verifier semantics change. The currently-red test is not fixed here.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline at authoring is 1 failed, 5858 passed (the known `test_plan_readiness` failure); judge on the DELTA.
- `python3 -m pytest tests/test_suite_adjudication.py tests/test_novalnomerge_integration.py` for the focused surface.
- A REAL end-to-end: a lane whose work is fine, against a tree carrying one unrelated red test, must reach the adjudication prompt and integrate on `SAFE TO IGNORE.` — this is the exact scenario that stranded eleven lanes.
- The inverse: a lane that genuinely breaks tests must reach `UNABLE TO FIX.` and be preserved, proving the fix did not simply disable the gate.
- `aw sanitize --agent` over a record containing real captured ids.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

Spec `25kzda` (`aw run deterministic run and verify`, `- Status: approved`) governs the run-and-verify pipeline, and its principle that agent prose and exit status are never completion authority is directly engaged here: this plan lets an AGENT'S ADJUDICATION permit integration over a red suite, which is a deliberate, attributed exception rather than a hole. THE EXECUTOR MUST READ THAT SECTION AND RECONCILE. If the spec forbids an agent verdict from clearing a red suite, this design is a spec AMENDMENT: declare the spec path in `Scope-Paths` and justify it BEFORE editing, per the plan-may-amend-a-spec rule, and note the justification is available (the alternative is provably losing validated work at scale, measured at eleven lanes and one duplicated payment). `AGENTS.md` needs no change; the runner behavior it describes is unaffected.

## Open questions

### OQ-01: How many retries, and how many re-prompts, before exhaustion?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE BY THE EXECUTOR, recorded so the numbers are deliberate rather than accidental. Both loops must be bounded (E-06) and exhaustion must be treated as `UNABLE TO FIX.`, so the failure mode is the safe one. RECOMMENDATION: small, since each iteration costs a paid model turn and the existing correction budget defaults to 2 for exactly that reason; one or two retries and two re-prompts is a reasonable start. State the chosen numbers and the reasoning in a comment so a later reader can tune them against observed behavior rather than guessing.

### OQ-02: Should `SAFE TO IGNORE.` be constrained to failures the agent did not cause?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, and worth the maintainer's attention because it is the one place this design can be abused. As specified, an agent may declare its OWN newly-broken test safe to ignore, and the runner would integrate. A cheap constraint is available: E-01 gives the failing ids on both sides, so the runner can tell the agent WHICH failures are new and refuse `SAFE TO IGNORE.` for those, requiring `RETRY TESTS.` or `UNABLE TO FIX.` instead. That preserves the maintainer's design (the agent still adjudicates pre-existing noise, which is the actual problem) while removing the self-clearing case. RECOMMENDATION: adopt it, but it is a policy call, and the plan works without it.

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

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

A reviewer should know three things. FIRST, this plan SUPERSEDES `32ij2j` rather than revising it, because both of that plan's mechanisms were measured structurally unavailable (F-4 and its filesystem-derived outcome). SECOND, its central design is a MAINTAINER RULING of 2026-09-08, not the author's preference: a hard programmatic gate was rejected as too fragile, and the runner is to ask the agent to adjudicate with three exact sentinels. THIRD, OQ-02 names the one abuse this design admits (an agent clearing its own breakage) and offers a cheap constraint; a reviewer who wants that constraint should say so, since the plan ships without it.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE REFLEXIVE HAZARD, which is unusual here and serious: this plan changes the gate that decides whether ITS OWN work is integrated. Verify by behavior in a scratch repository, and if the change strands its own lane, recover it by hand rather than trusting the mechanism under test. Re-locate every citation BY SYMBOL: `oc_runipd.py` and `agy_runipd.py` are the most heavily edited files in the repository. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`.
