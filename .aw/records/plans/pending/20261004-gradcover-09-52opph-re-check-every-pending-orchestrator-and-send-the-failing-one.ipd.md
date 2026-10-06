# IPD: Re-check every pending orchestrator and send the failing ones back for completion

- Date: 2026-10-04
- Kind: child
- Concern: Sixteen orchestrator plans are pending at authoring: 13 at `to-review` (`i18yaz`, `u4glub`, `z2l43n`, `1u4olp`, `63zo2f`, `itamry`, `u57rfv`, `4qv834`, `l8wvv3`, `qtz0us`, `axozpe`, `m0kl28`, `xhr0dj`), all refused by the old probe on 2026-10-03, and 3 at `approved` (`95jk4s`, `l4vw9o`, `9wzlou`). The maintainer ruled on 2026-10-04 that an approved plan which is not safe to execute MUST be demoted loudly, so an approved orchestrator that fails is demoted like the rest. Eleven of the 13 come from backlog items already `graduated` (`ildjse`, `dvonrn`, `eeiytw`, `7yz545`, `fcnz1r`, `mflqqf`, `s8veyk`, `ariaau`, `rgl2d4`, `sv9ce4`, `qbz8i1`); `itamry`'s `0livgf` and `l8wvv3`'s `h0tiaw` are `open`. The old verdicts came from a prompt with no named-child credit and no quotes (Order 02 discards them by bumping the store schema), so some of the 13 are false refusals and some are real; nobody can tell which until they are re-probed under the new contract. After Orders 03 and 05, any that still fail are `to-review` in violation of the new rule and turn `aw check plans` red (Order 03's `check.orchestrator-not-review-ready`); after Order 10, their `graduated` backlog items would also be flagged. This plan measures every pending orchestrator and makes the records truthful.
- Scope: RECORDS ONLY. IN: run `aw ipd coverage` over every pending orchestrator plan, which records the answer IN EACH PLAN (`25kzda` 2.5e), and commit those plan edits; for each NOT-ready orchestrator at `to-review` or `reviewed`, return it and every child of its Set that is still in `pending/` to `draft` with `aw ipd set draft <id6> --message "<findings>"` (children first is not required for a backward move; every backward move requires `--message`), and set its source backlog item from `graduated` back to `open` with `aw backlog set open <id6> --message "<orchestrator id6> not ready for review: <findings>"` (a source spec at `implementing` is set back to `approved` the same way, if any); for each NOT-ready orchestrator at `approved` or `auto-approved`, demote it the same way (loudly, recording `APPROVAL WITHDRAWN`), because an approved Set that is not ready is unsafe to execute; paste every verdict and every quoted finding into this plan's evidence. EXCLUDED FROM DEMOTION: every plan of Set `gradcover` itself (this plan's own Set, including orchestrator `1f4faf`); record its verdict, and if it is not ready STOP and report the quoted findings to the maintainer rather than demoting a Set that is mid-execution. OUT: fixing any orchestrator's content (done afterwards by re-running graduation on each reopened item, which Order 08 makes possible); any code change; touching any plan outside the affected Sets.
- Scope-Paths: .aw/records/plans/pending/, .aw/records/backlog/open/, .aw/records/backlog/graduated/, .aw/records/specs/approved/, .aw/records/specs/implementing/
- Item-Dependencies: executed:24qw39, executed:26m1nb
- Status: reviewed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 9
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 52opph

## Workflow history
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 (all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-008. Fixed: E-01 drops the `--commit` flag `qs00nc` replaced with default-commit plus `--no-commit` (PR-001); a could-not-ask or unusable answer never demotes (PR-002); terminal-directory children (`not-executed`, `superseded`) are never set and a finding naming a child outside the `## Child IPDs` table stops for the maintainer, since `l4vw9o`'s Set holds a `not-executed` child not in its table (measured) (PR-003); a plan queued or held in a lane by an active run is not demoted (PR-004); one setter-plus-commit discipline including the backlog file's move across directories (PR-005); withdrawn approvals listed per child with the executed/demoted split for partly executed Sets (PR-006); spec-source facts re-measured (PR-007); gate contract (PR-008).
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): wording updated for the maintainer ruling 2026-10-04: `aw ipd coverage` now writes each answer into the plan, and the sweep commits those edits.

- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of orchestrator `1f4faf` (findings PR-003, PR-004): added `executed:26m1nb` to `- Item-Dependencies:` because the backward `aw ipd set draft --message` edge this plan uses is added by Order 05 and was not reachable through the Order 08 chain; excluded Set `gradcover`'s own plans from demotion so this sweep cannot return its own mid-execution Set to `draft`.
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 09 of Set `gradcover`. Placed after Order 08 so a reopened backlog item can be re-graduated by continuing its existing plans, and before Order 10 so `check.graduation-incomplete` never fires on items this plan is about to reopen. The maintainer agreed on 2026-10-04 that the 13 refused orchestrators are re-checked and, where still failing, returned to `draft`.

## Goal

Leave every pending orchestrator plan carrying a recorded coverage answer under the new probe contract, and make the records match it: an orchestrator that is not ready for review is `draft`, its unexecuted children are `draft`, and its backlog item is `open`, each with the quoted reason in its history, and every withdrawn approval is named in the report.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measure

- [ ] E-01 Re-derive the population at execution time (do not trust the list in Concern): every plan under `.aw/records/plans/pending/` whose metadata `- Kind:` is `orchestrator` (read with `ipd_lint.parse`, never a whole-file substring scan). Run `python3 -m agent_workflows ipd coverage <id6> --agent` for each (it commits each recorded answer itself, one path-scoped commit per plan, `8mabmu` E-07 / `qs00nc` E-03; there is no `--commit` flag, only `--no-commit`, which must NOT be passed here) and save every record. An orchestrator whose answer is `could-not-ask` or `unknown` (the probe could not be asked, or its answer was unusable) is NOT a not-ready verdict: retry it once later in the run, and if it still has no answer, leave it and its Set exactly as they are and list it in the report as unmeasured. Likewise an orchestrator the tool skipped because its plan file had another party's uncommitted edit is unmeasured, not failed. Plans of Set `gradcover` are measured but are never demoted by E-02 or E-03 (if `1f4faf` is not ready, stop after E-01 and report its findings). Build a table: orchestrator id6, status, source backlog or spec id6 and its status, ready yes/no/unmeasured, and each finding (code, subject, quoted passage, verbatim). STOP AND REPORT, without demoting that Set, when a finding names a child that is NOT a row of the orchestrator's `## Child IPDs` table or that sits in a terminal directory: measured at review, Set `denypush` (`l4vw9o`, `approved`) holds `d5ntkj` under `not-executed/`, which is not in its table; spec `25kzda` 2.5d condition 2 judges the table's children, so such a finding would be an implementation defect in Order 03, and demoting an approved Set on it would withdraw an approval for a reason the contract does not give.
  - Depends on: none
  - Expected outcome: every measured pending orchestrator carries a committed `- Coverage:` record with its history line; every unmeasured one is named with its reason; the table is pasted into V-01.
  - Execution state: pending

### Task group 2: make the records truthful

- [ ] E-02 For each NOT-ready orchestrator OUTSIDE Set `gradcover` whose status is `to-review`, `reviewed`, `approved` or `auto-approved` (an unmeasured one from E-01 is never demoted): set every child of its Set that is in `pending/` and not already `draft` to `draft`, then the orchestrator, using `aw ipd set draft <id6> --message "returned to authoring by gradcover 52opph: <one-line findings summary>" --yes --no-commit`. Never set a child in a terminal directory (`executed/`, `superseded/`, `not-executed/`); the setter's terminal-reopen guard would refuse it, and it is not part of the unfinished work. BEFORE demoting a Set, run `python3 -m agent_workflows runs --active --agent` and skip (and report) any Set one of whose plans is queued or held in a lane by an active run, because demoting a plan under a live run strands that run's lane rather than stopping it. Re-read each plan immediately before its setter call. After the Set's setter calls, commit that Set's changed plan files in one `aw commit <this plan> -- <paths>` call naming each file, then verify with `git diff --cached --name-only` per the shared-checkout rule.
  - Depends on: E-01
  - Expected outcome: every such orchestrator and its pending children read `- Status: draft` with the setter's `demoted <from> -> draft` history line (and `APPROVAL WITHDRAWN` where the source was approved) and no `- Readiness:` line; no file under a terminal directory changed; every skipped Set is named with its reason.
  - Execution state: pending

- [ ] E-03 For each orchestrator demoted in E-02, set its source back: a `graduated` backlog item to `open` with `aw backlog set open <id6> --message "<orchestrator id6> returned to authoring: <summary>; re-run graduation to complete the handoff"`; a source spec at `implementing` to `approved` with `aw specs set <path> --status approved --message ...` (legal: `attention_contract.SPEC_TRANSITIONS['implementing']` contains `approved`, measured at review), otherwise record it for the maintainer. Measured at review, neither spec source is `implementing` (`25kzda` is `approved`; `wy9aru`, cited by `63zo2f`, is `to-review`), so no spec setter call is expected; re-derive at execution. `aw backlog set open` MOVES the item file from `backlog/graduated/` to `backlog/open/`, so the commit names both the old and the new path; pass `--message` and commit once after all items with `aw commit <this plan> -- <old and new paths>`. Leave an already-`open` item unchanged and append a note instead (`aw backlog set` with the same status and a message, which records a same-status history line).
  - Depends on: E-02
  - Expected outcome: every affected backlog item reads `- Status: open` with the history line; `aw check backlog` and `aw check release-gates` report no new finding (the `Blocks-Release` gate is unchanged).
  - Execution state: pending

- [ ] E-04 Report every APPROVAL WITHDRAWN by E-02 by id6 (orchestrators and children) with its findings quoted verbatim, so the maintainer can dispute a probe verdict, so the maintainer sees each approval that was withdrawn and why, then run `python3 -m agent_workflows check plans` and confirm `check.orchestrator-not-review-ready` reports nothing.
  - Depends on: E-03
  - Expected outcome: `aw check plans` lists no orchestrator under `check.orchestrator-not-review-ready` other than the unmeasured and skipped ones the report names; the report names every withdrawn approval (orchestrator AND child, by id6, with its previous status) and, for each partly executed Set, which children were already executed and which were demoted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- STATUS CHANGES GO THROUGH THE SETTERS, never text edits (`25kzda` 3.3 / `z7nbn1` 3.3). `aw ipd set draft` requires the backward edges Order 05 adds (E-05 of `26m1nb`).
- `graduated -> open` IS LEGAL for a backlog item (`attention_contract.BACKLOG_TRANSITIONS['graduated']` contains `open`).
- `aw ipd coverage` SPENDS A MODEL CALL PER ORCHESTRATOR whose plan has no current coverage record; since Order 02 moves the answer into the plan, every pending orchestrator starts with none. At authoring that is 16 calls.
- PARTLY EXECUTED SETS ARE IN THE POPULATION. Measured at review: `awrenamesel` (`95jk4s`) has 4 executed children and 1 `approved`; `denypush` (`l4vw9o`) 1 executed, 2 `approved`, 1 `not-executed`; `reqids` (`9wzlou`) 1 executed, 1 `approved`. Demoting such a Set halts its remaining work by design (maintainer ruling 2026-10-04); the report states the split.
- `aw ipd coverage` COMMITS EACH ANSWER ITSELF and skips a plan with another party's uncommitted edit (`8mabmu` E-07).
- SHARED CHECKOUT. Other agents may be editing these plans; re-read each plan immediately before setting it and stop on a conflicting concurrent edit (`AGENTS.md`, "Shared checkout").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | 16 pending orchestrators: 13 `to-review`, 3 `approved`, 0 `reviewed`, 0 `draft`. Re-measured at review (2026-10-06, `ipd_lint.parse` of each `- Kind:`): 17, the extra one being this Set's `1f4faf` (`reviewed`). | `grep -l '^- Kind: orchestrator' .aw/records/plans/pending/*.md` and a status count, 2026-10-03 |
| F-02 | Conditions 1 and 2 of `25kzda` 2.5d pass for all 16 at authoring: every child-table row resolves to a plan at `to-review` or later. So any refusal will come from coverage (condition 4) or rows (condition 3). | a script resolving each orchestrator's `## Child IPDs` ids to plan statuses, printing no failures for all 16 |
| F-03 | Source statuses: 11 `graduated`, 2 `open`. Two orchestrators also carry `- From-Spec:` (`63zo2f` from `wy9aru`, `m0kl28` from `25kzda`); `25kzda` is `approved`, so no spec rollback applies to it. Re-measured at review: also `9wzlou` from `25kzda`; `wy9aru` is `to-review`; the three approved orchestrators' backlog sources (`gyv9tf`, `oq05nc`, `vy20et`) are `graduated`; five sources carry `- Blocks-Release: next`. | `- From-Backlog:` / `- From-Spec:` values and their targets' `- Status:` |
| F-05 | Set `denypush` contains `d5ntkj` under `not-executed/`, which is not a row of `l4vw9o`'s `## Child IPDs` table. Conditions 1 and 3 pass for all 17 orchestrators (`find_unauthored_child_rows` returns no unauthored row; `orchestrator_row_conformance` conforming). | review script over `read_set_membership` and the two predicates |
| F-04 | `to-review -> draft` is illegal today (`validate_transition` returns `ok=False`). Order 05 (`26m1nb`) adds the edge and the `--message` requirement. The chain through Order 08 does NOT reach it (`24qw39` -> `nnsa2o` -> `r2wa38` -> `qs00nc`), so this plan declares `executed:26m1nb` directly (added by the 2026-10-04 review of `1f4faf`, PR-003). | `ipd_lifecycle.validate_transition('to-review','draft')` measured 2026-10-04 |

## Proposed changes (ordered, validatable)

1. Re-derive the population and record a coverage answer in each plan (E-01).
2. Demote not-ready orchestrators (any pre-execution status) and their pending children to `draft`, skipping unmeasured and run-held Sets (E-02).
3. Reopen their sources (E-03).
4. Report every withdrawn approval and confirm `aw check plans` (E-04).

## Deferred / out of scope (with reason)

- FIXING EACH ORCHESTRATOR. After this plan, re-run `aw oc run <backlog-id6>` on each reopened item; Orders 06 to 08 make that continue the existing plans, check the Set, and correct within budget.
  - Carrier-Declined: per-Set authoring is done by each item's own resumed graduation, not by this records sweep

## Scope check

- Over-scope: none. Scope-Paths are the record directories the setters write into; no code.
- Under-scope: after this plan the reopened items still need their graduations re-run; that is ordinary use of the fixed runner, not part of this Set.

## Required tests / validation

- Every `aw ipd coverage --agent` record pasted (or saved to the run evidence and summarized in a table with one row per orchestrator).
- `python3 -m agent_workflows check plans`, `check backlog` and `check release-gates`, each pasted before and after.
- `python3 -m agent_workflows attention --format json` before and after, showing the moved items' classes.
- `git diff --name-only` (and `git log --name-status` for this plan's commits) pasted, listing only plan and backlog (and, if any, spec) record files, with each backlog move shown as a rename.
- `python3 -m agent_workflows runs --active --agent` pasted before E-02.
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
  - Required evidence: paste the population command and its output, then the table (one row per orchestrator: id6, status, source and source status, ready/unmeasured, findings with quotes). Name every unmeasured orchestrator with its reason and every STOP raised for a finding outside the child table. Paste the count of `aw ipd coverage` calls that asked the model versus read a current record, and the commit that recorded the answers.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `runs --active` output, each `aw ipd set draft` command and its output (including the `DEMOTED` / `APPROVAL WITHDRAWN` warning), and each `aw commit` result. Paste `grep -n '^- Status:\|^- Readiness:'` for every demoted plan showing `draft` and no Readiness, and the new history line on each. Paste `git diff --name-only <pre-E-02 HEAD>..HEAD` showing no file under `executed/`, `superseded/` or `not-executed/` changed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste each `aw backlog set open` (and any spec setter) command and output; `grep -n '^- Status:\|^- Blocks-Release:'` for each reopened item showing `open` and its gate unchanged; `aw check backlog` and `aw check release-gates` before and after with no new finding.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m agent_workflows check plans` after, showing no `check.orchestrator-not-review-ready` finding; paste the list of withdrawn approvals (id6, previous status, findings) and each one's `APPROVAL WITHDRAWN` history line. Paste `aw attention --format json` before and after for the moved items. Paste `aw ipd lint` on this plan conforming, `aw sanitize --agent`, and `git diff --cached --name-only` immediately before committing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Records only. Requires `24qw39` and `26m1nb` executed first (and through them `qs00nc` and `8mabmu`); if `aw ipd coverage` or the backward `aw ipd set draft --message` edge is absent, STOP and report. Spends one model call per pending orchestrator without a current coverage record (17 at review). Scope fence: the declared record directories are the surface; an edit outside them may be made when genuinely required and is then JUSTIFIED at finalize with `--scope-reason <path>=<why>` (and an untouched declared path with `--scope-ack`). Commit through `aw commit <plan> -- <paths>`, naming each changed record file; never `git add -A`; never push. Paste the ACTUAL command output for every `V-*`; never paraphrase or claim a run you did not make. Under a runner, the runner owns `aw ipd begin`/`aw ipd finalize`; by hand, run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-move the plan to `executed/`.
