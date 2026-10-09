# IPD: Clarify and style status refusal messages and orchestrator readiness gates

- Date: 2026-10-07
- Kind: child
- Concern: Status refusal messages in `aw set` and `aw ipd set` (notably for orchestrator readiness and approval gates) are confusing, un-skimmable, and factually misleading. When attempting to approve orchestrator `itamry`, the setter printed `Orchestrator itamry is not ready for review:` even though it was already reviewed and was awaiting approval, dumped raw internal linter codes (`IPD-Q501`) without extracting the actual blocking question, and failed to explain the parent-child relationship. Furthermore, across `status_set.py` and `plan_readiness.py`, refusal messages are dense, unbulleted run-on sentences lacking ANSI color or bold highlighting on id6s, setids, and status words.
- Scope: Make `orchestrator_readiness.render_human` target-status-aware (`approved`, `reviewed`, `to-review`) and state the causal parent-child constraint clearly. Extract and display the title/text of child blocking open questions. Add ANSI bold and color styling for id6s, setids, and statuses across `orchestrator_readiness.py` and `status_set.py`. Polish and bulletize refusal messages for single-plan approval gates, backward transitions without `--message`, terminal reopenings, and priority backstops. Add regression tests verifying all revised outputs.
- Scope-Paths: agent_workflows/orchestrator_readiness.py, agent_workflows/status_set.py, agent_workflows/plan_readiness.py, tests/test_orchestrator_readiness.py, tests/test_status_set.py
- Item-Dependencies: none
- Status: executed
- Blocks-Release: next
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: hf5cc4
- Set: setrefuse
- Order: 1
- Highest E allocated: 07
- Author: antigravity
- Id: juu1rj

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: juu1rj verified (set setrefuse, attempt 1).
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (HIGH, fixed: styling must use the shared lifecycle resolver per approved spec uonrjg R10.3, not a hand palette), PR-002 (HIGH, fixed: render_human's coverage and runner-prompt callers kept byte-identical), PR-003 (MEDIUM, fixed: question extraction moved into review_readiness via defaulted Finding.questions; new E-06/E-07), PR-004 (MEDIUM, fixed: no ANSI in agent/JSON or shared refusal strings), PR-005 (MEDIUM, fixed: test-asserted phrases named), PR-006 (MEDIUM, fixed: V-items demand pasted behavioral output, not diffs), PR-007 (MEDIUM, fixed: inherited Blocks-Release next from hf5cc4), PR-008 (LOW, fixed: execution contract). Lint clean at author and review-finalize. Record: `.aw/records/reviews/20261007-setrefuse-01-juu1rj-clarify-and-style-status-refusal-messages-and-orchestrator-r.review.md`.
- 2026-10-07 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED

- 2026-10-07 to-review (antigravity): authored review-ready plan in an isolated worktree from backlog hf5cc4.
- 2026-10-07 draft (antigravity): created via aw ipd scaffold.

## Goal

Provide clear, skimmable, and visually styled error and refusal messages in `aw set` and `aw ipd set`, ensuring that orchestrator readiness checks reflect the requested target status (such as `approved`), explain parent-child blocking relationships plainly, extract blocking question text, and highlight all id6s, setids, and lifecycle statuses in bold colors.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Orchestrator readiness and causal child error rendering

- [x] E-01 Make `orchestrator_readiness.render_human` status-aware and causal (wording only; no styling, no file I/O).
  - Depends on: none
  - Expected outcome: `orchestrator_readiness.render_human(result, target_status=None, term=None)` gains two KEYWORD-ONLY optional parameters. When `target_status` is `"reviewed"`, `"approved"` or `"auto-approved"`, the header reads `Refusing to set {target_status} for orchestrator {id6} (set {setid}):` followed by ONE causal sentence stating that an orchestrator may not advance while a child in its Set is not ready, and naming the child id6(s) found. When `target_status` is `None` or `"to-review"`, the header stays exactly `Orchestrator {id6} is not ready for review:`, because that wording is ACCURATE for those calls and is relied on: `tests/test_orchestrator_status_gate.py` (`ipd set to-review ... --dry-run` asserts "not ready for review"), `run_coverage` (`aw ipd coverage`, which has no target status), and `runner_shared` (the continue-handoff builder, which embeds `render_human(readiness)` into an AGENT PROMPT, so it must stay plain text). With both new parameters omitted, output is BYTE-IDENTICAL to today for every existing caller.
  - Execution state: performed

- [x] E-06 Carry the blocking question's id and heading text on the child-lint finding, computed where the child path is known.
  - Depends on: none
  - Expected outcome: In `orchestrator_readiness.review_readiness`, in the `CODE_CHILD_LINT` branch (where `child.path` and `child_lint.diagnostics` are both in hand), for each diagnostic whose `code` is `ipd_lint.C_OQ` (`IPD-Q501`), read the `OQ-NN` id from the diagnostic message and look up that question's heading text in the child file with the shared `ipd_schema.OQ_HEADING_RE` (no new regex for the heading). Carry the result on `Finding` as a NEW trailing field with a default (for example `questions: tuple[tuple[str, str], ...] = ()` of `(oq_id, title)`), so every existing 4-argument construction and every keyword access keeps working. `render_human` then renders each as a sub-bullet `{oq_id}: {title}` under the child instead of the raw `IPD-Q501 ...` diagnostic string, and falls back to today's `detail` text when `questions` is empty (unreadable child, unmatched heading). `render_human` itself performs NO file I/O. `detail`, `code`, `subject` and `remedy` are unchanged, so `render_agent`, the `status_set` agent/JSON payload and the `runner_shared` markdown builder that read `rf.detail` are unaffected.
  - Execution state: performed

- [x] E-07 Style the human orchestrator refusal through the SHARED lifecycle resolver, never a local palette.
  - Depends on: E-01, E-06
  - Expected outcome: When `render_human` is given a `term` with `term.color` true, each id6 that has a known status is rendered with `agent_workflows.term.resolve_lifecycle("plans", <status>)` passed to `Term.format_lifecycle_compact(id6, resolved, word=True)`, and the target status word with `Term.style_lifecycle_text`; the setid and section labels use bold only (`Term.colorize(text, "bold")`), with NO lifecycle color, since a setid has no lifecycle. This is what approved spec `uonrjg` requires: Section 9.2 (glyph and id6 styled together in the lifecycle color), Section 9.1 (only glyph, id6 and status word carry lifecycle color) and R10.3 (status setters MUST consume the shared resolver; local lifecycle color tables are forbidden). Color on/off is decided ONLY by `term.color`, which already implements the `--color`/`--no-color` > `NO_COLOR`/`FORCE_COLOR` > `TERM` > `isatty()` precedence (`uonrjg` 9.3); do not consult `sys.stdout.isatty()` directly. With `term=None` or `term.color` false, output contains no `\x1b` byte (`uonrjg` A11).
  - Execution state: performed

- [x] E-02 Pass `target_status` and `term` from `status_set.run_set_command` to `render_human`.
  - Depends on: E-01, E-06, E-07
  - Expected outcome: In `agent_workflows.status_set.run_set_command`, in the orchestrator review-readiness gate (locate by the comment `Orchestrator review readiness gate` and the loop `for r in _unready_results:`), the human branch calls `term.line(_orch_readiness.render_human(r, target_status=<normalized plans target>, term=term))`, where the target is the same `normalize_target_status(target_status, "plans")` value the gate already computed for `_gated_orchestrators`. In the agent/JSON branch of the same gate, ADD `data.target_status` and a per-finding `questions` list (from E-06's field) ADDITIVELY: every existing key (`summary`, `data.id6`, `data.setid`, `data.ready`, `data.finding_codes`, `data.findings[].code/subject/detail/remedy`) keeps its current name and value, and no agent/JSON string contains an ANSI escape. Do NOT change the other `render_human` callers (`orchestrator_readiness.run_coverage` and the `runner_shared` continue-handoff builder); they keep the no-argument call and therefore today's exact text.
  - Execution state: performed

### Task group 2: Approval gate, demotion, reopen, and backstop message polish

- [x] E-03 Polish and style single-plan approval gate refusals in `plan_readiness.py` and `status_set.py`.
  - Depends on: none
  - Expected outcome: (a) In `agent_workflows.plan_readiness`, the open-question refusal names each blocking question as `OQ-NN: <heading text>` (extend `_blocking_question_ids` or add a sibling that returns id plus `ipd_schema.OQ_HEADING_RE` group 2), so the message carries the question itself, not only its id. `approval_refusals` keeps returning `List[str]` with ONE reason per element and keeps every distinctive phrase existing tests match on (notably "states a verdict that does not clear this plan" in `tests/test_review_record_classifier.py`), because it is shared with `specs.run_set`, which already prints one reason per line to stderr. (b) In `agent_workflows.status_set.validate_transition_allowed`, the approval-gate return string joins reasons as a header line `refusing to set <status> for <plan|spec> <id6>:` followed by one `  - <reason>` line per reason instead of `"; ".join(...)`, keeping the leading `refusing to set <status>` phrase that `tests/test_plan_priority_required.py` asserts. (c) In `run_set_command`'s human branch for a failed `validate_transition_allowed` (locate by `Refusing before making changes`), stop appending `. Refusing before making changes.` directly after a message that already ends in `.` (the source of the `..`), keeping the phrase `Refusing before making changes` that `tests/test_status_set.py` asserts. STYLING BOUNDARY: `validate_transition_allowed` and `approval_refusals` return PLAIN strings, because the same string becomes `Diagnostic.detail` in agent/JSON output; any id6/status styling is applied only where `run_set_command` writes the human line through `term`.
  - Execution state: performed

- [x] E-04 Polish backward demotion, terminal reopen, and priority backstop refusal messages in `status_set.py`.
  - Depends on: none
  - Expected outcome:
    1. In `agent_workflows.status_set.run_set_command` (backward demotion missing `--message`; locate by `backward plan transition requires an explicit --message`), the HUMAN output lists each demoted plan and its edge (e.g. `  - 62pkkg: approved -> to-review`), from the `_backward_plan_moves` list already computed, and prints the retry command built by the existing `_retry_command(..., extra=['--message "<reason>"'])` the agent branch already uses. Exit code stays 2.
    2. In `agent_workflows.status_set.run_set_command` (terminal reopen check; locate by `status.terminal_reopen_refused`), the human output is a short summary line, then one line per reopened plan as `  - <id6>: <terminal status> -> <target>` (falling back to the file name when the id6 is empty), then the two remedies already present in the agent branch's `next_actions` (a corrective IPD via `aw ipd scaffold`, or the `_retry_command` with `--allow-terminal-reopen`). The policy rationale is kept, shortened to one sentence. Exit code stays 2, and `tests/test_status_set.py`'s terminal-reopen test (asserts the id6 and `--allow-terminal-reopen` appear) keeps passing.
    3. In `agent_workflows.status_set.validate_transition_allowed` (priority/work-kind backstop; locate by `plan_priority_work_kind_problems`), each undecided field is its own `  - <problem>` line under the `refusing to set <status> for plan <id6>:` header, followed by the remedy command line. The phrase `refusing to set approved` is preserved.
    In all three, the agent/JSON branch is UNCHANGED (its `summary`, `diagnostics` and `next_actions` already carry this structure).
  - Execution state: performed

### Task group 3: Regression tests

- [x] E-05 Add unit tests for all revised refusal and gate output formats.
  - Depends on: E-01, E-02, E-03, E-04, E-06, E-07
  - Expected outcome: New tests in `tests/test_orchestrator_readiness.py` and `tests/test_status_set.py` that DRIVE the code (call `render_human` / `review_readiness` on a temp-repo Set, or run `run_set_command` / the CLI) and assert on returned text, exit codes and file contents, never on source structure (GUIDING_PRINCIPLES P16; no `inspect`/`ast`/source-text reads). They pin:
    1. `render_human(r, target_status="approved")` begins `Refusing to set approved for orchestrator <id6> (set <setid>):` and names the unready child.
    2. `render_human(r)` and `render_human(r, target_status="to-review")` are BYTE-IDENTICAL to the pre-change output for the same `ReviewReadiness` (the backward-compatibility invariant for `aw ipd coverage` and the runner prompt).
    3. A temp Set whose child has an open `- Blocking: yes` question `### OQ-06: <title>` yields a `child-lint-failing` finding whose `questions` carries `("OQ-06", "<title>")`, rendered as `OQ-06: <title>`; and a child whose heading cannot be matched falls back to the existing `detail` text without raising.
    4. With `Term(color=True)` the rendered text contains the escape sequence produced by `Term.style_lifecycle_text` for the target status (compare against that call's own output, not a hardcoded palette code); with `Term(color=False)` and with `term=None` it contains no `\x1b`.
    5. `aw ipd set approved <orch>` on an unready orchestrator, human mode, shows the new header and exits 1; the same with `--agent` emits a record whose existing keys are unchanged, whose `data.target_status` is `approved`, and which contains no `\x1b`.
    6. Backward demotion without `--message` names every demoted id6 and its edge in human output and exits 2.
    7. Single-plan approval refusal over a blocking question quotes `OQ-NN: <heading text>` on its own bulleted line, and the human output contains no `..`.
    8. Terminal-reopen and priority/work-kind backstop refusals list each plan / each missing field on its own line.
    The bare suite is then compared before and after (see V-05).
  - Execution state: performed

## Project conventions discovered (Step 0)

- `agent_workflows/orchestrator_readiness.py:render_human` renders human-readable summaries of review readiness using `ReviewReadiness` tuples.
- `agent_workflows/status_set.py:run_set_command` is the unified entry point for `aw set`, `aw ipd set`, `aw specs set`, `aw backlog set`, and `aw prompts set`.
- `agent_workflows/status_set.py:validate_transition_allowed` delegates approval gating to `agent_workflows/plan_readiness.py:approval_refusals`.
- ANSI colors and glyphs are provided by `agent_workflows/term.py:Term`, which provides `color256()`, `status()`, `glyph()`, and lifecycle styling helpers.

## Findings

1. `render_human` in `agent_workflows.orchestrator_readiness.render_human` hardcodes the string `Orchestrator {result.id6} is not ready for review:`, ignoring whether the caller was attempting `aw set to-review`, `aw set reviewed`, or `aw set approved`.
2. When a child fails author lint because of `IPD-Q501` (open blocking question), `render_human` dumps the raw diagnostic `[child-lint-failing] 62pkkg: child 62pkkg fails author lint: IPD-Q501 OQ-06: BLOCKING question is still 'open' ...` without extracting the question title or text.
3. In `agent_workflows.status_set.run_set_command` (orchestrator readiness loop), `run_set_command` calls `_orch_readiness.render_human(r)` without passing `target_status` or the active `term` instance.
4. In `agent_workflows.status_set.run_set_command` (backward plan transition check), the guard fails with a generic summary without naming the demoted plans in human terminal output, forcing the operator to guess which plan triggered the demotion check in a large batch.
5. In `agent_workflows.status_set.validate_transition_allowed` and `agent_workflows.status_set.run_set_command` (terminal reopen check), single-plan approval gate refusals, priority backstops, and terminal reopenings format as dense, unindented run-on strings lacking visual hierarchy.

## Proposed changes (ordered, validatable)

1. Extend `agent_workflows.orchestrator_readiness.render_human` to accept `target_status: str | None = None` and `term: Term | None = None`. Update header and child error formatting to be status-aware, causal, and ANSI styled.
2. In `agent_workflows.orchestrator_readiness`, add a helper to parse and extract the question title/text for `IPD-Q501` child findings.
3. Update `agent_workflows.status_set.run_set_command` to pass `target_status` and `term` into `render_human`.
4. Update `agent_workflows.status_set.validate_transition_allowed`, `agent_workflows.status_set.run_set_command`, and `agent_workflows.plan_readiness.approval_refusals` to produce clean, bulleted, visually styled refusal messages.
5. Add comprehensive unit tests in `tests/test_orchestrator_readiness.py` and `tests/test_status_set.py`.

## Deferred / out of scope (with reason)

- Modifying the underlying validation rules or loosening any approval/orchestrator gates: out of scope; this plan improves message clarity, diagnostic ergonomics, and visual styling without changing the underlying safety invariant.
  - Carrier-Declined: intentional design boundary; this plan focuses solely on refusal message clarity and styling without weakening safety invariants.
- Re-architecting `aw set` selector resolution or dispatch unification (tracked separately in backlog `fcnz1r`): out of scope.
  - Carrier: fcnz1r

## Scope check

- Over-scope: none; confined to message formatting and diagnostic rendering in `orchestrator_readiness.py`, `status_set.py`, `plan_readiness.py`, and test files. The `Finding.questions` field (E-06) is the one data-shape addition, and it is defaulted and additive.
- Under-scope: covers both orchestrator readiness gating (the direct issue encountered) and the surrounding status setter refusal surfaces. Deliberately NOT restyled: `specs.run_set`'s own stderr refusal (it already prints one reason per line and benefits from E-03(a)'s question text automatically) and the `runner_shared` markdown/prompt builders, which are agent-facing.

## Required tests / validation

- Unit tests in `tests/test_orchestrator_readiness.py` covering:
  - `render_human` with `target_status="approved"` producing `Refusing to set approved for orchestrator ...`.
  - Child failure formatting explaining parent orchestrator constraint.
  - Blocking question title/text extraction from child plan text.
  - ANSI color formatting enabled vs disabled.
- Unit tests in `tests/test_status_set.py` covering:
  - Backward demotion naming specific demoted plans in human output.
  - Single-plan approval refusal formatting with quoted blocking question.
  - Terminal reopen refusal formatting.
- Bare test suite `python3 -m pytest` passes with zero regressions.

## Spec / documentation sync

- No spec is edited. The change alters no lifecycle state, transition, gate predicate or machine-readable field name. The styling it adds is GOVERNED by approved spec `uonrjg` (cross-artifact lifecycle symbols and ANSI status styling): Section 9.1 (only glyph, id6 and status word carry lifecycle color), Section 9.2 (compact `GLYPH id6` form), Section 9.3 / acceptance A11 (no ANSI under `NO_COLOR`, `TERM=dumb`, non-TTY) and R10.3 (status setters MUST consume the shared resolver; no local lifecycle color table). E-07 implements against that contract rather than inventing a palette, so no amendment is needed.
- The runner-facing message templates in approved spec `25kzda` (`[IPD-REVIEW-ORCHESTRATOR-READY] Orchestrator <id6> is not ready for review: ...`, `SPEC-PLAN-SET`, `BACKLOG-GRADUATE-SET`) are NOT touched: they are emitted by `runner_shared`, not by `render_human`, and E-01 keeps `render_human`'s default wording unchanged.

## Open questions

### OQ-01: How should `render_human` format output when ANSI colors are disabled or stdout is not a TTY?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED (corrected at review 2026-10-07). `render_human` consults ONLY `term.color`, never `sys.stdout.isatty()` directly: `Term` already resolves the full `--color`/`--no-color` > `NO_COLOR`/`FORCE_COLOR` > `TERM` > `isatty()` precedence (approved spec `uonrjg` 9.3), and a direct `isatty()` check would let a TTY defeat `--no-color`/`NO_COLOR`. `term=None` means plain text. Colors come from the shared lifecycle resolver (`term.resolve_lifecycle` + `Term.format_lifecycle_compact` / `style_lifecycle_text`), not from hand-picked ANSI 256 codes (`uonrjg` R10.3); the setid has no lifecycle and gets bold only. Demonstrated at review: `Term(color=False).format_lifecycle_compact("abc123", resolve_lifecycle("plans","approved"), word=True)` returned `'◕ abc123 approved'` (no escape) and `Term(color=True)` returned `'\x1b[1;38;5;45m◕\x1b[0m \x1b[1;38;5;45mabc123\x1b[0m \x1b[1;38;5;45mapproved\x1b[0m'`.

### OQ-02: Should `render_human` read child plan files directly to extract blocking question text?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED (refined at review 2026-10-07). NO: `render_human` stays a pure renderer. The extraction happens in `review_readiness`'s `CODE_CHILD_LINT` branch, where `child.path` and the `IPD-Q501` diagnostics are already in hand, and the result travels on a new defaulted `Finding.questions` field (E-06). Putting I/O in the renderer would make `aw ipd coverage` and the runner's prompt builder read files as a side effect of printing, and `render_human` receives only a `ReviewReadiness`, which carries no child paths. Demonstrated at review: `ipd_schema.OQ_HEADING_RE.match("### OQ-06: Which admitted forms does TRACE treat as mandatory?").groups()` returned `('OQ-06', 'Which admitted forms does TRACE treat as mandatory?')`, and `plan_readiness._blocking_question_ids` on a one-question fixture returned `OQ-06`. On an unreadable file or unmatched heading the finding keeps `questions=()` and the renderer falls back to today's `detail`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL pytest output (`python3 -m pytest -o addopts="" -v tests/test_orchestrator_readiness.py`) for the tests pinning E-05 items 1 and 2, AND paste a python3 session printing `render_human(r, target_status="approved")` (new header plus causal sentence naming the child) and `render_human(r)` for the SAME `r`, together with the pre-change text of `render_human(r)` for the same `r` captured BEFORE editing (save it to a scratch file under `/tmp` at the start of execution) and an equality check showing the default output is unchanged.
  - Observed evidence:
```
$ python3 -m pytest -o addopts="" -v tests/test_orchestrator_readiness.py -k "test_render_human"
tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_render_human_target_status_approved PASSED [ 50%]
tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_render_human_byte_identical_default_and_to_review PASSED [100%]
======================= 2 passed, 21 deselected in 0.48s =======================

$ python3 -c '
from pathlib import Path
from agent_workflows import orchestrator_readiness as readiness

f = readiness.Finding(
    code=readiness.CODE_CHILD_STATUS,
    subject="62pkkg",
    detail="child 62pkkg has status '\''draft'\'' (must be to-review, reviewed, approved, auto-approved, or executed)",
    remedy="bring the child to `to-review` with `aw ipd set to-review 62pkkg`",
)
r = readiness.ReviewReadiness(
    applies=True,
    ready=False,
    findings=(f,),
    id6="itamry",
    setid="setfoo",
)

out_approved = readiness.render_human(r, target_status="approved")
print("=== render_human(r, target_status=\"approved\") ===")
print(out_approved)

out_default = readiness.render_human(r)
print("\n=== render_human(r) ===")
print(out_default)

pre_change = Path("/tmp/pre_change_render_human.txt").read_text()
print(f"\nDefault output matches pre-change text: {out_default == pre_change}")
assert out_default == pre_change
'
=== render_human(r, target_status="approved") ===
Refusing to set approved for orchestrator itamry (set setfoo):
  An orchestrator may not advance while a child in its Set is not ready (62pkkg).
  - [child-status-not-ready] 62pkkg: child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)
    Remedy: bring the child to `to-review` with `aw ipd set to-review 62pkkg`

=== render_human(r) ===
Orchestrator itamry is not ready for review:
  - [child-status-not-ready] 62pkkg: child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)
    Remedy: bring the child to `to-review` with `aw ipd set to-review 62pkkg`

Default output matches pre-change text: True
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the ACTUAL output of two CLI runs against a temp repo whose orchestrator is unready: `aw ipd set approved <orch-id6> --dry-run` in human mode (the new `Refusing to set approved for orchestrator` header, exit 1), and the same with `--agent` (the JSON record showing every pre-existing key unchanged plus `data.target_status: "approved"`, and no `\x1b`). Also paste `aw ipd coverage <orch-id6> --no-commit` output on the same repo showing the unchanged `Orchestrator <id6> is not ready for review:` header. A diff alone is not sufficient evidence.
  - Observed evidence:
```
=== CLI 1: aw ipd set approved orc001 --dry-run (Human) ===
Exit code: 1
Refusing to set approved for orchestrator orc001 (set tstset):
  An orchestrator may not advance while a child in its Set is not ready (chd001).
  - [child-status-not-ready] chd001: child chd001 has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)
    Remedy: bring the child to `to-review` with `aw ipd set to-review <child-id6>`
  - [coverage-record-absent] orc001: plan has no coverage record (never checked); run `aw ipd coverage orc001`
    Remedy: run `aw ipd coverage <id6>`

=== CLI 2: aw ipd set approved orc001 --dry-run --agent (Agent JSON) ===
Exit code: 1
{"schema":"aw.agent/v1","kind":"result","cmd":"ipd set","exit":1,"outcome":"findings","verified":true,"complete":true,"summary":"orchestrator orc001 is not ready for review (2 finding(s))","data":{"id6":"orc001","setid":"tstset","ready":false,"target_status":"approved","finding_codes":["child-status-not-ready","coverage-record-absent"],"findings":[{"code":"child-status-not-ready","subject":"chd001","detail":"child chd001 has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)","remedy":"bring the child to `to-review` with `aw ipd set to-review <child-id6>`","questions":[]},{"code":"coverage-record-absent","subject":"orc001","detail":"plan has no coverage record (never checked); run `aw ipd coverage orc001`","remedy":"run `aw ipd coverage <id6>`","questions":[]}]}}

=== CLI 3: aw ipd coverage orc001 --no-commit (Unchanged Header) ===
Exit code: 1
Orchestrator orc001 is not ready for review:
  - [child-status-not-ready] chd001: child chd001 has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)
    Remedy: bring the child to `to-review` with `aw ipd set to-review <child-id6>`
  (record written, not committed: commit suppressed by --no-commit)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the ACTUAL human output of `aw ipd set approved <id6>` on a temp plan with an open `- Blocking: yes` question `### OQ-01: <title>`, showing the header line and `OQ-01: <title>` on its own bulleted line and no `..`; paste `aw specs set <spec> --status approved` output on a temp spec with the same question, showing the spec surface also names the heading; and paste the pytest output for `tests/test_review_record_classifier.py` and `tests/test_plan_priority_required.py` (both must still pass, proving the shared phrases survived).
  - Observed evidence:
```
=== aw ipd set approved sp0001 (Human) ===
Exit code: 1
FAIL     Validation error on 20261004-tstset-01-sp0001-test.ipd.md: refusing to set approved for plan sp0001:
  - an unresolved BLOCKING open question remains (OQ-01: What should the default timeout be?). Resolve it, or pass --allow-open-questions to approve over it (the override is recorded in the artifact's history). Refusing before making changes.

=== aw specs set <spec> --status approved --by-human (Human) ===
Exit code: 1
STDERR: aw specs set: refusing to approve .aw/records/specs/20261004-spc001-01-spc001-test.spec.md (file unchanged):
  an unresolved BLOCKING open question remains (OQ-01: What should the default timeout be?). Resolve it, or pass --allow-open-questions to approve over it (the override is recorded in the artifact's history).

=== pytest tests/test_review_record_classifier.py tests/test_plan_priority_required.py ===
============================= 40 passed in 14.38s ==============================
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the ACTUAL human output and exit code of three CLI runs on temp repos: a backward move without `--message` (each demoted id6 with its `from -> to` edge, the retry command, exit 2); a terminal reopen without `--allow-terminal-reopen` (each plan with its terminal status, both remedies, exit 2); and an approval with `Priority: unresolved` and `Work-Kind: unresolved` (each field on its own line). Also paste `--agent` output for the backward move showing the agent record is unchanged from before (same `summary`, `rule`, and `next_actions`).
  - Observed evidence:
```
=== Run 1a: Backward move without --message (Human) ===
Exit code: 2
FAIL     aw set: backward plan transition requires an explicit --message explaining why the plan was demoted; refusing before making changes:
  - dem001: approved -> to-review
Retry with:
  aw ipd set to-review dem001 --message "<reason>"

=== Run 1b: Backward move without --message (--agent) ===
Exit code: 2
{"schema":"aw.agent/v1","kind":"error","cmd":"set","outcome":"cannot-run","exit":2,"verified":false,"complete":false,"findings":1,"diagnostics":[{"location":".aw/records/plans/pending/20261004-tstset-01-dem001-test.ipd.md","rule":"status.backward_plan_message_required"}],"next":"aw ipd set to-review dem001 --message \"<reason>\""}

=== Run 2: Terminal reopen without --allow-terminal-reopen (Human) ===
Exit code: 2
FAIL     Refusing to move 1 plan(s) out of a terminal disposition to 'to-review'.
  - ex0001: executed -> to-review
A terminal plan is a historical record; AGENTS.md directs a corrective IPD for a post-execution gap, not an in-place edit.
Remedies:
  - Write a corrective IPD instead: aw ipd scaffold --title <corrective plan title>
  - Override to reopen anyway (recorded in history): aw ipd set to-review ex0001 --allow-terminal-reopen --yes

=== Run 3: Approval with unresolved priority/work-kind (Human) ===
Exit code: 1
FAIL     Validation error on 20261004-tstset-02-unr001-test.ipd.md: refusing to set approved for plan unr001:
  - Priority is still the 'unresolved' scaffold sentinel; declare low, medium, or high
  - Work-Kind is still the 'unresolved' scaffold sentinel; declare bug, feature, chore, security, or followup
These are decided when the work is first recorded (the backlog item, or `aw ipd scaffold`); set them with `aw ipd set approved unr001 --priority ... --work-kind ...`. Refusing before making changes.
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the ACTUAL tail of a BARE `python3 -m pytest` run (the `N passed` summary line) taken BEFORE any code change and again AFTER, plus the list of failing node IDs from each; the bar is an EMPTY after-minus-before failing set (a pre-existing unrelated failure is recorded, not hidden). Paste `python3 -m pytest -o addopts="" -v tests/test_orchestrator_readiness.py tests/test_status_set.py tests/test_orchestrator_status_gate.py` showing each new E-05 test by name passing. Test counts are context, not the bar.
  - Observed evidence:
```
=== Bare python3 -m pytest BEFORE changes ===
6825 passed, 2 skipped, 3 warnings in 475.97s (0:07:55)
Failing node IDs before: []

=== Bare python3 -m pytest AFTER changes ===
6833 passed, 2 skipped, 3 warnings in 183.98s (0:03:03)
Failing node IDs after: []
After-minus-before failing set: EMPTY (0 regressions)

=== Targeted suite execution ===
$ python3 -m pytest -o addopts="" -v tests/test_orchestrator_readiness.py tests/test_status_set.py tests/test_orchestrator_status_gate.py
tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_term_styling_lifecycle_and_plain_escapes PASSED [ 84%]
tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_render_human_target_status_approved PASSED [ 85%]
tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_render_human_byte_identical_default_and_to_review PASSED [ 86%]
tests/test_orchestrator_readiness.py::TestOrchestratorReadinessRefusalStylingAndFormatting::test_child_lint_question_extraction_and_fallback PASSED [ 86%]
tests/test_status_set.py::RefusalMessagePolishAndGateTests::test_orchestrator_set_approved_human_and_agent_modes PASSED
tests/test_status_set.py::RefusalMessagePolishAndGateTests::test_backward_demotion_without_message_human_output PASSED
tests/test_status_set.py::RefusalMessagePolishAndGateTests::test_single_plan_approval_refusal_blocking_question_formatting PASSED
tests/test_status_set.py::RefusalMessagePolishAndGateTests::test_terminal_reopen_and_priority_backstop_multiline_output PASSED
============================= 146 passed in 42.27s =============================
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste a python3 session (or pytest output) on a temp Set whose child carries `### OQ-06: <title>` with `- Blocking: yes` / `- Status: open`, showing `review_readiness(...)` returns a `child-lint-failing` finding with `questions == (("OQ-06", "<title>"),)` and its `detail` unchanged from the pre-change form; a second case where the child's heading does not match showing `questions == ()` and no exception; and a construction `Finding("c","s","d","r")` with four positional arguments still succeeding.
  - Observed evidence:
```
=== Case 1: Matching OQ heading ===
finding.code: child-lint-failing
finding.subject: chd001
finding.questions: (('OQ-06', 'Which admitted forms does TRACE treat as mandatory?'),)
finding.detail: child chd001 fails author lint: IPD-H202 required H2 missing: Project conventions discovered (Step 0); IPD-H202 required H2 missing: Findings; IPD-H202 required H2 missing: Proposed changes (ordered, validatable); IPD-H202 required H2 missing: Deferred / out of scope (with reason); IPD-H202 required H2 missing: Scope check; IPD-H202 required H2 missing: Required tests / validation; IPD-H202 required H2 missing: Spec / documentation sync; IPD-H202 required H2 missing: Validation and cross-check (verify before reporting done); IPD-Q501 OQ-06: BLOCKING question is still 'open'. Ask the human and record the answer (run `/askme`, then set 'Status: resolved' with a rationale). If it does not actually block, set 'Blocking: no'.

=== Case 2: Unmatched OQ heading ===
finding2.questions: ()

=== Case 3: 4-argument Finding construction ===
f_legacy: Finding(code='c', subject='s', detail='d', remedy='r', questions=())
f_legacy.questions: ()
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste a python3 session printing `repr(render_human(r, target_status="approved", term=Term(color=True)))` showing the id6/status sequences equal to what `Term.format_lifecycle_compact` / `Term.style_lifecycle_text` produce for the same status, and the setid wrapped in bold only; then `repr(...)` with `Term(color=False)` and with `term=None`, each containing no `\x1b`. Paste `rg -n '38;5;|\\x1b\[' agent_workflows/orchestrator_readiness.py agent_workflows/status_set.py` showing NO hand-written escape or palette code was added (an empty result, exit 1, is the pass; confirmed empty at review on the base, so any hit was introduced by this change; this is a diff-hygiene check, not a behavioral test).
  - Observed evidence:
```
=== Term(color=True) ===
repr: "Refusing to set \x1b[1;38;5;45mapproved\x1b[0m for orchestrator itamry (set \x1b[1msetfoo\x1b[0m):\n  An orchestrator may not advance while a child in its Set is not ready (\x1b[38;5;245m○\x1b[0m \x1b[38;5;245m62pkkg\x1b[0m \x1b[38;5;245mdraft\x1b[0m).\n  - [child-status-not-ready] \x1b[38;5;245m○\x1b[0m \x1b[38;5;245m62pkkg\x1b[0m \x1b[38;5;245mdraft\x1b[0m: child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)\n    \x1b[1mRemedy:\x1b[0m bring the child to `to-review` with `aw ipd set to-review 62pkkg`"

expected_target in out_color: True
expected_child in out_color: True
expected_setid in out_color: True

=== Term(color=False) ===
repr: "Refusing to set approved for orchestrator itamry (set setfoo):\n  An orchestrator may not advance while a child in its Set is not ready (62pkkg).\n  - [child-status-not-ready] 62pkkg: child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)\n    Remedy: bring the child to `to-review` with `aw ipd set to-review 62pkkg`"
contains \x1b: False

=== term=None ===
repr: "Refusing to set approved for orchestrator itamry (set setfoo):\n  An orchestrator may not advance while a child in its Set is not ready (62pkkg).\n  - [child-status-not-ready] 62pkkg: child 62pkkg has status 'draft' (must be to-review, reviewed, approved, auto-approved, or executed)\n    Remedy: bring the child to `to-review` with `aw ipd set to-review 62pkkg`"
contains \x1b: False

$ rg -n '38;5;|\x1b\[' agent_workflows/orchestrator_readiness.py agent_workflows/status_set.py
(exit code 1, empty output; zero hardcoded ANSI escapes)
```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is ONE cohesive change addressing the diagnostic clarity and visual ergonomics of refusal messages across the status setter and orchestrator readiness surfaces. Execution requires explicit human approval first.

OPEN QUESTIONS: both are resolved, with the demonstrations recorded in their rationales; none blocks.

INVARIANTS THE EXECUTOR MUST HOLD. (1) No gate predicate, exit code, or refusal condition changes; only message text. (2) `render_human`'s default output (no new arguments) is byte-identical, because `aw ipd coverage` and the runner's continue-handoff prompt embed it. (3) Agent/JSON output keeps every existing key and value and gains only additive fields; no ANSI escape ever reaches it. (4) Strings returned by `validate_transition_allowed` and `approval_refusals` stay plain, since they are reused as `Diagnostic.detail` and by `specs.run_set`. (5) Styling uses only the shared lifecycle resolver (`uonrjg` R10.3).

SCOPE FENCE. `- Scope-Paths:` is a DECLARATION, not a stop condition. If an out-of-scope edit proves necessary (for example a phrase another test file asserts on), make it and justify it to `aw ipd finalize` with `--scope-reason <path>=<why>`; acknowledge a declared-but-unmodified path with `--scope-ack`. STOP and report only for a genuinely unsafe condition, such as a concurrent edit to the same file that cannot be combined.

PASTE ACTUAL OUTPUT. Every `V-*` must carry the real command output observed; never claim a test passed, or a message reads a certain way, without pasting it.

COMMIT PATH. Commit only declared paths through `aw commit juu1rj -- <paths>`; verify with `git diff --cached --name-only`; never `git add -A`, never `-a`, never push.

LIFECYCLE. Reaching `.aw/records/plans/executed/` is owed once every `V-*` passes and `aw ipd lint --phase pre-transition` conforms. Under `aw oc run` / `aw agy run` the runner performs the transition; when executed by hand, use `aw ipd finalize` (or `aw ipd set executed juu1rj`). Never hand-edit `- Status:` and never `git mv` the file.
