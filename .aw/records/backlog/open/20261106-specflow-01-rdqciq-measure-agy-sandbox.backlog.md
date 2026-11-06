- Id: rdqciq
- Status: open
- Set: specflow
- Priority: low
- Work-Kind: followup
- Summary: Measure what 'agy --sandbox' blocks (file reads outside the workspace?) so specflow agy participants could be labelled isolation: enforced

## Workflow history
- 2026-11-06 created (aw backlog): filed from hesuzv N-2 resolution

The Antigravity driver always passes --dangerously-skip-permissions, so a specflow (aw synth) agy participant can read peers' outputs and is recorded isolation: instruction-only (hesuzv N-2, resolved 2026-11-06). agy --help lists --sandbox ('Run in a sandbox with terminal restrictions enabled'); whether it stops file reads outside the workspace is unmeasured. Measure it; if it enforces the boundary, propose using it for specflow dispatches and relabel agy participants enforced.
