- Id: ucuqq6
- Status: open
- Blocks-Release: next
- Set: ucuqq6
- Priority: high
- Work-Kind: feature
- Summary: Runner questions follow /askme and support free-text answers and a clarification re-ask loop

## Workflow history
- 2026-11-06 created (aw backlog): Runner questions follow /askme and support free-text answers and a clarification re-ask loop

## Problem

The autonomous runners (`aw oc run` and `aw agy run`) let a worker agent park an item with questions for the human. The worker writes each question into the `questions[]` array of its JSON outcome file. The runner then shows the question to the human at the terminal when the queue drains (`runner_shared.drain_parked_questions`) and writes it into `<run_dir>/answers.md` for offline answering (`question_inbox.write_answers_file`). After the human answers, the runner resumes the parked item and gives the worker the answer in a `## Answers from the maintainer` notice (`runner_shared.build_answer_notice`).

This path does not meet the repository's question standard (`.aw/system/workflows/askme/askme.md`) or its writing standard (`.aw/system/workflows/technical-writing/technical-writing.md`). Four defects are observed in the code at commit `af0bd1dbc`:

1. **Questions have no required structure.** The worker directive tells the worker only to record the human's question in `questions[]`. The schema has one free-form `text` field of up to 2000 characters. Nothing asks for, checks, or renders the six facts that askme requires. Workers often write the whole question as one paragraph.
2. **The question assumes the human already knows the context.** The terminal header shows an internal group fingerprint and counters, for example `[g-08683e6391f14c68] (1 raiser(s), unblocks 1):`. `answers.md` uses `### Group <group_id>` and a list of raiser id6 values. Neither surface gives the artifact title, type, file path, or a plain-language summary. A human who has not opened the repository cannot tell what is blocked or why.
3. **Free-text answers are possible but not offered.** The data layer accepts free text by default (`allow_free_text` defaults to `true`). However, the terminal prompt prints only `Options:` and `Answer: `. It does not tell the human that a typed answer, a question, or a request for more context is accepted. `answers.md` gives the same `Answer: ` line with no such statement. A numeric answer outside the option range is silently dropped.
4. **There is no clarification loop.** The resumed worker receives any free text as a maintainer answer. No directive tells the worker that an answer such as "I do not understand" or "what does X mean?" is not a decision. askme states: "A complaint or clarification request is not a decision." It also states that such an answer is a rewrite request. The worker can therefore guess a decision from a request for help, and the human's request goes unanswered.

## Required change

The implementer must change `agent_workflows/runner_shared.py`, `agent_workflows/question_inbox.py`, the worker execution directives, and the runner prompt templates. The same behavior must apply on both hosts (`aw oc run` and `aw agy run`). The changes must produce the four results below.

### R1. Every runner question follows askme and the writing standard

1. The worker directives must tell the worker to compose every `questions[]` entry by `.aw/system/workflows/askme/askme.md` ("Compose a question the user can answer" and "Check before sending") and by `.aw/system/workflows/technical-writing/technical-writing.md`. Today the directives cite askme only for deciding whether a question belongs to the human.
2. The question text must be clear, concise, accurate, direct, and free of jargon. It must follow the writing principles of ASD-STE100 Simplified Technical English: short complete sentences, active voice, familiar words, consistent terms, and no filler or rhetorical bloat.
3. Each question must carry these six sections, in this order:
   - **Subject and purpose:** the feature, behavior, or artifact, and what it does, in plain language.
   - **Current situation:** what exists now, or the failure that was observed.
   - **Decision needed:** exactly what the human must choose or clarify, and why the answer is needed.
   - **Options and consequences:** each option and its concrete consequences, limitations, and downstream effects.
   - **Recommendation:** the recommended option, the factual reason, and the strength, which is one of `very weak`, `weak`, `medium`, `strong`, or `very strong`.
   - **Uncertainty:** each unknown that could change the decision.
4. The `questions[]` schema (`questions_schema_literal` and the validator that builds each clean entry) must carry the six sections as separate fields, or as one documented structured format inside `text`. The implementing plan chooses which. The validator must reject a question that lacks a section or that has a recommendation strength outside the five allowed values. The rejection must tell the worker which section is missing. The current 2000-character limit must be reviewed so that a complete six-section question fits.
5. The terminal renderer and `answers.md` must show the six sections under labeled headings. They must not show one unbroken paragraph.

### R2. The human needs no prior knowledge

1. Each question surface must assume that the human has not opened the repository, does not remember earlier discussion, and does not know what any id6 refers to.
2. The terminal prompt and `answers.md` must not use an opaque group fingerprint (such as `[g-08683e6391f14c68]`) or a bare id6 as the primary label of a question.
3. For each affected artifact, the surface must show the artifact title, its type (spec, plan, or backlog item), its file path relative to the repository root, and a one-sentence plain-language summary of what the artifact is about. `write_question` already resolves the artifact path; the runner must also resolve the title and summary from the artifact's front matter. When several artifacts share one question, the surface must list each one.
4. The group id may still appear as a secondary reference, because `answers.md` ingestion and `aw runs answer` use it to route answers.

### R3. The human can always write a free-text answer

1. The terminal prompt and `answers.md` must state that the human may type an option number or a free-text answer. The statement must say that a free-text answer may be a decision, a question, or a request for more context.
2. The worker directive must keep `allow_free_text` true for every question surfaced to a human. The validator must reject `allow_free_text: false`, or the runner must ignore it. The implementing plan chooses which and records the reason.
3. A free-text answer must be stored exactly as typed, after the existing control-character cleaning and the 4000-character limit. It must reach the resumed worker turn through `build_answer_notice`.
4. A numeric answer outside the option range must not be silently dropped. The runner must either store it as free text or re-prompt with a message that names the valid range.

### R4. A clarification request leads to a rewritten question

1. The answer notice and the resume directive must tell the worker to classify each answer before acting on it. An answer is either a definite decision or a clarification request. Examples of a clarification request are "I do not understand", "what does X mean?", a request for more context, and an askme invocation such as "/askme that again".
2. When the answer is a clarification request, the worker must not guess a decision, must not pick its own recommendation, and must not treat the request as consent. This follows askme: "A complaint or clarification request is not a decision."
3. Instead, the worker must answer the human's question inside the rewritten question, add the missing background, and rewrite the question with all six R1 sections. The worker must then return the rewritten question in `questions[]` and park the item again, so that the runner shows it to the human again.
4. When an answer both makes a clear choice and criticizes the wording, the worker must record the choice. This follows askme "Ask and wait".
5. The runner must link the rewritten question to the original question, so that `aw runs` and `answers.md` show the earlier exchange in order. The re-ask must count against the existing `--question-rounds` limit (default 2, from `DEFAULT_QUESTION_ROUNDS`). When the limit is reached, the runner must park the item with the rewritten question still open. It must not force a decision.

## Evidence

All line numbers refer to commit `af0bd1dbc`.

- `agent_workflows/runner_shared.py:26327-26359` (`QUESTION_REQUIRED_KEYS`, `QUESTION_TEXT_MAX_LENGTH`, `questions_schema_literal`): the schema carries one free-form `text` field (maximum 2000 characters) and no askme sections.
- `agent_workflows/runner_shared.py:27124-27190` (question entry validation): checks options and the `allow_free_text` type only; `allow_free_text` defaults to `true`; no content structure is checked.
- `agent_workflows/runner_shared.py:33698-33701` and `agent_workflows/runner_shared.py:36502-36506` (worker directives): cite askme only for "Establish facts before asking", the decision about who answers. They do not cite "Compose a question the user can answer" or the technical writing standard.
- `agent_workflows/runner_shared.py:25517-25528` (`drain_parked_questions`) and `agent_workflows/runner_shared.py:19541-19566` (`prompt_for_free_text`): build the header `[<group_id>] (<n> raiser(s), unblocks <m>):`, print the raw text and `Options:`, and end with `Answer: `. They do not mention free text.
- `agent_workflows/runner_shared.py:25541-25563`: an integer outside the option range does not set `selected_choice`, and it is stored as free text only if `allow_free_text` is true; otherwise the answer is dropped with no message.
- `agent_workflows/question_inbox.py:1367-1389` (`write_answers_file`): writes `### Group <group_id>`, question ids, and raiser id6 values; no artifact title, type, path, or summary; a bare `Answer: ` line.
- `agent_workflows/question_inbox.py:626-659` (`write_answer`): accepts free text when `allow_free_text` is true, so the data layer already supports R3.
- `agent_workflows/runner_shared.py:6433-6475` (`build_answer_notice`): passes the answer to the resumed worker as quoted human input with no instruction to tell a decision apart from a clarification request. It is used by the resume paths at `agent_workflows/runner_shared.py:42072`, `42095-42097`, `43052-43054`, and `43211`.
- A search for `clarif` in `agent_workflows/runner_shared.py` and `agent_workflows/question_inbox.py` finds no match. No clarification or re-ask behavior exists.
- `agent_workflows/runner_shared.py:17483` (`DEFAULT_QUESTION_ROUNDS = 2`): the existing limit on question rounds that R4.5 reuses.
- `.aw/system/workflows/askme/askme.md`, sections "Compose a question the user can answer", "Check before sending", and "Ask and wait": the six required facts, the zero-knowledge assumption, and the rule that a clarification request is a rewrite request.
- Backlog `fme4h4` (`.aw/records/backlog/open/20261105-fme4h4-01-fme4h4-runner-question-timeout-notification-and-formattin.backlog.md`) records the observed fingerprint header `[g-08683e6391f14c68]` from run `run-20261106T022102Z-4062370`.
- Maintainer instruction in this session: create this item as a release-blocking feature with high priority. This instruction authorizes creating the item. It does not authorize implementation.

## Acceptance evidence

The implementer must provide the evidence below. Each test must drive real functions or CLI commands and assert on real output, exit codes, and files. Tests must not read production source text (repository rule P16).

1. **Schema validation (R1.4).** Tests in `tests/test_question_carrier.py` or a new test module pass outcome JSON to the questions validator and show that:
   - a question with all six sections and a valid strength is accepted;
   - a question that lacks a section is rejected, and the message names the missing section;
   - a recommendation strength outside the five allowed values is rejected.
2. **Rendering (R1.5, R2, R3.1).** Tests in `tests/test_question_drain.py` and `tests/test_question_inbox.py` capture the terminal prompt text and the written `answers.md`, and show that:
   - the six sections appear under labeled headings;
   - each affected artifact shows its title, type, relative path, and summary;
   - no line starts with a bare `[g-` fingerprint label, and the primary label is not a bare id6;
   - a statement that free-text answers, questions, and clarification requests are accepted is present.
3. **Free-text round trip (R3.3, R3.4).** A test types a free-text answer at a simulated TTY prompt and also fills one into `answers.md` and ingests it. The test shows that the exact text appears in the `build_answer_notice` output for the resumed turn. A second test shows that an out-of-range number is stored as free text or causes a re-prompt; it is never silently dropped.
4. **Clarification loop (R4).** An end-to-end test with a scripted fake worker shows this sequence: the worker raises a question; the human answers "I do not understand what option 2 changes"; the resumed worker returns a rewritten question and does not record a decision; the runner shows the rewritten question again, linked to the original question; the human chooses an option; the item continues. A second test shows that reaching the `--question-rounds` limit leaves the rewritten question open and parks the item.
5. **Host symmetry.** The tests above, or a parameterized copy, pass for both the OpenCode and the Antigravity runner paths.
6. **Live trial.** The implementer runs at least one real `aw oc run` with a plan that makes the worker raise a human question. The implementer pastes the rendered terminal question and the `answers.md` excerpt into the plan evidence. The implementer answers once with a clarification request and pastes the rewritten question. The report must state any case where the live model did not follow the directive. Instructions cannot guarantee model compliance, so the schema check in item 1 is the enforced part.
7. The routine suite (`python3 -m pytest`) passes, and the runner output is pasted.

## Scope limits

- Backlog `fme4h4` owns the timeout notice, ANSI color, and box styling of the terminal prompt. This item owns the question content, the artifact context labels, the free-text statement, and the clarification loop. `fme4h4` items 3 and 4 (header context and structured rendering) overlap R1.5 and R2. The plan that implements either item must cite the other and implement the overlap once.
- Backlog `n2lr3g` owns making askme mandatory in interactive agent conversations and in the review workflows. This item covers only questions that pass through the runner question channel.
- This item does not remove the bounded question timeout or the `--question-rounds` limit, and it does not change who may answer (`actor` must stay `human`).
- This item does not change how gate-answer questions (`gate_answer_question`) or preflight open-question prompts are chosen. It applies to them only where they display text to a human through the same renderer.
- This item does not promise that a worker model will always write a good question. The validator enforces the structure; it cannot judge clarity. Clarity is checked by the live trial in acceptance item 6.
