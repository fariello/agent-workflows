- Id: em0z50
- Status: open
- Set: runnoop
- Priority: high
- Kind: bug
- Summary: aw oc run silently skips matched artifacts with no per-artifact reason and no end-of-run disposition summary (surfaced by reviewed plans counting as SUCCESS_STATES: 8/8 skipped, zero output explaining why)

## Workflow history
- 2026-08-29 created (aw backlog): aw oc run silently no-ops on reviewed plans: 'reviewed' is in SUCCESS_STATES so every step counts as already-succeeded (attempts 0) while routing to action=execute, and the driver prints no reason - no 'nothing to run / approve first' notice

OBSERVED 2026-08-29: 'aw oc run wtiso' with all 8 wtiso plans at Status: reviewed. Output was ONLY the run id, the state dir, and 'No OpenCode session was captured for this run.' The run dir WAS created (unlike i2fjf8) and 'aw runs <id>' shows '8 steps: 8 reviewed' with action=execute, Attempts: 0 for every row, an empty outcomes/, and a single 'run-created' event. Nothing was attempted and nothing explained why.

ROOT CAUSE (two interacting rules):
1. Routing: determine_action sends to-review/draft -> review and EVERYTHING ELSE -> execute, so a 'reviewed' plan gets action=execute.
2. Completion: SUCCESS_STATES = {executed, reviewed, approved} (oc_runipd.py:90) is used to decide a step already succeeded, and 'reviewed' is a member. So each reviewed step is treated as already-done and skipped before any work.
Net: 'reviewed' means BOTH 'route to execute' and 'already succeeded' - a dead zone where plans are too advanced to re-review, not approved so nothing executes them, yet counted as success. The queue exits 0 having done nothing.

WHY IT MATTERS NOW: plans pile up at 'reviewed' because the --full-auto reviewed->approved bridge never fires (see plan 97df1z / prose-gate bug). Every subsequent 'aw oc run <set>' then silently no-ops, so the user believes work is queued when nothing will ever run.

FIX (three parts; (b) and (c) are the GENERAL requirement, not specific to this bug):

(a) SEMANTICS: stop treating 'reviewed' as a success/terminal state for an execute-action step. A reviewed-but-unapproved plan is NOT runnable and NOT done - it is a distinct 'needs-approval' disposition, not a member of SUCCESS_STATES. Audit every SUCCESS_STATES use (oc_runipd.py:90 and its agy twin) and split 'review succeeded' from 'execution succeeded' (EXECUTION_SUCCESS_STATES already exists for the latter).

(b) PER-ARTIFACT LINE FOR EVERY MATCH (the general rule): every artifact the selector MATCHED gets its own output line, whether the tool acted on it or not. A skipped artifact is reported in the SAME shape as an acted-on one, with the reason it was skipped. Silence for a matched-but-untouched artifact is a bug. Examples of skip reasons that must be stated: reviewed-but-not-approved (needs approval), dependency unsatisfied (name the unmet dep), already executed (terminal), status not runnable, gate refused, filtered out by a flag. The user must never have to diff the ledger against the selector to discover what the tool ignored.

(c) END-OF-RUN DISPOSITION SUMMARY (the general rule): the run ends with a summary enumerating EVERY matched artifact and its final disposition - what the tool did to it, or why it did nothing. Include the counts per disposition and, where a disposition is actionable, the exact remedy command (e.g. 'needs-approval (8): aw ipd set approved <id6> --by-human, or re-run with --full-auto'). The summary is the authoritative answer to "what did this invocation actually do?" and must be printed even when the tool did nothing at all. Do NOT print a session-continuity footer implying a turn was attempted when none was; 'No OpenCode session was captured' currently reads like a launch failure when in fact nothing was tried.

SCOPE NOTE: (b) and (c) should be implemented as a shared reporting surface for the driver (oc + agy), not one-off prints, so every selector-driven verb reports matched-vs-acted consistently. Consider whether other selector-driven verbs (aw run, aw runs, aw ipd set, aw find) share the same gap and can adopt the same summary.

RELATED but DISTINCT: i2fjf8 is the phantom-run-id case (no run dir persisted, bogus resume hint). This item is the run-dir-written, steps-silently-counted-as-success case. Both are symptoms of the same missing reporting discipline; fix them in one pass.

TEST: (1) a run whose selector resolves only to reviewed-not-approved plans emits ONE line per matched plan stating needs-approval, emits the end-of-run summary with the per-disposition counts and the approve remedy, does NOT count those steps as 'reviewed' successes, and exits nonzero (or at minimum non-silently). (2) a mixed run (one runnable, one already-executed, one dependency-blocked, one needs-approval) emits four per-artifact lines with four distinct reasons and a summary whose counts sum to the number matched. (3) assert the summary is printed even when zero artifacts were acted on. Cover oc_runipd AND agy_runipd.
