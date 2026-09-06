# Spec Review (pre-approval specification reviewer)

Treat this file as the controlling instruction for reviewing a SPECIFICATION at `to-review`, then
improving that spec in place and advancing it to `reviewed` through the setter.

Review specification documents only. Do not change code, tests, runtime configuration,
infrastructure, or production data. Do not author plans. Reviewing a spec is not implementing it.

THIS IS THE SPEC-TIME SIBLING OF `plan-review`, and it is deliberately a SEPARATE package rather than
a conditional branch inside that one (maintainer ruling 2026-09-04; the evidence and the accepted
cost are recorded in `README.md` beside this file, which you should read once before your first run).
Read `../plan-review/plan-review.md` as a REFERENCE for the shared halves it owns; do NOT edit it,
and do NOT apply its plan-only obligations here (Section "Three prohibitions" states exactly which,
and why each one would corrupt a spec).

This workflow shares these sibling policies:
- `../release-review/fix-decision-policy.md`
- `../release-review/00-run-protocol.md`

## What is SHARED and must not be re-stated here

The findings/verdict/record machinery is single-sourced ON PURPOSE (spec `6m4kow` Section 5). Read it
from the shared authority rather than from a copy in this file, because a copy is the thing that
drifts:

| Shared thing | The one authority | Where it is written down |
|---|---|---|
| Severity (`BLOCKER|HIGH|MEDIUM|LOW`) and Scope (`IN-SCOPE|OVER-SCOPE|UNDER-SCOPE`) | `review_findings.SEVERITIES` | `../plan-review/plan-review.md`, "Severity and scope" |
| Remediation Risk and the Fix Bar | `../release-review/fix-decision-policy.md` | `../plan-review/plan-review.md`, 2.3 |
| Decision (`FIXED|DEFERRED|OPEN|REPLAN`) | `review_findings.DECISIONS` | `../plan-review/plan-review.md`, 2.2 |
| The four verdicts | `plan_readiness.VERDICTS` | `../plan-review/plan-review.md`, "Verdict and readiness" |
| The typed review record's shape | `review_findings.render_review` | `.aw/records/reviews/` |
| Whether a finding gates | `review_findings.is_gating` | the repo's `review_findings_gate.block_at` |

WHAT IS LOCAL TO THIS WORKFLOW is exactly two things: the SPEC RUBRIC (below), and the three
prohibitions. Anything else you find duplicated here is a defect; fix it by deleting the copy.

---
## Memory kernel
Re-read this before each step and before the final report:
1. Review specs only. Never write code, and never author the plans the spec will graduate into.
2. Verify claims from repository evidence, with `path:line`.
3. Fix by default. Severity never decides whether to fix; the Fix Bar does.
4. Resolve open questions interactively when possible; never guess a human decision.
5. NEVER hand-edit the spec's `- Status:` or its `## Workflow history`. `aw specs set` / `aw specs
   note` own both.
6. NEVER write `- Readiness:` onto a spec.
7. NEVER run `aw ipd lint` against a spec. `aw specs check` is the spec's structural gate.
8. Make at most two local commits. Never push.
9. The reviewed/not-reviewed enumeration is the literal final output.
10. A gate or interactive question MUST NOT assert or imply the verdict it precedes; it states what
    was found and asks what to do.

---
## Three prohibitions (each one a measured way `plan-review` would corrupt a spec)

These are not style preferences. Each is a real defect that would result from pointing the plan
reviewer at a spec, which is why this workflow exists as its own body.

### (a) Do NOT write `- Readiness:` onto a spec

`plan-review.md:377-398` REQUIRES writing that field, and its own text warns that "a consumer that
finds no field FAILS CLOSED". A spec has no such field in its schema, and spec `25kzda` Section 3.3
stops a `reviewed` spec at an unconditional human approval gate EVEN UNDER `--full-auto`. So there is
no automated readiness signal for a spec to record, and inventing one would create a machine signal
that no consumer is permitted to act on.

Your readiness judgement still belongs in the review: state it in the FINAL REPORT and in the review
record's verdict. It does not go into the spec's front matter.

### (b) Do NOT hand-edit `- Status:` or the workflow history

`plan-review.md:371-372` hand-edits `Status`. For a spec that is forbidden: `.aw/records/specs/README.md`
says the status and history are tool-owned, and a `hooks/status_untooled_gate.py` hook exists to catch
exactly this bypass. Use the verbs:

    aw specs set reviewed <id6> --message "<verdict>; <finding ids>"
    aw specs note <id6> --message "<annotation>"          # history only, no status change

The setter validates the transition, enforces the attestation gate (below), writes the history record,
and refuses byte-identically if the result would not conform. A text edit does none of that.

### (c) Do NOT run `aw ipd lint` against a spec

`plan-review.md:113-133` runs `aw ipd lint --phase author` as a preflight GATE, and that linter is
IPD-only. The subtle hazard is not that it would error: the preflight is GUARDED by "For each eligible
plan that is an agent-executable IPD", so handed a spec it would SKIP, and the gate would PASS BY NOT
RUNNING. A skipped gate that looks like a passed one is worse than an absent gate.

The spec equivalent, which `25kzda`'s own `SPEC-REVIEW-STRUCTURE` recovery command already names:

    aw specs check <spec-file>

Only a clean result proceeds. Exit 1 is a structural finding to repair before a passing verdict; a
failure to RUN is a hard stop, not a skip.

---
## Step 0: Scope and project contract

### 0.1 Build the review-scope ledger
The ledger contains ONLY the specs explicitly named in the invocation, plus any that the project's own
documented eligibility rules add. Do NOT enumerate other specs in the repository to build it.

Classify each candidate as:
- `ELIGIBLE` - review it.
- `NOT REVIEWED` - a candidate skipped, with the exact reason (missing, unreadable, malformed beyond
  review, not a specification, or a status for which review is not the next legal action per spec
  `25kzda` Section 3.3). NOT REVIEWED never lists a spec that was never a candidate.

REVIEW IS THE NEXT LEGAL ACTION at `to-review`, and at `draft` only when the draft is COMPLETE and was
admitted (spec `25kzda` Sections 3.3 and 2.5a). A spec at `approved`, `implementing`, `implemented`,
`deferred`, `parked`, or `superseded` is NOT REVIEWED with that status as the reason. Re-reviewing a
spec already at `reviewed` is legitimate ONLY when explicitly requested (`25kzda` 3.3's
`--action review` row); it appends a new round and KEEPS the status `reviewed`.

### 0.2 Discover controlling instructions
Read the applicable repository and directory-scoped instructions, guiding principles, the specs tree's
own README (the lifecycle a human follows), any spec this one cites via `- From-Spec:`, and the target
spec in full. Do not assume filenames. If instructions conflict, use the project's precedence rules;
if none resolve it, record an open question rather than silently choosing.

### 0.3 Discover the spec contract
Determine: the spec's location, front matter, status lifecycle and who owns each transition, its typed
gate fields, its history grammar, and the repository's approval rules. Determine what the spec is a
spec FOR: the production target, the invariants it must not break, and the artifacts that will
graduate from it.

---
## Step 1: Evidence and pre-review snapshot
For each eligible spec:
1. Read the whole spec.
2. List the material files, requirements, prior specs, decisions, and behaviors it relies on or claims.
3. Open the referenced evidence.
4. Verify material claims with `path:line` evidence. A spec's measured claim ("X does not exist",
   "N artifacts are in state S") is exactly the kind that rots; re-measure it rather than trusting it.
5. Record missing, stale, contradictory, or inaccessible evidence.

### Structural preflight (before semantic review)
Run the deterministic SPEC checker as a gate before spending semantic effort:

    aw specs check <spec-file>

Only a clean result proceeds. This proves STRUCTURE and STATE only (status enum, typed gates, history
presence, naming, metadata safety); it establishes nothing semantic, so the review below remains fully
required and separate. See prohibition (c): do NOT substitute `aw ipd lint`.

### Pre-review commit
Before editing:
1. Inspect repository status.
2. Isolate the eligible spec files.
3. If any target spec is untracked or modified, commit those spec files verbatim as
   `spec: pre-review snapshot of <scope>`.
4. If all target specs are committed and unchanged, skip the snapshot.

Never stage unrelated files. Never amend, reset, rebase, discard user changes, or push.

---
## Step 2: Review and revise

### 2.1 Apply all required views
Review against the spec rubric below, the project's principles, the domain invariants, the spec's own
goals and acceptance criteria, the eight personas
(`../release-review/00-run-protocol.md`), and the security lens as a mandatory cross-cutting concern.

### 2.2 Record findings
Record each distinct actionable issue; combine duplicate symptoms under one root cause; do not invent
findings. Classify each with Severity, Scope, Area, Evidence (`path:line`), Remediation Risk, and
Decision, using the SHARED vocabularies named in the table at the top of this file.

Write the findings to BOTH places:

1. The findings table in the final report (below).
2. A typed review record, `.aw/records/reviews/<...>.review.md`, using the same columns, with
   `- Subject-Id: <spec-id6>` and `- Subject-Type: spec`.

The record is what makes a severity readable by tooling, and for a spec it is now also the ATTESTATION
that the review happened (see Step 4). Append a new `## Round <n>` for a re-review rather than editing
an earlier round: the gate reads only the CURRENT round.

VERIFY THE RECORD PARSES. Any parse diagnostic in a review record is treated as BLOCKING by
`review_findings.subject_gating_blocks`, so a record that merely LOOKS right but does not parse will
block its own spec's approval with a cause that names a parse code rather than a finding. Check it:

    aw check all            # the record must raise no new finding
    python3 -c "from agent_workflows import review_findings as rf; d = rf.parse_review_file('<record>'); print(d.diagnostics)"

Both must be clean before you rely on the record.

### 2.3 Remediation Risk and Fix Bar
Use `../release-review/fix-decision-policy.md` unchanged. Fix every finding unless overall Remediation
Risk is Medium-High or High; every deferral must state the axis, why the risk reaches the threshold,
the required decision or evidence, and the consequence of leaving it unresolved. Effort, time, cost,
and tokens are never valid deferral reasons.

For OVER-SCOPE in a spec, the default fix is removal or explicit relocation to Non-goals, which is
normally Low risk.

### 2.4 Revise the spec in place
Make surgical edits to the spec's BODY:
- Preserve valid content and the required structure.
- Replace ambiguity instead of appending duplicate prose.
- Make an untestable requirement testable, or record why it cannot be.
- Add the missing acceptance criterion, constraint, non-goal, or decision rationale.
- Remove unsupported or gold-plated requirements.
- Do not weaken a valid requirement, and do not invent one the goal does not need.

DO NOT CHANGE WHAT THE SPEC DECIDES. A reviewer sharpens a requirement; a reviewer does not silently
substitute a different design. If the specified approach is unsound, that is a `REPLAN` finding with
the minimum shape of a sound replacement, not an in-place rewrite of the decision.

Remember prohibitions (a) and (b): the front-matter `- Status:` and the history are written ONLY by
`aw specs set` / `aw specs note`, and `- Readiness:` is never written at all.

---
## Step 3: Resolve open questions

### 3.1 Build the question set
Collect and deduplicate the spec's pre-existing open questions, the questions your findings created,
instruction conflicts, and any decision needed to repair or replan. Resolve from authoritative evidence
first and cite the source; do not ask the human what the repository already answers. Mark which
questions block correctness, security, scope, or approval.

A question you resolve yourself is a RECORDED DECISION, not a vanished one. For EVERY question you
resolve from evidence instead of asking, add one row to the `### Decisions` section of the current
`## Round <n>` in the typed review record, with the columns and the `Reversible` judgement rule defined
in `../plan-review/plan-review.md`, 3.1. That rule is shared and is deliberately not restated here.

A `Reversible: no` decision MUST NOT rest on your authority alone: record the row AND either raise it
in the spec as an open question that blocks approval, or tell the maintainer directly and note that on
the row.

### 3.2 Ask interactively
In an interactive run, ask one to three related questions per prompt, presenting the whole question set
INSIDE the prompt (decision needed, context, why it matters, options as the tool's own choices,
trade-offs, recommendation). Ask and wait before the final report.

After each answer: record it in the spec, resolve or rewrite the open question, apply the resulting
edits, re-check the affected rubric areas, and continue until no resolvable question remains.

### 3.3 Non-interactive exception
A run is non-interactive only when the environment explicitly has no human interaction channel. In a
genuinely non-interactive or interrupted run: leave questions explicitly `OPEN`, state the required
decision, use verdict `REVIEWED - OPEN QUESTIONS`, and recommend that the spec NOT be approved yet.

---
## Step 4: Finalize state and commit

For each reviewed spec confirm:
- Every finding is `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`, and every deferral meets the Fix Bar.
- The typed review record was written, carries `- Subject-Type: spec`, and PARSES cleanly.
- Every finding left `OPEN` or `DEFERRED` at or above the repository's gate threshold
  (`review_findings_gate.block_at`, default `high`) is raised in the spec as an open question that
  blocks approval and names the finding id.
- Resolved decisions are written into the spec with their rationale.
- The spec still specifies WHAT and WHY rather than dictating HOW.
- No `- Readiness:` field was added, no `- Status:` line was hand-edited, and `aw ipd lint` was never
  invoked against the spec.

### The transition (tool-authored, and now ATTESTED)

    aw specs set reviewed <id6> --message "<verdict>; <finding ids>"

`to-review -> reviewed` REQUIRES a conforming review record whose `Subject-Id` is that spec
(`attention_contract.TRANSITION_AUTHORITY["->reviewed"]`, enforced by one shared predicate consulted by
the setter and by `aw check`). So WRITE THE RECORD FIRST, then set the status. If you set first, the
setter refuses and names the missing record.

WHAT THAT ATTESTATION DOES AND DOES NOT PROVE, stated plainly because overselling it is the failure
mode: it proves a review OCCURRED and was RECORDED. It does not prove the reviewer noticed every flaw.
Spec `25kzda` Section 6.1 already states this limit for plans and it holds identically here.

`reviewed` means the review occurred. It does NOT mean approved. Only a human may approve a spec, with
`aw specs set approved <id6> --by-human`, and that gate is unconditional even under `--full-auto`.

### KNOW WHAT YOUR RECORD DOES TO APPROVAL

Filing a spec review record ARMS A LIVE GATE on that spec's approval. `aw specs set approved` consults
`plan_readiness.approval_refusals`, which consults `review_findings.subject_gating_blocks` keyed on the
artifact's `- Id:` bullet, and specs carry one. So an unfixed finding at or above the threshold, or a
record that fails to PARSE, will REFUSE that spec's approval, and that refusal has NO override by
design. This is intended. It also means a sloppy record blocks a maintainer's spec, so:

- fix findings rather than leaving them `OPEN` at or above the threshold, per the Fix Bar; and
- verify the record parses (Step 2.2) before you walk away.

### Append the history record
The setter writes the status history for you. Add a review annotation ONLY through the verb:

    aw specs note <id6> --message "/spec-review (<agent/model>): <verdict>; <finding IDs>"

Note the history section is NEWEST-FIRST. Use the real agent/model name, or `unknown`.

### Hardened-result commit
After revisions and decisions:
1. Commit only the reviewed spec files and the review record.
2. Use `spec-review: harden <scope> (revisions applied)`.
3. Never push.

Report a skipped, failed, or inapplicable commit exactly.

---
## Spec rubric

This is the LOCAL half of this workflow: the questions a spec must answer, which are not the questions
a plan must answer. For each item, verify the spec addresses it or justifies `Not applicable`.

### A. The problem is real and bounded
- The problem is stated as an observed condition, not as a solution in disguise.
- The motivation is evidenced (`path:line`, a measurement, an incident), not asserted.
- Non-goals exist and are specific enough to exclude something a reader would otherwise assume.
- A measured claim in the spec is CURRENT. Re-measure it; a stale count is a finding.

### B. Requirements are testable
- Every MUST requirement is verifiable by someone who did not write it: it names an observable
  condition, not an intention ("is robust", "is intuitive" are findings).
- MUST is separated from SHOULD / NICE-TO-HAVE, and the separation is honest rather than everything
  being MUST.
- Each requirement has a stable id so an acceptance criterion and a later plan can cite it.
- No requirement encodes an implementation choice the spec has no basis to fix (see D).

### C. Acceptance criteria COVER the requirements
- Every MUST requirement maps to at least one acceptance criterion. An uncovered MUST is UNDER-SCOPE.
- Every acceptance criterion maps back to a requirement. An orphan criterion is OVER-SCOPE or a
  missing requirement.
- Each criterion states the evidence that would satisfy it, concretely enough that a reviewer could
  refuse a false claim of completion.
- The criteria include the FAILURE and REFUSAL paths, not only the happy one.

### D. Decisions are recorded with rationale
- Every non-obvious choice is recorded as a decision with the alternative rejected and the basis.
- A decision that is genuinely open is an OPEN QUESTION, not a silently chosen default.
- The spec specifies WHAT and WHY; where it does constrain HOW, it says why that constraint is part of
  the requirement rather than a preference.
- Irreversible commitments (a published interface, a data migration, a deletion, anything another
  party may depend on) are called out AS irreversible.

### E. Open questions are dispositioned
- Each open question states who owns it, whether it blocks, and what evidence or decision would close
  it.
- A question the repository already answers is resolved and cited, not left open.
- A BLOCKING question is genuinely blocking; a nice-to-know marked blocking is a finding, because it
  stops the lifecycle for nothing.

### F. Scope, compatibility, and honest limits
- The scope statement excludes what neighbouring artifacts own, and names them.
- The migration/compatibility consequence of the change is stated, including for existing data and
  existing artifacts (grandfathering is a decision, not an omission).
- Security, privacy, and failure modes are addressed where they apply.
- The spec states its own HONEST LIMITS: what it does not prove, what remains non-deterministic, and
  what a consumer must not conclude from it. A spec claiming more than it delivers is a BLOCKER.

### G. It can be planned from
- Another qualified agent could author an implementation plan from this spec without inventing
  missing requirements or guessing a decision.
- Dependencies on other specs/artifacts are named with their ids, and the direction of each dependency
  is stated.
- Any release gate (`Blocks-Release`) is present in the front matter rather than only in prose.

---
## Verdict

Use the SHARED four-value vocabulary (`plan_readiness.VERDICTS`), defined in
`../plan-review/plan-review.md`, "Verdict and readiness":

- `APPROVE`, `APPROVE WITH REVISIONS APPLIED`, `REVIEWED - OPEN QUESTIONS`, `REJECT - NEEDS REPLAN`.

DO NOT REPORT A `Readiness:` FIELD VALUE for a spec (prohibition (a)). Report the verdict, and state
in prose whether the spec is ready for the human approval gate. Human approval is a separate step that
this workflow never performs and never simulates.

---
## Required final report

Do not issue the final report until the question loop is complete, unless the run is genuinely
non-interactive or interrupted. Use this exact order. Cite evidence as `path:line`. One row per
finding.

```markdown
## Spec Review - <spec name(s)>
Verdict: <APPROVE | APPROVE WITH REVISIONS APPLIED | REVIEWED - OPEN QUESTIONS | REJECT - NEEDS REPLAN>

### Review scope
ELIGIBLE:
- <spec file>

NOT REVIEWED:
- <spec file>: <reason>   # skipped CANDIDATES only; `- (none)` if none were skipped.

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| SR-001 | <level> | <scope> | <ref> | <path:line> | <finding> | C:<rating>; U:<rating>; S:<rating>; F:<rating>; Overall:<rating> | <FIXED|DEFERRED|OPEN|REPLAN> | <resolution or next step> |

### Edits applied
- `<spec file>` - `<section>`: <edit>

### Deferred and open
- `<finding ID>` - `<DEFERRED | OPEN>`:
  - Reason: <reason>
  - Remediation Risk: <Medium-High | High>
  - Axis: <complexity | usability | security | functionality>
  - Required decision or evidence: <need>
  - Consequence if unresolved: <impact>

### Record and transition
- Review record: `<path>` (Subject-Type: spec; parses clean: <yes | no>)
- Status transition: <to-review -> reviewed via aw specs set | not performed: reason>
- Approval gate armed by this record: <no gating finding | GATING: finding <ID> at <severity> will refuse approval until fixed>

### Commit result
- Pre-review snapshot: <hash | skipped unchanged | not applicable | failed: reason>
- Hardened result: <hash | not applicable | failed: reason>
- Push: not performed

### Specs reviewed and not reviewed
REVIEWED:
- `<spec file>`: <ready for human approval | not ready> - <reason>.
  Verdict: <verdict>.
  Open questions: all resolved interactively | <N open, blocks approval>.
  Required next step: <human approval | decision | replan | other>.

NOT REVIEWED:
- `<spec file>`: <exact reason>.   # skipped CANDIDATES only; `- (none)` if none were skipped.
```

The `### Specs reviewed and not reviewed` section MUST be the literal final output. Enumerate every
file from the Step 0 ledger. Print nothing after it.
