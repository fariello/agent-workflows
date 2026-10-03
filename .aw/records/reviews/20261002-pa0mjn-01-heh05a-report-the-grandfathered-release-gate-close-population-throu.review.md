# Review: Report the grandfathered release-gate close population through an opt-in advisory surface

- Subject-Id: heh05a
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged (its sha256 matched the sealed lane input), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before the edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `97c25afd1` with the shipped symbols (`_iter_items`, `_status_meta`, `_META_BLOCKS_RELEASE_RE`, `evaluate_blocking_close` with `carrier_index=_from_backlog_carrier_index(...)`, `_item_close_date`, `resolve_cutover_date`):

| Measure | Value |
|---|---|
| done items | 581 |
| done and gated | 303 |
| illegitimate (`error`) | 53 |
| cutover | `20261001` |
| latest close date | `20260926` |
| undatable | 0 |
| on or after the cutover | 0 |

`aw check release-gates --agent` gave `conforms` with exit 0. E-01's proceed branch holds. The two done counts have each moved by one since authoring, which E-01 already re-derives.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness (A) / core design claim | `agent_workflows/artifact_core.py:683` `drift_exit_code` reads `getattr(d, "severity", "")`; `agent_workflows/cli.py` check handler `exit_code = core.drift_exit_code(drift)` on the raw list; `agent_workflows/check_engine.py` `check.collisions-not-checked` constructed with `severity="info"` | The plan claims that registering the rule at `info` keeps the exit code at 0. That is false. Registry severity reaches only the enriched display copies. The exit code is scored on the raw drifts, and a bare `Drift` has `severity=""`, which counts as failing. Measured: a bare `Drift('x','check.collisions-not-checked','y')` gives `drift_exit_code` 1, and the same drift after `enrich_drift` gives 0. As written, `--grandfathered` would exit 1 on the 53 items. V-02's hand-built-drift evidence would also have passed or failed for the wrong reason. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 and E-03 now require `severity="info"` when each drift is constructed. V-02 now scores the list the function actually RETURNS and prints each `.severity`. |
| PR-002 | MEDIUM | UNDER-SCOPE | Silent failure (F) / sweep parity | `agent_workflows/check_engine.py` `check_types` calls `check_release_gates(repo_root)` with the comment "cannot diverge in their composed rule sets"; `agent_workflows/cli.py` the `check_types(...)` call passes `strict_setid_length` | The flag was threaded only into the `release-gates` target. `aw check all --grandfathered` would accept it and silently ignore it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now also threads the flag through `check_types`. E-05 adds a sweep-parity case, and V-04 adds an `aw check all --grandfathered` run. |
| PR-003 | MEDIUM | IN-SCOPE | Traceability (G) | plan OQ-01 "The classification in the detail text is what makes the cohort dismissible"; F-05 | OQ-01's resolution depends on the detail classifying the two cohorts, but no E-item or V-item required it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 requires a cohort classification derived from the carrier index. E-05 adds a cohort case, and V-03 quotes both detail strings. |
| PR-004 | MEDIUM | UNDER-SCOPE | Correctness / completeness | `agent_workflows/check_engine.py` at-rest arm `if cutover is not None:`; `RELEASE_GATE_RULES`; `tests/test_check_engine_release_gate.py::test_whole_family_rules_constant` | Two gaps. (a) With no cutover configured, the at-rest arm judges nothing, so the whole population is exempt, and the plan did not define the "complement" for that case. (b) The new rule was not added to `RELEASE_GATE_RULES`, whose membership a test pins at 8. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now specifies the no-cutover complement (report everything), makes the walk independent of `at_rest`, and adds the rule to `RELEASE_GATE_RULES` and the docstring. E-05 adds a no-cutover case and updates the family-constant test. |
| PR-005 | LOW | UNDER-SCOPE | Execution contract (Step 4) | plan `## Approval and execution gate` | The gate had no explicit honesty rule and no scope fence with the `--scope-reason`/`--scope-ack` route. It also told the executor to run `aw ipd finalize` unconditionally, with no runner-ownership condition. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the honesty rule, a declarative scope fence, and conditional runner/executor ownership of the transition. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does the advisory avoid the exit code? | Construct each drift with `severity="info"`, plus the registry entry | Registry only (measured to still exit 1); have the CLI enrich before scoring (a CLI-wide behavior change, out of scope) | `artifact_core.drift_exit_code`; `check.collisions-not-checked` precedent | yes |
| D-2 | What does `--grandfathered` mean with no cutover configured? | Report every illegitimate close, with a detail saying no cutover is configured | Report nothing (the population is then invisible, which defeats the plan's goal) | the at-rest arm's `if cutover is not None` | yes |
| D-3 | Should the flag also reach `aw check all`? | Yes, via `check_types` | `release-gates` target only (the flag would be silently ignored elsewhere) | the parity comment in `check_types` | yes |
