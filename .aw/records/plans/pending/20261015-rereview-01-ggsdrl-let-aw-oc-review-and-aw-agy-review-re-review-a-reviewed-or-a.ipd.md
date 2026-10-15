# IPD: Let aw oc review and aw agy review re-review a reviewed or approved plan behind an explicit confirmation

- Date: 2026-10-15
- Kind: child
- Concern: Backlog `dbr23q`. Measured 2026-10-15: after the maintainer answered `jmogmv` OQ-01 with an answer that inverted the plan's design, both `aw oc run --action review jmogmv` and `aw oc review jmogmv` refused with "--action review is illegal for 1 selected item(s): jmogmv (status 'reviewed' -> action 'execute')". Spec `25kzda` 2.6 says "`--action review` permits an explicit re-review of a complete `reviewed` IPD or spec. The result remains `reviewed`, with a new tool-authored history receipt", and its 3.2 legality row `reviewed, --action review` reads "Re-review; keep `reviewed`; append a review receipt". The runner never implemented it: `runner_shared.enforce_requested_action` refuses any item whose derived action differs from the requested one, and `run_selection_policy.runner_action` refinement (ii) derives `execute` for `reviewed`. The only workaround is a hand `aw ipd set to-review <id6>` demotion plus a commit.
- Scope: When `--action review` is requested (which `aw oc review <sel>` / `aw agy review <sel>` expand to via `cli.expand_host_review_argv`), a NAMED IPD at `reviewed`, `approved` or `auto-approved` is admitted for re-review behind a confirmation gate: `--yes` on the command line, or, on an interactive terminal, typing the exact phrase `re-review` at a prompt; unattended without `--yes` the item is refused (whole run refused, nothing created). Before dispatch each admitted item is demoted to `to-review` through the existing setter with reason "re-review requested via <host> review" (which, for approved/auto-approved, records APPROVAL WITHDRAWN and strips `- Approval:` and `- Readiness:`), so the review turn writes a fresh Readiness and the plan must be approved again. The `--full-auto` reviewed->auto-approved shortcut is skipped for these items. Orchestrators past review, terminal plans (`executed`, `superseded`, `not-executed`), `reusable` plans and non-IPD types keep today's refusal. A status-SWEEP (`aw oc review` with no selector) is unchanged and never sweeps reviewed/approved plans. Spec `25kzda` 2.6 / 3.2 / 4.4 and `ipd-spec`'s "no tool demotes automatically" sentence are amended to match.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_selection_policy.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_rereview_reviewed_plan.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md, .aw/system/workflows/plan-review/plan-review.md, docs/cli-reference.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: dbr23q
- Blocks-Release: next
- Set: rereview
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ggsdrl

## Workflow history
- 2026-10-15 to-review (aw set): authored from backlog dbr23q at HEAD df9ededb4; maintainer rulings 2026-10-15 recorded in Concern

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw oc review <id6>` (and the agy twin) re-reviews a plan that is already `reviewed` or `approved` after the operator confirms, instead of refusing, and leaves the plan needing a fresh approval.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: pure decision

- [ ] E-01 Add to `run_selection_policy` a pure `decide_rereview_admission(candidates, *, interactive, assume_yes, response)` returning a verdict naming admitted re-review ids, refused ids with a reason, and whether a prompt is needed, plus the constant `REREVIEW_CONFIRM_PHRASE = "re-review"` matched with the existing `is_confirmation_accepted`. A candidate is an IPD the operator NAMED (not a status sweep) whose status is `reviewed`, `approved` or `auto-approved` and whose kind is not an orchestrator past review. Rules: `assume_yes` admits all; interactive with the exact phrase admits all; interactive with anything else, or non-interactive without `assume_yes`, refuses all with a message naming `--yes` and the phrase.
  - Depends on: none
  - Expected outcome: unit-testable with no TTY or filesystem, mirroring `decide_draft_admission`.
  - Execution state: pending

### Task group 2: runner wiring

- [ ] E-02 Add `-y/--yes` to the `start` subparser in `oc_runipd.build_parser` and `agy_runipd.build_parser` (help: "confirm a re-review of a reviewed or approved plan named with --action review"), and make `cli.expand_host_review_argv` pass it through.
  - Depends on: none
  - Expected outcome: `aw oc review jmogmv --yes` parses to `start jmogmv --action review --yes`.
  - Execution state: pending
- [ ] E-03 In `runner_shared.initialize_run_core`, when `requested_action == "review"`: compute re-review candidates from the named selectors before `enforce_requested_action`; call `decide_rereview_admission` (prompting via `prompt_for_gate_phrase` when `is_interactive_run`); on refusal raise `DriverError` before the run directory exists; on admission override the candidates' derived action to `review` in `preflight_items`, so legality passes.
  - Depends on: E-01, E-02
  - Expected outcome: a named `reviewed` plan passes legality; an unconfirmed unattended run is refused with no run directory created.
  - Execution state: pending
- [ ] E-04 Still in `initialize_run_core`, for each admitted id: demote it to `to-review` via the existing `aw ipd set` path (`status_set`, the same call the runner already uses for child transitions, with `--yes` and message "re-review requested via <host> review"), commit it path-scoped as the runner commits its other status writes, skip the `status == "reviewed" and full_auto` auto-approve branch for it, and let queue build derive `review` normally from the new `to-review` status.
  - Depends on: E-03
  - Expected outcome: queue item `action == "review"`, `initial_status == "to-review"`; plan file history carries the demotion line; an approved plan's history says APPROVAL WITHDRAWN.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_rereview_reviewed_plan.py`: (a) table-driven `decide_rereview_admission` cases (yes, interactive phrase, interactive wrong phrase, unattended no-yes, orchestrator, terminal statuses excluded); (b) drive `initialize_run_core` (prepare-only, stubbed host as existing runner tests do) on a temp repo with a `reviewed` and an `approved` plan named under `--action review --yes`, asserting the queue actions are `review`, the plan files are now `to-review` with the demotion history line and no `- Readiness:`/`- Approval:`; (c) same without `--yes` unattended asserts `DriverError` and no run dir; (d) `--action review` with a status selector still refuses a `reviewed` plan exactly as today; (e) `--action execute` behavior unchanged.
  - Depends on: E-04
  - Expected outcome: all cases pass on both hosts' labels.
  - Execution state: pending

### Task group 4: contract sync

- [ ] E-06 Amend spec `25kzda` 2.6 (re-review admits a NAMED reviewed/approved/auto-approved IPD, requires `--yes` or the typed phrase, demotes to `to-review` first, withdraws approval), its 3.2 legality rows for `reviewed`/`approved` under `--action review`, and the 4.4 `IPD-REVIEW-LEGAL-TRANSITION` row (a re-review now runs `to-review` -> `reviewed`); amend `ipd-spec`'s "For any other plan no tool demotes automatically" to name this operator-confirmed demotion as the one exception; add a note to `plan-review.md` that a runner re-review arrives at `to-review` and writes a fresh Readiness; update the `aw oc review` entry in `docs/cli-reference.md` (if present; otherwise the `--help` text only) and a CHANGELOG line.
  - Depends on: E-04
  - Expected outcome: spec text and behavior agree; no em/en dashes in CHANGELOG/docs.
  - Execution state: pending
- [ ] E-07 Record `aw specs note` entries on `25kzda` and `ipd-spec` pointing at this plan.
  - Depends on: E-06
  - Expected outcome: both specs' `## Workflow history` carry the note.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Confirmation gates follow the pure-decide + enforce-wrapper pattern: `run_selection_policy.decide_draft_admission` / `runner_shared.enforce_draft_admission_gate`, exact phrases (`DRAFTS_CONFIRM_PHRASE = "run drafts"`), `y` deliberately rejected, `prompt_for_gate_phrase` never blocks (timeout).
- Gates that refuse do so BEFORE the run directory exists (`enforce_requested_action` docstring: "REFUSED BEFORE THE QUEUE IS FROZEN").
- `status_set._prepare_status_change` already supports `approved`->`to-review` and `reviewed`->`to-review` (`ipd_lifecycle._LEGAL_BACKWARD_EDGES`), requires a reason, writes "APPROVAL WITHDRAWN", and strips `- Approval:`/`- Readiness:` on a move to `to-review`.
- `runner_shared.reconcile_disposition` accepts a review turn ending at `reviewed` given positive evidence; `/plan-review` sets `reviewed` from `to-review`.
- The `enforce_requested_action` docstring records why the refusal exists (typing "review" must never EXECUTE); this plan preserves that by turning the item into a genuine review, never an execute.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Spec requires reviewed re-review; code refuses | spec `25kzda` 2.6 and 3.2 row vs `runner_shared.enforce_requested_action` "--action review is illegal" |
| F-2 | `reviewed` derives `execute` | `run_selection_policy.runner_action` refinement (ii) |
| F-3 | Demotion to `to-review` is already legal and clears Readiness | `status_set._prepare_status_change`, `ipd_lifecycle._LEGAL_BACKWARD_EDGES` |
| F-4 | `--full-auto` would auto-approve a reviewed plan before the action is derived | `runner_shared.initialize_run_core` "if status == \"reviewed\" and full_auto" |
| F-5 | Maintainer ruling 2026-10-15: accept reviewed AND approved; must require `-y/--yes` or an interactive "are you sure?" | interactive answer recorded on backlog `dbr23q` |

## Proposed changes (ordered, validatable)

E-01..E-07 in order.

## Deferred / out of scope (with reason)

- Re-review of specs (`25kzda` 2.6 also names specs): specs already reach review through their own legality row; not part of the measured failure.
  - Carrier-Declined: not requested; spec re-review was not part of the measured defect and has its own row.
- Advisory staleness flag: owned by sibling Order 02 of this Set.
  - Carrier: ygngc2

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

`python3 -m pytest tests/test_rereview_reviewed_plan.py tests/test_run_selection_policy.py -o addopts=""`, then the bare `python3 -m pytest`, then `aw ipd lint` and `aw specs check`.

## Spec / documentation sync

Spec `25kzda` (2.6, 3.2, 4.4) and `ipd-spec` (backward-move paragraph) are amended in E-06 because they define the legality table and the "no tool demotes automatically" rule this change alters; both are declared in Scope-Paths.

## Open questions

### OQ-01: Demote to `reviewed` or `to-review` before a re-review?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence 2026-10-15: `to-review`. Demoting to `reviewed` keeps the old `- Readiness:` (status_set strips it only on a move to `to-review`), so a stale `go-pending-approval` would survive the re-review's start; `to-review` forces the review to write a fresh attestation and matches `/plan-review`'s normal `to-review` -> `reviewed` path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted passing output of the E-05(a) table cases.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `aw oc review --help` / `aw oc run start --help` showing `--yes`, and the E-05 case asserting the expanded argv.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted E-05(c) passing (refusal, no run dir) and E-05(d) passing (sweep unchanged).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted E-05(b) passing, plus a real `aw oc run --prepare-only --action review <reviewed-id6> --yes` against a temp repo (code path `initialize_run_core`) showing the queue action `review` and the plan's demotion history line.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest tests/test_rereview_reviewed_plan.py tests/test_run_selection_policy.py -o addopts=""` output and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the amended 2.6 sentence and `ipd-spec` sentence quoted, and `aw specs check` output.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: the two spec history lines quoted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and human approval. Begin with `aw work begin ggsdrl` in an isolated worktree; commit via `aw commit ggsdrl -- <paths>`; never push or tag. Paste ACTUAL output in each `V-*`. Scope-Paths is a declaration; justify any out-of-scope edit at finalize with `--scope-reason`. STOP only for an unsafe concurrent edit to `runner_shared.py` that cannot be combined.
