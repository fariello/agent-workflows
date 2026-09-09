# IPD: Require an affirmative or negative defect report from every execute turn and re-ask once in session when it is missing

- Date: 2026-09-08
- Kind: child
- Concern: AN EMPTY LIST MEANS BOTH "I CHECKED AND FOUND NOTHING" AND "I NEVER LOOKED", AND NOTHING EVER ASKS WHICH. The execute prompt already demands a JSON outcome file carrying `incomplete_requirements` (`agent_workflows/oc_runipd.py:4902`, twin `agy_runipd.py:2445`) and the run viewer already reads and renders it (`run_viewer.py:82`, `:910`, `:1662-1663`). But the field is presented as `[]` in the schema literal, an empty value is indistinguishable from an unasked question, and no code path treats silence as a defect. So an agent that stumbles across a real bug and says nothing is INDISTINGUISHABLE from an agent that verified there was nothing to say.
  AND THE FIELD IS THE WRONG SHAPE FOR THE JOB EVEN WHEN FILLED. `incomplete_requirements` is scoped to THIS PLAN's own unmet requirements. Most of what an agent actually finds is neither: a bug in adjacent code, a gap between a spec and its implementation, a concern about a design it had to work around. There is no field for any of that, so the honest agent's only channel is `summary` prose, which no gate reads.
  THE MEASURED FAILURE MODE IS SCHEMA ADHERENCE, NOT SYNTAX, AND THIS PLAN MUST TARGET THE RIGHT ONE. Measured across the 223 agent-written outcome files present at authoring: ZERO malformed JSON, ZERO markdown fences wrapping JSON, ZERO unterminated strings. Agents emit syntactically valid JSON reliably here. What they do NOT do reliably is honor the intended SHAPE of a list element: backlog `rbftpl` measured 132 dicts against 126 bare strings out of 258 entries, re-measured at authoring as 132 dicts against 131 strings out of 263. So roughly half the time an agent writes prose where an object was wanted, inside perfectly valid JSON. A plan that adds a field without validating its element shape will collect the same 50% prose.
  THE MAINTAINER'S RULING, 2026-09-08, which this plan implements: "The instructions on executing an IPD must ask the agent to report any found bugs, gaps, concerns both affirmatively and negatively. If there are none, it must say so in a parsable manner. If there were, it must say so in a parsable manner. If neither exists, the runner must ask the agent to add it. The best design is one where when the agent is 'done' with an IPD, the runner asks the agent (in the same session) to fill out an outstanding bugs/gaps/etc. report."
  AND WHY IT IS A PREREQUISITE RATHER THAN A NICE-TO-HAVE. The same ruling states it is "a requirement before we can implement the check to see if a backlog / IPD exists for each item". Plan `rnkqrc` (`durablecapture-01`) is that check: it refuses a plan's transition to `executed` while it names an unfixed defect with no durable carrier. `rnkqrc` can only verify a DECLARED carrier; it cannot see a defect nobody declared. This plan produces the declaration, which is what makes `rnkqrc` more than a formality.
- Scope: Add a REQUIRED, explicitly tri-state defect report to the execute-turn outcome contract, validate each field's TYPE with tolerant coercion, and re-ask ONCE in the same session when the report is absent or ambiguous, feeding the specific violation back to the agent. Then teach the prompt the carrier rule: file a backlog item, and treat a spec as supporting material only. EXCLUDES the transition gate that consumes the report (`rnkqrc` owns it); EXCLUDES changing the verifier turn's separate verdict contract; EXCLUDES reading or fixing `incomplete_requirements`'s existing 50% prose entries retroactively.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, tests/test_defect_report.py
- Item-Dependencies: none
- Status: to-review
- Set: defreport
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: b7xarm

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored on a MAINTAINER RULING given while answering `rnkqrc` OQ-01, not from a backlog item, so it carries no `From-Backlog`. The ruling arrived as a challenge to `rnkqrc`'s premise: asked whether a spec should count as a durable carrier, the maintainer answered NO (carriers are a backlog item or a pending plan only) and then rejected the framing, asking how the runner could possibly "know" an unfixed defect exists. THAT CHALLENGE WAS CORRECT. `rnkqrc` cannot detect a defect; it is a DECLARATION gate that checks only mechanical facts (does a typed field exist, does its id6 resolve, is the target non-terminal). Confirmed by reading its E-01, which explicitly refuses prose matching as "spoofable by any incidental mention and brittle against rewording", and by its own F-6: 530 plans exist and ZERO carry the field, so on day one it catches nothing. The maintainer's response was to require the DECLARATION be produced, in session, before the check is built. This plan is that requirement. THREE DESIGN DECISIONS WERE TAKEN BY THE MAINTAINER AND ARE RECORDED SO AN EXECUTOR DOES NOT RE-OPEN THEM. (1) RE-ASK MECHANISM: ask once in the SAME session, rather than refusing the outcome as malformed. The cheaper alternative (hard error, no loop) was offered and rejected, because a forgetful agent's whole turn would be discarded over a missing report. (2) SPEC RULE: ALWAYS file the backlog item; a spec is supporting material, never the carrier. The maintainer's literal wording allowed the agent to judge whether a case was "just a spec" and then file a spec-review backlog item; offered the simpler rule that removes the judgement entirely, the maintainer chose it, having already said "I don't know when 'just a spec' would be enough". (3) FORMAT: the maintainer challenged JSON, citing cross-project research (currently being hit on another project) that agents generate rigorous JSON less reliably than structured markdown. I pushed back with in-repo evidence: D139 (maintainer-approved 2026-08-21) already fixes YAML-for-human-source and JSON-for-machine-consumption in one decision; no research in THIS repo compares agent EMISSION reliability across formats, and the one report raising it filed it unmeasured; the measured syntactic failure rate here is 0 of 223; and YAML specifically is contraindicated (D139 forecloses a runtime YAML parser, the token research flagged YAML offsets as brittle, and pending plan `xo3244` exists ONLY because YAML front matter in the research tree is invisible to the selector, 52 files carrying a status where 5 are found). The maintainer accepted JSON WITH AN EXPLICIT CAVEAT that is now a binding constraint: the concern applies to LARGER payloads, so THE REPORT MUST STAY SMALL, and if it grows the format decision must be revisited. That caveat is recorded as OQ-02 and enforced by E-01's field budget.

## Goal

Make an execute turn state, in a form a tool can read, whether it found any bugs, gaps or concerns, so that "nothing was reported" stops meaning "nobody knows", and so the transition gate `rnkqrc` builds has something real to verify.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: define the smallest report that answers the question

- [ ] E-01 DEFINE THE TRI-STATE REPORT SCHEMA IN `runner_shared.py`, host-neutral, and BUDGET ITS SIZE EXPLICITLY. Three states must be distinguishable and the third must not be silently reachable: FOUND (one or more findings), NONE-FOUND (an affirmative statement that the agent looked and found nothing), and ABSENT (neither statement present), which is the state E-04 re-asks on.
  DO NOT ENCODE THE STATE AS AN EMPTY LIST. That is the whole defect: `incomplete_requirements: []` already means both "checked, nothing" and "never looked". The state must be carried by an explicit value, so a missing key and a considered "none" are different bytes.
  SIZE IS A BINDING CONSTRAINT, NOT A PREFERENCE. The maintainer accepted JSON on the express condition that the report stay SMALL, because the format concern applies to larger payloads. So: a flat structure, a fixed and minimal key set, and no nesting beyond one list of small objects. Write the budget into the schema comment along with the reason, so a later author who wants to add a fifth field sees why they should not.
  EACH FINDING NEEDS ONLY WHAT A CARRIER DECISION REQUIRES: what was found, and where. Resist adding severity taxonomies, reproduction steps or triage fields; every one of those is a field an agent can get wrong and none is needed to decide whether a backlog item should exist.
  ONE SCHEMA, BOTH HOSTS. Define it once here; `oc_runipd` and `agy_runipd` reference it. Both prompt builders are already a known divergence surface, and a second copy of a schema literal is how the two hosts silently disagree.
  - Depends on: none
  - Expected outcome: one host-neutral tri-state schema with a fixed minimal key set, ABSENT distinguishable from NONE-FOUND by explicit value rather than emptiness, and a written size budget with its rationale.
  - Execution state: pending

### Task group 2: ask for it, affirmatively and negatively

- [ ] E-02 PUT THE DEMAND IN BOTH EXECUTE PROMPTS, in `oc_runipd.build_prompt` (`:4785`) and `agy_runipd.build_prompt` (`:2297`), alongside the existing outcome-JSON block (`oc_runipd.py:4886-4906`, `agy_runipd.py:2429-2449`).
  DEMAND BOTH DIRECTIONS EXPLICITLY. The prompt must say that finding nothing is a REPORTABLE RESULT that must be stated, not an absence to be left implicit. An instruction that only describes what to do when something IS found produces exactly today's ambiguity.
  SAY WHAT COUNTS, BRIEFLY, because the existing `incomplete_requirements` field trained agents to think only about THIS plan's unmet requirements. Bugs in adjacent code, gaps between a spec and its implementation, and design concerns worked around all count, and none of them fits the existing field.
  KEEP BOTH HOSTS' WORDING IDENTICAL, for the same reason as E-01.
  DO NOT REMOVE OR REPURPOSE `incomplete_requirements`. It has a live reader (`run_viewer.py:910`, `:1662`) and a distinct meaning (this plan's own unmet requirements). Adding a second, differently-scoped field is correct; overloading the first would break a working display.
  - Depends on: E-01
  - Expected outcome: both execute prompts demand the report, state that finding nothing must be affirmatively reported, name briefly what counts, use identical wording, and leave `incomplete_requirements` intact.
  - Execution state: pending

- [ ] E-03 TEACH THE PROMPT THE CARRIER RULE, which is the maintainer's ruling and the reason this plan feeds `rnkqrc`. The agent must be told: for each finding, FILE A BACKLOG ITEM. A spec may and should be written where a spec is genuinely what the work needs, and it should be referenced, but A SPEC IS NEVER THE CARRIER.
  DELEGATE NO JUDGEMENT ABOUT "JUST A SPEC". The maintainer explicitly chose the rule that removes it: always file the backlog item, treat any spec as supporting material. Do NOT implement a branch where the agent decides a case is spec-only and files something different; that judgement is the failure mode the rule exists to prevent, and the maintainer said plainly they do not know when "just a spec" would be enough.
  NAME THE TOOL, NOT THE FILE FORMAT. The agent should be pointed at `aw backlog new`, because a hand-written backlog file misses the minted id6 and the clustered filename, and the repository's own conventions forbid hand-naming records.
  DO NOT MAKE THE AGENT BLOCK ON FILING. If filing fails or the agent is out of scope to file, the REPORT is still required: an unreported finding is the defect this plan closes, and a reported-but-unfiled finding is strictly better than silence. State that order of priority explicitly in the prompt.
  - Depends on: E-02
  - Expected outcome: both prompts instruct the agent to file a backlog item per finding via `aw backlog new`, name a spec as supporting material only, delegate no just-a-spec judgement, and prioritize reporting over filing when the two conflict.
  - Execution state: pending

### Task group 3: validate the shape, then re-ask once

- [ ] E-04 VALIDATE PER FIELD WITH TOLERANT COERCION, because the measured defect is shape, not syntax. Agents here emit valid JSON (0 of 223 malformed) while writing prose where an object was wanted about half the time (132 dicts against 131 strings across 263 entries, backlog `rbftpl`).
  COERCE WHAT IS SAFELY COERCIBLE AND SAY SO. A bare string where a small object was expected carries the same fact in prose; accept it into a normalized form and RECORD that a coercion happened, rather than discarding a real finding on a formatting technicality. Discarding it would reproduce the silence this plan exists to end.
  DISTINGUISH THE THREE OUTCOMES THE VALIDATOR CAN REACH, and do not collapse them: VALID (used as-is), COERCED (used, with the coercion recorded), ABSENT-OR-AMBIGUOUS (triggers E-05's re-ask). Collapsing coerced into valid hides how often the schema is being missed; collapsing it into invalid throws away findings.
  NEVER RAISE, AND NEVER FAIL THE TURN ON THIS ALONE. A validator that crashes on unexpected input is a validator that gets wrapped in a bare `except` and neutered, which is exactly what happened to the spec-edit announcement (`oc_runipd.py:4149-4151`, `except Exception: pass`). Return a structured verdict.
  - Depends on: E-03
  - Expected outcome: a non-raising per-field validator returning VALID / COERCED / ABSENT-OR-AMBIGUOUS, coercing a bare string into the normalized finding form while recording the coercion, and never failing the turn by itself.
  - Execution state: pending

- [ ] E-05 RE-ASK ONCE, IN THE SAME SESSION, when E-04 reports ABSENT-OR-AMBIGUOUS. This is the maintainer's chosen design and it was chosen over the cheaper alternative deliberately: refusing the outcome as malformed would discard a whole turn's work over a missing report.
  IT MUST BE THE SAME SESSION, NOT A NEW TURN. The value is that the agent still holds the context of what it just did; a fresh session would have to re-derive its own findings from the diff, which is both expensive and less accurate. The runner has NO re-ask loop today, so this is new machinery and must be built as one narrow, reusable step rather than inline in one host's dispatch path.
  BOUND IT AT EXACTLY ONE ATTEMPT. An unbounded or multi-attempt loop turns a missing field into an open-ended spend. If the re-ask also fails to produce a parsable report, record THAT fact durably and move on; "the agent was asked and did not answer" is itself a finding a human should see, and it is materially different from "nobody asked".
  FEED THE SPECIFIC VIOLATION BACK. Do not re-send the original instruction verbatim. Say what was missing or ambiguous, because a generic re-ask invites the same output again. This is also where a shape violation from E-04 gets a second chance to be stated correctly.
  DO NOT RE-ASK A TURN THAT HAS NOTHING TO REPORT ON. A turn that never started work, or was stopped, or was blocked before doing anything, should not be billed for a follow-up. Decide the predicate from the turn's own recorded disposition and state it.
  - Depends on: E-04
  - Expected outcome: exactly one same-session re-ask naming the specific violation, skipped for a turn that did no work, with a durable record when the re-ask itself yields nothing.
  - Execution state: pending

### Task group 4: persist it where a gate can read it, and prove it

- [ ] E-06 PERSIST THE NORMALIZED REPORT ON THE RUN RECORD, beside the fields that already carry per-item results (`item["last_outcome"]`, `oc_runipd.py:6641`; `attempt["disposition"]` and `attempt["verification"]` just above it), so a later consumer reads a normalized structure rather than re-parsing an agent's raw file.
  THIS IS THE HANDOFF TO `rnkqrc`, so make it legible as such. Record the tri-state explicitly, the normalized findings, whether a coercion occurred, and whether a re-ask happened and what it produced. A gate that must distinguish "no defects found" from "never asked" needs all four.
  DO NOT BUILD THE GATE HERE. `rnkqrc` owns the transition refusal. This plan's obligation ends at producing a reliable, machine-readable record; consuming it is that plan's E-02 through E-04.
  WRITE IT ON BOTH HOSTS AT THE SAME SEAM. Both drivers already write these per-item fields in mirrored code; a field written by one host only would make the gate's behavior depend on which runner executed the plan.
  - Depends on: E-05
  - Expected outcome: the normalized report, its tri-state, any coercion, and the re-ask result all persisted on the run record by BOTH hosts at the existing per-item seam, with no gate logic added.
  - Execution state: pending

- [ ] E-07 PROVE EVERY STATE AND THE TWO CASES THAT MUST NOT FIRE, in a new `tests/test_defect_report.py`. Minimum cases: (a) FOUND with well-formed findings, used as-is; (b) NONE-FOUND stated affirmatively, accepted with NO re-ask; (c) ABSENT, triggering exactly ONE re-ask; (d) a bare string where an object was expected, COERCED and recorded as coerced rather than discarded; (e) the re-ask itself producing nothing, recorded durably; (f) a turn that did no work, NOT re-asked; (g) both hosts producing the identical persisted shape.
  CASE (b) IS THE POINT OF THE WHOLE PLAN. An affirmative "I looked and found nothing" must be accepted silently and must be distinguishable on disk from case (c). If a test cannot tell (b) from (c), the plan has not been implemented.
  CASE (d) IS THE MEASURED DEFECT. Assert the coercion is RECORDED, not just that it succeeded, since a silent coercion hides a 50% schema-miss rate.
  ASSERT THE RE-ASK IS BOUNDED AT ONE, explicitly, by counting invocations. An off-by-one here is an unbounded spend on a live run.
  DO NOT SPEND REAL MODEL TURNS. Stub the host invocation the way the existing driver tests do; a test that actually calls a model is neither deterministic nor free.
  - Depends on: E-06
  - Expected outcome: seven cases passing, with NONE-FOUND provably distinguishable from ABSENT on disk, the coercion recorded, the re-ask count asserted as exactly one, and no real model turn spent.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE CHANNEL AND A READER ALREADY EXIST. The prompt demands an outcome JSON (`oc_runipd.py:4886-4906`, `agy_runipd.py:2429-2449`) and `run_viewer` parses and renders `incomplete_requirements` (`:82`, `:910`, `:1662-1663`). This plan adds a field and a validator, not a new channel.
- BUT THE EXISTING FIELD IS DIFFERENTLY SCOPED. `incomplete_requirements` means THIS plan's unmet requirements. A bug in adjacent code has no home today.
- JSON IS THE ADOPTED FORMAT FOR MACHINE-CONSUMED OUTPUT, by maintainer-approved decision D139 (2026-08-21): YAML for human-authored source, JSON for what machines consume. A runtime YAML parser is foreclosed by that same decision.
- AND THE MEASURED EMISSION FAILURE IS SHAPE, NOT SYNTAX. 223 agent-written outcome files: 0 malformed, 0 fenced, 0 unterminated. Versus `rbftpl`'s measured ~50% bare-string-where-object-expected (132/131 of 263 at authoring). Validate types; do not switch formats.
- SIZE IS THE MAINTAINER'S STANDING CAVEAT on the format choice: JSON is accepted while the payload is SMALL. Treat the key set as a budget.
- A BARE `except Exception: pass` IS THE LOCAL ANTI-PATTERN TO AVOID. The spec-edit announcement was silenced exactly that way (`oc_runipd.py:4149-4151`) and plan `st5klo` exists to undo it. A validator must return a verdict, not vanish.
- THERE IS NO RE-ASK LOOP TODAY. `build_prompt`, `build_verifier_prompt`, `build_review_prompt` and `write_prompt` are the only prompt paths (`oc_runipd.py:4785`, `:4913`, `:4315`, `:4982`); none re-prompts an existing session. E-05 is new machinery.
- THE PER-ITEM RESULT SEAM IS ESTABLISHED: `item["last_outcome"]`, `item["status"]`, `item["verification_status"]` written together (`oc_runipd.py:6639-6642`), mirrored in `agy_runipd`.
- HAND-NAMING RECORDS IS FORBIDDEN, so E-03 must point the agent at `aw backlog new` rather than at a path.
- Both driver files are under concurrent edit by live runs and their line numbers moved by roughly 70 and 95 lines in a single day. Re-locate every symbol by NAME. The suite runs BARE.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | an empty list is two different facts | `incomplete_requirements: []` means both "checked, found nothing" and "never looked", and no code distinguishes them. | `oc_runipd.py:4902`; `agy_runipd.py:2445`; `run_viewer.py:910` |
| F-2 | HIGH | nothing ever asks | No path treats a missing or empty report as a defect; there is no re-ask anywhere. Only four prompt builders exist and none re-prompts a live session. | `oc_runipd.py:4785`, `:4913`, `:4315`, `:4982` |
| F-3 | HIGH | the existing field is the wrong scope | `incomplete_requirements` covers THIS plan's unmet requirements, so an adjacent-code bug or a spec-implementation gap has no typed home. | field name and its `run_viewer` rendering |
| F-4 | HIGH | **the measured defect is shape, not syntax** | 223 agent-written outcome files: 0 malformed, 0 markdown fences, 0 unterminated. Versus 132 dicts / 131 bare strings across 263 entries in one list field. So validate types; a format change fixes nothing. | measured at authoring; backlog `rbftpl` |
| F-5 | HIGH | this is `rnkqrc`'s missing half | `rnkqrc` refuses a transition on a DECLARED carrier and cannot see an undeclared defect; its own F-6 records 530 plans with ZERO carrying the field. The maintainer ruled the declaration must exist first. | `rnkqrc` E-01, F-6; maintainer ruling 2026-09-08 |
| F-6 | MEDIUM | JSON is the adopted machine format | D139 (maintainer-approved 2026-08-21) fixes YAML-for-human-source and JSON-for-machine-consumption in one decision, and forecloses a runtime YAML parser. | `DECISIONS.md` D139 |
| F-7 | MEDIUM | and YAML is specifically contraindicated here | The token research rejected a YAML registry partly for brittle offsets and merge conflicts; pending `xo3244` exists ONLY because YAML front matter in the research tree is invisible to the selector (52 carry a status, 5 are found). | token-efficiency findings; `xo3244` |
| F-8 | MEDIUM | the maintainer's format caveat is binding | JSON accepted on the express condition the report stays SMALL, the concern being larger payloads. Recorded as OQ-02 and enforced by E-01's budget. | maintainer, 2026-09-08 |
| F-9 | MEDIUM | silencing a validator is a live local anti-pattern | The spec-edit announcement is wrapped in `except Exception: pass`, and plan `st5klo` exists to undo exactly that. | `oc_runipd.py:4149-4151`; `st5klo` |
| F-10 | LOW | absence of an outcome file has a separate cause already fixed | `t74o5q` measured 23 verifier turns (40%) with no outcome file, caused by a stale plan path, fixed at `1549c018`. That is a different failure from an incomplete report and must not be conflated. | backlog `t74o5q` |
| F-11 | LOW | no `From-Backlog` to carry | This plan comes from a maintainer ruling given in an OQ answer, not from a backlog item, so the field is legitimately absent. | authoring context |

## Proposed changes (ordered, validatable)

1. Define the small tri-state schema once, host-neutral, with a written size budget (E-01).
2. Demand the report in both execute prompts, affirmatively and negatively (E-02).
3. Teach the carrier rule: always a backlog item, a spec is supporting material only (E-03).
4. Validate per field with tolerant coercion, never raising (E-04).
5. Re-ask exactly once in the same session, naming the specific violation (E-05).
6. Persist the normalized report on the run record for `rnkqrc` to consume (E-06).
7. Prove all seven cases, especially NONE-FOUND versus ABSENT (E-07).

## Deferred / out of scope (with reason)

- THE TRANSITION GATE THAT CONSUMES THIS REPORT. `rnkqrc` (`durablecapture-01`) owns refusing a plan's move to `executed` while an unfixed defect has no durable carrier. This plan produces the declaration; that plan verifies it. Building both here would make neither reviewable.
- THE VERIFIER TURN'S VERDICT CONTRACT. `build_verifier_prompt` has its own separate schema and its own live defects (`1bfppy`, `fzxfph`, `bxx9af` all touch verdict handling). Widening this plan into it would collide with three pending plans.
- RETROACTIVELY FIXING THE EXISTING 50% PROSE ENTRIES in `incomplete_requirements`. `rbftpl` measured them and graduated to its own plan. This plan prevents the pattern in the NEW field; rewriting historical run records would falsify history.
- CHANGING OR REMOVING `incomplete_requirements`. It has a live reader and a distinct meaning. Overloading it would break a working display for no gain.
- SWITCHING THE REPORT TO MARKDOWN OR YAML. Considered at the maintainer's request and settled: JSON, per D139, with the size caveat as OQ-02. A markdown report would additionally need a real CommonMark parser and an adversarial fixture corpus, which the repo's own linting research already found necessary and hard.
- A MULTI-ATTEMPT OR UNBOUNDED RE-ASK. E-05 is bounded at one deliberately; an unbounded loop converts a missing field into open-ended spend.
- MAKING THE AGENT BLOCK ON SUCCESSFULLY FILING A BACKLOG ITEM. Reporting outranks filing (E-03): a reported-but-unfiled finding is strictly better than silence, which is what this plan exists to end.
- A SEVERITY TAXONOMY OR TRIAGE FIELDS on a finding. Every added field is a field an agent can get wrong, and none is needed to decide whether a backlog item should exist. Excluded by E-01's size budget.
- FIXING THE ABSENT-OUTCOME-FILE CASE (F-10). Different cause, already fixed at `1549c018` for the measured instance.

## Scope check

- Over-scope: none. One schema, two prompt additions, one validator, one bounded re-ask, one persisted field, one test file.
- Scope-Paths justification: `agent_workflows/runner_shared.py` is where the host-neutral schema (E-01) and validator (E-04) belong, beside the other shared run-policy machinery, so neither host owns a private copy; `agent_workflows/oc_runipd.py` holds `build_prompt` (`:4785`) and its outcome-JSON literal (`:4886-4906`) that E-02/E-03 extend, the `except Exception: pass` anti-pattern E-04 must not repeat (`:4149-4151`), and the per-item result seam (`:6639-6642`) E-06 writes at; `agent_workflows/agy_runipd.py` holds the twin builder (`:2297`) and outcome literal (`:2429-2449`) so both hosts change identically; `tests/test_defect_report.py` is new because no existing module covers the outcome contract end to end.
- Under-scope, stated rather than left as `none`: this plan builds no transition gate, touches no verifier verdict logic, rewrites no historical run record, does not modify `incomplete_requirements`, adds no severity taxonomy, does not make filing mandatory, and amends no spec (see the sync section, which explains why the outcome contract's home is unsettled).

## Required tests / validation

- SEVEN CASES (E-07), each named with pasted output: FOUND used as-is; NONE-FOUND accepted with no re-ask; ABSENT triggering exactly one re-ask; a bare string COERCED and the coercion recorded; a fruitless re-ask recorded durably; a no-work turn NOT re-asked; both hosts persisting an identical shape.
- THE NONE-FOUND VERSUS ABSENT DISTINCTION PROVEN ON DISK, by pasting the two persisted records side by side and showing they differ. If they are byte-identical the plan has failed.
- THE RE-ASK COUNT ASSERTED AS EXACTLY ONE, by counting invocations, not by inspecting a log.
- THE COERCION RECORDED, not merely successful: paste the record showing a shape violation occurred, since a silent coercion would hide the measured 50% schema-miss rate.
- HOST SYMMETRY: the prompt text added to both hosts shown byte-identical (diff the two strings or paste the shared constant with both references), and the persisted shape shown identical.
- NEGATIVE PROOF THAT `incomplete_requirements` IS UNTOUCHED: `git diff` over its literal and over `run_viewer.py` showing no change to its parsing or rendering.
- NEGATIVE PROOF THAT NO BARE `except` WAS ADDED around the validator or the re-ask, since that is how the spec-edit announcement was silenced.
- NO REAL MODEL TURN SPENT: show the host invocation is stubbed the way existing driver tests stub it.
- THE SIZE BUDGET STATED AND MET: paste the final key set and the rendered prompt block's length, so the maintainer's small-payload condition is verifiable rather than asserted.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set. Measured on main at authoring: `5859 passed, 3 skipped, 2 xfailed`. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC PATH IS DECLARED, and the reason is worth a reviewer's attention because it is a gap rather than a clean answer. THE OUTCOME CONTRACT HAS NO SPEC HOME TODAY: the required keys exist only as a literal inside each host's prompt f-string (`oc_runipd.py:4886-4906`, `agy_runipd.py:2429-2449`), duplicated per host, governed by no `.spec.md`. So there is no approved contract for this plan to amend, and inventing one mid-plan would be a larger change than the plan itself.

WHAT THE EXECUTOR MUST DO INSTEAD: if a spec IS found to govern the outcome contract, STOP, add its path to `Scope-Paths`, and amend it in the same change, per the rule that a plan may amend a spec but must declare it. Do not silently extend a contract a spec describes.

WHAT SHOULD BE FILED REGARDLESS, as a finding rather than fixed here: the outcome contract deserves a spec, because two hosts currently carry two copies of one schema literal and nothing detects their divergence. E-01 reduces the new field's exposure by defining it once in `runner_shared.py`, which is the right direction, but the existing eighteen keys stay duplicated. Report that; do not fix it in this plan.

THE PROMPT TEXT IS AGENT-FACING, so the no-dashes rule does not bind it. Keep it short for the same reason E-01 budgets the schema: every sentence in an execute prompt is paid for on every turn.

DOCUMENT THE CARRIER RULE WHERE AN AGENT WILL MEET IT, not only in the prompt. If the runbook (`DEFAULT_RUNBOOK_TEXT`, `oc_runipd.py:2598`) is the place agents are told how to behave in a managed turn, the always-file-a-backlog-item rule belongs there too, so it survives a prompt rewrite.

## Open questions

### OQ-01: Should a NONE-FOUND report be trusted, or is it just a cheaper lie?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BECAUSE IT IS THE PLAN'S HONEST LIMIT AND THE MAINTAINER SHOULD SEE IT STATED. This plan converts silence into an explicit claim, which is a real improvement: a claim is attributable, auditable and falsifiable where silence is none of those. But it does NOT make the claim true. An agent that wants to finish can write "I found nothing" as easily as it can omit the field, and nothing here verifies the assertion against the diff. So the gain is accountability, not detection, and a reviewer should not read this plan as making an execute turn trustworthy about its own findings. TWO ROUTES EXIST IF THAT IS WANTED, both deliberately excluded: the VERIFIER turn already re-reads the work and could be asked to corroborate the report, which is cheap but collides with three pending plans editing the verdict path (`1bfppy`, `fzxfph`, `bxx9af`); or the report could be checked against the turn's own diff, which is a much larger piece of work and arguably a different plan. Non-blocking because an attributable claim is strictly better than the status quo of ambiguous silence.

### OQ-02: At what size does JSON stop being the right format for this report?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BY THE MAINTAINER'S OWN CONDITION, recorded so the condition is not lost. Asked to justify JSON, the maintainer cited cross-project experience that agents generate rigorous JSON less reliably than structured markdown, currently being hit on another project, and accepted JSON here ONLY on the basis that this report will be SMALL, adding "if that's the case, let's move forward with JSON since we're already knee deep in it". So the format decision is CONDITIONAL and the condition is size. In-repo evidence supports JSON at current scale (0 of 223 agent-written outcome files malformed, and D139 already fixing JSON for machine-consumed output), and no in-repo research compares emission reliability across formats, so the maintainer's concern rests on evidence this repository does not hold. THE PRACTICAL CONSEQUENCE, which E-01 implements: treat the key set as a BUDGET, keep the structure flat, and write the budget's rationale into the schema comment so a later author who wants a fifth field sees the condition. If the report ever grows past a handful of small fields, this question must be re-opened rather than quietly answered by accretion. Non-blocking because the report as scoped is small.

### OQ-03: Should a NONE-FOUND claim skip the re-ask on a turn that did substantial work?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS YES, SKIP IT, because the alternative defeats the design. The temptation is to distrust "I found nothing" after a large turn and ask again anyway. That is wrong for two reasons. First, it punishes the honest affirmative answer this plan exists to elicit: an agent that correctly states it found nothing would be interrogated, while one that omits the field entirely gets exactly the same treatment, so the incentive to answer disappears. Second, it converts a bounded one-shot into a routine second turn on most items, which is the open-ended spend E-05 is bounded to prevent. The re-ask fires on ABSENT-OR-AMBIGUOUS only. The separate and legitimate question of whether a NONE-FOUND claim should be CORROBORATED by a different party is OQ-01, and the answer there is a verifier or diff check, not a re-ask of the same agent that just made the claim.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the schema definition with its comment. Show FOUND, NONE-FOUND and ABSENT are distinguishable by an explicit value and NOT by list emptiness. Paste the written size budget and its rationale, and state the final key count. Confirm by grep that the schema is defined ONCE and referenced by both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the added prompt text from BOTH hosts and show they are byte-identical. Quote the sentence that requires finding nothing to be affirmatively reported. Quote the sentence naming what counts beyond this plan's own requirements. Paste `git diff` proving the `incomplete_requirements` literal is unchanged on both hosts.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the carrier-rule text from both prompts. Show it names `aw backlog new`, states a spec is supporting material only, and contains NO branch asking the agent to judge a just-a-spec case. Quote the sentence establishing that reporting outranks filing when the two conflict.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the validator and its three return states. Paste a test showing a bare string COERCED into the normalized form WITH the coercion recorded, and state why discarding it would have been wrong. Paste proof the validator does not raise on malformed input, and `git diff` showing no bare `except Exception: pass` was introduced.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the re-ask implementation showing it reuses the SAME session rather than opening a new turn. Paste the invocation COUNT asserted as exactly one. Paste an example re-ask message showing it names the SPECIFIC violation rather than repeating the original instruction. Paste the no-work-turn case showing no re-ask fired, and state the predicate used.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the persisted record for a FOUND case and for a NONE-FOUND case SIDE BY SIDE and show they differ from each other and from an ABSENT case. Confirm all four facts are present (tri-state, normalized findings, coercion flag, re-ask result). Show both hosts write the identical shape. Confirm no gate logic was added, since `rnkqrc` owns that.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the ACTUAL passing output of all seven cases. QUOTE the NONE-FOUND versus ABSENT assertion separately as the plan's central property. Show the host invocation is stubbed and no real model turn was spent. THEN paste the BARE `python3 -m pytest` summaries before and after and state the failure-set delta as a set with the counts you observed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. OQ-03 is resolved. OQ-01 states the plan's honest limit (an explicit claim is attributable, not verified) and OQ-02 records the maintainer's conditional acceptance of JSON, which E-01 enforces as a size budget; the plan delivers under either answer.

IT EXISTS BECAUSE A MAINTAINER RULING MADE IT A PREREQUISITE. `rnkqrc` (`durablecapture-01`) cannot see a defect nobody declared, and the maintainer ruled the declaration must be produced first, in session. A reviewer should therefore read this plan and `rnkqrc` together: this one produces the record, that one refuses a dishonest transition against it. Neither is sufficient alone.

IT CARRIES NO `Blocks-Release`, and no `From-Backlog`, because it came from a ruling given while answering an open question rather than from a backlog item. If the maintainer wants the pair gated on the next release, `rnkqrc` is the one to gate, since it is the enforcement half.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. Do NOT spend real model turns in tests; stub the host invocation as the existing driver tests do. Do NOT add a bare `except` around the validator or the re-ask: that is precisely how the spec-edit announcement was silenced and `st5klo` exists to undo it. Re-locate every symbol by NAME: both driver files are under concurrent edit and their line numbers moved by roughly 70 and 95 lines in a single day. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the NONE-FOUND versus ABSENT records shown side by side, the re-ask count asserted as exactly one, and the recorded coercion.
