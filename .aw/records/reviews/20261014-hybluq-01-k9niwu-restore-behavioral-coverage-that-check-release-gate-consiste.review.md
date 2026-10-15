# Review findings: plan k9niwu

- Subject-Id: k9niwu
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `1c221d64a` in an isolated review lane. The plan was committed and unchanged, so no snapshot was taken. `aw ipd lint --phase author --agent` was clean before the semantic review. `--phase review-finalize` was clean after the revisions; the only result was one `IPD-Z602` info on E-02, which is one test with four rows and stays as a single item.

Re-verified:
- The `check_engine.check_release_gate_consistency` Rule 2 `item_gate` map is populated by `if item_id and gate:`, and the docstring sentence that E-03 targets ("no live guard currently asserts this directly") is present. `tests/test_release_gate_one_way_mismatch.py` does not exist yet. `19313eed^:tests/test_bug_gate_check.py` holds the `MISMATCHES` rows and the `_item`/`_plan`/`_spec` helpers the plan cites, and its spec helper writes to `.aw/records/specs/`, which `_iter_spec_records` scans.
- Probe against current code on tmp fixtures: an ungated item with a gated plan, and an ungated item with a gated spec, both give `[]`. A gated item gives exactly one mismatch for each of these carriers: ungated plan, `v9z9z9` plan, `v9z9z9` spec. Each mismatch has its location at the carrier path and a detail that names the item id6. A matching plan gives `[]`. Results are the same with and without a release record.
- The plan's mutation, applied to a scratch copy of the package (`if item_id:` storing `(gate or "", str(f))`), makes the plan row and the spec row both report `check.from-backlog-gate-mismatch`. So the mutation check is demonstrable.
- `tests/support.declare_execution_role` exists. Sibling restoration plan `55kl2u` is `reviewed`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing (anti-vacuity) | `check_engine._iter_spec_records` scans only `.aw/records/specs` / `.agents/specs`; E-02 rows (a) to (c) are plan-only | The spec half of E-01 had no anti-vacuity row. A spec helper that wrote somewhere the scanner never reads would pass E-01(b) without testing anything. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-02(d): a gated item with a `v9z9z9` spec carrier from the same helper must produce one finding at the spec path (probe: it does). |
| PR-002 | LOW | IN-SCOPE | G. Verification strength | V-02 | V-02 asked only for one PASSED line, which cannot show which rows the test covers. | all Low | FIXED | V-02 now requires `-o addopts="" -v` output showing rows (a) to (d). Test names are treated as pointers only. |
| PR-003 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the honesty rule, `aw ipd begin`, a scope fence, an instruction not to commit the mutation, and a finalize step that depends on whether a runner is used. | all Low | FIXED | Rewrote the gate. Recorded the mutation demonstration in Required tests. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is the plan's mutation check feasible, or is it an undemonstrated HOW? | Feasible; recorded as demonstrated | Leave it undemonstrated (the rule requires a demonstration) | scratch-copy probe: both carriers flagged under mutation, none without it | yes |
