# Assessment run report - bugs scripts

- Date / run ID: 20260712-095953
- Concern: bugs
- Scope: python scripts (install-workflows.py, versioning.py, hatch_build.py, agent_workflows/*.py, tools under .agents/workflows/*)
- IPD written: [.agents/plans/pending/20260712-0959-01-assess-bugs-in-scripts.md](file://<repo-root>/.agents/plans/pending/20260712-0959-01-assess-bugs-in-scripts.md)
- Verdict: adequate for bugs

## Top findings

| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|
| BUG-01 | Low | Low | Software engineer | Dead code pattern (`and False`) in `run_checks.py` |
| BUG-02 | Medium | Low | Software engineer | Uncaught ValueError/OverflowError in `datetime.datetime.fromtimestamp` call |
| BUG-03 | Medium | Low | Software engineer | Uncaught AttributeError in PyPI latest version lookup if response JSON is not a dictionary |
| BUG-04 | Low | Low | QA engineer | Unused variable `line_no` and default `:1` line reporting in `scan_secrets.py` history scans |

(The complete findings list is in `findings.csv`.)

## Proposed plan (summary)

- Remove dead code path `and False` in `run_checks.py`.
- Add exception handling around `fromtimestamp` in `normalize_plan_names.py` to prevent potential crashes on Windows or systems with bad timestamps.
- Validate JSON structure is a dictionary in PyPI lookup (`versioning.py`) before calling `.get()`.
- Remove the unused `line_no` variable in `scan_secrets.py`.

## Deferred (with reason)

None.

## Out-of-repo / organizational notes (if any)

None.

## Next step

Review the IPD (optionally run the `plan-review` workflow on it) and approve before execution. This workflow does not execute the plan.
