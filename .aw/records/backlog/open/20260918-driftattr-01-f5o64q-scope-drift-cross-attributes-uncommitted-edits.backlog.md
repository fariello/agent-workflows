- Id: f5o64q
- Status: open
- Blocks-Release: next
- Set: driftattr
- Priority: low
- Work-Kind: bug
- Summary: check.scope-drift attributes an executor's own edit to every other plan holding a live receipt, inflating findings by files x plans

## Workflow history
- 2026-09-22 note (opencode its_direct/pt3-claude-opus-5-1m-us): RESOLVED IN SUBSTANCE by plan wmnmei (rcptstale-01), commit `3783bbe8`; left `open` deliberately for the maintainer to close. `check.scope-drift` now measures the plan's OWN isolated lane (maintainer ruling 2026-09-10, OQ-01 of that plan) instead of whichever tree the command runs in. MEASURED against this item's exact claim at HEAD `132e8333`: adding ONE uncommitted file to the checkout previously added one finding per live-receipt plan whose scope omitted it, and now adds a finding to the OWNING plan alone while changing no other plan's finding (plans newly flagged: the owner only; plans whose finding changed: none; cross-attributed to OTHER plans: NONE). The multiplicative `files x plans` growth is separately gone, because the rule now emits ONE finding per plan carrying a count and the paths rather than one per path: 380 findings from six plans became 4. NOT CLOSED HERE for two reasons: the fixing plan is not yet finalized (worker-role finalize is refused for a managed lane, `AW-LIFECYCLE-ROLE-001`), and closing a release-blocking `bug` is the maintainer's call on evidence they have seen. NOTE the direction differs from this item's own suggestion: it proposed splitting committed from uncommitted changes, and the maintainer chose TREE SELECTION instead, explicitly withdrawing the attribution-heuristic option. The residual gap is filed separately as `fkmjoy` (a lane whose base diverged from its receipt gets no advisory at all).
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): Found while executing plan m867ox: a 6-file change added 18 scope-drift findings across 4 unrelated in-flight plans.

MEASURED at HEAD cdace6a5 while executing plan m867ox.

check_scope_drift compares _paths_changed_by_this_execution(repo, base_head) against EACH plan's declared Scope-Paths, for every plan holding a LIVE begin receipt. Because the changed-path set is derived from the working tree, one agent's uncommitted edit is attributed to EVERY other plan with a live receipt whose scope does not name that path.

OBSERVED: editing the 6 files declared by plan m867ox took aw check from 496 to 514 findings (+18), all check.scope-drift, attributed to four unrelated pending plans (runanalytics-09 ixis0c, runanalytics-10 9xycbh, runnoop-01 zz5yxq, nobugship-01 zqs0px). None of those plans did anything wrong and none was touched. The growth is multiplicative: files_changed x plans_with_live_receipts.

WHY IT MATTERS RATHER THAN BEING COSMETIC: (1) the noise scales with concurrency, which is the direction this toolkit is moving (lane runners, parallel execution); (2) it invites the destructive fix the plan m867ox fence had to forbid explicitly, namely editing another agent's plan or widening its Scope-Paths to make a count go down; (3) it makes a real scope violation harder to see, because the signal is buried in cross-attributed noise. Plan m867ox had to spend a dedicated execution item (E-07) and a validation item (V-07) purely on explaining the delta, which is a symptom worth removing.

NOTE the evaluator ALREADY has the right instinct for adjacent cases: _receipt_is_live deliberately ignores a receipt whose plan is terminal or whose base_head is not an ancestor of HEAD, with the recorded rationale that 'comparing the whole working tree against them attributed other agents' uncommitted files to a finished plan'. This is the same failure for a plan that is merely CONCURRENT rather than finished. A candidate direction (needs design, not asserted here): distinguish COMMITTED changes since base_head (attributable to that plan's execution) from UNCOMMITTED working-tree changes (attributable to whoever currently holds the tree), or attribute an uncommitted path to at most the one plan whose lane/receipt actor owns it.
