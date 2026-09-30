# Review findings: plan eg9jjm

- Subject-Id: eg9jjm
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `2658514a` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` with ZERO findings BEFORE semantic review, and `--phase
review-finalize --agent` reports `conforming` with ZERO findings after the revisions, so nothing here
was structural. No pre-review snapshot was owed: the plan was committed and unmodified and the
lane-input copy under `.aw/state/lane-inputs/rev-8/` is byte-identical (`diff -q` reports IDENTICAL).
Bare suite at review HEAD: `3322 passed, 2 skipped, 3 warnings in 120.15s`. NO production file or test
was modified by this review; every probe ran in `tempfile` fixtures outside the checkout and `git diff
--stat -- agent_workflows/ tests/` is empty.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
RE-EXECUTING the measurements and on reading the surrounding call sites, which is what produced the two
findings that changed the work.

EVERY LOAD-BEARING CLAIM RE-EXECUTED AND ALL HOLD, INCLUDING BOTH INTRA-FUNCTION OFFSETS (F-15).
`integrate_retired_lane`'s body is 5044 characters with the teardown at 4567 and the
`process_backlog_close(run_dir, state, item)` call at 4974, reproducing F-04 digit for digit, and the
body contains ZERO `closed` predicates, so it really is the one unguarded bare call. The guard harm
reproduces verbatim: a record holding `closed: True` plus commit `abc123def456` became `{closed: False,
reason: "item is already done", rule: null, evidence: null, wrote_in: "main"}`, and
`unclosed_backlog_items` then returned `('bg0001', 'item is already done')`, which is exactly the
operator-visible line F-08 claims. The stranded half-move reproduces with both porcelain lines (` D
<graduated>` and `?? <done>`) while `git ls-tree -r HEAD` still records the item at `graduated/`, and
`dirty_tree_overlap` returned the stranded path when passed as the incoming change and `[]` for an
unrelated path, so F-03's gate interaction is real rather than a tidiness complaint. F-09's refusing
verdict reproduces with its exact reason string (`IPD carrier(s) not executed:
.aw/records/plans/superseded/...`), which means the plan's CORRECTION of its own backlog item is sound;
that correction is the plan's best work, because it narrows a frequency claim the item overstated while
leaving the severity claims untouched. `process_backlog_close` arrives at `integrate_retired_lane` as a
keyword parameter, confirming the injection rule E-04 must thread.
`tests/test_inlane_retirement_lands.py` carries the `_HOSTS` tuple as quoted and its 5 tests pass, so
F-11's test-surface choice is correct and gets both hosts by construction.

THE CENSUS THE PLAN IMPLIED BUT DID NOT STATE is worth recording because it is what makes the scope
provably right. Five sites reach the setter path in `runner_shared`: `retry_deferred_integrations`
is GUARDED and already routed through `perform_coordinator_backlog_close` (`pjuoyj`'s fix, the model
E-04 copies); `finish_reintegrated_item` is GUARDED with a bare call; the `execute_item_core`
self-finalize arm is GUARDED with a bare call; the in-lane arm correctly passes `lane_handle`/
`lane_repo`; and `integrate_retired_lane` alone is BOTH unguarded AND bare. So E-03 adds a guard three
other sites already carry and E-04 adopts a routing one other site already has, which is as low-risk as
a change to this file gets. Added to the plan's conventions so an executor does not "fix" a correct
site.

THE FINDING THAT CHANGED THE WORK (F-13) is that routing the write through the performer ALSO MOVES THE
SETTER'S OWN RELEASE-GATE TREE, and the plan never says so. The performer calls
`process_backlog_close(..., lane_repo=coord.path)`; that function computes `write_repo` from
`lane_repo` and hands `write_repo` to `close_backlog_item`, whose own docstring states that its single
`--dir` chooses BOTH the tree the item moves in AND the tree `check_engine.evaluate_blocking_close`
scans for carriers and resolves `--evidence` against, in its words "THE TWO CANNOT BE SPLIT FROM HERE".
So after E-04 the setter's gate evaluates in the coordinator worktree rather than in main. IT IS SAFE
HERE AND I MEASURED WHY rather than assuming: a coordinator worktree is a full checkout of main's HEAD
(verified to contain the plans and backlog trees), and `evaluate_backlog_close` returned the IDENTICAL
verdict in main and in the coordinator tree for the retired-plan shape. The permissive hazard that
docstring warns about is specific to a LANE, where this run's own plan already sits in `executed/` and a
lane-side carrier scan finds what main would not; a retired plan sits in `superseded/` in BOTH trees, so
no permissive shift occurs. The one real residual is that a tree pinned at HEAD cannot see a carrier or
evidence artifact that exists in main only as an UNCOMMITTED file, which makes the gate MORE likely to
refuse, i.e. the fail-closed direction. That is acceptable and it must be WRITTEN DOWN, because the next
reader's obvious "fix" would be to widen the tree, which would convert a safe refusal into the
permissive error the docstring warns about. Note the sibling plan `pjuoyj` did not address this either,
so this is a property inherited from the shipped mechanism rather than a new defect this plan introduces.

THE STALE DEFERRAL (F-14). The `--gate-dir` row described `9vglxd` as a PENDING plan overlapping this
one as a file and named `10pcd5` as its live carrier. Both facts have expired: `9vglxd` is `executed`
and `10pcd5` is `done`, so there is no pending sibling and no live carrier, and the row's
`- Carrier: 10pcd5` was pointing at a closed item. The flag itself SHIPPED (`--gate-dir` is on the `aw
backlog set` parser and honored in `backlog.run_set`, which resolves a separate gate root from it). What
did NOT change is the part E-04 depends on: the runner's own `close_backlog_item` still passes only
`--dir`, so from the runner the move tree and the gate tree remain one tree. Rewritten to state the
shipped reality, with the carrier replaced by a `Carrier-Declined` and the live consequence moved into
F-13 where an E-item can act on it.

WHAT I DELIBERATELY DID NOT CHANGE. The scope is the right size and F-12's exclusions are correct on
their merits: the self-finalize arm writes to its own execution tree by definition, and
`finish_reintegrated_item` is an out-of-band operator action, so neither is a defect. Splitting E-03
(guard) from E-04 (routing) is right because they are independent and the guard half stands alone if the
tree half were ever descoped, which the gate's FIRST refusal already anticipates. The four refusals in
the gate are unusually good and I left them verbatim: the E-01 re-measure gate, the never-force-a-
refusal rule, the do-not-turn-F-09's-refusal-into-a-close rule with E-02 case (4) pinning it, and the
do-not-modify-the-performer rule. The plan records NO suite baseline count, which is correct under its
own convention, so there was no stale number to annotate.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A. Correctness / B. Security (authorization) | `inspect.getsource(runner_shared.close_backlog_item)` docstring (`--dir` chooses the move tree AND the gate tree; "THE TWO CANNOT BE SPLIT FROM HERE") and its `--dir`-only argv; `process_backlog_close`'s `write_repo` assignment feeding `close_backlog_item(write_repo, ...)` beside its `evaluate_backlog_close(repo, ...)` call; `evaluate_backlog_close` driven in main and in a real coordinator worktree | Routing the write through the performer also moves the SETTER's own release-gate tree from main to the coordinator worktree, and the plan never states it. Measured SAFE for this shape (the coordinator tree is main's HEAD and the verdict was identical; the permissive lane hazard does not apply because a retired plan is in `superseded/` in both trees), with one residual: a carrier or evidence artifact present in main only as an uncommitted file is invisible to a HEAD-pinned tree, which is the fail-closed direction. Unstated, the next reader's obvious fix is to widen the tree, which would create the permissive error the docstring warns about. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-04 now requires a comment recording that the gate tree moved, why it is fail-closed here, and the uncommitted-only-carrier bound, and forbids widening the tree. V-04 now demands a measurement showing the verdict unchanged between the two trees, and makes a DIFFERING verdict a STOP. F-13 added. |
| PR-002 | MEDIUM | IN-SCOPE | G. Plan executability (evidence accuracy) | `ls .aw/records/plans/executed/*9vglxd*` resolves; `.aw/records/backlog/done/20260916-dirtygates-01-10pcd5-*`; `grep -n "gate_dir" agent_workflows/backlog.py agent_workflows/cli.py`; `close_backlog_item`'s argv | The `--gate-dir` deferral row is stale in both facts: it calls `9vglxd` a pending plan (it is `executed`) and names `10pcd5` as a carrier (it is `done`), so it carried a live obligation pointing at closed work. The flag shipped; what did not change is that the runner still passes only `--dir`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Row rewritten to the shipped reality, `- Carrier:` replaced with `- Carrier-Declined:`, and the live consequence relocated into F-13. F-14 added. |
| PR-003 | MEDIUM | IN-SCOPE | G. Plan executability (execution contract) | plan gate as authored (`Post-gate lifecycle move: on completion, transition this plan through the tooled lifecycle (aw ipd begin / aw ipd finalize)`) | The lifecycle clause instructed the executor unconditionally, which the rubric names as a finding because the runners own the transition and self-finalize when they execute a plan. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Rewritten as an unconditional finalize OBLIGATION with CONDITIONAL ownership, keeping the no-hand-move prohibition and the pre-transition lint plus pasted-evidence bar it already stated correctly. F-16 added. |
| PR-004 | LOW | IN-SCOPE | C. Architecture (mechanism census) | `inspect.getsource` over the five setter call sites in `runner_shared`; the guard predicate located at each | The plan's scope argument rested on a census it implied but never tabulated, leaving an executor to re-derive which of five sites is which and risking a "fix" to a correct one. Measured: `integrate_retired_lane` is the ONLY site both unguarded and bare, so E-03 adds a guard three siblings carry and E-04 adopts a routing one sibling has. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The five-site census added to `## Project conventions discovered (Step 0)` with each site's guard and routing state named. F-15 records the re-executed measurements including both intra-function offsets. |

### Decisions

ID | Question | Chosen | Alternatives considered | Basis | Reversible
D-1 | Routing through the performer moves the setter's release-gate tree to the coordinator worktree. Accept it, adopt `--gate-dir`, or descope the routing? | ACCEPT and document. Require E-04 to comment the shift, its fail-closed direction, and the uncommitted-only-carrier bound. | (a) Adopt `--gate-dir` so the gate stays on main, rejected because it would widen scope into `close_backlog_item`'s argv and `backlog.run_set`, neither declared, for a shift measured to change no verdict for this shape; (b) descope E-04 and ship only the guard, rejected because the stranded half-move is the release-blocking harm and it reproduced; (c) say nothing, rejected because the next reader's obvious fix is to widen the tree, which would create the permissive error `close_backlog_item`'s docstring warns about; (d) raise it as a blocking question, rejected because the repository answers it by measurement. | `close_backlog_item` docstring and argv; `process_backlog_close`'s `write_repo` versus `repo` split; a real coordinator worktree shown to contain the plans and backlog trees; `evaluate_backlog_close` returning `close=False` identically in main and in that tree for the retired-plan shape | yes
D-2 | The `--gate-dir` deferral row names a carrier that is `done` and a plan that is `executed`. Re-point the carrier or decline it? | DECLINE it with a stated reason. | (a) Re-point `- Carrier:` at a new backlog item for "make the runner pass `--gate-dir`", rejected because filing an item asserts an outstanding defect, and D-1 measured no verdict change for this shape, so there is nothing to fix; (b) delete the row, rejected because a reader needs to know the flag exists and that the runner deliberately does not use it. | `9vglxd` under `executed/`; `10pcd5` under `backlog/done/`; `--gate-dir` present in `cli.py` and honored in `backlog.run_set`; `close_backlog_item` argv carries `--dir` only | yes
D-3 | `runner_shared.py` is declared by roughly forty pending plans. Declare an `- Item-Dependencies:` edge to any of them? | No edge. | Declaring edges to the plans that mention this area, rejected because none edits `integrate_retired_lane`'s body: the plans naming it cite it only in findings, and the nearest neighbour (`z8ex9f`, which touches `teardown_lane_if_classified` call sites) declares `lane_containment.py` and not `runner_shared.py`. File overlap on a high-traffic module is what worktree isolation and the merge-and-revalidate gate already handle. | Searched every pending plan declaring `runner_shared.py` for `integrate_retired_lane`/`perform_coordinator_backlog_close`/`process_backlog_close`, then read each hit's `- Scope-Paths:` and E-items | yes
D-4 | Should the plan record a suite baseline count, as several sibling plans do? | No. Leave it absent. | Recording review's `3322 passed, 2 skipped`, rejected because the plan's own `Required tests` correctly demands a baseline captured at the SAME commit as the after-state, and a plan-recorded figure cannot distinguish a test this plan adds from a sibling landing on main; writing one would invite exactly the stale-bar problem other plans in this sweep had to have annotated. | Plan `## Required tests / validation` ("A baseline captured at the SAME commit as the after-state ... a baseline stated from memory is not a baseline"); bare suite at review HEAD `2658514a` -> `3322 passed, 2 skipped` | yes
