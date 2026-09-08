# IPD: State the runner-owns-begin-finalize role at turn start instead of only in the end-of-turn refusal

- Date: 2026-09-08
- Kind: child
- Concern: THE PROMPT INVITES THE ONE ACTION THE RUNNER WILL REFUSE, AND THE REFUSAL ARRIVES AN HOUR LATE. `AW-LIFECYCLE-ROLE-001` refuses `aw ipd begin`/`aw ipd finalize` from a managed worker lane, correctly: an in-lane agent running them forks a SECOND receipt and a SECOND lifecycle transaction the driver cannot see, and the in-lane receipt copy then hides the split (rationale comment `agent_workflows/ipd_lifecycle.py:51-71`, selector `worker_role_active` `:74`, refusal `_refuse_worker_role_verb` `:84`). This plan does NOT weaken that rule. It fixes the fact that the rule is stated ONLY in the refusal, at the END of a turn, while the prompt that opens the turn implies the opposite.
  MEASURED AT THIS HEAD, not remembered. The OpenCode execute prompt's ONLY mention of finalize presupposes the agent performs it: "If the IPD cannot validly finalize, preserve partial work using the repository-supported nonterminal checkpoint mechanism or an attributable isolated branch/worktree." (`agent_workflows/oc_runipd.py:4881-4884`, inside `build_prompt` `:4785`). Substring-checked across all four prompt builders (`oc_runipd.build_prompt` `:4785`, `oc_runipd.build_verifier_prompt` `:4913`, `agy_runipd.build_prompt` `:2297`, `agy_runipd.build_verifier_prompt` `:2410`) plus the three fragments they concatenate (`lane_containment.isolation_notice` `:352`, `reporting_contract.prompt_block` `:114`, `DEFAULT_RUNBOOK_TEXT` `oc_runipd.py:2598`): `AW-LIFECYCLE-ROLE` ABSENT, `begin/finalize` ABSENT, `do not run` ABSENT, `runner owns`/`runner performs` ABSENT. Nothing in the launched turn's prompt surface says who owns the transition.
  TWO ASYMMETRIES THE BACKLOG ITEM DID NOT KNOW, both found by measurement and both changing the work. FIRST, the misleading sentence exists on ONE host only: `agy_runipd.build_prompt` mentions finalize ZERO times (the paragraph is simply absent between its "Maximize safe forward progress" block `agy_runipd.py:2377-2381` and the outcome-JSON block `:2383`). So the REWORD has one site while the STATEMENT has four. SECOND, neither verifier prompt mentions finalize at all; they are SILENT, not misleading, so the item's premise that the verifier prompt "shares the role [of implying finalize]" is wrong in its diagnosis while its remedy still applies.
  THE OBSERVED COST, which is why this is a bug and not a wording preference. Plan `03ie04` completed all seven E-items and all seven V-items with pasted evidence, then reported `substantially-complete` with an `incomplete_requirements` entry explaining at length that finalize had refused with `AW-LIFECYCLE-ROLE-001`, that no begin receipt existed, and enumerating scope-reconciliation inputs for a human. Every word was correct and none of it should have been necessary. The refusal is a NON-ERROR path for a managed lane and reads as a hard failure: it is printed to stderr and returns `EXIT_CANNOT_RUN` (2) (`ipd_lifecycle.py:94-100`).
- Scope: State the role UP FRONT in all four prompt builders, reword the one misleading sentence, and add the "expected path, no further action" framing to the refusal message, each pinned by a prompt-text test so it cannot silently regress. EXCLUDES weakening or removing the role rule; excludes the suite gate that actually stranded the eleven lanes (`daexj1` owns it); excludes the green-COMPLETED misreport for a stranded run (`ys1dor`); excludes `aw attention` blindness to a stranded lane (`pr5b0t`, from backlog `nuanaw`); and excludes two of the item's five asks, which MEASUREMENT SHOWS ARE ALREADY SATISFIED (see Findings F-4 and F-5).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/ipd_lifecycle.py, tests/test_worker_role_refusal.py
- Item-Dependencies: none
- Status: to-review
- Set: roleadv
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 8b9ufm
- From-Backlog: fvl44r
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `fvl44r`. THE ITEM IS PARTLY OBSOLETE AND TWO OF ITS FIVE ASKS ARE DROPPED ON EVIDENCE, not on judgement. Ask (4) ("do not also emit the `--scope-reason`/`--scope-ack` reconciliation demand") is a NO-OP: the refusal emits neither. Captured by invoking `_refuse_worker_role_verb("finalize")` and substring-checking its stderr; the scope demand is built in `_reconcile_scope` (`ipd_lifecycle.py:1716`, flag strings `:1768`, `:1770`) and surfaced only by `finalize()`'s findings branch (`:2493-2508`), which the role guard at `:3126` returns BEFORE reaching. So whatever scope block `03ie04` reported came from the agent's own reasoning or a non-worker invocation, not from this refusal. There is nothing to remove and E-items for it would be fictional work. Ask (3) is HALF satisfied: the message already says "The runner performs begin/finalize for this lane" and "let the driver transition the plan" (`:96-99`), so only the NON-ERROR FRAMING is missing, which is what E-04 delivers. Ask (1) and (2) are entirely unbuilt and are the bulk of this plan; ask (5) is unbuilt and is recorded as an OPEN QUESTION rather than built, because answering it requires knowing at prompt-build time whether the runner WILL finalize, which is not knowable then. NO PLAN COVERS ANY PART: searched all five plan dispositions for `AW-LIFECYCLE-ROLE`, `worker_role`, `rolegate`, `_refuse_worker`, `begin/finalize`, `build_prompt`, `build_verifier_prompt`; the only pending hit is `yvvf98:382` explaining that its own lane runs with `AW_EXECUTION_ROLE=worker`, which is not an E-item. THE DECISION THIS PLAN REVERSES, cited because a reviewer must see it: superseded plan `tch3bo` (`lanecontain-01`) F-12 RECORDED this exact mixed prompt signal and deliberately declined to fix it by wording, holding that "that mismatch ... is now handled by ENFORCEMENT ... rather than by prompt wording". The counter-argument is the measured cost: enforcement without advertisement bills a full turn before the agent learns the rule, and `03ie04` paid it. Also corrected: the item cites HEAD `31169afd`; HEAD here is `fac69fbd` and every prompt-text claim was re-measured at it. The item's 46-turn/25-recovery figure could NOT be re-verified from a lane worktree, because `.aw/records/runs/` is gitignored and absent there; this plan therefore rests on the code measurements, not on that count.

## Goal

Tell the agent at the START of its turn what the runner will refuse at the END of it, so a managed lane stops paying a full turn to discover a rule that fits in one sentence, and stops reporting a correct, expected handoff as an incomplete turn.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the absence before fixing it

- [ ] E-01 WRITE THE FAILING PROMPT-TEXT TEST FIRST, covering all four builders, so the fix is demonstrated rather than asserted and cannot silently regress. Assert that each of `oc_runipd.build_prompt`, `oc_runipd.build_verifier_prompt`, `agy_runipd.build_prompt` and `agy_runipd.build_verifier_prompt` produces text containing the role statement. These four assertions must FAIL at HEAD; paste that failure.
  ASSERT ON RENDERED OUTPUT, NOT ON SOURCE TEXT. A test that greps the .py file would pass while the sentence sat in a branch no invocation reaches. Build the prompt by CALLING each function with a minimal state/item, the way `tests/test_worker_role_refusal.py` already constructs its inputs, and assert on the returned string.
  ASSERT A STABLE ANCHOR, NOT A WHOLE SENTENCE. Pin on the token `AW-LIFECYCLE-ROLE-001` plus a short invariant phrase, so a later prose improvement does not break the test for no reason. Choosing a whole-sentence match is the failure mode that makes prompt tests hated and then deleted.
  PUT THEM IN `tests/test_worker_role_refusal.py`, beside the refusal's existing behavior tests (the zero-side-effect assertions at that module's `RefusalTests`), so a reader sees the advertisement and the enforcement pinned in one place.
  - Depends on: none
  - Expected outcome: four assertions, one per builder, failing at HEAD with pasted output, asserting on RENDERED prompt text and pinned to a short stable anchor.
  - Execution state: pending

### Task group 2: advertise the rule where the agent will act on it

- [ ] E-02 ADD THE ROLE STATEMENT TO BOTH EXECUTE PROMPTS, in `oc_runipd.build_prompt` (`:4785`) and `agy_runipd.build_prompt` (`:2297`). It must say three things and no more: the RUNNER performs `aw ipd begin` and `aw ipd finalize` for this lane; the agent must NOT run them; the agent's terminal obligation is to write the outcome file the prompt already names and stop.
  PLACE IT WHERE THE AGENT WILL READ IT BEFORE WORKING, not in a trailing block. The natural seam is immediately before the outcome-JSON instructions (`oc_runipd.py:4886`, agy `:2383`), because that is where the prompt already tells the agent what "finishing" means, and the role statement is precisely a correction to that meaning.
  NAME THE TOKEN `AW-LIFECYCLE-ROLE-001`. An agent that hits the refusal despite the statement must be able to connect the two strings; an unnamed rule teaches nothing.
  KEEP BOTH HOSTS' WORDING IDENTICAL. `build_prompt` is already a class-(c) DIVERGED symbol slated for reconciliation by the `rununify` Set (`5e4sb6`'s child table); adding a THIRD divergence would make that reconciliation harder. If a shared constant is the cheaper way to keep them identical, prefer it, but do NOT re-home the builders here: that is `runnerlayer`'s work (`lyo1tz`, `9kmbr0`, `1f7xno`).
  - Depends on: E-01
  - Expected outcome: both execute prompts state runner-owns-begin/finalize, name the token, and name the outcome file as the terminal obligation, in identical wording on both hosts.
  - Execution state: pending

- [ ] E-03 ADD THE SAME STATEMENT TO BOTH VERIFIER PROMPTS, `oc_runipd.build_verifier_prompt` (`:4913`) and `agy_runipd.build_verifier_prompt` (`:2410`), and note in the change WHY it belongs there even though neither mentions finalize today.
  THE ITEM'S DIAGNOSIS IS WRONG HERE AND THE REMEDY IS STILL RIGHT. The verifier prompts are SILENT on finalize, not misleading (substring-verified: zero `finalize` occurrences). But silence is not safety: a verifier runs in the same managed worker lane under the same env selector, so it is subject to the same refusal, and an agent that decides on its own to "helpfully finalize" after verifying hits it identically. State the rule.
  DO NOT COPY THE MISLEADING SENTENCE INTO THEM. E-04 is deleting that sentence's implication from the one place it exists; reproducing it in two more prompts while fixing it in one would be a net loss.
  - Depends on: E-02
  - Expected outcome: both verifier prompts carry the identical role statement, with the change recording that the verifier was silent rather than misleading and why the statement still belongs.
  - Execution state: pending

### Task group 3: stop the two remaining mis-signals

- [ ] E-04 REWORD THE ONE MISLEADING SENTENCE, at `oc_runipd.py:4881-4884` only. It must describe the CONDITION ("the work is not validly complete") rather than the ACTION the agent is forbidden to take ("the IPD cannot validly finalize"). The preserve-partial-work instruction that follows is CORRECT and must survive intact; only the clause that presupposes the agent finalizes changes.
  THERE IS EXACTLY ONE SITE. Verified by substring across the package: `cannot validly finalize` appears only at `oc_runipd.py:4881`. Do NOT add the sentence to `agy_runipd.build_prompt` in order to "make the hosts match": that would create the defect on a second host in the name of symmetry. The hosts must match on the STATEMENT (E-02), not on the misleading sentence.
  - Depends on: E-03
  - Expected outcome: the OpenCode prompt's finalize sentence describes the condition, not the forbidden action; the preserve-partial-work instruction unchanged; `agy_runipd` still contains no such sentence.
  - Execution state: pending

- [ ] E-05 MAKE THE REFUSAL SAY "EXPECTED, NOT BROKEN", in `_refuse_worker_role_verb` (`ipd_lifecycle.py:84`), whose message is at `:94-100`. Add that this is the NORMAL path for a managed lane and that NO FURTHER ACTION is required from the agent beyond its outcome file. Keep every word that is already there: the token, "The runner performs begin/finalize for this lane", "report your result instead", "let the driver transition the plan".
  DO NOT CHANGE THE CHANNEL OR THE EXIT CODE. It writes to stderr and returns `EXIT_CANNOT_RUN` (2). Both are load-bearing: stderr keeps a caller parsing stdout unaffected (stated in the docstring at `:85-91`), and a nonzero code is what makes a scripted `aw ipd finalize` in a lane fail rather than appear to succeed. A "this is fine" message on exit 0 would be a genuine regression, since the verb really did not do what was asked. This is a WORDING fix; whether the exit code should differ for the expected case is recorded as OQ-02, not decided here.
  DO NOT REMOVE THE SCOPE-RECONCILIATION DEMAND, because it is NOT THERE. The item's ask (4) is a no-op at this HEAD (see F-4). If the executor finds it present after all, that is a finding to report, not a silent scope expansion.
  PRESERVE ZERO SIDE EFFECTS, which is already guaranteed by the guard's placement as the first statement of `run_begin` (`:2946-2947`) and `run_finalize` (`:3126-3127`) and already pinned by `tests/test_worker_role_refusal.py` (exit code, token, no receipt written, plan not moved) and `tests/test_turn_bounds.py`. Nothing to build; those tests must stay green.
  - Depends on: E-04
  - Expected outcome: the refusal states the expected-path framing and that no further action is required, with the token, remedy, stderr channel and exit code 2 all unchanged, and the existing zero-side-effect tests green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE ROLE RULE IS CORRECT AND ITS RATIONALE IS WRITTEN DOWN. The split-brain hazard (a forked in-lane receipt and transaction) is documented in the comment block at `ipd_lifecycle.py:51-71`, which also states the honest limit: it is an ENV SELECTOR, not a hardened boundary, and hard enforcement is an OS-sandbox question tracked elsewhere (`x03wgn` Phase 6 `1o4eif`). Do not re-litigate either.
- THE REFUSAL IS ALREADY WELL BUILT IN TWO RESPECTS: it fires before any selector resolution, gate, receipt write or plan mutation (docstring `:85-91`, call sites `:2946`, `:3126`), and its message already names the remedy.
- FOUR PROMPT BUILDERS, TWO HOSTS. `oc_runipd.build_prompt` `:4785`, `oc_runipd.build_verifier_prompt` `:4913`, `agy_runipd.build_prompt` `:2297`, `agy_runipd.build_verifier_prompt` `:2410`. A statement added to one host only is half a fix.
- THE PROMPT CONCATENATES THREE FRAGMENTS and none of them carries the rule: `lane_containment.isolation_notice` (`:352`, whose block says only "The driver integrates your lane back into the main checkout after this turn", `:399`), `reporting_contract.prompt_block` (`:114`), and `DEFAULT_RUNBOOK_TEXT` (`oc_runipd.py:2598`, twin `agy_runipd.py:1739`), which the prompt tells the agent to read (`oc_runipd.py:4860`). Any of the three would be a defensible home; the builders are chosen here because the statement must be unconditional.
- `build_prompt` IS A KNOWN DIVERGED SYMBOL. `5e4sb6` (`rununify` orchestrator) classifies it class (c) DIVERGED and defers its reconciliation, so this edit lands in a function someone will later unify. Keep the two hosts' new text IDENTICAL to make that easier.
- THE ZERO-SIDE-EFFECT PROPERTY IS ALREADY TESTED, in `tests/test_worker_role_refusal.py` and `tests/test_turn_bounds.py`. This plan must keep them green, not re-prove them.
- A PROMPT TEST MUST ASSERT ON RENDERED OUTPUT. Grepping the source would pass while the text sat unreachable.
- Shared checkout, concurrent edits, suite runs BARE. Both driver files are being edited by live runs; re-locate every symbol by NAME.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the prompt invites the forbidden action | The only finalize mention in either execute prompt presupposes the agent finalizes: "If the IPD cannot validly finalize, preserve partial work ...". | `agent_workflows/oc_runipd.py:4881-4884` |
| F-2 | HIGH | and never states who owns the transition | Substring-checked across all four builders plus `isolation_notice`, `prompt_block` and `DEFAULT_RUNBOOK_TEXT`: `AW-LIFECYCLE-ROLE` absent, `begin/finalize` absent, `do not run` absent, `runner owns`/`runner performs` absent. | `oc_runipd.py:4785`, `:4913`, `agy_runipd.py:2297`, `:2410`, `lane_containment.py:352`, `reporting_contract.py:114`, `oc_runipd.py:2598` |
| F-3 | MEDIUM | the misleading sentence is on ONE host, the gap is on FOUR | `cannot validly finalize` occurs only at `oc_runipd.py:4881`; `agy_runipd.build_prompt` mentions finalize zero times. So REWORD has one site, STATE has four. The item implies both prompts carry it. | substring across `agent_workflows/`; `agy_runipd.py:2377-2383` |
| F-4 | MEDIUM | **the item's ask (4) is a no-op: nothing to remove** | Captured `_refuse_worker_role_verb("finalize")`'s stderr: it contains neither `--scope-reason` nor `--scope-ack`. Those are built in `_reconcile_scope` and surfaced only by `finalize()`'s findings branch, which the role guard returns before reaching. | `ipd_lifecycle.py:94-100`, `:1716`, `:1768`, `:1770`, `:2493-2508`, guard `:3126` |
| F-5 | MEDIUM | the item's ask (3) is half satisfied | The message already says "The runner performs begin/finalize for this lane" and "let the driver transition the plan". Only the non-error framing is missing. | `ipd_lifecycle.py:96-99` |
| F-6 | MEDIUM | the verifier prompts are SILENT, not misleading | Neither verifier builder mentions finalize at all. The item's diagnosis ("shares the role") is wrong; the remedy still applies, since a verifier runs in the same worker lane under the same selector. | `oc_runipd.py:4913-4979`, `agy_runipd.py:2410-2476` |
| F-7 | MEDIUM | this plan REVERSES a recorded decision | Superseded `tch3bo` (`lanecontain-01`) F-12 recorded this exact mixed signal and declined to fix it by wording, holding it "is now handled by ENFORCEMENT ... rather than by prompt wording". The counter is the measured cost of enforcement without advertisement. | `tch3bo` F-12 |
| F-8 | MEDIUM | no plan covers any part | Searched all five dispositions for `AW-LIFECYCLE-ROLE`, `worker_role`, `rolegate`, `_refuse_worker`, `begin/finalize`, `build_prompt`, `build_verifier_prompt`. Only pending hit is `yvvf98:382`, a note that its lane runs as `worker`. `daexj1` (suite gate), `ys1dor` (run summary), `u06zo2` (lifecycle policy spec) are all disjoint. | plan-tree search |
| F-9 | LOW | the misattribution the item pre-empted holds | The finalize gate did NOT strand the eleven lanes: all twelve stranded items show suite-passing false and no finalize attempt. That cause is `daexj1`'s. This plan must not claim to fix stranding. | item's own measurement, retained |
| F-10 | LOW | zero-side-effect is already pinned | `tests/test_worker_role_refusal.py` asserts exit code, token, no receipt, plan not moved; `tests/test_turn_bounds.py` asserts the same shape. The item's test (f) needs keeping, not building. | both test modules |
| F-11 | LOW | the 46-turn measurement is unverifiable from a lane | `.aw/records/runs/` is gitignored and absent in a worktree, so the item's 46/25 counts could not be re-measured. This plan rests on code measurements instead. | `.aw/.gitignore` `records/runs/` |

## Proposed changes (ordered, validatable)

1. Write the four-builder prompt-text test and show it failing at HEAD (E-01).
2. State runner-owns-begin/finalize in both execute prompts, identically, naming the token (E-02).
3. State the same in both verifier prompts, recording why silence was not safety (E-03).
4. Reword the single misleading sentence to describe the condition, not the forbidden action (E-04).
5. Add the expected-path framing to the refusal, keeping token, remedy, channel and exit code (E-05).

## Deferred / out of scope (with reason)

- REMOVING OR WEAKENING THE ROLE RULE. The split-brain hazard is real and documented (`ipd_lifecycle.py:51-71`), and the honest limit (env selector, not a hardened boundary) is already written down. Hard enforcement is an OS-sandbox question owned elsewhere (`1o4eif`).
- THE ITEM'S ASK (4), REMOVING THE SCOPE-RECONCILIATION DEMAND FROM THE REFUSAL. Dropped as a NO-OP on evidence, not deferred: the refusal emits neither flag (F-4). Building an E-item for it would be fictional work. If the executor finds otherwise, report it.
- THE ITEM'S ASK (5), TELLING THE AGENT WHEN THE RUNNER WILL **NOT** FINALIZE. Genuinely wanted and genuinely harder: at prompt-build time the runner does not yet know whether its own suite gate will refuse, so an honest conditional statement needs a signal that does not exist at that seam. Recorded as OQ-01 with the concrete blocker rather than half-built. The adjacent half (a run whose work never landed reporting itself honestly) is `ys1dor`'s.
- THE SUITE GATE THAT ACTUALLY STRANDED THE ELEVEN LANES. `daexj1` (`integearn-03`) owns it. This plan changes no gate.
- THE GREEN-COMPLETED MISREPORT FOR A STRANDED RUN. `ys1dor` (`integearn-04`) owns it; its scope is `render_stream.py`.
- `aw attention` BLINDNESS TO A STRANDED LANE. `pr5b0t` (`lanestrand-01`, from backlog `nuanaw`) owns it.
- RE-HOMING OR UNIFYING THE PROMPT BUILDERS. `runnerlayer` (`lyo1tz`, `9kmbr0`, `1f7xno`) and `rununify` (`5e4sb6`) own that. This plan edits them in place and keeps the two hosts' new text identical precisely to make that later work easier.
- CHANGING THE REFUSAL'S EXIT CODE OR CHANNEL. Both are load-bearing (F-5 discussion in E-05). The question of whether an expected-path refusal deserves a distinct code is OQ-02, recorded and not decided.
- WRITING THE LIFECYCLE-AUTOMATION POLICY SPEC. `u06zo2` (`lcpolicy-01`) is producing exactly that spec and its E-01 inventories `driver_begin` and `aw ipd finalize`. This plan changes prose the spec will govern, so it must not contradict it; if `u06zo2` lands first, reuse its vocabulary.

## Scope check

- Over-scope: none. Four prompt strings, one sentence reworded, one message extended, one test module.
- Scope-Paths justification: `agent_workflows/oc_runipd.py` holds `build_prompt` (`:4785`), its misleading sentence (`:4881-4884`), `build_verifier_prompt` (`:4913`) and `DEFAULT_RUNBOOK_TEXT` (`:2598`) checked for the rule's absence; `agent_workflows/agy_runipd.py` holds the two peer builders (`:2297`, `:2410`) that must carry the identical statement; `agent_workflows/ipd_lifecycle.py` holds `_refuse_worker_role_verb` (`:84`) and its message (`:94-100`) that E-05 reframes, plus the two guard call sites (`:2946`, `:3126`) whose placement E-05 must not disturb; `tests/test_worker_role_refusal.py` holds the existing zero-side-effect assertions and is where E-01's four prompt-text assertions belong so advertisement and enforcement are pinned together.
- Under-scope, stated rather than left as `none`: this plan does not touch any gate, does not change the refusal's exit code or channel, does not add the conditional "the runner will not finalize" signal (OQ-01), does not re-home or unify the builders, does not edit `lane_containment.isolation_notice` or `DEFAULT_RUNBOOK_TEXT` (either would be a defensible home, but the builders are chosen because the statement must be unconditional), and writes no spec.

## Required tests / validation

- THE FOUR-BUILDER PROMPT TEST (E-01) shown FAILING at HEAD and PASSING after, both outputs pasted. A prompt test only ever run against the fixed code proves nothing about the absence it exists to prevent.
- ASSERTIONS ON RENDERED OUTPUT, proven by showing the test CALLS each builder rather than reading its source. Paste the test body.
- HOST SYMMETRY PROOF: the statement text in `oc_runipd` and `agy_runipd` is byte-identical (paste both, or paste the shared constant and both references).
- NEGATIVE PROOF FOR E-04: `cannot validly finalize` no longer appears anywhere, AND `agy_runipd.build_prompt` still contains no finalize sentence (so the fix did not spread the defect). Paste both substring checks.
- THE REFUSAL MESSAGE BEFORE AND AFTER, captured by invoking `_refuse_worker_role_verb("finalize")` and pasting stderr both times, with the exit code shown UNPIPED (`cmd >/dev/null 2>&1; echo $?`) as 2 both times.
- THE EXISTING ZERO-SIDE-EFFECT TESTS GREEN: `tests/test_worker_role_refusal.py` and `tests/test_turn_bounds.py` re-run with their own summary lines pasted.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated explicitly. Baseline on main 2026-09-08 per the graduation briefing: `1 failed, 5648 passed`; measured in this lane at HEAD `fac69fbd` the same module set reported green, so state what YOU observe rather than quoting either number. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count. Inside a lane worktree roughly 32 further failures are environmental (several tests read live repo state, and this lane itself runs with `AW_EXECUTION_ROLE=worker` which reds `test_worker_role_refusal` environmentally, per `yvvf98:382`) - judge on the delta and say so.
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC CHANGE IS EXPECTED, and no `.spec.md` path is declared in `Scope-Paths`. The role rule already exists and is already documented in code (`ipd_lifecycle.py:51-71`); this plan advertises it, and advertising an existing rule changes no contract.

ONE COORDINATION OBLIGATION. `u06zo2` (`lcpolicy-01`) is authoring the lifecycle-automation policy spec and its E-01 inventories `driver_begin` and `aw ipd finalize`, i.e. it will write down WHO may perform these verbs. If it lands first, E-02's statement must use its vocabulary rather than inventing a second phrasing for the same rule. If this plan lands first, the spec should quote the prompt statement. Either order is fine; contradicting it is not.

THE PROMPT TEXT ITSELF IS AGENT-FACING, not end-user prose, so the no-dashes rule does not bind it. The refusal message (E-05) is closer to operator-facing and should stay plain either way.

## Open questions

### OQ-01: Should the prompt or the refusal tell the agent when the runner will NOT finalize?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY OPEN, WITH THE BLOCKER NAMED, because it is the item's ask (5) and the honest answer is that the information does not exist at the seam where it would have to be stated. At `build_prompt` time the runner cannot know whether its own validation/suite gate will later refuse, so a prompt sentence promising "the runner will finalize" would be a claim it cannot keep, and that is strictly worse than silence: an agent told its work will land, whose work then strands, reports success it did not earn. The REFUSAL is a better seam (by then more is known), but the refusal fires in the AGENT's process while the decision belongs to the DRIVER's, so passing the fact across requires a channel that does not exist today. The adjacent half is already owned: `ys1dor` makes a run whose work never landed say so in red, and `pr5b0t` makes a stranded lane visible in `aw attention`. So the operator-facing gap is being closed from the other end, which is why this stays a question rather than becoming an E-item. What a maintainer must decide: whether the AGENT needs to know at all, given that the two surfaces above tell the HUMAN.

### OQ-02: Does an expected-path refusal deserve a distinct exit code?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN AND SUBORDINATE TO E-05, which changes wording only. The tension is real: the message will now say "this is the expected path, no further action required" while returning `EXIT_CANNOT_RUN` (2), and an agent reading exit codes still sees a failure. But changing the code is not obviously right either. The verb genuinely did not do what was asked, a scripted `aw ipd finalize` inside a lane MUST NOT appear to succeed, and `EXIT_CANNOT_RUN` is a shared constant whose meaning other call sites depend on. A third option exists (keep 2, and make the runner's own reporting classify this refusal as expected), which costs nothing here and belongs with whoever owns the run summary. Non-blocking because the wording fix delivers the value either way.

### OQ-03: Is a prompt-text test the right guard, or does it invite brittleness?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED IN FAVOUR OF THE TEST, with the brittleness bounded by construction. The risk is real and well known: a test pinning a whole sentence breaks on every prose improvement, gets marked annoying, and is deleted, leaving the regression unguarded. The mitigation is in E-01 and is not optional: assert a SHORT STABLE ANCHOR (the token `AW-LIFECYCLE-ROLE-001` plus one invariant phrase) on RENDERED output, never a full sentence and never the source file. That shape survives rewording while still failing if the statement disappears, which is exactly the property wanted. The alternative, trusting review to notice a deleted sentence in a 120-line f-string, is what allowed the gap to exist for the whole life of the feature.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new test body and its ACTUAL FAILING output at HEAD, before any prompt edit, showing all four builder assertions failing. Confirm by quoting the test that it CALLS each builder and asserts on the returned string rather than reading the source file. Quote the chosen anchor and state in one sentence why it is short and stable rather than a whole sentence.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the added statement from BOTH `oc_runipd.build_prompt` and `agy_runipd.build_prompt` and show they are byte-identical (a diff of the two strings, or the shared constant plus both references). Confirm the statement names `AW-LIFECYCLE-ROLE-001`, says the runner performs begin/finalize, says the agent must not run them, and names the outcome file as the terminal obligation. Paste the rendered prompt region showing WHERE it sits relative to the outcome-JSON block.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the added statement from BOTH verifier builders and show it matches E-02's text. Paste the substring check proving neither verifier prompt gained a "cannot validly finalize" style sentence. State in one sentence the recorded reason the statement belongs in a prompt that never mentioned finalize.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the reworded sentence with its file:line, showing it describes the CONDITION and no longer presupposes the agent finalizes, and showing the preserve-partial-work instruction that follows is intact. Paste TWO negative checks: `cannot validly finalize` absent package-wide, and `agy_runipd.build_prompt` still containing no finalize sentence.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the refusal's stderr BEFORE and AFTER, captured by invoking `_refuse_worker_role_verb("finalize")`, showing the new expected-path framing and showing the token, the "runner performs begin/finalize" clause, the "report your result instead" clause and the driver-transition clause all retained. Paste the UNPIPED exit code (`cmd >/dev/null 2>&1; echo $?`) as 2 both times. Paste the summary lines of `tests/test_worker_role_refusal.py` and `tests/test_turn_bounds.py` showing the zero-side-effect assertions green (or, if this lane runs as `worker` and reds them environmentally, say so explicitly and paste a run from a non-worker environment). THEN paste the BARE `python3 -m pytest` summaries before and after and state the failure-set delta explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. Both open questions (OQ-01, the conditional "runner will not finalize" signal; OQ-02, the exit code) are deliberately subordinate: the plan delivers its value with either answer, and each is recorded with the concrete blocker rather than guessed at.

IT CARRIES `Blocks-Release: next`, inherited from backlog `fvl44r` under the all-bugs-block-release rule. The justification is not prose quality: the prompt currently invites the one action the runner will refuse, and the cost is measured in whole agent turns (`03ie04` spent its terminal output reasoning about a rule that fits in one sentence).

IT DELIBERATELY REVERSES A RECORDED DECISION. `tch3bo` F-12 saw this mixed signal and chose enforcement over wording. A reviewer should weigh F-7 explicitly: the position here is that enforcement and advertisement are not alternatives, and that enforcing an unadvertised rule bills a full turn to teach it.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. Write the FAILING TEST FIRST and paste its failure. Re-locate every symbol by NAME: both driver files are being edited by live runs and their line numbers moved by roughly 70 and 95 lines in a single day, so every citation here is a starting point, not an address. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index. Do NOT edit any other plan, and do NOT weaken the role rule.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the failing-then-passing prompt test, the host-symmetry proof, and the before/after refusal capture with its unpiped exit code.
