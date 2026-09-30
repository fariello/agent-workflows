# Review findings: plan qqg41f

- Subject-Id: qqg41f
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-601 (HIGH, fixed), PR-602 (HIGH, fixed), PR-603 (MEDIUM, fixed), PR-604 (MEDIUM, fixed), PR-605 (MEDIUM, fixed), PR-606 (LOW, fixed)

## Round 1

Reviewed at HEAD `40650bfa` in an isolated review lane. The plan file was committed and byte-identical to
the lane input, so no pre-review snapshot was needed. Structural preflight `aw ipd lint --phase author
--agent` reported `conforming` (exit 0, zero findings) BEFORE semantic review; `--phase review-finalize`
reports `conforming` after revision. The plan is `- Kind: child`, so the `IPD-S407` orchestrator row check
does not apply. Baseline bare suite at HEAD: `3387 passed, 2 skipped, 3 warnings in 55.58s`.

THE PLAN'S CENTRAL JUDGEMENT IS CORRECT AND I VERIFIED IT RATHER THAN ACCEPTING IT. Backlog `caf5ed` asks
for a guard on six fixtures, and commit `19313eed` deleted all four files carrying them two days after the
item was filed; all four are absent from the working tree and the commit's own stat confirms the deletions
(406/562/1129/586 lines). So the plan is right to restore coverage instead of guarding an empty set, and
right to refuse the item's candidate direction (2) as a P16-prohibited code-structure pin. Its F-05 probe
reproduces exactly: a lane-arranged out-of-scope change gives one finding
`"1 changed path is outside the plan's declared Scope-Paths: 'other/f.txt'"` and the identical main-tree
arrangement gives zero.

THEN I BUILT THE PLAN'S ENTIRE PROPOSED ROW SET AS A THROWAWAY HARNESS AND MUTATED THE RULE UNDER IT,
because a plan whose whole deliverable is anti-vacuity coverage is worth nothing if its rows are themselves
vacuous. That is what produced every finding below, and it found three defects that reading could not.

DEFECT ONE, AND THE MOST SERIOUS: the authored row set covers the rule's HEADLINE CLAIM with no row at
all. Every row the plan specified arranges its change inside the lane, which leaves the main checkout
clean, which makes all of them blind to WHICH TREE was measured. Three measurements, all on real source.
Replacing the lane selection with the running tree (`exec_tree = Path(repo_root)`) fails exactly ONE of the
seven rows, row (a), which is the SAME single row an unconditional early return fails, so the two defects
are indistinguishable. Simulating the ACTUAL historical regression (the changed-path set becoming the union
of the lane's and the running tree's, which is what produced 350 findings of which 350 of 350 were other
agents' committed history) passes ALL SEVEN rows, because in each of them the union equals the lane. One
row closes all of it: MAIN dirty out of scope with a CLEAN lane, asserted SILENT. Measured: silent
unmutated, FIRES under the wrong-tree mutation, silent under the report-nothing mutation, so it is
discriminating and unconfounded. That is now E-06, with E-07 as the union-mutation proof, and the Goal
section states it as a third required property.

DEFECT TWO: E-04's terminal rows cannot reach the clause they claimed, and V-04 demanded evidence for it.
`check_scope_drift` iterates `_iter_type_files(repo_root, "plans")` with the default
`include_retired=False`; `check_engine.is_retired` returns True for any path segment in
`_RETIRED_PATH_SEGMENTS` = `{archive, done, executed, not-executed, parked, shipped, superseded}`, which is
a strict SUPERSET of `plans.TERMINAL` = `(executed, superseded, not-executed)`. So a terminal plan is never
yielded to the loop, its receipt is never read, and `_receipt_is_live` is never called. PROVED by replacing
`_receipt_is_live` with `lambda *_: True`, deleting the terminal rejection outright: both terminal rows
stayed SILENT and `_iter_type_files` returned `[]`. The rows assert a real observable contract and are kept,
relabelled, with the measured suppressor recorded; the production-side redundancy is filed as backlog
`f9nf0e`. The same probe found E-04's unreachable-base row over-determined: an orphan-commit base defeats
`_receipt_is_live` AND `_plan_execution_tree` at once, so its silence has two causes. The one-variable
arrangement is a LANE-ONLY COMMIT (`_receipt_is_live` False, lane still resolved, drift 0), which also pins
the asymmetry `_plan_execution_tree`'s own docstring documents.

DEFECT THREE: E-05's second mutation, as authored, is not a mutation. I applied "delete the `exec_tree is
None` guard" literally to real source (guard block matched and removed verbatim, module re-imported) and
ran all eight candidate rows: every one behaves exactly as unmutated. Deleting the guard removes the early
`continue` without redirecting the tree, and every row here has a resolvable lane so `exec_tree` is never
None. On the one arrangement where it IS None the mutated rule raises `FileNotFoundError: [Errno 2] No such
file or directory: 'None'`. Had this shipped, V-05 was unsatisfiable and its executor would have been stuck
or tempted to fabricate. Respecified as `exec_tree = Path(repo_root)`, measured to fail row (a) and E-06's
row.

TWO SMALLER MEASURED CORRECTIONS. E-03's firing row arranged one out-of-scope path, which cannot pin the
one-finding-per-plan collapse the rule's docstring calls load-bearing: with ONE dirty path the correct
collapsed rule and a per-path regression are byte-identical (`len==1`, same detail), so `assert len(drift)
== 1` passes for both; with THREE the assertion discriminates (`len==1` with a three-path detail versus
`len==3`). And E-01's `.gitignore` rationale is false: `check_scope_drift` excludes `.aw/state/` and
`.aw/worktrees/` unconditionally in its own comprehension, and omitting the `.gitignore` changes no row's
outcome, the only difference being two extra `??` entries in the main tree's porcelain. The write is kept
(it keeps E-06's main-tree assertion readable) and the false justification replaced, because a plan that
teaches a wrong mechanism is worse than one silent about it.

WHAT I CHECKED AND FOUND SOUND, recorded so the clean parts are visible: F-01 through F-08 all verify; the
`support.ready_plan_text` precedent is quoted accurately; the `include_retired`/`grandfathered`/no-receipt
silences are all real; the one-finding-per-plan collapse and its bounded tail behave as documented (13
offenders gives one finding naming ten paths and tailing `", and 3 more"`); `tests/support.py` is the right
home and `init_repo`/`git` exist there; the surviving `mock.patch`-based composition test is correctly
diagnosed as non-coverage and correctly left alone; and the plan's refusal of the meta-test is right on
P16. The plan's honesty about its own bound is unusually good and I strengthened rather than weakened it.

ONE API TRAP worth recording because it cost me a cycle: `worktree_lease.allocate_worktree` returns a
`WorktreeHandle` whose lane field is `path`, not `worktree_path` (that is `inspect_lane`'s field). E-01's
expected outcome now names it, since the helper is the one place it should be resolved.

Nothing in `agent_workflows/` was modified. All probe work lived in gitignored scratch under
`.aw/state/`, and every source mutation was applied to an in-memory copy or a scratch file, never to the
tracked module; `git diff --stat agent_workflows/` is empty.

## Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-601 | HIGH | UNDER-SCOPE | D. Anti-regression / E. Testing (the rule's headline claim is covered by no row) | Built all seven authored rows as a harness and mutated real source three ways. `exec_tree = Path(repo_root)`: fails ONLY row (a), the same row the report-nothing mutation fails. Changed-path set = union of lane and running tree (the actual 350-finding defect): passes ALL SEVEN rows. The row `main dirty out of scope / lane clean`: SILENT unmutated, FIRES under wrong-tree, SILENT under report-nothing | **Every authored row dirties the lane, leaving the main tree clean, so the whole module is blind to WHICH TREE the rule measured, which is the rule's headline claim and the reason it was rewritten.** A wrong-tree rule and a silent rule are different defects and the row set cannot distinguish them. Most damning: the exact historical regression the rule exists to prevent passes every authored row | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-06 adds the wrong-tree row (main dirty out of scope, lane clean, asserted SILENT) with its own task group, carrying the 350-finding citation and the 2026-09-10 accepted-cost note so it is not read as a bug report. New E-07 validates it against the union mutation and requires the asymmetry (only that row fails) as the evidence. New V-06 requires the three-way discrimination pasted; new V-07 requires the union-mutation output. Goal now states this as a third required property with the measurements; `- Scope:` includes it; F-11 records it; `Highest E allocated` raised to 07 |
| PR-602 | HIGH | IN-SCOPE | E. Testing (a required-evidence item that cannot be satisfied) | Applied "delete the `exec_tree is None` guard" literally to `check_engine.py` (guard block matched verbatim, mutated copy imported): all eight candidate rows behave exactly as unmutated. On a no-lane arrangement the mutated rule raises `FileNotFoundError: [Errno 2] No such file or directory: 'None'` | **E-05's second mutation is not a behavior change any test can catch, so V-05's demand for "at least one FAILING row" under it was unsatisfiable.** Deleting the guard removes an early `continue` without redirecting the tree, and every row has a resolvable lane so `exec_tree` is never None. An executor would have been blocked at V-05 or tempted to paste failures from the first mutation instead, in a plan whose whole subject is evidence that does not prove what it claims | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-05 respecifies the second mutation as `exec_tree = Path(repo_root)`, measured to fail row (a) and E-06's row, and explicitly forbids the retired spelling with the reason. V-05 requires the mutation diff to be quoted so a reader can see it redirects the tree, and FAILS evidence showing only the guard deleted. F-14 records the measurement; the Required-tests section carries the same correction |
| PR-603 | MEDIUM | IN-SCOPE | Evidence accuracy (a row attributed to a clause it cannot reach) | `plans.TERMINAL` = `(executed, superseded, not-executed)` is a strict subset of `check_engine._RETIRED_PATH_SEGMENTS` = `{archive, done, executed, not-executed, parked, shipped, superseded}`; `check_scope_drift` iterates `_iter_type_files(..., include_retired=False)`. MEASURED: with `_receipt_is_live` replaced by `lambda *_: True` both terminal rows stay SILENT and `_iter_type_files` returns `[]` | **E-04 asserts its terminal rows exercise `_receipt_is_live`'s terminal-plan branch, and they cannot: the retired-path filter removes the plan before its receipt is read.** V-04 then demanded evidence for that attribution. The rows assert a real contract, so the defect is the label, and a mislabelled row teaches a later reader that a clause is covered when nothing covers it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 rewritten: rows (b)/(c) are BLACK-BOX assertions of the observable contract, must record that the measured suppressor is the retired-path filter, and must not claim to exercise `_receipt_is_live`. V-04 FAILS any comment or docstring asserting otherwise. New OQ-02 records the keep-relabel-and-file decision with its rejected alternatives. Production redundancy filed as backlog `f9nf0e` (chore: the observable answer is correct); the fence row now carries `- Carrier: f9nf0e` in place of its now-false `Carrier-Declined`; a new Scope-check under-scope bullet names the residual gap |
| PR-604 | MEDIUM | IN-SCOPE | D. Anti-regression (an over-determined silent row) | Orphan-commit base: `_receipt_is_live=False` AND `_plan_execution_tree=None`, drift 0. Lane-only commit as `base_head`: `_receipt_is_live=False`, `_plan_execution_tree` resolves the LANE, drift 0. Control with honest base: `_receipt_is_live=True`, lane resolved, drift 1 | **E-04's unreachable-base row is silent for two independent reasons under the obvious arrangement, so it cannot say which clause it tests** and would pass even if the ancestry asymmetry the rule documents were removed. The plan's own standard ("one-variable") is the one it fails here | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 row (d) must freeze the receipt at a LANE-ONLY COMMIT and must NOT use an orphan commit, with the measurement stated. V-04 requires the printed `_receipt_is_live` / `_plan_execution_tree` pair (`False` plus a resolved lane) as proof of one-variableness. E-01 is explicitly told NOT to add a base-commit knob, since the caller constructs this after the helper returns. F-10 records it; a new conventions bullet generalizes the over-determination check |
| PR-605 | MEDIUM | IN-SCOPE | D. Anti-regression (a firing row that cannot pin the collapse it depends on) | With ONE out-of-scope path the correct collapsed rule and a simulated per-path regression are byte-identical (`len==1`, same detail), so `assert len(drift) == 1` passes for BOTH. With THREE: correct gives `len==1` and a three-path detail, regression gives `len==3`. At 13 offenders the detail names ten and tails `", and 3 more"` | **E-03's firing row arranges one path, so it cannot pin the ONE-FINDING-PER-PLAN collapse** that `check_scope_drift`'s docstring calls load-bearing ("A single frozen base used to emit one finding per intervening file, which is how 350 findings came from six causes"). The plan's own conventions section names the collapse as a constraint on how to assert, then specifies a row that cannot check it | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 row (a) must arrange THREE out-of-scope paths and assert BOTH `len(drift) == 1` and all three paths in that single detail. V-03 FAILS a one-path firing row with the reason. E-03's expected outcome and the proposed-changes entry updated; the conventions bullet now records the `_SCOPE_DRIFT_PATHS_NAMED` bound and the measured 13-offender tail; F-13 records the measurement |
| PR-606 | LOW | IN-SCOPE | G. Plan executability (a false mechanism claim, a missing knob, an incomplete gate, an undated count) | `check_scope_drift` excludes `.aw/state/`/`.aw/worktrees/` unconditionally in its own comprehension; MEASURED with and without the `.gitignore`, row (b) is SILENT either way and the lane resolves to `.aw/worktrees/<id6>`, the only difference being two `??` entries in the main porcelain. `WorktreeHandle` has field `path`, not `worktree_path`. Baseline suite `3387 passed, 2 skipped` versus the plan's `3246` | **Four small executability gaps.** E-01's `.gitignore` rationale is measurably false; E-01 exposes no plan-directory knob although E-04 needs `executed/` and `executed/YYYYMM/` placements; the gate omits the hard-MUST honesty rule and the conditional-ownership lifecycle transition the repository's contract requires; and the suite count is presented as a flat fact although it moves with every landed change | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 keeps the `.gitignore` write with a corrected rationale (fixture shape, keeping E-06's main-tree assertion readable) and an explicit instruction not to delete it either way; V-01 FAILS an evidence block repeating the false claim. E-01 gains the plan-directory knob and names `handle.path`. The gate now carries the paste-the-actual-output honesty MUST, the bare-run instruction, a declaration-style scope fence with the one genuinely-unsafe stop condition named, the open-questions statement, and the unconditional-finalize/conditional-owner transition with `aw ipd finalize qqg41f ... --apply` and the never-hand-roll prohibition. The baseline count is restated as dated context with an explicit "a mismatch is expected and must not be reported as a finding". F-12 records the gitignore measurement |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-601: the row set covers the measured-tree claim with nothing. Add a row, widen an existing row, or accept the gap? | ADD a dedicated wrong-tree row as its OWN E-item (E-06) plus a union-mutation proof (E-07) | (a) Add it as a fifth row of E-03's table; (b) accept the gap on the grounds that row (a) fails under the wrong-tree mutation anyway; (c) require only the mutation evidence in E-05 without a row | Option (b) is refuted by measurement and is the finding: row (a) fails identically under the report-nothing mutation, so it attributes nothing, and the ACTUAL historical defect (union of both trees) passes row (a) and every other authored row. Option (c) leaves the property unpinned in the committed suite, which is exactly the "mutation proved it once, nothing guards it after" shape this plan exists to end. Option (a) was the tempting minimal fix and is wrong for a stated reason: E-03's table is the CORE-CONTRACT table whose rows all share one arranging shape (dirty the lane), and this row inverts that shape, so burying it there hides the one row whose arrangement is different in the way that matters. Its own item and task group make the distinction legible and let E-07 depend on it explicitly | yes |
| D-2 | PR-603: the terminal rows cannot reach `_receipt_is_live`. Delete them, relabel them, or make them reach it? | RELABEL as black-box rows recording the measured suppressor, and file the production redundancy separately | (a) Delete both rows as untruthful; (b) make `check_scope_drift` pass `include_retired=True` so liveness becomes the real gate and the branch is exercised; (c) leave the attribution as authored | Option (c) ships a false claim into a module whose charter is anti-vacuity, and V-04 would have demanded evidence for it. Option (a) destroys live coverage of a REAL contract a consumer depends on (a terminal plan gets no drift advisory), which holds regardless of which internal mechanism produces it, to fix what is only a labelling error. Option (b) changes which mechanism is authoritative in production, is excluded by this plan's own fence (writing coverage around a moving subject), and is a maintainer's call about defense-in-depth rather than an agent's. Relabelling keeps the coverage honest and backlog `f9nf0e` carries the production question with three candidate directions and none asserted | yes |
| D-3 | PR-603 follow-on: is the unreachable branch a `bug` (which would gate the next release) or a `chore`? | `chore`, filed as `f9nf0e` with no `Blocks-Release` | (a) `bug` with `Blocks-Release: next`, since a documented branch nothing can reach is a live trap; (b) do not file at all, since nothing is broken | Option (a) fails the repository's stated test in `AGENTS.md`: the OBSERVABLE answer is correct in every arrangement measured, so no user can perceive anything, and inefficiency or redundancy a user cannot notice is explicitly not a defect. Gating a release on a change that alters no behavior is the over-filing that ruling warns against. Option (b) loses the measurement: the branch carries a substantial docstring explaining a decision nothing exercises, and a future change to the retired filter or a second caller would silently change which mechanism is load-bearing, so the trap is worth recording even though it is not a fault | yes |
| D-4 | PR-604: how should the unreachable-base row be arranged so its silence is attributable? | LANE-ONLY COMMIT frozen as `base_head` | (a) Orphan commit, the obvious construction; (b) a fabricated non-existent sha; (c) drop the row | Option (a) is the finding: measured, it defeats both ancestry checks at once, so the row would pass even if the documented asymmetry between them were removed. Option (b) is worse still, because `_plan_execution_tree` also fails on it and `_receipt_is_live` cannot distinguish "unreachable" from "git could not answer", which is its fail-safe path rather than the clause under test. Option (c) discards a clause the rule's docstring specifically argues is NOT redundant. The lane-only commit is the one construction where the base is reachable from the lane's HEAD but not the main tree's, which is precisely that documented asymmetry, and it measures `False` plus a resolved lane | yes |
| D-5 | Should the review author the tests, having built a working harness for all eight rows? | NO; the harness stays throwaway scratch outside the deliverable | (a) Promote the harness into `tests/test_check_scope_drift.py` since it is measured working; (b) paste the harness source into the plan as the intended implementation | The workflow is explicit that plan-review edits planning documents only. Beyond that, the harness deliberately cut corners the deliverable must not: it lives outside the test tree, hand-rolls its arranger rather than adding the shared helper that is E-01's entire point, and asserts nothing about the docstrings E-02/E-05/E-06 require. Option (b) would freeze fixture details probed in minutes into an executable contract and would pre-empt E-01's design. What the harness legitimately contributes is the six findings and the proof that the deliverable is achievable and non-vacuous, all recorded above | yes |
