# IPD: Extract the run viewer artifact audit into one shared module and consume it from doctor

- Date: 2026-09-08
- Kind: child
- Concern: THE ARTIFACT LOCATION-AND-STATUS AUDIT LIVES ONLY IN THE RUN VIEWER, SO THE DIAGNOSIS TOOL A HUMAN REACHES FOR CANNOT SEE IT. Verified at HEAD: `find_artifact_file` (`run_viewer.py:439`) and `audit_step_artifact` (`:465`) are defined in `run_viewer.py` and consumed ONLY there (three call sites, `:489`, `:1463`, `:2554`/`:2558`) plus its own tests. Measured: `grep audit_step_artifact\|find_artifact_file` over `doctor.py`, `check_engine.py` and `cli.py` returns ZERO. So `aw runs` can tell you a step's artifact is in the wrong directory or carries the wrong status, and `aw doctor` cannot.
  THE DUPLICATION RISK IS NOT HYPOTHETICAL IN THIS REPOSITORY, which is why the item asks for extraction rather than for a second implementation. `render_stream` exists because the two host drivers had re-forked the same rendering helpers, and `tests/test_runner_refork_guard.py` now pins 28 (runner, symbol) pairs against exactly that. The same pattern produced `evaluate_review_finding_escalation`, whose docstring states that `aw check` and `aw ipd lint` "both call THIS function, so the sweep and the checkpoint gate cannot drift apart". An audit predicate that answers "is this artifact where its status says it should be" is precisely the kind of judgement that must have ONE implementation.
  TWO DEFECTS IN THE CURRENT IMPLEMENTATION MAKE A LIFT-AND-SHIFT WRONG, and both were measured while graduating. FIRST, `find_artifact_file` hardcodes NINE search directories including `.aw/records/plans/archive` and two `.agents/` legacy paths, while the live tree has FIVE plans subdirs and no `archive/`. The plans archive is weekly-SHARDED (`<disposition>/YYYYMM/`) by `aw archive`, and a hardcoded list cannot track that, so an archived plan may already be invisible to the audit. SECOND, it matches with `id6 in p.name` and returns the FIRST hit, so it has no collision policy at all, while `selectors.resolve` treats an id6 matching several files as "a data bug to fix, not overridable by --force" because `MATCH_ID6` is in `UNIQUE_KINDS`. A shared module that inherited a first-match-wins reader would spread that weakness to `doctor`.
  SO THE SHARED MODULE MUST CONSUME THE EXISTING RESOLVER RATHER THAN THE EXISTING SEARCH LOOP. `selectors` already enumerates every record type through one traversal (`_iter_paths`, `:397`), already handles the dual `.aw/`/`.agents/` roots, already recurses shards, and already has a documented collision verdict. The extraction's value is one audit predicate; its risk is carrying a private filesystem walk into a second consumer.
  THE ITEM'S "account for active/live runner states" CLAUSE IS LOAD-BEARING AND IS THE MAIN REASON DOCTOR CANNOT SIMPLY CALL THIS TODAY. `audit_step_artifact` maps a step status onto an expected directory (`executed`/`complete` -> `executed/`, `superseded` -> `superseded/`, else `pending/`), and a step that is RUNNING legitimately has its plan in `pending/` while its status is neither terminal nor pending. `run_viewer`'s tests already cover a live case (`tests/test_run_viewer.py:1285`, `a1_live`). A doctor-side consumer that ignored liveness would report every in-flight run as a discrepancy, which is the fastest way to make a new diagnostic ignored.
- Scope: Extract the artifact location-and-status audit into ONE shared module, fix the two measured defects in its file lookup by consuming `selectors` instead of a private walk, and consume it from `aw doctor` in a way that cannot report an in-flight run as drift. EXCLUDES adding it to `aw check` (evaluated and deliberately deferred with a reason), and excludes changing what `aw runs` reports.
- Scope-Paths: agent_workflows/artifact_audit.py, agent_workflows/run_viewer.py, agent_workflows/doctor.py, tests/test_artifact_audit.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: to-review
- Set: auditshare
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 6ltz1y
- From-Backlog: onasuh

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `onasuh`. NOTHING IN THE ITEM IS OBSOLETE and its premise was verified rather than trusted: both functions are still defined in `run_viewer.py` (`:439`, `:465`), still consumed only there and in its tests, and `doctor.py`/`check_engine.py`/`cli.py` reference neither. TWO THINGS THE ITEM DID NOT SAY, both measured at graduation and both shaping the plan. FIRST, a straight lift-and-shift would propagate two real defects: `find_artifact_file` hardcodes NINE directories (including a nonexistent `plans/archive` and two legacy `.agents/` paths) against a live tree with FIVE plans subdirs and a weekly-SHARDED archive it cannot track, and it matches `id6 in p.name` returning the FIRST hit with no collision policy, while `selectors.resolve` treats an id6 multi-match as a data bug not overridable by `--force`. So the extraction must consume `selectors` rather than carry the private walk into a second consumer. SECOND, the item's "accounting for active/live runner states" clause is the reason doctor cannot just call this today: the predicate maps status onto an expected directory, and a RUNNING step legitimately sits in `pending/` with a non-terminal status, so a liveness-blind consumer would flag every in-flight run. `run_viewer`'s tests already cover a live case at `tests/test_run_viewer.py:1285`. The item's `aw check` half is evaluated and deferred with a reason rather than dropped silently.

## Goal

Give every diagnosis surface one answer to "is this artifact where its status says it should be", without carrying a private filesystem walk or a first-match-wins reader into a second consumer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin current behavior before moving it

- [ ] E-01 CHARACTERIZE THE EXISTING AUDIT BEFORE EXTRACTING IT, so the move is provably behavior-preserving for the surface that already depends on it. `aw runs` consumes this predicate in three places and its output is what an operator reads during recovery.
  PIN THE FOUR VERDICT SHAPES the current code produces: an artifact in its expected directory (clean), one in the WRONG directory (location drift), one whose on-disk `- Status:` disagrees with the step status (status drift), and one that cannot be found at all. `tests/test_run_viewer.py:1195` (`test_audit_step_artifact_and_summary`) already exercises several of these; read it first and extend rather than duplicate.
  PIN THE LIVE CASE EXPLICITLY. `tests/test_run_viewer.py:1285` builds `a1_live`, and `:1360` asserts that a particular arrangement yields NEITHER a location nor a status mismatch. That is the behavior a doctor consumer must inherit, so it must be pinned before the move, not discovered after.
  DO NOT CHANGE ANY VERDICT IN THIS ITEM. If a current verdict looks wrong, record it as a finding; changing behavior inside an extraction makes both unreviewable.
  - Depends on: none
  - Expected outcome: characterization tests pinning the four verdict shapes plus the live case, all passing at HEAD before any code moves.
  - Execution state: pending

### Task group 2: extract once, and fix the lookup while doing it

- [ ] E-02 CREATE THE SHARED MODULE AND MOVE THE AUDIT PREDICATE INTO IT, leaving `run_viewer` a consumer rather than an owner.
  MOVE, DO NOT COPY. `run_viewer` must import from the new module and keep no local definition, and a test must assert that (the `test_runner_refork_guard.py` pattern is the in-repo precedent: assert the attribute IS the owner's object, not merely equal to it). A copy is how `render_stream`'s ancestors drifted.
  KEEP `StepSummary` OUT OF THE SHARED MODULE'S SIGNATURE IF POSSIBLE. `audit_step_artifact` takes a `StepSummary`, which is a run-viewer concept; a doctor consumer has no steps. Prefer a predicate taking the primitive facts (id6, stem, configured path, status) with a thin `StepSummary`-shaped adapter left in `run_viewer`. If that split proves impractical, say so and explain why rather than importing run-viewer types into a general module.
  DO NOT MAKE THE NEW MODULE IMPORT `run_viewer`. That would invert the dependency and recreate the coupling this extraction removes; if you find yourself needing it, the split above is wrong.
  - Depends on: E-01
  - Expected outcome: a shared module owning the audit predicate; `run_viewer` importing it with no local definition and a test asserting object identity; no run-viewer types in the shared signature, or a written reason why.
  - Execution state: pending

- [ ] E-03 REPLACE THE PRIVATE FILE SEARCH WITH THE EXISTING RESOLVER, because carrying it forward would spread two measured defects to a second consumer.
  DEFECT ONE, THE HARDCODED DIRECTORY LIST: `find_artifact_file` names NINE directories including `.aw/records/plans/archive` (which does not exist) and two `.agents/` legacy paths, while the live tree has FIVE plans subdirs. The plans archive is weekly-SHARDED as `<disposition>/YYYYMM/` by `aw archive`, so a hardcoded list cannot follow it and an archived plan may already be unfindable. `selectors._iter_paths` (`:397`) already enumerates every type through one traversal, handles both roots, and recurses.
  DEFECT TWO, FIRST-MATCH-WINS WITH NO COLLISION POLICY: the loop returns on the first `id6 in p.name` hit. `selectors.resolve` instead treats an id6 matching multiple files as a data bug that `--force` cannot override, because `MATCH_ID6` is in `UNIQUE_KINDS`. Consuming the resolver gives the audit that verdict for free; keeping the loop would let `doctor` silently pick one of two colliding artifacts.
  NOTE THE SUBSTRING-VERSUS-EXACT DIFFERENCE IS REAL AND MUST BE DECIDED, not glossed. The current loop matches a SUBSTRING of the filename, which will also match a review record or walkthrough carrying the same id6 in its name (that is the documented review convention: a review carries its SUBJECT's id6). Measured on one case both approaches agreed, but the semantics differ, so state which you chose and why. The resolver's id6 rule reads the artifact's own declared `- Id:`, which is the stronger answer.
  BEWARE A PENDING OVERLAP: plans `76w6mq`, `xo3244` and `paw8so` all edit `selectors.py`. This plan must CONSUME the resolver, not modify it, so the overlap is read-only; say so explicitly and do not declare `selectors.py` in scope.
  - Depends on: E-02
  - Expected outcome: the audit resolves files through `selectors` with no private directory list; the archive-shard and collision cases are covered; the substring-versus-exact choice is stated; `selectors.py` is not modified.
  - Execution state: pending

### Task group 3: consume it from doctor without crying wolf

- [ ] E-04 CONSUME THE SHARED AUDIT FROM `aw doctor`, AND MAKE IT LIVENESS-AWARE, which is the item's "accounting for active/live runner states" requirement and the difference between a useful diagnostic and an ignored one.
  THE HAZARD, STATED CONCRETELY: the predicate maps a step status onto an expected directory (`executed`/`complete` -> `executed/`, `superseded` -> `superseded/`, else `pending/`). A step that is RUNNING RIGHT NOW legitimately has its plan in `pending/` and a status that is neither terminal nor `pending`. Three live runs are executing in this repository as this plan is authored, so a liveness-blind doctor rule would report in-flight work as drift on every invocation.
  REUSE THE LIVENESS NOTION THAT ALREADY EXISTS rather than inventing one. `run_viewer`'s own tests distinguish a live case (`tests/test_run_viewer.py:1285`), and `check_engine._receipt_is_live` is the in-repo precedent for "this record cannot describe work in progress, so do not advise on it" plus its fail-SAFE discipline (undeterminable means skip). Follow that direction: when liveness cannot be determined, do NOT report.
  REPORT AS ADVISORY, NOT AS AN ERROR, on first introduction. `aw doctor` is a diagnosis surface and a new rule that errors on day one against a corpus nobody has swept is how a check gets disabled. Measure the finding count on the live tree BEFORE choosing a severity, and state it.
  DO NOT CHANGE WHAT `aw runs` REPORTS. Its three call sites must produce byte-identical output; this item adds a consumer.
  - Depends on: E-03
  - Expected outcome: `aw doctor` reports artifact location/status drift, skips in-flight work, fails safe when liveness is undeterminable, and carries a severity chosen from a measured count; `aw runs` output unchanged.
  - Execution state: pending

- [ ] E-05 EVALUATE `aw check` AND RECORD THE DECISION RATHER THAN SILENTLY SKIPPING IT. The item says "and evaluate `aw check`", so a plan that only did doctor would leave half the request unanswered.
  THE ARGUMENT AGAINST is concrete and probably decisive: `aw check` is fail-closed in CI, and this audit compares a RUN's recorded step status against the tree, which means its verdict depends on gitignored run records under `.aw/records/runs/`. Those are absent from a fresh clone and from a lane worktree, so the same commit would produce different `aw check` results in CI than locally. A repository-level gate whose answer depends on untracked local state is not a gate.
  THE ARGUMENT FOR is that `aw check` is what agents and CI are pointed at, so a discrepancy invisible there is invisible in practice, which is the same reasoning behind `k9awrq`.
  DECIDE AND WRITE IT DOWN EITHER WAY, in the shared module's docstring so the next reader finds the reasoning at the code rather than in a closed plan. If the answer is no, say what WOULD make it viable (for example an audit keyed only on tracked artifacts, with no run-record input).
  - Depends on: E-04
  - Expected outcome: a recorded decision on `aw check` with its reasoning at the code, including what would make the rejected option viable.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-06 PROVE THE EXTRACTION MOVED NOTHING AND THE NEW CONSUMER COSTS NOTHING.
  ASSERT ONE IMPLEMENTATION: the shared module owns the predicate, `run_viewer` holds no local copy, and the attribute IS the same object (the refork-guard pattern). A test that only compares behavior would pass against a duplicate.
  ASSERT `aw runs` IS BYTE-UNCHANGED on a real recorded run, since the item's whole premise is that this surface already works and must keep working. Compare its output before and after.
  ASSERT THE TWO FIXED DEFECTS: a plan in a weekly-SHARDED archive path is FOUND (the hardcoded list could not), and an id6 matching multiple artifacts produces the collision verdict rather than a silent first pick.
  ASSERT THE LIVE CASE from doctor's side: an in-flight run produces NO finding. Build it as a fixture; do not depend on a live run being present, since three are running now and none may be later.
  RUN THE SUITE BARE (`python3 -m pytest`) and judge on the DELTA. Baseline measured on main 2026-09-08: `1 failed, 5648 passed`, the failure being the pre-existing `tests/test_orchestrator_retirement.py` case. Inside a lane worktree roughly 32 further failures are environmental, and `tests/test_run_viewer.py` is itself known to be environment-sensitive (it reads live repo state), so paste ITS OWN summary line separately rather than relying on the whole-suite count.
  - Depends on: E-05
  - Expected outcome: one implementation asserted by object identity, `aw runs` byte-unchanged, both lookup defects covered, an in-flight fixture producing no finding, and an empty bare-suite delta with `test_run_viewer.py`'s own line pasted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- BOTH FUNCTIONS ARE RUN-VIEWER-PRIVATE TODAY: defined at `run_viewer.py:439` and `:465`, consumed at `:489`, `:1463`, `:2554`, `:2558` and in `tests/test_run_viewer.py` only. `doctor.py`, `check_engine.py` and `cli.py` reference neither.
- THE ONE-IMPLEMENTATION PATTERN IS ESTABLISHED TWICE: `render_stream` plus `tests/test_runner_refork_guard.py` (28 pinned pairs), and `evaluate_review_finding_escalation`, whose docstring says both surfaces call it so they "cannot drift apart".
- `find_artifact_file` HARDCODES NINE DIRECTORIES including a nonexistent `plans/archive` and two `.agents/` legacy paths; the live tree has FIVE plans subdirs and the archive is weekly-SHARDED (`<disposition>/YYYYMM/`).
- IT ALSO RETURNS THE FIRST `id6 in p.name` MATCH, with no collision policy, while `selectors.resolve` treats an id6 multi-match as a data bug not overridable by `--force` (`MATCH_ID6` in `UNIQUE_KINDS`).
- `selectors._iter_paths` (`:397`) ALREADY does text-free enumeration across every type, both roots, recursively. Consume it.
- LIVENESS IS THE BLOCKER FOR A DOCTOR CONSUMER: the predicate maps status onto an expected directory, and a RUNNING step legitimately sits in `pending/`. `tests/test_run_viewer.py:1285` covers a live case.
- `check_engine._receipt_is_live` IS THE PRECEDENT for skipping records that cannot describe work in progress, including its fail-SAFE rule (undeterminable means skip).
- RUN RECORDS ARE GITIGNORED (`.aw/records/runs/`) and absent from a lane worktree, which is the load-bearing objection to an `aw check` rule.
- THREE PENDING PLANS EDIT `selectors.py` (`76w6mq`, `xo3244`, `paw8so`). This plan must only CONSUME it.
- `tests/test_run_viewer.py` IS ENVIRONMENT-SENSITIVE (reads live repo state); paste its own summary line.
- Shared checkout, concurrent edits, suite runs BARE. Re-locate every symbol by name.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | the item's premise holds | Both functions are defined and consumed only in `run_viewer.py` and its tests; `doctor.py`, `check_engine.py` and `cli.py` reference neither, so `aw doctor` cannot see artifact drift. | `run_viewer.py:439`, `:465`, `:489`, `:1463`, `:2554`, `:2558`; grep of the three other modules |
| F-2 | HIGH | a lift-and-shift would spread a stale directory list | `find_artifact_file` hardcodes NINE dirs including a nonexistent `.aw/records/plans/archive` and two `.agents/` paths; the live tree has FIVE plans subdirs and the archive is weekly-sharded, which a fixed list cannot track. | `run_viewer.py:443-453`; `ls -d .aw/records/plans/*/` |
| F-3 | HIGH | and a first-match-wins reader with no collision policy | The loop returns the first `id6 in p.name` hit, while `selectors.resolve` calls an id6 multi-match "a data bug to fix, not overridable by --force". Consuming the loop would give `doctor` a silent arbitrary pick. | `run_viewer.py:456-461`; `selectors.py` `UNIQUE_KINDS` |
| F-4 | HIGH | liveness is why doctor cannot just call it | The predicate maps status onto an expected directory; a RUNNING step legitimately sits in `pending/` with a non-terminal status, so a liveness-blind rule flags every in-flight run. Three runs are live as this is authored. | `audit_step_artifact`'s status mapping; `tests/test_run_viewer.py:1285` |
| F-5 | MEDIUM | the one-implementation pattern is established | `render_stream` + a 28-pair AST refork guard, and `evaluate_review_finding_escalation`'s "cannot drift apart" docstring. An audit predicate belongs in that class. | `tests/test_runner_refork_guard.py`; `check_engine.py` |
| F-6 | MEDIUM | the resolver already does the hard part | `selectors._iter_paths` enumerates every type through one traversal, handles both roots, and recurses shards. | `selectors.py:397` |
| F-7 | MEDIUM | the `aw check` half has a load-bearing objection | The audit consumes a RUN's step status, and run records are gitignored and absent from a lane, so a fail-closed CI rule would answer differently in CI than locally. | `.aw/records/runs/` gitignored |
| F-8 | MEDIUM | substring versus exact is a real semantic change | The current loop substring-matches filenames, which also matches a review record carrying its SUBJECT's id6 (the documented review convention). The resolver reads the artifact's own declared `- Id:`. | the review-record convention; both readers measured |
| F-9 | LOW | three pending plans edit the resolver | `76w6mq`, `xo3244`, `paw8so` all declare `selectors.py`. This plan must consume, not modify, and must not declare it. | their `Scope-Paths` |
| F-10 | LOW | the run-viewer suite is environment-sensitive | It reads live repo state and its failures have been environmental in recent baselines, so its own summary line must be pasted separately. | recent baseline measurements |

## Proposed changes (ordered, validatable)

1. Characterize the four verdict shapes plus the live case at HEAD (E-01).
2. Move the predicate into a shared module, leaving `run_viewer` a consumer with no local copy (E-02).
3. Replace the private directory walk with `selectors`, fixing the shard and collision defects (E-03).
4. Consume it from `aw doctor`, liveness-aware, advisory, with a measured count behind the severity (E-04).
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

## Scope check

- Over-scope: none. One new module, one call-site conversion, one new consumer, two test modules.
- Scope-Paths justification: `agent_workflows/artifact_audit.py` is the new shared module E-02 creates; `agent_workflows/run_viewer.py` holds both functions today and becomes a consumer (E-02, E-03), and its three call sites must stay behavior-identical (E-06); `agent_workflows/doctor.py` is the new consumer (E-04, E-05); `tests/test_artifact_audit.py` is new and carries the shard, collision and in-flight fixtures; `tests/test_run_viewer.py` holds the existing characterization coverage E-01 extends and the byte-identical proof E-06 needs. `agent_workflows/selectors.py` is deliberately NOT declared: this plan CONSUMES the resolver and three other pending plans already edit that file, so declaring it would invite a collision at the finalize scope gate. If the executor concludes the resolver must change, that is a scope-widening finding to report, not to make.
- Under-scope, stated rather than left as `none`: this plan adds no `aw check` rule, changes no `aw runs` output, modifies no resolver, alters no audit verdict, does not fix the gitignored run-record architecture, sweeps no real discrepancy, and does not reach `aw attention`. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, both summary lines pasted and counts stated. Baseline on main 2026-09-08: `1 failed, 5648 passed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- `tests/test_run_viewer.py`'s OWN summary line pasted separately, because that module reads live repo state and its failures have been environmental in recent baselines.
- AN OBJECT-IDENTITY ASSERTION that `run_viewer`'s audit attribute IS the shared module's object, following the `test_runner_refork_guard.py` pattern; a behavioral comparison is insufficient because it passes against a duplicate.
- `aw runs` OUTPUT BYTE-IDENTICAL on a real recorded run, before and after.
- A WEEKLY-SHARDED ARCHIVE FIXTURE proving a plan under `<disposition>/YYYYMM/` is now FOUND, which the hardcoded list could not do.
- A COLLISION FIXTURE proving an id6 matching multiple artifacts yields the collision verdict rather than a silent first pick.
- AN IN-FLIGHT FIXTURE proving `aw doctor` reports NOTHING for a running step, plus the fail-safe case (liveness undeterminable -> no report).
- THE MEASURED FINDING COUNT on the live tree that justified E-04's chosen severity.
- `aw check all --agent` PER-RULE counts before and after, showing no rule's count changed (this plan adds no check rule).
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

THE SHARED MODULE'S DOCSTRING IS THE PRIMARY DOCUMENTATION and must state three things the next reader will otherwise re-derive: that it is the ONE implementation and both `aw runs` and `aw doctor` call it (the `evaluate_review_finding_escalation` wording is the model, since that docstring exists precisely to stop a second implementation); WHY it resolves through `selectors` rather than a private directory list, naming the shard and collision defects that motivated it; and WHY it is liveness-aware, because a future change that drops that guard would make the doctor rule fire on every in-flight run.

E-05's `aw check` DECISION belongs in that same docstring, including what would make the rejected option viable. A decision recorded only in a closed plan is a decision the next reader re-litigates.

`find_artifact_file`'s current docstring ("Search the repository for an artifact markdown file matching id6 or stem") describes a substring search. If E-03 changes the matching semantics to the resolver's declared-`- Id:` rule, that docstring becomes wrong and must move with the behavior.

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
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DELIBERATELY OPEN, because the item asks for `aw check` to be EVALUATED and the honest evaluation reaches a genuine obstacle rather than a preference. The audit's input is a RUN's recorded step status, and run records live under gitignored `.aw/records/runs/`, absent from a fresh clone and from a lane worktree. So the same commit would yield different `aw check` results in CI than locally, and `aw check` is fail-closed in CI. A gate whose verdict depends on untracked local state is not a gate. Against that stands the reasoning behind `k9awrq`: `aw check` is what agents and CI are pointed at, so a discrepancy invisible there is invisible in practice. The resolvable middle ground, which E-05 must record, is an audit keyed ONLY on tracked artifacts (does every plan's `- Status:` agree with its directory?), which needs no run record and would be a legitimate `aw check` rule; whether to build that is the maintainer's call and is NOT this plan's scope.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL passing output of the characterization tests at HEAD, before any extraction, and name which of the four verdict shapes each covers. Quote the LIVE-case assertion specifically, since that is the behavior the doctor consumer must inherit. Confirm in one sentence that no verdict was changed, and paste any wrong-looking verdict you recorded as a finding instead of fixing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new module's definition site and the import in `run_viewer.py`. Paste the OBJECT-IDENTITY assertion and its passing output (`run_viewer`'s attribute IS the shared object). Paste a search proving `run_viewer` holds NO local definition. State whether the signature takes primitive facts or a `StepSummary`, and if the latter, paste the written reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the resolver-consuming lookup and a search proving no hardcoded directory list remains. Paste the ACTUAL passing output of the weekly-sharded-archive fixture (a plan under `<disposition>/YYYYMM/` is found) and of the collision fixture (an id6 matching several artifacts yields the collision verdict, not a first pick). State which matching semantics you chose (substring versus declared `- Id:`) and why. Paste `git status --porcelain agent_workflows/selectors.py` proving it was NOT modified.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `aw doctor`'s new output on the live tree with the MEASURED finding count, and state the severity chosen and why that count justified it. Paste the in-flight fixture's result showing NO finding, and the fail-safe case (liveness undeterminable -> no report). Paste `aw runs` output before and after on a real recorded run, byte-identical.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the recorded `aw check` decision AS WRITTEN IN THE SHARED MODULE'S DOCSTRING, not merely in this plan. It must state the gitignored-run-record objection and what would make the rejected option viable. Paste `aw check all --agent` per-rule counts before and after, proving no rule was added.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the BARE `python3 -m pytest` summary lines before and after and state the failure-set delta explicitly. Paste `tests/test_run_viewer.py`'s OWN summary line separately, and if it differs from baseline say whether that is the known environmental sensitivity or a real regression. Re-paste the object-identity assertion, the two defect fixtures and the in-flight fixture as a single verification pass, and confirm no real discrepancy found by the new rule was "fixed" by moving another agent's artifact.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. OQ-03 (`aw check`) is open but subordinate: E-05 requires a RECORDED DECISION rather than an implementation, and the plan's value (one shared audit, two lookup defects fixed, doctor able to see drift) lands regardless of how the maintainer answers it.

IT CARRIES NO `Blocks-Release`, because backlog `onasuh` carries none. It is `Work-Kind: feature` at `Priority: medium` and the maintainer did not gate it; that is stated so a reader does not assume a gate was dropped.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A` and never push. Do NOT modify `agent_workflows/selectors.py`: three pending plans already edit it and this plan consumes it read-only. Do NOT change any audit verdict or any `aw runs` output. Do NOT move, rename or edit any real artifact the new doctor rule flags: four agents are graduating concurrently and several Sets are executing, so report a real discrepancy instead. Build every new case from FIXTURES, not from live run records, which are gitignored and absent from a lane. Re-locate every symbol by NAME rather than by the line numbers cited here. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the object-identity assertion and the in-flight fixture producing no finding.
