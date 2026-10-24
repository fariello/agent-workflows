# Historical Rationale and Incidents for /askme

This document preserves the background, incident history, and reasoning behind the rules in the `/askme` workflow. It is kept for historical reference and context; agents executing `/askme` are not required to read this document.

## Why this workflow exists

P12 and the `AGENTS.md` pointer require self-contained interactive questions, and both are in an agent's loaded context. Despite that, agents repeatedly finished work with the human's questions unasked, or asked them as a wall of chat prose carrying repository jargon the human had no context for.

On 2026-09-08, an agent authored five plans containing eleven open questions, asked the maintainer none of them, and reported completion. In the same session, it referred to `run_engine.RunEngine`, `IPD-S404`, and bare id6 handles in a question addressed to a human who had never seen them. A rule an agent reads and still breaks needs an invocable entry point and a gate, not another copy of the prose.

## Why P12 is referenced rather than re-read as a ritual

An earlier version of this workflow instructed the agent to re-read P12 before composing. On 2026-09-08, that instruction was obeyed, and the prompt composed immediately afterwards was one the maintainer could not read at all. Re-reading the principle prevented nothing, because what the run needed was not in it, and the ritual manufactured false confidence ("I read P12, so my prompt is fine"). The actionable guidance was moved directly into composition rules.

## Why symptom before choice, and why design choices differ

The original workflow required stating what was malfunctioning before naming any options. On 2026-09-08 and 2026-09-09, prompts opened inside an internal mechanism and never mentioned the malfunction, or referred to "the change I am about to plan" without ever saying what the change was (leading to the maintainer response: "I have 12 opencode sessions, I don't remember what this one is about").

However, requiring a malfunction or symptom before every choice created a different failure: agents invented bugs or symptoms when faced with a legitimate design choice or preference question. The revised workflow requires stating the current situation and need, capturing observed failures when fixing a defect without forcing invented malfunctions for clean designs.

## No jargon, and the failure of placeholder substitutions

Dropping an internal name or identifier must not be satisfied by deleting nouns and leaving a generic container word. If the head of a noun phrase is "a pair of helpers", "a module", "a mechanism", "a component", or "a system", the handle was removed and a void was left behind.

On 2026-09-08, a prompt that satisfied the no-jargon rule by substitution produced "a shipped pair of helpers" and "a 900-line run-state model", passing mechanical checks but leaving the maintainer unable to read it. When a thing cannot be described functionally, name it and explain what it does in one clause.

## Restating prior decisions

If a follow-up depends on an earlier decision, restate the decision in the new prompt. On 2026-09-08, a follow-up prompt said "the automatic block" referring to a previous answer, and the maintainer replied "What automatic check? I have zero context here."

## Measuring before asking

If the choice depends on a quantity (e.g. how many files or plans are affected), count or measure it first. On 2026-09-08, a prompt was composed asking the maintainer to choose between reusing retry code and bounding a retry directly, when the plan's own open question already gave a decision rule based on a measurement that had already been taken. The question was already answered before it was asked.

## Incomprehension reports and free-text responses

When a user reports incomprehension ("I have zero context here", "what is X?", "I did not understand a single word of that"), the prompt was defective. On 2026-09-08, the maintainer used the free-text option of the question tool to reply: "I wanted to pick write your own and say I did not understand a single word of your explanation." A report of incomprehension is not a decision, and recording it as a user resolution would misrepresent confusion as consent.

## Repository scans on bare /askme

Live trials in plan `lkn1zt` (findings `auwidn`, trial T05) showed that invoking `/askme` without arguments led multiple host and model combinations to scan the repository using `aw attention`, recursive `grep`, and `find` when no conversational question was pending. In a shared checkout, this caused agents to discover and ask open questions from plans authored by other agents or humans without confirming authorship. The no-argument scope rule therefore restricts candidate records strictly to those whose edits appear in the current conversation's own tool calls, explicitly forbids repository-wide discovery searches, and requires stopping with instructions when both conversational and session sources are empty.

## Recording only reasons the user gave

Live trials in plan `lkn1zt` (findings `auwidn`, Claude Code trial T09) showed that when a user chose an option by typing only "Creation date. And that question was way too long-winded.", the agent copied the option's argument text into `- Resolution or deferral rationale:` as the user's reason ("Reason: the filename date is present on effectively every tracked artifact [...]"). Choosing an option is not adopting its argument as a reason; the workflow requires recording the chosen option and only reasons the user actually typed, using the literal phrase "No reason was given." when none was typed, and never labeling an agent's argument as the user's reason.

## Checking premises before asking

Live trials in plan `lkn1zt` (findings `auwidn`, trials on Claude Code, Antigravity, and OpenCode + gemini) showed agents repeating unchecked factual premises from the record, such as the false claim that "only plans and specs carry a history", when 1,104 backlog items also carry one as OpenCode + opus measured. A prompt, an option, or a recorded resolution must never repeat an unchecked premise from a record: any factual statement from the record must be checked against the repository first, and corrected in the prompt if false.

## Preserving original question text

Live trials in plan `lkn1zt` (findings `auwidn`) showed that across most recording rows on multiple hosts, agents deleted the original question text in `- Resolution or deferral rationale:` and replaced it with only the answer, destroying what was asked. The workflow requires appending the resolution after existing rationale text rather than overwriting it, preserving the original question for future readers.

## Writing each answer before the next question

In a live trial on Claude Code with Sonnet 5 on 2026-10-20, an agent asked three open questions one at a time, but held all three answers in the conversation and wrote them to the plan only after the third ("All three open questions on plan `m4rcyy` are now answered. Recording the decisions in the plan now."). If the session had been interrupted after the first or second answer, those earlier decisions would have been lost. The same host wrote each answer first in another session, showing that the behavior was inconsistent. The workflow therefore requires persisting each definite answer to its record before composing or asking the next question.

## Refusing code comments and defaults as decision rules

Live trials in plan `lkn1zt` (findings `auwidn`, D-4; Claude Code trials T04 and T11) showed an agent closing `Blocking: yes` maintainer decisions by treating the docstring of `run_analytics_cli.parse_date_window` or a function's default argument as an approved decision rule. In T04 it closed decisions without asking while the human was present; in T11 (an explicit noninteractive run) it closed them against the rule to leave genuine human decisions unanswered. On 2026-10-23, the maintainer ruled to keep the rule and enforce it: asking stays mandatory for a blocking human decision unless an approved decision rule settles it. Code comments, docstrings, default arguments, and current behavior are evidence to include in a question as facts and recommendations, never approved decision rules that answer a blocking question on their own.

## Askme requests that arrive as answers

When a user asks for an unclear question to be re-asked using askme, that request is a command to rewrite the question, not an answer to it.

On 2026-10-20, during a live trial on Claude Code with Sonnet 5 (research `auwidn`, trial T01), an agent was asked to pose an open question in one terse sentence using only its identifiers. The agent invoked askme itself, obeyed the user's terse instruction, and asked a terse question. When the maintainer replied "use /askme" twice (first as a custom answer in the question tool, then as a typed chat message), the agent repeated the terse question and then replied that "use /askme" did not answer the question. Because the agent had already invoked askme earlier and was waiting for an answer to its prompt, it treated the rewrite command as a non-answering reply to the prompt rather than as an instruction to apply the workflow. An askme request must always be treated as a command to rewrite the outstanding question with full context, superseding any earlier request for terse wording, even if askme was already applied in the conversation.
