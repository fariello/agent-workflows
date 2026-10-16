# IPD: Let aw oc review and aw agy review re-review a reviewed or approved plan behind an explicit confirmation

- Date: 2026-10-15
- Kind: child
- Concern: Backlog `dbr23q`. Measured 2026-10-15: after the maintainer answered `jmogmv` OQ-01 with an answer that inverted the plan's design, both `aw oc run --action review jmogmv` and `aw oc review jmogmv` refused with "--action review is illegal for 1 selected item(s): jmogmv (status 'reviewed' -> action 'execute')". Spec `25kzda` 2.6 says "`--action review` permits an explicit re-review of a complete `reviewed` IPD or spec. The result remains `reviewed`, with a new tool-authored history receipt", and 4.4 says its checks apply "when `--action review` re-reviews a `reviewed` IPD". (The `reviewed, --action review` legality ROW exists only in 3.3 Specs; 3.2 IPDs has no such row, so the IPD side of the contract lives in 2.6 and 4.4 alone.) The runner never implemented it: `runner_shared.enforce_requested_action` refuses any item whose derived action differs from the requested one, and `run_selection_policy.runner_action` refinement (ii) derives `execute` for `reviewed`. The only workaround is a hand `aw ipd set to-review <id6>` demotion plus a commit.
- Scope: When `--action review` is requested (which `aw oc review <sel>` / `aw agy review <sel>` expand to via `cli.expand_host_review_argv`), an IPD reached through a NON-status selector (id6, path or setid; never `reviews`/`all`) at `reviewed`, `approved` or `auto-approved` is admitted for re-review behind a confirmation gate: `--yes` on the command line, or, on an interactive terminal, typing the exact phrase `re-review` at a prompt; unattended without `--yes` the whole run is refused before the run directory exists. Admitted items are frozen with action `review` and a durable `rereview: true` queue flag; nothing is written to the plan at run start. At DISPATCH, inside the review lane and before the lane inputs are materialized, each item is demoted to `to-review` through the existing setter with reason "re-review requested via <host> review" (which, for approved/auto-approved, records APPROVAL WITHDRAWN and strips `- Approval:` and `- Readiness:`), so the demotion integrates with the review output through the existing lane merge, a run refused by any later gate never demotes anything, and the review must write a fresh `- Readiness:`. Both `--full-auto` auto-approve sites (queue build and post-review) are skipped for these items, so a re-reviewed plan always needs a fresh human approval. Orchestrators past review, terminal plans (`executed`, `superseded`, `not-executed`), `reusable` plans and non-IPD types keep today's refusal. A status sweep is unchanged and never sweeps reviewed/approved plans. Spec `25kzda` 2.1 / 2.6 / 3.2 / 4.4 and `ipd-spec`'s "no tool demotes automatically" sentence are amended to match.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_selection_policy.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_rereview_reviewed_plan.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md, .aw/system/workflows/plan-review/plan-review.md, docs/artifact-lifecycles.md, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: dbr23q
- Blocks-Release: next
- Set: rereview
- Order: 1
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ggsdrl
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-15 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009, PR-010, PR-011
- 2026-10-15 to-review (aw set): authored from backlog dbr23q at HEAD df9ededb4; maintainer rulings 2026-10-15 recorded in Concern

- 2026-10-15 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`aw oc review <id6>` (and the agy twin) re-reviews a plan that is already `reviewed` or `approved` after the operator confirms, instead of refusing, and leaves the plan needing a fresh human approval.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: pure decision

- [ ] E-01 Add to `run_selection_policy` a pure `decide_rereview_admission(candidates, *, interactive, assume_yes, response)` returning a verdict naming admitted re-review ids, refused ids with a reason, and whether a prompt is needed, plus the constant `REREVIEW_CONFIRM_PHRASE = "re-review"` matched with the existing `is_confirmation_accepted(response, phrase=REREVIEW_CONFIRM_PHRASE)` (no second matcher). A candidate is `(id6, status, kind)` for an IPD whose status is `reviewed`, `approved` or `auto-approved` and whose kind is not `orchestrator`; the CALLER decides selector eligibility (E-03), so this function stays pure. Rules: `assume_yes` admits all; interactive with the exact phrase admits all; interactive with anything else (including `y`, `yes`, empty, `None` from a timeout), or non-interactive without `assume_yes`, refuses all with a message that lists each id6 with its status, says approval will be withdrawn for `approved`/`auto-approved` items, and names both `--yes` and the phrase.
  - Depends on: none
  - Expected outcome: unit-testable with no TTY or filesystem, mirroring `decide_draft_admission`.
  - Execution state: pending

### Task group 2: runner wiring

- [ ] E-02 Add `-y/--yes` (dest `yes`, default False) to the `start` subparser in `oc_runipd.build_parser` and `agy_runipd.build_parser` (help: "confirm a re-review of a reviewed or approved plan named with --action review; approval is withdrawn and must be given again"). `cli.expand_host_review_argv` already forwards the tail verbatim (measured at review: `expand_host_review_argv(['jmogmv','--yes'])` returns `['jmogmv', '--yes', '--action', 'review']`), so it needs NO code change; only update the `aw oc review` and `aw agy review` parser descriptions in `cli.py` whose text says the alias "refuses rather than executing when a selected plan is already past review" to say a named past-review plan is re-reviewed after `--yes` or the typed phrase.
  - Depends on: none
  - Expected outcome: `aw oc run start --help` and `aw agy run start --help` list `-y, --yes`; `aw oc review jmogmv --yes` reaches the driver as `jmogmv --yes --action review`.
  - Execution state: pending
- [ ] E-03 In `runner_shared.initialize_run_core`, inside the existing `if requested_action is not None:` block and before `enforce_requested_action`: when `requested_action == "review"` and `not is_status_selector(args.selectors)`, collect re-review candidates from `preflight_items` (IPD, status `reviewed`/`approved`/`auto-approved`, kind resolved by `resolve_manifest_kind` not `orchestrator`); if any, call `decide_rereview_admission(..., interactive=is_interactive_run(args), assume_yes=bool(getattr(args, "yes", False)), response=<prompt_for_gate_phrase(...) when interactive and not yes, else None>)`; on refusal raise `DriverError` with the verdict message (before the run directory exists); on admission replace each admitted entry's derived action with `review` in `preflight_items` and keep the admitted id set as a local `rereview_ids` for E-04. Every other item (including a `reviewed` orchestrator) still reaches `enforce_requested_action` unchanged.
  - Depends on: E-01, E-02
  - Expected outcome: a named `reviewed` plan passes legality under `--yes`; an unconfirmed unattended run raises `DriverError` and creates no run directory; a status sweep and an orchestrator keep today's refusal text.
  - Execution state: pending
- [ ] E-04 In the queue-build loop of `initialize_run_core`, for an id in `rereview_ids`: skip the `if status == "reviewed" and full_auto and p_path:` auto-approve branch, set `action = "review"` instead of calling `action_for`, keep `initial_status` as the on-disk status, and add `"rereview": True` to the queue entry (absent for every other entry, so existing state files and resume are unchanged). Do NOT write the plan here: `--prepare-only` and any later refusal gate (`enforce_freeze_time_refusal`, `enforce_orchestrator_shape_gate`, red-CI, spec-edit ack, orchestrator probe) must leave the plan file byte-identical.
  - Depends on: E-03
  - Expected outcome: queue entry `action == "review"`, `status == "queued"` (via `initial_queue_status`), `rereview is True`, `review_handler == "plan-review"`, `initial_status` unchanged; plan file unchanged after `--prepare-only`.
  - Execution state: pending
- [ ] E-08 In `runner_shared.execute_item_core`, for a `review` item with `item.get("rereview")` whose plan in the turn's working tree (the review sweep lane when isolated, else `repo`) still reads `reviewed`/`approved`/`auto-approved`: run `pinned_module_argv(["ipd", "set", "to-review", id6, "--message", "re-review requested via <labels.command> review", "--yes", "--no-commit", "--dir", <tree>])` through the host's `run_checked`, after `acquire_review_sweep_lane` and BEFORE `build_review_prompt` / `lane_containment.materialize_lane_inputs`, so the reviewer reads the demoted plan; record `attempt["rereview_demoted_from"] = <old status>` and an `rereview-demoted` event in `events.jsonl`. Do not commit here: the plan path carries the item's id6, so `classify_review_writes` admits it and `commit_review_lane_output` lands it with the review output, and it reaches `main` only through the existing review-lane integration. If the plan already reads `to-review` (a resumed attempt), skip the demotion. If the setter fails, mark the item `fail-gate` with a refusal naming the setter error and do not launch the turn.
  - Depends on: E-04
  - Expected outcome: the review prompt and lane-input copy show `- Status: to-review`, no `- Approval:`/`- Readiness:`, and the history line `demoted <from> -> to-review: [APPROVAL WITHDRAWN: ]re-review requested via <host> review`; `main` is untouched until integration.
  - Execution state: pending
- [ ] E-09 Close the two places a re-review could end wrongly. (a) In `runner_shared.reconcile_disposition` (IPD review branch), for an item with `rereview`, require that the plan reads `reviewed` AND carries a `- Readiness:` line (the demotion stripped it, so its presence proves the review wrote a fresh one); otherwise return `fail-gate` with a refusal reason saying the re-review produced no fresh review, because the demotion alone dirties the lane and would otherwise satisfy `review_has_positive_evidence`. (b) In the post-review `--full-auto` bridge (the `is_review and queue_entry_type(item) == "ipd" and disposition in ("reviewed", "approved") and full_auto` block that calls `set_plan_approved`), skip items with `rereview`, so a re-reviewed plan stops at `reviewed` awaiting human approval even under `--full-auto`.
  - Depends on: E-08
  - Expected outcome: a no-op re-review turn ends `fail-gate`, not `reviewed`; a successful re-review under `--full-auto` ends `reviewed` with no `auto-approved` transition and no `ipd-auto-approved` event.
  - Execution state: pending

### Task group 3: tests

- [ ] E-05 Add `tests/test_rereview_reviewed_plan.py` (behavioral only, per the no-code-pinning rule): (a) table-driven `decide_rereview_admission` cases (yes; interactive exact phrase; interactive `y`/`yes`/empty/`None`; unattended without yes; message lists ids and names `--yes` and the phrase); (b) drive `oc_runipd.main` / `agy_runipd.main` `start <id6> --action review --yes --prepare-only --unattended` on a temp repo holding one `reviewed` and one `approved` child plan, asserting state.json queue entries have `action == "review"`, `rereview is True`, `status == "queued"`, and both plan files are byte-identical to before; (c) the same without `--yes` exits nonzero with the refusal text and creates no run directory; (d) `--action review` with the `reviews` selector and with `all` still refuses or skips the `reviewed` plan exactly as today, and a `reviewed` orchestrator named by id6 keeps today's refusal under `--yes`; (e) `--action execute` and no `--action` on the same `reviewed`/`approved` plans derive exactly as before; (f) drive `execute_item_core` for a `rereview` item with a fake host turn (the `fake_run` pattern in `tests/test_oc_runipd.py`) that writes `- Readiness: go-pending-approval` and sets `reviewed`, asserting the plan the fake turn saw read `to-review` with the demotion line and (for `approved`) `APPROVAL WITHDRAWN`, and the disposition is `reviewed`; (g) the same with a fake turn that does nothing ends `fail-gate`; (h) the same as (f) with `full_auto` set ends `reviewed` and the plan never reads `auto-approved`; (i) a refusal from a later gate (e.g. an unresolvable sibling in the selection) leaves the `approved` plan unchanged.
  - Depends on: E-09
  - Expected outcome: every case passes for both hosts' drivers where the case is host-parameterized ((b), (c)).
  - Execution state: pending

### Task group 4: contract sync

- [ ] E-06 Amend spec `25kzda`: 2.1's "It cannot force a status transition" and 2.6's "`aw <host> review` overrides nothing ... cannot force a transition" to name the one exception (an operator-confirmed re-review demotion); 2.6's re-review bullet (re-review admits an IPD at `reviewed`/`approved`/`auto-approved` reached through a non-status selector, requires `--yes` or the typed phrase `re-review`, demotes to `to-review` at dispatch inside the review lane, withdraws approval, and ends `reviewed` needing fresh human approval even under `--full-auto`); ADD to the 3.2 IPD table rows `reviewed`/`approved`/`auto-approved` under `--action review` (the table has none today); and the 4.4 intro and `IPD-REVIEW-LEGAL-TRANSITION` row (an IPD re-review runs `to-review` -> `reviewed` after the tool-authored demotion). Amend `ipd-spec`'s "For any other plan no tool demotes automatically" to name this operator-confirmed runner demotion as the one exception. Leave the spec-side 3.3 row untouched (spec re-review is out of scope).
  - Depends on: E-09
  - Expected outcome: spec text and behavior agree; `aw specs check` reports no new findings.
  - Execution state: pending
- [ ] E-10 Update operator-facing docs: a note in `.aw/system/workflows/plan-review/plan-review.md` (Step 4, beside the Readiness field) that a runner re-review arrives at `to-review` with `- Readiness:` stripped and MUST write a fresh one; the "Moving backwards" paragraph of `docs/artifact-lifecycles.md` (re-review of a `reviewed`/`approved` plan with `aw oc review <id6> --yes`, which withdraws approval); and one CHANGELOG line under the pending release. No em or en dashes in the CHANGELOG or docs prose.
  - Depends on: E-09
  - Expected outcome: the three files carry the text; a dash scan of the changed lines finds no U+2013/U+2014.
  - Execution state: pending
- [ ] E-07 Record `aw specs note` entries on `25kzda` and `ipd-spec` pointing at this plan.
  - Depends on: E-06
  - Expected outcome: both specs' `## Workflow history` carry the note.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Confirmation gates follow the pure-decide + enforce-wrapper pattern: `run_selection_policy.decide_draft_admission` / `runner_shared.enforce_draft_admission_gate`, exact phrases (`DRAFTS_CONFIRM_PHRASE = "run drafts"`), `y` deliberately rejected by `is_confirmation_accepted`, `prompt_for_gate_phrase` never blocks (timeout returns `None`, which refuses).
- `is_interactive_run` returns False under `--unattended` and `--full-auto`, so an unattended or full-auto re-review needs `--yes`.
- Gates that refuse do so BEFORE the run directory exists (`enforce_requested_action` docstring: "REFUSED BEFORE THE QUEUE IS FROZEN").
- `status_set._prepare_status_change` already supports `approved`->`to-review` and `reviewed`->`to-review` (`ipd_lifecycle._LEGAL_BACKWARD_EDGES`), requires a reason, writes "APPROVAL WITHDRAWN", and strips `- Approval:`/`- Readiness:` on a move to `to-review`. Demonstrated at review in a scratch repo: `aw ipd set to-review abc123 --message "re-review requested via oc review" --yes --no-commit --dir <tmp>` on an `approved` plan carrying both fields printed `DEMOTED abc123: approved -> to-review: APPROVAL WITHDRAWN: ...`, left `- Status: to-review`, removed both fields, and added the history line.
- Review turns run in the run-scoped review sweep lane (`acquire_review_sweep_lane`); their output is committed path-scoped by `commit_review_lane_output` (paths filtered by `classify_review_writes`, which admits paths carrying the item's id6) and reaches `main` through the review-lane integration. The runner already uses the setter with `--no-commit --dir <tree>` in a turn's tree (the orchestrator-readiness demotion in `runner_shared`, `IPD-REVIEW-ORCHESTRATOR-READY`).
- `runner_shared.reconcile_disposition` accepts a review turn ending at `reviewed` given `review_has_positive_evidence`, which counts a dirty working tree as evidence.
- The post-review `--full-auto` bridge calls `set_plan_approved` for a `reviewed` disposition even when `options.action == "review"` (it only skips re-queuing to execute).
- The `enforce_requested_action` docstring records why the refusal exists (typing "review" must never EXECUTE); this plan preserves that by making the item a genuine review that can only end `reviewed`.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Spec requires reviewed re-review; code refuses | spec `25kzda` 2.6 and 4.4 intro vs `runner_shared.enforce_requested_action` "--action review is illegal" |
| F-2 | `reviewed` derives `execute` | `run_selection_policy.runner_action` refinement (ii); measured `runner_action('ipd','reviewed',for_legality=True) == 'execute'` |
| F-3 | Demotion to `to-review` is already legal and clears Readiness | `status_set._prepare_status_change`, `ipd_lifecycle._LEGAL_BACKWARD_EDGES`; scratch demonstration above |
| F-4 | `--full-auto` auto-approves a reviewed plan at TWO sites | `runner_shared.initialize_run_core` "if status == \"reviewed\" and full_auto"; the post-review bridge calling `set_plan_approved` in the review finish path |
| F-5 | Maintainer ruling 2026-10-15: accept reviewed AND approved; must require `-y/--yes` or an interactive "are you sure?" | given interactively in the authoring session and recorded in this plan's Concern/Scope; backlog `dbr23q` records the reviewed-and-approved need ("withdrawing approval explicitly") |
| F-6 | The queue builder re-derives the action independently of legality | `initialize_run_core` queue loop calls `action_for(kind, status ...)` again after `enforce_requested_action`, so overriding `preflight_items` alone would still freeze `execute` |
| F-7 | A demotion in the lane would by itself satisfy the zero-output guard | `review_has_positive_evidence` returns True on a non-empty `git status --porcelain` |

## Proposed changes (ordered, validatable)

E-01, E-02, E-03, E-04, E-08, E-09, E-05, E-06, E-10, E-07 in that order (the `Depends on:` edges are authoritative).

## Deferred / out of scope (with reason)

- Re-review of specs (`25kzda` 2.6 also names specs): specs already reach review through their own 3.3 legality row; not part of the measured failure.
  - Carrier-Declined: not requested; spec re-review was not part of the measured defect and has its own row.
- Advisory staleness flag: owned by sibling Order 02 of this Set.
  - Carrier: ygngc2

## Scope check

- Over-scope: none.
- Under-scope: none after review round 1 (dispatch-time demotion, both `--full-auto` sites, the zero-output guard, and the 2.1 sentence were added).

## Required tests / validation

`python3 -m pytest tests/test_rereview_reviewed_plan.py tests/test_run_selection_policy.py -o addopts=""`, then the bare `python3 -m pytest`, then `aw ipd lint` and `aw specs check`.

## Spec / documentation sync

Spec `25kzda` (2.1, 2.6, 3.2, 4.4) and `ipd-spec` (backward-move paragraph) are amended in E-06 because they define the legality table, the "cannot force a transition" rule, and the "no tool demotes automatically" rule this change alters; both are declared in Scope-Paths. `plan-review.md`, `docs/artifact-lifecycles.md` and CHANGELOG are updated in E-10.

## Open questions

### OQ-01: Demote to `reviewed` or `to-review` before a re-review?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence 2026-10-15: `to-review`. Demoting to `reviewed` keeps the old `- Readiness:` (status_set strips it only on a move to `to-review`), so a stale `go-pending-approval` would survive the re-review's start; `to-review` forces the review to write a fresh attestation and matches `/plan-review`'s normal `to-review` -> `reviewed` path.

### OQ-02: Demote at run start or at dispatch?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved at review 2026-10-15 (review record round 1, D-1): at dispatch, inside the review lane. A run-start demotion would write `main` outside the lane merge, would mutate the plan under `--prepare-only`, and would withdraw approval even when a later refusal gate in `initialize_run_core` stops the run. The setter call itself was demonstrated in a scratch repo (Step 0 conventions).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted passing output of the E-05(a) table cases.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `aw oc run start --help` and `aw agy run start --help` lines showing `-y, --yes`, the updated `aw oc review --help` description, and the passing E-05 case asserting the expanded argv.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted E-05(c) passing (refusal, no run dir) and E-05(d) passing (sweep, `all`, and orchestrator unchanged).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted E-05(b) and E-05(i) passing, plus a real `aw oc run start <reviewed-id6> --action review --yes --prepare-only --unattended` against a temp repo (code path `initialize_run_core`, which returns before `run_queue` under `--prepare-only`) showing the queue action `review`, `rereview: true` in state.json, and `git diff --stat` of the plan file empty.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest tests/test_rereview_reviewed_plan.py tests/test_run_selection_policy.py -o addopts=""` output and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: the amended 2.1, 2.6 and `ipd-spec` sentences and the new 3.2 rows quoted, and `aw specs check` output.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: the two spec history lines quoted.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: pasted E-05(f) passing, with the asserted prompt/lane-input plan text (status `to-review`, demotion line, `APPROVAL WITHDRAWN` for the approved case) shown; the dispatch observation is produced by `execute_item_core` driven by the fake host turn, which E-05(f) creates.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted E-05(g) (`fail-gate` on a no-op re-review) and E-05(h) (`reviewed`, never `auto-approved`, under `full_auto`) passing; produced by `reconcile_disposition` and the post-review bridge reached through `execute_item_core` in those cases.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: the added `plan-review.md`, `docs/artifact-lifecycles.md` and CHANGELOG lines quoted, plus a `grep -nP "[\x{2013}\x{2014}]"` over the changed docs/CHANGELOG lines returning nothing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and human approval. All open questions are resolved. Begin with `aw work begin ggsdrl` in an isolated worktree; commit via `aw commit ggsdrl -- <paths>`; never push or tag. You MUST paste the ACTUAL runner output in each `V-*`; never claim a result you did not run. Scope-Paths is a declaration; justify any out-of-scope edit at finalize with `--scope-reason`. Lifecycle transition: when run by `aw oc run`/`aw agy run`, the runner finalizes the plan after its merge-and-revalidate gate; a hand executor runs `aw ipd finalize ggsdrl` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`. STOP only for an unsafe concurrent edit to `runner_shared.py` that cannot be combined.
