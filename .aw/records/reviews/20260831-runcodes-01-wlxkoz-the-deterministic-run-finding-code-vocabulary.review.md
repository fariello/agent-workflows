# Review: The deterministic run finding-code vocabulary over the shipped evidence and recovery layer

- Plan-Id: wlxkoz
- Reviewed-At: 2026-08-31
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

All claims verified at HEAD `381dbd5c1c313c16b4a833ed5c3541939872ee42`, working tree clean, target plan
committed and unchanged (pre-review snapshot correctly skipped per the workflow's Step 1). Structural
preflight `aw ipd lint --phase author` reports `conforming`.

The plan's central judgement is CORRECT: this is a naming-and-binding layer over shipped predicates, not a
new checker, and its refusal to build a second completion authority is the right call (its predecessor
`7f7782` would have created one, and two disagreeing checkers mean neither can authorize completion).

Verified TRUE:

- Spec `25kzda` 4.2 really does define exactly 13 `RUN-*` codes; I enumerated them and counted 13.
- All 13 really do grep to ZERO hits in the package, as do `unverifiable_ok` / `unverifiable-ok`.
- `DEFAULT_RETRY_LIMIT` really is `2`, so E-04's instruction not to re-litigate the value is correct and
  current.
- The three-state mapping vocabulary (BOUND / UNBOUND-BY-DEPENDENCY / UNBOUND-UNBUILT) is the right shape,
  and E-02's reasoning is the strongest sentence in the plan: "a code silently wired to a predicate that
  does not answer its question is a fail-OPEN checker."

THREE DEFECTS were found, all by checking the plan's premises against the code rather than reading its
prose.

1. PR-001, MEDIUM. A SCOPE COLLISION WITH AN APPROVED PLAN that the plan does not notice. Its Scope-Paths
   claim `tests/test_run_evidence_completion.py` and `tests/test_run_recovery_cli.py`, and BOTH are also in
   the Scope-Paths of APPROVED `runnamecollapse-01` (`0soncw`). The plan cites `0soncw` twice, but only for
   the `aw run` verb rename, and never notices they share two files. Partially mitigated by its own fence
   ("additive cases only; no existing assertion weakened"), which is why this is MEDIUM and not HIGH.
2. PR-002, LOW. E-01 instructs the executor to "follow that module's existing convention" for the `EV-*`
   table while ALSO requiring the new codes be "a DATA table... not branching logic". Those instructions
   conflict: the `EV-*` codes are NOT a data table. They are prose in a docstring
   (`run_evidence.py:540-545`) plus inline string literals scattered through branching logic
   (`:561`, `:575`, `:589`, `:602`, `:614`, `:624`, `:637`, `:650`). An executor following the cited
   precedent would produce exactly what the item forbids.
3. PR-003, LOW. Two `file:line` citations have DRIFTED: `retry_budget_remaining` is at
   `run_recovery.py:355`, not `:340`, and `DEFAULT_RETRY_LIMIT` is at `:62`, not `:47`. The symbols exist
   and the claims about them are true, so this is a staleness defect rather than a false claim, and the
   plan itself warns that HEAD moves hourly here.

All three are FIXED in place with bounded edits. The approach needed no replan.

The `m73aet`-before-`wlxkoz` ordering: the checklist records that 4 of the 13 codes depend on the commit
trailers, and this plan's own Deferred section says `RUN-COMMIT-CONTENTS`/`RUN-COMMIT-GATEWAY` "wait on the
trailers (`runtrail-01`, `m73aet`)". But that ordering lives ONLY in prose: this plan carries
`- Item-Dependencies: none`. Since the edge is declared BY the dependent plan, this plan is its correct
owner. Fixed as part of PR-001's resolution by recording the requirement explicitly; note the edge cannot
be a hard `executed:` prerequisite, because these two codes are deliberately UNBOUND here by design, so the
plan is genuinely runnable before `m73aet` lands.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | B. Sequencing / G. Plan executability | This plan's `- Scope-Paths:`; `0soncw`'s `- Scope-Paths:` entries 6 and 7 (`tests/test_run_recovery_cli.py`, `tests/test_run_evidence_completion.py`); computed by intersecting scope paths across all pending plans | Both of this plan's test files are ALSO in the Scope-Paths of APPROVED `runnamecollapse-01` (`0soncw`). The plan cites `0soncw` twice but only about the `aw run` verb rename, and never notices the shared files, so an executor would not know a concurrent approved plan may be editing the same two modules. `0soncw` is retiring `aw run` and collapsing inspection under `aw runs`, so its edits to these files are likely to be renames of invoked commands, which can collide textually with added cases. Partially mitigated by this plan's existing fence ("additive cases only; no existing assertion weakened, removed, or altered"), which is why this is MEDIUM rather than HIGH. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (the fix is a recorded coordination requirement, not a scope change) | FIXED | Added F8 naming the collision with its evidence. The scope fence now requires the executor to RE-MEASURE both files against `0soncw`'s state immediately before editing and to STOP and report if `0soncw` has landed changes to them, rather than merging blind. The Deferred section now records the `m73aet` ordering requirement explicitly (see the note above on why it cannot be a hard `executed:` edge). |
| PR-002 | LOW | IN-SCOPE | C. Clarity / G. Plan executability | `run_evidence.py:540-545` (docstring prose); `:561`, `:575`, `:589`, `:602`, `:614`, `:624`, `:637`, `:650` (inline literals in branching logic) | E-01 gives two conflicting instructions: make the 13 codes "a DATA table (code, message template, recovery command, failure action)... Keep it data, not branching logic", but ALSO "the module already holds the parallel shipped `EV-*` table, so follow that module's existing convention rather than inventing a new shape". There IS no `EV-*` data table. The `EV-*` codes are a docstring list plus bare string literals inside conditionals, i.e. precisely the branching-logic shape E-01 forbids. An executor who follows the cited precedent produces the wrong thing, and an executor who follows the data instruction must knowingly disregard an explicit instruction. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now states plainly that the `EV-*` codes are NOT a data table (with the evidence), that the DATA requirement wins, and that the new table should be the shape `EV-*` would have had, deliberately introducing the convention rather than copying the existing one. Added as F9. |
| PR-003 | LOW | IN-SCOPE | A. Correctness (citation accuracy) | Actual: `def retry_budget_remaining` at `run_recovery.py:355`; `DEFAULT_RETRY_LIMIT: int = 2` at `:62`. Plan claims `:340` and `:47`. | Two MEASURED citations in E-04 have drifted by roughly 15 lines. The symbols exist and every claim ABOUT them is true (including that the default is now 2), so this is staleness, not fabrication. It matters only because E-04 presents them as measured starting points "so the executor does not rediscover them", and a wrong line number costs exactly the rediscovery it meant to save. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Both citations corrected in E-04 to `:355` and `:62`, with a note that they were re-verified at HEAD `381dbd5c` and must be re-measured again before use, consistent with the plan's own standing warning that HEAD moves hourly. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | The checklist requires `m73aet` before `wlxkoz`. Should this plan carry a hard `- Item-Dependencies: executed:m73aet` edge? | NO. Record the ordering as an explicit REQUIREMENT in Deferred, and state that a future plan which BINDS the two trailer-dependent codes MUST carry the hard edge. | (a) Add the hard edge now. Rejected: `RUN-COMMIT-CONTENTS` and `RUN-COMMIT-GATEWAY` are recorded UNBOUND-BY-DEPENDENCY here BY DESIGN, so this plan is genuinely runnable before `m73aet` lands, and a hard edge would falsely block it at pre-execution. (b) Leave it in prose only, as found. Rejected: the ordering was real but unrecorded anywhere machine-readable or even in this plan's own Deferred section. | Plan Deferred section states those two codes "wait on the trailers (`runtrail-01`, `m73aet`)"; spec 4.2 defines all 13 codes; `ipd_lint.py:683` shows the pre-execution gate that a premature hard edge would trip | yes |
| D-2 | Two of this plan's test files are also claimed by APPROVED `0soncw`. Narrow this plan's scope, or coordinate? | COORDINATE: keep both files in scope, and require a re-measurement against `0soncw`'s state immediately before editing, with STOP-and-report if it has landed changes there. | (a) Drop the files and create a new test module. Rejected: the predecessor `7f7782`'s `tests/test_deterministic_checker.py` was rejected at review precisely because these modules already cover these surfaces, and a third module would duplicate fixtures. (b) Say nothing, relying on the existing additive-only fence. Rejected: additive-only is a mitigation, not immunity, since `0soncw` is rewriting the invoked command strings that existing assertions contain. | Computed Scope-Paths intersection across all pending plans; `0soncw`'s Scope-Paths entries 6 and 7; this plan's F7 and its existing additive-only fence | yes |


## Round 2

Opened 2026-08-31 at the maintainer's prompting ("maybe we should have split wlxkoz"), after round 1 had
already been recorded and the plan approved. Round 1 was WRONG to pass this plan's decomposition without
comment, and this round records why rather than quietly amending round 1 (the gate reads only the CURRENT
round, so a new round is the honest mechanism).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-004 | MEDIUM | IN-SCOPE | C. Right-sizing / G. Plan executability | This plan's 5 E-items mapped against its Scope-Paths: E-01/E-02 -> `run_evidence.py` (the 13-code vocabulary), E-03 -> flag/exit semantics, E-04 -> `run_recovery.py` (a one-line 0..10 bounds check). E-01 AND E-04 both declare `Depends on: none`. Sibling `6lu3rq` has the same E-item COUNT (5) and passed the same lint. | The plan bundles THREE INDEPENDENT CONCERNS and should be SPLIT before execution. Round 1 checked `aw ipd lint` (conforming, "standard" size) and treated that as clearing right-sizing, which the plan-review workflow explicitly forbids: "A passing count-based size lint does NOT clear right-sizing; conceptual density must be evaluated in semantic review." Count is not density. The practical cost is that integration is ALL-OR-NOTHING per plan, so fumbling the 13 verbatim transcriptions strands the trivially safe bounds check along with them. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (the split itself is bounded; the cost is a re-review and re-approval cycle, not design risk) | OPEN | NOT split tonight, deliberately and at the maintainer's direction: it was 01:15 and splitting costs a re-review plus re-approval, AND E-05's tests span all three concerns while touching the same two shipped test modules, so the split must first decide whether each child carries its own edits to those files (reintroducing the `0soncw` coordination question per child) or whether one child owns them. Recorded as F10 in the plan and as a DO-NOT-EXECUTE-AS-IS note in its scope fence, so a rested session splits it rather than rediscovering this. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Amend round 1, or open a round 2? | Open ROUND 2. | Editing round 1 in place. Rejected: the findings gate reads only the CURRENT round, and silently rewriting a completed round would hide that the miss happened. The reviews README states rounds are appended rather than edited for exactly this reason. | `.aw/records/reviews/README.md` on appending `## Round <n>`; `review_findings.current_findings()` semantics | yes |
| D-2 | Split now or record and defer? | RECORD AND DEFER, at the maintainer's explicit direction, with the plan marked do-not-execute-as-is. | Splitting at 01:15. Rejected on the maintainer's call: the E-05 test-coordination question needs a real answer, not a fast one, and the two genuinely safe plans (`m73aet`, `6lu3rq`) can run tonight without it. | Maintainer instruction 2026-08-31; E-05's stated scope over two shipped test modules also claimed by approved `0soncw` | yes |
