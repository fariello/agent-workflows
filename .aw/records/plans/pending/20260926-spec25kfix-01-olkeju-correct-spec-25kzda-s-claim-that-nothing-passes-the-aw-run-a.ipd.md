# IPD: Correct spec 25kzda's claim that nothing passes the AW-Run and AW-Item trailers

- Date: 2026-09-26
- Kind: child
- Concern: APPROVED SPEC `25kzda` STATES A FALSEHOOD ABOUT THE TRAILERS. Its preamble's "Infrastructure status" paragraph says the trailers' writer is built "but NOTHING PASSES THEM: zero of 3764 commits across all refs carry an `AW-Run` trailer; plan `wao266` from backlog `a8eufb` owns the wiring". Measured at HEAD `61ef21d8`: `git log --all --oneline --grep='^AW-Run:' | wc -l` -> `39`, of which 38 have subjects beginning `closed by aw oc run` (the driver-side backlog-close commit, `runner_shared.commit_backlog_close` passing `_gch.run_item_trailers(run_id, plan_id6)`, wired by `wao266`, which has EXECUTED) and one is an agent code commit (`8aabf15a`, IPD `hv9gar`). The spec's own preamble says a Set graduating from it must re-measure, but a false sentence in an approved spec is still what reviewers read first.
- Scope: IN: rewrite the trailer clause of the "Infrastructure status" paragraph so it states, without counts, that several driver-side commit sites pass trailers, agent code commits are generally untrailered, and nothing reads trailers back, each with a dated measurement and its carrier; move the trailers OUT of that sentence's "STILL NET-NEW and to be built:" list, because the writer is shipped and leaving them there keeps the sentence self-contradictory (review F-7); update that paragraph's own measurement header and the preamble's correction-history sentence to record this correction; record the amendment with `aw specs note`; and FILE ONE backlog item for the two code comments that repeat the same false claim (review F-8). OUT: Section 4.2's finding-code table (including the `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` rows, which stay correctly unbound); the other two dated preamble paragraphs; EDITING those two code comments (E-05 files their carrier instead); the rotted citations backlog `sbh1o1` tracks, which live in OTHER artifacts (see Findings F-4).
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: j0ag0u
- Set: spec25kfix
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: olkeju

## Workflow history
- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed in place

- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED in place. The core claim verified false (63 trailered commits at HEAD `46cb6af4`, not zero). PR-001: the target sentence also lists the trailers under "STILL NET-NEW and to be built", so rewriting only the parenthetical left it self-contradictory and still told a graduating Set to rebuild a shipped writer, which the paragraph's own header names as the defect that destroyed `a54m79`; E-02 now moves them out of that list. PR-004: the identical false claim lives in two CODE COMMENTS (`run_evidence`'s `RUN-COMMIT-CONTENTS` `waiting_on`, `ipd_lifecycle`'s attribution docstring, the latter pointing at the now-`done` `a8eufb`), so E-05 files one carrier rather than editing out-of-fence files. Also: counts and the site list were already stale and `8apjpp` has EXECUTED (a third driver-side site is live), so E-01/E-02 now word the site list categorically and re-verify plan statuses; `sbh1o1`'s quotation of the deleted sentence is preserved as a findable trail; and the false "tests read this spec by path" rationale was corrected. Findings F-6..F-9 added. Watermark 04 -> 05.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog j0ag0u on the maintainer's batch-graduation instruction. The false clause and the trailered-commit population were re-measured at HEAD 61ef21d8; backlog sbh1o1 was read and found to concern other artifacts, so it is not folded in.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make spec `25kzda`'s infrastructure paragraph say truthfully who passes and who reads the `AW-Run`/`AW-Item` trailers, worded so the next trailered commit site (for example plan `8apjpp`, or plan `a6xbso`'s agent-commit channel) does not make it false again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure

- [ ] E-01 RE-MEASURE at the executing HEAD and paste: (a) `rg -n "NOTHING PASSES THEM" <spec>` (the clause still present); (b) `git log --all --oneline --grep='^AW-Run:' | wc -l`; (c) `git log --all --format=%s --grep='^AW-Run:' | rg -c '^closed by aw'`; (d) `rg -n "trailers=_gch.run_item_trailers|run_item_trailers\(" agent_workflows` (which commit sites pass trailers now; the E-02 wording must name them GENERICALLY, never list them, because the list has already grown twice); (e) `rg -n "trailers:key|interpret-trailers --parse" agent_workflows` (whether anything reads trailers; if plan `199u11` has executed, `ipd_lifecycle` now reads `AW-Item` and E-02's "nothing reads" sentence must instead say finalize reads `AW-Item` demand-only while no `RUN-*` code is bound). If (a) finds nothing, STOP and report that the clause was already corrected.
  - THE AUTHORED MEASUREMENTS ARE ALREADY STALE, which is the whole argument for (d) being category-level (review PR-002, F-6). Re-measured at review on HEAD `46cb6af4`: (b) is `63`, not 39; (c) is `62`, not 38; and `8apjpp` (revcommit) HAS NOW EXECUTED, so a THIRD driver-side site is live (`runner_shared`'s review-output commit, `review(<host>): record the review of <id6>` carrying `AW-Run`/`AW-Item` plus `AW-Committed-By: driver`, 3 such commits in history). `aw commit` also THREADS trailers through `work_cmd` when a programmatic caller supplies `run_id`/`item_id6`, though no human flag exists. So do not treat F-5's "`8apjpp` will add a site" as future: verify each named plan's CURRENT status with `find .aw/records/plans -name "*<id6>*"` rather than trusting this plan's snapshot, and report which had executed by then.
  - Depends on: none
  - Expected outcome: (a) one hit; (b) a positive count; (c) all but a handful of (b); (d) SEVERAL driver-side sites (three at review time); (e) no reader outside prose comments unless `199u11` has executed.
  - Execution state: pending

### Task group 2: amend

- [ ] E-02 REWRITE THE TRAILER CLAUSE of the "Infrastructure status" paragraph. Replace the parenthetical beginning "(the ledger AND the writer are built" and ending "owns the wiring)" with, in substance (adjust to E-01's measurements): "(the ledger AND the writer are built - `git_commit_helper.run_item_trailers` formats them. Re-measured 2026-09-26: SEVERAL DRIVER-SIDE commit sites pass them (the runner's backlog-close commit, wired by plan `wao266`, and its review-output commit, added by plan `8apjpp`); the AGENT's own code commits are generally UNTRAILERED (backlog `j2srcc`); and NOTHING READS A TRAILER BACK (backlog `am1g38`), so no commit's ownership is yet decided by its trailer and Section 4.2's `RUN-COMMIT-*` rows stay unbound)". Keep "STILL NET-NEW and to be built:" and the rest of the sentence ("the prompt `Run contract` block, and `aw hooks install` ...") byte-identical. NO COUNTS: do not write any commit count, because each new trailered commit would falsify it; name the CATEGORIES and their carriers.
  - THE CLAUSE MUST ALSO STOP CLAIMING THE TRAILERS ARE "STILL NET-NEW and to be built" (review PR-001, F-7). That phrase INTRODUCES the list the parenthetical qualifies, and the trailers are the FIRST item in it. Rewriting only the parenthetical therefore leaves the sentence reading "STILL NET-NEW and to be built: the ... commit trailers (... the writer is built and driver-side sites pass them ...)", which is self-contradictory and still misleads exactly the reader this plan is protecting: a graduating Set told the trailers are net-new may rebuild the shipped writer, which is the precise failure mode the paragraph's own header says destroyed plan `a54m79`. FIX: move the trailers OUT of the "STILL NET-NEW" list into the paragraph's existing "PARTS ALREADY SHIPPED, which a graduating Set must CONSUME, not rebuild" material (or state inline that the WRITER is shipped and only the READ-BACK is net-new), leaving "the prompt `Run contract` block, and `aw hooks install`" as the genuinely net-new remainder. Adjust the list's leading punctuation so the remaining sentence is grammatical; that is a necessary consequence of the fix, not scope creep.
  - DO NOT DELETE THE SUBSTANCE `sbh1o1` DEPENDS ON WITHOUT LEAVING IT FINDABLE (review PR-003, F-4). Backlog `sbh1o1` cites this exact sentence as "THE UNDERLYING FACT SURVIVES", quoting "NOTHING PASSES THEM: zero of 3764 commits ...". After E-02 that quoted string is gone, so `sbh1o1`'s own evidence paragraph becomes a second instance of the citation rot it was filed about. Keep the two ids it relies on (`wao266` and the trailer topic) present in the rewritten clause, and record the interaction in E-04's amendment note so a reader of `sbh1o1` can follow the trail. Do NOT edit `sbh1o1` here (it is outside `- Scope-Paths:` and owns its own fix).
  - Wrap lines to the paragraph's existing width.
  - Depends on: E-01
  - Expected outcome: `rg -n "NOTHING PASSES THEM|zero of 3764" <spec>` returns nothing; the new clause names driver-side sites generically, untrailered agent commits, and the absent reader, each with a carrier; and the trailers no longer appear in the "STILL NET-NEW and to be built" list.
  - Execution state: pending

- [ ] E-03 RECORD THE CORRECTION IN THE PARAGRAPH'S OWN HISTORY, as the preamble convention requires ("Each therefore states its own measurement date and, where one exists, the commit that moved it"): extend the header "Infrastructure status (measured 2026-09-20 at `007d05e1`; corrected 2026-08-30 in `a59f2c53` and again 2026-09-20 by plan `wenmg4`, ..." with "; trailer clause re-measured 2026-09-26 by plan `olkeju`" (place it before the "because this paragraph originally declared" clause); and in the convention paragraph change "the infrastructure paragraph has been corrected twice (2026-08-30, then 2026-09-20)" to "the infrastructure paragraph has been corrected three times (2026-08-30, 2026-09-20, then its trailer clause 2026-09-26)". Both target strings were verified present and unique at review. Touch nothing else in the preamble.
  - Depends on: E-02
  - Expected outcome: both sentences name 2026-09-26 and `olkeju`/the trailer clause; `git diff` of the spec touches only the clause (E-02), these two sentences, and the history line (E-04).
  - Execution state: pending

- [ ] E-04 RECORD THE AMENDMENT on the spec's workflow history with `aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "AMENDED 2026-09-26 (plan olkeju, backlog j0ag0u): corrected the infrastructure paragraph's false 'NOTHING PASSES THEM' trailer clause; driver-side commit sites (wao266's backlog-close and 8apjpp's review-output commit) pass AW-Run/AW-Item, agent code commits are generally untrailered (j2srcc), nothing reads trailers back (am1g38); the trailers also moved out of the STILL NET-NEW list because the writer is shipped; worded without counts; Section 4.2 untouched. NOTE backlog sbh1o1 quoted the removed sentence as its surviving-fact evidence"` (the flag is `--message`), matching the existing `AMENDED ...` history records' shape. VERIFIED at review that `aw specs note` accepts an `approved` spec and prepends the record (tested on a scratch COPY; the tracked spec was not touched), and that three prior `AMENDED ...` records exist to match. Then run `aw specs check <spec>`.
  - Depends on: E-03
  - Expected outcome: a new `- 2026-09-26 note (aw specs): AMENDED 2026-09-26 (plan olkeju ...` line at the TOP of `## Workflow history` (the block is newest-first); `Status:` still `approved`; `aw specs check` conforming.
  - Execution state: pending

- [ ] E-05 REPORT, WITHOUT FIXING, THE TWO SIBLING COPIES OF THIS SAME FALSE CLAIM found at review (PR-004, F-8). Both are in CODE COMMENTS outside this plan's `- Scope-Paths:`, both assert the thing this plan is correcting, and neither has a carrier naming it: (1) `run_evidence.py`'s `RUN-COMMIT-CONTENTS` `waiting_on` string says "`m73aet`'s own executed receipt records that nothing in the tree passes trailers yet"; (2) `ipd_lifecycle.py` says "COMMIT TRAILERS (`AW-Run:`/`AW-Item:`) would settle it exactly, but essentially no commit in history carries one yet, so nothing can be consumed today (backlog `a8eufb`)" - and `a8eufb` is `done`, so that pointer is also dead. Do NOT edit either file (out of fence, and `run_evidence`'s string is part of the Section 4.2 transcription this plan deliberately leaves alone). Instead FILE ONE backlog item with `aw backlog new --work-kind chore` naming both locations and the fact that the correct statement is "driver-side sites pass them; nothing reads them back", and record its id6 here. This is the minimum that stops the correction being undone by the next reader who greps the codebase instead of the spec.
  - Depends on: E-01
  - Expected outcome: one new backlog item exists naming both comment locations and the dead `a8eufb` pointer; neither code file is modified by this plan.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The spec's preamble: "EVERY DATED PARAGRAPH BELOW IS A POINT-IN-TIME SNAPSHOT ... Each therefore states its own measurement date and, where one exists, the commit that moved it", and "NOTHING ENFORCES THIS ... their accuracy rests on whoever next touches them". E-03 follows that shape.
- Spec amendments are recorded as `aw specs note` history lines beginning `AMENDED <date> (plan <id6>, backlog <id6>): ...` (three existing examples, 2026-09-25).
- Section 4.2's table is transcribed into `run_evidence.RUN_FINDING_CODES`. The brief says a byte-equality test guards it; measured at HEAD `61ef21d8`, `rg -n RUN_FINDING_CODES tests/` returns NOTHING (the guarding file `tests/test_run_evidence_completion.py` was removed by the test trim `19313eed`). Section 4.2 is left untouched regardless, so the transcription stays exact whether or not a test watches it.
- AGENTS.md: "A PLAN MAY AMEND A SPEC, AND MUST DECLARE IT" in `- Scope-Paths:` and explain why in spec sync.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

All measured at HEAD `61ef21d8` on 2026-09-26.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MEDIUM | spec `25kzda` Infrastructure status | "NOTHING PASSES THEM: zero of 3764 commits" is false. | `git log --all --oneline --grep='^AW-Run:' \| wc -l` -> `39` |
| F-2 | INFO | who passes | 38 of the 39 are driver-side backlog-close commits; one is an agent commit. | `git log --all --format=%s --grep='^AW-Run:' \| rg -c '^closed by aw'` -> `38`; the other is `8aabf15a` (`hv9gar`) |
| F-3 | INFO | who reads | Nothing reads a trailer back, so the 4.2 `RUN-COMMIT-*` rows are still correctly unbound. | `run_evidence` `RUN-COMMIT-CONTENTS` `binding=UNBOUND_BY_DEPENDENCY`, `waiting_on` "a trailer READ-BACK predicate" |
| F-4 | LOW | backlog `sbh1o1` | Read in full: its rotted citations ("built but UNWIRED" at `:29`, "13 times") live in plan `i1hlgx` (EXECUTED), backlog `zrzfkw` (done), and also open backlog `eh91an` ("Spec 25kzda:28 concedes the ledger is built but UNWIRED"), NOT in this spec paragraph, so they are NOT folded in. One interaction: `sbh1o1` names this paragraph's "NOTHING PASSES THEM" sentence as where the underlying fact survives, and E-02 removes that sentence; `sbh1o1`'s own recommended fix (cite the spec's stable section and claim, not a quoted string) is unaffected. | `rg -l "built but UNWIRED" .aw/records` |
| F-5 | INFO | concurrent plans | `8apjpp` (revcommit) and `a6xbso` (trailread Order 1) add trailered sites, and `199u11` (trailread Order 2) adds a reader; a count-free wording survives the first two, and E-01(e) adapts the "nothing reads" sentence if `199u11` has executed first. SUPERSEDED IN PART at review: `8apjpp` has ALREADY EXECUTED (see F-6). | those plans' Scope |

Added at review, measured on HEAD `46cb6af4`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-6 | MEDIUM | this plan's own measurements | THE NUMBERS AND THE SITE LIST HAVE ALREADY MOVED, in hours. Trailered commits: `63`, not 39. Backlog-close subjects: `62`, not 38. And `8apjpp` is no longer a future plan: it is `executed`, so a THIRD driver-side site is live (`runner_shared`'s review-output commit, subject `review(<host>): record the review of <id6>`, carrying `AW-Run`/`AW-Item` plus `AW-Committed-By: driver`; 3 such commits in history). `aw commit` additionally THREADS trailers via `work_cmd.run_item_trailers` for a programmatic caller. This vindicates the plan's no-counts rule and extends it: the SITE LIST must be categorical too, which is why E-02's wording says "several driver-side sites" and names two as examples rather than enumerating. | `git log --all --oneline --grep='^AW-Run:' \| wc -l` -> `63`; `... \| rg -c '^closed by aw'` -> `62`; `.aw/records/plans/executed/20260925-revcommit-01-8apjpp-...ipd.md` with `- Status: executed`; `rg -n "run_item_trailers"` -> sites in `runner_shared` (x2) and `work_cmd` |
| F-7 | MEDIUM | spec `25kzda` Infrastructure status, the "STILL NET-NEW and to be built:" list | THE FALSE CLAIM IS NOT ONLY IN THE PARENTHETICAL. The trailers are the FIRST ITEM of the list introduced by "STILL NET-NEW and to be built:", so E-02 as originally written would leave "STILL NET-NEW and to be built: the ... commit trailers (... the writer is built and driver-side sites pass them ...)", which contradicts itself and still tells a graduating Set to build a shipped writer. That is the exact failure the paragraph's own header cites as having destroyed plan `a54m79` ("Creating a parallel capability module because this paragraph once called the descriptor net-new is the exact defect that destroyed `a54m79`"). E-02 now also moves the trailers out of that list. | the sentence read in full at `.aw/records/specs/approved/20260826-...spec.md` ("STILL NET-NEW and to be built: the hash-chained run ledger's `AW-Run:`/`AW-Item:` commit trailers (the ledger AND the writer are built ...") |
| F-8 | LOW | `run_evidence.py` `RUN-COMMIT-CONTENTS` `waiting_on`; `ipd_lifecycle.py` attribution docstring | THE SAME FALSE CLAIM EXISTS IN TWO CODE COMMENTS, neither carried by any item. `run_evidence` says "`m73aet`'s own executed receipt records that nothing in the tree passes trailers yet"; `ipd_lifecycle` says "essentially no commit in history carries one yet, so nothing can be consumed today (backlog `a8eufb`)" - and `a8eufb` is `done`, so that pointer is dead too. Correcting only the spec leaves a reader who greps the CODE with the same falsehood. E-05 files one item rather than editing either file (both are outside the fence, and `run_evidence`'s string belongs to the Section 4.2 transcription this plan deliberately does not touch). | the two quoted strings; `.aw/records/backlog/done/20260830-scopeattrib-01-a8eufb-...backlog.md` with `- Status: done` |
| F-9 | INFO | test coupling | THE SPEC EDIT IS SAFE FOR THE SUITE. No test reads this spec file by path: the `25kzda` references in `tests/` are all prose citations or transcribed constants (`tests/test_host_capability_extension.py` transcribes a message DELIBERATELY, "so the test compares the implementation against the SPEC rather than against itself", and that message is in Section 5.2, untouched here). Bare suite green at review: `2458 passed, 2 skipped in 36.79s`. `aw specs check` conforms before the edit. | `rg -n "25kzda" tests/*.py` reviewed in full; no `read_text`/`open(`/`Path(` on the spec |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the clause and the passing/reading sites.
2. E-02 rewrites the clause without counts AND moves the trailers out of the "STILL NET-NEW" list.
3. E-03 records the correction in the paragraph's own history.
4. E-04 records the amendment on the spec's workflow history.
5. E-05 files one item for the two sibling copies of the same false claim in code comments.

## Deferred / out of scope (with reason)

- Fixing the rotted `25kzda` citations in plan `i1hlgx`, backlog `zrzfkw`, and backlog `eh91an`.
  - Carrier: sbh1o1
  - Rationale: they are in other artifacts, one of them an executed plan that must not be edited in place; `sbh1o1` already tracks them.
- Section 4.2's `RUN-COMMIT-*` rows.
  - Carrier-Declined: correctly unbound today (F-3); binding needs a tree-diff proof (plan `199u11` Deferred).
- Correcting the two CODE COMMENTS that repeat this plan's false claim (`run_evidence`'s `RUN-COMMIT-CONTENTS` `waiting_on`, `ipd_lifecycle`'s attribution docstring, the latter also pointing at a `done` item).
  - Carrier-Declined: E-05 FILES the carrier for them, which is this plan's obligation and is where the fix belongs. Editing them here would put code-comment changes in a spec-only fence and would touch `run_evidence`'s Section 4.2 transcription, which this plan deliberately leaves byte-exact. The filed item is the durable record, so the obligation does not vanish when this plan executes.
- Updating `sbh1o1`'s own evidence paragraph, which quotes the sentence E-02 removes.
  - Carrier: sbh1o1
  - Rationale: `sbh1o1` is the item ABOUT citation rot in `25kzda` citations, so a rotted quotation inside it is squarely its own business; E-02 keeps the ids it depends on findable and E-04's note records the interaction, so the trail is not lost.

## Scope check

- Over-scope: none. E-02's removal of the trailers from the "STILL NET-NEW" list is INSIDE the declared trailer clause's own sentence and is required for that sentence to be true (F-7); the `- Scope:` line is updated to say so. E-05 files a backlog item rather than editing code, so no file outside the fence is modified.
- Under-scope: the plan as authored corrected ONE of three copies of the same false statement and did not notice that its own target sentence still called the trailers net-new. Both are now addressed (E-02's second bullet, E-05).
- Scope-Paths justification: the spec itself, for E-02 to E-04 (the `aw specs note` in E-04 writes into the same file). E-05 additionally CREATES one new backlog item file, whose path cannot be declared in advance because its id6 is minted at execution; take `--scope-reason` for it at finalize.

## Required tests / validation

- `aw specs check` on the spec, conforming (it conforms BEFORE the edit too, verified at review, so a failure after is attributable to the edit).
- `rg` checks in V-02 and V-03.
- Bare `python3 -m pytest` before and after; compare failing node IDs. NOTE the parenthetical rationale was checked and is WRONG: no test reads this spec by path (`tests/test_run_selection_policy.py` only CITES it in prose, and `tests/test_host_capability_extension.py` transcribes a Section 5.2 message deliberately, which this plan does not touch). The suite run is therefore a cheap regression check, not a coupling this edit could plausibly break (F-9).

## Spec / documentation sync

- THIS PLAN AMENDS spec `25kzda` (`.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`), declared in `- Scope-Paths:`. WHY: the approved spec asserts "NOTHING PASSES THEM", which has been false since `wao266` executed, and every plan reviewed against this spec inherits that false premise; the spec's own preamble says its snapshots decay and must be corrected by whoever next touches them. The amendment changes a dated STATUS snapshot, not a normative requirement: no section's behavior contract changes, and Section 4.2 is untouched.
- No user-facing docs change.

## Open questions

### OQ-01: Fold backlog `sbh1o1`'s citation fixes into this plan?

- Blocking: no
- Status: resolved
- Owner: maintainer (conditional instruction), resolved by this plan's author from repository evidence
- Resolution or deferral rationale: No. The maintainer's 2026-09-26 brief said to fold them in only if they are in the same paragraph; they are not (F-4), so `sbh1o1` stays its own item and this plan carries no second `From-Backlog`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the five E-01 command outputs (a) through (e).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the spec diff hunk for the clause; paste `rg -n "NOTHING PASSES THEM|zero of 3764" <spec>` returning nothing (exit 1); paste `rg -n "[0-9]+ of [0-9]+ commits" <spec>` returning nothing in the rewritten clause. ALSO paste the FULL rewritten sentence as it now reads, from "STILL NET-NEW" (or whatever replaces it) through the end, so a reader can see the trailers are no longer listed as net-new and that the sentence is grammatical (F-7). Show `wao266` and the trailer topic still appear in the clause, since backlog `sbh1o1` cites this sentence as its surviving-fact evidence (F-4/PR-003).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the two sentence diffs, and `git diff --stat` plus `git diff -U0 <spec> | rg '^@@'` showing only the three edited places.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `aw specs note` output, the new history line (at the TOP of the newest-first block), the unchanged `- Status: approved` line, and `aw specs check <spec>` conforming. Paste the bare `python3 -m pytest` summary BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty); the review baseline for comparison is `2458 passed, 2 skipped in 36.79s` on HEAD `46cb6af4`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the `aw backlog new` invocation and the resulting item path, and `rg -n "nothing in the tree passes trailers|essentially no commit in history carries one"` over the new item showing it names BOTH comment locations, plus a note that `a8eufb` is `done`. Paste `git status --porcelain agent_workflows/` showing NEITHER `run_evidence.py` nor `ipd_lifecycle.py` was modified by this plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A wording correction to an APPROVED spec: `25kzda`'s infrastructure paragraph stops claiming nothing passes the `AW-Run`/`AW-Item` trailers and says instead, without counts, that several driver-side commit sites pass them, agent code commits are generally untrailered, and nothing reads them back. It is a dated status snapshot, not a behavior contract; Section 4.2 and every normative section are untouched, and the spec stays `approved`.

TWO THINGS REVIEW ADDED THAT YOU ARE ALSO APPROVING. FIRST, the same sentence also lists the trailers under "STILL NET-NEW and to be built", and correcting only the parenthetical would leave it contradicting itself and still telling a graduating Set to rebuild a writer that already ships. That is the failure the paragraph's own header says destroyed plan `a54m79`, so the trailers move out of that list too. SECOND, the identical false claim lives in TWO CODE COMMENTS (`run_evidence`'s `RUN-COMMIT-CONTENTS` `waiting_on`, and `ipd_lifecycle`'s attribution docstring, which additionally points at backlog `a8eufb` that is already `done`). This plan does NOT edit them (out of fence, and one is part of the Section 4.2 transcription it deliberately preserves); it FILES one backlog item so correcting the spec does not leave a reader who greps the code with the old falsehood.

MEASUREMENT NOTE: the plan's own counts were already stale at review (63 trailered commits, not 39), and plan `8apjpp` has executed since authoring, adding a third trailered site. Nothing in the amendment depends on a count, which is why that drift costs nothing; the executor re-measures and words it categorically.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the one spec file, PLUS the one new backlog item file E-05 creates (its path cannot be declared in advance because its id6 is minted at execution). If an edit outside the declared path proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every claim pastes the ACTUAL command output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITIONS:
1. If E-01(a) finds the clause already gone, stop and report.
2. If any exploratory probe of `aw specs note` is wanted, run it on a COPY of the spec in a scratch repo, never on the tracked file; review did exactly that (it exits 0 on an `approved` spec and prepends the record), so no probe should be needed.

Commit ONLY the spec and the new backlog item through `aw commit olkeju -- <paths>` (never `git add -A`, never push). The runner announces this declared spec edit before the run. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `j0ag0u` `done` with `--evidence` citing the executed plan.
