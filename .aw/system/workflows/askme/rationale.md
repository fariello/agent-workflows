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
