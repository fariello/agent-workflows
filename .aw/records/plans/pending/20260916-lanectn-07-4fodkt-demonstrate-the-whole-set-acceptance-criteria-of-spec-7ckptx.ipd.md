# IPD: Demonstrate the whole-Set acceptance criteria of spec 7ckptx and write the verification record

- Date: 2026-09-16
- Kind: child
- Concern: The `lanectn` Set's whole-Set verification is parked on its ORCHESTRATOR (`h0zljh` E-02): demonstrate every live acceptance criterion of spec `7ckptx` Section 4 with pasted command evidence and write a verification record. All six of that orchestrator's children are already `executed`, so the runner will RETIRE it on sight, and retirement deliberately SKIPS the pre-transition E/V checkpoint on the premise that a parent's items are performed by nobody. The 31 live criteria would therefore be marked demonstrated having never been run, and the walkthrough would never be written, while the parent's own stated outcome ("any FAILING criterion blocks the Set and this orchestrator stays non-terminal") would be structurally unreachable.
- Scope: Perform the verification `h0zljh` E-02 describes, as a child that an agent actually executes: demonstrate each LIVE criterion of `7ckptx` Section 4 with pasted evidence, record any that cannot be demonstrated as UNVERIFIED with its reason, and write the verification record to `.aw/records/walkthroughs/`. Authors NO product code. Does NOT set the spec's status.
- Scope-Paths: .aw/records/walkthroughs, .aw/records/plans/pending/20260916-lanectn-07-4fodkt-demonstrate-the-whole-set-acceptance-criteria-of-spec-7ckptx.ipd.md
- Item-Dependencies: executed:604wra, executed:y5od1h, executed:xdr83v, executed:lhmrhx, executed:nna8yz, executed:cqx5v7
- From-Spec: 7ckptx
- From-Backlog: vqv9im
- Blocks-Release: next
- Status: to-review
- Set: lanectn
- Order: 7
- Highest E allocated: 04
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 4fodkt

## Workflow history

- 2026-09-16 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored to carry `h0zljh` E-02, the whole-Set verification, which is work that exists ONLY on the Order-0 orchestrator and is covered by no child. Written per the `AGENTS.md` rule that a step found on a parent and covered by no child gets a CHILD rather than deletion. TWO MEASUREMENTS TAKEN AT AUTHORING, both reproducible: (1) spec `7ckptx` Section 4 defines 36 `A*` criteria of which exactly 5 are marked WITHDRAWN in the spec text (`A7b`, `A7b-1`, `A7b-2`, `A7b-3`, `A7c`, all withdrawn by `R3.3a`), leaving 31 LIVE; (2) the enumeration in `h0zljh` E-02 covers 30 of those 31 and OMITS `A14b`, which is live and load-bearing. That omission is exactly the failure mode E-02's own text warns about ("an enumeration copied from an earlier draft is how a withdrawn criterion gets demonstrated or a live one gets skipped"), so this plan re-derives the list from the spec at execution time rather than trusting either enumeration.
- 2026-09-16 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Actually demonstrate that the `lanectn` Set delivered what spec `7ckptx` requires, and leave a durable record
that says which criteria passed, which failed, and which could not be demonstrated and why.

This exists because the verification is currently unreachable rather than merely unfinished. `AGENTS.md`
states the mechanism plainly: the runner retires an orchestrator once every child reads `executed` and
SKIPS the pre-transition checkpoint, so "work parked on the parent is marked complete having never been
performed OR verified." `h0zljh`'s six children are all `executed` today, so its E-02 is in exactly that
position.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the criterion list from the spec, not from a copy

- [ ] E-01 RE-DERIVE THE LIVE CRITERION LIST FROM THE SPEC AT EXECUTION HEAD, and refuse to proceed on a copied enumeration. Read `## 4. Testable acceptance criteria` in `.aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md` and partition every `A*` id into LIVE and WITHDRAWN by whether its own text says `WITHDRAWN`. Compare the result against BOTH prior enumerations and report every difference: (a) the authoring-time measurement recorded in this plan's history (36 total, 5 withdrawn, 31 live), and (b) the list written into `h0zljh` E-02, which omits `A14b`. DO NOT silently adopt either. If the spec has changed since authoring, the spec wins and the difference is reported.
  - Depends on: none
  - Expected outcome: a pasted table of every `A*` id with LIVE or WITHDRAWN and the requirement ids it cites, the totals, and an explicit statement of each difference from the two prior enumerations (or "none").
  - Execution state: pending

### Task group 2: demonstrate, and be honest about what cannot be demonstrated

- [ ] E-02 DEMONSTRATE EVERY LIVE CRITERION WITH PASTED COMMAND EVIDENCE, one row per criterion, in the order the spec lists them. The spec's own bar governs and is quoted here so it is not softened at execution time: "Each is falsifiable and names the requirement it proves. 'A test exists' is not evidence; the pasted result of running it is." So a criterion is satisfied by the pasted OUTPUT of a command, never by citing a test's name or asserting that a suite is green. Where a criterion demands a NEGATIVE control (`A1` requires that rewording the exception still fails the check; `A14b` requires that a test achieving the isolated behavior by making the rule report CLEAN FAILS the criterion), run the control and paste its result too, because a criterion whose negative control is skipped has not been demonstrated. Any criterion that cannot be demonstrated MUST be recorded UNVERIFIED with its specific reason; NEVER dropped, and never reported as passing.
  - Depends on: E-01
  - Expected outcome: every live criterion carries either pasted passing evidence, a pasted FAILING result, or an explicit UNVERIFIED verdict with a reason; the counts of each are stated; no criterion is absent from the enumeration.
  - Execution state: pending

- [ ] E-03 WRITE THE VERIFICATION RECORD to `.aw/records/walkthroughs/` as a `...-walkthrough.md`, carrying E-02's per-criterion result table, the E-01 list derivation with its differences, the execution HEAD, and a plainly-labeled summary of PASSED / FAILED / UNVERIFIED counts. State the honest limits in the record itself rather than only here: which criteria rest on a synthetic fixture rather than a real run, and which were demonstrated by a single observation rather than repeated. This is the deliverable `h0zljh` E-02 promised and could not produce.
  - Depends on: E-02
  - Expected outcome: one committed walkthrough file whose summary counts reconcile exactly with E-02's table, containing no criterion marked passed without pasted evidence.
  - Execution state: pending

### Task group 3: report the Set's true state without asserting a verdict that is not this plan's

- [ ] E-04 REPORT, DO NOT SET, whether spec `7ckptx` has reached `implemented`, and state the evidence either way. An agent may NOT set a spec `implemented`; that transition needs cited evidence and is the maintainer's. Report likewise on backlog `vqv9im`: state whether the merge evidence supports closing it, and leave the transition alone. If ANY live criterion is FAILED or UNVERIFIED, say explicitly that the Set is not demonstrably complete and name the criteria responsible, so the parent's retirement is a decision taken with the facts rather than a default.
  - Depends on: E-03
  - Expected outcome: a written report naming the spec's and the backlog item's evidenced state, with no status transition performed on either, and an explicit demonstrably-complete or not-demonstrably-complete verdict on the Set with the responsible criteria named.
  - Execution state: pending

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN (`AGENTS.md`). The distinction is not "has no checklist": a parent SHOULD list its children, because that is what makes a Set execute completely when an agent is told "execute this Set" with no runner. What must not be there is work covered by no child. `h0zljh` E-01 (sequence the six children) and E-03 (reconcile records, correctly refusing to set the spec itself) are legitimate orchestration. E-02 is not, and this plan is the prescribed remedy: "if you find yourself writing a STEP on the Order-0 plan that no child covers, do NOT delete it: ADD A CHILD for it."
- THE RUNNER SKIPS AN ORCHESTRATOR'S CHECKPOINT BY DESIGN, so this is a live defect and not a tidiness point. Retirement is gated on every child being `executed` and nothing else, and it spends no agent turn.
- A SPEC STATUS OF `implemented` IS NOT AN AGENT'S TO SET (`AGENTS.md`, `aw specs`), which is why E-04 reports rather than transitions. `h0zljh` E-03 already had this right and its wording is preserved.
- THE SET'S SIX CHILDREN ARE ALL `executed`: `cqx5v7` (01), `nna8yz` (02), `lhmrhx` (03), `y5od1h` (04), `xdr83v` (05), `604wra` (06). This plan declares all six as `Item-Dependencies` so it cannot be dispatched before the work it verifies exists.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `h0zljh` E-02 | THE WHOLE-SET VERIFICATION IS STRUCTURALLY UNREACHABLE, not merely pending. All six children are `executed`, so the runner retires the parent on sight and skips the pre-transition E/V checkpoint. E-02's 31 criteria and its walkthrough deliverable would be marked complete unperformed, and its own stated outcome ("any FAILING criterion blocks the Set and this orchestrator stays non-terminal") cannot fire. | `AGENTS.md` on orchestrator retirement; all six children present in `.aw/records/plans/executed/` |
| F2 | MEDIUM | `h0zljh` E-02 vs spec `7ckptx` Section 4 | THE PARENT'S ENUMERATION OMITS ONE LIVE CRITERION. Measured at authoring: the spec defines 36 `A*` ids, 5 marked WITHDRAWN (`A7b`, `A7b-1`, `A7b-2`, `A7b-3`, `A7c`, all by `R3.3a`), leaving 31 live. E-02's list ("A1 through A20 plus A5b, A5c, A8b, A8c, A10b, A10c, A10d, A10e, A12b, A15b") covers 30 and omits `A14b`, which cites `R5.4`/`R6.1` and carries an explicit anti-cheat clause. This is precisely what E-02's own text warns about. | programmatic partition of the spec's `A*` ids; the `h0zljh` E-02 line |
| F3 | LOW | spec `7ckptx` Section 4 | THE WITHDRAWALS ARE REAL AND E-02 IS RIGHT ABOUT THEM, recorded so a later reader does not re-add them. All five withdrawn ids say so in their own spec text and name `R3.3a` as the withdrawing requirement, so demonstrating them would assert behavior the spec now forbids. | `A7b` at spec `:518`, `A7b-1` `:524`, `A7b-2` `:529`, `A7b-3` `:533`, `A7c` `:537` |

## Proposed changes (ordered, validatable)

1. Re-derive the live criterion list from the spec, reporting every difference from the two prior enumerations (E-01).
2. Demonstrate each live criterion with pasted evidence, including negative controls, recording any UNVERIFIED with its reason (E-02).
3. Write the verification record to `.aw/records/walkthroughs/` with reconciling counts and stated limits (E-03).
4. Report the evidenced state of spec `7ckptx` and backlog `vqv9im` without transitioning either, and state whether the Set is demonstrably complete (E-04).

## Deferred / out of scope (with reason)

- SETTING spec `7ckptx` to `implemented`. An agent may not; it needs cited evidence and is the maintainer's transition. E-04 reports the evidence instead.
- SETTING backlog `vqv9im` to `done`. Same reason. Note `h0zljh` E-03 instructs the parent to set it; that instruction is left with the parent rather than moved here, because this plan's job is the verification E-02 promised, and a records transition performed from a verification child would spread the parent's bookkeeping across two artifacts.
- AMENDING `h0zljh` E-02 or the orchestrator's child table. Deliberately untouched: this plan does not edit another artifact to make itself look complete, and the maintainer may prefer to leave the parent's item as the historical record of what was intended. Whether to mark E-02 as delegated here is the maintainer's call, recorded as OQ-01.
- AUTHORING ANY PRODUCT CODE. This is a verification plan. If a criterion FAILS, the remedy is a new corrective plan, not a fix smuggled into the verification that would then be verifying itself.
- FIXING the `A14b` omission in the parent's text. E-01 reports the difference; editing the parent is out of scope for the same reason as above.

## Scope check

- Over-scope: none. Every item is contained in `h0zljh` E-02's own description apart from E-01's list re-derivation, which E-02's text explicitly demands ("Re-read Section 4 of the spec at execution time rather than trusting this list").
- Under-scope: none for the verification itself. This plan deliberately does NOT carry `h0zljh` E-01 (sequencing the children, already done) or E-03 (records reconciliation, legitimate orchestration that stays with the parent).

## Required tests / validation

1. No product code changes, so the suite is a REGRESSION FENCE rather than the subject: run `python3 -m pytest` bare and paste the summary line, confirming it is unchanged from the pre-execution baseline (also pasted).
2. `aw ipd lint --phase pre-transition` on this plan reports conforming.
3. `aw sanitize --agent` clean, which matters more than usual here: a verification record pasting real command output is a likely carrier of absolute local paths.
4. The walkthrough's PASSED / FAILED / UNVERIFIED counts reconcile exactly with E-02's per-criterion table, checked by re-counting the table rather than trusting the summary.

## Spec / documentation sync

Spec `7ckptx` is READ, never amended, by this plan: it is the authority the criteria come from, and a
verification that edited its own acceptance criteria would be worthless. `- Scope-Paths:` therefore
declares NO `.spec.md` file, and if execution finds a criterion that is wrong rather than unmet, that is a
finding for a separate spec amendment carrying its own review, not an edit made in passing here.

The walkthrough written by E-03 is the documentation deliverable.

## Open questions

### OQ-01: Should `h0zljh` E-02 be marked as delegated to this plan, or left as written?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking, because this plan is executable either way and the verification gets done either way. The question is only what the parent's text should say afterwards. Leaving it as written keeps the historical record of what was intended but means a reader of `h0zljh` alone still sees an item that its retirement will never perform. Marking it delegated is more honest but edits an `approved` plan's checklist, which is a change to an artifact this plan does not own. Recorded rather than acted on, per the convention that a plan should not edit another artifact to make its own scope look complete. The maintainer may also reasonably decide the parent should not retire until this child is `executed`, which its `Item-Dependencies` do not currently express in that direction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted LIVE / WITHDRAWN partition of every `A*` id in spec `7ckptx` Section 4 produced at execution HEAD, with totals, and an explicit per-difference statement against BOTH prior enumerations (the 36/5/31 authoring measurement and `h0zljh` E-02's 30-item list, whose omission of `A14b` must be either confirmed or shown to have changed). A list asserted without the derivation shown does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the per-criterion table with, for EVERY live criterion, either pasted command output or an explicit UNVERIFIED verdict with a reason. PLUS the two negative controls demonstrated rather than described: `A1`'s reworded exception still failing the check, and `A14b`'s rule still classifying a dirty tracked tree as NOT CLEAN with an identical path list on both paths while only the isolated caller declines to refuse. PLUS an explicit count of PASSED, FAILED and UNVERIFIED, and an explicit statement that no live criterion is missing from the table.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the walkthrough's path and its summary block pasted, with the PASSED / FAILED / UNVERIFIED counts RE-COUNTED from the table rather than copied from the summary, and the two figures shown to agree. PLUS the stated-limits section quoted, naming which criteria rest on a synthetic fixture and which were single-observation. PLUS `aw sanitize --agent` output showing clean, since this file pastes real command output.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the report quoted, showing (a) the evidenced state of spec `7ckptx` with no transition performed, provable by pasting the spec's unchanged `- Status:` line before and after, (b) the same for backlog `vqv9im`, and (c) the explicit demonstrably-complete or not-demonstrably-complete verdict on the Set naming any responsible criteria. A report that recommends `implemented` without naming the criteria supporting it does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Resolve no open question by guessing: `OQ-01` is non-blocking and the maintainer's, so
execute without it and do not edit `h0zljh` to close it. SCOPE FENCE: this plan declares
`.aw/records/walkthroughs` and its own plan file; an out-of-scope edit must be made only if genuinely
required and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left
unmodified needs a `--scope-ack`. THE HARD-MUST HONESTY RULE, which is the whole point of this plan: paste
the ACTUAL command output for every criterion and never claim a demonstration not performed; a criterion
that cannot be demonstrated is recorded UNVERIFIED with its reason, and recording UNVERIFIED honestly is a
SUCCESSFUL outcome of this plan while a criterion silently marked passed is a failure of it. Commit
path-scoped (`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours: this repository is a shared checkout with
concurrent sessions. After the gate, move this plan to `.aw/records/plans/executed/` via
`aw ipd finalize`, and do not claim done until `aw ipd lint --phase pre-transition` conforms and every
`V-*` above carries real observed evidence.
