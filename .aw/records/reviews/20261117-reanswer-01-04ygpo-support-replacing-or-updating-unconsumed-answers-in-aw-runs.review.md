# Review findings: ipd 04ygpo

- Subject-Id: 04ygpo
- Subject-Type: ipd
- Reviewed-At: 2026-11-18
- Reviewer: antigravity/gemini-4-hydrogen-high
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `fd79cced763ddff9e7d28665ba49099db1db3e06` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261117-reanswer-01-04ygpo-support-replacing-or-updating-unconsumed-answers-in-aw-runs.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent` returned `clean` (`exit: 0`, `2` non-blocking `info` `IPD-C802` advisories on the boilerplate validation rule), `aw specs check` on `6kwd2e` passed (`1 specs checked`), and the baseline pytest run on `tests/test_runs_answer.py`, `tests/test_question_resume.py`, and `tests/test_question_inbox.py` passed (`29 passed in 12.63s`). Inspection against governing spec `6kwd2e` (`R9.2`, `R9.5`, `A42`), backlog `9t7u5r`, `agent_workflows/question_inbox.py`, `agent_workflows/runner_shared.py`, `agent_workflows/cli.py`, `agent_workflows/run_cli.py`, `agent_workflows/notify/core.py`, `agent_workflows/set_records.py`, `agent_workflows/run_ledger_schema.py`, and existing tests produced findings PR-001..PR-007, all resolved and revised in place. Pass 2 re-evaluated all sections (correcting `execute_item_core` and reconciling `Deferred / out of scope` carriers and `Scope check`), and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` (`exit: 0`, `error: 0`, `warning: 0`, `info: 2` on the boilerplate validation rule).

### Proofreading

Checked `.aw/records/plans/pending/20261117-reanswer-01-04ygpo-support-replacing-or-updating-unconsumed-answers-in-aw-runs.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
| --- | --- | --- | --- |
| Front matter | `- Status: to-review`, missing `- Readiness:` and `- Review-Depth:`, 7 `- Scope-Paths:` entries | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard`, added `agent_workflows/runner_shared.py` to `- Scope-Paths:` and updated `- Scope:` | PR-001, PR-006, Step S7 front-matter requirements. |
| Workflow history | `to-review` and `draft` lines only | Prepended `/plan-review` entry with verdict `APPROVE WITH REVISIONS APPLIED`, findings PR-001..PR-007, and review record path | PR-006, Step S7 newest-first history requirement. |
| E-01 | Asked to append a workflow history note to `6kwd2e` with bare section tokens | Qualified citations as `6kwd2e R9.2`, `6kwd2e R9.5`, `6kwd2e A42` and specified newest-first `aw specs note` | PR-004, spec citation and newest-first history convention. |
| E-02 | Only checked `q_data_locked` status on `question_inbox.write_answer` | Re-ordered lock checks (`q_data_locked` first), added `answer-consumed` check in `events.jsonl`, clarified no-prior-answer and non-ledger `"event"` shape, and added `preflight_parked` status update in `runner_shared.py::consume_answers` | PR-001, close preflight and checkpoint consumption gaps. |
| E-03 | Contradictory `replace` wiring in interactive loop, unquoted `_p_runs_answer`, no sanitization or `"already answered"` compatibility | Fixed interactive `replace` boolean (`replace_flag or confirmed_replace`), required `_clean_worker_text`, preserved lowercase `"already answered"`, updated `_p_runs_answer` help text and `cli.py::_build_parser` citation | PR-002, prevent silent failure and test regression. |
| Proposed changes diagram | Checked `answers/<qid>.json exists?` before `question status == 'open'?` | Re-ordered flowchart to check `question status == 'open'?` and `answer-consumed` before `answers/<qid>.json exists?` and `replace == True?` | PR-004, Technical Writing Standard Requirement 12(d)/(e). |
| Deferred / out of scope | Three rows without durable carriers | Added `- Carrier-Declined:` subfields explaining each intentional exclusion | PR-007, `check.ipd-uncarried-obligation` compliance at `review-finalize`. |
| E-04, E-05, Required tests, V-01..V-05 | Omitted `test_question_inbox.py` and `test_question_preflight.py`; V-04 checked `inspect`/`ast` only in `test_runs_answer.py` | Added both test files to E-05 / V-05 / Required tests, added consumption-boundary test demands, and extended V-04 `rg` check to `tests/test_question_resume.py` | PR-001, PR-005, test coverage completeness. |
| Approval and execution gate | Unconditional `aw ipd finalize` instruction, missing execution contract elements | Added full execution contract (resolved OQs, scope fence, safety stop, evidence honesty, path-scoped `aw commit` / never-push, conditional runner/executor finalize ownership, and `9t7u5r` closure) | PR-003, Step S7 execution contract requirements. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
| --- | --- | --- | --- | --- | --- |
| (none) | | | | | |

### Step T

1. Yes. Amends spec `6kwd2e` (`R9.2`, `R9.5`, `A42`), adds `--replace` CLI flag to `aw runs answer`, adds `replace: bool = False` to `question_inbox.write_answer` and `write_group_answer`, and adds an `answer-replaced` event to `events.jsonl`.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact child plan with 5 execution items in 1 task group and 8 scope paths.
4. Yes. `- Scope-Paths:` explicitly declares every modified spec, source, test, and plan file.
5. Yes. A concurrency or state-boundary bug in `question_inbox.write_answer` could violate first-answer-wins across adapters or overwrite an already-consumed answer.

AW-TIER: standard

### Step R1

- Checked: `.aw/records/specs/implemented/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md` (`R9.2`, `R9.5`, `A42`, `## Workflow history`), `.aw/records/backlog/graduated/20261117-reanswer-01-9t7u5r-reanswer-recorded-questions.backlog.md`, `agent_workflows/question_inbox.py` (`write_answer`, `write_group_answer`, `set_question_status`, `group_open_questions`, `write_projection`, `read_answer`), `agent_workflows/runner_shared.py` (`consume_answers`, `execute_item_core`), `agent_workflows/cli.py` (`_build_parser` `_p_runs_answer`), `agent_workflows/run_cli.py` (`_run_answer`, `_emit_answer_record`, `_clean_worker_text`), `agent_workflows/notify/core.py` (`_apply_group_route`, `apply_inbound`), `agent_workflows/set_records.py` (`render_open_questions`), `agent_workflows/run_ledger_schema.py` (`RECORD_KINDS`, `validate_record`), `tests/test_runs_answer.py`, `tests/test_question_resume.py`, `tests/test_question_inbox.py`, `tests/test_question_preflight.py`, and `tests/test_runs_flag_position_parity.py`.
- Checked: Baseline pytest on `tests/test_runs_answer.py`, `tests/test_question_resume.py`, and `tests/test_question_inbox.py` (`29 passed in 12.63s`); `aw specs check` on `6kwd2e` (`all specs conform. 1 specs checked`).

### Step R2

- Checked: 1:1 bijection between E-01..E-05 and V-01..V-05; `- Scope-Paths:` completeness (including `agent_workflows/runner_shared.py`); `- Item-Dependencies: none`; concrete evidence in V-01..V-05; runtime-demonstration reachability (all demanded CLI/library observations map directly to E-01..E-05); and carrier obligations on `## Deferred / out of scope` (`check.ipd-uncarried-obligation` now clean).

### Step R3

- Checked: Security and privacy. `write_answer` preserves `QID_RE` path-traversal rejection, `actor == "human"` enforcement (RL-E051), option bounds, `allow_free_text`, length caps, and control-character rejection across both `replace=False` and `replace=True`. `run_cli._run_answer` sanitizes displayed prior answers via `_clean_worker_text` to prevent ANSI/control-sequence injection.

### Step R4

- Checked: Engineering rubric, right-sizing, anti-regression, and conceptual density. Closed the preflight and checkpoint `consume_answers` consumption gaps, ensured `tests/test_runs_answer.py:274-277` lowercase `"already answered"` compatibility, added `tests/test_question_inbox.py` and `tests/test_question_preflight.py` to E-05/V-05, and verified no flag-position parity conflict in `tests/test_runs_flag_position_parity.py`. Sized cleanly at 5 E-items, 1 task group, 8 Scope-Paths.

### Step R5

- Checked against reviewer personas:
  - QA / QC: Verified V-01..V-05 require pasted diffs, `aw specs check`, `--help` output, and pytest node results.
  - Testing & Regression: Caught the `tests/test_runs_answer.py:274-277` lowercase `"already answered"` assertion and expanded E-05 to cover `test_question_inbox.py` and `test_question_preflight.py`.
  - Architect: Preserved `question_inbox.write_answer` as the single shared writer and closed the `consume_answers` status/event boundary.
  - UI/UX & Novice: Required sanitized prior-answer display and explicit `'r'` / `--replace` confirmation before replacement.
  - Security / Red-Teamer: Verified RL-E051 actor enforcement, path validation, and ANSI stripping on prior answer display.

### Step R6

- Decomposition check: 5 E-items, 1 task group, 8 Scope-Paths. Right-sized for single-child execution; no split needed.

### Step R7

- Cross-plan alignment: Sole plan in Set `reanswer`; coordinates cleanly with backlog `9t7u5r` and implemented spec `6kwd2e`.

### Step S5

- Checked: Pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`, `Owner: maintainer`). Recorded self-resolved review decisions D-1..D-5 in `### Decisions`, all `Reversible: yes`. Zero human-owned blocking questions remain (`questions: []`).

### Pass 2

- Re-reviewed `E-01..E-05`, `V-01..V-05`, `Scope-Paths`, `Proposed changes`, `Deferred / out of scope`, and `Approval and execution gate` per `steps/s6-rereview.md` rule 1 after Pass 1 revisions.
- Reconciled `agent_workflows/runner_shared.py::execute_item_core` citation, `Deferred / out of scope` carriers (`Carrier-Declined`), and `Scope check` wording; removed one non-boilerplate em dash in E-02.
- Confirmed `aw ipd lint --phase review-finalize --agent --verbose` exited `0` (`clean`, `error: 0`, `warning: 0`, `info: 2` on the boilerplate validation rule).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| PR-001 | HIGH | IN-SCOPE | Correctness / Consumption Boundary | agent_workflows/runner_shared.py::consume_answers:25677-25849; agent_workflows/question_inbox.py::write_answer:699-727 | Checking only `questions/<qid>.json` `status == "open"` fails to block replacement of consumed answers when `consume_answers` commits a `preflight_parked` OQ answer without calling `set_question_status(..., "answered")` or snapshots `answers_pending` into `state.json` before `execute_item_core` transitions status; `write_answer` also checks `ans_file.exists()` before `q_data_locked`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `agent_workflows/runner_shared.py` to `- Scope-Paths:`, updated E-02 to mark `preflight_parked` questions `"answered"` after `offer_commit`, check `q_data_locked` before `ans_file.exists()`, and reject `replace=True` when `events.jsonl` records `answer-consumed` for `qid`. Recommendation strength: strong. |
| PR-002 | HIGH | IN-SCOPE | Correctness / Interactive UX & Regression | agent_workflows/run_cli.py::_run_answer:638-705; tests/test_runs_answer.py::test_runs_answer_interactive_and_ansi_stripped:267-277 | E-03 wired `getattr(args, "replace", False)` into interactive `write_group_answer` calls even when the user confirmed replacement via `'r'`, omitted `_clean_worker_text` sanitization when printing prior answers, omitted preserving the lowercase `"already answered"` substring asserted by `tests/test_runs_answer.py:274-277`, and cited `_p_runs_answer` as a module symbol instead of a local parser in `cli.py::_build_parser`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote E-03 to pass `bool(getattr(args, "replace", False)) or confirmed_replace` interactively, sanitize displayed prior answers via `_clean_worker_text`, include lowercase `"already answered"`, update `_p_runs_answer` help `description`/`epilog`, and fix the citation. Recommendation strength: strong. |
| PR-003 | MEDIUM | IN-SCOPE | Governance / Execution Gate | .aw/records/plans/pending/20261117-reanswer-01-04ygpo-support-replacing-or-updating-unconsumed-answers-in-aw-runs.ipd.md:158-163 | `## Approval and execution gate` unconditionally instructed running `aw ipd finalize` and omitted the scope fence, narrow safety stop, evidence honesty rule, and path-scoped commit / never-push contract. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced gate prose with the full execution contract including conditional runner/executor finalize ownership (`never a hand git mv` to `executed/`). Recommendation strength: strong. |
| PR-004 | MEDIUM | IN-SCOPE | Proofreading / Diagram & Spec Sync | .aw/records/plans/pending/20261117-reanswer-01-04ygpo-support-replacing-or-updating-unconsumed-answers-in-aw-runs.ipd.md:39,81-90 | The Mermaid flowchart checked `answers/<qid>.json exists?` before `question status == 'open'?`, disagreeing with `write_answer` control flow (Technical Writing Standard Requirement 12(d)/(e)); E-01 also said "Append" for `6kwd2e`'s newest-first `## Workflow history`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Re-ordered the Mermaid flowchart to check `question status == 'open'` and `answer-consumed` before branching on `answers/<qid>.json` and `replace == True`, and updated E-01 to record the newest-first history note via `aw specs note`. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | Testing / Validation Completeness | .aw/records/plans/pending/20261117-reanswer-01-04ygpo-support-replacing-or-updating-unconsumed-answers-in-aw-runs.ipd.md:54,59,110,149,154 | E-05, `## Required tests / validation`, and V-05 omitted `tests/test_question_inbox.py` and `tests/test_question_preflight.py`; V-04 checked `inspect`/`ast` only in `tests/test_runs_answer.py` while E-04 also edits `tests/test_question_resume.py`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `tests/test_question_inbox.py` and `tests/test_question_preflight.py` to E-05, Required tests, and V-05, and extended V-04's `rg` check to `tests/test_question_resume.py`. Recommendation strength: strong. |
| PR-006 | LOW | IN-SCOPE | Metadata / Front Matter | .aw/records/plans/pending/20261117-reanswer-01-04ygpo-support-replacing-or-updating-unconsumed-answers-in-aw-runs.ipd.md:9 | Plan status remained `to-review` without `- Readiness:` or `- Review-Depth:` prior to S7 finalization. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard`, and prepended the `/plan-review` line to `## Workflow history`. Recommendation strength: strong. |
| PR-007 | HIGH | IN-SCOPE | Governance / Durable Carriers | .aw/records/plans/pending/20261117-reanswer-01-04ygpo-support-replacing-or-updating-unconsumed-answers-in-aw-runs.ipd.md:101-106 | `aw ipd lint --phase review-finalize` reported `check.ipd-uncarried-obligation` error on the 3 bullets in `## Deferred / out of scope (with reason)` lacking durable carrier subfields. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Carrier-Declined:` subfields to all 3 deferred rows; re-running `aw ipd lint --phase review-finalize` exited 0 (`clean`). Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | How should `write_answer(..., replace=True)` enforce the unconsumed-only boundary across preflight and mid-run checkpoints? | Re-read `q_data_locked` before `ans_file.exists()` inside `FileLock`, reject `replace=True` when `answer-consumed` is in `events.jsonl`, and mark `preflight_parked` questions `"answered"` in `runner_shared.consume_answers` after `offer_commit`. | Rely solely on `questions/<qid>.json` `status == "open"` (leaves preflight-committed and checkpoint-queued answers unprotected). | `agent_workflows/runner_shared.py::consume_answers:25677-25849`; `agent_workflows/question_inbox.py::write_answer:699-727` | yes |
| D-2 | How should interactive `aw runs answer` handle existing answers and `'r'` confirmation? | Pass `bool(getattr(args, "replace", False)) or confirmed_replace` into `write_group_answer`, sanitize prior answer output via `_clean_worker_text`, and include lowercase `"already answered"` in the banner/prompt. | Pass only `getattr(args, "replace", False)` (breaks `'r'` confirmation) or omit `"already answered"` (breaks existing repeat test). | `agent_workflows/run_cli.py::_run_answer:638-705`; `tests/test_runs_answer.py:267-277` | yes |
| D-3 | How should `## Approval and execution gate` specify lifecycle transitions and execution rules? | Include the full execution contract with conditional runner/executor finalize ownership (`never a hand git mv` to `executed/`) and post-execution `9t7u5r` closure. | Leave unconditional `aw ipd finalize` prose (violates `steps/s7-finalize.md`). | `.aw/system/workflows/plan-review/steps/s7-finalize.md` | yes |
| D-4 | How should `Proposed changes` diagram order and `6kwd2e` history updates be specified? | Order the Mermaid flowchart to check `question status == 'open'` and `answer-consumed` before `answers/<qid>.json exists?` and `replace == True?`, and use `aw specs note` for `6kwd2e`. | Keep prior diagram order (contradicts `write_answer` control flow and Requirement 12d/e). | `.aw/system/workflows/technical-writing/technical-writing.md` Requirement 12; `agent_workflows/question_inbox.py::write_answer` | yes |
| D-5 | Which test modules should be included in E-05 / V-05 and V-04's no-code-pinning check? | Add `tests/test_question_inbox.py` and `tests/test_question_preflight.py` to E-05 / V-05, and check both `tests/test_runs_answer.py` and `tests/test_question_resume.py` in V-04. | Omit sibling question-inbox/preflight suites and leave `test_question_resume.py` unchecked for `inspect`/`ast`. | `tests/test_question_inbox.py`; `tests/test_question_preflight.py`; `tests/test_question_resume.py` | yes |
