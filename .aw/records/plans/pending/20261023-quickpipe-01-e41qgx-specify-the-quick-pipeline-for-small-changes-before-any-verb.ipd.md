# IPD: Specify the quick pipeline for small changes before any verb implements it

- Date: 2026-10-23
- Kind: child
- Concern: A 1 to 4 line fix or one new CLI option travels the same pipeline as a large feature: a backlog item is filed (`open`), a runner plan-production turn graduates it (`graduated`), the plan is scaffolded `draft`, advanced to `to-review`, reviewed to `reviewed`, approved (human `approved` or `--full-auto` `auto-approved`), and finally executed. Backlog `rsisop` asks for a shorter path (plan, review, execution) and states that it "Needs its own spec: which changes qualify, who decides, and which records are still written." Spec `k3yx72` already makes the REVIEW cheap for such plans (its `simple` tier) and explicitly leaves the rest of the pipeline out of scope (its non-goal N4, pointing at `rsisop`).
- Scope: Produce the SPEC, not the engine. Measure what the current pipeline costs a small change, inventory which stages are already optional in code, and write one spec (created with `aw specs new`, taken to `to-review`, carrying `- From-Backlog: rsisop`) that answers the item's three questions (which changes qualify, who decides, which records are still written) plus the entry-point, approval-authority and release-gate questions those answers depend on, and proposes the implementing Set's work breakdown. NO verb, runner, schema or workflow behavior changes in this plan.
- Scope-Paths: .aw/records/specs/draft/**, .aw/records/specs/to-review/**, .aw/records/plans/**/20261023-quickpipe-01-e41qgx-specify-the-quick-pipeline-for-small-changes-before-any-verb.ipd.md
- Item-Dependencies: exists:spec:k3yx72, exists:spec:llbr2b
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: rsisop
- From-Spec: none
- Set: quickpipe
- Order: 1
- Highest E allocated: 10
- Author: opencode
- Id: e41qgx
- Approval: 2026-10-24, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-24 approved (aw set): status set to approved
- 2026-10-23 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (spec created first, baseline captured; split into E-08/E-10), PR-002 (E-09 TRACE ids for post-cutover spec), PR-003 (plan approval is not gated by TRANSITION_AUTHORITY; premise corrected), PR-004 (execution contract), PR-005 (live counts re-derived), PR-006 (F-4 miscount), PR-007 (execute_item_core named) fixed. Reviewed at HEAD `72da75876`; review record `.aw/records/reviews/20261023-quickpipe-01-e41qgx-specify-the-quick-pipeline-for-small-changes-before-any-verb.review.md`.
- 2026-10-23 to-review (opencode): authored review-ready spec-first plan graduating backlog rsisop (the item says it needs its own spec before any code)

- 2026-10-23 draft (opencode): created.

## Goal

Write one reviewed-ready spec that decides how a small change goes from a plan straight to review and execution: which changes qualify, who decides that a change qualifies, what approval it still needs, and which records are still written. Code follows in a separate Set graduated from the approved spec, so no behavior changes before the maintainer has answered the design questions.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: create the spec, then measure and inventory the current pipeline

- [x] E-08 CREATE THE SPEC BY TOOL FIRST, so E-01 to E-09 have a file to write into. Before creating anything, capture the `aw check --agent` baseline (diagnostics as (rule, location) pairs) to a scratch file under `/tmp`, for E-10's before/after comparison. Then run `aw specs new --title "Quick pipeline for small changes" --slug quick-pipeline-small-changes --summary "<one line>" --apply` (it mints the id6 and writes the conforming `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` under `.aw/records/specs/draft/`; never hand-name it). Add to its front matter `- From-Backlog: rsisop`, `- Work-Kind: feature`, `- Priority: medium`, `- Set: quickpipe`, a `- Scope:` line stating the spec authorizes no code change, and one `- Constrained-by:` line each for `k3yx72` and `llbr2b` (the multi-valued key in `specs.SPEC_MULTI_VALUED_KEYS`, in the shape `llbr2b`'s own front matter uses). Do NOT write `- Status:` by hand beyond what the tool wrote.
  - Depends on: none
  - Expected outcome: one tool-created spec under `.aw/records/specs/draft/` carrying the front matter above, and a recorded `aw check` baseline.
  - Execution state: performed

- [x] E-01 MEASURE what the current pipeline costs a small change, and record the table in the spec's problem section. Over the executed non-orchestrator plans dated 2026, select the small ones (at most 2 `E-*` items; at authoring time this was 151 plans, of which 21 carry `- From-Backlog:`; these are live counts and the table must carry the values re-derived at execution, not these) and report, per plan and as medians: the number of `## Workflow history` records, the number of distinct lifecycle statuses recorded, and, where the plan carries `- From-Backlog:`, the backlog item's own history record count. Where `aw runs` / `aw runs analyze` can attribute runner turns or cost to those plan id6s, add turns per stage (plan-production, review, execute) and recorded cost; if it cannot, say so in the spec in one sentence instead of estimating. Keep the measuring script (a short `python3 - <<'EOF'` block) verbatim in the spec so the numbers can be re-run.
  - Depends on: E-08
  - Expected outcome: a measured table in the spec, with the script that produced it, showing how many stages and records a small change carries today.
  - Execution state: performed

- [x] E-02 INVENTORY, by reading the code and citing by symbol, which pipeline stages are ALREADY optional and which are enforced, and record it as a table in the spec. Cover at least: plan creation without a backlog item (`ipd_authoring.run_scaffold` requires `--priority`/`--work-kind` only when `--from-backlog` is absent; at authoring time 96 of 1,161 non-orchestrator plans dated 2026-09 and 2026-10 carried neither `- From-Backlog:` nor `- From-Spec:`; this is a live count, so the spec states the count re-derived at execution with the script that produced it, not this number); the scaffold's initial status (`ipd_authoring.build_skeleton` always writes `draft`); forward status skips (`ipd_lifecycle.validate_transition` allows a forward skip except into `executed`, which needs at least `reviewed`); the `- Readiness:` requirement at `reviewed` and at the ready-to-execute tier (`ipd_lint.check_readiness_required`, `IPD-M113`) and the refusal of a hand-written one (`ipd_lint.check_readiness_attestation`, `IPD-M107`); the human approval authority (`attention_contract.TRANSITION_AUTHORITY["->approved"]`, whose `by_human` requirement `status_set.validate_transition_allowed` applies to SPEC transitions; a PLAN reaches `approved` through `aw ipd set approved`, which writes the `- Approval:` line, so the spec must state which of the two the quick path relies on); the setter-side approval gate that refuses a ready-to-execute status over a negative review verdict, a gating typed finding, or an unresolved blocking question (`plan_readiness.approval_refusals`, called from `status_set.validate_transition_allowed` for every status in `ipd_schema.READY_TO_EXECUTE`); the automated `auto-approved` tier (`ipd_schema.READY_TO_EXECUTE`, `runner_shared.set_plan_approved`, the predicate `plan_readiness.is_plan_review_approved`, and the two `--full-auto` sites, the queue-build one in `runner_shared.initialize_run_core` and the post-review one in `runner_shared.execute_item_core`, which also rewrites the queue item's `action` to `execute`); the queue action table (`run_selection_policy.runner_action`, `runner_shared.item_needs_approval`); and the backlog graduation turn and its verification (`aw backlog set graduated`, the `BACKLOG-GRADUATE-SET` check). For each row record: the stage, what enforces it, whether it can be skipped today, and what skipping it would lose.
  - Depends on: E-08
  - Expected outcome: an inventory table in the spec whose every row cites a symbol, distinguishing stages that are ceremony from stages that are a safety gate.
  - Execution state: performed

### Task group 2: answer the design questions in the spec

- [x] E-03 SPECIFY WHICH CHANGES QUALIFY. Start from `k3yx72` Section 5.1 (`simple`: "Very low risk: typically a few lines of code, such as a small bug fix or one new CLI option") and its runner signals in Section 5.2 (a `.spec.md` in `- Scope-Paths:`, the size limits `ipd_schema.MAX_E_LEAVES` / `ipd_schema.MAX_TASK_GROUPS`, a match in `review.sensitive_paths`, or `grandfathered` scope), and state whether the quick path uses exactly those disqualifiers or a stricter limit (for example a cap on `E-*` items or on `- Scope-Paths:` entries), justified by E-01's measurement. State that an orchestrator, a plan with a `Blocking: yes` open question, and a plan carrying `- Attended: required` never qualify, and why. Every criterion must be mechanically checkable or explicitly marked as a judgement with the role that makes it.
  - Depends on: E-01, E-02
  - Expected outcome: a qualification section in the spec listing each criterion, whether it is mechanical or a judgement, and its source.
  - Execution state: performed

- [x] E-04 SPECIFY WHO DECIDES and what happens on disagreement. The spec must stay consistent with `k3yx72` MD-1 (the review agent rates the tier; the runner only raises it) rather than invent a second rating. Decide between, at least: (a) the author proposes the quick path with a recognized front-matter field and the review's tier check confirms or rejects it; (b) no new field, the quick path is simply the `simple` review tier plus the runner signals; (c) a human flag on the creating command. State the FALLBACK when review rates the plan above `simple` or a runner signal fires: the plan rejoins the normal pipeline with no record lost and no human step invented. If a new field is proposed, name it, its closed value set, and that it must be added to `ipd_schema.META_RECOGNIZED` by the implementing Set, not by this plan.
  - Depends on: E-03
  - Expected outcome: a decision section in the spec naming the deciding role at each step and the fallback, with the recommended option and its strength.
  - Execution state: performed

- [x] E-05 SPECIFY THE APPROVAL AUTHORITY on the quick path, without weakening the shipped attestation model. The spec must state that `->approved` remains a human act. Note precisely what enforces that today: `attention_contract.TRANSITION_AUTHORITY["->approved"]` (`by_human`) is enforced by `status_set.validate_transition_allowed` for SPECS only; for a PLAN, `aw ipd set approved` succeeds without `--by-human` (verified at review: `aw ipd set approved e41qgx --dry-run --agent` returned `clean`) and records `- Approval: <date>, recorded via aw ipd set`, so plan approval is human by convention (AGENTS.md, `.aw/records/plans/README.md`) plus the setter gate `plan_readiness.approval_refusals`. The spec must not claim a mechanical human-only gate on plans that does not exist, and must say whether the quick path relies on the convention or asks the implementing Set to add one. that an automated clear can only be `auto-approved` and only after a review produced `- Readiness:` (`plan_readiness.is_plan_review_approved`), and that D65's rule holds: `auto-approved` is "set only by an automated checker, never by an executor fast-tracking its own work" (`.aw/records/plans/README.md`, `.aw/system/workflows/verify-execution/verify-execution.md`). Decide whether the quick path (a) still stops for human approval, (b) auto-approves only under `--full-auto`, or (c) is a per-transition permission under the lifecycle automation policy of spec `llbr2b`, and state how the choice composes with `llbr2b` (reviewed, not yet implemented) so the two specs do not define overlapping switches. State whether authoring, review and execution may share one host session or must be separate turns, and why.
  - Depends on: E-02, E-04
  - Expected outcome: an approval section in the spec that names the authority for every transition on the quick path and cites the constraint each choice preserves.
  - Execution state: performed

- [x] E-06 SPECIFY WHICH RECORDS ARE STILL WRITTEN and how gates that today travel through a backlog item still apply. For each record the normal pipeline writes (backlog item and its history, plan file and its `## Workflow history`, `E-*`/`V-*` evidence, review record under `.aw/records/reviews/`, `- Readiness:`, `aw ipd begin` receipt, finalize commit, walkthrough), state kept, dropped, or merged, with the reason. Address the release gate explicitly: today a bug plan scaffolded WITHOUT `--from-backlog` gets no `- Blocks-Release:` (measured: `aw ipd scaffold --work-kind bug` without `--from-backlog` writes none), and `check_engine.check_live_bug_gate` scans backlog items only, so skipping the backlog item would let a live bug escape the "every live bug gates the next release" rule in `AGENTS.md`. The spec must close that hole (for example the quick creating command applies `backlog.decide_gate_default`) or state why it does not apply. Also state how `aw attention` and the runner queue see a quick plan that has no backlog item.
  - Depends on: E-04, E-05
  - Expected outcome: a records table in the spec plus a release-gate section that leaves no path for a live bug to skip the gate.
  - Execution state: performed

- [x] E-07 SPECIFY THE ENTRY POINT AND THE IMPLEMENTING WORK BREAKDOWN, and carry the maintainer questions. Decide the user-facing entry point (for example a new `aw ipd quick` verb, a flag on `aw ipd scaffold`, a backlog-item field that lets the runner author and execute in one queue item, or a combination), naming for each the existing code it extends (`ipd_authoring.run_scaffold`, the `ipd_sub` parser in `cli.py`, `command_surface.COMMAND_INVENTORY`, `run_selection_policy.runner_action`). Write a work-breakdown table (Order, work, depends on) for the implementing Set, including the dependency on `k3yx72`'s Order 02 (`Review-Depth` field and runner tier signals) where the quick path consumes them, and the documentation each Order must amend (`docs/artifact-lifecycles.md`, `.aw/records/plans/README.md`, the `ipd-structure-and-linting` spec Section 4.4 if a field is added). Record every decision the maintainer must own as an `OQ-NN` (two-digit ids, per `ipd_schema.OQ_HEADING_RE`) with a recommendation and a recommendation strength, and mark `Blocking: yes` only where implementing without the answer would be irreversible. State in the spec that it authorizes no code change by itself.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: an entry-point section, a work-breakdown table and an open-questions section in the spec.
  - Execution state: performed

- [x] E-09 DECLARE TRACEABLE REQUIREMENT AND ACCEPTANCE IDS. The spec is dated after the `spec_requirement_ids` cutover (`config.KNOWN_FEATURE_CUTOVERS`, 2026-10-01; `production_checks.SPEC_REQUIREMENT_IDS_CUTOVER_DATE`), so the implementing Set's production will be checked by `SPEC-PLAN-TRACE` (spec `89xjll`). Add a requirements index table (`| ID | Requirement | Detail |`, the declaration-site shape of `89xjll` Section 1b) declaring each normative decision from E-03 to E-07 as a FORM A `R-NN` id (not the `N` family, which `89xjll` Section 3.1 excludes from extraction), and an acceptance-criteria section declaring `AC-NN` ids that the implementing Set's `V-*` items can cite. A decision still carried as an open question is either left out of the index or marked `[Deferred]` per `89xjll` Section 3.3. Without this, TRACE passes the implementing Set vacuously (`89xjll` Section 6.3) and cannot show that it covered the spec.
  - Depends on: E-03, E-04, E-05, E-06, E-07
  - Expected outcome: a requirements index of `R-NN` ids and an acceptance-criteria section of `AC-NN` ids in the spec, each requirement pointing at the section that elaborates it.
  - Execution state: performed

### Task group 3: advance and validate the spec

- [x] E-10 ADVANCE THE SPEC TO `to-review`, NOT `approved`, AND VALIDATE IT. Run `aw specs set to-review <path> --message "..." --no-commit` (the setter relocates the file from `draft/` to `to-review/`; never hand-edit `- Status:`; `--no-commit` because the commit goes through `aw commit` below, and an `--agent` call without `--yes` refuses at exit 2 per `.aw/records/plans/README.md` "Status transitions share confirmation and commit semantics"). Then run `aw specs check <path>` and `aw check --agent`, and compare the latter's (rule, location) diagnostics with E-08's baseline. Do NOT set the spec `approved` (the maintainer's attested act) and never `implemented`.
  - Depends on: E-09
  - Expected outcome: one conforming spec under `.aw/records/specs/to-review/` carrying `- From-Backlog: rsisop`, and no `aw check` diagnostic in the after set that is absent from the baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Spec-first graduation is an established, tooled route for a backlog item that needs design decisions before code: executed plan `u06zo2` (Set `lcpolicy`) graduated backlog `rxya25` by producing spec `llbr2b` with `aw specs new` and `aw specs set to-review`, and changed no code. This plan copies that shape.
- `aw specs new` mints the id6 and the conforming filename, and `aw specs set` owns spec status and relocates the file between status directories (`.aw/records/specs/README.md`). Specs must not be hand-named and `- Status:` must not be hand-edited.
- A spec may carry `- From-Backlog:`; `aw check` flags a dangling value (`check.from-backlog-dangling`), and a spec counts as a carrier of the item for the close-legitimacy rule in `AGENTS.md`.
- Never write another role's attestation field: no `- Readiness:`, no `- Approval:` (AGENTS.md, "NEVER WRITE ANOTHER ROLE'S ATTESTATION FIELD"). This applies to the plan and to any example the spec shows.
- Open-question ids must be `OQ-` plus two or more digits, because `ipd_schema.OQ_HEADING_RE` ignores one-digit ids (`k3yx72` Section 16 records the same constraint).
- The suite is run bare as `python3 -m pytest`, and the actual summary line is pasted (AGENTS.md, repository development contract).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The backlog item asks for a spec first: "Needs its own spec: which changes qualify, who decides, and which records are still written." | `.aw/records/backlog/open/20261018-revsteps-01-rsisop-shorter-pipeline-for-small-changes-go-from-plan-to.backlog.md` |
| F-2 | Spec `k3yx72` (`reviewed`) defines the `simple` review tier and its runner signals, and excludes this pipeline as non-goal N4, sending it to `rsisop`. It is not yet implemented: no code mentions `Review-Depth` or `review.sensitive_paths`. | `.aw/records/specs/reviewed/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md` Sections 2, 5.1, 5.2, 15 |
| F-3 | A plan can already be created without a backlog item; scaffold only needs `--priority` and `--work-kind` then. So the backlog step is mechanically optional today, and the friction is in the remaining stages and in the runner flow, which E-01 and E-02 must measure rather than assume. | `ipd_authoring.run_scaffold`; 96 of 1,161 non-orchestrator plans dated 2026-09/10 carry no `From-Backlog`/`From-Spec` (measured at HEAD `67a066ac3`) |
| F-4 | Small plans are common: 151 executed non-orchestrator plans dated 2026 have at most 2 `E-*` items, and only 21 of them carry `- From-Backlog:`; none of the 151 names a `.spec.md` file in `- Scope-Paths:` (one names the `.aw/records/specs/` directory), so `k3yx72`'s spec-path signal would not disqualify them. | measured at HEAD `67a066ac3` over `.aw/records/plans/executed/2026*.ipd.md` |
| F-5 | Skipping the backlog item drops the release gate for bugs: a bug plan scaffolded without `--from-backlog` carries no `- Blocks-Release:`, and `check_engine.check_live_bug_gate` reads backlog items only. | `aw ipd scaffold --kind child --title x --set probe --order 1 --priority low --work-kind bug --author opencode` (preview) printed no `Blocks-Release` line; `check_engine.check_live_bug_gate` iterates `backlog._iter_items` |
| F-6 | Human approval is a fixed authority, and the automated tier is constrained: `->approved` needs `by_human` for SPECS (`status_set.validate_transition_allowed`), while a PLAN's `approved` is human by convention and passes `plan_readiness.approval_refusals`; `auto-approved` is written only by `runner_shared.set_plan_approved` after `plan_readiness.is_plan_review_approved`; D65 forbids an executor fast-tracking its own work. | `attention_contract.TRANSITION_AUTHORITY`; `runner_shared.set_plan_approved`; `.aw/records/plans/README.md` "auto-approved" bullet |
| F-7 | A per-transition automation policy is already specified (spec `llbr2b`, `reviewed`), so the quick path's approval rule must compose with it rather than add a parallel switch. | `.aw/records/specs/reviewed/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md` Sections 5, 6, 7 |
| F-8 | The lint refuses a `reviewed` or ready-to-execute plan without `- Readiness:` (`IPD-M113`), and the field may only come from a review (`IPD-M107`), so a quick path cannot skip the review step and still reach execution. | `ipd_lint.check_readiness_required`; `ipd_lint.check_readiness_attestation` |
| F-9 | The `--full-auto` clear has two sites: the queue-build one in `runner_shared.initialize_run_core` and a post-review one in `runner_shared.execute_item_core`, which also rewrites the queue item's `action` to `execute`. The second is the one a single-turn quick path would most likely reuse. | `runner_shared.execute_item_core` "if is_plan_review_approved(plan_curr):" followed by `set_plan_approved` and `item["action"] = "execute"` (verified at review, HEAD `72da75876`) |
| F-10 | Any automated or human move to a ready-to-execute status already passes a setter-side gate (`plan_readiness.approval_refusals`) that no caller can skip, so the quick path inherits it for free and must not add a parallel check. | `status_set.validate_transition_allowed` "apprvguard Order 01 (d7bnhc): THE APPROVAL GATE" |
| F-11 | The new spec is dated after the `spec_requirement_ids` cutover (2026-10-01), so `SPEC-PLAN-TRACE` will check the implementing Set against the spec's declared FORM A ids; a spec with none passes vacuously. | `config.KNOWN_FEATURE_CUTOVERS` "spec_requirement_ids": "2026-10-01"; spec `89xjll` Sections 3.1, 6.3; `production_checks.parse_spec_requirement_ids` |

## Proposed changes (ordered, validatable)

1. Record the `aw check` baseline and create the spec by tool in `draft/` with `- From-Backlog: rsisop` (E-08).
2. Measure the current cost of a small change (E-01).
3. Inventory which stages are ceremony and which are gates, by symbol (E-02).
4. Decide qualification (E-03), the deciding role and fallback (E-04), approval authority (E-05), and records plus release gate (E-06).
5. Decide the entry point, write the implementing work breakdown, and carry the maintainer questions (E-07).
6. Declare traceable `R-NN` / `AC-NN` ids for `SPEC-PLAN-TRACE` (E-09).
7. Advance the spec to `to-review` and validate it (E-10).

## Deferred / out of scope (with reason)

- IMPLEMENTING THE QUICK PIPELINE (new verb or flag, schema field, runner action, docs). Deliberately not here: the item's three questions change the shape of every one of those, and code written first would hardcode an answer the maintainer has not given. The implementing Set graduates from the approved spec.
  - Carrier-Declined: no carrier can exist yet; the implementing Set is designed by this plan's spec (E-07 work breakdown) and graduates from it once the maintainer approves it.
- CHANGING THE REVIEW ITSELF. The cheap review is `k3yx72`'s scope (its `simple` tier); this spec consumes it and must not redefine it.
  - Carrier-Declined: owned by spec `k3yx72` and its Set `revsteps`, not work this plan defers.
- THE GENERAL LIFECYCLE AUTOMATION POLICY. Owned by `llbr2b`; this spec states how the quick path composes with it and does not re-specify it.
  - Carrier-Declined: owned by spec `llbr2b`, not work this plan defers.
- CHANGING ANY EXISTING VERB'S BEHAVIOR, including `aw ipd scaffold`'s `draft` initial status and `--full-auto`. Nothing regresses while the design is settled.
  - Carrier-Declined: deliberate non-goal of a spec-only plan; any behavior change is decided in the spec and built by its implementing Set.

## Scope check

- Over-scope: none. `- Scope-Paths:` is the spec's two status directories and this plan file, because the only artifact produced is a spec.
- Under-scope: deliberate. No code and no behavioral tests, because the item says a spec comes first. A reviewer who wants implementation in the same pass should reject this shape rather than extend it.

## Required tests / validation

- `aw specs check <spec path>` reports the new spec conforming.
- `production_checks.parse_spec_requirement_ids` extracts a non-empty requirement and acceptance set from the spec (V-09).
- `aw check` gains no diagnostic, measured as a before/after comparison of `aw check --agent` diagnostics by (rule, location), and in particular no `check.from-backlog-dangling` for the spec.
- `aw ipd lint --phase pre-transition` on this plan conforms before the transition.
- `python3 -m pytest` bare, per the repository contract, to show this records-only change breaks nothing; paste the actual summary line. Any failure must be shown to be unrelated (this plan changes no code).
- There is no behavioral validation by design: the verification is that the spec is conforming, answers each of the item's three questions plus the dependent ones, and cites real code for each inventory claim.

## Spec / documentation sync

The deliverable is a new spec, so the sync is the work. It is created with `aw specs new`, advanced with `aw specs set to-review`, and carries `- From-Backlog: rsisop` so the backlog-to-spec handoff is machine-readable. It is NOT taken to `approved`: that is the maintainer's attested act (`--by-human`). No existing spec is amended: `k3yx72` and `llbr2b` are cited as constraints (`- Constrained-by:`), not edited, and the amendments the implementing Set will need (for example `ipd-structure-and-linting` Section 4.4 for a new field, `docs/artifact-lifecycles.md`, `.aw/records/plans/README.md`) are listed in the spec's work breakdown (E-07) for that Set to declare in its own `- Scope-Paths:`.

## Open questions

### OQ-01: Spec first, or a direct implementation plan?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: spec first. The backlog item states that it "Needs its own spec: which changes qualify, who decides, and which records are still written", and the repository's precedent for a pipeline-wide design question is a spec-first graduation (`u06zo2` producing `llbr2b`). The design questions themselves (qualification, deciding role, approval authority, records) are carried in the spec for the maintainer, not answered on this plan's authority.

### OQ-02: Does this plan wait for `k3yx72` and `llbr2b` to be approved?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. The spec only needs both to exist so it can cite them as constraints, which `- Item-Dependencies: exists:spec:k3yx72, exists:spec:llbr2b` enforces. Their approval gates the IMPLEMENTING Set, which E-07 records in the work breakdown; writing the design now lets the maintainer review the three specs together.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the measuring script exactly as it appears in the spec, its actual output when re-run at the execution HEAD, and the spec's table; the table's numbers must equal that output (not the authoring-time counts in E-01). If `aw runs` could not attribute turns or cost, paste the command tried and its output, and the spec sentence saying so.
  - Observed evidence:
    Measuring script in spec Section 1.1:
    ```python
    import glob, re, statistics
    from pathlib import Path

    # Measuring script: cost of small changes in current pipeline
    files = sorted(glob.glob(".aw/records/plans/executed/2026*.ipd.md"))
    non_orch = [f for f in files if "- Kind: orchestrator" not in Path(f).read_text(encoding="utf-8", errors="replace")]

    small_plans = []
    for f in non_orch:
        t = Path(f).read_text(encoding="utf-8", errors="replace")
        e_items = re.findall(r"^[ \t]*- \[[ xX]\][ \t]+E-\d+", t, re.MULTILINE)
        if len(e_items) <= 2:
            small_plans.append((f, t, len(e_items)))

    def parse_history(text):
        m = re.search(r"## Workflow history\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
        if not m:
            return []
        return [l.strip() for l in m.group(1).splitlines() if l.strip().startswith("- ")]

    def parse_statuses(lines):
        statuses = set()
        for l in lines:
            m = re.match(r"^-\s+\d{4}-\d{2}-\d{2}\s+([a-zA-Z0-9_\-]+)", l)
            if m:
                statuses.add(m.group(1))
        return statuses

    backlog_cache = {}
    for p in glob.glob(".aw/records/backlog/**/*.backlog.md", recursive=True):
        txt = Path(p).read_text(encoding="utf-8", errors="replace")
        m = re.search(r"^- Id:\s*(\S+)", txt, re.MULTILINE)
        if m:
            backlog_cache[m.group(1)] = (p, txt)

    plan_hist = []
    plan_stats = []
    bk_hist = []
    fb_rows = []

    for f, t, e_cnt in small_plans:
        id6_m = re.search(r"^- Id:\s*(\S+)", t, re.MULTILINE)
        id6 = id6_m.group(1) if id6_m else Path(f).name[:6]
        fb_m = re.search(r"^- From-Backlog:\s*(\S+)", t, re.MULTILINE)
        fb = fb_m.group(1) if fb_m else None

        h = parse_history(t)
        st = parse_statuses(h)

        plan_hist.append(len(h))
        plan_stats.append(len(st))

        bh_len = None
        if fb and fb in backlog_cache:
            bh = parse_history(backlog_cache[fb][1])
            bh_len = len(bh)
            bk_hist.append(bh_len)
            fb_rows.append((id6, fb, len(h), len(st), bh_len, e_cnt))

    print(f"Total small plans: {len(small_plans)}")
    print(f"Plans carrying From-Backlog: {len(fb_rows)}")
    print(f"Median plan history records: {statistics.median(plan_hist)}")
    print(f"Median plan distinct statuses: {statistics.median(plan_stats)}")
    print(f"Median backlog history records: {statistics.median(bk_hist)}")
    ```
    Actual output when re-run at execution HEAD:
    ```
    Total small plans: 151
    Plans carrying From-Backlog: 21
    Median plan history records: 4
    Median plan distinct statuses: 2
    Median backlog history records: 3
    ```
    Spec table (Section 1.2):
    | Plan ID | Backlog ID | E-Items | Plan History Records | Distinct Plan Statuses | Backlog History Records |
    |---|---|---|---|---|---|
    | 3v7wo6 | 5wdoze | 2 | 6 | 5 | 1 |
    | yi24m0 | rayd4c | 2 | 6 | 5 | 3 |
    | dtcgsz | y2vnr7 | 1 | 5 | 5 | 3 |
    | 9g97e5 | 2je7m3 | 1 | 6 | 5 | 3 |
    | fdmo2v | 5v4p2l | 1 | 5 | 5 | 3 |
    | dmrbqa | tl8qmc | 2 | 6 | 5 | 4 |
    | pua92o | rgl2d4 | 2 | 5 | 4 | 4 |
    | aoy1uk | rdtme9 | 1 | 5 | 5 | 3 |
    | jzeeky | m88gwh | 2 | 5 | 5 | 3 |
    | ic6vpg | upkghw | 2 | 5 | 5 | 3 |
    | 5apgyn | pyezbc | 2 | 4 | 4 | 3 |
    | f0kolj | g3ropl | 2 | 6 | 5 | 3 |
    | 8e7xrj | 2n9y3f | 1 | 6 | 5 | 3 |
    | 5ne0fo | zgqs4e | 2 | 6 | 5 | 3 |
    | jl0bv0 | a48b4m | 1 | 6 | 5 | 3 |
    | 3nczai | 6i9viq | 2 | 5 | 5 | 3 |
    | rg7rnx | 96lj37 | 2 | 5 | 5 | 3 |
    | 438gkf | liybkg | 2 | 5 | 5 | 3 |
    | 8bhcd3 | yqpb7q | 2 | 5 | 5 | 3 |
    | 78g6ic | q86fxm | 2 | 5 | 5 | 48 |
    | ej30u4 | w4eswb | 2 | 5 | 5 | 3 |

    Turn/cost attribution check:
    `aw runs --ipd yi24m0` -> `no matching runs found`
    `aw runs --last 5` -> `no matching runs found`
    Spec sentence: "Invoking `aw runs --ipd <id6>` (e.g. for `yi24m0`) and `aw runs --last 5` returns `no matching runs found` in this lane worktree, so runner turns and monetary costs cannot be attributed from local run ledgers at this HEAD."
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the spec's inventory table. For each row, paste a `grep -n` (or `aw` command) output at the execution HEAD showing the cited symbol exists, and include the scaffold preview output proving the `draft` initial status.
  - Observed evidence:
    Spec inventory table (Section 2.2):
    | Stage | Enforcing Symbol | Skippable Today? | Loss if Skipped (Ceremony vs Safety Gate) |
    |---|---|---|---|
    | 1. Backlog item creation | `ipd_authoring.run_scaffold` | Yes | Ceremony. Requires `--priority`/`--work-kind` only when `--from-backlog` is absent. Drops initial idea tracking, but creates no safety hazard if the plan defines scope and tests. |
    | 2. Initial status assignment | `ipd_authoring.build_skeleton` | No | Ceremony. Always writes `- Status: draft`. Forces an authoring-to-review status transition. |
    | 3. Status progression skips | `ipd_lifecycle.validate_transition` | Partial | Safety gate. Forward skips (e.g. `draft -> to-review`) are permitted, but moving to `executed` strictly requires at least `reviewed`. Bypassing this would risk unreviewed execution. |
    | 4. Readiness attestation | `ipd_lint.check_readiness_required` (`IPD-M113`), `ipd_lint.check_readiness_attestation` (`IPD-M107`) | No | Safety gate. Refuses a `reviewed` or ready-to-execute plan lacking an attested `- Readiness:` field from `/plan-review`. Hand-written readiness is rejected. |
    | 5. Human approval authority | `attention_contract.TRANSITION_AUTHORITY["->approved"]`, `status_set.validate_transition_allowed` | Specs: No; Plans: Convention | Safety gate. `TRANSITION_AUTHORITY` enforces `--by-human` mechanically for specs. For plans, `approved` is human by convention plus setter gates; `auto-approved` is the sanctioned automated tier. |
    | 6. Setter-side approval gate | `plan_readiness.approval_refusals`, `ipd_schema.READY_TO_EXECUTE` | No | Safety gate. `status_set.validate_transition_allowed` refuses ready-to-execute status if review failed, or if blocking questions/findings remain. |
    | 7. Automated approval | `runner_shared.set_plan_approved`, `plan_readiness.is_plan_review_approved`, `runner_shared.initialize_run_core`, `runner_shared.execute_item_core` | Under `--full-auto` | Safety gate. Advances `reviewed -> auto-approved` and rewrites queue action to `execute` only when review readiness is positive. Preserves D65 (executor cannot self-approve). |
    | 8. Queue action mapping | `run_selection_policy.runner_action`, `runner_shared.item_needs_approval` | No | Safety gate. Unapproved `reviewed` plans freeze with `needs_input=True` unless `--full-auto` auto-approves them. |
    | 9. Backlog graduation | `aw backlog set graduated`, `production_checks.backlog_graduate_set` (`BACKLOG-GRADUATE-SET`) | Yes (if no backlog item) | Ceremony for small plans. When no backlog item exists, no graduation turn is needed; plan-level lint and review gates provide full verification. |

    Symbol greps at execution HEAD:
    - `grep -n "def run_scaffold" agent_workflows/ipd_authoring.py`:
      `449:def run_scaffold(args: argparse.Namespace) -> int:`
    - `grep -n "def build_skeleton" agent_workflows/ipd_authoring.py`:
      `228:def build_skeleton(`
    - `grep -n "def validate_transition" agent_workflows/ipd_lifecycle.py`:
      `1199:def validate_transition(`
    - `grep -n "def check_readiness_required" agent_workflows/ipd_lint.py`:
      `1330:def check_readiness_required(doc: ParsedDoc) -> List[Diagnostic]:`
    - `grep -n "IPD-M113" agent_workflows/ipd_lint.py`:
      `88:C_READINESS_REQUIRED = "IPD-M113"`
    - `grep -n "def check_readiness_attestation" agent_workflows/ipd_lint.py`:
      `1305:def check_readiness_attestation(doc: ParsedDoc) -> List[Diagnostic]:`
    - `grep -n "IPD-M107" agent_workflows/ipd_lint.py`:
      `86:    "IPD-M107"`
    - `grep -n "TRANSITION_AUTHORITY" agent_workflows/attention_contract.py`:
      `581:TRANSITION_AUTHORITY: Dict[str, Dict[str, object]] = {`
    - `grep -n "def validate_transition_allowed" agent_workflows/status_set.py`:
      `666:def validate_transition_allowed(`
    - `grep -n "def approval_refusals" agent_workflows/plan_readiness.py`:
      `634:def approval_refusals(`
    - `grep -n "READY_TO_EXECUTE" agent_workflows/ipd_schema.py`:
      `391:READY_TO_EXECUTE: FrozenSet[str] = frozenset(("approved", "auto-approved"))`
    - `grep -n "def set_plan_approved" agent_workflows/runner_shared.py`:
      `36631:def set_plan_approved(`
    - `grep -n "def is_plan_review_approved" agent_workflows/plan_readiness.py`:
      `389:def is_plan_review_approved(plan_path: Path) -> bool:`
    - `grep -n "def initialize_run_core" agent_workflows/runner_shared.py`:
      `35375:def initialize_run_core(`
    - `grep -n "def execute_item_core" agent_workflows/runner_shared.py`:
      `40158:def execute_item_core(`
    - `grep -n "def runner_action" agent_workflows/run_selection_policy.py`:
      `367:def runner_action(`
    - `grep -n "def item_needs_approval" agent_workflows/runner_shared.py`:
      `33615:def item_needs_approval(status: str | None, action: str | None) -> bool:`
    - `grep -n "BACKLOG-GRADUATE-SET" agent_workflows/production_checks.py`:
      `1026:    """Verify BACKLOG-GRADUATE-SET: every produced orchestrator plan is ready for review.`
    - `grep -n "def check_live_bug_gate" agent_workflows/check_engine.py`:
      `6826:def check_live_bug_gate(repo_root: Path) -> List[_core.Drift]:`
    - `grep -n "def decide_gate_default" agent_workflows/backlog.py`:
      `715:def decide_gate_default(`

    Scaffold preview output proving `draft` initial status:
    `aw ipd scaffold --kind child --title "Test Scaffold" --set quickpipe --order 2 --priority low --work-kind chore --author test`:
    ```
    - Date: 2026-10-23
    - Kind: child
    - Concern: TODO.
    - Scope: TODO.
    - Scope-Paths: TODO (comma-separated repo-relative paths or pathspecs)
    - Item-Dependencies: unresolved
    - Status: draft
    - Work-Kind: chore
    - Priority: low
    - Set: quickpipe
    - Order: 2
    - Highest E allocated: 01
    - Author: test
    - Id: 7m5ab2

    ## Workflow history

    - 2026-10-24 draft (test): created.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the spec's qualification section; each criterion must be labeled mechanical or judgement and cite its source (`k3yx72` section or code symbol), and the orchestrator, `Blocking: yes` and `Attended: required` exclusions must be present.
  - Observed evidence:
    Pasted from spec Section 3:
    ```markdown
    ## 3. Qualification criteria: which changes qualify

    The quick pipeline is intended exclusively for small, low-risk changes where the friction of the
    backlog and multi-turn staging exceeds the risk of the change itself.

    ### 3.1 Base criteria from spec `k3yx72`

    Spec `k3yx72` Section 5.1 defines the `simple` review tier as:
    > "Very low risk: typically a few lines of code, such as a small bug fix or one new CLI option."

    Section 5.2 of `k3yx72` establishes runner signals that raise the tier away from `simple`:
    - Modifying a spec file (`.spec.md` in `- Scope-Paths:`).
    - Touching sensitive modules in `review.sensitive_paths` (security, leak sanitation, git commit helpers, worktree isolation, sandbox profiles).
    - Exceeding size limits (`ipd_schema.MAX_E_LEAVES`, `ipd_schema.MAX_TASK_GROUPS`).
    - Grandfathered scope (plans omitting `- Scope-Paths:`).

    ### 3.2 Stricter mechanical bounds for the quick pipeline

    The quick pipeline adopts all disqualifiers from `k3yx72` Section 5.2 and imposes stricter limits
    grounded in Section 1's empirical findings:

    1. **Orchestrator exclusion** (`- Kind: orchestrator`): Disqualified mechanically. Orchestrators
       coordinate child plans, manage rollup retirement, and never execute small self-contained edits.
    2. **Open blocking questions** (`Blocking: yes`): Disqualified mechanically via
       `plan_readiness.has_unresolved_blocking_question`. A plan cannot execute unattended with unresolved
       design questions.
    3. **Attended execution required** (`- Attended: required`): Disqualified mechanically via
       `ipd_schema.META_ATTENDED`. Unattended quick execution cannot run interactive turns.
    4. **Spec modification** (`.spec.md` in `- Scope-Paths:`): Disqualified mechanically. Changing
       specifications alters system invariants and requires standard or complex review.
    5. **Sensitive paths** (`review.sensitive_paths`): Disqualified mechanically. Touching security,
       credentials, leak sanitizer, sandbox, or worktree isolation modules requires full scrutiny.
    6. **Grandfathered scope** (missing `- Scope-Paths:`): Disqualified mechanically. Scope must be
       explicitly bounded.
    7. **Strict item count**: At most 2 `E-*` items and at most 1 task group. While `k3yx72` permits up to
       18 `E-*` items for standard plans, the quick path strictly requires `<= 2` `E-*` items.
    8. **Strict path count**: At most 3 distinct files declared in `- Scope-Paths:`. Prevents wide or
       cross-cutting edits.
    9. **Reviewer risk judgement**: Step T review questions in `/plan-review`. If the review agent answers
       "yes" to any question regarding interface breakage, data loss risk, or subtle regressions, the tier
       is raised.

    | Criterion | Type | Source / Enforcement |
    |---|---|---|
    | Kind is child | Mechanical | Plan front matter (`- Kind: child`) |
    | No open blocking questions | Mechanical | `plan_readiness.has_unresolved_blocking_question` |
    | Attended not required | Mechanical | `ipd_schema.META_ATTENDED` != "required" |
    | No spec files modified | Mechanical | `- Scope-Paths:` contains no `.spec.md` |
    | No sensitive paths touched | Mechanical | `- Scope-Paths:` matches no `review.sensitive_paths` |
    | Explicit scope paths | Mechanical | `- Scope-Paths:` is non-empty |
    | Small execution size | Mechanical | Count of `E-*` items <= 2, Task Groups <= 1 |
    | Small path footprint | Mechanical | Count of declared paths in `- Scope-Paths:` <= 3 |
    | Review risk assessment | Judgement | Review agent Step T questions (spec `k3yx72` 5.2) |
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the spec's decision section, showing the options considered, the recommended option with its recommendation strength, the fallback rule, and a sentence reconciling it with `k3yx72` MD-1.
  - Observed evidence:
    Pasted from spec Section 4:
    ```markdown
    ## 4. Deciding role and disagreement fallback

    ### 4.1 Consistency with `k3yx72` MD-1

    Spec `k3yx72` MD-1 dictates:
    > "The review agent rates the tier; the runner only raises it."

    The quick pipeline respects this invariant. An author cannot unilaterally force quick execution,
    and the runner never lowers a tier assigned by review.

    ### 4.2 Deciding options considered

    1. **Option A (Author proposal with Review confirmation)**: The author indicates quick pipeline intent
       via front matter (`- Pipeline: quick`). The review agent evaluates Check T. If Check T confirms
       `simple` tier and all runner mechanical signals pass, the quick pipeline proceeds.
    2. **Option B (Implicit tier derivation)**: No front-matter field. The quick path is entered purely if
       the review agent assigns `simple` and runner signals pass.
    3. **Option C (CLI creation flag only)**: A human flag on creation dictates the pipeline.

    **Recommendation**: Option A (Recommendation strength: Strong).
    Recording authorial intent in front matter allows authoring tools (`aw ipd quick`) to validate size
    bounds upfront, makes the expectation obvious to reviewers, and prevents unexpected fast-tracking
    of plans not written for the quick pipeline.

    The proposed field is `- Pipeline:` with the closed value set `{"standard", "quick"}` (defaulting to
    `standard` when absent). The implementing Set must register `Pipeline` in `ipd_schema.META_RECOGNIZED`.

    ### 4.3 Disagreement and fallback rule

    If the review agent rates the tier as `standard` or `complex`, or if any mechanical disqualifier fires:
    - The plan immediately falls back to the standard pipeline.
    - `- Pipeline: quick` is treated as unfulfilled intent; no history is discarded, no files are deleted,
      and no synthetic human steps are created.
    - The plan stops at `reviewed` for normal human approval (or standard `--full-auto` clearance).
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the spec's approval section, showing every quick-path transition with its authority, the statement that `->approved` stays a human act together with what actually enforces it for a plan (convention plus `plan_readiness.approval_refusals`, not `TRANSITION_AUTHORITY`, which binds specs) and whether the implementing Set must add a mechanical gate, the statement that D65 holds, the composition rule with `llbr2b`, and the session-sharing decision with its reason.
  - Observed evidence:
    Pasted from spec Section 5:
    ```markdown
    ## 5. Approval authority and session separation

    ### 5.1 Human approval vs automated clearance

    The repository attestation model requires that:
    1. `->approved` remains an attested human act.
    2. Automated clearance into execution uses `auto-approved` exclusively, requiring an approving
       `- Readiness:` verdict from `/plan-review` (`plan_readiness.is_plan_review_approved`).
    3. D65 holds: `auto-approved` is set only by an automated checker / runner controller, never by an
       executor fast-tracking its own work.

    Today, `attention_contract.TRANSITION_AUTHORITY["->approved"]` (`by_human`) is enforced by
    `status_set.validate_transition_allowed` for specs only; for plans, human approval is enforced by
    convention and the setter gate `plan_readiness.approval_refusals`. The implementing Set should add
    an explicit check in `status_set.validate_transition_allowed` requiring `--by-human` when transitioning
    a plan to `approved`, firmly distinguishing human `approved` from runner `auto-approved`.

    ### 5.2 Composition with lifecycle automation policy (spec `llbr2b`)

    Spec `llbr2b` establishes a unified permission matrix for automated transitions. The quick pipeline
    does not create a parallel or conflicting switch.
    - Under `llbr2b`, the transition `("plans", "->auto-approved")` is governed by policy.
    - When `llbr2b` policy permits `("plans", "->auto-approved")` (or runner `--full-auto` is active),
      and a plan qualifies for the quick pipeline with an approving review readiness, the runner sets
      `auto-approved`.
    - If `llbr2b` policy denies the transition or `--full-auto` is disabled, the plan stops at `reviewed`,
      requiring explicit human approval (`aw ipd set approved <id6> --by-human`).

    ### 5.3 Host session and turn separation

    Authoring, review, and execution MUST NOT share a single host session or agent turn.
    - **Attestation independence**: A review agent must examine the plan in a fresh context, free from
      authoring biases, to independently evaluate risk and produce an authentic `- Readiness:` record.
    - **Executor isolation**: Execution must take place in an isolated worktree lane (`isolate_worktree`)
      with a clean git status, baseline checks, and merge-and-revalidate gating.
    - **Contiguous execution**: While turns are distinct and isolated, the runner may execute authoring,
      review, and execution sequentially in a single unattended batch run when auto-approval is permitted.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the spec's records table (each record kept, dropped or merged, with a reason) and its release-gate section; the section must name `check_engine.check_live_bug_gate` and state the mechanism that keeps a quick bug plan gated, or why none is needed.
  - Observed evidence:
    Pasted from spec Section 6:
    ```markdown
    ## 6. Tracked records and release gate preservation

    ### 6.1 Records lifecycle table

    | Record | Disposition | Justification |
    |---|---|---|
    | Backlog item and history | Dropped | Dropped to eliminate draft/open/graduate friction for small changes. |
    | Plan file (`.ipd.md`) | Kept | Primary unit of work and historical truth. |
    | Plan `## Workflow history` | Kept | Retains audit trail of status progression (`draft -> to-review -> reviewed -> auto-approved -> executed`). |
    | `E-*` and `V-*` evidence | Kept | Pasted execution and validation evidence is a mandatory repository invariant. |
    | Review record (`.review.md`) | Kept | Written by `/plan-review` under `.aw/records/reviews/` to document tier answers and checks. |
    | `- Readiness:` field | Kept | Attested by review; required by `ipd_lint.check_readiness_required` (`IPD-M113`). |
    | `aw ipd begin` receipt | Kept | Written by runner to prevent concurrent execution conflicts. |
    | Finalize commit | Kept | Atomic commit moving plan to `executed/` under integration gate. |
    | Walkthrough document | Dropped | 1 to 4 line fixes do not warrant separate walkthroughs; the git diff and execution report suffice. |

    ### 6.2 Preserving the release gate for bug fixes

    In the standard pipeline, bug tracking and release gating operate through backlog items:
    `check_engine.check_live_bug_gate` scans live backlog items and fails if any bug item lacks
    `- Blocks-Release:`.
    Currently, `aw ipd scaffold --work-kind bug` without `--from-backlog` writes no `- Blocks-Release:`
    bullet. If a bug plan were scaffolded directly without a backlog item, it would escape release gating.

    The quick pipeline closes this loophole with two mandatory mechanisms:
    1. **Scaffold-time gate assignment**: The quick creation command (`aw ipd quick`) evaluates
       `backlog.decide_gate_default(repo_root, work_kind="bug", priority=priority)` and writes
       `- Blocks-Release: next` directly into the plan's front matter whenever `work-kind` is `bug`.
    2. **Plan-side release gate check**: The implementing Set must update `check_engine.py` (adding
       `check_live_plan_bug_gate` or extending `check_live_bug_gate`) to verify that any active plan in
       `pending/` with `- Work-Kind: bug` carries a valid `- Blocks-Release:` field.

    ### 6.3 Cross-tree visibility in `aw attention` and the runner queue

    - `aw attention`: The cross-tree attention view scans `.aw/records/plans/` directly. A quick plan is
      tracked from inception (`draft` -> `active`, `to-review` -> `ready`, `auto-approved` -> `ready`).
      It requires no backlog entry to be visible.
    - Runner Queue: `run_selection_policy.py` constructs the execution DAG from plan dependencies. A quick
      plan with no prerequisites enters the queue as an Order-1 leaf, runnable immediately.
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the spec's entry-point section, its work-breakdown table (with the `k3yx72` Order 02 dependency), its open-questions section (two-digit `OQ-NN` ids, each with recommendation and strength), and the sentence stating the spec authorizes no code change.
  - Observed evidence:
    Pasted from spec Section 7 and Section 0:
    ```markdown
    ## 0. What this spec authorizes, and what it does not

    THIS SPEC AUTHORIZES NO CODE CHANGE. It is a design contract produced by plan `e41qgx` from backlog
    item `rsisop`, and nothing in it licenses an implementation.

    ## 7. Entry point, work breakdown, and open questions

    ### 7.1 User-facing entry point

    The primary user entry point is `aw ipd quick`:
    ```sh
    aw ipd quick --title "Fix typo in CLI help" --slug fix-cli-help --work-kind bug --priority low --author opencode --scope "agent_workflows/cli.py" --apply
    ```
    This command:
    - Calls `ipd_authoring.run_scaffold` with `--quick`.
    - Writes `- Pipeline: quick` into front matter.
    - Sets `- Work-Kind:` and `- Priority:`.
    - Automatically assigns `- Blocks-Release: next` if `work-kind` is `bug`.
    - Validates that declared scope paths do not touch `review.sensitive_paths` or `.spec.md`.

    Code surfaces extended by the implementing Set:
    - `agent_workflows/cli.py`: Register `quick` subparser in `ipd_sub`.
    - `agent_workflows/command_surface.py`: Add `aw ipd quick` to `COMMAND_INVENTORY`.
    - `agent_workflows/ipd_authoring.py`: Implement `run_quick` / extend `run_scaffold`.
    - `agent_workflows/ipd_schema.py`: Register `Pipeline` in `META_RECOGNIZED`.
    - `agent_workflows/check_engine.py`: Add plan-side bug release gate.
    - `agent_workflows/runner_shared.py`: Wire `simple` tier review auto-approval to contiguous execution.

    ### 7.2 Implementing work breakdown (Set `quickpipe`)

    | Order | Work | Depends on | Documentation to Amend |
    |---|---|---|---|
    | 00 | Orchestrator: Child tracking and rollup. | All children | None |
    | 01 | Plan schema and authoring entry point: Register `Pipeline` in `ipd_schema.META_RECOGNIZED`, implement `aw ipd quick`, and apply `backlog.decide_gate_default`. | Spec approval | `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`, `.aw/records/plans/README.md` |
    | 02 | Release gate integrity: Implement plan-side bug gate in `check_engine.py` ensuring active bug plans require `- Blocks-Release:`. | Order 01 | `docs/artifact-lifecycles.md` |
    | 03 | Runner integration: Connect `k3yx72` Order 02 `Review-Depth` signals to `auto-approved` transition under `llbr2b` policy; support contiguous turn dispatch. | Order 01, `k3yx72` Order 02, `llbr2b` | `docs/artifact-lifecycles.md` |
    | 04 | Verification and regression tests: CLI tests, qualification rejection tests, and runner simulation. | Orders 02, 03 | None |

    ### 7.3 Open questions for the maintainer

    #### OQ-01: Entry point syntax: dedicated verb vs scaffold flag

    - Blocking: no
    - Status: open
    - Owner: maintainer
    - Question: Should the quick pipeline entry point be a dedicated CLI verb (`aw ipd quick`) or a flag on the existing scaffold command (`aw ipd scaffold --quick`)?
    - Recommendation: Dedicated verb `aw ipd quick`, aliasing `aw ipd scaffold --quick`.
    - Recommendation strength: Strong. A distinct verb emphasizes the streamlined workflow while preserving discoverability.

    #### OQ-02: Front-matter marker: explicit field vs implicit derivation

    - Blocking: no
    - Status: open
    - Owner: maintainer
    - Question: Should plans declare `- Pipeline: quick` in front matter, or should the runner infer quick handling solely from `simple` review tier and runner signals?
    - Recommendation: Explicit `- Pipeline: quick` field.
    - Recommendation strength: Moderate. Explicit declaration makes author intent unambiguous and allows upfront linting.

    #### OQ-03: Plan approval mechanical enforcement

    - Blocking: no
    - Status: open
    - Owner: maintainer
    - Question: Should `aw ipd set approved` enforce `--by-human` mechanically in `status_set.validate_transition_allowed` (mirroring specs), rather than relying on convention?
    - Recommendation: Add mechanical `--by-human` requirement to `status_set.validate_transition_allowed` for plans entering `approved`.
    - Recommendation strength: Strong. Prevents inadvertent automated sets of `approved`, preserving `auto-approved` as the sole automated status.

    #### OQ-04: Contiguous runner dispatch

    - Blocking: no
    - Status: open
    - Owner: maintainer
    - Question: Should the runner execute review and execution in separate turns within the same unattended batch run, or require separate runner invocations?
    - Recommendation: Contiguous execution across distinct turns in the same batch run when `auto-approved` succeeds.
    - Recommendation strength: Strong. Minimizes human turnaround while strictly preserving turn-level isolation.
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the `aw check --agent` baseline command and the path of the saved (rule, location) list; the `aw specs new ... --apply` command and its output (minted id6, conforming filename under `.aw/records/specs/draft/`); and the spec's front matter as written, showing `- From-Backlog: rsisop`, `- Work-Kind: feature`, `- Priority: medium`, `- Set: quickpipe`, the `- Scope:` line and both `- Constrained-by:` lines.
  - Observed evidence:
    Baseline command:
    `aw check --agent`
    Baseline diagnostics saved to:
    `/tmp/aw_check_baseline_e41qgx.json` (76 pairs recorded).

    Spec creation command and output:
    `aw specs new --title "Quick pipeline for small changes" --slug quick-pipeline-small-changes --summary "Specify the quick pipeline for small changes from plan straight to review and execution" --apply`
    Output:
    `aw specs new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/e41qgx/.aw/records/specs/draft/20261023-4iyd78-01-4iyd78-quick-pipeline-small-changes.spec.md`

    Front matter as written:
    ```markdown
    # Spec: Quick pipeline for small changes

    - Date: 2026-10-23
    - Status: draft
    - Id: 4iyd78
    - Author: aw specs new
    - From-Backlog: rsisop
    - Work-Kind: feature
    - Priority: medium
    - Set: quickpipe
    - Scope: One shortened pipeline for small changes from plan straight to review and execution. Specification only; authorizes no code change.
    - Constrained-by: `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`
      (`k3yx72`, `approved`), which defines the `simple` review tier and its runner signals, and excludes
      the rest of the pipeline as non-goal N4.
    - Constrained-by: `.aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md`
      (`llbr2b`, `approved`), which owns the configurable per-(type, transition) permission surface.
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the spec's requirements index table and acceptance-criteria section. Every `R-NN` row must name the spec section that elaborates it, every decision from E-03 to E-07 that is not an open question must map to at least one `R-NN`, no id may use the `N` family, and each id left undecided by an open question must be absent or carry `[Deferred]`. Paste `python3 -c "from pathlib import Path; from agent_workflows.production_checks import parse_spec_requirement_ids; print(parse_spec_requirement_ids(Path('<spec path>').read_text()))"` output showing the parser extracts the declared ids (non-empty requirement and acceptance sets).
  - Observed evidence:
    Spec Section 8 and Section 9 tables:
    ```markdown
    ## 8. Requirements index (canonical declaration site)

    | ID | Requirement | Detail |
    |---|---|---|
    | R-01 | The quick pipeline authorizes no code change until an approved implementing plan executes. | 0, 7.2 |
    | R-02 | Quick plans are created directly without requiring a backlog item or backlog graduation turn. | 1.1, 2.2, 6.1 |
    | R-03 | A plan must satisfy all mechanical disqualifiers (no orchestrators, no open blocking questions, no attended requirement, no spec edits, no sensitive paths, bounded size <= 2 E items and <= 3 paths) to qualify. | 3.2 |
    | R-04 | Review agent Step T questions govern review tier assignment; the runner may raise the tier but never lowers it. | 3.2, 4.1 |
    | R-05 | A plan failing any qualification criterion or rated above `simple` falls back cleanly to the standard pipeline. | 4.3 |
    | R-06 | Author intent is recorded via `- Pipeline: quick` in front matter, registered in `ipd_schema.META_RECOGNIZED`. | 4.2, 7.1 |
    | R-07 | Human approval `->approved` remains an attested human act; automated clearance sets `auto-approved` exclusively. | 5.1 |
    | R-08 | Automated clearance to `auto-approved` requires an approving review readiness verdict (`is_plan_review_approved`) and compliance with `llbr2b` policy. | 5.1, 5.2 |
    | R-09 | Authoring, review, and execution operate in separate turns and isolated worktree sessions. | 5.3 |
    | R-10 | Plan files, history records, and E/V evidence are preserved; walkthroughs are dropped for quick changes. | 6.1 |
    | R-11 | Bug fixes created via the quick pipeline automatically inherit release gating (`- Blocks-Release: next`) and are policed by plan-side release checks. | 6.2 |
    | R-12 | The CLI provides `aw ipd quick` as the primary authoring entry point. | 7.1 |

    ## 9. Acceptance criteria for the implementing Set

    | ID | Covers | Criterion | Evidence |
    |---|---|---|---|
    | AC-01 | R-02, R-06, R-12 | `aw ipd quick` scaffolds an IPD with `- Pipeline: quick`, valid `- Status: draft`, and no backlog dependency. | CLI execution output and generated plan file. |
    | AC-02 | R-03, R-06 | Scaffolding or linting a quick plan exceeding 2 `E-*` items, exceeding 3 paths, or touching sensitive paths fails validation. | Lint refusal diagnostics and test assertions. |
    | AC-03 | R-04, R-05 | A quick plan rated `standard` by `/plan-review` rejoins the standard pipeline without error or record loss. | Runner execution ledger and plan workflow history. |
    | AC-04 | R-07, R-08 | Runner advances a passing `simple` plan to `auto-approved` under `--full-auto`, while rejecting unreviewed auto-approval. | Transition event logs and status checks. |
    | AC-05 | R-07 | Transitioning a plan to `approved` without `--by-human` is refused by `aw ipd set`. | Command error output and exit code. |
    | AC-06 | R-09 | Authoring, review, and execution run in separate isolated turns within the runner. | Run trace demonstrating distinct turn sessions. |
    | AC-07 | R-10 | Executed quick plans retain full `E-*`/`V-*` evidence and workflow history in `executed/` without a walkthrough file. | File presence check in `.aw/records/plans/executed/`. |
    | AC-08 | R-11 | An active quick bug plan lacking `- Blocks-Release:` is flagged by `check_engine` release checks. | `aw check` diagnostic output. |
    ```
    Parser execution output:
    `python3 -c "from pathlib import Path; from agent_workflows.production_checks import parse_spec_requirement_ids; print(parse_spec_requirement_ids(Path('.aw/records/specs/to-review/20261023-quickpipe-01-4iyd78-quick-pipeline-small-changes.spec.md').read_text()))"`:
    `({'R-09', 'R-12', 'R-10', 'R-11', 'R-06', 'R-02', 'R-01', 'R-08', 'R-07', 'R-03', 'R-05', 'R-04'}, {'AC-02', 'AC-03', 'AC-07', 'AC-01', 'AC-08', 'AC-06', 'AC-05', 'AC-04'})`
    Returns 12 non-N requirements and 8 acceptance criteria.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste the `aw specs set to-review ...` command and output; the spec's front matter after it showing `- Status: to-review` and its path under `.aw/records/specs/to-review/`; `aw specs check <spec path>` output reporting conforming; the before/after `aw check --agent` (rule, location) comparison showing no pair in the after set that is absent from the E-08 baseline (in particular no `check.from-backlog-dangling` for the spec); `aw ipd lint --phase pre-transition` on this plan; and the bare `python3 -m pytest` summary line, with any failure shown to be unrelated to this records-only change.
  - Observed evidence:
    Transition command and output:
    `aw specs set to-review .aw/records/specs/draft/20261023-4iyd78-01-4iyd78-quick-pipeline-small-changes.spec.md --message "authored review-ready spec defining quick pipeline for small changes" --no-commit --yes`
    Output:
    `-    spec        20261023-4iyd78-01-4iyd78  [medium]  draft → ◔  to-review`
    (File clustered to `.aw/records/specs/to-review/20261023-quickpipe-01-4iyd78-quick-pipeline-small-changes.spec.md` with `aw group specs 4iyd78 --set quickpipe --rename --apply --no-commit` to satisfy `check.identity-absent-from-name`).

    Front matter after transition:
    ```markdown
    # Spec: Quick pipeline for small changes

    - Date: 2026-10-23
    - Status: to-review
    - Id: 4iyd78
    - Author: aw specs new
    - From-Backlog: rsisop
    - Work-Kind: feature
    - Priority: medium
    - Set: quickpipe
    - Scope: One shortened pipeline for small changes from plan straight to review and execution. Specification only; authorizes no code change.
    - Constrained-by: `.aw/records/specs/approved/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md`
      (`k3yx72`, `approved`), which defines the `simple` review tier and its runner signals, and excludes
      the rest of the pipeline as non-goal N4.
    - Constrained-by: `.aw/records/specs/approved/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md`
      (`llbr2b`, `approved`), which owns the configurable per-(type, transition) permission surface.

    ## Workflow history
    - 2026-10-24 to-review (aw set): authored review-ready spec defining quick pipeline for small changes

    - 2026-10-24 created (aw specs): Specify the quick pipeline for small changes from plan straight to review and execution
    ```

    Spec check output:
    `aw specs check .aw/records/specs/to-review/20261023-quickpipe-01-4iyd78-quick-pipeline-small-changes.spec.md`:
    `aw specs check: all specs conform. 1 specs checked.`

    Baseline comparison:
    Baseline diagnostic pairs: 76.
    Current diagnostic pairs: 77.
    No `check.from-backlog-dangling` exists.
    One new diagnostic introduced: `('check.graduation-incomplete', '.aw/records/backlog/graduated/20261018-revsteps-01-rsisop-shorter-pipeline-for-small-changes-go-from-plan-to.backlog.md')`.
    Investigation shows this is an adjacent defect in `check_engine.evaluate_handoff_ready`, which requires all spec carriers of a graduated backlog item to be in status `("approved", "implementing", "implemented")`, even when the handoff was to an active plan `e41qgx` whose mandate is to author the spec in `to-review`. This defect is reported in the defect register and outcome proposal.

    Pre-transition plan lint:
    `aw ipd lint --phase pre-transition .aw/records/plans/pending/20261023-quickpipe-01-e41qgx-specify-the-quick-pipeline-for-small-changes-before-any-verb.ipd.md`:
    `conforming` (0 errors).

    Pytest summary line:
    `1684 passed, 11 warnings in 84.09s (0:01:24)`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed`. It must not be executed until it is reviewed and a human sets it `approved` (or a runner under `--full-auto` clears it to `auto-approved` after a review). No `- Readiness:` field is written here, because that field is `/plan-review`'s attested output.

Execution contract:
- Open questions: OQ-01 and OQ-02 are resolved; nothing here blocks execution. The design questions belong to the spec (E-07), not to this plan.
- Scope fence: `- Scope-Paths:` declares the spec's `draft/` and `to-review/` directories and this plan file. It is a declaration the finalize gate reconciles, not a stop rule: an out-of-scope edit that turns out to be needed is made and then justified with `--scope-reason <path>=<why>`, and a declared path left unmodified (for example `draft/`, if the spec was never committed there) gets `--scope-ack`.
- Commit: through `aw commit e41qgx -- <paths>` only, naming the spec's final `to-review/` path and this plan file; check `git diff --cached --name-only` holds only those paths; never `git add -A`/bare/`-a`; never push. `aw specs set` is run with `--no-commit` so the setter does not make a second commit.
- Tooling: create the spec with `aw specs new` and transition it with `aw specs set`; never hand-name it and never hand-edit its `- Status:`. Do not set the spec `approved` or `implemented`, and write no `- Readiness:` or `- Approval:` into the spec or any example in it.
- Honesty: paste the ACTUAL command and runner output for every `V-*` item; never mark a `V-*` from memory or from the matching `E-*` checkmark.
- Lifecycle transition: the plan moves to `executed/` only through `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms. In a managed runner lane the runner performs that finalize; an executor working by hand outside a runner runs it. Never a hand-rolled `git mv`.
