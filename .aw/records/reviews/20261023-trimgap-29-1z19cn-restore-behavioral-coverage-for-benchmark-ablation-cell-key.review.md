# Review findings: plan 1z19cn

- Subject-Id: 1z19cn
- Subject-Type: ipd
- Reviewed-At: 2026-10-23
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `72da75876`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review (direct calls and the probe tool's own splice function):
- F-04 reproduces exactly: `generate_schedule()` with the E-01 inputs returns 4 `AblationTrialSpec`s with
  cell keys `{('t1','m1','high','opencode',1), ('t1','m1','high','opencode',2)}`, each key carried by two
  specs whose architectures are `{'monolith','modular'}`; `compute_aggregate_metrics([]).to_dict()` has the
  five stated keys, `sample_size 0`, 14 metrics, and the stated `task_correctness` entry, and is
  `json.dumps`-able; `GateEvaluationResult(...).to_dict()` equals the stated dict and the default
  `model_profile_name` serializes as `None`.
- F-03 reproduces: `tools.mutation_probe.apply_operator(src, q, "return-none")` returns changed source
  for all three qualnames.
- `AblationTrialSpec.cell_key` is a `@property` (`agent_workflows/benchmark_ablations.py`
  `def cell_key(self)`), and the dataclass fields match E-01's direct construction.
- `tools/mutation_probe.py` adds its worktree from `HEAD` (`"worktree", "add", "--detach", wt_dir, "HEAD"`),
  so E-05's ordering after E-04's commit is correct; `ProbeResult` carries `head`, `verdict`,
  `baseline_failing`, `mutant_failing` as V-05 demands.
- `tests/test_engine_restored_behavior.py` uses module-level `pytestmark = pytest.mark.core`; conftest
  `pytest_collection_modifyitems` keeps `core`-marked items on a bare run, so the new module joins the gate.
- `tests/test_benchmark_residual_payloads.py` does not exist yet (no collision).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | Execution contract (rubric G) | plan `## Approval and execution gate` | Gate lacked the hard-MUST paste-actual-output wording, a declarative scope fence with `--scope-reason` justification, the no-production-change rule, and runner versus hand `aw ipd finalize` ownership; it implied a hand move to `executed/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to the Set's standard contract (as in sibling `92tzo6`). |
| PR-002 | LOW | IN-SCOPE | Rubric E (evidence feasibility) | plan E-04, V-05 `<E-04 parent>` | V-05 and Required tests reference `<E-04 parent>` but no item records it, so the executor had to invent it. | all Low | FIXED | E-04 records `<E-04 commit>` and `<E-04 parent>`; V-05 demands both be pasted. |
| PR-003 | LOW | IN-SCOPE | Rubric D (invariant to test) | plan E-01 "two architectures share each cell, which is the property the key exists for" | The stated invariant (architectures share a cell) was only parenthetical; the set-equality assertion alone does not pin that each key groups both architectures. | all Low | FIXED | E-01 now asserts each key is carried by exactly two specs whose architectures are `{ARCH_MONOLITH, ARCH_MODULAR}` (measured at review); V-01 demands the asserting lines. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should the gate's contract wording follow the sibling Set plans? | Adopt the `92tzo6` gate wording adapted to this plan | Leave the original gate | `.aw/system/workflows/plan-review/plan-review.md` Step 4 execution-contract and scope-fence rules; `92tzo6` gate | yes |
