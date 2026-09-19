- Id: plsx3r
- Status: open
- Blocks-Release: next
- Set: plsx3r
- Priority: low
- Work-Kind: bug
- Summary: supports_session_resume misdescribes reality (opencode-only while agy resumes via --conversation) and gates no action class

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-14 created (aw backlog): supports_session_resume misdescribes reality (opencode-only while agy resumes via --conversation) and gates no action class

MEASURED during defreport b7xarm E-05, and reported rather than fixed because host_sandbox_profile.py is NOT in that plan's Scope-Paths (its own plan explicitly forbids the fix and the wiring).

WHERE: agent_workflows/host_sandbox_profile.py, the HostSandboxCapabilities.supports_session_resume assignment.

WHAT IS WRONG, two independent things:
1. IT IS FALSE AS A DESCRIPTION. The field is set TRUE for opencode only, but antigravity demonstrably resumes a conversation: agy_runipd.run_agy_turn emits `--conversation <id>` (with `--continue` as its fallback) and agy_runipd captures the conversation id per attempt. So the capability table says agy cannot do something it does.
2. IT GATES NOTHING. ACTION_CAPABILITY_REQUIREMENTS never requires it for any action class, so nothing reads it today.

WHY IT MATTERS, concretely: it is a live trap for the next author. defreport b7xarm added a same-session re-ask that BOTH hosts perform, and wiring that re-ask to this capability would have been the natural-looking move and would have WRONGLY REFUSED agy. The plan had to carry an explicit prohibition against doing so. A capability field that is wrong AND unused will eventually be trusted by someone.

SUSPECTED FIX: either set it TRUE for antigravity (matching reality, and note the two hosts spell resume differently: --session vs --conversation), or delete the field if no action class will ever require it. Deciding which is the actual work, and it needs a test that asserts the value against each host's real argv rather than against a hand-maintained table.
