# Review findings: plan 83nnyn

- Subject-Id: 83nnyn
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (MEDIUM, fixed), PR-010 (LOW, fixed), PR-011 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `6b16af225`. Plan committed and byte-identical to the lane
input (sha256 `e1b0a38d...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`.
Not an orchestrator (`- Kind: child`). Dependencies `qqrgv3` and `tv72xy` are `reviewed` and pending;
`tests/tools/` does not exist yet, so every tooling citation was checked against those plans' text.

Verified anchors: `tests/test_descriptive_refusal_hoist.py` `TEST_VALUES` (9 values, none at 300/301),
`REAL_NONEMPTY_VERBS` (10), `ALL_FIVE_ROUTES` (5), `FROZEN_SUFFIX_TABLE`; `attention_contract.refuse_unsafe_descriptive`
branches (`len(value) > max_len`); `tests/test_statusline_behavior.py` `generate_pairwise_covering_array`,
`test_box_renderer_invariants_across_swept_inputs`, `test_box_renderer_invariants_exhaustive_sweep` (`slow`,
`timeout(300)`, "preserved in slow suite (plan mat9bt E-05)"); executed plan `mat9bt` F-06 and OQ-01;
`tests/test_usage_refusal_agent_record.py` `test_required_arg_leaf_agent_mode`/`_json_mode`, `_capture_cli`,
`REQUIRED_LEAVES`; `tests/test_shared_flag_honored.py` "from tests.test_usage_refusal_agent_record import REQUIRED_LEAVES, _capture_cli";
`renderers.emit_usage_refusal`; research `offdhr` "CORRECTION (2026-10-16" section; `qqrgv3` E-02/E-03/E-05/E-07, F-7;
`hguae9` E-02 `core_measure`, E-05 budget guard; `GUIDING_PRINCIPLES.md` P16 table-test section; `Makefile` `test-serial`.

Measured at review: `pytest tests/ -m '' --collect-only -q -o addopts=""` = 9496 collected, 2171 parametrize cases;
the three statusline parametrized modules (146 node ids) ran in 0.66s serial; the 138 agent/json leaf cases in 7.79s;
`rg -l "unittest.TestCase|\(TestCase\)" tests` = 430 of 557 modules; `rg -c '"git", "init"' tests` = 328 in 186 files.
Template-copy probe (scratch, git 2.43.0): copy B did not see A's committed file, template unchanged, B HEAD absent
(exit 1), B `user.name` preserved, toplevel equals B; init+config 9.3ms vs copytree 3.7ms.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (measurement validity) | plan E-01 (pre-review) "`--cov-context=test --cov-branch`"; `qqrgv3` F-7 "their before/after comparisons against this baseline would report spurious losses" | E-01 and every per-batch diff used pytest-cov contexts, which `qqrgv3` shows are incomparable with its plugin and miss subprocess attribution; the zero-lost proofs would be wrong. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 runs `percov_run`/`percov_analyze`/`classify`, refuses on `pytest_exit` nonzero; protocol (f) and every V-item use `percov_analyze --compare`. |
| PR-002 | HIGH | IN-SCOPE | D (candidate source) | research `offdhr` CORRECTION "must not drive any deletion"; plan Scope and E-05..E-08 (pre-review) drew candidates from `offdhr` | The work list was the invalidated baseline. | all Low | FIXED | Protocol (a) and Scope take candidates from the `qqrgv3` owner list; `offdhr` names are context; unlisted owner rows are still processed, listed non-owner rows recorded `keep`; protected/`read-required` never deleted by metric. |
| PR-003 | HIGH | IN-SCOPE | D (regression detection) | `mat9bt` F-06 (pairwise misses 288 of 7,776 3-way combos), OQ-01 keep exhaustive; plan E-03 (pre-review) replaced the exhaustive sweep with pairwise | E-03 would delete the deliberately retained exhaustive arm and re-replace cheap full products with pairwise, a provable detection loss. | all Low | FIXED | E-03 collapses cheap products into full-product accumulate loops (node ids drop, combinations kept); the exhaustive sweep is `keep`/`speed-up` for `c8bfp9`; deferral row added. |
| PR-004 | HIGH | IN-SCOPE | C/E (fixture feasibility) | 430/557 modules are `unittest.TestCase`; `Makefile` `test-serial` runs `unittest discover` (no conftest); plan E-09 (pre-review) "function-scoped fixture ... registered from the root `conftest.py`" | A conftest fixture cannot be injected into TestCase methods nor reached under `unittest`, so most builders could not migrate. | all Low | FIXED | E-09 is a plain-function helper `tests/repo_template.py` plus optional fixture wrapper, with behavioral tests; mechanism demonstrated by probe. |
| PR-005 | MEDIUM | UNDER-SCOPE | G (right-sizing) | E-09 (pre-review) bundled helper creation with migration over many modules | Two deliverables and test surfaces in one item. | all Low | FIXED | Split into E-09 (helper + tests, no dependency) and E-11 (migration); V-11 added; E-10 depends on E-11. |
| PR-006 | MEDIUM | IN-SCOPE | D (boundary coverage) | `TEST_VALUES` has `VAL_LEN340`, `VAL_LEN1200`, nothing at 300/301; E-02 (pre-review) claimed an "at-length boundary" class | The reduction claimed a boundary the data does not test. | all Low | FIXED | E-02 adds 300/301 rows; V-02 demands a `>`-to-`>=` mutation caught. |
| PR-007 | MEDIUM | IN-SCOPE | G (re-derivation convention) | E-01 census bar, E-02 "roughly 110", E-04 "134 node ids become 67", V-04 "134-to-67"; review counts 9496/2171 and 69+69 | Collected counts used as bars and already stale. | all Low | FIXED | Counts are context; bars are behavior (every combination asserted, mutation caught, zero lost). F-2/F-5/F-7 updated with review figures. |
| PR-008 | MEDIUM | IN-SCOPE | D (cross-module imports) | `tests/test_shared_flag_honored.py` imports `REQUIRED_LEAVES, _capture_cli`; 62 test files import from other test modules | Merging or removing modules could break importers silently. | all Low | FIXED | Protocol (f) adds `git grep` for citations and `from tests.<module> import`; E-04 keeps both names; V-04/V-05..V-08 demand the grep output. |
| PR-009 | MEDIUM | UNDER-SCOPE | G (V evidence) | V-02, V-03 (pre-review) demanded counts and coverage only | No sensitivity demonstration for the reduced matrices. | all Low | FIXED | V-02 and V-03 demand a temporary mutation caught by the table with revert and empty `git diff -- agent_workflows/`. |
| PR-010 | LOW | IN-SCOPE | G (execution contract) | gate (pre-review) | Missing scope-fence wording, no-production-change rule, conditional finalize ownership, `aw ipd finalize`. | all Low | FIXED | Gate rewritten to the Set's contract (matches `tv72xy`). |
| PR-011 | LOW | IN-SCOPE | G (OQ-03 operability, batch size) | OQ-03 needs batch durations; E-05/E-06/E-08 each span 15-30 modules | No baseline durations recorded; very large batches in one pass. | all Low | FIXED | E-01 records per-batch durations, E-10 compares them; protocol commits large batches in module groups of about ten. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Reduce cheap statusline products to pairwise or keep full products? | Keep full products in accumulate loops; leave exhaustive sweep alone. | Pairwise everywhere (REJECTED: `mat9bt` F-06 measured 3-way loss; products cost ms). | `mat9bt` F-06, OQ-01; review timing 0.66s for 146 node ids. | yes |
| D-2 | Fixture or plain function for the shared repo template? | Plain function in `tests/repo_template.py`, optional fixture wrapper. | Conftest fixture only (REJECTED: unusable in 430 TestCase modules and under `unittest`). | review `rg` census; `Makefile` `test-serial`; probe output. | yes |
| D-3 | Which candidate list drives the batches? | `qqrgv3` owner list; `offdhr` names as context with explicit close-out of the 70. | `offdhr` lists (REJECTED: its own correction forbids it). | `offdhr` CORRECTION section; `qqrgv3` E-05/E-07. | yes |

No decision is `Reversible: no` (test edits are restorable from git; `vgus66` mutation-checks consolidations). No finding was left `OPEN` or `DEFERRED`.
