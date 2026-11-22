- Id: 2vj8w3
- Status: open
- Set: pubrun-bugs
- Work-Kind: bug
- Priority: high
- Summary: Do not write unignored .aw/state/checkup/last.json into legacy .agents/ or Backend:home repos without .aw/.gitignore
- Short-Description: Do not write unignored .aw/state/checkup/last.json into legacy .agents/ or Backend:home repos without .aw/.gitignore
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): Do not write unignored .aw/state/checkup/last.json into legacy .agents/ or Backend:home repos without .aw/.gitignore


## Context and observed behavior

In a legacy `.agents/` repository (such as `pubrun` before `--to-aw`, with `Backend: home` and no `.aw/.gitignore`), `agent_workflows/checkup.py::checkup_dir` delegates to `agent_workflows/ipd_lifecycle.py::control_state_dir`. Because `control_state_dir` only redirects to `AW_HOME` for `clean-delta` repositories, it creates `<repo>/.aw/state/checkup/last.json` directly inside the target checkout even though `.aw/state/` is not gitignored there. This leaves `?? .aw/state/` in `git status` and risks accidental commits of runtime state.

## Acceptance criteria

- `agent_workflows/ipd_lifecycle.py::control_state_dir` (or `agent_workflows/checkup.py::checkup_dir`) must not leave unignored `.aw/state/` files in a legacy `.agents/` repository or a `Backend: home` repository lacking `.aw/.gitignore`.
- Either route runtime state to `AW_HOME` when the repository has no canonical `.aw/` layout (or uses `Backend: home`), or ensure `.aw/.gitignore` protects `/state/` before writing.
- Behavioral tests verify `aw checkup` leaves `git status --porcelain` clean on a legacy `.agents/` repository.
