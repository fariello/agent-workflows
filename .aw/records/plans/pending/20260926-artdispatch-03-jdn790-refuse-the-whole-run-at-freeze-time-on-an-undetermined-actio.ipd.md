# IPD: Refuse the whole run at freeze time on an undetermined action, a non-conformant artifact, or an unsatisfiable dependency

- Date: 2026-09-26
- Kind: child
- Concern: SPEC `z7nbn1` 1.3, 1.4 AND 1.7 (as ruled 2026-09-26 in OQ-04, "split by when known") REQUIRE A WHOLE-RUN REFUSAL BEFORE ANY SESSION, LEASE OR WORKTREE for three conditions knowable at freeze, and the shipped runner refuses NONE of them as a run. Measured at HEAD `310ea53e`: (1) UNDETERMINED: the queue builder never produces `undetermined` because it derives actions from `runner_shared.action_for`, which has no such answer (plan `7icz68` makes the table's `undetermined` visible to the runner). (2) NON-CONFORMANT: the only pre-dispatch structural gate is `runner_shared.enforce_dependency_preflight`, which is IPD-only and checks the dependency graph, not the artifact's type contract; `25kzda`'s `RUN-STRUCTURE-PREFLIGHT` row (transcribed verbatim in `run_evidence.RUN_FINDING_CODES`) says `FAIL ITEM; ABORT RUN if identity/type is ambiguous`. (3) UNSATISFIABLE DEPENDENCY: an `executed:` edge whose target is neither in the batch nor already executed passes preflight and is discovered at dispatch by `runner_shared.edge_satisfied`, marking that one item `fail-depend` while independent items run. Reproduced on a scratch repo with three approved plans (`abc123`; `efg456` declaring `executed:abc123`; independent `ind789`): `aw oc run start efg456 ind789 --prepare-only --unattended` froze BOTH `efg456` and `ind789` as `queued`/`execute`, so the unrelated `ind789` would run in a batch spec 5.3 says must refuse. The approved contract that authorizes today's behavior, `25kzda` 3.1 gate 1 ("an unmet but valid dependency produces `dependency-not-met` without a host session") and the `RUN-STRUCTURE-PREFLIGHT` row, must be amended in the same change (spec `z7nbn1` 0.2, 5.3b).
- Scope: IN: (a) one freeze-time gate in `runner_shared.initialize_run_core`, sited with the existing pre-queue gates (after the typed queue is built in memory and BEFORE the run directory, any lease, lane or session), that collects EVERY finding across the selection and raises one `DriverError` (exit 2, no durable state, like `enforce_orchestrator_shape_gate`) for: an entry whose derived action is `undetermined` (5.1); an artifact whose type's structural checker reports a finding (5.2); an `executed:` edge that is unsatisfied on disk AND that this run provably cannot satisfy, judged over the FROZEN QUEUE (target present, frozen `queued` rather than awaiting approval, and able to reach `executed` in this run) rather than over the manifest, per E-05 (5.3); (b) the per-item `fail-depend` cascade for an in-batch prerequisite that FAILS during the run is untouched and re-proven (5.3a); (c) amend spec `25kzda` 3.1 gate 1 and 4.2's `RUN-STRUCTURE-PREFLIGHT` row, and the verbatim transcription in `run_evidence.RUN_FINDING_CODES`, to state the freeze-time whole-run refusal (5.3b). OUT: changing satisfaction semantics (spec `z7nbn1` 1.4: "adds a refusal point and changes no satisfaction semantics"; the consuming-action rule of `25kzda` 2.9 decides "could be met"); `--with-dependencies` (it already rebinds the selection before freezing, so an edge it can satisfy is in the batch by the time this gate runs); dispatch-time re-checking, which stays (spec 1.4a); and any change to how a `fail-depend` cascade re-evaluates.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_evidence.py, agent_workflows/run_selection_policy.py, tests/test_freeze_time_refusal.py, tests/test_runner_shared.py, tests/test_oc_runipd.py, tests/test_run_selection_policy.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:8l8dgb
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 3
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: jdn790

## Workflow history

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-011 all FIXED; review record `.aw/records/reviews/20260926-artdispatch-03-jdn790-refuse-the-whole-run-at-freeze-time-on-an-undetermined-actio.review.md`. Re-verified F-1..F-5 at lane HEAD bdbb4025: every seam reproduced, and F-4's counts CORRECTED (44 actionable plans not 55, with a different status split; 634 backlog items not 620; NINE live unsatisfied edges not four). ADDED two HIGH findings IN E-05's OWN could-be-met predicate, measured on the real 44-plan `aw oc run all` selection and cutting in OPPOSITE directions: it would REFUSE three legitimate in-batch edges whose target is `to-review` (F-6, all three inside this plan's own Set, so `aw oc run all` would refuse today) and ADMIT three that provably cannot be met because the target is frozen `reviewed`/needs-input and never dispatched (F-7, one of them this plan's own edge on 8l8dgb). E-05 now specifies the predicate over the FROZEN QUEUE with a recorded `--full-auto` decision. Also fixed an unimplementable severity criterion (F-8: spec/backlog validators return `severity=''` and no rule is registered, so `== "error"` would never fire), an orphaned shipped disposition code (F-9), a cost budget straddling its own threshold (F-10, re-measured 0.54-1.36s warm over 44 plans), and a stale terminal-lint count stated as a bar (F-11). Split the four over-dense items into six new ones (E-01..E-10) and rebuilt the V checklist to a 10-item bijection. `aw ipd lint --phase review-finalize` conforming, 0 findings.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 03 of Set artdispatch). The per-item unsatisfiable-edge behavior reproduced at HEAD 310ea53e on a scratch repo (efg456 + ind789 both frozen queued); RUN-STRUCTURE-PREFLIGHT's verbatim transcription in run_evidence located; corpus measured: 0 of 55 actionable plans and 0 of 19 specs and 0 of 620 backlog items fail their structural checker, and 4 live executed: edges point at non-executed targets. Carries the 25kzda amendment required by z7nbn1 0.2/5.3b.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Refuse, as a whole and before anything durable exists, any run whose selection contains something the runner cannot classify, something malformed, or a dependency that provably cannot be met in this run, while keeping the per-item cascade for a prerequisite that fails later.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: reproduce

- [ ] E-01 REPRODUCE AT THE EXECUTING HEAD on a scratch git repo (`AW_HOME` isolated), with three approved, author-conformant plans `abc123`, `efg456` (`- Item-Dependencies: executed:abc123`), `ind789` (none). Paste the frozen `state.json` queue for `oc run start efg456 ind789 --prepare-only --unattended` and for `abc123 efg456`. Then paste, for the current corpus: the number of selectable artifacts per type whose structural checker reports a finding (plans: `ipd_lint.lint_file(..., checkpoint="author")` for non-terminal plans, AND `checkpoint="pre-execution"` for the approved ones, since E-04 uses the action's own checkpoint and a plan can conform at one and not the other), specs `specs.validate_spec`, backlog `backlog.validate_item`.

  THEN BUILD E-05's TEST MATERIAL, which is the part of this item the rest of the plan depends on: every LIVE unsatisfied `executed:` edge in the `aw oc run all` selection, and for each one a row giving the dependent, the edge, whether the target is in the selection, the target's status, its derived action, its FROZEN QUEUE STATUS (`initial_queue_status`), and its needs-input flag (`item_needs_approval`). Those last two are what F-7 showed the authored predicate ignored. EVERY NUMBER HERE IS A LIVE POPULATION AND NONE IS A BAR; the authored counts were re-measured at review and three of four were stale, so re-derive rather than confirm. At review: 44 actionable plans (18 to-review, 13 reviewed, 13 approved), 0 non-conforming at `author` and 0 of 13 non-conforming at `pre-execution`, 0 of 19 specs, 0 of 634 backlog items, and NINE unsatisfied edges, of which three have a `review`-action in-batch target (`2ptgds`, `aeq7f8`, `y3p3p5`) and three have an `execute`-action target frozen `reviewed`/needs-input (`199u11`, `jdn790`, `iyi4hc`).
  - Depends on: none
  - Expected outcome: both runs freeze every item `queued`; the per-type conformance counts are pasted for both checkpoints; the unsatisfied-edge table is pasted with the frozen queue status and needs-input flag per target, since E-05's predicate is validated against it.
  - Execution state: pending

### Task group 2: the gate

- [ ] E-02 ADD `runner_shared.enforce_freeze_time_refusal(queue, *, repo, full_auto)` returning nothing or raising `DriverError` whose message lists EVERY finding, one per line, each naming the artifact id6, its type, its path and its status, and ending with the recovery command; the message states "No work started, and nothing durable was created". Call it from `initialize_run_core` immediately BEFORE `enforce_orchestrator_shape_gate` (both are freeze-time, deterministic, model-free, and precede `run_dir` creation; this ordering keeps the cheapest structural refusal first). It must run for `--prepare-only` too, as the shape gate does. Collect-all, not first-finding.
  - Depends on: E-01
  - Expected outcome: a clean selection passes through unchanged; any finding raises before `run_dir` exists.
  - Execution state: pending

- [ ] E-03 UNDETERMINED (spec 5.1, 1.7). A queue entry whose `action` (from plan `7icz68`'s `runner_action`, which has already applied draft completeness, the `reviewed` refinement and Kind) is `undetermined` is a finding: `[RUN-UNDETERMINED-ACTION] <type> <id6> (<path>) has status <status>, for which no action is defined`, with the recovery naming the status setter for that type. Per 1.7 this fires only AFTER the runner's own inputs: a `reviewed` IPD is not undetermined, and a `draft` IPD with a readable completeness answer is not. State which rows remain undetermined at execution. Re-measured at review from the shipped tables: the IPD rows `draft` and `reviewed` are `undetermined` in the TABLE but are both refined away by `runner_action`, so neither should reach this finding; the rows that genuinely remain are spec `draft` (no spec completeness parser exists), spec `reviewed`, spec `implementing` (its dispatch row stays with `25kzda`, spec `z7nbn1` section 7), and any unknown status on any type. FIVE SPECS IN THE LIVE CORPUS WOULD HIT THIS IF SELECTED (`pqsx96` and `i4gpto` draft, `c4gd2h` and `z7nbn1` implementing, `4sd62s` reviewed), and one of them is the very spec this plan graduated from, so the test fixture has a real analogue and the item is reachable rather than theoretical.
  - Depends on: E-02
  - Expected outcome: a selection of one `implementing` spec plus one approved plan refuses naming the spec; the plan does not run; a `reviewed` IPD and a complete `draft` IPD in a selection do NOT produce this finding, proving the refinement is consulted before the table.
  - Execution state: pending

- [ ] E-04 NON-CONFORMANT (spec 5.2, 1.3). For every queue entry, run its type's structural checker over that one file: IPD -> `ipd_lint.lint_file(path, checkpoint=<the checkpoint its action consumes>)` (`author` for a review action, matching what `/plan-review` requires to start; `pre-execution` for an execute action; a terminal entry is not linted, since a plan in a terminal directory returns `legacy/not evaluated` BY DESIGN, which `ipd_lint.lint_file`'s own terminal-directory branch does before any check runs, re-measured at review as 751 of 751 in `executed/` and stated as a PROPERTY rather than a count, since the population grows daily).

  THE SEVERITY CRITERION MUST BE `severity != "info"`, NOT "any error-severity finding", and this is a correctness requirement rather than wording (F-8). A raw `specs.validate_spec` / `backlog.validate_item` finding is an `artifact_core.Drift` whose `severity` field is the EMPTY STRING, because severity is stamped later by `check_engine.enrich_drift`; and NONE of the `attention.*` or `backlog.*` rules those validators emit is registered in `check_engine.RULE_REGISTRY`, so every one of them would reach `_DEFAULT_RULESPEC` and come back `error`. So a literal `severity == "error"` test NEVER FIRES for a spec or backlog artifact (the gate would silently pass every malformed one), while enriching first makes every such rule blocking including any the repository treats as advisory. Use the shipped convention instead, which `artifact_core.drift_exit_code` already documents and implements: everything except `info` fails, and "A legacy 3-field `Drift` carries an empty `severity` and is therefore still treated as failing". For the IPD side the equivalent is `ipd_lint`'s own disposition: refuse on `error`, and do NOT refuse on `legacy`, `quarantined`, or an advisory-only result. Paste, for one synthetic malformed artifact of EACH of the three types, the finding the gate saw and the severity it read.

  The finding message is `[RUN-STRUCTURE-PREFLIGHT] <item> violates <finding-code>: <detail>. Repair it, run aw check <type> <selector>, then: aw <host> run <selector>` (the recovery changes from `resume` to a fresh run, because no run exists). An entry whose type cannot be determined at all is also a finding here, not a skip.

  ASSUME THE CACHE BRANCH IS TAKEN. Measured at review over the REAL 44-plan `all` selection, three consecutive warm passes cost 1.358s, 0.540s and 0.550s (about 18.5ms per plan), extrapolating to about 0.93s for the 50-plan selection this item names: the cost straddles the 1s threshold and the run-to-run variance exceeds the distance to it (F-10). So do not treat "if it exceeds 1s warm" as a live coin flip. Implement the per-path content-digest cache within the call, measure, and paste the before/after numbers for a 50-plan selection; if the measurement genuinely comes in far below 1s on the executing machine, say so and record that the cache was still added (or deliberately not) with the numbers supporting it.
  - Depends on: E-03
  - Expected outcome: a malformed plan plus a valid plan refuses naming the malformed plan's finding code; a malformed SPEC and a malformed BACKLOG item each also refuse, proving the severity criterion actually fires for those two types; neither the valid plan nor anything else runs; no run directory or lane worktree exists afterwards; the 50-plan cost is pasted.
  - Execution state: pending

- [ ] E-05 PROVABLY UNSATISFIABLE DEPENDENCY (spec 5.3, 1.4). For every entry, for every edge: satisfied at freeze if `edge_satisfied` (the shipped authority, called exactly as `closure_target_admission` already calls it at queue-build time) says so for the entry's consuming action; otherwise COULD IT BE MET IN THIS RUN. Findings take the form `[RUN-DEPENDENCY-UNSATISFIABLE] <id6> requires <edge>; <target> is <status> and <why this run cannot change that>. Add it to the selection or run with --with-dependencies, then: aw <host> run <selector>`. `exists:` and `state:` edges are evaluated through `edge_satisfied` (they are judged from repository state and are never in-batch-satisfiable except `state:` targets in the batch, which follow the same rule). Do NOT change `edge_satisfied`, `cascade_dependency_blocked`, or the dispatch-time re-check.

  THE "COULD BE MET" PREDICATE IS THE WHOLE RISK OF THIS PLAN AND THE AUTHORED VERSION WAS WRONG IN BOTH DIRECTIONS, measured at review on the real 44-plan `aw oc run all` selection (F-6, F-7). It is therefore specified here rather than left to the executor, and it must be DERIVED FROM THE FROZEN QUEUE, not from the manifest, because the queue is what records the run's actual intent for each item.

  For an EXECUTE consumer, the edge could be met only if the target is in this batch AND the run will actually dispatch it to completion. Three conditions, all necessary:
  (i) the target is in the frozen queue;
  (ii) the target's frozen queue status is `queued`, i.e. it will be dispatched at all. A target frozen in a TERMINAL status never spends a turn, so an edge on it can never be met. This is the F-7 case and it is live three times: `initial_queue_status("reviewed")` is `reviewed`, which is in both hosts' `TERMINAL_STATES`, and `item_needs_approval("reviewed","execute")` is True, so `199u11 -> executed:a6xbso`, this plan's own `jdn790 -> executed:8l8dgb`, and `iyi4hc -> executed:5xzld0` would all be ADMITTED by the authored rule and then silently fail per-item anyway. Read the queue entry's `status` and its `NEEDS_INPUT_KEY` flag, both already frozen by the queue builder;
  (iii) the target's action can REACH `executed`, judged over the whole run and not from the frozen action alone. A frozen action of `execute` or `orchestrate` qualifies. A frozen action of `review` ALSO qualifies when the run can advance that item from review to execution in the same run, which spec `25kzda` 3.1 explicitly permits ("a complete draft IPD may be reviewed and, under `--full-auto`, truthfully marked `auto-approved` and executed in the same run"). This is the F-6 case and it is live three times INSIDE THIS PLAN'S OWN SET (`2ptgds -> executed:jdn790`, `aeq7f8 -> executed:2ptgds`, `y3p3p5 -> executed:aeq7f8`), so the authored rule would refuse `aw oc run all` on this repository today.

  RESOLVE (iii) EXPLICITLY AND RECORD WHICH WAY, because the two answers are both defensible and the choice is visible in behavior. Either (A) treat a `review`-action in-batch target as SATISFIABLE only under `--full-auto` (the flag is already in scope: the gate takes `full_auto`), refusing otherwise and naming the flag in the recovery, or (B) treat it as satisfiable whenever it is queued, on the ground that the dispatcher re-checks the edge per item and a review-then-approve chain is a legitimate authoring pattern. PREFER (A): it is the honest reading of "provably unsatisfiable in THIS run", it keeps the refusal's claim true, and (B) would admit a chain that genuinely cannot complete without human approval mid-run. Whichever is chosen, paste the resulting finding set over the live corpus for BOTH `--full-auto` settings, and if (A) is chosen, state plainly in the gate section that `aw oc run all` without `--full-auto` now refuses while three such edges are live, since that is a behavior change a human must accept knowingly.

  RE-DERIVE THE LIVE FINDING SET AT EXECUTION AND MAKE IT A GATE ON THE DESIGN, not a footnote: the predicate is correct only if, over the real corpus, every edge it refuses is one no run could meet and every edge it admits is one some run could. The nine live unsatisfied edges (F-4) are the test material; at review the authored predicate scored 3 wrong refusals and 3 wrong admissions out of 9.
  - Depends on: E-04
  - Expected outcome: `efg456 ind789` refuses naming `executed:abc123`, and `ind789` does not run; `abc123 efg456` proceeds with `abc123` ordered first; over the live corpus, an in-batch target frozen `reviewed`/needs-input is REFUSED (F-7's three edges) and a `review`-action in-batch target is handled per the recorded (A)/(B) decision with the full finding set pasted for both `--full-auto` settings.
  - Execution state: pending

### Task group 3: the contract

- [ ] E-06 AMEND SPEC `25kzda` in the same change (spec `z7nbn1` 0.2, 5.3b). (1) 3.1 gate 1: replace "An invalid source item fails preflight; an unmet but valid dependency produces `dependency-not-met` without a host session" with the split-by-when-known rule: a dependency provably unsatisfiable at freeze (target neither satisfied on disk nor in the batch able to reach the required state) REFUSES THE WHOLE RUN before any session, lease or worktree; a prerequisite satisfiable at freeze that fails during the run makes its dependents `dependency-not-met` (`fail-depend`) without a host session while independent items continue; cite `z7nbn1` OQ-04. (2) 4.2 `RUN-STRUCTURE-PREFLIGHT` row, Action column: from `FAIL ITEM; ABORT RUN if identity/type is ambiguous` to a terse cell stating the whole run is refused at freeze before any session (keep the cell terse; commentary goes in prose around the table, per the table's own transcription note), and its message template's recovery from `aw <host> run resume <run-id>` to `aw <host> run <selector>`. (3) Update `run_evidence.RUN_FINDING_CODES`' `RUN-STRUCTURE-PREFLIGHT` row to the new verbatim cells, and its `abort`/`abort_classes` so `validate_finding_table` stays clean (a freeze-time refusal is not a mid-run abort; record the chosen encoding and why). (4) Record `aw specs note <25kzda path> --message "Amended by artdispatch jdn790 (z7nbn1 OQ-04/5.3b): freeze-time whole-run refusal for undetermined, non-conformant, and provably unsatisfiable dependencies; in-run failures keep per-item fail-depend"`. Also check 4.3's `IPD-DEP-SATISFIED` row and 5.4 rule 6 ("outside the queue and unsatisfied ... becomes skipped / dependency_not_met") for the same contradiction and amend them in the same way if they state the per-item outcome for a freeze-time-knowable case; paste what was changed and what was judged consistent.
  - Depends on: E-05
  - Expected outcome: `25kzda` states the freeze-time refusal in every place that previously stated the per-item outcome for it; `run_evidence.validate_finding_table()` reports no finding; the spec is `aw specs check` clean.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-07 ADD `tests/test_freeze_time_refusal.py` WITH THE THREE REFUSAL-CLASS CASES AND THE TWO PRESERVED-BEHAVIOR CASES (behavioral only; temp git repos; both hosts; `AW_HOME` needs no per-test handling, since the root `conftest.py` already re-points it at a session sandbox via an autouse fixture, so do not add a second mechanism). Each refusal case asserts the refusal text names the artifact AND that no run directory, lane worktree or session was created AND that an unrelated valid plan in the same selection did NOT run: (1) 5.1: an `implementing` spec (or other E-03 undetermined row) plus a valid plan; (2) 5.2: a malformed plan plus a valid plan, a malformed SPEC plus a valid plan, and a malformed BACKLOG item plus a valid plan, the last two being what prove E-04's severity criterion fires at all for those types (F-8); (3) 5.3: `efg456` + `ind789` refuses naming `executed:abc123`. The two preserved-behavior cases, which must pass BOTH before and after and are what stop this plan over-refusing: (4) 5.3a: `abc123`, `efg456`, `ind789` all in the batch, `abc123`'s turn forced to fail (host spawn patched to exit nonzero), then `efg456` ends `fail-depend` and `ind789` runs to completion; (5) `efg456` + `abc123` in the batch PROCEEDS with `abc123` ordered first (assert the frozen order).
  - Depends on: E-06
  - Expected outcome: all pass on both hosts; (1), (2) and (3) FAIL against the pre-change code; (4) and (5) pass both before and after.
  - Execution state: pending

- [ ] E-08 ADD THE THREE PREDICATE-BOUNDARY CASES that pin E-05's "could be met" rule in both directions, since F-6 and F-7 measured the authored rule wrong in each: (a) an in-batch execute-action target frozen in a TERMINAL queue status (target `- Status: reviewed`, so `initial_queue_status` is `reviewed` and needs-input is set) is REFUSED at freeze, because it will never be dispatched; (b) the same selection with `--full-auto`, where that target is promoted to `auto-approved` and frozen `queued`, is ADMITTED, which proves the predicate reads the promotion rather than the raw status; (c) an in-batch `to-review` target of an `executed:` edge behaves per E-05's recorded (A)/(B) decision, with the test asserting that decision explicitly and its docstring naming the live corpus edges that motivated it (`2ptgds -> executed:jdn790` and its two siblings). Also assert the spec 2.9 review-consumer relaxation is untouched: `efg456` at `to-review` consuming `executed:abc123` with `abc123` at `to-review` in the batch is admitted.
  - Depends on: E-07
  - Expected outcome: (a) refuses and (b) admits from the SAME fixture differing only in `--full-auto`; (c) matches the recorded decision; the review-consumer case is admitted; (a) and (b) both FAIL against a build carrying E-05's authored action-only predicate.
  - Execution state: pending

- [ ] E-09 RECONCILE THE ORPHANED DISPOSITION CODE AND ITS TEST (F-9). `run_selection_policy.SKIP_DEPENDENCY_NOT_MET_EXTERNAL` (`dependency_not_met_external`) exists for "a dependency omitted from the queue and currently unsatisfied", and `item_disposition` selects it by matching `"not in this run"` in `edge_satisfied`'s reason text. After E-05 an item carrying such an edge can never be queued, so both the code and the `tests/test_run_selection_policy.py` row that asserts it ("a dependency on an OUT-OF-QUEUE target, reason supplied in the map") describe an outcome no run can reach. Decide and RECORD which: keep the code reachable because a dispatch-time re-check can still produce it for an edge that became unsatisfiable AFTER freeze (spec 1.4a keeps that re-check, so this is the likely answer and should be stated with the path that reaches it), or mark it unreachable and say what now covers the case. Do NOT simply delete the test row: if the code stays, the row stays; if it goes, say what replaced it. Enumerate every other test asserting a per-item `fail-depend` for a condition now refused at freeze, and convert only those, listing each one by node id.
  - Depends on: E-08
  - Expected outcome: the disposition code's reachability is decided and recorded with the path that reaches it or the reason nothing does; the converted test list names each node id; no test is deleted without a stated replacement.
  - Execution state: pending

- [ ] E-10 RE-RUN E-01's two scratch runs and the bare suite before and after; run `python3 -c "from agent_workflows import run_evidence as r; print(r.validate_finding_table())"`; and re-derive the live unsatisfied-edge finding set for both `--full-auto` settings, confirming every refusal is one no run could meet and every admission is one some run could.
  - Depends on: E-09
  - Expected outcome: `efg456 ind789` refuses with no run directory; `abc123 efg456` freezes normally; the finding-table check is clean; the live finding set is correct in both directions for both flag settings; the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Freeze-time gates in `initialize_run_core` precede `run_dir` creation and raise `DriverError`/`RunFlagRefusal`, which both hosts' `main` print and exit 2 with no durable state (`RunFlagRefusal` docstring). `enforce_orchestrator_shape_gate` is the collect-all precedent.
- `edge_satisfied` is the single definition of "is this typed edge met?"; `closure_target_admission` already calls it at queue-build time with a synthetic `{"action": "execute"}` item and `{"repo": ...}` state, so calling it before a run exists is established practice.
- `run_evidence.RUN_FINDING_CODES` transcribes 25kzda 4.2's `inspects` and `pass_criterion` cells VERBATIM (the spec's own note: "editing a cell here is a code change"); `validate_finding_table` enforces 12 codes and the abort-class vocabulary.
- 25kzda 4.1: ABORT RUN is reserved for six mid-run integrity classes; a freeze-time refusal is not an abort (nothing is running), which is why E-06 must record how the row encodes it.
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-5 are the author's, measured at HEAD `310ea53e` (2026-09-26); every one was re-verified at lane HEAD `bdbb4025` by `/plan-review` and reproduced, with F-4's counts CORRECTED (PR-006) because three of its four numbers were stale. F-6 through F-11 were ADDED by `/plan-review` on 2026-09-26.

THE TWO HIGH FINDINGS ARE BOTH IN E-05's OWN RULE, and they cut in OPPOSITE directions on the SAME corpus, which is why neither is a detail: as authored the rule REFUSES three live edges it should admit (F-6) and ADMITS three it should refuse (F-7). Measured on `aw oc run all` at this HEAD, a 44-plan selection: the whole run would refuse today.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | runner, unsatisfiable edge | Per-item, and an unrelated plan in the batch is queued to run. | scratch repo: `oc run start efg456 ind789 --prepare-only --unattended` -> `[('efg456','execute','queued'), ('ind789','execute','queued')]` |
| F-2 | HIGH | `enforce_dependency_preflight` | Static graph errors only; an unmet valid edge passes. | re-verified on a scratch repo: `preflight_dependency_findings(repo, [<efg456 path>])` -> `[]` although `efg456` declares `executed:abc123` and `abc123` is `approved` in `pending/` |
| F-3 | MEDIUM | `run_evidence.RUN_FINDING_CODES` | `RUN-STRUCTURE-PREFLIGHT` action `FAIL ITEM; ABORT RUN if identity/type is ambiguous`, `abort=ABORT_CONDITIONAL`, predicates `ipd_lint.lint_text`, `ipd_lint.lint_file`, `check_engine.check_type`. | row text, re-read verbatim |
| F-4 | INFO | corpus | Nothing selectable is non-conformant today; the unsatisfied-edge population is LIVE and was 9, not 4. CORRECTED AT REVIEW: three of the four authored numbers are stale, and one is a bar the plan must not carry. | re-measured: 44 actionable (sweepable) plans, not 55, split 18 to-review / 13 reviewed / 13 approved, not "47 to-review, 6 draft, 2 approved"; 0 of 44 non-conforming at `author` and 0 of 13 approved non-conforming at `pre-execution`; 19 of 19 specs and 634 of 634 backlog items zero findings (634, not 620); NINE live unsatisfied `executed:` edges, not four |
| F-5 | INFO | 25kzda | Per-item wording appears in 3.1 gate 1 and 4.2; 4.3 `IPD-DEP-SATISFIED` and 5.4 rule 6 describe the dependent outcome and must be checked for consistency. | spec text: 3.1 gate 1 reads "an unmet but valid dependency produces `dependency-not-met` without a host session"; 5.4 rule 6 reads "or is outside the queue and unsatisfied, the direct dependent becomes `skipped` / `dependency_not_met` without a session" |
| F-6 | HIGH | E-05's "COULD BE MET" rule as authored | IT REFUSES A LEGITIMATE IN-BATCH EDGE, and on THIS repository it would refuse `aw oc run all` outright. The rule requires an execute consumer's in-batch target to have action `execute` or `orchestrate`, but a `to-review` target's action is `review`, and a Set authored as a review-then-execute chain legitimately declares `executed:<sibling>` on a sibling that is still `to-review`. THREE SUCH EDGES ARE LIVE, all inside this plan's own Set: `2ptgds -> executed:jdn790`, `aeq7f8 -> executed:2ptgds`, `y3p3p5 -> executed:aeq7f8`. So the plan's own Set is the counterexample. The deeper error is a category confusion: "could the target reach `executed` in THIS run" is not answerable from the target's FROZEN action alone, because a run can legally advance an item through review then execution (spec `25kzda` 3.1: "a complete draft IPD may be reviewed and, under `--full-auto`, truthfully marked `auto-approved` and executed in the same run"). | direct call over the real corpus: `expand_selectors(m,["all"])` -> 44 plans; applying E-05's authored predicate yields 3 findings (`2ptgds`, `aeq7f8`, `y3p3p5`), each because the in-batch target's `action_for` is `review`; `EXECUTION_SUCCESS_STATES == ['executed']`, so a review turn alone genuinely cannot satisfy the edge either |
| F-7 | HIGH | E-05's "COULD BE MET" rule as authored | IT ADMITS AN EDGE THAT PROVABLY CANNOT BE MET, which is the exact failure the plan exists to prevent, so the rule as written is not merely too strict but also too lax. An in-batch target whose action IS `execute` can still be frozen in a TERMINAL queue status and never dispatched: `initial_queue_status("reviewed")` is `reviewed`, which is in both hosts' `TERMINAL_STATES`, and `item_needs_approval("reviewed","execute")` is True, so the item is frozen awaiting approval and spends no turn. Three such edges are live: `199u11 -> executed:a6xbso`, `jdn790 -> executed:8l8dgb` (this plan's OWN edge), `iyi4hc -> executed:5xzld0`, each target `reviewed`. The rule must consult the target's FROZEN QUEUE STATUS and the `--full-auto` promotion, not its action alone. Note the promotion genuinely changes the answer, which is why it must be read rather than assumed: with `--full-auto` all three become satisfiable and the admission is correct. | direct call: for `a6xbso`/`8l8dgb`/`5xzld0`, `action_for(...,'reviewed')` -> `execute` but `initial_queue_status('reviewed')` -> `'reviewed'` and `item_needs_approval('reviewed','execute')` -> True; `'reviewed' in oc_runipd.TERMINAL_STATES` -> True. Re-running the same predicate with `full_auto=True` yields 0 such edges, because `initialize_run_core` promotes a `reviewed` plan to `auto-approved` only under that flag |
| F-8 | MEDIUM | E-04's "any error-severity finding" criterion | THE CRITERION IS UNIMPLEMENTABLE AS WRITTEN for specs and backlog, and reading it literally would make the gate never fire for those two types. `specs.validate_spec` and `backlog.validate_item` return `artifact_core.Drift` records whose `severity` field is the EMPTY STRING: severity is stamped later by `check_engine.enrich_drift`, which every one of those rules reaches only through the `_DEFAULT_RULESPEC` because NONE of them is in `RULE_REGISTRY`. So either the gate tests `severity == "error"` and never fires, or it enriches first and then every spec/backlog rule is an error by default, including ones the repository treats as advisory elsewhere. `drift_exit_code`'s own documented convention is the third answer and the right one: everything except `info` fails. | direct call on synthetic malformed files: `specs.validate_spec` -> `attention.missing-status`, `attention.history-missing`, both `severity=''`; `backlog.validate_item` -> six rules, all `severity=''`; `check_engine.rule_spec(<any of them>).severity` -> `'error'` via `_DEFAULT_RULESPEC` with `registered=False`; `artifact_core.drift_exit_code` docstring: "an `info`-severity finding is ADVISORY ... A legacy 3-field `Drift` carries an empty `severity` and is therefore still treated as failing" |
| F-9 | MEDIUM | `run_selection_policy.SKIP_DEPENDENCY_NOT_MET_EXTERNAL` and its shipped test | THE PLAN MAKES A SHIPPED DISPOSITION CODE UNREACHABLE AND DOES NOT SAY SO. `dependency_not_met_external` exists precisely for "a dependency omitted from the queue and currently unsatisfied", and `item_disposition` selects it by matching the substring `"not in this run"` in `edge_satisfied`'s reason. After E-05 that item can never be queued, so the code becomes dead and its table-driven test case asserts behavior no run can produce. The plan's "Deferred / out of scope" declines to touch the cascade, which is right, but this is a different surface it silently orphans. | `grep -n dependency_not_met_external agent_workflows/` -> `run_selection_policy` only (definition, spec comment, and the `"not in this run" in named` selector); `tests/test_run_selection_policy.py` carries the row "a dependency on an OUT-OF-QUEUE target, reason supplied in the map" asserting that code from exactly that reason text |
| F-10 | MEDIUM | E-04's cost budget | THE GATE'S COST LANDS ON ITS OWN THRESHOLD, so "if it exceeds 1s warm, cache" is a coin flip rather than a decision, and the caching branch must be treated as taken. Measured over the REAL 44-plan `all` selection: three consecutive warm passes of `ipd_lint.lint_file(..., checkpoint="author")` took 1.358s, 0.540s, 0.550s (about 18.5ms per plan), which extrapolates to about 0.93s for the 50-plan selection E-04 names. The variance across identical warm runs is larger than the distance to the threshold. | `time.perf_counter()` around `for p in paths: ipd_lint.lint_file(p, checkpoint="author")` over the 44 paths `expand_selectors(m,["all"])` resolves |
| F-11 | LOW | E-04's terminal-skip justification | The count is stale and is stated as a bar: "735 of 735 measured". Re-measured, `executed/` holds 751 plans and all 751 lint `legacy/not evaluated` at `author`. The CONCLUSION is unchanged and is the point worth keeping; the census is a live population. | `Counter(ipd_lint.lint_file(p, checkpoint="author").disposition for p in Path(".aw/records/plans/executed").rglob("*.ipd.md"))` -> `{'legacy/not evaluated': 751}` |

## Proposed changes (ordered, validatable)

1. E-01 reproduces, measures the corpus, and builds E-05's test material.
2. E-02 adds the collect-all freeze-time gate.
3. E-03 refuses undetermined actions.
4. E-04 refuses non-conformant artifacts, on the `severity != "info"` criterion.
5. E-05 refuses provably unsatisfiable dependencies, with the could-be-met predicate specified.
6. E-06 amends 25kzda and its code transcription.
7. E-07 adds the three refusal-class tests and the two preserved-behavior tests.
8. E-08 adds the three predicate-boundary tests.
9. E-09 reconciles the orphaned disposition code and converts the affected tests.
10. E-10 re-probes, re-derives the live finding set both ways, and runs the suite.

## Deferred / out of scope (with reason)

- Changing how `fail-depend` items are re-evaluated when a prerequisite later succeeds in the same run.
  - Carrier-Declined: owned historically by backlog `nueip1` (now `done`), and spec `z7nbn1` 1.4a requires this plan to keep the in-run cascade exactly as it is; this plan adds a freeze-time refusal point only.
- Deciding "could be met" for a target whose in-batch action is itself refused at freeze.
  - Carrier-Declined: the gate is collect-all, so such a target's own finding is reported in the same refusal; the run never starts, so there is no partial state to reason about.

## Scope check

- Over-scope: none.
- Under-scope: `agent_workflows/ipd_lint.py`, `specs.py`, `backlog.py`, `check_engine.py` are called, not changed. `agy_runipd.py`/`oc_runipd.py` need no edit because the gate lives in the shared `initialize_run_core`; if a host needs a label, it is passed through the existing `labels`. ADDED AT REVIEW: `agent_workflows/run_selection_policy.py` and `tests/test_run_selection_policy.py` are now DECLARED, because E-09 reconciles `SKIP_DEPENDENCY_NOT_MET_EXTERNAL` and the table row that asserts it (F-9); if E-09 concludes the code stays reachable through the dispatch-time re-check and needs no edit, both paths are declared-but-unmodified and take a `--scope-ack` each at finalize, which is the honest outcome rather than an undeclared surprise edit.
- Scope-Paths justification: `runner_shared.py` holds the gate; `run_evidence.py` holds the verbatim row; the new test file holds E-07 and E-08; `run_selection_policy.py` and its test hold the orphaned disposition code E-09 reconciles; two existing test files may carry per-item assertions E-09 converts; the 25kzda spec takes E-06.

## Required tests / validation

- `tests/test_freeze_time_refusal.py` (new): the three refusal classes 5.1/5.2/5.3 including a malformed SPEC and a malformed BACKLOG item (E-07), the two preserved-behavior cases 5.3a and the in-batch proceed case (E-07), and the three predicate-boundary cases plus the review-consumer relaxation (E-08); refusal cases shown failing before the change, and the two predicate-boundary cases shown failing against E-05's authored action-only predicate.
- The orphaned `dependency_not_met_external` disposition reconciled and every converted per-item test listed by node id (E-09).
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
- Resolution or deferral rationale: the checkpoint its ACTION consumes, from repository evidence: `/plan-review` preflights `aw ipd lint --phase author` (`.aw/system/workflows/plan-review/plan-review.md`), and `ipd_lifecycle` lints `pre-execution` before executing (`ipd_lifecycle`'s `lint_file(plan_path, checkpoint="pre-execution")`). Using a stricter checkpoint for a review would refuse plans the review exists to fix; using `author` for an execute would admit a plan the lifecycle then refuses mid-run. CONFIRMED AT REVIEW that this distinction is not academic: the live corpus was linted at BOTH checkpoints and is currently clean at each (0 of 44 at `author`, 0 of 13 approved at `pre-execution`), so no plan is admitted at one and refused at the other today, but the two checkpoints do differ (`_REVIEW_ESCALATION_CHECKPOINTS` includes `pre-execution` and not `author`), so E-01 now measures both rather than only `author`.

### OQ-03: Is the gate's cost acceptable on large selections?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: YES, but the authored answer rested on a wrong figure and a threshold the cost straddles, so it is restated with the review's measurement. The authored claim (55 plans plus 19 specs plus 620 backlog items lint "within the same interactive pass", with plan discovery's 1.46s dominating) conflated the cost of linting the CORPUS with the cost of linting the SELECTION, and the gate only ever lints the selection. Re-measured at review over the real 44-plan `aw oc run all` selection: three consecutive warm passes of `ipd_lint.lint_file(..., checkpoint="author")` cost 1.358s, 0.540s and 0.550s, about 18.5ms per plan, extrapolating to roughly 0.93s for 50 plans. That is ACCEPTABLE for a gate that prevents a whole wasted run, but it sits ON E-04's own 1s threshold with run-to-run variance larger than the distance to it, so E-04 no longer treats the caching branch as conditional (F-10). Specs and backlog items are far cheaper (634 backlog items validate in well under the plan cost).

### OQ-04: Does a `review`-action in-batch target make an `executed:` edge satisfiable in this run?

- Blocking: no
- Status: resolved
- Owner: this plan's author, with the decision RECORDED at execution per E-05
- Resolution or deferral rationale: RAISED AT REVIEW (F-6), because the authored E-05 answered it implicitly and answered it wrongly, and the counterexample is this plan's own Set. Spec `25kzda` 3.1 permits a run to review and then execute the same item ("a complete draft IPD may be reviewed and, under `--full-auto`, truthfully marked `auto-approved` and executed in the same run"), so a frozen action of `review` does NOT prove the target cannot reach `executed`. But without `--full-auto` the chain stops at human approval, so it equally does not prove it can. The answer is therefore CONDITIONAL ON `--full-auto`, and E-05 requires the implementer to record which of the two readings it took, with the live finding set pasted for both flag settings. Recommended reading (A): satisfiable only under `--full-auto`, because that keeps the refusal's own claim ("provably unsatisfiable in THIS run") true. This is non-blocking because both readings are defensible and the evidence needed to choose is in the repository, not with the human; what would make it blocking is shipping either reading without recording it, which E-05 and E-08 now prevent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both frozen queues; the per-type conformance counts at BOTH the `author` and `pre-execution` checkpoints; and the live unsatisfied-edge TABLE with, per row, the dependent, the edge, whether the target is in the selection, its status, its derived action, its `initial_queue_status`, and its `item_needs_approval` flag.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the gate diff and its call site in `initialize_run_core`, showing it precedes `enforce_orchestrator_shape_gate` and `run_dir` creation.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the scratch-run refusal text for an undetermined spec plus a valid plan, `ls` of the state root showing no new run directory, and the evidence that a `reviewed` IPD and a complete `draft` IPD in a selection produce NO undetermined finding (the refinement is consulted before the table).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the refusal text for a malformed plan, a malformed SPEC and a malformed BACKLOG item each beside a valid plan; the severity value the gate actually read for each of the three (proving the `severity != "info"` criterion fires rather than an `== "error"` test that never would); the absence of any run directory and lane worktree (`git worktree list`); and the measured 50-plan cost before and after the content-digest cache.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the could-be-met predicate's diff; the `efg456 ind789` refusal and the `abc123 efg456` frozen queue with order; the RECORDED (A)/(B) decision for a `review`-action in-batch target with its rationale; and the FULL live finding set over the real corpus for BOTH `--full-auto` settings, with a line per edge stating whether it is refused or admitted and why that is correct.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the 25kzda diff (3.1 gate 1, the 4.2 row, and any 4.3/5.4 change or the stated reason each was consistent), the `RUN_FINDING_CODES` row diff, `validate_finding_table()` output, the `aw specs note` output, and `aw specs check <25kzda path>` clean.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_freeze_time_refusal.py -q` passing with count; with E-02..E-05 reverted, the three refusal cases FAILING (including the malformed spec and malformed backlog cases) and the 5.3a and in-batch-proceed cases still passing; passing again after restoring.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the three predicate-boundary cases passing, the (a)/(b) pair showing the SAME fixture refused without `--full-auto` and admitted with it, case (c) matching the recorded decision, the review-consumer relaxation admitted, and the FAILING output of (a) and (b) against a build carrying E-05's authored action-only predicate.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the recorded reachability decision for `dependency_not_met_external` with the code path that reaches it (or the reason nothing does), the disposition of the `tests/test_run_selection_policy.py` out-of-queue row, and the list of every converted per-item test by node id with the assertion each now makes.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the two post-change scratch runs, `validate_finding_table()` output, the re-derived live finding set for both `--full-auto` settings, and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A run now refuses as a whole, before creating anything, when its selection contains an item the runner cannot classify, a malformed artifact, or a dependency that cannot be met in this run. An unrelated valid plan in such a selection no longer runs. A prerequisite that was satisfiable when the run started and fails partway through keeps today's behavior: its dependents are marked `fail-depend` and everything else continues. This AMENDS approved spec `25kzda` (3.1 gate 1 and the `RUN-STRUCTURE-PREFLIGHT` row, with its code transcription), which spec `z7nbn1` 0.2 requires and calls irreversible in practice; the amendment is the reviewed contract every runner plan is checked against.

THE ONE THING TO WEIGH IS HOW OFTEN THIS WILL REFUSE, because the gate turns a partial run into no run, and the review measured that it bites on this repository TODAY. Nine `executed:` edges in the current 44-plan `aw oc run all` selection are unsatisfied at freeze. Three have a target that is in the batch but frozen awaiting human approval (`- Status: reviewed`), so they genuinely cannot be met and the gate correctly refuses them, including this plan's own edge on `8l8dgb`; under `--full-auto` those same three become satisfiable and are admitted. Three more declare `executed:` on a sibling that is still `to-review`, which is a legitimate review-then-execute chain inside this very Set, and whether those refuse depends on a decision the plan now requires the implementer to make and record (E-05's (A)/(B), recommended (A): satisfiable only under `--full-auto`). Under the recommended reading, `aw oc run all` WITHOUT `--full-auto` refuses while those three edges are live, and the operator's remedy is to name a narrower selection, pass `--full-auto`, or pass `--with-dependencies`. That is the intended trade (a refusal naming the edge beats a run that silently does part of the work), but it is a visible behavior change on the everyday command and is stated here so it is accepted knowingly rather than discovered.

Order 03 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `8l8dgb` so the gate sees typed spec and backlog entries.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New refusal tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).
