- Id: xqm16x
- Status: open
- Blocks-Release: next
- Set: xqm16x
- Priority: medium
- Work-Kind: bug
- Summary: aw check's errors/warnings tally keys on the rule NAME prefix instead of the finding's severity, so every warning is counted as an error

## Workflow history
- 2026-09-20 created (aw backlog): Found while wiring the IPD lint family into the plan sweep (lintreach k9awrq).

## Detail

`aw check`'s human summary reports an `errors` / `warnings` split that is computed from the RULE NAME
rather than from the finding's severity:

```python
err_cnt = sum(1 for d in drift if not d.rule.startswith("warn"))
warn_cnt = sum(1 for d in drift if d.rule.startswith("warn"))
```

NO rule id in `RULE_REGISTRY` starts with `warn` (every one is `check.*` or `attention.*`), so
`warn_cnt` is ALWAYS 0 and every finding is counted as an error, whatever its registered severity. The
enriched severity is available on each `Drift` (`enrich_drift` stamps it from the registry) and is what
`drift_exit_code` consumes, so the data needed is already in hand and simply is not read.

MEASURED: with a tree containing exactly one `warning`-severity finding
(`check.identity-absent-from-name`) plus one `info` advisory, the summary rendered
`errors  3   warnings  0`, while the same findings' registered severities are `warning` / `info` /
`error`. Observed while introducing `check.ipd-lint` (lintreach `k9awrq`).

USER-PERCEPTIBLE IMPACT, which is why this is `bug` rather than `chore`: the line is the operator's
at-a-glance triage signal, and it currently tells them every advisory is an error. Three registered
rules are advisory today (`check.review-decision-unescalated`, `check.identity-absent-from-name`,
`check.ipd-draft-ready-to-review`, plus the new `check.ipd-lint`), so the count is wrong on any tree
where one fires, and it misreports in the ALARMING direction. The exit code is computed separately by
`drift_exit_code` and is CORRECT, so only the displayed split is affected.

FIX SKETCH: count on `enrich_drift(d).severity` (`error` / `warning` / `info`) instead of on the rule
name, and decide whether `info` gets its own column or folds into `warnings`. Deliberately not fixed
inside `k9awrq`, whose declared `Scope-Paths` do not include `agent_workflows/cli.py`.

## Evidence

- `agent_workflows/cli.py`, the `err_cnt` / `warn_cnt` computation feeding the `rules` Evidence row
  (search for `d.rule.startswith("warn")`).
- `agent_workflows/check_engine.py`, `enrich_drift` / `RuleSpec` (the severity that should be read).
- `agent_workflows/artifact_core.py`, `drift_exit_code` (reads severity correctly, hence the exit code
  is right while the summary is wrong).
