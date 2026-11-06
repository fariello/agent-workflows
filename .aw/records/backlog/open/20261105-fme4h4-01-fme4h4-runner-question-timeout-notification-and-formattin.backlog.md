- Id: fme4h4
- Status: open
- Set: fme4h4
- Priority: medium
- Work-Kind: feature
- Summary: Runner drain question prompt timeout notification and formatting

## Workflow history
- 2026-11-06 created (aw backlog): Runner drain question prompt timeout notification and formatting

## Problem

When an autonomous run pauses with items awaiting human input, `runner_shared.drain_parked_questions` prompts the user for answers at the terminal using `runner_shared.prompt_for_free_text`. Today this interaction has several UX defects:

1. **Silent timeout on expiration**: `prompt_for_free_text` waits on `select.select` up to `question_timeout` (default 300 seconds). When the deadline expires without user keystrokes, the function returns `None` without printing any newline or timeout notification. In terminal scrollback, the next question or the parked summary prints immediately after the `Answer: ` prompt, creating the illusion that the runner did not wait at all and failed instantaneously.
2. **Poor visual distinction**: The question text, options, and prompt blend into surrounding execution logs and runner terminal stream outputs. There is no distinct box framing, visual divider, or highlight colors to make interactive prompts stand out.
3. **Opaque question headers**: The prompt header shows an internal hash and counter, such as `[g-08683e6391f14c68] (1 raiser(s), unblocks 1):`. This internal fingerprint is meaningless to users and gives no clear context about which artifact, file, or feature is blocked.
4. **Unstructured text dumps**: Worker agents often pack the entire question context, decision, options, and recommendation into a single unbroken paragraph in `questions[].text`. It lacks the clear structure of the `/askme` standard (Subject, Situation, Decision, Options with consequences, Recommendation with strength, Uncertainty).

## Required change

1. **Explicit timeout feedback**: When `prompt_for_free_text` times out, output a clear message on the stream (for example, `[Timed out after 300s. Questions parked to answers.md; resume with aw oc run resume <run_id>]`) so that terminal scrollback unambiguously explains why the prompt closed.
2. **Visual distinction and color formatting**: Format terminal questions with clear visual separation on interactive TTY streams (honoring `NO_COLOR` and non-TTY redirection):
   - Use bold headers, borders or visual delimiters, and colored option numbering.
   - Distinctly style the input prompt (`Answer: `).
3. **Informative question headers**: Replace the opaque fingerprint `[g-hash]` header with human-readable artifact context:
   - State the affected artifact id6, logical type (spec, plan, backlog), and artifact title.
   - State the plain-language impact (for example, `Blocks approval of Spec 36epid (Survey Collection Pipeline)`).
   - If multiple artifacts share the same question, list each affected artifact clearly.
4. **Structured `/askme` rendering and worker schema alignment**:
   - Update worker prompt directives and question validation to encourage or require structured question components matching the `/askme` standard (`.aw/system/workflows/askme/askme.md`).
   - In the runner's terminal question renderer, format structured sections (Subject, Current Situation, Decision Needed, Options & Consequences, Recommendation & Strength) with clean indentation and headings rather than rendering a raw single-paragraph text blob.

## Evidence

- `agent_workflows/runner_shared.py:19515-19625` (`prompt_for_free_text`): returns `None` on timeout with no printed notice.
- `agent_workflows/runner_shared.py:25460-25605` (`drain_parked_questions`): formats `prompt_str` with `[g-hash] (N raiser(s), unblocks M):` and iterates through question groups without timeout announcements.
- `agent_workflows/question_inbox.py`: groups questions by fingerprint without resolving artifact title or human-readable summary for terminal display.
- `.aw/records/runs/run-20261106T022102Z-4062370`: live incident on 2026-11-06 where a 1.5-hour review paused for questions at drain, timed out after 300s, and printed `Answer: ` immediately followed by the next question and summary, appearing to the user as an immediate failure that did not wait for an answer.
- `.aw/system/workflows/askme/askme.md`: defines the repository standard for clear, structured human decision prompts.

## Acceptance evidence

1. Automated unit and integration tests in `tests/test_question_drain.py` asserting that:
   - When a prompt times out, the stream receives an explicit timeout message with the elapsed seconds and parked destination.
   - The question header includes the affected artifact ID and type instead of only an internal group hash.
   - ANSI styling is emitted when streams are TTYs and omitted when `NO_COLOR=1` or streams are non-interactive.
2. An end-to-end dry-run or fixture test showing structured section rendering for multi-part `/askme` questions.

## Scope limits

This item does not change the core mid-run question architecture or remove question timeouts (bounded timeouts remain necessary to prevent wedged headless processes). It focuses on terminal UX, timeout transparency, and question comprehensibility.
