# IPD: Verify the hostdedup Set against all six completion criteria

- Date: 2026-09-21
- Kind: child
- Concern: The `hostdedup` Set's six-criterion acceptance check is owned by nobody who will run it. It sits on the Order-0 orchestrator `a5wdne` as that plan's only `E-*` item, and the runner RETIRES an orchestrator once every child is `executed` while deliberately SKIPPING the pre-transition E/V checkpoint. THE PARENT ALREADY KNOWS THIS AND SAYS SO IN ITS OWN ITEM TEXT: "if the runner retires this Set, this item is marked complete WITHOUT being performed, so the criteria that only E-01 checks (the cross-Set fork count and the two Order-03 durability properties) are verified by nobody. That is a known limitation of orchestrator retirement, not something this plan can fix." IT IS FIXABLE, and this is the fix: a child that owns the verification gets an agent turn. MEASURED 2026-09-22 in run `run-20260922T003414Z-1020752`, where the orchestrator coverage probe refused a 34-set launch naming `a5wdne` among five uncovered parents (`events.jsonl`, event `orchestrator-probe-gate`).
- Scope: Perform the Set-level acceptance check `a5wdne` E-01 describes, against all SIX completion criteria, and record its evidence. IN: the fork-count measurement using the COMMITTED scanner Order 01 produces; the coupling-guard check; the third-host execution and attribution check; the pre-cutover attribution check; the research immortalization check; and a bare green suite. OUT: any lifting, unifying, guard-rewriting or host-adding work (Orders 01/02/03 own those), and any re-performance of a child's own validation - this plan READS recorded evidence and measures the COMBINED result.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: executed:li44r9, executed:nmlx47, executed:xdvglg
- Status: to-review
- Set: hostdedup
- Order: 4
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 04vf1h

## Workflow history

- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.
- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the orchestrator coverage gate refused run `run-20260922T003414Z-1020752`, naming `a5wdne` as carrying work no child covers. The parent's E-01 had ALREADY RECORDED this exact hazard as "a known limitation of orchestrator retirement, not something this plan can fix"; this child is what makes it fixable. Content is lifted from the parent's item and its six criteria rather than invented, so the obligation is unchanged and only its owner moves; the parent's checklist stays in place.

## Goal

Make the `hostdedup` Set's completion claim real. The parent specifies six criteria and correctly warns
that retirement would tick them unperformed; three of them (the cross-Set fork count and the two Order-03
durability properties) are checked by NO child V-item, so without this plan they are verified by nobody.
After this executes, "the fork is collapsed and the seam holds" rests on a measurement rather than on a
checkbox the runner filled in.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set-level acceptance, on the criteria no child owns

- [ ] E-01 MEASURE THE FORK COUNT WITH THE COMMITTED SCANNER, against the 34-symbol baseline, and state the scanner's metric. USE ORDER 01's COMMITTED SCANNER AND NOTHING ELSE: the parent's own PR-006 records that "the same AST scan that produced the baseline" DOES NOT EXIST IN-TREE - the authoring scan was ad hoc and is not reproducible - which is why Order 01 must commit one and why this criterion must be measured with THAT. THE SYMBOL COUNT IS THE GATE (34 -> the five large functions alone); line figures are indicative only, per the parent's Goal, so do not report a line delta as if it were the criterion. If the committed scanner is absent when this runs, that is an upstream failure to REPORT, not a licence to re-improvise a scan whose numbers nobody can reproduce.
  - Depends on: none
  - Expected outcome: pasted scanner invocation and output with its metric stated, showing the before/after symbol counts; plus the scanner's own path in-tree, proving it is committed rather than ad hoc.
  - Execution state: pending

- [ ] E-02 VERIFY THE COUPLING GUARD REJECTS THE COUPLING RATHER THAN ONE SPELLING, and prove the guard is not vacuous. Two halves: confirm no runner imports the other runner, and confirm the guard FAILS against a reintroduction. THE VACUITY IS MEASURED, NOT HYPOTHETICAL: the parent records that 9 imports of the form `from agent_workflows.oc_runipd import` existed while `test_review_findings_cascade.py` asserted only `assertNotIn("import oc_runipd", agy_src)` and PASSED. So a green guard proves nothing by itself; demonstrate falsifiability by reintroducing a coupling in a scratch copy and showing the guard rejects it.
  - Depends on: E-01
  - Expected outcome: pasted guard output green on the real tree, PLUS pasted output of the same guard FAILING against a deliberately re-coupled scratch copy, naming the assertion that fires.
  - Execution state: pending

- [ ] E-03 VERIFY THE THREE REMAINING CRITERIA AND CLOSE THE SET, each with its own evidence: (a) a third host completes a real IPD execution with NO runner module of its own and attributes to that host rather than `unknown`; (b) a PRE-CUTOVER run record still attributes correctly, per the maintainer's host-id ruling; (c) the measured host contract is immortalized under `.aw/records/research/` so the codex/claude/hermes work starts from it. Then (d) paste a bare `python3 -m pytest`. Items (a) and (b) are the two Order-03 durability properties the parent names as checked by no child V-item, which is precisely why they are here; read Order 03's recorded evidence for them and REPORT rather than compensate if it is absent.
  - Depends on: E-02
  - Expected outcome: one evidence block per property (a)-(d), with the third-host run id and its recorded attribution quoted, the pre-cutover record named, the research path named, and the suite summary line pasted.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and the remedy for a parent carrying uncovered work is to ADD A CHILD, never to delete the parent's items: that checklist is what makes a hand-run `execute <setid>` complete when no runner is involved (`AGENTS.md`). This plan adds coverage and changes nothing on `a5wdne` except its child table.
- THE RETIREMENT HAZARD IS DOCUMENTED IN THE PARENT ITSELF, which is unusual and worth preserving: `a5wdne` E-01 names it and calls it unfixable from there. Leave that text in place; it is the evidence for why this child exists.
- SYMBOL COUNTS OVER LINE COUNTS in this Set, stated by the parent's Goal: the symbol figures reproduced exactly at review while the line figures did not, so the criteria are written against symbols.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `run-20260922T003414Z-1020752/events.jsonl`, event `orchestrator-probe-gate` | The coverage probe refused a 34-set launch naming `a5wdne` among five uncovered parents. Without this child the six-criterion check is performed by nobody and reported complete. |
| F-02 | HIGH | `a5wdne` E-01, quoted | The parent states that three criteria - the cross-Set fork count and the two Order-03 durability properties - are checked by NO child V-item, and that retirement would mark them complete unperformed. Those three are the core of this plan. |
| F-03 | HIGH | `a5wdne` PR-006, quoted | The reproducible scanner the fork-count criterion needs DID NOT EXIST in-tree at authoring; Order 01 must commit one. So E-01 must consume THAT scanner and must refuse to re-improvise, or the headline number becomes unreproducible again. |
| F-04 | MEDIUM | `a5wdne` completion criteria, quoted | The coupling guard was measured VACUOUS (9 real couplings coexisted with a passing assertion). A green guard is therefore not evidence; E-02 requires a falsifiability demonstration. |

## Proposed changes (ordered, validatable)

1. Measure the fork count with Order 01's committed scanner, stating its metric (E-01).
2. Verify the coupling guard is both green and falsifiable (E-02).
3. Verify the third-host, pre-cutover, and research criteria, then paste a bare green suite (E-03).

## Deferred / out of scope (with reason)

- ALL LIFTING, UNIFYING, GUARD-AUTHORING AND HOST-ADDING WORK. Orders 01, 02 and 03 own those; this plan
  measures their combined effect, which is why `Scope-Paths` names only records and no product code.
- COMMITTING THE SCANNER. That is Order 01's E-01 deliverable. If it is missing, E-01 here REPORTS the
  upstream gap rather than filling it, because a scanner authored by the verifier is not an independent
  measurement.
- RE-PERFORMING ANY CHILD'S VALIDATION. E-03 reads Order 03's recorded evidence for the two durability
  properties; compensating for absent evidence would hide an upstream validation failure.

## Scope check

- Over-scope: none.
- Under-scope: none. The parent carries exactly one `E-*` item enumerating six criteria; E-01 covers the
  first, E-02 the second, and E-03 the remaining four including the suite.

## Required tests / validation

No product code changes, so no new unit test. The validation IS the pasted measurement set, plus a bare
`python3 -m pytest` in E-03 to show the tree is green at the moment the Set is declared complete.

## Spec / documentation sync

N/A. This plan changes no contract: it performs a verification the parent already specified. The only
structural edit is the child-table row on `a5wdne`, which is what the coverage gate reads.

## Open questions

### OQ-01: If Order 01's committed scanner is absent when this runs, does this plan improvise one or refuse?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REFUSE AND REPORT, resolved from the parent's own PR-006 rather than deferred. That finding exists precisely because the authoring scan was ad hoc and unreproducible, so the criterion was rewritten to demand a committed scanner. A verifier that authors its own scanner to unblock itself reproduces the original defect (a headline number nobody else can re-derive) AND destroys the independence that makes the measurement worth anything. E-01's expected outcome therefore requires the scanner's in-tree path, which is what makes an improvised scan detectable rather than silent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the scanner's committed in-tree path, its invocation, its stated metric, and its output showing the symbol count fallen from 34 to the five large functions alone. An execution that reports a LINE delta as the criterion, or that runs a scan with no committed path, FAILS this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: two pasted runs of the coupling guard - green against the real tree, and FAILING against a scratch copy with a coupling reintroduced, naming the assertion that fires. A single green run does NOT satisfy this item; F-04 records that a vacuous guard already passed here once while 9 real couplings existed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: four labelled blocks. (a) the third host's run id plus its recorded attribution, showing the host name and not `unknown`; (b) the pre-cutover run record named, with its attribution quoted; (c) the `.aw/records/research/` path holding the host contract; (d) the bare `python3 -m pytest` summary line. If (a) or (b) rests on absent Order-03 evidence, the required evidence is the STATEMENT of that gap, which satisfies this item while failing the Set.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE. This plan's entire product is a verification, so there is nothing
to show but real output. Two specific temptations are named because both have already occurred in this
Set's history: improvising a fork-count scan when the committed one is missing (which is how the original
unreproducible number arose), and accepting a green coupling guard as proof when that guard was measured
vacuous while nine real couplings existed. In both cases the correct result is a named refusal or a
falsifiability demonstration, never a substitute measurement.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Change NO product code and author NO scanner. If the
work genuinely requires a path outside the fence, make the edit and justify it, since `aw ipd finalize`
refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-
unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.
