# Review findings: plan o3cfk4

- Subject-Id: o3cfk4
- Subject-Type: ipd
- Reviewed-At: 2026-09-24
- Reviewer: opencode/its_direct-pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `e3e2f8de` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0) BEFORE semantic review, so nothing found below is structural;
`--phase review-finalize` conforms after revision.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests
entirely on RUNNING the claims rather than re-reading them, which is what produced the retraction below.

THE PLAN'S OWN FIX WAS FALSIFIED BY MEASUREMENT, AND SO WAS THE SHIPPED CODE IT TRUSTED. The plan
correctly identifies that the shipped self-check guards `len(claimants) > 1` and is blind to `len == 0`.
It then proposes adding a `len == 0` branch. Measuring the actual query showed that fix cannot work,
because the defect is one layer deeper: the query reads the WORKING TREE, and both corruption shapes are
properties of the COMMIT.

```text
# PR-001: which tree does the check actually ask?
agent_workflows/backlog.py::_iter_items  ->  for f in sorted(d.glob("*.md"))
# a filesystem glob, so backlog_item_paths_for_id describes the WORKING TREE, not HEAD.

# both corruption shapes, in throwaway git fixtures, measured end to end:
addonly   WORKING-TREE claimants=1   COMMITTED(HEAD) claimants=2
          shipped guard len>1 fires? False | plan E-02 guard len==0 fires? False
delonly   WORKING-TREE claimants=1   COMMITTED(HEAD) claimants=0
          shipped guard len>1 fires? False | plan E-02 guard len==0 fires? False
```

Both guards are False in BOTH shapes. Two consequences follow, and the second is the one that decides
this review:

1. The shipped `attention.duplicate-id` write-time branch has NEVER been able to fire on the 36-item
   `_staged_paths` corruption its own comment says it exists to catch. A half-committed `git mv` leaves
   the working tree perfectly correct: exactly one file, in the right directory.
2. The plan's proposed `len == 0` branch could NOT have fired on `ca8e22e4`, the very commit the plan
   cites as its measured occurrence. Confirmed from the other direction with a fresh checkout:

```text
git worktree add --detach ../co0 HEAD   # HEAD = the deletion-only commit
find ../co0/.aw/records/backlog -name "*.backlog.md"
  -> find: '../co0/.aw/records/backlog': No such file or directory
# the item is in NEITHER committed tree, yet the working tree that produced that
# commit still held exactly one claimant, which is what the check would have read.
```

So the plan would have shipped a second check as blind as the first, and its tests would have gone
green, because the EXISTING tests for this check use no git repository at all:

```text
tests/test_runner_backlog_close.py::BacklogCloseIntegritySelfCheck._repo
  -> (root / ".aw/records/backlog/graduated").mkdir(parents=True, exist_ok=True)
# no `git init` anywhere in the class. So test_two_claimants_are_detected_which_is
# _the_36_item_corruption names the real corruption and constructs a shape that
# commit never produced; it passes against a check blind to every real occurrence.
```

ONE OF THE PLAN'S OWN FINDINGS OVERSTATES THE GAP, which matters because an executor would have built a
rule that already exists. F-3 claimed NO layer catches the absent shape. A partial detector does:

```text
check_engine.py rule table -> "check.from-backlog-dangling": RuleSpec("error", ...)
# fires when a plan/spec's From-Backlog resolves to no item.
git show ca8e22e4:.aw/records/plans/pending/...7jqev2....ipd.md | grep From-Backlog
  -> - From-Backlog: 8pcdoa
# and 8pcdoa is one of the ten items that same commit deleted, so this error rule
# WOULD have fired on the exact corruption the plan calls undetected.
```

The residual gap is real but narrower: an item with no surviving referrer, and the write-time moment.

TWO MEASURED FALSE-POSITIVE RISKS IN THE UNBUILT E-03, both of which would have made the new report
noise on its first day:

```text
# PR-004: validity is not "any findings"
artifact_core.drift_exit_code -> 1 if any(severity != "info" for d in drift) else 0
attention.LANE_SUPERSEDED_RULE -> graded `info` deliberately
# live on this tree:
lane drift count: 8   ... 4 of them severity `info`
exit code from lanes alone: 1
# a report counting raw findings announces an invalid board on a tree the gate calls valid.

# PR-005: the committed-tree check has nothing to inspect on the DEFAULT path
commit_backlog_close docstring:
  "Returns the new commit sha, or None when nothing was committed."
  "AN ISOLATED TURN NO LONGER CALLS IT: its move happens in the lane and is swept
   up by the lane's own finalize commit"
# so a naive "0 committed claimants" report fires on almost every normal run.
```

Also measured for E-03's cost, since a user-perceptible slowdown is itself a `bug` by repository policy:
`aw attention --check --agent` takes about 4.8s wall here (`real 0m4.823s`). Paid once per run that is
defensible, but the plan did not ask the executor to measure it, and now does.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A (correctness); G (plan executability) | `agent_workflows/backlog.py::_iter_items` (`d.glob("*.md")`); two-shape git fixture measurement; fresh checkout of `ca8e22e4` | THE PROPOSED FIX CANNOT WORK. The self-check's query reads the WORKING TREE, while both corruption shapes are properties of the COMMIT, so a half-committed `git mv` leaves the working tree correct. Measured: addition-only -> working-tree 1 / committed 2; deletion-only -> working-tree 1 / committed 0. `len > 1` AND the proposed `len == 0` are both False in both. The shipped duplicate branch therefore cannot fire on the 36-item corruption, and E-02 as authored could not have fired on `ca8e22e4`. Executing it would ship a second blind check. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Goal, Concern, Scope, E-01, E-02, the ordered changes, conventions, scope check, spec-sync and V-01/V-02 all rewritten. E-02 now adds a COMMITTED-tree claimant query and reports both broken counts from it. Recorded in the plan as F-6 with the measurement. The original `len == 0` wording is superseded in place and labelled so, rather than silently replaced. |
| PR-002 | HIGH | UNDER-SCOPE | E (testing/verification); D (anti-regression) | `tests/test_runner_backlog_close.py::BacklogCloseIntegritySelfCheck._repo` (plain `mkdir`, no `git init` in the class) | THE EXISTING TESTS MASK PR-001 AND WOULD HAVE MASKED THE NEW BRANCH TOO. Every case writes files into a `tempfile` directory with no git repository, so they assert only the working-tree query. `test_two_claimants_are_detected_which_is_the_36_item_corruption` names the real corruption but builds a shape no commit produces. A new test written in the same style would pass against a still-blind check. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as F-7. E-04 rewritten to require REAL git fixtures (`git init`, commit, `git mv`, commit one side), to cover both committed miscounts, and to state that a new test passing against current code has reproduced the blind spot rather than the defect. V-04 now demands the fail-first demonstration with the fixtures shown to use real commits. The existing no-git cases are kept (scope check says so) because they are inadequate, not wrong. |
| PR-003 | MEDIUM | IN-SCOPE | F (honest documentation) | `check_engine.py` rule table (`check.from-backlog-dangling`, severity `error`); `git show ca8e22e4:...7jqev2....ipd.md` -> `- From-Backlog: 8pcdoa` | THE PLAN'S F-3 OVERSTATES THE GAP. It claims no layer catches the absent shape; `check.from-backlog-dangling` is an `error` rule that fires on any plan/spec whose `From-Backlog` resolves to no item, and the plan committed IN `ca8e22e4` carries `From-Backlog: 8pcdoa`, one of the ten items that commit deleted. So an existing error rule WOULD have fired on the cited corruption. Left uncorrected, an executor may believe it is building the only detector. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-3 rewritten and downgraded MEDIUM, stating what the existing rule covers (the referrer case) and naming the genuinely uncovered cases (an item with no referrer; the write-time moment). E-01 now requires measuring this rather than assuming. The deferral for the portable rule is re-scoped to the corrected gap. |
| PR-004 | HIGH | IN-SCOPE | C (architecture/operability); F (prevent silent failure) | `artifact_core.drift_exit_code` (exempts `info`); `attention.lane_drift_severity` / `LANE_SUPERSEDED_RULE`; live: 8 lane findings, 4 `info`, exit 1 | E-03 WOULD HAVE BEEN WRONG ON ITS FIRST DAY. Validity is `drift_exit_code(drift) == 0`, not `len(drift) == 0`: `attention.lane-superseded` is graded `info` deliberately so it reports without failing the gate. A report computing validity from raw finding count announces an invalid board on a tree CI calls valid, which is the "trains people to ignore the rule" failure `4y7nzh` itself warns about. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as F-8. E-03 now requires computing validity through `drift_exit_code`, names the measurement, requires naming the outstanding rule ids (not merely that something is wrong), and requires silence on a records-free repository. E-04 and V-03 now require an `info`-only tree to be shown SILENT. |
| PR-005 | HIGH | IN-SCOPE | A (correctness); F (prevent silent failure) | `runner_shared.commit_backlog_close` docstring ("Returns the new commit sha, or None when nothing was committed"; "AN ISOLATED TURN NO LONGER CALLS IT") | THE COMMITTED-TREE CHECK MUST SKIP WHEN THERE IS NO SHA, and nothing in the plan said so. An ISOLATED turn is the DEFAULT and has its move swept into the lane's finalize commit, so there is frequently no commit here to inspect. A naive "0 committed claimants" report would fire on the normal path, making the new check noise immediately. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Recorded as F-9. E-02 now carries an explicit no-sha requirement (skip silently, with the reasoning recorded in the code, since it is the likeliest route to this check being ignored). E-04 and V-02 require the no-sha case to be shown silent. |
| PR-006 | MEDIUM | UNDER-SCOPE | C (architecture); E (testing) | `runner_shared.initialize_run_core` (`report_untracked_dirt_at_run_start(repo)` beside the flag refusals); `report_untracked_dirt_at_run_start` docstring; spec `25kzda` :222 | E-03 NAMED NO CONCRETE SEAM, saying only "the pre-flight region". The established run-start reporting seam already exists and has every property E-03 asks for (once per run, before the run directory, never raises, both hosts delegate there), and `25kzda` already documents its sibling report. Leaving this to the executor risks a second seam, a per-item report, or a needless host-module edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now names `report_untracked_dirt_at_run_start` in `initialize_run_core` as the site and forbids inventing a second seam. Added to the conventions section. The scope check now states this should require no host-module edit and to report if it does. Spec-sync notes `25kzda`'s existing parallel sentence as the likely amendment shape. |
| PR-007 | MEDIUM | IN-SCOPE | C (operability); F (KISS) | measured `aw attention --check --agent` -> `real 0m4.823s`; AGENTS.md release-gates ("inefficiency a user can notice is a defect") | E-03 ADDS AN UNMEASURED COST TO EVERY RUN START and the plan never asked for it to be measured. At about 4.8s for the full view, this is defensible once per run but must be known rather than assumed, and this repository treats a user-perceptible slowdown as a `bug` in its own right. Also unstated: whether to call the view in-process or shell out to the CLI and parse text. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires reusing the in-process functions and `drift_exit_code` rather than parsing CLI text, and requires the added startup cost to be MEASURED and pasted, with an instruction to report rather than silently slow every run. V-03 requires the measurement as evidence. |
| PR-008 | MEDIUM | IN-SCOPE | F (honest documentation) | the self-check comment block ("A `_staged_paths` bug committed this very relocation ... 36 items were corrupted"); `backlog_item_paths_for_id` docstring ("THE SCOPED INTEGRITY QUESTION") | TWO SHIPPED DOCSTRINGS NOW OVERCLAIM, given PR-001. Both assert the check answers the integrity question posed by the duplicate incident, which its working-tree query cannot observe. The plan's spec-sync section only asked to EXTEND that prose to mention the zero case, which would leave the false claim standing and mislead the next reader exactly as it misled this plan's author. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section rewritten: E-02 must CORRECT the self-check comment (not merely extend it) and correct `backlog_item_paths_for_id`'s docstring to state plainly that it describes the working tree and to point at the committed-tree sibling. |
| PR-009 | LOW | UNDER-SCOPE | B (security and privacy) | AGENTS.md leak-sanitizer paragraph; the new messages carry repository paths and a commit sha to stderr and the run ledger | THE VALIDATION SECTION DID NOT REQUIRE THE LEAK SANITIZER. This change adds new message strings to stderr and `events.jsonl`, which is precisely the surface the deterministic sanitizer scans; the existing sibling test already pins that these path strings must not be absolute. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `aw sanitize --agent` added to the required tests, and its output added to V-04's required evidence. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-001 falsifies E-02's premise. Is this plan REPLAN, or repairable with bounded edits? | Repair in place: keep the plan's target (the write-time check) and its structure, and re-aim E-02 from "count claimants differently" to "ask the committed tree". | REPLAN: rejected because the plan's DIAGNOSIS of a real gap, its two-layer scope, E-03 and E-04 all survive, and the correction is a change of QUERY within the same function and the same reporting shape. A replacement plan would have substantially this shape. Retiring it would also strand the inherited `Blocks-Release: next`. | `plan-review.md` Step 2.4 (REPLAN only when not repairable with bounded edits); the surviving items are E-01/E-03/E-04 plus E-02's reporting design (F-5) | yes |
| D-2 | Should E-02 fix `backlog_item_paths_for_id` to read the commit, or ADD a committed-tree sibling? | Add a sibling; leave the existing function's working-tree semantics untouched. | Changing the existing function: rejected on measured blast radius. Its working-tree contract is pinned by four existing tests including a both-hosts-share-one-object assertion, and the plan's own scope check forbids altering its query semantics. The two queries also answer genuinely different operator questions (a dirty checkout versus propagating corruption). | `tests/test_runner_backlog_close.py::BacklogCloseIntegritySelfCheck` (4 cases pinning working-tree behavior); the plan's `## Scope check` | yes |
| D-3 | PR-001 means the SHIPPED duplicate branch has never worked. Does that need its own corrective plan, or does this plan absorb it? | Absorb it: E-02's committed-tree query fixes both counts at once, in the same function, so no separate plan is needed. | A separate corrective IPD for the duplicate branch: rejected because it would touch the same block for the same reason in the same way, and two plans editing one guard is the collision this repository spends scope fences preventing. | `AGENTS.md` (a corrective IPD is for a post-execution gap in an `executed/` plan; this code is live and in this plan's declared scope) | yes |
| D-4 | Do the portable `check_engine`/`attention` duplicate-id rules share the same working-tree assumption PR-001 found in the runner? | NOT MEASURED, and explicitly flagged as unmeasured in the plan rather than assumed either way. | Asserting they are fine (would be an unverified claim about the CI gate's reach); or widening this plan to measure and fix them (rejected: the plan is runner-scoped, and the portable rule family is already deferred to a successor plan). | `plan-review.md` (verify claims from evidence; do not infer unsupported details); the plan's existing deferral of the portable rule | yes |
| D-5 | OQ-01 (build recommendation (ii), the opt-in pre-commit hook, here?) is `- Blocking: no` and `- Owner: maintainer`. Resolve it or leave it open? | Leave it OPEN, unchanged. It is correctly non-blocking and correctly owned by the maintainer. | Resolving it myself: rejected because it is a POLICY call about local-versus-CI enforcement (whether to add a fifth opt-in hook nobody has installed), which the repository does not answer and which is the maintainer's to make. A non-blocking open question does not make a plan NO-GO. | `plan-review.md` Step 3.1 ("Never guess a human decision") and the `NO-GO` ruling of 2026-09-10 (non-blocking questions do not gate) | yes |

### Deferred and open

No finding is DEFERRED, OPEN, or REPLAN. Every finding above is FIXED, so no escalation to a
`- Blocking: yes` question is owed under the `review_findings_gate` rule (default `block_at: HIGH`;
no `review_findings_gate` key is configured in `.aw/config/project.json`).

OQ-01 remains OPEN by design, carrying `- Blocking: no` and `- Owner: maintainer` (see D-5). It does
not gate readiness.

### Notes on what was NOT changed, and why

- No code, test, or spec file was touched by this review. Only the plan under review and this record.
- The plan's F-1 (the `len > 1` predicate) was NOT retracted. It is TRUE as far as it goes; it is
  merely not the whole defect. F-6 is recorded beside it rather than replacing it, so the plan shows
  both layers and the order in which they were found.
- The existing `BacklogCloseIntegritySelfCheck` no-git cases were NOT marked for deletion. They
  correctly pin the working-tree query, which D-2 keeps; deleting a passing test to replace it is how
  coverage silently shrinks, and the scope check now says so.
- `- Blocks-Release: next` was left in place. The plan addresses a live `bug`-kind item's detection
  gap, and PR-001 makes the underlying hole WIDER than the item claimed, not narrower, so the gate is
  still earned.
