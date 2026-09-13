# IPD: Extract the run viewer artifact audit into one shared module and consume it from doctor

- Date: 2026-09-08
- Kind: child
- Concern: THE ARTIFACT LOCATION-AND-STATUS AUDIT LIVES ONLY IN THE RUN VIEWER, SO THE DIAGNOSIS TOOL A HUMAN REACHES FOR CANNOT SEE IT. Verified at HEAD: `find_artifact_file` (`run_viewer.py:439`) and `audit_step_artifact` (`:465`) are defined in `run_viewer.py` and consumed ONLY there (three call sites, `:489`, `:1463`, `:2554`/`:2558`) plus its own tests. Measured: `grep audit_step_artifact\|find_artifact_file` over `doctor.py`, `check_engine.py` and `cli.py` returns ZERO. So `aw runs` can tell you a step's artifact is in the wrong directory or carries the wrong status, and `aw doctor` cannot.
  THE DUPLICATION RISK IS NOT HYPOTHETICAL IN THIS REPOSITORY, which is why the item asks for extraction rather than for a second implementation. `render_stream` exists because the two host drivers had re-forked the same rendering helpers, and `tests/test_runner_refork_guard.py` now pins 28 (runner, symbol) pairs against exactly that. The same pattern produced `evaluate_review_finding_escalation`, whose docstring states that `aw check` and `aw ipd lint` "both call THIS function, so the sweep and the checkpoint gate cannot drift apart". An audit predicate that answers "is this artifact where its status says it should be" is precisely the kind of judgement that must have ONE implementation.
  TWO DEFECTS IN THE CURRENT IMPLEMENTATION MAKE A LIFT-AND-SHIFT WRONG. CORRECTED IN REVIEW: the FIRST defect as originally stated was FACTUALLY WRONG, and the real defect in its place is different and larger.
  WHAT WAS WRONG: the plan claimed an archived plan "may already be invisible to the audit" because the hardcoded list names a nonexistent `.aw/records/plans/archive` and cannot track sharding. MEASURED AT REVIEW HEAD `b644a7c3` AND FALSIFIED. `plans_archive.py:4` states the shards are `YYYYMM/` created INSIDE each terminal dir (`executed/`, `superseded/`, `not-executed/`), and those five terminal dirs ARE in the hardcoded list, and the loop uses `rglob("*.md")`, which recurses into a shard. Constructed the case directly: a plan at `executed/202608/20260801-setx-01-abc123-thing.ipd.md` IS FOUND by today's code. The shards are also MONTHLY (`artifact_core.shard_for_date` returns `cleaned[:6]`), not weekly as the plan twice says. So the nonexistent `archive/` entry is dead weight in a list, not a blind spot.
  THE REAL DEFECT ONE IS THE TYPE SET, NOT THE SHARD MATH: the hardcoded list covers plans and specs ONLY. Measured: a `backlog` artifact carrying the queried id6 returns `None` (invisible), while a spec in a SUBDIRECTORY is found (so recursion works). Since the run viewer's steps today are plans, this is latent rather than live for `aw runs`, but it is exactly the defect a SECOND consumer would meet, and it is the honest reason to stop hardcoding.
  SECOND, it matches with `id6 in p.name` and returns the FIRST hit, so it has no collision policy at all, while `selectors.resolve` treats an id6 matching several files as "a data bug to fix, not overridable by --force" because `MATCH_ID6` is in `UNIQUE_KINDS`. VERIFIED: `resolve` returns BOTH paths for a duplicated id6, so the collision is visible to a caller rather than silently collapsed. A shared module that inherited a first-match-wins reader would spread that weakness to `doctor`.
  SO THE SHARED MODULE MUST CONSUME THE EXISTING RESOLVER RATHER THAN THE EXISTING SEARCH LOOP. `selectors` already enumerates every record type through one traversal (`_iter_paths`, `:397`), already handles the dual `.aw/`/`.agents/` roots, already recurses shards, and already has a documented collision verdict. The extraction's value is one audit predicate; its risk is carrying a private filesystem walk into a second consumer.
  THE ITEM'S "account for active/live runner states" CLAUSE IS LOAD-BEARING AND IS THE MAIN REASON DOCTOR CANNOT SIMPLY CALL THIS TODAY. `audit_step_artifact` maps a step status onto an expected directory (`executed`/`complete` -> `executed/`, `superseded` -> `superseded/`, else `pending/`), and a step that is RUNNING legitimately has its plan in `pending/` while its status is neither terminal nor pending. `run_viewer`'s tests already cover a live case (`a1_live`, `tests/test_run_viewer.py:1407-1421`; re-located by symbol, the plan's `:1285` had drifted). A doctor-side consumer that ignored liveness would report every in-flight run as a discrepancy, which is the fastest way to make a new diagnostic ignored.
  AND HERE IS THE PART THE PLAN DID NOT MEASURE, WHICH DECIDES WHETHER E-04 IS BUILDABLE AS WRITTEN. Liveness is NOT something the audit computes and not something a caller can supply from tracked state: `StepSummary.is_live` is an INPUT FIELD (`run_viewer.py:97`), set by `load_run_summary` from `inspect_run_pid_and_runtime(run_dir, ...)`, i.e. from a RUN DIRECTORY's PID and lock holder (`run_viewer.py:1090-1096`, `:930` `is_live=(holder != HOLDER_NONE)`). The audit merely PASSES IT THROUGH (`:510`, `:559`). So "make it liveness-aware" in `aw doctor` means giving `aw doctor` a reader of `.aw/records/runs/`, which is gitignored box-local state that `doctor.py` touches NOWHERE today (measured: zero `runs` references in `doctor.py`). That is the same objection OQ-03 accepts as decisive against `aw check`, and it applies to `aw doctor` for the same reason. E-04 must therefore state which of the three routes it takes rather than assuming liveness is available: read run records in doctor (couples a tracked-record sweeper to untracked state), report only steps that CANNOT be live (a strictly smaller rule), or leave the doctor consumer out and land the extraction alone.
- Scope: Extract the artifact location-and-status audit into ONE shared module, fix the two measured defects in its file lookup by consuming `selectors` instead of a private walk, and consume it from `aw doctor` in a way that cannot report an in-flight run as drift. EXCLUDES adding it to `aw check` (evaluated and deliberately deferred with a reason), and excludes changing what `aw runs` reports.
- Scope-Paths: agent_workflows/artifact_audit.py, agent_workflows/run_viewer.py, agent_workflows/doctor.py, tests/test_artifact_audit.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: auditshare
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 6ltz1y
- Approval: 2026-09-13, recorded via aw ipd set: status set to approved
- From-Backlog: onasuh

## Workflow history
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-B01..PR-B06 all FIXED, no deferrals, no new open questions. Core premise verified by symbol: both functions live in run_viewer.py, consumed only there (three call sites) and in its tests, with doctor.py/check_engine.py/cli.py referencing neither; both cited precedents (refork guard object-identity, evaluate_review_finding_escalation) are real. PR-B01 (HIGH): THE HEADLINE DEFECT IS FALSE. The plan claims archived plans may already be invisible and asks E-06 to assert the old lookup could not find a sharded plan; measured, plans_archive writes MONTHLY YYYYMM shards INSIDE the terminal dirs which ARE in the hardcoded list, the loop rglobs, and a constructed executed/202608/... plan IS FOUND today (shards are monthly, not weekly as the plan twice said), so that assertion would have failed. Replaced with the real defect: the TYPE SET covers plans and specs only, and a constructed backlog record returns None. PR-B02 (HIGH): E-04 may not be buildable as written and the plan's own OQ-03 holds the argument - liveness is an INPUT set from a run dir's PID/lock holder (is_live=(holder != HOLDER_NONE)) and merely passed through by the audit, while doctor.py reads zero run records, so a liveness-aware doctor rule means coupling a tracked-record sweeper to gitignored state, exactly the objection OQ-03 accepts as decisive against aw check; E-04 now requires an explicit recorded choice among (a) doctor reads run records, (b) tracked-only cannot-be-live, (c) no consumer this plan, with the warning that (b) risks duplicating the shipped IPD-M105, and I deliberately did not choose for the maintainer. PR-B03: F-10's environmental-sensitivity claim is stale and would have taught an executor to ignore a real regression - tests/test_run_viewer.py was fixture-isolated by e167c9b3 on 2026-09-08 and measures 75 passed in the primary checkout AND 75 passed in a fresh clone with ZERO run dirs. PR-B04: the suite baseline is wrong in both halves (real: 1 failed, 5958 passed at test_reporting_contract ParityTests from another party's gitignored opencode-recovery/ tree; test_orchestrator_retirement passes at 112). PR-B05: selectors has NO all-types entry point, both _iter_paths and resolve take one record_type, so cross-type coverage needs a stated method. PR-B06: the substring risk is INVERTED - it cannot bite today because reviews/ is never searched, and E-03's own widening creates it, so the exact declared-Id rule is what makes the widening safe (a review declares Subject-Id, so it is skipped for free). Verified correct and left alone: the collision defect (resolve returns both paths), IPD-M105 as OQ-03 describes, _receipt_is_live, the selectors read-only fence, OQ-01 and OQ-02. Three decisions recorded (D-1..D-3), all reversible. E/V counts unchanged at six each; aw ipd lint --phase review-finalize conforming. Readiness go-pending-approval: no unfixed BLOCKER/HIGH and no blocking question.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `onasuh`. NOTHING IN THE ITEM IS OBSOLETE and its premise was verified rather than trusted: both functions are still defined in `run_viewer.py` (`:439`, `:465`), still consumed only there and in its tests, and `doctor.py`/`check_engine.py`/`cli.py` reference neither. TWO THINGS THE ITEM DID NOT SAY, both measured at graduation and both shaping the plan. FIRST, a straight lift-and-shift would propagate two real defects: `find_artifact_file` hardcodes NINE directories (including a nonexistent `plans/archive` and two legacy `.agents/` paths) against a live tree with FIVE plans subdirs and a weekly-SHARDED archive it cannot track, and it matches `id6 in p.name` returning the FIRST hit with no collision policy, while `selectors.resolve` treats an id6 multi-match as a data bug not overridable by `--force`. So the extraction must consume `selectors` rather than carry the private walk into a second consumer. SECOND, the item's "accounting for active/live runner states" clause is the reason doctor cannot just call this today: the predicate maps status onto an expected directory, and a RUNNING step legitimately sits in `pending/` with a non-terminal status, so a liveness-blind consumer would flag every in-flight run. `run_viewer`'s tests already cover a live case at `tests/test_run_viewer.py:1285`. The item's `aw check` half is evaluated and deferred with a reason rather than dropped silently.

## Goal

Give every diagnosis surface one answer to "is this artifact where its status says it should be", without carrying a private filesystem walk or a first-match-wins reader into a second consumer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin current behavior before moving it

- [x] E-01 CHARACTERIZE THE EXISTING AUDIT BEFORE EXTRACTING IT, so the move is provably behavior-preserving for the surface that already depends on it. `aw runs` consumes this predicate in three places and its output is what an operator reads during recovery.
  PIN THE FOUR VERDICT SHAPES the current code produces: an artifact in its expected directory (clean), one in the WRONG directory (location drift), one whose on-disk `- Status:` disagrees with the step status (status drift), and one that cannot be found at all. `tests/test_run_viewer.py:1195` (`test_audit_step_artifact_and_summary`) already exercises several of these; read it first and extend rather than duplicate.
  PIN THE LIVE CASE EXPLICITLY. `tests/test_run_viewer.py:1285` builds `a1_live`, and `:1360` asserts that a particular arrangement yields NEITHER a location nor a status mismatch. That is the behavior a doctor consumer must inherit, so it must be pinned before the move, not discovered after.
  DO NOT CHANGE ANY VERDICT IN THIS ITEM. If a current verdict looks wrong, record it as a finding; changing behavior inside an extraction makes both unreviewable.
  - Depends on: none
  - Expected outcome: characterization tests pinning the four verdict shapes plus the live case, all passing at HEAD before any code moves.
  - Execution state: performed

### Task group 2: extract once, and fix the lookup while doing it

- [x] E-02 CREATE THE SHARED MODULE AND MOVE THE AUDIT PREDICATE INTO IT, leaving `run_viewer` a consumer rather than an owner.
  MOVE, DO NOT COPY. `run_viewer` must import from the new module and keep no local definition, and a test must assert that (the `test_runner_refork_guard.py` pattern is the in-repo precedent: assert the attribute IS the owner's object, not merely equal to it). A copy is how `render_stream`'s ancestors drifted.
  KEEP `StepSummary` OUT OF THE SHARED MODULE'S SIGNATURE IF POSSIBLE. `audit_step_artifact` takes a `StepSummary`, which is a run-viewer concept; a doctor consumer has no steps. Prefer a predicate taking the primitive facts (id6, stem, configured path, status) with a thin `StepSummary`-shaped adapter left in `run_viewer`. If that split proves impractical, say so and explain why rather than importing run-viewer types into a general module.
  DO NOT MAKE THE NEW MODULE IMPORT `run_viewer`. That would invert the dependency and recreate the coupling this extraction removes; if you find yourself needing it, the split above is wrong.
  - Depends on: E-01
  - Expected outcome: a shared module owning the audit predicate; `run_viewer` importing it with no local definition and a test asserting object identity; no run-viewer types in the shared signature, or a written reason why.
  - Execution state: performed

- [x] E-03 REPLACE THE PRIVATE FILE SEARCH WITH THE EXISTING RESOLVER, because carrying it forward would spread two measured defects to a second consumer.
  DEFECT ONE, RESTATED CORRECTLY IN REVIEW, BECAUSE THE ORIGINAL MOTIVATION WAS FALSE AND CHASING IT WOULD WASTE THE EXECUTOR'S TIME. The hardcoded list is NOT blind to archived plans: `aw plans archive` writes MONTHLY `YYYYMM/` shards INSIDE the terminal dirs (`plans_archive.py:4`; `artifact_core.shard_for_date` -> `cleaned[:6]`), those terminal dirs are in the list, and the loop `rglob`s, so a plan at `executed/202608/...` IS FOUND today (constructed and verified). Do NOT write a test asserting the current code cannot find a sharded plan; it can, and such a test would fail.
  THE ACTUAL DEFECT IS THE TYPE SET: the list covers plans and specs only, so an artifact of any other type carrying the queried id6 is invisible. Measured: a `backlog` record returns `None`. Latent for `aw runs` today (its steps are plans) but exactly what a second consumer meets, and the honest reason to stop hardcoding. The nonexistent `.aw/records/plans/archive` entry and the two `.agents/` legacy paths are dead weight to delete, not blind spots to fix.
  WHAT THE RESOLVER ACTUALLY OFFERS, AND ITS ONE CATCH: `selectors._iter_paths` (`:397`) enumerates one RECORD TYPE per call and `selectors.resolve(repo_root, record_type, selector)` likewise takes a single `record_type`. There is no all-types entry point, so "consume the resolver" means either passing the type the caller already knows (the run viewer knows its steps are plans) or looping the type vocabulary and defining precedence ACROSS types. Decide which and say so; the plan's phrasing implies a single all-types call that does not exist.
  DEFECT TWO, FIRST-MATCH-WINS WITH NO COLLISION POLICY: the loop returns on the first `id6 in p.name` hit. `selectors.resolve` instead treats an id6 matching multiple files as a data bug that `--force` cannot override, because `MATCH_ID6` is in `UNIQUE_KINDS`. Consuming the resolver gives the audit that verdict for free; keeping the loop would let `doctor` silently pick one of two colliding artifacts.
  NOTE THE SUBSTRING-VERSUS-EXACT DIFFERENCE IS REAL AND MUST BE DECIDED, not glossed. The current loop matches a SUBSTRING of the filename, which would also match a review record or walkthrough carrying the same id6 in its name (that is the documented review convention: a review carries its SUBJECT's id6). MEASURED IN REVIEW, and the danger is smaller than it looks but the fix is still right: because the hardcoded list never searches `reviews/` or `walkthroughs/` at all, today's loop CANNOT return a review record. So the substring risk is latent, and it becomes LIVE the moment the lookup starts enumerating more types, which is exactly what E-03 does. That inverts the usual reasoning: adopting the resolver's exact declared-`- Id:` rule is not merely tidier, it is what makes the type-set widening SAFE.
  A REVIEW RECORD ALSO WOULD NOT MATCH THE EXACT RULE, which is the point: it declares `- Subject-Id:`, not `- Id:` (verified in the review-tree README and in a real record), so `MATCH_ID6` skips it for free. State that as the reason for choosing exact, rather than asserting exact is generally better.
  BEWARE A PENDING OVERLAP: plans `76w6mq`, `xo3244` and `paw8so` all edit `selectors.py`. This plan must CONSUME the resolver, not modify it, so the overlap is read-only; say so explicitly and do not declare `selectors.py` in scope.
  - Depends on: E-02
  - Expected outcome: the audit resolves files through `selectors` with no private directory list; the archive-shard and collision cases are covered; the substring-versus-exact choice is stated; `selectors.py` is not modified.
  - Execution state: performed

### Task group 3: consume it from doctor without crying wolf

- [x] E-04 CONSUME THE SHARED AUDIT FROM `aw doctor`, AND MAKE IT LIVENESS-AWARE, which is the item's "accounting for active/live runner states" requirement and the difference between a useful diagnostic and an ignored one.
  THE HAZARD, STATED CONCRETELY: the predicate maps a step status onto an expected directory (`executed`/`complete` -> `executed/`, `superseded` -> `superseded/`, else `pending/`). A step that is RUNNING RIGHT NOW legitimately has its plan in `pending/` and a status that is neither terminal nor `pending`. Three live runs are executing in this repository as this plan is authored, so a liveness-blind doctor rule would report in-flight work as drift on every invocation.
  FIRST DECIDE WHETHER DOCTOR CAN KNOW LIVENESS AT ALL, because review measured that it cannot without new coupling, and this is the item's hardest question rather than a detail. `is_live` is an INPUT to the audit, not a derivation: it is set from a RUN DIRECTORY's PID/lock holder (`inspect_run_pid_and_runtime`, `is_live=(holder != HOLDER_NONE)`), and `doctor.py` reads no run records at all today. Choose ONE of three and record the choice with its cost:
  (a) DOCTOR READS RUN RECORDS. Honest but it couples a tracked-record sweeper to gitignored box-local state, which is the objection OQ-03 accepts as decisive against `aw check`; if it is decisive there it needs an argument here, not silence. Note the consequence: the doctor rule then reports nothing in a fresh clone or a lane worktree, where there are no run records.
  (b) REPORT ONLY WHAT CANNOT BE LIVE. A strictly smaller rule needing no run input: audit a TRACKED artifact whose own on-disk `- Status:` disagrees with its directory. Cheapest and CI-safe, but see the note below, because that predicate already ships.
  (c) LAND THE EXTRACTION WITHOUT THE DOCTOR CONSUMER, delivering one shared implementation plus the two lookup fixes, and leave the consumer to a follow-up once the liveness question has an owner.
  KNOW BEFORE CHOOSING (b) THAT IT LARGELY EXISTS: `ipd_schema._check_path_status` (`:432-456`) is a pure status-versus-directory predicate surfaced as lint rule `IPD-M105`, and OQ-03 already records that reachability, not the predicate, is the gap and that `k9awrq` owns it. So (b) risks duplicating a shipped rule; if you choose it, say what it adds that `IPD-M105` does not.
  REUSE THE LIVENESS NOTION THAT ALREADY EXISTS rather than inventing one, if you choose (a). `run_viewer`'s own tests distinguish a live case (`a1_live`, `tests/test_run_viewer.py:1407-1421`), and `check_engine._receipt_is_live` (`:1266`) is the in-repo precedent for "this record cannot describe work in progress, so do not advise on it" plus its fail-SAFE discipline (undeterminable means skip). Follow that direction: when liveness cannot be determined, do NOT report.
  REPORT AS ADVISORY, NOT AS AN ERROR, on first introduction. `aw doctor` is a diagnosis surface and a new rule that errors on day one against a corpus nobody has swept is how a check gets disabled. Measure the finding count on the live tree BEFORE choosing a severity, and state it.
  DO NOT CHANGE WHAT `aw runs` REPORTS. Its three call sites must produce byte-identical output; this item adds a consumer.
  - Depends on: E-03
  - Expected outcome: a RECORDED CHOICE among (a) doctor reads run records, (b) a tracked-only cannot-be-live rule, or (c) no doctor consumer this plan, with its cost stated; if (a) or (b), `aw doctor` reports artifact location/status drift, skips in-flight work, fails safe when liveness is undeterminable, and carries a severity chosen from a measured count; `aw runs` output unchanged in every case.
  - Execution state: performed

- [x] E-05 EVALUATE `aw check` AND RECORD THE DECISION RATHER THAN SILENTLY SKIPPING IT. The item says "and evaluate `aw check`", so a plan that only did doctor would leave half the request unanswered.
  THE ARGUMENT AGAINST is concrete and probably decisive: `aw check` is fail-closed in CI, and this audit compares a RUN's recorded step status against the tree, which means its verdict depends on gitignored run records under `.aw/records/runs/`. Those are absent from a fresh clone and from a lane worktree, so the same commit would produce different `aw check` results in CI than locally. A repository-level gate whose answer depends on untracked local state is not a gate.
  THE ARGUMENT FOR is that `aw check` is what agents and CI are pointed at, so a discrepancy invisible there is invisible in practice, which is the same reasoning behind `k9awrq`.
  DECIDE AND WRITE IT DOWN EITHER WAY, in the shared module's docstring so the next reader finds the reasoning at the code rather than in a closed plan. If the answer is no, say what WOULD make it viable (for example an audit keyed only on tracked artifacts, with no run-record input).
  - Depends on: E-04
  - Expected outcome: a recorded decision on `aw check` with its reasoning at the code, including what would make the rejected option viable.
  - Execution state: performed

### Task group 4: prove it

- [x] E-06 PROVE THE EXTRACTION MOVED NOTHING AND THE NEW CONSUMER COSTS NOTHING.
  ASSERT ONE IMPLEMENTATION: the shared module owns the predicate, `run_viewer` holds no local copy, and the attribute IS the same object (the refork-guard pattern). A test that only compares behavior would pass against a duplicate.
  ASSERT `aw runs` IS BYTE-UNCHANGED on a real recorded run, since the item's whole premise is that this surface already works and must keep working. Compare its output before and after.
  ASSERT THE TWO FIXED DEFECTS AS CORRECTED IN REVIEW. Defect one is the TYPE SET, so assert that an artifact of a type the old list never searched (a `backlog` record was the measured case, returning `None`) is now found. Do NOT assert that a MONTHLY-sharded plan under `executed/YYYYMM/` was previously unfindable: it was findable (constructed and verified), so that assertion would be false and the test would fail. If you want shard coverage, assert it still works AFTER the change, as a no-regression case. Defect two: an id6 matching multiple artifacts produces the collision verdict rather than a silent first pick.
  ASSERT THE LIVE CASE from doctor's side ONLY IF E-04 CHOSE (a) OR (b): an in-flight run produces NO finding. Build it as a fixture; do not depend on a live run being present. If E-04 chose (c), state that instead of fabricating a consumer-side test for a consumer that was not built.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA BY NODE ID. THE PLAN'S BASELINE WAS WRONG IN BOTH HALVES; re-measured on main at review HEAD `b644a7c3`: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, and the failure is NOT `tests/test_orchestrator_retirement.py` (which passes, `112 passed`) but `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by the GITIGNORED `opencode-recovery/` tree of another party's transcripts. It is pre-existing and unrelated; do NOT "fix" it and do NOT touch that tree (shared-checkout rule).
  AND `tests/test_run_viewer.py` IS NO LONGER ENVIRONMENT-SENSITIVE, so do not reason from that premise. It was converted to fixtures on 2026-09-08 (`e167c9b3`, "test: isolate run viewer fixtures"); measured at review HEAD it is `75 passed` in the primary checkout AND `75 passed` in a fresh clone with ZERO run dirs. Paste its own summary line anyway, but treat any failure as a REAL regression rather than an environmental artifact, which is the opposite of the plan's original instruction.
  - Depends on: E-05
  - Expected outcome: one implementation asserted by object identity, `aw runs` byte-unchanged, both lookup defects covered, an in-flight fixture producing no finding, and an empty bare-suite delta with `test_run_viewer.py`'s own line pasted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- BOTH FUNCTIONS ARE RUN-VIEWER-PRIVATE TODAY: defined at `run_viewer.py:439` and `:465`, consumed at `:489`, `:1463`, `:2554`, `:2558` and in `tests/test_run_viewer.py` only. `doctor.py`, `check_engine.py` and `cli.py` reference neither.
- THE ONE-IMPLEMENTATION PATTERN IS ESTABLISHED TWICE: `render_stream` plus `tests/test_runner_refork_guard.py` (28 pinned pairs), and `evaluate_review_finding_escalation`, whose docstring says both surfaces call it so they "cannot drift apart".
- `find_artifact_file` HARDCODES NINE DIRECTORIES, and the real defect is the TYPE SET (plans and specs only; a `backlog` record returns `None`), NOT shard blindness. Monthly `YYYYMM/` shards live INSIDE the terminal dirs and `rglob` already reaches them, so a sharded plan IS found today. The nonexistent `plans/archive` entry and two `.agents/` paths are dead weight.
- IT ALSO RETURNS THE FIRST `id6 in p.name` MATCH, with no collision policy, while `selectors.resolve` returns ALL matches for a duplicated id6 and treats that as a data bug not overridable by `--force` (`MATCH_ID6` in `UNIQUE_KINDS`).
- `selectors._iter_paths` (`:397`) does text-free enumeration for ONE record type per call, and `resolve` likewise takes ONE `record_type`. There is no all-types entry point; consuming it means passing a type or looping the vocabulary with a stated cross-type precedence.
- LIVENESS IS AN INPUT, NOT A DERIVATION, AND IT COMES FROM RUN RECORDS. `StepSummary.is_live` is set from a run dir's PID/lock holder (`inspect_run_pid_and_runtime`; `is_live=(holder != HOLDER_NONE)`) and the audit only passes it through. `doctor.py` reads no run records at all, so a liveness-aware doctor rule needs new coupling to gitignored state.
- `check_engine._receipt_is_live` IS THE PRECEDENT for skipping records that cannot describe work in progress, including its fail-SAFE rule (undeterminable means skip).
- RUN RECORDS ARE GITIGNORED (`.aw/records/runs/`) and absent from a lane worktree, which is the load-bearing objection to an `aw check` rule.
- THREE PENDING PLANS EDIT `selectors.py` (`76w6mq`, `xo3244`, `paw8so`). This plan must only CONSUME it.
- `tests/test_run_viewer.py` IS NO LONGER ENVIRONMENT-SENSITIVE: fixture-isolated on 2026-09-08 (`e167c9b3`), `75 passed` in both the primary checkout and a fresh clone with zero run dirs. Treat a failure there as a real regression.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the item's premise holds | Both functions are defined and consumed only in `run_viewer.py` and its tests; `doctor.py`, `check_engine.py` and `cli.py` reference neither, so `aw doctor` cannot see artifact drift. | `run_viewer.py:439`, `:465`, `:489`, `:1463`, `:2554`, `:2558`; grep of the three other modules |
| F-2 | HIGH | a lift-and-shift would spread a hardcoded TYPE SET (restated; the original shard claim was false) | The list covers plans and specs ONLY, so an artifact of any other type carrying the queried id6 is invisible: a `backlog` record returns `None`. Latent for `aw runs` (its steps are plans), live for any second consumer. | `run_viewer.py:450-459`; constructed backlog case -> `None`; spec-in-subdir case -> found |
| F-11 | HIGH | THE PLAN'S ORIGINAL DEFECT-ONE MOTIVATION IS FACTUALLY WRONG and would have produced a failing test | The plan says an archived plan "may already be invisible" and asks E-06 to assert the old code could not find a sharded plan. Measured: `aw plans archive` writes MONTHLY `YYYYMM/` shards INSIDE the terminal dirs, those dirs are in the hardcoded list, and the loop `rglob`s, so `executed/202608/...` IS FOUND today. The shards are monthly, not weekly as the plan twice states. | `plans_archive.py:4`; `artifact_core.shard_for_date` -> `cleaned[:6]`; constructed sharded plan -> FOUND |
| F-12 | HIGH | LIVENESS IS AN INPUT FROM RUN RECORDS, so E-04 as written may not be buildable | `StepSummary.is_live` (`run_viewer.py:97`) is set by `load_run_summary` from `inspect_run_pid_and_runtime(run_dir, ...)`, i.e. a run dir's PID/lock holder (`is_live=(holder != HOLDER_NONE)`); the audit only passes it through. `doctor.py` reads NO run records (measured: zero references). So "liveness-aware doctor" requires coupling a tracked-record sweeper to gitignored state, which is the very objection OQ-03 accepts as decisive against `aw check`. | `run_viewer.py:97`, `:930`, `:1090-1096`, `:510`, `:559`; grep of `doctor.py` |
| F-13 | MEDIUM | the substring risk is LATENT TODAY and becomes LIVE exactly when E-03 widens the type set | Today's loop cannot return a review record because the hardcoded list never searches `reviews/`. Widening the enumeration is what makes substring matching dangerous, so the exact declared-`- Id:` rule is what makes the widening safe. A review declares `- Subject-Id:`, not `- Id:`, so `MATCH_ID6` skips it for free. | constructed review-collision case; the reviews-tree convention |
| F-14 | MEDIUM | `selectors` HAS NO ALL-TYPES ENTRY POINT, which the plan's phrasing implies | `_iter_paths(repo_root, record_type)` and `resolve(repo_root, record_type, selector)` both take ONE type. "Consume the resolver" therefore means either passing the type the caller knows or looping the vocabulary and defining cross-type precedence. That choice must be made explicitly. | `selectors.py:397`, `:497-504` |
| F-3 | HIGH | and a first-match-wins reader with no collision policy | The loop returns the first `id6 in p.name` hit, while `selectors.resolve` calls an id6 multi-match "a data bug to fix, not overridable by --force". Consuming the loop would give `doctor` a silent arbitrary pick. | `run_viewer.py:456-461`; `selectors.py` `UNIQUE_KINDS` |
| F-4 | HIGH | liveness is why doctor cannot just call it | The predicate maps status onto an expected directory; a RUNNING step legitimately sits in `pending/` with a non-terminal status, so a liveness-blind rule flags every in-flight run. Three runs are live as this is authored. | `audit_step_artifact`'s status mapping; `tests/test_run_viewer.py:1285` |
| F-5 | MEDIUM | the one-implementation pattern is established | `render_stream` + a 28-pair AST refork guard, and `evaluate_review_finding_escalation`'s "cannot drift apart" docstring. An audit predicate belongs in that class. | `tests/test_runner_refork_guard.py`; `check_engine.py` |
| F-6 | MEDIUM | the resolver already does the hard part | `selectors._iter_paths` enumerates every type through one traversal, handles both roots, and recurses shards. | `selectors.py:397` |
| F-7 | MEDIUM | the `aw check` half has a load-bearing objection | The audit consumes a RUN's step status, and run records are gitignored and absent from a lane, so a fail-closed CI rule would answer differently in CI than locally. | `.aw/records/runs/` gitignored |
| F-8 | MEDIUM | substring versus exact is a real semantic change | The current loop substring-matches filenames, which also matches a review record carrying its SUBJECT's id6 (the documented review convention). The resolver reads the artifact's own declared `- Id:`. | the review-record convention; both readers measured |
| F-9 | LOW | three pending plans edit the resolver | `76w6mq`, `xo3244`, `paw8so` all declare `selectors.py`. This plan must consume, not modify, and must not declare it. | their `Scope-Paths` |
| F-10 | LOW | **CORRECTED: the run-viewer suite is NO LONGER environment-sensitive** | The plan says it reads live repo state and its failures are environmental. That was fixed on 2026-09-08 by `e167c9b3` ("test: isolate run viewer fixtures"): the module now builds its own run tree and its header states the hazard explicitly. Measured `75 passed` in the primary checkout AND `75 passed` in a fresh clone with ZERO run dirs. So any failure there is now a REAL regression, the opposite of the plan's instruction. | `git log -S` -> `e167c9b3`; fresh-clone run with 0 run dirs -> `75 passed` |
| F-15 | MEDIUM | THE SUITE BASELINE IS WRONG IN BOTH HALVES and names a test that passes | Plan cites `1 failed, 5648 passed` blaming `tests/test_orchestrator_retirement.py`, which passes (`112 passed`). Real: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, failing at `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` because of the gitignored `opencode-recovery/` tree belonging to another party. An executor could misread it as their own regression or clean up files that are not theirs. | bare pytest at `b644a7c3`; `tests/test_orchestrator_retirement.py` -> `112 passed` |
| F-16 | LOW | several cited line numbers had drifted | `find_artifact_file` is `:446` not `:439`; `audit_step_artifact` is `:472` not `:465`; its call sites are `:1599`, `:2845`, `:2849` not `:489`/`:1463`/`:2554`/`:2558`; the live test case is `:1407-1421` not `:1285`. The plan's own instruction to re-locate by name is right and is now the only citation rule. | measured by symbol at review HEAD |

## Proposed changes (ordered, validatable)

1. Characterize the four verdict shapes plus the live case at HEAD (E-01).
2. Move the predicate into a shared module, leaving `run_viewer` a consumer with no local copy (E-02).
3. Replace the private directory walk with `selectors`, fixing the TYPE-SET and collision defects, with the cross-type precedence stated (E-03).
4. Decide and record how `aw doctor` can know liveness at all, then consume the audit accordingly (advisory, measured count) or record why no consumer lands in this plan (E-04).
5. Record a reasoned decision on `aw check` at the code (E-05).
6. Prove one implementation, unchanged `aw runs`, both fixed defects, and an in-flight fixture producing nothing (E-06).

## Deferred / out of scope (with reason)

- ADDING AN `aw check` RULE. Evaluated in E-05 rather than silently skipped, and the objection is load-bearing: the audit consumes a run's recorded step status, run records are gitignored and absent from a lane worktree, so a fail-closed CI gate would answer differently in CI than locally. E-05 records what would make it viable (an audit keyed only on tracked artifacts).
- CHANGING WHAT `aw runs` REPORTS. Its three call sites must be byte-identical; the item asks for a shared engine, not a new run-viewer behavior.
- MODIFYING `selectors.py`. Three pending plans (`76w6mq`, `xo3244`, `paw8so`) already edit it; this plan consumes it read-only and deliberately does not declare it.
- CHANGING ANY AUDIT VERDICT. E-01 pins current behavior and forbids altering it; a wrong-looking verdict is a finding for a follow-up, because changing behavior inside an extraction makes both unreviewable.
- FIXING THE GITIGNORED-RUN-RECORD ARCHITECTURE. That is the substrate question behind `wmnmei` and the analytics Set; this plan works within it.
- SWEEPING ANY REAL DISCREPANCY THE NEW DOCTOR RULE FINDS. If it reports drift on another agent's plan, REPORT it: four agents are graduating concurrently and several Sets are executing, so moving someone's artifact would be exactly the shared-checkout violation the contract forbids.
- BACKFILLING THE AUDIT INTO `aw attention`. A third consumer multiplies the false-positive surface before the first new one has been proven; worth doing later if doctor's version earns trust.
- DELETING OR REWRITING `find_artifact_file`'s DEAD LIST ENTRIES AS A SEPARATE CONCERN. The nonexistent `.aw/records/plans/archive` and the two `.agents/` legacy paths are dead weight rather than defects, and E-03 removes the whole list anyway; do not file them as their own work.
- FIXING `tests/test_run_viewer.py`'s ENVIRONMENT SENSITIVITY. Already fixed by `e167c9b3` on 2026-09-08 (fixture isolation; `75 passed` in a fresh clone with zero run dirs). The plan's F-10 premise is corrected rather than acted on. NOTE for the executor: plan `utwr6y` (`testiso-01`) still proposes this conversion and its premise is now largely satisfied; that is that plan's problem, not this one's, and must not be pulled in here.
- GIVING `aw doctor` A RUN-RECORD READER AS A GENERAL CAPABILITY. If E-04 chooses route (a), it needs only what the audit requires; building a general run-record layer inside a tracked-record sweeper is an architectural change with its own review surface and belongs to the substrate question behind `wmnmei`.

## Scope check

- Over-scope: none. One new module, one call-site conversion, one new consumer, two test modules.
- Scope-Paths justification: `agent_workflows/artifact_audit.py` is the new shared module E-02 creates; `agent_workflows/run_viewer.py` holds both functions today and becomes a consumer (E-02, E-03), and its three call sites must stay behavior-identical (E-06); `agent_workflows/doctor.py` is the new consumer (E-04, E-05); `tests/test_artifact_audit.py` is new and carries the shard, collision and in-flight fixtures; `tests/test_run_viewer.py` holds the existing characterization coverage E-01 extends and the byte-identical proof E-06 needs. `agent_workflows/selectors.py` is deliberately NOT declared: this plan CONSUMES the resolver and three other pending plans already edit that file, so declaring it would invite a collision at the finalize scope gate. If the executor concludes the resolver must change, that is a scope-widening finding to report, not to make.
- Under-scope, stated rather than left as `none`: this plan adds no `aw check` rule, changes no `aw runs` output, modifies no resolver, alters no audit verdict, does not fix the gitignored run-record architecture, sweeps no real discrepancy, does not reach `aw attention`, does not build a general run-record reader for `aw doctor`, and does not touch `tests/test_run_viewer.py`'s environment sensitivity (already fixed by `e167c9b3`). Each is excluded with a reason above.
- A ROUTE-DEPENDENT SCOPE NOTE, since E-04 now has three legal answers: under routes (a) and (b) every declared path is modified as planned; under route (c) `agent_workflows/doctor.py` is DECLARED BUT UNMODIFIED. That is legitimate and is exactly what `aw ipd finalize`'s two-way reconciliation exists to record, so acknowledge it with `--scope-ack agent_workflows/doctor.py=...` rather than inventing a token edit to make the declaration look used.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted AND the failing node ids from each. Re-measured at review HEAD `b644a7c3`: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, failing at `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` (caused by the gitignored `opencode-recovery/` tree of another party; pre-existing, do NOT fix, do NOT touch that tree). The plan's `1 failed, 5648 passed` blaming `test_orchestrator_retirement` is superseded; that file passes. Criterion: AFTER minus BEFORE is EMPTY compared BY NODE ID, never an absolute count.
- `tests/test_run_viewer.py`'s OWN summary line pasted separately, now measured at `75 passed` in the primary checkout and `75 passed` in a fresh clone with zero run dirs. Since `e167c9b3` fixture-isolated it, a failure there is a REAL regression, not environmental.
- AN OBJECT-IDENTITY ASSERTION that `run_viewer`'s audit attribute IS the shared module's object, following the `test_runner_refork_guard.py` pattern; a behavioral comparison is insufficient because it passes against a duplicate.
- `aw runs` OUTPUT BYTE-IDENTICAL on a real recorded run, before and after.
- A TYPE-SET FIXTURE proving an artifact of a type the old list never searched (measured case: a `backlog` record, which returned `None`) is now FOUND. This REPLACES the plan's original sharded-archive assertion, which was based on a falsified premise: a MONTHLY-sharded plan under `executed/YYYYMM/` is already found today, so use it as a no-regression case only, never as proof of a fix.
- A COLLISION FIXTURE proving an id6 matching multiple artifacts yields the collision verdict rather than a silent first pick.
- E-04'S RECORDED ROUTE CHOICE among (a) doctor reads run records, (b) a tracked-only cannot-be-live rule, or (c) no doctor consumer this plan, with the cost stated. If (b), also state what it adds over the already-shipped `IPD-M105` (`ipd_schema._check_path_status`).
- IF (a) OR (b): AN IN-FLIGHT FIXTURE proving `aw doctor` reports NOTHING for a running step, plus the fail-safe case (liveness undeterminable -> no report), and THE MEASURED FINDING COUNT on the live tree that justified the chosen severity. If (c), state that no consumer-side test exists because no consumer was built, rather than fabricating one.
- `aw check all --agent` PER-RULE counts before and after, showing no rule's count changed (this plan adds no check rule).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THE SHARED MODULE'S DOCSTRING IS THE PRIMARY DOCUMENTATION and must state three things the next reader will otherwise re-derive: that it is the ONE implementation and both `aw runs` and `aw doctor` call it (the `evaluate_review_finding_escalation` wording is the model, since that docstring exists precisely to stop a second implementation); WHY it resolves through `selectors` rather than a private directory list, naming the shard and collision defects that motivated it; and WHY it is liveness-aware, because a future change that drops that guard would make the doctor rule fire on every in-flight run.

E-05's `aw check` DECISION belongs in that same docstring, including what would make the rejected option viable. A decision recorded only in a closed plan is a decision the next reader re-litigates.

`find_artifact_file`'s current docstring ("Search the repository for an artifact markdown file matching id6 or stem") describes a substring search. If E-03 changes the matching semantics to the resolver's declared-`- Id:` rule, that docstring becomes wrong and must move with the behavior.

THE DOCSTRING MUST NOT REPEAT THE FALSIFIED SHARD CLAIM. Review measured that monthly `YYYYMM/` shards live inside the terminal dirs and are already reached by `rglob`, so a comment claiming the old lookup could not see archived plans would enshrine a false statement at the code, which is worse than leaving it unexplained. Record the TYPE-SET limitation instead, which is the real one.

No spec change is expected: this is an internal refactor plus a new advisory. If the executor finds spec text asserting that `aw doctor` already surfaces artifact drift, that is a false claim to report rather than to edit.

## Open questions

### OQ-01: Should the shared audit take primitive facts or a `StepSummary`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: PRIMITIVE FACTS, WITH A THIN ADAPTER LEFT IN `run_viewer`. `audit_step_artifact` currently takes a `StepSummary`, which is a run-viewer concept carrying run-specific fields; a doctor consumer has no steps and would have to fabricate one, which is the tell that the type is wrong for a shared module. Taking (id6, stem, configured path, status) keeps the shared module independent of the run viewer and makes the dependency one-directional, which is the property that stops this becoming the coupling it was extracted to remove. E-02 permits reporting that the split is impractical, but requires a written reason rather than silently importing run-viewer types into a general module.

### OQ-02: Should the new doctor finding be an error or advisory on introduction?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: ADVISORY, WITH THE SEVERITY CHOSEN FROM A MEASURED COUNT, and the precedent is explicit. `check_engine`'s own review-escalation rule documents that a fail-closed ABSENT case "would mass-fail the entire corpus on day one", and `_receipt_is_live` fails SAFE for the same reason. This audit compares a run's recorded status against the tree across a corpus nobody has swept for this property, so an error-severity introduction is how a new diagnostic gets disabled rather than fixed. E-04 requires measuring the count on the live tree BEFORE choosing, which converts this from a preference into an evidenced decision, and leaves promoting it later available once the corpus is clean.

### OQ-03: Should `aw check` gain this rule?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: NO, `aw check` does not gain this rule, AND THE TRACKED-ONLY ALTERNATIVE IS NOT THIS PLAN'S TO BUILD EITHER, because measurement showed it MOSTLY ALREADY EXISTS. The obstacle stands as written (the audit's expected status comes from a RUN's recorded step status, run records are gitignored and absent from a clone or a lane, and `aw check` is fail-closed in CI, so a verdict depending on untracked local state is not a gate).
  WHAT THE MAINTAINER CHALLENGED, and it was the right question: why the RUN-shaped audit was being shared at all, rather than a general one. Traced to the source item `onasuh`, which asked to extract the audit so "`aw runs`, `aw doctor`, and other diagnosis tooling share a single source of truth". The audit in front of that item happened to be run-shaped because it lived in the run viewer; nobody asked whether run-shaped was the question `aw doctor` needed. MEASURED AND THE ANSWER IS NO: `aw doctor`'s six sections are environment, git working tree, cross-tree attention, security sanitizer and artifact schema contracts, and every one reads TRACKED records. So `aw doctor` and `aw check` are BOTH tracked-record sweepers and the run-record coupling is wrong for both, not only for `aw check`. This plan's careful liveness handling (E-04) exists only because the audit reads run state; it is correct for `aw runs` and would be unnecessary for a tracked-only audit.
  WHY THE OBVIOUS RE-SCOPE WAS THEN REJECTED, after being chosen and then re-examined: THE TRACKED-ONLY PREDICATE ALREADY EXISTS AND WORKS. `ipd_schema._check_path_status` (`:432-456`) is pure, takes only a status and a directory name, covers all five dispositions (terminal must match its directory, standing must be `reusable`, pre-terminal must be under `pending`), and surfaces as lint rule `IPD-M105` via `validate_metadata` (`:425-427`) with the directory resolved shard-safely by `ipd_lint._dir_of` (`:389-396`). Verified live, not dead code: a `pending/` file carrying `- Status: executed` yields `IPD-M105` at error disposition. So a shared tracked-only audit would duplicate a shipped predicate, and the honest remaining work is REACHABILITY, which `k9awrq` (`lintreach-01`) already owns: its E-02 calls `ipd_lint.lint_file` from the plan sweep, which brings `IPD-M105` along, and its E-03 is exactly the disposition-coverage decision that needs.
  SO THIS PLAN IS UNCHANGED. It keeps the run-shaped audit and shares it for `aw runs`' benefit; E-05 still records the `aw check` decision, and should now record THIS reasoning (the predicate exists, reachability is `k9awrq`'s) rather than the weaker "an audit keyed only on tracked artifacts would be viable".
  TWO GENUINELY UNOWNED DEFECTS WERE FOUND WHILE MEASURING AND ARE FILED SEPARATELY (backlog `dbslfm` and `4r91r1`), not fixed here: (1) `IPD-M105` catches only ONE DIRECTION, because a file in a terminal directory returns `DISPOSITION_LEGACY` with an empty diagnostic list before `check_metadata` runs (`ipd_lint.py:1023-1025`), so a plan sitting in `executed/` while its own `- Status:` says otherwise is invisible, and the whole `executed/` tree is exempt; `k9awrq` cannot fix it because its scope explicitly excludes changing any rule. (2) The equivalent check inside `aw attention` is SILENTLY DEAD in the `.aw/` layout: `attention.py:900-916` guards on `rel.startswith(".agents/plans/")` while `_rel_posix` yields un-normalized `.aw/records/plans/...` paths, so the branch never runs, and it carries a second independent bug (`rel.split("/")[2]` would yield `"plans"` even if the guard passed). Verified by measurement: an `.aw/`-layout plan in `executed/` carrying `- Status: superseded` produces NO drift, while the identical file under the legacy prefix produces `attention.disposition-mismatch`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL passing output of the characterization tests at HEAD, before any extraction, and name which of the four verdict shapes each covers. Quote the LIVE-case assertion specifically, since that is the behavior the doctor consumer must inherit. Confirm in one sentence that no verdict was changed, and paste any wrong-looking verdict you recorded as a finding instead of fixing.
  - Observed evidence: `tests/test_run_viewer.py::test_audit_step_artifact_pins_the_four_verdict_shapes` was added and run AT HEAD, before any code moved:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest -o addopts="" -q tests/test_run_viewer.py -k "audit"
    ..                                                                       [100%]
    2 passed, 74 deselected in 0.20s
    ```

    The four shapes, each a separate assertion block in that test: SHAPE 1 CLEAN (`cln001`, executed step + plan in `executed/` declaring `- Status: executed` -> all three flags False); SHAPE 2 LOCATION DRIFT ONLY (`loc002`, superseded step whose plan sits in `executed/` while its own status agrees -> `location_mismatch` True, `status_mismatch` False); SHAPE 3 STATUS DRIFT ONLY (`sta003`, executed step whose plan IS in `executed/` but declares `approved` -> `location_mismatch` False, `status_mismatch` True, `file_status == "approved"`); SHAPE 4 MISSING (`msg004`, nothing on disk -> `missing_entirely` True, `actual_path` and `file_status` both None). ISOLATING SHAPES 2 AND 3 IS NEW COVERAGE: the pre-existing `test_audit_step_artifact_and_summary` only had a case tripping BOTH flags at once, so neither was pinned alone.

    THE LIVE-CASE ASSERTION, quoted, since it is what the doctor consumer must inherit:

    ```python
    a_live = run_viewer.audit_step_artifact(
        _step("lve005", "running", "20260908-chr-05-lve005", is_live=True), repo_root=root)
    self.assertTrue(a_live.is_live)
    self.assertFalse(a_live.location_mismatch)
    self.assertFalse(a_live.status_mismatch)
    self.assertFalse(a_live.missing_entirely)
    ```

    Plus a pass-through assertion that the identical arrangement with `is_live=False` yields the SAME three verdicts and differs only in the flag, which is the mechanical proof that liveness is an input rather than a derivation. A `configured_file` short-circuit case is also pinned, because E-03 replaces the search that branch bypasses.

    NO VERDICT WAS CHANGED by this item: the test was written against the shipped behavior and passed on first run at HEAD. NO WRONG-LOOKING VERDICT WAS FOUND, so nothing was recorded as a finding here; one questionable behavior WAS found later while building the doctor consumer (a `pending/` record declaring a terminal status), but it is a property of the NEW tracked-only predicate and is handled in V-04, not a change to any existing verdict.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new module's definition site and the import in `run_viewer.py`. Paste the OBJECT-IDENTITY assertion and its passing output (`run_viewer`'s attribute IS the shared object). Paste a search proving `run_viewer` holds NO local definition. State whether the signature takes primitive facts or a `StepSummary`, and if the latter, paste the written reason.
  - Observed evidence: THE NEW MODULE'S DEFINITION SITES (`agent_workflows/artifact_audit.py`):

    ```
    $ grep -n "^class ArtifactAudit\|^def find_artifact\|^def audit_artifact\|^def audit_tracked_artifact\|^def build_index" agent_workflows/artifact_audit.py
    142:class ArtifactAudit:
    266:def build_index(
    319:def find_artifact(
    415:def audit_artifact(
    481:def audit_tracked_artifact(
    ```

    THE IMPORT AND RE-EXPORT IN `run_viewer.py`:

    ```
    $ grep -n "import artifact_audit\|StepArtifactAudit = _audit\|^def find_artifact_file\|^def audit_step_artifact" agent_workflows/run_viewer.py
    22:from agent_workflows import artifact_audit as _audit
    439:StepArtifactAudit = _audit.ArtifactAudit
    442:def find_artifact_file(repo_root: Path, id6: str, stem: str) -> Path | None:
    455:def audit_step_artifact(
    ```

    THE OBJECT-IDENTITY ASSERTION (`tests/test_artifact_audit.py::OneImplementationTests`), following the `test_runner_refork_guard.py` pattern because a behavioral comparison passes against a duplicate:

    ```python
    def test_run_viewer_audit_type_is_the_shared_module_object(self):
        self.assertIs(run_viewer.StepArtifactAudit, artifact_audit.ArtifactAudit)
    ```

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest -o addopts="" -q tests/test_artifact_audit.py -k "OneImplementation"
    collected 26 items / 21 deselected / 5 selected
    tests/test_artifact_audit.py .....                                       [100%]
    ======================= 5 passed, 21 deselected in 0.21s =======================
    ```

    NO LOCAL DEFINITION REMAINS in `run_viewer` (the dataclass, the status pattern and the private search list are all gone; the count is the number of matching lines, i.e. zero):

    ```
    $ grep -c "class StepArtifactAudit\|_STATUS_LINE_RE = re.compile\|search_dirs" agent_workflows/run_viewer.py
    0
    ```

    That is asserted in the suite too (`test_run_viewer_holds_no_local_audit_definition`), together with the reverse-direction guard `test_shared_module_does_not_import_run_viewer`, which keeps the dependency one-directional.

    THE SIGNATURE TAKES PRIMITIVE FACTS, resolving OQ-01 as it recommended: `audit_artifact(repo_root, id6, stem, *, status, configured_file, is_live, record_types)`. No run-viewer type appears anywhere in the shared module's signatures, and `test_shared_signature_takes_primitive_facts_not_a_step` calls it with primitives only. The `StepSummary`-shaped adapter stays in `run_viewer` as `audit_step_artifact`, which owns the step-to-primitives projection (including the `setid-id6` stem fallback) because it owns the type. No written impracticality reason is needed since the split held.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the resolver-consuming lookup and a search proving no hardcoded directory list remains. STATE how you obtained cross-type coverage given that `selectors.resolve` takes ONE `record_type` (a passed type, or a loop with stated precedence). Paste the ACTUAL passing output of the TYPE-SET fixture (an artifact of a type the old list never searched, e.g. a `backlog` record, is now found) and of the collision fixture (an id6 matching several artifacts yields the collision verdict, not a first pick). Paste the MONTHLY-shard case as a no-regression check, and explicitly confirm you did NOT assert the old code failed on it, since it did not. State which matching semantics you chose (substring versus declared `- Id:`) and why, including that a review record declares `- Subject-Id:` and so is skipped by the exact rule for free. Paste `git status --porcelain agent_workflows/selectors.py` proving it was NOT modified.
  - Observed evidence: THE RESOLVER-CONSUMING LOOKUP is `artifact_audit.build_index` + `find_artifact`, and NO hardcoded directory list remains (asserted by `test_no_hardcoded_directory_list_remains`, which also asserts the positive: the source contains `_sel._iter_paths`):

    ```
    $ grep -n "_sel._iter_paths\|_sel.resolve\|_sel._read_header\|_sel._read_id" agent_workflows/artifact_audit.py
    (enumeration + front-matter reading all go through selectors; no directory literals)
    $ grep -c 'records" / "plans" / "pending"\|"plans" / "archive"' agent_workflows/artifact_audit.py
    0
    ```

    CROSS-TYPE COVERAGE, given that `selectors.resolve` takes ONE `record_type` and there is deliberately no all-types entry point (F-14): I LOOP THE TYPE VOCABULARY, declared as the module constant `TYPE_PRECEDENCE` (`plans, specs, backlog, releases, roadmaps, research, prompts, walkthroughs, comms, other`). THE STATED CROSS-TYPE PRECEDENCE IS: an exact declared `- Id:` match is collected across ALL types FIRST and a multi-type hit is reported as a COLLISION rather than resolved by type order, so the ordering never silently decides between two declaring records; the order matters only for the filename tier and for `paths` determinism. `plans` leads because every caller today audits plans; `other` is last because it is a catch-all. Cross-type collision is asserted by `test_cross_type_id6_collision_is_reported`.

    A CORRECTION THE PLAN DID NOT ANTICIPATE, MEASURED AND LOAD-BEARING: `selectors` reads a BOUNDED 4096-byte header (`selectors._HEADER_BYTES`), so an EXACT-ONLY lookup regresses badly. Measured over all 1202 records of this tree, 268 declare their `- Id:` BELOW that cap, including THIS PLAN'S OWN FILE (byte offset 6485), and `selectors._read_id(_read_header(p))` returns None for every one of them:

    ```
    $ python3 -c "...; print('byte offset of - Id: line:', txt.index(chr(10)+'- Id: 6ltz1y'), 'header cap:', selectors._HEADER_BYTES, 'read_id:', selectors._read_id(selectors._read_header(p)))"
    byte offset of '- Id:' line: 6485
    header bytes cap: 4096
    read_id from bounded header: None
    ```

    So the lookup is TWO-TIER: exact declared `- Id:` first, then the clustered filename's id6 FIELD (`artifact_naming.parse_clustered`, never a bare substring), then `stem` as the last resort. Covered by `test_filename_tier_covers_a_declared_id_below_the_bounded_header`, which asserts both halves (the exact tier genuinely cannot see it; the audit finds it anyway via `kind == "filename-id6"`).

    THE TYPE-SET FIXTURE (defect one, as corrected in review), passing:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest -o addopts="" -q tests/test_artifact_audit.py -k "LookupDefect"
    collected 26 items / 17 deselected / 9 selected
    tests/test_artifact_audit.py .........                                   [100%]
    ======================= 9 passed, 17 deselected in 0.41s =======================
    ```

    The old behavior was measured at HEAD before the change, confirming the corrected motivation: a `backlog` record carrying the queried id6 returned `None`, while a spec in a SUBDIRECTORY was found (so recursion already worked):

    ```
    DEFECT-1 type set: backlog id6 -> None
    spec in subdir -> (found)
    ```

    `test_type_set_covers_every_record_type_not_just_plans_and_specs` extends that to six formerly invisible types.

    THE COLLISION FIXTURE (defect two), also measured at HEAD first, where the old loop silently returned the SECOND file:

    ```
    DEFECT-2 collision -> first pick: .../pending/20260902-sety-02-ccc333-two.ipd.md
    ```

    Now `test_defect_two_id6_collision_is_reported_not_silently_picked` asserts `is_collision` is True, `path` is None (no arbitrary pick), both candidates are listed, and the audit surfaces it as `missing_entirely` WITH the collision list rather than a confident verdict about one candidate.

    THE MONTHLY-SHARD CASE AS A NO-REGRESSION CHECK, and I EXPLICITLY DID NOT ASSERT THE OLD CODE FAILED ON IT, because review measured that it did not. Verified at HEAD before the change that a sharded plan WAS already found:

    ```
    SHARD (claimed defect, actually works): -> .../plans/executed/202608/20260801-setx-01-bbb222-thing.ipd.md
    ```

    `test_monthly_shard_still_found_no_regression` therefore asserts it STILL works after the change (and that the audit reports `actual_dir == "202608"` with `expected_dir == "executed"`), and its docstring records that the opposite assertion would be false.

    MATCHING SEMANTICS CHOSEN: EXACT DECLARED `- Id:` (with the filename-FIELD fallback above), not substring. THE REASON IS THE ONE F-13 GIVES, i.e. the widening is what makes it necessary: today's substring loop cannot return a review record only because the hardcoded list never searched `reviews/`, so widening the type set is exactly what would make substring matching dangerous. A REVIEW RECORD DECLARES `- Subject-Id:`, NOT `- Id:`, so `MATCH_ID6` skips it FOR FREE; and because the fallback tier parses the grammar's id6 FIELD rather than testing a substring, it cannot return a review either. Asserted by `test_exact_declared_id_beats_a_review_record_carrying_the_same_id6` (the plan is returned, `kind == "id6"`, no collision).

    `selectors.py` WAS NOT MODIFIED (empty output means no change):

    ```
    $ git status --porcelain agent_workflows/selectors.py
    $
    ```

    A PERFORMANCE NOTE, because consuming the resolver has a real cost the plan did not budget for and ignoring it would have been a regression: the run viewer audits EVERY step of EVERY displayed run, and a full multi-type walk measures ~560ms on this tree (the `other` catch-all alone is ~330ms for 4 files, since it sweeps the whole records tree). A per-step walk took `tests/test_run_viewer.py` from `2.41s` to `35.41s`. `build_index` therefore memoizes ONE traversal per (root, type-vocabulary), invalidated by record-directory mtimes so a lifecycle MOVE is still seen (asserted by `test_index_is_invalidated_when_an_artifact_moves`); the signature deliberately walks the literal layout instead of calling `selectors.record_dirs` per type, which measured ~1.6ms per call. Result: `76 passed in 4.00s`, and the worst single test fell from 6.63s to 0.56s. Statuses are always read FRESH (only path facts are cached), because an in-place `- Status:` edit does not change a directory mtime.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: FIRST state which of E-04's three routes you took ((a) doctor reads run records, (b) tracked-only cannot-be-live, (c) no doctor consumer) and paste the reasoning, including how you answered the objection that `doctor.py` reads no run records today and that OQ-03 treats run-record dependence as decisive against a CI gate. If (b), state what it adds over the shipped `IPD-M105`. If (a) or (b): paste `aw doctor`'s new output on the live tree with the MEASURED finding count, the severity chosen and why that count justified it, the in-flight fixture showing NO finding, and the fail-safe case (liveness undeterminable -> no report). If (c): say so plainly and paste no fabricated consumer evidence. IN EVERY CASE paste `aw runs` output before and after on a real recorded run, byte-identical.
  - Observed evidence: ROUTE TAKEN: **(b), THE TRACKED-ONLY CANNOT-BE-LIVE RULE**, implemented as `doctor.probe_artifact_audit` over `artifact_audit.audit_tracked_artifact`. The route choice and its cost are recorded AT THE CODE in that function's docstring, not only here.

    THE REASONING, AND HOW IT ANSWERS THE OBJECTION: route (a) was rejected because the objection is correct and decisive in the same way OQ-03 accepts it against `aw check`. `doctor.py` reads no run records anywhere (measured: zero `runs` references before this change), every other doctor probe reads TRACKED state, and run records live under `.aw/records/runs/`, which is gitignored and box-local. MEASURED IN THIS VERY LANE: `ls .aw/records/runs` -> `No such file or directory`, i.e. ZERO run dirs, while the primary checkout has 151. So route (a) would have produced a rule that reports nothing in exactly the environments where it most often runs (a fresh clone, a lane worktree), and it would couple a tracked-record sweeper to untracked state. THE COST OF (b), stated plainly rather than hidden: a genuine run-versus-tree discrepancy that only a run record can reveal remains visible only in `aw runs`. That is why the shared module still OWNS the run-shaped predicate for `aw runs` to use; the extraction's value (one implementation, two lookup defects fixed) lands either way.

    WHAT (b) ADDS OVER THE SHIPPED `IPD-M105`, which the plan required because (b) risked duplicating it. `IPD-M105` covers only ONE DIRECTION. MEASURED 2026-09-13 with `ipd_lint.lint_file` on two constructed plans:

    ```
    A pending/ + Status:executed    -> disposition: error                 codes: [... 'IPD-M105' ...]
    B executed/ + Status:superseded -> disposition: legacy/not evaluated   codes: []
    ```

    Case B is the blind spot: `ipd_lint.lint_file` returns `DISPOSITION_LEGACY` with an EMPTY diagnostic list for anything in a terminal directory, so the whole `executed/` tree is exempt and a plan sitting in `executed/` while its own status says `superseded` is invisible. This probe covers exactly that complement and DELIBERATELY DECLINES the `pending/` direction `IPD-M105` owns, so the two compose rather than overlap. It also spans EVERY artifact type, while `IPD-M105` is plans-only. That is asserted in `test_reports_the_ipd_m105_blind_spot`, which additionally asserts `IPD-M105` is NOT among the lint codes for the same file, so the claim cannot rot silently.

    THE MEASURED FINDING COUNT ON THE LIVE TREE IS **ZERO**, across all 1202 records of every type:

    ```
    $ python3 -m agent_workflows doctor --dir . --agent   # per-rule counts
      ...
      NEW RULE count (doctor.artifact-status-location-drift): 0
    ```

    SEVERITY CHOSEN: **`info` (ADVISORY)**, resolving OQ-02 as it recommended and justified BY that count. Zero live findings means nothing is being suppressed by choosing advisory, but the corpus has never been swept for this property, and `check_engine`'s own review-escalation rule documents that a fail-closed introduction "would mass-fail the entire corpus on day one". `core.drift_exit_code` treats `info` as non-failing, so introducing this CANNOT change `aw doctor`'s exit code; `test_advisory_severity_does_not_fail_the_doctor_exit_code` asserts that on a fixture that DOES produce a finding. Promotion later remains available.

    THE RULE IS NOT VACUOUS, shown on a fixture (human renderer):

    ```
      Advisory:    1 artifact(s) whose declared status disagrees with their directory
        - .aw/records/plans/executed/20260908-bs-01-bls001-x.ipd.md: declared Status: superseded expects superseded/ but the record is in executed/
    ```

    THE IN-FLIGHT FIXTURE SHOWING NO FINDING (`test_doctor_probe_reports_an_in_flight_run_as_nothing`), built from a fixture and never from a live run record: the exact on-disk arrangement a running execution leaves (plan in `pending/` carrying `approved`) yields `doctor.probe_artifact_audit(root) == []`, and the RUN-shaped audit given the same tree with `is_live=True` reports no drift either.

    THE FAIL-SAFE CASES (`test_fails_safe_for_everything_that_could_be_in_flight`), all five producing NO finding, in `check_engine._receipt_is_live`'s direction (undeterminable means skip):

    ```
      executed/ + Status:superseded (M105 BLIND SPOT -> must FIND)         -> FINDING executed/ expected superseded/
      executed/202608 shard + Status:not-executed (must FIND)              -> FINDING executed/ expected not-executed/
      executed/ + Status:executed (clean)                                  -> no finding
      pending/ + Status:approved (clean)                                   -> no finding
      pending/ + Status:executed (mid-finalize / M105's job -> FAIL SAFE)   -> no finding
      pending/ + no Status (nothing to compare)                            -> no finding
      pending/ + multi-word Status (unreadable -> skip)                    -> no finding
    ```

    A DEFECT I FOUND AND FIXED IN MY OWN FIRST IMPLEMENTATION, recorded because it is the exact failure mode E-04 warned about: my first version DID report `pending/` + `Status: executed` as a finding. That is the shape of a plan caught MID-FINALIZE (`ipd_lifecycle.finalize` writes the status and moves the file, and a sweep between the two would report a transaction in progress as drift), and it is also precisely the direction `IPD-M105` already owns. Both reasons say skip, so the predicate now returns None for it.

    `aw runs` OUTPUT IS BYTE-IDENTICAL BEFORE AND AFTER on a real recorded run, across five flag shapes (`(none)`, `--detail`, `--summary`, `--issues`, `--json`). The "before" capture was taken by stashing this change back to HEAD and re-running the identical command:

    ```
    $ diff before.txt after.txt && echo "BYTE-IDENTICAL"
    BYTE-IDENTICAL: aw runs output unchanged across all five flag shapes
    $ md5sum before.txt after.txt
    533440f91a30b9f894029bbaebdd76a9  before.txt
    533440f91a30b9f894029bbaebdd76a9  after.txt
    ```

    THE COMPARISON IS NOT VACUOUS: the fixture run deliberately carries a clean step, a clean executed step, a location+status drift step and a missing step, so the compared output contains real verdicts (from the `--issues` capture):

    ```
    │ 20260908-bi-03-ccc333 │ executed/ │ pending/ │ executed │ approved │
    │ bi-ddd444             │ executed/ │ missing  │ executed │ -        │
    ```

    The run record was BUILT AS A FIXTURE inside this lane rather than read from the primary checkout, because run records are gitignored and absent here and reading the main checkout is forbidden for a lane.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the recorded `aw check` decision AS WRITTEN IN THE SHARED MODULE'S DOCSTRING, not merely in this plan. It must state the gitignored-run-record objection and what would make the rejected option viable. Paste `aw check all --agent` per-rule counts before and after, proving no rule was added.
  - Observed evidence: THE DECISION AS WRITTEN IN `agent_workflows/artifact_audit.py`'s MODULE DOCSTRING (quoted verbatim, final paragraph):

    > THE ``aw check`` DECISION (IPD `6ltz1y` E-05, maintainer ruling 2026-09-08): NO, `aw check` does not gain this audit as a rule, and the tracked-only alternative is not the right shape either. `aw check` is FAIL-CLOSED in CI, while this audit's expected status comes from a RUN's recorded step status, and run records live under ``.aw/records/runs/``, which is GITIGNORED and absent from a fresh clone and from every isolated lane worktree the runner allocates. The same commit would therefore produce different `aw check` results in CI than locally, and a repository-level gate whose answer depends on untracked local state is not a gate. WHAT WOULD MAKE A CHECK RULE VIABLE is an audit keyed ONLY on tracked artifacts (comparing a record's own ``- Status:`` against its directory, with no run input) - but that predicate ALREADY SHIPS as ``ipd_schema._check_path_status``, surfaced as lint rule ``IPD-M105``, so building it here would duplicate a working rule. The honest remaining gap is REACHABILITY (getting ``IPD-M105`` into the sweep), which plan `k9awrq` owns. The same run-record-coupling objection applies to `aw doctor`, which is why the doctor consumer here is TRACKED-ONLY: see :func:`audit_tracked_artifact`.

    It records BOTH required elements: the gitignored-run-record objection, and what would make the rejected option viable (a tracked-only audit) TOGETHER WITH the measured reason that alternative is not this plan's to build (the predicate already ships; reachability is `k9awrq`'s). `test_docstring_records_the_aw_check_decision` asserts the docstring keeps mentioning `aw check`, `GITIGNORED`, `IPD-M105` and `tracked`, so the reasoning cannot be silently deleted.

    `aw check all --agent` PER-RULE COUNTS, BEFORE (measured by stashing this change back to HEAD) and AFTER:

    ```
    BEFORE                                    AFTER
      check.from-backlog-dangling        1      check.from-backlog-dangling        1
      check.id6-collision                1      check.id6-collision                1
      check.lifecycle-transition-invalid 15     check.lifecycle-transition-invalid 15
      check.name-nonconformant           3      check.name-nonconformant           3
      check.review-decision-unescalated  1      check.review-decision-unescalated  1
      check.scope-drift                  124    check.scope-drift                  139
      check.setid-collision              38     check.setid-collision              38
      check.system-layout-missing        1      check.system-layout-missing        1
      TOTAL 184                                 TOTAL 199
    ```

    NO RULE WAS ADDED: the rule SET is identical (eight rules before, the same eight after), and no `doctor.*` rule appears in `aw check` at all. The new finding lives only in `aw doctor` under `doctor.artifact-status-location-drift`.

    THE ONE COUNT THAT MOVED IS `check.scope-drift` (124 -> 139), AND IT IS NOT THIS RULE. Diffing by (location, rule) shows every new row belongs to FOUR OTHER PLANS' scope advisories, which count MY UNCOMMITTED FILES against their declared scopes while they sit in `pending/` with live begin receipts:

    ```
    NEW (location,rule) pairs after minus before:
      +5 check.scope-drift  .aw/records/plans/pending/20260908-actmodel-01-btot17-...
      +2 check.scope-drift  .aw/records/plans/pending/20260901-lanectn-05-xdr83v-...
      +5 check.scope-drift  .aw/records/plans/pending/20260908-actorparen-01-fn2l1u-...
      +3 check.scope-drift  .aw/records/plans/pending/20260908-runnerbugs-01-hp9rot-...
    REMOVED: (none)
    ```

    Not one of those locations is a file this plan touched, and none is a new rule; they are transient working-tree advisories that resolve once the change is committed. I did NOT "fix" them and did not touch those plans (shared checkout).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the BARE `python3 -m pytest` summary lines before and after AND the failing node ids from each, stating the failure-set delta BY NODE ID. Confirm the pre-existing `test_reporting_contract::ParityTests::test_only_expected_files_contain_the_full_contract_prose` failure appears in BOTH runs and was not "fixed", and that the gitignored `opencode-recovery/` tree was not touched. Paste `tests/test_run_viewer.py`'s OWN summary line separately and compare it against the measured `75 passed`; since `e167c9b3` fixture-isolated that module, treat ANY failure there as a real regression rather than environmental. Re-paste the object-identity assertion and both defect fixtures (type-set and collision) as a single verification pass, plus the in-flight fixture IF E-04 built a consumer. Confirm no real discrepancy found by the new rule was "fixed" by moving another agent's artifact.
  - Observed evidence: BARE SUITE, BEFORE (at HEAD `a9510164`, before any edit):

    ```
    5971 passed, 3 skipped, 2 xfailed in 84.53s (0:01:24)
    ```

    BARE SUITE, AFTER (on the committed change):

    ```
    5998 passed, 3 skipped, 2 xfailed in 76.34s (0:01:16)
    ```

    FAILING NODE IDS: **NONE IN EITHER RUN**, so the failure-set delta BY NODE ID is EMPTY:

    ```
    $ diff baseline-failed-nodes.txt final-failed-nodes.txt && echo "EMPTY DELTA"
    EMPTY DELTA
    ```

    +27 passing tests, which is the count this plan added (26 in `tests/test_artifact_audit.py`, 1 in `tests/test_run_viewer.py`).

    THE PLAN'S EXPECTED PRE-EXISTING FAILURE DOES NOT EXIST IN THIS LANE, AND I DID NOT "FIX" ANYTHING TO MAKE THAT SO. `test_reporting_contract::ParityTests::test_only_expected_files_contain_the_full_contract_prose` PASSES in both runs, because its stated cause is absent here: the gitignored `opencode-recovery/` tree of another party is not present in this lane (`ls -d opencode-recovery` -> `No such file or directory`). I did not create, touch, read or delete that tree.

    A BASELINE CORRECTION THE PLAN COULD NOT HAVE KNOWN, recorded because it would otherwise look like 17 regressions. The FIRST bare run in this lane reported `17 failed, 5954 passed`. All 17 are caused by the runner's own environment marker, not by repository state: the lane exports `AW_EXECUTION_ROLE=worker`, and `tests/test_worker_role_refusal.py::test_driver_own_process_is_not_worker_role` asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"` directly, while the begin/finalize CLI and runner-isolation tests refuse under a worker role by design. Proved by toggling ONLY that variable:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest -o addopts="" -q tests/test_worker_role_refusal.py tests/test_ipd_lifecycle_cli.py
    64 passed in 7.69s
    $ python3 -m pytest -o addopts="" -q tests/test_ipd_lifecycle_cli.py      # with the marker set
    2 failed, 55 passed in 6.81s
    ```

    Every suite figure quoted above is therefore measured with `env -u AW_EXECUTION_ROLE`, identically before and after, so the comparison is apples to apples. I changed no test and no production code to accommodate this.

    `tests/test_run_viewer.py`'s OWN SUMMARY LINE, separately:

    ```
    76 passed in 4.34s
    ```

    That is the review-measured `75 passed` PLUS the one characterization test E-01 added, with zero failures. Since `e167c9b3` fixture-isolated that module I treated it as a real-regression detector, and it earned its keep: the first resolver-consuming implementation passed it at `35.41s` instead of `2.41s`, which is what surfaced the per-step-traversal cost that `build_index` now memoizes (see V-03).

    THE SINGLE VERIFICATION PASS over the object-identity assertion and both defect fixtures, plus the in-flight fixture (E-04 DID build a consumer, route (b)):

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest -o addopts="" -q tests/test_artifact_audit.py tests/test_run_viewer.py
    102 passed in 5.42s
    ```

    Covering, by name: `test_run_viewer_audit_type_is_the_shared_module_object` (object identity, `assertIs`), `test_run_viewer_holds_no_local_audit_definition` and `test_shared_module_does_not_import_run_viewer` (the move, and its one-directional dependency), `test_defect_one_type_set_backlog_record_is_now_found` plus `test_type_set_covers_every_record_type_not_just_plans_and_specs` (defect one, TYPE SET), `test_defect_two_id6_collision_is_reported_not_silently_picked` plus `test_cross_type_id6_collision_is_reported` (defect two, collision), `test_monthly_shard_still_found_no_regression` (the shard case as no-regression ONLY, with its docstring recording that the opposite assertion would be false), and `test_doctor_probe_reports_an_in_flight_run_as_nothing` (in-flight fixture -> no finding).

    `aw runs` BYTE-IDENTICAL: see V-04 (`md5sum` match across five flag shapes on a non-vacuous fixture run).

    NO DISCREPANCY WAS "FIXED" BY MOVING ANYONE'S ARTIFACT. The new rule found ZERO findings on the live tree, so there was nothing to be tempted by; no record was moved, renamed or edited by this plan outside its declared scope. The only other-owner signal I saw was a transient `check.scope-drift` rise attributable to four other plans' advisories counting my uncommitted files (V-05), which I reported rather than touched.

    `aw sanitize --agent` CLEAN, and exit codes measured UNPIPED:

    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,...}
    sanitize exit=0
    doctor exit (unpiped)=1        # pre-existing repo findings, unrelated to this plan's advisory
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. OQ-03 (`aw check`) is open but subordinate: E-05 requires a RECORDED DECISION rather than an implementation, and the plan's value (one shared audit, two lookup defects fixed, doctor able to see drift) lands regardless of how the maintainer answers it.

IT CARRIES NO `Blocks-Release`, because backlog `onasuh` carries none. It is `Work-Kind: feature` at `Priority: medium` and the maintainer did not gate it; that is stated so a reader does not assume a gate was dropped.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Do NOT modify `agent_workflows/selectors.py`: three pending plans already edit it and this plan consumes it read-only. Do NOT change any audit verdict or any `aw runs` output. Do NOT move, rename or edit any real artifact the new doctor rule flags: four agents are graduating concurrently and several Sets are executing, so report a real discrepancy instead. Build every new case from FIXTURES, not from live run records, which are gitignored and absent from a lane. Re-locate every symbol by NAME rather than by the line numbers cited here. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the object-identity assertion and the in-flight fixture producing no finding.
