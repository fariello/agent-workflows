# IPD: Make graduation hand off only orchestrator plans that are ready for review

- Date: 2026-10-04
- Kind: orchestrator
- Concern: Graduating a backlog item (or producing plans from an approved spec) through `aw oc run` / `aw agy run` routinely hands off an orchestrator plan that the next run refuses. Measured 2026-10-03: three `--action review` runs over 53 queued plans were refused before any agent turn because the orchestrator coverage probe judged 13 of the 16 pending orchestrator plans (`i18yaz`, `u4glub`, `z2l43n`, `1u4olp`, `63zo2f`, `itamry`, `u57rfv`, `4qv834`, `l8wvv3`, `qtz0us`, `axozpe`, `m0kl28`, `xhr0dj`) to "carry work no child covers"; 11 of their 13 source backlog items already read `graduated`. Four separate defects combine: (1) the production prompt (`runner_shared.build_backlog_production_prompt`, and its spec twin) says nothing about orchestrator plans or coverage; (2) the orchestrator skeleton `aw ipd scaffold --kind orchestrator` writes `- TODO: whole-Set completion criteria.`, `- TODO: cross-IPD consistency / no-drift / dependency checks.` and `TODO: how the executed plan is verified.`, which are exactly the sections the probe reads and its prompt calls uncovered work; (3) production verification (`production_checks._check_ipd_conformance`, reached through `backlog_graduate_ipd` and `spec_plan_conformance`) checks each produced plan alone and never the Set, so it sets the source `graduated` / `implementing` with a refused orchestrator; (4) the probe itself gates every queued orchestrator regardless of whether the run can retire it, answers with a bare verdict line that names nothing, and does not credit work the orchestrator explicitly assigns to a named child (`axozpe` states in its `Required tests / validation` that Order 04, which its own child table resolves to `rlhmt9`, carries the final cross-child measurement, and was still refused). Nothing checks orchestrator readiness when `- Status:` is set, so `to-review` currently asserts something no tool verified.
- Scope: ORCHESTRATION ONLY. This plan sequences thirteen child plans and contributes no implementation, no test and no deliverable of its own. Every artifact is owned by exactly one child and named in the child table. IN: the dependency order, the Set-level completion criteria with the child that owns each, and the cross-child consistency checks. OUT: everything the children do, namely the amendments to five specs (Order 01), the probe's answer format and named-owner rule (Order 02), the shared review-readiness check and the `aw ipd coverage` verb (Order 03), the probe's scoping and its retirement-time re-check (Order 04), the `aw ipd set` refusal, the loud backward moves and the pinned scaffold default (Order 05), the production action's Set-level check (Order 06), the bounded correction turns (Order 07), resuming an unfinished handoff (Order 08), re-checking the 13 refused orchestrators (Order 09), the `aw backlog set graduated` / `aw specs set implementing` refusal (Order 10), the authoring instructions (Order 11), the end-to-end proof (Order 12), and the `From-Spec` nudge fix (Order 13). This Set does NOT redesign record handling into an object model (a separate discussion), and does NOT add any `C-*`/`Owner:` requirement-ownership syntax (deliberately deferred, see Deferred).
- Scope-Paths: .aw/records/plans/pending/20261004-gradcover-01-hm1h3l-amend-the-run-retirement-conformance-and-ipd-specs-for-orche.ipd.md, .aw/records/plans/pending/20261004-gradcover-02-8mabmu-make-the-coverage-probe-quote-the-work-it-found-and-credit-w.ipd.md, .aw/records/plans/pending/20261004-gradcover-03-qs00nc-add-one-shared-orchestrator-review-readiness-check-and-the-a.ipd.md, .aw/records/plans/pending/20261004-gradcover-04-5etev3-run-the-coverage-probe-only-where-a-run-can-retire-an-orches.ipd.md, .aw/records/plans/pending/20261004-gradcover-05-26m1nb-refuse-aw-ipd-set-to-review-reviewed-and-approved-for-an-orc.ipd.md, .aw/records/plans/pending/20261004-gradcover-06-r2wa38-check-the-whole-set-before-a-production-action-hands-off-a-b.ipd.md, .aw/records/plans/pending/20261004-gradcover-07-nnsa2o-send-a-refused-production-or-review-action-back-for-bounded.ipd.md, .aw/records/plans/pending/20261004-gradcover-08-24qw39-let-a-production-action-resume-an-unfinished-handoff-instead.ipd.md, .aw/records/plans/pending/20261004-gradcover-09-52opph-re-check-every-pending-orchestrator-and-send-the-failing-one.ipd.md, .aw/records/plans/pending/20261004-gradcover-10-sbiv1j-refuse-aw-backlog-set-graduated-and-aw-specs-set-implementin.ipd.md, .aw/records/plans/pending/20261004-gradcover-11-dalmk4-state-the-orchestrator-coverage-rule-in-the-production-promp.ipd.md, .aw/records/plans/pending/20261004-gradcover-12-wytlly-prove-end-to-end-that-a-graduation-yields-an-orchestrator-th.ipd.md, .aw/records/plans/pending/20261004-gradcover-13-jm27py-stop-the-from-spec-nudge-for-a-plan-that-declares-no-spec-so.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: 1c9d11692fee4dd64b1eed26bce8004b430d5a68f0aeee742e92f26bd7da4292
- Coverage-Checked: 2026-10-06 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 0
- Highest E allocated: 13
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1f4faf
- Approval: 2026-10-06, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-06 coverage pass (aw oc run): fingerprint 1c9d11692fee, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-06 approved (aw set): status set to approved
- 2026-10-06 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `wytlly` (finding PR-008): Order 12 now declares every child whose behavior its scenarios exercise (`nnsa2o`, `24qw39`, `26m1nb`, `r2wa38`, `qs00nc`, `8mabmu`), not only `sbiv1j`, `dalmk4`, `5etev3`; E-12 and the child-table row updated. Its Run C also approves its fixture orchestrator before orchestrating, since a `reviewed` orchestrator is not dispatched. The review verdict and readiness of this plan are unchanged.
- 2026-10-06 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `sbiv1j` (findings PR-001, PR-008): Order 10's `check.graduation-incomplete` is grandfathered by a new stamped cutover (88 of 189 graduated items have no active handoff, measured), and it now declares `26m1nb` and `r2wa38`; E-10 and the child-table row updated. Completion criterion 5's 'reports an already-`graduated` item whose plan has fallen back' applies to graduations after that cutover. The review verdict and readiness of this plan are unchanged.
- 2026-10-06 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `24qw39` (findings PR-001, PR-004): Order 08 now also depends on `26m1nb` (its continue prompt relies on the backward-move and children-first rules) and commits the agent's edits to existing handoff plans; E-08 and the child-table row updated. The review verdict and readiness of this plan are unchanged.
- 2026-10-06 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `dalmk4` (finding PR-001): Order 11 now also depends on `5etev3`, `r2wa38` and `sbiv1j`, because the `AGENTS.md` text it installs describes their gates; E-11 and the child-table row updated to match. The review verdict and readiness of this plan are unchanged.
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-007..PR-010 (round 2, all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-007 to PR-010 (round 2). Fixed: self-gating window after Order 03 stated with its remedy (PR-007); `axozpe` evidence corrected to its `Required tests / validation` and Order 04 (PR-008); "four spec amendments" corrected to five specs (PR-009); V-* status grep made `-m1` so it cannot match open-question `- Status:` lines (PR-010). Round-1 PR-006 confirmed fixed by the maintainer's 2026-10-04 ruling (OQ-03 resolved, non-blocking).
- 2026-10-05 to-review (aw set): returned to review after revision: maintainer ruling 2026-10-04 stores the coverage answer in the plan (25kzda 2.5e), resolving blocking OQ-03; every affected plan was rewritten to match
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): revised after review. OQ-03 RESOLVED by the maintainer (2026-10-04): the coverage answer is stored in the plan. Child-table purposes for Orders 01, 02, 03, 06 and 09 and completion criteria 2, 3 and 8 updated to match; the Set's children were revised the same day and returned to `to-review`.
- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `qs00nc` (finding PR-001): OQ-03 Context gains the freeze-gate ordering (`enforce_freeze_time_refusal` lints approved plans at `pre-execution` before the run-start probe). Context only; the question, options and verdict are unchanged.
- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `8mabmu` (PR-002): correction to Concern point (4): `axozpe` names its final-measurement owner as "Order 04" (resolved to `rlhmt9` only through its child table), not by id6; Order 01 A.4 and Order 02 E-01 now credit an Order number present in the table.
- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `jm27py` (PR-003): Order 01 `hm1h3l` now also carries `- From-Spec: none` (it cites `2vev8j` without editing it), so the authoring note below that every plan EXCEPT Order 01 carries it is superseded: every plan in the Set carries it.
- 2026-10-04 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-006 (PR-006 open, blocking OQ-03)

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 to PR-006. Fixed: ONE PREDICATE parity now owned by `wytlly` E-05 (PR-002); declared missing edges `52opph` -> `26m1nb` and `wytlly` -> `5etev3` (PR-003); `52opph` no longer demotes this Set (PR-004); execution contract completed (PR-005); scaffold wording corrected (PR-001). OPEN, blocking: OQ-03 / PR-006, the machine-local verdict makes the new `error` rules fail CI on every orchestrator at `to-review` or later.
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored at the maintainer's direct instruction (2026-10-04 session: "I don't want a backlog item, I want a plan or plan set, ready to review in an IWT"), after the three refused `--action review` runs of 2026-10-03 (run directories `run-20261003T172034Z-*`, `run-20261003T172037Z-3697351`, `run-20261003T172039Z-3698091`, `run-20261003T172049Z-3698977`, whose `orchestrator-probe-gate` events record `proceed: false` over the 13 orchestrators named in Concern). There is deliberately NO backlog item and therefore no `- From-Backlog:`. `- Blocks-Release: f33nrj` (the planned 2.0.0 release record) is set because every plan here is `Work-Kind: bug` and the repository rule is that a live bug gates the next release. Authored in an isolated worktree (`aw/author/gradcover`) and not merged.
  `- From-Spec: none` IS SET on every plan except Order 01, which amends specs and so declares each spec file in `- Scope-Paths:` instead. The Set amends `25kzda` rather than being produced from it, and Order 08 counts real `From-Spec` links as a spec's handoff output, so a real link would be wrong. Today `check.plan-spec-link-missing` (info) still nudges on `none`; Order 13 makes `none` and a declared spec edit answer it.
  THIS PLAN CARRIES ORCHESTRATION AND NOTHING ELSE. Every whole-Set obligation below names the child that performs it, including the end-to-end measurement (Order 12) and the re-check of the existing 13 orchestrators (Order 09), precisely because a runner retiring this plan skips its own E/V checkpoint.

## Goal

After this Set, graduating a backlog item or producing plans from a spec either hands off a Set the next run accepts, or fails visibly with the backlog item still `open` and the exact sentence that needs an owner. An orchestrator plan cannot reach `to-review`, `reviewed` or `approved` while its children are missing, unready, or while it carries work no child covers, and the coverage probe only runs where its answer can change what a run does.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: sequence the Set

- [ ] E-01 CONFIRM hm1h3l REACHED executed
  - Depends on: none
  - Expected outcome: hm1h3l reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-02 CONFIRM 8mabmu REACHED executed
  - Depends on: E-01
  - Expected outcome: 8mabmu reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-03 CONFIRM qs00nc REACHED executed
  - Depends on: E-02
  - Expected outcome: qs00nc reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-04 CONFIRM 5etev3 REACHED executed
  - Depends on: E-03
  - Expected outcome: 5etev3 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-05 CONFIRM 26m1nb REACHED executed
  - Depends on: E-03
  - Expected outcome: 26m1nb reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-06 CONFIRM r2wa38 REACHED executed
  - Depends on: E-03
  - Expected outcome: r2wa38 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-07 CONFIRM nnsa2o REACHED executed
  - Depends on: E-06
  - Expected outcome: nnsa2o reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-08 CONFIRM 24qw39 REACHED executed
  - Depends on: E-05, E-07
  - Expected outcome: 24qw39 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-09 CONFIRM 52opph REACHED executed
  - Depends on: E-05, E-08
  - Expected outcome: 52opph reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-10 CONFIRM sbiv1j REACHED executed
  - Depends on: E-05, E-06, E-09
  - Expected outcome: sbiv1j reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-11 CONFIRM dalmk4 REACHED executed
  - Depends on: E-04, E-05, E-06, E-10
  - Expected outcome: dalmk4 reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-12 CONFIRM wytlly REACHED executed
  - Depends on: E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-10, E-11
  - Expected outcome: wytlly reads `- Status: executed` on disk.
  - Execution state: pending

- [ ] E-13 CONFIRM jm27py REACHED executed
  - Depends on: none
  - Expected outcome: jm27py reads `- Status: executed` on disk.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | Plan | Purpose | Depends on |
| --- | --- | --- | --- | --- |
| 01 | hm1h3l | `.aw/records/plans/pending/20261004-gradcover-01-hm1h3l-amend-the-run-retirement-conformance-and-ipd-specs-for-orche.ipd.md` | Amend specs `25kzda` (2.5b, 3.2, 3.3, 3.4, 4.4, 4.8, 4.9, 5.5), `77tr3o` (R-12 and a new R-13), `r07vma` (R9, Section 3a limits 1 and 5), `ipd-structure-and-linting` (the linter's orchestrator review-readiness rule and the coverage-record attestation rule) and `ipd-spec` (loud, loop-free demotion), and add `25kzda` 2.5e (the coverage answer is stored in the plan) so every later child implements an approved contract rather than inventing one. Edits specs only. | none |
| 02 | 8mabmu | `.aw/records/plans/pending/20261004-gradcover-02-8mabmu-make-the-coverage-probe-quote-the-work-it-found-and-credit-w.ipd.md` | Change the probe's answer to a verdict line plus a verbatim quote of each uncovered passage, credit work the orchestrator explicitly assigns to a child in its own `## Child IPDs` table, record the answer and its quotes IN THE PLAN (`- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:`, `## Coverage findings`) instead of the gitignored 30-day cache, and surface them in the refusal and in `aw runs`. | `executed:hm1h3l` |
| 03 | qs00nc | `.aw/records/plans/pending/20261004-gradcover-03-qs00nc-add-one-shared-orchestrator-review-readiness-check-and-the-a.ipd.md` | Add ONE function that decides whether an orchestrator plan is ready for review (children exist, children ready, rows conform, coverage passes), an `aw ipd coverage` verb that runs the probe on demand and records the answer in the plan, an attestation lint rule for that record (`IPD-M112`), an `aw ipd lint` rule, and an `aw check` rule; every later gate calls this one function. | `executed:8mabmu` |
| 04 | 5etev3 | `.aw/records/plans/pending/20261004-gradcover-04-5etev3-run-the-coverage-probe-only-where-a-run-can-retire-an-orches.ipd.md` | Probe at run start only the orchestrators whose action in this run is `orchestrate`, and re-run the check inside `dispatch_orchestrator_item` immediately before retirement, so a `--action review` run is never blocked and a retirement is never unchecked. | `executed:qs00nc` |
| 05 | 26m1nb | `.aw/records/plans/pending/20261004-gradcover-05-26m1nb-refuse-aw-ipd-set-to-review-reviewed-and-approved-for-an-orc.ipd.md` | Make `aw ipd set to-review|reviewed|approved` refuse an orchestrator plan the shared check rejects, with a precise human and `aw.agent/v1` refusal; order a Set-wide transition children-first; make every backward move legal, reasoned and loud; pin with a test that `aw ipd scaffold --kind orchestrator` writes `- Status: draft` (it already does, `ipd_authoring` writes `"- Status: draft"`). | `executed:qs00nc` |
| 06 | r2wa38 | `.aw/records/plans/pending/20261004-gradcover-06-r2wa38-check-the-whole-set-before-a-production-action-hands-off-a-b.ipd.md` | Add the `BACKLOG-GRADUATE-SET` and `SPEC-PLAN-SET` verification codes to the production path so a produced orchestrator that fails the shared check fails the item, leaves the source `open`/`approved`, preserves the lane, and records the passing answer in the orchestrator when it succeeds. | `executed:qs00nc` |
| 07 | nnsa2o | `.aw/records/plans/pending/20261004-gradcover-07-nnsa2o-send-a-refused-production-or-review-action-back-for-bounded.ipd.md` | When the Set-level check (or the shared check after an orchestrator review) refuses, resume the same agent session with a correction packet naming each quoted passage, up to the run's `--retry-budget`, then fail honestly. | `executed:r2wa38` |
| 08 | 24qw39 | `.aw/records/plans/pending/20261004-gradcover-08-24qw39-let-a-production-action-resume-an-unfinished-handoff-instead.ipd.md` | Let a production action over an `open` backlog item (or `approved` spec) whose existing plans are unfinished CONTINUE them instead of refusing with `BACKLOG-GRADUATE-COUNT`'s duplicate-active branch, hand the agent the list of existing plans with their failures, and commit the agent's edits to those plans. | `executed:nnsa2o`, `executed:26m1nb` |
| 09 | 52opph | `.aw/records/plans/pending/20261004-gradcover-09-52opph-re-check-every-pending-orchestrator-and-send-the-failing-one.ipd.md` | Run `aw ipd coverage` over every pending orchestrator plan, record the answer in each plan, return each failing orchestrator and its children to `draft`, reopen its backlog item to `open`, and write the measured results into this plan's evidence so the per-Set fixes can be done by resumed graduation. Measures but never demotes this Set's own plans. | `executed:24qw39`, `executed:26m1nb` |
| 10 | sbiv1j | `.aw/records/plans/pending/20261004-gradcover-10-sbiv1j-refuse-aw-backlog-set-graduated-and-aw-specs-set-implementin.ipd.md` | Make `aw backlog set graduated` (both spellings) and `aw specs set implementing` refuse while any plan naming the source in `- From-Backlog:` / `- From-Spec:` is not ready, and add `check.graduation-incomplete` for the reverse drift, grandfathered by a stamped cutover. Ordered after Order 09 so the existing graduated items are reopened before the check would flag them. | `executed:52opph`, `executed:26m1nb`, `executed:r2wa38` |
| 11 | dalmk4 | `.aw/records/plans/pending/20261004-gradcover-11-dalmk4-state-the-orchestrator-coverage-rule-in-the-production-promp.ipd.md` | State the coverage rule where authors read it: both production prompts, the orchestrator skeleton's placeholders, the managed `AGENTS.md` block in `engine.py` and the installed `AGENTS.md`, and the `/plan-review` workflow. | `executed:26m1nb`, `executed:5etev3`, `executed:r2wa38`, `executed:sbiv1j` |
| 12 | wytlly | `.aw/records/plans/pending/20261004-gradcover-12-wytlly-prove-end-to-end-that-a-graduation-yields-an-orchestrator-th.ipd.md` | The Set's final cross-child measurement: drive a real graduation of a fixture backlog item through the runner with a scripted host, then a review run and an orchestrate run over the result, proving both the refusal path and the success path end to end; own the cross-surface ONE PREDICATE parity check (its E-05); run the bare suite. | `executed:sbiv1j`, `executed:dalmk4`, `executed:5etev3`, `executed:nnsa2o`, `executed:24qw39`, `executed:26m1nb`, `executed:r2wa38`, `executed:qs00nc`, `executed:8mabmu` |
| 13 | jm27py | `.aw/records/plans/pending/20261004-gradcover-13-jm27py-stop-the-from-spec-nudge-for-a-plan-that-declares-no-spec-so.ipd.md` | Make `check.plan-spec-link-missing` treat a written `- From-Spec: none` / `-` and a declared edit of the cited spec as answers, so it fires only when the relationship is undeclared. Independent of every other child. | none |

## Completion criteria (the whole Set is done only when)

1. A production action that writes an orchestrator plan the shared review-readiness check rejects ends `fail-gate` with the source backlog item still `open` (or the source spec still `approved`), names each uncovered passage verbatim, and preserves its lane. Owner: `r2wa38` implements it, `wytlly` measures it end to end.
2. After the bounded correction turns are spent, the item fails honestly rather than passing; when a correction succeeds, the source reaches `graduated` / `implementing` and a coverage pass matching the orchestrator's current text is recorded in the orchestrator plan itself, so the next run makes no probe call for it. Owner: `nnsa2o` implements it, `wytlly` measures it.
3. `aw ipd set to-review`, `reviewed` and `approved` refuse an orchestrator plan whose children are missing, below `to-review`, failing lint, whose rows do not conform, or whose coverage record is absent, out of date or a fail, and each refusal line names the child or passage and the exact fix. Owner: `26m1nb`.
4. `aw ipd lint --phase review-finalize` and `aw check plans` report the same orchestrator readiness findings as the setter, because all three call the one function. Owner: `qs00nc` implements it; `wytlly` E-05 measures parity across every surface.
5. `aw backlog set graduated` and `aw specs set implementing` refuse while a plan naming the source is not ready, on both setter spellings, and `check.graduation-incomplete` reports an already-`graduated` item (graduated on or after its stamped cutover) whose plan has fallen back. Owner: `sbiv1j`.
6. A `--action review` run over a queue containing orchestrator plans makes no coverage probe call and is not refused by the coverage gate; an orchestrate run still probes, and a retirement re-checks immediately before it happens. Owner: `5etev3`.
7. Every refusal and every `aw runs` row the probe produces quotes the passage it judged uncovered, and work explicitly assigned to a child in the orchestrator's own child table is not reported as uncovered. Owner: `8mabmu`.
8. Every pending orchestrator plan in the repository carries a committed coverage record; each one that fails is `draft` with its backlog item `open`, including any that were `approved`, whose withdrawn approvals are named. Owner: `52opph`.
9. The production prompts, the orchestrator skeleton, the managed `AGENTS.md` block and `/plan-review` state the rule that every whole-Set obligation names the child that performs it. Owner: `dalmk4`.
10. The amendments to the five specs Order 01 edits are in place and each child cites the amended section it implements. Owner: `hm1h3l`.
11. `check.plan-spec-link-missing` stays silent for a plan declaring `- From-Spec: none` or editing the cited spec, and still fires when the link is undeclared. Owner: `jm27py`.
12. Every backward plan status move requires a reason, warns, and records `APPROVAL WITHDRAWN` when it leaves `approved`; a second move on unchanged text is refused. Owner: `26m1nb`.
13. The bare suite shows no new failing node id at any child boundary. Owner: each child for its own boundary; `wytlly` for the final run.

## Cross-IPD validation

- ONE PREDICATE. After Order 05, Order 06, Order 04 and Order 10, every place that decides orchestrator readiness calls the single function Order 03 adds. Owner: `wytlly` E-05/V-05, which drives each surface (`aw ipd set`, `aw ipd lint --phase review-finalize`, `aw check plans`, a production run, a retirement) against the SAME fixture orchestrator and asserts the same finding code and quote on each. This is checked by outcome, never by reading source.
- NO CHILD MAY DELETE AN ORCHESTRATOR'S CHECKLIST to make a check pass, and no remedy text added by any child may suggest it. `r07vma` R2 and R7 bind every message this Set adds.
- NO CHILD MAY WEAKEN THE CHECK AT RETIREMENT. Order 04 moves the probe's run-start call; it must ADD the retirement-time call in the same change, so there is no commit in which an orchestrate run retires an orchestrator without a check.
- THE COULD-NOT-ASK RULE IS PRESERVED EXACTLY WHERE IT EXISTS TODAY (`25kzda` 2.5b, a run-time availability failure warns and proceeds), and Order 01 records the new and DIFFERENT rule for the setter and production paths (an unavailable probe leaves the plan or source where it is, because nothing has started and refusing costs nothing).
- DEMOTION IS LOUD AND CANNOT LOOP. After Order 05 every backward plan move requires a reason and warns, and Order 09's demotions use it; confirm by outcome that a promote, demote, promote sequence on unchanged text refuses the second promotion (Order 05 OQ-03).
- ORDER 05 PRECEDES ORDER 09, DECLARED. Order 09's demotions need the backward `aw ipd set draft --message` edge Order 05 adds; Order 09 declares `executed:26m1nb` directly (Order 08 now also declares it, since its continue prompt uses the same edge). Likewise Order 12 asserts Order 04's behavior and declares `executed:5etev3`.
- ORDER 09 NEVER DEMOTES THIS SET. This Set's own orchestrator and unexecuted children are pending while Order 09 runs; Order 09 measures them and stops and reports if `1f4faf` is not ready, rather than returning a mid-execution Set to `draft`.
- ORDER 09 PRECEDES ORDER 10. Order 10 makes `check.graduation-incomplete` an `aw check` error; if it landed first, the 11 already-`graduated` items whose orchestrators fail would turn `aw check` red in CI before they were reopened.
- EACH CHILD RE-MEASURES ITS OWN SUITE BASELINE. No child trusts a baseline written at authoring.
- THIS SET BECOMES SUBJECT TO ITS OWN GATE MID-EXECUTION. From the moment Order 03 (`qs00nc`) lands, this orchestrator is a pending `Kind: orchestrator` plan with no coverage record, so `check.orchestrator-not-review-ready` reports it, and if it is `approved` a NEW run (a resume or a second `aw oc run gradcover`) is refused whole at freeze time by `IPD-S408` at `pre-execution` (`runner_shared.enforce_freeze_time_refusal` lints approved IPDs at that checkpoint). That refusal is loud and names its own remedy, `aw ipd coverage 1f4faf`, an ordinary operator act and not work of this plan; Order 09 (`52opph`) records this plan's answer durably; and the retirement-time re-check (Order 04, `5etev3`) asks if no current record exists. A run already in progress is unaffected, because the freeze gate runs once at run start.

## Deferred / out of scope (with reason)

- THE `C-*` REQUIREMENT IDS WITH `Owner:` / `Covers:` FIELDS discussed with the maintainer 2026-10-04, which would make coverage a deterministic two-sided check. Deferred deliberately: it changes the IPD format, it overlaps the record-model redesign the maintainer asked to discuss next, and Order 02's named-owner rule plus Order 03's shared check close the false refusals and the missing gate without a format change.
  - Carrier-Declined: maintainer sequencing on 2026-10-04 ("address the issue with uncovered children being generated when graduating ... THEN let's talk about re-architecting"); to be reconsidered in that design discussion
- THE RECORD-MODEL REDESIGN (base record object, `Plan` / `PlanSet` classes, one parser) and whether it ships as a fork or a separate command set. Out of scope by the maintainer's explicit ordering.
  - Carrier-Declined: maintainer ordering on 2026-10-04; the next conversation, not this Set
- FIXING EACH OF THE 13 REFUSED ORCHESTRATORS' CONTENT. Order 09 measures and reopens them; the actual per-Set fix (a new child, or an owner sentence) is done by re-running graduation on each reopened backlog item after this Set lands, which Order 08 makes possible. Writing 13 Set-specific fixes inside this Set would be 13 unrelated scopes.
  - Carrier-Declined: each reopened backlog item carries its own fix through a resumed graduation; Order 09 records which ones
- A GENERAL DETECTOR THAT DEMOTES ANY APPROVED PLAN WHOSE SPEC, SCOPE, DEPENDENCIES OR CITED CODE CHANGED MATERIALLY SINCE APPROVAL. The maintainer ruled on 2026-10-04 that such a plan MUST be demoted loudly. This Set makes that demotion legal, loud and loop-free (Orders 01 and 05) and applies it to orchestrators that fail readiness (Order 09); detecting material change for ANY plan is a separate mechanism (what counts as material, which inputs to fingerprint at approval) with its own design questions.
  - Carrier-Declined: to be specified separately at the maintainer's direction; this Set supplies the legal, loud, loop-free demotion it will use

## Scope check

- Over-scope: none. This plan's `- Scope-Paths:` lists only the thirteen child plan files it sequences. It declares no source file, no test file and no spec, because it changes none.
- Under-scope: nothing is parked on this plan. The end-to-end measurement is Order 12, the existing-corpus re-check is Order 09, and the spec amendments are Order 01. The checklist contains only typed child-tracking rows.
- IF A REVIEWER FINDS UNCOVERED WORK, the remedy is to ADD A CHILD and a row to the table, not to add an item here and not to delete the checklist.

## Required tests / validation

This plan runs no tests of its own and ships no code. Each child validates itself with pasted evidence. The Set-level proof is Order 12 (`wytlly`): a scripted-host graduation driven through the real runner showing the refusal path, the correction path and the success path, followed by a review run and an orchestrate run over the produced Set, and a bare `python3 -m pytest` with its `N passed` line reconciled against a baseline that child measures itself.

## Open questions

### OQ-01: Should the Set be thirteen children, or fewer?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: thirteen (Order 13 was added 2026-10-04 at the maintainer's request). Each child touches one surface that can be reviewed and reverted alone: the specs (01), the probe's prompt and parser (02), a new shared function and verb (03), the run-start gate (04), the plan setter and scaffold (05), the production verifier (06), the correction loop (07), duplicate detection (08), a records-only sweep (09), the backlog and spec setters (10), authoring text (11), the end-to-end proof (12), and the `From-Spec` nudge (13). Merging 02 and 03 was considered and rejected because 02 changes a cached model contract (every verdict digest moves) while 03 adds new code paths; reviewing them together hides which change caused a regression.

### OQ-02: Should production failure leave the lane's plans on `main` as drafts, or keep them only in the preserved lane?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED from repository evidence: KEEP THEM IN THE PRESERVED LANE, which is what the shipped production path already does on any finding (`lane_containment.record_lane_preserved` is called and nothing integrates), and what `25kzda` 4.9 specifies ("FAIL ITEM after containment"). Order 08 makes a later production action find and continue that work. Integrating drafts onto `main` on failure would be a new behavior with no spec authority and would put unreviewed text into tracked history.

### OQ-03: Condition 4 (a recorded coverage verdict) is machine-local, so how should the model-free consumers treat a missing verdict?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-006
- Resolution or deferral rationale: RESOLVED 2026-10-04 by the maintainer, in session: STORE THE ANSWER IN THE PLAN ITSELF, so it is no longer machine-local. Specified in `25kzda` 2.5e (Order 01 `hm1h3l`), implemented by Order 02 `8mabmu` (`coverage_record`, the probe reading and writing the record, the cache retired) and Order 03 `qs00nc` (`IPD-M112`, which refuses a hand-written or incomplete record). Because every clone and CI read the same record, an absent or out-of-date record is an error in `aw ipd lint` and `aw check` without any CI or freeze-gate breakage. The fingerprint is stored beside the answer so an edit after a pass is reported as "plan changed since the check" instead of being silently trusted.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -m1 -n '^- Status:' <hm1h3l plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -m1 -n '^- Status:' <8mabmu plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `grep -m1 -n '^- Status:' <qs00nc plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `grep -m1 -n '^- Status:' <5etev3 plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `grep -m1 -n '^- Status:' <26m1nb plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `grep -m1 -n '^- Status:' <r2wa38 plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `grep -m1 -n '^- Status:' <nnsa2o plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `grep -m1 -n '^- Status:' <24qw39 plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `grep -m1 -n '^- Status:' <52opph plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `grep -m1 -n '^- Status:' <sbiv1j plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `grep -m1 -n '^- Status:' <dalmk4 plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste `grep -m1 -n '^- Status:' <wytlly plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `grep -m1 -n '^- Status:' <jm27py plan path>` showing `- Status: executed`, and the path showing it under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: The orchestrator carries 13 typed child-tracking rows, one per child, which is within the 18-leaf threshold but exceeds the usual Set width; every row is a status confirmation and none carries work. The breadth reflects twelve independently reviewable surfaces, not one large change, and splitting the Set into two Sets would sever the Order 09 before Order 10 ordering that keeps `aw check` green.

This plan requires explicit human approval before execution. It performs no work itself: under `aw oc run` / `aw agy run` the runner retires it once every child is `executed`; run by hand, the executor confirms each child in order and stops at the first that did not reach `executed`. The terminal transition is owned by the runner under a runner and by `aw ipd finalize` by hand; never hand-edit `- Status: executed` and never `git mv` it. Every `V-*` above demands the ACTUAL pasted command output, never a paraphrase. A hand executor commits only this plan's file through `aw commit <this plan> -- <path>`, and never pushes.
