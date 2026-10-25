# IPD: Split plan-review into step files with a section map, round layout, and five-level recommendation strength

- Date: 2026-10-24
- Kind: child
- Concern: Spec `k3yx72` (approved) replaces the single-turn plan review with a sequence of review checks that the runner sends as separate prompts (MD-7). The runner can only send checks that exist as separate files. Today `/plan-review` is one 48,108-byte file, `.aw/system/workflows/plan-review/plan-review.md`, so every review loads all of it whatever the plan's size, and no single check can be sent alone. Spec Section 4.3 maps every part of that file to exactly one step file; nothing is written yet. The spec also requires a five-level recommendation strength (MD-9) in `/plan-review` and `/askme`, and a review-record round layout with per-check subsections (Section 7.1), neither of which exists.
- Scope: Create the step files of spec `k3yx72` Section 4.3 under `.aw/system/workflows/plan-review/steps/`, turn `plan-review.md` into a checklist that runs those step files in order (so an interactive `/plan-review` still performs the whole review), keep every existing rule, add the old-to-new section map and the per-tier instruction byte totals to the `plan-review` README, amend `.aw/records/reviews/README.md` with the round layout of Section 7.1, and change `/askme` to the five-level recommendation strength (MD-9, Section 17.4). EXCLUDES all runner code (Orders 02, 04, 05), the citation resolver (Order 03, Stage 2), retiring `/plan-review-long` (Order 07, Stage 2: until then its parity references stay valid because no rule is deleted), and any change to `review_findings` parsing. BEHAVIOR CHANGE TO NOTE AT APPROVAL: from this plan's merge, every `/plan-review`, including the runner's default single-turn review (`runner_shared.build_review_prompt` sends `/plan-review <path>`), runs the tiered checklist, so a plan the agent rates `simple` gets checks P, T, Q, S5 to S7 instead of the full rubric. Spec `k3yx72` MD-7 and Section 4.3 require this, and it lands before the Order 09 pilot; the pre-change file stays readable at the baseline commit E-01 records.
- Scope-Paths: .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review/README.md, .aw/system/workflows/plan-review/steps/*.md, .aw/system/workflows/askme/askme.md, .aw/records/reviews/README.md, agent_workflows/review_findings.py, agent_workflows/plan_readiness.py, .aw/system/workflows/spec-review/spec-review.md, .aw/system/workflows/spec-review/README.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, .aw/system/workflows/plan-review-long/plan-review-long.md, tests/test_plan_review_feasibility_rule.py, tests/test_v_item_demonstration_reachability.py, tests/test_v_item_evidence_durability.py, tests/test_plan_review_step_files.py, CHANGELOG.md
- Item-Dependencies: executed:gv3smb
- Status: reviewed
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
- 2026-10-25 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED
- 2026-10-25 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED; review record .aw/records/reviews/20261024-revsteps-01-3bwrfx-split-plan-review-into-step-files-with-a-section-map-round-l.review.md
- 2026-10-25 to-review (aw set): authored review-ready from spec k3yx72 Stage 1 (MD-20)

- 2026-10-25 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every review check of spec `k3yx72` Section 4.2 a separate step file that the runner can send alone, without losing any rule of today's `plan-review.md`, and make the loss check reviewable through a section map.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: shared step files

- [ ] E-01 Before any edit, record the baseline in the plan's working notes for E-12 and V-18: the commit hash of the last pre-change `plan-review.md` (`git log -1 --format=%H -- .aw/system/workflows/plan-review/plan-review.md`) and the `aw check` summary line. Then create `.aw/system/workflows/plan-review/steps/_kernel.md` from the `plan-review.md` preamble (the planning-only rule, sibling policy pointers, and the from-memory fallback rules), the `## Memory kernel` section, and the instruction part of `## Step 0: Scope and project contract` that tells the agent to apply the `AGENTS.md` rules bearing on the plan (subsection `### 0.2 Discover controlling instructions`). Move, do not paraphrase: rule text is copied verbatim except where a sentence names a step by its old number, which is rewritten to name the step file. Drop the "SERIAL BY DESIGN" parity paragraph from the kernel and keep it in `plan-review.md` itself (E-11), because it describes the interactive checklist, not a check.
  - Depends on: none
  - Expected outcome: the baseline hash and `aw check` summary are recorded; `_kernel.md` exists and holds the memory kernel's nine numbered rules verbatim.
  - Execution state: pending

- [ ] E-02 Create `steps/_findings.md` from `### 2.1 Apply all required views`, `### 2.2 Record findings`, `### 2.3 Remediation Risk and Fix Bar`, `### 2.4 Revise the plan in place`, and `## Severity and scope`, verbatim. Add, from spec `k3yx72` Section 7.1, the rule that findings are rows in the current round's single `### Findings` table (columns exactly as `review_findings.FINDING_COLUMNS`) and that per-check notes go in a `### Step <check>` subsection beginning with one `- Checked: <what was examined>` line (Section 6). Add the closing sentence of MD-8: "Make sure that every edit you made in this step conforms to the proofreading instructions." Add the MD-9 rule that every recommendation states one of `very weak`, `weak`, `medium`, `strong`, `very strong`.
  - Depends on: none
  - Expected outcome: `_findings.md` exists; it carries the Fix Bar text and the Severity and scope text verbatim.
  - Execution state: pending

### Task group 2: check step files

- [ ] E-03 Create `steps/p-proofread.md` (check P): instruct the agent to apply prompt `wcisgc` (`.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md`) to the plan, by reference to that path rather than by copy; to record material changes and unresolved ambiguities in the current round's `### Proofreading` subsection as the two tables of spec Section 7.1 (Changes: location, old text summary, new text summary, reason; Issues: id, location, ambiguity, information needed, recommended answer, recommendation strength); to add open questions only through that Issues table (Section 6.1); to write citations in the forms of Section 11.1; and to change no front-matter value, H2 heading, E/V id or checkbox, `Execution state`, E/V field name, or existing open question's `Status:`/`Blocking:` (the refused list of Section 6.1), stating that the runner refuses such an edit. Because the `wcisgc` prompt lives under `.aw/records/`, which the installer does not ship to a target repository, state in the step file that when that path is absent the agent applies the seven numbered headings of `wcisgc` as summarized in one short paragraph inside `p-proofread.md` (copy the seven heading titles and one sentence each).
  - Depends on: none
  - Expected outcome: `p-proofread.md` exists, names `wcisgc` by path, and carries the fallback summary.
  - Execution state: pending

- [ ] E-04 Create `steps/t-tier.md` (check T): the five tier questions of spec `k3yx72` Section 5.2 verbatim, the instruction to answer each on one line in the round's `### Step T` subsection, the non-binding guidance paragraph of Section 5.2, the statement that the runner supplies the pre-pass facts (Section 4.1 item 4) in the first prompt when run by a runner and that an interactive reviewer collects them itself (`- Scope-Paths:`, E-item and task-group counts, whether a `.spec.md` is named), and the required last line `AW-TIER: <simple|standard|complex>`. Also create `steps/q-quick-risk.md` (check Q): answer "what could this change break, and what existing behavior does something else depend on?", record findings per `_findings.md`.
  - Depends on: none
  - Expected outcome: both files exist; `t-tier.md` contains all five questions and the marker line format.
  - Execution state: pending

- [ ] E-05 Create `steps/r1-references.md` (check `k3yx72` R1) and `steps/r2-executability.md` (check `k3yx72` R2). R1: until the citation resolver exists (Order 03), the agent checks every citation in the plan itself, locating each by symbol, heading, or quoted text (spec Section 4.2 row R1), and records `not-found`/`ambiguous`/`moved` results as findings; plus, verbatim, the numbered items 1 to 6 of `## Step 1: Evidence and pre-review snapshot` (read the plan, list and open the evidence, the citation-disposition rule including its "Costlier error" and "Git ref asymmetry" sub-bullets, record missing evidence, do not infer) and the sentence after them ("If missing evidence prevents reliable review, file a finding or open question."). Spec Section 4.3 maps no row to these items, so without this move the rewrite would drop them. R2: the E/V bijection, `- Scope-Paths:`, `- Item-Dependencies:`, concrete evidence in every `V-*`, and no hardcoded count of a mutable record tree; plus, verbatim, `### Structural preflight (before semantic review)`'s orchestrator subsections ``#### Orchestrator checklist row check and bounded repair loop (`IPD-S407`)`` and ``#### Orchestrator review readiness (`IPD-S408`)``, and the structure, evidence and count bullets of `### G. Plan executability`. Move the bullet beginning `- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**` byte-for-byte, because `tests/test_v_item_evidence_durability.py` compares it with `plan-review-long/review-rubric.md`.
  - Depends on: none
  - Expected outcome: both files exist; R1 carries Step 1 items 1 to 6 verbatim; R2 carries the `IPD-S407` and `IPD-S408` subsections verbatim.
  - Execution state: pending

- [ ] E-06 Create `steps/r3-security.md` (check `k3yx72` R3; full form: `### B. Security and privacy` verbatim; short form: its first three bullets, labelled as such for the `simple` tier of spec Section 5.1) and `steps/r4-engineering.md` (check `k3yx72` R4: `### A. Correctness and data integrity`, `### C. Architecture and operability`, `### D. Anti-regression and domain invariants`, `### E. Testing and verification`, `### F. KISS, principles, and UX` verbatim, plus the right-sizing and overloaded-item bullets of `### G. Plan executability` not moved by E-05, and the check that `## Spec / documentation sync` is truthful). Every bullet of rubric G must land in exactly one of R2 or R4; the section map (E-12) lists each.
  - Depends on: E-05
  - Expected outcome: both files exist; every rubric G bullet appears exactly once across `r2-executability.md` and `r4-engineering.md`.
  - Execution state: pending

- [ ] E-07 Create `steps/r5-personas.md` (check `k3yx72` R5: the eight viewpoints, by reference to `.aw/system/workflows/release-review/00-run-protocol.md#Review mindset: the eight reviewer personas`, not copied), `steps/r6-decomposition.md` (check `k3yx72` R6: decide whether the plan should become a plan Set; a recommended split records a proposed breakdown in the round and is a finding that forces `no-go`; until the split step exists (Order 06, Stage 2) the split is left for a human, as spec Section 10 item 1 already does for approved plans), and `steps/r7-cross-plan.md` (check `k3yx72` R7: consistency with Set siblings and the orchestrator; for an orchestrator, across the whole Set).
  - Depends on: none
  - Expected outcome: three files exist; `r5-personas.md` references the personas heading rather than copying it.
  - Execution state: pending

- [ ] E-08 Create `steps/s5-questions.md` from `## Step 3: Resolve open questions` verbatim (3.1 including both `####` subsections, 3.2, 3.3), plus `### The escalation RETURN PATH` and the finding escalation rule (an unfixed finding at or above the configured block level becomes a `Blocking: yes` question with `- Finding: <ID>`), plus the MD-11 rule (no `Blocking: yes` to `Blocking: no` without a recorded reason) and the MD-9 strength rule for every recommended answer. Keep the heading `#### Resolving HOW questions: demonstrate, do not describe` and its five anchor phrases exactly, because `tests/test_plan_review_feasibility_rule.py` and `spec-review.md` cite them. State that 3.2 (ask interactively) applies only to an interactive `/plan-review` run, and that a runner review records questions instead.
  - Depends on: none
  - Expected outcome: `s5-questions.md` exists and contains the five `ANCHOR_PHRASES` of `tests/test_plan_review_feasibility_rule.py`.
  - Execution state: pending

- [ ] E-09 Create `steps/s6-rereview.md`: decide whether the review's own edits need another pass; end the reply with exactly one last line `AW-REVIEW: AGAIN` or `AW-REVIEW: DONE` (spec Section 8.1); state that an interactive run decides the same thing and loops itself at most twice (Section 8.3). Do NOT write any verdict output in this step (MD-15).
  - Depends on: none
  - Expected outcome: `s6-rereview.md` exists with both marker lines spelled exactly.
  - Execution state: pending

- [ ] E-10 Create `steps/s7-finalize.md` from `## Step 4: Finalize state and commit` verbatim (including ``### Write the structured `Readiness` field (REQUIRED output of the review)`` and `### Hardened-result commit`), `## Verdict and readiness` and ``### A `NO-GO` is RE-EVALUABLE`` verbatim, and `## Required final report` verbatim. Add: the verdict outputs (`- Readiness:`, the status move, the one verdict-bearing history entry) are written in this step only and exactly once per review (MD-15, Section 7.2); the final commit subject starts with `plan-review:`; `- Review-Depth: <tier>` is written here (Section 7.2; the field is registered by Order 02 `gv3smb`, which is why this plan carries `- Item-Dependencies: executed:gv3smb`: until it lands, a plan carrying the field fails `aw ipd lint` with `IPD-M103` unknown field); and in a runner review the final report is the review record, not chat text (Section 4.3 row "Required final report"). Keep the four verdict tokens spelled exactly as `plan_readiness.VERDICTS`.
  - Depends on: none
  - Expected outcome: `s7-finalize.md` exists; it contains the four verdict tokens and the Readiness subsection verbatim.
  - Execution state: pending

### Task group 3: checklist, map, and pointers

- [ ] E-11 Rewrite `.aw/system/workflows/plan-review/plan-review.md` as the checklist (MD-7): keep the H1 and its first paragraph, keep verbatim the parts spec Section 4.3 assigns to the runner pre-pass, because an interactive run must still do them itself: `### 0.1 Build the review-scope ledger` and `### 0.3 Discover the plan contract and implementation context` (Section 4.3 row "Step 0", deterministic parts), the pre-review commit instruction (`### Pre-review commit`), and the whole of `### Structural preflight (before semantic review)` other than the two orchestrator `####` subsections E-05 moves, including the `aw ipd lint --phase review-finalize` re-run at the finalize checkpoint and its exit-code rules; then list, in order, "read and apply `steps/<file>`" for `_kernel.md`, `p-proofread.md`, `t-tier.md` (skipped for an orchestrator, which T does not rate: spec `k3yx72` Section 5.1), then the tier's checks as in spec Section 5.1 (`simple`: `q-quick-risk.md` and the short form of `r3-security.md` when tier question 2 is yes; `standard`: `r1` to `r4`; `complex`: `r1` to `r7`; orchestrator: `r1`, `r2`, `r7`), each with `_findings.md`, then `s5-questions.md`, `s6-rereview.md`, `s7-finalize.md`. Keep the "SERIAL BY DESIGN" parity paragraph, rewritten to say the checklist is serial. The file path and the `plan-review` manifest row in `.aw/system/workflows/index.md` do not change, so the command shims generated by `engine.generate_shim_members` need no change. The baseline commit E-01 recorded is written into the README by E-12, because Order 09 (`kk62qt`) compares the new review against "the current `/plan-review`" (spec `k3yx72` Section 13.3 V2) and E-12's map and V-12 count need the same fixed baseline.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09, E-10
  - Expected outcome: `plan-review.md` is a checklist that names every step file; an interactive `/plan-review` still runs every check, and still runs the scope ledger, pre-review commit, both lint phases, and orchestrator coverage.
  - Execution state: pending

- [ ] E-12 Add to `.aw/system/workflows/plan-review/README.md` (0) the pre-change baseline commit E-01 recorded, named as the `/plan-review` that Order 09's pilot uses for the current-review method (read it with `git show <hash>:.aw/system/workflows/plan-review/plan-review.md`); (a) the old-to-new section map: one row per heading of the pre-change `plan-review.md` (every H2, H3 and H4, including the preamble and the fenced report template) naming the step file it moved to, with each rubric G bullet listed separately by its first words; and (b) the instruction bytes sent per tier: the sum of `wc -c` over the files each tier's checklist names (`simple`, `standard`, `complex`, orchestrator), next to the 48,108 bytes of the pre-change file. Measure the bytes with `wc -c` after E-11 and paste them; do not estimate.
  - Depends on: E-11
  - Expected outcome: the README carries both tables with measured numbers.
  - Execution state: pending

- [ ] E-13 Update the readers that point into moved sections. `.aw/system/workflows/spec-review/spec-review.md` and `.aw/system/workflows/spec-review/README.md`: rewrite each `plan-review.md` reference to name the step file and heading that now holds the cited text (for example `../plan-review/steps/s5-questions.md`, "Resolving HOW questions: demonstrate, do not describe"), and replace every stale line-number citation of the form `plan-review.md:<line>` or `plan-review.md:<from>-<to>` (found with `rg -n "plan-review\.md:[0-9]" .aw/system/workflows`) with a step-file and heading citation. `.aw/system/workflows/plan-review-long/plan-review-long.md` and `03-resolve-and-finalize.md`: change the parity references to name the step files. Also update the two code comments that cite `plan-review.md` by stale line number (the two comments in `agent_workflows/review_findings.py` containing "because the shipped workflow table has it" and "says the history prose", each citing `plan-review.md` with a line-number suffix) and the comment in `agent_workflows/plan_readiness.py` that names `plan-review.md`, "Verdict and readiness", to name `steps/s7-finalize.md` and the heading; comments only, no code change. Do not change the meaning of any of these files.
  - Depends on: E-11
  - Expected outcome: `rg -n "plan-review\.md:[0-9]" .aw/system/workflows agent_workflows` prints nothing.
  - Execution state: pending

- [ ] E-14 Amend `.aw/records/reviews/README.md` sections `## Rounds` and `## Sections` with the spec `k3yx72` Section 7.1 layout: one `## Round <n>` per review invocation; re-review passes are `### Pass <k>` subsections, not new rounds; `### Proofreading` (two tables), `### Step <check>` (notes and evidence, no finding rows, first line `- Checked:`), `### Findings` (the round's single table, unchanged columns), `### Decisions` (unchanged). State that `review_findings.parse_review_text` reads finding rows only under a heading starting with `Findings`, so the new subsections do not change gating.
  - Depends on: none
  - Expected outcome: the README describes the five subsections and says gating is unchanged.
  - Execution state: pending

- [ ] E-15 Change `.aw/system/workflows/askme/askme.md` item 5 "**Recommendation:**" from the three labels `(Strong Recommend)`, `(Recommend)`, `(Weak Recommend)` to the five-level scale of MD-9: state the strength as one of `very weak`, `weak`, `medium`, `strong`, `very strong`, on the favored option. Keep the rest of item 5.
  - Depends on: none
  - Expected outcome: `askme.md` names the five levels and no longer names the three old labels.
  - Execution state: pending

### Task group 4: tests and commit

- [ ] E-16 Update the three tests that read moved text so they read the new location and assert the same rules: `tests/test_plan_review_feasibility_rule.py` (`PLAN_REVIEW_FILE` section 3.1 now in `steps/s5-questions.md`; rubric G anchors `drift_exit_code`, `check_engine.rule_spec`, `unsatisfiable` now in `steps/r2-executability.md` or `steps/r4-engineering.md`, whichever E-05/E-06 put them in), `tests/test_v_item_demonstration_reachability.py` and `tests/test_v_item_evidence_durability.py` (rubric G slice now from the step file; the byte-identical bullet comparison with `review-rubric.md` kept). The spec-review reference test must accept the new step-file path. Do not weaken any assertion; only the file and heading each test reads may change.
  - Depends on: E-11, E-13
  - Expected outcome: the three test modules pass against the new files with the same anchor phrases asserted.
  - Execution state: pending

- [ ] E-17 Add `tests/test_plan_review_step_files.py`, marked `core`, which installs into a scratch repository with `aw install -y <tmp>` (the `run_cli("install", "-y", ...)` pattern of `tests/test_installed_text_current.py`) and asserts on the INSTALLED tree: (a) every step file named in the installed `plan-review.md` exists under `plan-review/steps/` (parse the `steps/<name>.md` references from the checklist text and check each path); (b) `steps/t-tier.md` ends its instructions with the `AW-TIER:` marker format and `steps/s6-rereview.md` names both `AW-REVIEW: AGAIN` and `AW-REVIEW: DONE`; (c) `steps/s7-finalize.md` contains each token of `plan_readiness.VERDICTS`; (d) the installed `askme/askme.md` contains `very weak` and `very strong`. These are outcome checks on what a target repository receives, not checks on how the files are written. Do the install once per module (a module-scoped fixture), so the core tier pays one install (about 3.4 s measured at review) rather than four.
  - Depends on: E-11, E-15
  - Expected outcome: a new core test module that passes.
  - Execution state: pending

- [ ] E-18 Add one `CHANGELOG.md` entry: `/plan-review` is now a checklist of step files, each review check can be run on its own, and `/askme` recommendations use five strength levels. No em or en dashes. Then run `python3 -m pytest -o addopts="" -n auto tests/test_plan_review_feasibility_rule.py tests/test_v_item_demonstration_reachability.py tests/test_v_item_evidence_durability.py tests/test_plan_review_step_files.py tests/test_spec_review_attestation.py tests/test_run_scratch_path_guard.py`, the bare core gate `python3 -m pytest`, and `aw check`, and commit through `aw commit 3bwrfx -- <each changed path>`. Never push.
  - Depends on: E-12, E-14, E-16, E-17
  - Expected outcome: both pytest runs report no failures; `aw check` reports no error and no warning this plan introduced; one path-scoped commit.
  - Execution state: pending

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
  - Carrier: gv3smb, uiyoax
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

- [ ] V-01 validates E-01
  - Required evidence: paste the E-01 baseline hash and `aw check` summary line as recorded, `wc -c .aw/system/workflows/plan-review/steps/_kernel.md`, and the nine numbered memory-kernel lines as they appear in the file, plus `git show <E-01 baseline hash>:.aw/system/workflows/plan-review/plan-review.md | sed -n '/^## Memory kernel/,/^---/p'` showing the same nine lines.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `rg -n "^### |Make sure that every edit|very weak" .aw/system/workflows/plan-review/steps/_findings.md` showing the moved 2.1 to 2.4 headings, the MD-8 sentence, and the five strength levels.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `rg -n "wcisgc|### Proofreading" .aw/system/workflows/plan-review/steps/p-proofread.md` and the fallback paragraph listing the seven heading titles.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `rg -n "AW-TIER|^[1-5]\." .aw/system/workflows/plan-review/steps/t-tier.md` showing five numbered questions and the marker format, and `wc -c` of `q-quick-risk.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n "IPD-S407|IPD-S408|Live-artifact success criteria" .aw/system/workflows/plan-review/steps/r2-executability.md` and `rg -n "until the citation resolver|symbol, heading, or quoted text|Costlier error|Git ref asymmetry|If missing evidence prevents reliable review" .aw/system/workflows/plan-review/steps/r1-references.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `rg -n "^### " .aw/system/workflows/plan-review/steps/r3-security.md .aw/system/workflows/plan-review/steps/r4-engineering.md` showing rubric sections A to F, and the section map rows (E-12) assigning each rubric G bullet to exactly one of R2 or R4.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `rg -n "eight reviewer personas|00-run-protocol" .aw/system/workflows/plan-review/steps/r5-personas.md` and `wc -l` of `r6-decomposition.md` and `r7-cross-plan.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `rg -n -F -f <(printf '%s\n' "chooses a mechanism rather than a fact or a scope" "cites a demonstration that the mechanism produces the required outcome" "confirm empirically / if no form works, stop") .aw/system/workflows/plan-review/steps/s5-questions.md` showing all three phrases, and the line holding `#### Resolving HOW questions: demonstrate, do not describe`.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `rg -n "AW-REVIEW: (AGAIN|DONE)" .aw/system/workflows/plan-review/steps/s6-rereview.md` showing both markers.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `rg -n "APPROVE WITH REVISIONS APPLIED|REVIEWED - OPEN QUESTIONS|REJECT - NEEDS REPLAN|Review-Depth|plan-review:" .aw/system/workflows/plan-review/steps/s7-finalize.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `rg -o "steps/[a-z0-9_-]+\.md" .aw/system/workflows/plan-review/plan-review.md | sort -u` and `ls .aw/system/workflows/plan-review/steps/` showing the two lists match, `rg -n "0.1 Build the review-scope ledger|0.3 Discover the plan contract|Pre-review commit|--phase author|--phase review-finalize|aw ipd coverage" .aw/system/workflows/plan-review/plan-review.md` showing every retained pre-pass part, and `wc -c .aw/system/workflows/plan-review/plan-review.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste the count of headings outside code fences in the pre-change file (`git show <E-01 baseline hash>:.aw/system/workflows/plan-review/plan-review.md`, counted with a fence-aware `awk`) and the count of section-map rows in the README, showing every heading is mapped, plus the per-tier byte table and the baseline-commit line as written.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `rg -n "plan-review\.md:[0-9]" .aw/system/workflows agent_workflows` (expected: no output, exit 1) and `rg -n "plan-review/steps/" .aw/system/workflows/spec-review .aw/system/workflows/plan-review-long`.
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: paste the `git diff` of `.aw/records/reviews/README.md`.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: paste `rg -n "Recommend\)|very weak|very strong" .aw/system/workflows/askme/askme.md` showing the five-level wording and no old label.
  - Observed evidence:
  - Result: pending

- [ ] V-16 validates E-16
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_plan_review_feasibility_rule.py tests/test_v_item_demonstration_reachability.py tests/test_v_item_evidence_durability.py` with every test PASSED, and the `git diff --stat` of those three files.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_plan_review_step_files.py` with every test PASSED and none skipped, and its `--durations=0` line for the install fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-18 validates E-18
  - Required evidence: paste the summary lines of the E-18 named pytest run and of the bare `python3 -m pytest`, the `aw check` summary compared with the baseline E-01 recorded, and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited and justified in the finalize scope reconciliation. Commit only through `aw commit 3bwrfx -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
