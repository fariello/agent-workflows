- Id: fbxkvo
- Status: graduated
- Graduated-To: fbxkvo
- Set: pubrun-bugs
- Work-Kind: bug
- Priority: medium
- Summary: Relocate .agents/*/untracked/ during --to-aw and stop migrate_local_lanes_to_untracked from recreating untracked .agents/prompts/.gitignore
- Short-Description: Relocate .agents/*/untracked/ during --to-aw and stop migrate_local_lanes_to_untracked from recreating untracked .agents/prompts/.gitignore
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 graduated (aw backlog): graduated by run run-20261122T002647Z-1444530: 2cv6rz
- 2026-11-22 created (aw backlog): Relocate .agents/*/untracked/ during --to-aw and stop migrate_local_lanes_to_untracked from recreating untracked .agents/prompts/.gitignore


## Context and observed behavior

During `aw install --to-aw` on `pubrun`, `layout_migration` migrated tracked files out of `.agents/prompts/` (moving `.agents/prompts/.gitignore` to `.aw/records/prompts/.gitignore`) while leaving the gitignored `.agents/prompts/untracked/20260722-0002-01-session-handoff-resume.md` behind on disk. Immediately afterward, `agent_workflows/engine.py::migrate_local_lanes_to_untracked` iterated `_lane_bases` (which unconditionally includes `repo_root / ".agents" / "prompts"`), saw `.agents/prompts/untracked/` still present, and called `_ensure_untracked_gitignore` - recreating `.agents/prompts/.gitignore` as a brand-new untracked file (`?? .agents/prompts/.gitignore` under `git status -u`) on every subsequent `aw install`.

## Acceptance criteria

- `aw install --to-aw` relocates existing `.agents/prompts/untracked/` and `.agents/comms/untracked/` contents into `.aw/records/prompts/untracked/` and `.aw/records/comms/untracked/` (non-clobbering) and prunes emptied legacy directories.
- On a canonical `.aw/` repository, `agent_workflows/engine.py::migrate_local_lanes_to_untracked` does not recreate `.agents/prompts/.gitignore` or `.agents/comms/.gitignore`.
- Behavioral tests verify `aw install --to-aw` on a repo containing `.agents/prompts/untracked/<file>` migrates the file and leaves `git status -u --porcelain` free of `.agents/prompts/.gitignore`.
