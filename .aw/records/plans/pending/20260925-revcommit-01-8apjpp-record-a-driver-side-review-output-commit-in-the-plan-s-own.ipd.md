# IPD: Record a driver-side review output commit in the plan's own history

- Date: 2026-09-25
- Kind: child
- Concern: `runner_shared.commit_review_lane_output` commits a review turn's UNCOMMITTED sweep-lane output under the subject "review(<host>): record the review of <id6>", a driver-authored commit of content the agent produced. Re-measured at HEAD `8e74dcac`: the only product call site is the `if is_review and wt_handle is not None:` branch of `runner_shared.execute_item_core` (the two per-host sites the backlog cites were deduplicated by `70a2059f`); the commit carries NO `AW-Run`/`AW-Item` trailers, prints nothing to the operator, and leaves no mark in the plan's `## Workflow history`. Its only traces are `attempt["review_lane_commit"]` in `state.json` and a `review-lane-output-committed` event, neither of which survives outside the run directory. Across the 22 recorded runs with sweep reviews (87 sweep review attempts), the key `review_lane_commit` appears zero times and no commit in `git log --all` carries that subject, so the path has never fired; the gap is visibility of a rare, conservative write, not lost work.
- Scope: IN: (a) the driver commit carries the canonical `AW-Run`/`AW-Item` trailers (`git_commit_helper.run_item_trailers` composed with `compose_message_with_trailers`) plus an `AW-Committed-By: driver` trailer, so the commit is self-describing in permanent history; (b) the driver prints one yellow stderr line naming the id6, the commit and the paths when it commits, and one when a hook refuses; (c) the end-of-run report on both hosts counts driver-committed reviews; (d) the commit ATTRIBUTES ONLY THIS TURN'S OWN PATHS, because the sweep lane is shared across every review of the run and a previously-refused turn's staged files otherwise ride the NEXT turn's commit under the next turn's id6 (F-5, measured); (e) the reported path set is the set actually committed rather than `git status --porcelain`'s directory collapse (F-6, measured); (f) a regression test. OUT: writing a line into the plan's `## Workflow history` (rejected, see Findings F-3); refusing a non-committing review as a failed turn (the maintainer decision in OQ-01, defaulted to keep the safety net).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_review_lane_output_commit.py
- Item-Dependencies: none
- Status: to-review
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: wtaxvk
- Set: revcommit
- Order: 1
- Highest E allocated: 10
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8apjpp

## Workflow history

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501..PR-509, all FIXED, no deferrals. THE MATERIAL FINDING (PR-501, plan F-5): because the sweep lane is ONE tree shared by every review of a run and the function stages whatever `git status --porcelain` reports, a turn whose driver commit a hook REFUSED leaves its files STAGED, and the NEXT review's driver commit sweeps them in under the NEXT plan's id6 - so the very trailers this plan adds would make a FALSE ownership claim permanent, which is strictly worse than the untrailered commit it replaces. Measured live at review: turn 1 (`aaa111`, hook refusing) returned `None` leaving two files staged, then turn 2 (`bbb222`) committed FOUR files under subject `review(oc): record the review of bbb222`. Added E-03 to scope the staged set to the turn's own paths. Second measured defect (PR-502, F-6): `git status --porcelain` collapses an untracked DIRECTORY to one entry, so a first-use lane reports `.aw/` and the plan's own E-01 assertion on the returned paths, its operator line's path list, and its `<n> path(s)` count are all wrong; added E-04. Also corrected E-01's hook fixture (a hook in the worktree's own git dir is NEVER RUN - verified against git 2.43.0 - so the third case would have passed vacuously), pinned the one live `pal` binding E-03 may use, replaced the "latest attempt" predicate in the summary helper with an any-attempt scan plus the reason, and added the durable carrier that `aw check plans` reports as an `error` on this plan today.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog wtaxvk; re-measured that the driver-side review commit has one call site, carries no trailers or history mark, and has fired zero times in 87 recorded sweep review attempts.

## Goal

When the driver commits a review's leftover output, that fact is visible where a human looks: in the commit itself (trailers naming run, item and committer), on the operator's terminal, and in the run summary, without changing whether the work lands.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin today's behavior

- [ ] E-01 Add `tests/test_review_lane_output_commit.py` with the THREE baseline cases. Build a temp git repo (the `make_repo` shape in `tests/test_runner_shared.py`: `git init`, test identity, one initial commit) and add a worktree via `git worktree add`. COMMIT A `.aw/records/plans/pending/` DIRECTORY IN THE INITIAL COMMIT (write any placeholder file into it), because a first-use lane whose whole `.aw/` tree is untracked makes `git status --porcelain` report the single entry `.aw/` and not the plan file - measured at review, see F-6 - and a fixture that skips this pins the collapsed shape as though it were the normal one. Then write an untracked `.aw/records/plans/pending/x-rvc001-p.ipd.md` into the worktree and call `runner_shared.commit_review_lane_output(repo, handle, "rvc001", host_label="oc", run_id="run-test")` with `handle` a `worktree_lease.WorktreeHandle(lane_id=..., path=<worktree>, branch=<branch>, base_commit="HEAD")`. Assert: the returned sha is the worktree HEAD; `git interpret-trailers --parse` on its message yields `AW-Run: run-test`, `AW-Item: rvc001` and `AW-Committed-By: driver`; the subject is unchanged ("review(oc): record the review of rvc001"). Second case: a clean worktree returns `(None, ())` and makes no commit. Third case: a REFUSING `pre-commit` hook returns `(None, (<path>,))` and leaves the file uncommitted - INSTALL IT AT `repo/".git"/"hooks"/"pre-commit"`, chmod 0o755, which is `_install_hook`'s shape in `tests/test_git_commit_helper.py` and whose docstring states the reason ("which the isolated worktree also runs"). DO NOT install it in the worktree's OWN git dir (`git rev-parse --absolute-git-dir` inside the worktree, i.e. `.git/worktrees/<name>/hooks/`): verified against git 2.43.0 at review, a hook there is NEVER RUN (`git rev-parse --git-path hooks` resolves to the COMMON dir), so the case would pass vacuously by committing successfully and asserting nothing.
  - Depends on: none
  - Expected outcome: the trailer case FAILS at HEAD (`TypeError` on `run_id`, then missing trailers); the clean and hook cases pass once the signature exists.
  - Execution state: pending

### Task group 2: make the attribution TRUE before making it permanent

This group precedes the trailers deliberately. A trailer is an IMMUTABLE ownership claim (`git_commit_helper.run_item_trailers`: "these trailers are IMMUTABLE once committed, so their value is exactly that a later reader can TRUST them"), so adding one to a commit that can carry ANOTHER turn's files makes a false claim permanent. Fix WHAT is committed first, then label it.

- [ ] E-02 Add a FAILING test for the cross-turn attribution defect (F-5) to `tests/test_review_lane_output_commit.py`. In ONE worktree standing in for the shared sweep lane: install the refusing `pre-commit` hook at `repo/".git"/"hooks"/"pre-commit"`, write plan `p-aaa111.ipd.md` plus review record `r-aaa111.review.md`, call `commit_review_lane_output(repo, handle, "aaa111", host_label="oc")` and assert it returns a `None` sha (the hook refused). Remove the hook, write `p-bbb222.ipd.md` and `r-bbb222.review.md`, call it again for `"bbb222"`, and assert the resulting commit contains ONLY the two `bbb222` paths. Measured at review, this FAILS at HEAD: the second commit held FOUR files under subject `review(oc): record the review of bbb222`, because `git add` had already staged `aaa111`'s files and `git status --porcelain` still reports them (as `A `).
  - Depends on: E-01
  - Expected outcome: the new case FAILS at HEAD with four committed paths where two are asserted.
  - Execution state: pending

- [ ] E-03 SCOPE THE STAGED SET TO THIS TURN'S OWN PATHS in `runner_shared.commit_review_lane_output`. Accept a keyword-only `own_paths: Sequence[str] | None = None`; when supplied, intersect the `git status --porcelain` set with it and commit only that intersection, returning `(None, ())` when the intersection is empty. Derive the value at the call site from the SAME classifier the review path already uses for its scope report, `runner_shared.classify_review_writes(...).allowed`, which is documented as "the plan under review plus its own review record" - do NOT invent a second notion of what a review owns, and do NOT match on the id6 by substring. `review_record_path_fragment` is the existing id6-to-filename seam if a path test is needed. When `own_paths` is None the behavior is BYTE-IDENTICAL to today, so no other caller changes. State in the docstring that a path this turn did not write is deliberately LEFT STAGED rather than committed or reset: the lane is preserved at teardown when it holds work (`retire_review_sweep_lane` -> `lane_containment.teardown_review_sweep_lane`), so leaving it is recoverable while committing it under the wrong id6 is not.
  - Depends on: E-02
  - Expected outcome: E-02's new case passes; the three E-01 cases still pass unchanged.
  - Execution state: pending

- [ ] E-04 RETURN THE PATHS ACTUALLY COMMITTED, not `git status --porcelain`'s collapsed entries (F-6). Measured at review: for a first-use lane whose `.aw/` tree is entirely untracked, `git status --porcelain` reports the single line `?? .aw/`, so the function returns `('.aw/',)` while the commit contains `.aw/records/plans/pending/x-rvc001-p.ipd.md`. That one value feeds E-01's assertion, E-06's `<n> path(s)` count and its path list, and `attempt["review_lane_committed_paths"]` in the run record, so every one of them is wrong in exactly the case a fresh lane produces. Expand a directory entry with `git status --porcelain --untracked-files=all` (verify the flag's effect before relying on it), or read the committed set back with `git show --name-only --format= HEAD`, whichever E-03's intersection needs; state which was chosen and why. Add a test asserting the returned tuple equals the committed file set for an all-untracked `.aw/` tree.
  - Depends on: E-03
  - Expected outcome: the returned paths equal `git show --name-only --format= HEAD` for the untracked-directory case; FAILS at HEAD, which returns `('.aw/',)`.
  - Execution state: pending

### Task group 3: make the write visible

- [ ] E-05 In `runner_shared.commit_review_lane_output`, add a keyword-only `run_id: str | None = None` parameter and build the second `-m` body as `git_commit_helper.compose_message_with_trailers(<existing body>, [*git_commit_helper.run_item_trailers(run_id, id6), "AW-Committed-By: driver"])`. Note `compose_message_with_trailers` ALREADY passes every trailer through `validate_trailer` (its first statement is `cleaned = [validate_trailer(t) for t in trailers]`), so do not call it a second time. `AW-Committed-By` is a NEW trailer key in this repository (the tree carries only `AW-Run` and `AW-Item`); it satisfies `_TRAILER_TOKEN_RE` and was verified at review to round-trip through `git interpret-trailers --parse` beside the other two. Extend the docstring with a paragraph "VISIBLE BY CONSTRUCTION (revcommit `8apjpp`)" stating the trailers, why history is not written (F-3), and that the trailers are only truthful BECAUSE of E-03's scoping.
  - Depends on: E-04
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_review_lane_output_commit.py` passes, including E-01's trailer assertions.
  - Execution state: pending

- [ ] E-06 At the call site in `runner_shared.execute_item_core` (`review_commit, review_committed_paths = commit_review_lane_output(`), pass `run_id=str(state.get("run_id") or "") or None` and E-03's `own_paths`; when `review_commit` is set, print to stderr, yellow, "  ! review <id6> left its output uncommitted; the driver committed <n> path(s) as <sha12> (AW-Committed-By: driver)"; when `review_committed_paths` is set without a commit, print "  ! review <id6> left uncommitted output and a hook refused the driver's commit; the work stays in the sweep lane: <paths>". USE THE `pal` ALREADY IN SCOPE, bound once at the top of `execute_item_core` as `pal = Palette(should_color(sys.stdout))`; do not introduce a second binding. Note the stream/palette mismatch is PRE-EXISTING at this site (the neighbouring out-of-scope-paths warning prints a stdout-colored string to stderr) and is not this plan's to fix; follow the neighbour so the block stays uniform.
  - Depends on: E-05
  - Expected outcome: `grep -n 'the driver committed' agent_workflows/runner_shared.py` returns the new line inside the review branch; `python3 -m pytest -o addopts="" tests/test_review_lane_output_commit.py` still passes.
  - Execution state: pending

- [ ] E-07 Add a pure helper `runner_shared.driver_committed_reviews(state) -> list[str]` returning the id6 of every queue item ANY of whose attempts carries `review_lane_commit`, and `runner_shared.report_driver_committed_reviews(state, *, stream=None)` printing "N review(s) had their output committed by the driver: <id6s>" only when N > 0. ANY ATTEMPT, NOT THE LATEST, and the reason is measured rather than stylistic: a review's refused integration is re-attempted by the deferral ladder (`reattempt_deferred_integrations`, reached per dispatch-loop iteration), and `execute_item_core` appends a NEW attempt dict per turn (`item.setdefault("attempts", []).append(attempt)`), so a driver commit recorded on attempt 1 is invisible to a latest-attempt read once attempt 2 exists. A summary that silently drops a driver commit is the exact defect this plan exists to close. Follow the established shape at `finish_integrated_review_item` (`for attempt in reversed(item.get("attempts") or [])`) and tolerate a missing key throughout. Mirror `report_run_spec_edits`'s ADVISORY posture: it runs at exit, so wrap the computation so an exception reports itself rather than replacing a completed run's summary with a traceback. Call the reporter immediately after the PRIMARY end-of-run `report_run_spec_edits(state)` in both `oc_runipd.run_queue` and the agy twin (the sites commented "specvis st5klo E-03: the PRIMARY end-of-run site"); import it with the `as <same-name>` form beside `report_run_spec_edits` in each host, since `ruff` has stripped bare re-exports in this package before. Add tests over a hand-built `state`: one item whose attempt 1 carries `review_lane_commit` and whose attempt 2 does not (asserting it is still reported), one self-committed review, and an empty state that prints nothing.
  - Depends on: E-06
  - Expected outcome: the helper returns exactly the one id6 INCLUDING the two-attempt case; the reporter writes nothing for a state with none.
  - Execution state: pending

### Task group 4: prove it

- [ ] E-08 Re-derive the never-fired measurement at execution time rather than trusting this plan's authored count. Run `grep -rl review_lane_commit .aw/records/runs/*/state.json` (the tree is gitignored per `.aw/.gitignore` `records/runs/`, so it is machine-local and may be absent or differently populated in the executing checkout) and `git log --all --grep="record the review of" --oneline`. Record the numbers observed. This changes NO behavior and gates NOTHING: it exists because F-4's "0 of 87" is a live-artifact count, and a plan must not assert a drifting population as a fact at execution time.
  - Depends on: none
  - Expected outcome: both measurements recorded; an absent or empty runs tree is a valid observation, not a failure.
  - Execution state: pending

- [ ] E-09 Run the directly affected modules: `python3 -m pytest tests/test_review_lane_output_commit.py tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py`.
  - Depends on: E-07
  - Expected outcome: 0 failed.
  - Execution state: pending

- [ ] E-10 Run the bare suite `python3 -m pytest`.
  - Depends on: E-09
  - Expected outcome: summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Run-owned commits are identified by `AW-Run`/`AW-Item` trailers (spec `25kzda` 4.6, quoted at `git_commit_helper.TRAILER_KEY_RUN`); `run_item_trailers` requires the values come from live run state, never synthesized, which `state["run_id"]` and `item["id6"]` satisfy.
- `compose_message_with_trailers` validates every trailer itself (`cleaned = [validate_trailer(t) for t in trailers]`) and returns the message BYTE-IDENTICAL for an empty trailer list, which is what keeps its existing callers unaffected.
- `commit_review_lane_output` is path-scoped, runs hooks, and treats a hook rejection as "nothing committed"; none of that changes here.
- THE SWEEP LANE IS ONE TREE FOR THE WHOLE RUN, not one per review (`acquire_review_sweep_lane`: "the ONE lane every review turn of this run shares"; `retire_review_sweep_lane` is the coordinator's and runs at run end). Every per-turn computation on that tree must therefore be scoped to the turn, which is what F-5 measures and E-03 fixes.
- A git hook placed in a WORKTREE's own git dir is never run; `git rev-parse --git-path hooks` resolves to the COMMON git dir. Verified against git 2.43.0 at review. `tests/test_git_commit_helper.py::_install_hook` is the in-tree precedent and says so.
- `git status --porcelain` collapses an entirely untracked DIRECTORY to one entry (`?? .aw/`). Any code deriving a FILE list from it must expand or read back the committed set.
- `execute_item_core` binds `pal = Palette(should_color(sys.stdout))` once; `runner_shared` has no module-level `pal`.
- The auto-approve fallback reads the NEWEST history record only when `- Readiness:` is ABSENT (`plan_readiness.is_plan_review_approved`); a PRESENT field decides the answer but must be attested by `history_has_review_record`, which scans ANY record rather than the newest. `status_set` prepends records newest-first. F-3's argument is unchanged by this: a driver-written history line would still become the newest record and would still be the one the prose fallback reads for a pre-field plan.
- An OPEN or DEFERRED open question owes a TYPED durable carrier (`- Carrier:` / `- Carrier-Evidence:` / `- Carrier-Declined:`, `ipd_schema.CARRIER_FIELDS`); prose naming a backlog item satisfies nothing (`check_engine.evaluate_carrier_obligation`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone.

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `runner_shared.commit_review_lane_output` | The driver-authored commit carries no run/item/committer trailers, so permanent history cannot tell it from an agent's own review commit except by its body prose. | `subject = f"review({host_label}): record the review of {id6}"`; no `run_item_trailers` call in the function |
| F-2 | LOW | `execute_item_core` review branch | The commit is recorded only in `state.json` and `events.jsonl`; no operator-facing line. | `attempt["review_lane_commit"] = review_commit`; `"event": "review-lane-output-committed"` |
| F-3 | INFO | plan `## Workflow history` | Writing a driver line into the reviewed plan's history is REJECTED: it would become the newest record, and the auto-approve prose fallback reads only the newest record, so a driver line would silently mask the review's verdict. It would also need a second driver commit editing the plan. Trailers carry the same fact without touching the reviewed artifact. | `plan_readiness.is_plan_review_approved` fallback |
| F-4 | INFO | run records | Never fired, AS MEASURED AT AUTHORING: 0 of 87 sweep review attempts in 22 runs carried `review_lane_commit`; 0 commits with the subject in `git log --all`. A LIVE-ARTIFACT COUNT, re-derived at execution by E-08 rather than asserted: `.aw/records/runs/` is gitignored (`.aw/.gitignore` `records/runs/`), so the population is machine-local and was EMPTY in the review checkout. `git log --all --grep="record the review of"` returned nothing there too, which corroborates the second half. | grep of `.aw/records/runs/*/state.json`; `git log --all --grep="record the review of"` |
| F-5 | HIGH | `runner_shared.commit_review_lane_output` on the SHARED sweep lane | A TURN'S DRIVER COMMIT CAN CARRY A PREVIOUS TURN'S FILES UNDER THIS TURN'S id6, so the trailers this plan adds would make a FALSE ownership claim PERMANENT. The function stages `git status --porcelain`'s whole set; a hook refusal leaves those paths STAGED (git reports them `A `), and the sweep lane is ONE tree for every review of the run, so the next review's commit sweeps them in. | Measured at review in a temp repo: turn 1 (`aaa111`, refusing hook) returned `(None, ('...p-aaa111.ipd.md', '.aw/records/reviews/'))` and left `A  .aw/records/plans/pending/p-aaa111.ipd.md` staged; turn 2 (`bbb222`) then committed FOUR paths under subject `review(oc): record the review of bbb222`. `acquire_review_sweep_lane` docstring: "the ONE lane every review turn of this run shares" |
| F-6 | MED | `runner_shared.commit_review_lane_output` return value | THE RETURNED PATH SET IS NOT THE COMMITTED FILE SET when a directory is entirely untracked, which is exactly a first-use lane. `git status --porcelain` collapses it, so the function returns `('.aw/',)` for a commit containing one plan file, and that value feeds E-01's assertion, the operator line's `<n> path(s)` count and path list, and `attempt["review_lane_committed_paths"]`. | Measured at review: `commit_review_lane_output` returned `('.aw/',)` while `git show --name-only --format= HEAD` reported `.aw/records/plans/pending/x-rvc001-p.ipd.md` |
| F-7 | MED | `aw check plans` on THIS plan | OQ-01 owes a TYPED durable carrier and its prose sentence ("Backlog `wtaxvk` remains open as the carrier") satisfies nothing. Measured at review: `evaluate_durable_carrier` returns one `error`-severity drift on this plan, which also gates `aw ipd lint --phase pre-transition`. Note the prose is additionally FALSE: `wtaxvk` is `graduated`, not `open`. | `check_engine.evaluate_durable_carrier` -> "OQ-01 records an outstanding obligation with NO durable carrier"; `.aw/records/backlog/graduated/...-wtaxvk-....backlog.md` `- Status: graduated` |
| F-8 | INFO | `AW-Committed-By` | A NEW trailer key for this repository (the tree carries `AW-Run` and `AW-Item` only). Verified at review that it satisfies `_TRAILER_TOKEN_RE` and round-trips through `git interpret-trailers --parse` beside both existing keys. No reader is added: `RUN-COMMIT-CONTENTS` remains `UNBOUND_BY_DEPENDENCY` waiting on a trailer READ-BACK predicate, so this plan is a WRITER only and must not be described as closing that code. | `run_evidence` `RUN-COMMIT-CONTENTS` `waiting_on`: "a trailer READ-BACK predicate ... nothing reads a trailer back" |

## Proposed changes (ordered, validatable)

1. E-01 pins today's three baseline cases (with a hook fixture that actually runs).
2. E-02 adds the failing cross-turn attribution case; E-03 scopes the staged set to the turn's own paths; E-04 returns the real committed set. THIS ORDER IS LOAD-BEARING: the trailers must not be added to a commit that can carry another turn's files.
3. E-05 adds trailers.
4. E-06 threads `run_id` plus `own_paths` and prints the operator lines.
5. E-07 adds the run-summary count (any-attempt, advisory).
6. E-08 re-derives the never-fired measurement; E-09 and E-10 run the affected modules and the bare suite.

## Deferred / out of scope (with reason)

- Requiring a review turn to commit for itself and reporting a non-committing review as a failed turn. That is the maintainer decision OQ-01; this plan defaults to keeping the safety net.
  - Carrier: wtaxvk
- A trailer READ-BACK predicate that would bind `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY`. This plan WRITES `AW-Committed-By` and reads nothing; binding either code needs a checker proving a commit's tree diff equals the item-owned delta, which those codes' own `waiting_on` names and which is far outside this plan's surface.
  - Carrier-Declined: The obligation is already recorded in the shipped vocabulary itself, as the `UNBOUND_BY_DEPENDENCY` binding plus `waiting_on` prose on both codes in `run_evidence.RUN_FINDING_CODES`, which `aw check` and the release-review surface read. A backlog item would duplicate a durable, machine-readable declaration that already exists and is already revisited.
- Fixing the pre-existing stdout-palette-to-stderr mismatch at the review branch's print sites (the neighbouring out-of-scope-paths warning colors with a stdout palette and prints to stderr). Pre-existing, cosmetic, and touching it would put this plan's diff on lines it has no reason to change.
  - Carrier-Declined: A no-op in practice: `Palette(should_color(sys.stdout))` and the stderr equivalent differ only when exactly one of the two streams is a TTY, and the visible effect is at most absent color on a warning line. Filing an item would add noise to `aw attention` for a defect with no user-perceptible cost, which the repository's own `bug`-versus-`chore` test says is not one.

## Scope check

- Over-scope: none. E-02/E-03/E-04 are additions made by review and sit inside the same function this plan already opens; they are the precondition for the plan's own deliverable being TRUE rather than separate work (see PR-501's reasoning in the review record).
- Under-scope: none remaining. `commit_review_lane_output` has one product caller (grep across `agent_workflows`), and the end-of-run report is wired at both hosts. The one caller is reached only under `if is_review and wt_handle is not None:`, so no non-review path is affected.

## Required tests / validation

New `tests/test_review_lane_output_commit.py`: the three baseline cases (E-01), the cross-turn attribution case failing before E-03 (E-02), the collapsed-directory case failing before E-04, the trailer assertions failing before E-05, and the two-attempt summary case (E-07). Then the affected modules, then the bare suite.

## Spec / documentation sync

N/A: no spec describes the review sweep's driver commit (grep of `.aw/records/specs` for `commit_review_lane_output` and "record the review of" is empty). The rationale lives in the function docstring (E-02).

## Open questions

### OQ-01: Should the driver commit a review's uncommitted output at all, or should a non-committing review fail its turn?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: wtaxvk
- Resolution or deferral rationale: Default: keep the driver commit and make it visible (this plan). Evidence: no recorded sweep review has exercised it (F-4, re-derived by E-08), so the honesty cost is currently nil, while removing it would turn a future non-committing review from "landed and labelled" into "work stranded in a lane that is later torn down". If the maintainer prefers strictness, a follow-up replaces the commit with a refusal; the trailers added here are then harmless. ONE ARGUMENT CHANGED AT REVIEW, and it strengthens the case for strictness rather than the default: F-5 measured that on the SHARED sweep lane a hook-refused turn's staged files ride the next turn's commit, so the driver commit was not merely invisible, it could MISATTRIBUTE. E-03 fixes that, but the maintainer should weigh that the mechanism needed a fix at all when deciding whether the driver should author an agent's commit. Carrier is `wtaxvk` (currently `graduated`, i.e. still live in `aw attention`); the review record's D-1 records why the carrier is the backlog item rather than a new one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_review_lane_output_commit.py` run BEFORE E-05, pasted, showing the trailer case FAILING (`TypeError` naming `run_id`, or a missing `AW-Committed-By` assertion). PLUS proof the hook fixture is live rather than vacuous: paste the hook case's own assertion output showing the returned sha is `None`, and paste `git rev-parse --git-path hooks` executed INSIDE the fixture worktree, showing it resolves to the COMMON git dir and not to `.git/worktrees/<name>/hooks`. A hook case that passes because the commit succeeded proves nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the new cross-turn case run BEFORE E-03, pasted, FAILING. The failure output must show the actual committed path count or set (four paths where two are asserted); an assertion error naming only a boolean does not distinguish this defect from a fixture mistake.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the same case after E-03, pasted, PASSING, plus the pasted `git show --name-only --format= HEAD` of the second commit showing EXACTLY the two `bbb222` paths. Also paste evidence the `own_paths=None` default is byte-identical: the three E-01 cases still passing unchanged, and the `git diff` hunk showing the intersection is applied only when the parameter is supplied.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the collapsed-directory case before and after, pasted: BEFORE showing the returned tuple is `('.aw/',)` (or whatever the executing git reports) while `git show --name-only --format= HEAD` lists the plan file, and AFTER showing the two sets equal. State which technique was chosen (`--untracked-files=all` or read-back) and why.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest -o addopts="" tests/test_review_lane_output_commit.py` after E-05, pasted, all passed; plus the test's printed `git interpret-trailers --parse` output showing `AW-Run: run-test`, `AW-Item: rvc001`, `AW-Committed-By: driver` as three parsed trailers. PARSED OUTPUT, NOT A SUBSTRING MATCH ON THE MESSAGE: `git_commit_helper.compose_message_with_trailers`'s own docstring records that a commit whose trailers silently fail to parse SUCCEEDS either way, so only `--parse` distinguishes a real trailer block from text that looks like one.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `git diff -- agent_workflows/runner_shared.py` hunk at the `commit_review_lane_output(` call showing `run_id=`, `own_paths=` and both stderr messages, and showing the existing in-scope `pal` is used with no second binding introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: pasted passing output of the `driver_committed_reviews` tests INCLUDING the two-attempt case (commit on attempt 1, absent on attempt 2, still reported), and the diff hunks adding `report_driver_committed_reviews(state)` after `report_run_spec_edits(state)` in BOTH `oc_runipd.py` and `agy_runipd.py`, plus the `as <same-name>` import line added to each host.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted output of both commands with their observed counts. An empty or absent `.aw/records/runs/` tree is a valid result and must be stated as such rather than reported as the authored "0 of 87".
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: pasted summary line of `python3 -m pytest tests/test_review_lane_output_commit.py tests/test_runner_shared.py tests/test_oc_runipd.py tests/test_agy_runipd_cli.py` with 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: pasted final summary line of the bare `python3 -m pytest`, showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A change to the ONE function by which the driver commits a review turn's leftover output on the shared sweep lane. Two parts are behavioral rather than cosmetic and should be weighed as such. FIRST, E-03 narrows WHAT that commit stages: today it stages everything `git status --porcelain` reports in the lane, and review measured that this lets a hook-refused turn's files ride the NEXT turn's commit under the next plan's id6 (F-5). Narrowing it means a path this turn did not write is LEFT STAGED in the lane instead of being committed; that is recoverable (the lane is preserved at teardown when it holds work) but it is a real change in where an unattributed file ends up. SECOND, E-05 adds immutable ownership trailers to a commit on `main`, which is a permanent claim and is the reason E-03 precedes it. Everything else is reporting. The path has never been observed to fire (F-4, re-derived by E-08), so the expected blast radius on a normal run is zero.

SCOPE FENCE, stated as a DECLARATION for reconciliation, not as a stop directive. Within `agent_workflows/runner_shared.py`: `commit_review_lane_output` and the `if is_review and wt_handle is not None:` branch of `execute_item_core`, plus the two new module-level helpers. Within `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`: one import line and one call line each, beside the existing `report_run_spec_edits` site. `tests/test_review_lane_output_commit.py` is new. EXPLICITLY NOT IN SCOPE: `integrate_review_lane_branch` or `integrate_lane_branch` (the merge is unchanged), the sweep lane's allocation / refresh / retirement, `classify_review_writes`'s own classification rules (E-03 CONSUMES it and must not alter it), the stdout-palette-to-stderr mismatch, and any trailer READER. An out-of-scope edit is to be MADE and then JUSTIFIED through `aw ipd finalize --scope-reason`, never silently.

HARD MUST: paste the ACTUAL runner output for every `V-*`. Never claim a test passed without running it. Two claims in this plan are especially easy to fake and are named for that reason: V-01's hook case (which passes vacuously if the hook is installed where git does not read it) and V-05's trailer parse (which passes vacuously if asserted as a substring of the message instead of through `git interpret-trailers --parse`). Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

STOP AND REPORT, for a genuinely unsafe condition only: if `classify_review_writes(...).allowed` does not in fact yield the plan-under-review plus its review record for the executing tree (E-03's whole premise rests on it), or if `commit_review_lane_output` has acquired a second product caller since authoring whose behavior the new `own_paths` default would change.

This plan is `reviewed` (review complete; NOT approved) and needs explicit human approval before execution. The executor commits only the Scope-Paths via `aw commit 8apjpp -- <paths>`, never `git add -A`, never pushes, and pastes actual runner output for every V item. LIFECYCLE TRANSITION: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete observed evidence. Under `aw oc run` / `aw agy run` the RUNNER owns that transition and the executor must not hand-roll it; run by hand, the executor completes it with `aw ipd finalize` (never a hand-rolled `git mv`).
