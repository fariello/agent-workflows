# Step 3: Resolve, finalize, and report

## Purpose

Resolve human decisions, finalize review state, create the hardened commit, and
produce the deterministic final report.

## 1. Resolve open questions

Collect:

- pre-existing unresolved questions;
- questions created by findings;
- unresolved instruction conflicts;
- decisions required for repair or replan.

Resolve questions already answered by authoritative evidence and cite it.

### Resolving HOW questions: demonstrate, do not describe

1. A question is a HOW question when its resolution chooses a mechanism rather than a fact or a scope (such as a code shape, a placeholder form, a flag, an algorithm).
2. A HOW question may be marked `resolved` only when the resolution cites a demonstration that the mechanism produces the required outcome on a concrete case (a scratch-repo run, a probe, a test, pasted output), held to the same evidence standard as a Findings row.
3. If the reviewer cannot demonstrate it, they MUST instead either leave the question `open` (with `Blocking: yes` when execution depends on it) or convert it into a first spike E-item whose Expected outcome is the demonstration and whose stop condition names the question, and the review verdict MUST name the feasibility risk. State why the first branch bites: an open question carrying `- Blocking: yes` makes `aw ipd lint` report `error` with `IPD-Q501` at every checkpoint including `author`, so the plan cannot reach `approved` or be dispatched until a human answers (`IPD-Q501: OQ-01: BLOCKING question is still 'open'. Ask the human and record the answer`). Verified at review by inserting such a question into this plan: disposition went `conforming` -> `error` at `author`, `review-finalize` and `pre-execution` alike.
4. A resolution containing its own "confirm empirically / if no form works, stop" clause is by definition undemonstrated and falls under (3).
5. `- Owner: maintainer` on a resolved question means the maintainer answered; a reviewer's own choice records the reviewer (or `plan author`) as owner and gets a `### Decisions` row as 3.1 already requires. Write this so a human applies it: no gate checks it. The linter only verifies the `Owner` field is non-empty and not `none` (`ipd_lint`'s `has_owner`, passed to `ipd_schema.open_question_error` as a bare boolean that never sees the value), so a false `Owner: maintainer` passes every mechanical check. Measured example: plan `vtkfq8` OQ-03 resolved a carrier requirement with an inert placeholder and labelled it `Owner: maintainer`, which passed mechanical checks but failed execution because `- Status: open` was what enforced the obligation.

This rule is kept identical to the single-file `../plan-review/plan-review.md` per the parity note in `plan-review-long.md`.

Deduplicate overlapping questions. Mark which block correctness, security,
scope, architecture, or GO readiness.

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
- **Basis:** the `path:line` or artifact that authorized it. This is the same citation this
  section already requires; the row is where it becomes checkable.
- **Reversible:** `yes` or `no`, judged as below.

This is why the rule "resolve from evidence rather than asking" is safe: it converts a question
into a decision, not into silence. A reviewer who resolves ten questions and records none has
taken ten unreviewable turns, and a wrong one is then discoverable only by reading the code it
produced. Recording costs one row.

Read them back with `aw reviews decisions` (add `--irreversible` for the ones that matter most).

### Reversible or not, and what that obliges

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

In an interactive run, ask one to three related questions at a time.

For each question provide:

1. Decision needed.
2. Context.
3. Why it matters.
4. Options.
5. Trade-offs.
6. Recommendation and one-line reason.

Use plain language. Define acronyms and identifiers. Do not guess. Present this whole
six-part question set INSIDE the interactive prompt itself, so a human can decide from the
prompt alone (GUIDING_PRINCIPLES P12); do not strand it in chat. The "Options" item is
satisfied by the interactive tool's rendered CHOICES: supply the options AS the tool's answer
options, and do NOT also restate or preview them in the composed context prose (P12).

After each answer:

1. Record it in the owning plan.
2. Resolve or rewrite the open question.
3. Apply consequent edits.
4. Re-run affected rubric areas.
5. Ask any newly required dependent question.

Continue until no resolvable question remains.

A run is non-interactive only when no human channel exists. A delayed answer is
not non-interactive.

For a genuinely non-interactive run, leave questions `OPEN`, use verdict
`REVIEWED - OPEN QUESTIONS`, and recommend `NO-GO`.

## 2. Finalize plan state

For each reviewed plan confirm:

- every finding is `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`;
- every deferral meets the Fix Bar;
- the typed review record was written, and every finding left `OPEN` or `DEFERRED` at or above the
  repository's gate threshold (`review_findings_gate.block_at` in `.aw/config/project.json`, default
  `HIGH`) is ALSO raised in the plan as an open question carrying `- Blocking: yes` and
  `- Finding: <ID>` naming that finding. `check.review-finding-unescalated` enforces this, and the
  escalated question is then caught by the existing lint gate at EVERY checkpoint (not only
  `pre-execution`, since 2026-09-08), so an unfixed serious
  finding actually stops execution instead of merely being reported. This does NOT contradict
  "Severity is for reporting only": severity still does not decide whether to FIX anything (the Fix
  Bar alone does that, on Remediation Risk), only whether a finding you have ALREADY decided not to
  fix must be surfaced as blocking;
- resolved decisions are written into the plan;
- required spec and documentation work is included;
- tests and validation cover affected invariants;
- the plan does not claim implementation;
- for an agent-executable plan (an IPD or similar with actionable steps), the CREATOR authored BOTH the top execution checklist AND the end
  verification/cross-check checklist, and you (the REVIEWER) assessed both (execution covers every
  action/decision/deliverable/validation; verification maps 1:1 with concrete per-item evidence and
  is specific enough to catch a false completion claim). A missing/weak checklist is an UNDER-SCOPE
  finding you add or strengthen in place.

After all revision edits are applied, re-run the deterministic structural linter at the finalize
checkpoint as a GATE:

    aw ipd lint --phase review-finalize --agent <plan-file>

Only a `conforming` disposition permits a passing verdict; exit `1` is a structural finding to
repair; exit `2` is a hard stop. INVOKE the linter; do not paraphrase it. It proves structure/state
only; it does not establish semantic adequacy. (The `machine preflight unavailable: bootstrap`
label applies only while the linter does not yet exist.)

For a plan whose own first `- Kind:` bullet reads `orchestrator` (read from the plan's own first
`- Kind:` bullet in front matter; never use a whole-file containment scan like
`grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as `m7gvuz`),
`review-finalize` enforces typed child-tracking row conformance (`IPD-S407`).

**Honest exhaustion (R6):** If the orchestrator repair loop (budget of 2 attempts) exhausts with
`IPD-S407` violations unresolved, the plan remains `- Status: to-review`, the findings are recorded
in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this
path (not `no-go` and not a pass); absence is legal, silent, and leaves the plan unclearable by the field (and clearable by prose only on a genuine review record, which this path does not write).

Beside `review-finalize`, for an orchestrator, review readiness is checked with `aw ipd coverage <id6>` (`IPD-S408`). `aw ipd set reviewed` refuses an orchestrator with unresolved coverage findings (Order 05), so the reviewer resolves each quoted finding by assigning it by id6 to a child in the table or by adding a child plan and its row (never by deleting the checklist).

**Honest exhaustion for review readiness (`IPD-S408` / R6):** If the orchestrator review readiness repair loop (budget of 2 attempts) exhausts with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass); absence is legal, silent, and leaves the plan unclearable by the field (and clearable by prose only on a genuine review record, which this path does not write).

Apply the project's review-complete status. If it uses `Status`, set `reviewed`
unless the contract requires another value.

`reviewed` does not mean approved, GO, ready to execute, or executed.

### Write the structured `Readiness` field (REQUIRED output of the review)

Write your readiness into the plan's front matter as a machine-readable field, beside
`Status`:

```markdown
- Readiness: <go | go-pending-approval | no-go>
```

Map it from the readiness vocabulary in Section 4:

| Readiness you report | Field value |
|---|---|
| GO | `go` |
| GO - PENDING HUMAN APPROVAL | `go-pending-approval` |
| NO-GO | `no-go` |

THE HISTORY-LINE PROSE IS NOT THE PRIMARY MACHINE SIGNAL. Downstream automation evaluates readiness using a three-way rule: a valid attested field decides; a corrupt field refuses outright with no fallback; and an absent field falls back to history prose, clearing the plan only if the newest history entry is a genuine review record with an approving verdict, which is why IPD-M113 now refuses the absence at `reviewed` upstream of that fallback. Omitting the field leaves a clean plan that should have read `go-pending-approval` dependent on prose fallback instead of machine-attested clearance. Write exactly one of the three values, lowercase, with no extra words.

**Exception for exhausted orchestrator repair loop (`IPD-S407` / `IPD-S408` / R6):** If an orchestrator's
checklist repair loop or coverage repair loop exhausts its budget of 2 attempts unresolved, leave `- Readiness:` ABSENT
entirely. Do NOT write `- Readiness: no-go` or any other value; absence leaves the plan unclearable by the field and clearable by prose only on a genuine review record, which an exhausted R6 round has not produced, while honestly reflecting that no review verdict was reached.

Append or update:

```markdown
## Workflow history

- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>
```

Use `unknown` when the identifier is unavailable.

Note the history section is NEWEST-FIRST: a new record goes directly under the
`## Workflow history` heading, so the first record is the most recent.

## 3. Hardened-result commit

After all edits and decisions:

1. Commit only reviewed plans and any required run record.
2. Use `plan-review: harden <scope> (revisions applied)`.
3. Never include unrelated files.
4. Never push.
5. Report skipped or failed commits exactly.

## 4. Verdict and readiness

Use exactly one verdict:

- `APPROVE` - no revisions needed; no open questions; all deferrals pass.
- `APPROVE WITH REVISIONS APPLIED` - findings fixed; no open questions; all
  deferrals pass.
- `REVIEWED - OPEN QUESTIONS` - review complete, but human decisions remain.
- `REJECT - NEEDS REPLAN` - the approach is unsound and not safely patchable.

Readiness (human approval is a SEPARATE step from the review verdict; a reviewed,
clean plan is `GO - PENDING HUMAN APPROVAL`, never a bare `NO-GO`; reserve `NO-GO`
for genuine not-ready conditions):

- `GO` requires APPROVE or APPROVE WITH REVISIONS APPLIED, no open questions, no
  unfixed BLOCKER or HIGH, AND human approval (`Status: approved`). Cleared to proceed.
- `GO - PENDING HUMAN APPROVAL` - same clean bar as GO, but the human sign-off has
  not happened yet. The correct, positive readiness for a plan that passed review
  and only awaits approval. NOT a failure state.
- `NO-GO` - genuine not-ready: any open question, any unfixed BLOCKER/HIGH, or a
  `REVIEWED - OPEN QUESTIONS` / `REJECT - NEEDS REPLAN` verdict. NOT used merely
  because a clean plan lacks a signature.

A reviewed clean plan is `GO - PENDING HUMAN APPROVAL` (awaiting sign-off); it is
only `NO-GO` when a genuine not-ready condition remains.

## 5. Final report

Read `report-template.md` in full and use it exactly.

The final reviewed/not-reviewed enumeration MUST contain every item from the
Step 1 scope ledger and MUST be the literal last output.

## Exit gate

The run is complete only when:

- [ ] All resolvable questions are answered and applied.
- [ ] Each plan's review status and workflow history are updated.
- [ ] Every finding and deferral is reconciled.
- [ ] Verdict and GO/NO-GO are consistent.
- [ ] Hardened commit exists or is explained.
- [ ] Final report follows the template exactly.
- [ ] Nothing follows the reviewed/not-reviewed enumeration.
