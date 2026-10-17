# Review findings: plan 8u071n

- Subject-Id: 8u071n
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a70271854`. The plan was byte-identical to the lane input. `aw ipd lint --phase author --agent`: `clean`. Child plan. Prerequisite `mtmqlm` is `reviewed`, not yet executed, so `question_inbox` does not exist; its contract was read from that plan.

Verified:
- `run_cli.run_cli` dispatches `decisions`/`questions` to `_emit_projection`, which reads `_projection_dir` -> `set_records.run_artifacts_dir` (workflow-artifacts only).
- `cli._register_run_leaf` adds a REQUIRED `target`; it is fed from `run_viewer.RUNS_VIEWER_LEAF_NAMES` (nine names, also used as the unresolvable-target suggestion set). `analyze`/`query`/`export`/`submit` are registered directly on `runs_sub`; `_ViewerOrLeafSubParsersAction` routes registered leaf names.
- `cli.py` `_RUNS_DESCRIPTION` and the `"runs"` family help say "Read-only, with FOUR exceptions, named rather than counted".
- `command_surface` declares `runs questions` `read`, `(0, 1, 2)`; `runs analyze` is `mutation`/`mutation_gate="none"`. `tests/conformance_matrix.required_scenarios` derives required scenarios from the declaration; `test_conformance_matrix_structure` fails on an undeclared parser leaf.
- `docs/cli-output-contract.md` Section 3.1 exempts the `aw runs` family from `aw.agent/v1`; `tests/conformance_matrix.py` records `runs questions` as `sanctioned_raw`; `tests/test_live_conformance_sweep.py` expects `runs questions` exit 1 on its ledger fixture.
- `runner_shared.state_root` resolves the runs root through project context; `run_viewer.driver_holder_state` returns LIVE/NONE/UNKNOWN by flock acquirability; `term.is_interactive`, `term.strip_ansi`, `agent_schema.validate_agent_record`, `agent_schema.normalize_repo_path` exist.
- Spec `6kwd2e` R1.7, R4a.1, R4a.2, R9.2, R9.4a, R9.5, A10c, A45 read as cited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Executability (CLI registration) | agent_workflows/cli.py:2808 `_register_run_leaf` adds required `target`; agent_workflows/run_viewer.py:3502 `RUNS_VIEWER_LEAF_NAMES` | "registered beside `decisions`/`questions`" would go through `_register_run_leaf`, making the run id required and contradicting `aw runs answer` with no run id (R9.5). | all Low | FIXED | E-01 registers directly on `runs_sub` like `analyze`, both positionals `nargs="?"`, flags mutually exclusive, dispatch in `run_cli.run_cli`. |
| PR-002 | HIGH | IN-SCOPE | Output contract | spec R9.5 / A45 "`--agent` emits an `aw.agent/v1` result"; docs/cli-output-contract.md Section 3.1; `run_cli._emit_machine` | The `aw runs` family emits bare JSON under a documented exemption; the plan did not say how this leaf emits a real `aw.agent/v1` record, so the default helper would violate A45. The exit vocabulary for `already`/refusals was undefined. | all Low | FIXED | E-03 emits through `agent_schema` with exit parity, defines exit codes for every outcome; E-04 adds a Section 3.1 sentence; `docs/cli-output-contract.md` added to Scope-Paths. |
| PR-003 | MEDIUM | UNDER-SCOPE | Documentation honesty | cli.py `_RUNS_DESCRIPTION` "FOUR exceptions, named rather than counted" | A new mutating `aw runs` leaf would make the help text false. | all Low | FIXED | E-01 updates both help strings and the epilog; declared `mutation`. |
| PR-004 | MEDIUM | IN-SCOPE | Security (terminal injection) | spec R2 question text is worker-authored; plan E-02 "show each open question" | Agent-authored text printed to the operator's terminal unfiltered could carry escape sequences. | all Low | FIXED | E-02 strips ANSI and control characters; tested in E-05, evidenced in V-02. |
| PR-005 | MEDIUM | IN-SCOPE | Correctness (resolution, liveness, regression) | `runner_shared.state_root`; `run_viewer.driver_holder_state`; tests/test_live_conformance_sweep.py `"runs questions": 1` | Hardcoded `.aw/records/runs/` breaks under a companion backend; "driver lock held" did not name the probe or the UNKNOWN case; E-04 risked changing the ledger-fixture exit the conformance sweep pins, and a never-parked runner run's result was unstated. | all Low | FIXED | E-01 uses `state_root` and `driver_holder_state` (UNKNOWN listed); E-04 keeps the Set path, defines exit 1 for a never-parked run, updates the leaf help. |
| PR-006 | MEDIUM | IN-SCOPE | Testing (live-run reachability) | plan E-05 "against a LIVE scripted run (driver still running on a later item)" | No mechanism made the driver observably live during the assertion. | all Low | FIXED | E-05 blocks item 2's scripted turn on a file barrier while the driver holds `driver.lock`; V-04 names the producing code paths. |
| PR-007 | LOW | IN-SCOPE | Process | plan OQ-01 `Owner: maintainer`; Required tests `-q` | OQ-01 was settled by the spec, not a maintainer answer; `-q` hides `N passed`. | all Low | FIXED | Owner corrected (D-1); command drops `-q` and adds the surface and conformance tests. |

`aw ipd lint --phase review-finalize --agent`: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `aw runs` or `aw run`? (OQ-01) | `aw runs answer`. | `aw run answer` (REJECTED: the spec names the verb). | spec `6kwd2e` R9.5. | yes |
| D-2 | Machine output shape? | `aw.agent/v1` result through `agent_schema`, exits 0-2. | Family bare JSON (REJECTED: A45 requires `aw.agent/v1`). | spec A45; docs/cli-output-contract.md Section 3. | yes |
| D-3 | Exit code of an `already answered` or refused answer? | 1 (completed, negative result); malformed/absent qid 2. | 0 for `already` (REJECTED: a script could not tell its answer was not applied). | docs/cli-output-contract.md Section 3 three-state rule. | yes |
| D-4 | Is a run with UNKNOWN liveness listed with no run id? | Listed and labelled. | Dropped (REJECTED: `driver_holder_state` says unknown is never proof of death). | `run_viewer.driver_holder_state` docstring. | yes |

D-2 and D-3 define a new CLI contract but no consumer exists yet, so they remain reversible before release. No finding was left `OPEN` or `DEFERRED`.
