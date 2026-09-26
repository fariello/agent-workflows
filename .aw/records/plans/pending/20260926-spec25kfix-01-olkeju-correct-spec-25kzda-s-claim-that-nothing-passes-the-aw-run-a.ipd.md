# IPD: Correct spec 25kzda's claim that nothing passes the AW-Run and AW-Item trailers

- Date: 2026-09-26
- Kind: child
- Concern: APPROVED SPEC `25kzda` STATES A FALSEHOOD ABOUT THE TRAILERS. Its preamble's "Infrastructure status" paragraph says the trailers' writer is built "but NOTHING PASSES THEM: zero of 3764 commits across all refs carry an `AW-Run` trailer; plan `wao266` from backlog `a8eufb` owns the wiring". Measured at HEAD `61ef21d8`: `git log --all --oneline --grep='^AW-Run:' | wc -l` -> `39`, of which 38 have subjects beginning `closed by aw oc run` (the driver-side backlog-close commit, `runner_shared.commit_backlog_close` passing `_gch.run_item_trailers(run_id, plan_id6)`, wired by `wao266`, which has EXECUTED) and one is an agent code commit (`8aabf15a`, IPD `hv9gar`). The spec's own preamble says a Set graduating from it must re-measure, but a false sentence in an approved spec is still what reviewers read first.
- Scope: IN: rewrite ONLY the trailer clause of the "Infrastructure status" paragraph so it states, without counts, that driver-side commit sites pass trailers, agent code commits are generally untrailered, and nothing reads trailers back, each with a dated measurement and its carrier; update that paragraph's own measurement header and the preamble's correction-history sentence to record this correction; record the amendment with `aw specs note`. OUT: Section 4.2's finding-code table (including the `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` rows, which stay correctly unbound); the other two dated preamble paragraphs; the rotted citations backlog `sbh1o1` tracks, which live in OTHER artifacts (see Findings F-4).
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: j0ag0u
- Set: spec25kfix
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: olkeju

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog j0ag0u on the maintainer's batch-graduation instruction. The false clause and the trailered-commit population were re-measured at HEAD 61ef21d8; backlog sbh1o1 was read and found to concern other artifacts, so it is not folded in.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make spec `25kzda`'s infrastructure paragraph say truthfully who passes and who reads the `AW-Run`/`AW-Item` trailers, worded so the next trailered commit site (for example plan `8apjpp`, or plan `a6xbso`'s agent-commit channel) does not make it false again.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure

- [ ] E-01 RE-MEASURE at the executing HEAD and paste: (a) `rg -n "NOTHING PASSES THEM" <spec>` (the clause still present); (b) `git log --all --oneline --grep='^AW-Run:' | wc -l`; (c) `git log --all --format=%s --grep='^AW-Run:' | rg -c '^closed by aw'`; (d) `rg -n "trailers=_gch.run_item_trailers|run_item_trailers\(" agent_workflows` (which commit sites pass trailers now; if plan `8apjpp` or `a6xbso` has executed, more sites appear and the E-02 wording must name them generically, not list them); (e) `rg -n "trailers:key|interpret-trailers --parse" agent_workflows` (whether anything reads trailers; if plan `199u11` has executed, `ipd_lifecycle` now reads `AW-Item` and E-02's "nothing reads" sentence must instead say finalize reads `AW-Item` demand-only while no `RUN-*` code is bound). If (a) finds nothing, STOP and report that the clause was already corrected.
  - Depends on: none
  - Expected outcome: (a) one hit; (b) a positive count; (c) all but a handful of (b); (d) the driver-side sites; (e) no reader outside comments at HEAD `61ef21d8`.
  - Execution state: pending

### Task group 2: amend

- [ ] E-02 REWRITE THE TRAILER CLAUSE of the "Infrastructure status" paragraph. Replace the parenthetical beginning "(the ledger AND the writer are built" and ending "owns the wiring)" with, in substance (adjust to E-01's measurements): "(the ledger AND the writer are built - `git_commit_helper.run_item_trailers` formats them. Re-measured 2026-09-26: DRIVER-SIDE commit sites pass them (the runner's backlog-close commit, wired by plan `wao266`); the AGENT's own code commits are generally UNTRAILERED (backlog `j2srcc`); and NOTHING READS A TRAILER BACK (backlog `am1g38`), so no commit's ownership is yet decided by its trailer and Section 4.2's `RUN-COMMIT-*` rows stay unbound)". Keep "STILL NET-NEW and to be built:" and the rest of the sentence ("the prompt `Run contract` block, and `aw hooks install` ...") byte-identical. NO COUNTS: do not write any commit count or a list of every trailered site, because each new trailered site would falsify it; name the categories and their carriers only. Wrap lines to the paragraph's existing width.
  - Depends on: E-01
  - Expected outcome: `rg -n "NOTHING PASSES THEM|zero of 3764" <spec>` returns nothing; the new clause names driver-side sites, untrailered agent commits, and the absent reader, each with a carrier.
  - Execution state: pending

- [ ] E-03 RECORD THE CORRECTION IN THE PARAGRAPH'S OWN HISTORY, as the preamble convention requires ("Each therefore states its own measurement date and, where one exists, the commit that moved it"): extend the header "Infrastructure status (measured 2026-09-20 at `007d05e1`; corrected 2026-08-30 in `a59f2c53` and again 2026-09-20 by plan `wenmg4`, ..." with "; trailer clause re-measured 2026-09-26 by plan `olkeju`" (place it before the "because this paragraph originally declared" clause); and in the convention paragraph change "the infrastructure paragraph has been corrected twice (2026-08-30, then 2026-09-20)" to "the infrastructure paragraph has been corrected three times (2026-08-30, 2026-09-20, then its trailer clause 2026-09-26)". Touch nothing else in the preamble.
  - Depends on: E-02
  - Expected outcome: both sentences name 2026-09-26 and `olkeju`/the trailer clause; `git diff` of the spec touches only these three places.
  - Execution state: pending

- [ ] E-04 RECORD THE AMENDMENT on the spec's workflow history with `aw specs note .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md --message "AMENDED 2026-09-26 (plan olkeju, backlog j0ag0u): corrected the infrastructure paragraph's false 'NOTHING PASSES THEM' trailer clause; driver-side commit sites pass AW-Run/AW-Item, agent code commits are generally untrailered, nothing reads trailers back; worded without counts; Section 4.2 untouched"` (the flag is `--message`), matching the existing `AMENDED ...` history records' shape. Then run `aw specs check <spec>`.
  - Depends on: E-03
  - Expected outcome: a new `- 2026-09-26 note (aw specs): AMENDED 2026-09-26 (plan olkeju ...` line in `## Workflow history`; `Status:` still `approved`; `aw specs check` conforming.
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
| F-5 | INFO | concurrent plans | `8apjpp` (revcommit) and `a6xbso` (trailread Order 1) add trailered sites, and `199u11` (trailread Order 2) adds a reader; a count-free wording survives the first two, and E-01(e) adapts the "nothing reads" sentence if `199u11` has executed first. | those plans' Scope |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the clause and the passing/reading sites.
2. E-02 rewrites the clause without counts.
3. E-03 records the correction in the paragraph's own history.
4. E-04 records the amendment on the spec's workflow history.

## Deferred / out of scope (with reason)

- Fixing the rotted `25kzda` citations in plan `i1hlgx`, backlog `zrzfkw`, and backlog `eh91an`.
  - Carrier: sbh1o1
  - Rationale: they are in other artifacts, one of them an executed plan that must not be edited in place; `sbh1o1` already tracks them.
- Section 4.2's `RUN-COMMIT-*` rows.
  - Carrier-Declined: correctly unbound today (F-3); binding needs a tree-diff proof (plan `199u11` Deferred).

## Scope check

- Over-scope: none.
- Under-scope: none; the only file is the spec.
- Scope-Paths justification: the spec itself, for E-02 to E-04 (the `aw specs note` in E-04 writes into the same file).

## Required tests / validation

- `aw specs check` on the spec, conforming.
- `rg` checks in V-02 and V-03.
- Bare `python3 -m pytest` before and after (the spec is read by some tests' fixtures by path, e.g. `tests/test_run_selection_policy.py` cites it); compare failing node IDs.

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
  - Required evidence: paste the spec diff hunk for the clause; paste `rg -n "NOTHING PASSES THEM|zero of 3764" <spec>` returning nothing (exit 1); paste `rg -n "[0-9]+ of [0-9]+ commits" <spec>` returning nothing in the rewritten clause.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the two sentence diffs, and `git diff --stat` plus `git diff -U0 <spec> | rg '^@@'` showing only the three edited places.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `aw specs note` output, the new history line, the unchanged `- Status: approved` line, and `aw specs check <spec>` conforming. Paste the bare `python3 -m pytest` summary BEFORE and AFTER and the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A wording correction to an APPROVED spec: `25kzda`'s infrastructure paragraph stops claiming nothing passes the `AW-Run`/`AW-Item` trailers and says instead, without counts, that driver-side commit sites pass them, agent code commits are generally untrailered, and nothing reads them back. It is a dated status snapshot, not a behavior contract; Section 4.2 and every normative section are untouched, and the spec stays `approved`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the one spec file. If an edit outside the declared path proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every claim pastes the ACTUAL command output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if E-01(a) finds the clause already gone, stop and report.

Commit ONLY the spec through `aw commit olkeju -- <spec path>` (never `git add -A`, never push). The runner announces this declared spec edit before the run. On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Then close backlog `j0ag0u` `done` with `--evidence` citing the executed plan.
