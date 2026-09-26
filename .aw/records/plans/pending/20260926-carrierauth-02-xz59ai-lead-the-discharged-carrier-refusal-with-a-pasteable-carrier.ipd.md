# IPD: Lead the discharged-carrier refusal with a pasteable Carrier-Evidence remedy instead of generic fixes

- Date: 2026-09-26
- Kind: child
- Concern: A CORRECT `- Carrier: <id6>` ROW BECOMES A GATE REFUSAL EXACTLY WHEN ITS CARRIER SUCCEEDS, AND THE REFUSAL OFFERS THE DISHONEST ESCAPE AS READILY AS THE HONEST ONE. `check_engine._resolve_carrier` returns `terminal` for any carrier whose every owner has a status in `_CARRIER_TERMINAL_STATUSES` (`executed`, `superseded`, `not-executed`, `done`, `parked`), and `check_engine.evaluate_carrier_obligation` then returns `legitimate=False, severity="error"` with the reason "carrier <id6> resolves only to a terminal/hidden artifact (<status>); nothing revisits it" and the SAME three generic `fixes` it gives an uncarried row: hand it off, cite `<in-tree artifact path>`, or `Carrier-Declined: <why this needs no carrier>`. Any Set whose later sibling declares `Item-Dependencies: executed:<earlier>` and names the earlier work as a carrier hits this BY CONSTRUCTION at `aw ipd lint --phase pre-transition` (backlog `gyw4gp`, worked case plan `n9na1c`). The executor already knows WHICH artifact discharged the obligation, because the carrier index holds its path, but the message does not say it, so the cheapest keystroke is `Carrier-Declined`, which records a shipped obligation as "needs no carrier". Measured at HEAD `f46b6775` on live carriers `fuk1mr` (done backlog) and `tgyfs2` (executed plan): both return the generic three fixes, and the path of neither appears in the message.
- Scope: IN: (a) when a `- Carrier:` id6 resolves `terminal` because its target is FINISHED (a `done` backlog item or an `executed` plan), put a terminal-specific remedy in the verdict's REASON (the only text that reaches the executor at the gate, see F-3 and F-6) leading with a pasteable `- Carrier-Evidence: <repo-relative path of that artifact>` resolved from the carrier index, and a warning that `Carrier-Declined` is wrong when the work shipped; ALSO put the same suggestion in the verdict's first `fixes` entry, for the `--json` finding shape and for a future consumer, while recording HONESTLY that `aw check`'s `recovery` field does NOT currently carry it (F-6 measured the CLI overwriting it; that is pre-existing bug `evwmm2`, not this plan's to fix); (b) keep the VERDICT unchanged, `legitimate=False` (OQ-01); (c) leave the `superseded`/`not-executed`/`parked` terminal cases on the generic remedy, since those are NOT evidence the work shipped (OQ-02); (d) make the new path derivation NON-RAISING, because the index's absolute path is NOT always under `repo_root` (F-5: `companion` and `home` records backends put it outside, where `Path.relative_to` raises and the enclosing `try` in BOTH surfaces swallows the whole finding); (e) document the remedy in `.aw/records/plans/README.md` in the carrier vocabulary section plan `vtkfq8` writes; (f) behavioral tests. OUT: treating a finished carrier as satisfied; a rewrite verb; `resolve_evidence_artifact`; fixing `evwmm2`'s recovery overwrite.
- Scope-Paths: agent_workflows/check_engine.py, .aw/records/plans/README.md, tests/test_check_engine.py
- Item-Dependencies: executed:vtkfq8
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: gyw4gp
- Set: carrierauth
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: xz59ai

## Workflow history

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED, none deferred, none open; 5 decisions D-1..D-5 recorded. Reviewed at HEAD aa088502 (the plan's cited f46b6775 is an ancestor; `evaluate_carrier_obligation` is unchanged between them). `aw ipd lint --phase author --agent` reported `clean`/`findings: 0` before revision; the lane-input copy was byte-identical to the tracked file and the tree was clean, so no pre-review snapshot. BOTH authored defects reproduce exactly as stated and the design is right. FOUR SUBSTANTIVE CORRECTIONS, each measured. (1) F-3's `fixes[0]` -> `recovery` claim is FALSE at the CLI: `cli.py`'s check path calls `enrich_drift(d, recovery=fix or "")` with `doctor.build_remediation`'s generic fallback, which OVERWRITES the evaluator's recovery, so the agent record reads "inspect ... frontmatter and schema conformity" (new F-6; it is pre-existing bug `evwmm2`, already filed with the same measurement). The remedy therefore had to live in the REASON, which the plan already required, and the plan no longer claims a `recovery` outcome it cannot deliver. (2) THE NEW `relative_to` WOULD SILENTLY DELETE THE WHOLE FINDING on a `companion` or `home` records backend, where the index holds a path OUTSIDE `repo_root`: driven live, `_carrier_index` returns `<repo>.aw/records/...` and `Path.relative_to(repo_root)` raises `ValueError`, which the enclosing bare `except Exception` in `check_content` AND in `ipd_lint._merge_durable_carrier` swallows, taking `check.ipd-uncarried-obligation` from 1 finding to 0 at BOTH surfaces (new F-5, new E-07, new V-07). A fail-open on a fail-closed CI gate is the most serious thing this review found; the remedy is `os.path.relpath` plus a containment fallback that omits the suggestion rather than crashing. (3) E-02 CASE (3) WAS UNPROVABLE AS WRITTEN on a `done` BACKLOG item: `resolve_evidence_artifact` accepts any in-tree `.aw/records/` path, so pasting the case-1 suggestion is only proven for the backlog arm if the test actually drives it; case (3) now covers BOTH arms. (4) E-04's second half told the executor to paste the line and re-lint, but a plan whose ONLY obligation is that row then lints with no carrier finding for a trivially different reason; V-04 now also requires the negative control. ALSO: the multi-line reason is measured safe at both surfaces (`--json` and human lint preserve it; the tab-separated `--agent` drift path is not the one `aw check` uses) and the three-row detail concatenation is shown, so the plan states a length bound; the `Carrier-Note` the worked case used is measured NOT to be a schema field (`DEFERRED_SUBFIELD_RE` matches only the three carrier fields) so E-05's "optionally with a Carrier-Note" is now stated as free prose, not a typed field. Full record: `.aw/records/reviews/20260926-carrierauth-02-xz59ai-lead-the-discharged-carrier-refusal-with-a-pasteable-carrier.review.md`.
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
  - ALSO RE-MEASURE THE `recovery` FIELD, which F-6 found the CLI overwrites, so the executor does not build to a claim that is already false. Run `aw check plans --json` on the SAME scratch repo and paste the `data.policy_findings[]` entry for `check.ipd-uncarried-obligation`: its `detail` and its `recovery`. At review the recovery read `inspect <plan> frontmatter and schema conformity.` (the `doctor.build_remediation` fallback), NOT the evaluator's `fixes[0]`. If that is still true, E-03 must not be graded on the `recovery` field and V-04 records the fact instead of asserting the suggestion appears there.
  - Execution state: pending

### Task group 2: the remedy

- [ ] E-02 WRITE THE BEHAVIORAL TESTS FIRST in `tests/test_check_engine.py` (behavior only, no source-text or AST pins, per the 2026-09-26 test-policy ruling). Build a scratch repo in a `TemporaryDirectory` with `.aw/records/backlog/done/<...>-bk0001-....backlog.md` (`- Status: done`), `.aw/records/plans/executed/<...>-pl0001-....ipd.md` (`- Status: executed`), and a superseded plan `pl0002`; pass an explicit `carrier_index` built by `check_engine._carrier_index(repo)`. Cases: (1) `Carrier: bk0001` -> `legitimate` is False, `severity == "error"`, the reason contains the literal line `- Carrier-Evidence: .aw/records/backlog/done/<that filename>` and the word `Carrier-Declined` in a warning; `fixes[0]` contains the same Carrier-Evidence line; (2) `Carrier: pl0001` -> same shape with the executed plan's repo-relative path; (3) PASTING THE SUGGESTION WORKS, FOR BOTH ARMS: take the suggested line out of the case-1 verdict AND out of the case-2 verdict, feed each back as a `Carrier-Evidence` row, and assert `legitimate=True, path="SATISFIED"` each time. BOTH, not just the plan arm, because the two suggestions cite different trees and `vtkfq8` adds a tree-scoped refusal to this same branch; proving only one would leave the other's resolvability assumed. Parse the path out of the verdict rather than re-deriving it in the test, so the test proves the SUGGESTION resolves and not merely that some path does; (4) `Carrier: pl0002` (superseded) -> still refused with the GENERIC fixes and no Carrier-Evidence suggestion; (5) a carrier with one live and one done owner -> `legitimate=True, path="HANDOFF"` unchanged (measured at review: `_carrier_index` really does return both owners for a shared id6, and the live one short-circuits before any terminal owner is examined, so this case is a genuine negative control and not a tautology); (6) end to end, `check_engine.evaluate_durable_carrier` on a plan text carrying the case-2 row returns one Drift whose `detail` contains the Carrier-Evidence line; assert on `detail` and on the Drift's own `recovery`, and do NOT assert anything about what `aw check`'s CLI prints as its recovery, which F-6 measured is overwritten downstream.
  - Depends on: E-01
  - Expected outcome: cases (1), (2) and (6) FAIL against the unchanged code; (3), (4), (5) PASS before and after.
  - Execution state: pending

- [ ] E-03 IMPLEMENT IN `check_engine`. Make `_resolve_carrier` (or a sibling helper it calls, so the one resolution stays in one place) also return, for a `terminal` verdict, the finished owners: those whose status is `done` (record type `backlog`) or `executed` (record type `plans`), with their paths made repo-relative against `repo_root` (the index stores absolute paths, F-2) BY THE NON-RAISING RULE E-07 defines, not by a bare `Path.relative_to`. In `evaluate_carrier_obligation`'s `raw_carrier` branch, when every good id6 failed and at least one is terminal-with-a-finished-owner, build the refusal as: the existing locator and "terminal/hidden" detail, then "this obligation was discharged by finished work; cite it instead of the carrier:" followed by one pasteable `- Carrier-Evidence: <relpath>` line per finished owner (first one first), then "do NOT use `Carrier-Declined` here: the work shipped, so declining it would record it as needing no carrier". Put the first Carrier-Evidence suggestion in `fixes[0]` ahead of the three generic fixes. Keep `legitimate=False` and `severity="error"`. Keep `_resolve_carrier`'s other callers, if `rg -n "_resolve_carrier\(" agent_workflows` shows any at execution, unchanged in behavior (measured at review: the ONLY caller is `evaluate_carrier_obligation`, so a signature change is contained, but re-measure because `vtkfq8` lands first).
  - Depends on: E-02
  - Expected outcome: all six E-02 cases pass.
  - BOUND THE MESSAGE LENGTH, because the reason is concatenated per row into one Drift detail. `evaluate_durable_carrier` joins up to FIVE reasons with `"; "`; measured at review with a three-row plan, a ~230-char added remedy produced a ~1.1k-char detail, and five rows would reach roughly 1.8k. That is acceptable for the two surfaces this reaches (both measured multi-line-safe in F-7) but a multi-owner carrier must NOT multiply it further: emit AT MOST the FIRST finished owner's `- Carrier-Evidence:` line and, if more exist, a single trailing `(and N more finished owner(s))` count. An id6 with several finished owners is the ambiguous case anyway, and listing all of them would invite pasting the wrong one.
  - Execution state: pending

- [ ] E-07 MAKE THE PATH DERIVATION NON-RAISING, which is the correctness half of E-03 and the one defect this plan could otherwise INTRODUCE (F-5). Do NOT use `Path(p).relative_to(repo_root)`: the carrier index's paths come from `status_set.inventory_all_artifacts` over `selectors.record_dirs`, which resolves the records tree through the project context, and on a `companion` backend that root is `<repo>.aw/records` while on a `home` backend it is under the AW home, so the path is OUTSIDE `repo_root` and `relative_to` raises `ValueError`. Derive with `os.path.relpath` (which never raises) and then REQUIRE containment: if the result starts with `..` or is absolute, the artifact is not citable as a repo-relative `Carrier-Evidence` path (`resolve_evidence_artifact` would reject it anyway, measured at review), so OMIT the suggestion for that owner and fall through to the existing generic remedy for it. Never let this branch raise.
  - Depends on: E-02
  - Expected outcome: a `companion`- or `home`-backend repo still reports `check.ipd-uncarried-obligation` with the generic remedy, and the suggestion appears only when the cited path is genuinely repo-relative and resolvable.
  - WHY THIS IS THE MOST SERIOUS ITEM IN THE PLAN, stated so it is not optimized away: BOTH gate surfaces wrap this evaluator in a bare `except Exception` that is documented as "a repo-scan failure never masks the pure lint result" (`ipd_lint._merge_durable_carrier`) and as fail-isolation (`check_engine.check_content`). Measured at review by raising inside `evaluate_carrier_obligation` on a scratch repo: `check_content` went from rules `['check.ipd-lint-diagnostic', 'check.ipd-uncarried-obligation']` to `['check.ipd-lint-diagnostic']`, and `ipd_lint.lint_file --phase pre-transition` dropped `check.ipd-uncarried-obligation` from its diagnostics entirely. So an exception here does not fail loudly: it turns a fail-closed CI gate (`aw check plans` is fail-closed in `tests.yml`) and the pre-transition execution gate into silent passes. A message improvement must not be able to do that.
  - Execution state: pending

- [ ] E-04 CONFIRM THE TWO GATE SURFACES CARRY THE NEW TEXT. Re-run E-01's `aw ipd lint --phase pre-transition` on the scratch plan and `aw check plans --json` on a scratch repo containing it, and paste both: the lint diagnostic (built from `d.detail` in `ipd_lint._merge_durable_carrier`) must show the Carrier-Evidence line, and the `--json` finding's `detail` must show it too. DO NOT assert the check record's `recovery` is the suggestion: F-6 measured the CLI overwriting the evaluator's recovery with `doctor.build_remediation`'s generic fallback, so paste whatever `recovery` actually holds and name it as the pre-existing `evwmm2` defect rather than a failure of this item. Then paste the suggested line into the scratch plan's row in place of `- Carrier:` and show `aw ipd lint --phase pre-transition` no longer reports `check.ipd-uncarried-obligation` for that row.
  - Depends on: E-03, E-07
  - Expected outcome: both surfaces show the pasteable line in the DETAIL; pasting it clears the finding; the check `recovery` field is recorded as-is.
  - ADD THE NEGATIVE CONTROL TO THE PASTE-AND-CLEAR STEP, or it proves nothing. A plan whose ONLY obligation is that one row reports no carrier finding after ANY edit that removes the row, including deleting it, so "the finding is gone" is not evidence the pasted line resolved. Give the scratch plan a SECOND, deliberately uncarried row, and show the finding count going from 2 to 1 with the surviving locator named, rather than from 1 to 0.
  - Execution state: pending

### Task group 3: docs and suite

- [ ] E-05 DOCUMENT THE REMEDY in `.aw/records/plans/README.md`, inside the carrier vocabulary section `vtkfq8` E-05 creates (read it first; if it does not exist because `vtkfq8` changed shape, add a short "Carriers" subsection after the execution-contract section and say so at finalize). Add: a carrier that becomes `done`/`executed` before your plan finishes turns the row into a refusal on purpose (a reader pointed at a closed item would think the work is still pending); the remedy is to replace `- Carrier:` with the `- Carrier-Evidence:` line the refusal prints, and optionally to say why in the row's own prose; `Carrier-Declined` is for work that genuinely needs no carrier and is wrong for work that shipped. Name the ordered-Set pattern (a later sibling that depends on an earlier one) as the common way this arises. User-facing prose: no em or en dashes.
  - Depends on: E-03
  - Expected outcome: the README states the terminal-carrier remedy next to the carrier vocabulary.
  - DO NOT DOCUMENT `- Carrier-Note:` AS A FIELD. The worked case `n9na1c` wrote one and it reads well, but measured at review it is NOT in the schema: `ipd_schema.CARRIER_FIELDS` is exactly the three fields and `DEFERRED_SUBFIELD_RE` matches only `Carrier|Carrier-Evidence|Carrier-Declined`, so `_deferred_section_obligations` parses a `Carrier-Note` line into nothing (driven: the parsed field dict holds only `Carrier-Evidence`). Documenting it in the plans README would advertise a typed subfield that no reader reads, which is the "documented only in code" inversion `vtkfq8` F-9 exists to fix, pointed the wrong way. Either say plainly that the explanation goes in the row's PROSE, or, if the maintainer wants a typed note, that is a schema addition and belongs in its own plan (not this one).
  - Execution state: pending

- [ ] E-06 RUN THE BARE SUITE `python3 -m pytest` before (at E-01) and after E-05, plus `python3 -m pytest tests/test_ipd_lint.py tests/test_check_engine.py -o addopts="" -q` (the carrier evaluator is reached from both `aw check` and `aw ipd lint`), and `python3 -m agent_workflows check plans --agent` on the real tree before and after.
  - Depends on: E-05
  - Expected outcome: the after-minus-before failing node set is empty; `check plans` reports the same findings count (the change alters messages, never verdicts).
  - THE SAME-COUNT PROPERTY IS THE REGRESSION TEST FOR F-5, so read it that way rather than as a formality. A DROP in the `check.ipd-uncarried-obligation` count is the exact signature of the swallowed exception E-07 prevents, because the bare `except Exception` converts a raise into a missing finding rather than an error. So compare the count PER RULE, not the total, and if the carrier count falls, treat it as a FAILURE of E-07 and not as an improvement. (Measured at review on this tree: 1 `check.ipd-uncarried-obligation` finding plus the informational `check.collisions-not-checked`; re-derive rather than expecting that pair.)
  - Execution state: pending

## Project conventions discovered (Step 0)

- The carrier predicate is one evaluator shared by both surfaces: `check_engine.evaluate_durable_carrier` is called by `check_durable_carrier` (`aw check`) and `ipd_lint._merge_durable_carrier` (`aw ipd lint --phase pre-transition`); per-row verdicts come from `evaluate_carrier_obligation`.
- `_CARRIER_TERMINAL_STATUSES` deliberately includes `executed` because "an executed plan classes `done` in `aw attention`, which is the hiding place"; this plan does NOT change that set.
- `_carrier_index` returns `id6 -> [(record_type, status, absolute path)]`, filtered to `_CARRIER_TARGET_TYPES = ("backlog", "plans")`. Those absolute paths are NOT guaranteed to sit under `repo_root`: they come from `status_set.inventory_all_artifacts` over `selectors.record_dirs`, which honors the project's records backend, so a `companion` or `home` backend puts them outside (F-5). An id6 may also have SEVERAL owners, and `_resolve_carrier` returns `ok` as soon as one is non-terminal.
- BOTH gate surfaces wrap this evaluator in a bare `except Exception` (`check_engine.check_content`'s fail-isolation block, and `ipd_lint._merge_durable_carrier`'s "a repo-scan failure never masks the pure lint result"). That is deliberate, and it means an exception raised inside the evaluator DELETES the finding instead of failing loudly (F-5). Any new code in this branch must therefore be non-raising by construction.
- The `recovery` a rule puts on a Drift does NOT reach `aw check`'s output: `cli.py` re-enriches with `doctor.build_remediation`'s value, which for this rule is the generic `inspect ... frontmatter and schema conformity.` fallback (F-6, filed as `evwmm2`). Only `detail` is trustworthy as the executor-facing text today.
- `Carrier-Evidence` resolves through the shared `resolve_evidence_artifact` (an existing in-tree path under `.aw/records/` or `.agents/`); `vtkfq8` adds a walkthrough refusal on top, which executed plans and done backlog items do not trip.
- Tests are run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-4 were measured by the author at HEAD `f46b6775` on 2026-09-26. F-5 through F-8 were
measured at `/plan-review` (2026-09-26, HEAD `aa088502`, of which `f46b6775` is an ancestor), each by
DRIVING the predicate or the CLI on a scratch repo rather than by reading the code.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | `evaluate_carrier_obligation` | A finished carrier gets the same three generic fixes as an uncarried row, with no path. | `Carrier: fuk1mr` -> `False error ... carrier fuk1mr resolves only to a terminal/hidden artifact (done); nothing revisits it`, fixes `('hand it off: ...', 'cite evidence it is already addressed: add `- Carrier-Evidence: <in-tree artifact path>`', 'decline it explicitly, with a reason: ...')`; `tgyfs2` (executed) identical shape |
| F-2 | INFO | `_carrier_index` | The artifact to cite is already known. | `fuk1mr -> [('backlog','done','<abs>/.aw/records/backlog/done/20260922-revalbase-01-fuk1mr-....backlog.md')]`, `tgyfs2 -> [('plans','executed','<abs>/.aw/records/plans/executed/20260922-revalbase-01-tgyfs2-....ipd.md')]` |
| F-3 | MEDIUM | `ipd_lint._merge_durable_carrier` | The pre-transition gate shows ONLY the drift detail (`Diagnostic(0, 1, d.rule, d.detail)`), and the detail is built from verdict REASONS. So a remedy placed only in `fixes` would be invisible at the gate where the executor meets it. CORRECTED AT REVIEW: the original text added "`fixes` reach only `aw check`'s `recovery` field", which is true of the EVALUATOR and false of what `aw check` prints (F-6). | `evaluate_durable_carrier` builds `detail` from `v.reason` and `recovery=fixes[0]`; the `--json` finding's `recovery` measured as the generic fallback |
| F-4 | INFO | backlog `gyw4gp` | The worked case's manual fix was exactly this line, which is proof it is the right remedy. NOTE the `- Carrier-Note:` it also wrote is NOT a schema field (F-8). | "replaced '- Carrier: fuk1mr' with '- Carrier-Evidence: <path to the executed tgyfs2 plan>' plus a '- Carrier-Note:'" |
| F-5 | HIGH | the path derivation E-03 proposes, plus the bare `except Exception` in BOTH gate surfaces | **A BARE `Path.relative_to(repo_root)` WOULD SILENTLY DELETE THE WHOLE FINDING ON A NON-REPOSITORY RECORDS BACKEND, TURNING TWO FAIL-CLOSED GATES INTO SILENT PASSES.** The carrier index's paths come from `status_set.inventory_all_artifacts` over `selectors.record_dirs`, which resolves the records tree through the project context. On a `companion` backend that root is `<repo>.aw/records`, and on a `home` backend it is under the AW home: in BOTH cases the path is OUTSIDE `repo_root`, so `relative_to` raises `ValueError`, and each surface's enclosing bare `except Exception` swallows it. This is the one defect the plan could INTRODUCE, and it is the reason for new E-07. | companion fixture: `_carrier_index` -> `('plans','executed','/tmp/.../repo.aw/records/plans/executed/...ipd.md')`, then `Path(p).relative_to(root)` -> `ValueError: ... is not in the subpath of ...`; home fixture: same, under `<AW home>/projects/repo-<hash>/records/`. Consequence driven by raising inside `evaluate_carrier_obligation`: `check_engine.check_content(root,'plans')` rules went `['check.ipd-lint-diagnostic','check.ipd-uncarried-obligation']` -> `['check.ipd-lint-diagnostic']`, and `ipd_lint.lint_file(..., checkpoint='pre-transition')` dropped the rule from its diagnostics. `aw check plans` is fail-closed in `.github/workflows/tests.yml` |
| F-6 | MEDIUM | `cli.py`'s check path, via `doctor.build_remediation` | **`aw check` DOES NOT PRINT THE EVALUATOR'S `fixes[0]`, so half of this plan's stated delivery was already impossible.** The CLI calls `enrich_drift(d, recovery=fix or "")` where `fix` is `doctor.build_remediation`'s value, and `build_remediation` has no branch for `check.ipd-uncarried-obligation`, so it returns the generic fallback and OVERWRITES the evaluator's recovery. This is already filed as backlog `evwmm2` (`bug`/`high`/`Blocks-Release: next`) with this exact measurement, so it is not this plan's to fix; the plan's claim about it had to go. | patched the evaluator to set `fixes[0]` to the suggestion, then `aw check plans --json`: `detail` carried it, `recovery` read `inspect .aw/records/plans/pending/<plan> frontmatter and schema conformity.`; `doctor.build_remediation` read end to end (`detailed_fix=f"inspect {loc} frontmatter and schema conformity."`); `.aw/records/backlog/open/20260918-evwmm2-01-evwmm2-check-human-fix-ignores-recovery.backlog.md` |
| F-7 | INFO | both gate surfaces, with a multi-line reason | A MULTI-LINE reason is safe on the surfaces this actually reaches, which is what makes putting the remedy in the reason viable rather than a rendering risk. Driven with a three-line remedy injected: `aw ipd lint --phase pre-transition` (human) prints it verbatim; `aw check plans --json` carries it in `detail`; `aw ipd lint --agent` and `aw check --agent` emit no detail at all (the compact record is `location`+`rule` only), so neither can be broken by a newline. The tab-separated `render_agent_drift` path, which WOULD need `attention_contract.escape_detail`, is used by `plans_index`/`prompts_index`/`artifact_types`, none of which run this rule. Length: a three-row plan produced a ~1.1k-char joined detail; five rows (the cap in `evaluate_durable_carrier`) would reach roughly 1.8k. | scratch repo, evaluator monkeypatched to append a three-line remedy; outputs of `ipd lint` human/`--agent`/`--json` and `check plans` human/`--agent`/`--json` all inspected; `rg -n "render_agent_drift"` -> 3 call sites, none in the `aw check` path |
| F-8 | LOW | E-05 as authored, and the worked case | `- Carrier-Note:` IS NOT A TYPED FIELD, so documenting it would advertise a subfield nothing reads. `ipd_schema.CARRIER_FIELDS` is exactly the three carrier fields and `DEFERRED_SUBFIELD_RE` matches only `Carrier|Carrier-Evidence|Carrier-Declined`. | `_deferred_section_obligations` on a row carrying both `Carrier-Evidence` and `Carrier-Note` -> parsed fields `{'Carrier-Evidence': '...'}` (the note absent); `rg -n "Carrier-Note" agent_workflows/` -> no hits |

## Proposed changes (ordered, validatable)

1. E-01 re-measures on the post-`vtkfq8` tree, including the `recovery` field F-6 found overwritten.
2. E-02 writes the behavioral tests, failing half first, with paste-and-resolve driven on BOTH arms.
3. E-03 builds the terminal-specific remedy in the reason and `fixes[0]`, bounded in length.
4. E-07 makes the path derivation non-raising and containment-checked (F-5), so the change cannot silently disable the gate.
5. E-04 confirms both gate surfaces' DETAIL, records the `recovery` field as-is, and proves paste-and-clear against a negative control.
6. E-05 documents the remedy in the plans README, without inventing a `Carrier-Note` field (F-8).
7. E-06 suite and live `check plans` before and after, compared PER RULE so an F-5 regression cannot hide as an improvement.

## Deferred / out of scope (with reason)

- Treating a `done`/`executed` carrier as SATISFIED (item option 1).
  - Carrier-Declined: rejected on repository evidence (OQ-01); a terminal carrier is not proof the obligation was finished, as the `x7wfyx` case measured.
- An `aw ipd` verb that rewrites a discharged carrier into cited evidence (item option 2).
  - Carrier-Declined: with the pasteable line in the refusal the manual edit is one copy-paste; a mutating verb that edits another field of a plan at the gate is more surface than the remaining cost justifies.

## Scope check

- Over-scope: one claim removed rather than one item. The plan asserted the remedy would reach `aw check`'s `recovery` field; F-6 measured that the CLI overwrites it, so the claim was a deliverable this plan cannot produce and its fix belongs to backlog `evwmm2`. The Scope and E-04 now say so instead.
- Under-scope: two gaps closed. E-03's path derivation would have raised on a `companion` or `home` records backend and the surrounding fail-isolation would have converted that into a DELETED finding at both fail-closed gates (F-5), now its own item E-07 with its own validation; and E-04's paste-and-clear step had no negative control, so it would have passed on a row that was merely removed.
- `agent_workflows/ipd_lint.py` is deliberately NOT declared: it already forwards `d.detail`, which will carry the remedy (F-3), and its bare `except` is a fact E-07 designs around rather than a line to change.
- Scope-Paths justification: `check_engine.py` holds the predicate (`_resolve_carrier` or a sibling helper, plus `evaluate_carrier_obligation`'s `raw_carrier` branch); the plans README holds the vocabulary section; `tests/test_check_engine.py` holds E-02's cases including E-07's backend fixtures.

## Required tests / validation

- `tests/test_check_engine.py`: six behavioral cases including paste-and-resolve on BOTH arms and the superseded negative; cases (1), (2), (6) shown FAILING before E-03.
- `tests/test_check_engine.py` also covers E-07: a `companion`-backend fixture (`.aw/config/project.json` with `records_backend: companion`, records under `<repo>.aw/records/`) where the finished owner's path is outside `repo_root`, asserting the rule STILL reports at `error` with the generic remedy and no traceback, driven through `check_engine.check_content(repo, "plans")` so the bare `except` is in the path.
- `python3 -m pytest tests/test_ipd_lint.py tests/test_check_engine.py -o addopts="" -q`.
- Bare `python3 -m pytest` and live `check plans --agent` before and after, compared PER RULE (a drop in the carrier count is an F-5 regression, not progress).

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
  - Required evidence: paste both verdicts (legitimate, severity, reason, fixes), both `_carrier_index` owner tuples, and the scratch `aw ipd lint --phase pre-transition` diagnostic line. ALSO paste the scratch `aw check plans --json` finding for this rule showing its `detail` and its `recovery` verbatim, and state which of the two the remedy can actually reach (F-6).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_check_engine.py -o addopts="" -q -k carrier` (or the new test class name) BEFORE E-03 with cases (1), (2), (6) FAILING and the rest passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `check_engine.py` diff and the same pytest command passing in full after E-03, with the count; paste one full new refusal reason verbatim, and the joined `evaluate_durable_carrier` detail for a plan carrying THREE such rows, with its character length, so the length bound is observed rather than assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste (a) the `companion`-backend fixture's `_carrier_index` entry showing the owner path OUTSIDE `repo_root`, (b) `check_engine.check_content(repo, "plans")` on that fixture BEFORE the E-07 guard (or with the guard temporarily reverted in the worktree) showing `check.ipd-uncarried-obligation` MISSING, and AFTER showing it PRESENT at `error` with the generic remedy, (c) the same pair through `ipd_lint.lint_file(..., checkpoint="pre-transition")`, and (d) `git diff --stat agent_workflows/check_engine.py` showing the revert was undone. Then state plainly that no traceback was printed in either direction, because a silent drop is exactly the symptom.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the scratch `aw ipd lint --phase pre-transition` line and the `aw check plans --json` finding's `detail` showing the Carrier-Evidence line; paste that finding's `recovery` as-is and name it as `evwmm2` rather than asserting it carries the suggestion. Then paste the paste-and-clear run AGAINST THE NEGATIVE CONTROL: the two-row scratch plan's finding count going 2 -> 1 with the surviving locator named (not 1 -> 0, which any deletion would produce).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the README diff and a dash grep over the added lines showing no em or en dash. Also confirm the added text does NOT present `Carrier-Note` as a field (F-8), by pasting `rg -n "Carrier-Note" .aw/records/plans/README.md` with no hit, or by quoting the sentence that routes the explanation to prose.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER, the after-minus-before failing node-ID set (must be empty), the narrowed lint/check-engine run, and both live `check plans --agent` finding counts BROKEN DOWN BY RULE. State the `check.ipd-uncarried-obligation` count before and after explicitly and confirm it did not FALL; a fall is an F-5 regression.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A message change, not a rule change: when a plan's `- Carrier:` names work that has since finished (a `done` backlog item or an `executed` plan), the pre-transition refusal now prints the exact `- Carrier-Evidence: <path>` line to paste and warns that `Carrier-Declined` is wrong for shipped work. The refusal itself stays (`legitimate=False`); superseded, not-executed and parked carriers keep the generic remedy. The plans README documents it. Graduates backlog `gyw4gp` (a chore; no release gate) and runs after `vtkfq8`, which edits the same function and writes the README section this extends.

TWO THINGS A HUMAN SHOULD LOOK AT DELIBERATELY, both added at review. FIRST, THIS PLAN TOUCHES A FAIL-CLOSED GATE THAT FAILS SILENTLY WHEN IT RAISES. Both surfaces that consume this evaluator wrap it in a bare `except Exception`, so an exception inside the new branch does not error: it DELETES the `check.ipd-uncarried-obligation` finding, at `aw check plans` (fail-closed in CI) and at the `aw ipd lint --phase pre-transition` execution gate. The obvious implementation (`Path.relative_to(repo_root)`) raises on a `companion` or `home` records backend, where the carrier index legitimately holds a path outside the repo, and that was MEASURED at review (F-5). E-07 and V-07 exist solely to make the change non-raising, and V-07 demands the before/after at both surfaces. SECOND, ONE OF THE PLAN'S TWO CLAIMED OUTCOMES WAS ALREADY IMPOSSIBLE and has been withdrawn rather than quietly retained: `aw check` does not print the evaluator's `fixes[0]`, because the CLI overwrites `recovery` with a generic fallback (F-6). That is pre-existing bug `evwmm2` (`bug`/`high`/`Blocks-Release: next`), already filed with the same measurement, and is deliberately NOT fixed here; this plan's delivery is the refusal REASON, which both gates do show.

Scope fence (a DECLARATION for reconciliation, not a stop directive): `check_engine._resolve_carrier` (or one helper beside it) and `evaluate_carrier_obligation`'s `raw_carrier` branch; the plans README carrier section; `tests/test_check_engine.py`. `agent_workflows/ipd_lint.py` and `agent_workflows/doctor.py` are explicitly NOT in scope: the first already forwards the detail, and the second is `evwmm2`'s. An edit outside the declared paths, if one proves necessary, is made and then justified at finalize with `--scope-reason` per out-of-scope path; a declared-but-unmodified path takes `--scope-ack`.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. V-02 must show the new cases FAILING before the change. Two claims here are specifically easy to fake and must be DRIVEN rather than described: V-07's before/after at BOTH surfaces on a non-repository records backend (a passing test that never enters the outside-the-repo path proves nothing), and V-04's paste-and-clear, which must move a finding count from 2 to 1 against a second uncarried row rather than from 1 to 0.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if `vtkfq8` has NOT executed when this plan starts, stop rather than editing `evaluate_carrier_obligation`'s evidence branch under it, since the declared `- Item-Dependencies: executed:vtkfq8` is what keeps the two out of each other's way (the runner enforces this; a human executing by hand must check it). If no non-raising derivation can produce a citable repo-relative path for a finished owner, OMIT the suggestion for that owner and keep the generic remedy; do NOT remove the containment check to make a suggestion appear, because a `Carrier-Evidence` path outside the repo is refused by `resolve_evidence_artifact` anyway and would be advice that cannot work.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `gyw4gp` `done` with `--evidence` citing the executed plan.
