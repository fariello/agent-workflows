# IPD: Route the runners' action derivation through one public reader over the run-selection action table

- Date: 2026-09-26
- Kind: child
- Concern: THE PACKAGE HAS TWO STATUS-TO-ACTION MAPPINGS AND THEY DISAGREE, which is spec `z7nbn1` 2.2 / requirement 1.2 unmet. `run_selection_policy._ACTION_TABLES` (read only through the PRIVATE `run_selection_policy._action_for`) is the transcription of spec `25kzda` 3.2-3.6, but the runners never consult it: they derive every queue entry's action from `runner_shared.action_for(kind, status)` over `runner_shared.determine_action(status)`, which returns only `review`/`execute`/`orchestrate` and maps EVERY non-review status to `execute`. Measured at HEAD `310ea53e` by calling both: for `executed`, `superseded` and `not-executed` the table says `skip` while `action_for` says `execute` (`orchestrate` for an orchestrator); for `reviewed` the table says `undetermined` while `action_for` says `execute`; for `draft` the table says `undetermined` while `action_for` says `review`. The divergent mapping is read by the queue builder (`runner_shared.initialize_run_core`, two call sites), the dependency preflight's consuming-action map (`runner_shared._consuming_actions_for`), and `--action` legality (`runner_shared.enforce_requested_action`, fed by the same `initialize_run_core` preflight loop).
- Scope: IN: (a) a PUBLIC reader in `run_selection_policy` over `_ACTION_TABLES` (the maintainer's 2026-09-10 ruling recorded in backlog `oc3mhb`: a public reader, not a third copy), plus a runner-side derivation that layers the runner-only inputs (draft completeness, `--full-auto`/`reviewed`, and the orchestrator Kind refinement) ON TOP of the table's answer rather than beside it; (b) re-point `runner_shared.action_for` and `runner_shared.determine_action` through that reader, or remove them with their callers re-pointed (either is acceptable; the choice is recorded at execution); (c) decide and record the `orchestrate` treatment spec `z7nbn1` 2.2 requires; (d) a BEHAVIORAL equality test proving, for every (type, status) row of the table, that the action the RUNNER derives (by building a real queue on both hosts) equals the public reader's answer; (e) amend spec `z7nbn1` acceptance criterion 5.6 to drop its "an AST or grep check" wording, per the maintainer's 2026-09-26 no-structure-tests ruling. OUT: carrying spec/backlog artifacts in the queue (plan `8l8dgb`); refusing a run on `undetermined` (plan `jdn790`); any dispatch of `plan` (plans `aeq7f8`, `y3p3p5`); `render_stream.statusline_action_for_item`, which DISPLAYS an already-derived `item["action"]` and only falls back to a status guess for a hand-written entry lacking one (a display fallback, not a dispatch mapping; see F-6).
- Scope-Paths: agent_workflows/run_selection_policy.py, agent_workflows/runner_shared.py, tests/test_action_table_runner_parity.py, tests/test_run_selection_policy.py, tests/test_oc_runipd.py, tests/test_orchestrator_retirement.py, .aw/records/specs/approved/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: feature
- Priority: medium
- From-Backlog: oc3mhb
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7icz68

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 01 of Set artdispatch; carries From-Backlog oc3mhb per z7nbn1 0.2 so that item closes by handoff). Both mappings measured at HEAD 310ea53e by direct call across all nine IPD statuses and three Kinds; every caller of action_for/determine_action enumerated. Implements 5.6 behaviorally per the maintainer's 2026-09-26 no-structure-tests ruling and carries the one-line 5.6 wording amendment.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `run_selection_policy`'s action table the one answer to "what does a runner do with an artifact of this type in this status", with the runner's own inputs (draft completeness, `--full-auto`, orchestrator Kind) layered on its answer, so the preview, the review sweep, and the queue can no longer disagree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [ ] E-01 RE-MEASURE THE DIVERGENCE at the executing HEAD. (1) Paste, for each IPD status in `draft, to-review, reviewed, approved, auto-approved, reusable, executed, superseded, not-executed` and each Kind in `child, orchestrator, None`, the pair `(runner_shared.action_for(kind, status), run_selection_policy._action_for("ipd", status))`. (2) Grep `action_for(` and `determine_action(` across `agent_workflows/` and `tests/` and paste every CODE call site (not comments) with its enclosing function. At authoring these were: `runner_shared.initialize_run_core` (the `--action` preflight loop and the queue loop), `runner_shared._consuming_actions_for`, `runner_shared.action_for` itself (calls `determine_action`); re-exports in `oc_runipd` and `agy_runipd`; tests in `tests/test_oc_runipd.py`, `tests/test_orchestrator_retirement.py` (including `test_action_decision_shared_code_binding_and_queue_derivation`), and `tests/test_run_selection_policy.py` (the `determine_action(status) == "review"` sweep-parity loop). (3) Grep for any OTHER status-to-action mapping (a literal tuple of statuses mapped to `review`/`execute`) and paste each hit with a one-line classification (dispatch mapping, display fallback, or unrelated).
  - Depends on: none
  - Expected outcome: the disagreeing rows reproduce (`executed`/`superseded`/`not-executed` -> `execute` vs `skip`; `reviewed` -> `execute` vs `undetermined`; `draft` -> `review` vs `undetermined`), and the call-site list is complete.
  - Execution state: pending

### Task group 2: one table, one reader

- [ ] E-02 ADD THE PUBLIC READER `run_selection_policy.action_for_status(spec_type, status) -> str`, returning exactly what `_action_for` returns today (it may simply become `_action_for`'s public name, with `_action_for` kept as an alias so the existing callers and tests do not churn). Normalize `status` with `.strip().lower()` inside the reader (measured: `_action_for("ipd", "EXECUTED")` is `undetermined` today, and one discovered plan, `vfa1tl`, carries `- Status: EXECUTED`). Document at the definition that this is THE status-to-action authority for every type and that no other module may carry a second mapping (spec `z7nbn1` 1.2/5.6).
  - Depends on: E-01
  - Expected outcome: `action_for_status("ipd", "executed") == "skip"`, `action_for_status("ipd", "EXECUTED") == "skip"`, and every existing `tests/test_run_selection_policy.py` case passes unchanged.
  - Execution state: pending

- [ ] E-03 ADD THE RUNNER-SIDE DERIVATION `run_selection_policy.runner_action(spec_type, status, *, kind=None, authoring_complete=None, full_auto=False) -> str` (name may differ; record the chosen name). It CALLS `action_for_status` and refines ONLY the rows the table deliberately leaves `undetermined` because they depend on inputs the table does not see, plus the Kind refinement: (i) `draft` -> `review` when `authoring_complete` is True, `skip` when it is False (spec `25kzda` 3.2 row 1: an incomplete draft is a "Yellow skip", and authoring it unattended is forbidden), and stays `undetermined` when it is None (unreadable, or a type with no completeness parser, which today is every spec: `sweep_review_candidates_for_type`'s comment records that the spec completeness parser "does not exist yet"). THIS IS A BEHAVIOR CHANGE and is stated as one: today `determine_action("draft")` returns `review` for EVERY draft, so a NAMED incomplete draft is handed to `/plan-review` against spec 3.2; after this it is recorded `skip`; (ii) IPD `reviewed` -> `execute` (today's runner behavior, which the queue builder already gates through `item_needs_approval` / `initial_queue_status` so it is frozen `reviewed` and not dispatched unless `--full-auto` cleared it to `auto-approved`); (iii) for `kind == "orchestrator"`, an answer of `execute` becomes `orchestrate` (the E-04 decision). Every other row is returned verbatim from the table, INCLUDING `skip` for `executed`/`superseded`/`not-executed`. Document the three refinements at the definition, each citing its spec row, and state that a refinement never overrides a row the table answers.
  - Depends on: E-02
  - Expected outcome: `runner_action("ipd","executed",kind="child") == "skip"`; `runner_action("ipd","approved",kind="orchestrator") == "orchestrate"`; `runner_action("ipd","to-review",kind="orchestrator") == "review"`; `runner_action("ipd","draft",authoring_complete=True) == "review"`.
  - Execution state: pending

- [ ] E-04 DECIDE AND RECORD THE `orchestrate` TREATMENT (spec `z7nbn1` 2.2 requires the plan to either add it to the table or record why a Kind refinement does not count as a second table). Adopt the refinement (E-03 (iii)), and write the reason into the `runner_action` docstring and this plan's OQ-01 at execution: the table is keyed on (type, status) by spec 1.2's definition, and `orchestrate` is a function of (type, status, Kind) that is `execute` narrowed by one field, so it CONSUMES the table's answer rather than competing with it; adding a Kind column to the table would make every other type carry a dimension only IPDs have. If executing reveals a case where the refinement would contradict a table row (it must not: it only rewrites `execute`), STOP that approach and put `orchestrate` in the table instead, recording why.
  - Depends on: E-03
  - Expected outcome: the decision is written at the definition and in OQ-01; `orchestrate` is only ever produced from a table answer of `execute`.
  - Execution state: pending

### Task group 3: route the runners through it

- [ ] E-05 RE-POINT `runner_shared.action_for` AND `runner_shared.determine_action` THROUGH `run_selection_policy.runner_action` (or remove them and re-point their callers; record which). The `initialize_run_core` queue loop and `--action` preflight loop, and `_consuming_actions_for`, must all obtain their action from the one derivation, passing the authoring-completeness answer for a `draft` (via the existing `runner_shared.plan_authoring_complete`) and the Kind. Preserve the current behavior for EVERY row where the two mappings already agree. For the rows where they disagree, the table now wins: an `executed`/`superseded`/`not-executed` entry is queued with action `skip`. Before relying on that, trace and paste how a `skip` action flows through the consumers that branch on `item["action"]` (`runner_shared.initial_queue_status` already freezes `executed` as `executed` and retired statuses as `reviewed`, so neither is dispatched; `edge_satisfied`/`cascade_dependency_blocked`/`success_states_for_action` branch on `action != "review"`, which reads `skip` as the strict execute bar, the safe direction; `dependency_depth`/`queue_sort_key` read only `orchestrate`). A `skip` ENTRY MUST NEVER BE BORN `queued`, and that is load-bearing rather than tidy: `execute_item_core` computes `is_review = action == "review"` and treats EVERY other action as an execute turn, so a `queued` entry with action `skip` would be EXECUTED. Today only a `draft` can reach that combination (`initial_queue_status("draft")` is `queued`), so freeze a `skip`-action entry whose `initial_queue_status` would be `queued` as `not-run` instead (a canonical terminal status already in `runner_shutdown.KNOWN_ITEM_STATUSES` and `TERMINAL_STATES`, so resume and the ledger coherence check accept it; as a non-success terminal it cascades `fail-depend` to dependents, which is spec 3.2's "skip" outcome for them). Add a guard in `execute_item_core` (both hosts reach it) that raises `DriverError` naming the item if it is ever handed an action outside `review`/`execute` (and `orchestrate` never reaches it; the hosts' `run_queue` route that to `dispatch_orchestrator_item`), so a future path that queues `skip` fails loudly and item-locally instead of executing. Also confirm `runner_shared.expand_dependency_closure`'s skip rule is unaffected (its comment cites `action_for(kind, "executed")` returning `execute`; update that comment to the new truth). Keep the identity property `tests/test_orchestrator_retirement.py` pins (both hosts expose ONE shared object) if the functions are kept.
  - Depends on: E-04
  - Expected outcome: a queue built over an `executed` plan carries `action: skip`; a NAMED incomplete draft carries `action: skip` with queue status `not-run` and no turn; an approved orchestrator still carries `orchestrate`; a to-review plan still `review`; a `reviewed` plan still `execute` with `needs_input` true; `execute_item_core` handed a `skip` item raises `DriverError` before any spawn.
  - Execution state: pending

- [ ] E-06 ADD `tests/test_action_table_runner_parity.py` (BEHAVIORAL ONLY: no `inspect.getsource`, no `read_text` of `agent_workflows/*`, no AST). For EACH (status, kind) row over the IPD table's keys plus `draft` (complete AND incomplete) and `reviewed`, write one synthetic plan into a temp git repo, build a queue on BOTH hosts with `oc_runipd.initialize_run` / `agy_runipd.initialize_run` under `--prepare-only --unattended` with `AW_HOME` isolated (the shape `tests/test_orchestrator_retirement.py`'s queue-derivation case already uses), read the frozen `state.json` queue entry's `action`, and assert it equals `run_selection_policy.runner_action("ipd", status, kind=kind, authoring_complete=...)`, and for every row the table answers (not `undetermined`) also equals `action_for_status("ipd", status)` modulo the documented orchestrator refinement. Include the explicit `executed -> skip` row spec 5.6 names, and a case that hands `oc_runipd.execute_item` a `queued` item with action `skip` with the host spawn patched to fail the test if called, asserting `DriverError` and no spawn. Update the existing tests that asserted the old divergent answers (`tests/test_oc_runipd.py` orchestrator `action_for` cases, `tests/test_orchestrator_retirement.py` binding case, `tests/test_run_selection_policy.py` sweep-parity loop that calls `driver.determine_action`) to the new derivation, changing only the expectation, never weakening a behavior check. If a terminal-status queue build is refused earlier by selection (a NAMED executed plan is admitted, a retired one refused by `expand_selectors`), build the retired rows through a dependent's `executed:` edge or a Set selector exactly as the shipped tests do, and say which in the test docstring.
  - Depends on: E-05
  - Expected outcome: the parity test passes on both hosts; against the pre-change code it FAILS on the `executed`/`superseded`/`not-executed` rows (runner `execute`/`orchestrate`, table `skip`).
  - Execution state: pending

### Task group 4: spec wording

- [ ] E-07 AMEND SPEC `z7nbn1` ACCEPTANCE CRITERION 5.6 (one sentence) so it no longer requires "an AST or grep check": replace "an AST or grep check proves `_ACTION_TABLES` is the only type-plus-status-to-action mapping in the package" with wording that the only mapping is `_ACTION_TABLES`, read through the public reader, as shown by the second mapping's removal or re-pointing plus the behavioral runner-versus-table equality test. Leave every other word of 5.6 intact. Record the amendment with `aw specs note <spec path> --message "5.6 wording amended by artdispatch 7icz68: AST/grep check replaced by behavioral runner-vs-table equality (maintainer ruling 2026-09-26, no structure tests)"`. Do NOT change the spec's `- Status:`.
  - Depends on: E-06
  - Expected outcome: 5.6 reads as a behavioral criterion; the spec history carries the note; `aw specs check` on the file is clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `run_selection_policy` is deliberately a two-import pure module (`selectors`, `status_set`); `render_stream` is imported by neither it nor `runner_shared` at module level for the reverse reason. Keep the new reader pure (no `runner_shared` import).
- `runner_shared.action_for` is documented as "a DISPATCH decision, not a retirement authorization"; `ipd_lifecycle.retire_orchestrator` re-checks eligibility itself. Nothing in this plan changes that.
- `initial_queue_status` freezes `executed` verbatim and every other terminal status as `reviewed`; `item_needs_approval(status, action)` is `action != "review" and status == "reviewed"`. A `skip` action is therefore safe for both.
- Consumers read `item["action"]` by the idiom `action != "review"` (strict) or `== "orchestrate"`; no consumer tests `== "execute"` except `runner_shared` lane-landed parking (`item.get("action") != "execute"` returns early), which a `skip` entry correctly never reaches because it is not dispatched.
- Test policy (maintainer ruling 2026-09-26): behavior tests only, no source-text or AST pins. Suites run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `310ea53e` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.action_for` vs `run_selection_policy._action_for` | Two mappings disagree on five of nine IPD statuses. | direct calls: `executed`/`superseded`/`not-executed` -> `['execute','orchestrate','execute']` vs `skip`; `reviewed` -> `execute` vs `undetermined`; `draft` -> `review` vs `undetermined` |
| F-2 | HIGH | `runner_shared.initialize_run_core` | Queue and `--action` preflight derive from the second mapping. | `action = action_for(kind, status or "approved")`; preflight `action_for(resolve_manifest_kind(plan_info, probe_path), st)` |
| F-3 | MEDIUM | `runner_shared._consuming_actions_for` | Dependency preflight's consuming action comes from the same second mapping. | docstring: "Derived from the SAME `action_for(kind, status)` the queue builder uses" |
| F-4 | INFO | `run_selection_policy._action_for` | Private; read by `classify_paths` and `needs_review` only; tests call it directly. | `grep _action_for(` -> two package call sites; `tests/test_run_selection_policy.py` 4 direct uses |
| F-5 | LOW | `_action_for` | Status is not case-normalized. | `_action_for("ipd","EXECUTED")` -> `undetermined`; `vfa1tl` declares `- Status: EXECUTED` |
| F-6 | INFO | `render_stream.statusline_action_for_item` | A display label reader with a status fallback for entries lacking `action`; not a dispatch decision. | body returns `item["action"]` when present |
| F-8 | MEDIUM | `runner_shared.determine_action` | Every `draft` routes to `review`, complete or not, while spec `25kzda` 3.2 makes an incomplete draft a skip; a queued `skip` would be executed because `execute_item_core` treats every non-`review` action as execute. | `determine_action("draft")` -> `review`; `initial_queue_status("draft")` -> `queued`; `execute_item_core`: `is_review = action == "review"` |
| F-7 | INFO | `expand_dependency_closure` | Its skip-rule comment relies on `action_for(kind,"executed")` returning `execute`. | comment text "`action_for(kind, \"executed\")` returns `\"execute\"`" |

## Proposed changes (ordered, validatable)

1. E-01 re-measures both mappings and every caller.
2. E-02 exposes the public table reader.
3. E-03 adds the runner derivation layered on the reader.
4. E-04 records the `orchestrate` decision.
5. E-05 re-points the runner callers.
6. E-06 adds the behavioral parity test and updates the old expectations.
7. E-07 amends spec 5.6's wording.

## Deferred / out of scope (with reason)

- Carrying spec/backlog entries in the queue and deriving their actions there.
  - Carrier: 8l8dgb
  - Rationale: this plan makes the derivation type-aware by signature; plan `8l8dgb` makes non-plan entries reach it.
- Refusing a run whose selection contains an `undetermined` item.
  - Carrier: jdn790
  - Rationale: freeze-time refusal (spec 1.7/5.1) is that plan's concern; this plan only makes `undetermined` an answer the runner can see.
- `render_stream.statusline_action_for_item`'s status fallback.
  - Carrier-Declined: a display label for a hand-written entry with no `action`; it decides nothing and a queue built by the runner always carries `action`.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/oc_runipd.py` and `agy_runipd.py` re-export `action_for`/`determine_action` by name and need no edit if the names are kept; if E-05 removes them, the re-export lines must go too, and that edit is justified at finalize with `--scope-reason`.
- Scope-Paths justification: `run_selection_policy.py` gains the reader; `runner_shared.py` is re-pointed; the new test file holds E-06; three existing test files change expectations only; the z7nbn1 spec takes E-07's one-sentence amendment.

## Required tests / validation

- `tests/test_action_table_runner_parity.py` (new): one queue build per (status, kind) row on both hosts, asserting runner action equals the table reader; shown failing on the terminal rows before E-05.
- Existing `tests/test_run_selection_policy.py`, `tests/test_oc_runipd.py`, `tests/test_orchestrator_retirement.py` pass with expectations updated only where the old divergent answer was asserted.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- AMENDS spec `z7nbn1` (`.aw/records/specs/approved/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md`, declared in `- Scope-Paths:`), acceptance criterion 5.6 only. WHY: 5.6 as written demands "an AST or grep check proves `_ACTION_TABLES` is the only ... mapping", and the maintainer ruled on 2026-09-26 that no test may pin source text or code structure. The criterion's INTENT (one mapping, and the runner provably agrees with it for every row including `executed -> skip`) is satisfied by removing or re-pointing the second mapping plus E-06's behavioral equality test; only the method words change. Leaving the words would make every later reviewer read 5.6 as unmet, or tempt an implementer to add the forbidden test.
- Spec `25kzda` is not edited: its 3.2 table already says `executed`/`superseded`/`not-executed` are skips, so the runner now matches it.
- No user-facing docs.

## Open questions

### OQ-01: Is the `orchestrate` Kind refinement a second table?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO, from spec `z7nbn1` 1.2's own definition (the table answers "what is the next action for an artifact of this TYPE in this STATUS") and 2.2's explicit allowance. The refinement consumes the table's `execute` answer and narrows it by Kind; it never produces an action for a row the table answers differently. E-04 writes this at the definition and falls back to a table row if execution finds a contradiction.

### OQ-02: How is 5.6's "AST or grep check" satisfied without a structure test?

- Blocking: no
- Status: resolved
- Owner: maintainer (ruled 2026-09-26)
- Resolution or deferral rationale: RULED by the maintainer 2026-09-26: no tests that pin source text or code structure; implement 5.6 BEHAVIORALLY. Satisfied by E-05 (the second mapping is removed or re-pointed through the one reader) plus E-06 (for every row, the runner's queue-built action equals the public reader's), and E-07 amends 5.6's wording to match.

### OQ-03: Does `reviewed -> execute` in the runner derivation reintroduce a second mapping?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO. The table deliberately omits `reviewed` because spec `25kzda` 3.2 dispatches it on `--full-auto`, "a flag this module does not see" (the `_IPD_ACTIONS` comment). Refining an `undetermined` row with that runner-only input is exactly what spec `z7nbn1` 1.7 describes ("`undetermined` AFTER the runner has applied the inputs `run_selection_policy` deliberately does not see"). The queue builder's existing `needs_input` flag keeps an unapproved `reviewed` plan from being dispatched.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the 27-row (status x kind) comparison table from both functions and the enumerated call-site list with enclosing functions, plus the classification of every other status-to-action literal found.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff adding `action_for_status` and the output of `python3 -c "from agent_workflows import run_selection_policy as p; print(p.action_for_status('ipd','executed'), p.action_for_status('ipd','EXECUTED'), p.action_for_status('spec','approved'), p.action_for_status('backlog','open'))"` showing `skip skip plan plan`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `runner_action` diff and a one-line `python3 -c` printing the four expected-outcome values (`skip orchestrate review review`).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the docstring paragraph recording the decision and the resolved OQ-01 text as edited at execution.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of every re-pointed call site, the traced `skip` flow for each consumer named in E-05, and a `--prepare-only --unattended` scratch run's `state.json` queue entry showing `action: skip` for an executed plan and `orchestrate` for an approved orchestrator.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_action_table_runner_parity.py -q` passing with its count; then, with E-05's hunks temporarily reverted, the same command showing the terminal-status rows FAILING; then passing again; plus `python3 -m pytest -o addopts="" tests/test_run_selection_policy.py tests/test_oc_runipd.py tests/test_orchestrator_retirement.py -q` passing, and `grep -n "getsource\|read_text\|ast\." tests/test_action_table_runner_parity.py` showing no source or AST reads of `agent_workflows`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the 5.6 diff (only that criterion changed), the `aw specs note` output, `aw specs check <spec path>` clean, and the bare `python3 -m pytest` summary line BEFORE and AFTER this plan with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The runner stops carrying its own status-to-action rule: `run_selection_policy`'s table, read through a new public reader, becomes the one authority, and the runner's own inputs (draft completeness, `--full-auto`, orchestrator Kind) refine only the rows the table leaves undetermined. Two visible behavior changes. An `executed`/`superseded`/`not-executed` queue entry is now recorded with action `skip` instead of `execute`/`orchestrate`; such entries were already never dispatched, so no run does different work there. And a NAMED INCOMPLETE `draft` is now skipped (`not-run`, no turn) instead of being sent to `/plan-review`, which is what spec `25kzda` 3.2 always required; a complete draft is still reviewed. It also approves a one-sentence amendment to spec `z7nbn1` 5.6 replacing its "AST or grep check" method with the behavioral test, per the maintainer's 2026-09-26 ruling. This is Order 01 of Set `artdispatch`, graduated from spec `z7nbn1`; it carries `- From-Backlog: oc3mhb` so that item closes by handoff, and `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. In `runner_shared.py`, only `action_for`, `determine_action`, `_consuming_actions_for`, the two `initialize_run_core` derivation sites (and the queue-status freeze for a `skip` entry), the `execute_item_core` action guard, and the `expand_dependency_closure` comment. If an edit outside the declared paths proves necessary (for example the host re-export lines if E-05 removes the functions), make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. The new parity test must be shown FAILING against the pre-change runner.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Backlog `oc3mhb` is then closed by the handoff this plan's `From-Backlog` and matching `Blocks-Release` provide; its `graduated` transition is the graduating agent's, not this plan's.
