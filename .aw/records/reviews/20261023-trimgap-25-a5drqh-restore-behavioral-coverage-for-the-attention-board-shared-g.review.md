# Review findings: plan a5drqh

- Subject-Id: a5drqh
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed), PR-006 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `389409d8c`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `19313eed^:tests/test_attention_priority_blocker.py` is 391 lines, 26 tests, in the six named classes;
  `GateRefRenderingTests._gated` and `_DEEP` match the plan; `attention.SCHEMA_VERSION = 5`.
- Restored file run from scratch: `1 failed, 25 passed`, only `test_schema_version_and_json_keys` fails.
- `tools/mutation_probe.py --op return-none --extra-test 19313eed:... _shared_gate_ref`: `killed`, newly
  failing `test_shared_ref_folds_into_header_and_leaves_rows` (F-02 reproduces).
- Direct calls of `_shared_gate_ref` and `render_table` reproduce every F-05 output exactly; `render_json`
  emits the four keys E-02 asserts.
- `render_table` "all {len(visible)} gated by {shared_gate}" and `gate_in_header=bool(shared_gate)` exist.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Rubric G (commit will be rejected) | plan E-01 "Add `import pytest` and `pytestmark` after the imports"; review `ruff check` `I001 Import block is un-sorted`; `.pre-commit-config.yaml` `id: ruff` `args: [--fix]` | Placing `import pytest` after the first-party imports, as the wording reads, trips ruff I001, so the mutating hook rewrites and rejects the commit. | all Low | FIXED | E-01 places `import pytest` as its own group before `from agent_workflows ...`, matching `tests/test_attention_stem.py`; E-01/V-01 require clean ruff. |
| PR-002 | MEDIUM | IN-SCOPE | Execution contract / Rubric E | plan Required tests and V-03 "scratch mutation `return \"\"` as the first statement of `_shared_gate_ref`" | Validation told the executor to hand-edit a production file in the shared tree, which is risky and unneeded when `tools/mutation_probe.py` mutates a disposable worktree; and the hand edit gives no baseline check. | all Low | FIXED | V-03/V-04 and Required tests now use `tools/mutation_probe.py --op return-none ... -m core` after the E-04 commit, requiring `baseline_failing: 0`, `killed`, and `newly_failing` naming the restored and new tests; gate forbids hand-editing `agent_workflows/`. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (evidence does not prove core reach) | plan V-01 "`python3 -m pytest --collect-only -q tests/test_attention_priority_blocker.py` ... collected by the bare (core-tier) selection"; `conftest.pytest_collection_modifyitems` applies the core filter only on the testpaths fallback | An explicit-path collect skips the core filter, so it would list the tests even without the marker. | all Low | FIXED | V-01 now greps the BARE `--collect-only` output. |
| PR-004 | LOW | IN-SCOPE | Rubric E (unsatisfiable bar) | plan Required tests and V-01 "within the core-tier budget"; sibling `3wkrng` F-06 59.22s | The core tier already overruns 30s on this host before this plan. | all Low | FIXED | Bar is exit 0 with no failures; any budget block pasted, counted only if a test of this plan is among the slowest. |
| PR-005 | LOW | IN-SCOPE | Live-artifact convention / Rubric D | plan E-01 "25 of its 26", E-02 "all 26", E-03 "6 assertions" | Counts were the bar, and E-01 had no disposition if a different restored test failed at execution HEAD. | all Low | FIXED | Bars rewritten to "every restored test except the schema test" and one assertion per branch; E-01 carries the `jy7439`-style disposition rule (adjust with cited commit, or gated `bug` + strict xfail). |
| PR-006 | LOW | UNDER-SCOPE | Execution contract | plan `## Approval and execution gate`; E-04 | Gate lacked a declarative scope fence, `aw ipd finalize` ownership, and `<base>`; the commit was not ordered before the probe-based checks. | all Low | FIXED | Gate rewritten to the repo's standard contract; E-01 records `<base>`; E-04 commits the module before V-03/V-04. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the mutation check be performed? | `tools/mutation_probe.py` against the committed module | Hand scratch edit of `attention.py` (shared-tree risk, no baseline) | `tools/mutation_probe.py` worktree isolation; sibling plans `92tzo6`, `3wkrng` | yes |
| D-2 | How to treat a pre-existing core budget overrun? | Paste it; count only if this plan's tests are among the slowest | Keep "within 30s" (unsatisfiable on this host) | `conftest.pytest_sessionfinish`; `3wkrng` F-06 | yes |
