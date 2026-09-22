- Id: 6if6ko
- Status: open
- Set: 6if6ko
- Priority: low
- Work-Kind: chore
- Summary: labels.command already carries the run verb, so every caller suffixing 'run' renders 'aw oc run run <id6>' in an operator-facing remedy

## Workflow history
- 2026-09-22 created (aw backlog): labels.command already carries the run verb, so every caller suffixing 'run' renders 'aw oc run run <id6>' in an operator-facing remedy

FOUND WHILE EXECUTING plan `xipfy1` (retrywire), collecting V-05's RENDERED evidence.

WHAT IS WRONG. `HostLabels.command` is `aw oc run` / `aw agy run`, i.e. it ALREADY INCLUDES THE VERB. A caller that writes `f"{labels.command} run {id6}"` therefore renders `aw oc run run xipfy1`, a command that does not exist, inside a remedy whose whole purpose is to tell an operator what to type. I hit this in my own new code and fixed it there (`runner_shared.turn_retry_remedy`, now pinned for both hosts).

WHERE. `agent_workflows/runner_shared.py`, every `{labels.command}`/`{command}` interpolation that also writes a verb; the field is `HostLabels.command`.

WHY IT IS WORTH A CARRIER RATHER THAN NOTHING. The name `command` does not say whether the verb is included, so the mistake is the NATURAL one to make, and it is invisible in state: it only appears in rendered output, which is why a test asserting on a state dict cannot catch it. I did not audit the other interpolation sites, so I am NOT claiming any are currently wrong; the point is that nothing prevents the next one.

POSSIBLE FIXES, not prescribed: (a) rename the field (or add a sibling) so the contract is in the name, e.g. `run_command` versus `cli_root`; (b) a test that renders every operator-facing remedy for both hosts and refuses a doubled verb (`run run`, `resume resume`), which is cheap and catches the whole class; (c) leave it and document the contract on the field.

WORK-KIND chore and PRIORITY low deliberately: no currently shipped message is known to be malformed, so this is prevention rather than a live defect. If an audit finds a shipped remedy printing a doubled verb, that instance IS a user-visible bug and should be reclassified.
