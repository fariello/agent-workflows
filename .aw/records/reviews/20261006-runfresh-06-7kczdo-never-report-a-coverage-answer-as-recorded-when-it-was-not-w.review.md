# Review findings: plan 7kczdo

- Subject-Id: 7kczdo
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T030816Z-4078927` at HEAD `261df1ecc`. The plan was
committed and byte-identical to the sealed lane input (rev-7); no snapshot needed. `- Kind: child`, so `IPD-S407`
and `IPD-S408` do not apply. `aw ipd lint --phase author` clean before review; `review-finalize` clean after.

Re-measured by reading code (a scratch reproduction under `/tmp` was refused by the lane sandbox):
`coverage_record.write` returns `written=False` with "already has uncommitted changes; record not written" on a dirty
plan with `commit=True`; `runner_shared.probe_orchestrator` writes only for `no-executions` and for `executions`
WITH quotes, and folds the write detail into `detail`; `orchestrator_readiness.review_readiness` never reads
`written` into a finding; `run_coverage` prints only under `elif r.written:`; `CONDITION_4_CODES` has five codes and
is the filter `runner_shared.dispatch_orchestrator_item` applies at the retirement re-check;
`enforce_orchestrator_probe_gate` ignores `written`. The existing pin
`tests/test_orchestrator_probe_quotes.py::test_dirty_plan_is_not_written_or_committed` asserts the current refusal.
The real probe spawn refuses under `PYTEST_CURRENT_TEST` (`_assert_probe_spawn_is_permitted`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | A correctness / Goal | `orchestrator_readiness.CONDITION_4_CODES`; `runner_shared.dispatch_orchestrator_item` "`f.code in _orch_ready.CONDITION_4_CODES`" | The retirement-time re-check (one of the four asking consumers the Concern names) filters findings by `CONDITION_4_CODES`; a new code outside it is dropped, so the retirement would still proceed on an unrecorded answer. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 adds the code to `CONDITION_4_CODES`; E-04 adds a retirement re-check case; V-02/V-04 demand it. |
| PR-002 | HIGH | IN-SCOPE | E testing / reachability | E-04 "driving `aw ipd coverage` as a subprocess ... with a probe double (the `asker` seam, or a pre-arranged answer"; `run_coverage` exposes no asker; a current record skips the ask; `_assert_probe_spawn_is_permitted` | The demanded subprocess test is unreachable: no seam reaches the child, a pre-arranged record never exercises the not-written path, and the real spawn refuses under pytest. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now drives `cli.main(["ipd","coverage",...])` in-process with `ask_orchestrator_probe` patched, and states why a subprocess cannot work. |
| PR-003 | MEDIUM | IN-SCOPE | A correctness | E-02 "after an asking probe returns `no-executions` or `executions`, when `written` is False"; `probe_orchestrator` does not write for `executions` without quotes | Keying on the answer would add a spurious second finding for a quote-less fail that never tried to write. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New `ProbeOutcome.write_attempted`; the finding is gated on it and on not-cached; negative case added to the expected outcome and V-02. |
| PR-004 | MEDIUM | UNDER-SCOPE | D anti-regression / scope fence | `tests/test_orchestrator_probe_quotes.py::test_dirty_plan_is_not_written_or_committed` pins the current refusal; Scope-Paths omitted it | If E-01 chooses write-without-commit, this pin breaks and the file was undeclared. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added to Scope-Paths; E-01 says update (not delete) the pin, or `--scope-ack` if unchanged; included in the test command and V-04. |
| PR-005 | LOW | UNDER-SCOPE | F silent failure | E-02 "reported as `committed: false` with its reason"; `ReviewReadiness` and the `--agent` record carry no reason field | The written-not-committed reason had no carrier to the operator. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `write_detail` added to `ReviewReadiness` and the `--agent` per-orchestrator record. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should E-04 exercise the asking CLI path? | In-process `cli.main` with `ask_orchestrator_probe` patched | subprocess with a fake `opencode` on PATH (refused under pytest by `_assert_probe_spawn_is_permitted`); new env seam (production surface for tests) | `runner_shared._assert_probe_spawn_is_permitted`; `run_coverage` builds its own state | yes |
| D-2 | Key the not-written finding on answer or on a write attempt? | On `write_attempted` | on answer (double-reports quote-less fail) | `probe_orchestrator` write branches | yes |
