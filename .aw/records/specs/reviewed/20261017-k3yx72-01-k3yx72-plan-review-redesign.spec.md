# Spec: Runner-enforced, depth-scaled plan review

- Date: 2026-10-17
- Status: reviewed
- Id: k3yx72
- Author: aw specs new
- Scope: Replace the single-turn plan review with a runner-driven sequence of review prompts whose number scales with the plan's review tier (simple, standard, complex); proofread first; re-review by an exact reply marker; split over-large plans; check code citations by symbol; retire plan-review-long; decide prompt grouping by a measured experiment
- Work-Kind: feature
- Relation to prior work: Revises the 2026-10-17 draft of this spec after a four-model design review (research Set `revsteps`: prompt `y6vfto`, reports `r7rfdi`, `xd85vw`, `p6pbfx`, `2rrqp1`, reconciliation `vcg8mz`) and maintainer rulings in session. Amends runner spec `25kzda` (the review action and session use) and IPD structure-and-linting spec `20260802-1904` Section 10.2 (code citations). Must stay compatible with pending metadata spec `4sd62s` (Section 12).
- Set: revsteps

## 0. Terms

| Term | Meaning in this spec |
| --- | --- |
| Plan, IPD | An Implementation Plan Document under `.aw/records/plans/`. It has execution items (`E-*`) and matching validation items (`V-*`). |
| Plan Set, orchestrator | Plans that share a `- Set:` value. The Order-00 plan is the orchestrator. It lists its child plans and carries no work of its own. |
| Runner | The drivers `aw oc run` (OpenCode host) and `aw agy run` (Antigravity host). Shared logic is in `agent_workflows/runner_shared.py`. |
| Prompt | One message the runner sends to the review agent. The agent may take many model steps (model calls and tool calls) to answer one prompt. |
| Session | A host conversation that keeps its context across prompts. Both hosts can resume a session by its id. |
| Review invocation | One runner review of one plan, from the first prompt to the verdict, including any re-review passes. |
| Review record | The findings file under `.aw/records/reviews/` that the review writes. It has one `## Round <n>` section per review invocation. |
| Review tier | `simple`, `standard`, or `complex`. The tier decides which review checks run and how many prompts the review uses (Section 5). |
| Proofreading instructions | Prompt `wcisgc`, "Proofread Technical Artifacts", at `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md`. |
| Recommendation strength | One of `very weak`, `weak`, `medium`, `strong`, `very strong`, attached to every recommendation (Section 7.3). |
| Verdict outputs | The three things existing gates read to decide whether a review cleared a plan: the plan's `- Readiness:` field, its `- Status:` move from `to-review` to `reviewed`, and the one history entry that states a review verdict (`APPROVE`, `APPROVE WITH REVISIONS APPLIED`, `REVIEWED - OPEN QUESTIONS`, or `REJECT - NEEDS REPLAN`). |
| Reviewed-contract hash | The value of `agent_workflows/ipd_lifecycle.py::frozen_region_digest`: a SHA-256 over the plan's `- Scope-Paths:` list and the action text of every `E-*` and `V-*` item. It does NOT cover checkbox marks, `Execution state`, evidence fields, open questions, prose sections, or `## Workflow history`. Two plan texts with the same hash ask the executor to do the same work in the same files. |
| Plan-file hash | A SHA-256 over the plan file's exact bytes. Any edit changes it. |

Identifier note: under spec `89xjll` (requirement-id convention; this spec is dated after its 2026-10-01 cutover), the goal ids `G1`-`G5` and the check ids `R1`-`R7` are extracted as TRACE-mandatory requirement ids, and the acceptance ids `AC-01`... in Section 14 as acceptance ids. That is intended: each implementing plan's `E-*` items cite the goals and checks they build, and its `V-*` items cite the acceptance criteria they prove.

## 1. Problem

1. **Review is the largest cost.** The runner analytics attribute about half of all recorded agent
   cost to review. A direct read of 1,311 OpenCode review attempts (2026-10-17) found 16.05 billion
   tokens and $10,528 of recorded cost. 98.8 percent of the tokens were cache reads: each model step
   re-sends the whole conversation. The median attempt took 50 model steps and ended with a
   234,000-token context. Review cost is therefore roughly the number of steps multiplied by the
   context size per step. Most context is tool output: `bash` produced 71 percent of tool output
   bytes and `read` 27 percent. Source: the measurement table in prompt `okj4bg`
   (`.aw/records/prompts/pending/20261018-revsteps-02-okj4bg-runs-analyze-review-cost.prompt.md`),
   which backlog item `i2i81x` carries.
2. **Every plan gets the same review.** A 1-to-4-line change and a 40-item plan both receive the full
   `/plan-review` workflow. `/plan-review-long` was meant to review complex plans more deeply. It does
   not: it differs from `/plan-review` only in loading one step file at a time and in using parallel
   read-only lanes for batches of two or more plans.
3. **The runner cannot see inside a review.** One review turn does everything, and the runner can
   check only its final result.
4. **Plan text needs interpretation.** Shorthand, vague requirements, and unstated conditions in plans
   cause rework later.
5. **Line-number citations go stale.** Many artifacts wait in the queue at once, so a line number is
   usually wrong by the time a plan executes.

## 2. Goals and non-goals

Goals:

- G1. Scale review cost to the plan: a simple plan gets a short "did we miss something" review; a
  complex plan gets the full review.
- G2. Make each review check a separate, runner-visible unit, so the runner knows which checks ran.
- G3. Proofread every plan before it is reviewed.
- G4. Decide the prompt grouping by measurement, not by argument (Section 13).
- G5. Make code citations survive unrelated edits.

Non-goals:

- N1. Spec review and backlog review. Spec review is deferred; it may reuse this machinery later.
  Backlog items receive no review.
- N2. Preventing deliberate agent misbehavior. Agents have full access to the toolkit. Runner checks
  exist to catch skipped or forgotten work, not to defeat a hostile agent.
- N3. Crash-proofing. The review must resume sensibly after an interruption (Section 9.3); it need
  not survive every failure.
- N4. The shorter backlog-to-execution pipeline for small changes. It is filed separately as backlog
  work (Section 15).
- N5. A writing standard applied while drafting. The proofreading instructions apply at review time
  only.

## 3. Maintainer decisions

| ID | Decision |
| --- | --- |
| MD-1 | The review agent rates the review tier, after answering and recording the tier questions of Section 5.2. The runner forces no tier; it records each review's tier and answers so later analysis can compare tiers with execution outcomes. Orchestrators keep their fixed profile (Section 5.1), which is a structural fact, not a judgement. (Revised 2026-10-17 to option B; revised again 2026-10-19: no runner tier gates, because no evidence shows agents under-rate and hard gates have repeatedly cost more than they caught.) |
| MD-2 | A plan that should be a Set is split in a separate split step after a `no-go` verdict, without human approval (Section 10). |
| MD-3 | The agent signals a re-review with an exact last-line marker: `AW-REVIEW: AGAIN` or `AW-REVIEW: DONE` (Section 8). |
| MD-4 | `/plan-review-long` is retired. |
| MD-5 | Code citations use durable anchors (Section 11). Trailing line numbers are discouraged but allowed. All line numbers in technical artifacts are hints, never authority. Existing citations are treated as hints and are not rewritten. |
| MD-6 | All prompts of one review invocation run in one host session. |
| MD-7 | `/plan-review` becomes a checklist of step files, and the runner sends the same step files as prompts. |
| MD-8 | Proofreading of review edits is limited to the passages each step changed: every editing step ends with "Make sure that every edit you made in this step conforms to the proofreading instructions." |
| MD-9 | Every recommendation carries a recommendation strength (very weak, weak, medium, strong, very strong). `/askme` adopts the same five-level scale. |
| MD-10 | Citation problems are reported and never block a plan. The runner hands the report back to the agent at least once to fix (Section 11.2). |
| MD-11 | Any step may add open questions, each with a recommended answer and strength. No step may change an existing `Blocking: yes` to `Blocking: no` without recording why. |
| MD-12 | An interrupted review resumes after the last completed step in the same session. If that session cannot be resumed, the review restarts at the proofreading step in a new session (Section 9.3). |
| MD-13 | The runner never uses Antigravity's `--continue` fallback for a review. Without a captured session id it starts a new session. |
| MD-14 | Prompt counts are `simple` 2 to 3 prompts, `standard` 5 prompts, and `complex` either 7 grouped or 13 single prompts (12 for a plan outside a Set). The experiment in Section 13 chooses between the two `complex` variants. (Revised 2026-10-18 at spec review, SR-001: each count gained one prompt when S7 became its own final prompt under MD-15.) |
| MD-15 | The verdict outputs are written exactly once per review invocation, after the re-review loop has ended (marker `AW-REVIEW: DONE` and no runner trigger). They are written by S7, which is its own final prompt. Progress that no gate reads as a verdict (review-record `### Step` and `### Pass` subsections, and history entries with no verdict token) may be written at any time and as often as useful. (Spec review 2026-10-18, SR-001.) |
| MD-16 | A review that ends `no-go` leaves the plan at `reviewed` with `- Readiness: no-go`, as today. Only an exhausted orchestrator repair loop leaves the plan at `to-review` with `- Readiness:` absent. Answering a blocking question clears `no-go` without a re-review unless the answer changes the plan (Section 9.4). (Spec review 2026-10-18, SR-002.) |
| MD-17 | The grouping experiment is a pilot followed by a sized run under a human-set dollar cap, scored with a quality rubric as well as cost. On a result that is not shown different, `single-12` is the default (Section 13). (Spec review 2026-10-18, SR-003.) |
| MD-18 | The quoted-text citation form is `` `path` "text" `` (Section 11.1). (Spec review 2026-10-18, closes OQ-02.) |

## 4. Review sequence

The runner performs the pre-pass itself. It then sends the tier's prompts to one session in order.
After each prompt, the runner checks that prompt's postcondition (Section 6) before it sends the
next. If a postcondition fails, the runner re-asks once in the same session, naming what is missing.
If the re-ask also fails, the review invocation ends as `incomplete` (Section 9.1).

### 4.1 Runner pre-pass (no agent)

The runner:

1. Makes the pre-review commit when the plan is untracked or modified (the existing conditional
   rule in `plan-review.md#Pre-review commit`). The commit subject must not start with
   `plan-review:`.
2. Runs `aw ipd lint --phase author` and, for an orchestrator, `aw ipd coverage <id6>`.
3. Runs the citation resolver (Section 11.2) on the plan.
4. Collects the facts the tier questions ask about (Section 5.2): whether `- Scope-Paths:` names a
   `.spec.md` file, the execution-item and task-group counts, and the `- Scope-Paths:` list.
5. Records the plan-file hash and the reviewed-contract hash (Section 0) as the review baseline.
6. Puts the results of items 2 to 4 into the first prompt, so the agent does not re-derive them.

Item 6 also addresses Section 1 problem 1: facts the runner supplies are facts the agent does not
have to search for.

### 4.2 Review checks

Each check is one step file under `.aw/system/workflows/plan-review/steps/`. A prompt runs one or
more checks, depending on the tier and the grouping variant (Section 5.3).

| Check | What the agent does |
| --- | --- |
| P Proofread | Apply the proofreading instructions to the plan. Record material changes and unresolved ambiguities in the review record's `### Proofreading` subsection (Section 7.1). |
| T Tier | Rate the tier, give the reason, and end the reply with `AW-TIER: <simple\|standard\|complex>` on its own last line. |
| Q Quick risk | Answer: what could this change break, and what existing behavior does something else depend on? Record any finding. |
| R1 References | Fix or record every citation the resolver reported (Section 11.2). |
| R2 Executability | Check the E/V bijection, scope (`- Scope-Paths:`), dependencies (`- Item-Dependencies:`), that every `V-*` item demands concrete evidence, and that no item hardcodes a count of a mutable record tree. |
| R3 Security | Short form: secrets, input from outside the trust boundary, and destructive or irreversible actions. Full form: all of rubric section B in `plan-review.md`. |
| R4 Engineering | Rubric sections A and C to G in `plan-review.md`: correctness and data integrity, architecture and operability, invariants, testing (including the ban on code-pinning tests), simplicity, executability (including overloaded items), and the truthfulness of `## Spec / documentation sync`. |
| R5 Personas | The eight reviewer viewpoints: QA/QC, testing and regression, UI/UX, architect, software engineer, power user, novice, stakeholder. |
| R6 Decomposition | Decide whether the plan should become a plan Set. A recommended split records a proposed breakdown and forces `no-go` (Section 10). |
| R7 Cross-plan | For a plan in a Set: consistency with its siblings and its orchestrator. |
| S5 Questions | Resolve open questions from repository evidence. Escalate every unfixed finding at or above the configured block level to a `Blocking: yes` question with `- Finding: <ID>` (the existing Step 4 escalation rule). |
| S6 Re-review | End the reply with `AW-REVIEW: AGAIN` or `AW-REVIEW: DONE` (Section 8). |
| S7 Finalize | Sent only after the re-review loop has ended (MD-15). Write the verdict outputs: `- Readiness:`, the status move, and the one verdict-bearing history entry; then the final commit (Section 7.2). |

### 4.3 Step files and their source

The step files are made from the existing `plan-review.md` (741 lines, 48 KB). Every part of it goes
to exactly one place; nothing is dropped. Sizes are the current section sizes in bytes.

| Current `plan-review.md` part | Bytes | Goes to |
| --- | --- | --- |
| Memory kernel | 667 | `steps/_kernel.md`, sent once in prompt 1 |
| Step 0 (scope ledger, controlling instructions, plan contract) | 2,616 | Runner pre-pass (Section 4.1) for the deterministic parts; `steps/_kernel.md` for the instruction to apply the `AGENTS.md` rules that bear on the plan |
| Step 1 structural preflight and pre-review commit | 1,710 | Runner pre-pass |
| Step 1 orchestrator repair loops (`IPD-S407`, `IPD-S408`) | 3,333 | `steps/r2-executability.md`, orchestrator section |
| Step 2.1 views, 2.2 findings, 2.3 Fix Bar, 2.4 revise in place | 3,975 | `steps/_findings.md`, sent with every prompt that contains Q or R1 to R7 |
| Step 3.1 question set, resolving HOW questions, reversibility | 5,344 | `steps/s5-questions.md` |
| Step 3.2 ask interactively, 3.3 non-interactive exception | 1,340 | `steps/s5-questions.md` (the interactive part is used only by the free-form checklist) |
| Step 4 finalize, Readiness field, workflow history, hardened-result commit | 6,661 | `steps/s7-finalize.md` |
| Rubric A, C, D, E, F | 1,898 | `steps/r4-engineering.md` |
| Rubric B | 406 | `steps/r3-security.md` (full form); the short form is its first three bullets |
| Rubric G (plan executability) | 7,852 | `steps/r2-executability.md` (structure, evidence, counts) and `steps/r4-engineering.md` (right-sizing, overloaded items) |
| Severity and scope | 658 | `steps/_findings.md` |
| Verdict and readiness, NO-GO re-evaluable, escalation return path | 5,253 | `steps/s7-finalize.md` (verdict) and `steps/s5-questions.md` (escalation) |
| Required final report | 2,095 | `steps/s7-finalize.md`; in a runner review the report is the review record, not chat text |
| (new) proofreading | - | `steps/p-proofread.md`: prompt `wcisgc`, with open questions written to the review record (Section 6.1) and citations in the forms of Section 11 |
| (new) tier, quick risk, personas, decomposition, cross-plan, re-review | - | `steps/t-tier.md`, `steps/q-quick-risk.md`, `steps/r5-personas.md`, `steps/r6-decomposition.md`, `steps/r7-cross-plan.md`, `steps/s6-rereview.md` |

The personas in `.aw/system/workflows/release-review/00-run-protocol.md` and the Fix Bar in
`.aw/system/workflows/release-review/fix-decision-policy.md` are referenced, not copied.

Order 01 keeps a table in the new `/plan-review` README that maps every old section to its new file,
so a reviewer of Order 01 can confirm that nothing was lost. Order 01 also records the total bytes of
instructions sent per tier; a `simple` review sends `_kernel.md`, `p-proofread.md`, `t-tier.md`,
`q-quick-risk.md`, `_findings.md`, `s5-questions.md`, `s6-rereview.md`, and `s7-finalize.md`, not the
whole 48 KB file.

## 5. Review tiers

### 5.1 Checks per tier

| Tier | Intended plans | Checks |
| --- | --- | --- |
| `simple` | Very low risk: typically a few lines of code, such as a small bug fix or one new CLI option. | P, T, Q, S5, S6, S7. R3 short form when the agent's tier answers say the plan touches code that guards private data, commits, worktree isolation, or the sandbox. |
| `standard` | Most medium plans. | P, T, R1, R2, R3 (full), R4, S5, S6, S7. |
| `complex` | Large, cross-cutting, or contract-changing plans. | P, T, R1, R2, R3 (full), R4, R5, R6, R7 (Sets), S5, S6, S7. |
| `orchestrator` | Every Order-00 orchestrator, whatever its size. Not rated by T. | P, R1, R2 (child table, coverage, ordering), R7 across the Set, S5, S6, S7. Never R5 or R6. |

A plan in a Set receives its own tier. When the queue holds a Set's children and its orchestrator
for review, the children are reviewed first, so the orchestrator's R7 and coverage check see the
reviewed children. This is a CHANGE to queue ordering: today
`agent_workflows/runner_shared.py::dependency_depth` places an orchestrator after its Set's children
only when the orchestrator's action is `orchestrate`, not when it is `review`. Order 04 extends that
rule to `review` (Section 17.1).

### 5.2 Tier questions

Check T asks the agent to answer each question below in the review record's `### Step T`
subsection, one line each, before it gives the tier. The runner supplies the facts it collected in
the pre-pass (Section 4.1, item 4), so the agent does not search for them.

1. Does the plan change a spec, a public interface (CLI option, output format, file format,
   configuration key), or another contract that other code or other plans rely on?
2. Does the plan touch code that guards private data, commits, worktree isolation, merges to main,
   or the sandbox? Examples in this repository: `agent_workflows/leak_sanitizer.py`,
   `agent_workflows/local_leaks.py`, `agent_workflows/git_commit_helper.py`,
   `agent_workflows/commit_lock.py`, `agent_workflows/lane_containment.py`,
   `agent_workflows/egress_policy.py`, `agent_workflows/host_sandbox_profile.py`.
3. Is the plan large or cross-cutting: many execution items, several task groups, or changes in
   several unrelated modules?
4. Does the plan list the files it changes (`- Scope-Paths:`)? If not, what does the review know
   about its reach?
5. Could a mistake in this change lose data, break existing behavior that other code depends on, or
   be hard to undo?

Guidance in the step file, not a rule: a "yes" to question 1, 2, or 5 usually means `standard` or
`complex`; `simple` fits a change where every answer is "no" and the change is small.

The runner forces no tier. It records the tier and the five answers in run state, so the analytics
(backlog `i2i81x`) can later compare tiers with execution outcomes. A hard gate is added only if that
comparison shows agents under-rating plans.

For reference, measured 2026-10-18 over the 1,554 non-orchestrator plans dated 2026 in this
repository: 167 edit a `.spec.md` file, 61 touch one of the question 2 example modules, 1 exceeds the
size limits, and 290 (all dated before the `- Scope-Paths:` requirement) do not list their files.

The agent may raise the tier at any later check when review edits change an answer.

### 5.3 Prompt grouping

| Tier | Variant | Prompts |
| --- | --- | --- |
| `simple` | - | 1: P+T+Q. 2: S5+S6. 3: S7. When the plan has no open questions and Q records no finding, the runner may send prompt 2's checks in prompt 1 (two prompts total). |
| `standard` | - | 1: P+T. 2: R1+R2. 3: R3+R4. 4: S5+S6. 5: S7. |
| `complex` | `grouped-6` | 1: P+T. 2: R1+R2. 3: R3. 4: R4+R5. 5: R6+R7. 6: S5+S6. 7: S7. (The variant name counts the review prompts before S7.) |
| `complex` | `single-12` | One prompt per check: P, T, R1, R2, R3, R4, R5, R6, R7, S5, S6, then S7 (13 prompts). R7 is skipped for a plan outside a Set (12 prompts). |
| `orchestrator` | - | 1: P+R1+R2. 2: R7. 3: S5+S6. 4: S7. |

S7 is always its own prompt and is sent once, after the loop of Section 8 ends (MD-15). A re-review
pass therefore re-sends review checks and S5+S6, never S7.

The grouping is a runner setting (`review_variant`), recorded in run state, so that both `complex`
variants use the same step files and differ only in grouping. Until Section 13 has produced a
result, the default is `single-12` (MD-17).

Prompt 1 always contains P and T (P alone for an orchestrator), whatever tier is later chosen, so
prompt 1 is the same for every tier. The runner fixes the tier after prompt 1, from T's marker, and sends the rest of that tier's prompt list from prompt 2. Checks are
identified by name, not by position: when the agent raises the tier later (Section 5.2, last paragraph),
the runner sends, before S5, one prompt per group of the new tier's list that contains a check not
yet run, with only those checks. Checks already run are not repeated. A tier is never lowered after
prompt 1.

## 6. Postconditions

The runner checks these after each prompt. A check that fails triggers one re-ask (Section 4).

| Check | Postcondition |
| --- | --- |
| P | The structural preservation check passes (Section 6.1). The `### Proofreading` subsection exists in the current round. |
| T | The last non-empty line of the reply is exactly `AW-TIER: simple`, `AW-TIER: standard`, or `AW-TIER: complex`. The `### Step T` subsection answers all five tier questions of Section 5.2. |
| Q, R1 to R7 | The current round has a `### Step <check>` subsection for each check in the prompt (for example `### Step R4`). Findings, if any, are rows in the round's single `### Findings` table (Section 7.1). R1 additionally: the runner re-runs the resolver and the agent addressed every result it reported. |
| S5 | Every open question has `Blocking:` and `Status:`. Every `Blocking: no` added or changed in this review has a rationale. `check.review-finding-unescalated` passes. |
| S6 | The marker rules in Section 8.1 are met. |
| S6 (every pass before the last) and every check before S7 | The plan's `- Readiness:` value, `- Status:` value, and newest verdict-bearing history entry (as read by `plan_readiness.newest_verdict`) are byte-identical to their values at the pre-pass. A change is refused like a failed postcondition: the runner restores those three and re-asks once (MD-15). |
| S7 | One of: (a) `- Readiness:` holds `go`, `go-pending-approval`, or `no-go`, and `- Status:` is `reviewed`; or (b) `- Readiness:` is absent, `- Status:` is still `to-review`, and the round records an exhausted orchestrator repair (the existing `IPD-S407`/`IPD-S408` rule). Exactly one verdict-bearing history entry was added during the invocation. `aw ipd lint --phase author` reports no error that was not present at the pre-pass, except `IPD-Q501` for an open `Blocking: yes` question that S5 added or kept (that diagnostic is the intended effect of a blocking question, not a review defect). |

Every `### Step <check>` subsection starts with one line `- Checked: <what was examined>`, followed
by the check's notes. It may say `- Result: no findings`. The runner checks only that the subsection
and its `- Checked:` line exist.

The re-ask message names the failed postcondition and nothing else: `Your last reply did not complete
<check>: <the postcondition text that failed>. Complete it now and end your reply as the step file
requires.` The runner sends at most one re-ask per prompt.

These postconditions confirm that a check ran. They do not prove that the review was good (N2).

### 6.1 Structural preservation check (check P)

The runner parses the plan with `agent_workflows/ipd_lint.py::parse` before and after check P.

The runner refuses the proofreading edit when any of the following changed:

- A front-matter metadata value.
- The list or order of H2 headings.
- The set of `E-*` and `V-*` ids, or their checkbox states.
- Any `Execution state` value.
- The set of field names under any `E-*` or `V-*` item.
- The `Status:` or `Blocking:` value of an existing open question.

On refusal, the runner restores the plan to its pre-check content and re-asks once. A second
refusal ends the invocation as `incomplete`.

The runner does not refuse, but lists for check R2 and R4 to confirm, any change to:

- An `Expected outcome`, `Depends on`, or validation-evidence demand.
- A requirement word (`must`, `must not`, `should`, `may`) inside an `E-*` or `V-*` item.

Proofreading may add open questions only through the review record (Section 7.1). Check S5 moves
material ones into the plan.

Limit: this check proves that structure was kept. It cannot prove that meaning was kept.

## 7. Review record and outputs

### 7.1 Review record layout

One `## Round <n>` section per review invocation. Re-review passes are subsections inside that
round, not new rounds. Inside a round:

- `### Proofreading`: two tables. Changes: location, old text summary, new text summary, reason.
  Issues: id, location, ambiguity, information needed, recommended answer, recommendation strength.
- `### Step <check>`: one subsection per check that ran, with the check's notes and evidence. No
  finding rows.
- `### Pass <k>`: one subsection per re-review pass, listing which checks it re-ran.
- `### Findings`: the round's single findings table, in the existing `FINDING_COLUMNS` format of
  `agent_workflows/review_findings.py`. It carries every finding raised in any pass of the round,
  with its final decision. This keeps `review_findings.parse_review_text`, which reads finding rows
  only under a heading that starts with `Findings`, working unchanged.
- `### Decisions`: the existing decisions table.

`.aw/records/reviews/README.md` is amended to describe this layout.

### 7.2 Outputs that existing gates read

Per review invocation, whatever the number of passes:

- Exactly one VERDICT-BEARING history entry, in the existing
  `/plan-review (<agent/model>): <verdict>; ...` form (spec `25kzda` Section 4.4,
  `IPD-REVIEW-HISTORY`). This limits only entries that state a verdict, because gates read the newest
  one (`plan_readiness.newest_verdict`) as the review's result. Other history entries (progress
  notes with no verdict token, for example "pass 2 re-ran R2 after E-05 was added") are allowed and
  are not counted. Detailed per-check and per-pass evidence belongs in the review record
  (Section 7.1).
- Exactly one final commit whose subject starts with `plan-review:`
  (`agent_workflows/plan_readiness.py::review_staleness_index` finds the review by that prefix: it
  reads the plan as of that commit and compares it with the current plan). Earlier commits during
  the invocation, if any, must not use that prefix, or a later staleness check would compare
  against a mid-review text. The runner's fallback lane commit subject
  (`review(<host>): record the review of <id6>`) changes to the same prefix.
- The verdict outputs and the review tier are written in S7 only (MD-15). Reason: the runner decides
  whether another pass is needed only after S6's reply, so a verdict written earlier could leave a
  plan at `reviewed` + `go` that the runner has already scheduled for re-review. If the run then
  stopped, the plan would look finished, and under `--full-auto` it could be auto-approved without
  that re-review. The review tier is stored as `- Review-Depth: <tier>` (a new recognized field in
  `agent_workflows/ipd_schema.py::META_RECOGNIZED`). It is not part of the reviewed-contract hash,
  because that hash covers only `- Scope-Paths:` and the `E-*`/`V-*` action text (Section 0). Section
  12 covers storage under `4sd62s`.

### 7.3 Recommendations

Every recommendation the review writes (in an open question, a finding's resolution, or the
proofreading issues table) states its strength: `very weak`, `weak`, `medium`, `strong`, or
`very strong`. The step files instruct this; S5's postcondition checks it for open questions added
or changed in the review.

### 7.4 Open questions

- Any check may add an open question. It must carry a recommended answer and its strength.
- S5 tries to answer each question from repository evidence before leaving it open.
- Only an open question with `Blocking: yes` forces `no-go`. A `Blocking: no` question may stay
  open while the plan receives `go-pending-approval` or `go` (existing rule in
  `plan-review.md#Verdict and readiness`).
- No check may change an existing `Blocking: yes` to `Blocking: no` without a recorded reason.

## 8. Re-review

### 8.1 The marker

The agent ends the S6 reply with exactly one of these lines as the last non-empty line:

```text
AW-REVIEW: AGAIN
AW-REVIEW: DONE
```

Rules:

1. Only the last non-empty line counts. The marker text elsewhere in the reply has no effect.
2. Leading and trailing whitespace is ignored. The comparison is otherwise exact and
   case-sensitive. A trailing code fence line is ignored.
3. If the last line is missing or malformed, the runner re-asks once in the same session for the
   marker only (the existing `runner_shared.perform_defect_reask` pattern). If the re-ask also
   fails, the review invocation ends as `incomplete` (Section 9.1). A malformed marker never counts
   as `AGAIN` and never produces `no-go`.
4. A host failure (timeout, nonzero exit, cancellation) is handled as a host failure before any
   marker is parsed.
5. The runner extracts the agent's text with `runner_shared.probe_reply_text`. It does not reuse
   `classify_probe_reply`, which reads the first line and rejects a reply that contains both
   sentinels anywhere.

### 8.2 Runner triggers

The runner also starts a re-review pass, whatever the marker says, when any of the following changed
between the start and the end of the current pass:

- `E-*` or `V-*` items were added or removed.
- `- Scope-Paths:` or `- Item-Dependencies:` changed.
- An item listed for confirmation by Section 6.1 changed after the pass's R2/R4 checks ran.

The comparison baseline is the plan at the START OF THE CURRENT PASS. A pass that changes nothing
clears all triggers.

### 8.3 The loop

A re-review pass re-runs the tier's review checks (Q or R1 to R7) limited to the changed sections
and the sections that depend on them, then S5 and S6. The runner gives the agent the diff of the
plan file from the start of the previous pass to the start of this pass.

At most two re-review passes are allowed. If the second pass still produces a re-review, S7 must
write `no-go` and add an open question `Blocking: yes` that names what still changed, so that
`aw ipd recheck-readiness` can clear it after a human looks.

The loop ends when S6's reply carries `AW-REVIEW: DONE` and no runner trigger of Section 8.2 fired,
or when the pass limit is reached. Only then does the runner send S7 (MD-15).

## 9. Outcomes, sessions, and interruption

### 9.1 Outcomes

| Outcome | Meaning | Plan state afterwards |
| --- | --- | --- |
| `completed-pass` | S7 wrote `go` or `go-pending-approval`. | `reviewed` (existing transition). |
| `completed-negative` | S7 wrote `no-go`. Findings and blocking questions are kept. | `reviewed` with `- Readiness: no-go` (existing transition; spec `25kzda` Section 3.2 and `plan-review.md#Verdict and readiness`). A `reviewed` plan is not re-dispatched for review, so a `no-go` plan is not re-reviewed on every run; Section 9.4 states how it is cleared. |
| `completed-negative` (orchestrator repair exhausted) | `- Readiness:` is absent after an exhausted `IPD-S407`/`IPD-S408` repair loop. | Stays at `to-review` (existing rule in `plan-review.md#Orchestrator review readiness`). |
| `incomplete` | A re-ask failed, or a host failure could not be recovered. | Restored to the last completed step's content; stays at `to-review`; the run records the reason. No verdict output was written, because S7 was not reached (MD-15). |

### 9.2 Sessions

- All prompts of one review invocation use one session (MD-6).
- The runner captures the session id after the first prompt and resumes by that id for every later
  prompt. If no id was captured, it starts a new session (MD-13).
- Session rotation (`max_items_per_session`) never happens between prompts of one review
  invocation. One review invocation counts as one item toward that limit.
- Whether each review invocation should start a new session or reuse the previous plan's session is
  not decided. Measured data is mixed (OQ-07, and Section 13 variable V4).

### 9.3 Interruption and resume

The runner records, after each prompt: the review invocation id, the pass number, the last completed
prompt, the plan-file hash, and the session id.

On `aw <host> run resume`:

1. Restore the plan to the content recorded after the last completed prompt.
2. If the session can be resumed by id, continue with the next prompt in that session.
3. Otherwise, restart the review invocation at check P in a new session.

Each prompt and transcript gets a unique name per invocation, pass, prompt, and attempt, so a
resumed run does not overwrite earlier logs.

Because no verdict output exists before S7 (MD-15), an interrupted review always leaves the plan at
`to-review` with no `- Readiness:` written by this invocation, so an interruption cannot make an
unfinished review look finished.

### 9.4 Clearing a `no-go` after a blocking question is answered

Most `no-go` results exist only because a blocking question needs a human answer. Answering it should
not cost a full re-review. When a human answers a `Blocking: yes` question on a `reviewed` + `no-go`
plan (through `/askme`, `aw runs answer`, or an interactive run):

1. The agent that records the answer sets the question to `Status: resolved` with the answer, applies
   any plan edits the answer requires, and ends its reply with one line `AW-MATERIAL: yes` or
   `AW-MATERIAL: no`, preceded by a one-sentence reason. `yes` means the answer changes what the
   plan does or how, beyond the question's own text.
2. The runner compares the reviewed-contract hash (Section 0) of the plan at its last `plan-review:`
   commit with the current plan. This is the existing `substantive-edit` test in
   `agent_workflows/plan_readiness.py::review_staleness_from_texts`.
3. If the hash is unchanged AND the marker is `AW-MATERIAL: no`, the runner runs
   `aw ipd recheck-readiness <id6> --apply`. That verb moves `no-go` to `go-pending-approval` only
   when no blocking question is open, no gating finding is open, and the newest verdict is not
   `REJECT - NEEDS REPLAN`; it can never write `go`. No review prompt is sent.
4. If the hash changed OR the marker is `AW-MATERIAL: yes`, the runner runs a TARGETED re-review: a
   new review invocation whose first pass is a Section 8.3 pass limited to the changed sections and
   the sections that depend on them, followed by S5, S6, and S7. It is not a full review.
5. A missing or malformed `AW-MATERIAL:` line is re-asked once (the Section 8.1 rule 3 pattern). A
   second failure is treated as `AW-MATERIAL: yes`, because a missed re-review costs more than an
   unneeded one.
6. A human may force either path: `aw ipd recheck-readiness` directly, or a re-review with
   `aw <host> review <id6> --yes`.

Why both tests: the hash is deterministic but cannot see a design change made only in prose (for
example, a resolved question whose answer reverses an approach described in `## Proposed changes`).
The model's `AW-MATERIAL` judgement covers that case. Either test alone triggers the re-review.

Limit: a model that wrongly answers `no` for a prose-only design change clears the plan to
`go-pending-approval` without re-review. The human approval gate still stands between that and
execution unless `--full-auto` is used.

## 10. Split step

When R6 recommends a split and S7 writes `no-go`, the runner schedules a split step for the plan.

1. **Refusal case.** If the plan was `approved` when the review began, the runner does not split it.
   The `no-go` and the proposed breakdown stay for a human.
2. **Authoring.** An agent writes the new plans in full: an orchestrator at Order 00 and children at
   Order 01 and above, under a NEW Set id. Each new plan must pass `aw ipd lint --phase author` with
   no errors, be set to `to-review` with `aw ipd set`, and the orchestrator must pass
   `aw ipd coverage` before step 4. Scaffold output alone is
   not enough, because scaffolded plans carry `TODO` placeholders and
   `- Item-Dependencies: unresolved`.
3. **Graph changes.** In the same transaction:
   - The new plans take the original's `From-Backlog`, `From-Spec`, and `Blocks-Release` values, and
     those fields are removed from the original. Otherwise the superseded original stays a carrier
     that never executes, and a release-blocking backlog item can never close through its plans
     (`agent_workflows/check_engine.py::_carrier_is_executed`).
   - Every other plan whose `- Item-Dependencies:` names the original is changed to name the new
     orchestrator.
   - The original's prerequisites move to the child plans that need them.
4. **Retirement.** The original moves to `.aw/records/plans/superseded/` through the existing tooled
   setter, `aw ipd set superseded <id6> -m "split into Set <new-setid>"`. That setter already
   relocates the file, appends the history entry, and updates the original Set's orchestrator history
   (`agent_workflows/status_set.py`, the block commented "When a child plan is retired"; verified by
   a `--dry-run` at spec review). It does not write the `RETIRED YYYY-MM-DD: ...` header that
   `.aw/records/plans/README.md` asks for; Order 06 makes the split write that header (or makes the
   setter write it) so the successor Set is named in the plan body, not only in history.
5. **Failure.** If step 2 or 3 fails, the new files are deleted and the original stays in
   `pending/`.
6. **Queue.** Under spec `25kzda` Section 2.6, new plans never join a run already in progress. The
   new plans are reported as next actions and reviewed in the next run.
7. **Bound.** A plan created by a split cannot itself be split automatically.

Under spec `4sd62s`, the field changes in step 3 are writes through the metadata API instead of
text edits (Section 12).

## 11. Code citations

### 11.1 Forms

| Target | Form | What makes it unresolvable |
| --- | --- | --- |
| Python code | `path::Name`, `path::Class.method`, `path::outer.inner`, `path::CONSTANT` | Rename or deletion of that symbol. |
| Markdown | `path#Heading text`, with the exact heading text | A change to that heading text, or a duplicate heading. |
| Quoted text | `` `path` "text" ``: a backticked path, one space, then the text in double quotes. The text is one line and must occur exactly once in that file. Text that itself contains a double quote is written with `\"`, and a backslash as `\\`; no other escapes exist (MD-18). | An edit to the string, or a second occurrence. |
| Records | `<id6>`, `<id6> R-3`, `E-04`, `D153`, each with a descriptive name | Deletion of the artifact or item. |
| Generated files | Cite the generator (`path::Symbol`), not the generated file. | As for Python code. |

A line number may follow an anchor as a hint (MD-5). A line number alone is a hint, not a citation.
Line numbers inside pasted output (tracebacks, test output, diagnostics) are the reported fact and
are not citations.

The resolver checks that a target exists. It does not prove that the cited claim is still true.

### 11.2 The resolver

A new resolver in `aw check` resolves each citation at the current commit and reports `ok`,
`not-found`, `ambiguous`, `file-missing`, or `moved-to <path>`. It never blocks a plan (MD-10).

- It runs in the review pre-pass (Section 4.1). The runner gives its report to the agent in check
  R1, and the runner re-runs it after R1 and gives remaining problems back once.
- It runs again at `aw ipd begin` and its report is put into the execution prompt, so the executing
  agent fixes or works around remaining problems.
- Citations that name a target the plan itself will create are marked by the plan as proposed and
  are not reported as `not-found`. The marking syntax is left to Order 03's plan, which must carry
  it as a `Blocking: yes` open question until it is decided; it is an internal convention of the
  resolver and can change later without breaking any existing citation.
- Exact symbol resolution is for Python. Other languages fall back to a text search and report the
  result as a search match, not a resolved symbol.

### 11.3 Amendment to spec `20260802-1904` Section 10.2

This spec amends Section 10.2 as follows:

- Line numbers are hints in every technical artifact.
- The `IPD-C801` form check stays advisory, as Section 10.2 already requires.
- Existing citations are not rewritten, as Section 10.2 already requires.
- Section 10.2 gains a pointer to the resolver in Section 11.2 as the existence check.

## 12. Compatibility with metadata spec `4sd62s`

Spec `4sd62s` (status `reviewed`, `Blocks-Release: next`) moves artifact metadata into per-artifact
event logs at `.aw/records/meta/<id6>.jsonl`, keeps only `id` and `status` in front matter, removes
`## Workflow history` sections, and records each review round as one `review` event in the subject's
log.

This spec is written in terms of fields and events, so it works under either storage format:

| This spec | Today | Under `4sd62s` |
| --- | --- | --- |
| Review tier | `- Review-Depth:` line, registered in `META_RECOGNIZED` | A `review-depth` field set by the S7 review event |
| One verdict-bearing history entry per invocation (other entries allowed) | One verdict-bearing `## Workflow history` line, plus any progress lines | One `review` event (`4sd62s` Section 4.1a), plus any non-review events |
| Split field moves (Section 10 step 3) | Line edits through the existing setters | `set`/`unset` events through `artifact_meta` |
| Structural preservation check (Section 6.1) | Compares parsed front matter | Compares the folded event state |

Whichever ships first, the implementing plans must declare which format they target. If this spec's
plans run first, the `4sd62s` migration must carry `Review-Depth` like any other field.

## 13. Experiment: prompt grouping

### 13.1 Questions

1. For `complex` plans, does `grouped-6` cost less than `single-12` without lower review quality
   (Section 13.4 rubric)?
2. How does each model respond to each grouping: cost, steps, re-asks, and quality score?
3. (Optional, second round) Does a new session per review cost more or less than reusing the
   previous plan's session?

### 13.2 Prerequisites

- The analytics changes of backlog item `i2i81x` (request text: prompt `okj4bg`): token types, steps and context size, session reuse, tool use, run commit and
  label, model, and redo counts.
- Runs record a label, the git commit, the review variant, and the model on every attempt.
- The step files and both groupings exist (Section 15 Orders 01 and 04).

### 13.3 Design

| Variable | Values |
| --- | --- |
| V1 Plans | 3 pending plans: 1 `standard`, 2 `complex`. For each, a copy with planted defects: a `V-*` item that asks for no evidence, a wrong file path, and a changed CLI option that another command reads. |
| V2 Grouping | `standard`: the single 5-prompt variant. `complex`: `grouped-6` and `single-12`. |
| V3 Models | Opus 5.5 High (OpenCode) and Gemini 3.8 Flash High (Antigravity). GPT-6.1 Sol only if a Codex host exists or by hand. |
| V4 Session | Pilot and sized run: fixed (new session per review). A later round may compare new versus reused sessions with the chosen grouping. |

Each review runs in its own worktree from the same commit with a run label. The experiment has two
stages (MD-17):

1. **Pilot.** Each combination runs twice: about 24 reviews. Purpose: measure the real
   review-to-review variation in cost and in quality score, and calibrate the rubric (Section 13.4)
   by checking that two scorers agree on the same reviews. The pilot alone never chooses a variant.
2. **Sized run.** From the pilot's measured variation, compute the number of paired reviews needed
   for the test in Section 13.5 at the margins set in OQ-10, and record that number and its
   projected cost in the research report BEFORE running it. The run proceeds only up to the dollar
   cap a human sets in OQ-10.

Scale, for planning only: a median review costs $7.83 (Section 1 source). If review cost varies by
about 50 percent between attempts (not yet measured; the pilot measures it), an equivalence test at
95 percent confidence with a 5 percent cost margin needs several hundred to over a thousand paired
reviews; a 10 percent margin needs about a quarter of that.

### 13.4 Measures and quality rubric

Per review: tokens by type (new input, cache read, cache write, output, reasoning), model steps,
context size per step, wall time, cost where recorded (tokens otherwise; Antigravity records no
cost), re-asks and failed postconditions, re-review passes, verdict, and a quality score.

Quality is scored per review against a written rubric, not by planted-defect count alone, because a
review that finds every planted defect may still leave a worse design. The rubric scores at least:
planted defects found (each weighted by the harm it would cause if executed, not counted equally),
false findings raised, correctness of the edits the review made, and the design quality of the
reviewed plan afterwards. Scoring is done by a scorer that does not know which variant produced the
review. The weights and the scoring procedure are decided in OQ-10 before the sized run, so they
cannot be tuned to the result.

### 13.5 Decision rule

The sized run uses a paired equivalence test (two one-sided tests) on cost and on quality score,
at the confidence and margins set in OQ-10 (at least 95 percent; 99 percent preferred).

- If one variant is shown better on quality, choose it, even at higher cost, unless the cost
  difference exceeds the limit set in OQ-10.
- Otherwise, if one variant is shown cheaper and the two are shown equivalent on quality, choose the
  cheaper one.
- Otherwise (shown equivalent on both, or not shown different on either), choose `single-12`. It gives
  one runner-visible result per check, which shows which checks are worth optimizing later.
- If the dollar cap is reached before the test reaches its confidence, the result is
  `inconclusive` and the default stays `single-12`.

Record the pilot, the sample-size calculation, the sized run, and the decision as a research report
in Set `revsteps`.

## 14. Acceptance criteria

Each criterion is demonstrated with the scripted host on fixture plans unless it says otherwise, and
its evidence is pasted test output that names the fixture and the observed result.

- AC-01: A `simple` plan is reviewed in at most 3 prompts, a `standard` plan in 5, and a `complex`
  plan in 7 (`grouped-6`) or 13 (`single-12`, 12 outside a Set); the prompt count is read from the
  run's attempt records. (G1, G2)
- AC-02: The runner refuses a proofreading edit that changes an `E-*` checkbox, restores the plan, and
  re-asks once; a second refusal ends the invocation `incomplete`. (P, Section 6.1)
- AC-03: A malformed `AW-REVIEW:` line causes exactly one re-ask, and a second failure ends the
  invocation as `incomplete` with no `- Readiness:` written and the plan at `to-review`. (S6)
- AC-04: A re-review pass that changes nothing ends the loop; a fixture whose first pass adds an E/V
  pair and whose second pass changes nothing finishes `completed-pass`. A fixture that still triggers
  after the second pass finishes with `no-go` and a `Blocking: yes` question naming the change.
  (Section 8.3)
- AC-05: A finding recorded in pass 1 and not fixed still gates the plan after pass 2 (it appears in
  the round's single `### Findings` table and `review_findings.subject_gating_blocks` reports it).
  (R1-R7, Section 7.1)
- AC-06: One review invocation with two passes produces exactly one verdict-bearing history entry and
  exactly one `plan-review:` commit; progress entries without a verdict token are permitted and are
  ignored by `plan_readiness.newest_verdict`. (S7, MD-15)
- AC-07: A fixture whose agent writes `- Readiness:` in an S6 prompt has that write reverted by the
  runner and is re-asked; and a fixture interrupted after pass 1 leaves the plan at `to-review` with
  no new `- Readiness:`. (MD-15)
- AC-08: Check T records an answer to each of the five tier questions and the chosen tier, and the
  runner stores both in run state; the runner does not change the tier the agent chose. (T,
  Section 5.2)
- AC-09: A review ending `no-go` leaves the plan at `reviewed` + `- Readiness: no-go`, and a later run
  over `reviews` does not dispatch it for review. (MD-16)
- AC-10: Answering the only blocking question on a `reviewed` + `no-go` fixture with no contract edit
  and `AW-MATERIAL: no` ends at `go-pending-approval` with no review prompt sent; the same fixture
  with an `E-*` action edit, or with `AW-MATERIAL: yes`, or with a malformed marker after one re-ask,
  starts a targeted re-review instead. (Section 9.4)
- AC-11: A split of a plan carrying `From-Backlog` and `Blocks-Release` leaves the backlog item
  closable through the new plans, and rewrites another plan's `executed:<original>` dependency.
  (R6, Section 10)
- AC-12: A split of a plan that was `approved` at review start is refused; and a split whose
  authoring step fails deletes the new files and leaves the original in `pending/`. (Section 10)
- AC-13: The resolver reports `not-found` for a renamed symbol, `ambiguous` for a duplicated quoted
  string, accepts `` `path` "text" `` with an escaped `\"`, and treats a trailing line number as a
  hint; it never changes an exit code to blocking. (G5, Section 11)
- AC-14: An interrupted review resumes at the next prompt in the same session, or restarts at check P
  in a new session when the session is gone. (Section 9.3)
- AC-15: `/plan-review-long` no longer exists in the installed workflows, command shims, or index,
  shown by an install into a scratch repository. (MD-4)
- AC-16: Every check P run proofreads the plan, shown by a non-empty `### Proofreading` subsection in
  each fixture's review record. (G3)
- AC-17: The experiment in Section 13 has run through the pilot, the recorded sample-size calculation,
  and the sized run or the cap, and its research report records the decision under the Section 13.5
  rule. Evidence: the research report's path and decision line. (G4)

## 15. Work breakdown (proposed Set `revsteps`)

| Order | Work | Depends on |
| --- | --- | --- |
| 00 | Orchestrator. Child tracking only. | All children |
| 01 | Step files under `.aw/system/workflows/plan-review/steps/`, the `/plan-review` checklist, the proofreading adaptation, the review record layout (Section 7.1) and its README amendment, and the five-level recommendation strength in `/plan-review` and `/askme`. | Spec approval |
| 02 | `Review-Depth` field, the pre-pass tier facts (Section 4.1 item 4), and recording the tier and the tier answers in run state. | Spec approval |
| 03 | Citation resolver, its review and `aw ipd begin` integration, and the `20260802-1904` Section 10.2 amendment. | Spec approval |
| 04 | Runner multi-prompt review for both hosts: prompt lists per tier and `review_variant`, postconditions (including the verdict-output guard of MD-15), re-ask, structural preservation check, outcomes, session handling, resume. | 01, 02, 03 |
| 05 | Re-review marker, runner triggers, the loop, and the no-go clearing path of Section 9.4 (`AW-MATERIAL` marker, reviewed-contract hash test, `recheck-readiness` or targeted re-review). | 04 |
| 06 | Split step, including the graph changes and the `RETIRED` header on retirement through `aw ipd set superseded`. | 04 |
| 07 | Retire `/plan-review-long` (workflow, shims, index, installer entries, current docs, tests). | 01, 04 |
| 08 | Records README and `AGENTS.md` pointers: read a tree's README before editing an artifact in it. | 01, 03 |
| 09 | Run the experiment (Section 13: pilot, sample-size calculation, sized run under the cap) and set the default `review_variant`. Its plan carries OQ-10 as `Blocking: yes` until a human answers it. | 04, 05, analytics backlog item |

Separately filed backlog items (not part of this Set):

- `i2i81x`: analytics breakdowns and run labels for `aw runs analyze` (request: prompt `okj4bg`).
- `rsisop`: a shorter pipeline for small changes (plan to review to execution).

## 16. Open questions

Question ids use two digits (`OQ-02`, not `OQ-2`) because the open-question parser the approval gate
uses (`agent_workflows/ipd_schema.py::OQ_HEADING_RE`) matches only `OQ-` followed by two or more
digits; a one-digit id is invisible to `plan_readiness.has_unresolved_blocking_question`. Renumbered at
spec review (SR-005); the numbers are otherwise unchanged.

### OQ-02: Quoted-text citation syntax

- Blocking: no
- Status: resolved
- Owner: maintainer
- Question: How is a quoted-text citation written? Candidates from the design review: `` `path` "text" ``; `path::quote("<JSON string>")`; `path::"text"`. All three require one line and a unique match.
- Resolution or deferral rationale: Resolved 2026-10-18 by the maintainer at spec review: `` `path` "text" `` (MD-18, Section 11.1). The escape rule (`\"` and `\\` only) was added by the reviewer so a quoted text containing a double quote is still one unambiguous citation.

### OQ-07: Session per review

- Blocking: no
- Status: open
- Question: Should each review invocation start a new session, or reuse the previous plan's session?
- Data: of 1,311 review attempts, 404 in a session new to the run had a median 36,000-token first context, 81 steps, and $9.21 cost; 907 in a reused session had 229,000, 43 steps, and $6.78. The groups differ in period, plans, and models, so the comparison is not controlled.
- Recommendation: decide by Section 13 variable V4. Until then, keep today's behavior. Strength: medium.

### OQ-08: Sensitive-path list for this repository

- Blocking: no
- Status: resolved
- Owner: maintainer
- Question: Which paths in this repository go into a `review.sensitive_paths` list that forces the `complex` tier?
- Resolution or deferral rationale: Resolved 2026-10-19 by the maintainer: no such list. The runner forces no tier (MD-1 as revised); the candidate modules became examples in tier question 2 (Section 5.2), which the agent answers.

### OQ-09: Codex host for the experiment

- Blocking: no
- Status: open
- Question: Should the experiment include GPT-6.1 Sol? The runners do not drive Codex today.
- Recommendation: run the pilot with the two runner hosts and add Codex by hand only if the two disagree. Strength: weak.

### OQ-10: Experiment margins, confidence, quality rubric, and dollar cap

- Blocking: no (at spec level; Order 09's plan must carry it as `Blocking: yes`, so the sized run cannot start before it is answered)
- Status: open
- Owner: maintainer
- Question: For Section 13.5: the cost-equivalence margin and the quality-equivalence margin (for example cost within 5 percent with quality within 1 percent, or 10 percent with 3 percent); the confidence (95 or 99 percent); the largest extra cost accepted for a variant shown better on quality; the rubric weights of Section 13.4; and the dollar cap for the sized run.
- Why not now: the right margins depend on the review-to-review variation the pilot measures, and a cap set before that is a guess.
- Recommendation: answer after the pilot, from its recorded variation and the sample-size table it produces. Strength: strong.

### OQ-11: Who enforces the verdict-output guard between prompts

- Blocking: no
- Status: open
- Owner: Order 04 author
- Question: MD-15 forbids writing the verdict outputs before S7, and Section 6 makes the runner restore them if an earlier prompt changes them. Should the runner instead strip write permission for those fields (for example by denying the setter in non-S7 prompts), or is detect-and-restore enough?
- Recommendation: detect-and-restore. Non-goal N2 says runner checks catch forgotten or skipped work, not a hostile agent, and detect-and-restore is host-neutral. Strength: medium.

## 17. Amendments to other specs

Each implementing plan lists the spec it amends in its `- Scope-Paths:`.

### 17.1 Runner spec `25kzda` (Order 04)

1. Section 3.2, rows `draft` (complete) and `to-review`: "run plan review" means the multi-prompt
   review of this spec, with the tier and grouping of Section 5.
2. Section 4.4, `IPD-REVIEW-HISTORY`: "Exactly one new review entry" becomes "exactly one new
   verdict-bearing review entry; progress entries without a verdict token are allowed" (MD-15).
3. Section 5.4 (queue ordering): an orchestrator whose action is `review` is ordered after the Set's
   children whose action is also `review`, as it already is for action `orchestrate`.
4. Sessions: all prompts of one review invocation run in one session; rotation by
   `max_items_per_session` happens only between review invocations, and one invocation counts as one
   item; a review never uses Antigravity's `--continue` fallback (MD-6, MD-13).
5. Section 2.6 is unchanged: plans created by a split never join the current run.

### 17.2 IPD structure-and-linting spec `20260802-1904` (Order 03)

Section 10.2, as stated in Section 11.3.

### 17.3 Reviews README (Order 01)

`.aw/records/reviews/README.md` describes the round layout of Section 7.1.

### 17.4 `/askme` (Order 01)

The recommendation labels in `.aw/system/workflows/askme/askme.md` change from three levels to the
five of MD-9.

## Workflow history

- 2026-10-24 note (aw specs): Maintainer ruling 2026-10-19: MD-1 revised; the runner forces no review tier. Section 5.2 replaced by five recorded tier questions with the former signals as facts and examples; tier and answers recorded for later analysis. OQ-08 resolved (no sensitive-path list).
- 2026-10-19 note (aw specs): Post-review additions (no change to MD-1..MD-18): measured runner tier signals over 1,554 plans (5.2); step-file source map from plan-review.md (4.3); mid-review tier change rule (5.3); Step evidence line and re-ask wording (6); children-before-orchestrator for review is a queue-order change, not current behavior (5.1); Section 17 lists the exact amendments to 25kzda, 20260802-1904, the reviews README, and askme; tmp/ evidence replaced by prompt okj4bg and backlog items i2i81x and rsisop.
- 2026-10-19 note (aw specs): /spec-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; SR-001..SR-010 FIXED. Maintainer rulings MD-15 (verdict outputs once at loop end, S7 own prompt), MD-16 (no-go stays reviewed; 9.4 clearing path), MD-17 (pilot + sized experiment, single-12 default), MD-18 (quoted-text form). OQ-02 resolved; OQ-10 and OQ-11 added, non-blocking at spec level.
- 2026-10-19 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; SR-001..SR-010 all FIXED; record .aw/records/reviews/20261017-k3yx72-01-k3yx72-plan-review-redesign.review.md
- 2026-10-19 to-review (aw set): Complete draft admitted for /spec-review (named explicitly by id6; 25kzda 2.5a)

- 2026-10-17 note (aw specs): Revised after the four-model design review (reconciliation vcg8mz) and maintainer rulings MD-1 to MD-14: review tiers with prompt counts, orchestrator profile, runner tier signals (option B), single Findings table per round, pass-relative re-review baseline, marker re-ask, outcomes, session and resume rules, split as a graph rewrite, citation resolver report-only, 4sd62s compatibility, and the grouping experiment.
- 2026-10-17 created (aw specs): Replace single-turn /plan-review with runner-enforced discrete steps: proofread, complexity-scaled review depth, AW-REVIEW re-review marker, split step, durable citations; retire plan-review-long
