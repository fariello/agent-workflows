# IPD: Re-check every pending orchestrator and send the failing ones back for completion

- Date: 2026-10-04
- Kind: child
- Concern: Sixteen orchestrator plans are pending at authoring: 13 at `to-review` (`i18yaz`, `u4glub`, `z2l43n`, `1u4olp`, `63zo2f`, `itamry`, `u57rfv`, `4qv834`, `l8wvv3`, `qtz0us`, `axozpe`, `m0kl28`, `xhr0dj`), all refused by the old probe on 2026-10-03, and 3 at `approved` (`95jk4s`, `l4vw9o`, `9wzlou`). Eleven of the 13 come from backlog items already `graduated` (`ildjse`, `dvonrn`, `eeiytw`, `7yz545`, `fcnz1r`, `mflqqf`, `s8veyk`, `ariaau`, `rgl2d4`, `sv9ce4`, `qbz8i1`); `itamry`'s `0livgf` and `l8wvv3`'s `h0tiaw` are `open`. The old verdicts came from a prompt with no named-child credit and no quotes (Order 02 discards them by bumping the store schema), so some of the 13 are false refusals and some are real; nobody can tell which until they are re-probed under the new contract. After Orders 03 and 05, any that still fail are `to-review` in violation of the new rule and turn `aw check plans` red (Order 03's `check.orchestrator-not-review-ready`); after Order 10, their `graduated` backlog items would also be flagged. This plan measures every pending orchestrator and makes the records truthful.
- Scope: RECORDS ONLY. IN: run `aw ipd coverage` over every pending orchestrator plan, recording a verdict for each; for each NOT-ready orchestrator at `to-review` or `reviewed`, return it and every child of its Set that is not `executed` to `draft` with `aw ipd set draft <id6> --message "<findings>"` (children first is not required for a backward move), and set its source backlog item from `graduated` back to `open` with `aw backlog set open <id6> --message "<orchestrator id6> not ready for review: <findings>"` (a source spec at `implementing` is set back to `approved` the same way, if any); for each NOT-ready orchestrator at `approved`, change nothing and record it for the maintainer; paste every verdict and every quoted finding into this plan's evidence. OUT: fixing any orchestrator's content (done afterwards by re-running graduation on each reopened item, which Order 08 makes possible); any code change; demoting an `approved` plan; touching any plan outside the affected Sets.
- Scope-Paths: .aw/records/plans/pending/, .aw/records/backlog/open/, .aw/records/backlog/graduated/, .aw/records/specs/approved/, .aw/records/specs/implementing/
- Item-Dependencies: executed:24qw39
- Status: to-review
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 9
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 52opph

## Workflow history

- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 09 of Set `gradcover`. Placed after Order 08 so a reopened backlog item can be re-graduated by continuing its existing plans, and before Order 10 so `check.graduation-incomplete` never fires on items this plan is about to reopen. The maintainer agreed on 2026-10-04 that the 13 refused orchestrators are re-checked and, where still failing, returned to `draft`.

## Goal

Leave every pending orchestrator plan with a recorded verdict under the new probe contract, and make the records match it: an orchestrator that is not ready for review is `draft`, its unexecuted children are `draft`, and its backlog item is `open`, each with the quoted reason in its history.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measure

- [ ] E-01 Re-derive the population at execution time (do not trust the list in Concern): every plan under `.aw/records/plans/pending/` whose metadata `- Kind:` is `orchestrator` (read with `ipd_lint.parse`, never a whole-file substring scan). Run `python3 -m agent_workflows ipd coverage <id6> --agent` for each and save every record. Build a table: orchestrator id6, status, source backlog or spec id6 and its status, ready yes/no, and each finding (code, subject, quoted passage).
  - Depends on: none
  - Expected outcome: one recorded verdict per pending orchestrator, and the table pasted into V-01.
  - Execution state: pending

### Task group 2: make the records truthful

- [ ] E-02 For each NOT-ready orchestrator whose status is `to-review` or `reviewed`: set every child of its Set that is not `executed` to `draft`, then the orchestrator, using `aw ipd set draft <id6> --message "returned to authoring by gradcover 52opph: <one-line findings summary>"`. Do not touch an `executed` child. Commit through `aw commit <this plan> -- <paths>`.
  - Depends on: E-01
  - Expected outcome: every such orchestrator and its unexecuted children read `- Status: draft` with the history line; no executed plan changed.
  - Execution state: pending

- [ ] E-03 For each orchestrator demoted in E-02, set its source back: a `graduated` backlog item to `open` with `aw backlog set open <id6> --message "<orchestrator id6> returned to authoring: <summary>; re-run graduation to complete the handoff"`; a source spec at `implementing` to `approved` with `aw specs set <path> --status approved --message ...` only if that transition is legal under the spec setter, otherwise record it for the maintainer. Leave an already-`open` item unchanged and append a note instead (`aw backlog set` with the same status and a message, which records a same-status history line).
  - Depends on: E-02
  - Expected outcome: every affected backlog item reads `- Status: open` with the history line; `aw check backlog` and `aw check release-gates` report no new finding (the `Blocks-Release` gate is unchanged).
  - Execution state: pending

- [ ] E-04 For each NOT-ready orchestrator at `approved`, change nothing; list it with its findings in V-04 and in the final report as a maintainer decision (demoting it would withdraw a human approval). Then run `python3 -m agent_workflows check plans` and confirm `check.orchestrator-not-review-ready` reports only those `approved` ones, if any.
  - Depends on: E-03
  - Expected outcome: `aw check plans` lists no `to-review`/`reviewed` orchestrator under `check.orchestrator-not-review-ready`; any `approved` one is listed and named in the report.
  - Execution state: pending

## Project conventions discovered (Step 0)

- STATUS CHANGES GO THROUGH THE SETTERS, never text edits (`25kzda` 3.3 / `z7nbn1` 3.3). `aw ipd set draft` requires the backward edges Order 05 adds (E-05 of `26m1nb`).
- `graduated -> open` IS LEGAL for a backlog item (`attention_contract.BACKLOG_TRANSITIONS['graduated']` contains `open`).
- `aw ipd coverage` SPENDS A MODEL CALL PER ORCHESTRATOR on a cache miss; with Order 02's schema bump every pending orchestrator is a miss. At authoring that is 16 calls.
- SHARED CHECKOUT. Other agents may be editing these plans; re-read each plan immediately before setting it and stop on a conflicting concurrent edit (`AGENTS.md`, "Shared checkout").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | 16 pending orchestrators: 13 `to-review`, 3 `approved`, 0 `reviewed`, 0 `draft`. | `grep -l '^- Kind: orchestrator' .aw/records/plans/pending/*.md` and a status count, 2026-10-03 |
| F-02 | Conditions 1 and 2 of `25kzda` 2.5d pass for all 16 at authoring: every child-table row resolves to a plan at `to-review` or later. So any refusal will come from coverage (condition 4) or rows (condition 3). | a script resolving each orchestrator's `## Child IPDs` ids to plan statuses, printing no failures for all 16 |
| F-03 | Source statuses: 11 `graduated`, 2 `open`. Two orchestrators also carry `- From-Spec:` (`63zo2f` from `wy9aru`, `m0kl28` from `25kzda`); `25kzda` is `approved`, so no spec rollback applies to it. | `- From-Backlog:` / `- From-Spec:` values and their targets' `- Status:` |
| F-04 | `to-review -> draft` is illegal today (`validate_transition` returns `ok=False`). Order 05 adds the edge; this plan depends on it transitively through Order 08. | `ipd_lifecycle.validate_transition('to-review','draft')` measured 2026-10-04 |

## Proposed changes (ordered, validatable)

1. Re-derive the population and record a verdict for each (E-01).
2. Demote not-ready `to-review`/`reviewed` orchestrators and their unexecuted children to `draft` (E-02).
3. Reopen their sources (E-03).
4. Report not-ready `approved` orchestrators for a maintainer decision and confirm `aw check plans` (E-04).

## Deferred / out of scope (with reason)

- FIXING EACH ORCHESTRATOR. After this plan, re-run `aw oc run <backlog-id6>` on each reopened item; Orders 06 to 08 make that continue the existing plans, check the Set, and correct within budget.
  - Carrier-Declined: per-Set authoring is done by each item's own resumed graduation, not by this records sweep
- DEMOTING AN `approved` ORCHESTRATOR. A human approval is involved.
  - Carrier-Declined: reserved to the maintainer; reported in V-04

## Scope check

- Over-scope: none. Scope-Paths are the record directories the setters write into; no code.
- Under-scope: after this plan the reopened items still need their graduations re-run; that is ordinary use of the fixed runner, not part of this Set.

## Required tests / validation

- Every `aw ipd coverage --agent` record pasted (or saved to the run evidence and summarized in a table with one row per orchestrator).
- `python3 -m agent_workflows check plans`, `check backlog` and `check release-gates`, each pasted before and after.
- `python3 -m agent_workflows attention --format json` before and after, showing the moved items' classes.
- `git diff --name-only` pasted, listing only plan and backlog (and, if any, spec) record files.
- `aw ipd lint` on this plan conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec or document is edited. The records are brought into line with spec `25kzda` 2.5d and `77tr3o` R-13 as amended by Order 01.

## Open questions

### OQ-01: Should a not-ready orchestrator's children also go to `draft`, or stay `to-review`?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: to `draft`, except executed ones. A child at `to-review` under a `draft` orchestrator would be reviewed and possibly approved and executed while its Set is known to be incomplete, which is how work gets reported done for a Set that is not. Returning the Set to `draft` together keeps the Set's state honest; the children's content is unchanged, so a resumed graduation can promote them again in one `aw ipd set to-review <setid>` (Order 05 E-02).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the population command and its output, then the table (one row per orchestrator: id6, status, source and source status, ready, findings with quotes). Paste the count of `aw ipd coverage` calls that hit the model versus the cache.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste each `aw ipd set draft` command and its output. Paste `grep -n '^- Status:'` for every demoted plan showing `draft`, and the new history line on each. Paste `git diff --name-only` showing no file under `.aw/records/plans/executed/` changed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste each `aw backlog set open` (and any spec setter) command and output; `grep -n '^- Status:\|^- Blocks-Release:'` for each reopened item showing `open` and its gate unchanged; `aw check backlog` and `aw check release-gates` before and after with no new finding.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m agent_workflows check plans` after, showing which orchestrators (if any) `check.orchestrator-not-review-ready` lists, and confirm each listed one is `approved`; paste the list of not-ready `approved` orchestrators with their findings for the maintainer. Paste `aw attention --format json` before and after for the moved items. Paste `aw ipd lint` on this plan conforming, `aw sanitize --agent`, and `git diff --cached --name-only` immediately before committing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Records only. Commit through `aw commit <plan> -- <paths>`, naming each changed record file; never push. Spends one model call per pending orchestrator. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
