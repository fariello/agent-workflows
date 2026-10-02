- Id: 3ouico
- Status: open
- Set: agentfindings
- Priority: medium
- Work-Kind: chore
- Summary: aw.agent/v1 findings counts every Diagnostic regardless of severity, so one warning-severity diagnostic reports findings 1 on a clean repo (outcome clean, exit 0), blocking the cheap route for any advisory that should reach an agent

## Workflow history
- 2026-10-02 created (aw backlog): Filed at authoring of plan qp8fn1 (Set awinbox, from backlog xqem10), which declined this obligation rather than absorbing it into a one-key addition.

MEASURED 2026-10-02 at HEAD 2b6fcd437. result_types.CommandResult.to_agent_record derives the record's findings integer as len(self.diagnostics) if self.diagnostics else self.data.get('findings', 0), with NO severity filter. A clean CommandResult (status='clean', exit_code=0) carrying ONE severity='warning' Diagnostic produced outcome: clean, exit: 0, findings: 1, against findings: 0 without it.

WHY THIS MATTERS RATHER THAN BEING COSMETIC. findings is the integer an agent reads as 'how many problems were found'. A warning-severity diagnostic is by construction not a problem that gates anything (the exit code is computed separately and correctly from the drift set alone, by artifact_core.drift_exit_code, which exempts info), so a healthy repository can report a nonzero findings count beside outcome: clean and exit: 0. attention.run already ships exactly this shape: it emits order_notices as severity='warning' diagnostics, commented 'an ordering notice must reach an AGENT too, not only the human board'.

THE CONSEQUENCE THAT PROMPTED THIS FILING. The severity-blind tally makes 'emit a warning Diagnostic' an expensive route for any advisory that ought to reach an explicit --agent consumer, because the advisory inflates findings on a clean repo. Plan qp8fn1 wanted to surface the .aw/inbox/ waiting-drops count on aw attention --agent and REFUSED that route for this reason, taking an additive scalar Evidence key instead (which does not reach findings). That workaround is correct for one count and does not generalize: a genuinely diagnostic-shaped advisory has no equivalent escape.

NOT A DUPLICATE OF zosk0a OR xqm16x, AND THIS WAS MEASURED BECAUSE backlog xqem10 ASSERTED OTHERWISE. Both of those items concern aw check's HUMAN summary tally, which keyed on a rule-NAME prefix (d.rule.startswith('warn')) instead of severity. zosk0a is done, its carrier tzjtg4 is executed with Scope-Paths agent_workflows/cli.py, tests/test_check_severity_tally.py, and the fix landed as a severity-keyed {errors, warnings, info} dict on the check Evidence row. xqm16x is graduated to approved plan nwcf8j, whose Scope-Paths are agent_workflows/doctor.py, agent_workflows/attention.py, tests/test_severity_truth_surfaces.py. NEITHER declares agent_workflows/result_types.py, and a scan of every pending plan's Scope-Paths found no plan that does. So the aw.agent/v1 findings integer is untouched by both and has no existing carrier.

FIX SKETCH, DELIBERATELY NOT A DECISION. Counting only non-info, or only error-severity, diagnostics would make findings mean 'problems' consistently with the exit code. But findings is a published aw.agent/v1 field consumed by every verb, so changing its derivation is a cross-cutting contract change: it moves the number on commands that today report a nonzero count for warnings, and docs/cli-agent-protocol.md's stability clause covers ADDITIVE changes rather than a changed field MEANING. A sibling route is to keep findings as-is and add a severity breakdown beside it. Whichever is chosen needs a tree-wide survey of which verbs emit non-error diagnostics today, plus a decision on whether the change is additive or a v2 bump.

EVIDENCE
- agent_workflows/result_types.py, CommandResult.to_agent_record (the findings derivation).
- agent_workflows/result_types.py, Diagnostic (carries severity: error | warning | info).
- agent_workflows/artifact_core.py, drift_exit_code (reads severity correctly, hence the exit code is right while the count is not).
- agent_workflows/attention.py, attention.run (ships warning-severity diagnostics for order_notices).
- docs/cli-agent-protocol.md (publishes findings and the additive-stability rule).
- .aw/records/plans/pending/20261002-awinbox-04-qp8fn1-give-an-explicit-agent-consumer-the-inbox-waiting-drops-coun.ipd.md (the plan that declined this obligation and named this carrier).
