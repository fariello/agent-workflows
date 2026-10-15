# Review findings: plan swpf3q

- Subject-Id: swpf3q
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at `461fdf679`. The plan was committed and unchanged, so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review; `--phase review-finalize` clean after revisions.

Re-verified at review HEAD:
- `runner_shared.reconcile_agent_user_config` (`:47214`) and `report_discarded_user_config` (`:47333`) match the plan; both hosts call `report_discarded_user_config(run_dir)` at run end (`oc_runipd.py:4496`, `agy_runipd.py:3720`).
- `run_viewer` imports from `runner_shared` at `:41`; `StepSummary`/`RunSummary` at `:169`/`:224`; `--json`/`--agent` payloads are `asdict(...)`, so defaulted fields flow through.
- Probe (temp repo): `aw runs --json` exit 0 on a run with two discard events; `report_discarded_user_config` printed `Agent user-config changes discarded: 2 (9y27t2: config.json ['color_depth']; 9y27t2: notes.txt)`.
- Cost probe: 200k-line, ~12 MB `events.jsonl`: per-line `json.loads` scan 0.45s, substring-prefilter scan 0.035s.
- `format_multi_run_summary` prints `Total Cost:`/`Total Tokens:` only under `if has_any_cost:`.
- `prepare_agent_user_config` `turn_key` carries a suffix that the event record does not.
- No test asserts `format_run_human` `lines[3+]`; `lines[0..2]` are pinned in `test_runtime_and_pid_inspection`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | C. Operability / performance | `run_viewer.run_viewer_cli` `summary = load_run_summary(r_dir, repo_root)` per run; review probe 0.45s vs 0.035s | The plan added an unconditional full `json.loads` scan of every listed run's `events.jsonl` to `aw runs`, which today reads that file only on a rare fallback. On large logs the cost grows with every run listed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 mandates a substring prefilter before `json.loads` and `errors="replace"`. Added F-05 with the measurement. Mutation (b) pins the exact event match behind the prefilter. |
| PR-002 | MEDIUM | IN-SCOPE | F. UX / silent failure | `run_viewer.format_multi_run_summary` `if has_any_cost:` | The multi-run line was anchored after `Total Cost:`/`Total Tokens:`, which is printed only when some step has cost. On runs without usage data the warning would silently vanish. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 places it right after the header, outside the cost block. A test and V-06 cover the no-cost case (F-06). |
| PR-003 | MEDIUM | IN-SCOPE | G. Right-sizing | plan E-03 (six sub-steps across load, single-run render, step render, multi-run aggregate) | E-03 bundled the multi-run aggregate, a separate surface with its own test needs, into the per-run work. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split into E-06 with V-06. Added a `discarded_user_config_runs` count. Dependencies, order and `Highest E allocated: 06` updated. |
| PR-004 | MEDIUM | IN-SCOPE | A. Correctness | plan E-03.3 indexing; F-07 | Indexing by `id6` was unspecified for an event matching no step and for a repeated `id6`, and execute versus verify turns cannot be told apart. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The indexing rule is now explicit: unmatched events are still counted on the run, and repeated `id6` behavior is stated. F-07 records the grain limit (no writer change; not required by `c4q9e8`). |
| PR-005 | MEDIUM | UNDER-SCOPE | E. Test sensitivity | plan E-04, V-04 | E-04 claimed the tests "fail if the wiring is reverted" but required no mutation proof. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added mutations (a) (viewer skips the reader) and (b) (exact event match dropped), with `git diff --stat` after revert. Added `tests/test_runs_subdir_root.py` to the targeted runs. |
| PR-006 | LOW | IN-SCOPE | F. KISS | plan E-03.4 synthetic fallback | A count-only fallback rendering created a second source of truth for the human line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed. The line renders only from `discarded_user_config` through the shared formatter. |
| PR-007 | LOW | IN-SCOPE | E. Conventions | `tests/test_run_viewer.py` `class RunViewerTests(TestCase)` | The new run-viewer tests were not placed in a `TestCase`, which the module and the unittest dual-runner contract use. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now requires a `TestCase` subclass and the module's fixture helpers. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract | gate; OQ-01/OQ-02 `Owner: none` | The "Stop and report" wording read as a stop on scope. Owners were `none`. Mutation edits had no no-commit rule. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate reworded so stops are only for unsafe conditions. Owners set to `plan author`. Order and the no-commit rule added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How do we bound the added viewer cost? | Substring prefilter before `json.loads` | Cache per run (new state); read only with `--detail` (hides the warning by default) | review measurement 0.45s vs 0.035s | yes |
| D-2 | Where should the multi-run line go? | After the header, unconditional on cost | Inside the cost block (hidden without usage data) | `format_multi_run_summary` `if has_any_cost:` | yes |
| D-3 | Should the plan distinguish verify-turn discards? | No (event has no turn suffix; out of scope) | Add a `turn` field to the shipped writer | `prepare_agent_user_config` `turn_key`; backlog `c4q9e8` asks for count and keys per run | yes |
