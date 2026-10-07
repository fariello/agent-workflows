# Review findings: plan re15ol

- Subject-Id: re15ol
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T030816Z-4078927` at HEAD `f01dccb2e`. The plan was
committed and byte-identical to the sealed lane input (rev-4); no snapshot needed. `- Kind: child`, so `IPD-S407`
and `IPD-S408` do not apply. `aw ipd lint --phase author` clean before review; `review-finalize` clean after.
Order 02 (`34zv7d`, reviewed) is the dependency; `agent_workflows/loaded_code.py` does not exist yet.

Measured: `oc_runipd.build_parser().parse_args(["resume","run-x"])` and the agy twin give `output_mode='clean'`,
`verbosity=None`; `--quiet -vv` gives `quiet`, 2. `run_exit_code([executed, queued], stopped=False) == 1`, `stopped=True`
gives 0. Both hosts' `main` enter `with locked_run(run_dir):` with no `as` binding. `git log -S
test_no_call_site_was_rewritten -- tests/` lists `19313eed7`/`d4dd6b880`; `tests/test_rununify_run_queue.py` absent.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness | `oc_runipd.run_queue` `wind_down = _observe_between_turn_stop(run_dir, level, current_setid, wind_down)`; OQ-02 "before stop handling" | Restarting before the stop observation loses the in-memory wind-down and its captured level-2 set boundary, so a resumed process would stop at the wrong place. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Call placed after `_observe_between_turn_stop`; decision returns `none` while a stop level is pending; OQ-02 amended. |
| PR-002 | HIGH | IN-SCOPE | A correctness | `runner_shared.add_output_mode_flags` `sub_parser.set_defaults(output_mode="clean")`; E-02 "`--output-mode <mode>`" | No `--output-mode` flag exists; omitting the mode would make `resume` write `clean` into frozen options, resetting a `--quiet` run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 maps frozen mode to `--quiet`/`--raw` and verbosity to repeated `-v`; test asserts unchanged options. |
| PR-003 | HIGH | UNDER-SCOPE | C architecture | `oc_runipd.main` `with locked_run(run_dir):` then `run_queue(run_dir, ...)`; E-03 "add the `as lock` binding" | The loop cannot reach the lock handle; adding `as lock` in `main` does not pass it into `run_queue`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `run_lock` registers its handle in `_HELD_RUN_LOCKS`; no registered lock means no restart plus an `unavailable` event. |
| PR-004 | MEDIUM | UNDER-SCOPE | A / spec sync | Order 02 E-03 writes `loaded_code` only in `initialize_run_core`; spec A.2 "a restarted driver appends a new loaded-code record" | Nothing would append the new entry after a restart. | Low all axes | FIXED | E-01 appends it in the restart function before replacing. |
| PR-005 | MEDIUM | IN-SCOPE | A correctness | E-04 "record the refusal through `record_refusal` on no item"; `record_refusal(item, code, reason, remedy)` | `record_refusal` requires an item; "deliberate-stop path" would exit 0 for a limit refusal. | Low all axes | FIXED | Run-level `driver_restart_refusal` in state + event; loop breaks; exit 1 via `run_exit_code(stopped=False)`; summary renders it; `render_stream.py` added to Scope-Paths. |
| PR-006 | MEDIUM | IN-SCOPE | A correctness | E-01 restarts whenever changed | Restarting with nothing left to dispatch costs a process for no item. | Low all axes | FIXED | `has_work` input; `none` when no queued or deferred-integration item. |
| PR-007 | MEDIUM | OVER-SCOPE | G / right-sizing | E-05 scripted-host integration per host; `hohlc6` E-02 already drives the real driver on both hosts | Duplicates Order 05's end-to-end and bundles a large fixture into this item. | Low all axes | FIXED | E-05 keeps one real-exec case; the scripted-host run and the fresh `tool-identity-verified` assertion stay in Order 05. |
| PR-008 | LOW | IN-SCOPE | G executability | conventions cite removed pin tests; tests named missing `tests/test_agy_runipd.py`-style files; gate lacked contract wording; `AW_NO_DRIVER_RESTART` absent from E-items | Stale citations and incomplete gate. | Low all axes | FIXED | Conventions corrected; real test files listed; gate completed; decision handles the env switch. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Restart under a pending stop? | No; the stop proceeds on the current process | restart and rely on the stop file (loses set boundary) | `_observe_between_turn_stop` captures setid in memory | yes |
| D-2 | How does the loop reach the lock? | Module-level registry set by `run_lock` | add a `run_queue` parameter (touches every caller, ~87 test call sites) | `_RUN_ATTESTATIONS` precedent | yes |
| D-3 | Exit code at the restart limit | 1 (not a deliberate stop) | 0 via deliberate-stop path | `run_exit_code` measured; spec 5.3b point 5 "refuses" | yes |
| D-4 | Where does the end-to-end live? | Order 05 only | duplicate here | `hohlc6` E-02 | yes |
