- Id: hdxp39
- Status: open
- Set: hdxp39
- Priority: low
- Work-Kind: chore
- Summary: agent_workflows/runner_shared.py has one line that ruff-format would rewrite, so every plan touching that file must either sweep an unrelated reformat or restore it by hand

## Workflow history
- 2026-09-17 created (aw backlog): Found while executing rununify 06 (sy7uwh). At HEAD 85c14014, 'ruff format --check agent_workflows/runner_shared.py' reports the file WOULD be reformatted, at exactly one site: an implicitly-concatenated f-string return in the attempt-token helper (currently two physical lines, which ruff joins into one). Since ruff-format runs as a pre-commit hook, any agent that formats its own edits to this file also picks up that unrelated line, which then lands in a commit that does not own it; sy7uwh detected this and restored the line by hand rather than sweeping a co-worker's formatting into its own change. Concrete fix: land the one-line reformat as its own tiny commit so the file is format-clean and the next plan does not have to make the same judgement. Verify with 'ruff format --check agent_workflows/runner_shared.py' reporting 'already formatted'.
