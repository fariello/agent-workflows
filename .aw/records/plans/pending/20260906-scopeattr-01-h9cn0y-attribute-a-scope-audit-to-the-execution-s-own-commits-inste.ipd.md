# IPD: Attribute a scope audit to the execution's own commits instead of everything since its base

- Date: 2026-09-06
- Kind: child
- Concern: `aw ipd finalize` demands a `--scope-reason` for every path ANY agent committed since the finalizing plan's begin receipt was frozen. MEASURED 2026-09-07 finalizing `mm6wuz`: its receipt records `base_head: 6091014ce127...` frozen at `01:07:31Z`, thirteen commits had landed on main by finalize time, and finalize refused with TEN required `--scope-reason` entries of which only TWO were genuinely that plan's. The other eight are verifiable as other agents' work by `git log -1 -- <path>`: `agent_workflows/attention.py` was `976409e3`, `agent_workflows/commit_lock.py` was `798c5cb5`, `agent_workflows/ipd_lifecycle.py` was `efc7a1a1`, plus `git_commit_helper.py` and four test files from the same isolated-commit work.
  THE MECHANISM, AND IT IS HALF-GUARDED ALREADY. `_paths_changed_by_this_execution` unions `git diff --name-only <base>..HEAD` with `git status --porcelain` (`ipd_lifecycle.py:1194-1207`), and its own docstring concedes the gap: "unrelated concurrent commits on disjoint paths are handled by the intervening-commit collision check, not here". `_working_tree_path_is_owned` (`:1282-1302`) then filters the WORKING-TREE half with an ownership test whose stated reasoning applies verbatim to the committed half: an unowned path "in a shared checkout is almost certainly a concurrent agent's in-flight work, and demanding a `--scope-reason` for it would force this plan to either write a false claim into its permanent record or block on a condition it does not control". That is precisely what happens for a COMMITTED path, because a committed path lands in `committed_set` and is therefore treated as this execution's to justify (`:1414-1428`).
  WHY THIS IS WORSE THAN AN ANNOYANCE. First, IT CORRUPTS THE RECORD: the reasons are written into the plan's finalize evidence and its workflow history, so an executed plan asserts it edited files it never touched, and a future reader auditing what a plan changed gets a wrong answer from the artifact meant to be authoritative. In `mm6wuz`'s case each spurious reason explicitly names the real author and says NOT THIS PLAN'S EDIT, which keeps the record honest only because a human noticed. Second, IT TRAINS THE WRONG REFLEX: ten paths to justify with eight spurious is the condition under which an agent invents ten plausible justifications and moves on, and the gate's value depends entirely on a `--scope-reason` meaning something. That is the same dynamic `rnl3b7` records for `--no-verify` becoming routine. Third, IT SCALES WITH CONTENTION, so it is worst exactly when it matters most: a long execution in a busy repository accumulates the most unrelated commits.
- Scope: Attribute the committed half of the scope audit by AUTHORSHIP rather than by time window. For an isolated lane the attribution boundary already exists and is exact (the lane branch); for an in-place execution, extend the existing ownership filter to the committed half using the evidence the run already records. Keep the gate FAIL-CLOSED for a genuinely unattributable path: the goal is to stop demanding justification for another agent's commit, never to stop demanding it for an unexplained edit.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_finalize_scope_ownership.py, tests/test_finalize_isolated_commit.py
- Item-Dependencies: none
- Status: to-review
- Set: scopeattr
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: h9cn0y
- From-Backlog: hyx1dg

## Workflow history

- 2026-09-06 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `hyx1dg`, filed after finalizing `mm6wuz` required ten `--scope-reason` entries of which eight named other agents' commits. Every claim re-verified against code at HEAD `51524e28` rather than trusted. THE FINDING THAT SHAPES THIS PLAN, and it makes the fix an EXTENSION rather than a new mechanism: the ownership filter ALREADY EXISTS and its docstring already states the exact reasoning this plan applies (`ipd_lifecycle.py:1289-1302`), including that demanding a reason for an unowned path "would force this plan to either write a false claim into its permanent record or block on a condition it does not control". It simply only guards the working-tree half. `_paths_changed_by_this_execution`'s own docstring also CONCEDES the gap in as many words ("unrelated concurrent commits on disjoint paths are handled by the intervening-commit collision check, not here"), so this is a known-and-documented limitation rather than an oversight, which is why the plan's job is to close it rather than to argue it exists. ALSO CONFIRMED: `_changed_path_sources` (`:1170`) already SPLITS the two halves and `_paths_changed_by_this_execution` is explicitly "kept as the UNION-returning surface so every existing caller (notably `check_engine.check_scope_drift`) is unaffected", so a committed-half ownership filter has a natural seam and a documented compatibility constraint. `isolated_baseline` (`:865`, `:894`) already distinguishes the lane case from the in-place case, which is the discriminator E-01 needs.

## Goal

Stop making a plan justify another agent's commits, so a `--scope-reason` keeps meaning something and an executed plan's record says only what that plan actually changed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: attribute the isolated case exactly

- [ ] E-01 For an ISOLATED execution, attribute the committed half to the LANE BRANCH, which is an exact boundary rather than an inference. A lane's commits are precisely `base..lane_head`, so `git diff --name-only <base>..<lane_head>` IS this execution's committed change set, with no concurrent commit in it by construction.
  THE DISCRIMINATOR ALREADY EXISTS: `isolated_baseline` (`ipd_lifecycle.py:865`, `:894`) already distinguishes "the turn executes in THIS working tree" from "the turn executes in a FRESH worktree cut at this repository's head". Use it rather than re-deriving isolation from the environment.
  DO NOT CHANGE `base_head`. Its docstring records that `isolated_baseline` deliberately does NOT influence it (`:944`), and that separation is load-bearing for the receipt's other consumers. This item changes what the committed half is diffed AGAINST, not what the receipt freezes.
  - Depends on: none
  - Expected outcome: an isolated execution's committed half contains exactly its own lane commits; a concurrent commit on main cannot appear in it; `base_head` is unchanged in value and meaning.
  - Execution state: pending

- [ ] E-02 For an IN-PLACE execution, extend the EXISTING ownership filter to the committed half rather than writing a second one. `_working_tree_path_is_owned` (`:1282-1302`) already answers "is this path attributable to THIS execution" from positive evidence: it matches the frozen `Scope-Paths`, or it also appears in the other half, or it is an implicit lifecycle allowance.
  THE RUN ALREADY RECORDS THE ANSWER, so this is consumption rather than inference: the outcome record persists `last_outcome.commits[].sha` and `.paths` (verified present in `mm6wuz`'s state.json, listing all ten of its real paths), so an execution's own commits are knowable by sha. Prefer that evidence over a heuristic where it is available, and fall back to the ownership predicate where it is not.
  `_changed_path_sources` (`:1170`) ALREADY SPLITS THE HALVES, and `_paths_changed_by_this_execution` is documented as "kept as the UNION-returning surface so every existing caller (notably `check_engine.check_scope_drift`) is unaffected". So add the filter at the split, and DO NOT change the union surface's shape, or `aw check`'s scope-drift rule changes behavior as a side effect.
  - Depends on: E-01
  - Expected outcome: an in-place execution's committed half excludes paths attributable to another actor; the union surface's shape is unchanged so `check_scope_drift` is unaffected; no second ownership predicate exists.
  - Execution state: pending

### Task group 2: keep the gate honest

- [ ] E-03 KEEP THE GATE FAIL-CLOSED for a genuinely unattributable committed path, and make the refusal ACTIONABLE. This item is what stops the plan from becoming a way to skip scope justification.
  A PATH THIS EXECUTION CANNOT DISCLAIM STILL REQUIRES A REASON. If the evidence does not positively attribute a committed path to ANOTHER actor, it stays in the out-of-scope set exactly as today. The ownership filter's existing discipline is the model: it "only ever REMOVES paths from the out-of-scope set; it never adds any", and it removes only on POSITIVE evidence of non-ownership.
  REPORT THE DISTINCTION, because the current message is unactionable. "out-of-scope path needs a `--scope-reason`" gives the operator nothing when the path is another agent's; "this path changed since your base but was committed by `<sha>`, which is not this execution's" tells them immediately that no action is needed. Name the sha.
  DO NOT SUPPRESS THE INTERVENING-COMMIT SIGNAL. `_intervening_commits_touching` (`:1211`) computes which IN-SCOPE paths an intervening commit touched, and that collision signal is a different and still-wanted fact: another agent editing a path this plan DECLARED is worth surfacing. Leave it intact.
  - Depends on: E-02
  - Expected outcome: an unattributable committed path still demands a reason; a path positively attributed to another actor is excluded and, where surfaced, names the sha; the intervening-commit collision signal is unchanged.
  - Execution state: pending

### Task group 3: prove it

- [ ] E-04 Test the ATTRIBUTION deterministically, in a throwaway repository with two simulated actors. Assert: a path committed by THIS execution requires a reason if out of scope; a path committed by ANOTHER actor after `base_head` does NOT; a path with no positive attribution to another actor STILL requires one (the fail-closed case); and the intervening-commit signal still fires for an in-scope path another actor touched.
  REPRODUCE THE MEASURED INCIDENT as a regression fixture, using its real shape: a plan whose two genuine out-of-scope paths are `CHANGELOG.md` and one test file, with eight further paths committed by other actors between begin and finalize. Assert finalize demands exactly TWO reasons, not ten. That is the case that corrupted a record tonight.
  COVER BOTH EXECUTION MODES, since E-01 and E-02 take different routes: an isolated lane and an in-place execution must each attribute correctly.
  - Depends on: E-03
  - Expected outcome: four attribution cases plus the incident fixture pass; the fixture demands two reasons rather than ten; both execution modes are covered.
  - Execution state: pending

- [ ] E-05 Prove NOTHING ELSE MOVED, because this change touches a gate several other surfaces read. Assert `check_engine.check_scope_drift` behaves identically before and after, since `_paths_changed_by_this_execution`'s union surface exists precisely to keep it unaffected. Assert the in-scope-unmodified (`--scope-ack`) direction is untouched. Assert a finalize with genuinely zero out-of-scope paths still completes without prompting.
  RUN THE SUITE BARE (`python3 -m pytest`) and state before/after counts. MEASURE YOUR OWN BEFORE-BASELINE: the suite is NOT green at HEAD (`1 failed, 5612 passed` at authoring, the failure being pre-existing `test_orchestrator_retirement::RealRepositorySets`), so the criterion is that the AFTER failure set minus the BEFORE set is EMPTY.
  VALIDATE IN THE REAL CHECKOUT for anything reading `.aw/records/runs/`, which is gitignored and makes such tests fail in a bare worktree while passing in the real checkout.
  - Depends on: E-04
  - Expected outcome: `check_scope_drift` unchanged, the `--scope-ack` direction unchanged, a clean finalize still clean; bare suite delta empty with counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE OWNERSHIP FILTER ALREADY EXISTS AND ALREADY ARGUES THIS PLAN'S CASE. `_working_tree_path_is_owned`'s docstring (`ipd_lifecycle.py:1289-1302`) states that an unowned path "in a shared checkout is almost certainly a concurrent agent's in-flight work, and demanding a `--scope-reason` for it would force this plan to either write a false claim into its permanent record or block on a condition it does not control". This plan extends that reasoning to the committed half.
- THE GAP IS DOCUMENTED, NOT ACCIDENTAL. `_paths_changed_by_this_execution`'s docstring says "unrelated concurrent commits on disjoint paths are handled by the intervening-commit collision check, not here", which is exactly the case that misfires.
- THE HALVES ARE ALREADY SPLIT. `_changed_path_sources` (`:1170`) returns them separately and the union surface is "kept ... so every existing caller (notably `check_engine.check_scope_drift`) is unaffected". That is both the seam to use and a compatibility constraint to honor.
- THE FILTER'S DISCIPLINE IS ONE-DIRECTIONAL: it "only ever REMOVES paths from the out-of-scope set; it never adds any", and it removes only on POSITIVE evidence. Preserve that.
- `isolated_baseline` (`:865`, `:894`) ALREADY DISTINGUISHES the lane case from the in-place case, and deliberately does NOT influence `base_head` (`:944`).
- THE RUN ALREADY RECORDS ITS OWN COMMITS: `last_outcome.commits[].sha` and `.paths` are persisted (verified in `mm6wuz`'s state.json, listing exactly its ten real paths), so attribution has real evidence available rather than only heuristics.
- `_intervening_commits_touching` (`:1211`) is a DIFFERENT and still-wanted signal: another agent touching a path this plan DECLARED is worth surfacing.
- Run the suite BARE: `python3 -m pytest`. The suite is NOT green at HEAD, so judge on the DELTA.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | **THE MEASURED INCIDENT.** Finalizing `mm6wuz` demanded TEN `--scope-reason` entries; only TWO (`CHANGELOG.md`, `tests/test_runner_stop_level3.py`) were that plan's. | `aw ipd finalize mm6wuz` refusal output, 2026-09-07 |
| F-2 | THE EIGHT SPURIOUS PATHS ARE VERIFIABLY OTHER AGENTS' WORK: `attention.py` -> `976409e3`, `commit_lock.py` -> `798c5cb5`, `ipd_lifecycle.py` -> `efc7a1a1`, plus `git_commit_helper.py` and four test files from the same isolated-commit work. | `git log -1 --format="%h %s" -- <path>` per path |
| F-3 | Thirteen commits landed on main between `mm6wuz`'s begin receipt (`base_head: 6091014c`, frozen `01:07:31Z`) and its finalize. | `git log --oneline 6091014c..HEAD --no-merges \| wc -l` |
| F-4 | **THE GAP IS DOCUMENTED IN THE CODE ITSELF**, which is why this plan extends rather than argues: `_paths_changed_by_this_execution` says "unrelated concurrent commits on disjoint paths are handled by the intervening-commit collision check, not here". | `ipd_lifecycle.py:1194-1207` |
| F-5 | **THE FIX'S REASONING IS ALREADY WRITTEN**, for the other half: the ownership filter states that demanding a reason for an unowned path forces a plan "to either write a false claim into its permanent record or block on a condition it does not control". | `ipd_lifecycle.py:1289-1302` |
| F-6 | A COMMITTED PATH IS TREATED AS THIS EXECUTION'S BY CONSTRUCTION: the working-tree ownership test is applied only to paths NOT in `committed_set`, so any concurrent commit passes straight into `out_of_scope`. | `ipd_lifecycle.py:1414-1428` |
| F-7 | THE UNION SURFACE IS A COMPATIBILITY CONSTRAINT: it is documented as kept so `check_engine.check_scope_drift` is unaffected, so the filter must be added at the split, not by changing the union's shape. | `ipd_lifecycle.py:1204-1207` |
| F-8 | THE ISOLATED CASE HAS AN EXACT BOUNDARY AVAILABLE: `isolated_baseline` already distinguishes the modes, and a lane's commits are precisely `base..lane_head`, so no inference is needed there. | `ipd_lifecycle.py:865`, `:894` |
| F-9 | THE RUN ALREADY PERSISTS ITS OWN COMMIT SHAs AND PATHS, so in-place attribution has evidence rather than only a heuristic. | `mm6wuz` state.json `last_outcome.commits[]` |
| F-10 | THE RECORD-CORRUPTION IS REAL, not hypothetical: `mm6wuz`'s finalize evidence now carries eight reasons for paths it never touched, each explicitly saying NOT THIS PLAN'S EDIT and naming the real author, which was only possible because a human checked. | commit `b2bda903`; the plan's workflow history |
| F-11 | **THIS EXACT DEFECT WAS ALREADY FIXED ONCE, FOR THE OTHER HALF**, which is the strongest available evidence that the fix shape is right and that this plan is finishing an incomplete job rather than proposing a theory. `tests/test_finalize_scope_ownership.py` exists (11 tests) and its module docstring states the defect in almost this plan's words: `_paths_changed_by_this_execution` "unioned the committed diff since the frozen base with the ENTIRE `git status --porcelain` and applied no ownership filter, so in a SHARED checkout every concurrent agent's uncommitted file was attributed to whichever plan finalized first. That plan's only options were to write a false `--scope-reason` into its permanent record or to block until every other agent happened to be clean." It also records the correct discipline: the fix "RESCOPES the gate; it does not remove it", and a disregarded path is "RECORDED as disregarded rather than silently dropped". Prior work `scopeattrib` Order 01 (`lbgzxg`) fixed the WORKING-TREE half and left the COMMITTED half, which is exactly what `mm6wuz` hit. | `tests/test_finalize_scope_ownership.py:1-12` |

## Proposed changes (ordered, validatable)

1. Attribute an isolated execution's committed half to its lane branch, an exact boundary (E-01).
2. Extend the existing ownership filter to the committed half for the in-place case, consuming the run's own recorded commit shas, without changing the union surface (E-02).
3. Keep the gate fail-closed for an unattributable path and make the refusal name the responsible sha; leave the intervening-commit signal intact (E-03).
4. Pin four attribution cases plus the incident fixture, across both execution modes (E-04).
5. Prove `check_scope_drift`, the `--scope-ack` direction, and a clean finalize are all unchanged (E-05).

## Deferred / out of scope (with reason)

- COMMIT TRAILERS (`a8eufb`). `AW-Run:`/`AW-Item:` trailers would make authorship explicit and are the natural long-term substrate. Deliberately not required here: this plan closes the defect with evidence that ALREADY EXISTS (the lane boundary, the recorded commit shas), so it need not wait on a wider change. Note trailers are insufficient in general, since they mark COMMITS and not working-tree churn, which is why `p8ni63` records the same limitation; but for THIS defect the offending paths are precisely commits, so trailers would address it and remain worth doing.
- THE WORKING-TREE HALF'S ACCEPTED COST. The existing filter already documents that an executor's OWN uncommitted out-of-scope edit can be excused; that trade was made deliberately (Order 01 OQ-01/F3) and is not revisited here.
- CHANGING `base_head` OR THE RECEIPT SCHEMA. The receipt's freeze is load-bearing for other consumers and `isolated_baseline` deliberately does not influence it. This plan changes what the committed half is compared against, not what is frozen.
- THE INTERVENING-COMMIT COLLISION SIGNAL. Different fact, still wanted, explicitly preserved by E-03.
- `aw check`'s SCOPE-DRIFT RULE. Must be UNAFFECTED, which is why E-02 works at the split rather than the union; E-05 verifies it.
- THE OTHER DEFECTS FROM THE SAME RECOVERY. `integearn` (`32ij2j`, `xtklpd`) covers the earned-integration gate and its misreport; `integpath` covers the four `integdefer` items; `depreview` (`yf9fj9`, `phawyy`) covers the dependency gate and its missing reason. All surfaced from the same incident and all are separate mechanisms.

## Scope check

- Over-scope: none. One lifecycle module plus two test modules.
- Scope-Paths justification: `agent_workflows/ipd_lifecycle.py` holds `_changed_path_sources`, `_paths_changed_by_this_execution`, `_working_tree_path_is_owned`, the `out_of_scope` construction, and the finalize refusal (E-01..E-03); `tests/test_finalize_scope_ownership.py` is the EXACT prior-art suite for this defect (it already proves the working-tree half is ownership-filtered) and is where the committed-half cases belong; `tests/test_finalize_isolated_commit.py` covers the isolated mode E-01 changes.
- Under-scope, stated rather than left as `none`: this child does not add commit trailers, does not revisit the working-tree half's accepted cost, does not change `base_head` or the receipt schema, does not alter the intervening-commit signal, and does not touch `aw check`'s scope-drift rule. Each is excluded with a reason above.

## Required tests / validation

- `python3 -m pytest` BARE, before and after, with the `N passed` summary line pasted and counts stated. MEASURE YOUR OWN BEFORE-BASELINE; the criterion is that the AFTER failure set minus the BEFORE set is EMPTY, not an absolute count.
- Targeted: `tests/test_finalize_scope_ownership.py`, `tests/test_finalize_isolated_commit.py`, plus whatever module covers `check_engine.check_scope_drift`.
- A REPRODUCTION OF THE INCIDENT in a throwaway repository with two simulated actors, showing finalize demand TWO reasons rather than TEN, before and after.
- A CLEAN-FINALIZE CHECK: a plan with genuinely zero out-of-scope paths still finalizes without prompting.
- VALIDATE IN THE REAL CHECKOUT for anything reading the gitignored `.aw/records/runs/`.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw sanitize --agent` clean.

## Spec / documentation sync

`_paths_changed_by_this_execution`'s and `_working_tree_path_is_owned`'s DOCSTRINGS are the authoritative prose statement of how attribution works, and both must be updated: the first currently concedes the gap this plan closes, and the second describes an ownership test that now covers both halves. Extend them rather than replacing them, since each records reasoning (the union-surface compatibility constraint, the one-directional removal discipline) that must survive.

No spec change is expected. If the executor finds spec text asserting that a scope audit covers everything changed since the frozen base, NOTE IT for an amendment rather than editing the spec here.

The finalize refusal message is operator-facing: it must name the responsible sha for an excluded path where it surfaces one, and must not imply the operator did something wrong. Write no em or en dashes in user-facing prose.

## Open questions

### OQ-01: Should attribution prefer the run's recorded commit shas or the lane-branch boundary?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: USE THE LANE BOUNDARY WHERE IT EXISTS, and the recorded shas otherwise. They answer the same question with different strength. For an isolated execution the lane branch is EXACT: its commits are `base..lane_head` by construction, so no concurrent commit can be inside it and no inference is required. For an in-place execution there is no such boundary, and the run's persisted `last_outcome.commits[].sha` is the best available positive evidence. Preferring the exact boundary where available means the common case (isolation is the default) needs no heuristic at all, which is the safest possible shape for a gate.

### OQ-02: What if a path was committed by BOTH this execution and another actor?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: IT REMAINS THIS EXECUTION'S TO JUSTIFY. The filter must remove a path only on positive evidence that this execution did NOT touch it, and a path this execution committed fails that test regardless of who else committed it. This follows the existing filter's one-directional discipline ("only ever REMOVES paths from the out-of-scope set") and errs toward demanding a reason, which is the correct direction for a gate whose value depends on the field meaning something. The intervening-commit signal separately surfaces the other actor's involvement, so the information is not lost.

### OQ-03: Should an excluded path be reported at all, or silently dropped?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REPORTED, not silent, but as INFORMATION rather than as a demand. Silently dropping it would hide a real fact (a path in the plan's territory moved under it) and would make the audit harder to trust when it matters. Reporting it as "changed since your base but committed by `<sha>`, not this execution's" costs one line, tells the operator immediately that no action is needed, and preserves the audit trail. The existing filter's precedent supports this: it keeps what it disregarded VISIBLE ("what the ownership filter DISREGARDED, kept visible rather than silently dropped") rather than discarding it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the isolated-mode attribution code showing the lane boundary is used and naming the `isolated_baseline` discriminator. Paste a probe where a concurrent commit lands on main during an isolated execution, showing that path is ABSENT from the committed half. Paste `base_head` before and after, unchanged, and confirm in one sentence that the receipt's freeze was not touched.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the in-place attribution code and confirm by inspection that it EXTENDS `_working_tree_path_is_owned`'s predicate rather than adding a second one. Paste evidence the run's recorded commit shas are consumed. THEN paste proof the union surface's shape is unchanged, and `check_engine.check_scope_drift`'s tests passing, since that compatibility is the documented reason the union exists.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the FAIL-CLOSED case: a committed out-of-scope path with no positive attribution to another actor STILL demands a `--scope-reason`. This is the validation that proves the plan did not become a way to skip scope justification. Paste the improved refusal text for an excluded path, showing it names the responsible sha. Paste the intervening-commit signal still firing for an in-scope path another actor touched.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the ACTUAL output of the four attribution cases in both execution modes. Paste the INCIDENT FIXTURE and its assertion that finalize demands exactly TWO reasons; paste the same fixture against the PRE-FIX code demanding TEN, so the contrast is demonstrated rather than asserted. A fixture only ever run against the fixed code would pass even if attribution were inverted.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `check_scope_drift`'s tests passing unchanged, the `--scope-ack` (in-scope-unmodified) direction unchanged, and a clean finalize completing without prompting. Paste the BARE `python3 -m pytest` summary with before/after counts and show the AFTER-minus-BEFORE failure set is EMPTY. State that any test reading `.aw/records/runs/` was validated in the REAL checkout.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires explicit human approval (`- Status: approved`). Every open question above is resolved.

Scope fence: touch ONLY the three paths in `Scope-Paths`. Do NOT change `base_head` or the receipt schema. Do NOT change the shape of `_paths_changed_by_this_execution`'s union surface (that would alter `aw check`'s scope-drift rule as a side effect). Do NOT suppress or alter the intervening-commit collision signal. Do NOT write a second ownership predicate. Do NOT relax the `--scope-ack` (in-scope-unmodified) direction. Do NOT edit any spec. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

Commit ONLY the files you changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook. THIS IS A SHARED CHECKOUT: run `aw runs` before starting.

HARD HONESTY RULE: tests must be RUN and their ACTUAL output pasted into `Observed evidence`, including the `N passed` summary line from a BARE `python3 -m pytest`. A `V-*` item may not be marked `pass` from the matching execution checkmark. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` carries concrete pasted evidence.

YOU WILL BE MODIFYING THE GATE THAT GOVERNS YOUR OWN FINALIZE. Expect to meet it while working, and do NOT reach for a false `--scope-reason` to get your own work through. If it demands justification for a path you did not touch, that is either this plan's remaining work or a finding worth recording, and either way it is the information the plan exists to produce.

THE ITEM THAT MATTERS MOST IS V-03's FAIL-CLOSED CASE. This change makes a demanding gate demand less, which is the direction in which a mistake becomes invisible: an over-broad exclusion would let a genuine unexplained out-of-scope edit through with no reason recorded, and nothing would ever complain. A path is excluded ONLY on positive evidence that another actor committed it. If you find yourself excluding a path because you could not prove this execution DID touch it, the logic is inverted.

BASELINE HONESTY: the suite is NOT green at HEAD and this plan does not make it green. Judge on the DELTA, and do not report the pre-existing `test_orchestrator_retirement` failure as yours.

On completion, close backlog `hyx1dg`, which this plan carries as `- From-Backlog:`. That item carries no release gate, so none is inherited.
