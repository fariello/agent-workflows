# IPD: Scaffold plans that pass the durable-carrier gate, refuse walkthroughs as carrier evidence, and carry the new pending rows

- Date: 2026-09-25
- Kind: child
- Concern: Every freshly scaffolded plan FAILS `check.ipd-uncarried-obligation` at error the moment it is written: `aw ipd scaffold` emits an example `OQ-01` with `Status: open` and a deferred section, neither with a carrier field, and nothing in authoring mentions carriers. Measured at HEAD: `aw check plans` (fail-closed in CI) reports 24 such findings across 37 rows in plans written since 2026-09-24. Separately, `Carrier-Evidence` accepts a walkthrough path, and walkthroughs are untracked, so a leftover obligation can be discharged into a file nothing reads (maintainer ruling 2026-09-25: refuse it).
- Scope: IN: (a) `ipd_authoring.build_skeleton` emits carrier-ready placeholders; (b) `evaluate_carrier_obligation` refuses `Carrier-Evidence` under `.aw/records/walkthroughs/`; (c) document both in the records READMEs; (d) give each of the 37 live rows a real carrier or answer. OUT: the 2,318 uncarried rows in executed plans, which the rule by design never reads.
- Scope-Paths: agent_workflows/ipd_authoring.py, agent_workflows/check_engine.py, .aw/system/workflows/assess/templates/ipd.md, .aw/system/workflows/assess/templates/orchestrator-ipd.md, .aw/records/plans/README.md, .aw/records/walkthroughs/README.md, tests/test_ipd_authoring.py, tests/test_check_engine.py, .aw/records/plans/pending/**
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- Set: carrierauth
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: vtkfq8
- From-Backlog: dtrect
- Blocks-Release: next

## Workflow history
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog dtrect, absorbing 3yr30q (walkthrough carrier rule, maintainer ruling 2026-09-25) and the live remainder of retired rtyapw (0 grandfathered rows remain; 37 new rows fail CI). Reproduced at HEAD: a fresh `aw ipd scaffold` plan yields `check.ipd-uncarried-obligation` error on OQ-01; `resolve_evidence_artifact` accepts a walkthrough path.

## Goal

A newly scaffolded plan passes the carrier gate once its placeholders are filled, CI's `aw check plans` is green again, and an obligation can never be discharged into an untracked walkthrough.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: scaffold

- [ ] E-01 In `ipd_authoring.build_skeleton`, emit the example open question with a `- Carrier-Declined: TODO reason, or replace with - Carrier: <id6>` subfield, and emit the deferred section's placeholder as a bullet carrying the same carrier placeholder. Add both placeholder strings to `_AUTHORING_PLACEHOLDERS` so an unfilled plan still reads as a stub. Regenerate the two IPD templates so `tests/test_ipd_templates.py` stays byte-equal.
  - Depends on: none
  - Expected outcome: a fresh scaffold shows authors where a carrier goes; the placeholder text is flagged as unfinished.
  - Execution state: pending

- [ ] E-02 Test in `tests/test_ipd_authoring.py`: scaffold a plan into a temp repo, replace only the two carrier placeholders with a declined reason, and assert `check_engine.check_durable_carrier` returns no findings for it; assert the untouched scaffold still counts as unfinished via `authoring_placeholders_resolved`.
  - Depends on: E-01
  - Expected outcome: test passes; the carrier assertion fails against the pre-change skeleton.
  - Execution state: pending

### Task group 2: walkthrough refusal

- [ ] E-03 In `check_engine.evaluate_carrier_obligation`, refuse a `Carrier-Evidence` path under `.aw/records/walkthroughs/` with a message saying a walkthrough is not tracked and naming the three accepted fixes. Leave `resolve_evidence_artifact` itself unchanged, because backlog close evidence has different rules.
  - Depends on: none
  - Expected outcome: a walkthrough can no longer discharge a plan obligation; other evidence paths are unaffected.
  - Execution state: pending

- [ ] E-04 Test in `tests/test_check_engine.py` for both E-03 cases, and document the rule in `.aw/records/plans/README.md` (next to the carrier fields) and `.aw/records/walkthroughs/README.md`: a walkthrough is never a carrier; put the leftover work in a backlog item or plan.
  - Depends on: E-03
  - Expected outcome: tests pass; the walkthrough case fails against the pre-change check.
  - Execution state: pending

### Task group 3: live rows

- [ ] E-05 For each of the 24 pending plans `aw check plans` flags, give every flagged row a real carrier: an existing backlog item or plan id6 (`- Carrier:`), cited evidence (`- Carrier-Evidence:`), or a reasoned `- Carrier-Declined:`. Do not change any question's answer or Status to get past the check: an OPEN question stays open with a carrier naming who owns it. Plans in active review or owned by another session: edit only the carrier subfield and say so in the history line.
  - Depends on: E-03
  - Expected outcome: `aw check plans` reports zero `check.ipd-uncarried-obligation`.
  - Execution state: pending

- [ ] E-06 Run the bare suite and `python3 -m agent_workflows check all --agent`.
  - Depends on: E-02, E-04, E-05
  - Expected outcome: suite green; no carrier findings.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Carrier vocabulary: `ipd_schema.CARRIER_FIELD` / `CARRIER_EVIDENCE_FIELD` / `CARRIER_DECLINED_FIELD`; the one evaluator is `check_engine.evaluate_carrier_obligation`, shared by `aw check` and `aw ipd lint --phase pre-transition`.
- The IPD templates are asserted byte-equal to `build_skeleton` (`tests/test_ipd_templates.py`), so a skeleton change regenerates both templates.
- A plan may be edited by another session concurrently (AGENTS.md, Shared checkout); only the carrier subfield is touched on plans this plan does not own.

## Findings

All measured at HEAD `0c2e7970` unless stated.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ipd_authoring.build_skeleton` | A fresh scaffold fails the carrier gate at error on its own example OQ-01. | scratch repo: `check_durable_carrier` -> `error 1 obligation(s) name no durable carrier: OQ-01` |
| F-2 | HIGH | CI | `aw check plans` is fail-closed in CI and exits 1: 24 findings, 37 rows (23 questions, 14 deferred rows), all in plans dated 2026-09-24 onward. | `check plans --json` at HEAD |
| F-3 | MED | `evaluate_carrier_obligation` | `Carrier-Evidence` accepts a walkthrough, which nothing tracks. | `resolve_evidence_artifact(root, '.aw/records/walkthroughs/...')` -> True |
| F-4 | INFO | executed plans | 2,318 uncarried rows sit in executed/superseded plans; the rule never reads them by design. | measured over non-pending plans |

## Proposed changes (ordered, validatable)

1. E-01: carrier-ready scaffold placeholders.
2. E-02: scaffold-to-gate test.
3. E-03: walkthroughs are never carrier evidence.
4. E-04: test and document the walkthrough rule.
5. E-05: carry the 37 live rows.
6. E-06: bare suite and check all.

## Deferred / out of scope (with reason)

- The 2,318 uncarried rows in executed and superseded plans. The rule deliberately checks only pending plans, and executed plans are not edited in place (AGENTS.md).
  - Carrier-Declined: terminal plans are history; rewriting them would change the record, and the rule never reads them.
- A verb that adds a carrier to an existing row (`aw ipd carrier ...`), one of dtrect's candidate shapes.
  - Carrier-Declined: the scaffold placeholder plus the gate's own fix message cover the discoverability gap dtrect describes; a verb can follow if hand edits prove error-prone.

## Scope check

- Over-scope: E-05 edits other plans' carrier subfields; declared as `.aw/records/plans/pending/**` because CI is red on exactly those rows.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest tests/test_ipd_authoring.py tests/test_ipd_templates.py tests/test_check_engine.py -o addopts="" -q` plus the reverts in V-02 and V-04.
- `python3 -m agent_workflows check plans --agent` before and after.
- Bare `python3 -m pytest`.

## Spec / documentation sync

The IPD structure spec (`ipd-structure-and-linting`) is not changed: carriers are already specified there by `rnkqrc`. The two records READMEs gain the walkthrough rule (E-04), because that is where authors look for carrier fields.

## Open questions

### OQ-01: Should the scaffold's example question be emitted `resolved` instead of carrying a placeholder?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No, resolved on the ruled intent: the placeholder teaches the author where the carrier goes, while a pre-resolved example teaches nothing and hides a real open question behind a fake answer.

### OQ-02: Should walkthroughs be refused everywhere evidence is accepted (for example backlog close evidence)?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: No, resolved by the maintainer's 2026-09-25 ruling, which was about plan obligations: a closed backlog item citing a walkthrough still has its own record, so only the plan-obligation path is changed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new skeleton's OQ and deferred sections; paste `python3 -m pytest tests/test_ipd_templates.py -o addopts="" -q` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the test passing; revert E-01's skeleton change IN THE WORKTREE and paste it FAILING; restore.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the diff; paste `evaluate_carrier_obligation` driven on a row citing a walkthrough (refused) and one citing an executed plan (satisfied).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the tests passing and the revert-FAILING run; paste the two README diffs.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m agent_workflows check plans --agent` before (24 findings) and after (0 of that rule), and a list of plan id6 -> rows carried -> carrier chosen.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `check all` findings count, then paste the final summary line of a BARE `python3 -m pytest` (no added flags) showing 0 failed, and name any failure as pre-existing (with its node id and evidence it fails at the base commit) or new.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: three changes share one cause: authors cannot see or satisfy the carrier gate; each group is independently verifiable.

This plan is `to-review` and requires explicit human approval before execution.

Execution contract: commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). Justify any other path you must touch at finalize with `--scope-reason`. Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line; never claim a pass you did not run. Every `V-*` demands pasted, observed evidence and may not be ticked from its `E-*` checkmark.

When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to `executed/` through `aw ipd finalize`, never with a raw `git mv`. Then set the source backlog item(s) `done` with `--evidence` citing the executed plan.
