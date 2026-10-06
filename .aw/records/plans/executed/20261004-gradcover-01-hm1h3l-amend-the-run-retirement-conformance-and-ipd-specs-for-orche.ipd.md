# IPD: Amend the run, retirement, conformance and IPD specs for orchestrator review readiness

- Date: 2026-10-04
- Kind: child
- Concern: Five approved or implemented specs jointly forbid or fail to require what this Set must build. Spec `25kzda` Section 2.5b says the coverage check runs "over the orchestrators IN THAT RUN'S QUEUE only", regardless of action, which is what blocked three `--action review` runs on 2026-10-03; its Sections 4.8 and 4.9 define production success per plan with no Set-level check, which is how 11 backlog items reached `graduated` with refused orchestrators; its Sections 3.2 to 3.4 never say that an orchestrator's status is gated. Spec `77tr3o` R-12 places the check only "before a run spends an agent turn", not at retirement or at status change, and point 3 states the check "IS NOT A LINTER RULE" in terms an implementer could read as forbidding any lint consumer of it. Spec `r07vma` R9 and Section 3a limit 1 describe the probe as reading the full prose sections with no owner credit, and limit 5 says "nothing detects the omission" of a needed final child. Spec `ipd-structure-and-linting` Section 10's ("Deterministic linter contract") MUST-check list has no orchestrator readiness rule. Spec `ipd-spec` enumerates the only legal backward plan transitions (`approved -> reviewed`, `auto-approved -> reviewed`, `reviewed -> to-review`), so an orchestrator found not ready cannot be returned to `draft`, and a plan whose inputs changed after approval cannot be demoted past `reviewed` (measured: `ipd_lifecycle.validate_transition('to-review','draft')` returns `ok=False`, "missing predecessor"); spec `2vev8j` Section 4.8 requires every legal backward edge to be enumerated there. Without amendment, Orders 02 to 10 would each have to contradict an approved contract, which is the dead end `51vw4y` recorded.
- Scope: Edit exactly five spec files to state the new contract, append a dated `aw specs note` history line to each through the tool, and run `aw specs check` on each. IN: the text amendments enumerated in Proposed changes, by section name. OUT: any code, any test, any plan other than this one, any change to a spec's `- Status:`, and any amendment not enumerated here. The `C-*` requirement-ownership format is NOT introduced.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md, .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
- Item-Dependencies: none
- From-Spec: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: gradcover
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: hm1h3l

## Workflow history
- 2026-10-06 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: hm1h3l verified (set gradcover, attempt 1).
- 2026-10-06 approved (aw set): status set to approved
- 2026-10-06 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `5etev3` (finding PR-007): the retirement-time re-check (A.2) refuses on condition 4 (coverage) only, because conditions 1 to 3 are enforced at retirement by `evaluate_set_retirement` and the `IPD-S407` gate, and condition 2's ready list excludes `superseded`, which retirement accepts (backlog `31y86f`). When inserting A.6, the executor should make the CONSUMERS/UNAVAILABILITY sentences say so ("the retirement-time re-check, which decides on condition 4 only"). Wording clarification; the review verdict of this plan is unchanged.
- 2026-10-06 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-008..PR-010 (round 2, all fixed)
- 2026-10-06 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-008 to PR-010 (round 2). Fixed: 2.5d condition 2 now exempts executed children from the author lint, matching `qs00nc` F-06/E-01 (PR-008); D.1's author-advisory sentence moved from rule 20 (`IPD-M112`, an error at every checkpoint) to rule 19 (`IPD-S408`), matching `qs00nc` E-04 (PR-009); 2.5e history-line fingerprint stated as the 12-hex prefix `8mabmu` E-03 writes (PR-010). Round-1 PR-006 confirmed fixed by the maintainer's 2026-10-04 ruling (OQ-03 resolved).
- 2026-10-05 to-review (aw set): returned to review after revision: maintainer ruling 2026-10-04 stores the coverage answer in the plan (25kzda 2.5e), resolving blocking OQ-03; every affected plan was rewritten to match
- 2026-10-04 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): revised after review. OQ-03 RESOLVED by the maintainer (2026-10-04): the coverage answer is stored in the plan, not in the gitignored cache. Added `25kzda` Section 2.5e (where the answer is recorded, who writes it, how it is attested, exclusion from the execution-receipt fingerprint) and lint rule 20 (`IPD-M112`); A.2, A.3, A.6 condition 4, B.2 and D.1 now read the plan's record.
- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `qs00nc` (finding PR-001): OQ-03 Context gains the freeze-gate ordering (`enforce_freeze_time_refusal` lints approved plans at `pre-execution` before the run-start probe). Context only; the question, options and verdict are unchanged.
- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `8mabmu` (finding PR-002): A.4's named-child credit now accepts an Order number present in the child table as well as an id6. Measured: `axozpe`, the motivating false refusal, names its owner only as "Order 04"; the id6-only text would have left it refused. The review verdict and blocking OQ-03 of this plan are unchanged.
- 2026-10-04 re-scope (opencode its_direct/pt3-claude-opus-5.5-1m-us): from the /plan-review of `jm27py` (finding PR-003): added `- From-Spec: none`. This plan amends specs rather than being produced from one, and its Concern cites `2vev8j` without editing it, so after `jm27py` the Scope-Paths exemption alone would still leave `check.plan-spec-link-missing` firing on it. Metadata only; no amendment text changed, so the 2026-10-04 review verdict stands.
- 2026-10-04 reviewed (aw set): /plan-review: REVIEWED - OPEN QUESTIONS; PR-001..PR-007 (PR-006 open, blocking OQ-03)

- 2026-10-04 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001 to PR-007. Fixed: lint MUST-check list is Section 10, not 9 (PR-001); 2.5d now lists the four consumers that may ask and covers could-not-ask at retirement and after review (PR-002); A.7 no longer requires an unimplemented review skip that would deadlock every orchestrator without a verdict (PR-003); E.1 loop-freedom scoped to automated demotion (PR-004); wording, anchor, grep and gate fixes (PR-005, PR-007). OPEN, blocking: OQ-03 / PR-006.
- 2026-10-04 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 01 of Set `gradcover` at the maintainer's instruction to put detailed spec amendments in the plan that edits the specs, citing sections by name and never by line number. Every amendment below is written as the text the executor inserts or the exact change it makes, so a reviewer can approve the contract before any code exists.

## Goal

Make the five governing specs state, before any code changes, that an orchestrator plan's review readiness is one deterministic-plus-probe check; that it gates status changes, production success and retirement; that the run-start probe runs only where retirement is possible; and that the probe must quote what it found and credit explicitly assigned work.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: amend the five specs

- [x] E-01 Amend spec `25kzda` with the text of Proposed changes A.1 to A.9 (Sections 2.5b, a new 2.5d and 2.5e, 3.2, 3.3, 3.4, 4.4, 4.8, 4.9 and 5.5, exactly as listed there), then append the A.10 history line with `aw specs note <path> --message "<A.10 text>"`.
  - Depends on: none
  - Expected outcome: `aw specs check` on the `25kzda` file reports conforming; each of A.1 to A.9 is present verbatim or with only wording-level edits that do not change its meaning; the spec's `- Status:` still reads `approved`.
  - Execution state: performed

- [x] E-02 Amend spec `77tr3o` exactly as Proposed changes B.1 to B.3 state: rewrite R-12's "THEREFORE" paragraph and point 3, and add a new requirement R-13. Append the history line with `aw specs note`.
  - Depends on: E-01
  - Expected outcome: `aw specs check` on the `77tr3o` file reports conforming; R-12 point 3 no longer reads as forbidding a lint consumer; R-13 exists; `- Status:` still reads `approved`.
  - Execution state: performed

- [x] E-03 Amend spec `r07vma` exactly as Proposed changes C.1 to C.3 state: extend R9's PROBE bullet, rewrite Section 3a limit 1's last sentence, and rewrite Section 3a limit 5. Append the history line with `aw specs note`.
  - Depends on: E-02
  - Expected outcome: `aw specs check` on the `r07vma` file reports conforming; limit 5 names Set `gradcover` as what now detects an omitted final child; `- Status:` still reads `approved`.
  - Execution state: performed

- [x] E-04 Amend spec `ipd-structure-and-linting` exactly as Proposed changes D.1 and D.2 state: add items 19 and 20 to Section 10's ("Deterministic linter contract") MUST-check list and a paragraph after that list. Append the history line with `aw specs note`.
  - Depends on: E-03
  - Expected outcome: `aw specs check` on the `ipd-structure-and-linting` file reports conforming; item 19 exists and names `IPD-S408`, item 20 exists and names `IPD-M112`; `- Status:` still reads `implemented`.
  - Execution state: performed

- [x] E-06 Amend spec `ipd-spec` exactly as Proposed changes E.1 states: replace the enumerated legal backward transitions in its `## Workflow history` convention bullet with the rule that every backward move between non-terminal statuses is legal, loud and loop-free. Append the history line with `aw specs note`.
  - Depends on: E-04
  - Expected outcome: `aw specs check` on the `ipd-spec` file reports conforming; the convention bullet states the every-backward-move rule, the loudness requirements and the loop-freedom argument; `- Status:` still reads `implemented`.
  - Execution state: performed

### Task group 2: confirm nothing else moved

- [x] E-05 Confirm the five edits are the only changes, that no spec status changed, and that every cross-reference the new text makes (to `r07vma` R3, `25kzda` 2.5b, `77tr3o` R-5/R-12/R-13, the new codes, the new backward edges) resolves to text that exists after E-01 to E-04 and E-06.
  - Depends on: E-06
  - Expected outcome: `git diff --name-only` lists exactly the five spec files; every cross-reference grep returns a hit; `python3 -m agent_workflows check specs` gains no finding.
  - Execution state: performed

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
| F-07 | `ipd-structure-and-linting` Section 10 ("Deterministic linter contract", not Section 9, which is "Lint checkpoints and lifecycle state") says `aw ipd lint` "MUST make no model calls". A readiness lint rule must therefore READ a recorded answer, never ask for one. The only place an answer is kept today is `runner_shared.probe_verdict_store_path`, `.aw/state/runtime/orchestrator-probe-verdicts.json`, which `.aw/.gitignore` (`/state/`) excludes from git and `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS` expires after 30 days, so CI and other clones can never read one; hence Section 2.5e moves the answer into the plan. | the quoted Section 10 sentence; `probe_verdict_store_path`; `.aw/.gitignore`; `DEFAULT_PROBE_VERDICT_MAX_AGE_DAYS` |
| F-08 | The existing correction machinery is specified once: `25kzda` 5.5 lists "missing expected artifact or failed deterministic check for which a bounded correction is safe" as retryable. A Set-level production refusal is that class, so Order 07 needs only a sentence naming it, not a new retry rule. | the quoted 5.5 retryable list |

## Proposed changes (ordered, validatable)

Every block below is the text to insert or the precise edit to make. Section references are by name. "Replace" means replace the whole bullet or paragraph named; "add" means insert as stated.

### A. Spec `25kzda` (aw run deterministic run and verify)

A.1 Section 2.5b, the bullet beginning "It runs ONCE per run": REPLACE with:

> - It runs ONCE per run, AFTER the run directory exists and BEFORE any agent turn, lane worktree, or session, over the orchestrators in that run's queue WHOSE ACTION IN THIS RUN IS `orchestrate`, that is, the orchestrators this run could retire. An orchestrator queued for `review` (or any other action) is NOT probed here, because a review cannot retire it; probing it would refuse a run for an outcome the run cannot produce (measured 2026-10-03: three `--action review` runs over 53 plans were refused before any turn because of 13 orchestrators none of which the run could retire). The run-directory ordering is a deliberate exception to the rule that a pre-queue refusal leaves nothing durable: this gate spends a model call, which needs somewhere to be logged, and its refusal must be readable in `aw runs`, which reads durable run state. "Costs nothing" therefore means no agent turn, no worktree, and no session.

A.2 Section 2.5b: ADD a new bullet immediately after A.1:

> - THE CHECK IS REPEATED AT THE RETIREMENT POINT. Immediately before the runner retires an orchestrator (Section 2.5b's premise, spec `77tr3o` R-1 to R-6), it re-evaluates the orchestrator review-readiness check of Section 2.5d against the orchestrator's CURRENT on-disk text. A `- Coverage: pass` recorded IN THE PLAN for that exact text (Section 2.5e) spends nothing; an absent or out-of-date record asks the probe once and records the answer in the plan; any answer other than a pass, INCLUDING a could-not-ask, refuses the retirement with the `finalize-refused` reason and the quoted finding (Section 2.5d UNAVAILABILITY), leaving the orchestrator in `pending/` without failing the run. This closes the case in which an orchestrator was edited by a child's turn after the run-start probe.

A.3 Section 2.5b, the bullet beginning "A DELIVERED but unusable answer": REPLACE with:

> - THE ANSWER FORMAT IS A VERDICT LINE FOLLOWED BY QUOTED EVIDENCE. The first line is exactly one of the two sentinels. When it is the "contains executions" sentinel, every following non-empty line MUST be a quote line beginning `QUOTE: ` followed by a passage copied VERBATIM from the excerpt the probe was sent, one per uncovered obligation. A quote is valid only if its text occurs in the excerpt after whitespace normalization. A "contains executions" answer with no valid quote, a "contains no executions" answer with any following line, a reply carrying both sentinels, or any other shape is UNUSABLE and BLOCKS exactly as a positive finding does, because a permissive parser would convert a confused model into a silent pass. The valid quotes are recorded IN THE PLAN with the verdict (Section 2.5e) and are reproduced in the refusal and in `aw runs`, so the operator and the authoring agent are told WHAT to fix, not only THAT something is wrong.

A.4 Section 2.5b: ADD a new bullet immediately after A.3:

> - WORK EXPLICITLY ASSIGNED TO A NAMED CHILD IS COVERED. An obligation stated in the orchestrator's prose that names a child listed in the orchestrator's own `## Child IPDs` table as the plan that performs it, by that child's id6 OR by an Order number present in the table (for example "Order 04 `rlhmt9` carries the final cross-child measurement", or "which Order 04 carries as the last child" when the table has a `04` row), is covered and MUST NOT be reported. The probe prompt states this rule and is sent the child table. The rule does not let prose assign work to a plan outside the table, to an unnamed "later child", or to the orchestrator itself.

A.5 Section 2.5b, the bullet beginning "In an interactive terminal the operator must type the exact phrase `run uncovered`" (the spec has three bullets beginning "In an interactive terminal"; this is the one inside 2.5b): ADD at the end of that bullet:

> The flag and the phrase apply ONLY to this run-start gate. They do not satisfy the retirement-time re-check (A.2), the status-change gate, or the production gate of Section 2.5d, each of which refuses and names its own remedy.

A.6 ADD a new Section 2.5d immediately after Section 2.5c:

> ### 2.5d Orchestrator review readiness
>
> An orchestrator plan (`- Kind: orchestrator`) is READY FOR REVIEW only when ALL of these hold, evaluated by ONE shared function (one implementation, several consumers, the pattern of spec `r07vma` R3):
>
> 1. every row of its `## Child IPDs` table names a child plan that exists in the plans tree (an unresolvable or open-ended row such as `03+` is not ready, as in spec `77tr3o` OQ-2);
> 2. every such child carries `- Status:` `to-review`, `reviewed`, `approved`, `auto-approved` or `executed`; a child that is NOT in a terminal directory also passes `aw ipd lint` at the `author` checkpoint (a child under `executed/` with `- Status: executed` is ready without being linted, because the linter reports every terminal-directory plan as `legacy/not evaluated`, which is not a passing disposition);
> 3. its checklist rows conform to spec `r07vma` R1a (`IPD-S407`);
> 4. the plan carries a coverage record (Section 2.5e) whose verdict is `pass` and whose fingerprint matches the plan's CURRENT text.
>
> Conditions 1 to 3 are deterministic. Condition 4 is READ from the plan's own coverage record by every consumer except the four that may ASK when the record is absent or out of date (and write the answer into the plan): the production action of Sections 4.8 and 4.9, the post-review check `IPD-REVIEW-ORCHESTRATOR-READY` of Section 4.4, the retirement-time re-check of Section 2.5b, and the `aw ipd coverage` command. Each of these is already spending a run's or an operator's turn on this orchestrator, so one cached probe call is proportionate. `aw ipd set`, `aw ipd lint` and `aw check` NEVER ask, so the setter and the linters remain model-free.
>
> CONSUMERS. The function is called by: `aw ipd set` for a target of `to-review`, `reviewed`, `approved` or `auto-approved` on an orchestrator plan (refuse); `aw ipd lint` at `review-finalize` and `pre-execution` (rule `IPD-S408`); `aw check plans` (rule `check.orchestrator-not-review-ready`); the production verification codes `SPEC-PLAN-SET` and `BACKLOG-GRADUATE-SET`; the review verification code `IPD-REVIEW-ORCHESTRATOR-READY`; and the retirement-time re-check of Section 2.5b.
>
> UNAVAILABILITY. When condition 4 cannot be established because the probe could not be asked, the status-change, production, post-review and retirement-time consumers REFUSE and leave the plan or its source where it is, naming the command to retry (`aw ipd coverage <id6>`). A refused retirement leaves the orchestrator in `pending/` and is not a failure of the run, exactly as the other retirement refusals of spec `77tr3o` are. This differs deliberately from the run-start gate, which warns and proceeds: at each of these points refusing costs a later retry and nothing else, whereas proceeding would record a readiness claim nobody established.
>
> EVERY REFUSAL names the failing condition, the child id6 or quoted passage it concerns, and the exact command or edit that fixes it, on the human surface and as an `aw.agent/v1` record. The remedy text follows spec `r07vma` R7: it states the invariant, forbids satisfying it by deleting the checklist, and names the legitimate remedies (add a child that owns the work and a row for it, or assign the work in prose to an existing child by id6, or remove it if it is redundant).
>
> ### 2.5e Where the coverage answer is recorded
>
> The coverage answer is recorded IN THE ORCHESTRATOR PLAN ITSELF, not in a machine-local cache, so every clone, CI, and every later reviewer reads the same answer with no expiry. (Before Set `gradcover`, answers were kept only in `.aw/state/runtime/orchestrator-probe-verdicts.json`, which is gitignored and expires after 30 days, so CI and other clones could never see one.) The record is three metadata fields and, on a fail, one section:
>
> - `- Coverage: pass` or `- Coverage: fail`;
> - `- Coverage-Fingerprint: <hex>`, the fingerprint of the parts of the plan the question reads (its checklist action text, its `## Child IPDs` rows, and the prose sections the probe is sent), computed by the same function that builds the probe's input, so the answer and the fingerprint cannot cover different text;
> - `- Coverage-Checked: <YYYY-MM-DD> by <model>`;
> - on a fail, a `## Coverage findings` section listing each quoted passage, one bullet per `QUOTE:` line of the answer.
>
> A record is CURRENT when its fingerprint equals the fingerprint of the plan's current text. Ticking a checkbox, filling evidence, or appending history does not change the fingerprint. Any edit to the parts the question reads does, and makes the record OUT OF DATE, which every consumer treats exactly as an absent record (the four asking consumers ask again; `aw ipd set`, `aw ipd lint` and `aw check` report it, naming `aw ipd coverage <id6>`).
>
> ONLY THE TOOL WRITES THE RECORD. `aw ipd coverage`, the production action, the post-review check and the retirement-time re-check write all fields together, and append a matching `## Workflow history` line `coverage <pass|fail> (<tool>): fingerprint <first 12 hex digits of Coverage-Fingerprint>, model <model>`. A coverage record with no matching history line is refused by `aw ipd lint` (rule `IPD-M112`), the same defense `- Readiness:` has (`IPD-M107`). This does not make forgery impossible; it makes a hand-written record visible in review and in git history, which is the standard the repository already accepts for `- Readiness:`.
>
> THE RECORD IS NOT PART OF THE PLAN'S EXECUTION CONTRACT. The coverage fields, the `## Coverage findings` section and their history lines are excluded from the begin-receipt fingerprint (`ipd_lifecycle.frozen_region_digest`) and from the coverage fingerprint itself, so recording an answer neither invalidates an execution receipt nor changes the text it describes.
>
> The machine-local verdict store is RETIRED by Set `gradcover`: no consumer reads or writes it, and its file may be deleted.

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

A.10 History line (via `aw specs note`): `AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 2.5b scoped to orchestrators whose action is orchestrate, re-check added at the retirement point, answer format extended to a verdict plus verbatim QUOTE lines, named-child credit rule added, override scoped to the run-start gate; new Section 2.5d defines orchestrator review readiness and its consumers; new Section 2.5e records the coverage answer in the plan itself (Coverage, Coverage-Fingerprint, Coverage-Checked, ## Coverage findings), written only by the tool with a matching history line and excluded from the execution-receipt fingerprint, retiring the gitignored 30-day verdict cache; Sections 3.2-3.4 gate orchestrator status and production on it and allow continuing an unfinished handoff; new codes IPD-REVIEW-ORCHESTRATOR-READY, SPEC-PLAN-SET, BACKLOG-GRADUATE-SET; SPEC-PLAN-COUNT and BACKLOG-GRADUATE-COUNT pass criteria accept continued output; Section 5.5 classifies the new refusals as bounded corrections. Motivated by the 2026-10-03 refusal of three review runs over 13 orchestrators handed off as graduated.`

### B. Spec `77tr3o` (runner-owned orchestrator retirement)

B.1 R-12, the paragraph beginning "THEREFORE: before a run spends an agent turn": REPLACE its first sentence with:

> THEREFORE: before a run that may RETIRE an orchestrator spends an agent turn, allocates a lane worktree, or opens a session, it MUST establish, for every orchestrator in its queue whose action in that run is `orchestrate`, whether that orchestrator carries work no child covers, and MUST refuse (unattended) or prompt (interactive) when it does; and immediately before it retires one, it MUST re-establish that answer for the orchestrator's current text (spec `25kzda` 2.5b).

B.2 R-12 point 3: REPLACE with:

> 3. THE COVERAGE CHECK DOES NOT EXEMPT AN ORCHESTRATOR FROM EVIDENCE, AND R-5's REJECTION OF SHAPE (a) STANDS UNCHANGED. The pre-transition E/V checkpoint preserves Kind-parity (identical findings for an orchestrator and a child; pinned behaviorally by `TheRejectedShapeWasNotTaken`). What R-5 rejected is a lint EXEMPTION that lets an orchestrator reach `executed` with less evidence. A lint rule that REFUSES an orchestrator which is not ready for review (spec `25kzda` 2.5d, `IPD-S408`) is the opposite direction: it adds a refusal at `review-finalize` and `pre-execution`, never relaxes `pre-transition`, and reads the coverage record stored in the plan rather than asking a model. It is therefore permitted and is required by R-13. The two reasons a SYNTACTIC substitute for the semantic probe is still forbidden are unchanged: the dangerous case is stated in prose and matches no syntax, and a syntactic rule's false positives would drive deletion of the checklist (point 2).

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

> 19. for an orchestrator plan at the `review-finalize` and `pre-execution` checkpoints, that it is ready for review per spec `25kzda` Section 2.5d (`IPD-S408`), evaluating conditions 1 to 3 directly and condition 4 by READING the plan's own coverage record (spec `25kzda` 2.5e), never by asking a model. An absent coverage record, or one whose fingerprint does not match the current text, is an error that names `aw ipd coverage <id6>` as the remedy. Because the record is in the plan, the result is the same on every clone and in CI. At the `author` checkpoint the rule is advisory only, so a plan being written is not refused for children not yet written.
> 20. that a coverage record (`- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:`) is either wholly absent or complete, and is matched by a `coverage` line in `## Workflow history` (`IPD-M112`), at every checkpoint, as an error (an incomplete or unattested record is a defect at any stage, unlike a missing child).

D.2 ADD a paragraph immediately after the MUST-check list:

> Rule 19 is the one orchestrator-specific REFUSAL this command applies beyond `IPD-S407`. It does not change what `pre-transition` requires of an orchestrator (spec `77tr3o` R-5 and R-12 point 3): Kind-parity at `pre-transition` is unchanged. The check is the shared function, not a second implementation, so `aw ipd lint`, `aw check plans` and `aw ipd set` report identical findings for the same plan.

D.3 History line: `AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 10 gains rule 19 (IPD-S408, orchestrator review readiness per 25kzda 2.5d, reading the coverage record stored in the plan, model-free) and rule 20 (IPD-M112, a coverage record must be complete and attested by a history line) and a paragraph stating it does not alter pre-transition Kind-parity.`

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
- Greps pasted, each returning a hit after the edit: `2.5d Orchestrator review readiness`, `IPD-REVIEW-ORCHESTRATOR-READY`, `SPEC-PLAN-SET`, `BACKLOG-GRADUATE-SET`, `whose action in this run is \`orchestrate\`` (case-insensitive: A.1 writes it in capitals), `QUOTE: `, `R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY`, `IPD-S408`, `APPROVAL WITHDRAWN`, `2.5e Where the coverage answer is recorded`, `IPD-M112`.
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

- Blocking: no
- Status: resolved
- Owner: maintainer
- Finding: PR-006
- Resolution or deferral rationale: RESOLVED 2026-10-04 by the maintainer, in session: STORE THE ANSWER IN THE PLAN ITSELF. The question arose because the answer lived only in a gitignored file that expires after 30 days, so CI and other clones could never see one. With the answer recorded in the plan (new `25kzda` Section 2.5e: `Coverage`, `Coverage-Fingerprint`, `Coverage-Checked`, and `## Coverage findings` on a fail), every clone and CI read the same answer, so an absent or out-of-date record CAN safely be an error in `aw ipd lint` and `aw check`. The fingerprint is kept, stored beside the answer, so an edit after a pass is detected and reported plainly ("plan changed since the check on <date>") rather than the answer silently disappearing. Forgery by hand edit is handled as for `- Readiness:`: only the tool writes the record, it writes a matching history line, and `aw ipd lint` refuses a record without one (`IPD-M112`). Recorded in A.2, A.3, A.6, the new Section 2.5e, B.2 and D.1.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the `git diff` of the `25kzda` file. For EACH of A.1 to A.9 paste a grep returning the inserted text (or its distinctive phrase). Paste `python3 -m agent_workflows specs check <25kzda path>` conforming and `grep -n '^- Status:'` reading `approved`. Paste the new history line as it appears in `## Workflow history`.
  - Observed evidence:
    1. `git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    ```diff
    @@ -434,14 +434,22 @@ All four states are observable in `aw runs` output and in `--agent` JSON.
       the common case still costs nothing: an orchestrator that passes the shape check, carries a cached
       verdict from an earlier check of the same text, or belongs to a Set that has no children yet, spends
       nothing here.
    -- It runs ONCE per run, over the orchestrators IN THAT RUN'S QUEUE only. If no orchestrator is queued,
    -  no model call is made. The check is serialized across the queued orchestrators so it never fans out
    -  concurrent model calls.
    +- It runs ONCE per run, AFTER the run directory exists and BEFORE any agent turn, lane worktree, or session, over the orchestrators in that run's queue WHOSE ACTION IN THIS RUN IS `orchestrate`, that is, the orchestrators this run could retire. An orchestrator queued for `review` (or any other action) is NOT probed here, because a review cannot retire it; probing it would refuse a run for an outcome the run cannot produce (measured 2026-10-03: three `--action review` runs over 53 plans were refused before any turn because of 13 orchestrators none of which the run could retire). The run-directory ordering is a deliberate exception to the rule that a pre-queue refusal leaves nothing durable: this gate spends a model call, which needs somewhere to be logged, and its refusal must be readable in `aw runs`, which reads durable run state. "Costs nothing" therefore means no agent turn, no worktree, and no session.
    +- THE CHECK IS REPEATED AT THE RETIREMENT POINT. Immediately before the runner retires an orchestrator (Section 2.5b's premise, spec `77tr3o` R-1 to R-6), it re-evaluates the orchestrator review-readiness check of Section 2.5d against the orchestrator's CURRENT on-disk text. A `- Coverage: pass` recorded IN THE PLAN for that exact text (Section 2.5e) spends nothing; an absent or out-of-date record asks the probe once and records the answer in the plan; any answer other than a pass, INCLUDING a could-not-ask, refuses the retirement with the `finalize-refused` reason and the quoted finding (Section 2.5d UNAVAILABILITY), leaving the orchestrator in `pending/` without failing the run. This closes the case in which an orchestrator was edited by a child's turn after the run-start probe.
     - The check is cached on the orchestrator's EXACT text and child table. If the file has not changed
       since a previous run checked it, the cached verdict is reused and no call is made.
    -- A DELIVERED but unusable answer is treated as a positive finding (blocks, fail-closed). A
    -  could-not-ask failure (network error, rate limit, model unavailable) is retried, and if still
    -  failing, is WARNED and the run PROCEEDS, recording the known hole in the verification record.
    +- THE ANSWER FORMAT IS A VERDICT LINE FOLLOWED BY QUOTED EVIDENCE. The first line is exactly one of the two sentinels. When it is the "contains executions" sentinel, every following non-empty line MUST be a quote line beginning `QUOTE: ` followed by a passage copied VERBATIM from the excerpt the probe was sent, one per uncovered obligation. A quote is valid only if its text occurs in the excerpt after whitespace normalization. A "contains executions" answer with no valid quote, a "contains no executions" answer with any following line, a reply carrying both sentinels, or any other shape is UNUSABLE and BLOCKS exactly as a positive finding does, because a permissive parser would convert a confused model into a silent pass. The valid quotes are recorded IN THE PLAN with the verdict (Section 2.5e) and are reproduced in the refusal and in `aw runs`, so the operator and the authoring agent are told WHAT to fix, not only THAT something is wrong.
    +- WORK EXPLICITLY ASSIGNED TO A NAMED CHILD IS COVERED. An obligation stated in the orchestrator's prose that names a child listed in the orchestrator's own `## Child IPDs` table as the plan that performs it, by that child's id6 OR by an Order number present in the table (for example "Order 04 `rlhmt9` carries the final cross-child measurement", or "which Order 04 carries as the last child" when the table has a `04` row), is covered and MUST NOT be reported. The probe prompt states this rule and is sent the child table. The rule does not let prose assign work to a plan outside the table, to an unnamed "later child", or to the orchestrator itself.
    +- A DELIVERED OVERRIDE BINDS ONLY THE RUN-START GATE. Passing `--allow-uncovered-orchestrator-work '<why>'` lets a run proceed past the run-start gate for a named orchestrator despite a positive finding, recording the justification durably. It does NOT bypass the retirement re-check: a run that reaches retirement must establish coverage on the current text or leave the orchestrator in `pending/`.
    +
    +### 2.5d Orchestrator review readiness
    +
    +An orchestrator plan (`- Kind: orchestrator`) is READY FOR REVIEW only when ALL of these hold, evaluated by ONE shared function (one implementation, several consumers, the pattern of spec `r07vma` R3):
    +
    +1. every row of its `## Child IPDs` table names a child plan that exists in the plans tree (an unresolvable or open-ended row such as `03+` is not ready, as in spec `77tr3o` OQ-2);
    +2. every such child carries `- Status:` `to-review`, `reviewed`, `approved`, `auto-approved` or `executed`; a child that is NOT in a terminal directory also passes `aw ipd lint` at the `author` checkpoint (a child under `executed/` with `- Status: executed` is ready without being linted, because the linter reports every terminal-directory plan as `legacy/not evaluated`, which is not a passing disposition);
    +3. its checklist rows conform to spec `r07vma` R1a (`IPD-S407`);
    +4. the plan carries a coverage record (Section 2.5e) whose verdict is `pass` and whose fingerprint matches the plan's CURRENT text.
    +
    +Conditions 1 to 3 are deterministic. Condition 4 is READ from the plan's own coverage record by every consumer except the four that may ASK when the record is absent or out of date (and write the answer into the plan): the production action of Sections 4.8 and 4.9, the post-review check `IPD-REVIEW-ORCHESTRATOR-READY` of Section 4.4, the retirement-time re-check of Section 2.5b (which decides on condition 4 only), and the `aw ipd coverage` command. Each of these is already spending a run's or an operator's turn on this orchestrator, so one cached probe call is proportionate. `aw ipd set`, `aw ipd lint` and `aw check` NEVER ask, so the setter and the linters remain model-free.
    +
    +CONSUMERS. The function is called by: `aw ipd set` for a target of `to-review`, `reviewed`, `approved` or `auto-approved` on an orchestrator plan (refuse); `aw ipd lint` at `review-finalize` and `pre-execution` (rule `IPD-S408`); `aw check plans` (rule `check.orchestrator-not-review-ready`); the production verification codes `SPEC-PLAN-SET` and `BACKLOG-GRADUATE-SET`; the review verification code `IPD-REVIEW-ORCHESTRATOR-READY`; and the retirement-time re-check of Section 2.5b (which decides on condition 4 only).
    +
    +UNAVAILABILITY. When condition 4 cannot be established because the probe could not be asked, the status-change, production, post-review and retirement-time consumers REFUSE and leave the plan or its source where it is, naming the command to retry (`aw ipd coverage <id6>`). A refused retirement leaves the orchestrator in `pending/` and is not a failure of the run, exactly as the other retirement refusals of spec `77tr3o` are. This differs deliberately from the run-start gate, which warns and proceeds: at each of these points refusing costs a later retry and nothing else, whereas proceeding would record a readiness claim nobody established.
    +
    +EVERY REFUSAL names the failing condition, the child id6 or quoted passage it concerns, and the exact command or edit that fixes it, on the human surface and as an `aw.agent/v1` record. The remedy text follows spec `r07vma` R7: it states the invariant, forbids satisfying it by deleting the checklist, and names the legitimate remedies (add a child that owns the work and a row for it, or assign the work in prose to an existing child by id6, or remove it if it is redundant).
    +
    +### 2.5e Where the coverage answer is recorded
    +
    +The coverage answer is recorded IN THE ORCHESTRATOR PLAN ITSELF, not in a machine-local cache, so every clone, CI, and every later reviewer reads the same answer with no expiry. (Before Set `gradcover`, answers were kept only in `.aw/state/runtime/orchestrator-probe-verdicts.json`, which is gitignored and expires after 30 days, so CI and other clones could never see one.) The record is three metadata fields and, on a fail, one section:
    +
    +- `- Coverage: pass` or `- Coverage: fail`;
    +- `- Coverage-Fingerprint: <hex>`, the fingerprint of the parts of the plan the question reads (its checklist action text, its `## Child IPDs` rows, and the prose sections the probe is sent), computed by the same function that builds the probe's input, so the answer and the fingerprint cannot cover different text;
    +- `- Coverage-Checked: <YYYY-MM-DD> by <model>`;
    +- on a fail, a `## Coverage findings` section listing each quoted passage, one bullet per `QUOTE:` line of the answer.
    +
    +A record is CURRENT when its fingerprint equals the fingerprint of the plan's current text. Ticking a checkbox, filling evidence, or appending history does not change the fingerprint. Any edit to the parts the question reads does, and makes the record OUT OF DATE, which every consumer treats exactly as an absent record (the four asking consumers ask again; `aw ipd set`, `aw ipd lint` and `aw check` report it, naming `aw ipd coverage <id6>`).
    +
    +ONLY THE TOOL WRITES THE RECORD. `aw ipd coverage`, the production action, the post-review check and the retirement-time re-check write all fields together, and append a matching `## Workflow history` line `coverage <pass|fail> (<tool>): fingerprint <first 12 hex digits of Coverage-Fingerprint>, model <model>`. A coverage record with no matching history line is refused by `aw ipd lint` (rule `IPD-M112`), the same defense `- Readiness:` has (`IPD-M107`). This does not make forgery impossible; it makes a hand-written record visible in review and in git history, which is the standard the repository already accepts for `- Readiness:`.
    +
    +THE RECORD IS NOT PART OF THE PLAN'S EXECUTION CONTRACT. The coverage fields, the `## Coverage findings` section and their history lines are excluded from the begin-receipt fingerprint (`ipd_lifecycle.frozen_region_digest`) and from the coverage fingerprint itself, so recording an answer neither invalidates an execution receipt nor changes the text it describes.
    +
    +The machine-local verdict store is RETIRED by Set `gradcover`: no consumer reads or writes it, and its file may be deleted.
    @@ -695,6 +706,7 @@ The dispatch table defines the action per artifact kind and status:
     | `draft` | Do NOT run `/plan-review` automatically. Report as `needs_input` with the review slash-command for the user. | Same. | Running review without user opt-in. |
     | `to-review`, default | Run `/plan-review` in an isolated reviewer session. If clean, advance to `reviewed`. If findings, leave `to-review` with recorded findings. | Prompt before review. | Advancing without clean review. |
     | `to-review`, `--action review` | As default. | As default. | As default. |
    +| Orchestrator plan in `draft` or `to-review` | As the matching row above (a `draft` orchestrator's `to-review` transition is itself gated by Section 2.5d). After the review turn, evaluate Section 2.5d (`IPD-REVIEW-ORCHESTRATOR-READY`, Section 4.4; the probe may be asked); when it is not ready, return the plan to `to-review` and correct within the retry budget (Section 5.5). | Same. | Setting it `reviewed` while Section 2.5d fails. |
     | `reviewed`, default | Ask for explicit approval. If approved, tool-set `approved` with a human receipt and execute. If declined, stop `needs_input` or `skipped`. | Stop `needs_input`. Exact recovery names the human approval command. | Self-approval or treating model approval as human approval. |
     | `reviewed`, `--action review` | Stop `already_reviewed`: nothing to review. Report the human approval command as next action. | Same. | Running review on an already-reviewed plan. |
     | `approved` | Allocate isolated worktree, execute against acceptance criteria, capture evidence, tool-finalize, merge-back. | Same. | Bypassing isolation or lifecycle gate. |
    @@ -715,10 +727,12 @@ The action matrix for IPDs under execution:

     Both runners share this dispatch table via `runner_shared.py:action_for` and `runner_shared.py:is_executable`.

    +A status setter that refuses under Section 2.5d is a state gate, not a retryable failure (Section 5.5): the remedy is authoring, which the refusal names.
    +
     ### 3.3 Specs dispatch

     | Status / Mode | Unattended action | Interactive action | Prohibited |
     | --- | --- | --- | --- |
     | `draft` | Stop `needs_input`: authoring incomplete. | Same. | Advancing without authoring. |
     | `to-review` | Run `/spec-review`. If clean, advance to `reviewed`. | Prompt before review. | Advancing without clean review. |
     | `reviewed` | Stop `needs_input`: requires human approval. | Same. | Self-approval. |
    -| `approved` | Author one or more conformant IPDs linked by `From-Spec` (an orchestrated Set when the design decomposes into ordered phases); preserve `Blocks-Release` on each; tool-set spec to `implementing`; verify. | Same. Report generated IPDs as next actions; do not run them in the same run. | Modifying the approved requirements while authoring. |
    +| `approved` | Author one or more conformant IPDs linked by `From-Spec` (an orchestrated Set when the design decomposes into ordered phases); preserve `Blocks-Release` on each; tool-set spec to `implementing`; verify. Every produced orchestrator plan must pass Section 2.5d before the source is tool-set (`SPEC-PLAN-SET` / `BACKLOG-GRADUATE-SET`); when it does not, the source stays where it was. A source whose previously produced plans are unfinished is CONTINUED, not re-produced: the action is handed the existing plans and their findings, and `SPEC-PLAN-COUNT` / `BACKLOG-GRADUATE-COUNT` count them as this action's output. | Same. Report generated IPDs as next actions; do not run them in the same run. | Modifying the approved requirements while authoring. |
     | `implementing` | Re-check: are all linked IPDs terminal? If yes, tool-set `implemented` with evidence citation; if no, report pending IPDs as next actions. | Same. | Setting `implemented` while linked IPDs remain non-terminal. |

     ### 3.4 Backlog dispatch

     | Status / Mode | Unattended action | Interactive action | Prohibited |
     | --- | --- | --- | --- |
    -| `open` | Author the artifacts the item needs: any spec it requires (created and approved under the authority of this request, not deferred to a separate round trip) plus one or more conformant IPDs, each carrying `From-Backlog` and inheriting `Blocks-Release`; set the backlog item to `graduated` using the handoff receipt; verify. | Same. Report generated IPDs as next actions; do not run them in the same run. | Setting the item `graduated` before a conformant handoff exists, or setting it `done` (which would claim implementation that has not happened). |
    +| `open` | Author the artifacts the item needs: any spec it requires (created and approved under the authority of this request, not deferred to a separate round trip) plus one or more conformant IPDs, each carrying `From-Backlog` and inheriting `Blocks-Release`; set the backlog item to `graduated` using the handoff receipt; verify. Every produced orchestrator plan must pass Section 2.5d before the source is tool-set (`SPEC-PLAN-SET` / `BACKLOG-GRADUATE-SET`); when it does not, the source stays where it was. A source whose previously produced plans are unfinished is CONTINUED, not re-produced: the action is handed the existing plans and their findings, and `SPEC-PLAN-COUNT` / `BACKLOG-GRADUATE-COUNT` count them as this action's output. | Same. Report generated IPDs as next actions; do not run them in the same run. | Setting the item `graduated` before a conformant handoff exists, or setting it `done` (which would claim implementation that has not happened). |
     | `graduated` | Re-check: are all linked IPDs terminal? If yes, tool-set `done` with evidence citation; if no, report pending IPDs as next actions. | Same. | Setting `done` while linked IPDs remain non-terminal. |
     | `blocked` | Check gating condition. If resolved, unblock to `open`; if not, report gate status. | Same. | Advancing while gate remains unresolved. |
    @@ -925,6 +942,7 @@ Pre-execution runs `IPD-DISPATCH-ACTION`, `IPD-WORKTREE-ALLOCATION`, `IPD-PRECHEC
     | Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
     | --- | --- | --- | --- | --- |
     | `IPD-REVIEW-ADVANCE` | Plan status and workflow-history entry after review turn | Clean review advanced status to `reviewed` and recorded history entry | `[IPD-REVIEW-ADVANCE] Review did not advance plan <id6> to reviewed. Review findings remain. Correct them, then: aw <host> run <id6>` | FAIL ITEM |
    +| `IPD-REVIEW-ORCHESTRATOR-READY` | For an orchestrator plan, the Section 2.5d check after the review turn | The orchestrator is ready for review; a review that leaves it unready did not reach `reviewed` | `[IPD-REVIEW-ORCHESTRATOR-READY] Orchestrator <id6> is not ready for review: <findings>. Add or finish the named children, then: aw <host> run resume <run-id>` | RETRY, then FAIL ITEM |
     | `IPD-REVIEW-ROUND-BUDGET` | Review iteration count | Review converged within allowed review rounds (default 3) | `[IPD-REVIEW-ROUND-BUDGET] Review did not converge within <rounds> rounds on plan <id6>. Manual review required: aw <host> run <id6>` | FAIL ITEM |
     | `IPD-REVIEW-FINDINGS-CLEARED` | Review report findings vs residual plan content | All findings from previous round are addressed | `[IPD-REVIEW-FINDINGS-CLEARED] Unaddressed review findings in plan <id6>: <findings>. Correct them, then: aw <host> run <id6>` | RETRY, then FAIL ITEM |

    @@ -948,7 +966,8 @@ A production action (`aw oc run --action produce`, `aw agy run --action produce`
     | Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
     | --- | --- | --- | --- | --- |
     | `SPEC-PLAN-CREATED` | Baseline vs current IPD catalog | At least one new IPD exists in `.agents/plans/pending/` linking to the spec | `[SPEC-PLAN-CREATED] Spec <id6> produced 0 new IPDs in pending/. Repair by re-running production, then: aw <host> run <id6>` | RETRY, then FAIL ITEM |
    -| `SPEC-PLAN-COUNT` | Linked IPDs created | Expected count matches actual; single-plan vs ordered-Set matches spec scope | `[SPEC-PLAN-COUNT] Spec <id6> produced <actual> IPDs; expected <expected>. Repair by authoring missing IPDs, then: aw <host> run <id6>` | FAIL ITEM |
    +| `SPEC-PLAN-COUNT` | Linked IPDs created | Expected count matches actual; single-plan vs ordered-Set matches spec scope; previously produced active IPDs carrying the same `From-Spec` are this action's continued output (Section 3.3), not duplicates. Only a SECOND active Set for the same spec, or an IPD whose `From-Spec` names a different spec, fails. | `[SPEC-PLAN-COUNT] Spec <id6> produced <actual> IPDs; expected <expected>. Repair by authoring missing IPDs, then: aw <host> run <id6>` | FAIL ITEM |
     | `SPEC-PLAN-CONFORMANCE` | Each new IPD's linter result | `aw ipd lint` passes for every generated IPD | `[SPEC-PLAN-CONFORMANCE] Generated IPD <plan-id> fails lint: <details>. Repair with aw ipd sync <plan-path>, then: aw <host> run <id6>` | RETRY, then FAIL ITEM |
    +| `SPEC-PLAN-SET` | Every produced orchestrator plan, evaluated by Section 2.5d (the probe may be asked) | Every produced orchestrator is ready for review; a passing verdict is recorded for its current text | `[SPEC-PLAN-SET] Orchestrator <plan-id> produced from spec <id6> is not ready for review: <findings>. Fix it with the IPD authoring tools, then: aw <host> run resume <run-id>` | RETRY, then FAIL ITEM after containment |
     | `SPEC-PLAN-GATE-CARRY` | Spec/IPD `Blocks-Release` values | A spec release gate is copied exactly to the IPD; an absent spec gate is not invented | `[SPEC-PLAN-GATE-CARRY] Spec <id6> and IPD <plan-id> disagree on Blocks-Release. Quarantine the handoff, correct it, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment |
     | `SPEC-IMPLEMENTING-TRANSITION` | Spec status/history and IPD citation | Spec moved `approved -> implementing` through the setter only after the conformant IPD commit; history cites the IPD path and commit | `[SPEC-IMPLEMENTING-TRANSITION] Spec <id6> lacks a valid implementing transition tied to <plan-id>. Repair with aw spec set implementing <id6> --evidence <plan-path>, then: aw <host> run resume <run-id>` | RETRY, then FAIL ITEM |
    @@ -983,8 +1017,9 @@ Reusable execution runs all common checks plus the E/V, scope, command-freshness

     | Check | What is inspected | Pass criterion | Exact failure message and recovery command | Action |
     | --- | --- | --- | --- | --- |
    -| `BACKLOG-GRADUATE-COUNT` | Baseline/current IPDs and `From-Backlog` links | At least one new active IPD was created and every one links to the graduated backlog ID | `[BACKLOG-GRADUATE-COUNT] Backlog <id6> produced <count> linked IPDs; expected at least one, each carrying From-Backlog. Quarantine the action, reconcile them, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment; ABORT RUN only for duplicate identity ambiguity |
    +| `BACKLOG-GRADUATE-COUNT` | Baseline/current IPDs and `From-Backlog` links | At least one active IPD links to the backlog ID and every new one does; previously produced active IPDs carrying the same `From-Backlog` are this action's continued output (Section 3.4), not duplicates. Only a SECOND active Set for the same item, or an IPD whose `From-Backlog` names a different item, fails. | `[BACKLOG-GRADUATE-COUNT] Backlog <id6> produced <count> linked IPDs; expected at least one, each carrying From-Backlog. Quarantine the action, reconcile them, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment; ABORT RUN only for duplicate identity ambiguity |
     | `BACKLOG-GRADUATE-IPD` | Each new IPD's linter result, status/location, scope, resolved dependency field, and E/V rows | EVERY generated IPD is canonical, `to-review`, in `pending/`, has resolved `Item-Dependencies`, and is conformant | `[BACKLOG-GRADUATE-IPD] IPD <plan-id> generated from backlog <id6> fails <finding-code>: <detail>. Fix it, then: aw <host> run resume <run-id>` | RETRY, then FAIL ITEM |
    +| `BACKLOG-GRADUATE-SET` | Every produced orchestrator plan, evaluated by Section 2.5d (the probe may be asked) | Every produced orchestrator is ready for review; a passing verdict is recorded for its current text; only then may the item be set `graduated` | `[BACKLOG-GRADUATE-SET] Orchestrator <plan-id> produced from backlog <id6> is not ready for review: <findings>. Fix it with the IPD authoring tools, then: aw <host> run resume <run-id>` | RETRY, then FAIL ITEM after containment |
     | `BACKLOG-GATE-HANDOFF` | Backlog/IPD `Blocks-Release`, `From-Backlog`, active release resolution | If backlog blocks release R, every generated IPD (or the generated spec) also blocks R before the item is set `graduated`; all references resolve | `[BACKLOG-GATE-HANDOFF] Backlog <id6> did not preserve release gate <release> on IPD <plan-id>. Quarantine the handoff, correct the fields, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment |
     | `BACKLOG-GRADUATE-LEGITIMACY` | Backlog setter receipt, status/history, handoff evidence | Backlog changed `open -> graduated` through the setter only after the handoff commit; history cites the generated artifacts; the item was NOT set `done` | `[BACKLOG-GRADUATE-LEGITIMACY] Backlog <id6> was transitioned without a valid handoff, or was closed `done` instead of `graduated`. Contain the item, restore it with aw backlog set open <id6> --message "handoff incomplete", then: aw <host> run <id6>` | FAIL ITEM after containment |
     | `BACKLOG-CROSS-TREE` | Full cross-tree checker | No dangling gate, mismatched gate, orphaned live blocker, or dangling source link exists | `[BACKLOG-CROSS-TREE] Backlog handoff violates <finding-code>: <detail>. Quarantine the item, repair it, run aw check all, then: aw <host> run <id6>` | FAIL ITEM after containment |
    @@ -1338,6 +1373,8 @@ It must never retry these classes regardless of budget:

     An out-of-scope mutation therefore fails and contains the item on the first occurrence even if ten retries remain. A human gate and dependency-not-met outcome are state gates, not retryable failures. Each permitted correction has a new attempt number and idempotency key and invalidates stale evidence from earlier attempts.

    +A Set-level production refusal (`SPEC-PLAN-SET`, `BACKLOG-GRADUATE-SET`) and an orchestrator review refusal (`IPD-REVIEW-ORCHESTRATOR-READY`) are in the class "failed deterministic check for which a bounded correction is safe". The correction resumes the same host session where one exists, carries only the failing findings and their quoted passages, and counts against the action's `--retry-budget` exactly as other corrections do.
    +
     The runner provides three distinct classification surfaces that key on different evidence by design:
     - `turn_failure_is_retryable`: classifies a finished turn by its runner disposition.
     - `finalize_retry_decision`: classifies a refused finalize by the gate's findings carried across the subprocess boundary. It keys primarily on shipped lint finding codes (`finalize_refusal_is_retryable`, `retryable_finalize_finding_codes`), retaining a prose fallback for findings without a lint code and for answerable checkpoint messages excluded from the code set.
    @@ -1638,6 +1675,7 @@ This example demonstrates the revised guarantees: `all` is safely bounded; depen

     ## Workflow history

    +- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 2.5b scoped to orchestrators whose action is orchestrate, re-check added at the retirement point, answer format extended to a verdict plus verbatim QUOTE lines, named-child credit rule added, override scoped to the run-start gate; new Section 2.5d defines orchestrator review readiness and its consumers; new Section 2.5e records the coverage answer in the plan itself (Coverage, Coverage-Fingerprint, Coverage-Checked, ## Coverage findings), written only by the tool with a matching history line and excluded from the execution-receipt fingerprint, retiring the gitignored 30-day verdict cache; Sections 3.2-3.4 gate orchestrator status and production on it and allow continuing an unfinished handoff; new codes IPD-REVIEW-ORCHESTRATOR-READY, SPEC-PLAN-SET, BACKLOG-GRADUATE-SET; SPEC-PLAN-COUNT and BACKLOG-GRADUATE-COUNT pass criteria accept continued output; Section 5.5 classifies the new refusals as bounded corrections. Motivated by the 2026-10-03 refusal of three review runs over 13 orchestrators handed off as graduated.
     - 2026-10-02 note (aw specs): AMENDED (plan t18l64, backlog kw31r2): Section 5.5 amended to declare verification_retry_decision as a third classification surface alongside turn_failure_is_retryable and finalize_retry_decision, updating the class-to-surface table for missing or stale validation evidence across both finalize and verification gates.
     - 2026-10-01 note (aw specs): amend Section 2.1c consequence 2: refuse contradictory verification flags on both hosts and subcommands via shared predicate (plan zdgc6t, backlog byazcp)
     - 2026-10-01 note (aw specs): AMENDED (plan f7z10q, backlog u7bfks): infrastructure paragraph line-78 sentence amended to state what BOUND asserts (named resolving predicate) and does not assert (execution reachability), pointing at run_evidence.bound_run_finding_codes_reachability(); Section 4.2 table untouched
    ```
    2. Greps for A.1 to A.9:
    - A.1: `grep -n "WHOSE ACTION IN THIS RUN IS \`orchestrate\`"`:
      `437:- It runs ONCE per run, AFTER the run directory exists and BEFORE any agent turn, lane worktree, or session, over the orchestrators in that run's queue WHOSE ACTION IN THIS RUN IS \`orchestrate\`, that is, the orchestrators this run could retire.`
    - A.2: `grep -n "THE CHECK IS REPEATED AT THE RETIREMENT POINT"`:
      `438:- THE CHECK IS REPEATED AT THE RETIREMENT POINT. Immediately before the runner retires an orchestrator (Section 2.5b's premise, spec \`77tr3o\` R-1 to R-6), it re-evaluates the orchestrator review-readiness check of Section 2.5d against the orchestrator's CURRENT on-disk text.`
    - A.3: `grep -n "THE ANSWER FORMAT IS A VERDICT LINE FOLLOWED BY QUOTED EVIDENCE"`:
      `442:- THE ANSWER FORMAT IS A VERDICT LINE FOLLOWED BY QUOTED EVIDENCE. The first line is exactly one of the two sentinels.`
    - A.4: `grep -n "WORK EXPLICITLY ASSIGNED TO A NAMED CHILD IS COVERED"`:
      `443:- WORK EXPLICITLY ASSIGNED TO A NAMED CHILD IS COVERED. An obligation stated in the orchestrator's prose that names a child listed in the orchestrator's own \`## Child IPDs\` table as the plan that performs it, by that child's id6 OR by an Order number present in the table`
    - A.5: `grep -n "A DELIVERED OVERRIDE BINDS ONLY THE RUN-START GATE"`:
      `444:- A DELIVERED OVERRIDE BINDS ONLY THE RUN-START GATE. Passing \`--allow-uncovered-orchestrator-work '<why>'\` lets a run proceed past the run-start gate for a named orchestrator despite a positive finding, recording the justification durably.`
    - A.6: `grep -n "### 2.5d Orchestrator review readiness"` and `grep -n "### 2.5e Where the coverage answer is recorded"`:
      `446:### 2.5d Orchestrator review readiness`
      `463:### 2.5e Where the coverage answer is recorded`
    - A.7: `grep -n "Orchestrator plan in \`draft\` or \`to-review\`"` and `grep -n "A status setter that refuses under Section 2.5d"`:
      `709:| Orchestrator plan in \`draft\` or \`to-review\` | As the matching row above (a \`draft\` orchestrator's \`to-review\` transition is itself gated by Section 2.5d). After the review turn, evaluate Section 2.5d (\`IPD-REVIEW-ORCHESTRATOR-READY\`, Section 4.4; the probe may be asked); when it is not ready, return the plan to \`to-review\` and correct within the retry budget (Section 5.5). | Same. | Setting it \`reviewed\` while Section 2.5d fails. |`
      `730:A status setter that refuses under Section 2.5d is a state gate, not a retryable failure (Section 5.5): the remedy is authoring, which the refusal names.`
    - A.8: `grep -n "SPEC-PLAN-SET" and "BACKLOG-GRADUATE-SET" in Section 3.3 / 3.4`:
      `740:| \`approved\` | Author one or more conformant IPDs linked by \`From-Spec\` (an orchestrated Set when the design decomposes into ordered phases); preserve \`Blocks-Release\` on each; tool-set spec to \`implementing\`; verify. Every produced orchestrator plan must pass Section 2.5d before the source is tool-set (\`SPEC-PLAN-SET\` / \`BACKLOG-GRADUATE-SET\`); when it does not, the source stays where it was. A source whose previously produced plans are unfinished is CONTINUED, not re-produced: the action is handed the existing plans and their findings, and \`SPEC-PLAN-COUNT\` / \`BACKLOG-GRADUATE-COUNT\` count them as this action's output. | Same. Report generated IPDs as next actions; do not run them in the same run. | Modifying the approved requirements while authoring. |`
      `754:| \`open\` | Author the artifacts the item needs: any spec it requires (created and approved under the authority of this request, not deferred to a separate round trip) plus one or more conformant IPDs, each carrying \`From-Backlog\` and inheriting \`Blocks-Release\`; set the backlog item to \`graduated\` using the handoff receipt; verify. Every produced orchestrator plan must pass Section 2.5d before the source is tool-set (\`SPEC-PLAN-SET\` / \`BACKLOG-GRADUATE-SET\`); when it does not, the source stays where it was. A source whose previously produced plans are unfinished is CONTINUED, not re-produced: the action is handed the existing plans and their findings, and \`SPEC-PLAN-COUNT\` / \`BACKLOG-GRADUATE-COUNT\` count them as this action's output. | Same. Report generated IPDs as next actions; do not run them in the same run. | Setting the item \`graduated\` before a conformant handoff exists, or setting it \`done\` (which would claim implementation that has not happened). |`
    - A.9: `grep -n "IPD-REVIEW-ORCHESTRATOR-READY"`, `grep -n "SPEC-PLAN-SET"`, `grep -n "BACKLOG-GRADUATE-SET"`:
      `945:| \`IPD-REVIEW-ORCHESTRATOR-READY\` | For an orchestrator plan, the Section 2.5d check after the review turn | The orchestrator is ready for review; a review that leaves it unready did not reach \`reviewed\` | \`[IPD-REVIEW-ORCHESTRATOR-READY] Orchestrator <id6> is not ready for review: <findings>. Add or finish the named children, then: aw <host> run resume <run-id>\` | RETRY, then FAIL ITEM |`
      `971:| \`SPEC-PLAN-SET\` | Every produced orchestrator plan, evaluated by Section 2.5d (the probe may be asked) | Every produced orchestrator is ready for review; a passing verdict is recorded for its current text | \`[SPEC-PLAN-SET] Orchestrator <plan-id> produced from spec <id6> is not ready for review: <findings>. Fix it with the IPD authoring tools, then: aw <host> run resume <run-id>\` | RETRY, then FAIL ITEM after containment |`
      `1022:| \`BACKLOG-GRADUATE-SET\` | Every produced orchestrator plan, evaluated by Section 2.5d (the probe may be asked) | Every produced orchestrator is ready for review; a passing verdict is recorded for its current text; only then may the item be set \`graduated\` | \`[BACKLOG-GRADUATE-SET] Orchestrator <plan-id> produced from backlog <id6> is not ready for review: <findings>. Fix it with the IPD authoring tools, then: aw <host> run resume <run-id>\` | RETRY, then FAIL ITEM after containment |`
      `1376:A Set-level production refusal (\`SPEC-PLAN-SET\`, \`BACKLOG-GRADUATE-SET\`) and an orchestrator review refusal (\`IPD-REVIEW-ORCHESTRATOR-READY\`) are in the class "failed deterministic check for which a bounded correction is safe". The correction resumes the same host session where one exists, carries only the failing findings and their quoted passages, and counts against the action's \`--retry-budget\` exactly as other corrections do.`
    3. `python3 -m agent_workflows specs check .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    ```text
    aw specs check: all specs conform. 1 specs checked.
    ```
    4. `grep -n '^- Status:' .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    `4:- Status: approved`
    5. New history line in `## Workflow history`:
    `- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 2.5b scoped to orchestrators whose action is orchestrate, re-check added at the retirement point, answer format extended to a verdict plus verbatim QUOTE lines, named-child credit rule added, override scoped to the run-start gate; new Section 2.5d defines orchestrator review readiness and its consumers; new Section 2.5e records the coverage answer in the plan itself (Coverage, Coverage-Fingerprint, Coverage-Checked, ## Coverage findings), written only by the tool with a matching history line and excluded from the execution-receipt fingerprint, retiring the gitignored 30-day verdict cache; Sections 3.2-3.4 gate orchestrator status and production on it and allow continuing an unfinished handoff; new codes IPD-REVIEW-ORCHESTRATOR-READY, SPEC-PLAN-SET, BACKLOG-GRADUATE-SET; SPEC-PLAN-COUNT and BACKLOG-GRADUATE-COUNT pass criteria accept continued output; Section 5.5 classifies the new refusals as bounded corrections. Motivated by the 2026-10-03 refusal of three review runs over 13 orchestrators handed off as graduated.`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff` of the `77tr3o` file; paste greps returning B.1's "whose action in that run is `orchestrate`", B.2's "A lint rule that REFUSES", and B.3's "R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY". Paste `specs check` conforming, `- Status: approved` unchanged, and the new history line.
  - Observed evidence:
    1. `git diff .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md b/.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
    index 0a7dd3394..efe900bbd 100644
    --- a/.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
    +++ b/.aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
    @@ -14,6 +14,7 @@

     ## Workflow history

    +- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): R-12 scoped to runs that may retire an orchestrator and extended to a re-check at the retirement point; R-12 point 3 clarified that a refusing readiness lint rule is permitted and that R-5's rejection concerns exemptions only; new R-13 requires the 25kzda 2.5d readiness check at every status change and production handoff that would claim an orchestrator's Set is ready.
     - 2026-09-25 note (aw specs): AMENDED 2026-09-25 (statusvocab 9x7otz / cyamvi): canonical terminal status vocabulary updated (fail-depend, fail-merge, fail-gate, fail-verify, fail-begin, fail-lane, not-run, interrupted). Legacy terminal status tokens (including dependency-blocked, integration-blocked, merge-needs-human, merge-conflict, merge-refused, substantially-complete, failed-safely, not-attempted) remain readable forever for backward compatibility on historical run records (via TERMINAL_STATUS_ALIASES), but are no longer written by the runner.
     - 2026-09-24 note (aw specs): AMENDED 2026-09-24 (IPD kjqqzf): R-12(3)'s stale "zero occurrences of 'orchestrator'" sentence is corrected to reflect the behavioral Kind-parity property (the pre-transition checkpoint produces identical findings for an orchestrator and a child), matching the replacement of the source-text pin with a behavioral test in tests/test_orchestrator_retirement.py::TheRejectedShapeWasNotTaken after IPD-S407 landed in ipd_lint.py.
     - 2026-09-21 note (aw specs): AMENDED 2026-09-21 (maintainer-directed rename): the non-success terminal status list now names merge-needs-human and merge-refused rather than integration-blocked and merge-conflict. A pure one-for-one renaming of the same two statuses; the retirement rule itself is unchanged, and both pre-rename spellings remain recognized at read time via runner_shared.LEGACY_INTEGRATION_STATUS_ALIASES so an already-recorded run still classifies identically. Verified: tests/test_orchestrator_retirement.py passes.
    @@ -211,9 +212,7 @@ so the asymmetry is known in passing but unfixed.
       V-02. So a parent-only deliverable was marked complete having been neither performed nor verified,
       which is exactly the outcome R-5 intended to make impossible.

    -  THEREFORE: before a run spends an agent turn, allocates a lane worktree, or opens a session, it MUST
    -  establish for every orchestrator IN ITS QUEUE whether that orchestrator carries work no child
    -  covers, and MUST refuse (unattended) or prompt (interactive) when it does. The check is specified in
    +  THEREFORE: before a run that may RETIRE an orchestrator spends an agent turn, allocates a lane worktree, or opens a session, it MUST establish, for every orchestrator in its queue whose action in that run is `orchestrate`, whether that orchestrator carries work no child covers, and MUST refuse (unattended) or prompt (interactive) when it does; and immediately before it retires one, it MUST re-establish that answer for the orchestrator's current text (spec `25kzda` 2.5b). The check is specified in
       spec `25kzda` Section 2.5b, which owns its mechanism, its caching, its four-state answer, and its
       override; this requirement is what makes it OWED rather than optional, and states the three
       properties that follow from R-5 specifically:
    @@ -227,19 +226,14 @@ so the asymmetry is known in passing but unfixed.
          executions gets complied with by DELETING the parent's checklist, and that checklist is what
          makes `execute <setid>` complete and ordered when no runner is involved. Deleting it causes the
          lost work this spec exists to prevent.
    -  3. THE CHECK IS NOT A LINTER RULE, AND R-5's REJECTION OF SHAPE (a) STANDS UNCHANGED. The
    -     pre-transition E/V checkpoint preserves Kind-parity (producing identical findings for an
    -     orchestrator and a child; pinned behaviorally by `TheRejectedShapeWasNotTaken`), and does not
    -     exempt an orchestrator from evidence. Two independent reasons: the dangerous case is stated in
    -     PROSE and matches no syntax, so a pattern match catches only the tidy mistake; and measured over
    -     the live corpus every plan carrying `- Kind: orchestrator` carries checklist items, most of them
    -     legitimate orchestration, so a syntactic rule's false positives would drive exactly the
    -     deletion (2) forbids.
    +  3. THE COVERAGE CHECK DOES NOT EXEMPT AN ORCHESTRATOR FROM EVIDENCE, AND R-5's REJECTION OF SHAPE (a) STANDS UNCHANGED. The pre-transition E/V checkpoint preserves Kind-parity (identical findings for an orchestrator and a child; pinned behaviorally by `TheRejectedShapeWasNotTaken`). What R-5 rejected is a lint EXEMPTION that lets an orchestrator reach `executed` with less evidence. A lint rule that REFUSES an orchestrator which is not ready for review (spec `25kzda` 2.5d, `IPD-S408`) is the opposite direction: it adds a refusal at `review-finalize` and `pre-execution`, never relaxes `pre-transition`, and reads the coverage record stored in the plan rather than asking a model. It is therefore permitted and is required by R-13. The two reasons a SYNTACTIC substitute for the semantic probe is still forbidden are unchanged: the dangerous case is stated in prose and matches no syntax, and a syntactic rule's false positives would drive deletion of the checklist (point 2).

       An override exists for a maintainer who accepts the risk deliberately, and it MUST record a
       JUSTIFICATION rather than a bare boolean: the risk accepted is that a parent's items will be
       reported complete unperformed, and a record that says only "someone allowed this" cannot be audited.

    +- R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY WHILE ITS SET IS NOT. Added 2026-10-04 by Set `gradcover` (plan `hm1h3l`). R-12 checks coverage at run time, which is too late: by then the orchestrator has been handed off as `to-review`, its backlog item set `graduated`, and a run is refused with nobody positioned to fix it (measured 2026-10-03: 13 orchestrators, 11 of them from `graduated` items). So the same question is asked EARLIER, at every point that would claim the Set is ready: an orchestrator plan MUST NOT be set `to-review`, `reviewed`, `approved` or `auto-approved`, and a production action MUST NOT set its source `graduated` or `implementing`, unless the orchestrator passes the review-readiness check of spec `25kzda` Section 2.5d. The check is ONE function shared by every consumer (spec `r07vma` R3). Its refusal names the constructive action exactly as R-12 point 2 requires.
    +
     ## 4. Deliberately out of scope

     - The general `dependency-blocked`-is-terminal defect for ORDINARY items, and the all-or-nothing drain
    ```
    2. Greps for B.1, B.2, B.3:
    - B.1: `grep -n "whose action in that run is \`orchestrate\`"`:
      `215:  THEREFORE: before a run that may RETIRE an orchestrator spends an agent turn, allocates a lane worktree, or opens a session, it MUST establish, for every orchestrator in its queue whose action in that run is \`orchestrate\`, whether that orchestrator carries work no child covers, and MUST refuse (unattended) or prompt (interactive) when it does; and immediately before it retires one, it MUST re-establish that answer for the orchestrator's current text (spec \`25kzda\` 2.5b). The check is specified in`
    - B.2: `grep -n "A lint rule that REFUSES"`:
      `229:  3. THE COVERAGE CHECK DOES NOT EXEMPT AN ORCHESTRATOR FROM EVIDENCE, AND R-5's REJECTION OF SHAPE (a) STANDS UNCHANGED. The pre-transition E/V checkpoint preserves Kind-parity (identical findings for an orchestrator and a child; pinned behaviorally by \`TheRejectedShapeWasNotTaken\`). What R-5 rejected is a lint EXEMPTION that lets an orchestrator reach \`executed\` with less evidence. A lint rule that REFUSES an orchestrator which is not ready for review (spec \`25kzda\` 2.5d, \`IPD-S408\`) is the opposite direction: it adds a refusal at \`review-finalize\` and \`pre-execution\`, never relaxes \`pre-transition\`, and reads the coverage record stored in the plan rather than asking a model. It is therefore permitted and is required by R-13. The two reasons a SYNTACTIC substitute for the semantic probe is still forbidden are unchanged: the dangerous case is stated in prose and matches no syntax, and a syntactic rule's false positives would drive deletion of the checklist (point 2).`
    - B.3: `grep -n "R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY"`:
      `235:- R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY WHILE ITS SET IS NOT. Added 2026-10-04 by Set \`gradcover\` (plan \`hm1h3l\`). R-12 checks coverage at run time, which is too late: by then the orchestrator has been handed off as \`to-review\`, its backlog item set \`graduated\`, and a run is refused with nobody positioned to fix it (measured 2026-10-03: 13 orchestrators, 11 of them from \`graduated\` items). So the same question is asked EARLIER, at every point that would claim the Set is ready: an orchestrator plan MUST NOT be set \`to-review\`, \`reviewed\`, \`approved\` or \`auto-approved\`, and a production action MUST NOT set its source \`graduated\` or \`implementing\`, unless the orchestrator passes the review-readiness check of spec \`25kzda\` Section 2.5d. The check is ONE function shared by every consumer (spec \`r07vma\` R3). Its refusal names the constructive action exactly as R-12 point 2 requires.`
    3. `python3 -m agent_workflows specs check .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md`:
    ```text
    aw specs check: all specs conform. 1 specs checked.
    ```
    4. `grep -n '^- Status:' .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md`:
    `4:- Status: approved`
    5. New history line in `## Workflow history`:
    `- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): R-12 scoped to runs that may retire an orchestrator and extended to a re-check at the retirement point; R-12 point 3 clarified that a refusing readiness lint rule is permitted and that R-5's rejection concerns exemptions only; new R-13 requires the 25kzda 2.5d readiness check at every status change and production handoff that would claim an orchestrator's Set is ready.`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `git diff` of the `r07vma` file; paste greps returning C.1's "credits an obligation", C.2's "quoted passage rather than a bare verdict", and C.3's "the omission of a needed final child IS detected". Paste `specs check` conforming, `- Status: approved` unchanged, and the new history line.
  - Observed evidence:
    1. `git diff .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md b/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    index c8464204a..e50c62ea0 100644
    --- a/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    +++ b/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    @@ -18,6 +18,7 @@

     ## Workflow history

    +- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): R9's probe bullet records the quoted-evidence answer and named-child credit, and both controls now feed the 25kzda 2.5d review-readiness function; Section 3a limit 1 updated; limit 5 rewritten because the omitted-final-child case is now detected by 25kzda 2.5d.
     - 2026-09-28 note (aw specs): Section 3a limit 1 noted by 3brgb6: orchestrator coverage probe now actually reads Completion criteria and Cross-IPD validation prose sections
     - 2026-09-19 approved (aw specs, --by-human): APPROVED by the human maintainer (Gabriele Fariello) 2026-09-19, recorded by the agent at their explicit instruction in session. Approval covers the design as hardened through two review rounds: R1a's typed child-tracking row as the enforcement mechanism (chosen over a prose vocabulary after the maintainer resolved OQ-02 as TYPED), R1b's rule that a cross-child check is a final child with sibling dependencies, the bounded review-time repair loop with honest exhaustion, the batch-report-then-refuse run gate, and the RETENTION of the semantic coverage probe beside the new control per 25kzda 2.5b. The maintainer is on notice of the principal cost: ZERO of 32 live orchestrator rows conform to the new grammar, so every one of the 11 pending orchestrators needs its checklist rewritten, and the migration route is the implementing plan's to choose under acceptance criterion 12. OQ-01 (keeping authoring instructions from drifting from the enforcing code) remains open and non-blocking.
     ## 1. The problem, and what the existing control does not reach
    @@ -178,7 +179,7 @@ scoped to a DIFFERENT and narrower question than the probe's, and the two coexis
       STRUCTURE rather than judging wording, and it is the thing review can repair in a loop.
     - THE PROBE answers "does this orchestrator carry work no child covers, including work stated only in
       prose?" It is semantic, and it remains the control for the continuation lines and the orchestrator's
    -  prose sections, which R1a explicitly does NOT parse.
    +  prose sections, which R1a explicitly does NOT parse. It quotes each passage it judges uncovered (spec `25kzda` 2.5b), and it credits an obligation the orchestrator's prose explicitly assigns by id6 to a child in its own `## Child IPDs` table. Both the shape check and the probe verdict are inputs to the single review-readiness function of spec `25kzda` 2.5d, which is how R3's "one implementation" extends to the status setters and the production action.

     Neither subsumes the other, and the ordering is shape check first (free, and repairable at review) then
     probe (costly, and the backstop for prose). A run the shape check refuses never reaches the probe, so the
    @@ -332,8 +333,7 @@ than one with a narrow scope.
     1. A CONFORMING CHECKLIST IS NOT EVIDENCE THAT AN ORCHESTRATOR CARRIES NO UNCOVERED WORK. It is evidence
        that every ROW is a well-formed child-tracking row. R1a deliberately does not parse the continuation
        lines, the `## Completion criteria` section, or the `## Cross-IPD validation` section, and an
    -   obligation can still be written there. That residue is the semantic probe's job, which is why `25kzda`
    -   2.5b's prohibition still binds and the probe is retained.
    +   obligation can still be written there. That residue is the semantic probe's job, which is why `25kzda` 2.5b's prohibition still binds and the probe is retained. Since Set `gradcover`, the probe's finding is a quoted passage rather than a bare verdict, and an obligation explicitly assigned in prose to a named child is credited, so the residue the probe reports is the residue an author can act on.
     2. THE SHAPE CHECK HAS NO RECALL QUESTION FOR ROWS, AND AN UNQUANTIFIED ONE FOR PROSE. Within a row the
        check is structural, so "recall" does not apply: a deliverable cannot take the typed form. Outside a
        row it has no reach at all. An implementer should measure how much of the real violation population
    @@ -346,10 +346,7 @@ than one with a narrow scope.
        put it in the prose R1a does not read, and plausibly phrase it past a probe too. The controls raise the
        cost of the ACCIDENTAL violation, which is the measured failure mode (`rh5tt6`, and the 2026-09-06
        `Readiness` incident, were both pattern-completion rather than deception).
    -5. THE TYPED SHAPE IS A CONSTRAINT ON THE ROW, NOT A PROOF ABOUT THE SET. It guarantees that what a row
    -   SAYS is a child-tracking obligation. It does not guarantee the Set's children actually cover the Set's
    -   work: a parent can conform perfectly while its author simply omitted a needed final child. R1b names
    -   the remedy but nothing detects the omission, and this spec does not claim to.
    +5. THE TYPED SHAPE IS A CONSTRAINT ON THE ROW, NOT A PROOF ABOUT THE SET. It guarantees that what a row SAYS is a child-tracking obligation. Since Set `gradcover` the omission of a needed final child IS detected, but by a different control: the review-readiness check of spec `25kzda` 2.5d, whose coverage condition reports any whole-Set obligation no listed child is named as performing, and which gates the orchestrator's status and its source's graduation. The row grammar itself still proves nothing about the Set.
     6. THE MIGRATION IS NOT DESIGNED HERE. Section 5 cost 3 states that 11 orchestrators need rewriting and
        names the cutover pattern; choosing between a cutover, a sweep, and a grandfather clause is the
        implementing plan's decision, and a wrong choice there could strand a Set mid-flight.
    ```
    2. Greps for C.1, C.2, C.3:
    - C.1: `grep -n "credits an obligation"`:
      `182:  prose sections, which R1a explicitly does NOT parse. It quotes each passage it judges uncovered (spec \`25kzda\` 2.5b), and it credits an obligation the orchestrator's prose explicitly assigns by id6 to a child in its own \`## Child IPDs\` table. Both the shape check and the probe verdict are inputs to the single review-readiness function of spec \`25kzda\` 2.5d, which is how R3's "one implementation" extends to the status setters and the production action.`
    - C.2: `grep -n "quoted passage rather than a bare verdict"`:
      `336:   obligation can still be written there. That residue is the semantic probe's job, which is why \`25kzda\` 2.5b's prohibition still binds and the probe is retained. Since Set \`gradcover\`, the probe's finding is a quoted passage rather than a bare verdict, and an obligation explicitly assigned in prose to a named child is credited, so the residue the probe reports is the residue an author can act on.`
    - C.3: `grep -n "the omission of a needed final child IS detected"`:
      `349:5. THE TYPED SHAPE IS A CONSTRAINT ON THE ROW, NOT A PROOF ABOUT THE SET. It guarantees that what a row SAYS is a child-tracking obligation. Since Set \`gradcover\` the omission of a needed final child IS detected, but by a different control: the review-readiness check of spec \`25kzda\` 2.5d, whose coverage condition reports any whole-Set obligation no listed child is named as performing, and which gates the orchestrator's status and its source's graduation. The row grammar itself still proves nothing about the Set.`
    3. `python3 -m agent_workflows specs check .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md`:
    ```text
    aw specs check: all specs conform. 1 specs checked.
    ```
    4. `grep -n '^- Status:' .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md`:
    `4:- Status: approved`
    5. New history line in `## Workflow history`:
    `- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): R9's probe bullet records the quoted-evidence answer and named-child credit, and both controls now feed the 25kzda 2.5d review-readiness function; Section 3a limit 1 updated; limit 5 rewritten because the omitted-final-child case is now detected by 25kzda 2.5d.`
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `git diff` of the `ipd-structure-and-linting` file; paste greps returning item 19 with `IPD-S408` and item 20 with `IPD-M112` and the D.2 paragraph's "Kind-parity at `pre-transition` is unchanged". Paste `specs check` conforming, `- Status: implemented` unchanged, and the new history line.
  - Observed evidence:
    1. `git diff .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    index d12d15378..8aab07467 100644
    --- a/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    +++ b/.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    @@ -489,6 +489,10 @@ For a new or migrated IPD, it MUST check at least:
     16. terminal status, history, directory, and lifecycle-commit metadata agree at `post-transition` to the extent repository state makes them deterministically observable (`IPD-S405`: an executed plan carries an `executed` workflow-history entry);
     17. RETIRED: the no-em/en-dash style rule (formerly rule code IPD-D701) is no longer checked by this command. The no-dash convention is a user-facing prose rule only (GUIDING_PRINCIPLES P13, the AGENTS.md execution contract); IPDs are internal/AI-facing artifacts, so the linter does not flag dashes in them. Any other Markdown style rules delegated to this command are applied only to authored prose outside code, with front matter values exempted by schema and other explicitly excluded constructs.
     18. code citations in authored prose carry a DURABLE ANCHOR (Section 10.2), surfaced advisory-only (`IPD-C801`) and gated on an authoring-date cutover so plans predating the rule are silent.
    +19. for an orchestrator plan at the `review-finalize` and `pre-execution` checkpoints, that it is ready for review per spec `25kzda` Section 2.5d (`IPD-S408`), evaluating conditions 1 to 3 directly and condition 4 by READING the plan's own coverage record (spec `25kzda` 2.5e), never by asking a model. An absent coverage record, or one whose fingerprint does not match the current text, is an error that names `aw ipd coverage <id6>` as the remedy. Because the record is in the plan, the result is the same on every clone and in CI. At the `author` checkpoint the rule is advisory only, so a plan being written is not refused for children not yet written.
    +20. that a coverage record (`- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:`) is either wholly absent or complete, and is matched by a `coverage` line in `## Workflow history` (`IPD-M112`), at every checkpoint, as an error (an incomplete or unattested record is a defect at any stage, unlike a missing child).
    +
    +Rule 19 is the one orchestrator-specific REFUSAL this command applies beyond `IPD-S407`. It does not change what `pre-transition` requires of an orchestrator (spec `77tr3o` R-5 and R-12 point 3): Kind-parity at `pre-transition` is unchanged. The check is the shared function, not a second implementation, so `aw ipd lint`, `aw check plans` and `aw ipd set` report identical findings for the same plan.

     The linter MAY detect exact prohibited lifecycle commands or reserved markers inside the execution checklist, but it MUST NOT claim semantic certainty that arbitrary prose does or does not describe a lifecycle transition. The template excludes terminal transition from the execution list; semantic review enforces the general prohibition.

    @@ -823,6 +827,7 @@ After the IPD-system Set lands:

     ## Workflow history

    +- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 10 gains rule 19 (IPD-S408, orchestrator review readiness per 25kzda 2.5d, reading the coverage record stored in the plan, model-free) and rule 20 (IPD-M112, a coverage record must be complete and attested by a history line) and a paragraph stating it does not alter pre-transition Kind-parity.
     - 2026-10-01 note (aw specs): Section 10.2 amended (Set hesb87 tx0q0e E-01..E-04): require durable anchor within logical unit and proximity window (default 80 chars, CITATION_ANCHOR_PROXIMITY_WINDOW) to fix whole-line detector blindness; record refusal to promote IPD-C801 to a gate on measured undefined pre-fix and residual post-fix false-positive rates.
     - 2026-08-26 note (aw specs): Section 11: begin baseline dirty-check is Scope-Paths-scoped (path-overlap, ipdgates-03 OQ-01), not whole-tree; disjoint dirt allowed to preserve concurrent multi-agent workflow (beginscope vaq9qf E-03)
     - 2026-09-21 note (aw specs): Section 10.2 added (citeanchor mzc019 E-01): an IPD code citation MUST carry a durable anchor (symbol path, or a quoted content string, with a line number only appended and never alone), because a bare file:line expires between authoring and execution and then silently misdirects an executor to unrelated valid code. States the rationale, the (a)/(b)/(c) preference order, the line-as-subject exception, and that enforcement is advisory-only (IPD-C801) and date-gated. Section 10 list item 18 appended to point at it; no existing item renumbered.
    ```
    2. Greps for D.1 (items 19, 20) and D.2:
    - Item 19 (`IPD-S408`): `grep -n "IPD-S408" .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`:
      `492:19. for an orchestrator plan at the review-finalize and pre-execution checkpoints, that it is ready for review per spec 25kzda Section 2.5d (IPD-S408), evaluating conditions 1 to 3 directly and condition 4 by READING the plan's own coverage record (spec 25kzda 2.5e), never by asking a model.`
    - Item 20 (`IPD-M112`): `grep -n "IPD-M112" .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`:
      `493:20. that a coverage record (- Coverage:, - Coverage-Fingerprint:, - Coverage-Checked:) is either wholly absent or complete, and is matched by a coverage line in ## Workflow history (IPD-M112), at every checkpoint, as an error (an incomplete or unattested record is a defect at any stage, unlike a missing child).`
    - D.2 paragraph: `grep -n "Kind-parity at \`pre-transition\` is unchanged" .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`:
      `495:Rule 19 is the one orchestrator-specific REFUSAL this command applies beyond IPD-S407. It does not change what pre-transition requires of an orchestrator (spec 77tr3o R-5 and R-12 point 3): Kind-parity at pre-transition is unchanged. The check is the shared function, not a second implementation, so aw ipd lint, aw check plans and aw ipd set report identical findings for the same plan.`
    3. `python3 -m agent_workflows specs check .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`:
    ```text
    aw specs check: all specs conform. 1 specs checked.
    ```
    4. `grep -n '^- Status:' .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`:
    `4:- Status: implemented`
    5. New history line in `## Workflow history`:
    `- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 10 gains rule 19 (IPD-S408, orchestrator review readiness per 25kzda 2.5d, reading the coverage record stored in the plan, model-free) and rule 20 (IPD-M112, a coverage record must be complete and attested by a history line) and a paragraph stating it does not alter pre-transition Kind-parity.`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `git diff --name-only` listing exactly the five spec paths. Paste one grep per cross-reference introduced (`r07vma` R3 in `25kzda`; `25kzda` 2.5d in `77tr3o`, `r07vma` and `ipd-structure-and-linting`; `IPD-S408` in `25kzda` and `ipd-structure-and-linting`) returning a hit in the target. Paste `python3 -m agent_workflows check specs` showing no finding beyond a pre-edit baseline you measured and pasted. Paste the bare `python3 -m pytest` summary line as the Order 02 baseline. Paste `aw ipd lint` on this plan conforming and `git diff --cached --name-only` immediately before committing.
  - Observed evidence:
    1. `git diff --name-only .aw/records/specs/`:
    ```text
    .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
    .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
    .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    ```
    2. Greps for cross-references:
    - `r07vma` R3 in `25kzda` (`grep -n "spec \`r07vma\` R3" .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`):
      `477:An orchestrator plan (\`- Kind: orchestrator\`) is READY FOR REVIEW only when ALL of these hold, evaluated by ONE shared function (one implementation, several consumers, the pattern of spec \`r07vma\` R3):`
    - `25kzda` 2.5d in `77tr3o` (`grep -n "spec \`25kzda\` Section 2.5d" .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md`):
      `235:- R-13 AN ORCHESTRATOR MAY NOT BE MARKED READY WHILE ITS SET IS NOT. Added 2026-10-04 by Set \`gradcover\` (plan \`hm1h3l\`). ... unless the orchestrator passes the review-readiness check of spec \`25kzda\` Section 2.5d. The check is ONE function shared by every consumer (spec \`r07vma\` R3).`
    - `25kzda` 2.5d in `r07vma` (`grep -n "spec \`25kzda\` 2.5d" .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md`):
      `182:  prose sections, which R1a explicitly does NOT parse. It quotes each passage it judges uncovered (spec \`25kzda\` 2.5b), and it credits an obligation the orchestrator's prose explicitly assigns by id6 to a child in its own \`## Child IPDs\` table. Both the shape check and the probe verdict are inputs to the single review-readiness function of spec \`25kzda\` 2.5d, which is how R3's "one implementation" extends to the status setters and the production action.`
      `349:5. THE TYPED SHAPE IS A CONSTRAINT ON THE ROW, NOT A PROOF ABOUT THE SET. It guarantees that what a row SAYS is a child-tracking obligation. Since Set \`gradcover\` the omission of a needed final child IS detected, but by a different control: the review-readiness check of spec \`25kzda\` 2.5d, whose coverage condition reports any whole-Set obligation no listed child is named as performing, and which gates the orchestrator's status and its source's graduation. The row grammar itself still proves nothing about the Set.`
    - `25kzda` 2.5d in `ipd-structure-and-linting` (`grep -n "spec \`25kzda\` Section 2.5d" .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`):
      `492:19. for an orchestrator plan at the \`review-finalize\` and \`pre-execution\` checkpoints, that it is ready for review per spec \`25kzda\` Section 2.5d (\`IPD-S408\`), evaluating conditions 1 to 3 directly and condition 4 by READING the plan's own coverage record (spec \`25kzda\` 2.5e), never by asking a model.`
    - `IPD-S408` in `25kzda` and `ipd-structure-and-linting`:
      - `25kzda` line 486: `aw ipd lint at review-finalize and pre-execution (rule IPD-S408);`
      - `ipd-structure-and-linting` line 492: `ready for review per spec 25kzda Section 2.5d (IPD-S408)`
    3. `python3 -m agent_workflows check specs`:
    Pre-edit baseline:
    ```text
    AW check  specs                                                            89 ms
    ✓ CONFORMS  21 specs checked

    Findings:
      Issue: cross-tree collisions NOT checked by a per-type run
      - <collisions>
        1. <collisions>
        Fix: aw check all


    Evidence
      checked  21
      errors  0   warnings  0   info  1

    Next  aw specs check
    Agent output: --agent
    ```
    Post-edit verification:
    ```text
    AW check  specs                                                            89 ms
    ✓ CONFORMS  21 specs checked

    Findings:
      Issue: cross-tree collisions NOT checked by a per-type run
      - <collisions>
        1. <collisions>
        Fix: aw check all


    Evidence
      checked  21
      errors  0   warnings  0   info  1

    Next  aw specs check
    Agent output: --agent
    ```
    4. Bare `python3 -m pytest` summary line (Order 02 baseline):
    ```text
    5083 passed, 2 skipped, 3 warnings in 426.34s (0:07:06)
    ```
    5. `python3 -m agent_workflows ipd lint .aw/records/plans/pending/20261004-gradcover-01-hm1h3l-amend-the-run-retirement-conformance-and-ipd-specs-for-orche.ipd.md`:
    ```text
    - >  ◕  approved     plan        20261004-gradcover-01-hm1h3l  [high]  [blocking]  conforming
    ```
    6. `git diff --cached --name-only` immediately before committing:
    ```text
    .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
    .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md
    .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
    .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `git diff` of the `ipd-spec` file; paste greps returning "Every BACKWARD move between the non-terminal plan statuses is legal", "APPROVAL WITHDRAWN" and "can never start a loop". Paste `specs check` conforming, `- Status: implemented` unchanged, and the new history line.
  - Observed evidence:
    1. `git diff .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`:
    ```diff
    diff --git a/.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md b/.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
    index bfebe7d80..27ceb05de 100644
    --- a/.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
    +++ b/.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md
    @@ -20,7 +20,7 @@ Author from the template (`assess/templates/ipd.md`), or generate a conformant s

     - Metadata block (a bullet `- Field: value` list after the H1 title, NOT YAML front matter; "YAML front matter" means only actual `---` YAML, which the parser ignores): required `Date`, `Kind` (`child` or `orchestrator`), `Concern`, `Scope`, `Status`, `Author`; `Set` and `Order` together when in an ordered Set (`Order: 0` for an orchestrator, `>= 1` for a child); `Approval` when and only when `Status: approved`; `Highest E allocated` once any `E-*` exists (the allocation watermark); the `Quarantine`/`Quarantine owner`/`Quarantine follow-up` trio only on a quarantined nonterminal plan.
     - The H2 SECTION ORDER is exact and per-kind (child and orchestrator differ), enumerated in the schema. In BOTH kinds `## Detailed Implementation Checklist (TODO)` is the H2 IMMEDIATELY AFTER `## Goal` and `## Validation and cross-check ...` is the H2 IMMEDIATELY BEFORE `## Approval and execution gate`. (There is no "near the top/end"; placement is exact.)
    -- `## Workflow history` (append one dated line per workflow touch; never rewrite prior lines). Line direction in the file is NOT normative (writers prepend, authors append); readers derive order from record dates plus per-block direction and treat an unresolvable same-date tie as unordered. The durable fix is the `seq` journal of spec `2vev8j` 4.3. The only legal backward lifecycle transitions are `approved -> reviewed`, `auto-approved -> reviewed` (spec `2vev8j` 4.8 / spec `25kzda` 4.5), and `reviewed -> to-review` (re-review after revision, maintainer ruling 2026-09-26); every other backwards move fails closed.
    +- `## Workflow history` (append one dated line per workflow touch; never rewrite prior lines). Line direction in the file is NOT normative (writers prepend, authors append); readers derive order from record dates plus per-block direction and treat an unresolvable same-date tie as unordered. The durable fix is the `seq` journal of spec `2vev8j` 4.3. Every BACKWARD move between the non-terminal plan statuses is legal (`approved` or `auto-approved` to `reviewed`, `to-review` or `draft`; `reviewed` to `to-review` or `draft`; `to-review` to `draft`), because a plan whose spec, scope, dependencies or cited code changed after it was approved in a way that affects how it would be implemented, or that would undo work implemented since, is unsafe to execute and MUST be demoted. Added 2026-10-04 by plan `hm1h3l`; this supersedes the earlier three-edge enumeration (spec `2vev8j` 4.8 asked for the legal edges to be enumerated here, and this sentence is that enumeration). A backward move into a terminal status, and any move out of a terminal status, stays illegal (that is the separate terminal-reopen guard). EVERY BACKWARD MOVE IS LOUD: it requires a reason (`--message`), the setter prints a warning naming the plan, the old and new status and the reason, and the workflow-history line records `demoted <from> -> <to>: <reason>`; a move out of `approved` or `auto-approved` additionally records `APPROVAL WITHDRAWN`. An AUTOMATED demotion can never start a loop. For an orchestrator, promotion (to `to-review`, `reviewed`, `approved` or `auto-approved`) and automated demotion are decided by the same check (spec `25kzda` 2.5d) over the same recorded verdict for the same text: for unchanged text the check cannot both pass (allowing promotion) and fail (requiring demotion), so it can only move again after someone edits it. For any other plan no tool demotes automatically, so every demotion is a deliberate, reasoned act. No runner ever writes `approved` (`25kzda` 4.5), and a runner's `auto-approved` of an orchestrator passes the same check, so an automated demotion is never followed by an automated re-approval of unchanged text.
     - `## Detailed Implementation Checklist (TODO)` (mandatory): the EXECUTION checklist. Only executable leaves are checkboxes; each carries a unique `E-NN` id, `Depends on:` (`none` or comma-separated `E-*`), `Expected outcome:`, and `Execution state:` (`pending`|`performed`|`blocked`|`failed`). `E-* checked` means the action was PERFORMED, not that it was verified (F-07). The terminal lifecycle transition is NOT an `E-*` item (F-08); it is a post-gate transaction (see the lifecycle line). An `Expected outcome` counting live artifacts must state a property rather than an authored count; see `.aw/system/workflows/plan-review/plan-review.md` Rubric G for the re-derivation convention and code-facts exemptions.
     - `## Validation and cross-check` (mandatory): a SEPARATE evidence pass. Exactly one `V-NN validates E-NN` row per `E-NN` (a 1:1 bijection), each with `Required evidence:`, `Observed evidence:`, and `Result:` (`pending`|`pass`|`blocked`|`failed`). `V-* pass` means the evidence was INSPECTED and supports the expected outcome. Both the CREATOR (authors both checklists) and the REVIEWER (assesses both) are responsible for it (DECISIONS D115).
     - `## Open questions`: each question is an `### OQ-NN:` with `Blocking:` (`yes`|`no`), `Status:` (`open`|`resolved`|`deferred`), `Owner:`, and a resolution/deferral rationale. A blocking question may not be deferred and must be resolved before `pre-execution` (F-09).
    @@ -45,6 +45,7 @@ Size thresholds are WARNINGS and review triggers, not caps: the defaults are mor

     ## Workflow history

    +- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): every backward move between non-terminal plan statuses is now legal and mandatory when a plan's inputs changed materially after approval; every backward move requires a reason, warns, and records 'demoted <from> -> <to>: <reason>' (plus APPROVAL WITHDRAWN when leaving approved/auto-approved); loop-freedom stated for automated demotion (one check decides an orchestrator's promotion and demotion; no tool demotes another plan automatically; runners never write approved).
     - 2026-09-26 note (aw specs): plan pyuhnl: added reviewed -> to-review to legal backward transitions enumeration per maintainer ruling 2026-09-26
     - 2026-09-24 amended (tgop8e): added one-sentence pointer in checklist requirements to plan-review Rubric G for the live-artifact re-derivation convention.
     - 2026-08-08 migrated (aw specs): normalized status to `implemented` (was: canonical reference; produced by IPD `20260726-ipdcomplete-02-h409oe-ipd-spec-and-always-loaded-directive` (Set `ipd-completeness-guardrails`, Order 2))
    ```
    2. Greps for E.1:
    - "Every BACKWARD move between the non-terminal plan statuses is legal":
      `23:Every BACKWARD move between the non-terminal plan statuses is legal (\`approved\` or \`auto-approved\` to \`reviewed\`, \`to-review\` or \`draft\`; \`reviewed\` to \`to-review\` or \`draft\`; \`to-review\` to \`draft\`), because a plan whose spec, scope, dependencies or cited code changed after it was approved in a way that affects how it would be implemented, or that would undo work implemented since, is unsafe to execute and MUST be demoted.`
    - "APPROVAL WITHDRAWN":
      `23:the workflow-history line records \`demoted <from> -> <to>: <reason>\`; a move out of \`approved\` or \`auto-approved\` additionally records \`APPROVAL WITHDRAWN\`.`
    - "can never start a loop":
      `23:An AUTOMATED demotion can never start a loop. For an orchestrator, promotion (to \`to-review\`, \`reviewed\`, \`approved\` or \`auto-approved\`) and automated demotion are decided by the same check (spec \`25kzda\` 2.5d) over the same recorded verdict for the same text: for unchanged text the check cannot both pass (allowing promotion) and fail (requiring demotion), so it can only move again after someone edits it.`
    3. `python3 -m agent_workflows specs check .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`:
    ```text
    aw specs check: all specs conform. 1 specs checked.
    ```
    4. `grep -n '^- Status:' .aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`:
    `4:- Status: implemented`
    5. New history line in `## Workflow history`:
    `- 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): every backward move between non-terminal plan statuses is now legal and mandatory when a plan's inputs changed materially after approval; every backward move requires a reason, warns, and records 'demoted <from> -> <to>: <reason>' (plus APPROVAL WITHDRAWN when leaving approved/auto-approved); loop-freedom stated for automated demotion (one check decides an orchestrator's promotion and demotion; no tool demotes another plan automatically; runners never write approved).`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, and approval of THIS plan is approval of the contract the rest of Set `gradcover` implements. Commit only the five declared spec paths through `aw commit <plan> -- <paths>`; never `git add -A`; never push. Do not change any spec's `- Status:`. Under a runner, the runner performs `aw ipd begin`/`aw ipd finalize`; by hand, run `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never hand-edit `- Status: executed`. Every `V-*` demands the ACTUAL pasted command output; never paraphrase or claim a check you did not run.
