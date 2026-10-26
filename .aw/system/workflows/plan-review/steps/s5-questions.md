# Check S5: Resolve Open Questions

Complete this before the final report.

### 3.1 Build the question set
Collect and deduplicate:
- Pre-existing open questions.
- Questions created by findings.
- Instruction conflicts.
- Decisions needed to repair or replan.

Resolve questions from authoritative evidence first. Cite the source. Do not
ask the human what the repository already answers.

#### Resolving HOW questions: demonstrate, do not describe

1. A question is a HOW question when its resolution chooses a mechanism rather than a fact or a scope (such as a code shape, a placeholder form, a flag, an algorithm).
2. A HOW question may be marked `resolved` only when the resolution cites a demonstration that the mechanism produces the required outcome on a concrete case (a scratch-repo run, a probe, a test, pasted output), held to the same evidence standard as a Findings row.
3. If the reviewer cannot demonstrate it, they MUST instead either leave the question `open` (with `Blocking: yes` when execution depends on it) or convert it into a first spike E-item whose Expected outcome is the demonstration and whose stop condition names the question, and the review verdict MUST name the feasibility risk. State why the first branch bites: an open question carrying `- Blocking: yes` makes `aw ipd lint` report `error` with `IPD-Q501` at every checkpoint including `author`, so the plan cannot reach `approved` or be dispatched until a human answers (`IPD-Q501: OQ-01: BLOCKING question is still 'open'. Ask the human and record the answer`). Verified at review by inserting such a question into this plan: disposition went `conforming` -> `error` at `author`, `review-finalize` and `pre-execution` alike.
4. A resolution containing its own "confirm empirically / if no form works, stop" clause is by definition undemonstrated and falls under (3).
5. `- Owner: maintainer` on a resolved question means the maintainer answered; a reviewer's own choice records the reviewer (or `plan author`) as owner and gets a `### Decisions` row as 3.1 already requires. Write this so a human applies it: no gate checks it. The linter only verifies the `Owner` field is non-empty and not `none` (`ipd_lint`'s `has_owner`, passed to `ipd_schema.open_question_error` as a bare boolean that never sees the value), so a false `Owner: maintainer` passes every mechanical check. Measured example: plan `vtkfq8` OQ-03 resolved a carrier requirement with an inert placeholder and labelled it `Owner: maintainer`, which passed mechanical checks but failed execution because `- Status: open` was what enforced the obligation.

Mark which questions block correctness, security, scope, architecture, or GO.

A question you resolve yourself is not GONE. It is a RECORDED DECISION: a judgement call you
made on your own authority, with an alternative you rejected and a basis someone else can
check. So for EVERY question you resolve from evidence instead of asking, add one row to the
`### Decisions` section of the current `## Round <n>` in the typed review record:

```text
ID | Question | Chosen | Alternatives considered | Basis | Reversible
```

- **ID:** `D-1`, `D-2`, ... within the round.
- **Question:** what you would have asked the human.
- **Chosen:** what you decided.
- **Alternatives considered:** what you rejected. "None" is a claim you must mean.
- **Basis:** the `path:line` or artifact that authorized it. This is the same citation the
  paragraph above already requires; the row is where it becomes checkable.
- **Reversible:** `yes` or `no`, judged as below.

This is why the rule "resolve from evidence rather than asking" is safe: it converts a question
into a decision, not into silence. A reviewer who resolves ten questions and records none has
taken ten unreviewable turns, and a wrong one is then discoverable only by reading the code it
produced. Recording costs one row.

Read them back with `aw reviews decisions` (add `--irreversible` for the ones that matter most).

#### Reversible or not, and what that obliges

Judge `Reversible` on the COST OF BEING WRONG, not on your confidence:

- `yes`: a later maintainer can undo it by editing the plan or the code. Wrong costs a rewrite.
- `no`: it cannot be cleanly undone. Published interfaces, data or file migrations, deletions,
  a released artifact, anything another party may already depend on.

A `Reversible: no` decision MUST NOT rest on your authority alone. Record the row AND do one of:

- raise it in the reviewed plan as an open question carrying `- Blocking: yes`, so the existing
  lint gate refuses the plan at EVERY checkpoint until the human answers (since 2026-09-08 this
  fires from `author` onward, not only at `pre-execution`, so the stop happens earlier); or
- tell the maintainer directly and note that on the row (e.g. `Basis: ... ; maintainer told
  2026-08-29`), which is the honest path in a non-interactive run where no blocking question
  would be seen in time.

Recording alone is enough for a reversible decision and is NOT enough for an irreversible one.
That distinction is the whole point: a reversible wrong turn costs a rewrite, an irreversible one
cannot be undone, and resolving-instead-of-asking must never silently authorize the second.
`check.review-decision-unescalated` reports an unescalated `Reversible: no` row as a warning; it
is a backstop for a reviewer who skipped this step, not a substitute for doing it.

### Finding escalation rule
Every finding left `OPEN` or `DEFERRED` at or above the repository's gate threshold (`review_findings_gate.block_at` in `.aw/config/project.json`, default `HIGH`) is ALSO raised in the plan as an open question carrying `- Blocking: yes` and `- Finding: <ID>` naming that finding. `check.review-finding-unescalated` enforces this, and the escalated question is then caught by the existing lint gate at EVERY checkpoint (not only `pre-execution`, since 2026-09-08), so an unfixed serious finding actually stops execution instead of merely being reported.

No check may change an existing `Blocking: yes` to `Blocking: no` without a recorded reason (MD-11).

Every recommended answer for an open question must state its strength as one of `very weak`, `weak`, `medium`, `strong`, or `very strong` (MD-9).

### 3.2 Ask interactively
Notice: this interactive subsection applies only to an interactive `/plan-review` run. When run by a runner (non-interactive review invocation), questions are recorded in the plan and review record per Section 3.3 instead of prompting interactively.

In an interactive run, ask one to three related questions per prompt.

For each question provide:
1. **Decision needed**
2. **Context**
3. **Why it matters**
4. **Options**
5. **Trade-offs**
6. **Recommendation**

Use plain language. Define acronyms and identifiers. Ask and wait before the
final report. Do not guess or bury the recommendation. Present this whole six-part
question set INSIDE the interactive prompt itself, so a human answering from the prompt
can decide from the prompt alone (GUIDING_PRINCIPLES P12); do not strand it in chat.
The "Options" item is satisfied by the interactive tool's rendered CHOICES: supply the
options AS the tool's answer options, and do NOT also restate or preview them in the
composed context prose (P12).

After each answer:
1. Record it in the owning plan.
2. Resolve or rewrite the open question.
3. Apply resulting edits.
4. Re-check affected rubric areas.
5. Continue until no resolvable question remains.

### 3.3 Non-interactive exception
A run is non-interactive only when the environment explicitly has no human
interaction channel. A delayed reply is not non-interactive.

In a genuinely non-interactive or interrupted run (including a runner multi-prompt review):
- Leave questions explicitly `OPEN`.
- State the required decision.
- Use verdict `REVIEWED - OPEN QUESTIONS`.
- Recommend `NO-GO`.

### The escalation RETURN PATH

Step 4 requires an unfixed finding at or above the gate threshold to be escalated
INTO the plan as a `- Blocking: yes` question carrying `- Finding: <ID>`. That
escalation is defined in one direction only, so answering the question used to
leave the finding `OPEN` in the typed review record forever, and the gate that
reads that column kept blocking.

A finding whose escalated question is now `- Status: resolved` is therefore STALE.
Clear it by APPENDING a new `## Round <n>` to the review record that marks the
finding `fixed` and cites the answered question and its date; never edit the
earlier round in place, because round 1 was true when it was written and rewriting
it destroys the audit trail. `aw ipd recheck-readiness --stale-findings` reports
these (and writes the round under `--apply`), matching the question to the finding
on the question's declared `- Finding: <ID>` back-reference rather than on a
judgement about what the question was about. A question that is still open does NOT
make its finding stale. This review-record amendment still applies to a terminal
plan, clearing its stale gating finding without rewriting the plan file itself.

Record notes in the review record's `### Step S5` subsection starting with `- Checked: <what was examined>`.
Record findings per `_findings.md` in the current round's single `### Findings` table.
