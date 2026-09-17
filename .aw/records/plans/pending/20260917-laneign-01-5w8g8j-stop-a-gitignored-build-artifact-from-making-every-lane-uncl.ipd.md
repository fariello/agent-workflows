# IPD: Stop a gitignored build artifact from making every lane unclassifiable so lanes are never torn down

- Date: 2026-09-17
- Kind: child
- Concern: A lane that finished cleanly is preserved forever because it contains `__pycache__/*.pyc` and the run's own scratch files. `LaneInventory.classified` is `readable and not self.unknown and not self.uncollected_submission`, and `unknown` includes `unknown_ignored`, so ONE unaccounted gitignored file makes the lane unclassifiable and teardown refuses. Observed 2026-09-17 in run `run-20260917T023628Z-4108757`: lane `aw/lane/3dki3o` was PRESERVED naming "4176 unknown IGNORED file(s)", and the first eight listed were the run's OWN scratch (`commit-msg-plan.txt`, `commit-msg-tests.txt`, `e01-measurements.txt`, `final-suite.txt`) followed by `__pycache__/*.pyc`. Running Python in a lane is enough to guarantee this, so it is not an edge case: measured at authoring, this checkout holds 38 undisposed lane worktrees.
- Scope: Make the retention classifier account for gitignored paths that are provably not work product (Python bytecode caches and the run's own scratch under its submission directory), so a genuinely clean lane is torn down while a lane holding UNEXPLAINED content is still preserved. Does NOT change the dirty-tracked or unknown-untracked rules, does NOT touch the preserve-on-unreadable rule, and does NOT weaken the refusal for content the driver cannot account for.
- Scope-Paths: agent_workflows/lane_containment.py, tests/test_lane_retention.py
- Item-Dependencies: none
- Status: to-review
- Set: laneign
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 5w8g8j

## Workflow history

- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored after the maintainer asked what the "4,176-file lane-retention noise" from their overnight run actually was. INVESTIGATING IT CHANGED THE FINDING, which is why this plan exists rather than a one-line note: I had described it in chat as cosmetic message noise. It is not. `RETENTION_REASON_PATH_LIMIT` (`lane_containment.py:2850`) already caps the SENTENCE at 10 paths and its comment records the same 4134-file `__pycache__` measurement, so the message length is a solved, deliberate trade-off ("The EXACT COUNT is always stated, the full lists always survive in `as_dict()`... Truncating the recorded evidence instead would be the dishonest choice"). What is NOT solved is the CONSEQUENCE: `classified` (`:2889`) is false whenever `unknown_ignored` is non-empty, so the same bytecode files that the comment treats as a message-length problem also block teardown unconditionally. Measured at authoring: 38 lane worktrees are still allocated in this checkout, which is the accumulated cost.

## Goal

Let a clean lane be reclaimed. A lane whose only unaccounted content is bytecode the interpreter wrote
and scratch the run itself wrote is not holding work, and treating it as if it were means no lane is ever
torn down and the checkout grows a worktree per item forever.

The preservation rule itself is right and stays: a lane holding content the driver cannot explain must be
kept. This narrows what counts as unexplained, it does not relax what happens when something is.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the real population before deciding what is discardable

- [ ] E-01 INVENTORY THE ACTUAL UNACCOUNTED-IGNORED POPULATION across the lanes present at execution HEAD, and refuse to proceed to E-03 on this plan's figures. For each lane worktree, run the same inventory the classifier uses and group its `unknown_ignored` paths by shape: Python bytecode (`__pycache__/`, `*.pyc`), the run's own submission scratch (under the lane-submission subdir), lane inputs (under the lane-input subdir), and EVERYTHING ELSE. The last group is the one that decides this plan's safety: if it is non-empty, those paths are real unexplained content and the allowlist must not swallow them.
  - Depends on: none
  - Expected outcome: a pasted per-shape count across all lanes plus the complete "everything else" list (or an explicit statement that it is empty), measured at execution HEAD.
  - Execution state: pending

- [ ] E-02 CONFIRM THE CONSEQUENCE IS TEARDOWN REFUSAL, not merely a long message, since that is the claim this plan rests on and I want it re-proven rather than inherited. Show that `classified` returns False for an inventory whose ONLY unknown content is bytecode, and that the teardown decision therefore preserves the lane. Also confirm the message cap is already working as designed (the sentence truncates at 10, the full list survives in the record), so this plan does not re-solve a solved problem.
  - Depends on: none
  - Expected outcome: pasted evidence that a bytecode-only inventory yields `classified=False` and a preserved lane, plus confirmation that the reason sentence is capped and the recorded evidence is complete.
  - Execution state: pending

### Task group 2: narrow what counts as unexplained, without weakening the refusal

- [ ] E-03 ADD A NARROW, ENUMERATED DISCARDABLE-IGNORED CLASSIFICATION for paths that are provably not work product, keyed on shape rather than on a broad "ignored means fine" rule. The two candidate classes from E-01 are Python bytecode and the run's own scratch under its submission directory. ENUMERATE them as named constants with the reason at each, following the same discipline `runner_shared`'s injection list uses, so the allowlist cannot grow silently. DO NOT make `unknown_ignored` stop counting in general: an ignored file the driver cannot explain is exactly what spec R5.5's fail-toward-preservation rule is for, and a blanket exemption would delete the guard rather than sharpen it.
  - Depends on: E-01, E-02
  - Expected outcome: a tested classification in which a bytecode-only or scratch-only lane is classifiable, and a lane holding ANY other ignored file is still not; the allowlist enumerated with per-entry reasons.
  - Execution state: pending

- [ ] E-04 PROVE THE REFUSAL STILL FIRES, which is the load-bearing half and must be an INJECTED-REGRESSION test rather than an assertion about today's tree. Plant an unexplained ignored file in a lane fixture (something matching no allowlist entry) and show the lane is still preserved with the path NAMED in the reason. Then plant one file of each allowlisted shape and show the lane is torn down. A test that only checks the second half would pass while the guard was gone.
  - Depends on: E-03
  - Expected outcome: pasted evidence of both directions: an unexplained ignored file preserves the lane and is named; allowlisted shapes alone allow teardown.
  - Execution state: pending

- [ ] E-05 REPORT THE BACKLOG OF UNDISPOSED LANES this defect has already accumulated, as information for the maintainer rather than an action. State how many lane worktrees exist at execution HEAD, how many would become classifiable under E-03's rule, and how many hold genuinely unexplained content and would still be preserved. Do NOT tear any of them down: they may hold work, several correspond to plans whose disposition a human has not reviewed, and reclaiming them is a separate decision with its own risk.
  - Depends on: E-03
  - Expected outcome: a written count of existing lanes partitioned into would-become-classifiable and would-still-be-preserved, with an explicit statement that none was torn down by this plan.
  - Execution state: pending

## Project conventions discovered (Step 0)

- FAIL TOWARD PRESERVATION IS THE SPEC'S RULE, not an accident. `LaneInventory`'s docstring records that an inventory which could not run "knows nothing, so `classified` is `False` and the lane is preserved (spec R5.5's fail-toward-preservation rule)". This plan must keep that posture and narrow only what counts as unknown.
- THE MESSAGE CAP IS ALREADY SOLVED AND DELIBERATE. `RETENTION_REASON_PATH_LIMIT = 10` (`:2850`) exists because "a real lane whose `__pycache__` trees are ignored inventoried 4134 unknown ignored files", and its comment states the honesty rule: cap the sentence, never the recorded evidence. So the 4,176-file output the maintainer saw is the cap WORKING; the defect is elsewhere.
- THE INVENTORY IS DELIBERATELY PER-FILE. `LANE_INVENTORY_STATUS_ARGS` uses `--ignored=traditional` rather than `matching` precisely so ignored files are seen individually, because `matching` reports the ignored DIRECTORY and would let an unexplained file under an ignored directory be classified by that directory alone (`:2809-2813`). Any fix must preserve per-file granularity rather than reintroducing directory-level judgement.
- TWO GITIGNORED PREFIXES ARE ALREADY PART OF THE DESIGN. `LANE_SUBMISSION_SUBDIR` and `LANE_INPUT_SUBDIR` both live under `.aw/state/` deliberately, "that prefix is gitignored... so a materialized input never appears as a dirty TRACKED path in the lane and cannot contaminate the integration diff" (`:2017-2022`). So the codebase already reasons about gitignored driver-written content; this plan extends that reasoning to teardown.
- A RECEIPT-ACCOUNTED PATH IS ALREADY DISCARDABLE. `resolve_lane_teardown` unions each item's `discardable` set and subtracts it from the final unknown sets (`:3413-3428`), so the mechanism for "explained content" exists. E-03 should extend that concept rather than invent a parallel one.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `LaneInventory.classified` (`lane_containment.py:2889`) | **ONE GITIGNORED BYTECODE FILE PREVENTS TEARDOWN FOREVER.** `classified` requires `not self.unknown`, and `unknown` includes `unknown_ignored`, so any `__pycache__/*.pyc` left by running Python in a lane makes the lane permanently unclassifiable. Running the test suite in a lane guarantees it. | the property definition at `:2884-2891`; the observed `3dki3o` preservation naming 4176 ignored files |
| F2 | HIGH | this checkout | **THE COST IS MEASURED AND ONGOING: 38 undisposed lane worktrees.** Every finished item leaves its lane allocated, so the checkout accumulates one worktree per executed plan indefinitely. | `git worktree list` at authoring: 38 entries matching `aw/lane` |
| F3 | MEDIUM | my own earlier report | **I MISDIAGNOSED THIS AS COSMETIC AND THE CODE PROVES OTHERWISE.** I told the maintainer it was message noise. `RETENTION_REASON_PATH_LIMIT`'s comment shows the message length was already measured (4134 files) and deliberately capped, so the visible output is the SOLVED part; the unsolved part is that the same files block teardown. Recorded so the plan is not read as re-solving the cap. | `:2844-2850` versus `:2889` |
| F4 | MEDIUM | the fix direction | **THE OBVIOUS FIX WOULD DELETE THE GUARD.** Making `unknown_ignored` stop counting toward `classified` would tear down every lane including one holding an unexplained ignored file, which is precisely what spec R5.5 exists to prevent. The fix must be a narrow enumerated allowlist, and E-04's injected regression is what proves it stayed narrow. | `LaneInventory`'s fail-toward-preservation docstring |
| F5 | LOW | `--ignored=traditional` rationale | A FIX MUST NOT REGRESS TO DIRECTORY-LEVEL JUDGEMENT. The inventory deliberately reports ignored files per-file so an unexplained file under an ignored directory is still seen. An allowlist keyed on a directory PREFIX must therefore match precisely (bytecode caches, the submission subdir) and never on `.aw/state/` wholesale, which would hide anything written there. | `:2805-2813` |
| F6 | LOW | E-05's scope | THE EXISTING 38 LANES ARE NOT THIS PLAN'S TO RECLAIM. Some may hold work whose disposition a human has not reviewed, and this session already found one lane (`i3d6ml`) holding two commits of correct unmerged work. Reporting them is useful; tearing them down would risk exactly the loss the retention rule prevents. | the session's own recovery of the `i3d6ml`, `tx6q0h` and `sy7uwh` lanes |

## Proposed changes (ordered, validatable)

1. Inventory the real unaccounted-ignored population per shape across all lanes, and list everything that is not bytecode or run scratch (E-01).
2. Re-prove that the consequence is teardown refusal, and that the message cap is already correct (E-02).
3. Add a narrow, enumerated discardable-ignored classification with per-entry reasons (E-03).
4. Prove the refusal still fires with an injected unexplained ignored file (E-04).
5. Report the existing undisposed-lane backlog without touching it (E-05).

## Deferred / out of scope (with reason)

- TEARING DOWN THE 38 EXISTING LANES. Reported by E-05, not acted on. At least one lane in this checkout recently held unmerged correct work, so bulk reclamation is a separate decision needing human review per lane.
- THE REASON-SENTENCE LENGTH. Already solved deliberately by `RETENTION_REASON_PATH_LIMIT` with the honesty rule stated in its own comment. Re-solving it would be churn.
- THE DIRTY-TRACKED AND UNKNOWN-UNTRACKED RULES. Untouched. An untracked file the driver cannot explain is a different and stronger signal than an ignored one, and this plan makes no claim about it.
- ADDING `__pycache__` TO `.gitignore` OR STOPPING PYTHON WRITING BYTECODE IN LANES. Both would mask the classifier defect rather than fix it, and the second would slow every lane's test run.
- THE PRESERVE-ON-UNREADABLE RULE. Explicitly out of scope: an inventory that could not run must keep preserving, and nothing here changes that path.

## Scope check

- Over-scope: none. One classification rule and its tests.
- Under-scope: none for the reported defect. Reclaiming existing lanes is deferred above with a reason.

## Required tests / validation

1. `python3 -m pytest` bare, pasted summary line, compared against the pre-execution baseline (also pasted).
2. A lane fixture whose only unaccounted ignored content is bytecode: shown classifiable and torn down AFTER the change, and shown NOT classifiable before it.
3. THE INJECTED REGRESSION (mandatory): a lane fixture holding an unexplained ignored file, shown still preserved with the path named in the reason.
4. A lane fixture holding both an allowlisted shape and an unexplained file, shown preserved: the allowlist must not excuse a lane by majority.
5. The reason sentence still capped at 10 paths with the exact count stated and the full list present in the record, so the fix does not disturb the honesty rule.
6. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

SPEC `7ckptx` GOVERNS THIS BEHAVIOR (R5.5 retention, R5.6 reason codes) and is deliberately NOT declared in
`- Scope-Paths:`, because this plan's reading is that narrowing what counts as UNEXPLAINED is faithful to
R5.5's fail-toward-preservation rule rather than a change to it: a lane holding only interpreter bytecode is
not holding unclassifiable content in the sense R5.5 means. THAT READING IS THE EXECUTOR'S TO TEST, not to
assume. If R5.5's text asserts that ANY unaccounted ignored file preserves the lane, then this plan changes
the contract and the spec must be amended in the same change: declare
`.aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md` in `Scope-Paths` first, per
the spec-amendment rule, and record the reason here. Note plan `4fodkt` (lanectn-07) owns demonstrating
`7ckptx`'s acceptance criteria and its `A15`/`A15b` cover lane retention, so a criterion may need
re-deriving after this lands; say so in the execution note rather than editing that plan.

## Open questions

### OQ-01: Should the discardable-ignored allowlist be shape-based, or should a lane declare its own expected artifacts?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking; E-03 implements the SHAPE-BASED form, which is smaller and needs no new driver bookkeeping. FOR SHAPE-BASED: bytecode and the run's own scratch are recognizable without any declaration, the allowlist is enumerated in one place with reasons, and it composes with the existing receipt-accounted `discardable` mechanism. FOR DECLARED: a lane that declared everything it expected to write would need no allowlist at all and could not be surprised by a new artifact shape, but it puts the burden on every writer and a missed declaration becomes a preserved lane, which is the failure mode we already have. Recorded because the second form is the more principled design and the maintainer may prefer it despite the cost.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted per-shape inventory across the lanes present at execution HEAD (bytecode, run scratch, lane inputs, everything else) with counts, AND the complete "everything else" list or an explicit statement that it is empty. A summary without that list does NOT satisfy this item: it is the set that decides whether the allowlist is safe.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted proof that an inventory whose only unknown content is bytecode yields `classified=False` and a teardown decision of preserved, at execution HEAD. PLUS pasted confirmation that the reason sentence truncates at `RETENTION_REASON_PATH_LIMIT` while the full path list is present in the record, so the message cap is shown already correct rather than assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the enumerated allowlist quoted with its per-entry reasons, AND pasted before/after classification for a bytecode-only lane (not classifiable -> classifiable). PLUS an explicit statement that `unknown_ignored` still counts in general, with the code quoted to show the narrowing is by enumerated shape rather than by category.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: BOTH directions pasted from real test runs. (a) A lane holding an unexplained ignored file: still preserved, with the path NAMED in the reason. (b) A lane holding only allowlisted shapes: torn down. (c) A lane holding both: still preserved, proving the allowlist does not excuse a lane by majority. Evidence for (b) alone does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the written count of lane worktrees at execution HEAD partitioned into would-become-classifiable and would-still-be-preserved, with the measurement pasted rather than quoted from this plan's F2. PLUS an explicit statement that no lane was torn down and no lane branch deleted by this plan, verifiable by the unchanged `git worktree list` count.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (5 E-items in 2 task groups, under the 18-leaf / 5-group thresholds).

EXECUTION CONTRACT. `OQ-01` is non-blocking and the maintainer's; execute the SHAPE-BASED form and do not
invent a declaration mechanism. SCOPE FENCE: this plan declares `agent_workflows/lane_containment.py` and
`tests/test_lane_retention.py`; an out-of-scope edit must be made only if genuinely required and then
JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path. READ THE SPEC BEFORE ASSUMING NO
AMENDMENT: the spec-sync section above states this plan's reading of `7ckptx` R5.5 and requires the
executor to TEST it; if R5.5 says any unaccounted ignored file preserves the lane, declare the spec file
and amend it rather than changing behavior around it. THE ONE THING THIS PLAN MUST NOT DO: make
`unknown_ignored` stop counting toward `classified` in general. That would tear down a lane holding
unexplained content, which is the loss spec R5.5 exists to prevent and which this session has already seen
matter (three lanes held correct unmerged work). V-04's injected regression is mandatory, not optional.
THE HARD-MUST HONESTY RULE: paste the ACTUAL command and test output for every `V-*`; never claim a run not
performed. Commit path-scoped (`git commit -m msg -- <paths>`); never `git add -A`; never push. Before
every commit run `git diff --cached --name-only` and unstage anything not yours. After the gate, move this
plan to `.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
