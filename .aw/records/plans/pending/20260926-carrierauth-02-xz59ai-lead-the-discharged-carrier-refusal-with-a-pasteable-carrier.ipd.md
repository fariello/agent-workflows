# IPD: Lead the discharged-carrier refusal with a pasteable Carrier-Evidence remedy instead of generic fixes

- Date: 2026-09-26
- Kind: child
- Concern: A CORRECT `- Carrier: <id6>` ROW BECOMES A GATE REFUSAL EXACTLY WHEN ITS CARRIER SUCCEEDS, AND THE REFUSAL OFFERS THE DISHONEST ESCAPE AS READILY AS THE HONEST ONE. `check_engine._resolve_carrier` returns `terminal` for any carrier whose every owner has a status in `_CARRIER_TERMINAL_STATUSES` (`executed`, `superseded`, `not-executed`, `done`, `parked`), and `check_engine.evaluate_carrier_obligation` then returns `legitimate=False, severity="error"` with the reason "carrier <id6> resolves only to a terminal/hidden artifact (<status>); nothing revisits it" and the SAME three generic `fixes` it gives an uncarried row: hand it off, cite `<in-tree artifact path>`, or `Carrier-Declined: <why this needs no carrier>`. Any Set whose later sibling declares `Item-Dependencies: executed:<earlier>` and names the earlier work as a carrier hits this BY CONSTRUCTION at `aw ipd lint --phase pre-transition` (backlog `gyw4gp`, worked case plan `n9na1c`). The executor already knows WHICH artifact discharged the obligation, because the carrier index holds its path, but the message does not say it, so the cheapest keystroke is `Carrier-Declined`, which records a shipped obligation as "needs no carrier". Measured at HEAD `f46b6775` on live carriers `fuk1mr` (done backlog) and `tgyfs2` (executed plan): both return the generic three fixes, and the path of neither appears in the message.
- Scope: IN: (a) when a `- Carrier:` id6 resolves `terminal` because its target is FINISHED (a `done` backlog item or an `executed` plan), put a terminal-specific remedy in the verdict's REASON (the only text `aw ipd lint` surfaces, see F-3) leading with a pasteable `- Carrier-Evidence: <repo-relative path of that artifact>` resolved from the carrier index, and a warning that `Carrier-Declined` is wrong when the work shipped; make the same remedy the verdict's first `fixes` entry so `aw check`'s `recovery` field carries it too; (b) keep the VERDICT unchanged, `legitimate=False` (OQ-01); (c) leave the `superseded`/`not-executed`/`parked` terminal cases on the generic remedy, since those are NOT evidence the work shipped (OQ-02); (d) document the remedy in `.aw/records/plans/README.md` in the carrier vocabulary section plan `vtkfq8` writes; (e) behavioral tests. OUT: treating a finished carrier as satisfied; a rewrite verb; `resolve_evidence_artifact`.
- Scope-Paths: agent_workflows/check_engine.py, .aw/records/plans/README.md, tests/test_check_engine.py
- Item-Dependencies: executed:vtkfq8
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: gyw4gp
- Set: carrierauth
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: xz59ai

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog gyw4gp (option 3 plus a targeted message, keeping the verdict). Re-measured at HEAD f46b6775: evaluate_carrier_obligation on Carrier fuk1mr (done) and tgyfs2 (executed) returns the generic three fixes with no artifact path. Ordered after vtkfq8, which edits evaluate_carrier_obligation and writes the plans README carrier section this plan extends.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

When a plan's carrier has been discharged by finished work, the pre-transition refusal tells the executor the exact `- Carrier-Evidence:` line to paste and warns off `Carrier-Declined`, so the honest remedy is the easiest one; the gate itself still refuses.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 RE-MEASURE AT THE EXECUTING HEAD, after `vtkfq8` has executed (it edits `evaluate_carrier_obligation`'s evidence branch, so read the function fresh). In `python3 -c`, build `check_engine.CarrierObligation("deferred", "deferred row 1", 1, {"Carrier": X})` for X in a live done backlog id6 and a live executed plan id6 (at authoring `fuk1mr` and `tgyfs2`; pick any current pair if those moved), call `evaluate_carrier_obligation(repo, ob)`, and paste `legitimate`, `severity`, `reason`, `fixes`. Also paste `_carrier_index(repo)[X]` for each, showing the `(record_type, status, path)` owner the new remedy will cite. Then run `aw ipd lint --phase pre-transition` on a scratch copy of a plan carrying such a row and paste the diagnostic line, confirming only the reason reaches the lint output.
  - Depends on: none
  - Expected outcome: both verdicts `False`/`error` with the "terminal/hidden artifact" reason and the three generic fixes; no path appears; the lint line shows the reason only.
  - Execution state: pending

### Task group 2: the remedy

- [ ] E-02 WRITE THE BEHAVIORAL TESTS FIRST in `tests/test_check_engine.py` (behavior only, no source-text or AST pins, per the 2026-09-26 test-policy ruling). Build a scratch repo in a `TemporaryDirectory` with `.aw/records/backlog/done/<...>-bk0001-....backlog.md` (`- Status: done`), `.aw/records/plans/executed/<...>-pl0001-....ipd.md` (`- Status: executed`), and a superseded plan `pl0002`; pass an explicit `carrier_index` built by `check_engine._carrier_index(repo)`. Cases: (1) `Carrier: bk0001` -> `legitimate` is False, `severity == "error"`, the reason contains the literal line `- Carrier-Evidence: .aw/records/backlog/done/<that filename>` and the word `Carrier-Declined` in a warning; `fixes[0]` contains the same Carrier-Evidence line; (2) `Carrier: pl0001` -> same shape with the executed plan's repo-relative path; (3) PASTING THE SUGGESTION WORKS: a row with `Carrier-Evidence: <the path from case 2>` returns `legitimate=True, path="SATISFIED"` (proves the suggestion is resolvable by the same predicate, including after `vtkfq8`'s walkthrough refusal); (4) `Carrier: pl0002` (superseded) -> still refused with the GENERIC fixes and no Carrier-Evidence suggestion; (5) a carrier with one live and one done owner -> `legitimate=True, path="HANDOFF"` unchanged; (6) end to end, `check_engine.evaluate_durable_carrier` on a plan text carrying the case-2 row returns one Drift whose `detail` contains the Carrier-Evidence line and whose `recovery` equals `fixes[0]`.
  - Depends on: E-01
  - Expected outcome: cases (1), (2) and (6) FAIL against the unchanged code; (3), (4), (5) PASS before and after.
  - Execution state: pending

- [ ] E-03 IMPLEMENT IN `check_engine`. Make `_resolve_carrier` (or a sibling helper it calls, so the one resolution stays in one place) also return, for a `terminal` verdict, the finished owners: those whose status is `done` (record type `backlog`) or `executed` (record type `plans`), with their paths made repo-relative against `repo_root` (the index stores absolute paths, F-2). In `evaluate_carrier_obligation`'s `raw_carrier` branch, when every good id6 failed and at least one is terminal-with-a-finished-owner, build the refusal as: the existing locator and "terminal/hidden" detail, then "this obligation was discharged by finished work; cite it instead of the carrier:" followed by one pasteable `- Carrier-Evidence: <relpath>` line per finished owner (first one first), then "do NOT use `Carrier-Declined` here: the work shipped, so declining it would record it as needing no carrier". Put the first Carrier-Evidence suggestion in `fixes[0]` ahead of the three generic fixes. Keep `legitimate=False` and `severity="error"`. Keep `_resolve_carrier`'s other callers, if `rg -n "_resolve_carrier\(" agent_workflows` shows any at execution, unchanged in behavior.
  - Depends on: E-02
  - Expected outcome: all six E-02 cases pass.
  - Execution state: pending

- [ ] E-04 CONFIRM THE TWO GATE SURFACES CARRY THE NEW TEXT. Re-run E-01's `aw ipd lint --phase pre-transition` on the scratch plan and `aw check plans --agent` on a scratch repo containing it, and paste both: the lint diagnostic (built from `d.detail` in `ipd_lint._merge_durable_carrier`) must show the Carrier-Evidence line, and the check record's `recovery` must be it. Then paste the suggested line into the scratch plan's row in place of `- Carrier:` and show `aw ipd lint --phase pre-transition` no longer reports `check.ipd-uncarried-obligation` for that row.
  - Depends on: E-03
  - Expected outcome: both surfaces show the pasteable line; pasting it clears the finding.
  - Execution state: pending

### Task group 3: docs and suite

- [ ] E-05 DOCUMENT THE REMEDY in `.aw/records/plans/README.md`, inside the carrier vocabulary section `vtkfq8` E-05 creates (read it first; if it does not exist because `vtkfq8` changed shape, add a short "Carriers" subsection after the execution-contract section and say so at finalize). Add: a carrier that becomes `done`/`executed` before your plan finishes turns the row into a refusal on purpose (a reader pointed at a closed item would think the work is still pending); the remedy is to replace `- Carrier:` with the `- Carrier-Evidence:` line the refusal prints, optionally with a `- Carrier-Note:` saying why; `Carrier-Declined` is for work that genuinely needs no carrier and is wrong for work that shipped. Name the ordered-Set pattern (a later sibling that depends on an earlier one) as the common way this arises. User-facing prose: no em or en dashes.
  - Depends on: E-03
  - Expected outcome: the README states the terminal-carrier remedy next to the carrier vocabulary.
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` before (at E-01) and after E-05, plus `python3 -m pytest tests/test_ipd_lint.py tests/test_check_engine.py -o addopts="" -q` (the carrier evaluator is reached from both `aw check` and `aw ipd lint`), and `python3 -m agent_workflows check plans --agent` on the real tree before and after.
  - Depends on: E-05
  - Expected outcome: the after-minus-before failing node set is empty; `check plans` reports the same findings count (the change alters messages, never verdicts).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The carrier predicate is one evaluator shared by both surfaces: `check_engine.evaluate_durable_carrier` is called by `check_durable_carrier` (`aw check`) and `ipd_lint._merge_durable_carrier` (`aw ipd lint --phase pre-transition`); per-row verdicts come from `evaluate_carrier_obligation`.
- `_CARRIER_TERMINAL_STATUSES` deliberately includes `executed` because "an executed plan classes `done` in `aw attention`, which is the hiding place"; this plan does NOT change that set.
- `_carrier_index` returns `id6 -> [(record_type, status, absolute path)]`, filtered to `_CARRIER_TARGET_TYPES = ("backlog", "plans")`.
- `Carrier-Evidence` resolves through the shared `resolve_evidence_artifact` (an existing in-tree path under `.aw/records/` or `.agents/`); `vtkfq8` adds a walkthrough refusal on top, which executed plans and done backlog items do not trip.
- Tests are run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `f46b6775` on 2026-09-26.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `evaluate_carrier_obligation` | A finished carrier gets the same three generic fixes as an uncarried row, with no path. | `Carrier: fuk1mr` -> `False error ... carrier fuk1mr resolves only to a terminal/hidden artifact (done); nothing revisits it`, fixes `('hand it off: ...', 'cite evidence it is already addressed: add `- Carrier-Evidence: <in-tree artifact path>`', 'decline it explicitly, with a reason: ...')`; `tgyfs2` (executed) identical shape |
| F-2 | INFO | `_carrier_index` | The artifact to cite is already known. | `fuk1mr -> [('backlog','done','<abs>/.aw/records/backlog/done/20260922-revalbase-01-fuk1mr-....backlog.md')]`, `tgyfs2 -> [('plans','executed','<abs>/.aw/records/plans/executed/20260922-revalbase-01-tgyfs2-....ipd.md')]` |
| F-3 | MEDIUM | `ipd_lint._merge_durable_carrier` | The pre-transition gate shows ONLY the drift detail (`Diagnostic(0, 1, d.rule, d.detail)`), and the detail is built from verdict REASONS; `fixes` reach only `aw check`'s `recovery` field. So a remedy placed only in `fixes` would be invisible at the gate where the executor meets it. | `evaluate_durable_carrier` builds `detail` from `v.reason` and `recovery=fixes[0]` |
| F-4 | INFO | backlog `gyw4gp` | The worked case's manual fix was exactly this line, which is proof it is the right remedy. | "replaced '- Carrier: fuk1mr' with '- Carrier-Evidence: <path to the executed tgyfs2 plan>' plus a '- Carrier-Note:'" |

## Proposed changes (ordered, validatable)

1. E-01 re-measures on the post-`vtkfq8` tree.
2. E-02 writes the behavioral tests, failing half first.
3. E-03 builds the terminal-specific remedy in the reason and `fixes[0]`.
4. E-04 confirms both gate surfaces and that pasting the line clears the finding.
5. E-05 documents the remedy in the plans README.
6. E-06 suite and live `check plans` before and after.

## Deferred / out of scope (with reason)

- Treating a `done`/`executed` carrier as SATISFIED (item option 1).
  - Carrier-Declined: rejected on repository evidence (OQ-01); a terminal carrier is not proof the obligation was finished, as the `x7wfyx` case measured.
- An `aw ipd` verb that rewrites a discharged carrier into cited evidence (item option 2).
  - Carrier-Declined: with the pasteable line in the refusal the manual edit is one copy-paste; a mutating verb that edits another field of a plan at the gate is more surface than the remaining cost justifies.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/ipd_lint.py` is deliberately NOT declared: it already forwards `d.detail`, which will carry the remedy (F-3).
- Scope-Paths justification: `check_engine.py` holds the predicate; the plans README holds the vocabulary section; `tests/test_check_engine.py` holds E-02.

## Required tests / validation

- `tests/test_check_engine.py`: six behavioral cases including paste-and-clear and the superseded negative; cases (1), (2), (6) shown FAILING before E-03.
- `python3 -m pytest tests/test_ipd_lint.py tests/test_check_engine.py -o addopts="" -q`.
- Bare `python3 -m pytest` and live `check plans --agent` before and after.

## Spec / documentation sync

- No `.spec.md` is edited: the carrier vocabulary is documented in no spec (plan `vtkfq8` F-9 measured zero hits), and this plan changes message text, not a verdict or contract.
- `.aw/records/plans/README.md` gains the terminal-carrier remedy (E-05).

## Open questions

### OQ-01: Should a carrier that resolves to a done item or executed plan count as satisfied?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO, from repository evidence, as the graduation instruction directs. Backlog `rwhbci` measured `x7wfyx` closed `done` while half its work was unwritten, so terminal does not mean finished, and `_CARRIER_TERMINAL_STATUSES`' own comment says an executed plan is "the hiding place". Keeping the refusal and improving the remedy preserves the rule's ability to catch an abandoned row while making the honest fix cheap.

### OQ-02: Which terminal statuses get the Carrier-Evidence suggestion?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: Only `done` (backlog) and `executed` (plans). `superseded`, `not-executed` and `parked` mean the work was replaced, rejected, or shelved, so citing them as evidence would be the same false claim `Carrier-Declined` makes; those keep the generic fixes, and E-02 case (4) pins it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both verdicts (legitimate, severity, reason, fixes), both `_carrier_index` owner tuples, and the scratch `aw ipd lint --phase pre-transition` diagnostic line.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_check_engine.py -o addopts="" -q -k carrier` (or the new test class name) BEFORE E-03 with cases (1), (2), (6) FAILING and the rest passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `check_engine.py` diff and the same pytest command passing in full after E-03, with the count; paste one full new refusal reason verbatim.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the scratch `aw ipd lint --phase pre-transition` line and `aw check plans --agent` record showing the Carrier-Evidence line, then the lint output after pasting it showing no `check.ipd-uncarried-obligation` for that row.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the README diff and a dash grep over the added lines showing no em or en dash.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), the narrowed lint/check-engine run, and both live `check plans --agent` finding counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A message change, not a rule change: when a plan's `- Carrier:` names work that has since finished (a `done` backlog item or an `executed` plan), the pre-transition refusal now prints the exact `- Carrier-Evidence: <path>` line to paste and warns that `Carrier-Declined` is wrong for shipped work. The refusal itself stays (`legitimate=False`); superseded, not-executed and parked carriers keep the generic remedy. The plans README documents it. Graduates backlog `gyw4gp` (a chore; no release gate) and runs after `vtkfq8`, which edits the same function and writes the README section this extends.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `check_engine._resolve_carrier` (or one helper beside it) and `evaluate_carrier_obligation`'s `raw_carrier` branch; the plans README carrier section; `tests/test_check_engine.py`. An edit outside the declared paths, if one proves necessary, is made and then justified at finalize with `--scope-reason` per out-of-scope path; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-02 must show the new cases FAILING before the change.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `gyw4gp` `done` with `--evidence` citing the executed plan.
