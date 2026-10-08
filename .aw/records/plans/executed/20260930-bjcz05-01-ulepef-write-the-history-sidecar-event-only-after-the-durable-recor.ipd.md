# IPD: Write the history sidecar event only after the durable record it claims, closing the surviving half of the phantom-event defect

- Date: 2026-09-30
- Kind: child
- Concern: Approved spec `artifact-metadata-storage` (`2vev8j`) binds C5: "No writer may record an event for a transition that did not happen". Four writers still break it, and NOT in the shape the backlog item describes. `backlog.run_set`, `backlog.run_note`, `specs.run_set` and `specs.run_note` each append the advisory `record_history` event BEFORE the `artifact_core.atomic_write` (or `git_mv` plus `atomic_write`) that makes the transition real, so when that write fails the sidecar keeps an event for a transition that did not happen, the artifact on disk still carries its old status, and `aw record-history <id6>` reports the phantom to an operator as fact. Measured on this tree with an unwritable destination directory and no monkeypatching: `aw backlog set --status graduated` raises `PermissionError`, the item stays `- Status: open` in `open/`, and the sidecar holds `{"id6": "bk0008", ..., "message": "status -> graduated"}`; `aw record-history bk0008` then prints `- 20260930 [backlog] aw backlog set (aw backlog): status -> graduated` and exits 0. The item's OWN two stated halves (append before the close-legitimacy gate, append before the dry-run branch, and specs appending before validation) are ALREADY FIXED by commit `23ec426df` and are re-measured here as closed; the item anticipated this and instructed re-measurement rather than assumption.
- Scope: IN: move the advisory append AFTER the durable write it describes at all four reachable pre-write call sites (`backlog.run_set`, `backlog.run_note`, `specs.run_set` via `_sidecar_append`, `specs.run_note` via `_sidecar_append`), so a failed durable write leaves no event; a new behavioral test module driving each of the four verbs through a real CLI invocation whose durable write fails, asserting no sidecar record and the artifact unchanged, plus the converse that a SUCCEEDING write still records exactly one event; a correction to the four in-module comments that currently justify the placement on advisory grounds without addressing ordering; an amendment to spec `2vev8j` Section 7's second bullet, which states the defect in its already-fixed shape and is the authority a future author would read; and one CHANGELOG entry. OUT, each with a reason recorded under "Deferred": `backlog.run_new`, which already appends AFTER its write and is correct; `status_set.apply_status_change`, which writes NO sidecar record at all (that asymmetry is item `fcnz1r`'s, and `47ttnv` deliberately left it); C5's SECOND clause ("no status change may succeed while its durable history write silently fails"), which OQ-01 resolves from the spec's own text as binding the future tracked journal rather than today's gitignored sidecar, and which would contradict the maintainer's 2026-09-10 `vhbvwz` OQ-01 ruling recorded verbatim at `record_history.append_advisory` if applied to the sidecar; the per-artifact journal, `seq` ordering and locking that `2vev8j` specifies (this plan fixes ordering within TODAY's global sidecar and does not begin that migration); the uncaught `OSError` propagating out of `cli.main` on a failed artifact write, which is a separate robustness defect this plan measured and must not absorb; the history DATE-CLOCK skew between the two writers; and closing release-blocking item `19lmbe`, whose defect commit `23ec426df` fixed but which is still `open`.
- Scope-Paths: agent_workflows/backlog.py, agent_workflows/specs.py, tests/test_history_write_order.py, .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: bjcz05
- From-Spec: 2vev8j
- Blocks-Release: next
- Set: bjcz05
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ulepef

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ulepef verified (set bjcz05, attempt 1).
- 2026-10-01 approved (aw set): status set to approved

- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-801 (HIGH), PR-802 (HIGH), PR-803 (MEDIUM), PR-804 (MEDIUM), PR-805 (MEDIUM), PR-806 (LOW), PR-807 (LOW), PR-808 (LOW), PR-809 (LOW) all FIXED; zero deferred, zero open. Structural lint `conforming` at `--phase author` (one `IPD-Z602` density advisory on E-02, unassessed by the plan, now assessed and accepted in the Scope check) and at `--phase review-finalize`. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator row check does not apply. No production file, test, document or spec was modified by this review; four throwaway probe repositories were created under `.aw/state/tmp/` and deleted, and `git status --porcelain` is clean of them.
  THE DEFECT IS REAL, OPERATOR-VISIBLE, AND EVERY CENTRAL MEASUREMENT REPRODUCES INDEPENDENTLY. F-01: both halves the backlog item states ARE already fixed, re-confirmed by AST (`backlog.run_set` orders gate 1655, dry-run 1684, append 1697; `specs.run_set` orders validate 831, dry-run 857, append 867). F-02/F-03: all four surviving sites are append-before-write and all four phantom events reproduce through the shipped path with no monkeypatching, including both `run_note` verbs where the inline record is measurably ABSENT while the sidecar holds it. F-04: `aw record-history bk0004` printed `- 20261001 [backlog] aw backlog set (aw backlog): probe` and exited **0** while the item on disk still read `- Status: open`, which is the user-visible false record that justifies `bug` and the inherited `- Blocks-Release: next`. F-06: a five-character fixture id really does yield a silent false negative, with the `ValueError` warning reproduced verbatim. F-10: `run_new` is already write-then-append. OQ-01's resolution checks out in all four cited places (C5 line 88, C2 line 82, 4.2 line 161, E4 line 74 citing `.aw/.gitignore:11`, AC-7 saying "the JOURNAL write"), as does the `vhbvwz` ruling quoted from `record_history.append_advisory` and the `check_engine._CARRIER_TARGET_TYPES` value `('backlog', 'plans')`.
  TWO HIGH FINDINGS WERE CLAIMS AN EXECUTOR WOULD HAVE ACTED ON AND COULD NOT HAVE SATISFIED. PR-801: the specs moving case does NOT fail at `atomic_write` after a successful `git_mv`, as F-02, E-03, E-06 and V-03 all asserted. Instrumenting both functions and driving the real CLI traces `[('git_mv', 'RAISED PermissionError')]` with `atomic_write` NEVER REACHED, because `core.git_mv` falls back to `shutil.move` and that copy into the unwritable destination is what raises; with the destination writable the same probe traces `[('git_mv','OK'),('atomic_write','OK')]`. The defect and the fix are unaffected (the phantom event and the partial state both reproduce), but E-06 and V-03 demanded evidence of a state the prescribed probe cannot produce, so an honest executor would have been stuck. E-03 now states the placement positionally (after the whole `if moving: / else:` construct, exactly once) and all three items are forbidden from asserting the unmeasured half. PR-802: `aw specs note` accepts NO `--dir`, so the obvious fixture exits 2 on `unrecognized arguments`, writes no sidecar, and makes a failure case go GREEN without reaching the code under test, the same class of silent false negative the plan already guards against for id6 (F-06); E-06 now names it and requires that verb's success case to assert sidecar CONTENT.
  THREE MEDIUM FINDINGS. PR-803: the failure cases cannot assert an exit code, because F-11's uncaught `PermissionError` means `cli.main` RAISES; E-06 now requires `pytest.raises(OSError)` so the tests do not depend on a fix this plan deliberately defers. PR-804: the gate carried no scope fence; added as a DECLARATION with the three genuine stop conditions preserved, and the lifecycle paragraph now names `aw ipd finalize` with conditional runner ownership and records that `bjcz05` is already `graduated`. PR-805: E-02's and E-03's moves are each guarded (`if item.id:`, `if dest.resolve() != src.resolve():`, `if moving:`), so "move the call" was underspecified in a way that permits a half-made move; both items now say which block moves and where.
  FOUR LOW FINDINGS. PR-806: F-09's baseline is not reproducible (`3887 passed, 2 skipped`, zero failures, the authored date-skew failure PASSING because that test now normalizes history dates with `_DATE.sub` and records the skew as `fnb8pl` in a comment), and the authored `3487` differs from the measured `3887` by 400; the bar is now a by-name failure-set comparison and the gate paragraph no longer promises a non-green baseline. PR-807: F-08 drifted, with `8rsxy1`, `f7igdu` and `jbipfa` now in `executed/` and three statuses moved; the row is refreshed, and its central prediction is now PROVEN rather than predicted, since `jbipfa` landed in the same function (commit `da04c5cf0`) and left the append's position untouched. PR-808: F-07's grep claim named `test_history_provenance.py` as matching `history.jsonl`, which it does not (it reaches the sidecar through the API and by monkeypatching); corrected, conclusion unchanged. PR-809: the `IPD-Z602` advisory on E-02 was unassessed; now assessed and accepted with the reason recorded.
  Findings and one Decisions row in `.aw/records/reviews/20260930-bjcz05-01-ulepef-write-the-history-sidecar-event-only-after-the-durable-recor.review.md`.
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `bjcz05`. EVERY figure below was measured in this lane at HEAD `596fae9ef`, and the item's two stated halves BOTH measured ALREADY FIXED, which changes this plan's subject rather than its existence. The item says `backlog.run_set` appends before its `evaluate_blocking_close` gate and before the dry-run branch, and that `specs` appends before validating; measured, the order in `backlog.run_set` is gate, then dry-run, then append, and in `specs.run_set` it is validate, then dry-run, then append (F-01). Commit `23ec426df` made both changes on 2026-09-26 while fixing the `--dry-run` defect item `19lmbe` describes. The item's own text anticipated exactly this ("Confirm both against the current tree before fixing ... the exact reachable shape needs re-measuring rather than assuming"), so this is the expected case and not a reason to retire the item: a DIFFERENT and strictly worse C5 violation survives at four call sites, measured with no monkeypatching, and one of them (`run_note` on both trees) was never touched by that commit (F-02, F-03). The quoted spec prose in the item and in `47ttnv`'s Deferred row is therefore stale, which is why E-05 amends it: leaving it is how this item came to be filed against a fixed defect. GATE NOTE: item `bjcz05` carries `- Blocks-Release: next` and this plan inherits it unchanged. The reordering was PROVEN SUFFICIENT at authoring by emulating the post-fix ordering at runtime over all four verbs (F-05), so this plan is not proposing an untested remedy. C5's second clause is deliberately NOT implemented and is raised as BLOCKING OQ-01, because it contradicts a recorded maintainer ruling and only the maintainer can reconcile the two.

## Goal

Make the history sidecar incapable of recording a transition that did not happen, by writing its event only after the durable write that makes the transition real.

The deliverable is an ORDERING change at four call sites plus the first test coverage of this direction. Today's tests cover only the converse failure (the sidecar fails and the durable record must survive, `tests/test_history_provenance.py::SidecarFailureIsReportedTests`); nothing covers the sidecar succeeding while the durable write fails, which is the direction that manufactures a false record. After this plan a failed `backlog set`, `backlog note`, `specs set` or `specs note` leaves the sidecar byte-unchanged, while a successful one still records exactly one event, so spec `2vev8j`'s C5 first clause holds on the writers this plan touches.

Secondarily, and stated plainly because it is what let this defect be mis-filed: correct the authority. Spec `2vev8j` Section 7 describes the defect in a shape that no longer exists, and that stale sentence is what backlog item `bjcz05` was filed from and what plan `47ttnv` quoted forward as current. Amending it is cheaper than the next author re-measuring it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before changing anything

- [x] E-01 RE-MEASURE THE FOUR CALL SITES AND THE ALREADY-FIXED HALVES BEFORE EDITING, because this plan's whole premise is that a recorded figure rotted and the same rot can bite between authoring and execution. Record raw output for each of: (a) the ORDER of the advisory append relative to the durable write in each of `backlog.run_set`, `backlog.run_note`, `specs.run_set` and `specs.run_note`, by symbol, confirming the append still precedes the write in all four; (b) that `backlog.run_new` already appends AFTER its `core.atomic_write` and is therefore not in scope; (c) that a refused blocking close under `--dry-run` writes no sidecar record and that a plain `--dry-run` writes none either, i.e. the item's first stated half is still fixed; (d) that a `specs set` refused by `validate_spec` writes no sidecar record, i.e. the item's second stated half is still fixed; (e) that `status_set` writes no sidecar record at all, by confirming the module contains no `record_history` call. IF ANY MEASUREMENT HAS MOVED, use the new one, say so explicitly, and state whether the plan's shape still holds; do NOT adjust the argument, which depends on the ordering and not on the particular line numbers.
  - Depends on: none
  - Expected outcome: five measurements recorded with the command or symbol reference that produced each, plus an explicit statement per measurement of whether it matches the authoring finding, and if not, whether this plan's scope still holds.
  - Execution state: performed

### Task group 2: fix the order

- [x] E-02 REORDER THE TWO BACKLOG CALL SITES so the advisory append follows the durable write it describes. In `backlog.run_set`, the append currently sits between the dry-run early return and `core.atomic_write(dest, rendered)`; move it to AFTER that write and after the `src.unlink()` that completes the move, so the event is written only once the item genuinely occupies its new status and location. TWO MECHANICAL DETAILS, so the move is not half-made: the append is wrapped in an `if item.id:` guard, so the WHOLE guarded block moves rather than just the call, and the `src.unlink()` is itself inside an `if dest.resolve() != src.resolve():` guard (a same-directory status change does not unlink), so "after the unlink" means after that conditional block and not inside it. In `backlog.run_note`, the append currently precedes the `core.atomic_write(src, ...)` that adds the inline record; move it after, again moving the whole `if item.id:` block. PRESERVE THE ADVISORY CONTRACT EXACTLY: the append's return value must still be ignored, a failure must still only warn, and the durable write must still not depend on it in either direction, because the 2026-09-10 `vhbvwz` OQ-01 ruling recorded at `record_history.append_advisory` makes the sidecar a machine-local activity log that may never gate a durable write. This change makes the sidecar depend on the durable write, which is the permitted direction; it must NOT introduce the reverse dependency. Keep the message, `id6`, `tree`, `workflow`, `actor` and `artifact` arguments byte-identical, so no record's CONTENT changes and only its timing does. DO NOT change the dry-run branch, the `evaluate_blocking_close` gate, `_reattach_history`, or any status or placement logic.
  - Depends on: E-01
  - Expected outcome: in both `backlog.run_set` and `backlog.run_note` the `record_history.append_advisory` call follows the `core.atomic_write` for that verb, with every argument unchanged, and a failed append still only warns.
  - Execution state: performed

- [x] E-03 REORDER THE TWO SPECS CALL SITES, which differ from backlog in one way that must be handled deliberately. `specs.run_set` already DEFERS its message into a `sidecar_msg` local (that deferral is what commit `23ec426df` introduced to get the append past validation and past the dry-run branch), so the fix is to move the `_sidecar_append(repo_root, new_text, sidecar_msg)` call from before the write to after it. THE MOVING CASE IS WHAT MAKES THIS MORE THAN A ONE-LINE MOVE, and the rule is positional rather than keyed to any one call: when the spec changes status directory, `run_set` runs `dest_path.parent.mkdir(...)`, then `core.git_mv`, then `core.atomic_write(dest_path, new_text)`, so the append must follow the LAST durable step ON WHATEVER BRANCH IS TAKEN, meaning after the `atomic_write` inside the `if moving:` block and after the `atomic_write` in the `else:` block. Place it AFTER the whole `if moving: / else:` construct, once, so neither branch can be left behind and the two cannot drift; do NOT duplicate the call into both branches.
    WHICH CALL ACTUALLY FAILS IS NOT WHAT THE PLAN ORIGINALLY STATED, AND AN EXECUTOR MUST NOT REASON FROM THE OLD CLAIM (F-13, measured at review). Authoring recorded the partial state as "`git_mv` succeeded and `atomic_write` failed". Re-measured by instrumenting both functions and driving the real CLI with the destination directory `chmod 500`: the trace is `[('git_mv', 'RAISED PermissionError')]` and `atomic_write` IS NEVER REACHED, because `core.git_mv` falls back to `shutil.move` when `git mv` fails and `shutil.move` copies into the unwritable destination itself. So the measured failure is a FAILED `git_mv`, not a `git_mv`-then-failed-`atomic_write`. This does NOT change the fix (the append still precedes every durable step and still leaves a phantom event, which was re-measured: the sidecar held `"to-review: m"` while the file stayed in `draft/` and the destination stayed empty) and it does not change where the call goes. It DOES change what E-06 and V-03 may claim: a `chmod`-based probe cannot demonstrate a half-completed move, so neither item may assert that `git_mv` succeeded. Whether a genuinely half-completed move (`git_mv` done, `atomic_write` failed) is reachable at all was NOT established and must not be asserted; if E-06 wants that exact state it must construct it deliberately (for example by patching `core.atomic_write` to raise after letting `git_mv` run) and say that it did so.
    In `specs.run_note`, the `_sidecar_append` sits inside the duplicate-suppression `if` immediately before `core.atomic_write`; move it after, keeping it inside that `if` so a suppressed duplicate still writes no event. Preserve `_sidecar_append`'s own no-op-for-a-legacy-spec-without-an-id6 behavior (the `_SPEC_ID_RE` early `return`) and its advisory failure contract unchanged.
  - Depends on: E-02
  - Expected outcome: in `specs.run_set` the `_sidecar_append` call sits after the whole `if moving: / else:` construct so it follows the final `core.atomic_write` on either branch and appears exactly once, and in `specs.run_note` it follows that verb's `core.atomic_write` while remaining inside the duplicate-suppression guard.
  - Execution state: performed

- [x] E-04 CORRECT THE FOUR IN-MODULE COMMENTS that currently justify these call sites, because each argues the right thing about DURABILITY and is silent on ORDERING, which is how the placement survived review. `backlog.run_set`'s comment says a sidecar failure "can never affect the inline record, which `_reattach_history` has already assembled into `rendered` above and which is written by the `atomic_write` below"; after E-02 the write is no longer below, so the sentence becomes false as written. `backlog.run_note`'s one-line comment ("The sidecar remains a machine-local activity log and can never gate this write") is true and incomplete. `backlog.run_new`'s comment correctly describes the already-correct order and is a useful model to match. `specs._sidecar_append`'s docstring says the inline record "is written by the caller regardless of what happens here". Update each so it states the ordering rule and WHY, naming spec `2vev8j`'s C5 first clause: the sidecar may never precede the durable write it describes, because an event for a transition that did not happen is worse than a missing event. ADD BESIDE, DO NOT OVERWRITE, the existing dated attributions (`vhbvwz` E-04, OQ-01, awhistory Order 02), following this repository's convention of correcting beside a dated measurement rather than over it. Do not restate the whole ruling; point at `record_history.append_advisory`, which already holds it.
  - Depends on: E-03
  - Expected outcome: all four comments state the ordering rule and cite C5, every pre-existing dated attribution is still present and unaltered, and no comment any longer asserts that the durable write happens below the append.
  - Execution state: performed

### Task group 3: correct the authority and the record

- [x] E-05 AMEND SPEC `2vev8j` SECTION 7's SECOND BULLET, which is the authority this item was filed from and which now describes the defect in a shape that does not exist. It reads: "Specs append the event BEFORE validating and writing the Markdown, and backlog appends BEFORE its close-legitimacy gate and BEFORE the dry-run/apply decision, so a `--dry-run` PREVIEW or a REFUSED transition can leave a phantom event. This violates C5 today and is worth its own item." Replace the measurement, not the bullet's purpose: record that the gate-ordering and validation-ordering halves were fixed by commit `23ec426df` on 2026-09-26, that the surviving C5 violation is the append preceding the DURABLE WRITE at four sites, and name this plan as the carrier. Keep the bullet IN Section 7 rather than deleting it, and keep its "filed separately" framing, because the spec's own N5 non-goal ("NOT the two out-of-scope defects in Section 7") depends on both bullets existing; deleting one would orphan that reference. DO NOT touch Section 7's FIRST bullet (the lifecycle policy gap), Section 3's C5 statement, AC-7, or anything else in the spec: AC-7 still demands more than this plan delivers, and overwriting it to match what was built would be the inverse defect. Record the amendment through `aw specs set` so the spec's `## Workflow history` carries it; do not hand-edit the `- Status:` line and do not write any approval attestation.
  - Depends on: E-04
  - Expected outcome: Section 7's second bullet states the measured current shape with its fixing commit and this plan as carrier, Section 7's first bullet and the spec's C5, AC-7 and N5 text are byte-unchanged, and the amendment appears in the spec's workflow history via `aw specs set`.
  - Execution state: performed

- [x] E-06 ADD `tests/test_history_write_order.py` COVERING THIS DIRECTION BY OUTCOME, and one CHANGELOG entry. The test module must drive each of the four verbs through a real `cli.main` invocation (not by calling the internal writer) in a temporary repository, force the DURABLE WRITE to fail, and assert that the sidecar does not exist and the artifact on disk is byte-unchanged. Eight cases, four failing and four succeeding, because a passing-only suite cannot distinguish a fixed order from a test that never exercises the failure. FORCE THE FAILURE WITHOUT MONKEYPATCHING PRODUCTION CODE where possible: making the destination directory unwritable with `chmod 0o500` reproduces it through the shipped path, re-measured at review on all four verbs, and is preferable to patching `core.atomic_write`. SKIP THAT CASE WHEN RUNNING AS ROOT, since `chmod` does not deny root and the test would silently pass without exercising anything; `tests/test_find_single_read.py` already establishes that `pytest.skip` convention for exactly this reason and must be followed rather than reinvented. Include the specs DIRECTORY-CROSSING case specifically (a status change that moves the file between status directories), since an in-place-only test would not reach that code path. ASSERT WHAT THE PROBE ACTUALLY PRODUCES AND NOTHING MORE (F-13): under `chmod`, the failing call is `core.git_mv` (whose `shutil.move` fallback cannot write into the unwritable destination) and `core.atomic_write` is NEVER REACHED, so this case must assert only the observable outcome (no sidecar, source file still in its original directory, destination directory empty) and must NOT assert or imply that `git_mv` succeeded. If a genuinely half-completed move is wanted as a ninth case, it must be CONSTRUCTED deliberately (let `git_mv` run, then make `core.atomic_write` raise) and the test must say that is what it does; do not claim the `chmod` probe reaches that state, and do not assert it is reachable in production, which review did not establish.
    DO NOT ASSERT AN EXIT CODE ON THE FAILURE CASES. Re-measured at review on all four verbs: the `PermissionError` propagates out of `cli.main` (F-11), so a direct `cli.main` call RAISES rather than returning. The failure cases must therefore wrap the invocation in `pytest.raises(OSError)` (or an equivalent that tolerates the exception) and assert on the sidecar and the artifact only, so the test does not depend on the F-11 fix this plan deliberately does not make. The SUCCESS cases may and should assert `rc == 0`.
    ONE FIXTURE DETAIL THAT WILL OTHERWISE COST A ROUND TRIP (F-14, measured at review): `aw specs note` accepts NO `--dir` flag (it derives the repository root from the spec path via `specs._repo_root_of`), while `aw backlog set`, `aw backlog note` and `aw specs set` all accept `--dir`. A `specs note` case written with `--dir` exits 2 on `unrecognized arguments` and writes no sidecar, which looks exactly like a PASS for the wrong reason. Pass only the path for that verb, and have its success case assert the sidecar CONTENT so a usage error cannot masquerade as the fix working. Also assert the CONVERSE for each verb: a successful invocation still writes exactly one sidecar record with the expected message, so the fix cannot be mistaken for silently disabling the sidecar. OBEY P16: assert on sidecar contents, artifact bytes and exit codes only; do NOT read production source text, count call sites, or assert on comment wording anywhere in this module. Use VALID six-character id6 values in every fixture: `record_history.append` raises `ValueError` on a malformed id6 and `append_advisory` converts that into a warning and returns False, so a five-character fixture id yields a passing test that proves nothing (measured at authoring, where exactly this mistake made four probe cases report a false negative). Add one CHANGELOG entry under the pending 2.0.0 heading in the user-facing voice that file uses, naming the user-visible consequence (a failed status change no longer leaves a history record claiming it happened) rather than the call-site move.
  - Depends on: E-05
  - Expected outcome: a new test module whose eight cases pass, which drives all four verbs through `cli.main`, which reaches the specs directory-crossing case, which skips rather than silently passes under root, which uses valid six-character id6 fixtures, which passes no `--dir` to `specs note`, whose failure cases tolerate a raised `OSError` rather than asserting an exit code, and which reads no production source text; plus one CHANGELOG entry describing the user-visible consequence.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE SIDECAR IS ADVISORY AND MAY NEVER GATE A DURABLE WRITE, by an explicit maintainer ruling dated 2026-09-10 (`vhbvwz` OQ-01) recorded verbatim in `record_history.append_advisory`'s docstring: inline history is "the durable home", the sidecar is "a machine-local ACTIVITY LOG - it is gitignored, so it does not survive a clone", and "Letting an advisory log failure abort or gate a durable provenance write would invert exactly the durability model that ruling chose". This plan's change runs WITH that ruling, not against it: making the sidecar depend on the durable write is the permitted direction, and the reverse dependency is what C5's second clause would require and what OQ-01 establishes it does not demand of this store.
- THE SPEC DEFINES "DURABLE" AS CLONE-SURVIVING, which is what lets OQ-01 be resolved from evidence rather than escalated. Spec `2vev8j` C2 reads "A fresh clone carries the full durable history of every artifact. This is what E4 breaks today and is non-negotiable", its 4.2 specifies the journal as "git-tracked ... (not gitignored, which is what E4 punishes)", and its E4 measures that the sidecar is gitignored so "a fresh clone gets NEITHER copy". A gitignored file is therefore not a durable write under this spec's own definition, and the two seemingly opposed statements are each correctly scoped.
- A FAILED SIDECAR WRITE IS REPORTED, NEVER SWALLOWED, which `record_history.append_advisory` exists to centralize after plan `vhbvwz` E-04 found three call sites each wrapping `append` in a bare `except Exception: pass`. E-02 and E-03 must not reintroduce a per-site decision; the helper stays the one place that decides.
- CORRECT BESIDE A DATED MEASUREMENT, NEVER OVER IT. The module comments at these call sites carry dated plan attributions (`awhistory` Order 02, `vhbvwz` E-04 and E-08, OQ-01). E-04 and E-05 add the correction beside each rather than rewriting the record of what was decided when.
- TESTS PROVE OUTCOMES, NEVER CODE STRUCTURE (`GUIDING_PRINCIPLES` P16, restated in `AGENTS.md`). This is load-bearing for E-06 because the subject IS a statement ordering, which tempts a test to read the source and assert the append appears after the write. Such a test would pass against a reordered file that is behaviorally identical and fail against a correct refactor, so E-06 asserts only on the observable sidecar, the artifact bytes and the exit code.
- `chmod`-BASED DENIAL IS SKIPPED UNDER ROOT. `tests/test_find_single_read.py` guards its unreadable-file case with `pytest.skip("Running as root; chmod 0 does not deny read")`. E-06 follows this rather than inventing a second convention, because without it the failure cases would pass vacuously in a root container.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measurements taken in this lane worktree at HEAD `596fae9ef`, with `os.geteuid()` reporting 1000 (not root).

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | BOTH HALVES THE ITEM STATES ARE ALREADY FIXED, and this is the finding that most changes the plan's subject. The item says `backlog.run_set` appends "BEFORE its close-legitimacy gate and BEFORE the dry-run decision" and that specs appends "BEFORE validating and writing the Markdown". Measured, `backlog.run_set`'s order is `evaluate_blocking_close` refusal, then the `dry_run` early return, then `append_advisory`; and `specs.run_set`'s order is `validate_spec` refusal, then the `dry_run` early return, then `_sidecar_append`. Commit `23ec426df` ("Honor --dry-run on the --status spelling of aw backlog set and aw specs set", 2026-09-26, plan `wd6npl`) made both moves. | Four CLI probes in temporary repositories: a refused blocking close under `--dry-run` exits 1 with "refused:" and no sidecar file; a legitimate `--dry-run` exits 0, leaves the item byte-unchanged, leaves `done/` empty and writes no sidecar; a `specs set` refused by `validate_spec` exits 1 with "the resulting spec would not conform" and no sidecar; a `specs set --dry-run` exits 0 with no sidecar and the file unchanged. `git log -S` on the current dry-run guard returns `23ec426df` alone. | The plan must NOT be written as a fix for the item's stated shape, and any plan asserting that shape would fail review on measurement. The item is not retired, because F-02 and F-03 show a worse C5 violation surviving. E-01 re-measures all four at execution and E-05 corrects the spec sentence that caused the mis-filing. |
| F-02 | THE SURVIVING VIOLATION IS THE APPEND PRECEDING THE DURABLE WRITE, at four reachable sites, and it is measurable through the shipped code path with NO monkeypatching. With the destination directory `chmod 0o500`, `aw backlog set --status graduated` raises `PermissionError` out of `cli.main`, the item remains in `open/` still reading `- Status: open`, and the sidecar holds `{"id6": "bk0004", ..., "workflow": "aw backlog set", "message": "status -> graduated"}`. This is C5's first clause breached exactly: an event for a transition that did not happen. ALL FOUR SITES RE-MEASURED INDEPENDENTLY AT REVIEW AND ALL FOUR REPRODUCE; the AST order is `run_set` append-then-write, `run_note` append-then-write, `specs.run_set` append-then-write, `specs.run_note` append-then-write, with `run_new` correctly write-then-append. ONE SUB-CLAIM IS WRONG AND IS CORRECTED IN F-13: the specs moving case is NOT "`git_mv` succeeded and `atomic_write` failed"; the measured trace is `git_mv` RAISING and `atomic_write` never being reached. The phantom event and the partial on-disk state both reproduce regardless, so the defect and the fix are unaffected; only the mechanism statement was wrong, and E-03/E-06/V-03 are corrected so no item asserts the unmeasured half. | The `chmod 0o500` probe above for `backlog.run_set`; the same probe for `backlog.run_note` (sidecar holds `"message": "note: hello"` while the inline record is absent, re-verified by `grep -c hello` returning 0); for `specs.run_note` (sidecar holds `"note: hello"`, inline absent); and for `specs.run_set` in its directory-crossing form, leaving the source file in `draft/`, the destination directory empty, `git status --porcelain` showing only the untracked sidecar, and the sidecar holding `"to-review: m"`. | Fixes the scope at exactly four call sites (E-02, E-03). The directory-crossing case is why E-03 places the append after the whole `if moving: / else:` construct and why E-06 must include a directory-crossing case rather than only an in-place one. |
| F-03 | `run_note` ON BOTH TREES WAS NEVER TOUCHED BY THE FIX, so two of the four sites have never been in the correct order, and these are the PUREST C5 breach of the four: the sidecar records a note that the durable artifact does not contain. `23ec426df` changed only the two `run_set` paths. | `backlog.run_note` calls `append_advisory` above its `core.atomic_write`, with the one-line comment "The sidecar remains a machine-local activity log and can never gate this write (E-04)" - true about durability and silent about ordering. `specs.run_note` calls `_sidecar_append` immediately before `core.atomic_write` inside the duplicate-suppression `if`. Both probed above with the inline record measurably absent while the sidecar record exists. | E-02 and E-03 each cover a `run_set` and a `run_note`, so neither verb pair is half-fixed. E-06 drives all four verbs rather than the two the item names. |
| F-04 | THE PHANTOM IS OPERATOR-VISIBLE, which is what makes this a `bug` rather than an internal tidiness concern, and it answers the perceptibility test `AGENTS.md`'s release-gate section applies. After the failed `backlog set` above, `aw record-history bk0008 --dir <repo>` prints `History for bk0008` followed by `- 20260930 [backlog] aw backlog set (aw backlog): status -> graduated` and exits 0, while the item on disk reads `- Status: open`. An operator reading that output is told a transition happened that did not. | The `aw record-history` invocation above, run in the same temporary repository immediately after the failed transition, with its exit code 0 recorded. `cli._run_record_history` reads through `record_history.read_for`, which reads the sidecar only. | Justifies inheriting the item's `- Blocks-Release: next` rather than questioning it, and fixes the harm statement E-06's CHANGELOG entry must make: a user-visible false record, not a misordered statement. |
| F-05 | THE REORDERING IS PROVEN SUFFICIENT AND SUFFICIENTLY NARROW, measured at authoring by emulating the post-fix order at runtime rather than by assuming it. Buffering `append_advisory` and flushing the buffer only from a SUCCESSFUL `atomic_write` (the exact post-fix semantics, with no production edit) yields: all four verbs under a failing durable write leave `sidecar=False` with the event still buffered and unwritten; and all four verbs under a succeeding write leave `sidecar=True`. So moving the call is both necessary and enough, and it does not suppress the record in the normal case. | The emulation harness over all eight cases, printing `sidecar=False buffered_unflushed=1` for each of the four failure cases and `sidecar=True buffered_unflushed=0` for each of the four success cases. | This plan does not propose an untested remedy, and E-06's eight cases are a direct transcription of the eight already measured. It also bounds the change: no new buffering mechanism is needed in production, because moving the call achieves the same ordering. |
| F-06 | A MALFORMED FIXTURE id6 SILENTLY VOIDS A TEST OF THIS DEFECT, measured the hard way. `record_history.append` raises `ValueError` on an id6 that is not six characters, and `append_advisory` converts that into a stderr warning and `return False`, so a fixture using a five-character id (for example `bk9` or `aa201`) produces `sidecar=False` for a reason unrelated to ordering. Four of this plan's own authoring probes reported a false negative this way before the ids were corrected. | The warning text observed verbatim: "could not append to the history sidecar (.aw/records/history.jsonl) for ...: ValueError: record_history.append: 'bk9' is not a valid id6"; the same eight cases reporting `sidecar=True` on the success path once six-character ids were used. | E-06 states the valid-id6 requirement explicitly, and V-06 demands a demonstration that the success cases DO write a record, which is the check that catches this class. A failure-only test module would be satisfied by a broken fixture. |
| F-07 | THE OPPOSITE DIRECTION IS WELL COVERED AND THIS ONE IS NOT COVERED AT ALL, so this is new coverage rather than a repair. `tests/test_history_provenance.py::SidecarFailureIsReportedTests` monkeypatches `record_history.append` to raise and asserts across four cases that the inline record still lands and the warning is reported. No test anywhere forces the DURABLE write to fail. The nearest neighbours assert the absence of a sidecar after a REFUSED or PREVIEWED transition (`tests/test_backlog.py::BacklogDryRunTests` and `tests/test_specs_status_dirs.py::test_specs_set_status_dry_run_leaves_file_and_tree_clean`), which pin F-01's already-fixed halves and must keep passing untouched. | The two test classes read in full; `grep -rln history.jsonl tests/` returns `test_backlog.py`, `test_specs_status_dirs.py`, `test_installer.py` and `tests/fixtures/derive_plan_status_baseline.json`, and NOT `test_history_provenance.py` (corrected at review: that module reaches the sidecar through the `record_history` API and by monkeypatching `record_history.append`, never by naming the file, so the authored list was wrong on one entry while the conclusion stands). `tests/test_history_write_order.py` confirmed absent. The class carries 4 of the module's 7 tests. | E-06 adds a NEW module rather than extending `test_history_provenance.py`, keeping the two directions separately named and leaving the existing dry-run pins untouched. It also means the regression this plan fixes could recur today without any test going red, which is itself worth stating to a reviewer. |
| F-08 | SEVERAL PENDING PLANS SCOPE `backlog.py` AND `specs.py` AND NONE COLLIDES, measured rather than assumed. CORRECTED AT REVIEW, because three of the authored entries have left `pending/` and three statuses moved, which is the expected rot for a live population and is why E-01 re-measures rather than trusting this row: `8rsxy1`, `f7igdu` and `jbipfa` are all now in `.aw/records/plans/executed/`; `7ohskw`, `4nbvfr` (authored as `to-review`) and `m7fllj` are `reviewed`; `izh17y` is now `approved` (authored as `reviewed`); `uz05bl`, `ribg85` and `ynhst5` remain `approved`. The CONCLUSION HOLDS AND IS NOW PARTLY PROVEN RATHER THAN PREDICTED: `jbipfa` was the closest neighbour, editing `_reattach_history` in the same function E-02 touches, and it HAS LANDED (commit `da04c5cf0`) without moving the append. Its diff adds a `label` parameter and a `prior_status` computation and changes the inline record token; the `append_advisory` call and its position are untouched, re-verified by AST after the merge. So the predicted disjointness was correct in the one case that actually resolved. None of the remaining plans names a sidecar, an advisory append or `record_history` in its scope; no pending plan scopes `record_history.py`; no pending plan scopes spec `2vev8j`. | The `- Scope-Paths:` and `- Status:` lines re-read at review for every named plan, plus `find .aw/records/plans -name '*<id6>*'` locating the three that moved; `git show --stat da04c5cf0` and its `backlog.py` diff read in full; the post-merge AST order showing `run_set` still append(1697)-then-write(1707). | No `- Item-Dependencies:` edge is warranted: the plans touch disjoint concerns in shared files, the runner isolates each item in its own worktree and merges through a revalidation gate, and E-01 re-checks the four orderings at execution so a neighbour landing first is detected rather than assumed away. This plan adds a NEW test file, so no test module is contended. |
| F-09 | THE SUITE'S STATE IS LIVE AND THE AUTHORED BASELINE IS NOT REPRODUCIBLE, SO V-06 COMPARES BY FAILURE SET AND NEVER BY COUNT. Authoring recorded `1 failed, 3487 passed, 2 skipped`, the failure being `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` on a pure date diff, attributed to the local-versus-UTC history clock skew filed as `fnb8pl`, `lq2w86` and `2wae2x` (all still `open`, re-verified). CORRECTED AT REVIEW: a bare run reports `3887 passed, 2 skipped, 3 warnings in 247.19s` with ZERO failures, and that named test PASSES. Its assertion is no longer date-sensitive: it normalizes every history date with `_DATE.sub("- HIST_DATE ", ...)` before comparing, and its own comment records the skew as live bug `fnb8pl` rather than asserting a literal date. So the authored count drifted by 400 AND the authored failure is gone, for a structural reason rather than a time-of-day one. The SKEW ITSELF IS STILL REAL and is still owned by three open items; it just no longer fails this test. | The bare-run summary at review HEAD; the named test run alone reporting `1 passed`; its `_DATE` normalization and `fnb8pl` comment read; the three items' `open` status re-confirmed. | The validation bar is a FAILURE SET comparison by node id against an empty set, NOT a pass-count comparison: the authored `3487` and the review-measured `3887` differ by 400, so any constant is guaranteed to mislead. The executor must not carry the authored failure forward as expected, must not fix the skew (outside `- Scope-Paths:`, owned by three filed items), and must show any failure it does see reproducing on an unmodified tree before calling it pre-existing. |
| F-10 | `backlog.run_new` IS ALREADY CORRECT AND IS THE MODEL TO MATCH, so the fix has a precedent inside the same module rather than being invented. It calls `core.atomic_write(dest, rendered)` and only then `append_advisory`, and its comment states the reason in the right terms: the inline record "was written by the `atomic_write` directly above". | `backlog.run_new`'s write-then-append order and its comment, read in full. | E-04 can align the other comments to an existing in-repo wording instead of coining new prose, and E-01(b) confirms this site needs no edit, which is what keeps the change to four sites. |
| F-11 | A SEPARATE ROBUSTNESS DEFECT IS VISIBLE IN EVERY PROBE AND MUST NOT BE ABSORBED: the `PermissionError` and `OSError` from a failed artifact write propagate UNCAUGHT out of `cli.main`, so the operator gets a traceback rather than a diagnosed nonzero exit. This is true on all four verbs and is independent of ordering. | Every `chmod 0o500` probe reports `RAISED PermissionError` rather than a return code; no `except OSError` surrounds these `atomic_write` calls in either module. | Recorded on the Deferred list and NOT fixed here. It matters to this plan in one way only: E-06's failure cases must tolerate an exception as the outcome (asserting on the sidecar and the artifact, not on an exit code), because demanding a clean nonzero exit would make the test depend on a fix this plan does not make. |
| F-12 | RELEASE-BLOCKING ITEM `19lmbe` IS LIVE AND ITS DEFECT IS FIXED, which is adjacent enough to state and outside this plan's scope. It is `open` with `- Blocks-Release: next` (re-verified at review), and describes `aw backlog set --status` ignoring `--dry-run` because the guard read a nonexistent `apply` flag. Commit `23ec426df` fixed exactly that, and plan `wd6npl`'s own F-8 identified `19lmbe` as a duplicate and instructed closing it with `--evidence`; that close never happened. | Item `19lmbe`'s front matter; the current guard reading `if getattr(args, "dry_run", False) or not getattr(args, "apply", True):`; the F-01 probe showing `--dry-run` honored. | Recorded on the Deferred list with the item as its own carrier. Named because it is the same commit and the same sentence of the same spec that produced this plan, so an executor will encounter it; closing another item's release gate is a decision for its owner and is not this plan's work. |
| F-13 | THE SPECS MOVING CASE FAILS AT `git_mv`, NOT AT A LATER `atomic_write`, SO THE PLAN'S MECHANISM CLAIM WAS WRONG WHILE ITS DEFECT CLAIM WAS RIGHT. F-02 and E-03 both asserted the partial state is "`git_mv` succeeded and `atomic_write` failed". Measured at review by wrapping BOTH `artifact_core.git_mv` and `artifact_core.atomic_write` and driving the real CLI with the destination directory `chmod 500`: the trace is exactly `[('git_mv', 'RAISED PermissionError')]`, so `atomic_write` is NEVER REACHED. The cause is inside `git_mv` itself: when `git mv` exits nonzero it falls back to `shutil.move`, which copies into the unwritable destination and raises there. With the destination left writable the same probe traces `[('git_mv', 'OK'), ('atomic_write', 'OK')]` and exits 0, confirming the instrumentation is faithful. THE DEFECT IS UNAFFECTED: the phantom event still lands (sidecar holding `"to-review: m"`), the file stays in `draft/`, and the destination stays empty, so the append still precedes every durable step. What IS affected is what a test may claim. A `chmod`-based probe cannot demonstrate a half-completed move, and whether that state is reachable in production at all was NOT established here. | The two instrumented traces (failing and succeeding) with the sidecar contents and on-disk state after each; `artifact_core.git_mv`'s `shutil.move` fallback read; a direct `git mv` in the same fixture reporting `fatal: renaming ... failed: Permission denied`. | E-03 now states the rule positionally (after the whole `if moving: / else:` construct) rather than keyed to one call, and explicitly forbids reasoning from the old claim. E-06 and V-03 may assert only the observable outcome and must NOT assert that `git_mv` succeeded; a genuinely half-completed move, if wanted, must be CONSTRUCTED and declared as such. |
| F-14 | `aw specs note` TAKES NO `--dir`, WHICH TURNS A PLAUSIBLE E-06 FIXTURE INTO A TEST THAT PASSES FOR THE WRONG REASON. The other three verbs in scope (`backlog set`, `backlog note`, `specs set`) all accept `--dir`; `specs note`'s parser does not (its options are `--message` and `--date` plus the shared output flags), because it derives the repository root from the spec path through `specs._repo_root_of`. Measured: passing `--dir` to it exits **2** with `unrecognized arguments` and writes no sidecar. A failure case written that way asserts "no sidecar" and goes GREEN while never reaching the code under test. | `aw specs note --help` read in full; the invocation with `--dir` exiting 2 on `unrecognized arguments`; the same invocation without `--dir` reaching the real failure (sidecar holding `"note: hello"`, inline record absent). | E-06 now names this explicitly and requires the `specs note` success case to assert sidecar CONTENT, so a usage error cannot masquerade as the fix working. This is the same class of silent false negative as F-06's malformed id6, which is why it is called out beside it rather than left to the executor. |

## Proposed changes (ordered, validatable)

1. Re-measure the four orderings, `run_new`'s correct order, both already-fixed halves, and `status_set`'s silence; proceed on the measurement rather than on the item's or the spec's text (E-01).
2. Move the advisory append after the durable write in `backlog.run_set` and `backlog.run_note`, preserving every argument and the advisory failure contract (E-02).
3. Move the sidecar append after the final durable write in `specs.run_set` on both the moving and in-place branches, and after the write in `specs.run_note` while keeping it inside the duplicate guard (E-03).
4. Correct the four in-module comments to state the ordering rule and cite spec `2vev8j`'s C5, adding beside each existing dated attribution rather than over it (E-04).
5. Amend spec `2vev8j` Section 7's second bullet to the measured current shape, naming the fixing commit and this plan as carrier, leaving C5, AC-7, N5 and the first bullet untouched, recorded through `aw specs set` (E-05).
6. Add `tests/test_history_write_order.py` with eight outcome cases over four verbs (four failing writes, four succeeding), including the specs directory-crossing case, skipping under root, using valid id6 fixtures; plus one CHANGELOG entry in the user-facing voice (E-06).

## Deferred / out of scope (with reason)

- C5's SECOND CLAUSE, "no status change may succeed while its durable history write silently fails", which remains UNSATISFIED after this plan. It binds the git-tracked per-artifact journal that spec `2vev8j` 4.2 specifies and NOT today's gitignored sidecar, for the reasons resolved in OQ-01 (4.2 makes the journal tracked; C2 defines durable as clone-surviving; E4 names the sidecar as what breaks that; AC-7 says "the JOURNAL write"). Making a SIDECAR failure abort a transition would instead contradict the maintainer's 2026-09-10 `vhbvwz` OQ-01 ruling recorded at `record_history.append_advisory`, so it is deliberately not built here and this plan delivers C5's first clause only.
  - Carrier: ms06pi
  - Carrier-Note: `ms06pi` (graduated, `- Blocks-Release: next`) is the backlog item spec `2vev8j` graduated from and is the live carrier for the journal migration that C5's second clause presumes; the spec itself cannot be the carrier, because `check_engine._CARRIER_TARGET_TYPES` accepts only a backlog item or a plan, deliberately, "so a spec sharing no id6 with a plan cannot accidentally satisfy a handoff". The spec's AC-7 already demands both halves ("a failed history write FAILS the status change"), so the obligation is doubly recorded and is not lost by this plan delivering only the first. E-05 deliberately does NOT weaken AC-7 to match what this plan builds, which is what keeps the spec an honest record that half the criterion is still outstanding.
- THE PER-ARTIFACT JOURNAL, EXPLICIT `seq` ORDERING AND WRITER LOCK that `2vev8j` specifies. This plan fixes ordering within TODAY's single global `.aw/records/history.jsonl` and begins no migration. Its N3 non-goal already states that moving backlog and specs off the global sidecar is out of the spec's own scope pending OQ-2.
  - Carrier: ms06pi
  - Carrier-Note: `ms06pi` (graduated, `- Blocks-Release: next`) is the live backlog carrier for spec `2vev8j`'s journal migration, and a spec is not an accepted carrier type (see the note on the clause above). That spec's Migration step 4 says to "ROUTE EVERY WRITER, and fix the write-order bugs in Section 7 while there", so this plan does that step's write-order half early and in isolation, leaving the routing to the migration. Landing it first strictly reduces the migration's work and removes a live operator-visible false record in the meantime.
- `status_set.apply_status_change` WRITING NO SIDECAR RECORD AT ALL, so the two `aw backlog set` spellings differ in history recording as well as in ordering. The item's own closing note raises this and records that plan `47ttnv` deliberately did not touch it.
  - Carrier: fcnz1r
  - Carrier-Note: `fcnz1r` (open, `chore`) owns unifying the two dispatch paths and names the sidecar asymmetry as one of four deliberately divergent behaviors needing "a spec-level decision about which behaviors are canonical before any code moves". Adding a sidecar write to `status_set` would change behavior for the five trees that shared setter serves, which is exactly what that item exists to prevent being done piecemeal.
- THE UNCAUGHT `OSError` / `PermissionError` PROPAGATING OUT OF `cli.main` on a failed artifact write (F-11), which gives an operator a traceback instead of a diagnosed nonzero exit on all four verbs. A pre-existing defect this plan measured and did not create; fixing it means adding error handling to the write paths of two modules, which is a different change with a different risk profile, and this plan's tests are written not to depend on it either way.
  - Carrier-Declined: No obligation follows from fixing the ordering, and filing it is a judgement for the maintainer, since a hard failure on an unwritable records directory may be the intended behavior and only the PRESENTATION is poor. Recorded here with the measurement so whoever decides has it.
- THE HISTORY DATE-CLOCK SKEW between `backlog.py`'s local `date.today()` and `status_set.py`'s UTC date, which makes `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity` fail for part of every day in a timezone behind UTC (F-09).
  - Carrier: fnb8pl
  - Carrier-Note: Filed three times over (`fnb8pl`, `lq2w86`, `2wae2x`, all open); `fnb8pl`'s summary names this exact test. This plan NORMALIZES AROUND it by recording it as the validation baseline rather than fixing it or depending on it, following pending plan `jbipfa`, which treats the same skew the same way.
- CLOSING RELEASE-BLOCKING ITEM `19lmbe`, whose defect commit `23ec426df` fixed but which is still `open` carrying `- Blocks-Release: next` (F-12).
  - Carrier: 19lmbe
  - Carrier-Note: Its own item is the carrier, and plan `wd6npl`'s F-8 already records the intended close with `--evidence` citing that plan. Closing another item's release gate from inside an unrelated plan would be an undeclared records change outside this plan's `- Scope-Paths:`, and the close itself is gated on evidence its owner should cite.

## Scope check

- Over-scope: none. The production change is four call-site moves with no argument, message or control-flow change; the comment edits are confined to the four sites plus the one-line alignment at `run_new`; the spec edit is one bullet; the test module is new; the CHANGELOG gains one line. No status vocabulary, placement rule, gate, validator or dry-run branch is touched, and no record's CONTENT changes - only when it is written.
- Under-scope: deliberately, on three stated boundaries. FIRST, only C5's FIRST clause is delivered; the second binds the future tracked journal rather than today's sidecar (OQ-01), so after this plan `2vev8j`'s AC-7 is still only half satisfied and E-05 must not pretend otherwise. SECOND, only the four PRE-WRITE sites move; `status_set`'s total silence is a parity defect owned elsewhere, so the two `aw backlog set` spellings still disagree about history after this plan. THIRD, the sidecar remains a single global gitignored file with no `seq` and no lock, so this plan makes the existing store honest about ordering and does not make it durable across a clone.
- Right-sizing, assessed per E-item at review (6 E-items, 3 groups, both well under the structural thresholds) and INCLUDING the one `IPD-Z602` density advisory the linter raises, which the plan did not assess. The advisory is on E-02 ("4 clauses"), and review ACCEPTS it: the clauses are one move in `run_set`, the same move in `run_note`, and then two PROHIBITIONS (preserve the advisory contract, keep the arguments byte-identical). Two call sites in one function pair, one concern (ordering), one `V-*`, one shipped-path probe per verb; splitting it would create two items sharing one fixture and one green run, and would risk landing the fix on `run_set` while leaving `run_note` (which F-03 identifies as the purest breach) behind. E-03 is the densest remaining item because the moving branch needs positional care, and it is kept whole for the same reason: it is one concern in one function pair. E-06 bundles the test module and the CHANGELOG line, which review also accepts, since the CHANGELOG sentence is one line derived from the same user-visible consequence the tests assert and would otherwise be an E-item with no independent verification.

## Required tests / validation

- `python3 -m pytest` run BARE (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow'`), with the summary line pasted, COMPARED BY FAILURE SET AND NOT BY COUNT. Authoring recorded `1 failed, 3487 passed, 2 skipped, 3 warnings in 68.31s`; review re-measured `3887 passed, 2 skipped, 3 warnings in 247.19s` with ZERO failures and the authored failure now passing (F-09). So the bar is an empty failing-node-id set, with any failure shown to reproduce on an unmodified tree before being called pre-existing. No pass-count constant may gate this item.
- `python3 -m pytest tests/test_history_write_order.py` for the new module specifically, with per-case output pasted.
- `python3 -m pytest tests/test_history_provenance.py tests/test_backlog.py::BacklogDryRunTests tests/test_specs_status_dirs.py` pasted, proving the opposite-direction coverage and both already-fixed halves still hold after the reorder. These are the tests most likely to be disturbed by moving an append.
- A DELIBERATE-BREAK DEMONSTRATION: with the production reorder reverted (or one call site moved back), the new module's corresponding failure case must be observed FAILING, then passing again once restored. A check never observed failing is not established, and this plan's entire subject is an ordering that a passing test suite did not notice for weeks.
- `aw ipd lint --phase pre-transition` conforming before any terminal transition.
- `aw check` (or `aw check all`) clean, or no worse than its pre-change state with any pre-existing finding named, since E-05 edits a spec file and the release-gate and reference rules read it.
- `aw sanitize --agent` clean, because this plan's measurements were taken in temporary directories and name an absolute lane path, and none may reach a committed artifact.

## Spec / documentation sync

ONE SPEC FILE IS EDITED AND IT IS DECLARED. `.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md` is in `- Scope-Paths:` because E-05 amends Section 7's second bullet.

WHY THE AMENDMENT IS NECESSARY RATHER THAN OPTIONAL. That bullet is the AUTHORITY this defect was filed from: backlog item `bjcz05` quotes it verbatim, and plan `47ttnv`'s Deferred row quotes it forward again as a statement of current behavior. It has been stale since 2026-09-26 and has already caused one item to be filed against a fixed defect and one executed plan to record a false claim about live code. Fixing the code while leaving the bullet asserting the old shape would leave the spec, which is the copy a reviewer trusts, contradicting both the code and this plan. The amendment is a MEASUREMENT correction, not a contract change: the bullet keeps its place in Section 7, keeps its "filed separately" framing (which the spec's own N5 non-goal references), and keeps saying the defect is worth its own item, now naming this plan as that item's carrier.

WHAT IS NOT AMENDED, and this is the load-bearing half. Section 3's C5 statement is untouched. AC-7 is untouched, deliberately, even though this plan satisfies only its first half: weakening an acceptance criterion to match what was built is the inverse of the defect this plan fixes, and OQ-01 establishes that the second half binds the tracked journal the spec still owes rather than anything this plan builds. Section 7's first bullet (the lifecycle policy gap) is untouched, as are N3, N5 and the migration section. No `- Status:` line is hand-edited and no approval attestation is written; the amendment is recorded through `aw specs set`.

DOCUMENTATION SYNC. One CHANGELOG entry (E-06), in the user-facing voice that file uses and describing the user-visible consequence from F-04 rather than the call-site move. No README or `docs/` page documents the sidecar's write ordering, so none needs updating. `aw record-history`'s help text was already corrected by plan `eikajx` to stop claiming the sidecar holds full history and needs no further change here.

## Open questions

### OQ-01: Does spec 2vev8j's C5 second clause bind TODAY's advisory sidecar, which would contradict the 2026-09-10 ruling that the sidecar may never gate a durable write?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: NO, C5's second clause does not bind today's sidecar, because the spec itself defines "durable" in a way the sidecar explicitly fails. THE APPARENT CONTRADICTION, stated first so the resolution is checkable: C5 says "no status change may succeed while its durable history write silently fails" and AC-7 demands "a test with the journal write forced to fail, asserting the status did NOT change", while `record_history.append_advisory`'s docstring records a maintainer ruling dated 2026-09-10 (`vhbvwz` OQ-01) that the sidecar is "a machine-local ACTIVITY LOG" and that "Letting an advisory log failure abort or gate a durable provenance write would invert exactly the durability model that ruling chose", pinned by `tests/test_history_provenance.py::SidecarFailureIsReportedTests`. WHAT SETTLES IT, in three places in the same spec. FIRST, decision 4.2 states where history lives under this contract: "git-tracked, append-only, PER-ARTIFACT JSONL keyed by `<id6>`", explicitly "TRACKED (not gitignored, which is what E4 punishes)". SECOND, C2 defines the property that makes a write durable: "A fresh clone carries the full durable history of every artifact. This is what E4 breaks today and is non-negotiable." THIRD, E4 names the sidecar as the thing that breaks it: the full log "is GITIGNORED (`.aw/.gitignore:11`), so a fresh clone gets NEITHER copy. 176 of the 177 sidecar records exist only on the maintainer's machine." So the spec never treats today's sidecar as a durable history write; it treats it as the defect the journal replaces. AC-7's own wording agrees, saying "the JOURNAL write forced to fail" rather than the sidecar. BOTH STATEMENTS ARE THEREFORE TRUE AND SCOPED: the sidecar is advisory and may never gate a transition (the 2026-09-10 ruling, which this plan preserves exactly), and the future tracked journal must gate one (C5 and AC-7, which this plan does not deliver and does not weaken). NON-BLOCKING, because the plan is written to this resolution: E-02 and E-03 keep the advisory contract intact, and E-05 amends only Section 7's stale measurement while leaving C5 and AC-7 untouched. ONE POINT IS SURFACED FOR THE MAINTAINER rather than decided here, and it is a scheduling judgement and not a blocker: C5's second clause remains UNSATISFIED until the journal migration lands, so `2vev8j`'s AC-7 is still half open after this plan, which is recorded on the Deferred list with the spec as carrier rather than being quietly marked met.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste, for each of the five measurements, the raw output and the command or symbol reference that produced it: (a) the append-versus-write order in all four of `backlog.run_set`, `backlog.run_note`, `specs.run_set` and `specs.run_note`, quoted so a reader can see the append precedes the write; (b) `backlog.run_new`'s write-then-append order quoted, confirming it needs no edit; (c) a CLI transcript of a refused blocking close under `--dry-run` showing exit 1, "refused:" on stderr, the item byte-unchanged and NO sidecar file, plus a legitimate `--dry-run` showing exit 0, no move and no sidecar; (d) a CLI transcript of a `specs set` refused by `validate_spec` showing exit 1 and no sidecar; (e) evidence that `status_set` contains no `record_history` call. Then state, per measurement, whether it matches the authoring finding, and if any differs, whether this plan's four-site scope still holds and why. A summary assertion that the figures matched is NOT evidence; the raw output is.
  - Observed evidence:
    Measurements taken at executing HEAD `ecf74d5b2b155c7583ba4bb87e326e4c5ce69f56`:

    (a) Order of advisory append versus durable write at pre-change call sites:
    - `backlog.run_set` (pre-change): `_rh.append_advisory` at line 1829 preceded `core.atomic_write(dest, rendered)` at line 1839 and `src.unlink()` at line 1842:
      ```python
      1829: _rh.append_advisory(
      1839: core.atomic_write(dest, rendered)
      1842: src.unlink()
      ```
    - `backlog.run_note` (pre-change): `_rh.append_advisory` at line 1944 preceded `core.atomic_write(src, ...)` at line 1969:
      ```python
      1944: _rh.append_advisory(
      1969: core.atomic_write(src, "\n".join(out).rstrip() + "\n")
      ```
    - `specs.run_set` (pre-change): `_sidecar_append` at line 1024 preceded `core.atomic_write` at line 1034 (moving) and line 1051 (in-place):
      ```python
      1024: _sidecar_append(repo_root, new_text, sidecar_msg)
      1034: core.atomic_write(dest_path, new_text)
      1051: core.atomic_write(path, new_text)
      ```
    - `specs.run_note` (pre-change): `_sidecar_append` at line 1229 preceded `core.atomic_write` at line 1231:
      ```python
      1229: _sidecar_append(_repo_root_of(path), text, f"note: {args.message}")
      1231: core.atomic_write(path, "\n".join(out))
      ```
    Result: all four sites confirmed append-before-write, matching authoring findings.

    (b) `backlog.run_new` write-then-append order:
    In `agent_workflows/backlog.py`, `run_new` orders `atomic_write` at line 1413 before `append_advisory` at line 1422:
    ```python
    1413: core.atomic_write(dest, rendered)
    1417: # was written by the `atomic_write` directly above, so it is unaffected either way; the sidecar is
    1422: _rh.append_advisory(
    ```
    Result: confirms `run_new` already writes durable record before appending to sidecar; matches authoring finding.

    (c) CLI transcripts for refused blocking close under `--dry-run` and legitimate `--dry-run`:
    - Refused blocking close:
      ```
      $ python3 -m agent_workflows.cli backlog set bk0001 --status done --dry-run --dir <tmp_repo>
      Exit code: 1
      Stderr: aw backlog set: refused: backlog item carries Blocks-Release 'next'; closing it `done` would silently drop that release gate.
        - hand the gate to a plan: add `- From-Backlog: <this id6>` (and the same `- Blocks-Release`) to a plan via `aw ipd set ... --from-backlog <id6>`
        - cite satisfying evidence: `aw backlog set done <item> --evidence <in-tree artifact path>`
        - explicitly release the gate first: `aw backlog set done <item> --blocks-release -`
      Sidecar exists: False
      Item unchanged: True
      ```
    - Legitimate `--dry-run`:
      ```
      $ python3 -m agent_workflows.cli backlog set bk0001 --status parked --dry-run --dir <tmp_repo>
      Exit code: 0
      Stdout: --- would move /tmp/.../open/20261001-bk0001-test-item.md -> /tmp/.../parked/20261001-bk0001-test-item.md (status parked) ---
      Sidecar exists: False
      Item unchanged: True
      ```
    Result: matches authoring finding (F-01).

    (d) CLI transcript of `specs set` refused by `validate_spec`:
    ```
    $ python3 -m agent_workflows.cli specs set <tmp_repo>/.aw/records/specs/draft/20261001-sp0001-01-sp0001-test-spec.spec.md --status to-review --message review --no-commit
    Exit code: 1
    Stderr:
    aw specs set: the resulting spec would not conform; refused (file unchanged):
      spec.metadata-bullet-repeated: metadata bullet - Title: appears 2 times
    Sidecar exists: False
    ```
    Result: matches authoring finding (F-01).

    (e) `agent_workflows/status_set.py` contains no `record_history` call:
    ```python
    >>> 'record_history' in open('agent_workflows/status_set.py').read()
    False
    ```
    Result: matches authoring finding.

    Summary: All 5 measurements match authoring findings; the plan's 4-site scope holds.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste the post-change source of both backlog call sites showing the `append_advisory` call following the `core.atomic_write` (and, for `run_set`, following the `src.unlink()` that completes the move). Paste a `git diff` for `agent_workflows/backlog.py` proving the `id6`, `tree`, `workflow`, `actor`, `message` and `artifact` arguments are byte-identical to before and that no control flow, gate, dry-run branch or placement logic changed. Then paste a CLI transcript for BOTH verbs with the durable write failing, showing the artifact unchanged on disk and NO sidecar file; and a transcript for both with the write succeeding, showing exactly one sidecar record with the expected message. Finally paste `python3 -m pytest tests/test_history_provenance.py` passing, proving the advisory failure contract still holds in the other direction.
  - Observed evidence:
    Post-change source in `agent_workflows/backlog.py`:
    - `backlog.run_set`:
      ```python
      dest_dir.mkdir(parents=True, exist_ok=True)
      core.atomic_write(dest, rendered)
      moving = dest.resolve() != src.resolve()
      if moving:
          src.unlink()
      # Append this transition to the GLOBAL sidecar as well (awhistory Order 02). The inline block now
      # keeps the FULL history (plan `vhbvwz` E-08 stopped slimming it), so this is an additional
      # machine-local activity-log entry rather than the only durable copy.
      #
      # plan `vhbvwz` E-04: a failure here is REPORTED, never swallowed, and it can never affect the
      # inline record, which `_reattach_history` has already assembled into `rendered` above and which
      # was written by the `atomic_write` above.
      # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
      # because an event for a transition that did not happen is worse than a missing event. The
      # sidecar remains a machine-local activity log (OQ-01) and must never gate a durable write; see
      # `record_history.append_advisory`.
      # histdedup evbx9s E-03/E-04: skip sidecar appending on suppressed duplicate same-status writes,
      # following the specs.run_set precedent so the advisory log does not record phantom transitions.
      if item.id and not suppress:
          from agent_workflows import record_history as _rh

          _rh.append_advisory(
              repo_root,
              id6=item.id,
              tree="backlog",
              workflow="aw backlog set",
              actor="aw backlog",
              message=(getattr(args, "message", "") or f"status -> {new_status}").strip(),
              artifact=src.name,
          )
      ```
    - `backlog.run_note`:
      ```python
      core.atomic_write(src, "\n".join(out).rstrip() + "\n")

      # plan `vhbvwz` E-04 / OQ-01: the sidecar remains a machine-local activity log and can never gate
      # this write.
      # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
      # because an event for a transition that did not happen is worse than a missing event; see
      # `record_history.append_advisory`.
      if item.id:
          from agent_workflows import record_history as _rh

          _rh.append_advisory(
              repo_root,
              id6=item.id,
              tree="backlog",
              workflow="aw backlog note",
              actor="aw backlog",
              message=f"note: {message}",
              artifact=src.name,
          )
      sys.stdout.write(f"aw backlog note: appended a history record to {src}\n")
      ```

    Git diff for `agent_workflows/backlog.py`:
    ```diff
    --- a/agent_workflows/backlog.py
    +++ b/agent_workflows/backlog.py
    @@ -1416,6 +1416,9 @@ def run_new(args) -> int:
         # `except Exception: pass`. The inline `## Workflow history` record is already in `rendered` and
         # was written by the `atomic_write` directly above, so it is unaffected either way; the sidecar is
         # a machine-local activity log (OQ-01) and must never gate a durable write.
    +    # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
    +    # because an event for a transition that did not happen is worse than a missing event; see
    +    # `record_history.append_advisory`.
         if item.id:
             from agent_workflows import record_history as _rh

    @@ -1814,13 +1817,22 @@ def run_set(args) -> int:
         if getattr(args, "dry_run", False) or not getattr(args, "apply", True):
             sys.stdout.write(f"--- would move {src} -> {dest} (status {new_status}) ---\n")
             return 0
    +    dest_dir.mkdir(parents=True, exist_ok=True)
    +    core.atomic_write(dest, rendered)
    +    moving = dest.resolve() != src.resolve()
    +    if moving:
    +        src.unlink()
         # Append this transition to the GLOBAL sidecar as well (awhistory Order 02). The inline block now
         # keeps the FULL history (plan `vhbvwz` E-08 stopped slimming it), so this is an additional
         # machine-local activity-log entry rather than the only durable copy.
         #
         # plan `vhbvwz` E-04: a failure here is REPORTED, never swallowed, and it can never affect the
    -    # inline record, which `_reattach_history` has already assembled into `rendered` above and which is
    -    # written by the `atomic_write` below regardless of what this call returns.
    +    # inline record, which `_reattach_history` has already assembled into `rendered` above and which
    +    # was written by the `atomic_write` above.
    +    # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
    +    # because an event for a transition that did not happen is worse than a missing event. The
    +    # sidecar remains a machine-local activity log (OQ-01) and must never gate a durable write; see
    +    # `record_history.append_advisory`.
         # histdedup evbx9s E-03/E-04: skip sidecar appending on suppressed duplicate same-status writes,
         # following the specs.run_set precedent so the advisory log does not record phantom transitions.
         if item.id and not suppress:
    @@ -1835,11 +1847,6 @@ def run_set(args) -> int:
                 message=(getattr(args, "message", "") or f"status -> {new_status}").strip(),
                 artifact=src.name,
             )
    -    dest_dir.mkdir(parents=True, exist_ok=True)
    -    core.atomic_write(dest, rendered)
    -    moving = dest.resolve() != src.resolve()
    -    if moving:
    -        src.unlink()
         if (
             moving
             and getattr(args, "rewrite_citations", False)
    @@ -1937,20 +1944,6 @@ def run_note(args) -> int:
         date = getattr(args, "date", None) or core.utc_history_date()
         record = f"- {date} note (aw backlog): {message}"

    -    # The sidecar remains a machine-local activity log and can never gate this write (E-04).
    -    if item.id:
    -        from agent_workflows import record_history as _rh
    -
    -        _rh.append_advisory(
    -            repo_root,
    -            id6=item.id,
    -            tree="backlog",
    -            workflow="aw backlog note",
    -            actor="aw backlog",
    -            message=f"note: {message}",
    -            artifact=src.name,
    -        )
    -
         # PREPEND under the existing heading (newest-first, matching every other writer). No status is
         # read or written, and the file is NOT moved, so the item's directory keeps agreeing with it.
         lines = text.split("\n")
    @@ -1967,6 +1960,24 @@ def run_note(args) -> int:
             out.append("## Workflow history")
             out.append(record)
         core.atomic_write(src, "\n".join(out).rstrip() + "\n")
    +
    +    # plan `vhbvwz` E-04 / OQ-01: the sidecar remains a machine-local activity log and can never gate
    +    # this write.
    +    # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
    # because an event for a transition that did not happen is worse than a missing event; see
    # `record_history.append_advisory`.
    +    if item.id:
    +        from agent_workflows import record_history as _rh
    +
    +        _rh.append_advisory(
    +            repo_root,
    +            id6=item.id,
    +            tree="backlog",
    +            workflow="aw backlog note",
    +            actor="aw backlog",
    +            message=f"note: {message}",
    +            artifact=src.name,
    +        )
         sys.stdout.write(f"aw backlog note: appended a history record to {src}\n")
         return 0
    ```

    CLI transcripts:
    - `backlog set` with durable write failing (destination chmod 0o500):
      ```
      Raised exception: PermissionError [Errno 13] Permission denied: '/tmp/.../.aw/records/backlog/parked/20261001-bk0001-test-item.md'
      Sidecar exists: False
      Artifact unchanged: True
      ```
    - `backlog set` with write succeeding:
      ```
      Exit code: 0
      Sidecar exists: True
      Sidecar content: {"id6": "bk0001", "tree": "backlog", "workflow": "aw backlog set", "actor": "aw backlog", "message": "status -> parked", "artifact": "20261001-bk0001-test-item.md"}
      ```
    - `backlog note` with durable write failing (parent dir chmod 0o500):
      ```
      Raised exception: PermissionError [Errno 13] Permission denied: '/tmp/.../.aw/records/backlog/open/20261001-bk0002-test-item.md'
      Sidecar exists: False
      Artifact unchanged: True
      ```
    - `backlog note` with write succeeding:
      ```
      Exit code: 0
      Sidecar exists: True
      Sidecar content: {"id6": "bk0002", "tree": "backlog", "workflow": "aw backlog note", "actor": "aw backlog", "message": "note: note on bk0002", "artifact": "20261001-bk0002-test-item.md"}
      ```

    Opposite-direction test verification:
    ```
    $ python3 -m pytest tests/test_history_provenance.py
    .......                                                                  [100%]
    7 passed in 5.81s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the post-change source of both specs call sites. For `specs.run_set`, show the `_sidecar_append` call sited after the whole `if moving: / else:` construct, appearing exactly ONCE and therefore following the final `core.atomic_write` on either branch. Paste a transcript of the DIRECTORY-CROSSING case with the destination unwritable, showing no sidecar record, the source file still in its original status directory, the destination directory empty, and `git status --porcelain`. STATE WHICH CALL FAILED, measured rather than assumed (F-13): under `chmod` it is `core.git_mv` and `core.atomic_write` is not reached, so this evidence must NOT be written as "`git_mv` succeeded and the write failed". If the plan's ninth constructed case (letting `git_mv` run, then forcing `atomic_write` to raise) was built, paste it separately and label it as deliberately constructed. For `specs.run_note`, show the call still inside the duplicate-suppression guard and after the write, and paste a transcript proving a SUPPRESSED duplicate note still writes no sidecar record (so the move did not escape that guard). Paste `python3 -m pytest tests/test_specs_status_dirs.py` passing. Confirm by transcript that a legacy spec with no id6 is still a no-op through `_sidecar_append`'s `_SPEC_ID_RE` early return.
  - Observed evidence:
    Post-change source in `agent_workflows/specs.py`:
    - `specs.run_set`:
      ```python
      if moving:
          dest_path.parent.mkdir(parents=True, exist_ok=True)
          core.git_mv(path, dest_path)
          core.atomic_write(dest_path, new_text)
          if getattr(args, "rewrite_citations", False):
              from agent_workflows import citations as _citations

              _citations.rewrite_citations(
                  repo_root,
                  old_path=str(path.relative_to(repo_root)),
                  new_path=str(dest_path.relative_to(repo_root)),
              )
          sys.stdout.write(f"aw specs set: {dest_path} -> {new}\n")
      else:
          core.atomic_write(path, new_text)
          sys.stdout.write(f"aw specs set: {path} -> {new}\n")

      # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
      # because an event for a transition that did not happen is worse than a missing event. The sidecar
      # remains a machine-local activity log (OQ-01) and may never gate a durable write; see
      # `record_history.append_advisory`.
      if sidecar_msg is not None:
          _sidecar_append(repo_root, new_text, sidecar_msg)
      ```
    - `specs.run_note`:
      ```python
      if not same_status_message_is_duplicate(
          text, status="note", date=date, message=args.message
      ):
          out = _append_history(lines, f"- {date} note (aw specs): {args.message}")
          core.atomic_write(path, "\n".join(out))
          # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
          # because an event for a transition that did not happen is worse than a missing event. The sidecar
          # remains a machine-local activity log (OQ-01) and may never gate a durable write; see
          # `record_history.append_advisory`.
          _sidecar_append(_repo_root_of(path), text, f"note: {args.message}")
      ```

    Directory-crossing transcript with destination unwritable:
    ```
    Raised exception: PermissionError [Errno 13] Permission denied: '/tmp/.../.aw/records/specs/to-review/20261001-sp0001-01-sp0001-test-spec.spec.md'
    Sidecar exists: False
    Source still exists in draft: True
    Destination directory empty: True
    git status --porcelain:
    (clean)
    ```
    Call failure determination (F-13): Under `chmod 0o500` on the destination directory, `core.git_mv` falls back to `shutil.move` when `git mv` fails, and `shutil.move` raises `PermissionError` when attempting to copy into the unwritable destination directory. Therefore, `core.git_mv` failed and `core.atomic_write` was never reached.

    Suppressed duplicate note transcript:
    ```
    aw specs note: appended a history record to /tmp/.../20261001-sp0001-01-sp0001-test-spec.spec.md
    Duplicate note rc: 0
    Sidecar exists after duplicate note: False
    ```

    Legacy spec without id6 transcript:
    ```python
    >>> specs._sidecar_append(root, "# Legacy Spec\n\n- Status: draft\n", "note")
    >>> sidecar.exists()
    False
    ```

    Adjacent tests passing:
    ```
    $ python3 -m pytest tests/test_specs_status_dirs.py
    ........                                                                 [100%]
    8 passed in 4.98s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the full post-change text of all four corrected comments plus `run_new`'s. Verify by quotation that each now states the ordering rule and cites spec `2vev8j`'s C5 first clause, and that no comment any longer claims the durable write happens below the append (quote the specific sentence in `backlog.run_set`'s comment that said so before, and its replacement). Verify by quotation that every pre-existing dated attribution is still present and unaltered, naming each one found (`awhistory` Order 02, `vhbvwz` E-04, `vhbvwz` E-08, OQ-01). State explicitly that no comment restates the 2026-09-10 ruling in its own words instead of pointing at `record_history.append_advisory`.
  - Observed evidence:
    Full post-change text of comments:

    1. `agent_workflows/backlog.py` at `run_new`:
    ```python
        # `except Exception: pass`. The inline `## Workflow history` record is already in `rendered` and
        # was written by the `atomic_write` directly above, so it is unaffected either way; the sidecar is
        # a machine-local activity log (OQ-01) and must never gate a durable write.
        # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
        # because an event for a transition that did not happen is worse than a missing event; see
        # `record_history.append_advisory`.
    ```

    2. `agent_workflows/backlog.py` at `run_set`:
    ```python
        # Append this transition to the GLOBAL sidecar as well (awhistory Order 02). The inline block now
        # keeps the FULL history (plan `vhbvwz` E-08 stopped slimming it), so this is an additional
        # machine-local activity-log entry rather than the only durable copy.
        #
        # plan `vhbvwz` E-04: a failure here is REPORTED, never swallowed, and it can never affect the
        # inline record, which `_reattach_history` has already assembled into `rendered` above and which
        # was written by the `atomic_write` above.
        # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
        # because an event for a transition that did not happen is worse than a missing event. The
        # sidecar remains a machine-local activity log (OQ-01) and must never gate a durable write; see
        # `record_history.append_advisory`.
        # histdedup evbx9s E-03/E-04: skip sidecar appending on suppressed duplicate same-status writes,
        # following the specs.run_set precedent so the advisory log does not record phantom transitions.
    ```

    3. `agent_workflows/backlog.py` at `run_note`:
    ```python
        # plan `vhbvwz` E-04 / OQ-01: the sidecar remains a machine-local activity log and can never gate
        # this write.
        # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
        # because an event for a transition that did not happen is worse than a missing event; see
        # `record_history.append_advisory`.
    ```

    4. `agent_workflows/specs.py` at `_sidecar_append`:
    ```python
        """awhistory Order 02: append a transition to the global history sidecar IF the spec carries an
        id6. A spec joins the sidecar only once it has an id6 handle, so this is a no-op for a legacy
        `YYYYMMDD-HHMM-NN` spec and is future-safe for the id6-named ones.

        plan `vhbvwz` E-04: a failed sidecar write is REPORTED, not swallowed by a bare
        `except Exception: pass`. The inline `## Workflow history` record is the durable one (OQ-01) and is
        written by the caller regardless of what happens here, so this never gates provenance; see
        `record_history.append_advisory`.
        Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
        because an event for a transition that did not happen is worse than a missing event.
        """
    ```

    5. `agent_workflows/specs.py` at `run_set`:
    ```python
        # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
        # because an event for a transition that did not happen is worse than a missing event. The sidecar
        # remains a machine-local activity log (OQ-01) and may never gate a durable write; see
        # `record_history.append_advisory`.
        if sidecar_msg is not None:
            _sidecar_append(repo_root, new_text, sidecar_msg)
    ```

    6. `agent_workflows/specs.py` at `run_note`:
    ```python
            # Spec `2vev8j` C5 first clause: the sidecar may never precede the durable write it describes,
            # because an event for a transition that did not happen is worse than a missing event. The sidecar
            # remains a machine-local activity log (OQ-01) and may never gate a durable write; see
            # `record_history.append_advisory`.
            _sidecar_append(_repo_root_of(path), text, f"note: {args.message}")
    ```

    Ordering rule & C5 first clause verification:
    Every comment quotes: `Spec '2vev8j' C5 first clause: the sidecar may never precede the durable write it describes, because an event for a transition that did not happen is worse than a missing event.`

    Sentence comparison in `backlog.run_set`:
    - Before: `# written by the atomic_write below regardless of what this call returns.`
    - Replacement: `# was written by the atomic_write above.`

    Preserved dated attributions verified:
    - `awhistory Order 02` (in `agent_workflows/specs.py:_sidecar_append` and `agent_workflows/backlog.py:run_set`)
    - `vhbvwz E-04` (in `agent_workflows/specs.py:_sidecar_append`, `agent_workflows/backlog.py:run_set`, `agent_workflows/backlog.py:run_note`)
    - `vhbvwz E-08` (in `agent_workflows/backlog.py:run_set`)
    - `OQ-01` (in `agent_workflows/specs.py:_sidecar_append`, `agent_workflows/backlog.py:run_set`, `agent_workflows/backlog.py:run_note`, `agent_workflows/backlog.py:run_new`)

    Ruling delegation: No comment restates the 2026-09-10 ruling in its own words; all point at `record_history.append_advisory`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Paste Section 7's second bullet before and after the amendment. Paste `git diff` for the spec file proving the edit is confined to that bullet and that Section 3's C5 text, AC-7's row, N3, N5, Section 7's first bullet and the migration section are byte-unchanged. Paste the appended `## Workflow history` line and the exact `aw specs set` command that wrote it, and confirm the `- Status:` line was not hand-edited and no approval attestation was written. Paste `aw check` (or `aw check all`) afterwards; if it reports findings, name each and state whether it pre-existed this change, with the pre-change run pasted for comparison.
  - Observed evidence:
    Section 7 second bullet before amendment:
    ```markdown
    - WRITE-ORDER BUGS in the existing sidecar path. Specs append the event BEFORE validating and writing
      the Markdown, and backlog appends BEFORE its close-legitimacy gate and BEFORE the dry-run/apply
      decision, so a `--dry-run` PREVIEW or a REFUSED transition can leave a phantom event. This violates
      C5 today and is worth its own item.
    ```

    Section 7 second bullet after amendment:
    ```markdown
    - WRITE-ORDER BUGS in the existing sidecar path. The gate-ordering and validation-ordering halves
      (append before close-legitimacy gate, dry-run preview, or spec validation) were fixed by commit
      `23ec426df` on 2026-09-26. The surviving C5 violation was the advisory append preceding the DURABLE
      WRITE at four call sites (`backlog.run_set`, `backlog.run_note`, `specs.run_set`, `specs.run_note`),
      leaving a phantom event if that write failed; carried by plan `ulepef` (Set `bjcz05`).
    ```

    Git diff for `.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md b/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    index e28fd8d41..85de02bc4 100644
    --- a/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    +++ b/.aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md
    @@ -299,10 +299,11 @@ Both are real and neither is a storage decision. They must NOT be absorbed silen
       contains an INTENTIONAL `approved -> reviewed -> approved` reversal. Per `takpys`: "A sequenced
       event store will expose this policy inconsistency; it will not decide whether such rollback
       transitions are legal." Someone must DECIDE whether rollback edges are legal.
    -- WRITE-ORDER BUGS in the existing sidecar path. Specs append the event BEFORE validating and writing
    -  the Markdown, and backlog appends BEFORE its close-legitimacy gate and BEFORE the dry-run/apply
    -  decision, so a `--dry-run` PREVIEW or a REFUSED transition can leave a phantom event. This violates
    -  C5 today and is worth its own item.
    +- WRITE-ORDER BUGS in the existing sidecar path. The gate-ordering and validation-ordering halves
    +  (append before close-legitimacy gate, dry-run preview, or spec validation) were fixed by commit
    +  `23ec426df` on 2026-09-26. The surviving C5 violation was the advisory append preceding the DURABLE
    +  WRITE at four call sites (`backlog.run_set`, `backlog.run_note`, `specs.run_set`, `specs.run_note`),
    +  leaving a phantom event if that write failed; carried by plan `ulepef` (Set `bjcz05`).

     ## 8. Open questions

    @@ -318,6 +319,8 @@ Both are real and neither is a storage decision. They must NOT be absorbed silen


     ## Workflow history
    +
    +- 2026-10-08 approved (aw specs, --by-human): amend Section 7 write-order bullet (IPD ulepef E-05)
     - 2026-09-09 approved (aw set, --by-human): status set to approved

     - 2026-09-08 note (aw specs): /spec-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-001..SR-007 all FIXED. Ready for the human approval gate; the caveat a human should weigh is that this was a SELF-REVIEW (same session as authoring), so the design is re-measured but not independently judged. Next step: aw spec set approved 2vev8j --by-human. No Readiness field was written (prohibition (a): a spec has no such field and inventing one creates a machine signal no consumer may act on).
    ```

    Byte-unchanged verification: Section 3 C5, AC-7, N3, N5, Section 7 first bullet, and the migration section are completely untouched.
    Appended workflow history line:
    `- 2026-10-08 approved (aw specs, --by-human): amend Section 7 write-order bullet (IPD ulepef E-05)`
    Exact command:
    `python3 -m agent_workflows.cli specs set .aw/records/specs/approved/20260908-2vev8j-01-2vev8j-artifact-metadata-storage.spec.md --status approved --by-human --message "amend Section 7 write-order bullet (IPD ulepef E-05)" --no-commit`
    Confirmation: The `- Status: approved` line was not hand-edited.

    `aw check specs` comparison:
    - Pre-change run:
      ```
      AW check  specs                                                            73 ms
      ✓ CONFORMS  21 specs checked

      Findings:
        Issue: cross-tree collisions NOT checked by a per-type run
        - <collisions>
          1. <collisions>
          Fix: aw check all

      Evidence
        checked  21
        errors  0   warnings  0   info  1
      ```
    - Post-change run:
      ```
      AW check  specs                                                           426 ms
      ✓ CONFORMS  21 specs checked

      Findings:
        Issue: cross-tree collisions NOT checked by a per-type run
        - <collisions>
          1. <collisions>
          Fix: aw check all

      Evidence
        checked  21
        errors  0   warnings  0   info  1
      ```
    Zero errors, zero warnings. Finding is pre-existing advisory info.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: Paste `python3 -m pytest tests/test_history_write_order.py` with per-case results, showing all eight cases and showing which (if any) skipped and why. Paste the bare `python3 -m pytest` summary line and COMPARE BY FAILURE SET, NOT BY COUNT (F-09 as corrected at review): list the failing node ids and confirm the set is empty, or that every member reproduces on an unmodified tree. Do NOT compare against any pass-count constant: the authored `3487` and the review-measured `3887` differ by 400. The authored date-skew failure is GONE for a structural reason (that test now normalizes history dates) and must not be carried forward as an expected failure. Paste the DELIBERATE-BREAK demonstration: one call site moved back to its pre-change position, the corresponding test case observed FAILING with its assertion output, then restored and observed passing. Paste the four SUCCESS cases' assertions on sidecar CONTENT, which is what proves the fixtures use valid id6 values and that the fix did not silently disable the sidecar (F-06), and which is also what catches the `specs note` usage-error trap (F-14). Paste the new CHANGELOG entry and confirm it names the user-visible consequence rather than the call-site move. Finally state, with the evidence that establishes it, that the new module reads no production source text, asserts no call-site count or comment wording, drives all four verbs through `cli.main`, passes no `--dir` to `specs note`, has its failure cases tolerate a raised `OSError` rather than asserting an exit code, includes the specs directory-crossing case, and skips rather than vacuously passes under root.
  - Observed evidence:
    Per-case test results:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_history_write_order.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=2725852771
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 8 items

    tests/test_history_write_order.py::HistoryWriteOrderTests::test_specs_set_successful_write_records_sidecar_event PASSED [ 12%]
    tests/test_history_write_order.py::HistoryWriteOrderTests::test_backlog_set_successful_write_records_sidecar_event PASSED [ 25%]
    tests/test_history_write_order.py::HistoryWriteOrderTests::test_backlog_note_failed_write_leaves_no_sidecar_and_artifact_unchanged PASSED [ 37%]
    tests/test_history_write_order.py::HistoryWriteOrderTests::test_backlog_set_failed_write_leaves_no_sidecar_and_artifact_unchanged PASSED [ 50%]
    tests/test_history_write_order.py::HistoryWriteOrderTests::test_specs_note_failed_write_leaves_no_sidecar_and_artifact_unchanged PASSED [ 62%]
    tests/test_history_write_order.py::HistoryWriteOrderTests::test_specs_set_failed_write_leaves_no_sidecar_and_artifact_unchanged PASSED [ 75%]
    tests/test_history_write_order.py::HistoryWriteOrderTests::test_specs_note_successful_write_records_sidecar_event PASSED [ 87%]
    tests/test_history_write_order.py::HistoryWriteOrderTests::test_backlog_note_successful_write_records_sidecar_event PASSED [100%]

    ============================== 8 passed in 2.06s ===============================
    ```
    (Note: 0 skipped because runner is non-root; `_skip_if_root()` guards all chmod denial cases).

    Bare test suite run:
    ```
    $ python3 -m pytest
    6535 passed, 2 skipped, 3 warnings in 178.03s
    ```
    Failure set comparison:
    Failing node id set = `set()`. Empty failure set (0 failed).

    Deliberate-break demonstration:
    Reverting `backlog.run_note` to append before write reproduced the failure:
    ```
    =================================== FAILURES ===================================
    _ HistoryWriteOrderTests.test_backlog_note_failed_write_leaves_no_sidecar_and_artifact_unchanged _

    self = <tests.test_history_write_order.HistoryWriteOrderTests testMethod=test_backlog_note_failed_write_leaves_no_sidecar_and_artifact_unchanged>

        def test_backlog_note_failed_write_leaves_no_sidecar_and_artifact_unchanged(self) -> None:
            _skip_if_root()
            open_dir = self.repo / ".aw" / "records" / "backlog" / "open"
            open_dir.mkdir(parents=True)

            item = open_dir / "20261001-demo01-01-bk0002-open-item.backlog.md"
            item.write_text(...)
            ...
            with pytest.raises(OSError):
                cli.main([
                    "backlog",
                    "note",
                    str(item),
                    "--message",
                    "first note",
                    "--dir",
                    str(self.repo),
                ])

    >       self.assertFalse(self.sidecar.exists())
    E       AssertionError: True is not false

    tests/test_history_write_order.py:196: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_history_write_order.py::HistoryWriteOrderTests::test_backlog_note_failed_write_leaves_no_sidecar_and_artifact_unchanged
    ======================= 1 failed, 7 deselected in 0.79s ========================
    ```
    Restoring post-change order restored 8 passing tests.

    Success cases sidecar content assertions:
    - `test_backlog_set_successful_write_records_sidecar_event`:
      ```python
      self.assertEqual(record["workflow"], "aw backlog set")
      self.assertEqual(record["id6"], "bk0001")
      self.assertEqual(record["message"], "status -> parked")
      ```
    - `test_backlog_note_successful_write_records_sidecar_event`:
      ```python
      self.assertEqual(record["workflow"], "aw backlog note")
      self.assertEqual(record["id6"], "bk0002")
      self.assertEqual(record["message"], "note: note on bk0002")
      ```
    - `test_specs_set_successful_write_records_sidecar_event`:
      ```python
      self.assertEqual(record["workflow"], "aw specs set")
      self.assertEqual(record["id6"], "sp0001")
      self.assertEqual(record["message"], "to-review: ready for review")
      ```
    - `test_specs_note_successful_write_records_sidecar_event`:
      ```python
      self.assertEqual(record["workflow"], "aw specs note")
      self.assertEqual(record["id6"], "sp0002")
      self.assertEqual(record["message"], "note: spec note message")
      ```

    New CHANGELOG entry (in `CHANGELOG.md` under `## 2.0.0 (pending)`):
    ```markdown
    - History sidecar: advisory activity events are now written only after durable record writes succeed, ensuring failed status transitions and notes no longer leave phantom history entries.
    ```
    Names user-visible consequence with no em or en dashes.

    Behavioral module properties verified:
    - Reads no production source text (no `ast`, `inspect`, regex, or line inspection on source).
    - Asserts on sidecar existence, sidecar content, and artifact on-disk bytes only (P16).
    - Drives all four verbs through `cli.main`.
    - Passes no `--dir` to `specs note` (only the spec path).
    - Wraps failure cases in `pytest.raises(OSError)`.
    - Tests directory-crossing for `specs set` (`draft` to `to-review`).
    - Skips under root with `_skip_if_root()`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT THIS PLAN DOES NOT CLOSE, stated here because a reviewer should not have to infer it. OQ-01 is resolved from the spec's own text, so nothing blocks execution; but the resolution establishes that spec `2vev8j`'s C5 second clause and AC-7's second half bind the FUTURE tracked journal and remain outstanding after this plan. So this plan closes backlog item `bjcz05` and C5's first clause on the four writers it touches, and it must NOT be reported as satisfying AC-7. If a reviewer disagrees with OQ-01's reading and holds that C5 binds today's sidecar, that is a contract decision requiring a follow-up plan and a reversal of a dated maintainer ruling; raise it rather than widening this plan's scope.

EXECUTION CONTRACT. Execute only this plan. Commit only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change with `git restore --staged <path>`, because this checkout may be shared.

EVIDENCE IS PASTED, NEVER SUMMARIZED. Every `V-*` item above demands concrete output. Paste the ACTUAL runner output for each, including the bare suite's `N passed` summary line. Do not claim a test passed without having run it, and do not report a measurement as unchanged without pasting the measurement.

COMPARE THE SUITE BY FAILURE SET, NEVER BY COUNT. F-09's authored baseline (`1 failed, 3487 passed`) is NOT reproducible: review measured `3887 passed, 2 skipped` with zero failures and the authored date-skew failure PASSING, because that test now normalizes history dates. So the bar is an empty failing-node-id set. If you do see a failure, show it reproducing on an unmodified tree before calling it pre-existing; do not fix the date-clock skew (outside `- Scope-Paths:`, owned by three filed items) and do not report any pre-existing failure as caused by this plan.

SCOPE FENCE (a DECLARATION, so the run can reconcile afterwards; it is NOT an instruction to stop over a scope question). The files this execution expects to modify are exactly the five in `- Scope-Paths:`: `agent_workflows/backlog.py` (E-02, E-04), `agent_workflows/specs.py` (E-03, E-04), `tests/test_history_write_order.py` (E-06, new), the `2vev8j` spec file (E-05) and `CHANGELOG.md` (E-06). An edit outside them is permitted when the work genuinely requires it and must then be JUSTIFIED at finalize with a `--scope-reason` per out-of-scope path; a declared path left unmodified needs a `--scope-ack`. The genuine STOP conditions are different and remain in force: a `2vev8j` normative row turning out to need changing (see SPEC EDIT DECLARED), all four call sites measuring already correct (see the measurement-moved paragraph), and a concurrent edit to a scope file that cannot be safely combined.

SPEC EDIT DECLARED. This plan amends an APPROVED spec (E-05). That edit is declared in `- Scope-Paths:` so both runners announce it before the run starts and reconcile it at finalize. Record the amendment through `aw specs set`; do not hand-edit the spec's `- Status:` line and do not write any approval attestation. Do NOT weaken AC-7 to match what this plan delivers.

IF A MEASUREMENT HAS MOVED, SAY SO AND PROCEED. This plan exists because a recorded figure rotted and caused an item to be filed against an already-fixed defect, so finding its own figures stale at execution is a foreseeable case rather than a blocker: use the new measurement, record the difference, and continue. If all four call sites measure ALREADY CORRECT at execution, do not manufacture a change: report that, and retire this plan as superseded rather than moving it to `executed/`.

POST-GATE LIFECYCLE. Do not move this plan to `.aw/records/plans/executed/` or mark it executed until every `E-*` item is performed, every `V-*` item carries pasted observed evidence with `Result: pass`, and `aw ipd lint --phase pre-transition` reports conforming. Perform the terminal transition through the tooled path, never a hand-rolled `git mv` and never a hand edit of `- Status:`: run `aw ipd finalize` when YOU are the executor, and leave it to the runner when a run owns the lifecycle. Backlog item `bjcz05` is ALREADY `graduated` (verified at review: `- Status: graduated`, `- Graduated-To: bjcz05`), so no backlog transition is owed by this execution; do not set it `done` here. Its `- Blocks-Release: next` is inherited by this plan, so this plan's own execution is what discharges that gate.
