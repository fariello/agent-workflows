# IPD: Propagate a usable gate answer to the post-merge gate so an attributed-away failure is not re-blamed after the merge

- Date: 2026-09-22
- Kind: child
- Concern: A lane's suite failure is adjudicated TWICE by two independent gates, and the agent's answer reaches only the first, so a failure the agent correctly attributed away is silently re-litigated after the merge and refuses the lane anyway. MEASURED on item `ld8lb3` in run `run-20260922T024054Z-2245533`. GATE 1 is the per-lane suite signal: the agent was asked, answered `not-mine`, the record shows `answer: not-mine` with `usable: True`, and the release WORKED exactly as documented - `attempts[0]["integration_detail"]` ends "RELEASED by the agent's gate answer (not-mine)", `attempts[0]["finalized"]` is `True`, and the plan genuinely reached `executed/` on the lane branch (commit `78891bde`). GATE 2 is the POST-MERGE revalidation inside `runner_shared.make_integration_validation_runner`, reached later through `runner_shared.integrate_lane_branch`; it re-runs the suite on the merged tree and refuses on its own authority, consulting NEITHER the answer nor the baseline. The item's final status is `merge-refused`.
  THE ANSWER WAS WELL-FOUNDED, which is what makes the second adjudication a defect rather than a safeguard. The agent named `except Exception: pass` in `runner_shared` inside the region `tests/test_defect_report.py` fences, identified the commit that introduced it (`894d7924`, landed after the lane's base), proved it failing at its own base commit `301a1d8fbc15`, re-ran the node id with its own four source changes stashed out to show the failure persisting, and filed it as backlog `p9ag41` rather than opportunistically fixing another agent's code. That is precisely the good-faith attribution the feature exists to honor. It was honored once and then overridden by a gate that never saw it.
  THIS IS DELIBERATELY NARROWER THAN THIS PLAN'S ORIGINAL FILING, which claimed the release was inert. That claim is retracted in the backlog item's own history: the release is NOT inert, it simply governs `integration.earned` (and therefore self-finalize) and has no channel to the post-merge gate. Stating it correctly matters because it changes the fix from "make the release work" to "give the answer a channel to the second gate".
  A SECOND, SEPARATE HOLE IN THE SAME AREA: sibling item `65cuw0` hit the SAME combined-red refusal in the same run with `integration_gate_answer` equal to `null`, meaning it was never asked at all. So the ask is not reliably reached even when the conditions that triggered it for `ld8lb3` hold. Whatever gates the ask must be identified, because an escape hatch that opens for one item and not its neighbour is not a safety net.
- Scope: Give the recorded gate answer a channel to the post-merge revalidation gate, so failing ids the agent ATTRIBUTED AWAY with a usable answer do not drive a post-merge refusal, and determine and fix why the ask is reached for some refused items and not others. EXCLUDES the baseline-subtraction fix (sibling plan `tgyfs2`, backlog `fuk1mr`), which handles ids that were ALREADY red; this plan handles ids no baseline can catch (a failure that landed on main mid-turn, a flake, an order-dependence). Adds no new refusal kind, no new status, and no new answer token.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_gate_answer_propagation.py
- Item-Dependencies: none
- Status: to-review
- Set: gateinert
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: n9na1c
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- From-Backlog: c74dm7

## Workflow history

- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `c74dm7`, inheriting its `Blocks-Release: next` gate. THE ITEM'S ORIGINAL DIAGNOSIS WAS WRONG AND THIS PLAN CORRECTS IT rather than inheriting it: the filing said a `not-mine` release "has no effect", and the attempt record disproves that (`finalized: True`, plan reached `executed/` on the lane, detail records the release). The true shape is two independent gates where the answer reaches only the first. The correction is recorded in the backlog item's own history and the item's priority was lowered high -> medium accordingly, because the primary cause of the stranded lanes is `fuk1mr` and this is the second line of defense rather than the trigger.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make one adjudication final. When an agent supplies a usable, recorded answer attributing a suite failure away from its own work, that answer must survive the merge rather than being re-decided by a later gate that cannot see it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the true mechanism before changing it

- [ ] E-01 Document the TWO-GATE path in one place in `runner_shared`, by symbol, stating which gate each of the four answers governs today and which it does not. This is a prerequisite rather than bookkeeping: the backlog item's original diagnosis was wrong precisely because this path was not written down anywhere, and the in-code comment at the answer-consequence block currently describes only gate 1 while reading as though it describes integration as a whole.
  - Depends on: none
  - Expected outcome: a comment block naming `integration_is_earned`/`integration.earned` as gate 1 and `make_integration_validation_runner` (via `integrate_lane_branch`) as gate 2, and stating that an answer reaches only the former today.
  - Execution state: pending
- [ ] E-02 Determine WHY `ld8lb3` was asked and `65cuw0` was not, from the two items' recorded state in the same run, and state the predicate that differs. Do not change behavior in this item; report the finding into the plan so E-04 fixes a known cause rather than a guessed one.
  - Depends on: none
  - Expected outcome: the exact condition gating the ask is named by symbol, with the differing field values for the two items pasted.
  - Execution state: pending

### Task group 2: the channel

- [ ] E-03 Carry the ATTRIBUTED-AWAY failing id set forward from the recorded gate answer onto the item, as data the post-merge gate can read. Reuse the answer record already persisted under `GATE_ANSWER_RECORD_KEY`; add no new injection and no second vocabulary for the ids.
  - Depends on: E-01
  - Expected outcome: after a usable `not-mine`, the item carries the attributed id set alongside the existing answer record, with every existing key unchanged.
  - Execution state: pending
- [ ] E-04 Consume that set in the post-merge revalidation verdict so a merged-tree red consisting ONLY of attributed-away ids passes, while any unattributed id still refuses. A `mine` or `needs-human` answer must NOT release anything, and an absent or unusable answer must leave today's behavior exactly as it is. Also fix the ask-reachability cause E-02 identified, so the hatch opens for every refused item and not only some.
  - Depends on: E-02, E-03
  - Expected outcome: replaying `ld8lb3`'s recorded answer and merged failing set yields an integration rather than `merge-refused`; adding one unattributed id yields a refusal; `65cuw0`'s conditions now reach the ask.
  - Execution state: pending

### Task group 3: the guard

- [ ] E-05 Add a regression file pinning the propagation and its limits, including anti-fail-open controls: `mine` releases nothing, `needs-human` releases nothing, an unusable answer releases nothing, and an absent answer preserves today's verdict. Drive the real functions rather than reimplementing the predicate.
  - Depends on: E-03, E-04
  - Expected outcome: the file is RED against pre-fix source and GREEN after; each control FAILS if the corresponding answer is ever made to release.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The four answers and their consequences are already defined in ONE comment block in `runner_shared` above `GATE_ANSWER_RECORD_KEY`, which states `not-mine -> RELEASE this attempt's integration.earned`. Read precisely, that line is TRUE and scoped to gate 1; it is the absence of any statement about gate 2 that misleads. E-01 must extend that block rather than write a competing description elsewhere.
- Only `not-mine` releases on the answer alone; `fixed` earns a suite RE-RUN and the re-run decides. This plan must preserve that asymmetry exactly, since collapsing `fixed` into an answer-only release would let a claim substitute for a measurement.
- `record_refusal` is the ONE refusal writer and `needs-human` already routes through it so the existing diagnostics block renders it. No new renderer or refusal code is needed here.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The release is NOT inert; the original filing was wrong | `attempts[0]["finalized"] == True`, detail ends "RELEASED by the agent's gate answer (not-mine)", plan reached `executed/` on lane commit `78891bde` |
| F-2 | Two independent gates adjudicate the same failure | gate 1 `integration_is_earned`/`integration.earned`; gate 2 `make_integration_validation_runner` via `integrate_lane_branch` |
| F-3 | The answer has no channel to gate 2 | the post-merge factory reads neither the answer record nor the baseline; its verdict comes solely from the merged-tree run |
| F-4 | The answer was well-founded | agent cited the introducing commit `894d7924`, proved the failure at base `301a1d8fbc15`, reproduced it with its own changes stashed out, and filed `p9ag41` |
| F-5 | The ask is not reliably reached | `65cuw0` refused identically in the same run with `integration_gate_answer: null` |
| F-6 | The final status contradicts the honored answer | `integration_released_by_answer: not-mine` on an item whose `status` is `merge-refused` |

## Proposed changes (ordered, validatable)

1. Write down the two-gate path by symbol, extending the existing answer-consequence block (E-01).
2. Identify the predicate that gated the ask for one item and not the other (E-02).
3. Carry the attributed-away id set onto the item from the existing answer record (E-03).
4. Consume it in the post-merge verdict, and fix ask-reachability (E-04).
5. Pin propagation plus four anti-fail-open controls (E-05).

## Deferred / out of scope (with reason)

- Baseline subtraction in the post-merge gate: sibling plan `tgyfs2` (backlog `fuk1mr`) owns it. The two are complementary and must not be merged into one change: a baseline covers ids that were already red, an answer covers ids attributed away for reasons no baseline records.
- `reattempt_deferred_integrations`' accepted-and-ignored `validation_runner_for` (backlog `iv4n2c`): a different inert-injection defect in the same area, latent today.
- Any change to the answer VOCABULARY, the question text, or `fixed`'s re-run semantics: this plan adds a channel for an existing answer and deliberately changes no adjudication rule.
- Making `mine` or `needs-human` releasable: explicitly forbidden, and pinned as controls in E-05. Those answers refuse by design.

## Scope check

- Over-scope: none. Two paths, one of them a new test file.
- Under-scope: if E-02 finds the ask is gated outside `runner_shared` (for example in a host driver), the fix for ask-reachability may need one host path added to `Scope-Paths`. That would be additive widening, declared before commit per the execution contract, and the executor must report it rather than silently editing an undeclared file.

## Required tests / validation

- `python3 -m pytest tests/test_gate_answer_propagation.py` GREEN after, and RED before, the before-run produced by reverting only `agent_workflows/runner_shared.py` while keeping the new tests.
- `python3 -m pytest` bare, count line pasted, no new failing node ids against a baseline taken in the same worktree before the change.
- A REPLAY of `ld8lb3`'s recorded answer plus merged failing set through the real post-merge factory, showing it integrates; and the same with one unattributed id added, showing it refuses.
- The four anti-fail-open controls each demonstrated FAILING when the corresponding answer is forced to release.

## Spec / documentation sync

No `.spec.md` amendment is expected: spec `25kzda` governs what the gate must record, and this plan changes which gate consults an existing record. If E-01's written-down two-gate path contradicts any spec sentence describing integration as a single adjudication, the executor must report that contradiction rather than silently amend the spec, and the amendment then becomes a declared spec edit with its reason stated here.

## Open questions

### OQ-01: Should the attributed-away set be the agent's named ids, or every id in the gate-1 failure set the answer covered?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED to the ids the ANSWER WAS ASKED ABOUT, i.e. the `failures` set carried into the question, and NOT a free-text set parsed from the agent's prose. The question already carries that set (`failures=getattr(suite_result, "failures", ()) or ()`), so the scope of the answer is exactly what the agent was shown, which is both auditable and impossible to widen by wording. Parsing ids out of prose would let an agent release a failure it was never asked about.

### OQ-02: If the post-merge run surfaces a failure that is attributed-away AND a new one, what happens?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: REFUSE, naming only the unattributed id(s). The presence of one legitimately attributed failure never licenses ignoring a genuine regression beside it, and the refusal message must not list the attributed ids as reasons, since that is what made the original refusals so hard to diagnose.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the new comment block pasted, plus a grep showing it names both `integration_is_earned` and `make_integration_validation_runner`, plus confirmation by quotation that the pre-existing `not-mine -> RELEASE ... integration.earned` line is preserved rather than rewritten.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the gating condition named by symbol, with the differing recorded field values for `ld8lb3` (asked) and `65cuw0` (not asked) pasted side by side from that run's `state.json`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: the item dict pasted after a usable `not-mine`, showing the attributed id set present AND the pre-existing answer record unchanged key-for-key.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: the real post-merge factory driven with `ld8lb3`'s recorded inputs, pasting `passed=True` and the reason naming the attributed id; the same with one unattributed id added, pasting `passed=False` and a reason naming ONLY that new id; and evidence that `65cuw0`'s recorded conditions now reach the ask.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the new test file's output pasted GREEN after and RED before, the bare suite count line, and each of the four controls (`mine`, `needs-human`, unusable, absent) shown FAILING when forced to release.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`. THE SPECIFIC HAZARD OF THIS PLAN is that it widens when an integration is ALLOWED, which is the fail-open direction. The four anti-fail-open controls in E-05 are therefore not optional, and an executor who cannot make all four fail against a forced release must report that rather than proceed.
