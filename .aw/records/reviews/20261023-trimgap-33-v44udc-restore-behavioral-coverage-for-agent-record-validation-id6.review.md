# Review findings: plan v44udc

- Subject-Id: v44udc
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `503f15cbd`. The plan was byte-identical to the lane input and already committed (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 33), one new test module.

Verified at the lane HEAD:
- All F-03 values reproduced by direct calls (recorded as plan F-04): `validate_agent_record` error lists for `good`, `exit=7`, `{}`, and a result missing `verified`/`complete`; `is_valid_agent_record` True/False; `_existing_type_id6s` on the E-02 fixture `{'abc123', 'zzz999'}` and `set()` on an empty git repo; all ten `_infer_artifact_type` results; both `build_remediation` `summary_fix` strings contain `aw rename specs abc123` / `aw rename backlog abc123`.
- `doctor.build_remediation` name-nonconformant branch: `target_type = art_type or "plans"`, so the E-03 public-caller assertion does kill a `return-none` mutant.
- `artifact_rename._existing_type_id6s` has one caller (`run_rename_generic` `--to-id6`, feeding `mint_id6`) and swallows all exceptions, so `return-none` would make the caller receive `None`; the direct `== {...}` assertion kills it.
- No change since authoring HEAD `6c0a6b72a` to `agent_schema.py`, `artifact_rename.py`, `doctor.py`, `selectors.py`.
- `tools/mutation_probe.py` exists with `--op return-none --format json` and a `ProbeResult` carrying `head`, `selection`, `verdict`, `baseline_failing`, `mutant_failing`; it probes committed HEAD in a worktree, so E-04's commit-before-probe order is correct.
- Backlog `nzc6dm`, findings `wo21z5`, and precedent plan `33f8tn` (executed) all exist; `tests/test_record_residual_helpers.py` does not exist yet and no other pending plan declares it.
- Collection probe: in a scratch module, a plain class `PlainTests` was NOT collected, `UTTests(unittest.TestCase)` and `TestPlain` were (`2 passed`). `pyproject.toml` sets no `python_classes`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Test collection (silent no-op) | E-01..E-03 class names `ValidateAgentRecordTests`, `ExistingTypeId6sTests`, `InferArtifactTypeTests`; `pyproject.toml` `[tool.pytest.ini_options]` (no `python_classes`); collection probe above | The plan names `...Tests` classes and E-02/E-03 need `tmp_path`. As plain classes they would not be collected; as `unittest.TestCase` they could not take `tmp_path`. Either way some or all tests would silently not run and the E-05 probe would report `survived`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renamed to `TestValidateAgentRecord` / `TestExistingTypeId6s` / `TestInferArtifactType`, required plain pytest classes with the reason stated, and V-01 demands a non-zero collected count per class. |
| PR-002 | MEDIUM | IN-SCOPE | Sequencing | E-04 "Commit the module ... then run" | Nothing required the module to pass before it was committed, and V-01..V-03 cite `-v` output that no E-item produced. | all Low | FIXED | E-04 first runs `-v -n0` on the module (the V-01..V-03 evidence) and verifies the staged set, then commits. |
| PR-003 | MEDIUM | UNDER-SCOPE | Execution contract | old `## Approval and execution gate` | The scope-fence wording ("do not expand scope casually") does not match the declaration form. The "paste actual output" rule was weak. The rule for who runs the transition (runner or executor) was missing, and the gate implied a hand move to `executed/`. | all Low | FIXED | Gate rewritten as a full execution contract. |
| PR-004 | LOW | IN-SCOPE | Validation bar | E-04/V-04 "no failures"; `conftest.py` "CORE TIER BUDGET EXCEEDED" | The plan did not say whether a budget-only overrun fails it. That overrun depends on host load. The V-01 grep pattern `ast\.` also matched substrings such as `last.`. | all Low | FIXED | A budget-only overrun is recorded, not failed. The grep now uses word boundaries. |

`aw ipd lint --phase review-finalize --agent`: `clean` after `aw ipd set reviewed`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the test classes be shaped so they are collected and can use `tmp_path`? | Plain pytest `Test*` classes | `unittest.TestCase` with `tempfile` (deviates from the plan's `tmp_path`); module-level functions (equally valid; the plan's class grouping is kept) | collection probe; `pyproject.toml` ini options | yes |
| D-2 | Does a budget-only overrun in the bare gate fail this plan? | No, record it verbatim | Treat it as a failure (load-dependent) | `conftest.py` budget block; review f6el0l D-2 | yes |
