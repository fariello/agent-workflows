- Id: n2lr3g
- Status: open
- Blocks-Release: next
- Set: askmerequired
- Priority: high
- Work-Kind: bug
- Summary: Make /askme mandatory for substantive human questions and decisions

## Workflow history
- 2026-10-26 created (aw backlog): Make /askme mandatory for substantive human questions and decisions

## Problem

During the 2026-10-26 metadata-store spec review, the agent asked two design questions without enough background, definitions, examples or consequences for the maintainer to decide. The maintainer had to request /askme explicitly. Existing instructions already require self-contained questions, but the installed workflow pointer triggers /askme only on an explicit request. Review workflows repeat shorter questioning procedures instead of requiring the shared workflow. This is an observed instruction-following failure and a workflow integration gap; the underlying model cause is unknown.

## Required change

Make /askme the mandatory shared procedure whenever an agent asks the human a substantive project question or requests a decision, clarification or approval. The user must not have to invoke it. Preserve explicit user instructions and existing authorization; this requirement must not introduce unnecessary permission questions.

Update the source of the installed agent instructions in agent_workflows/engine.py, not only this repository's generated AGENTS.md. Route spec-review, plan-review and other workflows that ask project questions through .aw/system/workflows/askme/askme.md. Replace conflicting or duplicate question-composition procedures with references to that authority. Retain workflow-specific decision ownership and recording rules.

The procedure must explain the subject and purpose, current behavior, decision needed, options and consequences, recommendation strength and reason, and relevant uncertainty inside the displayed question. Explain necessary terms and use a concrete example when the distinction is otherwise hard to understand. Ask one decision at a time, wait, and record each answer before asking the next. A request for explanation is not a decision.

## Evidence

- AGENTS.md, Ask self-contained questions: context and options must be inside the prompt; brevity cannot remove necessary context.
- agent_workflows/engine.py, agents_pointer_prose: the installed /askme trigger currently names explicit user invocations.
- .aw/system/workflows/askme/askme.md, Compose a question the user can answer and Check before sending: the complete shared procedure already exists.
- .aw/system/workflows/spec-review/spec-review.md, Step 3.2, and .aw/system/workflows/plan-review/steps/s5-questions.md, 3.2: separate instructions permit one to three questions per prompt instead of requiring /askme.
- Maintainer instruction in this session: create a backlog item to make /askme mandatory. This authorizes backlog creation, not implementation.

## Acceptance evidence

Exercise actual agent conversations on supported hosts. Cover an initial project decision without an explicit /askme request, an explanation request, an unclear-question complaint, a plain-text /askme invocation, and multiple pending decisions. Inspect the rendered prompts for sufficient context and meaningful option consequences; verify that the agent does not infer consent and records each definite answer before the next question. Include a case already authorized by the user to catch unnecessary confirmation requests.

Exercise installation or update in a temporary target repository to verify the mandatory procedure is available there. Preserve target-neutral instructions. Capture actual behavior and outputs; do not substitute source-text assertions or checks that instruction phrases exist for evidence that the agent follows them.

## Scope limits

Do not implement metadata-store schema changes as part of this item. Do not promise that stronger instructions guarantee model compliance. Report observed failures and remaining limits from the conversation trials.
