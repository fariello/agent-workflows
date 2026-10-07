# Plan Review (pre-execution plan / IPD reviewer)
Treat this file as the controlling instruction for reviewing a proposed plan
before implementation, then improving that plan in place.

Review planning documents only. Do not change code, tests, runtime
configuration, infrastructure, or production data. Editing a plan is not
executing it.

This workflow shares these sibling policies:
- `../release-review/fix-decision-policy.md`
- `../release-review/00-run-protocol.md`

This portable single-file variant is SERIAL BY DESIGN: it does not auto-fan-out into parallel audit
lanes (a lone portable file spawning subagents is awkward and not universally available). For a
multi-plan batch that should review plans in parallel, use `../plan-review-long/plan-review-long.md`,
which auto-engages the read-only audit-lane convention (`../release-review/00-run-protocol.md`) when the
scope ledger has 2 or more eligible plans. The two variants are otherwise kept in deliberate parity.

If either is absent, apply these rules from memory:
- Fix findings by default.
- Defer only when the fix itself has Medium-High or High Remediation Risk on
  complexity, usability, security, or functionality.
- Severity is for reporting only.
- Effort, time, cost, and tokens never justify deferral.
- Review through QA/QC, testing/regression, UI/UX, architect, software
  engineer, power user, novice, and stakeholder views.
- Apply security as a mandatory cross-cutting lens.

---
## Memory kernel
Re-read this before each step and before the final report:
1. Review plans only.
2. Verify claims from repository evidence.
3. Fix by default. Severity never decides.
4. Resolve open questions interactively when possible.
5. Never guess a human decision.
6. Preserve valid plan content and required structure.
7. Make at most two local commits. Never push.
8. The reviewed/not-reviewed enumeration is the literal final output.
9. A gate or interactive question MUST NOT assert or imply the verdict it precedes (readiness, approval, GO); it states what was found and asks what to do. The verdict is formed only from the reviewed work's evidence.

---
## Step 0: Scope and project contract
Complete this before judging or editing a plan.

### 0.1 Build the review-scope ledger
The ledger contains ONLY the plans explicitly named in the invocation, plus any
that the project's own documented eligibility rules add. Do NOT enumerate other
plans in the repository (e.g. everything in `pending/` or `executed/`) to build
the ledger. A "candidate" is a ledger entry: an explicitly named target, or a
plan a documented eligibility rule adds. A plan that was never a candidate is an
"incidental file" and MUST NOT appear in the ledger or the final report.

Classify each candidate as:
- `ELIGIBLE` - review it.
- `NOT REVIEWED` - a candidate skipped, with the exact reason (missing,
  unreadable, malformed beyond review, not a planning document, or wrong status
  per project rules). NOT REVIEWED NEVER lists a plan that was never a candidate.
  If the ledger is exactly the requested target(s) and none were skipped, the
  final NOT REVIEWED section is `(none)`.

Use project eligibility and status rules when present. Otherwise review an
explicitly requested plan unless it is missing, unreadable, malformed beyond
review, or not a planning document.

A file referenced only as evidence is not in scope unless explicitly added.

The final enumeration MUST contain every ledger CANDIDATE and no incidental file.

### 0.2 Discover controlling instructions
Read the applicable repository and directory-scoped instructions, guiding
principles, contributor rules, plan lifecycle, specification obligations, plan
templates, and the target plan.

Do not assume filenames.

If instructions conflict, use the project's precedence rules. If none resolve
the conflict, record an open question. Do not silently choose.

### 0.3 Discover the plan contract and implementation context
Determine:
- Plan location, structure, front matter, status lifecycle, approval rules,
  traceability, workflow history, and commit rules.
- Project type, languages, frameworks, production runtime and data store,
  deployment model, integrations, security model, and test stack.
- Domain invariants from specifications, principles, ADRs, accepted plans,
  code, tests, constraints, and authoritative conversation context.

Apply the rubric to the real production target.

If the plan changes behavior, policy, workflow, API, authorization, state, or
domain rules, require specification and documentation synchronization.

If no project principles exist, use these fallbacks and record that choice:
- Intuitive and self-documenting.
- General-case and configurable.
- KISS.
- Honest documentation.

---
## Step 1: Evidence and pre-review snapshot
For each eligible plan:
1. Read the whole plan.
2. List material files, requirements, issues, ADRs, APIs, schemas, tests, and
   behaviors it relies on.
3. Open the referenced evidence.
4. Verify material claims with `path:line` evidence:
   - Locate the cited construct by symbol, heading, section ID, or quoted string, treating the line number as a hint (spec `ipd-structure-and-linting` Section 10.2).
   - Disposition:
     - Anchor resolves and only the line moved: no finding, or at most one LOW batched finding per plan noting the drift.
     - Anchor does not resolve anywhere, or resolves to something that contradicts the claim: a real evidence finding at the severity of the claim it supports.
     - Bare `path:line` with no anchor that no longer matches: search for the described construct before judging, and record which case applied.
   - Costlier error: rejecting a citation the reviewer merely failed to re-locate is WORSE than under-reporting drift, because a review finding is durable and tracked while drift is not. Measured in this repository: backlog `88manw` recorded that plan `si24ia`'s review finding PR-305 rejected a correct spec section citation and substituted a wrong one, which subsequent readers propagated. The rule covers section or heading anchors in specs and docs, not only code symbols.
   - Git ref asymmetry: the same costlier error rule applies to git citations. The trigger is narrow: ONLY when a reviewer is about to declare that a branch, lane, or commit cited as evidence no longer exists. `git branch -a` answers a question about REFS while the evidence lives in OBJECTS. Before declaring lane or branch evidence unrecoverable, a reviewer must search dangling objects by subject (e.g. via `runner_shared.find_dangling_commits_by_subject` or `git fsck --connectivity-only`), and must record which check was run. Precedent: backlog `1ffh63` recorded that review finding PR-001 on plan `kl18sz` declared a replay source unsatisfiable on a refs-only reading and weakened V-01 to a 4-path substitute plus a synthetic fallback, while the finalize tip was resolvable and the real replay was LARGER than claimed. Limits: dangling objects are LOCAL to one checkout, are NOT cloned, and expire to gc; a resolving dangling commit is a legitimate evidence source and NEVER a durable archive, and a plan must not be written to depend on one persisting.
5. Record missing, stale, contradictory, or inaccessible evidence.
6. Do not infer unsupported implementation details.

If missing evidence prevents reliable review, file a finding or open question.

### Structural preflight (before semantic review)
For each eligible plan that is an agent-executable IPD, run the deterministic structural linter as
a GATE before you spend semantic effort:

    aw ipd lint --phase author --agent <plan-file>

Then, after all revision edits are applied (Step 2/3), re-run at the finalize checkpoint:

    aw ipd lint --phase review-finalize --agent <plan-file>

Only a `conforming` disposition proceeds. Exit `1` (a conformance error) is a distinct STRUCTURAL
finding that MUST be repaired before a passing verdict; exit `2` (the linter could not run) is a
hard stop, not a skip. INVOKE the linter; do not paraphrase or hand-simulate its checks. The linter
proves STRUCTURE and STATE only (heading order, `E-*`/`V-*` bijection, state legality, metadata,
and coarse count thresholds); it establishes nothing semantic (coverage, correctness, evidence
sufficiency, truthful blocking-classification, or conceptual density per E-item), so the semantic
review below remains fully required and separate. A passing count-based size lint does NOT
clear right-sizing; conceptual density must be evaluated in semantic review.

#### Orchestrator checklist row check and bounded repair loop (`IPD-S407`)
Beside `review-finalize`, for any plan whose own first `- Kind:` bullet reads `orchestrator`
(read from the plan's own first `- Kind:` bullet in front matter; never use a whole-file containment
scan like `grep -l 'Kind: orchestrator'`, which misclassifies child plans quoting the bullet such as
`m7gvuz`), the linter validates typed child-tracking row conformance (`IPD-S407`).

If `IPD-S407` violations are reported:
1. **Bounded repair loop:** Ask the agent to repair the checklist rows and re-run the check, up to
   an attempt budget of 2 (default 2 per `resolve_retry_budget(None) == 2`; the repository-policy tier
   of that precedence is unimplemented, backlog `dh3us4`).
2. **Verbatim refusal message:** The repair prompt MUST carry child 01's refusal message verbatim
   (which states the invariant, forbids satisfying it by deletion, and names both remedies: moving the
   step to a child with dependencies, or removing it if redundant).
3. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record
   (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording
   the attempt number, what the check reported, what changed, and the row count before and after
   (`rows: N -> M`) so repair by deletion is distinguishable from relocation.
4. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with violations unresolved, the
   plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:`
   is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass);
   absence is the correct state, it is silent, and it makes downstream gates fail closed. (The
   auto-approve predicate reads `- Readiness:` first; `IPD-M107` refuses unattested values).

(Only while the linter does not yet exist may a run record say `machine preflight unavailable:
bootstrap`; once `aw ipd lint` is available that exception no longer applies.)

#### Orchestrator review readiness (`IPD-S408`)
Beside `review-finalize`, for any plan whose own first `- Kind:` bullet reads `orchestrator`, check review readiness with `aw ipd coverage <id6>`.

If coverage findings are reported:
1. **Bounded repair loop:** Resolve each quoted finding by assigning it by id6 to a child in the `## Child IPDs` table or by adding a child plan and its row (never by deleting the checklist), up to an attempt budget of 2.
2. **Attempt logging:** Log every attempt into the current `## Round <n>` of the typed review record (`.aw/records/reviews/<...>.review.md`, append-only per round; not the workflow history), recording the attempt number, what `aw ipd coverage` reported, and what changed.
3. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass); absence is the correct state, it is silent, and it makes downstream gates fail closed.

`aw ipd set reviewed` refuses an orchestrator with unresolved coverage findings (Order 05), so the reviewer resolves the findings before setting the status.

### Pre-review commit
Before editing:
1. Inspect repository status.
2. Isolate the eligible plan files.
3. If any target plan is untracked or modified, commit those plan files
   verbatim as:

   `plan: pre-review snapshot of <scope>`

4. If all target plans are committed and unchanged, skip the snapshot.

Never stage unrelated files. Never amend, reset, rebase, discard user changes,
or push.

If Git is unavailable or a commit fails, continue only when safe and record the
reason. Do not bypass hooks or safety controls unless project rules permit it.

---
## Step 2: Review and revise
### 2.1 Apply all required views
Review against:
- The engineering rubric below.
- Project principles.
- Domain invariants.
- Plan goals and acceptance criteria.
- The eight personas.
- The security lens.

### 2.2 Record findings
Record each distinct actionable issue. Combine duplicate symptoms under one
root cause. Do not invent findings. A maintainer's sizing or splitting question is an
actionable FINDING to investigate by decomposition, never a signal to dismiss because the
size lint passed.

Classify each finding with:
- **Severity:** `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`.
- **Scope:** `IN-SCOPE`, `OVER-SCOPE`, or `UNDER-SCOPE`.
- **Area:** rubric or project rule.
- **Evidence:** `path:line`, plus the symbol or a quoted string, for example the symbol `mod.func_name` beside its path and line.
- **Remediation Risk:** complexity, usability, security, functionality, and
  overall.
- **Decision:** `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.

Write the findings to BOTH places:

1. The findings table in the final report (below).
2. A typed review record, `.aw/records/reviews/<...>.review.md`, using the same columns.

The record is what makes a severity readable by tooling. Before it, severity survived only as prose,
so a `HIGH` left unfixed gated nothing. This is a transcription of the classification you already
made, not a second classification.

Append a new `## Round <n>` for a re-review rather than editing an earlier round: the gate reads only
the CURRENT (last) round, so a finding you raised in round 1 and fixed in round 2 correctly stops
counting against the plan.

### 2.3 Remediation Risk and Fix Bar
Overall Remediation Risk is the highest applicable axis rating.

- **Low:** Local, understood, easy to verify, unlikely to harm behavior.
- **Medium:** Bounded uncertainty with a clear verification path.
- **Medium-High:** Material chance of significant complexity, usability harm,
  security weakness, or functional regression.
- **High:** Likely major harm, a foundational unresolved decision, or no safe
  fix from available evidence.

Fix every finding unless overall Remediation Risk is Medium-High or High.

Every deferral MUST state:
- Axis or axes.
- Why the risk reaches the threshold.
- Required decision or evidence.
- Consequence of leaving it unresolved.

Effort, time, cost, and tokens are never valid deferral reasons.

For over-scope, the default fix is removal or explicit deferral from the plan.
That is normally Low risk.

### 2.4 Revise the plan in place
Make surgical edits:
- Preserve valid content and required structure.
- Replace ambiguity instead of appending duplicate prose.
- Add missing guardrails, sequencing, acceptance criteria, tests, validation,
  specification updates, and traceability.
- Remove unsupported or gold-plated scope.
- Keep the plan concise and executable.
- Do not weaken valid requirements.

When a finding spans plans, fix it in the owning plan and cross-reference it
from dependent plans.

When a revision corrects a mechanism, ordering, or classification, the
correction is not complete until every other item in the plan that quotes or
depends on the replaced wording has been swept and reconciled. This sweep
is not limited to `V-*` items: check every item, field, and prose block
(`E-*`, `V-*`, findings, proposed changes, gates, scope paths) against the plan
as it now reads, not merely your own diff. Grep for distinctive tokens of the
superseded wording (e.g. `PHASE_COMMITTED_INCOMPLETE` in `u23gbn`, where round 3
corrected E-06 and V-06 but left V-02 demanding an impossible state). If a stale
sibling belongs to an already executed plan and cannot be edited in place,
record the contradiction in a dated `## Workflow history` note where readers
will find it.

If the approach is fundamentally unsound and cannot be repaired with bounded
edits, mark `REPLAN`, explain why, and describe the minimum shape of a sound
replacement. Do not invent decisions that require the human.

---
## Step 3: Resolve open questions
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

### 3.2 Ask interactively
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

In a genuinely non-interactive or interrupted run:
- Leave questions explicitly `OPEN`.
- State the required decision.
- Use verdict `REVIEWED - OPEN QUESTIONS`.
- Recommend `NO-GO`.

---
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

THE HISTORY-LINE PROSE IS NOT THE PRIMARY MACHINE SIGNAL. Downstream automation evaluates readiness using a three-way rule: a valid attested field decides; a corrupt field refuses outright with no fallback; and an absent field falls back to history prose, clearing the plan only if the newest history entry is a genuine review record with an approving verdict. Omitting the field leaves a clean plan that should have read `go-pending-approval` dependent on prose fallback instead of machine-attested clearance. Write exactly one of the three values, lowercase, with no extra words.

**Exception for exhausted orchestrator repair loop (`IPD-S407` / `IPD-S408` / R6):** If an orchestrator's
checklist repair loop or coverage repair loop exhausts its budget of 2 attempts unresolved, leave `- Readiness:` ABSENT
entirely. Do NOT write `- Readiness: no-go` or any other value; absence leaves the plan unclearable by the field and clearable by prose only on a genuine review record, which an exhausted R6 round has not produced, while honestly reflecting that no review verdict was reached.

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

---
## Engineering rubric
For each item, verify the plan addresses it or justifies `Not applicable`.

### A. Correctness and data integrity
- Dependent writes are atomic; retries and handlers are idempotent.
- Concurrency, uniqueness, ordering, and partial-failure risks are handled.
- Production data-store syntax, types, constraints, and migrations are valid.
- Public data, audit, and serialized formats preserve required history and
  compatibility when relevant.

### B. Security and privacy
- Identity is verified; authorization is default-deny and resource-scoped.
- Secrets are not hardcoded; trust-boundary inputs are validated.
- Queries, commands, files, uploads, and outbound calls are safe when present.
- Sensitive data collection, logging, exposure, retention, and errors are
  minimized.
- Privileged bypasses and abuse controls are justified when relevant.

### C. Architecture and operability
- The design uses existing canonical mechanisms and avoids duplicate paths.
- New dependencies, services, abstractions, and async work are justified.
- State, caching, time, retries, failure handling, observability, rollout, and
  recovery are explicit when relevant.
- The plan provisions for real needs, not hypothetical scale.

### D. Anti-regression and domain invariants
- Name each affected invariant and map it to a test.
- Preserve intended correct behavior unless an approved change fixes it.
- Add characterization coverage for risky refactors.
- Do not freeze accidental behavior that project policy says to replace.
- Treat unexplained behavior changes as blockers.

### E. Testing and verification
Require concrete tests for applicable happy, validation, authorization,
constraint, failure, rollback, retry, concurrency, integration, accessibility,
and compatibility paths.

Use production-equivalent dependencies where differences matter.

State exact validation commands, environments, and expected evidence.

### F. KISS, principles, and UX
- Prefer the smallest correct design and reuse existing mechanisms.
- Variation should be data or configuration when appropriate.
- Map the plan to each project principle with verifiable outcomes.
- Minimize user effort and define loading, empty, error, success, and recovery
  states when user-facing.
- Include keyboard, semantic, focus, naming, contrast, and assistive feedback
  when accessibility applies.
- Prevent silent failure.

### G. Plan executability
Verify the plan states:
- Problem, driver, goals, non-goals, scope, and exclusions.
- Acceptance criteria and ordered implementation steps.
- Target components and existing mechanisms to reuse.
- Dependencies, sequencing, and data/API/workflow effects.
- Security, privacy, migration, documentation, and specification effects.
- Validation, rollout or recovery when relevant.
- Assumptions, open questions, ownership, and follow-up work.
- An execution contract in the gate: resolved open questions, a scope fence, the hard-MUST
  honesty rule (paste the actual runner output), path-scoped commit and never-push, and the
  lifecycle transition (unconditional finalize obligation with conditional runner/executor ownership;
  flag both a hand-rolled `git mv` to `executed/` and an unconditional `aw ipd finalize` instruction).
- For an agent-executable plan: BOTH a top execution checklist AND an end verification/cross-check
  checklist that maps 1:1 with concrete per-item evidence. A weak or absent verification checklist
  (one that could let an agent claim completion without doing every step) is an UNDER-SCOPE finding.
- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. Criteria counting **stable code facts** (schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations. In contrast, a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts; neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer). A V-item must instead demand the behaviour pinned plus the mechanism that pins it, and must require re-derivation at execution time. (Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)
- **Canonical no-error-added proof shape vs. unsatisfiable exit-0 demands (evidence-feasibility convention):** When a plan demands proof that an advisory rule adds no error, the author must demand evidence that can actually be produced. The canonical proof requires two limbs:
  (a) a **registry severity assertion**, showing the rule id resolves through `check_engine.rule_spec` to the intended severity; and
  (b) a **gate-consequence measurement**, driving `artifact_core.drift_exit_code` with the finding list and pasting its return value as a contrastive pair--asserting the real finding list exits 1 (e.g. `drift_exit_code(drift) == 1` for `warning` or `error`) AND that the same finding list with its severity swapped to `info` exits 0 (e.g. `drift_exit_code([d._replace(severity="info") for d in drift]) == 0`). The pair is what localizes the exit code to the severity under test.
  Where the rule is live on the repository corpus, an author may also permit or prefer an optional third limb: a **per-rule count delta** from `python3 -m agent_workflows check all --agent` before and after, showing the new rule id as the only id whose count moved.
  **Anti-pattern to flag:** Demanding "a synthetic tree whose only finding is the new rule, on which `aw check` exits 0" is **unsatisfiable** for any severity other than `info`. In `artifact_core.drift_exit_code`, `info` is the only severity exempted (both `error` and `warning` exit 1; clean/empty trees and `info`-only trees exit 0). `warning` does NOT mean "cannot fail anything"; `error` and `warning` have identical gate consequence (both exit 1) and differ only in condition classification. Writing an exit-0 demand for a non-`info` rule forces the executor to either refuse the item or mis-register the rule as `info`, shipping a contract defect. Reviewers must flag an unsatisfiable exit-0 demand as an in-scope plan defect. Proofs must be behavioral; demanding a source census, caller count, or `read_text`/`inspect` search against `agent_workflows/*.py` is strictly prohibited by GUIDING_PRINCIPLES P16.
- **Runtime-demonstration reachability vs. unsatisfiable observation demands (reachability convention):** For each `V-*` item whose `Required evidence:` demands that the software be **observed** doing something (such as a run, a dispatch, a state transition, or a queue re-evaluation)—as distinct from items demanding a diff, a file's content, a test result, or a search result, which are reachable by construction—the reviewer must verify reachability. The reviewer must **name the code path** (by symbol, per the repository's citation convention) that would produce the demanded observation or **name the sibling `E-*`** that creates that path within the same plan. When neither exists, the reviewer must raise an **UNDER-SCOPE** finding and either add the `E-*` that makes the demonstration reachable or rewrite the demand down to what is observable, recording which remedy was chosen. This check costs one question per runtime-demonstration item and no separate investigation because the reviewer is already reading the cited symbols for rubric G.
  **Measured precedent to flag:** In `akzy45` E-03/V-03, the plan demanded that an item blocked on a prerequisite which later succeeds in the same run become runnable without `--retry-incomplete`. No such code path exists on either host: `requeue_interrupted` and the `if retry_incomplete:` branch both sit outside the dispatch loop in `oc_runipd.run_queue` and `agy_runipd.run_queue`, with zero re-queue calls inside either dispatch loop. That plan was reviewed and approved, and its review round had already re-verified E-03 and corrected its premise once without catching that the surviving demonstration was unreachable. Review is the only enforcement surface; no mechanical lint rule is attempted because verifying reachability requires semantic reading of evidence demands and code paths.
- **Right-sizing and conceptual density (per E-item):** Evaluate whether each E-item addresses exactly **one concern** and is **executable in one focused pass**. A passing count-based size check (`aw ipd lint`) measures only structural count (>18 E-leaves / >5 groups), NOT conceptual density. For each IPD and each E-item, ask:
  (a) Does one E-item name multiple distinct deliverables or touch multiple independent code regions/files?
  (b) Does it bundle multiple independent test-surfaces (would it need several unrelated V-items)?
  (c) Could it be executed and verified as two or more independent passes?
  (d) Would a faster/weaker model lose focus/context executing it as one item?
  If YES to any diagnostic question, recommend splitting into smaller child IPDs (an UNDER-SCOPE / REPLAN finding)—a passing count-based size lint does NOT clear this.
- **Maintainer sizing signals:** A maintainer's sizing or splitting question is an actionable FINDING to investigate by decomposition, never a signal to dismiss because the size lint passed.

Another qualified agent or developer must be able to execute the plan without
inventing missing architecture.

---
## Severity and scope
Severity is for reporting only:
- **BLOCKER:** likely data loss, breach, normal-path failure, silent invariant
  violation, or core-principle violation.
- **HIGH:** material reliability, security, accessibility, maintainability, or
  required-coverage gap.
- **MEDIUM:** real gap on a non-critical path or uncommon condition.
- **LOW:** polish or small clarity improvement.

LOW and MEDIUM findings are fixed by default too.

Scope:
- **IN-SCOPE:** flaw in proposed work.
- **OVER-SCOPE:** not traceable to a driver or requirement.
- **UNDER-SCOPE:** required capability, guardrail, test, migration, or
  documentation is missing.

---
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

---
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
