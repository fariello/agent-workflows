# IPD: Probe every queued orchestrator for uncovered work before the run starts in earnest

- Date: 2026-09-07
- Kind: child
- Concern: The runner retires an orchestrator once every child is `executed`, omitting the pre-transition E/V checkpoint on the premise that its items are "performed by NOBODY" (`ipd_lifecycle.py:1825`, `ROLLUP_OMITTED_GATES`). When a parent carries work no child covers, that premise is false and the work is reported complete having never been performed OR verified. Nothing detects this. It cannot be a pattern match: the dangerous case is PROSE ("someone must migrate the database before the children run"), which matches no checklist syntax, so a syntactic rule catches only the tidy mistake and misses the harmful one. It is a semantic question, so it needs a model to answer it. A blunt syntactic rule was built and REVERTED 2026-09-07 for a second reason too: most orchestrator checklist items are legitimate orchestration, and a rule that flags them teaches agents to DELETE the checklist that makes non-runner execution complete.
- Scope: A bounded pre-run gate. IN: a short prompt per queued orchestrator returning ONE parsable line, over an explicitly bounded excerpt rather than the whole file; consuming child 02's cache so an unmodified orchestrator is never re-probed; an interactive prompt when a TTY is present, a hard failure when not, and an override flag that is recorded when used; emitting child 01's refusal record so the reason and its remedy reach both surfaces. OUT: the retirement predicate and the rollup transition (`77tr3o` owns both); any `ipd_lint` rule (rejected; see Deferred); backfilling the 46 existing orchestrators.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/engine.py, .aw/records/specs/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md, tests/test_orchestrator_probe.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: executed:r2i1b1, executed:8tgg6g
- Status: to-review
- Readiness: no-go
- Set: orchprobe
- Order: 3
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: m7gvuz

## Workflow history
- 2026-09-08 to-review (aw set): status set to to-review
- 2026-09-07 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review REVIEWED - OPEN QUESTIONS; PR-001..PR-010, eight FIXED and two OPEN. THE BLOCKER IS THAT E-04's SITING MAKES THE PROBE UNIMPLEMENTABLE AS WRITTEN. It says to gate BEFORE any run directory exists, but the only two model-invocation helpers both REQUIRE a `run_dir` and a queue `item`: `run_opencode(state, run_dir, item, plan_path, prompt_path, attempt_no, ...)` and `run_agy_turn(state, run_dir, item, prompt_path, attempt_no, ...)`, and each writes its transcript to `run_dir/sessions/<position:02d>-<id6>-attempt-N.jsonl` (`oc_runipd.py:4897-4905`), keyed on `item['position']`, which exists only once the queue is frozen. So a pre-directory probe has no way to call a model and no place to log the call, and the parent's criterion 3 additionally requires the refusal be readable in `aw runs`, which reads durable state. Resolved as D-1: site the probe AFTER the run directory exists but BEFORE any agent turn, lane worktree or session, which satisfies "costs nothing" in the sense that matters. SECOND, THE COST CLAIM WAS NEVER SIZED AND THE PLAN NEVER SAYS WHAT IS SENT: measured, the pending orchestrators are 30k to 66k characters (roughly 7.5k to 16.4k tokens each, ~58k tokens for all six), so "a short prompt" describes the instruction and not the payload; new E-03 requires an explicitly bounded excerpt (E-item action text plus the child table, the same inputs child 02's digest keys on) so the cache key and the probe input cannot diverge. THIRD, E-06 WOULD HAVE TRIPPED AN EXISTING TEST: `tests/test_orchestrator_retirement.py::test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module` requires every claim in the exact `###` section E-06 edits to map to a named test class in that module, and the plan neither declared that file nor knew the constraint. ALSO FIXED: the missing spec declaration the parent's CID-6 demands (now `77tr3o` in `Scope-Paths`, with R-5 named as the requirement whose premise this gate guards), the 46-of-130 denominator (really 46 of 47 `Kind: orchestrator` plans), an override with no recorded justification, and OQ-01's claim that per-role profile machinery exists (`runner_profiles` has NO role concept; `kgpptv` is approved but unexecuted). OPEN: OQ-02 (`Blocking: yes`, PR-002) on whether a run may be gated on a model call at all, and OQ-03 (`Blocking: yes`, PR-005) inheriting the parent's OQ-02 about the four approved orchestrators this gate blocks on day one.

- 2026-09-07 to-review (aw set): Authored and ready for critique: lint conforming, E/V bijection, every V-item demands pasted evidence. Set records the REJECTED syntactic-linter shape and why (it cannot separate legitimate orchestration from parent-only work, and its false positives push agents to delete the orchestration checklist), plus the deferred positive-assertion shape and its backfill cost.

- 2026-09-07 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Before a run spends an agent turn, establish for every queued orchestrator whether it holds work no child covers, and refuse or prompt when it does, naming the constructive fix. Cheap by caching, honest by failing closed, and never so noisy that an operator learns to ignore it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the probe

- [ ] E-01 Write the prompt, and BIAS IT TOWARD SUSPICION. It must return exactly one line, either `ORCHESTRATOR: CONTAINS EXECUTIONS` or `ORCHESTRATOR: CONTAINS NO EXECUTIONS`, and nothing else. It must state that a checklist naming the children is EXPECTED and is not an execution, since that is the legitimate orchestration case and a prompt that misreads it would produce constant false alarms on the five live orchestrators. It must instruct that any doubt resolves to `CONTAINS EXECUTIONS`: a false alarm costs one prompt, while a false clear launders a bad state with apparent authority, which is worse than having no probe at all.
  - Depends on: none
  - Expected outcome: a prompt held as data (not inlined at a call site), with the two sentinel strings as named constants so the parser and the prompt cannot drift.
  - Execution state: pending

- [ ] E-02 Parse the reply STRICTLY and fail closed. Accept only the two exact sentinels; anything else (extra prose, a refusal, an empty reply, a truncated turn) is `unknown`, which blocks exactly as `CONTAINS EXECUTIONS` does. A permissive parser here would convert a confused model into a silent pass, which is the failure mode this whole child exists to prevent.
  - Depends on: E-01
  - Expected outcome: a tri-state result; pasted proof that a chatty or empty reply yields `unknown` and blocks.
  - Execution state: pending

- [ ] E-03 Define and bound the PROBE INPUT explicitly: send the orchestrator's E-item action text plus its `## Child IPDs` table, NOT the whole file.
  WHY, MEASURED: the pending orchestrators are 30,106 to 65,705 characters (roughly 7,500 to 16,400 tokens each; ~58,000 tokens for all six), so "a short prompt" describes the INSTRUCTION and says nothing about the PAYLOAD, and an unbounded probe would send a 16k-token file to answer a yes/no question. Use the SAME two inputs child 02's digest keys on (`8tgg6g` E-02), so the cache key and the probe input cannot diverge: if the probe reasons over something the digest does not cover, an edit to that thing would serve a stale verdict, which is the one way this cache can be actively wrong rather than merely useless.
  - Depends on: E-02
  - Expected outcome: a bounded excerpt builder whose output is the digest's inputs; the per-orchestrator payload size recorded for the live corpus so a reader can see the cost.
  - Execution state: pending

- [ ] E-04 Probe only the orchestrators IN THIS RUN'S QUEUE, and consult child 02's cache first. `aw oc run all` could otherwise sweep the whole corpus; scope keeps the cost proportional to the run. A cache hit spends nothing; a miss or a digest change probes.
  - Depends on: E-03
  - Expected outcome: with 5 queued orchestrators all cached, ZERO model calls; after editing one orchestrator's E-item text, exactly ONE call.
  - Execution state: pending

### Task group 2: the gate and its voice

- [ ] E-05 Gate the run: PROMPT interactively when stdin is a TTY, FAIL when it is not, and provide an override flag for a maintainer who accepts the risk deliberately.
  SITE IT AFTER THE RUN DIRECTORY EXISTS BUT BEFORE ANY AGENT TURN, LANE WORKTREE OR SESSION. The pre-revision instruction ("before any agent turn or lane worktree is created ... a refusal creates no run directory lease") is NOT IMPLEMENTABLE, measured: the only two model-invocation helpers both REQUIRE a `run_dir` and a queue `item` (`run_opencode(state, run_dir, item, plan_path, prompt_path, attempt_no, ...)`, `run_agy_turn(state, run_dir, item, prompt_path, attempt_no, ...)`), and each writes its transcript to `run_dir/sessions/<position:02d>-<id6>-attempt-N.jsonl` (`oc_runipd.attempt_log_path:4897-4905`) keyed on `item['position']`, which only exists once the queue is frozen. So a pre-directory probe cannot call a model and cannot log the call. The parent's completion criterion 3 independently requires the refusal be readable in `aw runs`, which reads durable run state, and today's pre-queue gates (`initialize_run` raises at `oc_runipd.py:2791`/`:2871`, before `run_dir.mkdir` at `:2880`) leave nothing for it to read. "Costs nothing" therefore means NO AGENT TURN, NO WORKTREE, NO SESSION, not "no run directory".
  RECORD THE OVERRIDE WITH A REASON, not merely a flag. Require the maintainer to supply a justification string that is written into run state beside the override, so a later reader can tell an accepted risk from an unnoticed one AND why it was accepted. A bare boolean records that someone clicked past the gate and nothing about whether they should have.
  - Depends on: E-04
  - Expected outcome: the three paths demonstrated; a refusal leaves no worktree, no session and no agent turn, and its record is readable in `aw runs` after the process exits; the override is recorded with its justification.
  - Execution state: pending

- [ ] E-06 Emit child 01's refusal record with a REMEDY that names the constructive action: the uncovered work belongs in a child, so ADD A CHILD for it. Do NOT phrase it as "an orchestrator must not contain executions": `AGENTS.md` records that a prohibition-only message gets complied with by DELETION, and deleting these items destroys the orchestration checklist that makes non-runner execution complete. The remedy wording is the deliverable here, not a nicety.
  - Depends on: E-05
  - Expected outcome: the reason and remedy visible in both the end-of-run summary and `aw runs`, with the remedy naming child creation.
  - Execution state: pending

- [ ] E-07 Amend spec `77tr3o` (`- Status: approved`) so this gate is a recorded requirement rather than undocumented code, and declare the file in `Scope-Paths` (done) so the pre-run spec-impact announcement names it.
  WHY THAT SPEC AND NOT ANOTHER: its R-5 resolution is what CREATED the omission this gate compensates for. R-5 required the E/V pre-transition requirement be "resolved explicitly, not bypassed" and the maintainer chose shape (b), a runner-owned rollup that skips the checkpoint, on the premise that an orchestrator's items are performed by nobody. This gate is the control that makes that premise CHECKED rather than assumed, so a spec still asserting the bare premise is a spec that no longer describes the system. State the gate, its fail-closed behavior, and the override in the amendment.
  - Depends on: E-06
  - Expected outcome: an amended `77tr3o` recording the gate as a requirement alongside R-5's resolution, and the pre-run spec-impact announcement naming that file.
  - Execution state: pending

- [ ] E-08 Update the AGENTS.md managed block via `engine.py` (never by hand, it is generated) to state that this gate exists, what it checks, and what to do when it fires.
  KNOW THE TEST YOU WILL TRIP. The natural home is the `### The runners own ordering, isolation, and orchestrators` section, and `tests/test_orchestrator_retirement.py::test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module` reads EXACTLY that section (it slices from that heading to the next `### `) and asserts every claim fragment in its `mapping` dict is present AND backed by a named test class in that module. So new prose there requires new mapping entries and real tests behind them; `tests/test_orchestrator_retirement.py` is declared in `Scope-Paths` for that reason. Also update the neighbouring "Do NOT raise" instruction (`AGENTS.md:44`) if this gate's refusal becomes a legitimate thing to raise, since that list currently enumerates what an agent may report and a refusal nobody may mention is a refusal nobody acts on.
  While there, correct the stale denominator that section carries: it says "46 of 130 orchestrators carry checklist items", but 130 is the filename-`-00-` population of which 84 are pre-`Kind` legacy plans with ZERO E-items; among plans actually carrying `- Kind: orchestrator` it is 46 of 47.
  - Depends on: E-07
  - Expected outcome: regenerated AGENTS.md carrying the gate, the corrected denominator, mapping entries plus tests for every new claim, and the idempotent-render test still passing.
  - Execution state: pending

- [ ] E-09 Confirm both hosts share every symbol added, by OBJECT IDENTITY not grep (`2r306y`/`818uru`), and that `agy_runipd` gained no new import from `oc_runipd` (measured 47 by AST walk 2026-09-07; backlog `cnwy8g` recorded 40, so it is growing). Both hosts must reach the probe through `runner_shared`, never through the other host's driver, and BOTH must actually gate: `pgq326`'s review found agy DECIDING an orchestrator action while having no dispatch branch that read it, so a shared decider proves nothing about whether agy acts.
  - Depends on: E-05, E-06
  - Expected outcome: pasted object-identity proof per new symbol, an unchanged oc-to-agy import count, and a demonstration that `aw agy run` refuses on the same fixture `aw oc run` refuses on.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A prohibition-only message causes deletion. This is recorded in the AGENTS.md managed block and is the reason E-06 exists as its own item.
- The parent's checklist of children is LOAD-BEARING: most Sets are run by a human telling an agent "execute `<setid>`" with no runner at all, and that checklist is what makes execution ordered and complete. The probe must not flag it.
- `ipd_lint` must stay Kind-unaware: spec `77tr3o` R-5 chose the runner-side shape and rejected the linter route, and `tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken` asserts zero occurrences of "orchestrator" in `ipd_lint.py`.
- Both hosts must share one definition of anything added (`2r306y`/`818uru`), asserted by object identity, and `agy_runipd` must not gain another import from `oc_runipd` (measured 47 today; `cnwy8g` recorded 40).
- A MODEL CALL NEEDS A RUN DIRECTORY. `run_opencode` and `run_agy_turn` each take `run_dir` and a queue `item`, and each logs to `run_dir/sessions/<position:02d>-<id6>-attempt-N.jsonl` keyed on `item['position']`. There is no host helper for a one-shot model question outside a frozen queue, which is what makes E-05's siting a real constraint rather than a preference.
- THE AGENTS.md SECTION E-08 EDITS IS TEST-GUARDED IN AN UNUSUAL WAY. `test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module` slices `### The runners own ordering, isolation, and orchestrators` to the next `### ` and requires every fragment in its `mapping` dict to be present in that text AND backed by a named test class in the same module. New prose there is not free: it needs a mapping entry and a real test.
- BASELINE, MEASURED AT REVIEW: `python3 -m pytest` bare at HEAD `4fdc691b` gives `1 failed, 5632 passed, 3 skipped, 2 xfailed`. The single failure is `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`, asserting `{"kgpptv": "reviewed"}` while `kgpptv` reads `- Status: approved`: a test coupled to this repository's mutable plan statuses. It is in a module THIS child edits, so do not read it as caused here, and do not dismiss other failures in that module as known. Re-measure in the executing worktree and compare failing NODE IDS.
- THE PROFILE MACHINERY IS PER-RUN, NOT PER-ROLE. `runner_profiles` contains no `role` concept at all, and `resolve_launch_profile` (`oc_runipd.py:2660`) resolves ONE launch identity for the whole run. The per-role work is `kgpptv`, which is `approved` and NOT executed. OQ-01 must not be read as "reuse the existing per-role resolution".

## Findings

| Id | Severity | Location (2026-09-07) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_lifecycle.py:1825`, `ROLLUP_OMITTED_GATES` | Retirement omits the E/V checkpoint on a premise nothing enforces. | source read |
| F-2 | HIGH | corpus | 46 of the 47 plans carrying `- Kind: orchestrator` carry checklist items (98 percent). The "46 of 130" framing is diluted: 130 is the filename-`-00-` population and 84 of those are pre-`Kind` legacy plans with ZERO E-items. On the five live ones the items split into legitimate orchestration and parent-only work, and only the latter is the hazard. Direction matters: the probe meets an item-carrying orchestrator nearly every time, so its FALSE-POSITIVE rate dominates the cost. | re-counted at HEAD `4fdc691b` by parsing `- Kind:` and `- [ ] E-` across `.aw/records/plans/**` |
| F-3 | HIGH | design | The dangerous case is prose, which no pattern match sees. Hence a model, not a regex. | maintainer observation, agreed |
| F-4 | HIGH | design | A false clear is worse than no probe, so the prompt must bias toward suspicion and the parser must fail closed. | design reasoning; E-01/E-02 own it |
| F-5 | MED | `aw oc run all` | An unscoped probe could sweep the whole corpus; E-04 bounds it to the queue. | source read |
| F-6 | BLOCKER | `oc_runipd.run_opencode:5262`, `attempt_log_path:4897-4905`; `agy_runipd.run_agy_turn:2765`; `oc_runipd.py:2791`, `:2871`, `:2880` | **E-04's SITING (pre-revision) MADE THE PROBE UNIMPLEMENTABLE.** It required gating before any run directory exists, but both model-invocation helpers REQUIRE `run_dir` and a queue `item`, and both log to `run_dir/sessions/<position:02d>-<id6>-attempt-N.jsonl` keyed on `item['position']`, which exists only after the queue is frozen. There is no one-shot helper. Independently, the parent's criterion 3 requires the refusal be readable in `aw runs`, which reads durable state that a pre-directory refusal never creates (the existing pre-queue gates raise at `:2791`/`:2871`, before `mkdir` at `:2880`). | signatures printed via `inspect.signature`; `attempt_log_path` body read; raise sites compared to the mkdir line |
| F-7 | HIGH | corpus measurement | **THE COST WAS NEVER SIZED AND THE PAYLOAD NEVER SPECIFIED.** The plan says "a short prompt per queued orchestrator" but never states WHAT is sent. Measured, the pending orchestrators are 30,106 to 65,705 characters (~7,500 to ~16,400 tokens each; ~58,000 tokens for all six), so an unbounded probe sends a 16k-token file to answer a yes/no question, and "cheap by caching" would be doing a lot of work. | `len()` over each pending `Kind: orchestrator` file |
| F-8 | HIGH | `tests/test_orchestrator_retirement.py` (`test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module`) | **E-06 (now E-08) WOULD HAVE TRIPPED AN EXISTING TEST THE PLAN DID NOT KNOW ABOUT.** That test slices the exact `###` section this item edits and requires every claim fragment in its `mapping` dict to be present AND backed by a named test class in the same module. The plan neither declared that test file in `Scope-Paths` nor mentioned the constraint, so the executor would have regenerated AGENTS.md and hit a failure whose cause is a mapping dict it had never read. | test source read: the `paragraph()` slice and the `mapping` assertions |
| F-9 | MED | pre-revision E-04 | The override recorded only THAT it was used, not WHY. A bare boolean tells a later reader someone clicked past the gate and nothing about whether they were right to, which is the same "records the fact, not the judgement" gap the remedy field exists to close on the refusal side. | plan read |
| F-10 | MED | `runner_profiles`; `oc_runipd.resolve_launch_profile:2660`; `kgpptv` `- Status: approved` | OQ-01 said "the profile machinery exists" and pointed at `kgpptv`. Half true: profile resolution exists PER RUN, `runner_profiles` has no `role` concept whatsoever, and the per-role work (`kgpptv`) is approved but UNEXECUTED. An executor reading OQ-01 as "reuse the per-role resolver" would find nothing to reuse. | grepped `runner_profiles` for `role` (zero hits); read `resolve_launch_profile`; read `kgpptv`'s status |

## Proposed changes (ordered, validatable)

1. E-01 and E-02 make the probe trustworthy (suspicious prompt, strict parser).
2. E-03 bounds what is SENT to the digest's own inputs; E-04 bounds WHICH orchestrators, cache-first.
3. E-05 sites and gates it implementably (after the run dir, before any turn/worktree/session) with a justified override; E-06 makes it speak constructively.
4. E-07 records the contract in `77tr3o`; E-08 records it in AGENTS.md, honoring the mapping test.
5. E-09 proves both hosts actually gate, not merely decide.

## Deferred / out of scope (with reason)

- Any `ipd_lint` rule. REJECTED and recorded so it is not retried: it cannot separate orchestration from parent-only work, its false positives push agents to delete the orchestration checklist, and it collides with `77tr3o` R-5.
- Requiring a parent to positively assert it holds no work: deferred by the maintainer 2026-09-07, because every existing orchestrator would need backfilling and an un-backfilled parent would be indistinguishable from an unsafe one, the same trade-off `77tr3o` OQ-2 rejected.
- Backfilling the 46 existing orchestrators, and changing the retirement predicate or rollup transition.
- Probing a Set executed by a bare agent with no runner: out of reach by construction, and stated in the orchestrator's Scope check rather than hidden.
- Giving the probe its own per-ROLE model profile: `kgpptv` owns that and is approved-but-unexecuted, so this child must use the run's resolved profile and RECORD which, rather than build role routing here (OQ-01).
- Authoring the children that would clear the four approved orchestrators this gate blocks on day one: that is the parent's OQ-02 and is inherited here as OQ-03, not solved here.

## Scope check

- Over-scope: `engine.py` is in scope ONLY for the managed-block prose E-08 adds; do not touch the installer. `tests/test_orchestrator_retirement.py` is in scope ONLY for the mapping entries and tests E-08's new claims require; do not refactor it, and do NOT weaken `TheRejectedShapeWasNotTaken`, which the parent's CID-1 asserts must pass unmodified.
- Under-scope: none remaining. The bounded probe input (E-03), the spec amendment as its own item (E-07), and the both-hosts-actually-gate proof (E-09) were under-scope before review.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, baseline measured there and pasted, comparing failing NODE IDS not totals. The model call must be stubbed in tests: a test that spends tokens is not a test. At least one end-to-end exercise over a fixture Set whose orchestrator carries prose-only work, because that is the case a syntactic rule cannot catch and the reason this child exists.

TWO ADDITIONAL REQUIREMENTS FROM REVIEW. First, the false-positive side needs a fixture too: at least one orchestrator carrying ONLY orchestration (sequence the children, confirm the ledger) must pass the probe, because F-2 shows nearly every orchestrator carries items and a probe that flags orchestration would fire on almost all of them. The parent's CID-2 enumerates the live classification to use. Second, no test may reach the network or a real model; assert that by construction (a stub that raises if invoked unexpectedly), not by hoping.

## Spec / documentation sync

E-07 amends spec `77tr3o` and E-08 regenerates the AGENTS.md managed block from `engine.py`. Both files are declared in `Scope-Paths`, so the pre-run spec-impact announcement names the spec (the parent's CID-6 checks exactly that).

WHY `77tr3o` IS THE RIGHT SPEC, stated because the pre-revision text said only "the spec that governs the run gates", which resolves to nothing. `77tr3o` R-5 required the E/V pre-transition requirement be resolved explicitly rather than bypassed, and the maintainer chose shape (b): a runner-owned rollup that SKIPS the checkpoint, on the premise that an orchestrator's items are performed by nobody. This gate is the control that makes that premise checked instead of assumed, so a spec still asserting the bare premise no longer describes the system. If the gate is ALSO to be specified as a run gate, `25kzda` Sections 2.5/2.5a house the sibling admission gates and would be a second amendment; that is a judgement for the executor to record, not to skip.

## Open questions

### OQ-01: Which model answers the probe, and does it follow the run's profile?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED 2026-09-07 by the maintainer: USE THE RUN'S ALREADY-RESOLVED MODEL, record which model answered alongside each verdict (child 02 stores the field for exactly this reason), and add NO role routing here. Confirmed there is no per-role machinery to reuse: `runner_profiles` has no role concept, `resolve_launch_profile` (`oc_runipd.py:2660`) resolves one identity for the whole run, and `kgpptv` is approved but unexecuted and addresses the VERIFIER specifically, not an arbitrary new action. The general capability (per-action model settings) is to be filed as a BACKLOG ITEM rather than an IPD, because it is a decided-but-unscoped design question and not a task list; it graduates into a plan later if it earns it. Caching bounds the cost meanwhile.

### OQ-02: May a run be gated on a model call at all?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-002
- Resolution or deferral rationale: RESOLVED 2026-09-07 by the maintainer: option (b) PLUS A RETRY BUDGET. Distinguish COULD NOT ASK (unreachable, no binary, timeout, rate-limited) from ASKED AND GOT SOMETHING UNUSABLE. Retry a could-not-ask up to a maximum, default 3, configurable by flag or config variable. After the budget is exhausted, a could-not-ask does NOT block the run: it proceeds with a loud warning, so a model outage cannot halt work that is otherwise fine. An answer that WAS received but is unparsable, or that reports a problem, DOES block. This trades a narrow induced-hole risk for run availability, and the maintainer priced it deliberately.

### OQ-03: What happens to the four APPROVED orchestrators this gate blocks on day one?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: PR-005
- Resolution or deferral rationale: RESOLVED 2026-09-07 with the parent (`yeh7gc` OQ-02): CLEAR FIRST. The missing children for `5e4sb6`, `h0zljh`, `rh5tt6` and `3m0urk` are authored BEFORE this child lands, so the gate never fires on known debt and the override never becomes reflex. This child MUST NOT execute until that holds.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the prompt text, showing it names the two sentinels, states that a child checklist is expected and is not an execution, and instructs that doubt resolves to CONTAINS EXECUTIONS. Paste the sentinel constants proving prompt and parser share them.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste parser results for the two exact sentinels, plus a chatty reply, an empty reply, a truncated reply, and a reply with both sentinels: the last four must all yield `unknown` and BLOCK. Include a mutation check: loosen the parser, show a test fails, revert.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the excerpt the probe actually sends for one real orchestrator, with its character and approximate token count, and paste the digest inputs child 02 keys on beside it, showing they are THE SAME two things (E-item action text plus the child table). Paste the measured payload size for each pending orchestrator so the cost is on the record rather than described as "short".
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a run with all queued orchestrators cached showing ZERO model calls (a stub call counter is acceptable evidence), then edit one orchestrator's E-item text and paste the same run showing exactly ONE call. Paste proof the probe is queue-scoped: a run selecting ONE Set must not probe orchestrators outside it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste all three paths (interactive prompt, non-interactive failure, override accepted-and-recorded-with-its-justification). Paste proof a refusal left NO lane worktree, NO session and NO agent turn behind (an empty `sessions/` directory plus a zero attempt count is acceptable), and paste `aw runs` for the refused run read AFTER the process exited, showing the refusal is durable. Do NOT assert "no run directory": E-05 records why that is impossible, and a V-item demanding it would be unpassable.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the summary block and the `aw runs` output for a refused run, showing the reason AND a remedy that says to add a child. Assert the message does NOT read as a bare prohibition: paste the full string and state which words name the constructive action.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `77tr3o` diff showing the gate recorded as a requirement beside R-5's resolution, and paste the pre-run spec-impact announcement naming that file (which is the parent's CID-6). If a second spec (`25kzda` 2.5/2.5a) was judged to need amending too, paste that decision and its outcome; if it was judged unnecessary, say why.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the regenerated AGENTS.md passage; paste the corrected denominator in it (46 of 47 `Kind: orchestrator` plans, not 46 of 130); paste `test_every_assertion_in_the_new_text_maps_to_a_test_in_THIS_module` PASSING together with the mapping entries added and the test class each new claim maps to; and paste the idempotent-render test passing. Also paste `TheRejectedShapeWasNotTaken` passing UNMODIFIED, since the parent's CID-1 depends on it and this item edits the same module.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted object-identity output per new symbol showing both hosts resolve it to the same object from `runner_shared`; the AST-measured oc-to-agy import count before and after showing it did not increase from 47; and the `pgq326` lesson closed out by DEMONSTRATING that `aw agy run` refuses on the same fixture `aw oc run` refuses on, not merely that both compute the same decision.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION IS BLOCKED ON TWO QUESTIONS, and human approval alone clears neither. OQ-02 (`Blocking: yes`) asks whether a run may be gated on a model call at all: this would be the first non-deterministic gate in `aw <host> run`, and because it fails closed, an unavailable or confused model blocks a run that is otherwise fine. OQ-03 (`Blocking: yes`) is the parent's OQ-02 made live by this child: four APPROVED orchestrators carry parent-only work today, so the day this lands, each refuses or prompts on every run that queues it. The pre-execution checkpoint refuses while either is open.

Execution contract: commit ONLY the files this plan changed, path-scoped; never `git add -A`, never `-a`, never push. Verify the staged set before every commit and RE-VERIFY after any failed or hook-interrupted commit. Paste ACTUAL runner output when reporting tests passed.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved m7gvuz --by-human --message ...`) before execution, and its `Item-Dependencies` refuse dispatch until both `r2i1b1` and `8tgg6g` are executed. Do NOT hand-write a `Readiness:` field. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
