- Id: 1dvtiq
- Status: open
- Set: warnadvisory
- Priority: low
- Work-Kind: chore
- Summary: warning severity is not advisory: only info exempts drift_exit_code, which is a trap for the next rule author

## Workflow history
- 2026-09-21 created (aw backlog): warning severity is not advisory: only info exempts drift_exit_code, which is a trap for the next rule author

SPLIT OUT of plan 76w6mq's 'Deferred / out of scope' section so the obligation has a durable carrier instead of vanishing when that plan reaches executed.

MEASURED (re-confirmed 2026-09-21 while executing 76w6mq) by driving artifact_core.drift_exit_code with each severity value: 'error' -> 1, 'warning' -> 1, 'info' -> 0, '' (empty) -> 1. So the check engine's severity vocabulary reads as a three-level error/warning/info scale, but only 'info' is genuinely advisory: a 'warning' fails the gate exactly as an 'error' does.

WHY IT IS A TRAP RATHER THAN MERELY SURPRISING: a rule author who wants 'report it but do not fail the tree' reaches for 'warning' by name and gets a failing gate. This has already been reasoned through wrongly at least twice in-tree: 76w6mq's own E-05 was authored instructing 'register at warning so the repository does not fail its own check for documenting itself', which defeats its own stated goal, and review had to correct it to 'info'. Several shipped rules carry explanatory comments that exist only to warn the next reader about this (check.stale-index-missing, check.system-layout-missing, check.identity-absent-from-name, check.live-bug-ungated all discuss it at length).

NOT FIXED IN 76w6mq, correctly: changing what 'warning' MEANS would re-tier every existing warning-severity rule and is a separate contract decision with tree-wide exit-code consequences.

OPTIONS, for whoever takes this: (a) leave the behavior and rename the tier in the docs so the vocabulary stops implying a scale it does not have; (b) add a fourth explicitly-advisory tier; (c) make 'warning' non-failing and promote today's warning rules that SHOULD fail to 'error'. (c) is the largest and changes CI behavior. No option is obviously right, which is why this is filed for a maintainer decision rather than implemented.
