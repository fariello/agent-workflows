# IPD: Unify the review readiness verdict vocabulary and add a positive "GO - PENDING HUMAN APPROVAL" state

- Date: 2026-07-15
- Concern: usability / consistency of the review workflows' own output (naive-user clarity). Today a plan
  that PASSED review but merely awaits human sign-off is reported as `NO-GO` (plan-review.md:370:
  "A plan may be `Status: reviewed` and still be `NO-GO`"). To a naive reader `NO-GO` reads like failure,
  when the true state is "reviewed clean, just needs your signature". Separately, the GO/NO-GO vocabulary
  is defined INDEPENDENTLY in 5 workflows with pre-existing drift (`CONDITIONAL GO` vs `CONDITIONAL-GO`;
  two-way vs three-way scales; disagreement on whether human approval is folded into GO). This IPD makes
  the headline positive and unifies the vocabulary.
- Scope: workflow-body Markdown that DEFINES or EMITS the readiness verdict across plan-review,
  plan-review-long, verify-execution, verify, release-review, plus shared templates and plans-README;
  the one manifest description that carries GO/NO-GO text (`index.md`) and its regenerated shims; a
  DECISIONS entry (D79) and CHANGELOG. NO code logic change (the shim generator `shim_body` is untouched;
  only the manifest description string it copies changes). Historical records under `workflow-artifacts/`
  and `.agents/plans/executed/` are NOT touched.
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-15 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised when the maintainer noted that a
  clean plan reported as `NO-GO until human sign-off` reads wrong to a naive user, and that other
  projects say "GO pending human approval". A thorough `explore` inventory (below) confirmed 5
  independent definitions, no single source of truth, pre-existing `CONDITIONAL GO`/`CONDITIONAL-GO`
  drift, and that release-review ALREADY uses the preferred model (verdict + separate human consent).
  Maintainer chose: unify across all workflows; standard positive value = `GO - PENDING HUMAN APPROVAL`.
  Complete proposal; born to-review.

## Project conventions discovered (Step 0, VERIFIED via explore inventory + source)

- NO single source of truth. GO/NO-GO is defined in 5 workflows: plan-review (`plan-review.md:353-370`),
  plan-review-long (`03-resolve-and-finalize.md:86-102`, kept in deliberate parity with plan-review),
  verify-execution (`verify-execution.md:105-119,:155`), verify (`verify.md:92-93`), release-review
  (`08-final-ship-review.md:149` et al.), plus a 6th NO-GO clause in `templates/plans-README.md:50`.
- Pre-existing inconsistencies to fix while here: `CONDITIONAL GO` (space, dominant) vs `CONDITIONAL-GO`
  (hyphen, in `verify.md:92`, `08-final-ship-review.md:53`, `cold-start-orientation.md:47`); two-way
  (GO/NO-GO) vs three-way (GO/CONDITIONAL GO/NO-GO) scales; and the crux, that plan-review(-long) fold
  "reviewed but unapproved" into NO-GO while release-review keeps the verdict separate from human consent
  (the 3-rung tree, `08-final-ship-review.md:155-163`). release-review's model is the target to align to.
- Mirrors are GENERATED, never hand-edited: `shim_body` (`engine.py:394`), `generate_shim_members`
  (`engine.py:509`); descriptions come from the `index.md` manifest table. Only ONE description carries
  GO/NO-GO text (verify-execution, `index.md:31` -> shims `.opencode/commands/verify-execution.md:2`,
  `.claude/commands/verify-execution.md:2`). Regenerate via `aw install`; do NOT hand-edit shims.
- NO test asserts on the literal strings "GO"/"NO-GO"/readiness wording (explore grep of tests/). The
  lifecycle `Status:` enum (`draft/to-review/reviewed/approved/...`) is separate and IS tested
  (`test_plan_status.py`, `test_plans_board.py`); this IPD does NOT change that enum. Installer/packaging
  tests assert shims match `shim_body` output, so if `index.md:31` changes, shims must be regenerated.
- VERSION is git-tag-derived, not hand-bumped (`RELEASING.md`, `CONTRIBUTING.md:88-101`); this change
  rides the next release + a DECISIONS entry.
- House rule: no em dashes or en dashes in authored Markdown.

## Target vocabulary (the unified model)

Readiness values, standardized across ALL review workflows:

- `GO` - passed review AND cleared to proceed (for review workflows where the human step is separate,
  this remains the reviewer's positive verdict; it does NOT itself authorize execution).
- `GO - PENDING HUMAN APPROVAL` - passed review, no unfixed BLOCKER/HIGH, all questions resolved, but
  awaits the human sign-off (`Status: approved`) before execution. This REPLACES the old "NO-GO until
  sign-off" reporting for an otherwise-clean plan. Positive headline, caveat inline.
- `CONDITIONAL GO` - mostly ready with limited, clearly documented prerequisites (three-way scale;
  release-review/verify). Canonical SPACE spelling; the hyphenated `CONDITIONAL-GO` is eliminated.
- `NO-GO` - reserved for genuine not-ready: unfixed BLOCKER/HIGH, unresolved open questions, or a
  REJECT/REPLAN verdict. NOT used merely because a clean plan lacks a signature.

Principle (single statement to add to each workflow, replacing the divergent ones): "Human approval is a
separate step from the review verdict. A reviewed, clean plan is `GO - PENDING HUMAN APPROVAL`, never a
bare `NO-GO`; reserve `NO-GO` for genuine not-ready conditions." This mirrors release-review's existing
verdict-plus-consent separation.

## Proposed changes (ordered, validatable)

1. **Define the unified vocabulary once, reference it.** Add the four-value readiness definition + the
   "approval is separate" principle to the canonical rubric in `plan-review/plan-review.md:353-370`, and
   make the other definitions point to / restate it identically (parity). Update:
   `plan-review-long/03-resolve-and-finalize.md:86-102`; `verify-execution/verify-execution.md:105-119`;
   `verify/verify.md:92-93`; `templates/plans-README.md:50`. release-review already separates consent;
   only normalize its spelling (step 3) and add `GO - PENDING HUMAN APPROVAL` where it reports a plan-ish
   readiness.
2. **Update every EMIT/report site** so the final readiness LINE can print `GO - PENDING HUMAN APPROVAL`:
   `plan-review.md:413,:415`; `plan-review-long/report-template.md:46,:48,:49`;
   `verify-execution.md:155,:176`; release-review `templates/final-response.md` (DECISION block,
   `:129,:158,` etc.) and `08-final-ship-review.md` report-assembly; `cold-start-orientation.md:47`;
   `execution-plan.md:32`; `MANIFEST.md:29,:69`; `release-review/README.md:15,:67,:104,:108`.
3. **Fix the CONDITIONAL GO spelling drift**: standardize on the SPACE form everywhere; replace
   `CONDITIONAL-GO` at `verify.md:92`, `08-final-ship-review.md:53`, `cold-start-orientation.md:47`.
4. **Manifest + shims**: reword the verify-execution description at `index.md:31` to use the unified
   vocabulary, then regenerate shims via `aw install` (updates `.opencode/commands/verify-execution.md`
   and `.claude/commands/verify-execution.md`). Do NOT hand-edit the shims.
5. **Optional consistency in user docs** (only if they describe the verdict): `README.md:133`,
   `ARCHITECTURE.md:95`. Do NOT change `engine.py:584` (the baked AGENTS "after an explicit human GO"
   contract) - the word GO there means the human's go-ahead and is unaffected.
6. **Docs + DECISIONS.** DECISIONS entry D79 recording the unified readiness vocabulary, the new
   `GO - PENDING HUMAN APPROVAL` value, the CONDITIONAL-GO spelling fix, and that approval is a step
   separate from the verdict. CHANGELOG under the next minor.

## Deferred / out of scope

- Any change to the lifecycle `Status:` enum (`draft/to-review/reviewed/approved/...`) or its tests.
- Any change to `shim_body`/`generate_shim_members` LOGIC (only the manifest description string changes).
- Editing historical run records (`workflow-artifacts/**`) or executed IPDs (`.agents/plans/executed/**`).
- Collapsing the two-way vs three-way scale into one (workflows that legitimately need CONDITIONAL GO
  keep it; those that do not are not forced to add it). Only the drift/spelling and the missing positive
  value are fixed.

## Open questions (v1 leans for review)

1. Should `GO - PENDING HUMAN APPROVAL` also appear in verify-execution, whose GO means "truly executed
   as approved" (a different axis than pre-execution sign-off)? (Lean: verify-execution keeps GO/NO-GO on
   "truly executed"; the new value is a PRE-execution readiness state, so verify-execution likely does
   NOT need it. Confirm during edit; if it does not apply there, say so explicitly rather than forcing
   it.)
2. Exact rendering: `GO - PENDING HUMAN APPROVAL` vs `GO (pending human approval)`? (Lean: the dash form
   as the canonical enum token in rubric text; report lines may render the parenthetical for prose. Keep
   ONE canonical token so it is greppable.)
3. Does this warrant its own minor release soon, or ride the next scheduled cut? (Lean: ride the next
   cut; it is a docs/workflow clarity change, no code logic, and VERSION is tag-derived.)

## Dependencies / sequencing

- Independent of the agent-comms IPD line. No ordering constraint. Target the next MINOR (workflow
  wording is user-visible via installed workflows + one regenerated shim description).

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Edit ONLY the workflow-body Markdown files enumerated in "Proposed changes" steps 1-3
   (under `.agents/workflows/`), the manifest `index.md:31` (step 4), `README.md`/`ARCHITECTURE.md` only
   if they describe the verdict (step 5), `CHANGELOG.md`, and `DECISIONS.md` (D79). Regenerate the
   verify-execution shims via `aw install` (do NOT hand-edit shim files). Do NOT change `shim_body` logic,
   the lifecycle `Status:` enum, `engine.py:584`, or any historical/executed record. If the work seems to
   need more, STOP and report.
2. Authoring style: NO em dashes or en dashes in any Markdown you write.
3. VALIDATE: run the FULL test suite; paste the ACTUAL runner output (packaging/installer tests confirm
   the regenerated shims match `shim_body`). Grep the workflows to confirm ZERO remaining `CONDITIONAL-GO`
   (hyphen) and ZERO "reviewed ... still be NO-GO"-style phrasing for clean plans. Confirm
   `aw plan-names` clean.
4. COMMIT only this IPD's touched files, PATH-SCOPED (new files need `git add <path>` first); never
   `git add -A`/bare/`-a`; never push.
5. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit path-scoped.
6. RELEASE: the minor is cut separately via release-review Section 9 after a human rung choice.

HARD MUST: paste the real test output; regenerate (never hand-edit) shims; stay inside the scope fence;
never touch the lifecycle Status enum or historical records; never push. Not auto-executed; requires
human approval.
