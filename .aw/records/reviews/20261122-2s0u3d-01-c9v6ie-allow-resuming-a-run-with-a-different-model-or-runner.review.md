# Review findings: ipd c9v6ie

- Subject-Id: c9v6ie
- Subject-Type: ipd
- Reviewed-At: 2026-11-22
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed `.aw/records/plans/pending/20261122-2s0u3d-01-c9v6ie-allow-resuming-a-run-with-a-different-model-or-runner.ipd.md` against backlog `2s0u3d`, `agent_workflows/runner_shared.py`, `agent_workflows/agy_runipd.py`, and `agent_workflows/oc_runipd.py`. Surfaced two findings (`PR-001` and `PR-002`), both fixed in place.

`AW-TIER: standard`
`AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | Session isolation across host/model switch | .aw/records/plans/pending/20261122-2s0u3d-01-c9v6ie-allow-resuming-a-run-with-a-different-model-or-runner.ipd.md; agent_workflows/runner_shared.py | Clearing only `state["session_id"]`, `set_sessions`, and `question_resume_session` on host/model switch could leave a stale cross-host `session_id` inside an incomplete attempt's `review_steps`, causing the new host to pass the old host's session ID. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01` to clear `session_id` on incomplete `review_steps` entries alongside `state["session_id"]`, `set_sessions`, `options["session"]`, and `question_resume_session` (`D-1`). |
| PR-002 | LOW | IN-SCOPE | Resume flag validation & deduplication | .aw/records/plans/pending/20261122-2s0u3d-01-c9v6ie-allow-resuming-a-run-with-a-different-model-or-runner.ipd.md; agent_workflows/oc_runipd.py | Leaving `oc_runipd`'s standalone `--variant` resume block beside `apply_resume_host_and_model_switch` risks double-saving or ordering drift; blank `--model` validation should also execute before `load_state`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `E-01` to add `validate_resume_model_override` upfront and subsume `oc_runipd`'s standalone `--variant` override into `apply_resume_host_and_model_switch` (`D-2`). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should saved sessions be handled when switching host or model on resume? | Clear `state["session_id"]`, `state["set_sessions"]`, `options["session"]`, `state["session_item_count"]`, non-terminal `question_resume_session`, and incomplete `review_steps` `session_id` entries unless `--session` was explicitly passed on this resume. | Keep prior session IDs (rejected: causes cross-host or cross-model session errors). | `agent_workflows/runner_shared.py`, `agent_workflows/agy_runipd.py`, `agent_workflows/oc_runipd.py` | yes |
| D-2 | How should `resume` interact with `3cm15q` / `kgpptv` frozen profile contracts? | Keep `as <profile>` and `--verify-with` refused on `resume` and leave `options["launch_profile"]` untouched while supporting explicit `--model`, `--effort`, `--variant`, and `--opencode` overrides plus cross-host (`agy` <-> `oc`) handoff. | Re-resolve `runner-profiles.json` on resume (rejected: violates `3cm15q` E-04 and `kgpptv` E-02). | `agent_workflows/oc_runipd.py`, `tests/test_oc_runipd.py` | yes |
