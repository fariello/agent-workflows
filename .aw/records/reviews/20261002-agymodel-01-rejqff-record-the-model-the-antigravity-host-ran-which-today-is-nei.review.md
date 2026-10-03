# Review: Record the model the Antigravity host ran

- Subject-Id: rejqff
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

The target plan was committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified against the lane HEAD:

- `agy_runipd` has zero `observe_host_model` and zero `host_model` matches.
- The seam in `runner_shared.execute_item_core` calls `observe_host_model(session_id, options=state.get("options", {}), repo_root=repo)`, guarded by `if session_id and observe_host_model is not None`, and swallows every exception.
- `run_analytics_schema.resolve_attempt_model` falls back to `"export-session-current"` when `host_model_source` is absent.
- `render_agy_event` uses the placeholder `"antigravity"`.

Re-measured on the live host, now agy 1.2.15, one patch newer than the plan's 1.2.14:

- With no `--model`, the `init` event carries `conversation_id` and has no `model` key.
- With `--model gemini-3.8-flash-low`, the value is echoed back verbatim.

The probe ran under the gitignored `.aw/records/runs/` and was deleted afterwards.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Executability / mechanism (G) | `agent_workflows/runner_shared.py` `execute_item_core` call `observe_host_model(session_id, options=..., repo_root=repo)`; `runner_shared.attempt_log_path(run_dir, item, attempt_no, suffix)` | E-03 told the observer to "resolve the log by the same `attempt_log_path` the writer used". The seam passes no `run_dir`, `item`, `attempt_no` or log path, and `options` holds no run directory, so that cannot be done. A faithful executor would either have edited `runner_shared`, which is outside `Scope-Paths`, or produced a reader that never finds its log. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-07. E-03 now specifies that `run_agy_turn` parses the `init` line of the log it wrote into a module-level map keyed by `captured_conv_id`, always writing `None` when there is no model, and that `observe_host_model` pops from it. I demonstrated this in memory through the real `execute_item_core` with `driver_module=agy_runipd`: a modelled `init` recorded `{'host_model': 'gemini-3.8-flash-low', 'host_model_provider': '', 'host_model_source': 'init-event-echo'}`, while flagless and placeholder turns recorded `{}`. E-03, V-03 and E-05 were updated to match. |
| PR-002 | MEDIUM | UNDER-SCOPE | Correctness (A) | `agy_runipd.run_agy_turn` `if session_id: argv.extend(["--conversation", session_id])` (Set sessions reuse the id) | A per-conversation cache that is only written when a model is present would let an earlier modelled turn's value be recorded on a later flagless turn of the same conversation. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now writes the map entry on every turn, including `None`, and pops on read. Added E-05 case (d2) for a reused conversation id. |
| PR-003 | MEDIUM | IN-SCOPE | Test design honesty (D) | `tests/test_run_dashboard.py` `_write_run` / `test_antigravity_run` (fixture `state.json` read by `collect_rows`) | E-06 and F-06 claimed `test_antigravity_run` is "a live guard on the placeholder discipline". It reads a hand-written fixture and never runs an observer, so it cannot catch a reader that persists the placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both are reworded to call it a consumer-regression check. The guard role now sits with E-05 cases (b) and (c). |
| PR-004 | LOW | IN-SCOPE | Execution contract (G) | plan gate "stop and fix the reader"; "graduated by the runner on verification" | The gate told the executor to stop over a fixable in-scope defect, did not say that `Scope-Paths` is a declaration, did not say who runs finalize, and carried a stale claim about the backlog item. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The gate is rewritten. The E-01 host-behaviour stop is kept, because it is a genuine changed-prerequisite condition. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the observer reach a log the seam does not pass? | A module-level echo map populated by `run_agy_turn` and keyed by the captured conversation id | Widen the seam in `runner_shared` to pass `log_path`, which is outside `Scope-Paths` and changes the shared contract for both hosts; or scan the run's `logs/` directory by session id, which depends on filename heuristics | `runner_shared.execute_item_core` seam signature; in-memory demonstration recorded in PR-001 | yes |
| D-2 | Keep `init-event-echo` as the source label? | Keep it | Reuse `export-session-current` | `resolve_attempt_model` default; F-01 echo measurement re-run at review | yes |

### Open questions left open

OQ-01 (whether to close the flagless gap by changing launch behaviour) and OQ-02 (the verify-role key on both hosts) are maintainer decisions. They are non-blocking and remain `open`, because this run has no human interaction channel.
