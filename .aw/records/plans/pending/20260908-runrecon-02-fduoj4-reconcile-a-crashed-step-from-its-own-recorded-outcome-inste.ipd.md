# IPD: Reconcile a crashed step from its own recorded outcome instead of guessing from the plan directory

- Date: 2026-09-08
- Kind: child
- Concern: When a driver dies mid-turn, the reconciler decides what happened from the plan's DIRECTORY and never reads the step's own `outcomes/<NN>-<id6>.json`, so a step that finished its work, recorded `substantially-complete`, and committed to a lane is written down as `interrupted`. MEASURED (backlog `ydbhfd`, 2026-09-02): `aw oc run e32j35 97df1z` was killed by a server and network reboot; `outcomes/02-97df1z.json` had ALREADY been written and records `"disposition": "substantially-complete"` with `"commits": ["209227d54f1fd7e34115ee9a198c74513a99567d"]` and a substantive summary ending "aw ipd lint --phase pre-transition reports conforming". Re-read at HEAD `44d4950d`: that file still says exactly that, and `state.json` now records `97df1z` as `interrupted` with `last_outcome: None`. The authoritative answer was on disk in the same run directory and was not consulted.
  THE READ-SIDE SYMPTOM IS FIXED AND THE WRITE-SIDE GAP IS NOT. Executed plan `ssk6nf` added the read-time liveness projection, so `aw runs` now shows `abandoned?` rather than a false `running` (`run_viewer.py:836-838`: `if status == "running" and holder == HOLDER_NONE:` -> `ABANDONED`), and its `aw runs repair` verb (`repair_run`, `:2357`) durably reconciles. Both work. What neither does is read the outcome file. The in-tree `REPAIR_HELP` text ADMITS this in the shipped product (`run_viewer.py:2350-2354`): "The decision reads the plan's DIRECTORY, not the step's own `outcomes/<NN>-<id6>.json`. A step that recorded `substantially-complete` with committed lane work is therefore reconciled to `interrupted`, which understates it. Tracked as backlog `ydbhfd`." So this plan closes a gap the product documents against this item by id.
  THE CORRECT READER ALREADY EXISTS IN THE SAME MODULE AND IS NOT CALLED. `reconcile_disposition` (`oc_runipd.py:5843`) reads `outcomes/<NN>-<id6>.json`, then combines it with the plan bucket in a documented precedence: bucket `executed` wins; otherwise a recorded `disposition` of `executed` is DOWNGRADED to `substantially-complete` (an agent self-claim is not trusted); otherwise a recorded disposition in `TERMINAL_STATES` minus `{dependency-blocked, not-attempted}` is honored; otherwise the exit code decides. `reconcile_interrupted` (`:6782`), which is what the crash path and `aw runs repair` both use, reads only the bucket: verified by inspection of its source, `'outcomes' in src` is `False` and `'reconcile_disposition' in src` is `False`. Two functions in one file answer the same question from different evidence.
  THE FUNCTION IS ALSO NOT SHARED. Measured: `agy.reconcile_interrupted is oc.reconcile_interrupted` -> `False`, and `agy.reconcile_disposition is oc.reconcile_disposition` -> `False`. So both are duplicated per host and a one-sided fix would leave the agy crash path guessing.
- Scope: Make the interrupted-step reconciler consult the step's own recorded outcome before falling back to the directory guess, on BOTH hosts, preserving every existing refusal, and surface the recorded commits so lane work is visible. EXCLUDES the write-side lock and signal-handler gap (spec `c4gd2h`, plans `2ouj70`/`71vjbn`); excludes `aw run resume`'s inability to read a driver run (sibling backlog `sv8z1e`, NOT this plan's); excludes the `aw runs repair` discoverability defect (unfiled, reported rather than fixed here); excludes any new mutating verb.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/run_viewer.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_run_viewer.py
- Item-Dependencies: none
- Status: to-review
- Set: runrecon
- Order: 2
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: fduoj4
- Blocks-Release: next
- From-Backlog: ydbhfd

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `ydbhfd`, which carries `- Blocks-Release: next`; this plan inherits that gate. The item's cross-links were unusually careful and every one CHECKED OUT on re-measurement, which is why this plan is narrow rather than narrowed. CONFIRMED at HEAD `44d4950d`: `run_viewer.py:836-838` is still the two-input dead-holder branch the item located (its cited `:766-770` has drifted to `:836-838`); `run_viewer` NEVER reads `outcomes/` anywhere, its only occurrence of that path being the `REPAIR_HELP` prose that documents this very gap and names `ydbhfd`; `reconcile_disposition` (`:5843`) DOES read the outcome file and applies a documented precedence; and `reconcile_interrupted` (`:6782`), the function `repair_run` delegates to, does not (verified by inspecting its source rather than by grep on the file). The item's claim that the repair verb resolved the immediate symptom also held: `state.json` now records `97df1z` as `interrupted`, and the outcome file still records `substantially-complete` with a commit sha, so the DESIGN gap the item describes is exactly what remains.
  TWO THINGS THE ITEM DID NOT SAY that change the work. FIRST, `reconcile_interrupted` and `reconcile_disposition` are BOTH duplicated per host and are NOT shared objects (measured `is` -> `False` for both pairs), so this is one behavior change applied twice plus a sharing decision, not a single-site edit. SECOND, and this is the constraint that shapes E-02: `reconcile_disposition`'s precedence is not arbitrary, it encodes an ANTI-FABRICATION rule (a recorded `disposition: executed` is DOWNGRADED to `substantially-complete` because an agent self-claim is not authority), and `reconcile_interrupted` carries a SEPARATE anti-fabrication gate of its own for the force-interrupted case (`runner_stop.is_indeterminate` -> refuse the promotion, record a `reconciliation_conflict`, cite spec `c4gd2h` R22). Consuming the outcome file must not weaken either, and the item's own instruction to report a recovered disposition "marked as recovered-from-outcome, not as if the driver had reported it cleanly" is the right shape for exactly that reason.
  THE ITEM'S OWN QUESTION 3 (read-time view versus durable write) IS ANSWERED BY SHIPPED PRECEDENT rather than left open: executed plan `ssk6nf` deliberately REJECTED auto-repair on read ("A read command must not mutate (GUIDING_PRINCIPLES P10); the durable fix is the opt-in verb in E-04"), and shipped the opt-in `aw runs repair` instead. So this plan improves the WRITE path that verb already uses and does NOT add a read-time mutation. Recorded as OQ-01 only because the item asked it, with the shipped answer cited.
  ITS QUESTION 4 (a supported verb to clean a stale lock) IS NOT GRADUATED: the lock and signal-handler half is spec `c4gd2h`'s and plans `2ouj70`/`71vjbn`', which the item itself says not to re-specify.

## Goal

Make a crashed step's reconciliation read the evidence the step already wrote, so finished work is not recorded as merely interrupted, without weakening either anti-fabrication gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: share the reconciler before changing it

- [ ] E-01 EXTRACT `reconcile_interrupted` INTO `runner_shared.py` AS ONE IMPLEMENTATION, before changing its behavior. Measured: `agy.reconcile_interrupted is oc.reconcile_interrupted` -> `False`, so there are two copies today and changing one would leave the agy crash path guessing.
  EXTRACT BEFORE EXTENDING, and the reason is this repository's own measured history: extending one copy is what makes two surfaces disagree, and the `render_stream` re-fork happened precisely because a shared symbol was later re-defined in the other driver with nothing noticing. Prove the extraction is behavior-neutral with the suite BEFORE E-02 touches it.
  SITE IT IN `runner_shared.py`, NEVER LEAVE IT IN `oc_runipd` FOR AGY TO IMPORT. `agy_runipd` already imports 47 names from `oc_runipd` (AST-measured 2026-09-08) and zero flow back; adding this to that list would make it 48 and deepen the layering defect backlog `cnwy8g` owns. Note `run_viewer.repair_run` currently reaches in via `from agent_workflows import oc_runipd` and calls `oc_runipd.reconcile_interrupted`; that import must be re-pointed too, or the repair verb keeps calling the old path.
  CHECK FOR A DIFFERENCE BEFORE ASSUMING A PURE MOVE. The two copies may not be byte-identical the way other duplicated pairs are. Diff them and report; if they differ behaviorally, say how and which behavior the shared version takes, rather than silently picking one.
  - Depends on: none
  - Expected outcome: one `reconcile_interrupted` in `runner_shared.py`; both hosts and `run_viewer.repair_run` call it; the diff between the two former copies reported; the suite green before any behavior change.
  - Execution state: pending

### Task group 2: consult the recorded outcome

- [ ] E-02 MAKE THE RECONCILER READ `outcomes/<NN>-<id6>.json` AND HONOR A RECORDED DISPOSITION, falling back to the current directory guess only when no outcome file exists, it is unparseable, or it carries no disposition. That fallback ordering is the item's requirement 2 and it preserves the honest guess for a step that really did die before producing anything.
  REUSE `reconcile_disposition`'s PRECEDENCE, DO NOT WRITE A SECOND ONE. It already encodes the answer (`oc_runipd.py:5843`): bucket `executed` wins; else a recorded `disposition == "executed"` is DOWNGRADED to `substantially-complete`; else a recorded disposition in `TERMINAL_STATES - {"dependency-blocked", "not-attempted"}` is honored; else the exit code decides. Note it is ALSO duplicated per host (`agy.reconcile_disposition is oc.reconcile_disposition` -> `False`), so decide whether to share it too or to extract just the precedence, and say why.
  THE DOWNGRADE IS NOT AN INCONVENIENCE, IT IS THE ANTI-FABRICATION RULE. An agent writing `disposition: executed` into its own outcome file is a self-claim, and this repository does not treat a self-claim as completion authority. If you find yourself removing that downgrade to make the measured case report `executed`, STOP: the measured case's outcome file says `substantially-complete`, which is honored WITHOUT any downgrade, so the item needs no relaxation of that rule.
  DO NOT WEAKEN THE FORCE-INTERRUPT REFUSAL. `reconcile_interrupted` already refuses to promote an item flagged `runner_stop.is_indeterminate`, records a `reconciliation_conflict`, emits an `interrupted-promotion-refused-unknown-outcome` event, and cites spec `c4gd2h` R22 in the message. An outcome file must NOT override that: a force-cut turn's own self-report is exactly the evidence R22 says the driver never established. Add the outcome consultation on the non-indeterminate path only, and pin the indeterminate path unchanged with a control test.
  MARK A RECOVERED DISPOSITION AS RECOVERED. The item requires it be reported "marked as recovered-from-outcome, not as if the driver had reported it cleanly", and that distinction is load-bearing: a driver-reported disposition was observed by the driver, a recovered one was read from a file the driver never validated. Record the provenance beside the value.
  - Depends on: E-01
  - Expected outcome: a recorded disposition is honored through the EXISTING precedence with no second implementation; the `executed` downgrade and the indeterminate refusal are both unchanged and pinned by control tests; a recovered disposition carries a recovered-from-outcome provenance marker.
  - Execution state: pending

- [ ] E-03 SURFACE THE RECORDED COMMITS so lane work is visible rather than something a human must go looking for. The item names this specifically, and the measured case is why: `outcomes/02-97df1z.json` records `"commits": ["209227d5..."]` and `"pushed": false`, and that sha is the only pointer to a lane holding a net-new module plus tests.
  DO NOT VALIDATE OR MERGE ANYTHING. Reporting a recorded sha is not the same as confirming it exists, and confirming a lane is mergeable belongs to the `integpath` Set (`rl67b0`'s `integrate` verb, `51vw4y`'s deferral ladder). If the sha cannot be resolved in the repository, report it as recorded-but-unresolved rather than dropping it or asserting it.
  - Depends on: E-02
  - Expected outcome: the recovered step's recorded commits are visible in the reconciliation output and in the run record; nothing is validated, merged, or resolved; an unresolvable sha is reported as such.
  - Execution state: pending

### Task group 3: the read surface, and proof

- [ ] E-04 MAKE THE `abandoned?` LABEL STOP APPEARING FOR A STEP WHOSE OUTCOME IS KNOWN, without turning a read into a write. `run_viewer.py:836-838` flips `running` -> `ABANDONED` on the two inputs it has (item status, lock holder) and never reads `outcomes/`; its only reference to that path is the `REPAIR_HELP` prose documenting this gap.
  A READ MUST NOT MUTATE, and that is settled precedent rather than a preference: executed plan `ssk6nf` explicitly REJECTED auto-repair on read, citing `GUIDING_PRINCIPLES` P10, and shipped the opt-in `aw runs repair` verb instead. So the read surface may report a BETTER-INFORMED label derived from the outcome file, or may keep `abandoned?` and point at the repair verb, but it may NOT reconcile on read. Decide which, and record the decision with the P10 citation.
  IF YOU CHANGE THE LABEL, UPDATE `REPAIR_HELP`'s LIMITATION PARAGRAPH. It currently states the limitation as fact and names `ydbhfd`; leaving it after fixing the limitation would make the shipped help text lie. That paragraph is at `run_viewer.py:2350-2354`.
  - Depends on: E-03
  - Expected outcome: the read surface either reports a better-informed label or points at the repair verb, with the decision and its P10 basis recorded; no read-time mutation; `REPAIR_HELP`'s limitation paragraph corrected if the limitation is gone.
  - Execution state: pending

- [ ] E-05 PROVE IT ON THE MEASURED CASE AND ON THE FALLBACKS, FROM FIXTURES. `.aw/records/runs/` is gitignored and roughly 32 tests fail inside a lane worktree because several read live run state, so a test built on the live corpus passes here and fails in isolation. `tests/test_run_viewer.py` is one of the modules affected.
  BUILD THE FIXTURE FROM THE REAL MEASURED SHAPE: a queue item stuck at `running` with `last_outcome: None`, a dead lock holder, and an `outcomes/<NN>-<id6>.json` carrying `disposition: substantially-complete` plus a `commits` list. That is the exact shape of the incident, and a fixture that simplifies it away stops testing the defect.
  COVER ALL FOUR FALLBACK BRANCHES, since the item's requirement 2 is specifically about them: no outcome file, unparseable outcome file, outcome file with no `disposition` key, and outcome file with a disposition the precedence does not honor. Each must yield the current `interrupted` guess, unchanged.
  ADD THE TWO CONTROL TESTS that prove nothing was relaxed: an outcome file claiming `disposition: executed` must still be recorded `substantially-complete` (the anti-fabrication downgrade), and an item flagged indeterminate must STILL be refused even when its outcome file claims success (spec `c4gd2h` R22). These two are the load-bearing half of E-05.
  - Depends on: E-04
  - Expected outcome: a fixture reproducing the measured shape; all four fallback branches asserted unchanged; both anti-fabrication control tests passing; no test reads the gitignored live run tree.
  - Execution state: pending

- [ ] E-06 PIN THE SHARING SYMMETRICALLY AND MUTATION-CHECK IT. Register the extracted symbol in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE` with BOTH runners listed, which its `test_the_table_covers_both_runners` already enforces, and assert object identity across `oc_runipd`, `agy_runipd`, `runner_shared` and the `run_viewer` call path.
  GREP IS NOT EVIDENCE OF SHARING. It cannot distinguish a shared object from a textually identical copy, which is how `render_stream` was re-forked; the one-sided versions of this guard were RETIRED for that reason. Mutation-check: define a local copy in `agy_runipd`, show the guard FAILS, revert, show it passes.
  - Depends on: E-01, E-05
  - Expected outcome: a `REFORK_TABLE` row covering both runners; object identity asserted across all four call paths; the guard demonstrated to fail under a re-fork mutation; the AST-measured oc-to-agy import count unchanged at 47 or lower.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A READ COMMAND MUST NOT MUTATE. `GUIDING_PRINCIPLES` P10, applied deliberately by executed plan `ssk6nf`, which rejected auto-repair on read and shipped the opt-in `aw runs repair` verb instead. Its own `repair_run` (`run_viewer.py:2357`) refuses while a live driver holds the run and refuses when it cannot PROVE no driver holds it (flock unavailable), which is the fail-closed posture to preserve.
- THE ANTI-FABRICATION RULES ARE TWO, NOT ONE, AND BOTH ARE IN THE PATH THIS PLAN EDITS. `reconcile_disposition` DOWNGRADES a self-claimed `executed` to `substantially-complete` because an agent's self-report is not authority. `reconcile_interrupted` REFUSES to promote a force-interrupted item even when the plan sits in `executed/`, records a `reconciliation_conflict`, and cites spec `c4gd2h` R22 in its message. Neither may be weakened to make a case report better.
- THE CORRECT READER IS ALREADY IN THE FILE. `reconcile_disposition` (`oc_runipd.py:5843`) reads the outcome file and applies a documented precedence; `reconcile_interrupted` (`:6782`) does not (verified by inspecting its source). This is a wiring gap between two functions in one module.
- BOTH FUNCTIONS ARE DUPLICATED PER HOST AND ARE NOT SHARED OBJECTS (measured `is` -> `False` for both pairs), so a one-sided fix leaves the agy crash path guessing.
- THE SHIPPED HELP TEXT ALREADY DOCUMENTS THIS GAP AND NAMES THE ITEM (`run_viewer.py:2350-2354`), so fixing it obliges correcting that paragraph.
- THE IMPORT DIRECTION IS ONE-WAY: `agy_runipd` imports 47 names from `oc_runipd`; `oc_runipd` imports zero from agy. Shared symbols go in `runner_shared`. Note `run_viewer` reaches into `oc_runipd` for the reconciler today, so it is a third caller to re-point.
- `.aw/records/runs/` IS GITIGNORED, and `tests/test_run_viewer.py` is among the modules that suffer when a test reads live run state. Use fixtures.
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals; a bare run on main is `1 failed, 5648 passed` (the known `tests/test_orchestrator_retirement.py` failure, which reads live plan statuses).

## Findings

| Id | Severity | Location (measured at HEAD `44d4950d`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `oc_runipd.py:6782`, `agy_runipd.py:4053` | `reconcile_interrupted` decides from the plan DIRECTORY only; it never reads `outcomes/<NN>-<id6>.json`. Inspected its source: `'outcomes' in src` is `False`, `'reconcile_disposition' in src` is `False`. | `inspect.getsource` on the live function |
| F-2 | HIGH | `oc_runipd.py:5843` | `reconcile_disposition` in the SAME module already reads the outcome file and applies a documented precedence, including the anti-fabrication downgrade of a self-claimed `executed`. So two functions answer one question from different evidence. | source read |
| F-3 | HIGH | run `run-20260902T013603Z-1758564` | The measured case is still on disk and still divergent: `outcomes/02-97df1z.json` records `substantially-complete` with `commits: ["209227d5..."]`, while `state.json` records the step as `interrupted` with `last_outcome: None`. | re-read both files at HEAD |
| F-4 | HIGH | measured | Neither function is shared: `agy.reconcile_interrupted is oc.reconcile_interrupted` -> `False`; same for `reconcile_disposition`. A one-sided fix leaves the agy crash path guessing. | `python3 -c` identity check |
| F-5 | MED | `run_viewer.py:836-838` | The `abandoned?` projection has exactly two inputs (item status, lock holder) and never consults `outcomes/`. `run_viewer`'s ONLY occurrence of that path is the help text documenting this gap. | source read; grep for `outcomes` in the module returns one hit, in prose |
| F-6 | MED | `run_viewer.py:2350-2354` | The shipped `REPAIR_HELP` states the limitation as fact and names backlog `ydbhfd`, so fixing it obliges correcting the help text or the product ships a false statement. | source read |
| F-7 | MED | `oc_runipd.py:6817-6840` | `reconcile_interrupted` already carries its own anti-fabrication gate for the force-interrupted case, citing spec `c4gd2h` R22, and it must survive the change. | source read |
| F-8 | LOW | `run_viewer.py:2408` | `aw runs repair` is routed from a magic first POSITIONAL token rather than a subparser, so `aw runs --help` cannot list it; the code documents this as deliberate (every READ path stays side-effect free) and handles `repair --help` by hand. The item notes it as a small unfiled discoverability defect. NOT graduated here. | source read |
| F-9 | CONFIRMED-NOT-DUPLICATE | executed plan `ssk6nf` | `ssk6nf` fixed the READ-side false `running` and deliberately stopped there, rejecting auto-repair on read on `GUIDING_PRINCIPLES` P10 grounds. It never consults the outcome file, so this item's subject is genuinely not covered by it. | read that plan's deferred section |

## Proposed changes (ordered, validatable)

1. E-01 extracts `reconcile_interrupted` into `runner_shared` as ONE implementation and re-points all three callers, proving behavior-neutrality first.
2. E-02 makes it consult the recorded outcome through `reconcile_disposition`'s EXISTING precedence, on the non-indeterminate path only, marking a recovered value as recovered.
3. E-03 surfaces the recorded commits without validating or merging anything.
4. E-04 decides the read-surface treatment within the no-mutation rule and corrects the help text if the limitation is gone.
5. E-05 proves the measured case, all four fallbacks, and both anti-fabrication controls, from fixtures.
6. E-06 pins the sharing symmetrically and mutation-checks the guard.

## Deferred / out of scope (with reason)

- THE WRITE-SIDE LOCK AND SIGNAL-HANDLER GAP (no SIGINT/SIGTERM handler, `run_lock` never unlinks, so a dead PID stays readable). Owned by spec `c4gd2h` and plans `2ouj70`/`71vjbn`, and the backlog item explicitly says "Do not re-specify it here". This plan improves what is inferred from a stale lock; it does not change the lock.
- `aw run resume` CANNOT READ A DRIVER RUN AT ALL (it reads `ledger.jsonl` while the drivers write `events.jsonl`). Sibling backlog `sv8z1e`, same Set, NOT this plan's and NOT touched. That item covers the missing ACTION; this one covers the wrong FACTS. Independent; either can land first.
- A SUPPORTED VERB TO CLEAN A STALE `driver.lock`. The item's question 4. Not graduated: it belongs with the lock ownership above, and `repair_run` deliberately "does NOT delete the stale `driver.lock`" today, which is a stated choice rather than an oversight.
- AUTO-REPAIR ON READ. Rejected by shipped precedent (`ssk6nf`, `GUIDING_PRINCIPLES` P10), not by this plan's preference.
- THE `aw runs repair` DISCOVERABILITY DEFECT (F-8): routed from a magic positional token so `aw runs --help` cannot list it. The item notes it as small, separate and unfiled. Reported rather than fixed, because changing it means adding a subparser to a surface deliberately kept side-effect-free, which is a different decision.
- VALIDATING OR MERGING THE RECOVERED LANE. The `integpath` Set owns integration (`rl67b0`'s `integrate` verb, `51vw4y`'s deferral ladder, `29wvmj`'s executed-transition gate). This plan reports a recorded sha; it does not act on it.
- RELAXING EITHER ANTI-FABRICATION RULE. Named in the fence because it is the tempting shortcut: the measured case needs NEITHER relaxation, since its outcome file already says `substantially-complete`.

## Scope check

- Over-scope: `run_viewer.py` is in scope ONLY for the read-surface decision (E-04) and the help-text correction. Do NOT add a mutating path to it, do NOT change `repair_run`'s refusals, and do NOT restructure the `repair` routing. Do NOT edit `runner_stop.py` or the lock.
- Under-scope: stated rather than left as `none`. After this plan a crashed step reports its own recorded disposition and commits, but the lane is not merged, `aw run resume` still cannot read a driver run (`sv8z1e`), the stale lock still requires no supported cleanup verb, and `aw runs repair` is still undiscoverable from `--help`. Each is named above with its owner.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. Fixtures for every run shape; never the gitignored live tree, which is specifically what makes `tests/test_run_viewer.py` fragile in a lane. The two anti-fabrication control tests are mandatory, not optional: without them a reviewer cannot tell a correct fix from a relaxed gate.

## Spec / documentation sync

TWO documents are implicated and NEITHER is amended by this plan, so no spec file is declared in `- Scope-Paths:`.
FIRST, spec `c4gd2h` (`.aw/records/specs/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md`) owns the graceful-quit lifecycle and its R22 forbids fabricating a disposition. This plan CONSUMES that rule and strengthens compliance with it by reading real evidence instead of guessing; it must not edit the spec. If the reading shows R22 is read as forbidding the recovered-from-outcome path entirely, STOP and report to the maintainer rather than proceeding, because that would make the item's own requirement 1 unimplementable as written.
SECOND, the shipped `REPAIR_HELP` string (`run_viewer.py:2350-2354`) is user-facing documentation that currently asserts the limitation this plan removes and cites `ydbhfd` by id. E-04 obliges correcting it. That is a documentation change inside a source file rather than a spec amendment, and the corrected text must be written in plain prose without em or en dashes, per the user-facing-prose rule.
Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Read-time view or durable write?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY SHIPPED PRECEDENT, recorded rather than re-litigated because the backlog item asked it as its question 3. Executed plan `ssk6nf` explicitly rejected auto-repair on read, citing `GUIDING_PRINCIPLES` P10 ("A read command must not mutate"), and shipped the opt-in `aw runs repair` verb as the durable fix. THEREFORE this plan improves the WRITE path that verb already uses (E-01 through E-03) and gives the READ path only a better-informed label or a pointer to the verb (E-04), never a mutation. The item's own worry that "a read-time view leaves `state.json` permanently claiming `running`" is already addressed by the existence of the repair verb; what was missing was the verb reading the right evidence.

### OQ-02: Should `reconcile_disposition` be shared too, or only its precedence extracted?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-02 requires the EXISTING precedence be reused rather than reimplemented either way, so the plan is executable under both answers. The question is a real trade-off measured rather than guessed: `reconcile_disposition` is also duplicated per host (`is` -> `False`) and is a much larger function with a deliberate-stop branch, a review branch, and the exit-code fallback, so sharing it wholesale is a bigger change than this plan's subject and touches paths (the review branch, the stop branch) that other pending Sets are editing. Extracting only the outcome-precedence portion is smaller and sufficient. Decide from the diff between the two copies and record the reason; do not share it wholesale merely because it is nearby.

### OQ-03: Does a recovered disposition change the run's exit code or aggregate verdict?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer for the operational preference
- Resolution or deferral rationale: NOT blocking, because the item's subject is the RECORD being wrong and fixing the record is complete without touching an exit code, so the plan stands either way. The question exists because reconciliation runs inside `run_queue` on resume (`reconcile_interrupted` is called there), and a step whose status changes from `interrupted` to `substantially-complete` becomes a member of `EXECUTION_SUCCESS_STATES`, which feeds dependency satisfaction and the run's exit code. That is a real consequence and could make a resumed run report success it previously did not. The conservative answer is to change the recorded disposition and NOT the aggregate verdict in the same plan, and to state the interaction explicitly so a maintainer can decide. Measure which readers of the item status are reached before answering.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the extracted function's location in `runner_shared.py`. Paste a `python3 -c` showing `oc_runipd`, `agy_runipd` and the `run_viewer` call path all resolve it to the SAME object. Paste the DIFF between the two former copies and state whether they differed behaviorally and which behavior the shared version took. Paste the suite green BEFORE any behavior change, demonstrating the extraction alone changed nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the reconciliation of the MEASURED shape (item at `running`, dead holder, outcome file recording `substantially-complete` with a commit sha), showing the recorded disposition honored and the recovered-from-outcome provenance marker present. Paste proof no second precedence was written (show the CALL into the existing one, not a similar expression). Paste the TWO control tests: a self-claimed `executed` still downgraded to `substantially-complete`, and an indeterminate item STILL refused with its `reconciliation_conflict` and R22 citation intact, even with an outcome file claiming success. Those two are the load-bearing half.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the reconciliation output showing the recorded commits, and the run record field carrying them. Paste the unresolvable-sha case showing it is reported as recorded-but-unresolved. Paste proof nothing was validated or merged (no git merge, checkout, or ref write in the changed code; show the absence).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: state the read-surface decision and paste the code. Paste `aw runs` output for the measured run BEFORE and AFTER, showing what the label now says. Paste proof the read path performs NO write (assert `state.json`'s mtime and content are unchanged across a read, not merely that no write was intended). Paste the corrected `REPAIR_HELP` paragraph, or state why the limitation still stands. Confirm the corrected text contains no em or en dashes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the fixture and the tests with their actual runner output. Paste ALL FOUR fallback branches (no outcome file, unparseable, no `disposition` key, unhonored disposition) each yielding the unchanged `interrupted` guess. Paste proof no test reads `.aw/records/runs/`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the new `REFORK_TABLE` row showing BOTH runners, and `tests/test_runner_refork_guard.py` passing. Paste object-identity output across all four call paths. Paste the MUTATION CHECK in full: define a local copy in `agy_runipd`, paste the FAILING guard output, revert, paste the passing output. Paste the AST-measured oc-to-agy import count before and after, showing it did not increase from 47.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the seven paths in `- Scope-Paths:`. Do NOT weaken the self-claimed-`executed` downgrade. Do NOT weaken the force-interrupt refusal or its R22 citation. Do NOT add a read-time mutation. Do NOT change `repair_run`'s refusals or restructure the `repair` routing. Do NOT edit `runner_stop.py`, the lock, or the signal handlers. Do NOT touch sibling backlog `sv8z1e`'s subject (`aw run resume`). Do NOT validate, merge, or act on a recovered lane. Do NOT edit spec `c4gd2h` or spec `25kzda`, and never the latter's §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. `oc_runipd.py`, `agy_runipd.py` and `run_viewer.py` are being edited by live runs; measured, the two drivers' line numbers moved roughly 70 and 95 lines in a single day, and the backlog item's own `run_viewer` citation had already drifted from `:766-770` to `:836-838`. Find `reconcile_interrupted`, `reconcile_disposition`, `repair_run`, `driver_holder_state`, `REPAIR_HELP`, and `runner_stop.is_indeterminate` by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved fduoj4 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. ON COMPLETION, close backlog `ydbhfd`, which this plan carries as `- From-Backlog:` and whose `- Blocks-Release: next` gate it inherits. Do NOT close sibling `sv8z1e`: it is a different defect, owned by another agent's lane in this shared checkout.
