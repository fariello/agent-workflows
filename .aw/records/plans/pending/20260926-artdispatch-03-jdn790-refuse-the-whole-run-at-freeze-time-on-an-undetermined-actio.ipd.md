# IPD: Refuse the whole run at freeze time on an undetermined action, a non-conformant artifact, or an unsatisfiable dependency

- Date: 2026-09-26
- Kind: child
- Concern: SPEC `z7nbn1` 1.3, 1.4 AND 1.7 (as ruled 2026-09-26 in OQ-04, "split by when known") REQUIRE A WHOLE-RUN REFUSAL BEFORE ANY SESSION, LEASE OR WORKTREE for three conditions knowable at freeze, and the shipped runner refuses NONE of them as a run. Measured at HEAD `310ea53e`: (1) UNDETERMINED: the queue builder never produces `undetermined` because it derives actions from `runner_shared.action_for`, which has no such answer (plan `7icz68` makes the table's `undetermined` visible to the runner). (2) NON-CONFORMANT: the only pre-dispatch structural gate is `runner_shared.enforce_dependency_preflight`, which is IPD-only and checks the dependency graph, not the artifact's type contract; `25kzda`'s `RUN-STRUCTURE-PREFLIGHT` row (transcribed verbatim in `run_evidence.RUN_FINDING_CODES`) says `FAIL ITEM; ABORT RUN if identity/type is ambiguous`. (3) UNSATISFIABLE DEPENDENCY: an `executed:` edge whose target is neither in the batch nor already executed passes preflight and is discovered at dispatch by `runner_shared.edge_satisfied`, marking that one item `fail-depend` while independent items run. Reproduced on a scratch repo with three approved plans (`abc123`; `efg456` declaring `executed:abc123`; independent `ind789`): `aw oc run start efg456 ind789 --prepare-only --unattended` froze BOTH `efg456` and `ind789` as `queued`/`execute`, so the unrelated `ind789` would run in a batch spec 5.3 says must refuse. The approved contract that authorizes today's behavior, `25kzda` 3.1 gate 1 ("an unmet but valid dependency produces `dependency-not-met` without a host session") and the `RUN-STRUCTURE-PREFLIGHT` row, must be amended in the same change (spec `z7nbn1` 0.2, 5.3b).
- Scope: IN: (a) one freeze-time gate in `runner_shared.initialize_run_core`, sited with the existing pre-queue gates (after the typed queue is built in memory and BEFORE the run directory, any lease, lane or session), that collects EVERY finding across the selection and raises one `DriverError` (exit 2, no durable state, like `enforce_orchestrator_shape_gate`) for: an entry whose derived action is `undetermined` (5.1); an artifact whose type's structural checker reports a finding (5.2); an `executed:` edge whose target is neither in the batch nor satisfied on disk (5.3); (b) the per-item `fail-depend` cascade for an in-batch prerequisite that FAILS during the run is untouched and re-proven (5.3a); (c) amend spec `25kzda` 3.1 gate 1 and 4.2's `RUN-STRUCTURE-PREFLIGHT` row, and the verbatim transcription in `run_evidence.RUN_FINDING_CODES`, to state the freeze-time whole-run refusal (5.3b). OUT: changing satisfaction semantics (spec `z7nbn1` 1.4: "adds a refusal point and changes no satisfaction semantics"; the consuming-action rule of `25kzda` 2.9 decides "could be met"); `--with-dependencies` (it already rebinds the selection before freezing, so an edge it can satisfy is in the batch by the time this gate runs); dispatch-time re-checking, which stays (spec 1.4a).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_evidence.py, tests/test_freeze_time_refusal.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:8l8dgb
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 3
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: jdn790

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 03 of Set artdispatch). The per-item unsatisfiable-edge behavior reproduced at HEAD 310ea53e on a scratch repo (efg456 + ind789 both frozen queued); RUN-STRUCTURE-PREFLIGHT's verbatim transcription in run_evidence located; corpus measured: 0 of 55 actionable plans and 0 of 19 specs and 0 of 620 backlog items fail their structural checker, and 4 live executed: edges point at non-executed targets. Carries the 25kzda amendment required by z7nbn1 0.2/5.3b.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Refuse, as a whole and before anything durable exists, any run whose selection contains something the runner cannot classify, something malformed, or a dependency that provably cannot be met in this run, while keeping the per-item cascade for a prerequisite that fails later.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 REPRODUCE AT THE EXECUTING HEAD on a scratch git repo (`AW_HOME` isolated), with three approved, author-conformant plans `abc123`, `efg456` (`- Item-Dependencies: executed:abc123`), `ind789` (none). Paste the frozen `state.json` queue for `oc run start efg456 ind789 --prepare-only --unattended` and for `abc123 efg456`. Then paste, for the current corpus: the number of selected-able artifacts per type whose structural checker reports a finding (plans: `ipd_lint.lint_file(..., checkpoint="author")` for non-terminal plans; specs: `specs.validate_spec`; backlog: `backlog.validate_item`), and every live `executed:` edge whose target is not executed. At authoring: 0 of 55 actionable plans (47 to-review, 6 draft, 2 approved) non-conforming, 0 of 19 specs, 0 of 620 backlog items; 4 edges (`199u11 -> a6xbso`, `xz59ai -> vtkfq8`, `iyi4hc -> 5xzld0`, `2yqt0a -> wd6npl`).
  - Depends on: none
  - Expected outcome: both runs freeze every item `queued`; the corpus counts are pasted.
  - Execution state: pending

### Task group 2: the gate

- [ ] E-02 ADD `runner_shared.enforce_freeze_time_refusal(queue, *, repo, full_auto)` returning nothing or raising `DriverError` whose message lists EVERY finding, one per line, each naming the artifact id6, its type, its path and its status, and ending with the recovery command; the message states "No work started, and nothing durable was created". Call it from `initialize_run_core` immediately BEFORE `enforce_orchestrator_shape_gate` (both are freeze-time, deterministic, model-free, and precede `run_dir` creation; this ordering keeps the cheapest structural refusal first). It must run for `--prepare-only` too, as the shape gate does. Collect-all, not first-finding.
  - Depends on: E-01
  - Expected outcome: a clean selection passes through unchanged; any finding raises before `run_dir` exists.
  - Execution state: pending

- [ ] E-03 UNDETERMINED (spec 5.1, 1.7). A queue entry whose `action` (from plan `7icz68`'s `runner_action`, which has already applied draft completeness, the `reviewed` refinement and Kind) is `undetermined` is a finding: `[RUN-UNDETERMINED-ACTION] <type> <id6> (<path>) has status <status>, for which no action is defined`, with the recovery naming the status setter for that type. Per 1.7 this fires only AFTER the runner's own inputs: a `reviewed` IPD is not undetermined, and a `draft` IPD with a readable completeness answer is not. State which rows remain undetermined at execution (at authoring, by the tables: spec `draft` (no spec completeness parser), spec `reviewed` without `--action review`, spec `implementing` (its dispatch row stays with `25kzda`, spec `z7nbn1` section 7), and any unknown status on any type).
  - Depends on: E-02
  - Expected outcome: a selection of one `implementing` spec plus one approved plan refuses naming the spec; the plan does not run.
  - Execution state: pending

- [ ] E-04 NON-CONFORMANT (spec 5.2, 1.3). For every queue entry, run its type's structural checker over that one file: IPD -> `ipd_lint.lint_file(path, checkpoint=<the checkpoint its action consumes>)` (`author` for a review action, matching what `/plan-review` requires to start; `pre-execution` for an execute action; terminal skips are not linted, since `executed` plans are legacy-not-evaluated by design, 735 of 735 measured); spec -> `specs.validate_spec(path, text)`; backlog -> `backlog.validate_item(path, text)`. Any error-severity finding is `[RUN-STRUCTURE-PREFLIGHT] <item> violates <finding-code>: <detail>. Repair it, run aw check <type> <selector>, then: aw <host> run <selector>` (the recovery changes from `resume` to a fresh run, because no run exists). An entry whose type cannot be determined at all is also a finding here, not a skip. Measure and paste the added freeze-time cost on a 50-plan selection; if it exceeds 1s warm, cache per-path lint results keyed on content digest within the call and say so.
  - Depends on: E-03
  - Expected outcome: a malformed plan plus a valid plan refuses naming the malformed plan's finding code; neither runs; no run directory or lane worktree exists afterwards.
  - Execution state: pending

- [ ] E-05 PROVABLY UNSATISFIABLE DEPENDENCY (spec 5.3, 1.4). For every entry, for every `executed:<id6>` edge: satisfied at freeze if `edge_satisfied` (the shipped authority, called exactly as `closure_target_admission` already calls it at queue-build time) says so for the entry's consuming action; COULD BE MET if the target is in this batch with an action that can reach the required state in this run (for an execute consumer: target action `execute` or `orchestrate`; for a review consumer: target action `review` or `execute`, or target already `reviewed`/`approved`, per `25kzda` 2.9's review row); otherwise a finding: `[RUN-DEPENDENCY-UNSATISFIABLE] <id6> requires <edge>; <target> is <status> and not in this run. Add it to the selection or run with --with-dependencies, then: aw <host> run <selector>`. `exists:` and `state:` edges are evaluated the same way through `edge_satisfied` (they are judged from repository state and are never in-batch-satisfiable except `state:` targets in the batch, which follow the same rule). Do NOT change `edge_satisfied`, `cascade_dependency_blocked`, or the dispatch-time re-check.
  - Depends on: E-04
  - Expected outcome: `efg456 ind789` refuses naming `executed:abc123`, and `ind789` does not run; `abc123 efg456` proceeds with `abc123` ordered first.
  - Execution state: pending

### Task group 3: the contract

- [ ] E-06 AMEND SPEC `25kzda` in the same change (spec `z7nbn1` 0.2, 5.3b). (1) 3.1 gate 1: replace "An invalid source item fails preflight; an unmet but valid dependency produces `dependency-not-met` without a host session" with the split-by-when-known rule: a dependency provably unsatisfiable at freeze (target neither satisfied on disk nor in the batch able to reach the required state) REFUSES THE WHOLE RUN before any session, lease or worktree; a prerequisite satisfiable at freeze that fails during the run makes its dependents `dependency-not-met` (`fail-depend`) without a host session while independent items continue; cite `z7nbn1` OQ-04. (2) 4.2 `RUN-STRUCTURE-PREFLIGHT` row, Action column: from `FAIL ITEM; ABORT RUN if identity/type is ambiguous` to a terse cell stating the whole run is refused at freeze before any session (keep the cell terse; commentary goes in prose around the table, per the table's own transcription note), and its message template's recovery from `aw <host> run resume <run-id>` to `aw <host> run <selector>`. (3) Update `run_evidence.RUN_FINDING_CODES`' `RUN-STRUCTURE-PREFLIGHT` row to the new verbatim cells, and its `abort`/`abort_classes` so `validate_finding_table` stays clean (a freeze-time refusal is not a mid-run abort; record the chosen encoding and why). (4) Record `aw specs note <25kzda path> --message "Amended by artdispatch jdn790 (z7nbn1 OQ-04/5.3b): freeze-time whole-run refusal for undetermined, non-conformant, and provably unsatisfiable dependencies; in-run failures keep per-item fail-depend"`. Also check 4.3's `IPD-DEP-SATISFIED` row and 5.4 rule 6 ("outside the queue and unsatisfied ... becomes skipped / dependency_not_met") for the same contradiction and amend them in the same way if they state the per-item outcome for a freeze-time-knowable case; paste what was changed and what was judged consistent.
  - Depends on: E-05
  - Expected outcome: `25kzda` states the freeze-time refusal in every place that previously stated the per-item outcome for it; `run_evidence.validate_finding_table()` reports no finding; the spec is `aw specs check` clean.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD `tests/test_freeze_time_refusal.py` (behavioral only; temp git repos; `AW_HOME` isolated; both hosts). Cases, each asserting the refusal text names the artifact AND that no run directory, lane worktree or session was created AND that an unrelated valid plan in the same selection did NOT run: (1) 5.1: an `implementing` spec (or other E-03 undetermined row) plus a valid plan; (2) 5.2: a malformed plan (missing required metadata) plus a valid plan; a malformed backlog item plus a valid plan; (3) 5.3 both ways: `efg456` + `abc123` in the batch runs with `abc123` ordered first (assert the frozen order), and `efg456` + `ind789` refuses naming `executed:abc123`; (4) 5.3a: `abc123`, `efg456`, `ind789` all in the batch, `abc123`'s turn forced to fail (host spawn patched to exit nonzero), then `efg456` ends `fail-depend` and `ind789` runs to completion; (5) the review-consumer relaxation: `efg456` at `to-review` with `abc123` at `to-review` in the batch is admitted (spec 2.9 review row). Update any existing test that asserted an unsatisfiable edge produces per-item `fail-depend` at dispatch for an item that can now never be queued, changing it to assert the freeze-time refusal, and list each one.
  - Depends on: E-06
  - Expected outcome: all pass on both hosts; (1), (2), (3)-refusal FAIL against the pre-change code; (3)-proceed, (4) and (5) pass both before and after.
  - Execution state: pending

- [ ] E-08 RE-RUN E-01's two scratch runs and the bare suite before and after; run `python3 -c "from agent_workflows import run_evidence as r; print(r.validate_finding_table())"`.
  - Depends on: E-07
  - Expected outcome: `efg456 ind789` refuses with no run directory; `abc123 efg456` freezes normally; the finding-table check is clean; the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Freeze-time gates in `initialize_run_core` precede `run_dir` creation and raise `DriverError`/`RunFlagRefusal`, which both hosts' `main` print and exit 2 with no durable state (`RunFlagRefusal` docstring). `enforce_orchestrator_shape_gate` is the collect-all precedent.
- `edge_satisfied` is the single definition of "is this typed edge met?"; `closure_target_admission` already calls it at queue-build time with a synthetic `{"action": "execute"}` item and `{"repo": ...}` state, so calling it before a run exists is established practice.
- `run_evidence.RUN_FINDING_CODES` transcribes 25kzda 4.2's `inspects` and `pass_criterion` cells VERBATIM (the spec's own note: "editing a cell here is a code change"); `validate_finding_table` enforces 12 codes and the abort-class vocabulary.
- 25kzda 4.1: ABORT RUN is reserved for six mid-run integrity classes; a freeze-time refusal is not an abort (nothing is running), which is why E-06 must record how the row encodes it.
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `310ea53e` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | runner, unsatisfiable edge | Per-item, and an unrelated plan in the batch is queued to run. | scratch repo: `oc run start efg456 ind789 --prepare-only --unattended` -> `[('efg456','execute','queued'), ('ind789','execute','queued')]` |
| F-2 | HIGH | `enforce_dependency_preflight` | Static graph errors only; an unmet valid edge passes. | `preflight_dependency_findings(repo, [199u11])` -> `[]` although its target `a6xbso` is `to-review` |
| F-3 | MEDIUM | `run_evidence.RUN_FINDING_CODES` | `RUN-STRUCTURE-PREFLIGHT` action `FAIL ITEM; ABORT RUN if identity/type is ambiguous`, `abort=ABORT_CONDITIONAL`, predicates `ipd_lint.lint_text`, `ipd_lint.lint_file`, `check_engine.check_type`. | row text |
| F-4 | INFO | corpus | Nothing selectable is non-conformant today; four live edges point at non-executed targets. | 55/55 actionable plans author-conforming; 19/19 specs and 620/620 backlog items zero findings; 4 edges listed in E-01 |
| F-5 | INFO | 25kzda | Per-item wording appears in 3.1 gate 1 and 4.2; 4.3 `IPD-DEP-SATISFIED` and 5.4 rule 6 describe the dependent outcome and must be checked for consistency. | spec text |

## Proposed changes (ordered, validatable)

1. E-01 reproduces and measures the corpus.
2. E-02 adds the collect-all freeze-time gate.
3. E-03 refuses undetermined actions.
4. E-04 refuses non-conformant artifacts.
5. E-05 refuses provably unsatisfiable dependencies.
6. E-06 amends 25kzda and its code transcription.
7. E-07 adds behavioral tests for 5.1, 5.2, 5.3, 5.3a.
8. E-08 re-probes and runs the suite.

## Deferred / out of scope (with reason)

- Changing how `fail-depend` items are re-evaluated when a prerequisite later succeeds in the same run.
  - Carrier-Declined: owned historically by backlog `nueip1` (now `done`), and spec `z7nbn1` 1.4a requires this plan to keep the in-run cascade exactly as it is; this plan adds a freeze-time refusal point only.
- Deciding "could be met" for a target whose in-batch action is itself refused at freeze.
  - Carrier-Declined: the gate is collect-all, so such a target's own finding is reported in the same refusal; the run never starts, so there is no partial state to reason about.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/ipd_lint.py`, `specs.py`, `backlog.py`, `check_engine.py` are called, not changed. `agy_runipd.py`/`oc_runipd.py` need no edit because the gate lives in the shared `initialize_run_core`; if a host needs a label, it is passed through the existing `labels`.
- Scope-Paths justification: `runner_shared.py` holds the gate; `run_evidence.py` holds the verbatim row; the new test file holds E-07; two existing test files may carry per-item assertions E-07 converts; the 25kzda spec takes E-06.

## Required tests / validation

- `tests/test_freeze_time_refusal.py` (new): 5.1, 5.2, 5.3 both ways, 5.3a, and the review-consumer relaxation, on both hosts; the refusal cases shown failing before the change.
- `run_evidence.validate_finding_table()` clean.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- AMENDS spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`, declared in `- Scope-Paths:` so both runners announce the edit). WHY: spec `z7nbn1` 0.2 and acceptance criterion 5.3b REQUIRE it: `z7nbn1`'s freeze-time whole-run refusal (OQ-04, maintainer ruling 2026-09-26) is STRICTER than `25kzda` 3.1 gate 1 and the `RUN-STRUCTURE-PREFLIGHT` row, which fail only the offending item, and shipping the stricter behavior while the approved contract still describes the looser one would leave every later runner plan reviewed against a false contract. `z7nbn1` 0.2 calls this "IRREVERSIBLE-IN-PRACTICE"; the amendment is confined to the cells and sentences that state the per-item outcome for a freeze-time-knowable condition, and 1.4a's in-run cascade is restated, not weakened.
- `z7nbn1` itself is not edited here.
- No user-facing docs.

## Open questions

### OQ-01: Does a freeze-time finding refuse the whole run or only the item?

- Blocking: no
- Status: resolved
- Owner: maintainer (ruled 2026-09-26)
- Resolution or deferral rationale: RULED by the maintainer 2026-09-26 at spec review (spec `z7nbn1` OQ-04): SPLIT BY WHEN KNOWN. Undetermined action, non-conformant artifact, and a dependency provably unsatisfiable in this run refuse the WHOLE run before any session; an in-batch prerequisite that fails during the run keeps today's per-item `fail-depend`. This plan implements exactly that and carries the matching `25kzda` amendment.

### OQ-02: Which lint checkpoint applies to a selected plan?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: the checkpoint its ACTION consumes, from repository evidence: `/plan-review` preflights `aw ipd lint --phase author` (`.aw/system/workflows/plan-review/plan-review.md`), and `ipd_lifecycle` lints `pre-execution` before executing (`ipd_lifecycle`'s `lint_file(plan_path, checkpoint="pre-execution")`). Using a stricter checkpoint for a review would refuse plans the review exists to fix; using `author` for an execute would admit a plan the lifecycle then refuses mid-run.

### OQ-03: Is the gate's cost acceptable on large selections?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: measured bound at authoring: linting all 55 actionable plans plus 19 specs plus 620 backlog items ran within the same interactive pass (plan discovery alone is about 1.46s and dominates); E-04 measures the gate's own increment and caches by content digest if it exceeds 1s warm.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both frozen queues and the corpus counts per type plus the live unsatisfied-edge list.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the gate diff and its call site in `initialize_run_core`, showing it precedes `enforce_orchestrator_shape_gate` and `run_dir` creation.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the scratch-run refusal text for an undetermined spec plus a valid plan, and `ls .aw/records/runs` (or the state root) showing no new run directory.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the refusal text for a malformed plan plus a valid plan, the absence of any run directory and lane worktree (`git worktree list`), and the measured added cost on a 50-plan selection.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `efg456 ind789` refusal and the `abc123 efg456` frozen queue with order.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the 25kzda diff (3.1 gate 1, the 4.2 row, and any 4.3/5.4 change or the stated reason each was consistent), the `RUN_FINDING_CODES` row diff, `validate_finding_table()` output, the `aw specs note` output, and `aw specs check <25kzda path>` clean.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_freeze_time_refusal.py -q` passing with count; with E-02..E-05 reverted, the refusal cases FAILING and the proceed/5.3a/review cases passing; passing again after restoring; and the list of converted existing tests.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the two post-change scratch runs and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A run now refuses as a whole, before creating anything, when its selection contains an item the runner cannot classify, a malformed artifact, or a dependency that cannot be met in this run (target neither executed nor in the batch). An unrelated valid plan in such a selection no longer runs. A prerequisite that was satisfiable when the run started and fails partway through keeps today's behavior: its dependents are marked `fail-depend` and everything else continues. This AMENDS approved spec `25kzda` (3.1 gate 1 and the `RUN-STRUCTURE-PREFLIGHT` row, with its code transcription), which spec `z7nbn1` 0.2 requires and calls irreversible in practice; the amendment is the reviewed contract every runner plan is checked against. Order 03 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `8l8dgb` so the gate sees typed spec and backlog entries.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New refusal tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).
