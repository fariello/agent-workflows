- Id: rfofos
- Status: open
- Blocks-Release: next
- Set: rfofos
- Priority: high
- Work-Kind: bug
- Summary: Attended plans are skipped by the runners and need four manual steps (work begin, cd, start an agent, prompt it) to run

## Workflow history
- 2026-10-18 created (aw backlog): Attended plans are skipped by the runners and need four manual steps (work begin, cd, start an agent, prompt it) to run

Plans marked `- Attended: required` (for example lkn1zt) are frozen not-run by `aw oc run` / `aw agy run`, and `aw work begin <id6>` only allocates a worktree. To run one the maintainer must cd into the worktree, start an agent and tell it to execute the plan. Measured 2026-10-17 on lkn1zt: every run since the marker was added (four runs across both hosts) recorded attended-session-required with zero attempts. Fix (maintainer ruling 2026-10-17): `aw work begin` opens the interactive session in the worktree with the execute prompt, and both runners at a terminal pause the queue at an attended plan, open that session, and continue when it exits. Unattended runs keep holding the plan. Interim until runner turns can ask questions themselves (Set qchan, wpv9r7).
