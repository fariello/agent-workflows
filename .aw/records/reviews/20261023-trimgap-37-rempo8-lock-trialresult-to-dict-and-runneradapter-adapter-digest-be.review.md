# Review findings: plan rempo8

- Subject-Id: rempo8
- Subject-Type: ipd
- Reviewed-At: 2026-10-24
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (LOW, fixed), PR-002 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `fa3959eaf`. The plan was byte-identical to the lane input and already committed at `44b151c3e` (pre-review snapshot skipped). `aw ipd lint --phase author --agent`: `clean`. Child plan (Set `trimgap`, Order 37), test-only.

Verified at the lane HEAD:
- F-01: `python3 tools/mutation_probe.py --format json --op return-none agent_workflows/benchmark_runners.py::RunnerAdapter.adapter_digest -- -o addopts= -q -p no:randomly -n0 -m "not slow and not livecorpus" tests/test_benchmark_runners_reports.py tests/test_benchmark_corpus.py` -> `verdict: survived`, `baseline_failing: 0`, `mutant_failing: 0`, `head: fa3959eaf...`. Reproduces.
- F-02: `BenchmarkRunRecord.to_dict` (`agent_workflows/benchmark_reports.py:98`, `"trials": [t.to_dict() for t in self.trials]`) and `RunnerDouble.run_trial` (`adapter_digest=self.adapter.adapter_digest()`, both success and pending branches) and `execute_live_runner` (`adapter_digest=adapter.adapter_digest()`) confirmed in `agent_workflows/benchmark_runners.py`.
- F-03: every value re-measured by direct call: the three digests, canonical-JSON equality (`True`), the nine-key set, `trial_id` `t1_m1_opencode_t1`, success/timeout `status`/`failure_kind`/`score_result`/`transcript`, manifest `identity.adapter_digest` equal to the adapter digest, JSON round-trip `True`, non-empty `rerun_command`.
- `tests/test_benchmark_corpus.py` carries `pytestmark = pytest.mark.core`; `tests/test_benchmark_runner_payloads.py` does not yet exist; `tools/mutation_probe.py` output carries `head`, `selection`, `verdict`, `baseline_failing`, `newly_failing` as V-04 demands.
- Gate already handles a pre-existing core budget overrun (E-03 reports it rather than failing; V-03 does not demand exit 0), so the sibling `bli2ba` PR-001 defect is absent here.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | G. Executability | plan E-01 "`run_trial(task, profile, trial=1)`"; E-02 defines the `SeededTask`/`ModelProfile` values; `agent_workflows/benchmark_corpus.py:56` `class SeededTask` | E-01 used undefined `task`/`profile` that only E-02 defined, and neither named the module `SeededTask` is imported from (`benchmark_corpus`, not `benchmark_runners`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now defines module-level `TASK`/`PROFILE` fixtures with explicit import sources; E-01 and E-02 both use them. |
| PR-002 | LOW | IN-SCOPE | G. Sequencing | plan E-02 "- Depends on: none" | E-02 adds a class to the module E-01 creates but declared no dependency. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 `Depends on: E-01`. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where do the shared `SeededTask`/`ModelProfile` test values live? | Module-level constants defined in E-01 | Duplicate per class; pytest fixtures | Plan E-01/E-02 used identical values; `agent_workflows/benchmark_corpus.py:56` | yes |
