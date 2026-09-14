# Review: retire an orchestrator in a coordinator-owned throwaway worktree, child u23gbn (Set dirtygates)

- Subject-Id: u23gbn
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Rounds: 3 (the CURRENT round is the last one written; the findings gate reads it alone)

## Round 1

Reviewed at HEAD `b16e1108`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review. At `--phase review-finalize` the linter reports exactly one finding,
`IPD-Q501` for the blocking OQ-03 this review raised, which is the gate working as designed and is the
same disposition Orders 01 and 02 carry.

DISCLOSURE: same repository and same model family as the author, so this is close to a self-review and
worth less than an independent one. Its value therefore rests on what was DRIVEN rather than re-read.
Measured here: a real rollup retirement instrumented and sampled at two instants; the `after_move`
fault-injection rollback reproduced end to end; the proposed worktree-plus-CAS mechanism BUILT BY HAND
in scratch repos and its resulting shared-tree state measured, including the `--ff-only` reconciliation
in both its clean and contended forms; a detached worktree probed for whether it receives a gitignored
generated file; the `_finalize_transaction` caller set enumerated by grep; the corpus counted for actual
retirements against executed orchestrators; and the drift test that guards the index gate read to see
what it actually asserts.

THE PLAN'S DIAGNOSIS IS CORRECT AND REVIEW CONFIRMED IT INDEPENDENTLY. The maintainer's challenge to
the atomicity claim was right, and the window is not merely inferable from the phase names: sampling
`git status --porcelain` inside a successful retirement gave `RM pending/<plan> -> executed/<plan>` at
the post-move instant and `R  <same>` plus two untracked manifests at the pre-commit instant (new
F-1a). F-3's rollback residue reproduced exactly as the plan describes. The worker-role analysis (F-5),
the journal-is-recovery-not-atomicity distinction (F-2), and F-3a's own honest severity qualifier all
held up and were left alone.

THE FINDING THAT STOPS THE PLAN IS A BLAST RADIUS IT NEVER DECLARES. Every mechanism the plan proposes
lives in `_finalize_transaction`, which is SHARED CODE with exactly two callers: `finalize` and
`retire_orchestrator`. So the plan is titled and scoped as being about orchestrator retirement while in
fact proposing to change the terminal transition for every plan in the repository, or else to fork a
second transaction body, which is exactly the drift spec `77tr3o` OQ-1 recorded as its ACCEPTED COST.
The plan never states which it intends. That is not a gap a reviewer should close by choosing: it
decides the blast radius of the most load-bearing write in the toolkit, and one branch of it is not
cleanly reversible. Escalated as blocking OQ-03 with both options costed.

THE CENTRAL MECHANISM ALSO DOES NOT DELIVER ITS OWN STATED ACCEPTANCE, which is the finding that most
changed the plan's text. Built by hand: a worktree commit landed by bare CAS leaves the shared checkout
reading `R  p/executed/plan.md -> p/pending/plan.md`, dirty in the INVERSE direction, because HEAD now
holds the new path while the working tree still holds the old one; adding `commit_isolated`'s own
trailing `git reset` yields ` D p/executed/plan.md` plus `?? p/pending/` instead. So "the shared
checkout is never mutated" is unobtainable, V-01's demanded proof could never have been produced, and an
executor pursuing it would either fake the evidence or force the tree. The same measurement supplied the
honest mechanism: `git merge --ff-only` applies the rename while leaving an unrelated peer's dirt
untouched, and REFUSES (rc=1, peer bytes preserved) when a local change to the moved file would be
overwritten. New E-06 adds that step, V-06 pins both arms, and the plan's Goal now says plainly that the
window shrinks rather than vanishes.

ONE OPEN QUESTION WAS RESOLVED AGAINST THE AUTHOR'S OWN PREFERENCE, on measurement. OQ-02 preferred
regenerating the plans manifests inside the throwaway worktree, calling it the stronger property. It
breaks the SUCCESS path: both manifests are gitignored, a detached worktree does not receive them, a
regeneration there is discarded with the worktree, and the shared copies keep stale bytes, which turns
`aw index plans --check` into a `check.stale-index-stale` finding whose registered severity is
`warning` and therefore fails the gate. Worse, it would de-facto remove `plans-index-refresh-fail-loud`
from the shared tree while the test guarding that gate still passed, because the test asserts only that
the gate's NAME appears in a tuple. E-03 now restores prior bytes on rollback and leaves the success
path alone.

TWO VALIDATION ITEMS WERE SATISFIABLE WITHOUT DOING THE WORK, which is the class of defect most worth
catching before execution. V-03 demanded a repository-level `git status` be empty before and after; both
manifests are gitignored HERE, so it is empty either way and the residue is visible only in the fixture,
so V-03 could have passed against unchanged code. And E-05 prescribed observing a SUCCESSFUL retirement
through the fault-injection hooks, which raise and abort by construction, so the prescribed technique
cannot produce the evidence its V-item demands. Both now name the observation seam and the level at
which the property is actually visible.

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-401 | BLOCKER | IN-SCOPE | C (architecture), G (executability) | `ipd_lifecycle.py:2559` with its only callers at `:2544` and `:2405`; spec `77tr3o:220-227` | THE BLAST RADIUS IS UNDECLARED. Every mechanism the plan proposes lives in `_finalize_transaction`, shared by `finalize` (every ordinary plan, `aw ipd finalize`, `aw set executed`) and `retire_orchestrator`. Changing it in place alters the terminal transition for 500+ plans, not the 4 rollup retirements the plan's own F-6 implies; confining the change forks a second transaction body, which is precisely the drift spec `77tr3o` OQ-1 accepted as a known cost. The plan never says which it intends, and its title and Scope imply a narrowness its mechanisms do not have. | C:High; U:Low; S:Medium; F:High; Overall:High | OPEN | Escalated as blocking OQ-03 with both options costed and their consequences named. E-01/E-02/E-05/E-06 gated on the answer; E-03/E-04 explicitly ungated so a ruling either way leaves executable work. Spec-sync section now states that a "fork" ruling REQUIRES amending `77tr3o` in this plan. New F-8. |
| PR-402 | BLOCKER | IN-SCOPE | A (correctness), E (testing) | measured at review: bare CAS leaves `R  p/executed/plan.md -> p/pending/plan.md`; with `commit_lock.py:281-284`'s reset, ` D p/executed/plan.md` + `?? p/pending/` | THE MECHANISM CANNOT DELIVER E-01's ACCEPTANCE OR THE PLAN'S GOAL. "No edit, move, or commit in the shared checkout; main advances by one ref update" leaves the working tree holding the plan at its OLD path while HEAD holds the new one, i.e. dirty in the inverse direction, which reads as an unexplained reverse rename and is worse than the in-progress move it replaces. V-01 demanded proof of that unobtainable property, so an executor would have had to fabricate evidence or force the tree. | C:Medium; U:Low; S:Medium-High; F:High; Overall:Medium-High | FIXED | Goal rewritten to shrink-not-eliminate with the reason stated; E-01's expected outcome weakened to what it can deliver and annotated with why; new E-06 adds the measured `--ff-only` reconciliation (clean case preserves peer dirt, contended case REFUSES rc=1 preserving peer bytes) with an explicit prohibition on `checkout -f`/`reset --hard`/manual move; new V-06 pins both arms; V-01 rewritten to a comparison rather than an emptiness assertion. New F-7. |
| PR-403 | HIGH | IN-SCOPE | A (correctness), C | `.aw/.gitignore:45-46`; a fresh detached worktree measured NOT to receive a gitignored generated file; `check_engine.py:336`; `tests/test_orchestrator_retirement.py:2079`, `:2104` | OQ-02's PREFERRED ROUTE BREAKS THE SUCCESS PATH. Regenerating the manifests in the throwaway worktree discards them with the worktree and leaves the shared copies stale, so `aw index plans --check` reports `check.stale-index-stale` (registered `warning`, which fails the gate), and `plans-index-refresh-fail-loud` is de-facto removed from the shared tree while the test guarding it still passes because that test only checks the gate's NAME. | C:Low; U:Low; S:Low; F:Medium-High; Overall:Medium | FIXED | OQ-02 resolved AGAINST the author's preference with the measurement as basis; E-03 now restores prior bytes from the journal and keeps the success path's shared-tree regeneration, and covers the deleted-before case (a fresh clone has neither manifest). A live-gate check (`aw index plans --check` clean after a success) added to Required tests and V-06. New F-9. |
| PR-404 | HIGH | IN-SCOPE | E (testing) | `git check-ignore -v .aw/records/plans/INDEX.json`; `git ls-files --error-unmatch` reports both untracked; the plan's own F-3a | V-03 WAS SATISFIABLE WITHOUT ANY FIX. It demanded `git status --porcelain` be empty before and after, but both manifests are gitignored in THIS repository, so a repo-level status is empty whether or not E-03 is implemented; the residue is observable only in the test fixture. The plan's F-3a already knew this and V-03 did not reflect it. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | V-03 now requires the FIXTURE-level observation, states why the repo level is insufficient, and adds the deleted-before case. E-03's expected outcome re-worded to the fixture level. |
| PR-405 | HIGH | IN-SCOPE | E (testing) | `_fault` raises `_InjectedFault` at `ipd_lifecycle.py:2593-2595`, class at `:154-155` | E-05'S PRESCRIBED TECHNIQUE CANNOT PRODUCE ITS EVIDENCE. It said to observe a SUCCESSFUL retirement using "the fault-injection hooks `after_move` and `before_commit`", but fault injection raises and aborts the transaction, so by construction it can only observe a FAILED one. The V-item would then be unsatisfiable as written and an executor would improvise or overclaim. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-05 now names the seam review actually used (patch `_refresh_plans_index_fail_loud` and `commit_lock.commit_isolated`, delegating to the real functions), requires a before/after comparison against F-1a's baseline rather than an absolute cleanliness claim, and requires the remaining residue be enumerated in the test's docstring. V-05 requires confirmation that fault injection was NOT used for these instants. |
| PR-406 | MEDIUM | OVER-SCOPE | G (plan executability) | `Scope-Paths` as authored vs every E-item; `runner_shared.py:3258` cited only by F-6 | `agent_workflows/runner_shared.py` was declared in `Scope-Paths` with no E-item touching it. Its only appearance is F-6's citation of `dispatch_orchestrator_item`, a call site this plan does not change. A declared-but-unmodified path costs the executor a `--scope-ack` at finalize for nothing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed from `Scope-Paths`. Scope check records the removal and its reason, and separately records that E-04 must ADD `tests/test_ipd_lifecycle_cli.py` in the pass that makes the declaration true. |
| PR-407 | MEDIUM | IN-SCOPE | G (honest documentation), spec sync | spec `77tr3o:170-183` (R-4/R-5/R-6) vs `:220-227` (OQ-1's accepted cost) | THE SPEC-SYNC SECTION CITED THE WRONG REQUIREMENTS. It named R-4/R-5/R-6, which govern the transition's honesty, the E/V checkpoint and the receipt, none of which this plan touches. The text that actually governs is OQ-1's recorded accepted cost, which instructs that the rollup keep every gate the main path applies and that a test pin it, and that is exactly what PR-401 and PR-403 are about. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Spec-sync section rewritten to cite OQ-1's accepted cost as the governing text, and to state that a "fork" ruling on OQ-03 REQUIRES amending the spec in this plan with the spec file added to `Scope-Paths` first. |
| PR-408 | LOW | IN-SCOPE | G (honest documentation) | corpus grep: 4 plans carry a rollup retirement history line against 41 `Kind: orchestrator` plans in `executed/` | F-6 CLAIMED "cheap and frequent, so the window is hit often". The cheap half is true; the frequency half is not. Only 4 retirements exist in the whole tracked corpus. Overstating exposure inflates the plan's apparent urgency relative to its `Priority: medium`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-6 rewritten with the measured counts and an explicit note that the window is real but rarely entered, which is consistent with this plan being `medium` while its siblings are `high`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The plan proposes changes to `_finalize_transaction` without saying whether the shared body changes or a rollup-specific copy is made. Should review pick one? | No. Raise it as blocking OQ-03 with both options costed, and gate the four affected E-items on the answer. | Assume the narrow reading (fork a rollup path) and review the mechanics, since the plan's title and Scope imply it; or assume the broad reading (change the shared body) because that is where the code actually is. | `ipd_lifecycle.py:2559` has exactly two callers (`:2544`, `:2405`), so the two options differ by 500+ plans of blast radius versus a second transaction body that spec `77tr3o:220-227` names as an accepted-but-minimized cost. AGENTS.md reserves scope and risk-appetite calls to the maintainer, and the broad option is not cleanly reversible once every plan's transition has moved. | no |
| D-2 | E-01's stated acceptance ("no edit, move, or commit in the shared checkout") is unobtainable. Weaken the plan's claim, or add a step to make the claim true? | Both, honestly: weaken the Goal and E-01 to what a ref update can deliver, AND add E-06's reconciliation so the end state is better than today rather than differently broken. | Leave the claim and let the executor discover it (which would invite fabricated evidence or a forced tree); or add the reconciliation while keeping the stronger wording. | Measured: bare CAS leaves `R  p/executed/plan.md -> p/pending/plan.md` and the `commit_isolated` reset variant leaves ` D` plus `??`, so the shared tree must be reconciled either way; `git merge --ff-only` was measured to do it while REFUSING rather than clobbering a peer's change. | yes |
| D-3 | How should E-06 handle a reconciliation that git refuses? | Report it as `PHASE_COMMITTED_INCOMPLETE` naming the objecting paths, and forbid forcing. | Force the tree into line (`checkout -f` / `reset --hard` / manual move); or roll back the landed commit. | Git's refusal is protecting a co-worker's uncommitted bytes (measured: the peer's content survived intact), which AGENTS.md's shared-checkout rule forbids destroying; and `_resume_post_commit` (`:2884-2891`) already establishes that a landed lifecycle commit is resumed, never rolled back. | yes |
| D-4 | OQ-02 asks whether to regenerate the manifests in the worktree or restore them from the journal. The author prefers the worktree. Resolve it, or leave it for the maintainer? | Resolve it from evidence, AGAINST the author's preference: restore from the journal. | Leave it open as authored (it was marked non-blocking); or follow the author's stated preference. | Measured: a detached worktree does not receive a gitignored generated file, so the worktree route leaves the shared manifests stale, which trips `check.stale-index-stale` at `warning` severity (`check_engine.py:336`) and silently voids the `plans-index-refresh-fail-loud` gate while its string-only test still passes. That is a correctness answer, not a preference. | yes |
| D-5 | E-04 pins tree preservation in the rollup fault tests. Should the identical hole in the ordinary finalize tests be in scope? | Yes. Require the same assertion in `tests/test_ipd_lifecycle_cli.py:968` and `:983`, with the file added to `Scope-Paths` in that pass. | Leave the sibling suite alone as out of scope, and file a separate item. | `_rollback_precommit` is shared code with both suites exercising it, so pinning the property on only one caller leaves the other free to regress the exact defect F-3 records; the addition is two assertions in existing tests, which the Fix Bar rates Low remediation risk. | yes |

D-1 is `Reversible: no` and is ESCALATED as the workflow requires: raised in the reviewed plan as OQ-03
carrying `- Blocking: yes` and `- Finding: PR-401`, so `aw ipd lint` refuses the plan at every
checkpoint until the maintainer answers (verified: `IPD-Q501` at `--phase review-finalize`). It is the
architectural counterpart of the orchestrator's OQ-02 and of Order 02's OQ-03, narrowed to the
transaction body.

## Round 3

Reviewed at HEAD `5b0396b0`. Structural preflight `aw ipd lint --phase author` CONFORMED (clean, 0
findings) before semantic review, and conformed again after the E-07/E-08 additions once their V-items
were added (the linter caught the missing bijection itself, `IPD-I303` twice, which is the gate working).
At `--phase review-finalize` it now reports exactly one finding, `IPD-Q501` for the blocking OQ-04 this
round raised, which is the intended disposition for an escalated question.

DISCLOSURE: same repository and same model family as the author, so this remains close to a self-review.
Its value rests on what was DRIVEN. Measured this round, all against real code rather than scratch
analogues: F-1a's baseline reproduced by instrumenting a real successful retirement in the repository's
own fixture; `commit_isolated` CALLED with a mutation staged in a separate coordinator worktree, to see
what it actually does; the whole proposed sequence built end to end (worktree mutate, worktree commit,
no ref advance, ff-only merge) and its shared-tree result measured; a third merge arm (peer COMMIT rather
than peer edit) measured for its exit code; `_refresh_plans_index_fail_loud` run at the position the new
ordering would put it in and the manifest then checked; `_rollback_precommit` CALLED with a
worktree-shaped journal against a peer edit; the `commit_isolated` and `offer_commit` caller sets
enumerated by grep; and both required suites run for real counts.

ROUND 2'S FIXES HELD. The corrected ff-only-as-the-advance ordering (F-10) is right, and this round
re-measured its clean and contended arms and confirmed both. The OQ-03 propagation (PR-014) and the
E-03/E-04 re-assignment (PR-015) were correctly applied. Nothing from round 2 was reopened.

THE FINDING THAT WOULD HAVE STOPPED EXECUTION IMMEDIATELY IS PR-021, AND IT WAS FOUND BY CALLING THE
FUNCTION RATHER THAN READING IT. E-01's central instruction was "the existing pattern to reuse is
`commit_lock.commit_isolated`". It cannot be reused, and not for the CAS-ordering reason round 2
identified: `commit_isolated` copies each named path FROM the shared tree INTO its own worktree
(`commit_lock.py:226-231`) and propagates a deletion when the shared source is absent (`:232-234`). Its
direction is shared -> worktree, so a mutation made in a coordinator-owned worktree is invisible to it.
Called exactly as E-01 prescribes, it returned `error` / "git add failed in isolated worktree: fatal:
pathspec 'p/executed/plan.md' did not match any files", HEAD unmoved, nothing committed. An executor
following E-01 literally would have hit this in the first hour. The sound shape was then built and
measured end to end and is now written into E-01.

THE TWO FINDINGS THAT MATTER MOST ARE DEFECTS THE PLAN'S OWN CHANGE CREATES, AND BOTH WERE OWNED BY
NOBODY. This is the class this review exists to catch, because each would have shipped as a silent
regression inside a change whose stated purpose is to make the repository safer.

PR-022 (F-12): the relocation INVERTS the `plans-index-refresh-fail-loud` gate from a guard into a false
pass. `_refresh_plans_index_fail_loud` regenerates the manifests by scanning the plans tree ON DISK
(`plans_index.scan_plans` walks `rglob("*.md")`) and it runs inside the mutating phase, AFTER today's
shared-tree `git mv`. Move the relocation into the worktree and the shared disk still shows the plan at
`pending/`, so the manifest is generated describing the OLD layout, converges against it, and the gate
PASSES; the ff-only merge then relocates the file and the manifest is instantly stale. MEASURED: the
manifest contained the `pending/` path and not the `executed/` one, and `aw index plans --check` returned
rc=1 reporting `check.stale-index-stale` on both manifests at `warning` severity, which fails the gate.
So the transaction would report success while leaving precisely the state the gate exists to prevent.
`ROLLUP_SHARED_GATES` (`:2066`) declares the rollup KEEPS this gate and spec `77tr3o` OQ-1 requires a
test to pin that it does; round 1's F-9 already established the guarding test checks only the gate's
NAME, so this loss would have been invisible. New E-07 and V-07.

PR-024 (F-14): the rollback becomes a peer-data-destroying write, which is the exact harm this Set
exists to stop. Step 2 of `_rollback_precommit` (`:1910-1920`) unconditionally writes the snapshot bytes
over the plan's original path. Correct today, because this transaction is the party that moved that file
away. Once the relocation happens in the worktree the shared-tree file is never touched, so the same
write becomes an unconditional overwrite of whatever a peer has there. Note the asymmetry that makes it
reachable: step 1 (`:1888-1908`) DOES guard the destination against `moved_bytes` and refuses a
destructive restore on mismatch; `original_path` has no guard because until now it needed none. MEASURED
against the real function with a worktree-shaped journal: before `'- Status: approved\nPEER EDIT IN
FLIGHT, uncommitted\n'`, after `'- Status: approved\nORIGINAL\n'`. The peer's bytes were gone. The call
then returned `ok=False` for an unrelated fixture reason, which is itself the sharper point: the
destructive write is not undone by the later failure, so even a rollback that REPORTS failure has
already destroyed the edit. New E-08 and V-08.

A THIRD RECONCILIATION ARM WAS MISSING (PR-023, F-13). E-06 measured a clean case and a contended one.
If a peer COMMITS to main between the worktree snapshot and the merge, no fast-forward exists at all:
`git merge --ff-only` exits 128 (not the 1 of the overwrite refusal) with "fatal: Not possible to
fast-forward", HEAD unmoved, the landed commit not an ancestor of HEAD, and the shared tree CLEAN. That
is materially different from the contended arm and is exactly what `commit_isolated` already calls
`ISO_RACED`, so the existing vocabulary should be reused. E-06 and V-06 now require the arms be
distinguished by exit code and tree state, never by string-matching git's prose.

ONE STALE OBLIGATION AND ONE WRONG COUNT (PR-025). Round 2 correctly established this plan needs
`tests/test_ipd_lifecycle_cli.py`, but left it as a prose instruction to add the path during execution
rather than declaring it. That is a trap: `Scope-Paths` is inside the frozen region
(`frozen_region_digest`, `:495-503`), so editing it mid-execution invalidates the begin receipt and
`finalize_precheck` refuses as STALE (`:1476-1483`). Declared now, together with the two files F-11
makes unavoidable. The suite count was also wrong: measured 57, not 58.

THE BLOCKING QUESTION IS NEW AND IS THE DIRECT DESCENDANT OF OQ-03. Fixing `commit_isolated` means
either extending it in place (it also backs `git_commit_helper.offer_commit`, the single shared commit
path behind 7 call sites across 8 modules, which AGENTS.md documents as "immune by construction" to
sweeping a co-worker's work into a commit) or adding a sibling and accepting a second implementation of
the CAS and its `ISO_RACED` honesty. OQ-03's precedent argues for extending in place; OQ-03's own
REASONING, that invisible divergence is the danger, argues against putting a documented safety guarantee
at risk to avoid one extra function. A reviewer must not pick that. Escalated as OQ-04, `Blocking: yes`,
gating every item in the plan (all of them depend on E-01 directly or transitively).

No product code was modified by this review.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-021 | BLOCKER | IN-SCOPE | C (architecture), G (executability) | `commit_lock.py:226-234` (copy direction), `:270` (the CAS); measured `error` / "pathspec 'p/executed/plan.md' did not match any files"; callers `ipd_lifecycle.py:2752` and `git_commit_helper.py:595` | E-01'S CENTRAL "REUSE `commit_isolated`" INSTRUCTION IS NOT IMPLEMENTABLE. The helper copies each named path FROM the shared tree INTO its own worktree and propagates a deletion when the shared source is absent, so its direction is shared -> worktree and a mutation made in a coordinator-owned worktree is invisible to it. Called as E-01 prescribes it committed nothing and returned an error. This is stronger than round 2's CAS-ordering tension (F-10): the helper cannot see the work at all. Fixing it means either extending the function that also backs `offer_commit` (every `aw` self-commit) or adding a sibling that duplicates the CAS and `ISO_RACED`. | C:High; U:Low; S:Medium; F:High; Overall:High | OPEN | E-01 rewritten with the measured sound shape (commit in the coordinator's own worktree, stage only paths that exist, do NOT advance the ref, let E-06's ff-only merge advance it) which was verified end to end. New F-11. `commit_lock.py` and `tests/test_isolated_commit.py` added to `Scope-Paths`. The fork-or-extend decision ESCALATED as blocking OQ-04 with both costs measured; not a reviewer's call. |
| PR-022 | BLOCKER | UNDER-SCOPE | A (correctness), D (anti-regression), E (testing) | `_refresh_plans_index_fail_loud` `:1656-1695` called at `:2700`; `plans_index.py:99` (`rglob` scan); measured `check.stale-index-stale` on both manifests, rc=1; severity `check_engine.py:336`; gate declared `:2066`; string-only test `tests/test_orchestrator_retirement.py:2079`,`:2104` | THE RELOCATION INVERTS A DECLARED GATE INTO A FALSE PASS, AND NO ITEM OWNED IT. The index refresh scans the plans tree on disk inside the mutating phase, after today's shared-tree `git mv`. Once the relocation moves to the worktree, the shared disk still shows `pending/`, so the manifest is generated for the OLD layout, converges, and the gate PASSES; the merge then makes it stale. Measured: manifest names the `pending/` path not the `executed/` one, `aw index plans --check` rc=1 with `check.stale-index-stale` (`warning`, fails the gate). The transaction reports success while leaving the exact state the gate prevents, and per F-9 the guarding test keys on the gate's NAME so the loss is invisible. Spec `77tr3o` OQ-1 requires a test to pin that the rollup keeps every gate the main path applies. | C:Medium; U:Low; S:Low; F:High; Overall:Medium | FIXED | New E-07 moves the refresh to AFTER the reconciliation, keeps it fail-loud, and requires a post-commit refresh failure be classified committed-incomplete rather than rolled back (a landed commit is resumed, never reverted, `:2884-2891`). New V-07 demands the before/after manifest samples AND proof the gate still refuses. New F-12. Goal and Scope updated to carry the obligation. |
| PR-023 | HIGH | UNDER-SCOPE | A (correctness), E (testing) | measured: `git merge --ff-only` rc=128, "fatal: Not possible to fast-forward, aborting", HEAD unmoved, `merge-base --is-ancestor` false, `git status --porcelain` empty; `commit_lock.py:270-279` | A DIVERGED BRANCH IS A THIRD ARM E-06 DID NOT MEASURE. E-06 covered clean and contended (peer edits the moved file). A peer COMMIT landing between the worktree snapshot and the merge leaves no fast-forward at all, exiting 128 rather than 1, with a CLEAN tree and the plan still at `pending/`. That is a different condition from the overwrite refusal and needs its own classification; it is precisely `ISO_RACED`. Distinguishing the arms by git's prose would be fragile since the prefixes differ (`error:` vs `fatal:`). | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | E-06 gains the third arm with its measured exit code and the instruction to reuse the `ISO_RACED` vocabulary and classify by exit code plus tree state. Expected outcome and V-06 both extended. Required tests gains the diverged case. New F-13. |
| PR-024 | BLOCKER | UNDER-SCOPE | A (correctness), B (data integrity), D | `_rollback_precommit` unguarded write `:1910-1920` vs its guarded twin `:1888-1908`; measured before `'...PEER EDIT IN FLIGHT, uncommitted\n'` / after `'...ORIGINAL\n'` | THE ROLLBACK BECOMES A PEER-DATA-DESTROYING WRITE, THE EXACT HARM THIS SET EXISTS TO STOP. Step 2 unconditionally writes the snapshot bytes over the plan's original path, which is correct only because this transaction is the party that moved that file away. Once the relocation happens in the worktree the shared file is never touched, so the write becomes an unconditional overwrite of a peer's content. Step 1 guards the destination against `moved_bytes`; `original_path` has no guard because until now it needed none. Measured: the peer's bytes were destroyed. The write is not undone by the later failure, so even a rollback that REPORTS failure has already destroyed the edit. | C:Low; U:Low; S:Medium-High; F:High; Overall:Medium | FIXED | New E-08 gives `original_path` the same guard the destination has, makes "leave it alone" the default under the new sequence, refuses with unknown-outcome naming the path on mismatch, and forbids undoing a landed merge. New V-08 requires the peer's bytes shown identical before and after AND the pre-fix baseline, so the item is not satisfiable by a fixture that never had a peer edit. New F-14. Named in the gate as a must-ship-with-E-01 condition. |
| PR-025 | MEDIUM | IN-SCOPE | G (executability), evidence accuracy | `frozen_region_digest` `:495-503`, `finalize_precheck` stale refusal `:1476-1483`; measured `57 passed` for `tests/test_ipd_lifecycle_cli.py`, `112 passed` for `tests/test_orchestrator_retirement.py` | A STALE SCOPE OBLIGATION AND A WRONG COUNT. Round 2 established this plan needs `tests/test_ipd_lifecycle_cli.py` but left it as an instruction to ADD to `Scope-Paths` during execution. That is a trap rather than a chore: `Scope-Paths` is inside the frozen region, so editing it mid-execution invalidates the begin receipt and finalize refuses as STALE. Separately the plan claimed 58 tests in that suite; the real count is 57. | C:Low; U:Low; S:Low; F:Medium; Overall:Low | FIXED | `Scope-Paths` now declares all five files the E-items touch (the two F-11 forces plus the CLI suite). The execution-contract paragraph records the obligation as DISCHARGED and explains why a mid-execution scope edit is the wrong remedy. Count corrected to 57 with an instruction to re-measure and a note that `-o addopts=""` is required to see per-file counts. Scope check's under-scope note closed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-6 | `commit_isolated` cannot be reused (F-11). Should review pick between extending it and adding a sibling? | No. Raise it as blocking OQ-04 with both options costed, and gate every item on the answer. | Extend it in place, following OQ-03's precedent that one implementation beats two whose drift is invisible; or add a sibling, keeping `offer_commit`'s path provably untouched. | `commit_isolated` has two callers (`ipd_lifecycle.py:2752`, `git_commit_helper.py:595`), the second being `offer_commit`, the shared commit path behind 7 call sites across 8 modules that AGENTS.md documents as immune by construction to sweeping a co-worker's work into a commit. OQ-03's precedent points one way and its reasoning the other, so the two arguments genuinely conflict and the choice is a risk-appetite call AGENTS.md reserves to the maintainer. | no |
| D-7 | The index-gate inversion (F-12): fix it in this plan, or file it separately since it is arguably a pre-existing ordering assumption? | Fix it here, as new E-07. | File a separate backlog item and let this plan ship the relocation alone; or leave it to Order 06, which already touches index residue. | The defect does not exist today: it is CREATED by this plan's E-01, so it is this plan's regression and nobody else's. Shipping E-01 without it leaves `check.stale-index-stale` unreported while a gate that `ROLLUP_SHARED_GATES:2066` declares kept reports success, which is the invisible-divergence class OQ-03 was resolved to avoid. Order 06 owns the RESIDUE of a failed retirement, a different condition. | yes |
| D-8 | The rollback's unguarded write (F-14): does it belong to this plan or to Order 06, which owns rollback residue? | This plan, as new E-08. | Hand it to Order 06 with the rest of the rollback work. | Same basis as D-7 and stronger: the write is correct today and becomes destructive only because E-01 relocates the mutation, so it is this plan's regression. Order 06's scope is regenerated-index residue after a failed retirement, not the plan file's bytes. Deferring it would ship a measured data-loss path in the change whose stated purpose is to stop exactly that harm. | yes |
| D-9 | E-05's prescribed observation seam patches two functions this plan itself changes. Re-specify it, or leave the executor to adapt? | Re-specify: require the BEFORE samples be captured against unmodified code first, then require the post-change counterpart instants be named and justified in the test docstring. | Leave it, since an executor would notice; or drop the comparison and assert only the post-change state. | E-07 relocates `_refresh_plans_index_fail_loud` and F-11 establishes `commit_isolated` no longer performs this commit, so both named patch points cease to mark the instants they were chosen for. A test that silently samples different instants before and after is not the comparison V-05 demands, and round 1 already had to fix an E-05 technique that could not produce its own evidence. | yes |
| D-10 | Should `Scope-Paths` be corrected by review, or left as the execution-time instruction round 2 wrote? | Correct it now, declaring all five files. | Leave the prose instruction and let the executor add the paths in the first pass. | `Scope-Paths` is inside `frozen_region_digest` (`:495-503`) and `finalize_precheck` refuses a receipt whose frozen region changed (`:1476-1483`), so following the instruction would invalidate the receipt mid-execution. `tests/test_ipd_lifecycle_cli.py` was already established as needed in round 2, and F-11 makes `commit_lock.py` plus its suite unavoidable, so all five are known now and none rests on a guess. | yes |

D-6 is `Reversible: no` and is ESCALATED as the workflow requires: raised in the reviewed plan as OQ-04
carrying `- Blocking: yes` and `- Finding: PR-021`, so `aw ipd lint` refuses the plan at every checkpoint
until the maintainer answers (verified: `IPD-Q501` at both `--phase author` and
`--phase review-finalize`). It is OQ-03's descendant, one layer down: same question, about the shared
commit helper rather than the shared transaction body.

## Round 4

DISCHARGE ONLY. NO NEW REVIEW WAS PERFORMED. This round exists to record that round 2's gating finding
was resolved by the maintainer's own decision, taken on 2026-09-13 through the `askme` workflow, one
interactive prompt at a time. Nothing in the plan was re-reviewed here and no new finding was sought;
appending a round is the mechanism `plan-review.md:187` prescribes for this, since the gate reads only
the current round. The earlier rounds are left exactly as written.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-021 | BLOCKER | IN-SCOPE | G (executability) | the resolved `OQ-04` in this plan's `## Open questions` | `commit_isolated` needed either a no-advance mode or a sibling, and it also backs every `aw` self-commit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | DISSOLVED rather than chosen: the maintainer ruled the retirement will mint its own branch, work in a worktree on it, commit normally and merge. Git permits many worktrees but only one per branch, and `commit_isolated` needs its copy-in plus hand-moved ref only because it insists on committing onto `main`, which the operator's checkout already holds. So the shared helper is untouched, its 12 tests keep pinning it, and the compare-and-swap disappears along with the reconcile it forced. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does the maintainer's answer to OQ-04 discharge PR-021, or does the finding need a fresh review pass? | It discharges it; record the discharge and leave the earlier rounds untouched. | Run a further full review round on this plan. | The finding's own recorded remedy was a human decision, and that decision is now recorded in the owning plan with its reasoning. A further round was priced on evidence and rejected: the round earlier the same day cost 3h 02m and $106.07 across nine items and raised four NEW blocking questions, so it was not expected to yield a clean sheet. | yes |

HONEST LIMIT: the discharge rests on the maintainer's decision, not on an independent reviewer's
re-examination. If a later reader needs assurance that this plan's content was checked afresh, that
assurance is in rounds 1 and 2 and not here.
