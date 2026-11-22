# Plan Review Record: c9v6ie

- Date: 2026-11-22
- Subject: .aw/records/plans/pending/20261122-2s0u3d-01-c9v6ie-allow-resuming-a-run-with-a-different-model-or-runner.ipd.md
- Subject-Id: c9v6ie
- Reviewer: antigravity/gemini
- Review-Depth: standard
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | Medium | In-scope | `agent_workflows/runner_shared.py` | `runner_shared.py` reads `last_step.get("session_id")` from incomplete `review_steps` during multi-step review resume. | Clearing only `state["session_id"]`, `set_sessions`, and `question_resume_session` on host/model switch could leave a stale cross-host `session_id` inside an incomplete attempt's `review_steps`, causing the new host to invoke `--session` with the old host's session ID. | Low | Fixed in plan | Updated `E-01` to clear `session_id` on incomplete `review_steps` entries alongside `state["session_id"]`, `set_sessions`, `options["session"]`, and `question_resume_session`. |
| PR-002 | Low | In-scope | `agent_workflows/oc_runipd.py` | `oc_runipd.py` `args.command == "resume"` already applies `args.variant` in a standalone block before `args.session`. | Leaving a duplicate `--variant` block beside `apply_resume_host_and_model_switch` risks double-saving or ordering drift; blank `--model` validation should also execute before `load_state` to stay fail-closed. | Low | Fixed in plan | Updated `E-01` to validate blank `--model` upfront (`validate_resume_model_override`) and subsume `oc_runipd`'s standalone `--variant` override into `apply_resume_host_and_model_switch`. |

### Decisions

| Decision | Choice | Rationale |
|---|---|---|
| D-01 | Preserve `3cm15q` / `kgpptv` refusal of `as <profile>` and `--verify-with` on `resume` and keep `options["launch_profile"]` untouched. | Explicit `--model`, `--effort`, `--variant`, and `--opencode` overrides satisfy credit-exhaustion handoffs without violating frozen creation-time profile invariants. |
| D-02 | Rebind `state["driver"]`, seed target `default_host_options`, and replace the prior host's model on cross-host handoff (`agy` <-> `oc`). | Prevents an OpenCode `provider/model` string from being passed to `agy` or an Antigravity model ID from being passed to `opencode`. |
