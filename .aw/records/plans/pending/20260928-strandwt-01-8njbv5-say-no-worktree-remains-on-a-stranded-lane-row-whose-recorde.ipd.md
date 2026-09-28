# IPD: Say 'no worktree remains' on a stranded-lane row whose recorded worktree is gone

- Date: 2026-09-28
- Kind: child
- Concern: A stranded-lane row OMITS its worktree segment when the recorded tree is absent, so the reader cannot tell "this lane never had a worktree" from "the worktree was reclaimed". Those two need different next acts: the second means recovery is a BRANCH MERGE and not a tree inspection. Worse, measured here, OMISSION HAS A THIRD CAUSE that the obvious one-line fix would mislabel: `lane_worktree_display` also returns None for a tree that EXISTS outside the repository, so a marker keyed on "display is None" would assert a tree is gone when it is there.
- Scope: Add an explicit `no worktree remains` segment to `attention.stranded_lane_drift`'s `bits` assembly, gated on the record HAVING named a worktree that is now provably ABSENT, never merely on the display being omitted. Add a shared predicate beside `runner_shared.lane_worktree_display` so the two rendering decisions cannot drift, and tests pinning the marker's presence in the reclaimed case and its ABSENCE in the never-had-one case, the tree-still-exists case, and the exists-outside-the-repository case.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/runner_shared.py, tests/test_attention.py, tests/test_runner_shared.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: aqb4dv
- Set: strandwt
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: 8njbv5
- Approval: 2026-09-28, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-28 approved (aw set): status set to approved
- 2026-09-28 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-401, PR-402, PR-403, PR-404, PR-405. All twelve authored findings reproduce exactly, including all six cases of F-03, both constructed fixtures, the 34-symbol fingerprint list and the 414-character over-bound row. The design is right: keying on absence rather than on the omitted display is the correct refusal of the backlog item's proposed mechanism. Corrected three executor traps: TWO of E-03's four assertions refute the naive form, not one, so V-03 predicted the wrong failure count (new F-13); the reclaimed fixture swaps which worktree value the record carries, so E-04 must assert on the rendered detail and not on rec['worktree'] (new F-14); and F-02/F-10's live counts had already drifted, now labelled context rather than bars (new F-16). Added F-15 recording that no existing assertion covers the edited segment, OQ-04 recording the unreadable-path fail direction, and a do-not-edit fence naming lane_worktree_display and describe_lane.

- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog item `aqb4dv`, which carries OQ-03 of executed plan `0ta5vg` (stranrep-01). Every measurement in Findings taken in this lane at HEAD `9514ff02` against the run records resolved through `attention._resolve_runs_repo_root`, not carried over from the item. The item's scope line proposed keying the marker on the omitted display; F-03 measures that this MISLABELS an existing tree outside the repository, so the plan keys on absence directly and carries the corrected reasoning in OQ-01. Spec amendment declared: `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` F3a gains one sentence permitting the marker, and is in `- Scope-Paths:`.

## Goal

Make a stranded-lane row say WHICH kind of missing worktree it has, so a reader knows whether to inspect a tree or to merge a branch, WITHOUT ever asserting a tree is gone when it is not. The marker appears exactly when the run record named a worktree and that path is provably absent from disk; in every other omission case the row stays as it is today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: give the renderer a predicate it can key on safely

- [x] E-01 Add a shared predicate to `agent_workflows/runner_shared.py`, beside `lane_worktree_display` and with the same `(repo, worktree)` signature, answering the NARROW question "did the record name a worktree that is now provably ABSENT?". Return True only when the recorded value is truthy AND the resolved path does not exist; return False for a falsy value (no worktree was ever recorded) and False for a path that EXISTS, wherever it exists. Reuse `lane_worktree_display`'s own existence helper semantics rather than writing a second existence test: treat an unreadable path (`OSError`/`RuntimeError`) as ABSENT for the display decision but state in the docstring that this predicate therefore inherits that conservative direction, because the cost is one extra marker rather than a wrong verdict. Put it in `runner_shared` and NOT in `attention`, for the reason `lane_worktree_display`'s docstring already gives for living there: the two decisions read the same field and a second spelling in the renderer is the F-4 drift class this repository has paid for. Do NOT edit `lane_worktree_display` itself, and do NOT edit `describe_lane` (F-06 records that `describe_lane` IS in the pre-move fingerprint fixture's pinned symbol list while `lane_worktree_display` and `stranded_lane_records` are NOT).
  - Depends on: none
  - Expected outcome: A new `runner_shared` predicate that returns True for an absent recorded path, False for a falsy value, and False for an existing path whether inside or outside the repository. `lane_worktree_display`'s source and behavior are byte-identical.
  - Execution state: performed

- [x] E-02 Use that predicate in `attention.stranded_lane_drift`'s `bits` assembly. The existing shape is `display = rs.lane_worktree_display(...)` then `if display: bits.append("worktree {0}".format(display))`; add an `elif` arm that appends the literal `no worktree remains` when the E-01 predicate is True, so the marker sits in the SAME positional slot the worktree segment occupies today and the row's field order does not change. Do not reorder, reword or remove any existing bit. Do not make the marker unconditional on `display` being falsy, which is the item's proposed shape and which F-03 measures to be wrong. Extend the function's docstring with one sentence recording that omission had three causes and only one of them is reported, so the next reader does not re-widen it.
  - Depends on: E-01
  - Expected outcome: A reclaimed-worktree row reads `...; no worktree remains; run <id>: ...`; a row whose tree exists still reads `...; worktree .aw/worktrees/<lane>; ...` unchanged; a row that never named a worktree gains nothing.
  - Execution state: performed

### Task group 2: pin the three cases the marker must NOT claim

- [x] E-03 Add tests to `tests/test_runner_shared.py`, in or beside the existing `LaneWorktreeDisplayExistenceTests` class (which is E-05 of `0ta5vg` and already builds fixtures of this shape in a throwaway repo), asserting the E-01 predicate directly over FOUR inputs: an absent path inside the repository (True), a falsy value (False), an existing path inside the repository (False), and an EXISTING path outside the repository whose parent is not named `worktrees` (False). Assert in the same test that `lane_worktree_display` still returns exactly what it returns today for all four, so the new predicate is proven ADDITIVE rather than a change to the display contract. Build every fixture in a throwaway repo, per that class's own standing rule: this repository holds live `aw/lane/*` branches and in-repo lane worktrees, and a test that touched one could destroy the unintegrated work this surface exists to protect.

  TWO of these four refute the naive `display is None` form, not one, and the plan originally claimed only the fourth did. Measured at review (F-13): the FALSY case also diverges, because a falsy record yields `None` too, so the naive predicate would answer "provably absent" for a lane that never had a worktree and print the marker on exactly the row the item asks it to stay off. Keep both assertions and expect BOTH to go red under the mutation V-03 prescribes; an executor who sees only one red has not reproduced the measurement.
  - Depends on: E-01
  - Expected outcome: Four assertions over the predicate plus four unchanged-display assertions, all passing, with the falsy AND the existing-outside-the-repository cases both failing if the predicate is ever rewritten to key on the omitted display.
  - Execution state: performed

- [x] E-04 Add a rendering test to `tests/test_attention.py` driving the marker through `stranded_lane_drift` itself, not through the predicate, because the item asks for a change to the ROW and a predicate test cannot prove a row changed. This is NET-NEW COVERAGE of that segment rather than a strengthening of an existing assertion: F-15 measures that the only existing test touching this `bits` assembly asserts on `rec.location` alone and drives a sentinel record with no `worktree` key, so nothing today could observe the marker either way.

  Extend `StrandedLaneViewTests`' fixture with a RECLAIMED variant: build the lane exactly as `_fixture` does, commit work in it, then `git worktree remove --force` it, leaving the branch and its commit. Measured in F-04 that this yields one `STRANDED` record with `commits_ahead: 1`, a recorded worktree, and that worktree absent from disk, so the case is genuinely reachable and is not a synthetic contrivance. ASSERT ON THE RENDERED `detail`, NOT ON `rec["worktree"]`, and F-14 is why: `describe_lane` prefers the REGISTERED worktree, so removing the tree deregisters it and the record's `worktree` SWITCHES from the live in-repo path to the fixture's absolute `ABSOLUTE_WORKTREE` value. That swap is a feature here, since it makes the reclaimed case exercise the leak guard on a real absolute home path (measured clean), but an assertion on the record field would be asserting on a value whose identity changes across the remove.

  Assert the detail contains `no worktree remains` and does NOT contain `worktree .aw/worktrees/`; assert the existing `_fixture` (tree present) still contains `worktree .aw/worktrees/lane01` and does NOT contain the marker; and assert a NEVER-HAD-ONE row gains neither, using a run state whose only lane is a `review_sweep_lane` record carrying `branch`/`lane_id`/`base_commit` and NO `worktree` key, which F-05 measures produces one `STRANDED` record with `worktree: None`. Assert in every case that the rendered detail contains no absolute path and no home-directory prefix, since F8a binds every surface and this item adds a new segment to one. Compose any new absolute fixture value at runtime as `ABSOLUTE_WORKTREE` already does; a literal home-directory path in a tracked file fails `aw sanitize`.
  - Depends on: E-02
  - Expected outcome: Three rendered rows pinned by their detail text (reclaimed carries the marker, present carries the path, never-had-one carries neither), plus the leak assertion, all through `stranded_lane_drift`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This bites here in particular: backlog item `aqb4dv` cites `attention.py:1277-1279` as the "None-means-omit contract", and at this HEAD those lines are inside `_plans_record`'s disposition check, which has nothing to do with lanes. The contract it means is `runner_shared.lane_worktree_display`'s documented "returns None so the caller OMITS it", so this plan cites that symbol.
- `aw attention` IS MEASURABLE FROM INSIDE A LANE, and the opposite claim has been written into three plans in this family and refuted by measurement each time. `attention._resolve_runs_repo_root` detects `.aw/worktrees` in the resolved path and walks up to the owning checkout. Verified in THIS lane: the resolved runs root is the main checkout and `discover_run_dirs` returns 300 run directories. Every measurement below prints or states the resolved root for that reason.
- THE SUITE RUNS BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`; `python3 -m pytest` with no added flags is the contract, and a second `-q` would suppress the `N passed` line this plan's validation requires. Use `-o addopts=""` only for a narrowed per-test count.
- THE FIXTURE'S ABSOLUTE PATH IS COMPOSED, NOT WRITTEN AS A LITERAL. `StrandedLaneViewTests.ABSOLUTE_WORKTREE` assembles its home path at runtime with the reason recorded in a comment, because the deterministic leak-sanitizer correctly fails a tracked file containing one even in a fixture. Any new fixture in that class follows the same rule.
- THE DETAIL STRING HAS A DEFINED BOUND AND THE MARKER FITS. Spec Section 8.8 requires descriptive fields to be bounded, and `attention_contract.MAX_DESCRIPTIVE_LEN` is 300. F-07 measures the margin.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE OMISSION IS REAL AND IS THE SHIPPED BEHAVIOR, so the item describes something live. `runner_shared.lane_worktree_display` returns None for an absent path and `attention.stranded_lane_drift` appends the worktree bit only `if display`, so the segment silently vanishes. Its docstring states the intent: "IT ALSO OMITS A WORKTREE THAT IS NOT THERE, because a row asserting a directory that was reclaimed months ago sends the reader to inspect a tree that does not exist." | Read of both symbols at HEAD `9514ff02`. |
| F-02 | THE POPULATION IS OVERWHELMINGLY THE RECLAIMED CASE, which is what makes the marker worth adding at all. Over all 298 readable run records in the resolved main checkout, `stranded_lane_records(..., attention_only=False)` returns 519 lane records: 514 name a worktree that is ABSENT from disk, 5 name one that EXISTS, and ZERO fail to name one. So the overwhelming majority of rows are exactly the case the reader currently cannot distinguish. THESE DIGITS ARE A LIVE POPULATION AND ARE CONTEXT, NEVER A BAR: they had already drifted by review (F-16 re-measures 538 records, 531 absent / 7 exists / 0 unrecorded). The PROPERTY that must hold, and which any re-derivation must confirm, is that the absent case dominates and the never-recorded case is absent from the live corpus. | Probe over `run_viewer.discover_run_dirs` + `stranded_lane_records` with `worktree_lease.memoize_worktrees`, classifying each record's `worktree` by `Path.exists()`. Re-derived at review; see F-16. |
| F-03 | **THE ITEM'S PROPOSED KEY IS WRONG, AND THIS IS THE MOST IMPORTANT FINDING.** The item scopes the change to the `bits` list, where the available signal is `display is None`; but omission has THREE causes, not two. Measured over six inputs against a throwaway repo: falsy -> None; inside-repo ABSENT -> None; inside-repo EXISTS -> `.aw/worktrees/live`; **OUTSIDE-repo EXISTS with a non-`worktrees` parent -> None**; outside-repo EXISTS with a `worktrees` parent -> `.aw/worktrees/abc123`; outside-repo ABSENT -> None. So a marker keyed on the omitted display would print "no worktree remains" for a tree that IS THERE, which is the same class of false assertion (a row that misdirects the reader's next act) that `0ta5vg` E-05 existed to remove. The fix must key on ABSENCE directly. CORRECTED AT REVIEW, IN THIS FINDING'S OWN FAVOUR: the naive form is wrong in a SECOND way this row understated. It also answers True for the FALSY record, since that yields `None` too, so it would print the marker on the never-had-one row the item expressly asks it to stay off. Both wrong answers are pinned by E-03; see F-13. | Six-case probe calling `runner_shared.lane_worktree_display` in a throwaway git repo, printing the display for each; reproduced exactly at review, all six values as stated. Naive-versus-correct divergence probe for the second wrong answer (F-13). |
| F-04 | THE RECLAIMED CASE IS CONSTRUCTIBLE AS A FIXTURE AND CLASSIFIES AS `STRANDED`, so E-04 needs no contrivance. Building a lane worktree, committing in it, then `git worktree remove --force` leaves the branch and its commit: `stranded_lane_records` returns ONE record with `lane_state: STRANDED`, `commits_ahead: 1`, `dirty: False`, a recorded worktree, that worktree absent from disk, and `lane_worktree_display` -> None. | Fixture probe in a throwaway repo mirroring `StrandedLaneViewTests._fixture` plus `git worktree remove --force`. |
| F-05 | THE NEVER-HAD-ONE CASE IS ALSO CONSTRUCTIBLE, which matters because the item explicitly asks that the marker not appear for it and F-02 shows the live corpus contains zero instances to test against. A run state whose only lane is a `review_sweep_lane` record with `branch`/`lane_id`/`base_commit` and no `worktree` key yields one `STRANDED` record with `worktree: None`. `runner_shared.lane_records_including_sweep` builds that record from `review_sweep_lane_record`, forwarding `sweep.get("worktree")`, which is absent. | Fixture probe with `state[runner_shared.REVIEW_SWEEP_LANE_KEY]` set and `queue: []`; printed `worktree: None`. |
| F-06 | THE TWO FUNCTIONS THIS PLAN TOUCHES ARE NOT IN THE PINNED FINGERPRINT SET, so neither edit can break the pure-move proof. `tests/fixtures/runner_shared_premove_fingerprints.json` pins 34 symbols; its lane-related entries are `_lane_records_from_state`, `build_recovery_lane_notice`, `describe_lane`, `disable_lane_prompt`, `format_lane_report` and `print_lane_interrupt_report`. Neither `lane_worktree_display` nor `stranded_lane_records` appears, and this plan edits neither pinned symbol. `0ta5vg` relied on the same reading for its own E-05. | JSON probe of the fixture's `symbols` list, filtered for `lane`/`strand`. |
| F-07 | THE MARKER FITS THE SECTION 8.8 BOUND WITH ROOM TO SPARE. Simulating the amended assembly over all 519 records: the 514 rows that gain the marker run 185 to 223 characters against `MAX_DESCRIPTIVE_LEN` 300, so the longest has 77 characters of headroom; the segment itself costs 21 characters including its separator. One row is ALREADY over the bound at 414 characters (`aw/lane/8l8dgb`, `SUPERSEDED`), and it gains NOTHING from this change because its tree exists, so this plan neither causes nor worsens that. | Probe computing the simulated detail length for every record with and without the marker; per-group min/median/max printed. |
| F-08 | THE PRE-EXISTING OVER-BOUND ROW IS NOT THIS PLAN'S TO FIX, and saying so is honest rather than evasive. `attention.stranded_lane_drift` never calls `attention_contract.is_safe_descriptive`, so the 300-character bound is not enforced on a lane detail today at all; `is_safe_descriptive`'s callers are in `specs`, `backlog` and `check_engine`. The 414-character row is therefore a pre-existing, separately-caused gap that predates this item. Deferred with a carrier rather than silently inherited. | `rg` for `is_safe_descriptive` across `agent_workflows/`, each call site classified; length probe from F-07. |
| F-09 | THE ITEM'S OWN COMPATIBILITY CLAIM CHECKS OUT. Spec F8a forbids an ABSOLUTE path in any surface and F3a as amended by `0ta5vg` says an absent worktree "MUST NOT be rendered"; the marker names no path at all, so it violates neither. F3a's amended sentence is nonetheless phrased as a rendering prohibition ("the worktree segment is OMITTED when the path is absent"), which a strict reader can take to forbid printing anything in that slot, so the amendment in E-02's spec sync is needed to make the marker unambiguously permitted rather than merely unforbidden. | Read of spec F3a's worktree paragraph and F8a in `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`. |
| F-10 | THE MARKER CHANGES ZERO ROWS ON TODAY'S REPORTED SET, and this is stated up front because it is the fact most likely to be mistaken for a reason not to do the work. `stranded_lane_drift` in this lane returns exactly ONE row (`aw/lane/8l8dgb`, `attention.lane-superseded`, `info` severity), and its worktree EXISTS, so it keeps its path segment and gains nothing. The absent-worktree records are all filtered out before rendering (`attention_only=True` reports only lanes needing attention; the live corpus is dominated by `EMPTY`). The change is forward-looking: the next genuinely stranded lane whose tree has been reclaimed is the beneficiary, and F-04 shows that shape is one `git worktree remove` away. THE ROW SET IS A LIVE POPULATION (F-16): reproduced exactly at review, including the 414-character detail, but V-02's bar is the before/after equality measured in the executing tree, never this count. | `attention.stranded_lane_drift(Path("."))` -> 1 record, printed with its rule and detail; `Counter` over `lane_state` for every record. Reproduced at review: same single row, same rule, same severity, detail length 414. |
| F-11 | `aw attention` STAYS READ-ONLY, which spec F3a requires explicitly ("This clause adds NO write of any kind"). Both E-items add only a path-existence read and a string append; no git command, no mutation, no new subprocess. The existence read is already performed today inside `lane_worktree_display`, so this adds no filesystem call that was not already made. | Inspection of the two edits' shape against `lane_worktree_display`'s existing `_exists` call. |
| F-12 | THE MARKER IS A RENDERING DECISION AND NOT A FILESYSTEM-DERIVED VERDICT, which is the line spec F3a draws and which this plan must not cross. `lane_worktree_display`'s docstring already states the distinction for the identical check: "The only question asked is whether ONE already-derived DISPLAY field should be rendered." The lane's `lane_state`, `landed` and `why` all still come from the run record via `classify_lane_integration`; nothing in either edit reads the filesystem to decide a classification. | Read of `lane_worktree_display`'s closing paragraph and of `stranded_lane_drift`'s record loop, confirming `rule` and `severity` derive only from `rec["lane_state"]`. |
| F-13 | **ADDED AT REVIEW. TWO OF E-03's FOUR ASSERTIONS GO RED UNDER THE NAIVE FORM, NOT ONE, so V-03's evidence requirement as authored would have been unsatisfiable as literally written.** E-03 calls the existing-outside-the-repository case "the discriminating one" and V-03 requires showing it "FAILING while the other three pass". Measured over all four inputs with the predicate rewritten as `lane_worktree_display(...) is None`: the FALSY case also fails, because a falsy record yields `None` too, so the naive form answers True ("provably absent") for a lane that never had a worktree - which is exactly the never-had-one row the item explicitly asks the marker NOT to appear on. So the naive form is wrong in TWO ways, the plan's central finding F-03 understates its own case, and an executor following V-03 literally would see two failures where the plan predicted one and could reasonably conclude the fixture was broken. The correction strengthens the plan: the naive form is refuted twice over. | Probe evaluating the naive and correct predicates over E-03's four inputs and printing which assertions diverge from the wanted answer: `['2 falsy', '4 existing-outside-non-lane']`, count 2. |
| F-14 | **ADDED AT REVIEW. THE RECLAIMED FIXTURE E-04 PRESCRIBES SILENTLY SWAPS WHICH `worktree` VALUE THE RECORD CARRIES, and that swap is what makes the test meaningful, so it must be stated or an executor will mis-assert.** `describe_lane` prefers the REGISTERED worktree over the recorded `preserved_worktree` (the fixture's own comment says so). Measured before and after `git worktree remove --force` on the real `_fixture` shape: BEFORE, `rec["worktree"]` is the live in-repo path and the display is `.aw/worktrees/lane01`; AFTER, git deregisters the tree so the fallback takes over and `rec["worktree"]` becomes the fixture's ABSOLUTE home-directory value, whose display is None and for which the marker correctly fires. Two consequences E-04 must carry: the reclaimed case exercises the leak guard on the ABSOLUTE recorded value (which is a strength, and the rendered detail was measured clean of any home-directory prefix and of the absolute string), and an executor asserting on `rec["worktree"]` rather than on the rendered detail would be asserting on a value that changes identity across the remove. | Before/after probe on the `_fixture` shape with `ABSOLUTE_WORKTREE` recorded: `record worktree` went from the in-repo path (`exists: True`, display `.aw/worktrees/lane01`) to the absolute home path (`exists: False`, display `None`, predicate True). Rendered detail via the real `stranded_lane_drift`: no home-directory prefix, no absolute value, no `worktree .aw/worktrees/`. |
| F-15 | **ADDED AT REVIEW. THE ONE EXISTING TEST THAT DRIVES THIS `bits` ASSEMBLY IS UNAFFECTED, so E-02 carries no hidden regression, and saying so is what makes the no-regression claim checkable rather than asserted.** `tests/test_runner_shared.py::test_attention_stranded_lane_drift_delegates_to_shared_records` calls the real `attention.stranded_lane_drift` and then patches `stranded_lane_records` with a sentinel record. That sentinel carries NO `worktree` key, so it is the never-had-one shape and gains nothing under the correct predicate; and the test asserts only on `rec.location`, never on `detail`, so it could not see the marker either way. The honest statement is therefore that no existing assertion covers the segment this plan edits, which is precisely why E-04 is required rather than optional. | Read of that test's two assertions (both `[rec.location for rec in ...]`); probe confirming the sentinel's `worktree` is `None`, its display `None`, and the correct predicate `False`. |
| F-16 | **ADDED AT REVIEW. F-02's COUNTS ARE A LIVE POPULATION AND HAVE ALREADY DRIFTED SINCE AUTHORING, so they are context and must never become an acceptance bar.** The plan states 298 readable records, 519 lane records, 514 absent / 5 exists / 0 unrecorded. Re-measured in this lane four hours later through the same probe shape: 302 run dirs, 301 readable, 538 lane records, 531 absent / 7 exists / 0 unrecorded, and the `lane_state` census is 532 `EMPTY` / 1 `SUPERSEDED` / 3 `LIVE` / 2 `LANDED` against the plan's 515/1/1/2. Every CONCLUSION the plan draws from these numbers survives unchanged and is in fact reinforced: the reclaimed case still dominates overwhelmingly, and the never-had-one case is still ZERO in the live corpus (which is why F-05's constructed fixture is necessary). Only the digits moved. Flagged because the repository's own convention forbids a live-artifact count as a success criterion, and because a validation item comparing against a stale figure would fail for the wrong reason. | Re-ran the F-02 probe shape (`discover_run_dirs` + `stranded_lane_records(attention_only=False)` under `memoize_worktrees`) and the `lane_state` Counter in this lane; printed the resolved runs root to confirm the same target as the plan's own measurement. |

## Proposed changes (ordered, validatable)

1. Add a `(repo, worktree)` predicate to `runner_shared` beside `lane_worktree_display` that is True only for a recorded path that is provably absent, and False for a falsy value or for any path that exists (E-01).
2. Append a `no worktree remains` bit in `attention.stranded_lane_drift` as an `elif` on that predicate, in the slot the worktree segment already occupies, with a docstring sentence recording that omission had three causes and only one is reported (E-02).
3. Pin the predicate over four inputs in `tests/test_runner_shared.py`, including the TWO cases that discriminate it from the naive display-is-None form (falsy and existing-outside-the-repository; F-13), plus four assertions that `lane_worktree_display`'s own answers are unchanged (E-03).
4. Pin the rendered ROW in `tests/test_attention.py` over three fixtures (reclaimed, present, never-had-one) through `stranded_lane_drift`, asserting on the rendered `detail` rather than on `rec["worktree"]` (F-14), with a leak assertion on each (E-04).
5. Amend spec F3a with one sentence permitting the marker, and record why in the spec-sync section (E-02's spec sync; the spec file is in `- Scope-Paths:`).

## Deferred / out of scope (with reason)

- THE PRE-EXISTING OVER-BOUND LANE DETAIL is not fixed here. F-07 and F-08 measure one live row at 414 characters against a 300-character Section 8.8 bound, and that `attention.stranded_lane_drift` never applies `is_safe_descriptive` to a lane detail at all. Fixing it means either truncating a field the spec says must not be silently truncated, or emitting a new `attention.unsafe-field` violation for a row the gate already reports, and both are decisions about the output-safety contract rather than about this item's wording question. This plan measures the margin and provably does not worsen it: the row in question gains nothing because its tree exists.
  - Carrier: hv8zlg
- MARKING WHICH KIND OF ABSENCE occurred (never-created versus reclaimed-after-use) is not attempted. The run record carries `preserved_disposition` and a per-attempt `worktree_disposition`, so a richer taxonomy is conceivable, but the item asks for the reader to be able to act, and "no worktree remains" already answers the act question (merge the branch, do not inspect a tree). Adding a second axis would need its own measurement of how reliably those disposition fields are populated across 298 records, which is a separate question.
  - Carrier-Declined: There is nothing owed. This is a rejected ENLARGEMENT of the item's question, not an unmet part of it: the item asks only whether the row should say "no worktree remains" rather than omitting the field, and this plan answers that in full. A carrier would name an obligation no artifact holds and nobody has asked for.
- CHANGING WHICH LANES ARE REPORTED, or any lane's `lane_state`, `severity`, rule id or exit-code contribution, is explicitly rejected rather than deferred. This plan adds one display segment. If `aw attention --check`'s exit code or the reported row COUNT changes, the plan has failed; V-04 is the check that catches it.
  - Carrier-Declined: This row records a PROHIBITION on this plan, not an outstanding defect. The reported set is correct today and no future work is owed; the prohibition is enforced inside this plan by V-04.
- RENDERING A WORKTREE THAT EXISTS OUTSIDE THE REPOSITORY is left exactly as it is: omitted, per F8a, because the only truthful rendering would be an absolute path. F-03 measures this case as reachable, and this plan's contribution is to stop it being MISLABELLED as gone. Whether such a tree deserves a distinct marker of its own ("worktree is outside this repository") is a question about F8a's omission rule, not about this item.
  - Carrier-Declined: Nothing is owed after E-01 lands. The harm this row describes (a reader misled about an out-of-repo tree) is CLOSED by this plan rather than deferred by it, since the predicate returns False for it and no marker is printed. What is left undone is an additive new marker nobody has requested, and E-03's fourth assertion pins the correct behavior permanently.

## Scope check

- Over-scope: none. `agent_workflows/runner_shared.py` carries only E-01's new predicate, with `lane_worktree_display`, `describe_lane` and `stranded_lane_records` untouched; `agent_workflows/attention.py` carries only E-02's `elif` arm and its docstring sentence; the two test files carry E-03 and E-04; the spec carries one amended sentence in F3a. No rule id, severity, schema version or exit-code path changes, and `SCHEMA_VERSION` stays 4 because no payload KEY is added (the marker is inside the existing `detail` string).
- Under-scope: The pre-existing over-bound detail row survives (deferred above with a carrier obligation), and no new marker is added for a tree that exists outside the repository (deferred above, declined with reason). After this plan, a reclaimed worktree is stated rather than implied, and the three omission causes are distinguished in code and in tests. CONFIRMED AT REVIEW that no existing assertion covers the segment being changed (F-15), so E-04 is net-new coverage and its absence would leave the marker untested; and that the two functions this plan must not touch (`lane_worktree_display`, `describe_lane`) are named in the gate with the reason for each.

## Required tests / validation

- `python3 -m pytest` run BARE, with its `N passed` summary line pasted, compared against a baseline captured BEFORE any edit. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `python3 -m pytest tests/test_attention.py tests/test_runner_shared.py -o addopts=""` for the per-test counts on the two test files this plan edits.
- `python3 -m pytest tests/test_oc_runipd.py tests/test_attention_contract.py tests/test_local_leaks.py -o addopts=""` as the targeted regression set: the files that stub `stranded_lane_drift`, pin the descriptive-field contract, or would catch a home path entering a tracked fixture.
- A DELIBERATE-FAILURE DEMONSTRATION for E-03: temporarily rewrite the predicate as `lane_worktree_display(...) is None`, show the fourth assertion (existing tree outside the repository) FAILING while the other three pass, then restore. That contrast IS finding F-03 and is the reason this plan does not implement what the backlog item literally proposed.
- A DELIBERATE-FAILURE DEMONSTRATION for E-04: temporarily make the marker unconditional on a falsy `display`, show the never-had-one assertion FAILING, then restore.
- A BEFORE/AFTER measurement of `attention.stranded_lane_drift(Path("."))` in the executing tree, printing the resolved runs root, the row count, and each row's rule. The count and every rule id MUST be identical before and after; per F-10 the single live row's detail must also be UNCHANGED, because its worktree exists.
- `aw attention --check` before and after, with the exit code pasted both times, and they must match.
- `aw check` to confirm no new drift, and `aw ipd lint --phase pre-transition` conforming.
- `aw sanitize --agent` before commit, since this plan's evidence blocks quote local command output and the new test adds a fixture path.
- `git diff --cached --name-only` immediately before committing, which must list exactly the five paths in `- Scope-Paths:` and nothing another party changed.

## Spec / documentation sync

`.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` IS in `- Scope-Paths:` and F3a MUST be amended by one sentence.

WHY THE AMENDMENT IS NEEDED RATHER THAN OPTIONAL (F-09). F3a's worktree paragraph, as amended by `0ta5vg`, reads as a rendering PROHIBITION: "the worktree segment is OMITTED when the path is absent and rendered repository-relative when it is present". A strict reader takes that to forbid printing anything in that slot for an absent tree, which is exactly what this plan does print. The amendment must state that an absent recorded worktree MAY be reported by an explicit marker that names NO path, that the marker is keyed on the path being provably absent and never on the display having been omitted (because omission has other causes, F-03), and that F8a is untouched because the marker contains no path. The change is strictly NARROWING in the direction F3a already cares about: it adds information while removing none, and it forbids one wrong implementation.

HOW TO WRITE IT, because this spec has a known hazard. The spec is `- Status: implemented`, so `aw specs set` refuses a transition and `aw specs note` is the permitted surface. That verb DESTROYED a history record on this very spec once (backlog `i8wmte`, measured 2026-09-19 while `0ta5vg` executed the amendment this plan extends); the defect was fixed by executed plan `vhbvwz` so `_append_history` now PREPENDS and PRESERVES priors. Verify that before trusting it: this spec carries NO `- Id:` line, which is the case whose gitignored-sidecar fallback wrote nothing, so a regression here loses the record outright. Count the history records before and after, paste both counts, and confirm the existing `pr5b0t` and `0ta5vg` records are still present by `grep -c`. The spec's `- Status:` stays `implemented` and no transition is attempted.

No user-facing documentation changes: the marker appears only in `aw attention`'s stranded-lane section, whose content is not reproduced in any doc.

## Open questions

### OQ-01: The item scopes the change to the `bits` list, where the only available signal is the omitted display. Is that the right key?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT as NO, key on ABSENCE directly, and this reverses what the item proposed. The item's scope line says "attention.stranded_lane_drift's detail assembly (the 'bits' list)", where the signal in hand is `display` being falsy. F-03 measures six inputs and finds omission has THREE causes: a falsy record, an absent path, and a path that EXISTS OUTSIDE the repository with a non-`worktrees` parent (which `lane_worktree_display` omits to satisfy F8a, since the only truthful rendering would be absolute). Keying on the omitted display would therefore print "no worktree remains" for a tree that is there, reintroducing the same class of false assertion `0ta5vg` E-05 removed. So E-01 adds an explicit absence predicate and E-02 keys on that; E-03's fourth assertion fails for the naive form, which is why that assertion exists. The item's intent is fully honored (its own words are "a test asserting the marker appears only when the record HAD a worktree that is now absent, not when it never had one"); only its proposed mechanism is corrected, and the item did not have this measurement available.

### OQ-02: Where does the predicate live, `runner_shared` or `attention`?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as `runner_shared`, beside `lane_worktree_display`, from the reason that function's own docstring already gives for living there. The two decisions read the SAME field and answer two halves of one question; a predicate in the renderer would be a second reading of `worktree` in a different module, which is the drift class where "a renderer reading one spelling while the producer writes another" has already cost this repository (see `attention.rs_lane_superseded`'s docstring, which re-reads the lane-state token from `runner_shared` for exactly this reason rather than re-spelling it). `attention` imports `runner_shared` lazily already, inside `stranded_lane_drift` itself, so no new import coupling is created. The counter-argument, that the marker is presentation and presentation belongs to the renderer, is answered by noting the predicate is not presentation: it is a fact about the recorded path, and the STRING stays in `attention`.

### OQ-03: Should the marker's wording be the item's "no worktree remains", or something naming the remedy?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: RESOLVED as the item's literal wording, on two grounds. First, the maintainer owns this as a presentation choice (the item records "DECISION OWNER: maintainer") and wrote that exact phrase, so adopting it is the narrowest reading of what was asked; inventing different words would substitute this author's taste for the decision-owner's. Second, the remedy is ALREADY in the row: every detail ends with `lane_remedy_hint`, which names `aw oc integrate <id6>` (verified present in the one live row's detail), so a remedy-naming marker would duplicate it. The wording is a one-line change if the maintainer prefers another phrase at review, and E-04 pins it as a literal so the change would be visible rather than silent. UPHELD AT REVIEW, with the maintainer-ownership point noted as the operative one: the reviewer has no standing to re-decide a presentation choice the item assigns to the maintainer, and the plan correctly takes the narrowest reading rather than treating silence as licence.

### OQ-04: Should the predicate treat an UNREADABLE path (`OSError`/`RuntimeError`) as absent, given that direction prints a marker rather than suppressing one?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode)
- Resolution or deferral rationale: YES, INHERIT `lane_worktree_display`'s CONSERVATIVE DIRECTION, which is what E-01 already specifies; recorded as a question because the two callers' conservative directions point OPPOSITE ways and that is worth stating once rather than leaving a later reader to re-derive it. For the DISPLAY, treating an unreadable path as absent OMITS a segment, which strictly reduces output and cannot leak; the existing `_exists` helper documents exactly that reasoning. For the MARKER, the same treatment ADDS a segment, asserting "no worktree remains" about a path that may well be there but is unreadable (a permission-denied mount, say). So the shared direction is not automatically right and needed checking. It is nonetheless correct here, for a reason E-01 states and this review endorses: the cost is one possibly-superfluous marker on a row that is ALREADY being reported for attention and whose remedy (merge the branch) is unaffected, whereas the alternative (treat unreadable as present, suppress the marker) restores the exact silent ambiguity this item exists to remove, and does so precisely in the case where the reader most needs telling that something is wrong with the path. RESOLVED FROM EVIDENCE rather than asked because it is a fail-direction judgement inside an already-approved rendering contract, not a change to what the surface reports or to any verdict; E-01's docstring requirement makes the inheritance explicit so the next reader sees it was chosen.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Paste the full committed source of the new predicate. Paste `git diff agent_workflows/runner_shared.py` showing the addition and showing ZERO changed lines inside `lane_worktree_display`, `describe_lane` or `stranded_lane_records`. Paste a `python3 -c` probe over the four inputs of E-03 printing the predicate's answer for each, which must be True / False / False / False in the order absent-inside, falsy, existing-inside, existing-outside-non-lane-shape. Paste the JSON probe of `tests/fixtures/runner_shared_premove_fingerprints.json`'s `symbols` list showing the new name is absent from it and that no pinned symbol was edited (F-06).
  - Observed evidence: Verified. Full committed source added to runner_shared.py, diff shows zero lines modified in other functions, four-input probe returns True/False/False/False, and premove fingerprints probe shows symbol absent.
    Full committed source of `lane_worktree_is_absent` from `agent_workflows/runner_shared.py`:
    ```python
    def lane_worktree_is_absent(repo: Path, worktree: Any) -> bool:
        """Answer whether the record named a worktree that is now provably absent from disk.

        Returns True only when ``worktree`` is truthy AND the resolved path does not exist.
        Returns False when ``worktree`` is falsy (no worktree was ever recorded), and False
        when the path exists, whether inside or outside the repository.

        Reuses the same existence semantics as :func:`lane_worktree_display`: an unreadable
        path (raising OSError or RuntimeError) is treated as absent. This predicate therefore
        inherits that conservative direction, because the cost is one extra marker rather than
        a wrong verdict.
        """
        if not worktree:
            return False

        def _exists(path: Path) -> bool:
            try:
                return path.exists()
            except (OSError, RuntimeError):
                return False

        try:
            candidate = Path(str(worktree))
            root = Path(repo).resolve()
            resolved = (
                candidate.resolve()
                if candidate.is_absolute()
                else (root / candidate).resolve()
            )
        except (OSError, RuntimeError, ValueError):
            return True
        return not _exists(resolved)
    ```

    `git diff agent_workflows/runner_shared.py`:
    ```diff
    diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
    index 14794d84..93a5c09d 100644
    --- a/agent_workflows/runner_shared.py
    +++ b/agent_workflows/runner_shared.py
    @@ -2105,6 +2105,40 @@ def lane_worktree_display(repo: Path, worktree: Any) -> Optional[str]:
         return text if text not in ("", ".") else None


    +def lane_worktree_is_absent(repo: Path, worktree: Any) -> bool:
    +    """Answer whether the record named a worktree that is now provably absent from disk.
    +
    +    Returns True only when ``worktree`` is truthy AND the resolved path does not exist.
    +    Returns False when ``worktree`` is falsy (no worktree was ever recorded), and False
    +    when the path exists, whether inside or outside the repository.
    +
    +    Reuses the same existence semantics as :func:`lane_worktree_display`: an unreadable
    +    path (raising OSError or RuntimeError) is treated as absent. This predicate therefore
    +    inherits that conservative direction, because the cost is one extra marker rather than
    +    a wrong verdict.
    +    """
    +    if not worktree:
    +        return False
    +
    +    def _exists(path: Path) -> bool:
    +        try:
    +            return path.exists()
    +        except (OSError, RuntimeError):
    +            return False
    +
    +    try:
    +        candidate = Path(str(worktree))
    +        root = Path(repo).resolve()
    +        resolved = (
    +            candidate.resolve()
    +            if candidate.is_absolute()
    +            else (root / candidate).resolve()
    +        )
    +    except (OSError, RuntimeError, ValueError):
    +        return True
    +    return not _exists(resolved)
    +
    +
     # ---- already-landed dispatch gate (mergeskip `8k0z40`) --------------------------------------------

     ALREADY_LANDED_STATUS: str = "already-landed"
    ```
    The diff shows ZERO lines modified in `lane_worktree_display`, `describe_lane`, or `stranded_lane_records`.

    Four-input probe output:
    ```
    1. absent-inside: True
    2. falsy: False
    3. existing-inside: False
    4. existing-outside-non-lane-shape: False
    ```

    Fingerprints JSON probe:
    ```
    lane_worktree_is_absent in symbols: False
    ```
    No pinned symbol was edited.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/attention.py` in full. It must show ONLY the `elif` arm and the docstring sentence, with the existing `display` bit, every other bit, the `rule`/`severity` derivation and the sort key untouched. Paste the BEFORE/AFTER measurement of `attention.stranded_lane_drift(Path("."))` in the executing tree, printing the resolved runs root, the row count and each row's rule and FULL detail; the rows whose worktree EXISTS must be byte-identical before and after, since only an absent recorded worktree can gain the marker. Re-derive the row set rather than comparing against a number quoted here: review measured ONE row in this lane (`aw/lane/8l8dgb`, `attention.lane-superseded`, `info`, 414 characters, worktree present) but that is a live population which drifts as runs land (F-16), so the BAR is the before/after equality you measure in your own tree, not any count written in this plan. Paste `aw attention --check`'s exit code before and after, which must match. State in one sentence that no `SCHEMA_VERSION` bump was made and why (no payload key added).
  - Observed evidence: Verified. Attention diff shows only elif arm and docstring, before/after stranded_lane_drift row count is 0/0 and valid, aw attention --check exit code matches (0/0), and SCHEMA_VERSION bump not needed.
    `git diff agent_workflows/attention.py`:
    ```diff
    diff --git a/agent_workflows/attention.py b/agent_workflows/attention.py
    index aaf46eb2..d28a8cf1 100644
    --- a/agent_workflows/attention.py
    +++ b/agent_workflows/attention.py
    @@ -1565,7 +1565,10 @@ def stranded_lane_drift(repo_root: Path) -> List[core.Drift]:
         `aw/lane/03ie04`, safe by construction) and the worktree is rendered repository-relative through
         `runner_shared.lane_worktree_display`, which returns None rather than an absolute path. The
         recorded `preserved_worktree` is an absolute home path in most run items, and `integration_detail`
    -    embeds an absolute repository path, so NEITHER is printed.
    +    embeds an absolute repository path, so NEITHER is printed. A worktree omitted from display has
    +    three distinct causes (never recorded, absent from disk, or existing outside the repository); only
    +    the provably absent case reports an explicit 'no worktree remains' marker, while the other two
    +    remain omitted.

         Returns `[]` on any failure to read the run records, which is the honest answer for a repository
         that has never run a driver: absence of run records is not evidence of a stranded lane.
    @@ -1635,6 +1638,8 @@ def stranded_lane_drift(repo_root: Path) -> List[core.Drift]:
             display = rs.lane_worktree_display(target_root, rec.get("worktree"))
             if display:
                 bits.append("worktree {0}".format(display))
    +        elif rs.lane_worktree_is_absent(target_root, rec.get("worktree")):
    +            bits.append("no worktree remains")
             if rec.get("run_id"):
                 # ONE ROW PER LANE, so the row must say how many runs touched it: the per-branch collapse in
                 # `stranded_lane_records` replaced N identical-in-substance rows with one, and dropping the
    ```

    BEFORE measurement of `attention.stranded_lane_drift(Path("."))`:
    ```
    resolved runs repo root: <repo-root>
    row count: 0
    ```

    AFTER measurement of `attention.stranded_lane_drift(Path("."))`:
    ```
    resolved runs repo root: <repo-root>
    row count: 0
    ```
    Both before and after return 0 rows; equality holds identically.

    `aw attention --check` exit code before: 0 (`aw attention --check: the view is valid.`)
    `aw attention --check` exit code after: 0 (`aw attention --check: the view is valid.`)

    No `SCHEMA_VERSION` bump was made because no payload key was added (the marker is inside the existing `detail` string).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Paste the full committed source of the new predicate tests and their passing output from `python3 -m pytest tests/test_runner_shared.py -o addopts=""`. Then paste the DELIBERATE-FAILURE contrast that is this item's whole point: temporarily rewrite the predicate body as `return lane_worktree_display(repo, worktree) is None`, paste the test output, and confirm that EXACTLY TWO assertions go red, the FALSY case and the EXISTING-OUTSIDE-THE-REPOSITORY case, while the absent-inside and existing-inside cases pass. Two, not one: review measured this (F-13) after the plan as authored predicted one, so a run showing a single failure means the fixtures do not match E-03 and must be fixed before this item is verified. Restore and paste green again. Confirm in one sentence that every fixture was built in a throwaway repository and that no `aw/lane/*` branch or `.aw/worktrees/` directory of this checkout was read or written by the test.
  - Observed evidence: Verified. Four predicate tests pass in test_runner_shared, deliberate failure under naive form yields exactly two failures (falsy and existing-outside), tests pass on restore, and all throwaway repo.
    Committed source of the new predicate tests in `tests/test_runner_shared.py`:
    ```python
    def test_predicate_absent_inside_returns_true(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            gone = repo / ".aw" / "worktrees" / "reclaimed"
            self.assertFalse(gone.exists())
            self.assertTrue(runner_shared.lane_worktree_is_absent(repo, str(gone)))
            self.assertIsNone(runner_shared.lane_worktree_display(repo, str(gone)))

    def test_predicate_falsy_returns_false(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            for falsy_val in (None, ""):
                self.assertFalse(
                    runner_shared.lane_worktree_is_absent(repo, falsy_val)
                )
                self.assertIsNone(runner_shared.lane_worktree_display(repo, falsy_val))

    def test_predicate_existing_inside_returns_false(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            live = repo / ".aw" / "worktrees" / "alive"
            live.mkdir(parents=True)
            self.assertTrue(live.exists())
            self.assertFalse(
                runner_shared.lane_worktree_is_absent(repo, str(live))
            )
            self.assertEqual(
                runner_shared.lane_worktree_display(repo, str(live)),
                ".aw/worktrees/alive",
            )

    def test_predicate_existing_outside_non_lane_returns_false(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            repo = _make_lane_fixture_repo(root)
            outside = root / "somewhere_else" / "not_worktrees" / "live_tree"
            outside.mkdir(parents=True)
            self.assertTrue(outside.exists())
            self.assertFalse(
                runner_shared.lane_worktree_is_absent(repo, str(outside))
            )
            self.assertIsNone(
                runner_shared.lane_worktree_display(repo, str(outside))
            )
    ```

    Passing output from `python3 -m pytest tests/test_runner_shared.py -o addopts=""`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=492420728
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 99 items

    tests/test_runner_shared.py ............................................ [ 44%]
    .......................................................                  [100%]

    ============================= 99 passed in 11.85s ==============================
    ```

    DELIBERATE-FAILURE contrast with predicate body temporarily rewritten as `return lane_worktree_display(repo, worktree) is None`:
    ```
    =========================== short test summary info ============================
    FAILED tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_predicate_existing_outside_non_lane_returns_false
    FAILED tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_predicate_falsy_returns_false
    ================== 2 failed, 7 passed, 90 deselected in 0.97s ==================
    ```
    Confirmed: EXACTLY TWO assertions go red (`test_predicate_falsy_returns_false` and `test_predicate_existing_outside_non_lane_returns_false`), while absent-inside (`test_predicate_absent_inside_returns_true`) and existing-inside (`test_predicate_existing_inside_returns_false`) pass.

    Restored green:
    ```
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_predicate_falsy_returns_false PASSED [ 11%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_NO_surface_ever_renders_an_ABSOLUTE_path PASSED [ 22%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_an_ABSENT_worktree_is_OMITTED PASSED [ 33%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_an_absent_worktree_OUTSIDE_the_repository_is_still_omitted PASSED [ 44%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_predicate_existing_inside_returns_false PASSED [ 55%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_predicate_existing_outside_non_lane_returns_false PASSED [ 66%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_predicate_absent_inside_returns_true PASSED [ 77%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_the_guard_protects_the_SUCCESS_return_not_only_the_reconstruction PASSED [ 88%]
    tests/test_runner_shared.py::LaneWorktreeDisplayExistenceTests::test_an_EXISTING_worktree_still_renders_REPOSITORY_RELATIVE PASSED [100%]
    ======================= 9 passed, 90 deselected in 0.83s =======================
    ```

    Confirmation: Every fixture was built inside a `tempfile.TemporaryDirectory()` throwaway repository and no `aw/lane/*` branch or `.aw/worktrees/` directory of this checkout was read or written by the test.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Paste the full committed source of the rendering test and its passing output. Paste, for each of the three fixtures, the ACTUAL rendered `detail` string: the reclaimed one containing `no worktree remains` and not `worktree .aw/worktrees/`, the present one containing `worktree .aw/worktrees/lane01` and not the marker, and the never-had-one one containing neither. Paste the DELIBERATE-FAILURE demonstration for the unconditional form (marker on any falsy `display`), showing the never-had-one assertion red, then restored green; review confirmed this mutation reddens that assertion ALONE, leaving the reclaimed and present rows byte-identical, so exactly one failure is the correct result here (unlike V-03's two). Paste the leak assertion evidence: no rendered detail contains an absolute path or `/home/`, and state that the reclaimed fixture's record carries the ABSOLUTE value at render time (F-14), so this assertion is exercising the real leak shape rather than a benign one. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line and state it against the pre-change baseline captured in the same tree (compare failing NODE IDS, not totals, since the suite is order-randomized and other lanes land concurrently); paste `python3 -m pytest tests/test_attention.py tests/test_runner_shared.py -o addopts=""` and the targeted regression set; paste the spec-amendment evidence required by the spec-sync section (history record counts before and after, plus `grep -c pr5b0t` and `grep -c 0ta5vg` on the spec, all nonzero after); paste `aw check` and state that any error it reports was present BEFORE your edits (review measured two pre-existing errors in this tree, on `4er1ev` and `.aw/system/layout.json`, neither related to this plan); paste `aw ipd lint --phase pre-transition`; paste `aw sanitize --agent`; paste `aw find backlog hv8zlg` confirming the deferred over-bound-detail carrier still resolves and is still live (it was filed at authoring time, so this is a re-check and not a new filing); and paste `git diff --cached --name-only` immediately before committing, which must list exactly the five paths in `- Scope-Paths:` plus this plan.
  - Observed evidence: Verified. Rendering test passes in test_attention, 3 fixture details verified, deliberate failure yields 1 failure on never-had-one, clean leaks, suite passes with 0 regressions, and spec amended.
    Full committed source of the rendering test and fixtures from `tests/test_attention.py`:
    ```python
    def _never_had_one_fixture(self, td: Path) -> Path:
        import subprocess
        from agent_workflows import runner_shared as rs

        root = _mk_repo(td)
        for cmd in (
            ["git", "init", "-q", "-b", "main"],
            ["git", "config", "user.email", "test@example.invalid"],
            ["git", "config", "user.name", "Test"],
        ):
            subprocess.run(cmd, cwd=root, check=True)
        subprocess.run(["git", "add", "-A"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=root, check=True)
        base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()

        # Create a branch with a commit beyond base for the sweep lane
        subprocess.run(["git", "branch", "aw/lane/sweep01", base], cwd=root, check=True)
        subprocess.run(["git", "checkout", "-q", "aw/lane/sweep01"], cwd=root, check=True)
        (root / "sweep.txt").write_text("sweep work\n", encoding="utf-8")
        subprocess.run(["git", "add", "sweep.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "sweep commit"], cwd=root, check=True)
        subprocess.run(["git", "checkout", "-q", "main"], cwd=root, check=True)

        run_dir = root / ".aw" / "records" / "runs" / "run-20260917T000000Z-1"
        run_dir.mkdir(parents=True)
        (run_dir / "state.json").write_text(
            json.dumps(
                {
                    "run_id": "run-20260917T000000Z-1",
                    "repo": str(root),
                    "queue": [],
                    rs.REVIEW_SWEEP_LANE_KEY: {
                        "branch": "aw/lane/sweep01",
                        "lane_id": "sweep01",
                        "base_commit": base,
                    },
                }
            ),
            encoding="utf-8",
        )
        return root

    def test_stranded_lane_worktree_marker_rendering(self):
        # 1. Reclaimed fixture: worktree committed and then removed
        with tempfile.TemporaryDirectory() as td:
            root_reclaimed = self._fixture(Path(td), reclaimed=True)
            with self._holder(False):
                drifts_reclaimed = att.stranded_lane_drift(root_reclaimed)
            self.assertEqual(len(drifts_reclaimed), 1)
            detail_reclaimed = drifts_reclaimed[0].detail
            self.assertIn("no worktree remains", detail_reclaimed)
            self.assertNotIn("worktree .aw/worktrees/", detail_reclaimed)
            self.assertNotIn(self.ABSOLUTE_WORKTREE, detail_reclaimed)
            self.assertNotIn("/home/", detail_reclaimed)

        # 2. Present fixture: worktree exists
        with tempfile.TemporaryDirectory() as td:
            root_present = self._fixture(Path(td))
            with self._holder(False):
                drifts_present = att.stranded_lane_drift(root_present)
            self.assertEqual(len(drifts_present), 1)
            detail_present = drifts_present[0].detail
            self.assertIn("worktree .aw/worktrees/lane01", detail_present)
            self.assertNotIn("no worktree remains", detail_present)
            self.assertNotIn(self.ABSOLUTE_WORKTREE, detail_present)
            self.assertNotIn("/home/", detail_present)

        # 3. Never-had-one fixture: no worktree key
        with tempfile.TemporaryDirectory() as td:
            root_never = self._never_had_one_fixture(Path(td))
            with self._holder(False):
                drifts_never = att.stranded_lane_drift(root_never)
            self.assertEqual(len(drifts_never), 1)
            detail_never = drifts_never[0].detail
            self.assertNotIn("no worktree remains", detail_never)
            self.assertNotIn("worktree .aw/worktrees/", detail_never)
            self.assertNotIn("/home/", detail_never)
    ```

    Passing output:
    ```
    tests/test_attention.py::StrandedLaneViewTests::test_stranded_lane_worktree_marker_rendering PASSED [100%]
    ======================= 1 passed, 38 deselected in 0.51s =======================
    ```

    Actual rendered `detail` strings for the three fixtures:
    - Reclaimed fixture:
      `STRANDED lane; plan lane01; 1 commit(s) beyond base; integration_signal=suite-failed; no worktree remains; run run-20260917T000000Z-1: the lane holds work that is NOT reachable from HEAD. Recover it with \`aw oc integrate lane01\`.`
      (contains `no worktree remains` and does NOT contain `worktree .aw/worktrees/`)
    - Present fixture:
      `STRANDED lane; plan lane01; 1 commit(s) beyond base; integration_signal=suite-failed; worktree .aw/worktrees/lane01; run run-20260917T000000Z-1: the lane holds work that is NOT reachable from HEAD. Recover it with \`aw oc integrate lane01\`.`
      (contains `worktree .aw/worktrees/lane01` and does NOT contain `no worktree remains`)
    - Never-had-one fixture:
      `STRANDED lane; plan sweep01; 1 commit(s) beyond base; run run-20260917T000000Z-1: the lane holds work that is NOT reachable from HEAD. Recover it with \`aw oc integrate sweep01\`.`
      (contains neither `no worktree remains` nor `worktree .aw/worktrees/`)

    DELIBERATE-FAILURE demonstration for the unconditional form (mutating `elif rs.lane_worktree_is_absent(...)` to `else`):
    ```
    =========================== short test summary info ============================
    FAILED tests/test_attention.py::StrandedLaneViewTests::test_stranded_lane_worktree_marker_rendering
    ======================= 1 failed, 38 deselected in 0.53s =======================
    E AssertionError: 'no worktree remains' unexpectedly found in 'STRANDED lane; plan sweep01; 1 commit(s) beyond base; no worktree remains; run run-20260917T000000Z-1: the lane holds work that is NOT reachable from HEAD. Recover it with `aw oc integrate sweep01`.'
    ```
    Confirmed: Reddented that assertion ALONE (`self.assertNotIn("no worktree remains", detail_never)`), leaving reclaimed and present rows passed; restored green upon restoration.

    Leak assertion evidence:
    No rendered detail contains an absolute path or `/home/`. The reclaimed fixture's record carries the ABSOLUTE value at render time (`ABSOLUTE_WORKTREE = "/" + "home" + "/someone/VC/proj/.aw/worktrees/lane01"`), exercising the real leak shape rather than a benign one.

    Whole-plan no-regression evidence:
    - BARE `python3 -m pytest`:
      Baseline: `FAILED tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once`
      `1 failed, 2995 passed, 2 skipped, 3 warnings in 85.58s`
      Post-change: `FAILED tests/test_dependency_block_reporting.py::test_drain_and_cascade_mapped_reasons_rendered_once`
      `1 failed, 3000 passed, 2 skipped, 3 warnings in 45.01s`
      The failing node ID is identical (`test_drain_and_cascade_mapped_reasons_rendered_once`, pre-existing), with 5 new tests passing (4 in test_runner_shared + 1 in test_attention).
    - `python3 -m pytest tests/test_attention.py tests/test_runner_shared.py -o addopts=""`:
      `============================= 138 passed in 15.71s =============================`
    - Targeted regression set (`python3 -m pytest tests/test_oc_runipd.py tests/test_attention_contract.py tests/test_local_leaks.py -o addopts=""`):
      `============================= 203 passed in 45.04s =============================`
    - Spec-amendment evidence on `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`:
      History record count before: 2; history record count after: 3.
      `grep -c pr5b0t`: 1; `grep -c 0ta5vg`: 2; `grep -c 8njbv5`: 1 (all nonzero).
    - `aw check`:
      4 findings across 1740 artifacts (all 4 pre-existing: `4er1ev`, `q5l2r3`, `gvf2sq` uncarried obligations in pending plans, and `.aw/system/layout.json`).
    - `aw ipd lint --phase pre-transition`:
      Conforming (verified below).
    - `aw sanitize --agent`:
      `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    - `aw find backlog hv8zlg`:
      `open hv8zlg .aw/records/backlog/open/20260928-hv8zlg-01-hv8zlg-stranded-lane-detail-exceeds-descriptive-bound.backlog.md` (live and open).
    - `git diff --cached --name-only` immediately before committing:
      Lists exactly the five paths in `- Scope-Paths:` plus this plan.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` with `- Readiness: go-pending-approval`, written by `/plan-review` on 2026-09-28 as the output of that review. `reviewed` is not approval: explicit human sign-off (`- Status: approved`) is still required before execution.

WHAT THE HUMAN IS APPROVING, in one paragraph. The design is unchanged and is right: the plan refuses the mechanism its own backlog item proposed, because keying the marker on the omitted display would assert "no worktree remains" about a tree that is there, and it keys on absence directly instead. Every one of its twelve authored findings reproduced at review, including all six cases of F-03, both constructed fixtures, the 34-symbol fingerprint list, and the 414-character over-bound row. Review corrected three things an executor would otherwise have tripped on: the naive form is refuted by TWO of E-03's four assertions rather than one, so V-03 predicted the wrong number of failures (F-13); the reclaimed fixture silently swaps which `worktree` value the record carries, so an assertion on the record field rather than the rendered detail would be asserting on a moving target (F-14); and F-02/F-10's live counts had already drifted by review, so they are now labelled context rather than bars (F-16). Nothing about the code change moved.

On execution, the executor MUST: commit only the five paths named in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including the two deliberate-failure demonstrations in V-03 and V-04 that prove the new tests are real guards rather than tests that were never red. An edit outside the fence is to be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason`, not treated as a reason to stop.

THE ONE WAY THIS PLAN CAN FAIL SILENTLY, stated for the executor: if the marker ever prints for a worktree that EXISTS, the plan has caused the same class of false assertion `0ta5vg` E-05 was written to remove, and it would be invisible in a green suite unless the discriminating predicate assertions are really present. V-03's deliberate failure is the check that proves they are, and it must be performed by reading the failing assertions' NAMES and confirming there are TWO of them, not by observing that the suite is green. Note the two mutations differ in how many assertions they redden and this is not a mistake: V-03's naive form reddens two (falsy and existing-outside), while V-04's unconditional form reddens exactly one (never-had-one), leaving the reclaimed and present rows byte-identical. A run that produces any other count has not reproduced the measurement.

DO NOT EDIT `lane_worktree_display`. It is the function whose contract E-03 proves unchanged, and the temptation is real because the new predicate answers a question it nearly answers already. Adding the marker decision to it, or hoisting its `_exists` helper into a shared shape, would break the additivity E-03 asserts and would put the display contract at risk for no gain. `describe_lane` is separately off limits: F-06 measures it as a PINNED symbol in `tests/fixtures/runner_shared_premove_fingerprints.json` while `lane_worktree_display` and `stranded_lane_records` are not.

THE SECOND SILENT FAILURE IS THE SPEC HISTORY. The amendment must go through `aw specs note` on a spec with NO `- Id:`, which is precisely the shape whose prior record was destroyed once (backlog `i8wmte`). Count the records before and after and grep for the two prior plan ids; a silent loss here would remove the provenance of F3a's own two earlier amendments.

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence.
