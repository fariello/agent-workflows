- Id: 144b3x
- Status: open
- Set: 144b3x
- Priority: medium
- Work-Kind: chore
- Summary: driver_finalize discards finalize_precheck's structured findings, forcing prose matching on the refusal message

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing plan zzcrlo (finalback). `ipd_lifecycle.finalize_precheck` computes a structured `findings: Tuple[str, ...]` alongside its (exit_code, message), and `run_finalize` can already emit a machine-readable CommandResult with typed diagnostics under --agent/--json. But both drivers' `driver_finalize` shell out to `aw ipd finalize` WITHOUT --agent and keep only `(returncode, combined_output)`, so the structure is destroyed at the subprocess boundary. Consequence measured in zzcrlo: the send-back's retryable-class allowlist (`runner_shared.finalize_refusal_is_retryable`) has to match FINDING PROSE ('not \'performed\' at pre-transition' and two siblings) because no structured path reaches the runner. That works and is pinned by a test against the real `ipd_lint` output, but it is brittle by construction: a reworded diagnostic silently changes which refusals are retryable. FIX: have driver_finalize request --agent (or --json) and parse the typed diagnostics, then key the classification on codes//structure instead of prose. WHERE: agent_workflows/oc_runipd.py driver_finalize, agent_workflows/agy_runipd.py driver_finalize, agent_workflows/runner_shared.py RETRYABLE_FINALIZE_FINDING_TEXTS.
