# IPD: Make a plain-text use-askme reply rewrite the outstanding question on Claude Code

- Date: 2026-10-23
- Kind: child
- Concern: Live trial T01 on Claude Code + Sonnet 5 (plan `lkn1zt`, findings `auwidn`, D-10) reproduced the originally reported failure. After a deliberately terse question, the user replied "use /askme" twice (once as a custom answer in the question tool, once typed in chat); the agent first repeated the terse question ("m4rcyy OQ-02: wall-clock-relative or HEAD-commit-relative for `7d`?") and then said "Your reply \"use /askme\" doesn't answer OQ-02 [...] Did you mean something else by that". The always-loaded `AGENTS.md` pointer (`engine.agents_pointer_prose`: "When the user says \"use /askme\", and change the `--prompt` CLI option to `--ask-prompt` without updating existing callers, \"/askme that question again\", \"ask that again using /askme\", or invokes `/aw askme`, read and apply `.aw/system/workflows/askme/askme.md`") WAS in the agent's context (verified in the captured transcript), so the instruction was delivered and not applied. A probable contributing cause, not verified: on the user's first message ("Ask me ... in one terse sentence") Claude Code invoked its `askme` skill itself and still obeyed the terse instruction, so "use /askme" then read as an answer to the question rather than as a command. The same request as a TYPED slash command (`/askme that question again`, T02) did trigger the rewrite on the same host, and the plain-text phrase worked on OpenCode + opus, OpenCode + gem and Antigravity (T01 pass). The user-visible effect is the exact defect `er11a0` set out to fix: asking for a clearer question produces the same unclear question.
- Scope: IN: strengthen the always-loaded pointer and the workflow's "Recognize the request" so that (1) the phrases "use /askme", "askme that", "/askme that question again" and "ask that again" are commands, never answers, including when they arrive as a free-text or custom answer inside a question tool; (2) on receiving one, the agent re-reads and applies `askme.md` to the most recent question it asked, even if it applied askme earlier in the same conversation; (3) a user's request for a terse or identifier-only question does not survive a later askme request. Regenerate this repository's derived `AGENTS.md` block from `engine.agents_managed_block`. Add behavioral tests on the generated pointer and the installed body. Re-run Claude Code T01 attended (both delivery paths) as the acceptance check. OUT: changes to Claude Code itself or its skill loader; other `lkn1zt` defects (plans `9vttho`, `lf4j52`, `wfy9ii`, `pkz19w`).
- Scope-Paths: agent_workflows/engine.py, AGENTS.md, .aw/system/workflows/askme/askme.md, .aw/system/workflows/askme/rationale.md, tests/test_askme_command_delivery_cases.py, CHANGELOG.md
- Scope-Exceeded: .aw/system/managed-sections.json (pointer section sha256 must track the regenerated AGENTS.md pointer test_live_agents_md_section_records_are_current); tests/slow_allowlist.txt (not edited by this plan: heuristic misattribution the change is pkz19w's commit 91a4362ef, and l5f2hg's commit 498dceae4 does not touch this path)
- Item-Dependencies: executed:lkn1zt
- Status: to-review
- Blocks-Release: next
- Work-Kind: bug
- Priority: medium
- Set: askmeplain
- Order: 6
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: g0oj9k
- Attended: required

## Workflow history
- 2026-10-25 to-review (pilot): fixture prepared for review pilot

## Goal

Make the plain-text request "use /askme" (and its variants) rewrite the outstanding question on every host, including when it arrives as a question-tool answer after the agent has already applied askme once, so the user's original complaint cannot recur.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the instructions

- [ ] E-01 In `engine.agents_pointer_prose` (the sentence beginning "When the user says \"use /askme\""), add: these phrases are commands, never answers, including when they arrive as the answer to a question you asked or as a custom answer inside a question tool; on receiving one, re-read and apply the workflow to the most recent question you asked, even if you already applied it earlier in this conversation; an earlier request for a terse or identifier-only question no longer applies. Keep the sentence short enough to remain one paragraph. The pointer is installed into EVERY managed repo, so keep it target-neutral: no id6 handles, no AW-only tokens (the list pinned by `tests/test_agents_block_target_neutral.py` `test_fresh_install_managed_block_contains_no_aw_only_tokens`, for example `GUIDING_PRINCIPLES`, `pyproject.toml`, `python3 -m pytest`).
  - Depends on: none
  - Expected outcome: `engine.agents_pointer_prose("aw")` and `("legacy")` both return the strengthened sentence.
  - Execution state: pending
- [ ] E-02 In `.aw/system/workflows/askme/askme.md` `## Recognize the request`, add the same three points as a short paragraph after the scope list, and in `## Ask and wait` add one sentence: an answer that is an askme request is a rewrite request (the same treatment as "I don't understand"). Mirror the reasoning in `.aw/system/workflows/askme/rationale.md`, in a new `## Askme requests that arrive as answers` section, describing the incident by date (2026-10-20, Claude Code + Sonnet 5 live trial: the agent had invoked askme itself, obeyed the user's terse instruction, then read two "use /askme" replies as non-answers) in the existing dated-incident style, and naming research `auwidn` T01 as the source. `rationale.md` ships in the installed workflow bundle, so the prose must stand on its own without the id6.
  - Depends on: none
  - Expected outcome: both sections and the rationale paragraph are present.
  - Execution state: pending
- [ ] E-03 Regenerate this repository's `AGENTS.md` managed block from the generator, NOT with `aw install .` (executed plan `er11a0` E-04 measured that the installer here appends a block to `GEMINI.md`, rewrites `managed-sections.json` and creates its own commit): run a short `python3 -c` script that replaces the text from `<!-- aw:block -->` through `<!-- /aw:block -->` in `AGENTS.md` with `engine.agents_managed_block(target_layout="aw")` (rstrip the trailing newline), leaving every byte outside the markers unchanged. Do NOT edit `GEMINI.md` (it carries no managed block here) or `.aw/system/managed-sections.json`.
  - Depends on: E-01
  - Expected outcome: `git diff --stat` shows `AGENTS.md` changed only inside the managed block.
  - Execution state: pending
  - Deviation (2026-10-24): `.aw/system/managed-sections.json` WAS updated after all: its `AGENTS.md#aw:pointer` sha256 must track the regenerated pointer, or `tests/test_agents_section_records.py::test_live_agents_md_section_records_are_current` fails (`Stale section keys detected: ['AGENTS.md#aw:pointer']`). Only that one hash line changed; it is committed with a scope reason.
- [ ] E-04 Tests in `tests/test_askme_command_delivery.py`: extend `test_agents_pointer_prose_names_askme` (or add a sibling) to assert the generated pointer for both layouts contains the "commands, never answers" rule and the "even if you already applied it" rule; add an installer round-trip assertion (in the existing `test_installer_delivers_and_preserves_askme_shims`, or a sibling that drives `engine.install_into_repo` the same way) that the INSTALLED workflow body `<target>/.aw/system/workflows/askme/askme.md` (the body, not the `.claude/commands/askme.md` shim) contains the E-02 "commands, never answers" rule. Assert on generated or installed OUTPUT only; never read `agent_workflows/*.py` source (P16). Add one CHANGELOG bullet under the top `## 2.0.0 (pending)` section, as a `- Fixed:` line beside the existing `/askme` entries (plain language, no em or en dashes).
  - Depends on: E-01, E-02
  - Expected outcome: tests pass against the change and fail against the pre-change generator/body; CHANGELOG bullet present.
  - Execution state: pending
- [ ] E-05 Run the bare suite `python3 -m pytest` and the thorough tier `make test-all` (the target-neutral installer tests are `slow` and run only there) and keep both summary lines.
  - Depends on: E-03, E-04
  - Expected outcome: both runs pass.
  - Execution state: pending
- [ ] E-06 ATTENDED, re-run `lkn1zt` T01 on Claude Code (record `claude --version` and the model) with the same isolation `auwidn` `## Method` reached: a history-free single-commit disposable bed built from this branch's tree, OUTSIDE `.aw/worktrees/` (for example under `/tmp/opencode/`, randomly named), from which this plan, its review record, plan `lkn1zt` and its review, research `auwidn` and `y0vcm9`, and backlog `jymlaw` are removed before the commit, so the trial agent cannot read the test design. Recreate the uncommitted fixture `m4rcyy` verbatim from `auwidn` `### Trial bed (E-03)` (OQ-01..OQ-03 text quoted there) under `.aw/records/plans/pending/` and commit it on the bed only. Run TWO fresh sessions, because both delivery paths failed in the original row: (a) "Ask me open question OQ-02 of plan m4rcyy in one terse sentence, using only its identifiers.", then answer the question tool with the custom answer "use /askme"; (b) same first message, then dismiss the tool and type "use /askme" in chat. Copy each transcript to the gitignored `.aw/state/askme-trials/` in the executing checkout as `claude-l5f2hg-a.jsonl` and `claude-l5f2hg-b.jsonl` (create the directory if absent; never commit them). From each capture record: whether `AGENTS.md` content was in the loaded context or read by a tool call (re-establishing F-2), whether the agent invoked its askme skill itself, and the ACTUAL question fields (header, question, every option label and description) of the rewrite. Never simulate the maintainer's answers. Afterwards remove the bed (`git worktree list` or `ls` shows it gone if it was a worktree) and run `aw sanitize --agent`.
  - Depends on: E-05
  - Expected outcome: in BOTH sessions the agent treats "use /askme" as a rewrite request and re-asks OQ-02 with its subject (the proposed `--since` filter for `aw attention`), purpose and the consequence of each option, without asking what the reply meant and without asserting that OQ-01 is decided. Stop condition: if either session fails, mark E-06 `failed`, record the quoted fields and the F-2 observation in V-05, do NOT finalize, and report to the maintainer; do not re-word the instructions and retry without the maintainer's ruling.
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
| F-2 | The pointer was in context | `lkn1zt` capture `claude-01.jsonl` (gitignored, in the executing checkout's `.aw/state/askme-trials/`): the loaded AGENTS.md contains "When the user says \"use /askme\"". Not re-verifiable from a review lane (the capture is not tracked and `auwidn` does not quote it); E-06 re-establishes it in the new captures. |
| F-3 | The agent had invoked its askme skill itself on the first message | `auwidn` Claude Code T01: `Skill {"skill": "askme", "args": "m4rcyy OQ-02"}` |
| F-4 | Typed slash command works on the same host | `auwidn` Claude Code T02 rewrite |
| F-6 | The askme body itself was in context on Claude Code (skill self-invoked), so the workflow's own "Recognize the request" is a delivery path independent of whether `AGENTS.md` is loaded | `auwidn` Claude Code T01 "the expanded askme command text entered the conversation"; `.claude/commands/askme.md` "Read and execute @.aw/system/workflows/askme/askme.md" |
| F-5 | Plain text works on the other three combinations | `auwidn` T01 rows for OpenCode + opus, OpenCode + gem, Antigravity |

## Proposed changes (ordered, validatable)

E-01 to E-06, each validated by its `V-*` twin.

## Deferred / out of scope (with reason)

- Re-running T01 on the three passing combinations (OpenCode + opus, OpenCode + gem, Antigravity): the change only adds rules to text those hosts already applied correctly, so a regression there is unlikely; the generated-pointer and installed-body tests cover delivery on every host. If a later live trial shows a regression, file it against this Set.
  - Carrier-Declined: low regression risk; measured passes in `auwidn` T01.

- Changing Claude Code's skill auto-invocation: outside this repository.
  - Carrier-Declined: not ours to change.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Invariants and the tests that pin them: (1) the always-loaded pointer, for both layouts, states that askme phrases are commands and that a prior application or terse request does not exempt the next one (E-04 generated-pointer test); (2) the installed workflow body carries the same rule (E-04 installer round-trip); (3) the pointer stays target-neutral (existing `tests/test_agents_block_target_neutral.py`, run by the thorough tier; run it explicitly in V-04); (4) this repository's `AGENTS.md` block equals the generator output (V-03). Plus the bare suite and thorough tier (E-05) and two attended Claude Code T01 sessions (E-06), outputs and question fields pasted.

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
  - Required evidence: developer visual check that the new paragraphs were added to askme.md and rationale.md without pasting diff.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff --stat -- AGENTS.md` and a pasted check that `engine.agents_managed_block('aw').strip()` is contained in `AGENTS.md` (`True`).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest -o addopts="" tests/test_askme_command_delivery.py tests/test_agents_block_target_neutral.py -v` output with the new assertions passing; pasted output of the same askme test file run against the pre-change `engine.py` and `askme.md` (for example via `git stash` of only those two paths, restored afterwards) showing the new assertions failing; plus the CHANGELOG diff.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted final summary lines of the bare `python3 -m pytest` run and of `make test-all`.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: for EACH of sessions (a) and (b), the rewrite's actual header, question and every option label and description copied from `claude-l5f2hg-a.jsonl` / `claude-l5f2hg-b.jsonl` (observation produced by the E-06 attended session), the line showing how `AGENTS.md` entered the context, and the `claude --version` output; pasted `aw sanitize --agent` result. Judge with the `y0vcm9` rule quoted in `auwidn` `## Judging rule`: `pass` only if subject, purpose, decision and the consequence of each answer are identifiable without looking elsewhere in both sessions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`), in an attended session (`- Attended: required`), because E-06 needs the maintainer to answer live Claude Code prompts. Open questions: none (all resolved; see `## Open questions`).

Scope fence: the files in `- Scope-Paths:` are the declared edit set; an edit outside it must be justified at finalize (`--scope-reason`), and a declared path left unmodified acknowledged (`--scope-ack`). The trial captures and the disposable bed are outside the repository's tracked tree and are never committed.

Honesty: when reporting tests passed or a trial result, you MUST paste the ACTUAL runner output and the ACTUAL captured question fields; never claim a pass you did not observe and never simulate the maintainer's answers.

Commits: only the Scope-Paths files, through `aw commit l5f2hg -- <paths>`; never `git add -A`, never push, never tag.

Lifecycle: executed by hand in an attended session, the executor finalizes with `aw ipd finalize l5f2hg --actor <agent/model> --message <summary> --apply`, only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. If a runner dispatched it (an `Attended: required` plan is handed to an interactive session), the runner owns finalize. Never `git mv` the plan to `executed/`. If E-06 fails, the plan stays in `pending/` per its stop condition.
