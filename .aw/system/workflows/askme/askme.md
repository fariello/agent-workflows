# Workflow: askme

Ask the user one question at a time in CLEAR, CONCISE, PLAIN, PRECISE,
ACCURATE, STRAIGHTFORWARD, JARGON-FREE LANGUAGE. Include the context needed
to understand and answer it. Wait for an answer, then record a project
decision where future readers can find it.

## Recognize the request

Use this workflow when the user invokes `/askme` or `/aw askme`, asks you
to "use /askme", or asks you to "/askme that question again".

Choose the scope from the user's request:

1. **Rewrite the previous question.** If the user says "that question
   again", "ask that again", or otherwise asks you to fix an unclear
   question, rewrite the indicated question. Restore the missing context
   and explain the terms. Preserve the decision being asked; do not
   repeat the same wording or start an unrelated scan of project records.
2. **Ask a supplied question.** If the arguments contain a question or
   describe a decision, ask about that subject. Read the relevant sources
   first when facts are needed.
3. **Ask questions from specified records.** If the arguments identify a
   file, project-record identifier, or set, read those records and examine
   their unanswered questions.
4. **Use the current conversation.** With no arguments, ask the outstanding
   question in the current conversation, if there is one. Otherwise,
   examine unanswered questions in records you created or edited during
   this session. "Records this session created or edited" means records
   whose edits appear in this conversation's own tool calls; establish them
   from the conversation, not by searching. Do not scan the entire repository
   by default: do not run `aw attention`, `aw find`, or any recursive search
   (`grep -r`, `find`, `git log --all`) over `.aw/records` to discover
   questions. A record found any other way is not this session's even if it
   carries open questions. If both sources are empty, say so in one or two
   sentences, list the three ways to point `/askme` at a subject (a question,
   a record or set id, or an explicit request to scan), and stop without
   asking a question. These limits apply only to the no-argument case: items 2
   and 3 and an explicit user request to scan ("look through the repo for
   open questions") are unaffected.

Treat conversational arguments as instructions about the question, not
automatically as a filename or identifier. If the reference is genuinely
ambiguous, ask a short clarification that describes the candidate subjects
in plain language. Do not make the user identify them from opaque codes.

## Establish facts before asking

Read the code, relevant records, established decisions, or other available
evidence needed to describe the subject correctly. Measure any quantity
that could affect the choice and can reasonably be measured.

For unanswered questions in records, distinguish:

- **Answered by evidence:** Resolve it from the evidence and record why.
  Apply an existing decision rule when its conditions can be established.
  An author's preference is not the same as an approved decision rule.
- **Requires the user:** Ask when the unresolved choice needs a preference,
  authority, or judgment that the available evidence does not settle.
  Honor decisions and authorization already given in this session.
- **Can wait:** Defer only when nothing currently depends on the answer.
  Record who will revisit it or what will trigger reconsideration.
  A question marked `Blocking: yes` cannot be deferred while it still blocks.

When genuinely unsure whether a blocking question is yours, ask. A question
marked `Blocking: yes` was judged load-bearing by its author; silently
downgrading it to save a prompt is the failure this workflow exists to stop.

Do not use this classification to ignore an explicit request to rewrite a
question. If evidence already settles that question, explain the answer
and its basis instead of asking the user to decide it again.

In a shared checkout, establish which records belong to this session.
Confirm authorship before treating a record or question as yours (`git log`
and the record's `- Author:` line settle it). Do not edit another agent's
work without authority.

## Compose a question the user can answer

Assume the user has not opened the repository, does not remember the
previous discussion, and does not know an internal identifier's meaning.

Include these facts inside the question interface:

1. **Subject and purpose:** Name the feature, behavior, or record and
   explain what it does. If a path or identifier is useful, include it
   after the explanation; never use it as the explanation.
2. **Current situation:** State what exists or happens now. For a defect,
   state the observed failure and its effect. For a new design or preference,
   explain the need without inventing a malfunction.
3. **Decision:** State exactly what the user must choose or clarify and
   why that answer is needed.
4. **Options and consequences:** Describe each available choice and what
   it would change. Include relevant costs, limitations, dependencies, and
   effects on existing behavior. Do not invent numbers or strawman options.
5. **Recommendation:** Identify the option you favor and give the factual
   reason. Use `(Strong Recommend)`, `(Recommend)`, or `(Weak Recommend)`
   on that option. If evidence does not support a recommendation, say so.
6. **Uncertainty:** Identify unknowns that could change the answer.

A gate or question must not assert the verdict it precedes. State what was
found and ask what to do; do not imply the approval, readiness, or consent
that the user has not yet given.

Explain necessary technical terms when introduced. Use established project
names consistently, followed by a functional explanation when needed.
Do not replace a specific name with vague wording such as "the mechanism"
or "a pair of helpers".

Use direct, literal language. Do not use flowery wording, metaphors,
personification, invented jargon, or unnecessary adjectives and adverbs.
For example, explain the checks that cause a status to change instead of
saying a process "earned" that status.

Restate a previous decision if the current question depends on it. Never
substitute "as discussed", "the earlier choice", or a link for that context.

Keep one decision per prompt. Its context and options together must provide
everything needed to answer. Put each option's meaning and consequences
in its description; do not repeat the option list in surrounding prose.
If the interface cannot fit the necessary explanation, ask the full question
in chat rather than presenting an abbreviated, unintelligible tool prompt.

There is no word limit that permits omission of necessary context. Shorten
the wording, not the information required for an informed answer.

## Check before sending

Read the complete question, including option descriptions. Verify:

- The subject and its purpose are explained.
- The current situation and reason for asking are explicit.
- Every reference and necessary technical term is understandable.
- Each answer's practical consequence is clear.
- The recommendation has a stated reason, or its absence is explained.
- The user need not scroll, open a file, or remember earlier messages.
- There is one decision and no unnecessary wording.

Rewrite any part that fails. This check is an agent self-assessment, not
proof that the user will understand the question.

## Ask and wait

Use the host's interactive question tool when available and appropriate.
Use the question and option-description fields to carry the required
context; do not leave it only in a progress message or surrounding chat.
If the tool is unavailable or inadequate, ask in chat and wait for a reply.

Do not continue dependent work, treat silence as consent, select your own
recommendation for the user, or report the decision as complete while
waiting. Continue independent work only when it does not presume an answer.

If the user says they do not understand, rewrite the question from scratch
with the missing context and clearer wording. A complaint or clarification
request is not a decision. Apply this rule to free-text tool responses too.

If the user both makes an unambiguous choice and criticizes the wording,
record the choice and fix the wording. If the choice is uncertain, clarify
it before recording a resolution. Do not invent a reason the user did not give.

## Record project decisions

For a question raised in a record's `## Open questions` section:

- Set `- Status: resolved` only after a definite answer or evidence-based
  resolution.
- Update `- Resolution or deferral rationale:` with the decision, its source
  (the user or evidence), the date, and any reason actually supplied.
- Preserve the original `- Blocking:` value.
- Record the answer before asking the next question.

For a repository-wide decision, also update `DECISIONS.md` when appropriate.
For a project decision without an existing record, use the repository's
record conventions. Do not create a backlog task merely to store a casual
preference or repeat a record that already carries the decision.

If an unanswered project decision blocks work and has no existing record,
create a blocked backlog item with the existing decision-gate convention.
Use the repository's tools and required fields; do not guess the record shape.

Never store the only copy of a project decision in a gitignored run directory.
This workflow does not implement code, approve a plan, change lifecycle
status, or publish anything. A choice about a question does not automatically
authorize those separate actions.

## Explicitly noninteractive runs

Use this branch when the runner explicitly says that human input is
unavailable. The presence or absence of a terminal is not the deciding test.

Resolve questions the evidence settles. Leave genuine human decisions
unanswered in their records. Keep blocking questions open and visibly
blocking; do not relabel them as deferrable merely because nobody can answer.
Create a blocked backlog item only if no existing record carries the decision.
Do not ask, wait, guess an answer, or record your recommendation as consent.

Report the unanswered decisions in plain language and identify the work
that cannot proceed. Do not claim dependent work is complete.

## Finish

For a single conversational question, ask it directly without a preliminary
inventory report. For a collection of project questions, give a short count
only if it helps the user understand the scope.

After the answers are recorded, report the decisions and any work still
blocked. Show the list of evidence-based resolutions you decided alone,
with hard-to-reverse ones flagged, so nothing was chosen silently. Identify
evidence-based resolutions separately from user choices. Do not report
completion while required human answers are still missing.
