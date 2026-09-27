- Id: 41mtsm
- Status: open
- Blocks-Release: next
- Set: 41mtsm
- Priority: medium
- Work-Kind: bug
- Summary: git_commit_helper._is_interactive trusts stdin alone, so a driver-spawned aw verb with stdin inherited and stdout piped prints a commit prompt into the pipe and blocks; adopt artifact_adopt.leak_gate_is_interactive (or the equivalent both-streams-plus-AW_NONINTERACTIVE fence)

## Workflow history
- 2026-09-27 created (aw backlog): git_commit_helper._is_interactive trusts stdin alone, so a driver-spawned aw verb with stdin inherited and stdout piped prints a commit prompt into the pipe and blocks; adopt artifact_adopt.leak_gate_is_interactive (or the equivalent both-streams-plus-AW_NONINTERACTIVE fence)

Measured at review on Linux: git_commit_helper._is_interactive keys on stdin alone. With stdin on a real pty and stdout on a pipe (the driver shape), offer_commit(repo, ["mine.txt"], message="probe") printed 'Commit these path-scoped changes? [Y/n]' into the pipe and blocked on input() until a 20s timeout killed it. The fence used by artifact_adopt.leak_gate_is_interactive, runner_stop.interrupt_menu_is_safe, and ipd_lifecycle.run_finalize additionally requires the output stream to be a TTY and honors AW_NONINTERACTIVE/CI.
