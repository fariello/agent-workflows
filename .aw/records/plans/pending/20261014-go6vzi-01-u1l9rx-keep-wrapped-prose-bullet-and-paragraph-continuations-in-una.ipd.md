# IPD: Keep wrapped prose bullet and paragraph continuations in unattached_section_prose so orchestrator coverage sees wrapped child owners

- Date: 2026-10-14
- Kind: child
- Concern: `ipd_lint.unattached_section_prose` drops all indented lines (`if raw[:1].isspace(): continue`), truncating hard-wrapped prose bullets and paragraphs in allowlisted orchestrator sections (`## Completion criteria (the whole Set is done only when)`, `## Cross-IPD validation`, `## Required tests / validation`, etc.) at their first newline and hiding child-owner attributions (`OWNER: <child-id6>`) that wrap onto continuation lines.
- Scope: Update `ipd_lint.unattached_section_prose` to keep indented non-subfield continuation lines that immediately continue an unattached prose bullet or paragraph and join them onto the preceding kept line while still dropping indented lines that follow a checklist leaf, a `- Key: value` subfield, a heading, or a blank line; update the `runner_shared.probe_cache_payload` and `runner_shared.probe_cache_digest` docstrings to reflect the narrowed exclusion; and add behavioral tests in `tests/test_orchestrator_probe_payload.py` pinning wrapped `OWNER: <child-id6>` bullet extraction, `E-*` continuation exclusion, and subfield-continuation exclusion.
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/runner_shared.py, tests/test_orchestrator_probe_payload.py, .aw/records/plans/pending/20261014-go6vzi-01-u1l9rx-keep-wrapped-prose-bullet-and-paragraph-continuations-in-una.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: go6vzi
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: go6vzi
- Order: 1
- Highest E allocated: 03
- Author: Antigravity
- Id: u1l9rx
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record 20261014-go6vzi-01-u1l9rx)
- 2026-10-14 to-review (aw set): authored review-ready plan for go6vzi

- 2026-10-14 draft (Antigravity): created.

## Goal

Ensure `ipd_lint.unattached_section_prose` (and therefore `runner_shared.probe_cache_payload`, `runner_shared.probe_cache_digest`, and `runner_shared.orchestrator_probe_excerpt`) preserves and joins indented continuation lines of unattached prose bullets and paragraphs while still excluding indented lines that follow a checklist leaf (`_LEAF_RE`), a subfield (`_SUBFIELD_RE`), a heading, or a blank line. This prevents the orchestrator coverage probe from seeing truncated first lines of wrapped bullets and falsely refusing sets whose `OWNER: <child-id6>` attribution wraps onto a continuation line (as measured on orchestrator `m0kl28` prior to commit `592bfbf0b`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Join unattached prose continuation lines in `ipd_lint.unattached_section_prose`

- [ ] E-01 Update `ipd_lint.unattached_section_prose` (`def unattached_section_prose(text: str) -> dict[str, str]:` in `agent_workflows/ipd_lint.py`) so that indented non-subfield lines immediately continuing an unattached prose bullet or paragraph are kept and joined with `" "` onto the preceding kept line in `sections[current_h2]`, while indented lines following a checklist leaf (`_LEAF_RE`), a subfield (`_SUBFIELD_RE`), a heading (`_H2_RE` / `_H3_RE`), or a blank line (`not raw.strip()`) are still dropped.
  - Depends on: none
  - Expected outcome: `ipd_lint.unattached_section_prose` tracks a per-section boolean `in_prose` (initialized `False` and reset to `False` on `_H2_RE`, `_H3_RE`, `_LEAF_RE`, `_SUBFIELD_RE`, and blank lines `not raw.strip()`, checked before `raw[:1].isspace()`). When `raw[:1].isspace()` is true and `in_prose` is `True` (with `sections[current_h2]` non-empty), `unattached_section_prose` joins the stripped continuation onto the last kept line (`sections[current_h2][-1] = f"{sections[current_h2][-1].rstrip()} {raw.strip()}"`) and keeps `in_prose = True` so multi-line wrapped bullets and paragraphs become single joined lines; when `in_prose` is `False`, the indented line is dropped. Structural disjointness with `ipd_lint.leaf_action_blocks` / `runner_shared.e_item_action_blocks` continues to hold by construction (`0` shared lines over 40 characters across all 91 corpus orchestrators), and the function docstring documents the updated continuation rule.
  - Execution state: pending

- [ ] E-02 Update the docstrings of `runner_shared.probe_cache_payload` (`def probe_cache_payload(orchestrator_text: str) -> dict[str, Any]:` in `agent_workflows/runner_shared.py`) and `runner_shared.probe_cache_digest` (`def probe_cache_digest(orchestrator_text: str) -> str:` in `agent_workflows/runner_shared.py`) so the `WHAT THE ALLOWLIST AND EXTRACTOR DO NOT REACH` and `NOT COVERED` notes state that indented continuation lines of unattached prose bullets and paragraphs are joined and covered while indented lines following a checklist leaf or `- Key: value` subfield remain excluded from `prose_sections` (pinned by `c3`).
  - Depends on: E-01
  - Expected outcome: Both docstrings in `agent_workflows/runner_shared.py` accurately describe the narrowed residual indented-line exclusion and note the one-time coverage-fingerprint shift for orchestrators with wrapped prose bullets (`go6vzi`). The `probe_cache_payload` residual-gap bullet's measured figures ("476 lines (74,625 characters) ... 14 hazard hits") describe the OLD all-indented exclusion and become false; either RE-MEASURE them against the new extractor at execution time (indented non-subfield lines inside allowlisted sections that still reach neither extractor, over all `- Kind: orchestrator` plans) and record the new figures with the date, or replace them with a qualitative statement. Do not leave the old numbers.
  - Execution state: pending

### Task group 2: Behavioral regression tests in `tests/test_orchestrator_probe_payload.py`

- [ ] E-03 Add behavioral tests in `tests/test_orchestrator_probe_payload.py` (`class TestProbePayloadDefaultSuite(unittest.TestCase):`) verifying wrapped prose bullet joining, `OWNER: <child-id6>` preservation in `orchestrator_probe_excerpt`, digest sensitivity to continuation-line edits, and continued exclusion of `E-*` leaf and subfield continuation lines.
  - Depends on: E-01, E-02
  - Expected outcome: `TestProbePayloadDefaultSuite` gains tests confirming that: (1) an orchestrator whose `## Completion criteria (the whole Set is done only when)` bullet wraps `OWNER: syn002 (executed).` onto an indented continuation line (and a three-line wrapped bullet) yields an `orchestrator_probe_excerpt` and `probe_cache_payload["prose_sections"]` containing the joined full bullet on one line with `OWNER: syn002 (executed).` present, produces the exact same `probe_cache_digest` as the single-line unwrapped bullet, and changes `probe_cache_digest` when the wrapped continuation line is edited; and (2) an `E-*` checklist leaf's indented continuation line (as well as an indented line following a blank line after a leaf or following a `- Key: value` subfield) is excluded from `unattached_section_prose` and `probe_cache_payload["prose_sections"]` while the leaf's continuation remains in `probe_cache_payload["e_items"]`. Both `python3 -m pytest tests/test_orchestrator_probe_payload.py` (default suite) and `python3 -m pytest tests/test_orchestrator_probe_payload.py -m livecorpus -o addopts=""` pass with zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_lint.unattached_section_prose` (`def unattached_section_prose(text: str) -> dict[str, str]:` in `agent_workflows/ipd_lint.py`) walks `ipd_lint._structural_lines(text or "")` (`def _structural_lines(text: str) -> List[Tuple[int, str]]:`), which already strips YAML front matter, fenced code blocks (`_FENCE_RE`), 4-space/tab indented code blocks (`if raw.startswith("    ") or raw.startswith("\t"):`), and block quotes (`>`), while yielding 1-to-3-space indented lines (including 2-space wrapped bullet continuations and leaf subfields) and blank lines.
- `ipd_lint.leaf_action_blocks` (`def leaf_action_blocks(text: str, leaves: Iterable[Leaf]) -> tuple[str, ...]:` in `agent_workflows/ipd_lint.py`, called by `runner_shared.e_item_action_blocks`) anchors on each `Leaf.line` and reads forward through indented continuation lines, stopping at the first blank line (`if not stripped: break`), next leaf (`- [`), heading (`#`), subfield (`_SUBFIELD_RE`), or non-indented line (`if not raw[:1].isspace(): break`), and joins the collected lines with `" ".join(...)`.
- `runner_shared.probe_cache_payload` (`def probe_cache_payload(orchestrator_text: str) -> dict[str, Any]:` in `agent_workflows/runner_shared.py`) is the single function backing both `runner_shared.probe_cache_digest` and `runner_shared.orchestrator_probe_excerpt`, so updating `ipd_lint.unattached_section_prose` updates both the prompt excerpt and the coverage fingerprint together by construction.
- `runner_shared.PROBE_PROMPT_TEMPLATE` (`PROBE_PROMPT_TEMPLATE = (` in `agent_workflows/runner_shared.py`) instructs the model to copy each uncovered obligation quote verbatim "on one line", so joining wrapped bullet continuations onto their opening bullet line in `unattached_section_prose` ensures the model both reads the complete bullet (including a wrapped `OWNER: <child-id6>`) and can quote an uncovered wrapped bullet on one line.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- All tests must test observable behavior and outcomes (`AGENTS.md`, `GEMINI.md` Rule 6: no `inspect`, `ast`, regex, or substring checks on production source).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | `ipd_lint.unattached_section_prose` unconditionally drops every indented line (`if raw[:1].isspace(): continue`), severing hard-wrapped prose bullets and paragraphs at their first newline. | In `agent_workflows/ipd_lint.py` (`def unattached_section_prose(text: str) -> dict[str, str]:`), after skipping `_H3_RE`, `_LEAF_RE`, and `_SUBFIELD_RE`, `if raw[:1].isspace(): continue` discards every 1-to-3-space continuation line yielded by `_structural_lines`. On orchestrator `m0kl28` prior to commit `592bfbf0b`, three `## Completion criteria (the whole Set is done only when)` bullets wrapped `OWNER: nxh5s4 (executed)` and `OWNER: nxh5s4 and rozdkp` onto 2-space indented continuation lines; `orchestrator_probe_excerpt` sent only the truncated first lines (`- A capability on ... set True`, `- The probe returns False, ... create a`, `- No action is gated: ... stays`), causing 5 consecutive `IPD-S408` `coverage-fail` refusals on 2026-10-11 before commit `592bfbf0b` unwrapped the bullets onto single lines. |
| F-02 | Keeping and joining indented lines when and only when they continue an unattached prose line preserves structural disjointness with `e_item_action_blocks` and preserves the `c3` subfield-continuation pin. | `leaf_action_blocks` (`def leaf_action_blocks(text: str, leaves: Iterable[Leaf]) -> tuple[str, ...]:` in `agent_workflows/ipd_lint.py`) only collects indented lines that immediately follow a `_LEAF_RE` opening line before any blank line, `_SUBFIELD_RE`, heading, or non-indented line. In `unattached_section_prose`, setting `in_prose = True` only when a non-indented non-leaf, non-subfield, non-heading line is appended to `sections[current_h2]`, and resetting `in_prose = False` on `_H2_RE`, `_H3_RE`, `_LEAF_RE`, `_SUBFIELD_RE`, and blank lines (`not raw.strip()`, checked before `raw[:1].isspace()`), guarantees that: (a) every indented line captured by `leaf_action_blocks` has `in_prose == False` and is dropped; (b) every indented line following a `- Key: value` subfield (including `SYNTHETIC_ORCHESTRATOR_RESIDUAL_GAP` in `tests/test_orchestrator_probe_payload.py::TestProbePayloadDefaultSuite.test_synthetic_c3_indented_line_residual_gap` and multi-line `- Observed evidence:` / `- Execution note:` blocks in Group A) has `in_prose == False` and is dropped; and (c) across all 91 `- Kind: orchestrator` plans in `.aw/records/plans/`, Group A (`moved == 0` on all 6 invariants), Group B (`moved == 91` on `b1`, `0` on `b2`), and Group C (`shared_lines_over_40 == 0`, `shared_cells_over_25 == 0`) all pass. |
| F-03 | Live-corpus fingerprint impact is zero on pending orchestrators. | Measured across `.aw/records/plans/`: 91 plans carry `- Kind: orchestrator` (1 in `pending/`, `k93w2g`, plus 90 in terminal directories `executed/` and `superseded/`). Under the updated `unattached_section_prose`, 21 of the 91 orchestrators change their allowlisted `prose_sections` payload (20 in `executed/`, 1 in `superseded/`), while the single pending orchestrator `k93w2g` (`20261011-uncitedaudit-00-k93w2g-audit-and-mutation-prove-behavioral-coverage-across-the-unci.ipd.md`) has no wrapped allowlisted prose bullets and retains its exact digest `d726a52ad65c242b8ed20406c3bd86645978472bac3872090f938c7e8a2c51af`. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/ipd_lint.py` (E-01)**:
   - In `unattached_section_prose(text: str) -> dict[str, str]`:
     - Track `in_prose = False`.
     - When `_H2_RE.match(raw)` matches: set `current_h2`, initialize `sections[current_h2]` if absent, set `in_prose = False`, and `continue`.
     - When `current_h2 is None`: `continue`.
     - Check `if not raw.strip():` before `raw[:1].isspace()`: set `in_prose = False` and `continue`.
     - When `_H3_RE.match(raw)`, `_LEAF_RE.match(raw)`, or `_SUBFIELD_RE.match(raw)` matches: set `in_prose = False` and `continue`.
     - When `raw[:1].isspace()` is true: if `in_prose and sections[current_h2]`, join the stripped line onto the active prose line via `sections[current_h2][-1] = f"{sections[current_h2][-1].rstrip()} {raw.strip()}"` (leaving `in_prose = True` for further continuation lines); then `continue`.
     - For any remaining non-indented prose line: `sections[current_h2].append(raw)` and set `in_prose = True`.
   - Update `unattached_section_prose`'s docstring to document that indented lines continuing an unattached prose bullet or paragraph are joined onto their opening line while indented lines following a leaf, subfield, heading, or blank line are excluded.

2. **`agent_workflows/runner_shared.py` (E-02)**:
   - Update the docstrings of `probe_cache_payload` and `probe_cache_digest` where they describe excluded indented lines inside allowlisted sections so they reflect that wrapped continuation lines of unattached prose bullets/paragraphs are joined and covered, while indented lines following a checklist leaf or `- Key: value` subfield remain excluded from `prose_sections`.

3. **`tests/test_orchestrator_probe_payload.py` (E-03)**:
   - Add `test_wrapped_completion_criteria_bullet_keeps_owner_continuation` and `test_e_leaf_indented_continuation_still_excluded_from_unattached_prose` to `TestProbePayloadDefaultSuite` testing:
     - Wrapped 2-line and 3-line bullets in `## Completion criteria (the whole Set is done only when)` carrying `OWNER: syn002 (executed).` on the indented continuation line are joined onto the bullet's opening line in `unattached_section_prose`, `probe_cache_payload["prose_sections"]`, and `orchestrator_probe_excerpt`.
     - The `probe_cache_digest` of the wrapped-bullet document equals the `probe_cache_digest` of the equivalent unwrapped single-line bullet document, and editing the wrapped continuation line moves `probe_cache_digest`.
     - An `E-*` checklist leaf's indented continuation line (and an indented line after a blank line or after a `- Key: value` subfield) is absent from `unattached_section_prose` and `probe_cache_payload["prose_sections"]`, while the `E-*` leaf's continuation remains present in `probe_cache_payload["e_items"]`.

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Run `python3 -m pytest tests/test_orchestrator_probe_payload.py tests/test_orchestrator_shape_composed.py tests/test_orchestrator_shape_gate.py` (default suite).
- Run `python3 -m pytest tests/test_orchestrator_probe_payload.py -m livecorpus -o addopts=""` to verify Group A, Group B, and Group C invariants across all corpus orchestrators.
- Run `aw sanitize --agent` and the bare repository test suite `python3 -m pytest`.

## Spec / documentation sync

- Update the docstrings of `ipd_lint.unattached_section_prose` (`agent_workflows/ipd_lint.py`) and `runner_shared.probe_cache_payload` / `runner_shared.probe_cache_digest` (`agent_workflows/runner_shared.py`). No `.spec.md` file requires amendment because `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` Section 2.5b and `.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md` Section 3a limit 1 already specify that the probe reads the allowlisted unattached prose sections and credits obligations assigned in prose to a named child; dropping wrapped bullet continuation lines was an extractor bug in `ipd_lint.unattached_section_prose`, not a spec contract.

## Open questions

### OQ-01: Should blank lines terminate an unattached prose continuation block in `unattached_section_prose`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence as YES (`if not raw.strip(): in_prose = False; continue`, checked before `if raw[:1].isspace():`). This matches `ipd_lint.leaf_action_blocks` (`if not stripped: break`), treats whitespace-only lines as blank lines rather than continuation lines, prevents an indented block after a blank line from being welded onto an earlier bullet, and produces identical results (`0` shared lines over 40 chars, `0` shared table cells over 25 chars, `0` Group A movers) across all 91 orchestrators in `.aw/records/plans/`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste the output of a `python3 -c` command calling `ipd_lint.unattached_section_prose` and `runner_shared.orchestrator_probe_excerpt` on a synthetic orchestrator whose `## Completion criteria (the whole Set is done only when)` bullet wraps `OWNER: syn002 (executed).` onto a 2-space indented continuation line and whose `E-01` leaf carries a 2-space indented continuation line, showing the joined single-line bullet (including `OWNER: syn002 (executed).`) in `unattached_section_prose` and `orchestrator_probe_excerpt` while `E-01`'s continuation line appears only under `### Checklist item action text` and not under `### Unattached prose sections`. ALSO paste a fingerprint-impact measurement RE-DERIVED at execution time (not the authoring figures in F-03): for every `- Kind: orchestrator` plan currently in `.aw/records/plans/pending/`, its `runner_shared.probe_cache_digest` under the pre-change and post-change extractor (e.g. via `git stash`-free comparison against `git show HEAD:agent_workflows/ipd_lint.py` loaded under a scratch module name in `.aw/state/`), naming any pending orchestrator whose digest moved; a moved digest is acceptable but must be named so its `- Coverage:` record is known to re-probe.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff -- agent_workflows/ipd_lint.py agent_workflows/runner_shared.py` showing the implementation in `unattached_section_prose` and the updated docstrings in `unattached_section_prose`, `probe_cache_payload`, and `probe_cache_digest`, with the old "476 lines (74,625 characters)" figures removed or replaced by re-measured, dated figures (and the measurement command output pasted if re-measured).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the actual runner output showing the new wrapped-bullet, digest-equality, digest-sensitivity and leaf/subfield-exclusion tests PASSED by name (names are pointers, the behaviors are the bar), and that the existing `test_synthetic_c3_indented_line_residual_gap` still passes, from (1) `python3 -m pytest tests/test_orchestrator_probe_payload.py tests/test_orchestrator_shape_composed.py tests/test_orchestrator_shape_gate.py -o addopts=""`, (2) `python3 -m pytest tests/test_orchestrator_probe_payload.py -m livecorpus -o addopts=""`, (3) `aw sanitize --agent`, and (4) bare `python3 -m pytest`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved u1l9rx --by-human`) or dispatch by an authorized runner turn; OQ-01 is resolved and no question blocks. Begin with `aw ipd begin u1l9rx`. This plan carries `- Blocks-Release: next` inherited from backlog `go6vzi`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `agent_workflows/ipd_lint.py` or `agent_workflows/runner_shared.py` that cannot be safely combined, or the Group A/B/C live-corpus invariants failing under the new extractor (which would mean the disjointness premise of F-02 no longer holds).

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. Scratch comparison modules live under the gitignored `.aw/state/` and are never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit u1l9rx -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, run `aw ipd finalize u1l9rx` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
