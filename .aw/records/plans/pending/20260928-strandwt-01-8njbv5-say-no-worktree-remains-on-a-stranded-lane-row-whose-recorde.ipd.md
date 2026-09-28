# IPD: Say 'no worktree remains' on a stranded-lane row whose recorded worktree is gone

- Date: 2026-09-28
- Kind: child
- Concern: A stranded-lane row OMITS its worktree segment when the recorded tree is absent, so the reader cannot tell "this lane never had a worktree" from "the worktree was reclaimed". Those two need different next acts: the second means recovery is a BRANCH MERGE and not a tree inspection. Worse, measured here, OMISSION HAS A THIRD CAUSE that the obvious one-line fix would mislabel: `lane_worktree_display` also returns None for a tree that EXISTS outside the repository, so a marker keyed on "display is None" would assert a tree is gone when it is there.
- Scope: Add an explicit `no worktree remains` segment to `attention.stranded_lane_drift`'s `bits` assembly, gated on the record HAVING named a worktree that is now provably ABSENT, never merely on the display being omitted. Add a shared predicate beside `runner_shared.lane_worktree_display` so the two rendering decisions cannot drift, and tests pinning the marker's presence in the reclaimed case and its ABSENCE in the never-had-one case, the tree-still-exists case, and the exists-outside-the-repository case.
- Scope-Paths: agent_workflows/attention.py, agent_workflows/runner_shared.py, tests/test_attention.py, tests/test_runner_shared.py, .aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: aqb4dv
- Set: strandwt
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: 8njbv5

## Workflow history

- 2026-09-28 draft (opencode): created.
- 2026-09-28 to-review (opencode): authored from backlog item `aqb4dv`, which carries OQ-03 of executed plan `0ta5vg` (stranrep-01). Every measurement in Findings taken in this lane at HEAD `9514ff02` against the run records resolved through `attention._resolve_runs_repo_root`, not carried over from the item. The item's scope line proposed keying the marker on the omitted display; F-03 measures that this MISLABELS an existing tree outside the repository, so the plan keys on absence directly and carries the corrected reasoning in OQ-01. Spec amendment declared: `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md` F3a gains one sentence permitting the marker, and is in `- Scope-Paths:`.

## Goal

Make a stranded-lane row say WHICH kind of missing worktree it has, so a reader knows whether to inspect a tree or to merge a branch, WITHOUT ever asserting a tree is gone when it is not. The marker appears exactly when the run record named a worktree and that path is provably absent from disk; in every other omission case the row stays as it is today.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: give the renderer a predicate it can key on safely

- [ ] E-01 Add a shared predicate to `agent_workflows/runner_shared.py`, beside `lane_worktree_display` and with the same `(repo, worktree)` signature, answering the NARROW question "did the record name a worktree that is now provably ABSENT?". Return True only when the recorded value is truthy AND the resolved path does not exist; return False for a falsy value (no worktree was ever recorded) and False for a path that EXISTS, wherever it exists. Reuse `lane_worktree_display`'s own existence helper semantics rather than writing a second existence test: treat an unreadable path (`OSError`/`RuntimeError`) as ABSENT for the display decision but state in the docstring that this predicate therefore inherits that conservative direction, because the cost is one extra marker rather than a wrong verdict. Put it in `runner_shared` and NOT in `attention`, for the reason `lane_worktree_display`'s docstring already gives for living there: the two decisions read the same field and a second spelling in the renderer is the F-4 drift class this repository has paid for. Do NOT edit `lane_worktree_display` itself, and do NOT edit `describe_lane` (F-06 records that `describe_lane` IS in the pre-move fingerprint fixture's pinned symbol list while `lane_worktree_display` and `stranded_lane_records` are NOT).
  - Depends on: none
  - Expected outcome: A new `runner_shared` predicate that returns True for an absent recorded path, False for a falsy value, and False for an existing path whether inside or outside the repository. `lane_worktree_display`'s source and behavior are byte-identical.
  - Execution state: pending

- [ ] E-02 Use that predicate in `attention.stranded_lane_drift`'s `bits` assembly. The existing shape is `display = rs.lane_worktree_display(...)` then `if display: bits.append("worktree {0}".format(display))`; add an `elif` arm that appends the literal `no worktree remains` when the E-01 predicate is True, so the marker sits in the SAME positional slot the worktree segment occupies today and the row's field order does not change. Do not reorder, reword or remove any existing bit. Do not make the marker unconditional on `display` being falsy, which is the item's proposed shape and which F-03 measures to be wrong. Extend the function's docstring with one sentence recording that omission had three causes and only one of them is reported, so the next reader does not re-widen it.
  - Depends on: E-01
  - Expected outcome: A reclaimed-worktree row reads `...; no worktree remains; run <id>: ...`; a row whose tree exists still reads `...; worktree .aw/worktrees/<lane>; ...` unchanged; a row that never named a worktree gains nothing.
  - Execution state: pending

### Task group 2: pin the three cases the marker must NOT claim

- [ ] E-03 Add tests to `tests/test_runner_shared.py`, in or beside the existing `LaneWorktreeDisplayExistenceTests` class (which is E-05 of `0ta5vg` and already builds every relevant fixture shape), asserting the E-01 predicate directly over FOUR inputs: an absent path inside the repository (True), a falsy value (False), an existing path inside the repository (False), and an EXISTING path outside the repository whose parent is not named `worktrees` (False). The fourth case is the discriminating one and is why this test is not redundant with E-04: `lane_worktree_display` returns None for it (measured, F-03), so a predicate written as "display is None" passes the first three assertions and fails only this one. Assert in the same test that `lane_worktree_display` still returns exactly what it returns today for all four, so the new predicate is proven ADDITIVE rather than a change to the display contract. Build every fixture in a throwaway repo, per that class's own standing rule: this repository holds live `aw/lane/*` branches and in-repo lane worktrees, and a test that touched one could destroy the unintegrated work this surface exists to protect.
  - Depends on: E-01
  - Expected outcome: Four assertions over the predicate plus four unchanged-display assertions, all passing, and the fourth predicate case failing if the predicate is ever rewritten to key on the omitted display.
  - Execution state: pending

- [ ] E-04 Add a rendering test to `tests/test_attention.py` driving the marker through `stranded_lane_drift` itself, not through the predicate, because the item asks for a change to the ROW and a predicate test cannot prove a row changed. Extend `StrandedLaneViewTests`' fixture with a RECLAIMED variant: build the lane exactly as `_fixture` does, commit work in it, then `git worktree remove --force` it, leaving the branch and its commit. Measured in F-04 that this yields one `STRANDED` record with `commits_ahead: 1`, a recorded worktree, and that worktree absent from disk, so the case is genuinely reachable and is not a synthetic contrivance. Assert the detail contains `no worktree remains` and does NOT contain `worktree .aw/worktrees/`; assert the existing `_fixture` (tree present) still contains `worktree .aw/worktrees/lane01` and does NOT contain the marker; and assert a NEVER-HAD-ONE row gains neither, using a run state whose only lane is a `review_sweep_lane` record carrying `branch`/`lane_id`/`base_commit` and NO `worktree` key, which F-05 measures produces one `STRANDED` record with `worktree: None`. Assert in every case that the rendered detail contains no absolute path and no `/home/` substring, since F8a binds every surface and this item adds a new segment to one.
  - Depends on: E-02
  - Expected outcome: Three rendered rows pinned by their detail text (reclaimed carries the marker, present carries the path, never-had-one carries neither), plus the leak assertion, all through `stranded_lane_drift`.
  - Execution state: pending

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
| F-02 | THE POPULATION IS OVERWHELMINGLY THE RECLAIMED CASE, which is what makes the marker worth adding at all. Over all 298 readable run records in the resolved main checkout, `stranded_lane_records(..., attention_only=False)` returns 519 lane records: 514 name a worktree that is ABSENT from disk, 5 name one that EXISTS, and ZERO fail to name one. So 514 of 519 rows are exactly the case the reader currently cannot distinguish. | Probe over `run_viewer.discover_run_dirs` + `stranded_lane_records` with `worktree_lease.memoize_worktrees`, classifying each record's `worktree` by `Path.exists()`. |
| F-03 | **THE ITEM'S PROPOSED KEY IS WRONG, AND THIS IS THE MOST IMPORTANT FINDING.** The item scopes the change to the `bits` list, where the available signal is `display is None`; but omission has THREE causes, not two. Measured over six inputs against a throwaway repo: falsy -> None; inside-repo ABSENT -> None; inside-repo EXISTS -> `.aw/worktrees/live`; **OUTSIDE-repo EXISTS with a non-`worktrees` parent -> None**; outside-repo EXISTS with a `worktrees` parent -> `.aw/worktrees/abc123`; outside-repo ABSENT -> None. So a marker keyed on the omitted display would print "no worktree remains" for a tree that IS THERE, which is the same class of false assertion (a row that misdirects the reader's next act) that `0ta5vg` E-05 existed to remove. The fix must key on ABSENCE directly. | Six-case probe calling `runner_shared.lane_worktree_display` in a throwaway git repo, printing the display for each. |
| F-04 | THE RECLAIMED CASE IS CONSTRUCTIBLE AS A FIXTURE AND CLASSIFIES AS `STRANDED`, so E-04 needs no contrivance. Building a lane worktree, committing in it, then `git worktree remove --force` leaves the branch and its commit: `stranded_lane_records` returns ONE record with `lane_state: STRANDED`, `commits_ahead: 1`, `dirty: False`, a recorded worktree, that worktree absent from disk, and `lane_worktree_display` -> None. | Fixture probe in a throwaway repo mirroring `StrandedLaneViewTests._fixture` plus `git worktree remove --force`. |
| F-05 | THE NEVER-HAD-ONE CASE IS ALSO CONSTRUCTIBLE, which matters because the item explicitly asks that the marker not appear for it and F-02 shows the live corpus contains zero instances to test against. A run state whose only lane is a `review_sweep_lane` record with `branch`/`lane_id`/`base_commit` and no `worktree` key yields one `STRANDED` record with `worktree: None`. `runner_shared.lane_records_including_sweep` builds that record from `review_sweep_lane_record`, forwarding `sweep.get("worktree")`, which is absent. | Fixture probe with `state[runner_shared.REVIEW_SWEEP_LANE_KEY]` set and `queue: []`; printed `worktree: None`. |
| F-06 | THE TWO FUNCTIONS THIS PLAN TOUCHES ARE NOT IN THE PINNED FINGERPRINT SET, so neither edit can break the pure-move proof. `tests/fixtures/runner_shared_premove_fingerprints.json` pins 34 symbols; its lane-related entries are `_lane_records_from_state`, `build_recovery_lane_notice`, `describe_lane`, `disable_lane_prompt`, `format_lane_report` and `print_lane_interrupt_report`. Neither `lane_worktree_display` nor `stranded_lane_records` appears, and this plan edits neither pinned symbol. `0ta5vg` relied on the same reading for its own E-05. | JSON probe of the fixture's `symbols` list, filtered for `lane`/`strand`. |
| F-07 | THE MARKER FITS THE SECTION 8.8 BOUND WITH ROOM TO SPARE. Simulating the amended assembly over all 519 records: the 514 rows that gain the marker run 185 to 223 characters against `MAX_DESCRIPTIVE_LEN` 300, so the longest has 77 characters of headroom; the segment itself costs 21 characters including its separator. One row is ALREADY over the bound at 414 characters (`aw/lane/8l8dgb`, `SUPERSEDED`), and it gains NOTHING from this change because its tree exists, so this plan neither causes nor worsens that. | Probe computing the simulated detail length for every record with and without the marker; per-group min/median/max printed. |
| F-08 | THE PRE-EXISTING OVER-BOUND ROW IS NOT THIS PLAN'S TO FIX, and saying so is honest rather than evasive. `attention.stranded_lane_drift` never calls `attention_contract.is_safe_descriptive`, so the 300-character bound is not enforced on a lane detail today at all; `is_safe_descriptive`'s callers are in `specs`, `backlog` and `check_engine`. The 414-character row is therefore a pre-existing, separately-caused gap that predates this item. Deferred with a carrier rather than silently inherited. | `rg` for `is_safe_descriptive` across `agent_workflows/`, each call site classified; length probe from F-07. |
| F-09 | THE ITEM'S OWN COMPATIBILITY CLAIM CHECKS OUT. Spec F8a forbids an ABSOLUTE path in any surface and F3a as amended by `0ta5vg` says an absent worktree "MUST NOT be rendered"; the marker names no path at all, so it violates neither. F3a's amended sentence is nonetheless phrased as a rendering prohibition ("the worktree segment is OMITTED when the path is absent"), which a strict reader can take to forbid printing anything in that slot, so the amendment in E-02's spec sync is needed to make the marker unambiguously permitted rather than merely unforbidden. | Read of spec F3a's worktree paragraph and F8a in `.aw/records/specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md`. |
| F-10 | THE MARKER CHANGES ZERO ROWS ON TODAY'S REPORTED SET, and this is stated up front because it is the fact most likely to be mistaken for a reason not to do the work. `stranded_lane_drift` in this lane returns exactly ONE row (`aw/lane/8l8dgb`, `attention.lane-superseded`, `info` severity), and its worktree EXISTS, so it keeps its path segment and gains nothing. The 514 absent-worktree records are all filtered out before rendering (`attention_only=True` reports only lanes needing attention; the live corpus classifies 515 as `EMPTY`, 2 `LANDED`, 1 `LIVE`, 1 `SUPERSEDED`). The change is forward-looking: the next genuinely stranded lane whose tree has been reclaimed is the beneficiary, and F-04 shows that shape is one `git worktree remove` away. | `attention.stranded_lane_drift(Path("."))` -> 1 record, printed with its rule and detail; `Counter` over `lane_state` for all 519 records. |
| F-11 | `aw attention` STAYS READ-ONLY, which spec F3a requires explicitly ("This clause adds NO write of any kind"). Both E-items add only a path-existence read and a string append; no git command, no mutation, no new subprocess. The existence read is already performed today inside `lane_worktree_display`, so this adds no filesystem call that was not already made. | Inspection of the two edits' shape against `lane_worktree_display`'s existing `_exists` call. |
| F-12 | THE MARKER IS A RENDERING DECISION AND NOT A FILESYSTEM-DERIVED VERDICT, which is the line spec F3a draws and which this plan must not cross. `lane_worktree_display`'s docstring already states the distinction for the identical check: "The only question asked is whether ONE already-derived DISPLAY field should be rendered." The lane's `lane_state`, `landed` and `why` all still come from the run record via `classify_lane_integration`; nothing in either edit reads the filesystem to decide a classification. | Read of `lane_worktree_display`'s closing paragraph and of `stranded_lane_drift`'s record loop, confirming `rule` and `severity` derive only from `rec["lane_state"]`. |

## Proposed changes (ordered, validatable)

1. Add a `(repo, worktree)` predicate to `runner_shared` beside `lane_worktree_display` that is True only for a recorded path that is provably absent, and False for a falsy value or for any path that exists (E-01).
2. Append a `no worktree remains` bit in `attention.stranded_lane_drift` as an `elif` on that predicate, in the slot the worktree segment already occupies, with a docstring sentence recording that omission had three causes and only one is reported (E-02).
3. Pin the predicate over four inputs in `tests/test_runner_shared.py`, including the existing-outside-the-repository case that discriminates it from the naive display-is-None form, plus four assertions that `lane_worktree_display`'s own answers are unchanged (E-03).
4. Pin the rendered ROW in `tests/test_attention.py` over three fixtures (reclaimed, present, never-had-one) through `stranded_lane_drift`, with a leak assertion on each (E-04).
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
- Under-scope: The pre-existing over-bound detail row survives (deferred above with a carrier obligation), and no new marker is added for a tree that exists outside the repository (deferred above, declined with reason). After this plan, a reclaimed worktree is stated rather than implied, and the three omission causes are distinguished in code and in tests.

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
- Resolution or deferral rationale: RESOLVED as the item's literal wording, on two grounds. First, the maintainer owns this as a presentation choice (the item records "DECISION OWNER: maintainer") and wrote that exact phrase, so adopting it is the narrowest reading of what was asked; inventing different words would substitute this author's taste for the decision-owner's. Second, the remedy is ALREADY in the row: every detail ends with `lane_remedy_hint`, which names `aw oc integrate <id6>` (verified present in the one live row's detail), so a remedy-naming marker would duplicate it. The wording is a one-line change if the maintainer prefers another phrase at review, and E-04 pins it as a literal so the change would be visible rather than silent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the full committed source of the new predicate. Paste `git diff agent_workflows/runner_shared.py` showing the addition and showing ZERO changed lines inside `lane_worktree_display`, `describe_lane` or `stranded_lane_records`. Paste a `python3 -c` probe over the four inputs of E-03 printing the predicate's answer for each, which must be True / False / False / False in the order absent-inside, falsy, existing-inside, existing-outside-non-lane-shape. Paste the JSON probe of `tests/fixtures/runner_shared_premove_fingerprints.json`'s `symbols` list showing the new name is absent from it and that no pinned symbol was edited (F-06).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff agent_workflows/attention.py` in full. It must show ONLY the `elif` arm and the docstring sentence, with the existing `display` bit, every other bit, the `rule`/`severity` derivation and the sort key untouched. Paste the BEFORE/AFTER measurement of `attention.stranded_lane_drift(Path("."))` in the executing tree, printing the resolved runs root, the row count and each row's rule and FULL detail; per F-10 the count, the rules AND the one row's detail must be byte-identical, because its worktree exists. Paste `aw attention --check`'s exit code before and after, which must match. State in one sentence that no `SCHEMA_VERSION` bump was made and why (no payload key added).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the full committed source of the new predicate tests and their passing output from `python3 -m pytest tests/test_runner_shared.py -o addopts=""`. Then paste the DELIBERATE-FAILURE contrast that is this item's whole point: temporarily rewrite the predicate body as `return lane_worktree_display(repo, worktree) is None`, paste the test output showing the EXISTING-OUTSIDE-THE-REPOSITORY assertion FAILING while the other three pass, restore, and paste green again. Confirm in one sentence that every fixture was built in a throwaway repository and that no `aw/lane/*` branch or `.aw/worktrees/` directory of this checkout was read or written by the test.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste the full committed source of the rendering test and its passing output. Paste, for each of the three fixtures, the ACTUAL rendered `detail` string: the reclaimed one containing `no worktree remains` and not `worktree .aw/worktrees/`, the present one containing `worktree .aw/worktrees/lane01` and not the marker, and the never-had-one one containing neither. Paste the DELIBERATE-FAILURE demonstration for the unconditional form (marker on any falsy `display`), showing the never-had-one assertion red, then restored green. Paste the leak assertion evidence: no rendered detail contains an absolute path or `/home/`. ALSO carry the whole-plan no-regression evidence here, since this is the last item before commit: paste the BARE `python3 -m pytest` output with its `N passed` line and state it against the pre-change baseline; paste `python3 -m pytest tests/test_attention.py tests/test_runner_shared.py -o addopts=""` and the targeted regression set; paste the spec-amendment evidence required by the spec-sync section (history record counts before and after, plus `grep -c pr5b0t` and `grep -c 0ta5vg` on the spec, all nonzero after); paste `aw check`; paste `aw ipd lint --phase pre-transition`; paste `aw sanitize --agent`; paste `aw find backlog hv8zlg` confirming the deferred over-bound-detail carrier still resolves and is still live (it was filed at authoring time, so this is a re-check and not a new filing); and paste `git diff --cached --name-only` immediately before committing, which must list exactly the five paths in `- Scope-Paths:`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution; it carries no `- Readiness:` field, because that field is an OUTPUT of review and writing one here would forge the attestation that gates auto-approval.

On execution, the executor MUST: commit only the five paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; verify the staged set with `git diff --cached --name-only` before committing, since this is a shared checkout and another party's work must never be swept in; run the BARE `python3 -m pytest` suite and paste its ACTUAL output rather than claiming success; and complete every `V-*` item with the concrete pasted evidence it demands, including the two deliberate-failure demonstrations in V-03 and V-04 that prove the new tests are real guards rather than tests that were never red.

THE ONE WAY THIS PLAN CAN FAIL SILENTLY, stated for the executor: if the marker ever prints for a worktree that EXISTS, the plan has caused the same class of false assertion `0ta5vg` E-05 was written to remove, and it would be invisible in a green suite unless the fourth predicate assertion is really present. V-03's deliberate failure is the check that proves it is, and it must be performed by reading the failing assertion's name, not by observing that the suite is green.

THE SECOND SILENT FAILURE IS THE SPEC HISTORY. The amendment must go through `aw specs note` on a spec with NO `- Id:`, which is precisely the shape whose prior record was destroyed once (backlog `i8wmte`). Count the records before and after and grep for the two prior plan ids; a silent loss here would remove the provenance of F3a's own two earlier amendments.

Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and every validation item above is verified with pasted evidence.
