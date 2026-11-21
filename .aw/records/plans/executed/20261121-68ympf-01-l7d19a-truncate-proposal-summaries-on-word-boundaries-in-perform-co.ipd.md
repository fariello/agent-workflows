# IPD: Truncate proposal summaries on word boundaries in perform_coordinator_proposal_file

- Date: 2026-11-21
- Kind: child
- Concern: `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` slices `proposed_change` at 24 characters (`[:24]`) without respecting word boundaries when building the filed backlog summary and IPD title, while `_write_fallback_record` in the same function uses `[:60]`. In `run-20261121T014040Z-2638602`, proposal `735ium` for IPD `60mazt` received `- Summary: Proposal from 60mazt: Create and execute a sco` and slug `proposal-from-60mazt-create-and-execute-a-sco`, splitting the word `scoped` mid-token.
- Scope: Add a word-boundary truncation helper `_truncate_proposal_summary(text: str, max_chars: int = 60) -> str` and a word-boundary slug helper `_truncate_proposal_slug(text: str, max_chars: int = 50) -> str` in `agent_workflows/runner_shared.py`, and use them in both the live filing path and `_write_fallback_record` inside `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` (passing `--slug` to `aw backlog new` for `size="material"` so both `- Summary:` and the `.backlog.md` filename slug end on complete words without hitting `agent_workflows/backlog.py::run_new`'s 50-character `kebab_slug` hard slice, while `size="small"` produces a complete-word `# IPD:` title via `aw ipd scaffold` whose derived filename slug remains bounded by `agent_workflows/artifact_core.py::kebab_slug`). Add behavioral and helper unit tests in `tests/test_run_proposal_channel.py` covering `size="material"`, `size="small"`, `_write_fallback_record` (held lock), and edge cases (words straddling character 24 and character 60, word ending exactly at `max_chars`, single unbroken token over `max_chars`, trailing punctuation, and embedded newlines/tabs). EXCLUDES: lane defect backlog recovery (`8s4qhh` / `8h1q1k`) and changing `agent_workflows/artifact_core.py::kebab_slug` globally.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_run_proposal_channel.py, .aw/records/plans/pending/20261121-68ympf-01-l7d19a-truncate-proposal-summaries-on-word-boundaries-in-perform-co.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: standard
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

- 2026-11-21 executed (aw agy run model=Gemini-4-Neon-High): aw agy run self-finalize: l7d19a verified (set 68ympf, attempt 2).
- 2026-11-21 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 FIXED
- 2026-11-21 /plan-review (antigravity/gemini-4-neon-high): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 FIXED; review record .aw/records/reviews/20261121-68ympf-01-l7d19a-truncate-proposal-summaries-on-word-boundaries-in-perform-co.review.md
- 2026-11-21 to-review (aw set): Authored review-ready child plan graduated from backlog 68ympf
- 2026-11-21 draft (antigravity/gemini): created.

## Goal

Prevent `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` from cutting proposal summaries, IPD titles, and backlog filename slugs off mid-word at 24 characters by using shared 60-character summary and 50-character backlog-slug word-boundary truncation helpers.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Word-boundary proposal summary truncation

- [x] E-01 Add two small helpers in `agent_workflows/runner_shared.py`:
  1. `_truncate_proposal_summary(text: str, max_chars: int = 60) -> str`: normalize whitespace (`re.sub(r"\s+", " ", text).strip()`), return `s` unchanged when `len(s) <= max_chars`; otherwise check `s[: max_chars + 1]` for the last space so a word ending *exactly* at `max_chars` (`s[max_chars] == " "`) is preserved rather than dropped, falling back to `s[:max_chars]` only for a single unbroken token longer than `max_chars`; strip trailing punctuation and spaces (`" .,;:!?-_/([{'\""`), falling back to the unstripped cut (never returning `""` for non-empty `s`) if stripping empties the string.
  2. `_truncate_proposal_slug(text: str, max_chars: int = 50) -> str`: convert `text` with `agent_workflows/artifact_core.py::kebab`, return unchanged when `len(k) <= max_chars`, otherwise check `k[: max_chars + 1]` for the last `"-"` boundary (preserving a token ending exactly at `max_chars` and falling back to `k[:max_chars].strip("-")` only for a single unbroken token longer than `max_chars`), and default to `"proposal"` if empty.
  3. Wire `_truncate_proposal_summary(proposed_change, max_chars=60)` into both `_write_fallback_record` and the live coordinator path inside `agent_workflows/runner_shared.py::perform_coordinator_proposal_file`, and pass `["--slug", _truncate_proposal_slug(summary, max_chars=50)]` to `aw backlog new` in the `size="material"` branch so `agent_workflows/backlog.py::run_new`'s 50-character `kebab_slug` hard slice never splits a word in the backlog filename slug.
  - Depends on: none
  - Expected outcome: Both live and fallback proposal filing paths produce clean, complete-word summaries/titles up to 60 characters, and `size="material"` backlog filenames carry complete-word slugs up to 50 characters within repository naming rules.
  - Execution state: performed

- [x] E-02 Add behavioral and helper unit tests in `tests/test_run_proposal_channel.py` (strictly behavioral, zero source-code inspection via `inspect`/`ast`/regex/`read_text` per `GUIDING_PRINCIPLES` P16):
  1. Unit tests for `_truncate_proposal_summary` and `_truncate_proposal_slug` covering: short strings unchanged, multi-word strings longer than 60/50 chars, a word ending *exactly* at `max_chars` (not dropped), a single unbroken token longer than `max_chars`, embedded newlines/tabs, trailing punctuation at the cut, and all-punctuation prefix fallback (non-empty).
  2. Live coordinator tests driving `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` with a multi-word `proposed_change` longer than 60 characters (containing a word straddling character 24 and another straddling character 60):
     - For `size="material"`: assert `- Summary:` ends on a complete word (no mid-word cut like `sco`), the `.backlog.md` filename slug (`<= 50` chars) ends on a complete word and passes `agent_workflows/artifact_naming.py::parse_clustered`, and `agent_workflows/backlog.py::validate_item` returns zero drift.
     - For `size="small"`: assert `# IPD:` title ends on a complete word (no mid-word cut at 24 or 60), and the scaffolded `.ipd.md` file conforms to `agent_workflows/ipd_lint.py` (`author` / draft checks) and clustered filename rules.
  3. Fallback path test (held `integration_lock`, matching `test_coordinator_performer_held_integration_lock`) verifying `_write_fallback_record` uses `_truncate_proposal_summary` on word boundaries for both `size="material"` and `size="small"`.
  Run `python3 -m pytest -o addopts="" -v tests/test_run_proposal_channel.py`, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition` on this plan, and `aw sanitize --agent`.
  - Depends on: E-01
  - Expected outcome: All proposal-channel tests, `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition`, and `aw sanitize --agent` pass.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` currently computes `clean_summary = re.sub(r"[\r\n]+", " ", proposed_change).strip()[:60]` in `_write_fallback_record` and `[:24]` in the coordinator worktree loop.
- `agent_workflows/backlog.py::run_new` derives the backlog filename slug via `agent_workflows/artifact_core.py::kebab_slug(args.slug or item.summary or "item", 50, "item")`, which hard-slices `kebab(text)[:50]`. Because `"Proposal from <id6>: "` is 22 characters (21 kebab chars), passing a 60-character `clean_summary` without `--slug` still produces an 82-character summary that `kebab_slug` cuts mid-word at 50 characters. Passing `--slug` (already supported by `aw backlog new`) guarantees a complete-word backlog slug.
- `agent_workflows/ipd_authoring.py` derives the IPD filename slug via `agent_workflows/artifact_core.py::kebab_slug(title, 60, "ipd")` and has no `--slug` CLI flag on `aw ipd scaffold`; therefore `# IPD:` title uses the 60-character word-boundary helper while IPD filename slug truncation remains owned by `artifact_core.kebab_slug`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `agent_workflows/runner_shared.py::perform_coordinator_proposal_file` slices `proposed_change` mid-word at `[:24]`, inconsistent with `_write_fallback_record` (`[:60]`), and does not pass a word-boundary `--slug` to `aw backlog new`. | `agent_workflows/runner_shared.py::perform_coordinator_proposal_file`; `agent_workflows/backlog.py::run_new`; observed in `735ium` (`Proposal from 60mazt: Create and execute a sco`, slug `proposal-from-60mazt-create-and-execute-a-sco`). |

## Proposed changes (ordered, validatable)

1. Add `_truncate_proposal_summary(text, max_chars=60)` and `_truncate_proposal_slug(text, max_chars=50)` in `agent_workflows/runner_shared.py`, replace both `[:60]` and `[:24]` slices in `perform_coordinator_proposal_file`, and pass `--slug` to `aw backlog new` (`E-01`).
2. Add helper unit tests and behavioral tests for `size="material"`, `size="small"`, and `_write_fallback_record` in `tests/test_run_proposal_channel.py` and run all validation gates (`E-02`).

```mermaid
flowchart TD
    A[Normalize whitespace in proposed_change] --> B{len <= max_chars?}
    B -->|Yes| C[Return normalized text]
    B -->|No| D{Space in text[:max_chars + 1]?}
    D -->|Yes| E[Slice at last space boundary]
    D -->|No| F[Hard-slice single token at max_chars]
    E --> G[Strip trailing punctuation; keep pre-strip cut if empty]
    F --> G
    G --> H[Build Proposal from id6 summary/title]
    H --> I{size == material?}
    I -->|Yes| J[Pass summary and word-boundary --slug <= 50 chars to aw backlog new]
    I -->|No| K[Pass title to aw ipd scaffold or fallback writer]
```

## Deferred / out of scope (with reason)

- Landing agent-filed defect backlog items from preserved proposal lanes: owned by sibling plan `8h1q1k` (from backlog `8s4qhh`).
  - Carrier: 8h1q1k
- Changing `agent_workflows/artifact_core.py::kebab_slug` globally to truncate on hyphen/word boundaries (which affects `aw ipd scaffold`, `aw specs new`, `aw prompts`, and migration renames across the repository): out of scope for this coordinator proposal-filing fix.
  - Carrier-Declined: `artifact_core.kebab_slug` is shared across all record types and migrations; changing it globally risks altering filename expectations across unrelated commands and tests, whereas passing `--slug` to `aw backlog new` fixes the observed proposal backlog defect without cross-tree blast radius.

## Scope check

- Over-scope: none. Only `agent_workflows/runner_shared.py`, `tests/test_run_proposal_channel.py`, and this plan are modified.
- Under-scope: none. Handles multi-word strings, exact-boundary words, single-token strings over `max_chars`, trailing punctuation, newlines/tabs, `--slug` for `material` proposals, `small` proposals, and `_write_fallback_record`.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_run_proposal_channel.py`
- `aw suite` (core tier passes)
- `make typecheck` (0 mypy errors)
- `aw ipd lint --phase pre-transition` on this plan (`outcome: "clean"`)
- `aw sanitize --agent` (`outcome: "clean"`)

## Spec / documentation sync

N/A: internal formatting bug fix in coordinator proposal filing; no CLI flags, user-facing documentation, or specification contracts change.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result (which are reachable by construction), name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `git diff agent_workflows/runner_shared.py` summary showing `_truncate_proposal_summary` (with exact-boundary preservation and non-empty punctuation-strip fallback) used in both `_write_fallback_record` and the live coordinator path inside `perform_coordinator_proposal_file`, plus `_truncate_proposal_slug` passed via `--slug` to `aw backlog new`.
  - Observed evidence: `git diff agent_workflows/runner_shared.py`:
    - Added `_PROPOSAL_SUMMARY_STRIP_CHARS = " .,;:!?-_/([{'\""`, `_truncate_proposal_summary(text: str, max_chars: int = 60) -> str` (collapses whitespace via `re.sub(r"\s+", " ", text).strip()`, returns `s` if `len(s) <= max_chars`, checks `s[: max_chars + 1].rfind(" ")` to preserve words ending at `max_chars` with `s[:max_chars]` single-token fallback, and returns `raw_cut.rstrip(_PROPOSAL_SUMMARY_STRIP_CHARS) or raw_cut`), and `_truncate_proposal_slug(text: str, max_chars: int = 50) -> str` (converts via `artifact_core.kebab`, checks `k[: max_chars + 1].rfind("-")`, falls back to `k[:max_chars].strip("-")` or `"proposal"`).
    - In `_write_fallback_record`: replaced `re.sub(r"[\r\n]+", " ", proposed_change).strip()[:60]` with `clean_summary = _truncate_proposal_summary(proposed_change, max_chars=60)`.
    - In live coordinator path of `perform_coordinator_proposal_file`: replaced `re.sub(r"[\r\n]+", " ", proposed_change).strip()[:24]` with `clean_summary = _truncate_proposal_summary(proposed_change, max_chars=60)`.
    - In the `size="material"` branch: added `slug = _truncate_proposal_slug(summary, max_chars=50)` and passed `"--slug", slug` in `backlog_args` to `aw backlog new`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste actual output from `python3 -m pytest -o addopts="" -v tests/test_run_proposal_channel.py` (showing helper unit tests and live/fallback behavioral tests passing with zero source-code inspection), `aw suite`, `make typecheck`, `aw ipd lint --phase pre-transition` on this plan, and `aw sanitize --agent`.
  - Observed evidence:
    - `python3 -m pytest -o addopts="" -v tests/test_run_proposal_channel.py`: `42 passed in 12.11s` (including all 12 unit tests in `TestProposalSummaryTruncation`, `test_coordinator_material_proposal_truncates_summary_and_slug_on_word_boundaries`, `test_coordinator_small_proposal_truncates_title_on_word_boundary`, and `test_coordinator_fallback_record_truncates_on_word_boundary[material|small]`, zero source-code inspection).
    - `aw suite`: `2653 passed, 11 warnings in 89.74s (0:01:29)` (exit 0).
    - `make typecheck`: `python3 -m mypy agent_workflows` -> `Success: no issues found in 228 source files` (exit 0).
    - `aw ipd lint --phase pre-transition --agent .aw/records/plans/pending/20261121-68ympf-01-l7d19a-truncate-proposal-summaries-on-word-boundaries-in-perform-co.ipd.md`: `{"schema":"aw.agent/v1","kind":"result","cmd":"ipd lint","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["plans-lint"],"next":null}`.
    - `aw sanitize --agent`: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6855,"findings":0,"evidence":["leak-scan"],"next":null}`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review (`Status: reviewed`), human approval (`Status: approved` or `auto-approved`), and with all blocking open questions resolved. Scope fence: edits are declared in `- Scope-Paths:` (`agent_workflows/runner_shared.py`, `tests/test_run_proposal_channel.py`, and this plan); if execution requires touching an undeclared path or leaving a declared path unmodified, document it at finalization with `--scope-reason PATH=WHY` or `--scope-ack PATH[=NOTE]`. Shared-checkout safety: never revert, stage, commit, discard, or reformat unrelated changes or untracked files belonging to another agent or human. Honesty rule (hard MUST): paste the actual runner output for every required test and validation command in `V-01..V-02`; never claim a check passed without running it. Commit only files changed for this plan through `aw commit l7d19a -- <paths>` (never `git add -A`, bare `git add`, `git commit -a`, or `--no-verify`; never push). Lifecycle transition: never hand-roll `git mv` into `.aw/records/plans/executed/`; after `aw ipd lint --phase pre-transition` reports `clean` and every `V-*` reads `pass` with pasted evidence, when executed by a runner with `self_finalize=True` leave finalization to the driver, and when executed directly or attended run `aw ipd finalize l7d19a` to move the plan to `.aw/records/plans/executed/`.
