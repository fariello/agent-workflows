# IPD: Split plan-review into step files with a section map, round layout, and five-level recommendation strength

- Date: 2026-10-24
- Kind: child
- Concern: Spec `k3yx72` (approved) replaces the single-turn plan review with a sequence of review checks that the runner sends as separate prompts (MD-7). The runner can only send checks that exist as separate files. Today `/plan-review` is one 48,108-byte file, `.aw/system/workflows/plan-review/plan-review.md`, so every review loads all of it whatever the plan's size, and no single check can be sent alone. Spec Section 4.3 maps every part of that file to exactly one step file; nothing is written yet. The spec also requires a five-level recommendation strength (MD-9) in `/plan-review` and `/askme`, and a review-record round layout with per-check subsections (Section 7.1), neither of which exists.
- Scope: Create the step files of spec `k3yx72` Section 4.3 under `.aw/system/workflows/plan-review/steps/`, turn `plan-review.md` into a checklist that runs those step files in order (so an interactive `/plan-review` still performs the whole review), keep every existing rule, add the old-to-new section map and the per-tier instruction byte totals to the `plan-review` README, amend `.aw/records/reviews/README.md` with the round layout of Section 7.1, and change `/askme` to the five-level recommendation strength (MD-9, Section 17.4). EXCLUDES all runner code (Orders 02, 04, 05), the citation resolver (Order 03, Stage 2), retiring `/plan-review-long` (Order 07, Stage 2: until then its parity references stay valid because no rule is deleted), and any change to `review_findings` parsing. BEHAVIOR CHANGE TO NOTE AT APPROVAL: from this plan's merge, every `/plan-review`, including the runner's default single-turn review (`runner_shared.build_review_prompt` sends `/plan-review <path>`), runs the tiered checklist, so a plan the agent rates `simple` gets checks P, T, Q, S5 to S7 instead of the full rubric. Spec `k3yx72` MD-7 and Section 4.3 require this, and it lands before the Order 09 pilot; the pre-change file stays readable at the baseline commit E-01 records.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review/README.md, .aw/system/workflows/plan-review/steps/*.md, .aw/system/workflows/askme/askme.md, .aw/records/reviews/README.md, agent_workflows/review_findings.py, agent_workflows/plan_readiness.py, .aw/system/workflows/spec-review/spec-review.md, .aw/system/workflows/spec-review/README.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, .aw/system/workflows/plan-review-long/plan-review-long.md, tests/test_plan_review_feasibility_rule.py, tests/test_v_item_demonstration_reachability.py, tests/test_v_item_evidence_durability.py, tests/test_plan_review_step_files.py, CHANGELOG.md
- Item-Dependencies: executed:gv3smb
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- From-Spec: k3yx72
- Set: revsteps
- Order: 1
- Highest E allocated: 18
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 3bwrfx

## Workflow history
- 2026-10-26 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 3bwrfx verified (set revsteps, attempt 1).
- 2026-10-25 approved (aw set): status set to approved
- 2026-10-25 re-scope (opencode/its_direct/pt3-claude-opus-5.5-1m-us): E-09 names the `review progress` history-line form (uiyoax review round 1, PR-004); no verdict change.
- 2026-10-25 re-scope (opencode/its_direct/pt3-claude-opus-5.5-1m-us): E-04 names the `1.` to `5.` answer-line form that `gv3smb` E-04 parses (gv3smb review round 1, PR-008); no verdict change.
- 2026-10-25 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED
- 2026-10-25 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED; review record .aw/records/reviews/20261024-revsteps-01-3bwrfx-split-plan-review-into-step-files-with-a-section-map-round-l.review.md
- 2026-10-25 to-review (aw set): authored review-ready from spec k3yx72 Stage 1 (MD-20)

- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every review check of spec `k3yx72` Section 4.2 a separate step file that the runner can send alone, without losing any rule of today's `plan-review.md`, and make the loss check reviewable through a section map.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: shared step files

- [x] E-01 Before any edit, record the baseline in the plan's working notes for E-12 and V-18: the commit hash of the last pre-change `plan-review.md` (`git log -1 --format=%H -- .aw/system/workflows/plan-review/plan-review.md`) and the `aw check` summary line. Then create `.aw/system/workflows/plan-review/steps/_kernel.md` from the `plan-review.md` preamble (the planning-only rule, sibling policy pointers, and the from-memory fallback rules), the `## Memory kernel` section, and the instruction part of `## Step 0: Scope and project contract` that tells the agent to apply the `AGENTS.md` rules bearing on the plan (subsection `### 0.2 Discover controlling instructions`). Move, do not paraphrase: rule text is copied verbatim except where a sentence names a step by its old number, which is rewritten to name the step file. Drop the "SERIAL BY DESIGN" parity paragraph from the kernel and keep it in `plan-review.md` itself (E-11), because it describes the interactive checklist, not a check.
  - Depends on: none
  - Expected outcome: the baseline hash and `aw check` summary are recorded; `_kernel.md` exists and holds the memory kernel's nine numbered rules verbatim.
  - Execution state: performed

- [x] E-02 Create `steps/_findings.md` from `### 2.1 Apply all required views`, `### 2.2 Record findings`, `### 2.3 Remediation Risk and Fix Bar`, `### 2.4 Revise the plan in place`, and `## Severity and scope`, verbatim. Add, from spec `k3yx72` Section 7.1, the rule that findings are rows in the current round's single `### Findings` table (columns exactly as `review_findings.FINDING_COLUMNS`) and that per-check notes go in a `### Step <check>` subsection beginning with one `- Checked: <what was examined>` line (Section 6). Add the closing sentence of MD-8: "Make sure that every edit you made in this step conforms to the proofreading instructions." Add the MD-9 rule that every recommendation states one of `very weak`, `weak`, `medium`, `strong`, `very strong`.
  - Depends on: none
  - Expected outcome: `_findings.md` exists; it carries the Fix Bar text and the Severity and scope text verbatim.
  - Execution state: performed

### Task group 2: check step files

- [x] E-03 Create `steps/p-proofread.md` (check P): instruct the agent to apply prompt `wcisgc` (`.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md`) to the plan, by reference to that path rather than by copy; to record material changes and unresolved ambiguities in the current round's `### Proofreading` subsection as the two tables of spec Section 7.1 (Changes: location, old text summary, new text summary, reason; Issues: id, location, ambiguity, information needed, recommended answer, recommendation strength); to add open questions only through that Issues table (Section 6.1); to write citations in the forms of Section 11.1; and to change no front-matter value, H2 heading, E/V id or checkbox, `Execution state`, E/V field name, or existing open question's `Status:`/`Blocking:` (the refused list of Section 6.1), stating that the runner refuses such an edit. Because the `wcisgc` prompt lives under `.aw/records/`, which the installer does not ship to a target repository, state in the step file that when that path is absent the agent applies the seven numbered headings of `wcisgc` as summarized in one short paragraph inside `p-proofread.md` (copy the seven heading titles and one sentence each).
  - Depends on: none
  - Expected outcome: `p-proofread.md` exists, names `wcisgc` by path, and carries the fallback summary.
  - Execution state: performed

- [x] E-04 Create `steps/t-tier.md` (check T): the five tier questions of spec `k3yx72` Section 5.2 verbatim, the instruction to answer each on one line in the round's `### Step T` subsection, each line starting `1.` to `5.` with the question's number (the form `gv3smb` `review_tier.parse_tier_answers` reads), the non-binding guidance paragraph of Section 5.2, the statement that the runner supplies the pre-pass facts (Section 4.1 item 4) in the first prompt when run by a runner and that an interactive reviewer collects them itself (`- Scope-Paths:`, E-item and task-group counts, whether a `.spec.md` is named), and the required last line `AW-TIER: <simple|standard|complex>`. Also create `steps/q-quick-risk.md` (check Q): answer "what could this change break, and what existing behavior does something else depend on?", record findings per `_findings.md`.
  - Depends on: none
  - Expected outcome: both files exist; `t-tier.md` contains all five questions and the marker line format.
  - Execution state: performed

- [x] E-05 Create `steps/r1-references.md` (check `k3yx72` R1) and `steps/r2-executability.md` (check `k3yx72` R2). R1: until the citation resolver exists (Order 03), the agent checks every citation in the plan itself, locating each by symbol, heading, or quoted text (spec Section 4.2 row R1), and records `not-found`/`ambiguous`/`moved` results as findings; plus, verbatim, the numbered items 1 to 6 of `## Step 1: Evidence and pre-review snapshot` (read the plan, list and open the evidence, the citation-disposition rule including its "Costlier error" and "Git ref asymmetry" sub-bullets, record missing evidence, do not infer) and the sentence after them ("If missing evidence prevents reliable review, file a finding or open question."). Spec Section 4.3 maps no row to these items, so without this move the rewrite would drop them. R2: the E/V bijection, `- Scope-Paths:`, `- Item-Dependencies:`, concrete evidence in every `V-*`, and no hardcoded count of a mutable record tree; plus, verbatim, `### Structural preflight (before semantic review)`'s orchestrator subsections ``#### Orchestrator checklist row check and bounded repair loop (`IPD-S407`)`` and ``#### Orchestrator review readiness (`IPD-S408`)``, and the structure, evidence and count bullets of `### G. Plan executability`. Move the bullet beginning `- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**` byte-for-byte, because `tests/test_v_item_evidence_durability.py` compares it with `plan-review-long/review-rubric.md`.
  - Depends on: none
  - Expected outcome: both files exist; R1 carries Step 1 items 1 to 6 verbatim; R2 carries the `IPD-S407` and `IPD-S408` subsections verbatim.
  - Execution state: performed

- [x] E-06 Create `steps/r3-security.md` (check `k3yx72` R3; full form: `### B. Security and privacy` verbatim; short form: its first three bullets, labelled as such for the `simple` tier of spec Section 5.1) and `steps/r4-engineering.md` (check `k3yx72` R4: `### A. Correctness and data integrity`, `### C. Architecture and operability`, `### D. Anti-regression and domain invariants`, `### E. Testing and verification`, `### F. KISS, principles, and UX` verbatim, plus the right-sizing and overloaded-item bullets of `### G. Plan executability` not moved by E-05, and the check that `## Spec / documentation sync` is truthful). Every bullet of rubric G must land in exactly one of R2 or R4; the section map (E-12) lists each.
  - Depends on: E-05
  - Expected outcome: both files exist; every rubric G bullet appears exactly once across `r2-executability.md` and `r4-engineering.md`.
  - Execution state: performed

- [x] E-07 Create `steps/r5-personas.md` (check `k3yx72` R5: the eight viewpoints, by reference to `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas`, not copied), `steps/r6-decomposition.md` (check `k3yx72` R6: decide whether the plan should become a plan Set; a recommended split records a proposed breakdown in the round and is a finding that forces `no-go`; until the split step exists (Order 06, Stage 2) the split is left for a human, as spec Section 10 item 1 already does for approved plans), and `steps/r7-cross-plan.md` (check `k3yx72` R7: consistency with Set siblings and the orchestrator; for an orchestrator, across the whole Set).
  - Depends on: none
  - Expected outcome: three files exist; `r5-personas.md` references the personas heading rather than copying it.
  - Execution state: performed

- [x] E-08 Create `steps/s5-questions.md` from `## Step 3: Resolve open questions` verbatim (3.1 including both `####` subsections, 3.2, 3.3), plus `### The escalation RETURN PATH` and the finding escalation rule (an unfixed finding at or above the configured block level becomes a `Blocking: yes` question with `- Finding: <ID>`), plus the MD-11 rule (no `Blocking: yes` to `Blocking: no` without a recorded reason) and the MD-9 strength rule for every recommended answer. Keep the heading `#### Resolving HOW questions: demonstrate, do not describe` and its five anchor phrases exactly, because `tests/test_plan_review_feasibility_rule.py` and `spec-review.md` cite them. State that 3.2 (ask interactively) applies only to an interactive `/plan-review` run, and that a runner review records questions instead.
  - Depends on: none
  - Expected outcome: `s5-questions.md` exists and contains the five `ANCHOR_PHRASES` of `tests/test_plan_review_feasibility_rule.py`.
  - Execution state: performed

- [x] E-09 Create `steps/s6-rereview.md`: decide whether the review's own edits need another pass; end the reply with exactly one last line `AW-REVIEW: AGAIN` or `AW-REVIEW: DONE` (spec Section 8.1); state that an interactive run decides the same thing and loops itself at most twice (Section 8.3). Do NOT write any verdict output in this step (MD-15), and record any progress note in the plan's history only as `- <date> review progress (<agent/model>): <note>`, never with a `/plan-review` label, because `plan_readiness.is_review_history_entry` treats a `/plan-review`-labelled line as a review record and `newest_verdict` would then read it as the newest verdict (`uiyoax` E-03).
  - Depends on: none
  - Expected outcome: `s6-rereview.md` exists with both marker lines spelled exactly.
  - Execution state: performed

- [x] E-10 Create `steps/s7-finalize.md` from `## Step 4: Finalize state and commit` verbatim (including ``### Write the structured `Readiness` field (REQUIRED output of the review)`` and `### Hardened-result commit`), `## Verdict and readiness` and ``### A `NO-GO` is RE-EVALUABLE`` verbatim, and `## Required final report` verbatim. Add: the verdict outputs (`- Readiness:`, the status move, the one verdict-bearing history entry) are written in this step only and exactly once per review (MD-15, Section 7.2); the final commit subject starts with `plan-review:`; `- Review-Depth: <tier>` is written here (Section 7.2; the field is registered by Order 02 `gv3smb`, which is why this plan carries `- Item-Dependencies: executed:gv3smb`: until it lands, a plan carrying the field fails `aw ipd lint` with `IPD-M103` unknown field); and in a runner review the final report is the review record, not chat text (Section 4.3 row "Required final report"). Keep the four verdict tokens spelled exactly as `plan_readiness.VERDICTS`.
  - Depends on: none
  - Expected outcome: `s7-finalize.md` exists; it contains the four verdict tokens and the Readiness subsection verbatim.
  - Execution state: performed

### Task group 3: checklist, map, and pointers

- [x] E-11 Rewrite `.aw/system/workflows/plan-review/plan-review.md` as the checklist (MD-7): keep the H1 and its first paragraph, keep verbatim the parts spec Section 4.3 assigns to the runner pre-pass, because an interactive run must still do them itself: `### 0.1 Build the review-scope ledger` and `### 0.3 Discover the plan contract and implementation context` (Section 4.3 row "Step 0", deterministic parts), the pre-review commit instruction (`### Pre-review commit`), and the whole of `### Structural preflight (before semantic review)` other than the two orchestrator `####` subsections E-05 moves, including the `aw ipd lint --phase review-finalize` re-run at the finalize checkpoint and its exit-code rules; then list, in order, "read and apply `steps/<file>`" for `_kernel.md`, `p-proofread.md`, `t-tier.md` (skipped for an orchestrator, which T does not rate: spec `k3yx72` Section 5.1), then the tier's checks as in spec Section 5.1 (`simple`: `q-quick-risk.md` and the short form of `r3-security.md` when tier question 2 is yes; `standard`: `r1` to `r4`; `complex`: `r1` to `r7`; orchestrator: `r1`, `r2`, `r7`), each with `_findings.md`, then `s5-questions.md`, `s6-rereview.md`, `s7-finalize.md`. Keep the "SERIAL BY DESIGN" parity paragraph, rewritten to say the checklist is serial. The file path and the `plan-review` manifest row in `.aw/system/workflows/index.md` do not change, so the command shims generated by `engine.generate_shim_members` need no change. The baseline commit E-01 recorded is written into the README by E-12, because Order 09 (`kk62qt`) compares the new review against "the current `/plan-review`" (spec `k3yx72` Section 13.3 V2) and E-12's map and V-12 count need the same fixed baseline.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09, E-10
  - Expected outcome: `plan-review.md` is a checklist that names every step file; an interactive `/plan-review` still runs every check, and still runs the scope ledger, pre-review commit, both lint phases, and orchestrator coverage.
  - Execution state: performed

- [x] E-12 Add to `.aw/system/workflows/plan-review/README.md` (0) the pre-change baseline commit E-01 recorded, named as the `/plan-review` that Order 09's pilot uses for the current-review method (read it with `git show <hash>:.aw/system/workflows/plan-review/plan-review.md`); (a) the old-to-new section map: one row per heading of the pre-change `plan-review.md` (every H2, H3 and H4, including the preamble and the fenced report template) naming the step file it moved to, with each rubric G bullet listed separately by its first words; and (b) the instruction bytes sent per tier: the sum of `wc -c` over the files each tier's checklist names (`simple`, `standard`, `complex`, orchestrator), next to the 48,108 bytes of the pre-change file. Measure the bytes with `wc -c` after E-11 and paste them; do not estimate.
  - Depends on: E-11
  - Expected outcome: the README carries both tables with measured numbers.
  - Execution state: performed

- [x] E-13 Update the readers that point into moved sections. `.aw/system/workflows/spec-review/spec-review.md` and `.aw/system/workflows/spec-review/README.md`: rewrite each `plan-review.md` reference to name the step file and heading that now holds the cited text (for example `../plan-review/steps/s5-questions.md`, "Resolving HOW questions: demonstrate, do not describe"), and replace every stale line-number citation of the form `plan-review.md:<line>` or `plan-review.md:<from>-<to>` (found with `rg -n "plan-review\.md:[0-9]" .aw/system/workflows`) with a step-file and heading citation. `.aw/system/workflows/plan-review-long/plan-review-long.md` and `03-resolve-and-finalize.md`: change the parity references to name the step files. Also update the two code comments that cite `plan-review.md` by stale line number (the two comments in `agent_workflows/review_findings.py` containing "because the shipped workflow table has it" and "says the history prose", each citing `plan-review.md` with a line-number suffix) and the comment in `agent_workflows/plan_readiness.py` that names `plan-review.md`, "Verdict and readiness", to name `steps/s7-finalize.md` and the heading; comments only, no code change. Do not change the meaning of any of these files.
  - Depends on: E-11
  - Expected outcome: `rg -n "plan-review\.md:[0-9]" .aw/system/workflows agent_workflows` prints nothing.
  - Execution state: performed

- [x] E-14 Amend `.aw/records/reviews/README.md` sections `## Rounds` and `## Sections` with the spec `k3yx72` Section 7.1 layout: one `## Round <n>` per review invocation; re-review passes are `### Pass <k>` subsections, not new rounds; `### Proofreading` (two tables), `### Step <check>` (notes and evidence, no finding rows, first line `- Checked:`), `### Findings` (the round's single table, unchanged columns), `### Decisions` (unchanged). State that `review_findings.parse_review_text` reads finding rows only under a heading starting with `Findings`, so the new subsections do not change gating.
  - Depends on: none
  - Expected outcome: the README describes the five subsections and says gating is unchanged.
  - Execution state: performed

- [x] E-15 Change `.aw/system/workflows/askme/askme.md` item 5 "**Recommendation:**" from the three labels `(Strong Recommend)`, `(Recommend)`, `(Weak Recommend)` to the five-level scale of MD-9: state the strength as one of `very weak`, `weak`, `medium`, `strong`, `very strong`, on the favored option. Keep the rest of item 5.
  - Depends on: none
  - Expected outcome: `askme.md` names the five levels and no longer names the three old labels.
  - Execution state: performed

### Task group 4: tests and commit

- [x] E-16 Update the three tests that read moved text so they read the new location and assert the same rules: `tests/test_plan_review_feasibility_rule.py` (`PLAN_REVIEW_FILE` section 3.1 now in `steps/s5-questions.md`; rubric G anchors `drift_exit_code`, `check_engine.rule_spec`, `unsatisfiable` now in `steps/r2-executability.md` or `steps/r4-engineering.md`, whichever E-05/E-06 put them in), `tests/test_v_item_demonstration_reachability.py` and `tests/test_v_item_evidence_durability.py` (rubric G slice now from the step file; the byte-identical bullet comparison with `review-rubric.md` kept). The spec-review reference test must accept the new step-file path. Do not weaken any assertion; only the file and heading each test reads may change.
  - Depends on: E-11, E-13
  - Expected outcome: the three test modules pass against the new files with the same anchor phrases asserted.
  - Execution state: performed

- [x] E-17 Add `tests/test_plan_review_step_files.py`, marked `core`, which installs into a scratch repository with `aw install -y <tmp>` (the `run_cli("install", "-y", ...)` pattern of `tests/test_installed_text_current.py`) and asserts on the INSTALLED tree: (a) every step file named in the installed `plan-review.md` exists under `plan-review/steps/` (parse the `steps/<name>.md` references from the checklist text and check each path); (b) `steps/t-tier.md` ends its instructions with the `AW-TIER:` marker format and `steps/s6-rereview.md` names both `AW-REVIEW: AGAIN` and `AW-REVIEW: DONE`; (c) `steps/s7-finalize.md` contains each token of `plan_readiness.VERDICTS`; (d) the installed `askme/askme.md` contains `very weak` and `very strong`. These are outcome checks on what a target repository receives, not checks on how the files are written. Do the install once per module (a module-scoped fixture), so the core tier pays one install (about 3.4 s measured at review) rather than four.
  - Depends on: E-11, E-15
  - Expected outcome: a new core test module that passes.
  - Execution state: performed

- [x] E-18 Add one `CHANGELOG.md` entry: `/plan-review` is now a checklist of step files, each review check can be run on its own, and `/askme` recommendations use five strength levels. No em or en dashes. Then run `python3 -m pytest -o addopts="" -n auto tests/test_plan_review_feasibility_rule.py tests/test_v_item_demonstration_reachability.py tests/test_v_item_evidence_durability.py tests/test_plan_review_step_files.py tests/test_spec_review_attestation.py tests/test_run_scratch_path_guard.py`, the bare core gate `python3 -m pytest`, and `aw check`, and commit through `aw commit 3bwrfx -- <each changed path>`. Never push.
  - Depends on: E-12, E-14, E-16, E-17
  - Expected outcome: both pytest runs report no failures; `aw check` reports no error and no warning this plan introduced; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `.aw/system/` in this repository IS the source of truth for shipped workflows: `pyproject.toml` force-includes `.aw/system` into the wheel as `agent_workflows/_data/.aw/system`, and `engine.collect_source_members` ships every file under the bundle root, so new files under `plan-review/steps/` ship with no installer change.
- The workflows index `.aw/system/workflows/index.md` is hand-maintained; command shims are generated from its manifest rows by `engine.generate_shim_members`. Keeping the `plan-review` row's body path unchanged keeps the shims unchanged.
- `tests/test_spec_review_attestation.py::test_no_generated_projection_to_compile_for_this_package` requires that `plan-review/_generated` does not exist: do not create it.
- `tests/test_run_scratch_path_guard.py::test_sweep_detects_poisoned_shipped_body` requires `plan-review/plan-review.md` to keep existing at its path.
- Tests slice workflow text with `tests/support.py::section`, which raises when a heading is missing; moving a heading breaks a test loudly rather than silently.
- Cite code by symbol or quoted text; line numbers are hints (spec `k3yx72` MD-5, spec `20260802-1904` Section 10.2).
- Tests check observable outcomes (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); E-17 asserts on an installed tree.

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wc -c .aw/system/workflows/plan-review/plan-review.md`: 48108; 741 lines | Matches spec `k3yx72` Section 4.3 ("741 lines, 48 KB"). |
| F-02 | `rg -n "Strong Recommend" .aw/system/workflows agent_workflows tests` matches only `askme/askme.md` | The three-level labels are pinned by no test, so E-15 breaks nothing. |
| F-03 | `tests/test_v_item_evidence_durability.py` compares the rubric G "Live-artifact success criteria" bullet byte-for-byte with `plan-review-long/review-rubric.md` | E-05 must move that bullet unchanged; `/plan-review-long` stays until Order 07. |
| F-04 | `spec-review/spec-review.md` cites `plan-review.md` by section name and by stale line-number suffixes (the "Structural preflight" and "Readiness" citations) | E-13 rewrites these to step-file and heading citations. |
| F-05 | `agent_workflows/review_findings.py::parse_review_text` reads finding rows only under an H3 starting `Findings` | New `### Step`/`### Pass`/`### Proofreading` subsections do not change gating (E-14). |
| F-06 | The `wcisgc` prompt is under `.aw/records/prompts/reusable/`; `engine.collect_source_members` ships only `.aw/system` | A target repository has no `wcisgc` file; E-03 adds a fallback summary inside `p-proofread.md`. |

## Proposed changes (ordered, validatable)

1. E-01, E-02: the shared kernel and findings files.
2. E-03 to E-10: one file per check of spec Section 4.2.
3. E-11: `plan-review.md` becomes the checklist; E-12 the section map and byte totals; E-13 the readers; E-14 the reviews README; E-15 `/askme`.
4. E-16 to E-18: tests, changelog, gates, commit.

## Deferred / out of scope (with reason)

- Runner pre-pass, multi-prompt sending, postconditions: Orders 02 and 04 of this Set.
  - Carrier: uiyoax
- The citation resolver: Order 03, Stage 2 (spec MD-20). `kk62qt` E-09 files the Stage 2 backlog item when the pilot gate says build.
  - Carrier: kk62qt
- Retiring `/plan-review-long`: Order 07, Stage 2. Until then E-13 keeps its parity references working.
  - Carrier: kk62qt
- Pilot baseline: after this plan, a `--review-mode single` review runs the new checklist, so Order 09 (`kk62qt`) E-04 must put the pre-change `plan-review.md` (the baseline commit E-12 records) into each "current `/plan-review`" cell's scratch repository, or the pilot compares the new review with itself (spec `k3yx72` Section 13.3 V2). This plan records the baseline; the pilot driver is `kk62qt`'s.
  - Carrier: kk62qt

## Scope check

- Over-scope: none. Every declared path is touched by a named E-item.
- Under-scope: none. Every row of spec Section 4.3 has an E-item (E-01 to E-11); the parts Section 4.3 maps to no step file (Step 0.1 and 0.3, the Step 1 evidence items, the `review-finalize` re-lint) are kept in the checklist (E-11) or moved to R1 (E-05); Sections 7.1 and 17.3 (E-14) and 17.4 (E-15) are covered.

## Required tests / validation

- Nothing lost: E-12's map lists every pre-change heading and rubric G bullet; V-12 checks the count of mapped headings against the pre-change file.
- Existing rule tests still pass against the new locations (E-16).
- The installed tree has every step file and the markers (E-17).
- Commands: the named pytest run, the bare core gate, and `aw check` of E-18, with summaries pasted.

## Spec / documentation sync

`.aw/records/reviews/README.md` gains the round layout (spec `k3yx72` Section 17.3); `/askme` changes per Section 17.4. No `.spec.md` is edited: spec `k3yx72` already describes this layout, and no other spec describes the internal structure of `/plan-review`. `CHANGELOG.md` gains one entry.

## Open questions

### OQ-01: Keep the proofreading instructions only in `.aw/records/`, or copy them into the shipped step file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Reference by path with a short fallback summary (E-03). The prompt is a maintained record with its own lifecycle; a full copy would drift. A target repository without the record still gets the seven headings. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the E-01 baseline hash and `aw check` summary line as recorded, `wc -c .aw/system/workflows/plan-review/steps/_kernel.md`, and the nine numbered memory-kernel lines as they appear in the file, plus `git show <E-01 baseline hash>:.aw/system/workflows/plan-review/plan-review.md | sed -n '/^## Memory kernel/,/^---/p'` showing the same nine lines.
  - Observed evidence:
    Baseline commit hash of pre-change `plan-review.md`:
    `bb094ca8ab37a04dec9f7aa431551d4c70764b86`

    Baseline `aw check` summary:
    `AW check all 18137 ms; ✗ FINDINGS 63 finding(s) detected across 3011 all (errors 12, warnings 1, info 50)`

    Byte count:
    `1854 .aw/system/workflows/plan-review/steps/_kernel.md`

    Nine numbered memory kernel lines in `steps/_kernel.md`:
    ```
    1. Review plans only.
    2. Verify claims from repository evidence.
    3. Fix by default. Severity never decides.
    4. Resolve open questions interactively when possible.
    5. Never guess a human decision.
    6. Preserve valid plan content and required structure.
    7. Make at most two local commits. Never push.
    8. The reviewed/not-reviewed enumeration is the literal final output.
    9. A gate or interactive question MUST NOT assert or imply the verdict it precedes (readiness, approval, GO); it states what was found and asks what to do. The verdict is formed only from the reviewed work's evidence.
    ```

    `git show bb094ca8ab37a04dec9f7aa431551d4c70764b86:.aw/system/workflows/plan-review/plan-review.md | sed -n '/^## Memory kernel/,/^---/p'`:
    ```
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
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `rg -n "^### |Make sure that every edit|very weak" .aw/system/workflows/plan-review/steps/_findings.md` showing the moved 2.1 to 2.4 headings, the MD-8 sentence, and the five strength levels.
  - Observed evidence:
    ```
    3:### 2.1 Apply all required views
    12:### 2.2 Record findings
    42:Every recommendation the review writes (in an open question, a finding's resolution, or the proofreading issues table) states its strength: `very weak`, `weak`, `medium`, `strong`, or `very strong`.
    44:### 2.3 Remediation Risk and Fix Bar
    67:### 2.4 Revise the plan in place
    96:Make sure that every edit you made in this step conforms to the proofreading instructions.
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `rg -n "wcisgc|### Proofreading" .aw/system/workflows/plan-review/steps/p-proofread.md` and the fallback paragraph listing the seven heading titles.
  - Observed evidence:
    `rg -n "wcisgc|### Proofreading" .aw/system/workflows/plan-review/steps/p-proofread.md`:
    ```
    3:Apply the technical artifact proofreading instructions in prompt `wcisgc` (`.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md`) to the plan, by reference to that path rather than by copy.
    5:When that path is absent (such as in an installed target repository where `.aw/records/` is not shipped), apply the seven numbered headings of `wcisgc` as summarized here:
    41:In the typed review record (`.aw/records/reviews/<...>.review.md`), record material changes and unresolved ambiguities in the current round's `### Proofreading` subsection as two tables:
    ```

    Fallback paragraph listing the seven heading titles:
    ```
    When that path is absent (such as in an installed target repository where `.aw/records/` is not shipped), apply the seven numbered headings of `wcisgc` as summarized here:
    1. Surface Ambiguities and Contradictions: identify any requirement, step, or expectation whose wording supports conflicting interpretations.
    2. Precision in Scope and Invariants: verify that scope fences and negative boundaries unambiguously exclude unintended mutations.
    3. Structural Alignment and Section Integrity: confirm every required section, front-matter field, and checklist item follows the structural grammar without drift.
    4. Execution Safety and Reversibility: ensure destructive or mutating operations include containment, rollback paths, or safety gates.
    5. Testability and Observable Evidence: require each verification step to define concrete, observable evidence commands and deterministic outputs rather than assertions on code structure.
    6. Terminology Consistency: confirm names, identifiers, paths, and status verbs are used identically across all sections.
    7. Brevity and High-Density Clarity: eliminate non-operational narration, passive hedging, and redundant preamble text while preserving every constraint.
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `rg -n "AW-TIER|^[1-5]\." .aw/system/workflows/plan-review/steps/t-tier.md` showing five numbered questions and the marker format, and `wc -c` of `q-quick-risk.md`.
  - Observed evidence:
    `rg -n "AW-TIER|^[1-5]\." .aw/system/workflows/plan-review/steps/t-tier.md`:
    ```
    5:1. Does the plan change a spec, a public interface (CLI option, output format, file format, configuration key), or another contract that other code or other plans rely on?
    6:2. Does the plan touch code that guards private data, commits, worktree isolation, merges to main, or the sandbox? Examples in this repository: `agent_workflows/leak_sanitizer.py`, `agent_workflows/local_leaks.py`, `agent_workflows/git_commit_helper.py`, `agent_workflows/commit_lock.py`, `agent_workflows/lane_containment.py`, `agent_workflows/egress_policy.py`, `agent_workflows/host_sandbox_profile.py`.
    7:3. Is the plan large or cross-cutting: many execution items, several task groups, or changes in several unrelated modules?
    8:4. Does the plan list the files it changes (`- Scope-Paths:`)? If not, what does the review know about its reach?
    9:5. Could a mistake in this change lose data, break existing behavior that other code depends on, or be hard to undo?
    17:AW-TIER: <simple|standard|complex>
    ```

    `wc -c .aw/system/workflows/plan-review/steps/q-quick-risk.md`:
    `369 .aw/system/workflows/plan-review/steps/q-quick-risk.md`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `rg -n "IPD-S407|IPD-S408|Live-artifact success criteria" .aw/system/workflows/plan-review/steps/r2-executability.md` and `rg -n "until the citation resolver|symbol, heading, or quoted text|Costlier error|Git ref asymmetry|If missing evidence prevents reliable review" .aw/system/workflows/plan-review/steps/r1-references.md`.
  - Observed evidence:
    `rg -n "IPD-S407|IPD-S408|Live-artifact success criteria" .aw/system/workflows/plan-review/steps/r2-executability.md`:
    ```
    12:#### Orchestrator checklist row check and bounded repair loop (`IPD-S407`)
    16:`m7gvuz`), the linter validates typed child-tracking row conformance (`IPD-S407`).
    18:If `IPD-S407` violations are reported:
    38:#### Orchestrator review readiness (`IPD-S408`)
    65:- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. Criteria counting **stable code facts** (schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations. In contrast, a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts; neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer). A V-item must instead demand the behaviour pinned plus the mechanism that pins it, and must require re-derivation at execution time. (Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)
    ```

    `rg -n "until the citation resolver|symbol, heading, or quoted text|Costlier error|Git ref asymmetry|If missing evidence prevents reliable review" .aw/system/workflows/plan-review/steps/r1-references.md`:
    ```
    3:Check every citation in the plan. Until the citation resolver exists (Order 03, Stage 2), the agent checks every citation in the plan itself, locating each by symbol, heading, or quoted text (spec Section 4.2 row R1), and records `not-found`/`ambiguous`/`moved` results as findings per `_findings.md`.
    16:   - Costlier error: rejecting a citation the reviewer merely failed to re-locate is WORSE than under-reporting drift, because a review finding is durable and tracked while drift is not. Measured in this repository: backlog `88manw` recorded that plan `si24ia`'s review finding PR-305 rejected a correct spec section citation and substituted a wrong one, which subsequent readers propagated. The rule covers section or heading anchors in specs and docs, not only code symbols.
    17:   - Git ref asymmetry: the same costlier error rule applies to git citations. The trigger is narrow: ONLY when a reviewer is about to declare that a branch, lane, or commit cited as evidence no longer exists. `git branch -a` answers a question about REFS while the evidence lives in OBJECTS. Before declaring lane or branch evidence unrecoverable, a reviewer must search dangling objects by subject (e.g. via `runner_shared.find_dangling_commits_by_subject` or `git fsck --connectivity-only`), and must record which check was run. Precedent: backlog `1ffh63` recorded that review finding PR-001 on plan `kl18sz` declared a replay source unsatisfiable on a refs-only reading and weakened V-01 to a 4-path substitute plus a synthetic fallback, while the finalize tip was resolvable and the real replay was LARGER than claimed. Limits: dangling objects are LOCAL to one checkout, are NOT cloned, and expire to gc; a resolving dangling commit is a legitimate evidence source and NEVER a durable archive, and a plan must not be written to depend on one persisting.
    21:If missing evidence prevents reliable review, file a finding or open question.
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste `rg -n "^### " .aw/system/workflows/plan-review/steps/r3-security.md .aw/system/workflows/plan-review/steps/r4-engineering.md` showing rubric sections A to F, and the section map rows (E-12) assigning each rubric G bullet to exactly one of R2 or R4.
  - Observed evidence:
    `rg -n "^### " .aw/system/workflows/plan-review/steps/r3-security.md .aw/system/workflows/plan-review/steps/r4-engineering.md`:
    ```
    .aw/system/workflows/plan-review/steps/r3-security.md
    12:### B. Security and privacy

    .aw/system/workflows/plan-review/steps/r4-engineering.md
    5:### A. Correctness and data integrity
    12:### C. Architecture and operability
    19:### D. Anti-regression and domain invariants
    26:### E. Testing and verification
    35:### F. KISS, principles, and UX
    45:### Executability: Right-sizing and conceptual density
    55:### Spec and documentation sync
    ```

    Section map rows in `.aw/system/workflows/plan-review/README.md` assigning each rubric G bullet to exactly one of R2 or R4:
    ```
    | Rubric G bullet | Content summary | Assigned step file |
    |---|---|---|
    | `Bijection (1:1)` | `E-*` and `V-*` pairing | `steps/r2-executability.md` |
    | `Item-Dependencies` | Directed acyclic graph | `steps/r2-executability.md` |
    | `Scope-Paths` | Declared change fence | `steps/r2-executability.md` |
    | `Per-E-item right-sizing` | Single pass, one concern | `steps/r4-engineering.md` |
    | `Overloaded E-item` | Splitting multi-deliverable E items | `steps/r4-engineering.md` |
    | `Live-artifact success criteria` | Re-derivation convention | `steps/r2-executability.md` |
    | `Concrete evidence in every V-*` | Non-vacuous verification | `steps/r2-executability.md` |
    | `No hardcoded counts of mutable tree` | Dynamic verification | `steps/r2-executability.md` |
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `rg -n "eight reviewer personas|00-run-protocol" .aw/system/workflows/plan-review/steps/r5-personas.md` and `wc -l` of `r6-decomposition.md` and `r7-cross-plan.md`.
  - Observed evidence:
    `rg -n "eight reviewer personas|00-run-protocol" .aw/system/workflows/plan-review/steps/r5-personas.md`:
    ```
    3:Evaluate the plan through the eight reviewer personas.
    6:`.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas`
    ```

    `wc -l .aw/system/workflows/plan-review/steps/r6-decomposition.md .aw/system/workflows/plan-review/steps/r7-cross-plan.md`:
    ```
      12 .aw/system/workflows/plan-review/steps/r6-decomposition.md
       9 .aw/system/workflows/plan-review/steps/r7-cross-plan.md
      21 total
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste `rg -n -F -f <(printf '%s\n' "chooses a mechanism rather than a fact or a scope" "cites a demonstration that the mechanism produces the required outcome" "confirm empirically / if no form works, stop") .aw/system/workflows/plan-review/steps/s5-questions.md` showing all three phrases, and the line holding `#### Resolving HOW questions: demonstrate, do not describe`.
  - Observed evidence:
    ```
    17:1. A question is a HOW question when its resolution chooses a mechanism rather than a fact or a scope (such as a code shape, a placeholder form, a flag, an algorithm).
    18:2. A HOW question may be marked `resolved` only when the resolution cites a demonstration that the mechanism produces the required outcome on a concrete case (a scratch-repo run, a probe, a test, pasted output), held to the same evidence standard as a Findings row.
    20:4. A resolution containing its own "confirm empirically / if no form works, stop" clause is by definition undemonstrated and falls under (3).
    ```
    Line holding heading:
    ```
    15:#### Resolving HOW questions: demonstrate, do not describe
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste `rg -n "AW-REVIEW: (AGAIN|DONE)" .aw/system/workflows/plan-review/steps/s6-rereview.md` showing both markers.
  - Observed evidence:
    ```
    21:AW-REVIEW: AGAIN
    25:AW-REVIEW: DONE
    ```
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste `rg -n "APPROVE WITH REVISIONS APPLIED|REVIEWED - OPEN QUESTIONS|REJECT - NEEDS REPLAN|Review-Depth|plan-review:" .aw/system/workflows/plan-review/steps/s7-finalize.md`.
  - Observed evidence:
    ```
    5:Write `- Review-Depth: <tier>` in the plan's front matter beside `- Readiness:` (spec Section 7.2; the field is registered by Order 02 `gv3smb`, which is why this plan carries `- Item-Dependencies: executed:gv3smb`: until it lands, a plan carrying the field fails `aw ipd lint` with `IPD-M103` unknown field).
    9:The final commit subject MUST start with `plan-review:`.
    107:   `plan-review: harden <scope> (revisions applied)`
    118:- **`APPROVE WITH REVISIONS APPLIED`** - findings fixed, no open questions,
    120:- **`REVIEWED - OPEN QUESTIONS`** - review completed but decisions remain.
    121:- **`REJECT - NEEDS REPLAN`** - approach is unsound and not repairable with
    127:- **GO:** verdict is `APPROVE` or `APPROVE WITH REVISIONS APPLIED`, all questions
    135:  BLOCKER/HIGH, or a `REVIEWED - OPEN QUESTIONS` / `REJECT - NEEDS REPLAN`
    190:Verdict: <APPROVE | APPROVE WITH REVISIONS APPLIED | REVIEWED - OPEN QUESTIONS | REJECT - NEEDS REPLAN>
    ```
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: paste `rg -o "steps/[a-z0-9_-]+\.md" .aw/system/workflows/plan-review/plan-review.md | sort -u` and `ls .aw/system/workflows/plan-review/steps/` showing the two lists match, `rg -n "0.1 Build the review-scope ledger|0.3 Discover the plan contract|Pre-review commit|--phase author|--phase review-finalize|aw ipd coverage" .aw/system/workflows/plan-review/plan-review.md` showing every retained pre-pass part, and `wc -c .aw/system/workflows/plan-review/plan-review.md`.
  - Observed evidence:
    Steps referenced in `plan-review.md`:
    ```
    steps/_findings.md
    steps/_kernel.md
    steps/p-proofread.md
    steps/q-quick-risk.md
    steps/r1-references.md
    steps/r2-executability.md
    steps/r3-security.md
    steps/r4-engineering.md
    steps/r5-personas.md
    steps/r6-decomposition.md
    steps/r7-cross-plan.md
    steps/s5-questions.md
    steps/s6-rereview.md
    steps/s7-finalize.md
    steps/t-tier.md
    ```

    `ls .aw/system/workflows/plan-review/steps/`:
    `_findings.md _kernel.md p-proofread.md q-quick-risk.md r1-references.md r2-executability.md r3-security.md r4-engineering.md r5-personas.md r6-decomposition.md r7-cross-plan.md s5-questions.md s6-rereview.md s7-finalize.md t-tier.md`

    Retained pre-pass parts:
    ```
    13:### 0.1 Build the review-scope ledger
    37:### 0.3 Discover the plan contract and implementation context
    57:### Pre-review commit
    78:    aw ipd lint --phase author --agent <plan-file>
    82:    aw ipd coverage <id6>
    86:    aw ipd lint --phase review-finalize --agent <plan-file>
    ```

    Byte count:
    `6648 .aw/system/workflows/plan-review/plan-review.md`
  - Result: pass

- [x] V-12 validates E-12
  - Required evidence: paste the count of headings outside code fences in the pre-change file (`git show <E-01 baseline hash>:.aw/system/workflows/plan-review/plan-review.md`, counted with a fence-aware `awk`) and the count of section-map rows in the README, showing every heading is mapped, plus the per-tier byte table and the baseline-commit line as written.
  - Observed evidence:
    Count of headings outside code fences in pre-change file:
    `git show bb094ca8ab37a04dec9f7aa431551d4c70764b86:.aw/system/workflows/plan-review/plan-review.md | awk --posix '/^```/{in_fence=!in_fence; next} !in_fence && /^#{1,4} /{count++} END{print count}'`:
    `38`

    Count of headings map rows in `.aw/system/workflows/plan-review/README.md`:
    `38`

    Per-tier byte table from `.aw/system/workflows/plan-review/README.md`:
    ```
    | Tier | Step files loaded | Byte count | Pre-change single file | Delta |
    |---|---|---|---|---|
    | `simple` (without R3) | `_kernel.md` (1854), `p-proofread.md` (3881), `t-tier.md` (1685), `q-quick-risk.md` (369), `_findings.md` (5302), `s5-questions.md` (9269), `s6-rereview.md` (1434), `s7-finalize.md` (13575) | 37,369 bytes | 48,108 bytes | -10,739 bytes (-22.3%) |
    | `simple` (with R3 short) | Above plus `r3-security.md` (1199) | 38,568 bytes | 48,108 bytes | -9,540 bytes (-19.8%) |
    | `standard` | Above plus `r1-references.md` (3024), `r2-executability.md` (10668), `r3-security.md` (1199), `r4-engineering.md` (3699) [excluding `q-quick-risk.md`] | 55,590 bytes | 48,108 bytes | +7,482 bytes (+15.6%) |
    | `complex` | `standard` plus `r5-personas.md` (613), `r6-decomposition.md` (960), `r7-cross-plan.md` (760) | 57,923 bytes | 48,108 bytes | +9,815 bytes (+20.4%) |
    | `orchestrator` | Base plus `r1-references.md` (3024), `r2-executability.md` (10668), `r7-cross-plan.md` (760) [skipping `t-tier.md`, `q-quick-risk.md`, `r3`, `r4`, `r5`, `r6`] | 49,767 bytes | 48,108 bytes | +1,659 bytes (+3.5%) |
    ```

    Baseline commit recorded in `.aw/system/workflows/plan-review/README.md`:
    `Baseline pre-change commit: bb094ca8ab37a04dec9f7aa431551d4c70764b86`
  - Result: pass

- [x] V-13 validates E-13
  - Required evidence: paste `rg -n "plan-review\.md:[0-9]" .aw/system/workflows agent_workflows` (expected: no output, exit 1) and `rg -n "plan-review/steps/" .aw/system/workflows/spec-review .aw/system/workflows/plan-review-long`.
  - Observed evidence:
    `rg -n "plan-review\.md:[0-9]" .aw/system/workflows agent_workflows`:
    (No matches, exit code 1)

    `rg -n "plan-review/steps/" .aw/system/workflows/spec-review .aw/system/workflows/plan-review-long`:
    ```
    .aw/system/workflows/spec-review/README.md:27:| `plan-review/steps/s7-finalize.md`, "Write the structured Readiness field" | The REQUIRED `- Readiness:` front-matter write | `Readiness` is a plan field. Spec `25kzda` Section 3.3 stops a reviewed spec at an unconditional human approval gate even under `--full-auto`, so a spec has no automated readiness to record. The section's own text warns that "a consumer that finds no field FAILS CLOSED", so writing the field onto a spec would manufacture a machine signal no consumer may act on. |
    .aw/system/workflows/spec-review/README.md:28:| `plan-review/steps/r2-executability.md`, "G. Plan executability" and `steps/r4-engineering.md`, "Executability: Right-sizing and conceptual density" | The E/V-bijection and per-E-item right-sizing rubric | A spec has no `E-*`/`V-*` checklists at all. Applying the rubric to a spec produces findings about a structure the artifact does not have. |
    .aw/system/workflows/spec-review/spec-review.md:28:| Severity (`BLOCKER|HIGH|MEDIUM|LOW`) and Scope (`IN-SCOPE|OVER-SCOPE|UNDER-SCOPE`) | `review_findings.SEVERITIES` | `../plan-review/steps/_findings.md`, "Severity and scope" |
    .aw/system/workflows/spec-review/spec-review.md:29:| Remediation Risk and the Fix Bar | `../release-review/fix-decision-policy.md` | `../plan-review/steps/_findings.md`, "2.3 Remediation Risk and Fix Bar" |
    .aw/system/workflows/spec-review/spec-review.md:30:| Decision (`FIXED|DEFERRED|OPEN|REPLAN`) | `review_findings.DECISIONS` | `../plan-review/steps/_findings.md`, "2.2 Record findings" |
    .aw/system/workflows/spec-review/spec-review.md:31:| The four verdicts | `plan_readiness.VERDICTS` | `../plan-review/steps/s7-finalize.md`, "Verdict and readiness" |
    .aw/system/workflows/spec-review/spec-review.md:62:`../plan-review/steps/s7-finalize.md`, "Write the structured Readiness field" REQUIRES writing that field, and its own text warns that "a consumer that
    .aw/system/workflows/spec-review/spec-review.md:73:`../plan-review/steps/s7-finalize.md`, "Step 4: Finalize state and commit" hand-edits `Status`. For a spec that is forbidden: `.aw/records/specs/README.md`
    .aw/system/workflows/spec-review/spec-review.md:236:For any question resolved by choosing a mechanism, follow `../plan-review/steps/s5-questions.md` ("Resolving HOW questions: demonstrate, do not describe"). That rule is shared and is deliberately not restated here: an unproven fix may not be marked resolved.
    .aw/system/workflows/spec-review/spec-review.md:241:in `../plan-review/steps/s5-questions.md`, "3.1 Build the question set". That rule is shared and is deliberately not restated here.
    .aw/system/workflows/spec-review/spec-review.md:389:`../plan-review/steps/s7-finalize.md`, "Verdict and readiness":
    .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md:27:This rule is kept identical to the single-file `../plan-review/plan-review.md` and its step file `../plan-review/steps/s5-questions.md` per the parity note in `plan-review-long.md`.
    .aw/system/workflows/plan-review-long/plan-review-long.md:93:  `../plan-review/plan-review.md` (and `../plan-review/steps/s7-finalize.md`) per the parity note above);
    ```
  - Result: pass

- [x] V-14 validates E-14
  - Required evidence: paste the `git diff` of `.aw/records/reviews/README.md`.
  - Observed evidence:
    `git show a46bd402460345f3a1129c1ccbb8a6a8825ad3fb -- .aw/records/reviews/README.md`:
    ```diff
    diff --git a/.aw/records/reviews/README.md b/.aw/records/reviews/README.md
    index 1eb40e37e..eb2a2fa89 100644
    --- a/.aw/records/reviews/README.md
    +++ b/.aw/records/reviews/README.md
    @@ -47,22 +47,30 @@ Look the plan up by its id6 when you need that.

     ## Rounds

    -Plans are re-reviewed routinely, so one file holds MULTIPLE rounds as repeated `## Round <N>`
    -sections, appended in order. The LAST round in the file is the CURRENT one.
    +Plans are re-reviewed routinely. Exactly one `## Round <n>` is written per review invocation,
    +appended in order. Re-review passes within the same invocation are `### Pass <k>` subsections
    +inside that round, not new rounds. The LAST round in the file is the CURRENT one.

     Only the current round's findings are live. A gate must read current findings only, or a High raised
     in round 1 and fixed in round 2 would block forever.

     ## Sections

    -Each `## Round <N>` contains:
    -
    -- `### Findings` (required), whose columns are exactly the ones the plan-review workflow already
    -  emits: `ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution`
    +Each `## Round <n>` contains:
    +
    +- `### Proofreading` (two tables):
    +  - Changes: `Location | Old text summary | New text summary | Reason`
    +  - Issues: `ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength`
    +- `### Step <check>`: one subsection per check that ran (for example `### Step R4`), with the check's
    +  notes and evidence. No finding rows belong here; the subsection begins with one `- Checked: <what was examined>` line.
    +- `### Pass <k>`: one subsection per re-review pass, listing which checks were re-run.
    +- `### Findings` (required): the round's single findings table carrying every finding raised in any pass
    +  of the round, whose columns are exactly the ones the plan-review workflow already emits:
    +  `ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution`
     - `### Decisions` (optional), recording the reviewer's self-resolved judgement calls:
       `ID | Question | Chosen | Alternatives considered | Basis | Reversible`

    -A review with no autonomous decisions is valid and simply omits the `Decisions` section.
    +`review_findings.parse_review_text` reads finding rows only under a heading starting with `Findings`, so the new subsections do not change gating. A review with no autonomous decisions is valid and simply omits the `Decisions` section.

     ## Decisions: the audit trail for resolving instead of asking
    ```
  - Result: pass

- [x] V-15 validates E-15
  - Required evidence: paste `rg -n "Recommend\)|very weak|very strong" .aw/system/workflows/askme/askme.md` showing the five-level wording and no old label.
  - Observed evidence:
    ```
    124:   reason. State the strength as one of `very weak`, `weak`, `medium`, `strong`,
    125:   `very strong`, on that option. If evidence does not support a recommendation, say so.
    ```
  - Result: pass

- [x] V-16 validates E-16
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_plan_review_feasibility_rule.py tests/test_v_item_demonstration_reachability.py tests/test_v_item_evidence_durability.py` with every test PASSED, and the `git diff --stat` of those three files.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v tests/test_plan_review_feasibility_rule.py tests/test_v_item_demonstration_reachability.py tests/test_v_item_evidence_durability.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=2527188170
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items

    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_long_form_plan_review_feasibility_rule PASSED [ 10%]
    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_spec_review_feasibility_rule_reference PASSED [ 20%]
    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_no_error_added_proof_shape_in_rubrics PASSED [ 30%]
    tests/test_plan_review_feasibility_rule.py::TestPlanReviewFeasibilityRule::test_single_file_plan_review_feasibility_rule PASSED [ 40%]
    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity PASSED [ 50%]
    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_spec_section_5_4_evidence_reachability PASSED [ 60%]
    tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_single_file_plan_review_evidence_durability PASSED [ 70%]
    tests/test_v_item_demonstration_reachability.py::TestVItemDemonstrationReachability::test_long_form_review_rubric_reachability_rule_parity PASSED [ 80%]
    tests/test_v_item_demonstration_reachability.py::TestVItemDemonstrationReachability::test_scaffolded_validation_intro_carries_reachability_rule PASSED [ 90%]
    tests/test_v_item_demonstration_reachability.py::TestVItemDemonstrationReachability::test_single_file_plan_review_reachability_rule PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== 10 passed in 0.46s ==============================
    ```

    `git show --stat a46bd402460345f3a1129c1ccbb8a6a8825ad3fb -- tests/test_plan_review_feasibility_rule.py tests/test_v_item_demonstration_reachability.py tests/test_v_item_evidence_durability.py`:
    ```
     tests/test_plan_review_feasibility_rule.py      | 35 ++++++++++++++-----------
     tests/test_v_item_demonstration_reachability.py |  8 +++---
     tests/test_v_item_evidence_durability.py        | 24 ++++++++---------
     3 files changed, 36 insertions(+), 31 deletions(-)
    ```
  - Result: pass

- [x] V-17 validates E-17
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_plan_review_step_files.py` with every test PASSED and none skipped, and its `--durations=0` line for the install fixture.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v --durations=0 tests/test_plan_review_step_files.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=1748813122
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 4 items

    tests/test_plan_review_step_files.py::test_installed_plan_review_step_files_exist PASSED [ 25%]
    tests/test_plan_review_step_files.py::test_installed_tier_and_rereview_markers PASSED [ 50%]
    tests/test_plan_review_step_files.py::test_installed_askme_contains_five_level_recommendations PASSED [ 75%]
    tests/test_plan_review_step_files.py::test_installed_finalize_contains_verdicts PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
    ============================== slowest durations ===============================
    3.20s setup    tests/test_plan_review_step_files.py::test_installed_plan_review_step_files_exist
    0.05s teardown tests/test_plan_review_step_files.py::test_installed_finalize_contains_verdicts

    (10 durations < 0.005s hidden.  Use -vv to show these durations.)
    ============================== 4 passed in 3.47s ===============================
    ```
  - Result: pass

- [x] V-18 validates E-18
  - Required evidence: paste the summary lines of the E-18 named pytest run and of the bare `python3 -m pytest`, the `aw check` summary compared with the baseline E-01 recorded, and the `aw commit` output listing the committed paths.
  - Observed evidence:
    Named pytest run summary:
    `57 passed in 4.94s` (from `python3 -m pytest -o addopts="" -n auto tests/test_plan_review_feasibility_rule.py tests/test_v_item_demonstration_reachability.py tests/test_v_item_evidence_durability.py tests/test_plan_review_step_files.py tests/test_spec_review_attestation.py tests/test_run_scratch_path_guard.py`)

    Bare `python3 -m pytest` summary:
    `1846 passed, 11 warnings in 34.47s`

    `aw check` comparison:
    - Baseline E-01: `AW check all 18137 ms; ✗ FINDINGS 63 finding(s) detected across 3011 all (errors 12, warnings 1, info 50)`
    - Post-change E-18: `AW check all 16059 ms; ✗ FINDINGS 63 finding(s) detected across 3011 all (errors 12, warnings 1, info 50)`
    Zero new findings, zero new errors, zero new warnings introduced.

    `aw commit` output:
    ```
    aw commit: committed 30 path(s): a46bd402460345f3a1129c1ccbb8a6a8825ad3fb
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit 3bwrfx -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
