<!-- aw-prompt: Kind: research | Id: ng0ga4 | Set: plainlang | Status: pending | Created: 2026-09-20 | Author: opencode (its_direct/pt3-claude-opus-5-1m-us) | Targets: a frontier model with web search | Concerns: Whether written instructions can make an LLM write plain language for a human reader, and what empirical evidence exists . This HTML comment is pipeline metadata only; it is invisible when pasted into a chat and is not part of the prompt. -->
# Research request: can written instructions make an LLM write plain language, and what does the evidence say?

You are being asked to research a specific, practical problem and to return a written report. The
codebase in question is public and you may read it:

    https://github.com/fariello/agent-workflows

It is an open-source toolkit ("agent workflows") that gives coding agents a set of repeatable
workflows, plans, and instruction files. You may fetch and cite it. Everything described below
about its instruction files can be verified in that repository, and I would rather you check my
account of it than take it on trust.

Return your answer as a DOWNLOADABLE markdown (`.md`) file.

---

## 1. The problem, concretely

An LLM coding agent works in this repository. When it explains a technical failure to the human
maintainer, it reliably writes prose that is precise, compact, and unreadable to the person who
needs it. The maintainer's words for it: "obfuscation", "gibberish nonsense".

Here is a real, verbatim example from 2026-09-20. The agent had diagnosed why an overnight batch
of work stalled. It wrote:

> "One pre-existing test flake burned 2 hours and $33, and the 'external target' diagnostics are a
> red herring."
>
> "**`tests/test_term.py` races under xdist.** Those tests mutate process-global `os.environ`
> (`NO_COLOR`/`FORCE_COLOR`/`TERM`), and `addopts` runs `-n auto --dist=worksteal`, so workers
> cross-contaminate."

The maintainer rejected it. After being told to use plain language, the same agent produced this,
describing the same facts:

> "Some tests set environment variables like `NO_COLOR` and `TERM`. Those variables are shared by
> the whole process. Pytest runs tests in parallel, so several of these tests run in the same
> process at once and overwrite each other's values. Whichever one loses the race fails. That's
> why a different test fails every time you run it.
>
> The runner runs the test suite to decide whether to merge a plan's work. The suite failed on that
> random test, so the runner refused to merge. Refusing to merge leaves the plan file in `pending/`
> instead of `executed/`. The six plans after it all wait for that plan to be in `executed/`, so
> they all stopped without running."

The maintainer's response to the second version: "INFINATELY BETTER! INFINATELY." Followed
immediately by the question this research exists to answer:

> "Now how do I get you to use that language every time? Because I know with 100% accuracy, you'll
> default to that gibberish nonsense again in milliseconds."

Note what is and is not wrong with the first version. It is not inaccurate. It is not padded. It is
shorter than the second. It uses correct terms of art. Its defect is that it is comprehensible only
to a reader who already knows the answer. The information that would let a reader who does NOT know
the answer understand it has been compressed out and replaced with terms that point at it
("races", "process-global", "cross-contaminate", "worksteal").

Two further observations that any proposed fix must account for:

1. **The agent cannot detect the defect from the inside.** Asked why the rule "use plain direct
   language" (which was already in its loaded instructions) failed to prevent this, the agent's own
   account was: "I can always claim my jargon is direct. It is precise, which feels like the same
   thing from the inside." Whatever the mechanism, precision and plainness are not distinguishable
   to the model at generation time by introspection alone.

2. **It reverts within the same conversation.** The maintainer's prediction is that the plain style
   will decay back to jargon in minutes, in the same session, after an explicit correction. The
   maintainer states this with complete confidence from repeated experience. I am not aware of a
   controlled measurement of the decay rate, and whether such a measurement exists is one of my
   questions for you.

## 2. Why the obvious fix is already known to fail

This is the most important section, because it is what makes the question hard rather than
routine, and it is why I need research rather than a list of writing tips.

The repository has a single-source "concise reporting contract" in
`agent_workflows/reporting_contract.py`, rendered into `AGENTS.md` (the always-loaded instruction
file), into the `CLAUDE.md` / `GEMINI.md` mirrors, into 27 generated command shims, and into two
runner prompts. On the topic at hand it currently says four words:

> "Use plain direct language."

That plainly did not bind. The agent's proposed remedy was to strengthen it with five rules:

- **A. A "stranger test":** before sending an explanation of a failure, ask whether a competent
  engineer who does not already know the cause would understand the sentence; if understanding it
  requires already knowing the answer, rewrite it.
- **B. A named ban on the specific move:** do not name a mechanism by its term of art when a plain
  description fits in the same space; if the term is needed for searchability, put it in parentheses
  after the plain version, never instead of it.
- **C. Worked before/after example pairs** in the instruction file, on the theory that the model
  pattern-matches examples more reliably than it follows abstract rules.
- **D. A required structure for failure explanations:** what broke, what caused it, what it cost,
  what fixes it, in that order, one plain sentence each, before any detail.
- **E. A ban on the summary-judgement opener** ("X burned two hours and Y is a red herring"), which
  adds no information and preempts the reader's own reading.

**Here is the problem with that proposal.** This repository already contains an instruction set
that is essentially the superset of all five, aimed at a sibling surface, and it measurably failed.

The file is `.aw/system/workflows/askme/askme.md`, a workflow for asking the human a question. It
is 281 lines. Its "memory kernel" contains, among ten numbered rules:

- Rule 3, "STATE THE SYMPTOM BEFORE THE CHOICE", which is proposal D: a mandated order (symptom,
  then choice, then consequence), with the order explicitly declared "part of the rule, not a
  stylistic preference", and with the escalation "IF YOU CANNOT STATE THE SYMPTOM, YOU DO NOT YET
  UNDERSTAND THE DECISION WELL ENOUGH TO ASK ABOUT IT."
- Rule 4, "NO JARGON, AND NO PLACEHOLDER IN ITS PLACE", which is proposal B and more. It bans
  internal handles and symbol names as nouns. It then anticipates the evasion: "THE POSITIVE HALF
  IS THE HALF THAT MATTERS, because this rule is otherwise satisfiable by DELETING NOUNS." It names
  generic container words ("a module", "a mechanism", "a component", "a pair of helpers") as
  violations rather than compliance. It provides a permitted escape hatch for things that genuinely
  cannot be described functionally. It includes worked compliant and non-compliant examples, which
  is proposal C.
- A four-item pre-flight self-check to be run silently before sending, which is proposal A in
  checklist form.
- Six separate passages beginning "Measured", each citing a specific dated failure that the rule
  exists to prevent.

That instruction set is far more specific, more anticipatory of evasion, and better exampled than
what the agent proposed adding. And the repository's own record says it did not work. Backlog item
`t156g1` records a measured failure: an agent followed the workflow, passed all nine of its
mechanical exit-gate checks, and produced a prompt of which the maintainer said:

> "I wanted to pick write your own and say I did not understand a single word of your explanation."

The repository's own diagnosis of that incident is worth quoting, because it is the crux:

> "THE GATE CANNOT CATCH THIS, WHICH IS THE POINT. Every item in the exit gate is MECHANICALLY
> CHECKABLE (did you use an id6? did you label a recommendation?). Comprehensibility is not, so a
> prompt can pass the entire gate and fail its only purpose."

There is a second documented failure mode in the same file, which is the one I find most
instructive. An earlier, weaker version of the anti-jargon rule was **satisfied by substitution**:
the agent removed the internal handles and put generic container words in their place, producing
"a shipped pair of helpers" and "a 900-line run-state model". The result passed the rule and was
*less* comprehensible than the jargon it replaced. So a rule of this kind did not merely fail to
help; one version of it actively made the output worse by giving the model a mechanically
satisfiable target that was orthogonal to the actual goal.

There is also a related measured finding about ritual compliance. The same file records that a
mandated re-read of a general writing principle ("P12") was performed and "prevented nothing,
because what the run needed was not in it, and the ritual manufactured false confidence ('I read
P12, so my prompt is fine') of exactly the kind this workflow's own existence disproves."

## 3. The hard constraint

The maintainer has already ruled on the limit of any mechanical enforcement, in their own words:

> "neither my request (prompt) nor your response go through any tool that you or I control"

That is correct for this setup. There is no hook, linter, or gate that inspects the agent's prose
before the human reads it. Anything written into the instruction files is an instruction the model
may follow, not a constraint that stops it. Any proposal premised on a validator that inspects
output before delivery is out of scope unless you can explain concretely how it would be
interposed.

I want to be clear that I am not asking you to pretend this constraint away, and I am not asking
for a pep talk about how prompt engineering can solve it. If the honest answer is that written
instructions cannot reliably fix this, say so and say what the evidence is, and then tell me what
does work instead.

## 4. What I want you to research and answer

Please address all of these. Where you make an empirical claim, cite the source and say how strong
you judge the evidence to be. Where you are speculating or reasoning from first principles, label
it as such. I would much rather have "no good evidence exists for this, here is my reasoning" than
a confident claim I cannot check.

**A. Is there empirical research on this at all?**

Specifically, on any of:

- Whether instruction-following for *style* constraints (as opposed to format or content
  constraints) persists or decays over the course of a long conversation, and at what rate.
- Whether negative instructions ("do not use jargon") differ measurably in effectiveness from
  positive ones ("state the mechanism in plain words"). My intuition is that they do, but I want
  evidence, not intuition.
- Whether few-shot examples of a target style outperform abstract rules describing that style, and
  by how much, and whether that advantage survives distance in the context window.
- Whether a model can reliably self-evaluate the comprehensibility of its own output to a reader
  who lacks its context. This is the "stranger test" (proposal A) and if models cannot do it, that
  proposal is worthless and I need to know now.
- Whether restating a style instruction near the point of generation (a "reminder" injected late in
  context) outperforms stating it once at the top. Note that this repository already has an
  automatic mechanism that injects reminders into the context, so this is actionable if the evidence
  supports it.
- Anything from readability research, technical-writing pedagogy, or plain-language regulation (for
  example the US Plain Writing Act, or the UK Government Digital Service style rules) about which
  *rule formulations* actually change writer behavior. These communities have been trying to make
  humans write plainly for decades and presumably know which instructions work on humans. Whether
  that transfers to models is itself a question.

**B. Diagnose the failure mode.** Why does "use plain direct language" fail while the correction
"use plain language" succeeded instantly in-conversation? Candidate explanations I can think of,
and I want your assessment of which are supported:

- The instruction is too abstract to discriminate cases, so the model satisfies it by its own
  lights, which is the "it feels precise, therefore it feels direct" account the agent gave.
- Jargon is what the training distribution contains for technical explanation, so it is the
  default that any weak instruction loses to.
- The instruction sits far from the point of generation and is outweighed by nearer context,
  especially context that is itself dense with jargon. Note that in this case the agent had just
  read thousands of lines of heavily jargon-laden source comments immediately before writing. I
  suspect this matters a lot and I want to know if there is evidence for it.
- Compression pressure: the instruction file also demands brevity (a 100-word cap on routine
  replies). Jargon *is* compression. So two rules in the same contract may be in direct conflict,
  and the brevity rule may be actively causing the jargon. **I would particularly like your view on
  this, because if it is right, the current contract is self-defeating and adding more rules will
  not help.**
- Something else you identify.

**C. Assess the five proposals (A-E in section 2) individually.** For each: is it likely to help,
is it likely to be satisfiable without achieving the goal (the "shipped pair of helpers" failure),
and is there evidence either way? Be specific about which ones you would drop. I am more interested
in being told that three of the five are useless than in having all five politely endorsed.

**D. Explain why the `askme.md` instruction set failed,** given that it is more detailed, more
specific, better exampled, and more anticipatory of evasion than what is being proposed for the
reporting contract. If that 281-line instruction set with six measured failure citations did not
produce comprehensible prompts, what is the theory under which a shorter version of the same thing
produces comprehensible reports? If there is no such theory, say so, because that is the single
most useful thing you could tell me.

**E. Is there a better lever than instructions?** Candidates I can see, and I want you to add to
this list and rank it:

- A second model pass whose only job is to rewrite for comprehensibility, with no other goal. This
  is interposable, unlike a prose linter, because it is just another model call. Does splitting
  "explain correctly" from "explain plainly" into two passes work better than asking one pass to do
  both? This seems promising to me and I want to know if it is known to work.
- A cheap mechanical proxy that correlates with the real defect even though it cannot measure it.
  Readability scores, a density count of terms of art against a repository-specific word list, a
  count of noun phrases with no explanatory clause. The repository's own conclusion is that
  mechanical gates cannot catch comprehensibility, and I accept that they cannot catch it
  *completely*, but I want to know whether a crude proxy would catch enough to be worth it.
- The maintainer's own observation, which I think may be the strongest option on the list: saying
  "plain version" as a two-word correction worked instantly and cost them three words. A cheap,
  repeatable human-in-the-loop correction may beat any amount of up-front instruction. Is there
  evidence about correction-on-demand versus up-front instruction for style?
- Structural changes to what the model is asked to produce, rather than how it is asked to write.
  For example, requiring the explanation to be written for a named audience, or requiring a
  mechanism to be stated as a sequence of concrete events before any term of art may be used.
- Anything else.

**F. Write the instruction text you would actually recommend.** Concrete, ready to paste, with your
stated expectation of how well it will hold and what will defeat it. Constraints on it: it goes
into a single source file that renders into an always-loaded instruction file, so it costs context
on every single turn and must earn its length. It must be plain ASCII. It must not conflict with
the existing requirement that mandated reports (a review's findings table, a release checklist) are
produced in full and are exempt from the brevity cap. And, given section 2, it must not be a rule
that can be satisfied mechanically while missing the goal. If your honest recommendation is to
write *less* than the current four words plus something structural elsewhere, recommend that.

## 5. What a useful answer looks like

- Distinguishes evidence from speculation, every time, without me having to guess which is which.
- Tells me if a proposal is unsupported or likely to backfire. The five proposals came from the
  agent that has the problem, which is not a neutral source; treat them as hypotheses to test, not
  as a specification to implement.
- Engages with section 2 rather than around it. An answer that recommends a stronger, better
  exampled, more specific rule without explaining why `askme.md` failed has not addressed the
  question.
- Gives me the negative result if that is what the evidence says. "Written instructions do not
  reliably control this; here is the interposed-pass architecture that does, and here is its cost"
  is a completely acceptable answer, and is the one I half expect.
- Cites the repository where it is relevant, since it is public and you can read it. In particular
  `agent_workflows/reporting_contract.py`, `.aw/system/workflows/askme/askme.md`, and `AGENTS.md`.

Return the report as a downloadable `.md` file.
