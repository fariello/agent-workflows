- Id: b7tlsh
- Status: open
- Blocks-Release: next
- Set: b7tlsh
- Priority: medium
- Work-Kind: bug
- Summary: Spec 25kzda 5.2 worked example claimed the oc descriptor proves commit-gateway enforcement that supports_commit_gateway reports False

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan 4h7tt0 (retiring RUN-NO-PUSH from spec 25kzda 4.2). Section 7's worked example asserted the CURRENT oc capability descriptor 'positively proves standard isolated-worktree, commit-gateway, hook, fresh-session, and no-push enforcement'. MEASURED at HEAD 2815aa56: probe_runner_safety_capabilities() returns supports_commit_gateway False and supports_deny_push False, both DECLARED AND NEVER PROBED (host_sandbox_profile._DECLARED_UNENFORCED), only supports_fresh_verifier_session True. So the sentence was false in TWO clauses. 4h7tt0 was authorized to fix the NO-PUSH half and reframed the whole sentence as an explicit worked-example assumption with the measurement stated, so the spec no longer misleads. THIS ITEM COVERS THE REMAINING QUESTION 4h7tt0 COULD NOT DECIDE: whether any spec text should claim commit-gateway enforcement at all, given no such enforcement exists and backlog aagh7v proposes deleting the sibling deny_push flag for exactly that reason. User-perceptible: a reader auditing 'what does the oc host guarantee' would have believed two protections were in force that fail closed.
