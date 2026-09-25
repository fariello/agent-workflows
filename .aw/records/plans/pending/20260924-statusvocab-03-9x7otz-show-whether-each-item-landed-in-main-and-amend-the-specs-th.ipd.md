# IPD: Show whether each item landed in main and amend the specs that name a legacy status

- Date: 2026-09-24
- Kind: child
- Concern: THE RUN SUMMARY HAS NO COLUMN FOR THE ONLY FACT AN OPERATOR NEEDS, AND EIGHT SPECS STILL NAME THE VOCABULARY ORDER 01 REPLACES. The table renders `Status`, `Item`, `Action`, `Verified` and `Issue`, and NONE of them answers "did this reach `main`". Today the answer is obtainable only by listing `.aw/records/plans/executed/` by hand, which is what a human had to do to triage run `run-20260924T050407Z-3108751`. The directory is also the one signal no agent can assert, which is why `runner_shared.edge_satisfied` was deliberately re-pointed at it by maintainer ruling on 2026-09-19 after an in-run status shortcut dispatched a plan into a tree with none of its prerequisite's work, costing "2h 10m and $55.02 for nothing integrated". SEPARATELY, eight specs name at least one legacy status token, and a spec is the contract every other plan is reviewed against: leaving one stale after Order 01 lands would re-authorize the removed vocabulary for every future plan reviewed against it. THE STATUS-VERSUS-LANDED RELATIONSHIP IS DIRECTIONAL, NOT EQUAL, and this is the trap that must be designed for rather than discovered: re-measured across all 28 items of that run, `executed` had zero false positives but THREE FALSE NEGATIVES (`yeh7gc` recorded `dependency-blocked`, `m7gvuz` `failed-safely`, `xdvglg` `substantially-complete` are ALL in `executed/` and ALL in `main`). A naive column that simply restated the status would read `no` for three items that landed.
- Scope: Add a `Landed` column to the run summary derived from the plan's terminal DIRECTORY, and amend the eight specs that name a legacy status token so the contract matches the vocabulary Order 01 ships. IN: the run summary table and its renderer, the directory-derived predicate that feeds the column, and the eight spec files in their real status subdirectories. OUT: deriving the column from any recorded status or self-report (the whole point is that it is independent of both), changing the status vocabulary itself (Order 01 owns it), and changing what any gate refuses.
- Scope-Paths: agent_workflows/run_viewer.py, agent_workflows/runner_shared.py, tests/test_run_summary_table.py, tests/test_run_viewer.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, .aw/records/specs/approved/20260906-77tr3o-01-77tr3o-runner-orchestrator-retirement.spec.md, .aw/records/specs/approved/20260901-7ckptx-01-7ckptx-worker-lane-containment.spec.md, .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, .aw/records/specs/approved/20260912-6kwd2e-01-6kwd2e-midrun-question-surfacing.spec.md, .aw/records/specs/to-review/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md, .aw/records/specs/draft/20260920-i4gpto-01-i4gpto-standalone-executed-plan-audit.spec.md, .aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md
- Item-Dependencies: executed:cyamvi
- Status: reviewed
- Set: statusvocab
- Order: 3
- Highest E allocated: 03
- Priority: high
- Work-Kind: bug
- Blocks-Release: next
- Readiness: go-pending-approval
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: 9x7otz

## Workflow history
- 2026-09-24 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED, none deferred, none open; OQ-01 RESOLVED from repository evidence so no open questions remain; readiness `go-pending-approval`. Record: `.aw/records/reviews/20260924-statusvocab-03-9x7otz-show-whether-each-item-landed-in-main-and-amend-the-specs-th.review.md`. `aw ipd lint --phase author` conformed BEFORE semantic review and `--phase review-finalize` conforms after, so nothing found was structural. DISCLOSURE: same agent and model authored this plan, so this is a SELF-REVIEW; the two serious findings came from COUNTING the specs it claims to enumerate and READING the renderer it proposes to change. WHAT HOLDS: all eight declared spec paths EXIST at their declared subdirectories (notable, since sibling `cyamvi`'s round 1 found all seven of its spec paths stale, and this plan already absorbed that correction); the directory-is-the-authority premise is correctly cited; and F-01's directional framing is right. PR-001 (HIGH): "THE EIGHT SPECS THAT NAME A LEGACY STATUS TOKEN" is a false completeness claim repeated in four places - measured tree-wide, 23 `.spec.md` files carry a legacy token. The eight are a defensible SCOPE JUDGEMENT and a false CENSUS, and the plan recorded no exclusion rule, so an executor re-deriving it would find 23 and could not tell which 15 were excluded or why. E-03 now carries the rule (ordinary-English usage, or `superseded/`) with the excluded files named, forbids widening, and requires the census re-derived with any undeclared status-literal file REPORTED rather than edited. PR-002 (HIGH): E-01 would have added a SECOND resolver for a fact the table already computes per row, and the second one is wrong - `ArtifactAudit.actual_dir` climbs a monthly shard via `_disposition_dir`, while `plan_bucket` returns the raw parent segment, so an archived `executed/YYYYMM/` plan would read `202608` and the column would report a LANDED plan as not landed, which is the exact false-negative class F-01 exists to prevent. PR-003: `render_steps_table` has TWO column variants (5-header `short`, 9-header default), each with its own `headers`/`aligns`/`rows.append` triple, and the plan named one. PR-004: V-02 required `aw runs` output from `.aw/records/runs/`, which is gitignored and absent from a lane, with no fallback. PR-005: the gate was one sentence; for the Set's only spec-amending child the missing do-not-edit-an-undeclared-spec rule was the costliest omission. Four decisions recorded (D-1 OQ-01 resolved to a four-value mapping on `TERMINAL_DIRECTORY_SEGMENTS` and `classify_difference` evidence, D-2 keep 8 rather than widen to 23, D-3 no ninth spec needed since `0718` and `uonrjg` are already declared, D-4 the gitignored run directory is absent and its claims were corroborated by proxy). NOTE FOR APPROVAL: the consequential half is EIGHT SPEC AMENDMENTS, five to `approved` specs.
- 2026-09-24 reviewed (aw set): /plan-review round 1: APPROVE WITH REVISIONS APPLIED. PR-001..PR-005 all FIXED, none deferred, none open; OQ-01 resolved from evidence (D-1), so no open questions remain. PR-001: 'the eight specs that name a legacy status token' is a false completeness claim - 23 spec files carry one; the eight are the right scope judgement, so E-03 now records the exclusion rule and requires the census re-derived with any undeclared status-literal file reported rather than edited. PR-002: E-01 would add a second resolver for a fact the table already computes, and plan_bucket returns the raw parent segment where ArtifactAudit.actual_dir climbs a monthly shard, so an archived executed/YYYYMM/ plan would have read as not landed. PR-003: render_steps_table has two column variants each with its own headers/aligns/row triple. PR-004: V-02 required evidence from a gitignored directory absent in a lane, with no fallback. PR-005: the gate was one sentence and, for the Set's only spec-amending child, lacked the do-not-edit-an-undeclared-spec rule. Record: .aw/records/reviews/20260924-statusvocab-03-9x7otz-show-whether-each-item-landed-in-main-and-amend-the-specs-th.review.md. Readiness go-pending-approval.
- 2026-09-24 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored as part of splitting the oversized cyamvi plan into a Set on maintainer instruction; complete enough to critique.

- 2026-09-24 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Let an operator read one column and know whether the work is in `main`, and leave no spec describing a vocabulary the runner no longer writes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the operator-facing fact

- [ ] E-01 DERIVE `Landed` FROM THE PLAN'S TERMINAL DIRECTORY AND FROM NOTHING ELSE, REUSING THE DIRECTORY FACT THE TABLE ALREADY COMPUTES. DO NOT derive it from the recorded status, from the attempt's disposition, or from any field an agent writes: independence from self-report is the property, not an implementation detail, and F-01 measures three items where status and landedness disagree.

  REUSE, DO NOT ADD A SECOND RESOLVER (corrected at review, PR-002). `render_steps_table` already calls `audit_step_artifact` ONCE PER ROW, and the `ArtifactAudit` it returns already carries `actual_dir`, computed by `artifact_audit._disposition_dir`, which is the plan's disposition directory and ALREADY CLIMBS A MONTHLY SHARD (`executed/202608/` resolves to `executed`, by an explicit `re.fullmatch(r"\d{6}", parent)` branch). A fresh `plan_bucket` call in the renderer would be a SECOND path to one fact, would re-resolve the plan path per row, and - the actual defect - `plan_bucket` returns the raw parent segment, so an ARCHIVED plan would read its shard (`202608`) instead of `executed` and the column would say a landed plan did not land. So derive the column from the audit already in hand. Keep the predicate itself SHARED and thin (a pure directory-name-to-verdict mapping, so both hosts and any later surface reach one object) and feed it `audit.actual_dir`; the plan's `- Scope-Paths:` already declares `runner_shared.py` for that predicate. `edge_satisfied`'s `executed:` branch remains the precedent for WHY the directory is the authority, and is not the code to copy.
  - Depends on: none
  - Expected outcome: one shared directory-to-verdict predicate, fed from the per-row `ArtifactAudit` the table already builds; no second plan-path resolution added to the renderer; an archived `executed/YYYYMM/` plan reads as landed.
  - Execution state: pending

- [ ] E-02 RENDER THE COLUMN IN THE RUN SUMMARY TABLE, beside `Status` rather than replacing it, because the two are independent facts and the DISAGREEMENT between them is diagnostic. Keep the existing columns unchanged. A replayed historical run must render without error, which means the column must tolerate a plan that has since moved, been superseded, or been deleted, and must say so rather than guessing.

  `render_steps_table` HAS TWO COLUMN VARIANTS AND BOTH MUST BE UPDATED (added at review, PR-003): the `short` branch renders 5 headers (`Status`, `Item`, `Action`, `Verified`, `Issue`) and the default branch renders 9 (adding `Attempts`, `Elapsed`, `Cost`, `Total Tok`). Each has its OWN `headers` list, its OWN parallel `aligns` list, and its OWN `rows.append([...])`, so a column added to one variant and not the other silently vanishes from half the surfaces, and a `headers`/`aligns`/row-cell length mismatch skews the box art rather than raising. Update all three lists in BOTH branches.

  DO NOT ADD A GLYPH TO THIS CELL. `render_box_table` measures width with `len(strip_ansi(cell))` rather than by rendered width, which the module records as the reason the `Status` column carries no glyph: a 2-code-point, 1-column grapheme over-counts its column and skews the border. Use plain words plus color, which is also what keeps the column readable under `NO_COLOR` and in a pipe.
  - Depends on: E-01
  - Expected outcome: `aw runs` shows `Landed` per item in BOTH the short and the full variant, with `headers`/`aligns`/row-cells the same length in each; a historical run renders; a missing plan reads as unknown rather than as `no`.
  - Execution state: pending

### Task group 2: the contract

- [ ] E-03 AMEND THE EIGHT DECLARED SPECS THAT DESCRIBE A LEGACY TOKEN AS A VALUE A RUNNER WRITES, stating in each that legacy tokens remain READABLE FOREVER and are no longer WRITTEN. The read-versus-write sentence is required, not decorative: without it a later reader concludes the old spelling is invalid input and "fixes" the back-compatibility path Order 01 built for gitignored historical run directories. THE EIGHT ARE DECLARED AT THEIR REAL PATHS ACROSS FOUR STATUS SUBDIRECTORIES (`approved/` x5, `to-review/`, `draft/`, `implementing/`), each verified to exist at review; two are NOT `approved` (`z7nbn1` is `to-review`, `i4gpto` is `draft`) and amending a non-approved spec is legitimate but must be stated so a reviewer is not surprised.

  THE SCOPE IS A JUDGEMENT, NOT A CENSUS, AND THE DIFFERENCE IS LOAD-BEARING (corrected at review, PR-001). Measured across the whole specs tree at review, TWENTY-THREE `.spec.md` files contain at least one legacy token, not eight. The declared eight are the ones this plan judges to describe the RUNNER'S WRITTEN VOCABULARY; the other fifteen are deliberately EXCLUDED, and the exclusion rule is: a file is out of scope when its occurrences are (a) the ordinary English word `blocked`/`partial` rather than a status literal, which is the bulk of them (`attention-visible-backlog-tier` 29, `attention-registry-and-cross-tree-status` 10, `release-record-and-blocker-gate` 9, `ipd-structure-and-linting` 9+3, `llbr2b` 2, `ipd-spec` 2, `agents-artifact-organization` 2, `uniform-artifact-naming-grammar` 1, `2vev8j` 1, `r07vma` 2, `pip-distribution` 1, `physical-aw-hierarchy` 1, `command-surface-redesign` 1), or (b) in a `superseded/` spec that must not be rewritten (`aw-project-layout-storage-wizard-and-state`, `setid-uniqueness-across-types-and-graduation-links`). DO NOT SILENTLY WIDEN TO 23: a spec using `blocked` as English is not stale, and editing it would churn an approved contract for nothing. DO RE-DERIVE the census at execution and REPORT any file that carries a status LITERAL and is not declared, because that is a genuine miss this plan would otherwise ship; if one is found, report it rather than editing an undeclared path, since the finalize scope gate reconciles declared against actual.
  - Depends on: none
  - Expected outcome: none of the eight DECLARED specs names a legacy token as a value a runner writes; each carries the read-versus-write distinction; `aw specs check` conforming; the re-derived census reported with any undeclared status-literal file named rather than edited.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE SPECS TREE USES STATUS SUBDIRECTORIES, and a plan declaring the old flat path will refuse to finalize. Measured at authoring: `.aw/records/specs/` contains `approved/`, `deferred/`, `draft/`, `implemented/`, `implementing/`. An earlier draft of this Set declared all seven spec paths flat and would have edited eight undeclared files.
- THE DIRECTORY IS THE AUTHORITY FOR "DID THIS LAND", by maintainer ruling 2026-09-19 recorded at `edge_satisfied`: the in-run status shortcut was REMOVED in favour of "ONE authority: the plan's directory on disk", because `executed/` "is exactly where `aw ipd finalize` puts a plan and a directory move is harder to forge than a status field". E-01 reuses that authority rather than inventing a second one.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT: both runners announce declared spec edits before a run starts and the finalize scope gate reconciles declared against actual. All eight are declared.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- F-01 STATUS AND LANDEDNESS DISAGREE ON REAL DATA, AND THE DISAGREEMENT IS THE POINT. Re-measured over all 28 items of `run-20260924T050407Z-3108751`: zero items recorded `executed` are absent from `executed/`, but THREE items NOT recorded `executed` are present in it (`yeh7gc` `dependency-blocked`, `m7gvuz` `failed-safely`, `xdvglg` `substantially-complete`). All three were landed afterwards by hand. So `Landed` must be measured against the DIRECTORY and must NOT be required to agree with the status column; a validation demanding agreement would accept a column that reads `no` for three landed items.
- F-02 THE ASYMMETRY STRENGTHENS THE CASE FOR THE COLUMN RATHER THAN WEAKENING IT. A false negative means work IS in `main` while the run says otherwise, which is precisely the state an operator cannot currently see and which caused three plans in that run to be triaged in the wrong order.
- F-04 "THE EIGHT SPECS" IS A SCOPE JUDGEMENT AND NOT A CENSUS, and stating it as a census was a false completeness claim (added at review, PR-001). Measured across the whole specs tree: 23 `.spec.md` files carry at least one legacy token. The 15 excluded ones use `blocked`/`partial` as ORDINARY ENGLISH or sit in `superseded/`. The eight declared are those describing the RUNNER'S WRITTEN vocabulary. E-03 now carries the exclusion rule and requires the census re-derived at execution, so a genuine miss is reported rather than shipped.
- F-05 THE DIRECTORY FACT IS ALREADY COMPUTED PER ROW, so E-01 must reuse it rather than add a second resolver (added at review, PR-002). `render_steps_table` calls `audit_step_artifact` once per row and the resulting `ArtifactAudit.actual_dir` is the disposition directory, already climbing a monthly shard via `artifact_audit._disposition_dir`. A fresh `plan_bucket` call would return the raw parent segment, so an archived plan under `executed/YYYYMM/` would read its shard instead of `executed` and the column would report a landed plan as not landed.
- F-03 EIGHT SPECS, FOUR SUBDIRECTORIES, TWO NOT APPROVED. Measured at authoring: `0718`, `77tr3o`, `7ckptx`, `uonrjg`, `6kwd2e` in `approved/`; `z7nbn1` in `to-review/`; `i4gpto` in `draft/`; `c4gd2h` in `implementing/`. `c4gd2h` is included because Order 01 cites its R21 for the `interrupted` promotion, so its vocabulary must match too.

## Proposed changes (ordered, validatable)

1. E-01 add the directory-derived landed predicate.
2. E-02 render the `Landed` column beside `Status`.
3. E-03 amend the eight specs with the read-versus-write sentence.

## Deferred / out of scope (with reason)

- Deriving `Landed` from a recorded status or an agent's outcome file: independence from self-report is the property this plan exists to add.
- Changing the status vocabulary: Order 01 (`cyamvi`) owns it, and this plan depends on it being executed first.
- Adding a landed column to `aw attention` or any other surface: this plan changes the RUN SUMMARY, and a second surface is a separate decision with its own consumers.

## Scope check

One derived column from an authority that already exists, plus eight spec amendments that make the contract match the shipped vocabulary. No gate changes, no vocabulary changes, no new authority invented.

## Required tests / validation

Run the suite BARE (`python3 -m pytest`); `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Re-derive the baseline at execution rather than trusting a number authored days earlier; at authoring it was `8850 passed, 5 skipped, 2 xfailed` on `main` `a631a1f6`. Gate on NO NEW failures. Paste ACTUAL output for every `V-*`.

## Spec / documentation sync

EIGHT SPECS ARE AMENDED AND ALL EIGHT ARE DECLARED, at their real paths across four status subdirectories. WHY THIS PLAN AND NOT ORDER 01: a spec amended before the code emits the new vocabulary would leave the contract ahead of the implementation, and this plan's `- Item-Dependencies: executed:cyamvi` enforces that ordering. Each amendment states that legacy tokens stay READABLE and are no longer WRITTEN, because Order 01's back-compatibility path depends on historical run directories remaining parseable and `.aw/records/runs/` is gitignored and unmigratable.

## Open questions

- [x] OQ-01 Should `Landed` distinguish "in `main`" from "in a terminal directory that is not `executed/`" (superseded, not-executed)? Blocking: no. RESOLVED AT REVIEW (D-1): YES, three values (`yes`, `no`, `n/a`), as recommended. `nmlx47` is verified as the live example: it sits in `.aw/records/plans/superseded/` with `- Status: superseded`, is terminal, correctly never landed, and is not a problem, so a column reading `no` for it would mimic a failure. The repository already draws exactly this distinction in code rather than treating every non-`executed` terminal directory alike: `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` names four terminal segments (`executed`, `superseded`, `not-executed`, `reusable`), and `artifact_audit.classify_difference` earns a `CLASS_RETIRED` verdict from a `RETIRED` banner rather than inferring failure from the directory. So `n/a` for `superseded`/`not-executed`/`reusable`, `yes` for `executed` (including a monthly shard), `no` for a plan still in `pending/`, and `unknown` for a plan that cannot be resolved at all. E-01 and V-01 carry this four-way mapping.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the predicate's answer for the three F-01 counter-examples (`yeh7gc`, `m7gvuz`, `xdvglg`) showing `Landed` = yes DESPITE a non-`executed` recorded status, and for one genuinely stranded item showing no. Paste proof the predicate reads no status field and no outcome file, by inspection of its inputs. ALSO paste all four values of the OQ-01 mapping driven from real records: `yes` for an `executed/` plan, `n/a` for `nmlx47` in `superseded/`, `no` for a plan still in `pending/`, and `unknown` for an unresolvable id6. AND paste an ARCHIVED `executed/YYYYMM/` case reading `yes` rather than its shard name, since that is the specific defect PR-002 identified; if no archived plan exists in the tree at execution, construct a synthetic path and say so.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `aw runs` for `run-20260924T050407Z-3108751` showing the `Landed` column. THE BAR IS DIRECTIONAL: `Landed` must agree with the DIRECTORY for every item, and must NOT be required to agree with the STATUS column; paste the three rows where they legitimately disagree as expected output rather than as failures. Paste a replayed run whose plan has since moved, showing unknown rather than a guess. PASTE BOTH TABLE VARIANTS (the `short` 5-column form and the default 9-column form), since PR-003 found each has its own `headers`/`aligns`/row-cell triple and a column added to one alone vanishes from the other. Paste one run rendered with color DISABLED (`NO_COLOR=1` or piped) proving the verdict is readable as a WORD and not by color alone, per the repository's own redundant-cue rule.
  - NOTE ON THE CITED RUN: `.aw/records/runs/` is gitignored, so this directory may be absent at execution in a fresh clone or a lane. If it is, say so and substitute a synthetic run directory carrying the same three status-versus-landed disagreements rather than skipping the evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the amended section from each of the eight specs, and `aw specs check` conforming. Paste the read-versus-write sentence verbatim from at least three, including one of the two non-`approved` specs, and state that amending a `to-review`/`draft` spec was deliberate.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Human approval required before execution. WHAT A HUMAN IS APPROVING: one derived operator-facing column, and EIGHT SPEC AMENDMENTS, five of them to `approved` specs. The spec edits are the consequential half, because a spec is the contract every future plan is reviewed against.

ORDERING IS ENFORCED AND NOT ADVISORY: `- Item-Dependencies: executed:cyamvi` means this plan cannot dispatch until Order 01 is in `.aw/records/plans/executed/`. That edge is re-checked AT DISPATCH, not only at queue build, so an unmet edge marks this one item and does not fail the run. Do not execute this plan by hand ahead of Order 01: a spec amended before the code emits the new vocabulary leaves the contract ahead of the implementation, which is the whole reason this work is Order 03.

OPEN QUESTIONS: OQ-01 was RESOLVED AT REVIEW from repository evidence (D-1), so none remain open. Do not re-decide the four-way `yes`/`no`/`n/a`/`unknown` mapping mid-run; it is recorded in OQ-01 and consumed by E-01 and V-01.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS: `- Scope-Paths:` names two modules, two test files, and eight specs, all verified to exist at review. It is a DECLARATION, not a stop order: an out-of-scope edit that is genuinely required must be MADE and then JUSTIFIED to `aw ipd finalize` with a `--scope-reason` per path, and a declared path left unmodified needs a `--scope-ack`. Do not halt over a scope question. DO halt for a genuinely unsafe condition (an unresolvable concurrent-edit conflict, or a prerequisite whose symbols are absent).

THE ONE SCOPE RULE THAT IS NOT DISCRETIONARY HERE: do NOT edit an UNDECLARED `.spec.md`. E-03's re-derived census will find files carrying legacy tokens that this plan deliberately excluded (15 of the 23 measured at review use the words as ordinary English or sit in `superseded/`). REPORT a genuine miss; do not widen the edit. Both runners announce declared spec edits before the run and reconcile declared against actual at run end, INCLUDING a spec modified without being declared, so an undeclared spec edit is visible and is a defect. This is the only child of Set `statusvocab` licensed to amend a spec.

HONESTY RULE (hard MUST): run the suite BARE as `python3 -m pytest` and paste the ACTUAL summary line; do not add `-n0`, a second `-q`, or `-p no:randomly`. Re-derive the baseline at execution rather than trusting the authored `8850 passed, 5 skipped, 2 xfailed`, and gate on NO NEW failures. Every `V-*` above demands pasted evidence and may not be marked complete from the matching `E-*` checkmark or from memory. Where a `V-*` names a gitignored run directory that is absent, say so and substitute a synthetic one rather than skipping the evidence.

COMMIT DISCIPLINE: commit only the declared paths, path-scoped, through `aw commit`; never `git add -A`, never `-a`, and never push. This is a shared checkout, so run `git diff --cached --name-only` before each commit and unstage anything that is not yours. Note `runner_shared.py` is also declared by siblings Order 01 and Order 02; the runner isolates each item in its own worktree and returns changes through the merge-and-revalidate gate, so the overlap is not a hazard to stop over.

LIFECYCLE TRANSITION: this plan is `- Kind: child`, so the transition is owned unconditionally but its PERFORMER depends on the path. Under `aw oc run`/`aw agy run` the runner performs finalize; do not hand-roll a `git mv` to `executed/` on any path. Executed by hand, the executor runs `aw ipd finalize` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries real observed evidence.
