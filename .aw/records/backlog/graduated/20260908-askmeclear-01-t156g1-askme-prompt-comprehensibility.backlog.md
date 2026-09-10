- Id: t156g1
- Status: graduated
- Set: askmeclear
- Priority: high
- Work-Kind: bug
- Summary: askme produced an unintelligible prompt that passed all nine exit-gate checks; the gate is entirely mechanical so it cannot test comprehensibility

## Workflow history
- 2026-09-10 graduated (aw set): Graduated into plan 5wtzqv (Set askmefix), which carries - From-Backlog: t156g1 and fixes all four diagnosed defects in one change: the anti-jargon rule gains a positive obligation (the generic-placeholder anti-pattern is named a violation), the symptom is required before any option in a fixed symptom-choice-consequence order, Step 1's sort gains an already-states-a-decision-rule test (the root cause: the measured question was answered by plan zzcrlo's own OQ-03 plus a measurement already in hand), and incomprehension through any channel including the free-text option becomes discard-and-re-ask. Plus the one deliberately non-mechanical exit-gate item, and the mandated P12 re-read dropped with the citation kept and the pre-flight list given exactly one home (relocate-versus-reference left as non-blocking OQ-01, bounded by P12's six other callers). SCOPE AND VALIDATION POSTURE WERE SET BY THE MAINTAINER INTERACTIVELY 2026-09-09: all four causes in one plan, and NO trial-run gate. They rejected my claim that any part could be 'automated': 'neither my request (prompt) nor your response go through any tool that you or I control', which is correct, so the plan's tests are scoped honestly as anti-deletion presence guards on the workflow body and the plan states plainly that comprehensibility is unproven. graduated NOT done: the design is handed off, no code is written.
- 2026-09-08 created (aw backlog): FILED from a measured failure during /aw askme on plan zzcrlo, at the maintainer's request. The maintainer reported: 'I wanted to pick write your own and say I did not understand a single word of your explanation.' The prompt satisfied every exit-gate item, which is the finding: all nine checks are mechanical (id6 used? recommendation labelled?) and comprehensibility is not, so the gate passes a prompt that fails its only purpose. Three defects with three different fixes, plus a maintainer-raised recommendation to DROP the mandated GUIDING_PRINCIPLES P12 re-read (it was performed in this run and prevented nothing, because the needed guidance is not in P12) while keeping the citation and moving P12's pre-flight self-check list into the askme kernel where composition happens.

MEASURED 2026-09-09, and the evidence is a prompt that PASSED EVERY EXIT-GATE ITEM and was still
unintelligible to the maintainer, who replied: "I wanted to pick write your own and say I did not
understand a single word of your explanation."

The run: `/aw askme` on plan `zzcrlo`'s open questions. The workflow was followed as written. P12 WAS
READ before composing. The prompt satisfied all nine exit-gate checks: one question, no reference to an
earlier message, no id6 or symbol name as its subject, a labelled recommendation, and measured numbers
included. The maintainer could not parse it.

THE GATE CANNOT CATCH THIS, WHICH IS THE POINT. Every item in the exit gate is MECHANICALLY CHECKABLE
(did you use an id6? did you label a recommendation?). Comprehensibility is not, so a prompt can pass
the entire gate and fail its only purpose. The checks that are easy to automate are not the ones that
test the thing that matters.

THREE DISTINCT DEFECTS, each needing a different fix.

1. THE ANTI-JARGON RULE HAS NO POSITIVE HALF, so it is satisfiable by DELETING NOUNS. Kernel item 3
   forbids an id6, a symbol name, or a finding code as the subject. It never says what to write
   INSTEAD. Complying by substitution produced "a shipped pair of helpers" and "a 900-line run-state
   model": strictly WORSE than the banned names, because a named thing can be looked up while an
   anonymous thing cannot be pictured at all. The rule removed the handle and left a void.
   FIX: state the positive obligation. When you drop an internal name, replace it with what the thing
   DOES in the reader's terms ("the retry code built for another part of the system", not "a shipped
   pair of helpers"). A placeholder that carries no meaning is a violation, not compliance.

2. THE PROMPT DESCRIBED THE FIX AND NEVER THE PROBLEM. It opened inside a mechanism ("a pending fix
   needs to give an item one bounded second attempt"), and the actual bug (a run prints COMPLETED when
   its work never landed) appeared NOWHERE. P12 lists "the general reason a decision is needed", which
   was treated as satisfied by describing the remedy rather than the symptom.
   FIX: require the SYMPTOM before the CHOICE. A prompt that explains only the remedy has skipped the
   one thing that makes the options meaningful.

3. THE QUESTION WAS NOT THE HUMAN'S TO ANSWER, so Step 1's sort was wrong. Plan `zzcrlo`'s E-04 already
   states the rule (use the shipped `run_recovery` helpers if the adaptation is genuinely small,
   otherwise bound the retry directly and RECORD the divergence). The measurement was already in hand:
   `plan_retry` needs a `run_engine.RunEngine`, neither driver imports `run_engine` or `run_state`
   (measured 0 references), those modules total 905 lines, and `plan_retry` has ZERO production callers
   (tests only). So the repository had already answered it, and the kernel's own closing line applies:
   "Asking a question the repository answers is as much a failure as not asking one it cannot."
   FIX: make Step 1 test explicitly whether the OWNING ARTIFACT already states a decision rule. A
   question whose artifact says "do X if measurement M, else Y and record it" is YOURS once M is
   measured, not the human's.

WHAT THE HUMAN DID THAT THE WORKFLOW SHOULD HAVE ANTICIPATED: they reached for the tool's
"write your own answer" escape hatch to report incomprehension. The workflow has a rule for
"I have zero context here" (Step 3: STOP AND RE-ASK, the prompt was defective) but frames it as the
HUMAN lacking context rather than the PROMPT failing to supply it. That framing is subtly wrong and is
probably why it was not reached for here.
FIX: name the escape-hatch case explicitly. Any answer reporting incomprehension, including one
delivered through a free-text option, means DISCARD THE ANSWER and re-ask. Do not record it.

ON THE MANDATED P12 RE-READ, and this is a SEPARATE recommendation the maintainer raised: reading P12
did not prevent any of the above, because the guidance the run needed IS NOT IN P12. There are already
THREE layers carrying this: the always-loaded `AGENTS.md` managed block (`:73`, a condensed P12), the
`askme` memory kernel (9 items), and P12 itself (~2,070 chars). The mandated read is therefore mostly
RITUAL COMPLIANCE, and it manufactures false confidence ("I read P12, so my prompt is fine"), which is
exactly the failure `askme`'s own preamble describes when it says P12 alone was measured insufficient.
Note P12 does hold ONE thing the kernel lacks: its pre-flight self-check list ("Can the user answer
without reopening other material?").
PROPOSED: DROP the mandated re-read, KEEP a one-line citation (P8, single source of truth), and MOVE
P12's pre-flight list into the kernel where composition actually happens. Do NOT delete P12 or its
content; this is about where the obligation is stated, not whether it holds.

SUGGESTED ADDITION TO THE EXIT GATE, the one non-mechanical item, phrased so it is answerable: could a
reader who has never opened this repository restate, in their own words, the PROBLEM, the CHOICE, and
the CONSEQUENCE of each option? If the prompt names no symptom, or if any noun in it is a placeholder
the reader cannot picture, it fails.

DO NOT FIX THIS BY ADDING MORE PROSE TO P12. A fourth copy of the same guidance is the drift P8
forbids, and three copies already failed. The fixes above are changes to the KERNEL and the SORT, plus
one honest non-mechanical gate item.
