# Spec: Runner-enforced, depth-scaled plan review

- Date: 2026-10-17
- Status: draft
- Id: k3yx72
- Author: aw specs new
- Scope: Replace single-turn /plan-review with runner-enforced discrete steps: proofread, complexity-scaled review depth, AW-REVIEW re-review marker, split step, durable citations; retire plan-review-long
- Set: revsteps

> DRAFT DESIGN SUMMARY. This spec currently holds the reviewed design summary, not yet the full
> normative spec. It will be rewritten in place after the multi-model design review (research Set
> `revsteps`, prompt `y6vfto`, reconciliation `vcg8mz`) is reconciled.

## 0. Terms

| Term | Meaning in this document |
| --- | --- |
| Plan, IPD | An Implementation Plan Document under `.aw/records/plans/`. It carries execution items (`E-*`) and validation items (`V-*`), and every `E-*` has a matching `V-*` (the E/V bijection). |
| Plan Set, orchestrator | Plans that share a `- Set:` value. The Order-00 plan is the orchestrator. It tracks its child plans and carries no work of its own. |
| Runner | The `aw oc run` (OpenCode) and `aw agy run` (Antigravity) drivers. Their shared logic is in `agent_workflows/runner_shared.py`. |
| Turn, session | A turn is one prompt sent to an agent and the agent's reply. A session is a conversation that keeps its context across turns. Both runners can already resume a session. |
| Review record | The typed findings file under `.aw/records/reviews/` that `/plan-review` writes today. It is organized in `## Round <n>` sections. |
| `- Readiness:` | The review verdict field (`go`, `go-pending-approval`, `no-go`). Only the review may write it. The runner's auto-approve logic reads it. |
| Fix Bar | The existing rule in `.aw/system/workflows/release-review/fix-decision-policy.md`: fix every finding by default, and defer a fix only when the fix itself carries Medium-High or High risk. |
| Proofreading instructions | The technical-artifact proofreading prompt, currently at `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md` (prompt `wcisgc`). |
| Depth | The review level for one plan: `simple`, `standard`, or `complex`. |
| Floor | The minimum depth that the runner computes from measurable plan properties. |

## 1. Goal

Replace the single-turn `/plan-review` with a sequence of discrete review steps:

- The runner sends each step as its own prompt, and it verifies the result of each step before it
  sends the next one.
- The review depth scales with the plan's complexity.
- The runner computes the floor. The reviewing agent may raise the depth, but it may lower the depth
  below the floor only with a recorded reason.
- Every review starts by proofreading the plan against the proofreading instructions.
- A free-form agent that runs `/plan-review` follows the same steps from a checklist.

The problems this solves:

1. **Plan text that a reader must interpret.** The proofreading pass removes shorthand, vague
   requirements, and unstated conditions before the semantic review reads the plan.
2. **The same review effort for every plan.** A plan with five items and a plan with forty items
   now receive the same review. `/plan-review-long` was intended to review complex plans more
   deeply, but it does not. It differs from `/plan-review` only in two ways: it loads one step file
   at a time, and it uses parallel read-only audit lanes for batches of two or more plans.
3. **Reviews that the runner cannot verify.** Today one review turn does all of the work. The runner
   can check only the final result.
4. **Code citations that become wrong.** Pending plans, specs, and open backlog items currently
   contain 166 `path:line` citations across 23 files. A line number stops matching when an unrelated
   edit lands in the cited file. This happens often, because many artifacts wait in the queue at the
   same time.

## 2. Scope

In scope:

- The plan review workflow (`/plan-review`) and the runner's review action for plans and plan Sets.
- The complexity assessment, the floor, and the depth levels.
- The split of an over-complex plan into a plan Set.
- The re-review signal and the re-review loop.
- A durable citation format and a resolver that checks it.
- Retirement of `/plan-review-long`.
- Pointers in the records READMEs and in `AGENTS.md` that direct agents to the artifact rules.

Out of scope:

- Spec review (`/spec-review`). It is deferred. It can reuse the step machinery later.
- Backlog review. Backlog items receive no review.
- A writing standard that agents apply while they draft. The proofreading instructions apply only at
  review time. A separate writing-instructions draft is not adopted.
- Records that are already executed or otherwise historical. Those records keep their existing
  citations and their references to `/plan-review-long`.

## 3. Decisions already made by the maintainer

| ID | Decision |
| --- | --- |
| MD-1 | The runner computes the floor. The agent may raise the depth. The agent may lower it below the floor only with a recorded reason. |
| MD-2 | A plan that should be a Set is split in a separate split step after a `no-go` verdict. The new plans return to the review queue. No human approval is required. |
| MD-3 | The agent signals a re-review with a marker line in its reply: `AW-REVIEW: AGAIN` or `AW-REVIEW: DONE` (Section 8). The runner adds its own change triggers. The loop stops after two re-review rounds. |
| MD-4 | `/plan-review-long` is retired. |
| MD-5 | The durable citation format (Section 7) is adopted, starting with plans. |
| MD-6 | All agent steps of one review run in one agent session. |
| MD-7 | `/plan-review` becomes a checklist that references step files, so a free-form review and a runner review use the same instructions. |
| MD-8 | The final proofreading of review edits covers only the passages that the review changed. |

## 4. The review sequence

The runner performs S-01 itself. It sends S-02 through S-07 to one agent session, in order. After
each agent step, the runner checks that step's postcondition. If a postcondition fails, the runner
stops the review, records the reason in the run records, and leaves the plan at `to-review`.

| Step | Actor | Action | Postcondition that the runner checks |
| --- | --- | --- | --- |
| S-01 Snapshot and structure | Runner | Make the pre-review commit. Run `aw ipd lint`. For an orchestrator, run `aw ipd coverage`. Compute the floor (Section 5). | The lint and coverage results and the floor are recorded in the run records. |
| S-02 Proofread | Agent | Apply the proofreading instructions to the plan. For a Set, apply them to every plan in the Set. | The edit passes the wording-only check (Section 4.1). The proofreading change summary and issue list are recorded in the current review round. |
| S-03 Assess complexity | Agent | Rate the plan `simple`, `standard`, or `complex`, and give the reason. | The rating is at or above the floor, or a reason for the lower rating is recorded. The runner writes the final depth to the plan as `- Review-Depth:`. |
| S-04 Review steps | Agent | Run each review step that the depth requires (Section 6). Each review step is one prompt. | Each required review step added its own section to the current review round. |
| S-05 Resolve open questions | Agent | Resolve open questions from repository evidence. Mark each remaining question `Blocking: yes` or `Blocking: no`. | Every open question carries a `Blocking:` value. |
| S-06 Re-review decision | Agent and runner | The agent ends its reply with the marker line (Section 8). The runner evaluates its own triggers. | The marker line is valid. The runner either starts a re-review round or continues to S-07. |
| S-07 Verdict and finalize | Agent | Write `- Readiness:`. Perform the existing finalize actions: the status transition through `aw ipd set`, the workflow-history line, and the commit. | The `- Readiness:` value is valid. The status transition is legal. `aw ipd lint` conforms. |

The re-review decision (S-06) comes before the verdict (S-07). This order means that the verdict is
always the last edit, so no review edit can land after the verdict that it would make out of date.

Every agent step that edits the plan ends with this instruction: "Make sure that every edit you made
in this step conforms to the proofreading instructions." This instruction is the limited final
proofreading (MD-8).

In a runner review, no human is available, so S-05 follows the existing non-interactive rule in
`plan-review.md`: an unresolved question stays open, and the plan receives `no-go`. In a free-form
review with a human present, S-05 asks the human, as `/plan-review` does today.

### 4.1 Wording-only check for S-02

The runner parses the plan with the existing IPD parser (`agent_workflows/ipd_lint.py::parse`)
before and after S-02. The runner refuses the step if any of the following changed:

- A front-matter metadata value.
- The list or order of H2 headings.
- The set of `E-*` and `V-*` ids, or the checkbox state of any of them.
- The set of open-question ids, or any `Blocking:` value.
- Lint conformance. The plan must still conform after the step.

A changed requirement word (`must`, `must not`, `should`, `may`) does not cause a refusal. The
runner records the change as a re-review trigger (Section 8), because the proofreading instructions
forbid a change of requirement force without an established basis.

Limit: this check proves that the plan structure was preserved. It cannot prove that the prose
improved.

## 5. The floor

The runner computes the floor from measurable plan properties. The thresholds below are proposed
initial values. They become configuration in `.aw/config/project.json` so that they can be tuned
after use.

| Floor | Condition (proposed) |
| --- | --- |
| `complex` | At least one of: the plan exceeds the size-lint thresholds in `agent_workflows/ipd_schema.py` (more than 18 E-leaves, or more than 5 task groups); the plan is an orchestrator; `- Scope-Paths:` names a `.spec.md` file; `- Work-Kind:` is `security`. |
| `standard` | The plan is not `complex`, and at least one of: more than 5 E-leaves; more than 3 `- Scope-Paths:` entries; `- Scope-Paths:` entries span more than one top-level directory. |
| `simple` | All other plans. |

The agent's S-03 rating is final when it is at or above the floor. A rating below the floor is
accepted only with a written reason. The runner records the floor, the rating, and any reason in the
review record and in the run records that `aw runs` shows.

## 6. Review steps by depth

Each review step has one step file and is sent as one prompt.

| Step | Purpose | `simple` | `standard` | `complex` |
| --- | --- | --- | --- | --- |
| R1 References | Run the citation resolver (Section 7). Correct each broken citation, or record it as a finding when the correct target cannot be established. | Yes | Yes | Yes |
| R2 Executability | Check the E/V bijection, the scope, and the dependencies. Check that every `V-*` item demands concrete evidence. | Yes | Yes | Yes |
| R3 Security | Apply the security lens. The short form checks only secrets, trust-boundary input validation, and destructive or irreversible actions. The full form applies all of rubric section B in `plan-review.md`. | Short form | Full | Full |
| R4 Engineering rubric | Apply rubric sections A and C to G in `plan-review.md` (correctness and data integrity, architecture and operability, invariants, testing, KISS and UX, executability). | No | Yes | Yes |
| R5 Personas | Apply the eight reviewer personas: QA/QC, testing and regression, UI/UX, architect, software engineer, power user, novice, and stakeholder. | No | No | Yes |
| R6 Decomposition | Decide whether the plan should become a plan Set. A recommended split produces a `no-go` verdict and a proposed breakdown (Section 9). | No | No | Yes |
| R7 Cross-plan | Check consistency across the plans of a Set. | Sets only | Sets only | Sets only |

The step files reuse the existing content of `plan-review.md`: its rubric, the Fix Bar, the severity
levels, and the findings rules. The redesign does not invent a new rubric.

Number of agent prompts per review, without re-review rounds: `simple` 8 (S-02, S-03, R1 to R3,
S-05, S-06, S-07), `standard` 9, and `complex` 11. R7 adds one prompt for a Set.

## 7. Durable citation format

A citation must remain valid through unrelated edits, and it must fail visibly when its target
changes.

| Target | Form | What makes it invalid |
| --- | --- | --- |
| Python code | `path::Name` or `path::Class.method` | A rename or deletion of that symbol. |
| Markdown | `path#Heading text`, with the exact heading text | A change to that heading's text. |
| Records | `<id6>`, `<id6> R-3`, `E-04`, `D153`, each with a descriptive name | Nothing. These ids do not change. |
| Text with no named symbol | `path` plus a short exact quoted string that occurs exactly once in the file | An edit to that string. |

A resolver in `aw check` validates every citation in a plan at the current commit. Review step R1
runs the resolver. `aw ipd begin` (the start of plan execution) also runs it (see OQ-3).

Line numbers remain allowed only inside pasted output, such as a traceback or test output, where the
line number is the reported fact. The lint rule for unanchored citations (`IPD-C801`) changes to
flag any line-number citation outside pasted output. The rule is advisory at first. It becomes an
error for new plans after a cutover date.

Limit: exact symbol resolution is planned for Python only. For other languages, the resolver falls
back to a text search for the symbol name.

Migration: review step R1 corrects the existing 166 citations as each plan passes review. No bulk
rewrite is planned.

## 8. Re-review signal and loop

### 8.1 The agent's signal

In S-06, the agent must end its reply with exactly one of these lines, alone on the last non-empty
line of the reply:

```text
AW-REVIEW: AGAIN
AW-REVIEW: DONE
```

The runner applies these rules:

1. The runner reads only the last non-empty line of the reply. The marker text anywhere else in the
   reply has no effect. This rule prevents a quotation or a negation such as "no AW-REVIEW: AGAIN is
   needed" from counting as a request.
2. The comparison ignores leading and trailing whitespace. It is otherwise exact and case-sensitive.
3. A missing, malformed, or truncated last line is a protocol failure. The runner treats a protocol
   failure as `AW-REVIEW: AGAIN`, so a lost signal causes an extra review and never a skipped one.
4. The runner extracts the agent's text from host output with the existing shared extractor
   (`agent_workflows/runner_shared.py::probe_reply_text`). The parsing follows the pattern of the
   existing orchestrator probe (`agent_workflows/runner_shared.py::classify_probe_reply`), which
   already requires an exact sentinel line.

### 8.2 The runner's own triggers

The runner also starts a re-review, whatever the agent's signal says, when any of the following
changed between S-01 and S-06:

- `E-*` or `V-*` items were added or removed.
- `- Scope-Paths:` or `- Item-Dependencies:` changed.
- A requirement word changed (Section 4.1).

The agent can cause a re-review. The agent cannot suppress a runner trigger.

### 8.3 The loop

A re-review round reruns the S-04 review steps for the plan's depth, and then S-05 and S-06. The
runner gives the agent the diff of the plan since the previous round, and it instructs the agent to
limit the review to the changed sections and the sections that depend on them.

The runner allows at most two re-review rounds. If S-06 of the second re-review round still produces
a re-review (from the agent's signal or from a runner trigger), the runner skips further rounds. In
S-07 the agent must then write `no-go`, and the runner records the reason "re-review limit reached".

## 9. Split step

When R6 recommends a split and the verdict is `no-go`, the runner schedules a split step:

1. An agent creates the new plans with `aw ipd scaffold`, from the breakdown that R6 recorded: an
   orchestrator at Order 00, and children at Order 01 and above.
2. The runner retires the original plan to `.aw/records/plans/superseded/`, with a `RETIRED` header
   that names the new Set.
3. The new plans enter the review queue at `to-review`. Each new plan receives its own full review.

The review never approves plans that it wrote. No human approval is required (MD-2). The new plans
inherit the original plan's `- From-Backlog:`, `- From-Spec:`, and `- Blocks-Release:` values (see
OQ-4).

## 10. The new `/plan-review`

`/plan-review` becomes a short checklist that points to step files under
`.aw/system/workflows/plan-review/steps/`. A free-form agent follows the checklist. The runner sends
the same step files as its prompts, so both paths use one set of instructions. Example:

```text
Do each of the following in turn:
- [ ] S-01: Run `aw ipd lint` and `aw ipd coverage` on <plan>. Make the pre-review commit.
- [ ] S-02: Read and execute steps/proofread.md on <plan>.
- [ ] S-03: Read and execute steps/assess-complexity.md. Record the depth.
- [ ] S-04: For each review step that your depth requires, read and execute steps/<step>.md.
- [ ] S-05: Read and execute steps/resolve-questions.md.
- [ ] S-06: Read and execute steps/rereview.md.
- [ ] S-07: Read and execute steps/finalize.md.
```

In a free-form review, nothing enforces the checklist. The runner is the enforcement point, by
design.

The proofreading instructions (prompt `wcisgc`) move to `steps/proofread.md`, with two adaptations:

1. Section 6 of the proofreading instructions ("Handle unresolved issues visibly") uses the plan's
   existing open-question mechanism instead of an inline "Unresolved" annotation: an entry in the
   plan's open questions with `- Blocking: yes` or `- Blocking: no`. Lint rule `IPD-Q501` and the
   runner already read these entries.
2. Section 5 of the proofreading instructions ("Check references, coordination, and consistency")
   uses the citation format in Section 7 of this document.

The review record format changes so that each review step adds its own subsection inside the current
`## Round <n>`. The runner checks for these subsections in S-04. This change amends
`.aw/records/reviews/README.md`.

## 11. Work breakdown (proposed Set `revsteps`)

One spec comes first. The plans graduate from the approved spec.

| Order | Work | Depends on |
| --- | --- | --- |
| Spec | One spec that defines Sections 4 to 10. It amends spec `25kzda` (the runner contract; the review action becomes multi-step) and Section 10.2 of the IPD spec (citations). | None |
| 00 | Orchestrator for the Set. It holds child tracking only. | All children |
| 01 | Step files, the proofreading adaptation, the new `/plan-review` checklist, and the review record subsections. | Spec |
| 02 | The `- Review-Depth:` field in `ipd_schema.py` and lint, and the floor computation with its configuration. | Spec |
| 03 | The citation resolver in `aw check`, the `IPD-C801` change, and the `aw ipd begin` check. | Spec |
| 04 | The runner's multi-step review session in `runner_shared.py` for both hosts: step order in one session, the postcondition after each step, and the S-02 wording-only check. | 01, 02, 03 |
| 05 | The re-review marker parser, the runner triggers, and the two-round limit. | 04 |
| 06 | The split step and the requeue of the new plans. | 04 |
| 07 | Retirement of `/plan-review-long`: remove the workflow, its command shims, its entry in `.aw/system/workflows/index.md`, and its installer entries. Update current documentation (`README.md`, `ARCHITECTURE.md`, `docs/`) and tests. | 01, 04 |
| 08 | Reinforcement: the records READMEs describe the citation format and the review steps. `AGENTS.md` gains one line that tells agents to read a tree's README before they create or edit an artifact in that tree. | 01, 03 |

## 12. Validation

- Each child plan's own `V-*` items, with the actual test-runner output pasted as evidence.
- An end-to-end runner test with three fixture plans, one for each depth. The test shows that the
  runner sends exactly the steps that each depth requires, and that the runner refuses a step whose
  postcondition fails.
- A test that the runner refuses a proofreading edit that changes an `E-*` checkbox state.
- Tests of the marker parser: `AGAIN`, `DONE`, a marker that appears only in the middle of the reply,
  a missing last line, and a reply that contains both markers.
- A test that the re-review loop stops after two rounds and produces `no-go`.
- A test that the resolver flags a renamed symbol, a changed heading, and a line-number citation
  outside pasted output.
- A live review of at least one real pending plan at each depth on one host, reported as observed. A
  host that is not available is recorded as "not run", not as "passed".

## 13. Risks

| Risk | Mitigation |
| --- | --- |
| Turn cost grows with the number of steps (8 to 11 prompts per review instead of 1). | All steps share one session (MD-6), so the plan and the repository context load once. The cost is measured in the live validation. |
| The floor thresholds classify plans wrongly. | The thresholds are configuration. The agent can raise the depth. The floor and the rating are recorded so that the thresholds can be tuned. |
| A free-form review does not follow the checklist. | Accepted. Runner runs are the enforcement point, by design. |
| Retiring `/plan-review-long` breaks managed repositories that call it. | Order 07 removes the shim through the installer. Order 01 provides the replacement checklist. |
| The wording-only check refuses legitimate proofreading. | The check covers structure only. Prose changes are always allowed. |
| The agent omits or garbles the marker line. | A protocol failure counts as `AGAIN` (Section 8.1), and the two-round limit bounds the cost. |

## 14. Open questions

| ID | Question | Blocking |
| --- | --- | --- |
| OQ-1 | Resolved by MD-3: the agent's signal is the `AW-REVIEW: AGAIN` or `AW-REVIEW: DONE` last line. | Resolved |
| OQ-2 | What is the exact syntax of the quoted-text citation form in Section 7? | Yes, for Order 03 |
| OQ-3 | When `aw ipd begin` finds a broken citation, should it refuse to begin, or only warn? A refusal stops stale plans from executing. A warning avoids blocking a plan whose stale citation is harmless. | Yes, for Order 03 |
| OQ-4 | Should a split step's new plans inherit the original plan's `- From-Backlog:`, `- From-Spec:`, and `- Blocks-Release:` values? Proposed answer: yes, all three. | No |
| OQ-5 | Should changes to security-sensitive paths raise the floor to `complex`? This requires a configured list of such paths, which does not exist today. | No |
| OQ-6 | For a plan Set, is the depth assessed once for the Set or once for each plan? Proposed answer: once for each plan; the orchestrator is always `complex`. | No |

## Workflow history

- 2026-10-17 created (aw specs): Replace single-turn /plan-review with runner-enforced discrete steps: proofread, complexity-scaled review depth, AW-REVIEW re-review marker, split step, durable citations; retire plan-review-long
