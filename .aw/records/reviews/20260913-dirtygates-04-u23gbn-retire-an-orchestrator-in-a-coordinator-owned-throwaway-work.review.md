# Review: retire an orchestrator in a coordinator-owned throwaway worktree, child u23gbn (Set dirtygates)

- Subject-Id: u23gbn
- Subject-Type: ipd
- Reviewed-At: 2026-09-13
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

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
