# IPD: Specify the quick pipeline for small changes before any verb implements it

- Date: 2026-10-23
- Kind: child
- Concern: A 1 to 4 line fix or one new CLI option travels the same pipeline as a large feature: a backlog item is filed (`open`), a runner plan-production turn graduates it (`graduated`), the plan is scaffolded `draft`, advanced to `to-review`, reviewed to `reviewed`, approved (human `approved` or `--full-auto` `auto-approved`), and finally executed. Backlog `rsisop` asks for a shorter path (plan, review, execution) and states that it "Needs its own spec: which changes qualify, who decides, and which records are still written." Spec `k3yx72` already makes the REVIEW cheap for such plans (its `simple` tier) and explicitly leaves the rest of the pipeline out of scope (its non-goal N4, pointing at `rsisop`).
- Scope: Produce the SPEC, not the engine. Measure what the current pipeline costs a small change, inventory which stages are already optional in code, and write one spec (created with `aw specs new`, taken to `to-review`, carrying `- From-Backlog: rsisop`) that answers the item's three questions (which changes qualify, who decides, which records are still written) plus the entry-point, approval-authority and release-gate questions those answers depend on, and proposes the implementing Set's work breakdown. NO verb, runner, schema or workflow behavior changes in this plan.
- Scope-Paths: .aw/records/specs/draft/**, .aw/records/specs/to-review/**, .aw/records/plans/**/20261023-quickpipe-01-e41qgx-specify-the-quick-pipeline-for-small-changes-before-any-verb.ipd.md
- Item-Dependencies: exists:spec:k3yx72, exists:spec:llbr2b
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: rsisop
- From-Spec: none
- Set: quickpipe
- Order: 1
- Highest E allocated: 08
- Author: opencode
- Id: e41qgx

## Workflow history
- 2026-10-23 to-review (opencode): authored review-ready spec-first plan graduating backlog rsisop (the item says it needs its own spec before any code)

- 2026-10-23 draft (opencode): created.

## Goal

Write one reviewed-ready spec that decides how a small change goes from a plan straight to review and execution: which changes qualify, who decides that a change qualifies, what approval it still needs, and which records are still written. Code follows in a separate Set graduated from the approved spec, so no behavior changes before the maintainer has answered the design questions.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: measure and inventory the current pipeline

- [ ] E-01 MEASURE what the current pipeline costs a small change, and record the table in the spec's problem section. Over the executed non-orchestrator plans dated 2026, select the small ones (at most 2 `E-*` items; at authoring time this was 151 plans, of which 21 carry `- From-Backlog:`) and report, per plan and as medians: the number of `## Workflow history` records, the number of distinct lifecycle statuses recorded, and, where the plan carries `- From-Backlog:`, the backlog item's own history record count. Where `aw runs` / `aw runs analyze` can attribute runner turns or cost to those plan id6s, add turns per stage (plan-production, review, execute) and recorded cost; if it cannot, say so in the spec in one sentence instead of estimating. Keep the measuring script (a short `python3 - <<'EOF'` block) verbatim in the spec so the numbers can be re-run.
  - Depends on: none
  - Expected outcome: a measured table in the spec, with the script that produced it, showing how many stages and records a small change carries today.
  - Execution state: pending

- [ ] E-02 INVENTORY, by reading the code and citing by symbol, which pipeline stages are ALREADY optional and which are enforced, and record it as a table in the spec. Cover at least: plan creation without a backlog item (`ipd_authoring.run_scaffold` requires `--priority`/`--work-kind` only when `--from-backlog` is absent; at authoring time 96 of 1,161 non-orchestrator plans dated 2026-09 and 2026-10 carried neither `- From-Backlog:` nor `- From-Spec:`); the scaffold's initial status (`ipd_authoring.build_skeleton` always writes `draft`); forward status skips (`ipd_lifecycle.validate_transition` allows a forward skip except into `executed`, which needs at least `reviewed`); the `- Readiness:` requirement at `reviewed` and at the ready-to-execute tier (`ipd_lint.check_readiness_required`, `IPD-M113`) and the refusal of a hand-written one (`ipd_lint.check_readiness_attestation`, `IPD-M107`); the human approval authority (`attention_contract.TRANSITION_AUTHORITY["->approved"]`); the automated `auto-approved` tier (`ipd_schema.READY_TO_EXECUTE`, `runner_shared.set_plan_approved`, the predicate `plan_readiness.is_plan_review_approved`, and the two `--full-auto` sites in `runner_shared.initialize_run_core` and the post-review path); the queue action table (`run_selection_policy.runner_action`, `runner_shared.item_needs_approval`); and the backlog graduation turn and its verification (`aw backlog set graduated`, the `BACKLOG-GRADUATE-SET` check). For each row record: the stage, what enforces it, whether it can be skipped today, and what skipping it would lose.
  - Depends on: none
  - Expected outcome: an inventory table in the spec whose every row cites a symbol, distinguishing stages that are ceremony from stages that are a safety gate.
  - Execution state: pending

### Task group 2: answer the design questions in the spec

- [ ] E-03 SPECIFY WHICH CHANGES QUALIFY. Start from `k3yx72` Section 5.1 (`simple`: "Very low risk: typically a few lines of code, such as a small bug fix or one new CLI option") and its runner signals in Section 5.2 (a `.spec.md` in `- Scope-Paths:`, the size limits `ipd_schema.MAX_E_LEAVES` / `ipd_schema.MAX_TASK_GROUPS`, a match in `review.sensitive_paths`, or `grandfathered` scope), and state whether the quick path uses exactly those disqualifiers or a stricter limit (for example a cap on `E-*` items or on `- Scope-Paths:` entries), justified by E-01's measurement. State that an orchestrator, a plan with a `Blocking: yes` open question, and a plan carrying `- Attended: required` never qualify, and why. Every criterion must be mechanically checkable or explicitly marked as a judgement with the role that makes it.
  - Depends on: E-01, E-02
  - Expected outcome: a qualification section in the spec listing each criterion, whether it is mechanical or a judgement, and its source.
  - Execution state: pending

- [ ] E-04 SPECIFY WHO DECIDES and what happens on disagreement. The spec must stay consistent with `k3yx72` MD-1 (the review agent rates the tier; the runner only raises it) rather than invent a second rating. Decide between, at least: (a) the author proposes the quick path with a recognized front-matter field and the review's tier check confirms or rejects it; (b) no new field, the quick path is simply the `simple` review tier plus the runner signals; (c) a human flag on the creating command. State the FALLBACK when review rates the plan above `simple` or a runner signal fires: the plan rejoins the normal pipeline with no record lost and no human step invented. If a new field is proposed, name it, its closed value set, and that it must be added to `ipd_schema.META_RECOGNIZED` by the implementing Set, not by this plan.
  - Depends on: E-03
  - Expected outcome: a decision section in the spec naming the deciding role at each step and the fallback, with the recommended option and its strength.
  - Execution state: pending

- [ ] E-05 SPECIFY THE APPROVAL AUTHORITY on the quick path, without weakening the shipped attestation model. The spec must state that `->approved` remains human-only (`attention_contract.TRANSITION_AUTHORITY`), that an automated clear can only be `auto-approved` and only after a review produced `- Readiness:` (`plan_readiness.is_plan_review_approved`), and that D65's rule holds: `auto-approved` is "set only by an automated checker, never by an executor fast-tracking its own work" (`.aw/records/plans/README.md`, `.aw/system/workflows/verify-execution/verify-execution.md`). Decide whether the quick path (a) still stops for human approval, (b) auto-approves only under `--full-auto`, or (c) is a per-transition permission under the lifecycle automation policy of spec `llbr2b`, and state how the choice composes with `llbr2b` (reviewed, not yet implemented) so the two specs do not define overlapping switches. State whether authoring, review and execution may share one host session or must be separate turns, and why.
  - Depends on: E-02, E-04
  - Expected outcome: an approval section in the spec that names the authority for every transition on the quick path and cites the constraint each choice preserves.
  - Execution state: pending

- [ ] E-06 SPECIFY WHICH RECORDS ARE STILL WRITTEN and how gates that today travel through a backlog item still apply. For each record the normal pipeline writes (backlog item and its history, plan file and its `## Workflow history`, `E-*`/`V-*` evidence, review record under `.aw/records/reviews/`, `- Readiness:`, `aw ipd begin` receipt, finalize commit, walkthrough), state kept, dropped, or merged, with the reason. Address the release gate explicitly: today a bug plan scaffolded WITHOUT `--from-backlog` gets no `- Blocks-Release:` (measured: `aw ipd scaffold --work-kind bug` without `--from-backlog` writes none), and `check_engine.check_live_bug_gate` scans backlog items only, so skipping the backlog item would let a live bug escape the "every live bug gates the next release" rule in `AGENTS.md`. The spec must close that hole (for example the quick creating command applies `backlog.decide_gate_default`) or state why it does not apply. Also state how `aw attention` and the runner queue see a quick plan that has no backlog item.
  - Depends on: E-04, E-05
  - Expected outcome: a records table in the spec plus a release-gate section that leaves no path for a live bug to skip the gate.
  - Execution state: pending

- [ ] E-07 SPECIFY THE ENTRY POINT AND THE IMPLEMENTING WORK BREAKDOWN, and carry the maintainer questions. Decide the user-facing entry point (for example a new `aw ipd quick` verb, a flag on `aw ipd scaffold`, a backlog-item field that lets the runner author and execute in one queue item, or a combination), naming for each the existing code it extends (`ipd_authoring.run_scaffold`, the `ipd_sub` parser in `cli.py`, `command_surface.COMMAND_INVENTORY`, `run_selection_policy.runner_action`). Write a work-breakdown table (Order, work, depends on) for the implementing Set, including the dependency on `k3yx72`'s Order 02 (`Review-Depth` field and runner tier signals) where the quick path consumes them, and the documentation each Order must amend (`docs/artifact-lifecycles.md`, `.aw/records/plans/README.md`, the `ipd-structure-and-linting` spec Section 4.4 if a field is added). Record every decision the maintainer must own as an `OQ-NN` (two-digit ids, per `ipd_schema.OQ_HEADING_RE`) with a recommendation and a recommendation strength, and mark `Blocking: yes` only where implementing without the answer would be irreversible. State in the spec that it authorizes no code change by itself.
  - Depends on: E-03, E-04, E-05, E-06
  - Expected outcome: an entry-point section, a work-breakdown table and an open-questions section in the spec.
  - Execution state: pending

### Task group 3: create and validate the spec

- [ ] E-08 CREATE THE SPEC BY TOOL and take it to `to-review`, NOT `approved`. Run `aw specs new --title "Quick pipeline for small changes" --slug quick-pipeline-small-changes --summary "<one line>" --apply` (it mints the id6 and the conforming `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` name), write the content from E-01 to E-07 into it, add `- From-Backlog: rsisop`, `- Work-Kind: feature`, `- Priority: medium` and `- Set: quickpipe`, and add `- Constrained-by:` lines for `k3yx72` and `llbr2b`. Advance it with `aw specs set to-review <path> --message "..."` (never by hand-editing `- Status:`), then run `aw specs check` and `aw check`. Do NOT set the spec `approved` (the maintainer's attested act) and never `implemented`.
  - Depends on: E-07
  - Expected outcome: one conforming spec under `.aw/records/specs/to-review/` carrying `- From-Backlog: rsisop`, and no new `aw check` diagnostic.
  - Execution state: pending

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
| F-2 | Spec `k3yx72` (`reviewed`) defines the `simple` review tier and its runner signals, and excludes this pipeline as non-goal N4, sending it to `rsisop`. It is not yet implemented: no code mentions `Review-Depth` or `review.sensitive_paths`. | `.aw/records/specs/reviewed/20261017-k3yx72-01-k3yx72-plan-review-redesign.spec.md` Sections 2, 5.1, 5.2, 15 |
| F-3 | A plan can already be created without a backlog item; scaffold only needs `--priority` and `--work-kind` then. So the backlog step is mechanically optional today, and the friction is in the remaining stages and in the runner flow, which E-01 and E-02 must measure rather than assume. | `ipd_authoring.run_scaffold`; 96 of 1,161 non-orchestrator plans dated 2026-09/10 carry no `From-Backlog`/`From-Spec` (measured at HEAD `67a066ac3`) |
| F-4 | Small plans are common: 151 executed non-orchestrator plans dated 2026 have at most 2 `E-*` items, and only 21 of them carry `- From-Backlog:`; 150 of the 151 name no spec in `- Scope-Paths:`. | measured at HEAD `67a066ac3` over `.aw/records/plans/executed/2026*.ipd.md` |
| F-5 | Skipping the backlog item drops the release gate for bugs: a bug plan scaffolded without `--from-backlog` carries no `- Blocks-Release:`, and `check_engine.check_live_bug_gate` reads backlog items only. | `aw ipd scaffold --kind child --title x --set probe --order 1 --priority low --work-kind bug --author opencode` (preview) printed no `Blocks-Release` line; `check_engine.check_live_bug_gate` iterates `backlog._iter_items` |
| F-6 | Human approval is a fixed authority, and the automated tier is constrained: `->approved` needs `by_human`; `auto-approved` is written only by `runner_shared.set_plan_approved` after `plan_readiness.is_plan_review_approved`; D65 forbids an executor fast-tracking its own work. | `attention_contract.TRANSITION_AUTHORITY`; `runner_shared.set_plan_approved`; `.aw/records/plans/README.md` "auto-approved" bullet |
| F-7 | A per-transition automation policy is already specified (spec `llbr2b`, `reviewed`), so the quick path's approval rule must compose with it rather than add a parallel switch. | `.aw/records/specs/reviewed/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md` Sections 5, 6, 7 |
| F-8 | The lint refuses a `reviewed` or ready-to-execute plan without `- Readiness:` (`IPD-M113`), and the field may only come from a review (`IPD-M107`), so a quick path cannot skip the review step and still reach execution. | `ipd_lint.check_readiness_required`; `ipd_lint.check_readiness_attestation` |

## Proposed changes (ordered, validatable)

1. Measure the current cost of a small change (E-01).
2. Inventory which stages are ceremony and which are gates, by symbol (E-02).
3. Decide qualification (E-03), the deciding role and fallback (E-04), approval authority (E-05), and records plus release gate (E-06).
4. Decide the entry point, write the implementing work breakdown, and carry the maintainer questions (E-07).
5. Create the spec by tool at `to-review` with `- From-Backlog: rsisop` and validate it (E-08).

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

- [ ] V-01 validates E-01
  - Required evidence: paste the measuring script exactly as it appears in the spec, its actual output when re-run at the execution HEAD, and the spec's table; the table's numbers must equal the output. If `aw runs` could not attribute turns or cost, paste the command tried and its output, and the spec sentence saying so.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the spec's inventory table. For each row, paste a `grep -n` (or `aw` command) output at the execution HEAD showing the cited symbol exists, and include the scaffold preview output proving the `draft` initial status.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the spec's qualification section; each criterion must be labeled mechanical or judgement and cite its source (`k3yx72` section or code symbol), and the orchestrator, `Blocking: yes` and `Attended: required` exclusions must be present.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the spec's decision section, showing the options considered, the recommended option with its recommendation strength, the fallback rule, and a sentence reconciling it with `k3yx72` MD-1.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the spec's approval section, showing every quick-path transition with its authority, the statements that `->approved` stays human-only and that D65 holds, the composition rule with `llbr2b`, and the session-sharing decision with its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the spec's records table (each record kept, dropped or merged, with a reason) and its release-gate section; the section must name `check_engine.check_live_bug_gate` and state the mechanism that keeps a quick bug plan gated, or why none is needed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the spec's entry-point section, its work-breakdown table (with the `k3yx72` Order 02 dependency), its open-questions section (two-digit `OQ-NN` ids, each with recommendation and strength), and the sentence stating the spec authorizes no code change.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the `aw specs new ... --apply` command and output (minted id6, conforming filename); the spec's front matter showing `- Status: to-review`, `- From-Backlog: rsisop` and the `- Constrained-by:` lines; the `aw specs set to-review` command and output; `aw specs check` output reporting conforming; the before/after `aw check --agent` comparison showing no new diagnostic; `aw ipd lint --phase pre-transition` on this plan; and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until it is reviewed and a human sets it `approved` (or a runner under `--full-auto` clears it to `auto-approved` after a review). No `- Readiness:` field is written here, because that field is `/plan-review`'s attested output.

Execution contract: change only the paths in `- Scope-Paths:`; commit through `aw commit e41qgx -- <paths>`, never `git add -A`, never push. Create the spec with `aw specs new` and transition it with `aw specs set`; never hand-name it and never hand-edit its `- Status:`. Do not set the spec `approved` or `implemented`. Paste actual command output for every `V-*` item. The terminal transition is performed by `aw ipd finalize` (or by the runner in a managed lane) after `aw ipd lint --phase pre-transition` conforms.
