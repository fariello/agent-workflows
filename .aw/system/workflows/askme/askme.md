# Workflow: askme (ask the human the open decisions, then record the answers)

Ask the human every question that is genuinely theirs to answer, ONE PROMPT AT A TIME, through the
interactive question tool, in plain English with enough context to decide from the prompt alone. Then
record each answer durably in the artifact that raised the question.

THE COMPOSITION RULES LIVE IN `GUIDING_PRINCIPLES.md` PRINCIPLE 12 AND ARE NOT RESTATED HERE. Read P12
before composing anything. This workflow adds only the parts P12 does not cover: how to decide WHICH
questions are the human's, where the answer goes so it survives the session, and what to do when there
is nobody to ask. If you find yourself wanting to restate P12's composition guidance in this file,
don't; reference it (GUIDING_PRINCIPLES P8, single source of truth).

WHY THIS EXISTS, stated plainly because it is a correction and not a feature. P12 and the `AGENTS.md`
pointer already require self-contained interactive questions, both are in an agent's loaded context,
and agents STILL finish work with the human's questions unasked, or ask them as a wall of chat prose
carrying repository jargon the human has no context for. Measured 2026-09-08: an agent authored five
plans containing eleven open questions, asked the maintainer none of them, and reported completion; in
the same session it referred to `run_engine.RunEngine`, `IPD-S404` and bare id6 handles in a question
addressed to a human who had never seen them. A rule an agent reads and still breaks needs an
invocable entry point and a gate, not a third copy of the prose.

## What it does and does not do

- Produces: one interactive prompt per decision, and a recorded answer in the OWNING artifact's
  `## Open questions` block (`- Status: resolved` plus a `- Resolution or deferral rationale:` that
  states what was decided and why).
- Produces, for questions with no owning artifact: a `blocked` backlog item carrying a typed
  `- Gate-Kind: decision` gate, so an unanswered decision stays visible to `aw attention` instead of
  evaporating with the session.
- Does NOT decide anything the repository can answer. Resolving a question from evidence is the
  DEFAULT (see Step 2); asking is the exception reserved for what only the human can settle.
- Does NOT change code, approve anything, or move an artifact through its lifecycle.
- Does NOT ask about work in flight that is not yours. In a shared checkout, another agent's plan is
  not your question to ask.

## Memory kernel (carry these to the end of the run)

1. ONE QUESTION PER PROMPT. Not two, not a set. A human answering a stack of coupled questions cannot
   answer any of them well, and the answer to the second usually depends on the first.
2. FULL CONTEXT INSIDE THE PROMPT. The human may not have read the file, may not know the id6, and may
   not remember the earlier conversation. Never say "as discussed above", never make them scroll.
3. NO JARGON. No id6 handles as nouns, no symbol names, no finding codes, no internal vocabulary. Name
   the THING and what it does. `xipfy1` is not a subject; "the plan that spends the retry budget" is.
4. LABEL YOUR RECOMMENDATION with exactly one of `(Strong Recommend)`, `(Recommend)`, or
   `(Weak Recommend)`, on the option you favor. If you have no view, say so in the context and label
   nothing. An unlabeled option set makes the human do work you already did.
5. EVERY OPTION IS A REAL CHOICE, with its actual cost stated. An option you have already ruled out is
   not an option; delete it. Padding a prompt with a strawman wastes the human's only scarce resource.
6. NEVER REFER TO A PRIOR ANSWER INSTEAD OF RESTATING IT. If a follow-up depends on an earlier
   decision, restate the decision in the new prompt. Measured 2026-09-08: a follow-up prompt said
   "the automatic block" referring to a previous answer, and the maintainer replied "What automatic
   check? I have zero context here." That is this workflow's own failure mode.
7. MEASURE BEFORE YOU ASK, WHEN THE ANSWER IS MEASURABLE. If the human's choice depends on a number
   (how many files this breaks, how many plans this fails), get the number FIRST and put it in the
   prompt. A prompt that asks the human to guess at a fact you could have counted is a wasted prompt.
8. ASK BEFORE YOU REPORT, NOT AFTER. A question raised in a final report is a question that did not get
   asked. Wait for the answer.
9. A GATE OR QUESTION MUST NOT ASSERT THE VERDICT IT PRECEDES. State what was found and ask what to do;
   do not imply the approval, readiness, or GO that the human has not yet given.

## Inputs

`$ARGUMENTS` may name the artifact whose questions to ask about (a path, an id6, or a set id). Omit it
to scan the work of the current session.

## Step 0: Discover

Establish, without guessing:

- WHICH ARTIFACTS ARE IN SCOPE. From `$ARGUMENTS` if given. Otherwise the artifacts you created or
  edited in this session. In a shared checkout, confirm authorship before treating a question as
  yours: `git log` and the artifact's own `- Author:` line settle it.
- WHETHER THERE IS A HUMAN TO ASK. An interactive question tool plus a real terminal means yes. A
  runner turn means NO, and the drivers say so explicitly in the prompt they hand you ("this run is
  non-interactive: do not invoke an interactive question tool or wait for human input"). Under a
  runner, go to Step 5.
- WHAT THE QUESTIONS ACTUALLY ARE. Read each artifact's `## Open questions` section. Each block is
  `### OQ-NN: <question>` with `- Blocking:` (`yes`/`no`), `- Status:` (`open`/`resolved`/`deferred`),
  `- Owner:`, and `- Resolution or deferral rationale:`.

Report the inventory before asking anything: how many questions, how many marked blocking, and which
you intend to resolve yourself versus ask about.

## Step 1: Separate the human's questions from your own

Sort every open question into exactly one of three piles. Getting this wrong in either direction is
the main way this workflow fails.

- YOURS TO RESOLVE. The repository can answer it: the code, the tests, the git history, an approved
  spec, or a prior decision settles it. Resolve these yourself (Step 2). Most questions are here.
- THE HUMAN'S TO DECIDE. Scope, priority, risk appetite, cost, a public contract, a product
  behavior, anything irreversible, anything where the repository has no opinion and two reasonable
  people would choose differently. Ask these (Step 3).
- GENUINELY DEFERRABLE. Not needed now, and nothing is blocked by waiting. Record the deferral with an
  owner or a trigger; do not spend a prompt on it. Note the grammar forbids a `Blocking: yes` question
  from being `deferred`, which is deliberate: if it truly blocks, it cannot wait.

WHEN IN DOUBT ABOUT A BLOCKING QUESTION, ASK. A question its own author marked `Blocking: yes` is a
question someone judged load-bearing; silently downgrading it to save a prompt is the failure this
workflow exists to stop.

## Step 2: Resolve what you can, and show your work

For each question in the first pile: resolve it from evidence, and record the reasoning in the
artifact (`- Status: resolved`, and a rationale naming the evidence). Then, after the interactive
round, SHOW THE HUMAN THE LIST of what you decided alone, in one or two lines each, so nothing was
chosen silently. Flag anything hard to reverse.

Do not ask the human to ratify a decision the repository already made. Do not present a resolved
question as open in order to look thorough.

## Step 3: Ask, one prompt at a time

Compose per `GUIDING_PRINCIPLES.md` P12 and the memory kernel above. Then, for each question:

1. Ask it through the interactive question tool, alone.
2. WAIT for the answer. A delayed reply is not a non-interactive session.
3. Record the answer (Step 4) before asking the next question, so an interrupted session does not lose
   what the human already told you.

If the tool is unavailable but a human is present, ask in chat with the same content and say plainly
that the interactive tool was unavailable.

STOP AND RE-ASK IF THE ANSWER SHOWS THE QUESTION FAILED. "I have zero context here", "what is X?", or
a request for the meaning of a term means the prompt was defective, not the human. Re-ask with the
missing context supplied. Do not proceed on a guess about what they meant.

## Step 4: Record every answer durably

The answer goes in the artifact that RAISED the question, because that is where the next reader and
the next agent will look, and where the existing approval gate reads it:

- Set `- Status: resolved`.
- Write `- Resolution or deferral rationale:` stating WHAT was decided, that the HUMAN decided it, the
  date, and the reason they gave. A rationale that records only the outcome loses the reasoning, which
  is the part that is expensive to reconstruct.
- Leave `- Blocking:` as it was. It records what the question WAS, not how it ended.

For a question with no owning artifact, file a backlog item with `--status blocked --gate-kind
decision`, and close it when answered. For a decision that shapes the repository beyond one artifact,
also add an entry to `DECISIONS.md`.

Never record an answer ONLY in a run directory under `.aw/records/runs/`: that tree is gitignored and
per-machine, so the answer would not survive.

## Step 5: When there is no human (a runner turn)

Do not block, do not prompt, do not wait. Instead:

- Resolve what the repository can answer, and record it with its evidence.
- For each genuine human decision, record it as an unanswered question in the artifact and, if nothing
  else carries it, as a `blocked` backlog item with a `decision` gate so `aw attention` surfaces it.
- Say so in the turn's report, naming each deferred decision.

A blocking question that reaches a runner unasked is a planning failure upstream, not something to
resolve by guessing under automation.

## Output

- Every asked question answered and recorded in its owning artifact.
- A short list of what you resolved yourself, hard-to-reverse items flagged.
- For anything unasked: a durable record that survives the session.

## Exit gate (satisfy every item before reporting done)

- [ ] Every open question in scope is sorted into resolved-by-me, asked-and-answered, or recorded as
      deferred with an owner or trigger. Nothing was silently dropped.
- [ ] Every question the human answered is recorded in its owning artifact with `Status: resolved` and
      a rationale naming the human, the date, and their reason.
- [ ] Each prompt asked exactly ONE question and carried its own context, with no reference to an
      earlier answer or message.
- [ ] No prompt used an id6 handle, a symbol name, or a finding code as its subject.
- [ ] Every option set had a recommendation label, or the prompt said there was no recommendation.
- [ ] Where the human's choice depended on a number, the number was measured and included.
- [ ] The list of self-resolved decisions was shown to the human.
- [ ] No answer lives only in a gitignored run directory.
- [ ] No artifact belonging to another agent was edited.

## Reminders

- The interactive tool renders the choices. Do not also list them in the context prose (P12).
- One question per prompt beats a well-organized set of five.
- Asking a question the repository answers is as much a failure as not asking one it cannot.
