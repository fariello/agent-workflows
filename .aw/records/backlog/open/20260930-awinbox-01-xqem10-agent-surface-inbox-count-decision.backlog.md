- Id: xqem10
- Status: open
- Set: awinbox
- Priority: low
- Work-Kind: followup
- Summary: Decide whether the aw attention inbox waiting-drops count should reach an explicit --agent/--json consumer, given that emitting it as a warning diagnostic inflates a clean record's findings from 0 to 1

## Workflow history
- 2026-09-30 created (aw backlog): Filed as the durable carrier for OQ-02 of plan olmvgw (from backlog an77ub). Owner is the maintainer: it is a question about audience and about what findings means, not about mechanism.

CARRIER for OQ-02 of plan `olmvgw` (Set `awinbox`, from backlog `an77ub`).

THE QUESTION. Plan olmvgw re-lands the advisory footer line in the aw attention HUMAN board counting raw drops waiting in .aw/inbox/. Should an EXPLICIT --agent or --json consumer receive that count too?

THE PREMISE IS NARROWER THAN WHEN THIS WAS FIRST ASKED, and that correction is why it is worth re-asking rather than inheriting. Plan 9iiqmm's OQ-04 asked the same thing believing select_output routed to OutputMode.AGENT on ANY non-TTY stdout, so it concluded the nudge reached an interactive terminal and nothing else. That is FALSE and was retracted 2026-09-19 (docs/cli-output-contract.md Section 9; select_output's docstring now reads 'TTY-NESS OF STDOUT AFFECTS COLOR ONLY, NEVER THE MODE'). Confirmed 2026-09-30: a redirected cli.main(['attention', ...]) renders the BOARD. So every agent reading aw attention through a pipe ALREADY sees the line, which was the audience the original question worried about. What remains is strictly the explicit --agent/--json case.

THREE ROUTES, COSTED, with the blocker reproduced rather than cited.

(a) LEAVE IT, which is olmvgw's scope. Zero risk; the board covers human and piped-agent readers. Cost: an explicit --agent consumer sees nothing.

(b) A WARNING Diagnostic on the agent path. This is EXACTLY the shipped precedent: attention.run already emits order_notices as severity='warning' diagnostics with the comment 'an ordering notice must reach an AGENT too, not only the human board', and it does not touch the exit code (owned by core.drift_exit_code). MEASURED COST, 2026-09-30: result_types.CommandResult.to_agent_record derives findings as len(self.diagnostics) with NO severity filter. A clean CommandResult (status='clean', exit_code=0) carrying ONE severity='warning' Diagnostic produced outcome: clean, exit: 0, findings: 1, against findings: 0 without it. A consumer reading findings as 'problems found' sees a phantom finding on a healthy repo, which is a worse contract break than the invisibility it fixes.

(c) An Evidence value key beside the existing attention key, which does NOT inflate findings. Cost: the compact agent record sanitizes evidence to the bare key name, so the number is visible only under --verbose, making it nearly as invisible as (a).

WHAT WOULD UNBLOCK ROUTE (b). The severity-blind findings tally is independently filed twice already: zosk0a (aw check reports info-severity findings as errors, keying on rule-name prefix rather than severity) and xqm16x (the same tally counting warnings as errors). If either is fixed such that a warning no longer inflates findings, route (b) becomes the cheap answer and follows a precedent already in the same function. So the sequencing matters: do not decide this against today's tally if that tally is about to change.

OWNER: maintainer. This is a judgement about who the nudge is for and about what findings promises, not a technical choice.

PRECONDITION: plan olmvgw must land first, since there is no count to surface until it does.
