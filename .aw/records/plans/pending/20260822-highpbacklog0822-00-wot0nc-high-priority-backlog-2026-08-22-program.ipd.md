# IPD: High-Priority Backlog 2026-08-22 Program

- Date: 2026-08-22
- Kind: orchestrator
- Concern: Drive five high/medium-priority backlog items to closure as one coordinated, independently-executable Set.
- Scope: Coordinate seven child IPDs (disclosure prep, an agy false-ERROR bug fix, a slash-alias deprecation warning, a two-part CLI empty/error UX pass, and a two-part IPD right-sizing check); no domain redesign and no work beyond the five source backlog items.
- Status: draft
- Set: highpbacklog0822
- Order: 0
- Highest E allocated: 03
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: wot0nc

## Workflow history

- 2026-08-22 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created from five open high/medium-priority backlog items (2p6mgq, uhbdt1, 21ni81, oijafw, 8iy2dk) at the maintainer's request; the two items needing more than three material changes (oijafw, 8iy2dk) were each split into two children.

## Goal

Close five open backlog items as one batch of small, independently-executable, independently-verifiable child IPDs, so a real agent (including a faster/weaker tier) can execute each child in a single focused pass without inventing missing architecture.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Sequence the independent children

- [ ] E-01 Confirm the child dependency order below and that each child carries a resolved, self-contained execution contract before any child executes; children with `Depends on: none` may run in any order or in parallel.
  - Depends on: none
  - Expected outcome: every child has an approved, unambiguous scope and no cross-child ordering conflict remains.
  - Execution state: pending

### Material change 2: Execute the children

- [ ] E-02 Execute Orders 01-07 in dependency order: 01, 02, 03, 06, 07 are independent; Order 05 depends on Order 04; Orders 04 and 05 additionally require the pending `awcliux` renderer boundary (Set `awcliux`, Order 02 `czw99i`) to be executed first, or STOP and report if its shared human-output components are absent.
  - Depends on: E-01
  - Expected outcome: each source backlog item's fix has landed and its owning backlog record is set to `done`.
  - Execution state: pending

### Material change 3: Close the batch

- [ ] E-03 After every child is in `executed/`, set each of the five source backlog items (2p6mgq, uhbdt1, 21ni81, oijafw, 8iy2dk) to its correct terminal status and confirm no `Blocks-Release: next` obligation for oijafw or 8iy2dk remains unmet.
  - Depends on: E-02
  - Expected outcome: the five backlog items are closed (or 2p6mgq is explicitly parked on the human send) and the release-gate obligations are discharged.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | File | Purpose | Source item | Depends on |
| --- | --- | --- | --- | --- |
| 01 | `20260822-highpbacklog0822-01-dtl6dz-opencode-coordinated-disclosure-preparation.ipd.md` | Agent-safe PREPARATION of the OpenCode disclosure (assemble/verify packet, tracking record); drafting + send + clock are human-owned | 2p6mgq | none |
| 02 | `20260822-highpbacklog0822-02-n5kvff-fix-agy-run-py-false-error-on-sandboxed-write-to-file-reject.ipd.md` | Stop `agy_run.py` reporting ERROR when a sandboxed `write_to_file` rejection follows a successful `run_command` write | uhbdt1 | none |
| 03 | `20260822-highpbacklog0822-03-h4e9yi-deprecation-warning-for-per-workflow-slash-command-aliases.ipd.md` | Add a migrate-to-`/aw <verb>` deprecation notice to the generated per-workflow slash-command shims | 21ni81 | none |
| 04 | `20260822-highpbacklog0822-04-89bby9-empty-loading-and-error-state-ux-shared-helper-and-conventio.ipd.md` | Shared empty/loading/error-state helper + convention (echo active filters, suggest next step) | oijafw (1/2) | awcliux Order 02 (czw99i) |
| 05 | `20260822-highpbacklog0822-05-4ug8xp-empty-and-error-state-ux-surface-wide-rollout-and-tests.ipd.md` | Roll the convention across every read/list/mutation verb + tests | oijafw (2/2) | Order 04 |
| 06 | `20260822-highpbacklog0822-06-por1hi-ipd-right-sizing-rubric-in-review-workflows-and-authoring-gu.ipd.md` | Add a per-E-item conceptual-density right-sizing rubric to plan-review, plan-review-long, the assess harness, and scaffold authoring guidance | 8iy2dk (1/2) | none |
| 07 | `20260822-highpbacklog0822-07-wb045s-ipd-right-sizing-mechanical-lint-heuristic.ipd.md` | Add a mechanical lint heuristic flagging an E-item that names multiple deliverables/test-surfaces | 8iy2dk (2/2) | none |

## Completion criteria (the whole Set is done only when)

- All seven children are in `.aw/records/plans/executed/` with `Status: executed` and each child's `aw ipd lint --phase post-transition` conforms.
- Backlog `uhbdt1`, `21ni81`, `oijafw`, `8iy2dk` are `done`; `2p6mgq` is `done` only if the human has sent the disclosure, otherwise it stays `open`/`parked` on the human send with the prepared packet cited.
- No `Blocks-Release: next` obligation remains for `oijafw` or `8iy2dk`.
- No child expanded scope beyond its single source backlog item.

## Cross-IPD validation

- Confirm Orders 04-05 REUSE the `awcliux` renderer boundary and do not introduce a second human-output path (KISS / no duplicate paths).
- Confirm Orders 06-07 are consistent: the prose rubric (06) and the mechanical heuristic (07) use the same "one concern / executable-in-one-focused-pass per E-item" definition and do not contradict each other.
- Confirm Order 01 changed no code and drafted no send-ready disclosure text authored by the agent (human-owned boundary honored).

## Deferred / out of scope (with reason)

- Any backlog item not in the five named here.
- Eventual PRUNING of the per-workflow slash aliases (Order 03 only warns; removal is a later decision).
- The human drafting and sending of the OpenCode disclosure and its 30-45 day clock (human-owned; Order 01 only prepares).

## Scope check

- Over-scope: none.
- Under-scope: none; the two large items are split so each child holds at most three material changes.

## Required tests / validation

Per-child: each child states and runs its own tests/validation. Set-level: after all children execute, run the full test suite and `aw ipd lint --all` and paste the actual output; confirm the five backlog records reflect their terminal state.

## Open questions

### OQ-01: Must Orders 04-05 wait for the whole awcliux Set, or only its renderer boundary (Order 02 czw99i)?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Orders 04-05 require only the `awcliux` human-TTY renderer boundary (Set `awcliux` Order 02 `czw99i`, itself gated on Order 01 `hd3kln`), not the full `awcliux` Set. If that boundary is not yet executed when Order 04 starts, STOP and report rather than duplicating the output layer.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: each child file exists in `pending/`, carries an execution contract, and the dependency table above matches each child's stated `Depends on`; paste the `aw ipd lint --all` disposition for the Set.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: all seven children are in `executed/` with `Status: executed` and each `aw ipd lint --phase post-transition` conforms; paste the actual lint output per child.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `aw backlog check` (or the record files) show 2p6mgq/uhbdt1/21ni81/oijafw/8iy2dk at their terminal status and no unmet `Blocks-Release: next`; paste the actual command output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: seven small children each own exactly one source backlog item (two items split to keep each child at or under three material changes); the orchestrator only sequences and closes the batch.

Review and explicit human approval are required. No plan moves to `executed/` until its E/V evidence passes `aw ipd lint --phase pre-transition`.

### Execution contract

1. Open questions RESOLVED: OQ-01 above is resolved; no blocking question remains at the orchestrator level. Each child carries its own open-question state.
2. Scope fence: this orchestrator sequences and closes the batch; it changes no code itself. Each child touches only the files named in its own scope. Do not expand scope; if a child seems to need to touch a file outside its scope, STOP and report.
3. Honesty rule (hard MUST): when you report tests/lint/backlog-check passed, paste the ACTUAL runner output; never claim a pass you did not run.
4. Commit ONLY each child's own changed files, path-scoped (`git commit -- <path>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: each child transitions itself on completion (append its `## Workflow history` line, set `Status: executed`, `git mv` from `pending/` to `executed/`, path-scoped lifecycle commit) only after its E items are performed and its V items are verified with pasted evidence. This orchestrator transitions last, after all seven children are in `executed/` and the five backlog records are closed.
