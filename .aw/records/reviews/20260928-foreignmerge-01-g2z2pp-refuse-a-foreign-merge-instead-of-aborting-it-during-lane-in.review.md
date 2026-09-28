# Review findings: plan g2z2pp

- Subject-Id: g2z2pp
- Subject-Type: ipd
- Reviewed-At: 2026-09-28
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `821245a6` in a lane worktree. Structural preflight `aw ipd lint --phase author
--agent` CONFORMED before revision (exit 0, `findings: 0`), and `--phase review-finalize` CONFORMS
after revision (exit 0, `findings: 0`). No pre-review snapshot was owed: `git status --porcelain --`
on the plan path was empty.

THIS IS A STRONG PLAN AND ITS DIAGNOSIS IS CORRECT. Every premise measurement reproduced. F-01
reproduces EXACTLY, including the incident's signature: driving the real
`runner_shared.integrate_lane_branch` against a scratch repo holding a third party's staged
`git merge --no-ff --no-commit` returned `kind='fail-merge'` with the reason
`[aw-integration-cause=git-merge-conflict][aw-conflict-shape=unknown] merge-back conflict; fatal: You
have not concluded your merge (MERGE_HEAD exists).`, the staged set went from `['other.txt']` to `[]`,
the index tree hash changed, `MERGE_HEAD` was gone, and the newest reflog entry read
`reset: moving to HEAD`. F-03 reproduces on all three probes (`merge_write_set` -> `['lanefile.txt']`,
`dirty_tree_overlap` -> `[]`, `conflicted_paths` -> `[]`), so the existing guards are genuinely blind
to this condition and a new arm really is required. F-04 reproduces on both sides. F-06 reproduces:
an octopus `MERGE_HEAD` file held two ids while `git rev-parse MERGE_HEAD` printed one, so E-01's
insistence on the `--git-path`-plus-read spelling is correct and its prohibition is well founded.
E-01's linked-worktree claim reproduces precisely (`--git-path` resolved into
`<common>/.git/worktrees/<name>/`, `<worktree>/.git/MERGE_HEAD` did not exist, and a merge in a linked
worktree is invisible from the primary checkout and vice versa). E-03's stated site exists and is
unambiguous. F-07's staleness correction is right, F-08's both-hosts conclusion is right, F-09's
lane-local aborts are correctly fenced out, F-12's gap is real, and F-13/F-14's constraints on the
reason string are accurate. The refusal-kind reuse argued in OQ-01 is correct and well reasoned, and
OQ-02's keep-both answer is right for the reasons it gives. Carriers `p7dtbr` and `csmtjp` both exist
on disk.

WHAT REVIEW FOUND IS ONE SUBSTANTIVE DEFECT IN THE PROPOSED FIX, plus three corrections and a stale
comparison bar.

**THE OWNERSHIP PROOF IS NOT AN OWNERSHIP PROOF (PR-201, HIGH, and the finding this review exists
for).** `MERGE_HEAD` records WHICH commit was merged; it records nothing about WHO merged it. So
`owns_merge_in_progress(repo, branch=handle.branch)`, implemented exactly as E-02 specifies, returns
True for a THIRD PARTY's merge of this lane's own branch. MEASURED at HEAD `821245a6`: a human ran
`git merge --no-ff lane/probe` in main, hit a conflict, resolved one path by hand and staged an
additional file (`human_only.txt`) existing on no branch; `MERGE_HEAD` equalled the lane tip exactly,
the predicate returned **True**, and `git merge --abort` then took the staged set from
`['extra.txt', 'f.txt', 'human_only.txt']` to `[]`, deleted `human_only.txt` outright, and reverted the
hand resolution. That is the SAME harm class this plan exists to remove, reached through the very race
E-03's own text admits it cannot close: a peer stages a merge between E-03's read and our merge
attempt, and if what they merged happens to be our lane branch, the branch comparison cannot tell us
apart. The plan reasons carefully about that window (F-05, OQ-02) and concludes correctly that value
comparison "does not depend on timing at all" - but value comparison of the MERGED-FROM branch does not
establish authorship, which is the property the abort actually needs.

**AND A LOCALE-SAFE FIX IS ALREADY IN HAND, WHICH IS WHY THIS IS FIXABLE RATHER THAN A REPLAN
(PR-201's remedy).** The arm is reached only after the driver's own `git merge --no-ff` returned, whose
exit code is in scope. MEASURED: a merge that STARTS AND CONFLICTS returns rc=1; a merge git REFUSES TO
START because `MERGE_HEAD` already exists returns rc=128, reproduced against both a clean staged
foreign merge and a conflicted one. The exit code carries no language, so conjoining it with the branch
test satisfies `merge_in_progress`'s standing prohibition on matching git's English and keeps the
shipped locale test green. E-04 now requires that conjunction and E-05 gains a fifth case pinning the
impostor shape, to be shown RED against a branch-comparison-only implementation.

**THE PREDICATE'S NAME OVERSTATES WHAT IT PROVES (PR-202, MEDIUM).** Given PR-201, `owns_...` will
mislead the next reader into treating a True answer as authority to abort, which is exactly the mistake
the original E-04 made. E-02 now requires either a name for the property actually established or a
docstring opening with the limit stated in one sentence, and requires the choice recorded. This is not
cosmetic: the whole plan is a response to a predicate whose NAME ("is a merge in progress") was read as
a different claim ("did my merge start"), and shipping a second predicate with the same defect would
repeat the defect being fixed.

**E-04's "ONE CONDITION" INVITES A HALF FIX (PR-203, LOW, and it resolves in the plan's favor).** E-04
says to change "the conflict-arm condition", singular, while the block contains FOUR
`git merge --abort` calls (the re-derivation-commit-refused arm, the re-derivation-apply-failed arm, the
history-append-commit-refused arm, and the ordinary conflict refusal). Measured by indentation, all four
are nested strictly under the single `if merge_in_progress(repo):` guard (guard at indent 4; aborts at
16, 12, 12, 8), so narrowing the one guard DOES gate all four and the plan's instruction is correct as
written. It is recorded because an executor who greps for `merge --abort`, finds four, and changes only
the one E-04's prose evokes would ship a partial fix that passes case 1 and leaks on the re-derivation
arms.

**F-11's BASELINE IS ALREADY STALE AND IS USED AS A BAR TWICE (PR-204, LOW).** F-11 records
`2935 passed, 2 skipped` at HEAD `6a68f7fa`; measured `2937 passed, 2 skipped` at HEAD `821245a6`,
because main advanced between authoring and review. The Required tests section and V-05 both told the
executor to compare against the stale figure, which would manufacture a spurious discrepancy. Both now
require a re-derived same-commit baseline judged on failing node ids, which is what the execution
contract demands anyway.

**THE IMPOSTOR SHAPE WAS ABSENT FROM THE SCOPE BOUNDARY (PR-205, LOW).** The Scope check's under-scope
paragraph named two knowing limits, neither of them this one, so a reader would reasonably conclude the
plan had considered and excluded it. It is now stated as explicitly IN scope with its carrier items,
which is the honest position given PR-201's measurement.

Everything else checked and HELD. The plan's refusal to touch the lane-local aborts, to add a fourth
refusal kind, to tag a cause on the new reason, or to paste git stderr into it are all correct and
well evidenced. The octopus case E-02 mentions was verified to return False under the specified
implementation, correctly preserving a mixed merge. OQ-03's deferral is genuine, non-blocking and
carried by an existing item.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
| --- | -------- | ----- | ---- | -------- | ------- | ---------------- | -------- | ---------- |
| PR-201 | HIGH | IN-SCOPE | A. Correctness and data integrity / D. Anti-regression | MEASURED at HEAD `821245a6`: a human's `git merge --no-ff lane/probe` in main, conflicted, one path hand-resolved, plus a staged `human_only.txt` existing on no branch -> `MERGE_HEAD` == lane tip, the E-02 predicate returned **True**, and `git merge --abort` took `git diff --cached --name-only` from `['extra.txt','f.txt','human_only.txt']` to `[]`, deleted `human_only.txt`, and reverted `f.txt` to `main`. Separately measured: the driver's own merge returns **rc=1** started-and-conflicted, **rc=128** refused-because-`MERGE_HEAD`-exists (both a clean and a conflicted foreign merge) | **`MERGE_HEAD` PROVES WHICH COMMIT WAS MERGED, NOT WHO MERGED IT**, so the specified predicate answers True for a third party's merge of this lane's own branch and E-04 would abort it. That is the plan's own harm class, reachable through the exact race E-03 admits it cannot close. A locale-safe started-it signal (the merge's own exit code) is already in scope at that arm, so the remedy is a conjunction, not a redesign. | C:Low; U:Low; S:Medium; F:Medium; Overall:Medium | FIXED | E-04 now requires the abort to fire only on the CONJUNCTION of the branch match AND the started-it return code, with the measured rc values recorded and an explicit prohibition on falling back to text; E-05 gains case 5 (the impostor shape) which must be shown RED against a branch-comparison-only implementation; V-04 requires the conjunction quoted and the rc values pasted; V-05 requires the second deliberate-failure demonstration. New F-15, F-16. The approval gate and the silent-failure list both name it. |
| PR-202 | MEDIUM | IN-SCOPE | F. Self-documenting / G. Executability | PR-201's measurement; the plan's own origin, which is a predicate (`merge_in_progress`, "is ANY merge in progress") read as a different claim ("did MY merge start") | **THE NAME `owns_merge_in_progress` ASSERTS THE PROPERTY IT DOES NOT ESTABLISH**, so the next reader will treat a True answer as authority to abort - the identical misreading this plan exists to fix, reintroduced in a new symbol. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now requires either a name for the property actually proven (e.g. `merge_in_progress_is_of_branch`) or a docstring opening with the limit in one sentence, and requires the choice recorded; its Expected outcome demands the limit documented with the impostor case cited; V-02 requires the name, the limit sentence quoted, and the impostor measurement pasted as a True result. |
| PR-203 | LOW | IN-SCOPE | G. Executability | MEASURED by an indentation walk over `inspect.getsource(runner_shared.integrate_lane_branch)`: `if merge_in_progress(repo):` at indent 4; four `_run_git(repo, ["merge", "--abort"])` at indents 16, 12, 12, 8, all strictly deeper. Plan E-04 as authored: "Change the conflict-arm condition" | The block holds FOUR aborts, not one. The plan's single-guard instruction is CORRECT because all four nest under it, but the singular phrasing invites an executor who greps for `merge --abort` to change only one and ship a partial fix that passes case 1 while leaking on the re-derivation arms. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 gained an executor note stating the measured nesting and warning not to mistake "one condition" for "one abort"; V-04 requires a one-sentence confirmation with an indentation or diff citation that all four are gated. New F-17. |
| PR-204 | LOW | IN-SCOPE | E. Testing and verification | F-11 records `2935 passed, 2 skipped` at HEAD `6a68f7fa`; measured `2937 passed, 2 skipped` at HEAD `821245a6`. The Required tests section and V-05 both instructed comparison against the recorded figure | **THE COMPARISON BAR IS STALE AND WAS CITED TWICE**, so an executor following it would report a spurious discrepancy against a baseline from a different commit, contradicting the plan's own same-commit-baseline contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both sites now require a RE-DERIVED same-commit baseline judged on the delta of failing node ids, with F-11's figure explicitly named as not-the-bar. New F-18. |
| PR-205 | LOW | UNDER-SCOPE | G. Executability (scope honesty) | The Scope check's under-scope paragraph named two knowing limits, neither the impostor shape; PR-201's measurement shows that shape is reachable and mis-answered | The scope boundary read as though every residual had been enumerated, so a reader would conclude the impostor shape had been considered and excluded rather than not considered. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The under-scope paragraph now states the impostor shape is explicitly IN scope, names why (reachable through the race E-03 cannot close, and mis-answered by the branch comparison alone), and points at E-04's conjunction and E-05 case 5 as its cover. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
| --- | -------- | ------ | ----------------------- | ----- | ---------- |
| D-1 | PR-201: the specified ownership proof admits the plan's own harm class. REPLAN, or repair? | REPAIR by requiring a CONJUNCTION with the merge's own exit code. The plan's architecture (a positive proof, a pre-merge refusal, a narrowed abort, both-host tests) is right; only the sufficiency of one predicate was wrong, and the missing half is already in scope at the call site. | (a) REPLAN: rejected, four of five items stand unchanged and the fifth needs one added conjunct, so nothing structural is wrong. (b) Accept the residual and document it as a known limit: rejected - this plan's entire purpose is to stop the runner destroying unowned merge state, so shipping a version that still does so in a measured, reproducible shape would contradict its own goal. (c) Match git's "You have not concluded your merge" text instead of the exit code: rejected and explicitly prohibited in the revised plan, because `merge_in_progress`'s docstring records that git's English is localizable and version-dependent and the shipped suite drives both failure classes under a forced non-English locale, so a text test would regress it. (d) Pass a new parameter recording what this call did: rejected, `tests/test_runner_shared.py::test_each_wrapper_keeps_the_ORIGINAL_signature` pins that no wrapper may expose an injected parameter, so a signature change would break a shipped contract test - and it is unnecessary, since the exit code is already a local. | The measured impostor destruction at HEAD `821245a6`; the measured rc=1 versus rc=128 discrimination on both foreign shapes; `merge_in_progress`'s own docstring on text matching; the plan's Step 0 note recording the wrapper-signature contract test. | yes |
| D-2 | PR-202: rename the predicate, or keep the name and document the limit? | OFFER BOTH and require the choice to be RECORDED, rather than dictating one. | Dictating a rename: rejected as a naming decision the executor is better placed to make in context, and either route closes the misreading. Dictating "keep the name": rejected, the name is the more likely cause of the next misreading and a reviewer should not entrench it. What is NOT optional either way is that the limit be stated in the docstring, which is why that half is mandatory in both branches. | PR-201's measurement establishing the limit; the plan's own origin as a predicate-name misreading; `merge_in_progress`'s docstring as the house precedent for stating a limit in the symbol's own documentation. | yes |
| D-3 | PR-203: is the plan's single-guard instruction wrong, or merely risky to read? | MERELY RISKY: the instruction is CORRECT and is kept, with the measured nesting added as an executor note. | Rewriting E-04 to enumerate four condition changes: rejected as actively wrong - there is one guard and four nested aborts, so instructing four changes would invite an executor to add three redundant conditions or to restructure a block the plan elsewhere requires left byte-identical. | The measured indentation of the guard (4) against the four aborts (16, 12, 12, 8); E-04's own requirement that the re-derivation and history-append blocks stay byte-identical. | yes |

Every finding is `FIXED`; none is left `OPEN` or `DEFERRED`, so no escalation to a `- Blocking: yes`
question is owed and the repository's `HIGH` gate threshold is satisfied without one. PR-201 is `HIGH`
and was FIXED in place rather than escalated, which is correct under the Fix Bar: its overall
Remediation Risk is Medium (a bounded, local change adding one conjunct from a value already in scope,
whose discriminating signal was measured on both shapes), not Medium-High. No decision above is
`Reversible: no`. OQ-01 and OQ-02 remain `resolved` as authored and were checked; OQ-03 remains
`deferred` with its existing carrier `p7dtbr`, which exists on disk. No new open question is created.

### Verification performed at review

- `aw ipd lint --phase author --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- `aw ipd lint --phase review-finalize --agent <plan>` -> exit 0, `"outcome":"clean"`, `"findings":0`.
- No pre-review snapshot was owed: `git status --porcelain -- <plan>` was EMPTY before editing.
- **F-01 REPRODUCED EXACTLY, INCLUDING THE INCIDENT SIGNATURE.** Driving the real
  `runner_shared.integrate_lane_branch` with a third party's `git merge --no-ff --no-commit` staged in
  main: returned `integrated=False`, `kind='fail-merge'`, reason
  `[aw-integration-cause=git-merge-conflict][aw-conflict-shape=unknown] merge-back conflict; fatal: You
  have not concluded your merge (MERGE_HEAD exists).`; staged set `['other.txt']` -> `[]`; index tree
  `ce351df8d485` -> `1ed80cf6e3df`; `MERGE_HEAD` GONE; newest reflog entry `'reset: moving to HEAD'`;
  and the argv trace ended in `['merge', '--abort']`.
- **F-03 REPRODUCED ON ALL THREE PROBES** against that same fixture: `merge_write_set(repo,
  'lane/probe')` -> `['lanefile.txt']`, `dirty_tree_overlap(repo, ['lanefile.txt'])` -> `[]`,
  `conflicted_paths(repo)` -> `[]`. So every existing pre-merge guard reports CLEAR.
- **F-06 REPRODUCED.** An octopus `git merge --no-commit --no-ff b1 b2`: the `MERGE_HEAD` file read via
  `git rev-parse --git-path` held TWO ids (`622f583b365d`, `eb5c580027da`) while
  `git rev-parse MERGE_HEAD` printed ONE line (`622f583b365d`). So E-01's prohibition is well founded.
- **F-04 REPRODUCED, AND THE GENUINE-CONFLICT SIDE CHECKED EXPLICITLY** because it is what keeps
  today's abort working after E-04's narrowing: in the genuine conflict `MERGE_HEAD` == the lane tip
  exactly (`af0f4d0e17a5`), `conflicted_paths` -> `['f.txt']`, so the all-entries-match test is True
  there.
- **E-01's LINKED-WORKTREE CLAIM REPRODUCED.** In a linked worktree mid-merge: `<wt>/.git` IS a file;
  `git rev-parse --git-path MERGE_HEAD` resolved into `<common>/.git/worktrees/wt_linked/MERGE_HEAD`
  and that path EXISTS; `<wt>/.git/MERGE_HEAD` does NOT exist; the `--git-path` read returned the
  correct id. Also measured and worth recording: `merge_in_progress(<linked worktree>)` is True while
  `merge_in_progress(<primary>)` is False for the same merge, so the two trees' merge states are
  independent.
- **THE OCTOPUS-WITH-A-FOREIGN-PARENT CASE E-02 NAMES** was verified under the specified
  implementation: `MERGE_HEAD` = `['12530467a751', '185e5eff685f']`, lane tip `12530467a751`, predicate
  **False**, so the mixed merge would be routed to the foreign arm and preserved. E-02's `all`
  quantifier is correct.
- **PR-201, THE IMPOSTOR MEASUREMENT.** A human's `git merge --no-ff lane/probe` in main: rc=1,
  `MERGE_HEAD` = `['61150aab3b6c']` == lane tip `61150aab3b6c`, predicate **True**. After the human
  hand-resolved `f.txt` and staged `human_only.txt`: `git diff --cached --name-only` =
  `['extra.txt', 'f.txt', 'human_only.txt']`, `git write-tree` = `4906736ae27b`. After
  `git merge --abort`: staged = `[]`, `human_only.txt` no longer exists, `f.txt` reads `'main\n'`.
- **PR-201's REMEDY MEASURED ON BOTH SHAPES.** Started-and-conflicted: `git merge --no-ff` rc=**1**,
  `merge_in_progress` True, stderr empty. Refused-because-`MERGE_HEAD`-exists: rc=**128**,
  `merge_in_progress` True, stderr `'fatal: You have not concluded your merge (MERGE_HEAD exists).'`
  (reproduced against a CLEAN staged foreign merge, rc=0 to stage, and against a conflicted one).
- **PR-203, THE ABORT COUNT AND NESTING.** `grep` finds four `_run_git(repo, ["merge", "--abort"])`
  inside `integrate_lane_branch`; an indentation walk places the guard at indent 4 and the four aborts
  at 16, 12, 12 and 8, all strictly deeper, so the single-guard narrowing gates all four.
- **E-03's SITE VERIFIED.** Within `integrate_lane_branch`'s source: the `dirty_tree_overlap` call is
  at relative line +102, `execute_merge_and_revalidate_gate` at +122, the `--ff-only` merge at +153,
  the `--no-ff` merge at +155 and the post-merge guard at +198. So "after the dirty guard and before
  the gate" is a real, unambiguous location.
- **PR-204, THE BASELINE.** Bare `python3 -m pytest` at HEAD `821245a6` -> `2937 passed, 2 skipped,
  3 warnings` with the standard `201 tests were deselected` notice, against F-11's recorded
  `2935 passed, 2 skipped` at HEAD `6a68f7fa`.
- **F-07 CONFIRMED.** `integration_lock_path` and `concurrent_driver_consent` both exist;
  `integrate_under_repository_lock(` appears at 11 call sites in `runner_shared`;
  `tests/test_concurrent_driver_guard.py` exists. So the driver-versus-driver window is closed by the
  lock and the consent hole is real and deliberately out of scope, as F-07 states.
- **F-13 CONFIRMED.** The `record_refusal` write site is guarded by
  `if cause == INTEGRATION_CAUSE_GIT_CONFLICT:` and the surrounding comment records the
  no-redaction constraint verbatim, so an untagged transient reason cannot reach that writer.
- **CITED SURFACES AND CARRIERS ALL EXIST.** `tests/test_runner_shared.py::LaneIntegrationBehaviorTests`
  and its `_git_trace` helper;
  `tests/test_merge_conflict_sendback.py::test_case_3_called_with_merge_in_progress_refuses_without_second_merge`;
  all four files named in Required tests; backlog `p7dtbr` at
  `.aw/records/backlog/open/20260928-p7dtbr-01-p7dtbr-poll-rung-cannot-see-merge-in-progress.backlog.md`
  and `csmtjp` at `.aw/records/backlog/graduated/20260917-csmtjp-01-csmtjp-abort-destroys-a-concurrent-merge.backlog.md`.
  `tests/test_foreign_merge_refusal.py` does not yet exist, as expected for a pending plan.
- Post-revision suite re-check: `python3 -m pytest` -> `2937 passed, 2 skipped, 3 warnings in 88.74s
  (0:01:28)`, the same pass/skip counts as the baseline above, confirming this review touched no code
  (it edited only the plan and this record). The wall time differs from the baseline run because the
  machine was concurrently loaded; the counts are the signal, not the duration.
- `aw sanitize --agent` -> exit 0, no findings.

### Probe scripts

The four probe scripts backing these measurements were written under
`.aw/workflow-artifacts/plan-review-g2z2pp/` (gitignored, so not committed): `probe_foreign.py` (the
F-01 destructive reproduction with the argv trace and index-tree comparison, the three blind guards,
and the abort count and nesting), `probe_predicate.py` (F-06's octopus truncation, the
genuine-conflict `MERGE_HEAD` value, and the linked-worktree resolution), `probe_fix.py` (E-01/E-02
implemented as specified, E-03's site located, the octopus-with-foreign-parent case, and the impostor
destruction), and `probe_residual.py` (the reachability argument and the rc=1 versus rc=128
discrimination).
