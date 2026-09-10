# IPD: Widen the pre-merge dirty check to every path the merge would write, after the shared extraction

- Date: 2026-09-07
- Kind: child
- Concern: The pre-merge dirty guard checks the wrong set of paths. `dirty_tree_overlap(repo, changed_files)` is called with `lane.changed_files`, so it compares main's dirty paths only against files THE LANE changed. A non-fast-forward merge can also write files the lane never touched (commits that landed on main since the lane base, and renames of lane-touched files), and those are outside the check. The guard reports "clear" and the merge then fails anyway.
  REPRODUCED 2026-09-07, so this is measured rather than argued: lane changed only `a.txt`; main renamed `a.txt` to `renamed.txt` and was dirty there; `dirty_tree_overlap(repo, ["a.txt"])` returned `[]` (guard says clear) and `git merge --no-ff` then failed with "Your local changes to the following files would be overwritten by merge: renamed.txt". The guard passed and the merge died.
  TODAY THE COST IS ONLY A WORSE MESSAGE. Both mis-dispositions are terminal, so the operator gets `merge-conflict` plus git's raw stderr instead of the accurate `integration-blocked` ("main tree has un-owned dirty paths overlapping the incoming change: <paths>"). Verified that git fails closed on its own in every dangerous case and the driver's only recovery is `git merge --abort`, with no `reset`, `checkout -f`, `stash`, or `clean` anywhere. It is NOT a data-safety bug and must not be described as one.
  BUT THE LADDER BREAKS THAT SYMMETRY, WHICH IS WHY THIS MATTERS NOW. Sibling `51vw4y` makes the dirty-overlap refusal (`integration-blocked`) NON-TERMINAL via a defer/poll/ask ladder, while a real conflict (`merge-conflict`) stays terminal, correctly. Once that lands, misclassifying transient co-worker dirt as `merge-conflict` converts a recoverable deferral into permanent in-run loss plus a dependency cascade. The diagnostic defect becomes a functional one.
- Scope: Compute the pre-merge dirty check against every path the merge would actually write (the merge-base-to-both-tips path set), not just the lane's changed files, so transient dirt on a path the merge touches is classified `integration-blocked` rather than `merge-conflict`. ONE implementation in shared code. Change no refusal into an acceptance: this plan makes refusal MORE accurate, never rarer.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/lane_containment.py, tests/test_runner_shared.py, tests/test_merge_dirty_scope.py
- Item-Dependencies: executed:6sb3yu, executed:51vw4y
- Status: to-review
- Set: mergedirty
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: fujm0y
- From-Backlog: h1ksy6
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `h1ksy6` with its SEQUENCING CORRECTED, which is the whole reason this plan is not a transcription of the item. The item says `dirty_tree_overlap` "is still in `main`, in TWO copies" and cites `oc_runipd.py:1923` plus `agy_runipd.py:1156`. Both facts are about to stop being true: approved plan `6sb3yu` is queued RIGHT NOW to extract both copies into `runner_shared.py` as ONE implementation. Verified at authoring: two copies still exist (`oc_runipd.py:1951`, `agy_runipd.py:1241`), `runner_shared.py` defines none, and every line number the item cites has already drifted. So this plan declares `executed:6sb3yu` and instructs the executor to fix ONE function, not two. It also declares `executed:51vw4y` because `5wdoze` line 113 states these two "must be reconciled, not stacked blindly": widening the input set makes refusal MORE reachable, and doing that while refusal is still TERMINAL would make things worse, not better.

## Goal

A transient dirty path that the merge would actually write is reported as `integration-blocked` (deferrable) rather than `merge-conflict` (terminal), so the ladder can recover it and the operator gets an accurate reason.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: establish the post-extraction ground truth

- [ ] E-01 RE-LOCATE THE FUNCTION AND CONFIRM THERE IS EXACTLY ONE, before changing anything. This plan is authored against a tree with TWO copies (`oc_runipd.py:1951`, `agy_runipd.py:1241`, none in `runner_shared.py`) and is sequenced to execute against a tree with ONE, after `6sb3yu`. Locate `dirty_tree_overlap` and `integrate_lane_branch` BY SYMBOL and record where each now lives.
  IF TWO COPIES STILL EXIST, STOP AND REPORT rather than fixing both. Two copies means `6sb3yu` did not land, the declared dependency was not honored, and patching both would recreate the duplication `6sb3yu` exists to remove and that `cnwy8g` documents. The correct action is to report, not to work around.
  ALSO CONFIRM `51vw4y`'s LADDER IS PRESENT, by checking whether a non-terminal `integration-deferred` status exists. If the ladder has NOT landed, say so and STOP: widening the refusal's input set while every refusal is still terminal makes the failure mode strictly worse, which is what `5wdoze` line 113 warns against.
  - Depends on: none
  - Expected outcome: a written statement, by symbol, that exactly ONE `dirty_tree_overlap` exists and where; plus confirmation the ladder is present. Any other finding is a stop-and-report.
  - Execution state: pending

### Task group 2: widen the input set

- [ ] E-02 COMPUTE THE PATH SET THE MERGE WOULD ACTUALLY WRITE, and pass THAT to the dirty check instead of `lane.changed_files`. The correct set is the union of paths differing between the merge base and BOTH tips, which captures the two cases the lane's own diff misses: files changed on main since the lane base, and RENAMES of lane-touched files (the reproduced case).
  DERIVE IT FROM GIT, NOT FROM ARITHMETIC ON THE LANE DIFF. Use the merge base and the two tips (e.g. `git merge-tree` or a merge-base plus two `diff --name-only` calls); do not attempt to predict rename targets by inspecting the lane diff alone, which is exactly the reasoning that produced the defect.
  KEEP THE RENAME HANDLING THE FUNCTION ALREADY HAS. Its porcelain parser takes the last path token so both endpoints of a `orig -> dest` rename count as dirty; that behavior is correct and must survive, because the reproduced failure was a rename.
  - Depends on: E-01
  - Expected outcome: the pre-merge check receives every path the merge would write; the reproduced rename case now returns a non-empty overlap where it previously returned `[]`.
  - Execution state: pending

- [ ] E-03 PROVE THE DISPOSITION CHANGES AND THAT NOTHING BECAME PERMISSIVE. The observable win is classification: the reproduced case must now yield `integration-blocked` (with the accurate operator-facing reason naming the paths) instead of `merge-conflict`. Assert the reason string names the offending path.
  THE ANTI-REGRESSION HALF IS THE LOAD-BEARING ONE: widening an input set to a REFUSAL can only ever refuse MORE, so prove no case that previously integrated now refuses. Enumerate and assert: a clean main still fast-forwards; a clean main that has advanced still non-ff merges; dirt on a genuinely non-overlapping path still integrates and is left untouched (verified 2026-09-07: git only writes paths in the diff, and the dirty edit survives). A widened check that refuses a previously-clean integration is a FAILURE of this plan, not a stricter success.
  DO NOT TURN A REAL CONFLICT INTO A DEFERRAL. `merge-conflict` must remain reachable and terminal for genuine textual conflict; only the dirty-overlap case moves. Assert a true conflict still returns `merge-conflict`.
  - Depends on: E-02
  - Expected outcome: the reproduced case classifies `integration-blocked` with the paths named; every previously-integrating case still integrates; genuine conflict still returns `merge-conflict`.
  - Execution state: pending

- [ ] E-04 TEST THROUGH REAL GIT MERGES ON BOTH HOSTS, in a new `tests/test_merge_dirty_scope.py`, because the defect is precisely that real merge state was never consulted. Build the reproduced fixture: base with `a.txt`; lane changes `a.txt`; main renames `a.txt` to `renamed.txt` and is dirty there; assert the widened check catches it.
  A MOCKED PATH SET PROVES NOTHING HERE. The bug is in which paths get computed from real git history, so a test that hands the function a pre-built list would have passed against the broken code. Drive actual `git merge` behavior in a throwaway repository.
  ASSERT BOTH HOSTS FROM THE ONE SHARED IMPLEMENTATION. After `6sb3yu` there is a single function; assert by object identity that both drivers reach it, rather than running the same assertions twice against two symbols.
  - Depends on: E-03
  - Expected outcome: a test failing against pre-change HEAD on the rename case, passing after, driven through real merges, with both hosts shown to use one implementation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `6sb3yu` (approved, queued at authoring) extracts `dirty_tree_overlap` and `integrate_lane_branch` into `runner_shared.py` as ONE implementation each; its own measurement is that the only behavioral difference between the two copies was a commit-subject label. This plan is sequenced AFTER it.
- `51vw4y` (approved) adds the `integration-deferred` ladder making a dirty-overlap refusal non-terminal. `5wdoze` line 113 explicitly pairs it with this item: "these two must be reconciled, not stacked blindly".
- Every re-attempt must route through `orchestrate_isolation.execute_merge_and_revalidate_gate`; `git merge-tree` cleanliness proves absence of TEXTUAL conflict only, never that the suite still passes.
- NO DIRT RESOLUTION: the driver's only recovery on this path is `git merge --abort`. Keep it that way.
- Shared checkout, and both driver modules are being edited by concurrent runs. Re-locate every symbol.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | wrong input set | The guard is called with `lane.changed_files`, so paths the merge writes but the lane never touched are unchecked. | reproduced 2026-09-07: `dirty_tree_overlap(repo, ["a.txt"])` -> `[]` while `git merge --no-ff` failed on `renamed.txt` |
| F-2 | HIGH | sequencing, not transcription | The item says TWO copies exist and cites `oc:1923` / `agy:1156`. Two copies DO exist but at `oc:1951` / `agy:1241`, and `6sb3yu` is queued to collapse them, so a plan written against two copies would be wrong by execution time. | `grep -n "def dirty_tree_overlap"` -> `oc_runipd.py:1951`, `agy_runipd.py:1241`; `runner_shared.py` has 0 |
| F-3 | HIGH | ladder interaction | Widening a refusal's input set makes refusal MORE reachable. Doing that while every refusal is terminal makes the failure worse; after the ladder it makes recovery better. Order matters. | `5wdoze:113`; `51vw4y` adds non-terminal `integration-deferred` |
| F-4 | MEDIUM | severity is diagnostic today | Git fails closed on its own in every dangerous case and the driver only ever `merge --abort`s, so today's cost is a worse message, not lost work. Do not call this a data-safety bug. | verified 2026-09-07: no `reset`/`checkout -f`/`stash`/`clean` on the integration path; dirty non-overlapping edits survive a successful merge |
| F-5 | MEDIUM | dead prior gate | The item's original `Gate-Kind: artifact` / `Gate-Ref: 2c122z` pointed at a plan retired to `superseded/` in `70b5338a`, so the gate was released and the defect left unowned. That is why it is being graduated now rather than waiting. | `2c122z` is in `.aw/records/plans/superseded/` |
| F-6 | LOW | rename handling exists | The porcelain parser already treats both endpoints of `orig -> dest` as dirty; the reproduced failure was a rename, so this behavior must survive the widening. | `dirty_tree_overlap` docstring and body |

## Proposed changes (ordered, validatable)

1. Confirm exactly ONE `dirty_tree_overlap` exists post-extraction, and that the ladder is present; otherwise stop and report (E-01).
2. Compute the merge's real write set from git and pass it to the check (E-02).
3. Prove the disposition changes to `integration-blocked` and that nothing previously-integrating now refuses (E-03).
4. Test through real merges on both hosts from the one shared implementation (E-04).

## Deferred / out of scope (with reason)

- CONTENT-BASED NARROWING of the false-positive rate (skip the refusal when main's dirty version is byte-identical to what the merge would produce): declined by the maintainer 2026-09-05 as low-value relative to the ladder. Recorded, not implemented.
- PATH-CATEGORY ALLOWLISTS ("docs are safe", "review records are harmless"): explicitly REJECTED, not deferred. They reason about who probably wrote a file rather than whether it can conflict, which is the fail-open inference `d07nz2` prohibits.
- THE DEFERRAL LADDER ITSELF: `51vw4y`. This plan depends on it and does not reimplement any rung.
- THE EXTRACTION: `6sb3yu`. This plan depends on it and must not perform it.
- OWNERSHIP DETECTION (`a8eufb`): would improve the refusal MESSAGE by naming whose dirt it is; orthogonal to which paths are checked.

## Scope check

- Over-scope: none. One shared module, two drivers (call sites only), two test files.
- Under-scope: this plan does NOT extract the function (`6sb3yu`), does NOT add or alter any ladder rung (`51vw4y`), and does NOT narrow the refusal by content or category.

## Required tests / validation

New `tests/test_merge_dirty_scope.py` driving REAL git merges in throwaway repositories, covering the reproduced rename case, the three previously-integrating cases, and a genuine conflict. Plus the bare suite on a self-measured delta.

## Spec / documentation sync

No `.spec.md` is amended: this plan changes which paths a check consults, not any contract. Spec `25kzda`'s integration dispositions (`integration-blocked`, `merge-conflict`) already exist and keep their meanings; this plan makes the classification ACCURATE rather than redefining either.

The operator-facing refusal reason is user-facing prose: it must name the offending paths and must NOT tell the operator to commit or stash work AGENTS.md forbids them to touch (`z2isfg` wording discipline). Write no em or en dashes there.

## Open questions

### OQ-01: Should the widened set also include paths a merge would write only under conflict resolution?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED as authored: NO, out of scope and unnecessary. The merge-base-to-both-tips union covers every path a clean merge writes, which is the case the guard runs before. A path written only DURING conflict resolution is by definition already a `merge-conflict`, which stays terminal and correctly needs a human, so classifying it as deferrable dirt would be wrong. Widening further would also risk refusing integrations that would have succeeded, which E-03's anti-regression half exists to prevent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "def dirty_tree_overlap" agent_workflows/*.py` showing EXACTLY ONE definition and naming its module. Paste evidence the ladder is present (the `integration-deferred` status and its non-terminal treatment). If either check failed and you stopped, paste what you found and confirm NO edit was made; a stop-and-report is a successful outcome for this item, not a failure.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the new path-set computation and the git commands it runs. Paste the REPRODUCED CASE end to end: build base/lane/main-rename, show `dirty_tree_overlap` returning `[]` for the OLD input set and NON-EMPTY for the new one, in the same fixture. Confirm the rename endpoint handling survived by pasting a `orig -> dest` porcelain line being parsed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the reproduced case's disposition as `integration-blocked` (NOT `merge-conflict`) with the operator-facing reason naming `renamed.txt`.
    THEN PASTE THE ANTI-REGRESSION SET, which is the half that can actually break something: a clean main fast-forwarding; a clean advanced main non-ff merging; and dirt on a genuinely NON-overlapping path still integrating with the dirty edit shown intact afterwards. Any previously-integrating case that now refuses is a FAILED validation.
    Paste a genuine textual conflict still returning `merge-conflict`, proving the terminal path survives.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new test FAILING against pre-change HEAD on the rename case and passing after. Paste proof the tests drive REAL merges (the fixture's git commands), not a hand-built path list. Paste the object-identity check showing both drivers reach ONE `dirty_tree_overlap`.
    Paste the bare `python3 -m pytest` summary line with a self-measured BEFORE baseline and the AFTER-minus-BEFORE failure set EMPTY. Inside a lane worktree, ~14 `test_run_viewer.py` failures belong to the separate `agrlvw` defect (plan `utwr6y`); do not report them as this plan's.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`).

THIS PLAN IS ORDER-SENSITIVE AND E-01 ENFORCES IT. It declares `executed:6sb3yu` (so there is ONE function to fix, not two) and `executed:51vw4y` (so a widened refusal is deferrable rather than terminal). The runner re-checks dependencies at dispatch, so an unmet edge marks this item `dependency-blocked` and continues. Do NOT hand-run this plan against a tree where either is missing: with two copies you would double-patch, and without the ladder you would make transient dirt permanently fatal more often, which is precisely what `5wdoze:113` warns against.

WIDENING A REFUSAL CAN ONLY REFUSE MORE, so the anti-regression evidence in V-03 is not optional garnish; it is the proof this plan did not break integration. If a previously-integrating case now refuses, the plan is wrong, not the case.

DO NOT RELAX ANY REFUSAL to make a test pass, and do not resolve dirt. The driver's only recovery on this path is `git merge --abort`; keep it that way.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting, and re-locate every cited symbol, since this plan's own line numbers are the second generation and will move again.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

On completion, close backlog `h1ksy6` (this plan carries `- From-Backlog: h1ksy6` and inherits its `Blocks-Release: next`). Note `h1ksy6`'s own text still describes a two-copy tree and cites stale line numbers; the close should not propagate those.
