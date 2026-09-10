# Workflow: askme (ask the human the open decisions, then record the answers)

Ask the human every question that is genuinely theirs to answer, ONE PROMPT AT A TIME, through the
interactive question tool, in plain English with enough context to decide from the prompt alone. Then
record each answer durably in the artifact that raised the question.

The canonical composition rule is `GUIDING_PRINCIPLES.md` P12 (ask self-contained questions), which this
workflow references rather than restates (GUIDING_PRINCIPLES P8, single source of truth). This workflow
adds what P12 does not cover: how to decide WHICH questions are the human's, how to compose one the
reader can actually act on, where the answer goes so it survives the session, and what to do when there
is nobody to ask.

THERE IS DELIBERATELY NO INSTRUCTION HERE TO GO AND RE-READ P12 FIRST, and its removal is a measured
correction rather than an oversight. That instruction used to open this file; on 2026-09-08 it was
obeyed, and the prompt composed immediately afterwards was one the maintainer could not read at all.
Re-reading the principle prevented nothing, because what the run needed was not in it, and the ritual
manufactured false confidence ("I read P12, so my prompt is fine") of exactly the kind this workflow's
own existence disproves. The guidance you actually need at composition time is in the memory kernel
below, which now carries P12's pre-flight self-check list.

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
3. STATE THE SYMPTOM BEFORE THE CHOICE. Say WHAT IS GOING WRONG, or what will go wrong if nothing is
   decided, BEFORE you name a single option, in terms an operator would recognize from actually using
   the tool. "A run reports that it finished successfully when its work never landed" is a symptom. "A
   pending fix needs to give an item one bounded second attempt" is a remedy, and a remedy stated alone
   leaves the options with nothing to be weighed against.
   THE ORDER IS PART OF THE RULE, not a stylistic preference: SYMPTOM, then CHOICE, then the CONSEQUENCE
   of each option. A prompt that mentions the symptom only after the options has already lost the reader.
   IF YOU CANNOT STATE THE SYMPTOM, YOU DO NOT YET UNDERSTAND THE DECISION WELL ENOUGH TO ASK ABOUT IT.
   Go back and find out what breaks. Measured twice on 2026-09-08 and once on 2026-09-09: a prompt
   opened inside a mechanism and never mentioned the malfunction, and the maintainer could not read it;
   a later prompt in the same session referred to "the change I am about to plan" without ever saying
   what the change was, and the reply was "I have 12 opencode sessions, I don't remember what this one
   is about". Both were this rule missing.
4. NO JARGON, AND NO PLACEHOLDER IN ITS PLACE. No id6 handles as nouns, no symbol names, no finding
   codes, no internal vocabulary. Name the THING and what it does. `xipfy1` is not a subject; "the plan
   that spends the retry budget" is.
   THE POSITIVE HALF IS THE HALF THAT MATTERS, because this rule is otherwise satisfiable by DELETING
   NOUNS. When you drop an internal name, replace it with what the thing DOES in the reader's terms.
   "The retry code built for another part of the system" is compliance. "A shipped pair of helpers" is
   not: it is the same sentence with the handle removed and nothing put back.
   A GENERIC CONTAINER WORD IS A VIOLATION, NOT COMPLIANCE. If the head of your noun phrase is `a pair
   of helpers`, `a module`, `a mechanism`, `a component`, `a system`, or any other word that would fit
   equally well in front of any code in the repository, you have removed the handle and left a void. A
   named thing can at least be looked up; an anonymous thing cannot even be pictured, so the
   substitution made the prompt WORSE than the jargon it replaced. Measured 2026-09-08: a prompt that
   satisfied this rule by substitution produced "a shipped pair of helpers" and "a 900-line run-state
   model", passed every exit-gate item, and left the maintainer unable to read it.
   IF A THING CANNOT BE DESCRIBED FUNCTIONALLY, NAME IT AND EXPLAIN IT IN ONE CLAUSE. That is the
   honest escape and it is permitted, because without it this rule sometimes has no compliant option,
   which is how the void gets produced. "The lint check that refuses a plan whose questions are
   unanswered (`check_open_questions`)" is fine. A named-and-explained thing is decidable; an anonymous
   one is not.
5. LABEL YOUR RECOMMENDATION with exactly one of `(Strong Recommend)`, `(Recommend)`, or
   `(Weak Recommend)`, on the option you favor. If you have no view, say so in the context and label
   nothing. An unlabeled option set makes the human do work you already did.
6. EVERY OPTION IS A REAL CHOICE, with its actual cost stated. An option you have already ruled out is
   not an option; delete it. Padding a prompt with a strawman wastes the human's only scarce resource.
7. NEVER REFER TO A PRIOR ANSWER INSTEAD OF RESTATING IT. If a follow-up depends on an earlier
   decision, restate the decision in the new prompt. Measured 2026-09-08: a follow-up prompt said
   "the automatic block" referring to a previous answer, and the maintainer replied "What automatic
   check? I have zero context here." That is this workflow's own failure mode.
8. MEASURE BEFORE YOU ASK, WHEN THE ANSWER IS MEASURABLE. If the human's choice depends on a number
   (how many files this breaks, how many plans this fails), get the number FIRST and put it in the
   prompt. A prompt that asks the human to guess at a fact you could have counted is a wasted prompt.
9. ASK BEFORE YOU REPORT, NOT AFTER. A question raised in a final report is a question that did not get
   asked. Wait for the answer.
10. A GATE OR QUESTION MUST NOT ASSERT THE VERDICT IT PRECEDES. State what was found and ask what to do;
   do not imply the approval, readiness, or GO that the human has not yet given.

PRE-FLIGHT SELF-CHECK, silently, before you send any prompt. This list moved here from
`GUIDING_PRINCIPLES.md` P12 on 2026-09-09 because it belongs where composition actually happens, and it
lives in exactly one place (P8):

- Can the user answer without reopening other material?
- Is every included fact necessary?
- Is the reason for asking clear?
- Have I avoided repeating the tool's choices?

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
  TEST WHETHER THE OWNING ARTIFACT ALREADY STATES A DECISION RULE, and do it FIRST, because this is
  the cheapest way to avoid the worst outcome. A question whose own artifact says "do X if measurement
  M, else Y and record it" is YOURS the moment M is measured. Measure M and apply the rule. Do not hand
  a human back a rule they already wrote. The corollary is what makes this actionable: if the artifact
  states a rule and you have NOT measured M, your work is to MEASURE, not to ask.
  Measured 2026-09-08, and it is why this test exists: a prompt was composed asking the maintainer to
  choose between reusing existing retry code and bounding a retry directly, when the plan's own open
  question already said to prefer reuse if the adaptation was small and otherwise to bound it directly
  and record the divergence, and the deciding measurement had already been taken. The question was
  answered before it was asked.
  THE TEST FIRES ONLY ON A RULE THAT IS DECIDABLE ONCE MEASURED. An artifact expressing a lean, a
  preference, or an author's hunch has NOT decided anything, and treating it as a decision is the
  opposite failure. When the artifact states a genuine rule but applying it needs a judgment call the
  repository cannot make, the question is still the human's. If that leaves you genuinely unsure on a
  question marked blocking, the tiebreak below settles it: ASK.
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

DISCARD AND RE-ASK IF THE ANSWER REPORTS INCOMPREHENSION. "I have zero context here", "what is X?", "I
did not understand a single word of that", or a request for the meaning of a term means THE PROMPT WAS
DEFECTIVE. The defect is that the prompt failed to supply what the reader needed, not that the reader
lacked context. Re-ask with the whole context restated from scratch, and do not proceed on a guess about
what they meant.

THIS APPLIES ON EVERY CHANNEL, INCLUDING THE TOOL'S FREE-TEXT OPTION, and that is the case most likely
to be missed. A human who cannot understand a prompt often has no listed option that fits, so they reach
for "write your own answer" to say so. Measured 2026-09-08: the maintainer did exactly that, replying "I
wanted to pick write your own and say I did not understand a single word of your explanation." A
free-text answer reporting incomprehension is a defective prompt, not a decision.

A DISCARDED ANSWER IS NEVER RECORDED AS A RESOLUTION. Do not write it into the artifact, do not name the
human as having decided it, and do not carry it forward as their preference. The harm is specific and
worth naming: Step 4 would otherwise produce a rationale claiming the human decided something they had
just said they could not understand, and a later reader has no way to tell that apart from consent.

DISTINGUISH AN ANSWER-PLUS-COMPLAINT FROM A NON-ANSWER, since they look similar and are opposites. A
human who picks an option and separately objects to the prompt's length, tone, or framing HAS answered:
record the decision, and fix the prompt next time. A human who reports not understanding has NOT
answered, and there is nothing to record.

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

THE FIRST ITEM IS THE ONE THAT MATTERS AND THE ONLY ONE THAT IS NOT MECHANICAL. Every other item here
can be decided by looking (did you use a handle? did you label a recommendation?), and that is exactly
why this gate once passed a prompt the maintainer could not read: comprehensibility is not decidable by
looking, so a gate made only of mechanical checks cannot gate it. Do this one honestly or the rest are
decoration.

READ IT BACK AS A STRANGER, WITH ITS LIMIT STATED PLAINLY: this is a SELF-ASSESSMENT by the agent that
composed the prompt, so it can be ticked without being performed and it is NOT proof that the prompt is
comprehensible. The only real evidence is the human's reply, which arrives after this gate. It is here
because it changes what a conscientious agent does at composition time, which is the population that
produced the measured failure: that prompt was written by an agent following the rules, not evading them.

- [ ] Re-read the composed prompt as a reader who has NEVER OPENED THIS REPOSITORY, and name out loud,
      in your own words, three things: the PROBLEM, the CHOICE, and the CONSEQUENCE of each option. It
      FAILS if the prompt names no symptom (only a remedy), if you cannot state one of the three without
      going back to the artifact, or if any noun in it is a placeholder the reader cannot picture (`a
      pair of helpers`, `a module`, `a mechanism`). If it fails, rewrite it before asking; do not ask and
      hope.
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
