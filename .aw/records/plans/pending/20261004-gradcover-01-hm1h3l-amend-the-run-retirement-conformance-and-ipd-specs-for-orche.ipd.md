# IPD: Amend the run, retirement, conformance and IPD specs for orchestrator review readiness

- Date: 2026-10-04
- Kind: child
- Concern: Five approved or implemented specs jointly forbid or fail to require what this Set must build. Spec `25kzda` Section 2.5b says the coverage check runs "over the orchestrators IN THAT RUN'S QUEUE only", regardless of action, which is what blocked three `--action review` runs on 2026-10-03; its Sections 4.8 and 4.9 define production success per plan with no Set-level check, which is how 11 backlog items reached `graduated` with refused orchestrators; its Sections 3.2 to 3.4 never say that an orchestrator's status is gated. Spec `77tr3o` R-12 places the check only "before a run spends an agent turn", not at retirement or at status change, and point 3 states the check "IS NOT A LINTER RULE" in terms an implementer could read as forbidding any lint consumer of it. Spec `r07vma` R9 and Section 3a limit 1 describe the probe as reading the full prose sections with no owner credit, and limit 5 says "nothing detects the omission" of a needed final child. Spec `ipd-structure-and-linting` Section 10's ("Deterministic linter contract") MUST-check list has no orchestrator readiness rule. Spec `ipd-spec` enumerates the only legal backward plan transitions (`approved -> reviewed`, `auto-approved -> reviewed`, `reviewed -> to-review`), so an orchestrator found not ready cannot be returned to `draft`, and a plan whose inputs changed after approval cannot be demoted past `reviewed` (measured: `ipd_lifecycle.validate_transition('to-review','draft')` returns `ok=False`, "missing predecessor"); spec `2vev8j` Section 4.8 requires every legal backward edge to be enumerated there. Without amendment, Orders 02 to 10 would each have to contradict an approved contract, which is the dead end `51vw4y` recorded.
- Scope: Edit exactly five spec files to state the new contract, append a dated `aw specs note` history line to each through the tool, and run `aw specs check` on each. IN: the text amendments enumerated in Proposed changes, by section name. OUT: any code, any test, any plan other than this one, any change to a spec's `- Status:`, and any amendment not enumerated here. The `C-*` requirement-ownership format is NOT introduced.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md, .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: hm1h3l

## Workflow history
- 2026-10-04 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-007 (PR-006 open, blocking OQ-03)

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 to PR-007. Fixed: lint MUST-check list is Section 10, not 9 (PR-001); 2.5d now lists the four consumers that may ask and covers could-not-ask at retirement and after review (PR-002); A.7 no longer requires an unimplemented review skip that would deadlock every orchestrator without a verdict (PR-003); E.1 loop-freedom scoped to automated demotion (PR-004); wording, anchor, grep and gate fixes (PR-005, PR-007). OPEN, blocking: OQ-03 / PR-006.
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 01 of Set `gradcover` at the maintainer's instruction to put detailed spec amendments in the plan that edits the specs, citing sections by name and never by line number. Every amendment below is written as the text the executor inserts or the exact change it makes, so a reviewer can approve the contract before any code exists.

## Goal

Make the five governing specs state, before any code changes, that an orchestrator plan's review readiness is one deterministic-plus-probe check; that it gates status changes, production success and retirement; that the run-start probe runs only where retirement is possible; and that the probe must quote what it found and credit explicitly assigned work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: amend the five specs

- [ ] E-01 Amend spec `25kzda` with the text of Proposed changes A.1 to A.9 (Sections 2.5b, a new 2.5d, 3.2, 3.3, 3.4, 4.4, 4.8, 4.9 and 5.5, exactly as listed there), then append the A.10 history line with `aw specs note <path> --message "<A.10 text>"`.
  - Depends on: none
  - Expected outcome: `aw specs check` on the `25kzda` file reports conforming; each of A.1 to A.9 is present verbatim or with only wording-level edits that do not change its meaning; the spec's `- Status:` still reads `approved`.
  - Execution state: pending

- [ ] E-02 Amend spec `77tr3o` exactly as Proposed changes B.1 to B.3 state: rewrite R-12's "THEREFORE" paragraph and point 3, and add a new requirement R-13. Append the history line with `aw specs note`.
  - Depends on: E-01
  - Expected outcome: `aw specs check` on the `77tr3o` file reports conforming; R-12 point 3 no longer reads as forbidding a lint consumer; R-13 exists; `- Status:` still reads `approved`.
  - Execution state: pending

- [ ] E-03 Amend spec `r07vma` exactly as Proposed changes C.1 to C.3 state: extend R9's PROBE bullet, rewrite Section 3a limit 1's last sentence, and rewrite Section 3a limit 5. Append the history line with `aw specs note`.
  - Depends on: E-02
  - Expected outcome: `aw specs check` on the `r07vma` file reports conforming; limit 5 names Set `gradcover` as what now detects an omitted final child; `- Status:` still reads `approved`.
  - Execution state: pending

- [ ] E-04 Amend spec `ipd-structure-and-linting` exactly as Proposed changes D.1 and D.2 state: add item 19 to Section 10's ("Deterministic linter contract") MUST-check list and a paragraph after that list. Append the history line with `aw specs note`.
  - Depends on: E-03
  - Expected outcome: `aw specs check` on the `ipd-structure-and-linting` file reports conforming; item 19 exists and names `IPD-S408`; `- Status:` still reads `implemented`.
  - Execution state: pending

- [ ] E-06 Amend spec `ipd-spec` exactly as Proposed changes E.1 states: replace the enumerated legal backward transitions in its `## Workflow history` convention bullet with the rule that every backward move between non-terminal statuses is legal, loud and loop-free. Append the history line with `aw specs note`.
  - Depends on: E-04
  - Expected outcome: `aw specs check` on the `ipd-spec` file reports conforming; the convention bullet states the every-backward-move rule, the loudness requirements and the loop-freedom argument; `- Status:` still reads `implemented`.
  - Execution state: pending

### Task group 2: confirm nothing else moved

- [ ] E-05 Confirm the five edits are the only changes, that no spec status changed, and that every cross-reference the new text makes (to `r07vma` R3, `25kzda` 2.5b, `77tr3o` R-5/R-12/R-13, the new codes, the new backward edges) resolves to text that exists after E-01 to E-04 and E-06.
  - Depends on: E-06
  - Expected outcome: `git diff --name-only` lists exactly the five spec files; every cross-reference grep returns a hit; `python3 -m agent_workflows check specs` gains no finding.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (`AGENTS.md`, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT"). All five files are in `- Scope-Paths:`, so both runners announce these edits before the run and reconcile them at the end.
- SPECS ARE AMENDED IN PLACE WITH A DATED HISTORY LINE. The established form is an `aw specs note` record reading `AMENDED <date> (plan <id6>): <what changed and why>`; see the most recent `25kzda` history lines (plans `t18l64`, `zdgc6t`, `f7z10q`). Status is not changed by an amendment; `approved -> to-review` is not a legal spec transition (recorded in the `physical-aw-hierarchy` spec's history).
- CITE BY SECTION NAME, NEVER BY LINE NUMBER. The maintainer asked for this explicitly, and `ipd-structure-and-linting` Section 10.2 requires durable anchors.
- `25kzda`'s preamble states that dated paragraphs are point-in-time snapshots. New text below states rules, not measurements, except where it names the 2026-10-03 incident as motivation, which it dates.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | `25kzda` 2.5b requires the probe over every queued orchestrator regardless of action. Its second bullet reads "It runs ONCE per run, over the orchestrators IN THAT RUN'S QUEUE only". `runner_shared.enforce_orchestrator_probe_gate` implements that literally via `queued_orchestrator_targets`, which filters on `kind == "orchestrator"` and never on `action`. | the quoted 2.5b bullet; `queued_orchestrator_targets` body; the four 2026-10-03 run directories whose `state.json` queue items carry `action: review` and whose `orchestrator-probe-gate` event reads `proceed: false` |
| F-02 | A `review` action can never retire an orchestrator: retirement happens only in `runner_shared.dispatch_orchestrator_item`, which both hosts call only when `runnable.get("action") == "orchestrate"` (`oc_runipd` and `agy_runipd` dispatch loops). `runner_shared.action_for` returns `orchestrate` only for `reviewed`/`approved` orchestrators. So the 2.5b gate on a review run guards against an outcome the run cannot produce. | the `action == "orchestrate"` branches in both host dispatch loops; `action_for('orchestrator','to-review') == 'review'` measured 2026-10-04 |
| F-03 | `25kzda` 4.9's `BACKLOG-GRADUATE-IPD` and 4.8's `SPEC-PLAN-CONFORMANCE` are per-plan only. `production_checks._check_ipd_conformance` checks bucket, status, origin link, Scope-Paths, Item-Dependencies and `lint_file(checkpoint="review-finalize")` for one file; nothing reads the child table or the probe. | `_check_ipd_conformance` body; the 11 `graduated` items behind the 13 refused orchestrators (`ildjse`, `dvonrn`, `eeiytw`, `7yz545`, `fcnz1r`, `mflqqf`, `s8veyk`, `ariaau`, `rgl2d4`, `sv9ce4`, `qbz8i1`) |
| F-04 | `77tr3o` R-12 point 3 says "THE CHECK IS NOT A LINTER RULE, AND R-5's REJECTION OF SHAPE (a) STANDS UNCHANGED", and explains that the pre-transition checkpoint must keep Kind-parity. What R-5 rejected was a linter EXEMPTION that lets an orchestrator skip evidence; a lint rule that REFUSES an unready orchestrator at `review-finalize` is the opposite direction and does not touch Kind-parity at `pre-transition`. Point 3 must say so, or Order 03's lint consumer reads as a violation. | R-5's OQ-1 resolution text ("the linter learns a `Kind: orchestrator` + runner-rollup exemption" was REJECTED); `ipd_lint.check_orchestrator_rows` already exists as an orchestrator-only lint rule (`IPD-S407`) gated to `review-finalize`, `pre-execution` and `pre-transition`, so an orchestrator-specific lint rule is already shipped precedent |
| F-05 | `r07vma` Section 3a limit 5 states "a parent can conform perfectly while its author simply omitted a needed final child. R1b names the remedy but nothing detects the omission". That limit is exactly what this Set closes, so leaving it unamended would make the spec wrong. | the quoted limit 5 text |
| F-06 | The probe's answer contract is a bare sentinel line (`PROBE_SENTINEL_EXECUTIONS`/`PROBE_SENTINEL_NO_EXECUTIONS`), and `classify_probe_reply` treats anything else as `unknown`. A refusal therefore cannot name what was found; `axozpe`'s refusal is unactionable. 2.5b must permit a quote block or Order 02 breaks the strict-parser rule 2.5b states. | `PROBE_PROMPT_TEMPLATE` ("Reply with EXACTLY ONE of these two lines and NOTHING else"); `classify_probe_reply` equality test |
| F-07 | `ipd-structure-and-linting` Section 10 ("Deterministic linter contract", not Section 9, which is "Lint checkpoints and lifecycle state") says `aw ipd lint` "MUST make no model calls". A readiness lint rule must therefore READ a recorded probe verdict, never ask for one. The verdict store (`runner_shared.read_probe_verdict`) is a local file read, so this is compatible. | the quoted Section 9 sentence; `read_probe_verdict` reads `probe_verdict_store_path` only |
| F-08 | The existing correction machinery is specified once: `25kzda` 5.5 lists "missing expected artifact or failed deterministic check for which a bounded correction is safe" as retryable. A Set-level production refusal is that class, so Order 07 needs only a sentence naming it, not a new retry rule. | the quoted 5.5 retryable list |

## Proposed changes (ordered, validatable)

Every block below is the text to insert or the precise edit to make. Section references are by name. "Replace" means replace the whole bullet or paragraph named; "add" means insert as stated.

### A. Spec `25kzda` (aw run deterministic run and verify)

A.1 Section 2.5b, the bullet beginning "It runs ONCE per run": REPLACE with:

> - It runs ONCE per run, AFTER the run directory exists and BEFORE any agent turn, lane worktree, or session, over the orchestrators in that run's queue WHOSE ACTION IN THIS RUN IS `orchestrate`, that is, the orchestrators this run could retire. An orchestrator queued for `review` (or any other action) is NOT probed here, because a review cannot retire it; probing it would refuse a run for an outcome the run cannot produce (measured 2026-10-03: three `--action review` runs over 53 plans were refused before any turn because of 13 orchestrators none of which the run could retire). The run-directory ordering is a deliberate exception to the rule that a pre-queue refusal leaves nothing durable: this gate spends a model call, which needs somewhere to be logged, and its refusal must be readable in `aw runs`, which reads durable run state. "Costs nothing" therefore means no agent turn, no worktree, and no session.

A.2 Section 2.5b: ADD a new bullet immediately after A.1:

> - THE CHECK IS REPEATED AT THE RETIREMENT POINT. Immediately before the runner retires an orchestrator (Section 2.5b's premise, spec `77tr3o` R-1 to R-6), it re-evaluates the orchestrator review-readiness check of Section 2.5d against the orchestrator's CURRENT on-disk text. A recorded passing verdict for that exact text is served from the cache and spends nothing; a cache miss asks the probe once; any answer other than a pass, INCLUDING a could-not-ask, refuses the retirement with the `finalize-refused` reason and the quoted finding (Section 2.5d UNAVAILABILITY), leaving the orchestrator in `pending/` without failing the run. This closes the case in which an orchestrator was edited by a child's turn after the run-start probe.

A.3 Section 2.5b, the bullet beginning "A DELIVERED but unusable answer": REPLACE with:

> - THE ANSWER FORMAT IS A VERDICT LINE FOLLOWED BY QUOTED EVIDENCE. The first line is exactly one of the two sentinels. When it is the "contains executions" sentinel, every following non-empty line MUST be a quote line beginning `QUOTE: ` followed by a passage copied VERBATIM from the excerpt the probe was sent, one per uncovered obligation. A quote is valid only if its text occurs in the excerpt after whitespace normalization. A "contains executions" answer with no valid quote, a "contains no executions" answer with any following line, a reply carrying both sentinels, or any other shape is UNUSABLE and BLOCKS exactly as a positive finding does, because a permissive parser would convert a confused model into a silent pass. The valid quotes are recorded with the verdict and are reproduced in the refusal and in `aw runs`, so the operator and the authoring agent are told WHAT to fix, not only THAT something is wrong.

A.4 Section 2.5b: ADD a new bullet immediately after A.3:

> - WORK EXPLICITLY ASSIGNED TO A NAMED CHILD IS COVERED. An obligation stated in the orchestrator's prose that names, by id6, a child listed in the orchestrator's own `## Child IPDs` table as the plan that performs it (for example "Order 04 `rlhmt9` carries the final cross-child measurement") is covered and MUST NOT be reported. The probe prompt states this rule and is sent the child table. The rule does not let prose assign work to a plan outside the table, to an unnamed "later child", or to the orchestrator itself.

A.5 Section 2.5b, the bullet beginning "In an interactive terminal the operator must type the exact phrase `run uncovered`" (the spec has three bullets beginning "In an interactive terminal"; this is the one inside 2.5b): ADD at the end of that bullet:

> The flag and the phrase apply ONLY to this run-start gate. They do not satisfy the retirement-time re-check (A.2), the status-change gate, or the production gate of Section 2.5d, each of which refuses and names its own remedy.

A.6 ADD a new Section 2.5d immediately after Section 2.5c:

> ### 2.5d Orchestrator review readiness
>
> An orchestrator plan (`- Kind: orchestrator`) is READY FOR REVIEW only when ALL of these hold, evaluated by ONE shared function (one implementation, several consumers, the pattern of spec `r07vma` R3):
>
> 1. every row of its `## Child IPDs` table names a child plan that exists in the plans tree (an unresolvable or open-ended row such as `03+` is not ready, as in spec `77tr3o` OQ-2);
> 2. every such child carries `- Status:` `to-review`, `reviewed`, `approved`, `auto-approved` or `executed`, and passes `aw ipd lint` at the `author` checkpoint;
> 3. its checklist rows conform to spec `r07vma` R1a (`IPD-S407`);
> 4. the coverage probe's verdict for the orchestrator's CURRENT text is a recorded pass.
>
> Conditions 1 to 3 are deterministic. Condition 4 is READ from the verdict store by every consumer except the four that may ASK on a miss (and record the answer): the production action of Sections 4.8 and 4.9, the post-review check `IPD-REVIEW-ORCHESTRATOR-READY` of Section 4.4, the retirement-time re-check of Section 2.5b, and the `aw ipd coverage` command. Each of these is already spending a run's or an operator's turn on this orchestrator, so one cached probe call is proportionate. `aw ipd set`, `aw ipd lint` and `aw check` NEVER ask, so the setter and the linters remain model-free.
>
> CONSUMERS. The function is called by: `aw ipd set` for a target of `to-review`, `reviewed`, `approved` or `auto-approved` on an orchestrator plan (refuse); `aw ipd lint` at `review-finalize` and `pre-execution` (rule `IPD-S408`); `aw check plans` (rule `check.orchestrator-not-review-ready`); the production verification codes `SPEC-PLAN-SET` and `BACKLOG-GRADUATE-SET`; the review verification code `IPD-REVIEW-ORCHESTRATOR-READY`; and the retirement-time re-check of Section 2.5b.
>
> UNAVAILABILITY. When condition 4 cannot be established because the probe could not be asked, the status-change, production, post-review and retirement-time consumers REFUSE and leave the plan or its source where it is, naming the command to retry (`aw ipd coverage <id6>`). A refused retirement leaves the orchestrator in `pending/` and is not a failure of the run, exactly as the other retirement refusals of spec `77tr3o` are. This differs deliberately from the run-start gate, which warns and proceeds: at each of these points refusing costs a later retry and nothing else, whereas proceeding would record a readiness claim nobody established.
>
> EVERY REFUSAL names the failing condition, the child id6 or quoted passage it concerns, and the exact command or edit that fixes it, on the human surface and as an `aw.agent/v1` record. The remedy text follows spec `r07vma` R7: it states the invariant, forbids satisfying it by deleting the checklist, and names the legitimate remedies (add a child that owns the work and a row for it, or assign the work in prose to an existing child by id6, or remove it if it is redundant).

A.7 Section 3.2, the IPD dispatch table: ADD one row after the `to-review` row:

> | Orchestrator plan in `draft` or `to-review` | As the matching row above (a `draft` orchestrator's `to-review` transition is itself gated by Section 2.5d). After the review turn, evaluate Section 2.5d (`IPD-REVIEW-ORCHESTRATOR-READY`, Section 4.4; the probe may be asked); when it is not ready, return the plan to `to-review` and correct within the retry budget (Section 5.5). | Same. | Setting it `reviewed` while Section 2.5d fails. |

and ADD this sentence after the table's closing paragraph:

> A status setter that refuses under Section 2.5d is a state gate, not a retryable failure (Section 5.5): the remedy is authoring, which the refusal names.

A.8 Section 3.3, the `approved` row's "Interactive action" cell and Section 3.4, the `open` row's "Interactive action" cell: ADD at the end of each:

> Every produced orchestrator plan must pass Section 2.5d before the source is tool-set (`SPEC-PLAN-SET` / `BACKLOG-GRADUATE-SET`); when it does not, the source stays where it was. A source whose previously produced plans are unfinished is CONTINUED, not re-produced: the action is handed the existing plans and their findings, and `SPEC-PLAN-COUNT` / `BACKLOG-GRADUATE-COUNT` count them as this action's output.

A.9 Section 4.4 table: ADD one row:

> | `IPD-REVIEW-ORCHESTRATOR-READY` | For an orchestrator plan, the Section 2.5d check after the review turn | The orchestrator is ready for review; a review that leaves it unready did not reach `reviewed` | `[IPD-REVIEW-ORCHESTRATOR-READY] Orchestrator <id6> is not ready for review: <findings>. Add or finish the named children, then: aw <host> run resume <run-id>` | RETRY, then FAIL ITEM |

Section 4.8 "IPD authoring from an approved spec" table: ADD one row after `SPEC-PLAN-CONFORMANCE`:

> | `SPEC-PLAN-SET` | Every produced orchestrator plan, evaluated by Section 2.5d (the probe may be asked) | Every produced orchestrator is ready for review; a passing verdict is recorded for its current text | `[SPEC-PLAN-SET] Orchestrator <plan-id> produced from spec <id6> is not ready for review: <findings>. Fix it with the IPD authoring tools, then: aw <host> run resume <run-id>` | RETRY, then FAIL ITEM after containment |

Section 4.9 table: ADD one row after `BACKLOG-GRADUATE-IPD`:

> | `BACKLOG-GRADUATE-SET` | Every produced orchestrator plan, evaluated by Section 2.5d (the probe may be asked) | Every produced orchestrator is ready for review; a passing verdict is recorded for its current text; only then may the item be set `graduated` | `[BACKLOG-GRADUATE-SET] Orchestrator <plan-id> produced from backlog <id6> is not ready for review: <findings>. Fix it with the IPD authoring tools, then: aw <host> run resume <run-id>` | RETRY, then FAIL ITEM after containment |

and REPLACE the `BACKLOG-GRADUATE-COUNT` "Pass criterion" cell with:

> At least one active IPD links to the backlog ID and every new one does; previously produced active IPDs carrying the same `From-Backlog` are this action's continued output (Section 3.4), not duplicates. Only a SECOND active Set for the same item, or an IPD whose `From-Backlog` names a different item, fails.

and make the same change to `SPEC-PLAN-COUNT`'s "Pass criterion" cell with `From-Spec`.

Section 5.5: ADD after the paragraph listing the classes that are never retried:

> A Set-level production refusal (`SPEC-PLAN-SET`, `BACKLOG-GRADUATE-SET`) and an orchestrator review refusal (`IPD-REVIEW-ORCHESTRATOR-READY`) are in the class "failed deterministic check for which a bounded correction is safe". The correction resumes the same host session where one exists, carries only the failing findings and their quoted passages, and counts against the action's `--retry-budget` exactly as other corrections do.

A.10 History line (via `aw specs note`): `AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 2.5b scoped to orchestrators whose action is orchestrate, re-check added at the retirement point, answer format extended to a verdict plus verbatim QUOTE lines, named-child credit rule added, override scoped to the run-start gate; new Section 2.5d defines orchestrator review readiness and its consumers; Sections 3.2-3.4 gate orchestrator status and production on it and allow continuing an unfinished handoff; new codes IPD-REVIEW-ORCHESTRATOR-READY, SPEC-PLAN-SET, BACKLOG-GRADUATE-SET; SPEC-PLAN-COUNT and BACKLOG-GRADUATE-COUNT pass criteria accept continued output; Section 5.5 classifies the new refusals as bounded corrections. Motivated by the 2026-10-03 refusal of three review runs over 13 orchestrators handed off as graduated.`

### B. Spec `77tr3o` (runner-owned orchestrator retirement)

B.1 R-12, the paragraph beginning "THEREFORE: before a run spends an agent turn": REPLACE its first sentence with:

> THEREFORE: before a run that may RETIRE an orchestrator spends an agent turn, allocates a lane worktree, or opens a session, it MUST establish, for every orchestrator in its queue whose action in that run is `orchestrate`, whether that orchestrator carries work no child covers, and MUST refuse (unattended) or prompt (interactive) when it does; and immediately before it retires one, it MUST re-establish that answer for the orchestrator's current text (spec `25kzda` 2.5b).

B.2 R-12 point 3: REPLACE with:

> 3. THE COVERAGE CHECK DOES NOT EXEMPT AN ORCHESTRATOR FROM EVIDENCE, AND R-5's REJECTION OF SHAPE (a) STANDS UNCHANGED. The pre-transition E/V checkpoint preserves Kind-parity (identical findings for an orchestrator and a child; pinned behaviorally by `TheRejectedShapeWasNotTaken`). What R-5 rejected is a lint EXEMPTION that lets an orchestrator reach `executed` with less evidence. A lint rule that REFUSES an orchestrator which is not ready for review (spec `25kzda` 2.5d, `IPD-S408`) is the opposite direction: it adds a refusal at `review-finalize` and `pre-execution`, never relaxes `pre-transition`, and reads a recorded probe verdict rather than asking a model. It is therefore permitted and is required by R-13. The two reasons a SYNTACTIC substitute for the semantic probe is still forbidden are unchanged: the dangerous case is stated in prose and matches no syntax, and a syntactic rule's false positives would drive deletion of the checklist (point 2).

B.3 ADD a new requirement after R-12:

> - R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY WHILE ITS SET IS NOT. Added 2026-10-04 by Set `gradcover` (plan `hm1h3l`). R-12 checks coverage at run time, which is too late: by then the orchestrator has been handed off as `to-review`, its backlog item set `graduated`, and a run is refused with nobody positioned to fix it (measured 2026-10-03: 13 orchestrators, 11 of them from `graduated` items). So the same question is asked EARLIER, at every point that would claim the Set is ready: an orchestrator plan MUST NOT be set `to-review`, `reviewed`, `approved` or `auto-approved`, and a production action MUST NOT set its source `graduated` or `implementing`, unless the orchestrator passes the review-readiness check of spec `25kzda` Section 2.5d. The check is ONE function shared by every consumer (spec `r07vma` R3). Its refusal names the constructive action exactly as R-12 point 2 requires.

B.4 History line: `AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): R-12 scoped to runs that may retire an orchestrator and extended to a re-check at the retirement point; R-12 point 3 clarified that a refusing readiness lint rule is permitted and that R-5's rejection concerns exemptions only; new R-13 requires the 25kzda 2.5d readiness check at every status change and production handoff that would claim an orchestrator's Set is ready.`

### C. Spec `r07vma` (orchestrator conformance parser and repair loop)

C.1 Section 2, R9, the bullet beginning "THE PROBE answers": ADD at the end:

> It quotes each passage it judges uncovered (spec `25kzda` 2.5b), and it credits an obligation the orchestrator's prose explicitly assigns by id6 to a child in its own `## Child IPDs` table. Both the shape check and the probe verdict are inputs to the single review-readiness function of spec `25kzda` 2.5d, which is how R3's "one implementation" extends to the status setters and the production action.

C.2 Section 3a, limit 1: REPLACE its final sentence ("That residue is the semantic probe's job...") with:

> That residue is the semantic probe's job, which is why `25kzda` 2.5b's prohibition still binds and the probe is retained. Since Set `gradcover`, the probe's finding is a quoted passage rather than a bare verdict, and an obligation explicitly assigned in prose to a named child is credited, so the residue the probe reports is the residue an author can act on.

C.3 Section 3a, limit 5: REPLACE with:

> 5. THE TYPED SHAPE IS A CONSTRAINT ON THE ROW, NOT A PROOF ABOUT THE SET. It guarantees that what a row SAYS is a child-tracking obligation. Since Set `gradcover` the omission of a needed final child IS detected, but by a different control: the review-readiness check of spec `25kzda` 2.5d, whose coverage condition reports any whole-Set obligation no listed child is named as performing, and which gates the orchestrator's status and its source's graduation. The row grammar itself still proves nothing about the Set.

C.4 History line: `AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): R9's probe bullet records the quoted-evidence answer and named-child credit, and both controls now feed the 25kzda 2.5d review-readiness function; Section 3a limit 1 updated; limit 5 rewritten because the omitted-final-child case is now detected by 25kzda 2.5d.`

### D. Spec `ipd-structure-and-linting`

D.1 Section 10 "Deterministic linter contract" (the `aw ipd lint` MUST-check list, the list beginning "For a new or migrated IPD, it MUST check at least"): ADD item 19 after item 18:

> 19. for an orchestrator plan at the `review-finalize` and `pre-execution` checkpoints, that it is ready for review per spec `25kzda` Section 2.5d (`IPD-S408`), evaluating conditions 1 to 3 directly and condition 4 by READING the recorded coverage verdict for the plan's current text, never by asking a model. An absent or stale verdict is a finding that names `aw ipd coverage <id6>` as the remedy. At the `author` checkpoint the rule is advisory only, so a plan being written is not refused for children not yet written.

D.2 ADD a paragraph immediately after the MUST-check list:

> Rule 19 is the one orchestrator-specific REFUSAL this command applies beyond `IPD-S407`. It does not change what `pre-transition` requires of an orchestrator (spec `77tr3o` R-5 and R-12 point 3): Kind-parity at `pre-transition` is unchanged. The check is the shared function, not a second implementation, so `aw ipd lint`, `aw check plans` and `aw ipd set` report identical findings for the same plan.

D.3 History line: `AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 10 gains rule 19 (IPD-S408, orchestrator review readiness per 25kzda 2.5d, reading a recorded probe verdict, model-free) and a paragraph stating it does not alter pre-transition Kind-parity.`

### E. Spec `ipd-spec` (authoring and executing an IPD)

E.1 The `## Workflow history` convention bullet, the sentence beginning "The only legal backward lifecycle transitions are": REPLACE that sentence with:

> Every BACKWARD move between the non-terminal plan statuses is legal (`approved` or `auto-approved` to `reviewed`, `to-review` or `draft`; `reviewed` to `to-review` or `draft`; `to-review` to `draft`), because a plan whose spec, scope, dependencies or cited code changed after it was approved in a way that affects how it would be implemented, or that would undo work implemented since, is unsafe to execute and MUST be demoted. Added 2026-10-04 by plan `hm1h3l`; this supersedes the earlier three-edge enumeration (spec `2vev8j` 4.8 asked for the legal edges to be enumerated here, and this sentence is that enumeration). A backward move into a terminal status, and any move out of a terminal status, stays illegal (that is the separate terminal-reopen guard). EVERY BACKWARD MOVE IS LOUD: it requires a reason (`--message`), the setter prints a warning naming the plan, the old and new status and the reason, and the workflow-history line records `demoted <from> -> <to>: <reason>`; a move out of `approved` or `auto-approved` additionally records `APPROVAL WITHDRAWN`. An AUTOMATED demotion can never start a loop. For an orchestrator, promotion (to `to-review`, `reviewed`, `approved` or `auto-approved`) and automated demotion are decided by the same check (spec `25kzda` 2.5d) over the same recorded verdict for the same text: for unchanged text the check cannot both pass (allowing promotion) and fail (requiring demotion), so it can only move again after someone edits it. For any other plan no tool demotes automatically, so every demotion is a deliberate, reasoned act. No runner ever writes `approved` (`25kzda` 4.5), and a runner's `auto-approved` of an orchestrator passes the same check, so an automated demotion is never followed by an automated re-approval of unchanged text.

E.2 History line: `AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): every backward move between non-terminal plan statuses is now legal and mandatory when a plan's inputs changed materially after approval; every backward move requires a reason, warns, and records 'demoted <from> -> <to>: <reason>' (plus APPROVAL WITHDRAWN when leaving approved/auto-approved); loop-freedom stated for automated demotion (one check decides an orchestrator's promotion and demotion; no tool demotes another plan automatically; runners never write approved).`

## Deferred / out of scope (with reason)

- ANY CODE OR TEST CHANGE. This plan writes contract text only; Orders 02 to 10 implement it.
  - Carrier-Declined: by construction; each later child cites the section it implements
- THE `C-*` / `Owner:` / `Covers:` REQUIREMENT-OWNERSHIP FORMAT. Not introduced; see the orchestrator's Deferred section.
  - Carrier-Declined: maintainer sequencing 2026-10-04
- AMENDING `z7nbn1`, which also describes production actions. Its Section 3 delegates the verification codes to `25kzda` 4.8/4.9 ("this spec does not restate them"), so the new codes reach it through that delegation with no edit.
  - Carrier-Declined: measured; `z7nbn1` Section 4.4 says it does not restate the codes

## Scope check

- Over-scope: none. Exactly the five spec files are edited.
- Under-scope: the amendments say what MUST be built; nothing here builds it. A reader must not treat these specs as describing shipped behavior until Orders 02 to 10 execute; each new paragraph is written as a requirement, not a measurement.

## Required tests / validation

- `python3 -m agent_workflows specs check <path>` for each of the five files, pasted, each conforming.
- `python3 -m agent_workflows check specs`, pasted, with no new finding against a baseline measured before editing.
- `git diff --name-only` pasted, listing exactly the five spec paths.
- Greps pasted, each returning a hit after the edit: `2.5d Orchestrator review readiness`, `IPD-REVIEW-ORCHESTRATOR-READY`, `SPEC-PLAN-SET`, `BACKLOG-GRADUATE-SET`, `whose action in this run is \`orchestrate\`` (case-insensitive: A.1 writes it in capitals), `QUOTE: `, `R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY`, `IPD-S408`, `APPROVAL WITHDRAWN`.
- `grep -n '^- Status:'` on each file, pasted, showing the status unchanged (`approved`, `approved`, `approved`, `implemented`, `implemented`).
- `aw ipd lint` on this plan conforming.
- No suite run is required by this plan's own change (no code changes), but run the bare suite once and paste the summary line so the boundary baseline is recorded for Order 02.

## Spec / documentation sync

THIS PLAN IS THE SPEC SYNC FOR THE WHOLE SET. It edits five specs, all declared in `- Scope-Paths:`. WHY each edit is needed: `25kzda` is the run contract every runner behavior here changes; `77tr3o` owns the retirement premise the probe protects and must require the earlier gate; `r07vma` owns the "one implementation" rule and states a limit this Set removes; `ipd-structure-and-linting` lists what `aw ipd lint` must check and gains a rule; `ipd-spec` is where spec `2vev8j` 4.8 requires legal backward edges to be enumerated, and Order 09 cannot return an unready orchestrator to `draft` without the new rule. No user-facing documentation is changed here; Order 11 updates authoring text.

## Open questions

### OQ-01: Should an unavailable probe at a status change refuse, or warn and proceed like the run-start gate?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: REFUSE at the status-change and production consumers (A.6, UNAVAILABILITY). The run-start gate warns and proceeds because halting an otherwise fine run for a model outage wastes a night's work (`25kzda` 2.5b, the maintainer's OQ-02 ruling recorded in `runner_shared`'s probe section). At a status change nothing has started, so refusing costs one retry; proceeding would write `to-review` without anyone having established readiness, which is the exact defect this Set exists to fix.

### OQ-02: Should the readiness lint rule be an error at the `author` checkpoint too?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: advisory at `author`, refusing at `review-finalize` and `pre-execution` (D.1). An orchestrator is legitimately written before its children, and `aw ipd scaffold` produces it first; refusing it at `author` would block the normal authoring order.

### OQ-03: Should a missing or expired coverage verdict be an error in `aw ipd lint` and `aw check`?

- Blocking: yes
- Status: open
- Owner: maintainer
- Finding: PR-006
- Context: this plan writes the contract text the question turns on (A.6 condition 4 and D.1 rule 19: "An absent or stale verdict is a finding"). The verdict store (`runner_shared.probe_verdict_store_path`, `.aw/state/runtime/`) is gitignored by `.aw/.gitignore` `/state/`, never committed, and expires after `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS = 30`. Order 03 (`qs00nc` E-04) makes the check rule an `error`, and CI runs `aw check plans --agent` fail-closed. So CI, every other clone, and this machine after 30 days would fail on every orchestrator at `to-review` or later, permanently. Same decision as orchestrator `1f4faf` OQ-03; answer it once and record it in both plans.
- Decision needed: (a) recommended: for the model-free consumers (`aw ipd lint`, `aw check`) an absent or expired verdict is advisory and a recorded FAIL is an error, while conditions 1 to 3 stay errors and the asking consumers still refuse; (b) persist a pass as a tracked attestation (forgeable by hand edit); (c) drop condition 4 from lint and check. The chosen answer rewrites D.1's sentence and the 2.5d CONSUMERS paragraph here, and `qs00nc` E-04/V-04.
- Resolution or deferral rationale: open; raised by the 2026-10-04 /plan-review of `hm1h3l` (finding PR-006, carried from the `1f4faf` review).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` of the `25kzda` file. For EACH of A.1 to A.9 paste a grep returning the inserted text (or its distinctive phrase). Paste `python3 -m agent_workflows specs check <25kzda path>` conforming and `grep -n '^- Status:'` reading `approved`. Paste the new history line as it appears in `## Workflow history`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `git diff` of the `77tr3o` file; paste greps returning B.1's "whose action in that run is `orchestrate`", B.2's "A lint rule that REFUSES", and B.3's "R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY". Paste `specs check` conforming, `- Status: approved` unchanged, and the new history line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` of the `r07vma` file; paste greps returning C.1's "credits an obligation", C.2's "quoted passage rather than a bare verdict", and C.3's "the omission of a needed final child IS detected". Paste `specs check` conforming, `- Status: approved` unchanged, and the new history line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `git diff` of the `ipd-structure-and-linting` file; paste a grep returning item 19 with `IPD-S408` and the D.2 paragraph's "Kind-parity at `pre-transition` is unchanged". Paste `specs check` conforming, `- Status: implemented` unchanged, and the new history line.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `git diff --name-only` listing exactly the five spec paths. Paste one grep per cross-reference introduced (`r07vma` R3 in `25kzda`; `25kzda` 2.5d in `77tr3o`, `r07vma` and `ipd-structure-and-linting`; `IPD-S408` in `25kzda` and `ipd-structure-and-linting`) returning a hit in the target. Paste `python3 -m agent_workflows check specs` showing no finding beyond a pre-edit baseline you measured and pasted. Paste the bare `python3 -m pytest` summary line as the Order 02 baseline. Paste `aw ipd lint` on this plan conforming and `git diff --cached --name-only` immediately before committing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `git diff` of the `ipd-spec` file; paste greps returning "Every BACKWARD move between the non-terminal plan statuses is legal", "APPROVAL WITHDRAWN" and "can never start a loop". Paste `specs check` conforming, `- Status: implemented` unchanged, and the new history line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, and approval of THIS plan is approval of the contract the rest of Set `gradcover` implements. Commit only the five declared spec paths through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Do not change any spec's `- Status:`. Under a runner, the runner performs `aw ipd begin`/`aw ipd finalize`; by hand, run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-edit `- Status: executed`. Every `V-*` demands the ACTUAL pasted command output; never paraphrase or claim a check you did not run.
