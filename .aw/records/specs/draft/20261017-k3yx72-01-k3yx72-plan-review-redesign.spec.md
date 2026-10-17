# Spec: Runner-enforced, depth-scaled plan review

- Date: 2026-10-17
- Status: draft
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

## 1. Problem

1. **Review is the largest cost.** The runner analytics attribute about half of all recorded agent
   cost to review. A direct read of 1,311 OpenCode review attempts (2026-10-17) found 16.05 billion
   tokens and $10,528 of recorded cost. 98.8 percent of the tokens were cache reads: each model step
   re-sends the whole conversation. The median attempt took 50 model steps and ended with a
   234,000-token context. Review cost is therefore roughly the number of steps multiplied by the
   context size per step. Most context is tool output: `bash` produced 71 percent of tool output
   bytes and `read` 27 percent.
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
| MD-1 | The review agent rates the review tier. The runner raises the tier only for a few signals that are almost never wrong (Section 5.2). The agent may raise the tier freely and may lower it below a runner signal only with a recorded reason. (Revised 2026-10-17: option B.) |
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
| MD-14 | Prompt counts are `simple` 1 to 2 prompts, `standard` 4 prompts, and `complex` either 6 grouped or 12 single prompts. The experiment in Section 13 chooses between the two `complex` variants. |

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
4. Computes the runner tier signals (Section 5.2).
5. Records the plan's content digest as the review baseline.
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
| S7 Finalize | Write `- Readiness:`, the review history entry, and the final commit (Section 7.2). |

## 5. Review tiers

### 5.1 Checks per tier

| Tier | Intended plans | Checks |
| --- | --- | --- |
| `simple` | Very low risk: typically a few lines of code, such as a small bug fix or one new CLI option. | P, T, Q, S5, S6, S7. R3 short form only when a runner signal names a sensitive path. |
| `standard` | Most medium plans. | P, T, R1, R2, R3 (full), R4, S5, S6, S7. |
| `complex` | Large, cross-cutting, or contract-changing plans. | P, T, R1, R2, R3 (full), R4, R5, R6, R7 (Sets), S5, S6, S7. |
| `orchestrator` | Every Order-00 orchestrator, whatever its size. Not rated by T. | P, R1, R2 (child table, coverage, ordering), R7 across the Set, S5, S6, S7. Never R5 or R6. |

A plan in a Set receives its own tier. When the queue holds a Set's children and its orchestrator,
the children are reviewed first, so the orchestrator's R7 and coverage check see the reviewed
children.

### 5.2 Runner tier signals

The runner raises the tier to `complex` when at least one of the following is true:

1. `- Scope-Paths:` names a `.spec.md` file.
2. The plan exceeds the existing size-lint limits in `agent_workflows/ipd_schema.py`
   (`MAX_E_LEAVES` = 18 execution items, or `MAX_TASK_GROUPS` = 5 task groups).
3. `- Scope-Paths:` matches a path in the configured sensitive-path list
   `review.sensitive_paths` in `.aw/config/project.json`. The package default is an empty list;
   this repository seeds its own list.

The runner raises the tier to `standard` when `- Scope-Paths:` is `grandfathered` (the plan does not
declare what it changes).

The agent's tier T is final when it is at or above the runner's tier. A lower tier requires a
recorded reason, and the runner accepts it. If review edits make a signal true that was false at
the pre-pass, the runner raises the tier and sends the newly required checks before S5.

### 5.3 Prompt grouping

| Tier | Variant | Prompts |
| --- | --- | --- |
| `simple` | - | 1: P+T+Q. 2: S5+S6+S7. When the plan has no open questions and Q records no finding, the runner may send prompt 2's checks in prompt 1 (one prompt total). |
| `standard` | - | 1: P+T. 2: R1+R2. 3: R3+R4. 4: S5+S6+S7. |
| `complex` | `grouped-6` | 1: P+T. 2: R1+R2. 3: R3. 4: R4+R5. 5: R6+R7. 6: S5+S6+S7. |
| `complex` | `single-12` | One prompt per check: P, T, R1, R2, R3, R4, R5, R6, R7, S5, S6, S7. R7 is skipped for a plan outside a Set (11 prompts). |
| `orchestrator` | - | 1: P+R1+R2. 2: R7. 3: S5+S6+S7. |

The grouping is a runner setting (`review_variant`), recorded in run state, so that both `complex`
variants use the same step files and differ only in grouping. Section 13 decides the default.

When the agent's tier T differs from the tier the first prompt assumed, the runner continues with
the prompt list of the final tier.

## 6. Postconditions

The runner checks these after each prompt. A check that fails triggers one re-ask (Section 4).

| Check | Postcondition |
| --- | --- |
| P | The structural preservation check passes (Section 6.1). The `### Proofreading` subsection exists in the current round. |
| T | The last non-empty line of the reply is exactly `AW-TIER: simple`, `AW-TIER: standard`, or `AW-TIER: complex`. A tier below the runner's tier has a recorded reason. |
| Q, R1 to R7 | The current round has a `### Step <check>` subsection for each check in the prompt (for example `### Step R4`). Findings, if any, are rows in the round's single `### Findings` table (Section 7.1). R1 additionally: the runner re-runs the resolver and the agent addressed every result it reported. |
| S5 | Every open question has `Blocking:` and `Status:`. Every `Blocking: no` added or changed in this review has a rationale. `check.review-finding-unescalated` passes. |
| S6 | The marker rules in Section 8.1 are met. |
| S7 | One of: (a) `- Readiness:` holds `go`, `go-pending-approval`, or `no-go`; or (b) `- Readiness:` is absent and the round records an exhausted orchestrator repair (the existing `IPD-S407`/`IPD-S408` rule). The status transition is legal. `aw ipd lint --phase author` reports no error that was not present at the pre-pass. |

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

- Exactly one review history entry, in the existing `/plan-review (<agent/model>): <verdict>; ...`
  form (spec `25kzda` Section 4.4, `IPD-REVIEW-HISTORY`).
- Exactly one final commit whose subject starts with `plan-review:`
  (`agent_workflows/plan_readiness.py::review_staleness_index` finds the review by that prefix).
  The runner's fallback lane commit subject (`review(<host>): record the review of <id6>`) changes to
  the same prefix.
- `- Readiness:` and the review tier are written in S7, not earlier, so no mid-review write changes
  the reviewed text. The review tier is stored as `- Review-Depth: <tier>` (a new recognized field in
  `agent_workflows/ipd_schema.py::META_RECOGNIZED`), excluded from the review-staleness digest
  (Section 12 covers storage under `4sd62s`).

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
and the sections that depend on them, then S5 and S6. The runner gives the agent the diff since the
start of the previous pass.

At most two re-review passes are allowed. If the second pass still produces a re-review, S7 must
write `no-go` and add an open question `Blocking: yes` that names what still changed, so that
`aw ipd recheck-readiness` can clear it after a human looks.

## 9. Outcomes, sessions, and interruption

### 9.1 Outcomes

| Outcome | Meaning | Plan state afterwards |
| --- | --- | --- |
| `completed-pass` | S7 wrote `go` or `go-pending-approval`. | `reviewed` (existing transition). |
| `completed-negative` | S7 wrote `no-go`, or `- Readiness:` is absent after an exhausted orchestrator repair. Findings and blocking questions are kept. | Stays at `to-review`. |
| `incomplete` | A re-ask failed, or a host failure could not be recovered. | Restored to the last completed step's content; stays at `to-review`; the run records the reason. |

### 9.2 Sessions

- All prompts of one review invocation use one session (MD-6).
- The runner captures the session id after the first prompt and resumes by that id for every later
  prompt. If no id was captured, it starts a new session (MD-13).
- Session rotation (`max_items_per_session`) never happens between prompts of one review
  invocation. One review invocation counts as one item toward that limit.
- Whether each review invocation should start a new session or reuse the previous plan's session is
  not decided. Measured data is mixed (Section 1, and Section 13 variable V3).

### 9.3 Interruption and resume

The runner records, after each prompt: the review invocation id, the pass number, the last completed
prompt, the plan's content digest, and the session id.

On `aw <host> run resume`:

1. Restore the plan to the content recorded after the last completed prompt.
2. If the session can be resumed by id, continue with the next prompt in that session.
3. Otherwise, restart the review invocation at check P in a new session.

Each prompt and transcript gets a unique name per invocation, pass, prompt, and attempt, so a
resumed run does not overwrite earlier logs.

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
4. **Retirement.** The original moves to `.aw/records/plans/superseded/` through a tooled retirement
   command, with a `RETIRED` header that names the new Set. No such command exists today
   (retirement is a hand-written header plus `git mv`); Order 06 adds one.
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
| Quoted text | Syntax not decided (OQ-2). Must name a path and a single-line string that occurs exactly once in that file. | An edit to the string, or a second occurrence. |
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
  are not reported as `not-found`. (Exact marking syntax: OQ-2.)
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
| One review history entry per invocation | One `## Workflow history` line | One `review` event (`4sd62s` Section 4.1a) |
| Split field moves (Section 10 step 3) | Line edits through the existing setters | `set`/`unset` events through `artifact_meta` |
| Structural preservation check (Section 6.1) | Compares parsed front matter | Compares the folded event state |

Whichever ships first, the implementing plans must declare which format they target. If this spec's
plans run first, the `4sd62s` migration must carry `Review-Depth` like any other field.

## 13. Experiment: prompt grouping

### 13.1 Questions

1. For `complex` plans, does `grouped-6` cost less than `single-12` without finding fewer defects?
2. How does each model respond to each grouping: cost, steps, re-asks, and defects found?
3. (Optional, second round) Does a new session per review cost more or less than reusing the
   previous plan's session?

### 13.2 Prerequisites

- The analytics changes requested in `tmp/20261017-runs-analyze-review-cost.prompt.md` (to be filed
  as a backlog item): token types, steps and context size, session reuse, tool use, run commit and
  label, model, and redo counts.
- Runs record a label, the git commit, the review variant, and the model on every attempt.
- The step files and both groupings exist (Section 15 Orders 01 and 04).

### 13.3 Design

| Variable | Values |
| --- | --- |
| V1 Plans | 3 pending plans: 1 `standard`, 2 `complex`. For each, a copy with planted defects: a `V-*` item that asks for no evidence, a wrong file path, and a changed CLI option that another command reads. |
| V2 Grouping | `standard`: the single 4-prompt variant. `complex`: `grouped-6` and `single-12`. |
| V3 Models | Opus 5.5 High (OpenCode) and Gemini 3.8 Flash High (Antigravity). GPT-6.1 Sol only if a Codex host exists or by hand. |
| V4 Session | First round: fixed (new session per review). Second round: new versus reused, with the better grouping. |

Each combination runs twice. First round: about 24 reviews. Each review runs in its own worktree
from the same commit with a run label.

### 13.4 Measures

Per review: tokens by type (new input, cache read, cache write, output, reasoning), model steps,
context size per step, wall time, cost where recorded (tokens otherwise; Antigravity records no
cost), re-asks and failed postconditions, re-review passes, verdict, and planted defects found.

### 13.5 Decision rule

Choose the variant with the lower median token cost unless it finds fewer planted defects in total
across both models. With two runs per combination the results are read review by review; a
difference smaller than about two times is not treated as real. Record the results as a research
report in Set `revsteps`.

## 14. Acceptance criteria

1. A `simple` plan is reviewed in at most 2 prompts, a `standard` plan in 4, and a `complex` plan in
   6 or 12 according to `review_variant`; demonstrated on fixture plans with the scripted host.
2. The runner refuses a proofreading edit that changes an `E-*` checkbox, and restores the plan.
3. A malformed `AW-REVIEW:` line causes exactly one re-ask, and a second failure ends the invocation
   as `incomplete` without writing `- Readiness:`.
4. A re-review pass that changes nothing ends the loop; a fixture whose first pass adds an E/V pair
   and whose second pass changes nothing finishes `completed-pass`.
5. A finding recorded in pass 1 and not fixed still gates the plan after pass 2 (it appears in the
   round's single `### Findings` table and `review_findings.subject_gating_blocks` reports it).
6. One review invocation with two passes produces exactly one review history entry and one
   `plan-review:` commit.
7. Runner signals raise the tier for a plan that edits a `.spec.md` file, and the review records the
   agent's reason when it rates lower.
8. A split of a plan carrying `From-Backlog` and `Blocks-Release` leaves the backlog item closable
   through the new plans, and rewrites another plan's `executed:<original>` dependency.
9. A split of a plan that was `approved` at review start is refused.
10. The resolver reports `not-found` for a renamed symbol, `ambiguous` for a duplicated quoted
    string, and treats a trailing line number as a hint; it never changes an exit code to blocking.
11. An interrupted review resumes at the next prompt in the same session, or restarts at check P in
    a new session when the session is gone.
12. `/plan-review-long` no longer exists in the installed workflows, command shims, or index.
13. The experiment in Section 13 has run and its result is recorded.

## 15. Work breakdown (proposed Set `revsteps`)

| Order | Work | Depends on |
| --- | --- | --- |
| 00 | Orchestrator. Child tracking only. | All children |
| 01 | Step files under `.aw/system/workflows/plan-review/steps/`, the `/plan-review` checklist, the proofreading adaptation, the review record layout (Section 7.1) and its README amendment, and the five-level recommendation strength in `/plan-review` and `/askme`. | Spec approval |
| 02 | `Review-Depth` field, runner tier signals, and the `review.sensitive_paths` setting. | Spec approval |
| 03 | Citation resolver, its review and `aw ipd begin` integration, and the `20260802-1904` Section 10.2 amendment. | Spec approval |
| 04 | Runner multi-prompt review for both hosts: prompt lists per tier and `review_variant`, postconditions, re-ask, structural preservation check, outcomes, session handling, resume. | 01, 02, 03 |
| 05 | Re-review marker, runner triggers, and the loop. | 04 |
| 06 | Split step, including the graph changes and a tooled retirement command. | 04 |
| 07 | Retire `/plan-review-long` (workflow, shims, index, installer entries, current docs, tests). | 01, 04 |
| 08 | Records README and `AGENTS.md` pointers: read a tree's README before editing an artifact in it. | 01, 03 |
| 09 | Run the experiment (Section 13) and set the default `review_variant`. | 04, 05, analytics backlog item |

Separately filed backlog items (not part of this Set):

- Analytics breakdowns and run labels for `aw runs analyze` (prompt
  `tmp/20261017-runs-analyze-review-cost.prompt.md`).
- A shorter pipeline for small changes: skip the backlog step and go from plan to review to
  execution.

## 16. Open questions

### OQ-2: Quoted-text citation syntax

- Blocking: yes (for Order 03)
- Status: open
- Question: How is a quoted-text citation written? Candidates from the design review: `` `path` "text" ``; `path::quote("<JSON string>")`; `path::"text"`. All three require one line and a unique match.
- Recommendation: `path::"text"`, because it extends the `path::Symbol` form and needs no new escape language for most strings; use the JSON form only when the text contains a double quote. Strength: weak.

### OQ-7: Session per review

- Blocking: no
- Status: open
- Question: Should each review invocation start a new session, or reuse the previous plan's session?
- Data: of 1,311 review attempts, 404 in a session new to the run had a median 36,000-token first context, 81 steps, and $9.21 cost; 907 in a reused session had 229,000, 43 steps, and $6.78. The groups differ in period, plans, and models, so the comparison is not controlled.
- Recommendation: decide by Section 13 variable V4. Until then, keep today's behavior. Strength: medium.

### OQ-8: Sensitive-path list for this repository

- Blocking: no
- Status: open
- Question: Which paths in this repository go into `review.sensitive_paths`?
- Candidates: the leak sanitizer, `git_commit_helper`, `lane_containment`, the integration lock, the sandbox and egress code.
- Recommendation: start with those five and add paths when a `simple` review misses a problem there. Strength: weak.

### OQ-9: Codex host for the experiment

- Blocking: no
- Status: open
- Question: Should the experiment include GPT-6.1 Sol? The runners do not drive Codex today.
- Recommendation: run the first round with the two runner hosts and add Codex by hand only if the two disagree. Strength: weak.

## Workflow history

- 2026-10-17 note (aw specs): Revised after the four-model design review (reconciliation vcg8mz) and maintainer rulings MD-1 to MD-14: review tiers with prompt counts, orchestrator profile, runner tier signals (option B), single Findings table per round, pass-relative re-review baseline, marker re-ask, outcomes, session and resume rules, split as a graph rewrite, citation resolver report-only, 4sd62s compatibility, and the grouping experiment.
- 2026-10-17 created (aw specs): Replace single-turn /plan-review with runner-enforced discrete steps: proofread, complexity-scaled review depth, AW-REVIEW re-review marker, split step, durable citations; retire plan-review-long
