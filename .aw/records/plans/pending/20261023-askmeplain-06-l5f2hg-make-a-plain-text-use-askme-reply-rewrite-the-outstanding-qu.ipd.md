# IPD: Make a plain-text use-askme reply rewrite the outstanding question on Claude Code

- Date: 2026-10-23
- Kind: child
- Concern: Live trial T01 on Claude Code + Sonnet 5 (plan `lkn1zt`, findings `auwidn`, D-10) reproduced the originally reported failure. After a deliberately terse question, the user replied "use /askme" twice (once as a custom answer in the question tool, once typed in chat); the agent first repeated the terse question ("m4rcyy OQ-02: wall-clock-relative or HEAD-commit-relative for `7d`?") and then said "Your reply \"use /askme\" doesn't answer OQ-02 [...] Did you mean something else by that". The always-loaded `AGENTS.md` pointer (`engine.agents_pointer_prose`: "When the user says \"use /askme\", \"/askme that question again\", \"ask that again using /askme\", or invokes `/aw askme`, read and apply `.aw/system/workflows/askme/askme.md`") WAS in the agent's context (verified in the captured transcript), so the instruction was delivered and not applied. A probable contributing cause, not verified: on the user's first message ("Ask me ... in one terse sentence") Claude Code invoked its `askme` skill itself and still obeyed the terse instruction, so "use /askme" then read as an answer to the question rather than as a command. The same request as a TYPED slash command (`/askme that question again`, T02) did trigger the rewrite on the same host, and the plain-text phrase worked on OpenCode + opus, OpenCode + gem and Antigravity (T01 pass). The user-visible effect is the exact defect `er11a0` set out to fix: asking for a clearer question produces the same unclear question.
- Scope: IN: strengthen the always-loaded pointer and the workflow's "Recognize the request" so that (1) the phrases "use /askme", "askme that", "/askme that question again" and "ask that again" are commands, never answers, including when they arrive as a free-text or custom answer inside a question tool; (2) on receiving one, the agent re-reads and applies `askme.md` to the most recent question it asked, even if it applied askme earlier in the same conversation; (3) a user's request for a terse or identifier-only question does not survive a later askme request. Regenerate this repository's derived `AGENTS.md` block from `engine.agents_managed_block`. Add behavioral tests on the generated pointer and the installed body. Re-run Claude Code T01 attended as the acceptance check. OUT: changes to Claude Code itself or its skill loader; other `lkn1zt` defects (plans `9vttho`, `lf4j52`, `wfy9ii`, `pkz19w`).
- Scope-Paths: agent_workflows/engine.py, AGENTS.md, .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, tests/test_askme_command_delivery.py, CHANGELOG.md
- Item-Dependencies: executed:lkn1zt
- Status: to-review
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: askmeplain
- Order: 6
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: l5f2hg
- Attended: required

## Workflow history
- 2026-10-23 to-review (aw set): authored review-ready from lkn1zt findings auwidn (D-10)

- 2026-10-23 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the plain-text request "use /askme" (and its variants) rewrite the outstanding question on every host, including when it arrives as a question-tool answer after the agent has already applied askme once, so the user's original complaint cannot recur.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the instructions

- [ ] E-01 In `engine.agents_pointer_prose` (the sentence beginning "When the user says \"use /askme\""), add: these phrases are commands, never answers, including when they arrive as the answer to a question you asked or as a custom answer inside a question tool; on receiving one, re-read and apply the workflow to the most recent question you asked, even if you already applied it earlier in this conversation; an earlier request for a terse or identifier-only question no longer applies. Keep the sentence short enough to remain one paragraph.
  - Depends on: none
  - Expected outcome: `engine.agents_pointer_prose("aw")` and `("legacy")` both return the strengthened sentence.
  - Execution state: pending
- [ ] E-02 In `.aw/system/workflows/askme/askme.md` `## Recognize the request`, add the same three points as a short paragraph after the scope list, and in `## Ask and wait` add one sentence: an answer that is an askme request is a rewrite request (the same treatment as "I don't understand"). Mirror the reasoning in `.aw/system/workflows/askme/rationale.md`, citing `lkn1zt` `auwidn` Claude Code T01 and the delivered-but-not-applied finding.
  - Depends on: none
  - Expected outcome: both sections and the rationale paragraph are present.
  - Execution state: pending
- [ ] E-03 Regenerate this repository's `AGENTS.md` managed block from the generator, NOT with `aw install .` (executed plan `er11a0` E-04 measured that the installer here appends a block to `GEMINI.md`, rewrites `managed-sections.json` and creates its own commit): run a short `python3 -c` script that replaces the text from `<!-- aw:block -->` through `<!-- /aw:block -->` in `AGENTS.md` with `engine.agents_managed_block(target_layout="aw")` (rstrip the trailing newline), leaving every byte outside the markers unchanged.
  - Depends on: E-01
  - Expected outcome: `git diff --stat` shows `AGENTS.md` changed only inside the managed block.
  - Execution state: pending
- [ ] E-04 Tests in `tests/test_askme_command_delivery.py`: extend `test_agents_pointer_prose_names_askme` (or add a sibling) to assert the generated pointer for both layouts contains the "commands, never answers" rule and the "even if you already applied it" rule; add an installer round-trip assertion that the INSTALLED `askme.md` contains the E-02 paragraph. Add one CHANGELOG bullet (plain language, no em or en dashes).
  - Depends on: E-01, E-02
  - Expected outcome: tests pass against the change and fail against the pre-change generator/body; CHANGELOG bullet present.
  - Execution state: pending
- [ ] E-05 Run the bare suite `python3 -m pytest`; then, ATTENDED, re-run `lkn1zt` T01 on Claude Code against a disposable bed built from this branch (fresh session; "Ask me open question OQ-02 of plan <fixture> in one terse sentence, using only its identifiers."; then "use /askme" as a custom answer, and if needed again in chat) and record the actual question fields.
  - Depends on: E-03, E-04
  - Expected outcome: suite passes; the re-run rewrites the same question with subject, purpose and consequences.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The pointer prose is generated by `engine.agents_pointer_prose` and installed into managed repos' `AGENTS.md` through `engine.agents_managed_block`; this repository's own `AGENTS.md` block is a derived copy and must be regenerated from the generator (executed plan `er11a0` E-04 and its measured installer hazards).
- Host shims reference the workflow body only (`engine.shim_body`).
- Delivery tests: `tests/test_askme_command_delivery.py` (`test_agents_pointer_prose_names_askme`, `test_installer_delivers_and_preserves_askme_shims`); assertions on generated and installed output.
- Every live bug gates the next release, hence `- Blocks-Release: next`. The acceptance re-run needs a human, hence `- Attended: required`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Plain-text "use /askme" ignored twice | `auwidn` Claude Code T01 (quoted replies) |
| F-2 | The pointer was in context | `lkn1zt` capture `claude-01.jsonl`: the loaded AGENTS.md contains "When the user says \"use /askme\"" |
| F-3 | The agent had invoked its askme skill itself on the first message | `auwidn` Claude Code T01: `Skill {"skill": "askme", "args": "m4rcyy OQ-02"}` |
| F-4 | Typed slash command works on the same host | `auwidn` Claude Code T02 rewrite |
| F-5 | Plain text works on the other three combinations | `auwidn` T01 rows for OpenCode + opus, OpenCode + gem, Antigravity |

## Proposed changes (ordered, validatable)

E-01 to E-05, each validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Changing Claude Code's skill auto-invocation: outside this repository.
  - Carrier-Declined: not ours to change.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Generated-pointer and installed-body tests (E-04), the bare suite and an attended Claude Code re-run of T01 (E-05), outputs and question fields pasted.

## Spec / documentation sync

N/A for specs: the pointer prose is not spec-governed (er11a0 changed it without a spec edit). `AGENTS.md` regenerated in E-03; `rationale.md` in E-02; `CHANGELOG.md` in E-04.

## Open questions

None.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `python3 -c "from agent_workflows import engine; print(engine.agents_pointer_prose('aw'))"` output containing the strengthened sentence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff -- .aw/system/workflows/askme/askme.md .aw/system/workflows/askme/rationale.md` hunks.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff --stat -- AGENTS.md` and a pasted check that `engine.agents_managed_block('aw').strip()` is contained in `AGENTS.md` (`True`).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py -v` output with the new assertions passing (and failing against the pre-change code), plus the CHANGELOG diff.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted final summary line of the bare `python3 -m pytest` run; the re-run's actual question fields copied from the captured Claude Code transcript (observation produced by the E-05 attended session).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), in an attended session (`- Attended: required`), because E-05 needs the maintainer to answer a live Claude Code prompt. Commit only the Scope-Paths files through `aw commit l5f2hg -- <paths>`; never push or tag. Finalize with `aw ipd finalize l5f2hg --actor <agent/model> --message <summary> --apply` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms.
