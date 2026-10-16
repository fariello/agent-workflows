# Review findings: plan vgus66

- Subject-Id: vgus66
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (MEDIUM, fixed), PR-010 (LOW, fixed), PR-011 (LOW, fixed), PR-012 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `20f1a9dae`. Plan committed and byte-identical to the lane input
(sha256 `19419a76...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an
orchestrator (`- Kind: child`). Upstream children `qqrgv3`, `tv72xy`, `83nnyn`, `c8bfp9` are `reviewed` and
pending; `tests/tools/` does not exist yet, so tooling citations were checked against those plans' text.

Verified anchors: prompt `4ul37x` Method steps 3 to 5 and "Evidence required in the final report"; research
`7ry5kv` "full (8794 tests)" row and `offdhr` CORRECTION section; `qqrgv3` E-02/E-03 (`percov_run`,
`percov_analyze --compare`), E-05 defect-citation rule, E-07 (baseline directory, consumer plans to use
`percov_*`, F-7); `hguae9` E-02 (`core_measure`, `leaf_probe`); `c8bfp9` "this child deletes nothing", F-7,
OQ-02; `CHANGELOG.md` `## 2.0.0 (pending)` with flat `Added:`/`Fixed:`/`Changed:` bullets; `aw research`
verbs `promote --to`, `set-outcome --to`, `new --order` optional; `.aw/records/research/README.md` shelf status.

Measured at review: `pip show mutmut` not found; `git rev-list --count 6ea45c974..HEAD` 383 and 78 files under
`agent_workflows/` changed; a temporary worktree at HEAD with `tests/` and `conftest.py` checked out from
`6ea45c974` (55 paths) collected 9101 tests over current code (worktree removed; `git status` clean afterwards).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (measurement validity) | E-01 (pre-review) "`--cov-context=test`"; `qqrgv3` F-7 and E-07 (consumer plans must use `percov_*`) | Final coverage used pytest-cov flags that are incomparable with the `qqrgv3` baseline (context labels, no subprocess attribution), producing spurious losses or misses. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 uses `percov_run` and `percov_analyze --compare`, refuses on `pytest_exit` nonzero, and regenerates a missing baseline at its recorded HEAD. |
| PR-002 | HIGH | IN-SCOPE | D (parity attribution) | F-5: 78 production files changed during the Set | Comparing baseline to final mixes production changes with test changes, so a lost line can be a refactor and a test loss can be masked; "code deleted on main" was an escape hatch. | all Low | FIXED | E-01 adds a test-isolating comparison (Set-start tests over current code, demonstrated feasible, F-6) as the bar; E-02 drops the "deleted on main" justification. |
| PR-003 | HIGH | IN-SCOPE | D (mutation validity) | E-05 (pre-review) never ran the original test against the mutation | A mutation the deleted test would not have caught proves nothing about detection retained. | all Low | FIXED | E-05 requires the original test to fail on the mutation; otherwise replace the mutation or record `no-detecting-mutation`; V-05 demands the original's failure line. |
| PR-004 | MEDIUM | IN-SCOPE | E (sampling) | E-04 vs E-05: not-applicable pins "do not count toward the 20" but were in the draw; `c8bfp9` deletes nothing | The random sample could fall under 20 applicable rows, and the `c8bfp9` stratum was empty by construction. | all Low | FIXED | Pins excluded before drawing; per-child proportional stratification with minimums; `c8bfp9` population defined as split/converted tests. |
| PR-005 | MEDIUM | IN-SCOPE | E (defect set derivation) | E-04 "345 test files cite an id6" | No rule for deriving the defect-citing set. | all Low | FIXED | Uses `git show` of each removed test plus the `qqrgv3` E-05 id6/incident rule. |
| PR-006 | MEDIUM | IN-SCOPE | E (flake protocol) | E-07 (pre-review) "serial run of every module that failed" | Did not separate ordering from xdist effects or handle failures that reproduce serially. | all Low | FIXED | Same-seed single-test and module serial reruns; serial-reproducing failures dispositioned as real; quarantine form and Work-Kind specified. |
| PR-007 | MEDIUM | IN-SCOPE | E (restoration quality) | E-02 restorations unverified | Restored tests were not shown to detect anything. | all Low | FIXED | Each restoration needs a fail-on-mutation, pass-on-revert pair (V-02). |
| PR-008 | MEDIUM | IN-SCOPE | G (tooling citation) | E-03 "its `tests/tools/` measurement script" | Unnamed tool; leaves added since hguae9 would read as regressions. | all Low | FIXED | Names `core_measure` and `leaf_probe`; separates new leaves; budget guard checked. |
| PR-009 | MEDIUM | UNDER-SCOPE | G (right-sizing) | E-09 (pre-review) bundled decision-table finalization, final report, CHANGELOG and sanitizer | Several deliverables in one item. | all Low | FIXED | Split into E-09 (decision table) and E-10 (report and CHANGELOG); V-10 added. |
| PR-010 | LOW | IN-SCOPE | G (repo facts) | CHANGELOG has no testing/internal section; `aw research new --order 05` collides with set orders; "final status" unnamed; `git diff <base>..HEAD` includes other plans' commits | Instructions did not match repo mechanics. | all Low | FIXED | `- Changed:` bullet under `## 2.0.0 (pending)`; `--order` omitted; `set-outcome`/`promote` named; changed files derived from `AW-Item` trailers (F-7). |
| PR-011 | LOW | IN-SCOPE | G (OQ owner) | OQ-02 `Owner: maintainer` with no recorded answer | Owner label overstated. | all Low | FIXED | Owner corrected to plan author with reason. |
| PR-012 | LOW | IN-SCOPE | G (execution contract) | gate (pre-review) | Missing scope-fence wording, worktree cleanup, `AW_CONFIG_DIR` rule, conditional finalize ownership. | all Low | FIXED | Gate rewritten to the Set's contract; `conftest.py` added to Scope-Paths for flake fixes. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What is the coverage-parity bar when production code moved? | Set-start tests over current code vs final tests over current code. | Raw baseline vs final with removed-line exclusion (REJECTED: mixes refactors with test loss). | F-5, F-6 probe. | yes |
| D-2 | Does a mutation count if the original test would not catch it? | No. | Count any plausible mutation (REJECTED: proves nothing about retained detection). | prompt `4ul37x` step 3 "the bug it was meant to catch". | yes |
| D-3 | OQ-02 owner | Plan author. | Keep `maintainer` (REJECTED: no recorded answer). | OQ-02 text. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
