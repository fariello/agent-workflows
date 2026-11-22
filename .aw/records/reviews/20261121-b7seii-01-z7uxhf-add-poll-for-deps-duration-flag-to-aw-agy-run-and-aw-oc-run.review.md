# Review findings: ipd z7uxhf

- Subject-Id: z7uxhf
- Subject-Type: ipd
- Reviewed-At: 2026-11-22
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed `.aw/records/plans/pending/20261121-b7seii-01-z7uxhf-add-poll-for-deps-duration-flag-to-aw-agy-run-and-aw-oc-run.ipd.md` against backlog `b7seii`, `agent_workflows/runner_shared.py` (`RUN_POLICY_FLAGS`, `freeze_run_policy_flags`, `enforce_freeze_time_refusal`, `initialize_run_core`), `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, and `agent_workflows/selectors.py`. Surfaced two `MEDIUM` findings (`PR-001` and `PR-002`), both fixed in place.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | R2 / R4 / Preview contract | .aw/records/plans/pending/20261121-b7seii-01-z7uxhf-add-poll-for-deps-duration-flag-to-aw-agy-run-and-aw-oc-run.ipd.md; agent_workflows/runner_shared.py::initialize_run_core | `E-02` did not specify `--prepare-only` behavior when combined with `--poll-for-deps`; entering a sleep loop under `--prepare-only` would violate `--prepare-only`'s non-blocking preview contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified in `E-02` that `--prepare-only` disables polling and evaluates dependencies immediately (`D-1`). |
| PR-002 | MEDIUM | IN-SCOPE | R1 / R4 / Cache freshness | .aw/records/plans/pending/20261121-b7seii-01-z7uxhf-add-poll-for-deps-duration-flag-to-aw-agy-run-and-aw-oc-run.ipd.md; agent_workflows/runner_shared.py::initialize_run_core; agent_workflows/selectors.py::scan_once | `E-02` did not explicitly state that `discover_plans` and `build_dynamic_manifest` must run inside each poll iteration inside a fresh `selectors.scan_once()` after `selectors._record_dirs_cached.cache_clear()`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Specified dynamic manifest rebuild and cache clearing per poll tick in `E-02` (`D-2`). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `--poll-for-deps` interact with `--prepare-only`? | Disable polling under `--prepare-only` so preview runs evaluate dependencies immediately without sleeping. | Sleep under `--prepare-only` (rejected: violates non-blocking preview contract). | `agent_workflows/runner_shared.py::initialize_run_core` | yes |
| D-2 | How should each poll tick observe newly merged `executed` plans on disk? | Run `discover_plans` / `build_dynamic_manifest` inside the poll loop inside a fresh `selectors.scan_once()` after calling `selectors._record_dirs_cached.cache_clear()`. | Reuse the initial manifest across ticks (rejected: stale manifest would never see newly executed plans). | `agent_workflows/runner_shared.py::initialize_run_core`, `agent_workflows/selectors.py::scan_once` | yes |
