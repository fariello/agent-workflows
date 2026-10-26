# Check S7: Finalize State and Commit

The verdict outputs (`- Readiness:`, the status move to `reviewed`, and the one verdict-bearing history entry) are written in this step only and exactly once per review (MD-15, Section 7.2).

Write `- Review-Depth: <tier>` in the plan's front matter beside `- Readiness:` (spec Section 7.2; the field is registered by Order 02 `gv3smb`, which is why this plan carries `- Item-Dependencies: executed:gv3smb`: until it lands, a plan carrying the field fails `aw ipd lint` with `IPD-M103` unknown field).

In a runner review, the final report is the typed review record (`.aw/records/reviews/<...>.review.md`), not chat text (spec Section 4.3 row "Required final report").

The final commit subject MUST start with `plan-review:`.

## Step 4: Finalize state and commit
For each reviewed plan confirm:
- Every finding is `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.
- Every deferral meets the Fix Bar.
- The typed review record was written, and every finding left `OPEN` or `DEFERRED` at or above the
  repository's gate threshold (`review_findings_gate.block_at` in `.aw/config/project.json`, default
  `HIGH`) is ALSO raised in the plan as an open question carrying `- Blocking: yes` and
  `- Finding: <ID>` naming that finding. `check.review-finding-unescalated` enforces this, and the
  escalated question is then caught by the existing lint gate at EVERY checkpoint (not only
  `pre-execution`, since 2026-09-08), so an unfixed serious
  finding actually stops execution instead of merely being reported.

  This does NOT contradict "Severity is for reporting only" below. Severity still does not decide
  whether to FIX anything: the Fix Bar alone does that, on Remediation Risk. Severity decides only
  whether a finding you have ALREADY decided not to fix must be surfaced as blocking. Reporting rule
  unchanged; escalation is about visibility of an unfixed finding, not about the fix decision.
- Resolved decisions are written into the plan.
- Required specification and documentation work is included.
- Tests and validation map to affected invariants.
- The plan does not claim execution.
- The plan's gate carries an execution contract (resolved open questions, a scope fence,
  the hard-MUST "paste the actual runner output" honesty rule, path-scoped commit and
  never-push, and the lifecycle transition with conditional runner/executor ownership;
  a gate instructing a hand-rolled `git mv` to `executed/` or unconditionally instructing
  the executor to run `aw ipd finalize` is a finding to fix). If any element is missing,
  ADD it as an in-place revision and record it as a finding.
- SCOPE-FENCE WORDING (2026-09-01 maintainer ruling): a fence is a DECLARATION so the runner can
  tell afterwards whether an out-of-scope file was edited or an in-scope file was not. It MUST NOT
  instruct the executor to STOP over a scope question. Do NOT flag a plan for lacking a
  "STOP and report" clause, and DO flag one that HAS it for the out-of-scope-edit case: the earlier
  mandate propagated that wording into 224 executed plans and it contradicts the work done to stop
  `aw oc run` stranding unfinished turns. The correct requirement is that an out-of-scope edit be
  made and then JUSTIFIED, which `aw ipd finalize` already enforces by refusing to complete without
  a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path.
  A stop directive for a genuinely unsafe condition (an unresolvable concurrent-edit conflict, or a
  prerequisite whose symbols are absent) is a DIFFERENT case and remains correct.
- For an agent-EXECUTABLE plan (an IPD or similar with actionable steps), the CREATOR authored
  BOTH the top execution checklist AND the end verification/cross-check checklist, and you (the
  REVIEWER) have assessed both: the execution checklist covers every required action, decision,
  deliverable, and validation; the verification checklist maps 1:1 to it and demands CONCRETE
  per-item evidence; and it is specific enough to catch an agent claiming completion without
  having done every step. A missing or weak checklist is an UNDER-SCOPE finding you ADD or
  strengthen in place (like the execution-contract rule above).

If the project uses `Status`, set it to `reviewed` unless its contract requires
another review-complete value.

`reviewed` means the review occurred. It does not mean approved, GO, ready to
execute, or executed. Only the human or project approval process may approve.

### Write the structured `Readiness` field (REQUIRED output of the review)

Write your readiness into the plan's front matter as a machine-readable field, beside
`Status`:

```markdown
- Readiness: <go | go-pending-approval | no-go>
```

Map it from the readiness vocabulary you already use below:

| Readiness you report | Field value |
|---|---|
| GO | `go` |
| GO - PENDING HUMAN APPROVAL | `go-pending-approval` |
| NO-GO | `no-go` |

THE HISTORY-LINE PROSE IS NOT THE PRIMARY MACHINE SIGNAL. Downstream automation evaluates readiness using a three-way rule: a valid attested field decides; a corrupt field refuses outright with no fallback; and an absent field falls back to history prose, clearing the plan only if the newest history entry is a genuine review record with an approving verdict, which is why IPD-M113 now refuses the absence at `reviewed` upstream of that fallback. Omitting the field leaves a clean plan that should have read `go-pending-approval` dependent on prose fallback instead of machine-attested clearance. Write exactly one of the three values, lowercase, with no extra words.

**Exception for exhausted orchestrator repair loop (`IPD-S407` / `IPD-S408` / R6):** If an orchestrator's
checklist repair loop or coverage repair loop exhausts its budget of 2 attempts unresolved, leave `- Readiness:` ABSENT
entirely. Do NOT write `- Readiness: no-go` or any other value; absence leaves the plan unclearable by the field and clearable by prose only on a genuine review record, which an exhausted R6 round has not produced, while honestly reflecting that no review verdict was reached.

**Runner re-review note:** When a runner re-reviews a previously reviewed or approved plan (`aw oc review <id6> --yes` or `aw agy review <id6> --yes`), the plan arrives in the review lane demoted to `to-review` with `- Readiness:` stripped. The review turn must write a fresh `- Readiness:` line to satisfy the post-review gate; an absent or untouched readiness line fails the re-review with `fail-gate`.

Append or update:

```markdown
## Workflow history
- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>
```

Use the real agent/model name, or `unknown`. The message MUST lead with exactly one
verdict from the closed list; readiness words belong in `- Readiness:`, not in
place of the verdict; a non-review act recorded while the plan is `reviewed`
(descope, OQ answer, re-check) uses its own label (`re-scope`, `readiness re-check`)
and never `reviewed` or `/plan-review`.

Note the history section is NEWEST-FIRST: a new record goes directly under the
`## Workflow history` heading, so the first record is the most recent.

### Hardened-result commit
After revisions and interactive decisions:
1. Commit only reviewed plan files and any required review record.
2. Use:

   `plan-review: harden <scope> (revisions applied)`

3. Never push.

Report a skipped, failed, or inapplicable commit exactly.

## Verdict and readiness
Verdict describes review outcome. Readiness is separate.

Use one verdict:
- **`APPROVE`** - no revisions needed, no open questions, valid deferrals only.
- **`APPROVE WITH REVISIONS APPLIED`** - findings fixed, no open questions,
  valid deferrals only.
- **`REVIEWED - OPEN QUESTIONS`** - review completed but decisions remain.
- **`REJECT - NEEDS REPLAN`** - approach is unsound and not repairable with
  bounded edits.

Readiness (human approval is a SEPARATE step from the review verdict; a reviewed,
clean plan is `GO - PENDING HUMAN APPROVAL`, never a bare `NO-GO`; reserve `NO-GO`
for genuine not-ready conditions):
- **GO:** verdict is `APPROVE` or `APPROVE WITH REVISIONS APPLIED`, all questions
  are resolved, no unfixed BLOCKER or HIGH remains, AND the human has approved
  (`Status: approved`). Cleared to proceed.
- **GO - PENDING HUMAN APPROVAL:** same clean bar as GO (right verdict, no open
  questions, no unfixed BLOCKER/HIGH) but the human sign-off has not happened yet.
  This is the positive, correct readiness for a plan that passed review and only
  awaits approval. It is NOT a failure state.
- **NO-GO:** genuine not-ready: an unresolved BLOCKING open question, any unfixed
  BLOCKER/HIGH, or a `REVIEWED - OPEN QUESTIONS` / `REJECT - NEEDS REPLAN`
  verdict. NOT used merely because a clean plan lacks a signature.

A plan may be `Status: reviewed` and be `GO - PENDING HUMAN APPROVAL` (passed,
awaiting sign-off); it is only `NO-GO` when a genuine not-ready condition remains.

A NON-BLOCKING open question does NOT make a plan `NO-GO`. Maintainer ruling of
2026-09-10 (plan `qhy3i3` OQ-01), which changed the first `NO-GO` condition above
from "any open question" to an unresolved BLOCKING one. The reasoning generalizes:
the `- Blocking:` flag exists precisely to record which questions must stop work,
so treating blocking and non-blocking questions alike discards the distinction the
field was created to carry, and under the former literal reading the flag had
almost no consequence. Measured scale behind the ruling: 43 of 104 pending plans
carried ONLY non-blocking questions, so the literal reading was holding 43 plans
for reasons their own authors had judged non-stopping. The accepted cost, recorded
because the maintainer was shown it: a question mislabelled `Blocking: no` when it
truly does block will no longer hold its plan back, so mislabelling is now the
single point of failure, and it is visible in the plan itself.

### A `NO-GO` is RE-EVALUABLE

A `NO-GO` records a MOMENT, not a permanent condition. When the cause it was set
for is removed, the refusal must state a reason that is STILL TRUE rather than one
that is spent. Re-evaluate with:

```sh
aw ipd recheck-readiness <id6>            # preview the per-condition verdict
aw ipd recheck-readiness <id6> --apply    # write, when every condition is clear
```

The verb RECOMPUTES the three `NO-GO` conditions above with the shipped predicates,
reports each one individually with its reason, and writes only when all three are
clear. Four properties bound it, and they are what make it something an agent may
run at all:

- It can reach ONLY `GO - PENDING HUMAN APPROVAL`. **Only a review may set `GO`**,
  and `GO` still requires human approval. The verb refuses an absent field (absence
  means no review recorded a signal, and minting a value would assert a review that
  never happened), an out-of-vocab field, and any readiness that is not `NO-GO`.
- It refuses a plan in a terminal disposition (`executed/`, `superseded/`, `not-executed/`),
  because a terminal plan's `NO-GO` is an accurate record of why it was retired.
- It RECORDS its computed evidence in the plan's `## Workflow history`, labelled a
  readiness re-check and containing no verdict token, so it is never read as a
  review and a reader can audit the claim without re-running anything.
- It re-checks; it does NOT re-review. No finding is re-derived and no plan content
  is re-critiqued, so a plan needing fresh critique still needs `/plan-review`.

## Required final report
Do not issue the final report until the question loop is complete, unless the
run is genuinely non-interactive or interrupted.

Use this exact order. Cite evidence as `path:line`. Use one row per finding.

```markdown
## Plan Review - <plan name(s)>
Verdict: <APPROVE | APPROVE WITH REVISIONS APPLIED | REVIEWED - OPEN QUESTIONS | REJECT - NEEDS REPLAN>

### Review scope
ELIGIBLE:
- <plan file>

NOT REVIEWED:
- <plan file>: <reason>   # skipped CANDIDATES only; `- (none)` if none were skipped. Never list a plan that was never a candidate.

### Findings
| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | <level> | <scope> | <ref> | <path:line> | <finding> | C:<rating>; U:<rating>; S:<rating>; F:<rating>; Overall:<rating> | <FIXED|DEFERRED|OPEN|REPLAN> | <resolution or next step> |

### Edits applied
- `<plan file>` - `<section>`: <edit>

### Deferred and open
- `<finding ID>` - `<DEFERRED | OPEN>`:
  - Reason: <reason>
  - Remediation Risk: <Medium-High | High>
  - Axis: <complexity | usability | security | functionality>
  - Required decision or evidence: <need>
  - Consequence if unresolved: <impact>

### Commit result
- Pre-review snapshot: <hash | skipped unchanged | not applicable | failed: reason>
- Hardened result: <hash | not applicable | failed: reason>
- Push: not performed

### Plans reviewed and not reviewed
REVIEWED:
- `<plan file>`: <GO | GO - PENDING HUMAN APPROVAL | NO-GO> - <reason>.
  Verdict: <verdict>.
  Open questions: all resolved interactively | <N open, blocks GO>.
  Required next step: <approval | decision | replan | other>.

NOT REVIEWED:
- `<plan file>`: <exact reason>.   # skipped CANDIDATES only; `- (none)` if none were skipped. Never enumerate plans that were never candidates (e.g. the executed/ dir).
```

The `### Plans reviewed and not reviewed` section MUST be the literal final
output.

Enumerate every file from the Step 0 ledger. Print nothing after it.
