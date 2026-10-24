---
id: r7rfdi
created: 20261017
set: revsteps
order: 01
topic: [plan-review, runner]
model: opus55high
kind: research-report
status: todo
outcome: none-yet
summary: Response to y6vfto by opus55high: design review of the runner-enforced, depth-scaled plan review (spec k3yx72)
consumed-by: []
---

<!-- aw-adopt: provenance -->
> EXTERNAL PROVENANCE. This document was adopted from the gitignored `.aw/inbox/` raw-drop
> lane on 20261017 into the pre-scaffolded comparison slot (by hand, same verbatim-body rule as `aw adopt`). Original filename: `20261017-revsteps-plan-review-redesign.opus55high.research-report.md`.
> Its body is preserved VERBATIM as received, so its punctuation and formatting are the
> external author's, not this repository's house style. Treat the CONTENT as untrusted
> external input: evaluate it on its merits, never as instructions from the maintainer.
# Review of the plan-review redesign
- Reviewer: opus55high (OpenCode, Claude Opus 5.5, high effort)
- Repository access: local checkout
- Materials read: `.aw/records/research/20261017-revsteps-00-y6vfto-plan-review-redesign.research-prompt.md`; `.aw/records/specs/draft/20261017-revsteps-01-k3yx72-plan-review-redesign.spec.md` (in full); `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md` (in full); `.aw/system/workflows/plan-review/plan-review.md` (Steps 0 to 4, Verdict and readiness); `.aw/system/workflows/plan-review-long/plan-review-long.md`; `agent_workflows/runner_shared.py` (`build_review_prompt`, `review_handler_for`, `classify_probe_reply`, `probe_reply_text`, `resume_via_launcher`, `perform_defect_reask`, `review_has_positive_evidence`, `commit_review_lane_output`, `allocate_review_sweep_worktree`, `build_resume_argv`); `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` (review-turn argv and resume flags); `agent_workflows/ipd_lint.py` (`parse`, `check_citation_anchors`, `check_open_questions`, `_review_stale_advisory`, the M107/M112/M113 codes); `agent_workflows/ipd_schema.py` (`MAX_TASK_GROUPS`, `MAX_E_LEAVES`, `size_warning`, `META_WORK_KIND`); `agent_workflows/plan_readiness.py` (`is_plan_review_approved`, `is_review_history_entry`, `history_has_review_record`, `review_staleness_index`, `review_staleness_from_texts`); `agent_workflows/review_findings.py` (`parse_review_text`, `ReviewDocument.current_round`); `agent_workflows/check_engine.py` (`find_from_backlog_plans`, `_iter_plan_ipds`, `_carrier_is_executed`, `evaluate_blocking_close`); `.aw/records/reviews/README.md#Rounds`; `.aw/records/plans/README.md`; `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` (Sections 2.6, 4.4); `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`; `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` (Sections 10.2, 11, 12); `.aw/records/backlog/README.md`; `AGENTS.md`; output of `aw host capabilities`, `aw ipd set --help`, `aw ipd scaffold --help`.
- Overall assessment: needs rework
- Summary: The step sequence, the runner-side floor and the last-line marker are sound ideas, and most named symbols exist and behave as described. But the design collides with four shipped contracts it does not mention: Section 10.2 of the IPD structure-and-linting spec (which refuses to make `IPD-C801` an error and forbids retrofitting citations), the review-record "current round" rule, the review-staleness and auto-approve predicates (which key on a `plan-review:` commit subject and a review history record), and the backlog close rule (which counts a superseded carrier as unfinished forever). Its depth floor, measured against 1,544 real plans, puts almost every plan at `standard` or above, so the cost reduction the depth model promises does not materialize.

## 6.2 Top issues

- **F-01** ranks first because Section 7 contradicts an implemented, deliberately measured contract (spec `20260802-1904` Section 10.2), and the design names the wrong spec as the one it amends, so the conflict would not even be seen during spec review.
- **F-02** ranks second because re-review rounds written as new `## Round <n>` sections would make each partial re-review round the only "current" round, so findings raised in the full first pass silently stop gating.
- **F-07** ranks third because the split step, as written, turns every `Blocks-Release` backlog item it touches into one that can never close on the HANDOFF route, and it bypasses the plan's own retirement and naming tooling.

## 6.3 Findings

| Field | Content |
| --- | --- |
| ID | F-01 |
| Severity | blocker |
| Category | citations |
| Location | §7 (the `IPD-C801` paragraph and "Migration"), §11 row "Spec", §2 "Out of scope" |
| Issue | The design changes `IPD-C801` to flag any line-number citation and to become an error for new plans after a cutover, and it has review step R1 rewrite existing citations "as each plan passes review". The implemented spec that owns this rule refuses both changes on the record. It says the advisory tier "IS A MEASURED FINAL POSITION, NOT A PROVISIONAL ONE, AND PROMOTION TO A GATING SEVERITY IS REFUSED". It also says "Existing citations are NOT retrofitted", because rewriting them in in-flight plans risks corrupting evidence. The design also names the wrong spec: §11 says it amends "Section 10.2 of the IPD spec" and the research prompt names `20260726-1340-01-ipd-spec.spec.md`. That file has no Section 10.2. Section 10.2 is in `20260802-1904-01-ipd-structure-and-linting.spec.md`. A third, smaller mismatch: the shipped rule already accepts a line number as a "trailing convenience" next to a symbol (form (c)), and the new rule would flag that form. |
| Evidence | `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md#10.2 Code-citation anchors (a citation MUST name something that survives to execution)`, quoting "PROMOTION TO A GATING SEVERITY IS REFUSED" and "Existing citations are NOT retrofitted". `agent_workflows/ipd_lint.py::check_citation_anchors` (docstring: "Returns ADVISORY diagnostics only"). `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` has only the headings "What an IPD MUST contain" to "Workflow history" and no Section 10. Design §11: "Section 10.2 of the IPD spec (citations)". |
| Basis | Verified |
| Proposed change | Name `20260802-1904` Section 10.2 as the amended spec in §11 and in the research prompt. Then do one of two things. (a) Keep `IPD-C801` advisory, and put enforcement in the new RESOLVER instead. A resolver checks whether a citation resolves, not what form it takes, so it does not have the false-positive problem that drove the refusal. Make R1's rewrites forward-only: R1 may ADD a durable anchor next to an old offset, but must not delete the offset. (b) Explicitly reverse the Section 10.2 ruling, with new measurements that answer its two stated reasons. Either way, keep form (c) ("symbol plus trailing line") legal. Recount the "166 citations" claim (see F-12). |

| Field | Content |
| --- | --- |
| ID | F-02 |
| Severity | blocker |
| Category | rereview |
| Location | §8.3, §10 (last paragraph), §4 S-04 postcondition |
| Issue | §10 says each review step "adds its own subsection inside the current `## Round <n>`". §8.3 says a re-review round reruns the S-04 steps but limits them to the changed sections. Review-record readers treat the LAST `## Round` as the only current one, and gates read only current findings. If each re-review round opens a new `## Round`, its partial re-review becomes the only current round, and an unfixed `HIGH` from the full first pass stops counting. If re-review rounds instead append to the same `## Round`, the S-04 postcondition ("each required review step added its own section to the current review round") is already satisfied by the first pass, so the runner cannot tell whether the re-review steps ran. The design does not say which of these happens. |
| Evidence | `agent_workflows/review_findings.py::ReviewDocument.current_round` ("The LAST round in the file"); `agent_workflows/review_findings.py::ReviewDocument.current_findings` ("This is the accessor a gate must use"); `.aw/records/reviews/README.md#Rounds` ("Only the current round's findings are live"). Design §8.3: "limit the review to the changed sections and the sections that depend on them". |
| Basis | Verified (reader behavior); Inferred (the consequence for the design, since the design does not specify the layout) |
| Proposed change | Define one `## Round <n>` per review INVOCATION (one runner review action), and record re-review passes inside it as `### Pass <k>` subsections. Require the final pass to carry forward, in its `### Findings` table, every finding from earlier passes with its final Decision. The reader then sees one complete current table. The S-04 postcondition becomes "pass k contains one subsection per required step, each with a `Findings` table (possibly empty) and the step's required evidence block" (see F-05). Amend `.aw/records/reviews/README.md#Sections` and `review_findings.parse_review_text` in Order 01 accordingly. |

| Field | Content |
| --- | --- |
| ID | F-03 |
| Severity | major |
| Category | gate-interaction |
| Location | §4 S-01, §4 S-07, §11 Order 04 |
| Issue | Three existing gates read the OUTPUT of today's single review turn in specific shapes. The design does not say the multi-step review keeps producing them. (1) Review staleness finds the review baseline by the newest commit whose subject starts with `plan-review:` and compares that blob with the current plan. The current workflow's hardened-result commit uses that subject. The runner's own fallback commit does not (`review(<host>): record the review of <id6>`). The design moves "the commit" into S-07 without fixing the subject. (2) Auto-approval requires a review history record, recognized by `/plan-review` in the record's middle or by a verdict-leading message, plus a valid `- Readiness:`. (3) Spec `25kzda` Section 4.4 `IPD-REVIEW-HISTORY` requires "Exactly one new review entry" per review. A two-round re-review that writes a history line per round would break that check. The design also writes `- Review-Depth:` in S-03, before review edits, so that write lands inside the reviewed snapshot. |
| Evidence | `agent_workflows/plan_readiness.py::review_staleness_index` (`if not subject.startswith("plan-review:")`); `.aw/system/workflows/plan-review/plan-review.md#Hardened-result commit` ("`plan-review: harden <scope> (revisions applied)`"); `agent_workflows/runner_shared.py::commit_review_lane_output` (subject `review({host_label}): record the review of {id6}`); `agent_workflows/plan_readiness.py::is_review_history_entry`; `agent_workflows/plan_readiness.py::is_plan_review_approved`; spec `25kzda` `#4.4 IPD review verification`, row `IPD-REVIEW-HISTORY`. |
| Basis | Verified |
| Proposed change | Add a §4 subsection "Outputs that existing gates read", stating: S-07 writes exactly one `## Workflow history` line in the existing `/plan-review (<agent/model>): <verdict>; <ids>` form per review invocation, whatever the number of re-review passes. The final commit subject starts with `plan-review:`. The runner's fallback lane commit is changed to the same prefix, or `review_staleness_index` is changed to also accept it (a separate fix that is needed today anyway). `- Review-Depth:` is written in S-07 together with `- Readiness:`. Add `- Review-Depth:` to the fields that `ipd_lifecycle.frozen_region_digest` excludes, so the field cannot make a review look stale. Add a test that a two-pass review yields one history line and one `plan-review:` commit. |

| Field | Content |
| --- | --- |
| ID | F-04 |
| Severity | major |
| Category | depth-model |
| Location | §5 (the `standard` row), §6 (the prompt count table), §13 row 1 |
| Issue | The floor conditions do not discriminate on this repository's plans. I applied the §5 conditions (with E-leaves counted from checklist lines) to all 1,544 plans dated 2026 in `pending/` and `executed/`. Spanning "more than one top-level directory" holds for 1,068 of them, mostly because nearly every code plan lists `agent_workflows/` and `tests/` together (963 plans). "More than 3 Scope-Paths" holds for 672 and "more than 5 E-leaves" for 654. Of the 30 pending plans, 0 come out `simple`, 22 `standard` and 7 `complex`. Of the 439 plans executed since 2026-10-01, 43 come out `simple`. The `simple` tier exists only for plans that touch one directory. A plan that changes code and adds its test, the normal case, can never be `simple`. So the stated benefit (problem 2, "the same review effort for every plan") becomes "almost every plan gets the same `standard` review". |
| Evidence | Measurement on the local checkout, 2026-10-17, by a script applying §5 to each plan's `- Scope-Paths:`, `- Kind:`, `- Work-Kind:` and E-checkbox lines (counts above). `agent_workflows/ipd_schema.py::size_warning` (`task_group_count > MAX_TASK_GROUPS or e_leaf_count > MAX_E_LEAVES`) confirms the `complex` thresholds of 18 and 5. |
| Basis | Verified (counts); Inferred (that this is undesirable) |
| Proposed change | Count Scope-Paths by distinct non-test top-level directory, so `tests/` and the code it tests count as one. Replace "more than 3 Scope-Paths" with a count of distinct production source files. Add signals that predict review risk better than size: (a) the plan changes a public contract (a CLI flag, an `aw.agent/v1` field, a file format, a spec), detectable from Scope-Paths under `docs/`, `.aw/records/specs/` or files named in a configured list; (b) `- Item-Dependencies:` is non-empty; (c) the plan carries `- Blocks-Release:`. Before fixing thresholds, run the floor over the corpus and publish the resulting tier distribution in the spec, with a target such as "about a third `simple`". |

| Field | Content |
| --- | --- |
| ID | F-05 |
| Severity | major |
| Category | enforcement |
| Location | §4 (S-02 to S-05 postconditions), §5 (rating), §8.1 rule 3 |
| Issue | Each agent-step postcondition can be met without doing the step. (1) S-04 checks only that a subsection exists, so an empty subsection or "No findings" passes. (2) S-02 passes when the proofreading changed nothing, and the change summary can be "none". (3) S-03 passes whenever the rating is at the floor, so always answering the floor, with no reasoning, always passes. (4) S-05 passes when every question carries `Blocking:`, so marking every question `Blocking: no` passes and removes the `no-go` that blocking questions would cause. The existing workflow names a mislabeled `Blocking: no` as "the single point of failure". The design admits only one of these limits (§4.1 "cannot prove that the prose improved"). |
| Evidence | Design §4 table, postcondition column; §5 "The agent's S-03 rating is final when it is at or above the floor"; `.aw/system/workflows/plan-review/plan-review.md#Verdict and readiness` ("mislabelling is now the single point of failure"); spec `25kzda` `#4.4 IPD review verification` ("The quality of a review is not deterministically provable"). |
| Basis | Verified (what the postconditions check); Inferred (agent behavior) |
| Proposed change | Make each step produce EVIDENCE the runner can check against the repository, not just a heading. R1: the resolver's machine output for every citation, which the runner re-runs and compares. R2: a table with one row per `E-*`/`V-*` id in the plan, which the runner diffs against `ipd_lint.parse(...).exec_leaves`. R3/R4: one row per rubric item in the step file (for example `A1` to `G7`), each with `applies`/`not applicable` and a quoted plan passage or a durable citation that the runner checks exists in the plan or repository, the same check `classify_probe_reply` applies to `QUOTE:` lines. S-03: the agent must state the measured signals and a one-line reason even at the floor. S-05: every `Blocking: no` added or changed in this review needs a one-line `- Resolution or deferral rationale:`, which `ipd_lint.check_open_questions` already parses. State plainly in §13 that these raise the cost of fake compliance but do not prove review quality. |

| Field | Content |
| --- | --- |
| ID | F-06 |
| Severity | major |
| Category | feasibility |
| Location | §4 (sequence), MD-6, §11 Order 04, §13 rows 1 and 6 |
| Issue | The design does not say how one session survives failures across 8 to 11 prompts, and it misses three shipped constraints. (1) Both hosts can resume a session (`aw host capabilities`: `supports_session_resume` yes for both). But on Antigravity, when no conversation id is captured the driver falls back to `--continue`, which resumes the most recent conversation and not necessarily this review's. (2) Each host's launcher is pinned by tests to "EXACTLY TWO callers", and follow-up turns go through `resume_via_launcher` and are counted in `session_turn_counts`. A multi-prompt review adds a new kind of follow-up turn that existing session-turn rules and fakes must accept. (3) The review prompt today is a bare slash command, deliberately free of prose because the host absorbs anything on the command line as `$ARGUMENTS`. Isolated reviews add the lane notice on following lines. Step prompts that pass a step file path and a plan path must keep that shape. Unaddressed failure cases: a host crash or timeout between steps; `aw <host> run resume` of an interrupted run (which step restarts, in which session?); another agent editing the plan in main while the review runs in the shared sweep lane. |
| Evidence | `aw host capabilities` output (both hosts: `supports_session_resume` yes); `agent_workflows/agy_runipd.py` launch argv (`if session_id: ... "--conversation" ... elif use_continue: argv.append("--continue")`); `agent_workflows/runner_shared.py::resume_via_launcher` ("each host's launcher has EXACTLY TWO callers"); `agent_workflows/runner_shared.py::perform_defect_reask` ("a re-ask CONSUMES a turn"); `agent_workflows/runner_shared.py::build_review_prompt` ("Deliberately prose-free ON THE COMMAND LINE"); `agent_workflows/runner_shared.py::allocate_review_sweep_worktree` ("the ONE lane every review turn of `run_id` runs in"). |
| Basis | Verified (constraints); Inferred (failure behavior, which the design does not specify) |
| Proposed change | Add a §4 subsection "Session and failure behavior". (a) Capture the session id after the first agent step, and refuse (fail the review, leave `to-review`) rather than fall back to `--continue` for later steps. (b) Record the last completed step and the plan digest after each step in the run state. On resume, restart at the first incomplete step in the same session if it can be resumed, otherwise restart from S-02 in a new session with the plan as it now is. Never skip S-02. (c) Before each step, compare the main-branch plan digest with the digest the lane started from. If main changed, stop with a named refusal (`review-plan-changed-upstream`) rather than merge two reviews. (d) Route step prompts through the existing review launch path, or record that Order 04 relaxes the "two callers" pin and updates its tests. (e) Keep each step prompt in the existing shape: the command on line 1, prose on later lines. |

| Field | Content |
| --- | --- |
| ID | F-07 |
| Severity | major |
| Category | split |
| Location | §9 steps 1 to 3, OQ-4, MD-2 |
| Issue | Four problems with the split step. (1) Release gates: the backlog close rule counts EVERY plan carrying `- From-Backlog: <item>` as a carrier, and a plan carrier is "finished" only if its path contains `executed`. The plan iterator walks the whole plans tree, `superseded/` included. So after a split, the superseded original still carries `- From-Backlog:` and is never "executed". The item can never close on the HANDOFF route, and only `--evidence` or `--blocks-release -` can close it. (2) Tooling: `aw ipd scaffold` creates a plan for a NEW Set with `--set` and `--order`. The design does not say which Set id the new plans get. If they reuse the original plan's Set, the original's Order slot collides. The design's own §11 says "the runner retires the original" but gives no tool for it, and the plans README says retirement is a separate `RETIRED` header plus `git mv` flow that finalize does not perform. (3) Partly reviewed plans: if the original was `reviewed` or `approved` before this review (a re-review), its readiness and any human approval are discarded silently. (4) Requeue order: the new orchestrator depends on its children, and the design does not say the new plans are reviewed in this run or a later one. Nor does it say whether the orchestrator coverage gate runs before the children exist. |
| Evidence | `agent_workflows/check_engine.py::find_from_backlog_plans` (iterates `_iter_plan_ipds`); `agent_workflows/check_engine.py::_iter_plan_ipds` (`base.rglob("*.ipd.md")` over the whole plans tree); `agent_workflows/check_engine.py::_carrier_is_executed` (`return "executed" in p.parts`, with the comment that superseded and not-executed "are terminal but not finished"); `.aw/records/plans/README.md` ("Plan RETIREMENT (`superseded`/`not-executed`) is the separate `RETIRED ...` header + `git mv` flow"); `aw ipd scaffold --help` (`--set SET --order ORDER` required). |
| Basis | Verified (close rule and tooling); Inferred (the design's intent on Set ids and ordering) |
| Proposed change | (a) Answer OQ-4 "yes, and in the same transaction clear `- From-Backlog:` and `- From-Spec:` on the superseded original" (or teach `_carrier_is_executed`'s callers to ignore superseded carriers that a successor replaced). Add a test that a split does not strand a release-blocking backlog item. (b) Mint a NEW Set id for the split, so no Order slot collides, and record `Superseded-By: <new setid>` in the `RETIRED` header. (c) Add `aw ipd retire <id6> --superseded-by <setid> --reason ...` (or name the existing verb if there is one) so the runner does not hand-edit a header. (d) Refuse to split a plan that was `approved` before the review began. Leave it `no-go` with a finding, because discarding a human approval is a human decision. (e) Queue the new children first and the orchestrator last, in the same run, using the existing dependency-depth sort, and run the coverage gate on the orchestrator after its children are authored. |

| Field | Content |
| --- | --- |
| ID | F-08 |
| Severity | major |
| Category | rereview |
| Location | §8.1 rule 3, §8.2, §8.3, §13 row 6 |
| Issue | The loop terminates, but too often it terminates in a failure. (1) The proofreading step S-02 runs before S-06 on every review. Any changed requirement word in S-02 is a runner trigger (§4.1). So any review in which proofreading changes "should" to "must" always gets at least one re-review. (2) A protocol failure counts as `AGAIN`. After two rounds, the third trigger forces `no-go` with "re-review limit reached". So two garbled markers, or one garbled marker plus one runner trigger in round 2, put a clean plan at `no-go`, and the human must re-run the review. (3) §8.2 compares S-01 with S-06, cumulatively. In round 2 that comparison still sees the round-1 changes, so the trigger fires again even when round 2 changed nothing, and the loop always exhausts if round 1 changed any E-item or Scope-Paths. (4) A re-review round reruns only S-04 to S-06, not S-02, so a re-review edit is never proofread except by the MD-8 one-line reminder. |
| Evidence | Design §4.1 ("records the change as a re-review trigger"); §8.1 rule 3; §8.2 ("changed between S-01 and S-06"); §8.3 ("reruns the S-04 review steps ..., and then S-05 and S-06"; "the agent must then write `no-go`"). |
| Basis | Verified (design text); Inferred (outcomes) |
| Proposed change | (a) Compare each round with the START OF THAT ROUND, not with S-01. (b) Make a protocol failure re-ask ONCE in the same session for the marker only (the existing `perform_defect_reask` pattern), and count it as `AGAIN` only if the re-ask also fails. (c) Do not count a requirement-word change from S-02 as a runner trigger, because S-04 has not yet reviewed the plan. Instead, list S-02's requirement-word changes as an input that R2 and R4 must confirm in pass 1. (d) Write the limit outcome as `no-go` with an open question `Blocking: yes` naming what still changed, so `aw ipd recheck-readiness` can clear it after a human looks, rather than leaving a `no-go` with no recorded reason. |

| Field | Content |
| --- | --- |
| ID | F-09 |
| Severity | major |
| Category | gap |
| Location | §4.1 |
| Issue | The wording-only check protects front matter, H2 headings, ids, checkboxes and open-question ids. It misses the parts of a plan whose wording an executor actually acts on and a proofreader is most likely to change: each item's `Expected outcome`, `Depends on`, and `Execution state` sub-fields, the `## Validation` evidence demands, and each open question's `Status:` and rationale. A proofreading edit could change an `Expected outcome` from "exit 0" to "exit 1", or set an `Execution state` to `performed`, and pass. The second change is exactly the attestation forgery `AGENTS.md` forbids. The parser already exposes these sub-fields. |
| Evidence | `agent_workflows/ipd_lint.py::parse` returns `exec_leaves` whose `Leaf.fields` include `Depends on`, `Expected outcome` and `Execution state`, and `open_questions` entries with `Status` and `Resolution or deferral rationale` (observed on a pending plan). `AGENTS.md` ("never hand-write ... an `Execution state: performed` for work you did not do"). |
| Basis | Verified |
| Proposed change | Add to the refusal list: any change to an `Execution state` value; any change to an open question's `Status`; and any change to the set of field NAMES under each leaf. For `Expected outcome`, `Depends on` and the validation demands, whose prose may legitimately be clarified, record a change as a runner trigger (like requirement words) rather than refusing it, so S-04 must look at it. |

| Field | Content |
| --- | --- |
| ID | F-10 |
| Severity | major |
| Category | gap |
| Location | §4 S-05, §4 last paragraph, §2 "In scope" |
| Issue | Two contracts the review owns today are missing from the step allocation. (1) The `IPD-S407`/`IPD-S408` orchestrator repair loops, with their two-attempt budget and the rule to leave `- Readiness:` absent when they are exhausted. The design gives S-07 no such exception and its postcondition requires a valid `- Readiness:` value, so the runner would refuse the correct behavior. (2) The Step 4 escalation rule: every unfixed finding at or above `review_findings_gate.block_at` must become a `Blocking: yes` question with `- Finding: <ID>`. The design's S-05 covers question resolution but not this escalation, and §6 does not assign it to any step. |
| Evidence | `.aw/system/workflows/plan-review/plan-review.md#Orchestrator checklist row check and bounded repair loop (`IPD-S407`)`; `.aw/system/workflows/plan-review/plan-review.md#Write the structured `Readiness` field (REQUIRED output of the review)` ("leave `- Readiness:` ABSENT entirely"); `.aw/system/workflows/plan-review/plan-review.md#Step 4: Finalize state and commit` (escalation with `- Finding: <ID>`). Design §4 S-07 postcondition: "The `- Readiness:` value is valid". |
| Basis | Verified |
| Proposed change | Put the S407/S408 loops in S-01 (deterministic detection, which the runner already does for coverage) plus a bounded repair inside R7 or R2 for orchestrators, and make the S-07 postcondition "valid `- Readiness:`, OR absent with a recorded exhausted-repair reason". Add the escalation to S-05 explicitly, with the postcondition that `check.review-finding-unescalated` passes. |

| Field | Content |
| --- | --- |
| ID | F-11 |
| Severity | minor |
| Category | depth-model |
| Location | §5 (`complex` row), OQ-6 |
| Issue | Two `complex` triggers are weak. (1) "The plan is an orchestrator": an orchestrator "carries no work of its own" (§0), so a full `complex` review with eight personas and a decomposition step (R5, R6) reviews a child-tracking table. R6 on an orchestrator asks whether a Set should become a Set. (2) "`Work-Kind:` is `security`": `security` is a valid Work-Kind, but the field is an author's choice, and the same author can avoid it. The floor exists because the author or reviewer may under-rate. |
| Evidence | Design §0 ("It tracks its child plans and carries no work of its own"); `.aw/records/backlog/README.md` (`- Work-Kind: bug \| feature \| chore \| security \| followup`); `aw ipd set --help` (`--work-kind {bug,feature,chore,security,followup}`). |
| Basis | Verified (field values); Inferred (the misclassification) |
| Proposed change | Give orchestrators their own path instead of a depth: R1, R2 (child table, coverage, ordering), and R7 across the Set, and never R5/R6. Keep `Work-Kind: security` as a trigger, but rely mainly on the OQ-5 path list (see the answer below). |

| Field | Content |
| --- | --- |
| ID | F-12 |
| Severity | minor |
| Category | correctness |
| Location | §1 problem 4, §7 "Migration" |
| Issue | The "166 `path:line` citations across 23 files" claim does not match the current tree, and the design does not say how it was counted. My count (regex `<path>.<ext>:<line>` over pending plans, all non-implemented, non-superseded specs, and open backlog items) found 189 in 13 files, with 0 in pending plans. 133 of the 189 are in two specs (`llbr2b` 85, `6kwd2e` 48), and specs are out of scope (§2: spec review is deferred). So "review step R1 corrects the existing 166 citations as each plan passes review" would correct almost none of them, because almost none are in plans. |
| Evidence | Local count, 2026-10-17 (method above). Design §2 "Out of scope: Spec review"; §7 "Migration: review step R1 corrects the existing 166 citations as each plan passes review". |
| Basis | Verified (my count); the design's method is unknown |
| Proposed change | State the counting method and recount at spec time. Rewrite the migration sentence to say that the debt is mostly in specs and will be addressed when spec review adopts R1. Or note that `aw ipd set --rewrite-citations` already exists and say whether it is relevant. |

| Field | Content |
| --- | --- |
| ID | F-13 |
| Severity | minor |
| Category | citations |
| Location | §7 table, row "Text with no named symbol"; §7 "Limit" |
| Issue | The quoted-text form "occurs exactly once in the file" fails on common cases. A string that is unique when written becomes ambiguous when a second copy is added (for example, a test that asserts the message), and the citation then becomes invalid with no edit to the cited code. The form also does not cover moved files, generated files (the command shims, managed `AGENTS.md` blocks), or a quoted string that contains a backtick. The Python-only symbol limit is reasonable, but the text-search fallback for other languages can match a comment or a string, so the fallback should resolve only, never prove. |
| Evidence | Design §7 table and "Limit". This repository generates `.opencode/commands/*.md`, `.claude/commands/*.md` and the `AGENTS.md` managed block from `agent_workflows/engine.py`. |
| Basis | Verified (generated files exist); Inferred (resolver behavior) |
| Proposed change | Adopt the syntax in the OQ-2 answer below. Define "unique" as unique within the cited file at the resolving commit, and report "now ambiguous" as a distinct resolver result from "not found". For a generated file, require citing the generator (`path::Symbol`) instead. For a moved file, let the resolver follow `git log --follow` once and report "moved to <path>" as a warning that R1 must correct. |

| Field | Content |
| --- | --- |
| ID | F-14 |
| Severity | minor |
| Category | cost |
| Location | §6 (prompt counts), §13 row 1 |
| Issue | The prompt counts in §6 add up as stated: `simple` 8 = S-02, S-03, R1, R2, R3, S-05, S-06, S-07. But given F-04, the expected per-plan count is 9 (`standard`) for almost every plan, plus re-review rounds (each adding 5 or 6 prompts), and R7 for Sets. That is about 9 to 20 prompts per plan, not 8 to 11. "The plan and the repository context load once" is not true of every host: on a host that re-sends the conversation each turn, input tokens grow with every prompt in the session. No measurement exists in the repository. |
| Evidence | Design §6 ("Number of agent prompts per review"); §13 ("All steps share one session (MD-6), so the plan and the repository context load once"). |
| Basis | Inferred |
| Proposed change | Merge steps that need no separate enforcement point. S-03 can be part of S-02's reply (a marker line `AW-DEPTH: <level>` validated like `AW-REVIEW`). R1 and R2 are mostly mechanical and can share one prompt with two evidence tables. S-05 and S-06 can share one prompt, because S-06 only adds the marker. That gives `simple` 5, `standard` 6, `complex` 8, without losing any postcondition. Add a validation item that measures tokens and wall time per depth on one real run before the thresholds are fixed. |

| Field | Content |
| --- | --- |
| ID | F-15 |
| Severity | minor |
| Category | gap |
| Location | §4 (the runner/free-form split), §10, §13 row 3 |
| Issue | The runner review has no human, so S-05 cannot ask. The free-form checklist omits two runner checks that are cheap to run by hand: the §4.1 wording-only check, and the floor. A free-form review would then routinely pick a lower depth than the runner would, and the two paths would diverge. That conflicts with MD-7 ("a free-form review and a runner review use the same instructions"). |
| Evidence | Design §10 checklist (S-01 runs lint and coverage only; S-03 "Record the depth"); §5 floor computed only by the runner. |
| Basis | Inferred |
| Proposed change | Expose both as CLI verbs (for example `aw ipd review-floor <id6>` and `aw ipd wording-check <id6> --since <commit>`). Have the runner call the same functions, and have the free-form checklist call the verbs in S-01 and after S-02. |

| Field | Content |
| --- | --- |
| ID | F-16 |
| Severity | wording |
| Category | wording |
| Location | §0 "Turn, session"; §4 S-01; §4 S-02 postcondition |
| Issue | (1) §0 says "Both runners can already resume a session", but does not say that Antigravity falls back to "most recent conversation" without an id (F-06). That difference is material. (2) S-01 says "Make the pre-review commit". Today that commit is conditional ("If all target plans are committed and unchanged, skip the snapshot"). As worded, the runner would always commit, possibly making empty commits. (3) The S-02 postcondition requires the change summary and issue list to be "recorded in the current review round", but the review record format (F-02) has no place for them. |
| Evidence | `.aw/system/workflows/plan-review/plan-review.md#Pre-review commit` ("If all target plans are committed and unchanged, skip the snapshot"); design §0, §4. |
| Basis | Verified |
| Proposed change | (1) State the Antigravity behavior. (2) Write "Make the pre-review commit when a target plan is untracked or modified (the existing conditional rule)". (3) Define a `### Proofreading` subsection in the round format, with `Changes` and `Issues` tables. |

| Field | Content |
| --- | --- |
| ID | F-17 |
| Severity | wording |
| Category | wording |
| Location | §4.1 last bullet; §8.1 rule 4; §6 R3 |
| Issue | (1) "Lint conformance. The plan must still conform after the step" does not say which lint phase. `aw ipd lint` has `author`, `review-finalize`, `pre-execution` and `pre-transition` phases with different rules, so a reader cannot implement this. (2) §8.1 rule 4 says the parsing "follows the pattern" of `classify_probe_reply`, which reads the FIRST non-empty line, while §8.1 rule 1 reads the LAST. "Follows the pattern" therefore means something narrower than a reader will assume. (3) R3 short form "trust-boundary input validation" is not defined anywhere in `plan-review.md` rubric section B. |
| Evidence | `agent_workflows/runner_shared.py::classify_probe_reply` ("First non-empty line must equal one sentinel"); `agent_workflows/ipd_lint.py::_review_stale_advisory` (`checkpoint not in ("author", "review-finalize")`, showing phase-dependent rules). |
| Basis | Verified |
| Proposed change | (1) Name the phase: "`aw ipd lint --phase author` reports no new error compared with before the step". Say "no NEW error" so a plan that was already non-conforming is not blocked by proofreading. (2) Say "uses the same exact-match, fail-closed approach as `classify_probe_reply`, applied to the last non-empty line". (3) List the three short-form checks as named rubric items in the R3 step file. |

## 6.4 Answers to open questions

**OQ-2 (exact syntax of the quoted-text citation).**
Answer: `` `path` "exact text" ``, meaning a backticked repository-relative path, one space, and the cited text in straight double quotes on the same line. Rules:
- The cited text must be 8 to 120 characters and must contain no double quote or newline.
- The resolver matches it after collapsing runs of whitespace, as `classify_probe_reply` already does for `QUOTE:` lines.
- For text that contains a double quote, use a backtick-fenced form instead: `` `path` `exact "text"` ``.
- Results are `ok`, `not-found`, `ambiguous (N matches)`, `file-missing` or `moved-to <path>`.

Examples:
- `` `agent_workflows/runner_shared.py` "record the review of" ``
- `` `agent_workflows/plan_readiness.py` `subject.startswith("plan-review:")` `` (backtick form, because the cited text contains a double quote)

Reason: the form is easy to parse, it reuses the whitespace normalization the runner already trusts, and its length bounds stop both trivial strings ("return") and pasted paragraphs. Basis: judgement. The whitespace normalization is Verified in `agent_workflows/runner_shared.py::classify_probe_reply`.

**OQ-3 (broken citation at `aw ipd begin`: refuse or warn).**
Answer: warn, and record the warning in the execution receipt. Refuse only for a citation inside an item's `Expected outcome` or in `Scope-Paths` whose result is `file-missing`.

Reason: `aw ipd begin` is the last gate before an agent spends a turn. Refusing on any broken citation would stop plans whose stale citation is in explanatory prose, which is the false-positive cost that spec Section 10.2 cites in refusing to gate `IPD-C801`. A missing file named in Scope-Paths or in an expected outcome means the plan cannot be executed as written, which is a real refusal case.

Basis: judgement, constrained by the Verified Section 10.2 ruling (F-01). This answer also requires the spec amendment in F-01.

**OQ-4 (split inheritance of `From-Backlog`, `From-Spec`, `Blocks-Release`).**
Answer: yes, all three, AND clear `- From-Backlog:` and `- From-Spec:` on the superseded original in the same commit.

Reason: without the clearing, the superseded original stays a carrier that is never `executed`. That makes the HANDOFF close route unreachable for the backlog item.

Basis: Verified against `agent_workflows/check_engine.py::_carrier_is_executed` and `agent_workflows/check_engine.py::_iter_plan_ipds` (F-07).

**OQ-5 (security-sensitive paths raise the floor).**
Answer: yes. Add a configured list `review_depth.security_paths` (globs) in `.aw/config/project.json`, with an empty default. Seed this repository's own list in its config, not in the package defaults. Candidates: the sandbox and egress code, `git_commit_helper`, `lane_containment`, the leak sanitizer, and anything handling tokens.

Reason: Work-Kind is author-chosen (F-11), while paths are measured. An empty default keeps other repositories unaffected until they opt in.

Basis: judgement. The module names are Verified to exist in `agent_workflows/`, but I did not audit which of them are security-relevant.

**OQ-6 (depth per Set or per plan).**
Answer: per plan, as proposed, but the orchestrator gets its own fixed step list (R1, R2 for the child table and coverage, R7) rather than `complex`.

Reason: an orchestrator carries no work, so R5 and R6 have nothing to evaluate. Its risk is cross-plan consistency, which is R7's job.

Basis: judgement, based on the design's own §0 definition of an orchestrator (F-11).

## 6.5 Challenges to fixed decisions

- **MD-5 (adopt the durable citation format, starting with plans).** The harm: an earlier measured contract already refuses part of what §7 builds on MD-5. Spec `20260802-1904` Section 10.2 refuses to promote `IPD-C801` to a gating severity and forbids retrofitting existing citations. The format itself does not conflict with Section 10.2; the enforcement and migration do. If MD-5 is read as including the error cutover and the R1 rewrites, it reverses Section 10.2 without engaging its evidence (a measured false-positive class of about 4 to 5% of flags that are pasted diagnostics). Evidence: `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md#10.2 Code-citation anchors (a citation MUST name something that survives to execution)`. I am not challenging the format, only reading MD-5 as including the gating, which the design's §7 does.
- **MD-2 (split without human approval).** The harm is limited to one case: a plan that was `approved` by a human before this review. Splitting it supersedes a human-approved artifact without a human act. The plans README and `AGENTS.md` both treat human approval as a step the runner never performs for the human. Evidence: `.aw/records/plans/README.md` ("Explicit human approval is still required before execution") and spec `25kzda` `#4.4 IPD review verification` (re-review "ends `reviewed` needing fresh human approval even under `--full-auto`"). A narrow carve-out (do not auto-split a plan that was `approved` when the review began) removes the harm without reversing MD-2 for the common case.

## 6.6 Alternative designs

1. **Deterministic pre-pass plus one agent turn, with the runner checking evidence tables.**
   - Description: the runner computes everything that needs no model before any prompt: lint, coverage, the floor, the citation resolver, and the E/V and Scope-Paths inventory. It injects the results into ONE review turn whose required output is the review record with per-step evidence tables (F-05). After the turn, the runner checks every table against the repository, and re-asks once in the same session for any missing or invalid table. Proofreading stays a separate first turn, because it edits the plan and the wording-only check needs a clean before/after.
   - Improves: 2 to 3 prompts per plan instead of 8 to 20. No new session-continuity risk. Reuses today's launch path, so no change to the two-callers pin. Enforcement equals or exceeds the step design, because the evidence tables, not the prompt boundaries, are what the runner checks.
   - Costs: a large single turn is more prone to the instruction drift that `plan-review-long` was meant to reduce. The design's per-step prompts are a direct response to that. The checks must be precise enough that a table cannot be filled by rote.
2. **The step design, with steps merged where no new check is gained (see F-14).**
   - Description: keep MD-6 and the step sequence, but use six prompt slots: S-02 + S-03 (marker `AW-DEPTH:`), R1 + R2, R3, R4 + R5 (standard and complex), R6 + R7 (complex and Sets), and S-05 + S-06 + S-07 with the marker. Run the re-review as one prompt over the diff (F-08).
   - Improves: about 40% fewer prompts, and every postcondition in §4 is still checkable.
   - Costs: larger individual prompts, and the step files must be written so that two steps can share a reply without their sections being confused.

## 6.7 Limits of this review

- I did not read the full `runner_shared.py` (about 48,000 lines) or the review-dispatch code paths in `oc_runipd.py` and `agy_runipd.py` end to end. Findings about session behavior (F-06) are based on the named symbols, the launch argv code, and `aw host capabilities`, not on a trace of a real multi-turn review.
- I did not run either host. Nothing in this review was observed in a live session.
- The floor measurement (F-04) used my own parser of `- Scope-Paths:` (comma and semicolon separated, backticks stripped) and E-checkbox lines, not the runner's future implementation. Plans with no `- Scope-Paths:` (281 of 1,544) count as single-directory, which biases the result toward `simple`, so the real `standard`-or-above share is at least what I report.
- The citation count (F-12) used one regex. Citations in other shapes (for example, without a file extension) are not counted, and I do not know what method produced the design's 166.
- I did not read `.aw/system/workflows/release-review/fix-decision-policy.md`, the `plan-review-long` step files other than its orchestrator, `ARCHITECTURE.md`, or the installer code that Order 07 would change. I did not evaluate the work breakdown's ordering beyond noting F-01's effect on the Spec row.
- I evaluated the proofreading instructions (`wcisgc`) only where the design adapts them (§10). I did not apply them line by line to the design. The wording findings (F-16, F-17) are the defects I judged could change implementation.
