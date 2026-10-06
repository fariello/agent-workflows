# Review findings: plan wytlly

- Subject-Id: wytlly
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (HIGH, fixed), PR-006 (HIGH, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (MEDIUM, fixed), PR-010 (MEDIUM, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261006T040814Z-944` at HEAD `1e0b4ab01`. The plan was committed and byte-identical
to the sealed lane input (rev-13); no snapshot needed. `- Kind: child`. `aw ipd lint --phase author` clean before;
`review-finalize` clean after (two `IPD-Z602` info advisories only).

Re-measured: `runner_shared.probe_orchestrator` / `ask_orchestrator_probe` / `enforce_orchestrator_probe_gate` seams;
`initialize_run_core`'s gate call (no `asker`); `runner_shared.initial_queue_status` (`reviewed` frozen without approval);
`run_selection_policy.runner_action` refinements (ii)/(iii); `dispatch_orchestrator_item` signature; `run_viewer.render_step_details`;
`lane_containment.LANE_PRESERVED_EVENT`; `tests/test_backlog_production.py` `_patch_host_agent`, `_make_test_repo`;
`tests/test_spec_production.py` `test_quarantine_lane_preserved_on_failure`; `pyproject.toml` markers and `conftest.py` guards;
and the contracts of `8mabmu`, `qs00nc`, `5etev3`, `26m1nb`, `r2wa38`, `nnsa2o`, `24qw39`, `sbiv1j` as currently written.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | E reachability | `runner_shared.initial_queue_status` ("A plan with status 'reviewed' waiting for human approval is frozen 'reviewed'") | Run C ran an orchestrate pass over a `reviewed` orchestrator, which is frozen `reviewed` and never dispatched; the demanded retirement was unreachable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Run C approves the orchestrator with `aw ipd set approved --by-human` first and asserts the action is `orchestrate`. |
| PR-002 | HIGH | IN-SCOPE | G right-sizing | E-01 action text (three runs, three surfaces) | E-01 bundled graduation, review and orchestrate runs, each with its own assertions and evidence. | Overall:Low | FIXED | Split into E-01 (Run A), E-06 (Run B), E-07 (Run C) via `aw ipd sync`; V-06/V-07 added. |
| PR-003 | HIGH | IN-SCOPE | E seams | `initialize_run_core` calls `enforce_orchestrator_probe_gate` without `asker`; `probe_orchestrator` resolves `ask_orchestrator_probe` at call time; `r2wa38` E-04 | No mechanism stated for injecting the probe into full runs, and no answer format, so a scripted "contains executions" would be classified `unknown` by `8mabmu`'s strict parser. | Overall:Low | FIXED | Patch `runner_shared.ask_orchestrator_probe`; double answers in the sentinel plus `QUOTE:` format decided from the excerpt; docstring states it proves plumbing, not model judgement. |
| PR-004 | HIGH | IN-SCOPE | E fidelity | all existing graduation tests pass `--no-isolate-worktree`; `test_quarantine_lane_preserved_on_failure` | Lane preservation (E-02) and "backlog item graduated on main" need isolation; following the existing pattern would make them vacuous. | Overall:Low | FIXED | Isolation kept on; main-tree vs lane assertions stated. |
| PR-005 | HIGH | IN-SCOPE | E correctness | `nnsa2o` E-02 ("re-asks because the edited orchestrator's coverage fingerprint changed"); `5etev3` E-02; `nnsa2o` E-03 | Probe counts: E-02's unchanged correction reuses the recorded `fail` (1 call, unstated); Run B counted only "run start" though Order 07's post-review re-check also runs. | Overall:Low | FIXED | E-02 asserts 1 call; Run B asserts 0 over the whole run; Run C 0 at start and retirement. |
| PR-006 | HIGH | IN-SCOPE | E correctness | `26m1nb` E-01; `qs00nc` E-06; `r2wa38` E-01; `5etev3` E-02 | E-05 demanded "the same finding code" on five surfaces, but production and retirement wrap findings in their own codes (`BACKLOG-GRADUATE-SET`, `finalize-refused`): unsatisfiable as written. Surface (5) also had no stated seam. | Overall:Low | FIXED | Same inner code on setter/lint/check, same quote and subject on all five, surface codes on (4)/(5); (5) via `DispatchRunCase`/`make_run` with Order 04's `asker`. |
| PR-007 | MEDIUM | IN-SCOPE | E observability | `nnsa2o` E-03 records the code only via `record_refusal` | "`IPD-REVIEW-ORCHESTRATOR-READY` passed" is not an observable event. | Overall:Low | FIXED | Observed as no such refusal plus `reviewed` status. |
| PR-008 | MEDIUM | IN-SCOPE | G sequencing | E-01..E-05 exercise `nnsa2o`, `24qw39`, `26m1nb`, `r2wa38`, `qs00nc`, `8mabmu` | Those were reached only transitively through `sbiv1j`/`dalmk4`. | Overall:Low | FIXED | All declared in `- Item-Dependencies:`; gate names the omitted ones and why. |
| PR-009 | MEDIUM | IN-SCOPE | G conventions | `_make_test_repo` (no install); `pyproject.toml` `slow` marker; `conftest.py` 60 s/240 s guards; `_HOSTS` loop | `--records-backend repository` named for a harness that runs no install; OQ-01 cited a nonexistent "slow threshold"; only one host covered. | Overall:Low | FIXED | Convention corrected; OQ-01 sets 30 s per test; both hosts in every runner scenario. |
| PR-010 | MEDIUM | UNDER-SCOPE | G checklist / contract | V-01..V-05; gate | V-items lacked per-host, per-run concrete evidence (mutation detail, structure grep command, baseline timing); gate lacked scope fence, honesty rule and resolved-OQ statement. | Overall:Low | FIXED | V-items rewritten with concrete pasted evidence; gate contract completed; "do not weaken an assertion" rule added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does Run C reach `orchestrate`? | Approve the orchestrator with `--by-human` in the fixture | `--full-auto` (adds an auto-approve dependency on `- Readiness:`, which the test would have to forge) | `runner_shared.initial_queue_status`; AGENTS.md attestation rule | yes |
| D-2 | What does five-surface parity compare? | Inner code on three surfaces, quote and subject on five | demand one outer code (unsatisfiable) | child contracts cited in PR-006 | yes |
| D-3 | Slow threshold for OQ-01 | 30 s wall per test, mark the test not the file | mark the whole file; no threshold | no repo threshold exists; `conftest.py` guards | yes |
| D-4 | How is the probe injected into full runs? | Patch `runner_shared.ask_orchestrator_probe` | add an `asker` parameter to `initialize_run` (production change, out of scope) | `r2wa38` E-04 precedent; `tests/test_orchestrator_shape_gate.py` | yes |
