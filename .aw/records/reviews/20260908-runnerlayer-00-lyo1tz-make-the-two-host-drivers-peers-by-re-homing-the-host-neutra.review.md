# Review: make the two host drivers peers by re-homing the host-neutral half of the oc-to-agy imports, orchestrator lyo1tz (Set runnerlayer)

- Subject-Id: lyo1tz
- Subject-Type: ipd
- Reviewed-At: 2026-09-09
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `28e69e9d`. `aw ipd lint --phase author` CONFORMING before semantic review and
`--phase review-finalize` CONFORMING after every revision, so nothing in this round is structural.

DISCLOSURE: the same agent/model authored this Set, so this is a SELF-REVIEW. Its value therefore
rests on RE-MEASURING the claims rather than re-reading them. Six things were run rather than
inspected: the oc-to-agy and agy-to-oc import sets were AST-walked and diffed against every
enumeration in the Set; `DriverError`'s identity was checked across all three modules; the symmetry
guard's `_SHARED_NAMES` tuple was counted in-process; `runner_shared`'s imports were AST-checked for
the admission rule; both child plans were read and linted; and both suite baselines were re-measured.
The first produced the BLOCKER.

SCOPE: only this orchestrator was a candidate. The two children (`9kmbr0`, `1f7xno`) were read as
EVIDENCE, not reviewed, and are not in the ledger; each needs its own `/plan-review`. Also read:
`agy_runipd.py`, `oc_runipd.py`, `runner_shared.py`, `ipd_lifecycle.py`,
`tests/test_runner_item_dependencies.py`, `.pre-commit-config.yaml`, executed plan `818uru`, approved
plan `5e4sb6`, and backlog `cnwy8g`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-B01 | BLOCKER | IN-SCOPE | A. Correctness; E. Testing (a stale number used as a pass criterion) | AST walk at HEAD `28e69e9d`; two-way set difference against both plans' enumerations | **THE SET'S CENTRAL MEASUREMENT IS WRONG BY ONE, THE MISSING NAME IS ABSENT FROM EVERY ENUMERATION, AND THE WRONG FIGURE WAS A VALIDATION CRITERION.** Measured: `agy_runipd` imports **48** names from `oc_runipd`, not 47, across the same eight statements. The 48th is `dependency_status_detailed`, and it appears in NO list in this Set: not in this parent's F-9 concern groups, and not in child 01's E-02 group enumeration, which itemizes exactly 47 names. Verified by set difference that nothing else drifted (live-minus-enumerated is exactly `{dependency_status_detailed}`; enumerated-minus-live is EMPTY). THREE CONSEQUENCES, each concrete rather than tidiness: V-02 required pasting "the AST-measured oc-to-agy import count BEFORE (47)", so a correct measurement of 48 FAILS validation and invites an executor to "fix" its own correct number; child 01 classifying "all 47" leaves one name unclassified, after which child 02's residual set-difference check cannot balance in either direction; and the omitted name is precisely the one whose earlier absence from a guard caused a real defect (see PR-B02). The count ALSO moved during this review, 47 to 48 in one day, which is the strongest evidence the Set has for its own freeze guard and is worth stating as such. | C:Low; U:Low; S:Low; F:High; Overall:Medium | FIXED | Added F-10. Concern re-measured to 48 with the missing name named and the "do not use 47 as a criterion" rule stated. Scope now defines the set size as "whatever the AST says at execution time". E-01 requires the classification to cover the measured set and to record the count found; E-02 and CID-1 now compare SETS and require self-measured endpoints rather than a literal baseline; V-01 requires `dependency_status_detailed` to carry a verdict specifically; V-02 forbids asserting a literal BEFORE figure. Child table and completion criteria reworded off the fixed number. |
| PR-B02 | MEDIUM | IN-SCOPE | D. Anti-regression; A. Correctness | counted `_SHARED_NAMES` in-process; `tests/test_runner_item_dependencies.py:1617`, `:1633` | The symmetry guard this Set names as its single most important protection is described wrongly in three places: it asserts object identity for **TWELVE** names, not eleven. The twelfth is `dependency_status_detailed`, added by `03ie04` E-04 precisely because its ABSENCE from that tuple had let the guard pass over agy's real copy of the function. So the one name this Set forgot to enumerate (PR-B01) is also the one whose omission from a guard already caused the exact class of defect this Set exists to prevent, which makes the coincidence worth recording rather than quietly correcting. The cited anchors have also drifted: the class is at `:1617` and the tuple at `:1633`, not `:1179`/`:1182`. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-11. The hard-constraint bullet now states twelve with the `03ie04` history and the corrected anchors, and instructs finding them by NAME. |
| PR-B03 | MEDIUM | UNDER-SCOPE | C. Architecture; G. Plan executability | `ipd_lifecycle.ROLLUP_OMITTED_GATES`, `ROLLUP_SHARED_GATES`; `runner_shared.find_unauthored_child_rows` | The Step 0 convention asserts the orchestrator-retirement contract ("the runner ... deliberately SKIPS the pre-transition E/V checkpoint") from GUIDANCE rather than from the code, which matters because that assertion is the entire justification for this parent holding confirm-only items. VERIFIED and now cited: `ROLLUP_OMITTED_GATES` names exactly ONE omission, `pre-transition-ev-checkpoint`, with the recorded reason that an orchestrator's items are "performed by NOBODY (the runner supersedes its coordination role)", while `ROLLUP_SHARED_GATES` still performs worker-role refusal, actor-and-message, early crash recovery, the exclusive finalize lock and more. Also unverified in the plan: the retirement refusal it invokes (`unauthored-child-rows`) is ONE-DIRECTIONAL (extra children on disk are fine, only a declared row resolving to nothing refuses), and both declared rows DO resolve, so no refusal is expected. Without these facts a reader cannot tell whether this parent's three items are legitimate orchestration or work that will be marked done unperformed. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Step 0 convention rewritten with the measured gate contract and its consequence for this parent; a second convention records the one-directional refusal. The gate gained a "WHAT RETIREMENT ACTUALLY OMITS" paragraph stating both consequences and what a refusal would and would not mean. |
| PR-B04 | MEDIUM | IN-SCOPE | A. Correctness (an unstated starting state) | `.aw/records/backlog/graduated/...cnwy8g...backlog.md` | E-03 and V-03 require confirming backlog `cnwy8g` reaches `done` without saying what it reads TODAY. It is already `graduated` (verified), and it carries NO `Blocks-Release`. Both facts change what the executor must check: the transition is `graduated -> done` rather than a close from `open`, and because the item is ungated the close needs NO HANDOFF/SATISFIED/DE-GATED evidence at all. Left unstated, an executor could hunt for a gate discharge that does not exist, or worse, fabricate an evidence citation to satisfy a ladder that never fires. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Added F-12. E-03 states the current status and the ungated consequence; V-03 records the expected transition and requires confirming no gate-discharge evidence was fabricated. |
| PR-B05 | LOW | IN-SCOPE | E. Testing (a verification step that cannot pass as written) | counted the Set on disk | This parent's V-03 and child 02's V-07 both prescribe "a grep over all four plans in this Set". The Set has THREE plans (`lyo1tz`, `9kmbr0`, `1f7xno`). A conscientious executor could read a correct three-file result as evidence of a missing plan and go looking for it, or treat the criterion as unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-13. E-03 and V-03 now name all three plans explicitly and instruct grepping the Set as it exists rather than to a count. (Child 02's own copy of the error is noted for its review; not edited here, since this review's ledger is this parent only.) |
| PR-B06 | LOW | IN-SCOPE | E. Testing (stale baseline); A. Correctness (self-contradiction) | measured at HEAD `28e69e9d`; the plan's own F-8 versus its child table | Two smaller inaccuracies. The suite baseline is stale in BOTH halves: measured `1 failed, 5919 passed, 3 skipped, 2 xfailed` with the failure being the ENVIRONMENTAL `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, not the `1 failed, 5648 passed` attributed to `tests/test_orchestrator_retirement.py`, which now gives `112 passed`. And the plan CONTRADICTS ITSELF on the module name: F-8 correctly records that the module is `runner_shared.py` and that the item's `runner_common` is stale, then the child table says "keeping `runner_common`-style admission". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-14 and two Step 0 conventions. Baseline replaced with measured values and the executor told to quote neither figure; the child table's `runner_common` corrected. |

CONFIRMED SOUND, AND IT IS THE WHOLE ARCHITECTURE OF THE SET. Every load-bearing claim other than the
count was re-measured and holds. The DIRECTION claim is exact: 0 names flow agy-to-oc, and
`runner_shared` imports NEITHER driver (AST-checked, so a lazy in-function import could not hide),
which means the admission rule this Set must preserve currently holds and can only be broken by a
child adding something. `DriverError` really is one object (`oc is agy is runner_shared` -> `True`), so
the item's sole behavioral consequence is genuinely discharged and this Set's refusal to carry a
`Blocks-Release` gate is correct and faithful rather than an omission. `818uru` is `executed` and its
fence really does say "Do NOT re-home the 40 oc-to-agy imports", so the work is real and unowned, and
the sequencing precondition the backlog item demanded is satisfied. `ruff` and `ruff-format` really are
pre-commit hooks, so the `as <same-name>` hazard is live on every commit this Set will make. The
grouping in F-9 is accurate. `5e4sb6` is `approved` and does own the broader unification, so the
scope boundary is real. And the TWO-CHILD SPLIT is the right call for the reason given: a move reviewed
against a classification made during that move is reviewed against nothing.

THIS PARENT ALSO PASSES THE ORCHESTRATOR TEST, which is worth stating because it is the failure mode
the house rules warn about most. All three of its E-items merely CONFIRM a fact that a child's own
`V-*` already gated; none produces a deliverable, establishes a baseline, or reconciles records. Its
`Scope-Paths` are the two children and it edits no source file. Its child table declares rows that both
resolve, so retirement will not refuse. That combination is exactly what makes an Order-0 plan safe
under a runner that skips its E/V checkpoint, and the plan now cites the code contract rather than
asserting it.

WHAT THIS ROUND CHANGED ABOUT THE PLAN'S SHAPE. Nothing about the design, everything about the
numbers. This is a Set whose entire purpose is to make an accreting count visible and freeze it, and
the count accreted past the Set's own paperwork between authoring and review, in a way that would have
failed its own validation and left one name unclassified. So the fix is systematic rather than
arithmetic: every count in the plan is now framed as a snapshot to be re-derived at execution time,
and the checks that mattered were converted from count comparisons to set differences, which are
immune to a moving baseline. That the missed name is the same one whose earlier omission from the
symmetry guard caused a real defect is the sharpest possible illustration of why the freeze guard is
the deliverable and not the classification.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The measured count is 48, not the 47 written throughout the Set. Correct every occurrence to 48, or reframe the counts as snapshots to be re-derived? | Reframe as snapshots, state 48 as the review-time measurement, and convert the load-bearing checks to set differences. | (a) Replace 47 with 48 everywhere; rejected because the count demonstrably moves faster than the paperwork (40 -> 47 -> 48 in six days), so a corrected literal would be stale again before execution and would fail validation the same way. (b) Leave 47 and note the drift in prose; rejected because V-02 used it as a PASS CRITERION, so prose alone would not stop a correct run from failing. | The measured drift itself (40 at filing, 47 at authoring, 48 at review) plus V-02's original wording "BEFORE (47)"; a set difference against child 01's classification is invariant under a moving baseline in a way a count comparison is not. | yes |
| D-2 | Should this review resolve OQ-01 by classifying the ambiguous names itself? | No: leave OQ-01 `open`, endorse its criterion, and spot-check its worked examples. | Resolving it here; rejected because the per-name classification IS child 01's deliverable, and a reviewer pre-deciding it would defeat the two-child split whose entire value is that the move is reviewed against an independently produced, frozen artifact. Also rejected: escalating it to the maintainer, since the criterion offered is checkable from code and no decision is stranded. | The Set's own rationale for splitting ("a move reviewed against a classification made during the move is reviewed against nothing"); child 01 verified to carry the same question as its own OQ-01, so the delegation is real; the criterion (a name is opencode-specific only if its BODY references an opencode-only concept) is the only formulation offered that is checkable rather than connotative, and its three worked examples hold on inspection. | yes |
| D-3 | This parent holds three E-items. Does that violate the "an orchestrator holds orchestration, not work of its own" rule? | No: they are legitimate, and the plan should CITE the code contract that makes them so. | Deleting them; rejected because AGENTS.md is explicit that a parent SHOULD carry a child checklist so a human told "execute the Set" runs it completely, and deleting it causes the lost work that rule exists to prevent. Adding to them; rejected for the opposite reason. | `ipd_lifecycle.ROLLUP_OMITTED_GATES` omits exactly the `pre-transition` E/V checkpoint because an orchestrator's items are "performed by NOBODY"; all three items here are pure confirmations of facts a child's own `V-*` gated, and the parent's `Scope-Paths` are the two children with no source file touched. | yes |
| D-4 | Child 02's V-07 repeats the "all four plans" error. Fix it here? | No: fix it in this parent only, and note it for child 02's own review. | Editing child 02; rejected because it was never a candidate in this review's ledger, editing a plan without reviewing it would leave an unrecorded change in an unreviewed artifact, and each child needs its own `/plan-review` where the correction belongs with its findings. | The workflow's ledger rule (a file referenced only as evidence is not in scope unless explicitly added); the Set has three plans, counted on disk. | yes |
