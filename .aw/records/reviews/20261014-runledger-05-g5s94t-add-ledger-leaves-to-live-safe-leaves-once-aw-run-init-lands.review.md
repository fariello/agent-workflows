# Review findings: plan g5s94t

- Subject-Id: g5s94t
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `f140d2448`. The plan was committed and byte-identical to the
lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`, 0 findings. Not an
orchestrator.

`aw run init` (`v47z9u`, `reviewed`) has not landed, so the empirical probe hand-appended the `kind: "run"`
header `v47z9u` E-03 specifies at `.aw/records/runs/run-abcdef1234/ledger.jsonl` in a scratch git repo under
the lane's gitignored `.aw/state/`, plus `wf.json` and both projection files, and drove all eight read
leaves (human, `--agent`, `--json`, `run_cli_tty(no_color=True)`) and the four writers (sequenced and
isolated) through `tests.conformance_matrix.run_cli`. A second probe injected the authored template seed
into `build_installed_project_template` as a pytest plugin and ran the mutation sweeps
(`89 passed, 8 xfailed`). Both probes were deleted afterwards.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E (test correctness) | `agent_workflows/cli.py` `_register_run_leaf` (`--workflow` only for start/next/record/resume/cancel/status/finalize) | The authored `live_leaf_argv` passes `--workflow` to `runs show`, which has no such flag: probe `runs show ... --workflow wf.json` exit 2 `unrecognized arguments`. The live sweeps would have failed (or, worse, passed on exit 2, see PR-002). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `--workflow` limited to `runs next`/`resume`/`status`; F-04 rewritten with measured codes. |
| PR-002 | HIGH | UNDER-SCOPE | D/E (non-vacuity) | `agent_workflows/command_surface.py` (every ledger leaf's `exit_contract` contains 2); probe "cwd=REPO-no-dir rc=2" for all eight | Every ledger leaf exits 2 when run against the checkout, and 2 is in every `exit_contract`, so any sweep that uses `LIVE_SAFE_LEAVES[leaf]` without `live_leaf_argv` passes vacuously. The authored E-05 routed only two of five such sweeps (`test_no_color_transport_contrast_observes_ansi` and both heavy tests were not routed). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 routes all five; `live_leaf_argv` raises `ValueError` for a ledger leaf without a fixture dir; V-09 demands a pasted fail-when-unfixtured demonstration; F-10 added. |
| PR-003 | HIGH | IN-SCOPE | E (test correctness) | `agent_workflows/run_cli.py` `_run_decisions`/`_run_questions` (`return 1 if "_No autonomous decisions recorded._" in text else 0`) | F-04 claimed `runs decisions` / `runs questions` exit 0, but with "none recorded" projections (the natural seed) they exit 1 (probe). The authored assertion set `{0, 1}` hid the discrepancy; E-09 now asserts the exact code. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-04 corrected; E-02 pins the marker-line contents; E-09 asserts exact codes; E-01 re-measures and stops on drift. |
| PR-004 | MEDIUM | IN-SCOPE | E (test environment) | `agent_workflows/runner_shared.py` `state_root`; probe "bare git dir -> OUTSIDE (home)" | A session `live_ledger_dir` from `mktemp` + `git init` alone would make `aw run init` write the fixture ledger under the home-scoped projects tree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `seed_ledger_fixture` creates `.aw/records/` first and asserts the ledger path is inside root; F-09 added. |
| PR-005 | MEDIUM | IN-SCOPE | C (KISS, isolation) | `tests/conformance_matrix.py` `build_installed_project_template` (`baseline_status`); `.aw/.gitignore` | The authored E-02 seeded a full ledger plus projections into the template every `MUTATION_UNIVERSE` leaf clones, though only `run init` needs anything (`wf.json`). Probe: no regression, and `git status` delta `?? wf.json`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Template gets `wf.json` only, written after `baseline_status`; the ledger lives in the per-session `live_ledger_dir` and per-test fresh fixtures; F-05 rewritten with the measurement. |
| PR-006 | MEDIUM | IN-SCOPE | G (registry contract) | `tests/test_agent_surface_conformance.py` `test_mutation_exemption_registry_contract` (`valid_reason_kinds`) | E-03 (e) said to "cite Section 3.1" for the four writers without naming a `reason_kind`; the natural reading (`sanctioned_raw`, as for the readers) fails that contract test. It also did not say whether `runs decisions`/`runs questions` stay exempt. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 (split from E-03) names each kind: readers `sanctioned_raw`, decisions/questions `not_runnable`, writers `arg_fixture_needed`; leaf set unchanged; OQ-02 revised. |
| PR-007 | MEDIUM | UNDER-SCOPE | B (privacy) / C | probe: `runs evidence --agent` `"ledger": "<absolute path>"`; `runs verify-ledger` human `Ledger: <absolute path>`; `_run_decisions` markdown under `--json` | Making these leaves live surfaces two measured machine-surface gaps (markdown on `--agent`/`--json`; absolute-path leak shape, D92) that this test-only plan cannot fix and that had no carrier. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New E-07 files one backlog item (Scope-Paths extended); E-09 pins today's decisions/questions behavior so a fix is visible; F-07, F-08 added. |
| PR-008 | MEDIUM | IN-SCOPE | G (right-sizing) | authored E-02, E-03, E-05 | E-03 mixed LIVE_SAFE/RUNNABLE edits with twelve registry rewrites; E-05 mixed routing five existing sweeps with two new tests. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-03/E-04 and E-06/E-09 with matching V-items. |
| PR-009 | LOW | IN-SCOPE | G (evidence strength) | authored V-01, V-04, V-05; E-05 writers | The writer test only asserted exit codes (a no-op CLI would pass), and V-items did not demand the re-measured table or a non-vacuity demonstration. `run init`'s `--fields`/`--json` mutation cases had no stated fallback if `v47z9u` does not honor them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-09 (b) asserts `run_state == "cancelled"` after the sequence; V-01/V-09 demand the table and the fail-unfixtured run; E-05 allows only a strict `KNOWN_BROKEN` xfail with a filed id. |

`IPD-Z602` (info) remains on E-02: it is one deliverable (the fixture helpers and the template `wf.json`
they need) and was not split further.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Where does the read-sweep ledger live? | A session `live_ledger_dir` with `.aw/records/`, not the mutation template. | Seed the template (REJECTED: only `run init` needs anything there, PR-005). | F-05 probe; `state_root`. | yes |
| D-2 | Exemption kinds for the twelve leaves? | Readers `sanctioned_raw` (Section 3.1); decisions/questions `not_runnable`; writers `arg_fixture_needed`. | Writers `sanctioned_raw` (REJECTED: fails registry contract); decisions/questions `sanctioned_raw` (REJECTED: no section sanctions markdown on `--json`). | `test_mutation_exemption_registry_contract`; `docs/cli-output-contract.md` Section 3.1. | yes |
| D-3 | Fix F-07/F-08 here? | No; file one backlog item (E-07). | Fix in `run_cli.py` (REJECTED: production change, outside this test-only plan's scope and pinned by `tests/test_run_recovery_cli.py`). | Plan Scope OUT clause. | yes |
| D-4 | What do the sweeps assert for the ledger leaves? | Exact measured codes, re-measured at E-01. | Membership in `{0, 1}` (REJECTED: hid PR-003). | F-04 probe. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
