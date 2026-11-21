# IPD: Truncate proposal summaries on word boundaries in perform_coordinator_proposal_file

- Date: 2026-11-21
- Kind: child
- Concern: `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` slices `proposed_change` at 24 characters (`[:24]`) without respecting word boundaries when building the filed backlog summary and IPD title, while `_write_fallback_record` in the same function uses `[:60]`. In `run-20261121T014040Z-2638602`, proposal `735ium` for IPD `60mazt` received `- Summary: Proposal from 60mazt: Create and execute a sco` and slug `proposal-from-60mazt-create-and-execute-a-sco`, splitting the word `scoped` mid-token.
- Scope: Add a small word-boundary truncation helper in `agent_workflows/runner_shared.py` (with a 60-character budget matching `_write_fallback_record`, collapsing whitespace and trimming trailing punctuation after backing up to the last word boundary when needed) and use it in both the live filing path and `_write_fallback_record` inside `perform_coordinator_proposal_file`. Add a behavioral test in `tests/test_run_proposal_channel.py` verifying that a multi-word `proposed_change` longer than 24 (and longer than 60) characters produces a filed proposal summary and filename slug that end on a complete word. EXCLUDES: lane defect backlog recovery (`8s4qhh` / `8h1q1k`).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_run_proposal_channel.py, .aw/records/plans/pending/20261121-68ympf-01-l7d19a-truncate-proposal-summaries-on-word-boundaries-in-perform-co.ipd.md
- Item-Dependencies: none
- Status: to-review
- Short-Description: Use a word-boundary truncation helper with a 60-character budget in perform_coordinator_proposal_file so proposal summaries and slugs never split words mid-token.
- Work-Kind: bug
- Priority: low
- From-Backlog: 68ympf
- Blocks-Release: next
- Set: 68ympf
- Order: 1
- Highest E allocated: 02
- Author: antigravity/gemini
- Id: l7d19a

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-21 to-review (aw set): Authored review-ready child plan graduated from backlog 68ympf
- 2026-11-21 draft (antigravity/gemini): created.

## Goal

Prevent `perform_coordinator_proposal_file` from cutting proposal summaries and filename slugs off mid-word at 24 characters by using a shared 60-character word-boundary truncation helper.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Word-boundary proposal summary truncation

- [ ] E-01 Add a helper `_truncate_proposal_summary(text: str, max_chars: int = 60) -> str` in `agent_workflows/runner_shared.py` that normalizes whitespace (`re.sub(r"\s+", " ", text).strip()`), returns the string unchanged when `len(s) <= max_chars`, and otherwise slices to `max_chars`, backs up to the last space boundary if one exists (falling back to the hard slice only for a single unbroken token longer than `max_chars`), and strips trailing punctuation/spaces. Use `_truncate_proposal_summary(proposed_change, max_chars=60)` in both `_write_fallback_record` and the live coordinator path inside `perform_coordinator_proposal_file`. Verify that the resulting `aw backlog new` and `aw ipd scaffold` filenames stay within repository filename length limits.
  - Depends on: none
  - Expected outcome: Both live and fallback proposal filing paths produce clean, complete-word summaries up to 60 characters without splitting words mid-token.
  - Execution state: pending

- [ ] E-02 Add a behavioral test in `tests/test_run_proposal_channel.py` passing a multi-word `proposed_change` longer than 60 characters (including a word straddling character 24 and another straddling character 60) through `perform_coordinator_proposal_file` for both `size="material"` (backlog) and `size="small"` (draft IPD), asserting that the filed record's summary/title ends on a complete word (no mid-word cut like `sco`) and conforms to `aw backlog check` / `ipd_lint`. Run `python3 -m pytest -o addopts="" -v tests/test_run_proposal_channel.py`, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition` on this plan, and `aw sanitize --agent`.
  - Depends on: E-01
  - Expected outcome: All proposal-channel tests, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition`, and `aw sanitize --agent` pass.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` currently computes `clean_summary = re.sub(r"[\r\n]+", " ", proposed_change).strip()[:60]` in `_write_fallback_record` and `[:24]` in the coordinator worktree loop.
- `aw backlog new` and `aw ipd scaffold` already bound derived filename slugs automatically, so a 60-character word-boundary summary keeps filenames conformant while making `- Summary:` and `# IPD:` readable.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `perform_coordinator_proposal_file` slices `proposed_change` mid-word at `[:24]`, inconsistent with `_write_fallback_record` (`[:60]`). | `agent_workflows/runner_shared.py::perform_coordinator_proposal_file`; observed in `735ium` (`Proposal from 60mazt: Create and execute a sco`). |

## Proposed changes (ordered, validatable)

1. Add `_truncate_proposal_summary(text, max_chars=60)` in `agent_workflows/runner_shared.py` and replace both `[:60]` and `[:24]` slices in `perform_coordinator_proposal_file` (`E-01`).
2. Add behavioral tests for `size="material"` and `size="small"` proposals in `tests/test_run_proposal_channel.py` and run all validation gates (`E-02`).

## Deferred / out of scope (with reason)

- Landing agent-filed defect backlog items from preserved proposal lanes: owned by sibling plan `8h1q1k` (from backlog `8s4qhh`).
  - Carrier: 8h1q1k
  - Carrier-Evidence: .aw/records/plans/executed/20261121-8s4qhh-01-8h1q1k-land-agent-filed-defect-backlog-items-on-main-when-a-lane-st.ipd.md

## Scope check

- Over-scope: none. Only `agent_workflows/runner_shared.py`, `tests/test_run_proposal_channel.py`, and this plan are modified.
- Under-scope: none. Handles multi-word strings, single-token strings over `max_chars`, newlines, and both `material` and `small` proposals.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_run_proposal_channel.py`
- `aw suite` (core tier passes)
- `make typecheck` (0 mypy errors)
- `aw ipd lint --phase pre-transition` on this plan (`outcome: "clean"`)
- `aw sanitize --agent` (`outcome: "clean"`)

## Spec / documentation sync

N/A: internal formatting bug fix in coordinator proposal filing.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result (which are reachable by construction), name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff agent_workflows/runner_shared.py` summary showing `_truncate_proposal_summary` used in both `_write_fallback_record` and the live coordinator path inside `perform_coordinator_proposal_file`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste actual output from `python3 -m pytest -o addopts="" -v tests/test_run_proposal_channel.py`, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition` on this plan, and `aw sanitize --agent`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute after review and approval (`approved` or `auto-approved`). Commit only files changed for this plan through `aw commit l7d19a -- <paths>` (never `git add -A`, bare `git add`, `git commit -a`, or `--no-verify`; never push). Finalize to `.aw/records/plans/executed/` only via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
