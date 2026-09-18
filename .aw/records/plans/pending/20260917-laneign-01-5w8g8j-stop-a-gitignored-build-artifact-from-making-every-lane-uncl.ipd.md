# IPD: Stop a gitignored build artifact from making every lane unclassifiable so lanes are never torn down

- Date: 2026-09-17
- Kind: child
- Concern: A lane that finished cleanly is preserved forever because it contains `__pycache__/*.pyc` and the run's own scratch files. `LaneInventory.classified` is `readable and not self.unknown and not self.uncollected_submission`, and `unknown` includes `unknown_ignored`, so ONE unaccounted gitignored file makes the lane unclassifiable and teardown refuses. Observed 2026-09-17 in run `run-20260917T023628Z-4108757`: lane `aw/lane/3dki3o` was PRESERVED naming "4176 unknown IGNORED file(s)", and the first eight listed were the run's OWN scratch (`commit-msg-plan.txt`, `commit-msg-tests.txt`, `e01-measurements.txt`, `final-suite.txt`) followed by `__pycache__/*.pyc`. Running Python in a lane is enough to guarantee this, so it is not an edge case: measured at authoring, this checkout holds 38 undisposed lane worktrees.
- Scope: Make the retention classifier account for gitignored paths that are provably not work product (Python bytecode caches and the run's own scratch under its submission directory), so a genuinely clean lane is torn down while a lane holding UNEXPLAINED content is still preserved. Does NOT change the dirty-tracked or unknown-untracked rules, does NOT touch the preserve-on-unreadable rule, and does NOT weaken the refusal for content the driver cannot account for.
- Scope-Paths: agent_workflows/lane_containment.py, tests/test_lane_retention.py, .aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md
- Item-Dependencies: none
- Status: to-review
- Readiness: no-go
- Set: laneign
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 5w8g8j

## Workflow history

- 2026-09-17 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-011; readiness `no-go` on TWO blocking findings. Reviewed at HEAD `5a7d81d1`; `aw ipd lint --phase author` conforming before revision. THE DIAGNOSIS IS EXACTLY RIGHT AND I RE-PROVED IT: `classified` is `readable and not self.unknown and not self.uncollected_submission` (`:2891`) and `unknown` unions `unknown_ignored` (`:2884-2886`), so a bytecode-only inventory yields `classified=False` with `reason_codes=('unknown-ignored-file',)`, measured directly. Every convention claim verifies verbatim, including the `RETENTION_REASON_PATH_LIMIT` honesty comment, the `--ignored=traditional` rationale, and the receipt-accounted `discardable` union at `:3409-3428`. BUT I RAN THE REAL INVENTORY OVER A REAL LANE, WHICH E-01 DEFERRED TO EXECUTION, AND THE POPULATION IS NOT WHAT THE PLAN ASSUMES: 4170 unknown-ignored paths here, of which bytecode is 505 (12 percent) and 3655 are `.opencode/node_modules/**`, a tool-installed dependency tree the plan never mentions, plus 7 `.pytest_cache/` files. Simulating the plan's own two-class allowlist leaves 3665 paths and `classified` still False, so THE PLAN AS SCOPED DOES NOT FIX THE DEFECT IT REPORTS. Worse, its own motivating example is misattributed: `commit-msg-plan.txt`, `e01-measurements.txt` and `final-suite.txt` are NOT gitignored (`git check-ignore` finds no rule), so they are `unknown_untracked`, a category this plan explicitly declares out of scope, and none of the four is under `LANE_SUBMISSION_SUBDIR` (`.aw/state/lane-submissions`), so the proposed scratch allowlist would catch none of them. AND THE SPEC BLOCKS THE APPROACH: `7ckptx` (approved) R5.5 says the enumeration "MUST include ignored files; 'ignored means disposable' is the specific reasoning that previously destroyed lane content silently", with live acceptance criterion A15 demonstrated PASSING by executed plan `4fodkt` and pinned by `tests/test_lane_retention.py` (42 passed). So this is a spec AMENDMENT, not an interpretation; the spec file is now declared in `Scope-Paths`. Also: `uncollected_submission` independently forces `classified=False` and no allowlist touches it; F2's 38-worktree figure measures 13 here and E-01/E-05 need `.aw/records/runs/`, which is gitignored and ABSENT in a lane. E-01..E-05 revised, E-06..E-08 added, `Highest E` 05 -> 08. OQ-02 and OQ-03 raised `Blocking: yes` carrying PR-001 and PR-002.
- 2026-09-17 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored after the maintainer asked what the "4,176-file lane-retention noise" from their overnight run actually was. INVESTIGATING IT CHANGED THE FINDING, which is why this plan exists rather than a one-line note: I had described it in chat as cosmetic message noise. It is not. `RETENTION_REASON_PATH_LIMIT` (`lane_containment.py:2850`) already caps the SENTENCE at 10 paths and its comment records the same 4134-file `__pycache__` measurement, so the message length is a solved, deliberate trade-off ("The EXACT COUNT is always stated, the full lists always survive in `as_dict()`... Truncating the recorded evidence instead would be the dishonest choice"). What is NOT solved is the CONSEQUENCE: `classified` (`:2889`) is false whenever `unknown_ignored` is non-empty, so the same bytecode files that the comment treats as a message-length problem also block teardown unconditionally. Measured at authoring: 38 lane worktrees are still allocated in this checkout, which is the accumulated cost.

## Goal

Let a clean lane be reclaimed. A lane whose only unaccounted content is bytecode the interpreter wrote
and scratch the run itself wrote is not holding work, and treating it as if it were means no lane is ever
torn down and the checkout grows a worktree per item forever.

The preservation rule itself is right and stays: a lane holding content the driver cannot explain must be
kept. This narrows what counts as unexplained, it does not relax what happens when something is.

MEASURED AT REVIEW, AND THIS CHANGES WHAT THE PLAN MUST DO. E-01 deferred the population measurement to
execution; I ran it. `inventory_lane` over a real lane at review HEAD:

```text
unknown_ignored: 4170     classified: False    reason_codes: ('unknown-ignored-file', 'uncollected-submission')
  opencode node_modules      3655      <- 88 percent; a tool-installed dependency tree, unmentioned by this plan
  bytecode                    505      <- 12 percent; the only class the plan's allowlist names
  RESIDUE (.pytest_cache/)      7
  other .opencode               3
```

And simulating this plan's own two-class allowlist (bytecode + the submission subdir):

```text
unknown_ignored before: 4170
after the plan's TWO-CLASS allowlist: 3665
classified under the plan's fix: False
```

SO THE FIX AS SCOPED DOES NOT FIX THE REPORTED DEFECT. Three consequences the executor must carry.

1. THE POPULATION IS DOMINATED BY A THIRD CLASS. `.opencode/node_modules/**` is an agent tool's installed
   dependency tree. Whether it is discardable is a REAL judgement (it is regenerable from a lockfile, but it
   is not driver-written and not interpreter-written), and it is OQ-02, not something to assume.
2. THE PLAN'S OWN EXAMPLE IS MISATTRIBUTED. `commit-msg-plan.txt`, `commit-msg-tests.txt`,
   `e01-measurements.txt` and `final-suite.txt` are NOT gitignored (verified with `git check-ignore`: no
   rule matches), so they are `unknown_untracked`, which this plan's Scope explicitly excludes; and none is
   under `LANE_SUBMISSION_SUBDIR` (`.aw/state/lane-submissions`), so the proposed scratch allowlist catches
   none of them. Either the run that produced them had a different ignore configuration, or the Concern's
   attribution of those names to the `unknown IGNORED` sentence is wrong. The `unknown IGNORED` sentence
   (`:2938-2943`) can only list ignored paths, so both cannot be true.
3. `uncollected_submission` IS A SECOND, INDEPENDENT BLOCKER. `classified` also requires
   `not self.uncollected_submission`, and no ignored-path allowlist touches it. Measured in this lane:
   `uncollected_submission=True`. A lane whose collection receipt is missing or incomplete stays preserved
   however clean its file set is, so a fix aimed only at ignored paths cannot be sufficient by itself.

WHAT IS ALREADY SOLVED AND MUST NOT BE REBUILT. `driver_written_lane_paths` already accounts for every
materialized lane INPUT from the sealed manifest (measured here: 8 paths, all under `.aw/state/lane-inputs/`,
all already discardable), and `submission_retention.collected_paths` already makes a COLLECTED submission
discardable from the receipt. So two of E-01's four shape categories are already handled, and the
`discardable` mechanism the plan wants to extend has TWO existing precedents with per-entry reasoning
(`generated_manifest_paths` and the history sidecar, `:3209-3255`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the real population before deciding what is discardable

- [ ] E-01 INVENTORY THE ACTUAL UNACCOUNTED-IGNORED POPULATION across the lanes present at execution HEAD, and refuse to proceed to E-03 on this plan's figures. For each lane worktree, run the same inventory the classifier uses and group its `unknown_ignored` paths by shape: Python bytecode (`__pycache__/`, `*.pyc`), AGENT-TOOL DEPENDENCY TREES (`.opencode/node_modules/**` and any sibling), TEST-RUNNER CACHES (`.pytest_cache/`), the run's own submission scratch (under `LANE_SUBMISSION_SUBDIR`), lane inputs (under `LANE_INPUT_SUBDIR`), and EVERYTHING ELSE. The last group is the one that decides this plan's safety: if it is non-empty, those paths are real unexplained content and the allowlist must not swallow them. TWO CATEGORIES ARE ALREADY SOLVED and must be reported as such rather than re-derived: lane INPUTS are already accounted by `driver_written_lane_paths` from the sealed manifest, and a COLLECTED submission is already accounted by `submission_retention.collected_paths`, so neither can legitimately appear in the residue. MEASURED AT REVIEW so the executor has a target to reproduce or refute: 4170 unknown-ignored paths in one lane, 505 bytecode, 3655 `.opencode/node_modules`, 7 `.pytest_cache`, 3 other `.opencode`.
  - Depends on: none
  - Expected outcome: a pasted per-shape count across all lanes plus the complete "everything else" list (or an explicit statement that it is empty), measured at execution HEAD, compared against the review figures above. State the RATIO each class contributes: a class the allowlist omits is a class that keeps the lane preserved.
  - Execution state: pending

- [ ] E-06 CLASSIFY THE AGENT-TOOL DEPENDENCY TREE, which is 88 percent of the population and is the reason the authored plan would not have worked. `.opencode/node_modules/**` is neither interpreter-written nor driver-written: an agent tool installed it. Decide, and RECORD THE REASON at the decision site, whether it is discardable. THE ARGUMENT FOR: it is regenerable from a lockfile, gitignored, never committed, and losing it costs an `npm install` rather than work. THE ARGUMENT AGAINST: it is not written by anything this repository controls, so the "provably not work product" test that justifies the bytecode entry does not obviously transfer, and an allowlist keyed on a third party's directory name is a standing invitation for the next tool's tree to be missed the same way. DO NOT GUESS: if OQ-02 is unanswered, implement NOTHING for this class and report that the defect therefore remains for any lane an OpenCode agent ran in, rather than quietly widening the allowlist to make a number look better.
  - Depends on: E-01
  - Expected outcome: the classification decision with its reason recorded in code, or an explicit statement that the class is left unhandled pending OQ-02 together with the measured consequence (which lanes remain preserved).
  - Execution state: pending

- [ ] E-07 ADDRESS OR SCOPE OUT `uncollected_submission`, the SECOND independent blocker no allowlist touches. `classified` requires `not self.uncollected_submission`, so a lane with a missing or incomplete collection receipt stays preserved however clean its files are (measured `True` in a real lane at review). Determine whether the lanes this plan aims to reclaim are blocked by this too; if they are, say plainly that the ignored-path fix alone does not reclaim them, and either scope this in with a stated design or defer it with a reason. DO NOT relax it silently: R2.5 makes receipt ABSENCE mean NOT COLLECTED precisely so a driver that crashed before collecting cannot lose the lane's only copy.
  - Depends on: E-01
  - Expected outcome: a measured statement of how many of the target lanes are blocked by `uncollected_submission` in addition to (or instead of) unknown-ignored paths, and an explicit in-scope or deferred decision with its reason.
  - Execution state: pending

- [ ] E-02 CONFIRM THE CONSEQUENCE IS TEARDOWN REFUSAL, not merely a long message, since that is the claim this plan rests on and I want it re-proven rather than inherited. Show that `classified` returns False for an inventory whose ONLY unknown content is bytecode, and that the teardown decision therefore preserves the lane. Also confirm the message cap is already working as designed (the sentence truncates at 10, the full list survives in the record), so this plan does not re-solve a solved problem. ALREADY CONFIRMED AT REVIEW, pasted here so this item verifies rather than discovers: `LaneInventory(readable=True, unknown_ignored=("__pycache__/m.cpython-311.pyc",)).classified` is `False` with `reason_codes=('unknown-ignored-file',)`, while the same inventory with no unknown content is `True`. ALSO RECONCILE THE CONCERN'S OWN EXAMPLE, which does not survive scrutiny: `commit-msg-plan.txt`, `commit-msg-tests.txt`, `e01-measurements.txt` and `final-suite.txt` are NOT gitignored at review HEAD, so they cannot appear in an `unknown IGNORED` sentence, and none is under `LANE_SUBMISSION_SUBDIR`. Either the observed run's lane had a different ignore configuration, or those names came from the `unknown UNTRACKED` clause. Say which, because it decides whether the run-scratch class exists at all in the ignored population.
  - Depends on: none
  - Expected outcome: pasted evidence that a bytecode-only inventory yields `classified=False` and a preserved lane, plus confirmation that the reason sentence is capped and the recorded evidence is complete, PLUS a stated reconciliation of the four scratch filenames against their actual porcelain status.
  - Execution state: pending

### Task group 2: narrow what counts as unexplained, without weakening the refusal

- [ ] E-03 ADD A NARROW, ENUMERATED DISCARDABLE-IGNORED CLASSIFICATION for paths that are provably not work product, keyed on shape rather than on a broad "ignored means fine" rule. The candidate classes are whatever E-01 measured and E-06 cleared, NOT the two the authored plan guessed: bytecode is only 12 percent of the real population. ENUMERATE each as a named constant with the reason at the decision site, EXTENDING THE EXISTING `discardable` MECHANISM rather than inventing a parallel one, and follow the two precedents already in this function (`generated_manifest_paths` at `:3209` and the history sidecar at `:3236`), each of which states WHY widening discardability is safe for its specific entry. That "why widening is safe HERE specifically" paragraph is the house form and is required per entry. DO NOT make `unknown_ignored` stop counting in general: an ignored file the driver cannot explain is exactly what spec R5.5's fail-toward-preservation rule is for, and a blanket exemption would delete the guard rather than sharpen it. DO NOT KEY ON A DIRECTORY THE WAY `driver_written_lane_paths` REFUSES TO: its docstring records that returning the revision DIRECTORY "would make ANY file a worker dropped inside it discardable, so an unexplained file would be destroyed because of WHERE it sits rather than because a record accounts for it - which is the hardcoded-path-list behavior spec R5.5 forbids". A bytecode entry keyed on `__pycache__/` plus a `*.pyc` suffix is defensible because the shape IS the proof; a `.opencode/node_modules/` prefix entry is the case that docstring warns about and needs E-06's explicit decision.
  - Depends on: E-01, E-02, E-06, E-08
  - Expected outcome: a tested classification in which a lane holding only cleared shapes is classifiable, and a lane holding ANY other ignored file is still not; the allowlist enumerated with a per-entry "why discarding this is safe" reason in the house form. State the measured post-fix residue: if a real lane is still not classifiable, say so plainly rather than declaring the defect fixed.
  - Execution state: pending

- [ ] E-04 PROVE THE REFUSAL STILL FIRES, which is the load-bearing half and must be an INJECTED-REGRESSION test rather than an assertion about today's tree. Plant an unexplained ignored file in a lane fixture (something matching no allowlist entry) and show the lane is still preserved with the path NAMED in the reason. Then plant one file of each allowlisted shape and show the lane is torn down. A test that only checks the second half would pass while the guard was gone. REUSE THE EXISTING FIXTURES: `tests/test_lane_retention.py` already builds exactly these cases (`build/output.log` as the unexplained ignored file, `.aw/state/unexplained/deep.txt` as the under-an-ignored-prefix case at `:327`, and a manifest-emptied case at `:358-368`), all 42 currently green, so the injected regression is an addition to a working harness rather than a new one. THE `.aw/state/unexplained/deep.txt` TEST IS THE ONE MOST LIKELY TO BREAK if the allowlist is keyed loosely, and it is a deliberate guard: keep it passing.
  - Depends on: E-03
  - Expected outcome: pasted evidence of both directions: an unexplained ignored file preserves the lane and is named; cleared shapes alone allow teardown. PLUS `tests/test_lane_retention.py` green as a whole (review baseline `42 passed`), with the pre-existing under-an-ignored-prefix and manifest-emptied guards shown still passing.
  - Execution state: pending

- [ ] E-05 REPORT THE BACKLOG OF UNDISPOSED LANES this defect has already accumulated, as information for the maintainer rather than an action. State how many lane worktrees exist at execution HEAD, how many would become classifiable under E-03's rule, and how many hold genuinely unexplained content and would still be preserved. PARTITION BY REASON CODE, not just by count, since review found `uncollected-submission` firing alongside `unknown-ignored-file` in the same lane (E-07); a lane blocked by both is not reclaimed by this plan. Do NOT tear any of them down: they may hold work, several correspond to plans whose disposition a human has not reviewed, and reclaiming them is a separate decision with its own risk. NOTE THE MEASUREMENT ENVIRONMENT, because this item cannot run as written from inside a lane: `git worktree list` in a review lane reports 13 `aw/lane` entries here, not the 38 F2 claims from the main checkout, and `.aw/records/runs/` is GITIGNORED and ABSENT in a lane, so `inventory_lane` cannot read a collection receipt and reports `uncollected_submission=True` for every lane regardless of truth. State which tree you measured from and acknowledge the receipt limitation rather than reporting a false partition.
  - Depends on: E-03, E-07
  - Expected outcome: a written count of existing lanes partitioned by REASON CODE into would-become-classifiable and would-still-be-preserved, the measuring tree named, the receipt-availability limitation stated, and an explicit statement that none was torn down by this plan.
  - Execution state: pending

- [ ] E-08 AMEND SPEC `7ckptx` R5.5 IN THE SAME CHANGE, because this plan changes the contract rather than interpreting it. THE SPEC TEXT IS EXPLICIT (`:451-454`): "Teardown MUST be refused while a lane holds content the driver cannot classify: a dirty tracked file, an unknown untracked OR IGNORED file, or an unimported submission. The enumeration MUST include ignored files; 'ignored means disposable' is the specific reasoning that previously destroyed lane content silently." Adding a class of ignored file that no longer refuses is a narrowing of that MUST, so the spec must say so. THE AMENDMENT MUST STATE THE PRINCIPLE, NOT THE PATTERN LIST: what makes a class exempt (provably regenerable, written by the toolchain rather than by the work, and enumerated with a stated reason) so the next class is judged rather than pattern-matched. Also RE-DERIVE ACCEPTANCE CRITERION A15 (`:613-614`, "the same for an unknown IGNORED file"), which executed plan `4fodkt` demonstrated PASSING: state whether it still holds as written or needs the exempt-class carve-out, and record the answer in the spec rather than editing `4fodkt`.
  - Depends on: E-06
  - Expected outcome: the spec diff pasted showing R5.5 amended with the exemption PRINCIPLE and A15's status re-derived, plus a statement of why the narrowing is faithful to the fail-toward-preservation posture. If E-06 concludes no class is safely exemptible, this item records that the spec needs NO amendment and the plan's approach is withdrawn.
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
| F2 | HIGH | this checkout | **THE COST IS MEASURED AND ONGOING: 38 undisposed lane worktrees.** Every finished item leaves its lane allocated, so the checkout accumulates one worktree per executed plan indefinitely. **CAVEAT ADDED AT REVIEW: the figure is tree-dependent and cannot be reproduced from a lane.** `git worktree list` in a review lane at HEAD `5a7d81d1` reports 13 `aw/lane` entries, not 38. The trend claim stands; the number must be re-measured from the main checkout and the measuring tree named (E-05). | `git worktree list` at authoring: 38 entries matching `aw/lane`; 13 measured in a lane at review |
| F3 | MEDIUM | my own earlier report | **I MISDIAGNOSED THIS AS COSMETIC AND THE CODE PROVES OTHERWISE.** I told the maintainer it was message noise. `RETENTION_REASON_PATH_LIMIT`'s comment shows the message length was already measured (4134 files) and deliberately capped, so the visible output is the SOLVED part; the unsolved part is that the same files block teardown. Recorded so the plan is not read as re-solving the cap. | `:2844-2850` versus `:2889` |
| F4 | MEDIUM | the fix direction | **THE OBVIOUS FIX WOULD DELETE THE GUARD.** Making `unknown_ignored` stop counting toward `classified` would tear down every lane including one holding an unexplained ignored file, which is precisely what spec R5.5 exists to prevent. The fix must be a narrow enumerated allowlist, and E-04's injected regression is what proves it stayed narrow. | `LaneInventory`'s fail-toward-preservation docstring |
| F5 | LOW | `--ignored=traditional` rationale | A FIX MUST NOT REGRESS TO DIRECTORY-LEVEL JUDGEMENT. The inventory deliberately reports ignored files per-file so an unexplained file under an ignored directory is still seen. An allowlist keyed on a directory PREFIX must therefore match precisely (bytecode caches, the submission subdir) and never on `.aw/state/` wholesale, which would hide anything written there. | `:2805-2813` |
| F6 | LOW | E-05's scope | THE EXISTING LANES ARE NOT THIS PLAN'S TO RECLAIM. Some may hold work whose disposition a human has not reviewed, and this session already found one lane (`i3d6ml`) holding two commits of correct unmerged work. Reporting them is useful; tearing them down would risk exactly the loss the retention rule prevents. | the session's own recovery of the `i3d6ml`, `tx6q0h` and `sy7uwh` lanes |
| F7 | BLOCKER | the allowlist's own scope | **THE FIX AS SCOPED DOES NOT FIX THE REPORTED DEFECT, MEASURED END TO END.** The real unknown-ignored population in a lane is 4170 paths: 505 bytecode (12 percent), 3655 `.opencode/node_modules/**`, 7 `.pytest_cache/`, 3 other `.opencode`. Simulating the plan's own two-class allowlist leaves 3665 paths and `classified` still `False`, so the lane is still preserved. The dominant class is an agent tool's installed dependency tree the plan never mentions. | `inventory_lane` run against a real lane at review HEAD `5a7d81d1`; the simulated allowlist result pasted in the Goal |
| F8 | BLOCKER | spec `7ckptx` R5.5 | **THIS IS A SPEC AMENDMENT, NOT AN INTERPRETATION, AND THE SPEC SAYS SO IN THE PLAN'S OWN WORDS.** R5.5 (`:451-454`) states the enumeration "MUST include ignored files; 'ignored means disposable' is the specific reasoning that previously destroyed lane content silently". Live acceptance criterion A15 (`:613-614`) pins "the same for an unknown IGNORED file" and executed plan `4fodkt` demonstrated it PASSING. The spec-sync section's hope that narrowing is "faithful to R5.5 rather than a change to it" does not survive that text. | `7ckptx` `Status: approved`, `:451-454`, `:613-614`; `4fodkt` V-06 evidence recording A15 passed with `retention_reasons=['unknown-ignored-file']` |
| F9 | HIGH | the Concern's own example | **THE FOUR CITED SCRATCH FILES ARE NOT GITIGNORED, SO THEY CANNOT BE IN THE `unknown IGNORED` LIST, AND NONE IS UNDER THE SUBMISSION SUBDIR.** `git check-ignore` matches no rule for `commit-msg-plan.txt`, `e01-measurements.txt` or `final-suite.txt`, so they classify as `unknown_untracked`, which this plan's Scope explicitly excludes; and `_is_within(f, [LANE_SUBMISSION_SUBDIR])` is False for all four, so the proposed scratch allowlist catches none of them. The plan's motivating anecdote and its remedy do not meet. | `git check-ignore -v` on each; `_is_within` evaluated against `LANE_SUBMISSION_SUBDIR = ".aw/state/lane-submissions"`; the `unknown IGNORED` sentence at `:2938-2943` can list only ignored paths |
| F10 | HIGH | `LaneInventory.classified` | **`uncollected_submission` IS A SECOND, INDEPENDENT BLOCKER THAT NO ALLOWLIST TOUCHES.** `classified` requires `not self.uncollected_submission` as well, measured `True` in a real lane, so a lane with a missing or incomplete collection receipt stays preserved however clean its file set is. A fix aimed only at ignored paths cannot reclaim such a lane. | `:2891`; `inventory_lane` reporting `uncollected_submission=True, reason_codes=('unknown-ignored-file', 'uncollected-submission')` |
| F11 | MEDIUM | E-01 and E-05's feasibility | **TWO ITEMS CANNOT RUN AS WRITTEN FROM INSIDE A LANE.** `.aw/records/runs/` is gitignored (`.aw/.gitignore:records/runs/`) and ABSENT in a lane, so no collection receipt is readable and `submission_retention` returns `uncollected=True` for every lane by construction; and `git worktree list` sees a different set than the main checkout. Both items must name the tree they measured from and acknowledge the receipt limitation, or they will report a false partition. | `ls .aw/records/runs` -> absent; `submission_retention` detail "no run directory or item was supplied"; 13 vs 38 worktrees |
| F12 | MEDIUM | E-03's design | THE EXTENSION POINT AND ITS HOUSE FORM ALREADY EXIST TWICE, so E-03 should follow them rather than invent a shape. `generated_manifest_paths` (`:3209`) and the history sidecar (`:3236`) are each enumerated with a "why widening discardability is safe HERE specifically" paragraph, and each records the MEASURED "refusing always" failure it fixed. Two of E-01's four shape categories are also already solved: lane inputs by `driver_written_lane_paths` (8 paths measured, all discardable) and collected submissions by `submission_retention.collected_paths`. | `:3209-3255`; `driver_written_lane_paths` run against this lane |

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

- Over-scope: none. One classification rule, its tests, and the spec amendment that rule requires.
- Under-scope: closed at review on four counts, and it was substantial. The allowlist covered 12 percent of
  the real population and would have left the lane preserved (F7, now E-01/E-06); the spec amendment was
  hoped away (F8, now E-08 and the declared spec path); `uncollected_submission` was an unnoticed second
  blocker (F10, now E-07); and the Concern's own example does not classify the way the plan assumes (F9, now
  reconciled in E-02).
- Under-scope, remaining and deliberate: reclaiming existing lanes is deferred below with a reason. NOTE THE
  HONEST LIMIT this creates: with OQ-02 unanswered, this plan may land a correct narrow bytecode exemption
  and STILL not reclaim a single real lane. That is an acceptable increment (it removes one true cause and
  the guard stays intact) but it must not be reported as fixing the defect the Concern describes.

## Required tests / validation

1. `python3 -m pytest` showing NO NEW failures against a baseline taken THE SAME WAY, with both summary lines
   pasted and the invocation form stated. NOTE, measured at review: in a managed worker lane a bare run
   reports 31 failures that are PRESENT BEFORE ANY CHANGE, because `AW_EXECUTION_ROLE=worker` makes lifecycle
   verbs refuse by design; with `env -u AW_EXECUTION_ROLE` the same tree is clean. Do not "fix" those and do
   not gate on an absolute count.
2. A lane fixture whose only unaccounted ignored content is bytecode: shown classifiable and torn down AFTER the change, and shown NOT classifiable before it.
3. THE INJECTED REGRESSION (mandatory): a lane fixture holding an unexplained ignored file, shown still preserved with the path named in the reason.
4. A lane fixture holding both an allowlisted shape and an unexplained file, shown preserved: the allowlist must not excuse a lane by majority.
5. The reason sentence still capped at 10 paths with the exact count stated and the full list present in the record, so the fix does not disturb the honesty rule.
6. `tests/test_lane_retention.py` green as a whole (review baseline `42 passed`), with the two pre-existing
   guards most at risk from a loose allowlist shown still passing by name: the under-an-ignored-prefix case
   (`.aw/state/unexplained/deep.txt`, `:327`) and the manifest-emptied case (`:358-368`).
7. THE END-TO-END POPULATION CHECK, which is the one the authored plan lacked and which is why it would have
   shipped without fixing anything: run the real `inventory_lane` against a REAL lane before and after, and
   paste the unknown-ignored count and `classified` for both. If `classified` is still `False` after the
   change, say so plainly as the result rather than reporting the unit tests as success.
8. THE SPEC AMENDMENT diff (E-08) pasted, with A15's re-derived status stated.
9. `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

SPEC `7ckptx` GOVERNS THIS BEHAVIOR (R5.5 retention, R5.6 reason codes). **THE AUTHORED SECTION HOPED NO
AMENDMENT WAS NEEDED AND ASKED THE EXECUTOR TO TEST THAT; I TESTED IT AT REVIEW AND THE ANSWER IS THAT AN
AMENDMENT IS REQUIRED.** The spec file is now DECLARED in `- Scope-Paths:` and E-08 owns the edit.

R5.5's text is not silent on this and does not leave room for the "faithful narrowing" reading (`:451-454`):

> Teardown MUST be refused while a lane holds content the driver cannot classify: a dirty tracked file, an
> unknown untracked OR IGNORED file, or an unimported submission. The enumeration MUST include ignored
> files; "ignored means disposable" is the specific reasoning that previously destroyed lane content
> silently.

That last clause is the plan's own approach named as the historical defect. Adding a class of ignored file
that no longer refuses is therefore a NARROWING OF A MUST, and the honest route is to amend the requirement
and say why, not to argue the narrowing was always inside it. `7ckptx` is `Status: approved`, so this is the
highest-leverage change the plan makes and it must be declared and announced, per the spec-amendment rule.

WHAT THE AMENDMENT MUST SAY, per E-08: the PRINCIPLE that makes a class exempt (provably regenerable,
written by the toolchain rather than by the work, enumerated with a stated reason at the decision site) so
the next class is judged rather than pattern-matched. A pattern list alone would recreate the failure R5.5
warns about one tool at a time.

ACCEPTANCE CRITERION A15 (`:613-614`) says "the same for an unknown IGNORED file" and executed plan `4fodkt`
demonstrated it PASSING with `retention_reasons=['unknown-ignored-file']`. E-08 must re-derive whether it
still holds as written or needs the carve-out, and record that IN THE SPEC. Do NOT edit `4fodkt`: it is in
`.aw/records/plans/executed/` and a post-execution gap is closed by a new corrective plan, never in place.
`tests/test_lane_retention.py` (42 passing at review) is the pinned surface and is already declared.

## Open questions

### OQ-01: Should the discardable-ignored allowlist be shape-based, or should a lane declare its own expected artifacts?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking; E-03 implements the SHAPE-BASED form, which is smaller and needs no new driver bookkeeping. FOR SHAPE-BASED: bytecode and the run's own scratch are recognizable without any declaration, the allowlist is enumerated in one place with reasons, and it composes with the existing receipt-accounted `discardable` mechanism. FOR DECLARED: a lane that declared everything it expected to write would need no allowlist at all and could not be surprised by a new artifact shape, but it puts the burden on every writer and a missed declaration becomes a preserved lane, which is the failure mode we already have. Recorded because the second form is the more principled design and the maintainer may prefer it despite the cost.
- ADDED AT REVIEW: the measurement strengthens the DECLARED case more than the plan expected. 88 percent of the real population is `.opencode/node_modules/**`, a tree no declaration by this repository's driver would ever cover, so neither form handles it without an explicit judgement (OQ-02). And note the repository ALREADY has a declared-style mechanism that works well: `driver_written_lane_paths` reads the sealed manifest and its docstring explains why manifest-sourced beats path-sourced ("A hardcoded list would agree today and be wrong silently after the next layout change"). That is evidence for the declared form, not against it.

### OQ-02: Is an agent tool's installed dependency tree (`.opencode/node_modules/**`) discardable?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-001
- Resolution or deferral rationale: RAISED AT REVIEW and BLOCKING, because it is 88 percent of the population and without an answer this plan does not achieve its own goal. MEASURED: 3655 of 4170 unknown-ignored paths in a real lane are `.opencode/node_modules/**`; with the plan's authored two-class allowlist applied, 3665 remain and `classified` is still `False`, so no lane an OpenCode agent worked in is reclaimed. FOR DISCARDABLE: it is gitignored, never committed, regenerable from a lockfile, and losing it costs an `npm install` rather than work, which is the same argument the two existing `discardable` entries make. AGAINST: it is written by a THIRD-PARTY TOOL, not by the driver and not by the interpreter, so the "provably not work product" test does not transfer as cleanly; and an entry keyed on one vendor's directory name is exactly the "hardcoded path list" that `driver_written_lane_paths`'s docstring refuses and that R5.5 names as the historical cause of silent content loss. A tool that writes elsewhere next month is missed the same way. WHY IT IS THE MAINTAINER'S CALL: it decides whether the exemption principle is "the toolchain wrote it" (broad, covers future tools, weakens the guard) or "this repository can prove it regenerable" (narrow, needs an entry per tool). E-06 implements NOTHING for this class while the question is open and must report the consequence instead of widening the allowlist to improve a number.

### OQ-03: R5.5 must be amended. Approve the narrowing of an approved spec's MUST?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-002
- Resolution or deferral rationale: RAISED AT REVIEW and BLOCKING. The authored plan hoped this was an interpretation; the spec text refutes that. R5.5 (`:451-454`) requires the refusal enumeration to INCLUDE ignored files and names "ignored means disposable" as "the specific reasoning that previously destroyed lane content silently", and live criterion A15 pins it, demonstrated PASSING by executed plan `4fodkt`. So the plan narrows a MUST in an `approved` spec, which is the highest-leverage change it makes and is not an executor's decision. THE QUESTION IS NARROW: may an enumerated, per-entry-justified class of provably-regenerable toolchain output be exempt from R5.5's refusal, and does A15 keep its current wording or gain the carve-out? FOR: the alternative is measured and bad, a checkout that accumulates one worktree per executed plan forever. AGAINST: the requirement's own history is that this exact reasoning destroyed content, so a maintainer may prefer a different remedy entirely (an `aw` verb that reclaims a lane after an explicit human check, or making the lane's tool cache live outside the worktree) which would need no spec change at all. E-08 is written to amend the spec if approved and to record "no amendment needed, approach withdrawn" if not.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted per-shape inventory across the lanes present at execution HEAD (bytecode, agent-tool dependency trees, test-runner caches, run scratch, lane inputs, everything else) with counts AND per-class ratios, AND the complete "everything else" list or an explicit statement that it is empty. A summary without that list does NOT satisfy this item: it is the set that decides whether the allowlist is safe. Compare explicitly against the review figures (4170 / 505 bytecode / 3655 `.opencode/node_modules` / 7 `.pytest_cache` / 3 other) and state whether they reproduce. Confirm lane inputs and collected submissions appear in the ALREADY-ACCOUNTED set rather than the residue.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted proof that an inventory whose only unknown content is bytecode yields `classified=False` and a teardown decision of preserved, at execution HEAD. PLUS pasted confirmation that the reason sentence truncates at `RETENTION_REASON_PATH_LIMIT` while the full path list is present in the record, so the message cap is shown already correct rather than assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the enumerated allowlist quoted with its per-entry "why discarding this is safe HERE specifically" reason in the house form the two existing entries use, AND pasted before/after classification for a bytecode-only lane (not classifiable -> classifiable). PLUS an explicit statement that `unknown_ignored` still counts in general, with the code quoted to show the narrowing is by enumerated shape rather than by category. PLUS the REAL-LANE result required by Required tests item 7: the unknown-ignored count and `classified` before and after, against an actual lane. If `classified` is still `False`, this item is satisfied by stating that honestly; it is NOT satisfied by presenting the unit fixtures as if the defect were fixed.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: BOTH directions pasted from real test runs. (a) A lane holding an unexplained ignored file: still preserved, with the path NAMED in the reason. (b) A lane holding only cleared shapes: torn down. (c) A lane holding both: still preserved, proving the allowlist does not excuse a lane by majority. Evidence for (b) alone does not satisfy this item. PLUS `tests/test_lane_retention.py` green as a whole (review baseline `42 passed`) with the under-an-ignored-prefix and manifest-emptied guards named and shown passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the count of lane worktrees at execution HEAD partitioned BY REASON CODE into would-become-classifiable and would-still-be-preserved, with the measurement pasted rather than quoted from this plan's F2, and the MEASURING TREE named (a lane sees a different set: 13 vs F2's 38 at review). PLUS an explicit acknowledgement that `.aw/records/runs/` is gitignored and absent in a lane, so if measured from a lane every entry reports `uncollected_submission=True` by construction and the partition is not trustworthy; say which tree gave the reported numbers. PLUS an explicit statement that no lane was torn down and no lane branch deleted by this plan, verifiable by the unchanged `git worktree list` count.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the classification decision for `.opencode/node_modules/**` with its reason quoted from the code, OR an explicit statement that the class was left unhandled pending OQ-02 together with the measured consequence (the post-fix unknown-ignored count and `classified` for a real lane, showing which lanes remain preserved). A decision to include the class made WITHOUT an OQ-02 answer does not satisfy this item and would be exactly the silent widening R5.5 warns about.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the measured count of target lanes whose `reason_codes` include `uncollected-submission`, alongside those blocked only by `unknown-ignored-file`, from a tree where collection receipts are actually READABLE (state which). PLUS the in-scope or deferred decision with its reason, and an explicit statement that R2.5's receipt-absence-means-not-collected rule was not relaxed.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the `7ckptx` diff pasted showing R5.5 amended with the exemption PRINCIPLE (not merely a pattern list) and A15's status re-derived and recorded in the spec, plus a statement of why the narrowing keeps the fail-toward-preservation posture. Confirm no other spec section moved. If E-06 concluded no class is safely exemptible, paste the recorded "no amendment needed, approach withdrawn" statement instead. Confirm `4fodkt` was NOT edited.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required (8 E-items in 2 task groups, under the 18-leaf / 5-group thresholds). The
  three items added at review are each narrow: E-06 is one classification decision, E-07 one measurement plus
  a scope call, E-08 one spec clause.

DO NOT EXECUTE UNTIL OQ-02 AND OQ-03 ARE ANSWERED. OQ-02 decides 88 percent of the population and without it
the plan cannot reach its own goal; OQ-03 asks permission to narrow a MUST in an `approved` spec whose text
names this plan's approach as the historical cause of silent content loss. Both are blocking and both are the
maintainer's.

FOUR FACTS MEASURED AT REVIEW THAT YOU MUST NOT RE-DERIVE FROM THE ORIGINAL TEXT. FIRST, the real
unknown-ignored population in a lane is 4170 paths of which bytecode is 505; the authored two-class allowlist
leaves 3665 and `classified` still `False`, so it does not fix the defect. SECOND, the Concern's four scratch
filenames are NOT gitignored and are NOT under `LANE_SUBMISSION_SUBDIR`, so the run-scratch class as described
may not exist in the ignored population at all. THIRD, `uncollected_submission` independently forces
`classified=False` and no allowlist touches it. FOURTH, `7ckptx` R5.5 requires the enumeration to include
ignored files and names "ignored means disposable" as the reasoning that previously destroyed lane content, so
this is an AMENDMENT; the spec file is declared and E-08 owns it.

EXECUTION CONTRACT. `OQ-01` is non-blocking and the maintainer's; execute the SHAPE-BASED form and do not
invent a declaration mechanism. SCOPE FENCE: this plan declares `agent_workflows/lane_containment.py`,
`tests/test_lane_retention.py` and
`.aw/records/specs/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md`; an out-of-scope edit must be
made only if genuinely required and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and
a declared path left unmodified needs a `--scope-ack`. DO NOT EDIT `4fodkt`: it is in `executed/`, and a
post-execution gap is closed by a new corrective plan, never in place; record A15's re-derivation in the SPEC.
THE ONE THING THIS PLAN MUST NOT DO: make `unknown_ignored` stop counting toward `classified` in general.
That would tear down a lane holding unexplained content, which is the loss spec R5.5 exists to prevent and
which this session has already seen matter (three lanes held correct unmerged work). V-04's injected
regression is mandatory, not optional, and so is the real-lane population check (Required tests item 7): a
green unit suite over hand-built fixtures is exactly how this plan could have shipped while reclaiming
nothing. THE HARD-MUST HONESTY RULE: paste the ACTUAL command and test output for every `V-*`; never claim a
run not performed; and if the post-fix lane is still not classifiable, REPORT THAT as the result rather than
presenting the fixtures as success. RUN THE SUITE stating which form you ran and gate on NO NEW failures
rather than an absolute count (a worker lane shows 31 pre-existing failures by design). Commit path-scoped
(`git commit -m msg -- <paths>`); never `git add -A`; never push. Before every commit run
`git diff --cached --name-only` and unstage anything not yours. After the gate, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`, and do not claim done until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
