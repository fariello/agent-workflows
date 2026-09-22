- Id: ytrz7u
- Status: open
- Set: ytrz7u
- Priority: medium
- Work-Kind: chore
- Summary: prior_attempt_summary's allowlist silently drops any NEW attempt key, so a per-attempt record added for the agent is inert on the default isolated path

## Workflow history
- 2026-09-22 created (aw backlog): prior_attempt_summary's allowlist silently drops any NEW attempt key, so a per-attempt record added for the agent is inert on the default isolated path

FOUND WHILE EXECUTING plan `xipfy1` (retrywire), which needed to hand a correction packet to the next turn.

WHAT IS WRONG. `lane_containment.prior_attempt_summary` projects an ALLOWLIST (`_PRIOR_ATTEMPT_SAFE_KEYS`) for an ISOLATED turn, and isolation is the DEFAULT for an execute item. So any NEW key written onto an attempt record for the agent's benefit is SILENTLY STRIPPED before it reaches the prompt on exactly the path a real run takes. There is no warning, no test failure and no log line: the feature simply does nothing, and it does nothing only in production, because a unit test asserting on the attempt dict still passes.

WHERE. `agent_workflows/lane_containment.py`, `_PRIOR_ATTEMPT_SAFE_KEYS` and `prior_attempt_summary`; consumed by `runner_shared.build_prompt`.

WHY IT IS WORTH A CARRIER. The allowlist itself is CORRECT and must stay: its purpose is to keep absolute out-of-lane driver-side paths (`prompt`, `log", `worktree`) out of an isolated turn's prompt, and that is a real containment guarantee (spec R1.1). The defect is the FAILURE MODE, which is silent. `finalize_refused` works through this channel only because somebody remembered to add it to the list; `xipfy1` measured that a packet left on the attempt record never arrives and had to render its own prompt notice instead.

POSSIBLE FIXES, not prescribed: (a) a test that enumerates keys written onto attempt records and fails when one is neither allowlisted nor explicitly marked driver-only, which turns the silent drop into a red test; (b) a DENYLIST of the known path-bearing keys instead of an allowlist, so a new key is carried by default and only genuinely unsafe ones are stripped (note this INVERTS the fail-closed direction and needs thought about whether containment or delivery should fail closed); (c) leave the mechanism alone and document at the write sites that a new attempt key does not reach the agent, naming the notice-rendering route as the supported alternative.

NOT FILED AS A BUG because no user-visible behavior is wrong today: the two keys that use this channel are both allowlisted. It is a TRAP for the next author, which is a chore.
