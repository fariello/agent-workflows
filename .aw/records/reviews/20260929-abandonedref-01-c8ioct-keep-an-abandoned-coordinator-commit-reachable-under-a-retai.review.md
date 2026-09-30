# Review findings: plan c8ioct

- Subject-Id: c8ioct
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `7280e7e0` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` with ZERO findings BEFORE semantic review, and `--phase
review-finalize --agent` reports `conforming` with ZERO findings after the revisions, so nothing here
was structural. No pre-review snapshot was owed: the plan was committed and unmodified and the
lane-input copy under `.aw/state/lane-inputs/rev-7/` is byte-identical (`diff -q` reports IDENTICAL).
Bare suite at review HEAD: `3322 passed, 2 skipped, 3 warnings in 165.17s`. NO production file or
test was modified by this review; every probe ran in `tempfile` fixtures outside the checkout, and
`git diff --stat -- agent_workflows/ tests/` is empty.

DISCLOSURE: the same agent and model authored this plan, so this is a SELF-REVIEW. Its value rests on
RE-EXECUTING the fourteen measurements rather than re-reading them, which is what this review did.

EVERY LOAD-BEARING CLAIM RE-EXECUTED AND ALL HOLD (F-16), which for a plan of this kind is the
finding. Driving the REAL `commit_lock.coordinator_worktree` in git fixtures: the abandoned arm leaves
`cat-file -e` rc 0, `merge-base --is-ancestor <sha> HEAD` rc 1, `for-each-ref` showing ONLY
`refs/heads/master`, the sha ABSENT from `reflog --all`, and `fsck` reporting `dangling commit <sha>`;
`gc --prune=now` in an UNPROBED fixture then takes `cat-file -e` to rc 1 and silences `fsck`, so the
loss is real and not theoretical. The classification triad E-04 depends on is exact: nothing-committed
gives `tip == base` True with `is-ancestor` rc 0, landed gives `tip != base` with rc 0, abandoned
gives `tip != base` with rc 1. The ORDERING claim is exact and is the subtlest thing in the plan:
`rev-parse <branch>` returns rc 0 before `worktree remove`, rc 0 after it, rc 0 after `worktree
prune`, and rc 128 only after `branch -D`, so the retention genuinely must sit before that line and
the plan puts it there. The namespace holds on BOTH halves: a retained
`refs/aw/abandoned/coordinator/<sha12>` survives `gc --prune=now` with `git show` and `git
cherry-pick` both rc 0, while `branch -a` stays `* master`, `branch --list 'aw/*'` is empty, `status
--porcelain` is empty and `for-each-ref refs/heads/` is unchanged; `update-ref` twice to the same name
and value is rc 0, so the idempotence claim holds too. Against a real bare remote, neither `git push
origin master` nor `git push --all` carried the ref. The prune works at three ages from ONE
`for-each-ref` call (60d and 20d deleted and collected, 0d surviving). A ref written FROM A LANE is
visible in the main checkout and survives lane teardown plus gc with its bytes still readable, which
matters because the runners execute in lanes by default. `gc.pruneExpire` is unset, so git's 2-week
default really is the basis for the 14-day window.

THE SHIPPED DEFECTS AND THE BOUNDARY ARE ALSO CONFIRMED (F-17). `coordinator_worktree`'s docstring
carries the false premise verbatim ("That is safe here BECAUSE the caller has already landed (or
deliberately abandoned) the commit"), and `land_worktree_commit` carries both over-claiming sentences
("The work is preserved in coordinator commit ", "The work is preserved as commit " with "(cherry-pick
or retry)"). `tests/test_commit_lock.py` does NOT exist while `tests/test_git_commit_helper.py` cites
it by name, so E-02 closes a real dangling citation. `land_worktree_commit` is called INSIDE the
`with _clock.coordinator_worktree(...)` block, which is the structural fact OQ-03 turns on, so that
resolution is sound rather than merely plausible. F-04's journal claim holds: a clean rollback calls
`_clear_finalize_journal`, so on the peer-edit arm the dangling commit really is the only carrier of
the agent's released bytes. Both named must-not-regress classes exist. Carrier `0ndipg` resolves to a
real open backlog item, so F-13's out-of-scope row genuinely filed its work. On cross-plan risk: two
`approved` plans declare `ipd_lifecycle.py` (`ygb3nk`, `qo9khm`), but NEITHER mentions
`coordinator_worktree`, `land_worktree_commit` or `_finalize_transaction`, and their own scope paths
are `work_cmd.py` and `runner_shared.py`, so there is no site collision and no dependency edge is owed.

THE ONE SUBSTANTIVE GAP (F-15) is that E-05's prune keys on `%(committerdate:unix)`, which is the date
stored IN THE COMMIT rather than the moment the ref was written, and the plan called the window
"principled" without stating the assumption that reconciles the two. The assumption HOLDS: review
measured a real `coordinator_worktree` commit's committer date equal to wall-clock time at retention
(delta 0 seconds), and the toolkit backdates no commit anywhere (zero `GIT_COMMITTER_DATE` or
`GIT_AUTHOR_DATE` assignments across `agent_workflows/` and `tests/`). So the mechanism is correct and
needs no redesign. What earns a finding is that the failure mode is SILENT AND IMMEDIATE if it ever
stops holding: review constructed a commit backdated 60 days, retained it, and measured that a 14-day
cutoff deletes its ref on the very NEXT invocation, destroying precisely the commit this plan exists
to save. Review also priced the obvious fixes and both are dead ends, which is worth recording so
nobody spends a round on them: `%(creatordate:unix)` returns the SAME backdated value, and a
`refs/aw/*` ref carries no reflog (`git reflog show <ref>` is empty), so there is no cheaper true
retention timestamp available in one call. The correct remedy is therefore a written assumption, not a
different key.

THE GATE DEFECT (F-19) matters more here than it usually would. The lifecycle clause instructed the
executor UNCONDITIONALLY to run `aw ipd finalize`, which the rubric names as a finding to fix because
the runners OWN that transition and self-finalize. In THIS plan the transition machinery is the
SUBJECT: `_finalize_transaction` is the function E-06 edits, so an executor following the original
text under `aw oc run` would invoke a transition the runner is already performing, exercising the very
failure arms under change. Rewritten as an unconditional finalize OBLIGATION with CONDITIONAL
ownership.

WHAT I DELIBERATELY DID NOT CHANGE, because each is already right. The `refs/aw/*` choice over a
branch or a tag is a measured decision, not a default, and OQ-01 prices all three options against the
backlog item's own open design. The fail-soft posture for both the ref write and the prune is correct
and cites the repository's own precedent (`_rollback_precommit`'s recorded reasoning that escalating
housekeeping inside a failing transaction "would block an operator for no safety gain"). The split of
E-02 from E-03 is genuine rather than padding: one pins the helper's contract in isolation and the
other pins what a transaction's operator sees, and they fail for different reasons. The refusal-
preserving assertions in E-03 and the two plan-specific prohibitions in the gate are exactly the right
guard for a plan whose subject invites a `checkout -f` shortcut, and V-03 correctly demands proof that
the exit code is NOT `EXIT_OK` so the class cannot be satisfied by making a contended finalize
succeed. The scaffold line "Add further leaves as `- [ ] E-NEW <action>`" is conventional here (181
executed plans carry it) and is not a finding. No spec governs this teardown, so the N/A spec-sync is
correct.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness / C. Operability | `git for-each-ref --format='%(committerdate:unix)' refs/aw/abandoned/` against a commit built with `GIT_COMMITTER_DATE` 60 days back; the same field measured equal to wall-clock for a real `coordinator_worktree` commit (delta 0s); `grep -rn "GIT_COMMITTER_DATE\|GIT_AUTHOR_DATE" agent_workflows/*.py tests/*.py` -> nothing | E-05 prunes on the COMMIT's date, not the retention time, and the plan called the 14-day window "principled" without stating the assumption that reconciles them. The assumption holds today (a coordinator commit is created when it is retained; nothing in the toolkit backdates a commit), so the mechanism is correct. But the failure mode if it stops holding is silent and immediate: a backdated commit's ref is deleted on the next invocation, destroying the commit the plan exists to save. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now requires the assumption in a comment beside the cutoff and names both rejected alternatives with their measurements (`creatordate` returns the same backdated value; a `refs/aw/*` ref has no reflog to date from). V-05 now demands the comment quoted plus a real invocation showing committer date equals retention time, and an explicit statement of the bound. F-15 added. |
| PR-002 | MEDIUM | IN-SCOPE | G. Plan executability (execution contract) | plan `## Approval and execution gate` as authored (`After execution ... move this plan to .aw/records/plans/executed/ through the tooled terminal transition (aw ipd finalize)`) | The lifecycle clause instructed the executor unconditionally, which the rubric flags because the runners own the transition and self-finalize. It is worse than boilerplate here: `_finalize_transaction` is the function E-06 edits, so a double invocation under `aw oc run` would exercise the very failure arms under change. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | Rewritten as an unconditional finalize OBLIGATION with CONDITIONAL ownership (runner self-finalizes when it executes the plan; hand execution runs the verb after a conforming pre-transition lint and pasted `V-*` evidence), retaining the no-hand-`git mv` prohibition. F-19 added. |
| PR-003 | LOW | IN-SCOPE | E. Testing and verification | F-12's `3246 passed, 2 skipped` at authoring HEAD `74b9c5c2` versus `3322 passed, 2 skipped, 3 warnings in 165.17s` measured at review HEAD `7280e7e0`; plan `## Required tests / validation` quoting the authoring figure | The plan's `Required tests` section cited F-12's authoring count beside the (correct) instruction to compare against a lane-re-taken baseline, which invites an executor to treat a stale number as the bar. Ordinary drift from sibling plans landing, not a defect. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-12 annotated in place with the re-measured figure and an explicit statement that it is a dated observation and not the bar; `Required tests` now names BOTH dated figures and directs comparison by node id against the executor's own lane baseline. F-18 added. |
| PR-004 | LOW | IN-SCOPE | G. Plan executability (evidence durability) | re-execution of all fourteen findings at review HEAD `7280e7e0` | Recorded as a POSITIVE finding because it is what licenses the plan: every load-bearing measurement reproduces, including the three that decide the design (the classification triad, the `branch -D` ordering, and the namespace's gc-immunity-plus-invisibility), plus the lane-retention property that matters because runners execute in lanes. No claim was found overstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-16 and F-17 added recording the re-executed values and the confirmed cross-plan boundary, so a later reader can see which HEAD each fact was last true at rather than re-deriving it. |

### Decisions

ID | Question | Chosen | Alternatives considered | Basis | Reversible
D-1 | E-05's prune keys on the commit's date rather than the retention time. Change the mechanism or record the assumption? | RECORD THE ASSUMPTION. Keep `%(committerdate:unix)` and require a comment stating that a coordinator commit is created when it is retained, so its committer date IS its retention time. | (a) Switch to `%(creatordate:unix)`, rejected because review measured it returns the SAME backdated value for a backdated commit, so it fixes nothing; (b) date the ref from its own reflog, rejected because a `refs/aw/*` ref has no reflog (`git reflog show <ref>` empty); (c) write the retention timestamp into the ref name or a sidecar, rejected as a new storage format for a hazard that cannot currently occur; (d) raise it as a blocking question, rejected because the repository answers it (nothing backdates a commit). | Measured: a real `coordinator_worktree` commit's `committerdate` equalled wall-clock exactly; a 60-day-backdated `commit-tree` reported `committerdate:unix` and `creatordate:unix` identically against a now-14d cutoff; `git reflog show refs/aw/abandoned/coordinator/<sha12>` empty; zero `GIT_COMMITTER_DATE`/`GIT_AUTHOR_DATE` assignments in `agent_workflows/` or `tests/` | yes
D-2 | Two `approved` plans declare `agent_workflows/ipd_lifecycle.py`. Declare an `- Item-Dependencies:` edge? | No edge. | Declaring `executed:ygb3nk, executed:qo9khm`, rejected because neither plan touches any symbol this one edits and their real scope paths are `work_cmd.py` and `runner_shared.py`; a false ordering edge would delay a release-blocking bug fix behind unrelated work. | Searched both plans for `coordinator_worktree`, `land_worktree_commit`, `_finalize_transaction`, `commit_lock` -> no matches; read each plan's `- Scope-Paths:` and `- Scope:` | yes
D-3 | Is `refs/aw/abandoned/coordinator/<sha12>` the right namespace, or should review overrule OQ-01? | Uphold OQ-01. `refs/aw/*` is correct. | (a) A retained branch under `refs/heads/aw/abandoned/*`, rejected and re-verified worse: it appears in `git branch -a`, is carried by `git push --all`, and is swept by `worktree_lease`'s `refs/heads/` enumeration; (b) a tag, rejected outright because the execution contract forbids creating tags outside a release GO and a tag is carried by `--follow-tags`; (c) naming only the sha, rejected because review measured gc collecting it, so it is necessary but insufficient (and the plan already folds it in as E-06's honest fallback). | Re-measured: the retained ref survived `gc --prune=now` with `show`/`cherry-pick` rc 0 while `branch -a`, `branch --list 'aw/*'`, `status --porcelain` and `for-each-ref refs/heads/` were all unchanged; neither push form carried it to a real bare remote; only two ref enumerations exist in the toolkit and both are `refs/heads/`-scoped | yes
D-4 | F-12's suite baseline has drifted from 3246 to 3322. Treat as a defect or as drift? | Drift. Annotate both figures and direct comparison against the executor's own lane baseline. | Failing the plan for a stale count, rejected because the plan's own E-01 already requires re-taking the baseline on the lane, which is the correct instruction; the only real risk was the `Required tests` section reading as if 3246 were the bar. | Bare `python3 -m pytest` at review HEAD `7280e7e0` -> `3322 passed, 2 skipped`, same 207 deselected by the configured `-m 'not slow'` | yes
