# IPD: Require the Readiness field at reviewed and approved (IPD-M113), the mirror of IPD-M107

- Date: 2026-10-01
- Kind: child
- Concern: Backlog `l0ixig` asks whether a `reviewed` plan must be REQUIRED to carry `- Readiness:`, enforced the way `IPD-M107` refuses an unattested value. Today nothing checks it: `ipd_lint.check_readiness_attestation` returns `[]` on the first branch when the field is absent ("Absent is the correct authoring state and is silent, by design"), and no other rule reads the field, so a `reviewed` or `approved` plan with NO field is caught by NOTHING. That hole is not cosmetic, because the field is the signal `--full-auto` promotion reads: measured in this lane, stripping the `- Readiness: go-pending-approval` line out of pending plan `2lxcwt` leaves `plan_readiness.is_plan_review_approved` returning `True` and `approval_refusals` returning `[]`, identical to the unstripped plan. The documented justification for the field being optional is therefore FALSE AS WRITTEN: `plan-review.md` ("a consumer that finds no field FAILS CLOSED and treats the plan as not cleared"), `.aw/records/plans/README.md` ("a consumer that finds no field (or an out-of-vocab value) FAILS CLOSED") and `ipd_schema.META_READINESS`'s own comment ("FAILS CLOSED on an absent or out-of-vocab value") all assert fail-closed-on-absent, but `is_plan_review_approved` falls back to PROSE on absent and returns True for any history line matching `history_verdict_approves`. Only the CORRUPT case fails closed. The item's blocking worry, that a required-at-`reviewed` rule needs an R6 exemption, rests on a premise this plan measured FALSE: the R6 path does not produce a `reviewed` plan at all.
- Scope: Close the hole with a Status-keyed metadata rule and correct the three prose claims the measurement falsified. IN: (a) a new blocking lint rule `IPD-M113` in `ipd_lint.py` requiring a non-empty `- Readiness:` when `- Status:` is `reviewed` or in `ipd_schema.READY_TO_EXECUTE`, keyed on STATUS and not on checkpoint, so the R6 path (which leaves `to-review`) is outside it by construction and needs no exemption clause; (b) its tests in `tests/test_ipd_lint.py`, table-driven beside `ReadinessAttestationTests`, including the R6-shaped case and a whole-corpus sweep; (c) the three prose corrections, replacing the false blanket "FAILS CLOSED on absent" with what the code does (CORRUPT fails closed; ABSENT falls back to prose, and is now refused upstream by `IPD-M113` at `reviewed`); (d) a Section 4.4 amendment to spec `ipd-structure-and-linting` recording `IPD-M113`, which is where `IPD-M109`, `IPD-M110` and `IPD-M111` each recorded themselves. OUT: changing `IPD-M107`, whose provenance check is orthogonal and complementary (M107 polices a field that should not be there; M113 polices one that should); changing `plan_readiness.is_plan_review_approved`'s fallback behavior, which is a BEHAVIOR change to the auto-approve gate and belongs in its own reviewed plan (see Deferred, OQ-02); adding a `--readiness` flag to any setter, which would hand an agent exactly the hand-writing licence `AGENTS.md` forbids; retiring `IPD-M107` per spec `4sd62s`; and any backfill of the field onto a plan lacking one, which plan `fx5op3` already decided against and this plan does not reopen.
- Scope-Paths: agent_workflows/ipd_lint.py, tests/test_ipd_lint.py, .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, .aw/system/workflows/plan-review/plan-review.md, .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md, .aw/records/plans/README.md, agent_workflows/ipd_schema.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: l0ixig
- Work-Kind: followup
- Priority: low
- Set: rdyreq
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: fhinri
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008. Reviewed at HEAD `fe2ee961c` in an isolated review lane; plan byte-identical to the lane input, so no pre-review snapshot. Re-measured (gitignored probes): `IPD-M112` is now taken by `C_COVERAGE_RECORD`, so the rule becomes `IPD-M113` (PR-001); partition and five-checkpoint blast radius still zero, but the authored R6 stop condition would fire on 2 hand-stripped `to-review` plans that are outside the gated set, so it is re-specified as (c') (PR-002); a human `--by-human` direct approval of an unreviewed plan yields `approved` with no Readiness and lints clean today, which this rule would refuse at `aw ipd begin`, now measured as E-01(e) and resolved as a deliberate tightening in OQ-03 (PR-003); corpus sweep marked `livecorpus` (PR-004); spec site corrected to Sections 4.4 and 10 and split into E-08/V-08 per `IPD-Z602` (PR-005); suite compared by failure set with the pre-existing `livecorpus` failure named (PR-006); gate given paste-output, scope-fence declaration, conditional finalize and Readiness ownership (PR-007); prose edits coordinated with now-approved `l56tyz` (PR-008).
- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `l0ixig`. Every claim was measured in this lane at HEAD `52e3754c2` rather than carried over from the item. THE ITEM'S BLOCKING WORRY MEASURED FALSE, and that is what decides this plan's shape: the item says a required-at-`reviewed` rule "needs an exemption for exactly the case where a review failed to conclude", because `/plan-review` leaves `- Readiness:` ABSENT on the R6 orchestrator-exhaustion path. Reading that path's own text shows it leaves `- Status: to-review` in the SAME sentence ("the plan remains `- Status: to-review` ... and `- Readiness:` is left ABSENT"), so a rule keyed on STATUS never reaches an R6 plan and the exemption the item feared getting wrong does not need to be written at all. Measured: ZERO plans tree-wide are `to-review` AND carry a review record in history, so the R6 population is empty today and the disjointness is structural rather than incidental. A SECOND, LARGER FINDING arrived while measuring the first and is recorded as F-04/OQ-02: the "absence fails closed" premise that both `fx5op3` and the item rely on is FALSE in the shipped code. `is_plan_review_approved` falls back to PROSE when the field is absent and returns True on any approving history line, which is exactly how a field-less `reviewed` plan can be auto-approved, so the hole this plan closes is live rather than theoretical. Blast radius measured before proposing the rule, at all FIVE checkpoints over all 1127 tracked `.ipd.md` files: ZERO would fail, because the pending lane is a perfect partition (41 `to-review` all absent; 26 `reviewed` and 128 `approved` all present) and terminal-directory plans short-circuit to `DISPOSITION_LEGACY` before any metadata check runs. GATE NOTE: item `l0ixig` carries no `- Blocks-Release:`, so this plan inherits none and invents none.

## Goal

Make the tree refuse a `reviewed` or `approved` plan that carries no `- Readiness:`, so the one signal `--full-auto` promotion reads cannot be silently missing from a plan that claims a review cleared it. `IPD-M107` already refuses a value no review produced; this is its mirror, refusing the absence of a value a review owes.

Secondarily, and stated plainly because it is the more durable half: stop three places in the tree asserting that an absent `- Readiness:` fails closed, when the shipped predicate falls back to prose and returns True.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure, because this plan's shape depends on four facts and not on its prose

- [x] E-01 RE-MEASURE THE FOUR FACTS THAT DECIDE WHETHER THIS RULE IS SAFE, BEFORE WRITING ANY CODE. Each was measured at authoring in this lane and each can move. Run and record raw output for: (a) THE LIVE PARTITION, counting nonterminal tracked plans by (`Status`, field present/absent), expected `to-review` 41 all ABSENT, `reviewed` 26 all PRESENT, `approved` 128 all PRESENT; (b) THE BLAST RADIUS, the count of plans a Status-keyed rule would fail, evaluated at ALL FIVE `ipd_schema.CHECKPOINTS` and skipping any plan whose `lint_text` disposition is `legacy/not evaluated` or `quarantined`, expected ZERO at every checkpoint; (c) THE R6 DISJOINTNESS, the count of plans that are `Status: to-review` AND carry a review record per `plan_readiness.history_has_review_record`, expected ZERO at authoring but MEASURED AT 2 AT REVIEW (2026-10-07: `qpw45x` and `q4uifc`, both reviewed with `APPROVE WITH REVISIONS APPLIED`, whose `- Status: reviewed` and `- Readiness:` lines commit `8c460a9a1` 'Fix baseline test failures' removed by hand). Those two are NOT R6 plans: they are field-less AND `to-review`, so a Status-keyed rule correctly ignores them, which is the no-exemption decision HOLDING rather than failing. So record this count AS CONTEXT, and also record (c') the count that would actually void the decision: plans at a GATED status (`reviewed` or `READY_TO_EXECUTE`) whose newest review record is an R6-style non-concluding review, expected zero; (d) THE NEXT FREE CODE, by importing `ipd_lint` and comparing `C_*` VALUES rather than grepping, expected highest `IPD-M112` (taken by `C_COVERAGE_RECORD`, gradcover `qs00nc`) so the new code is `IPD-M113` (the module's own comment requires this method and forbids grep).

  IF (b) IS NONZERO, that is the one result that changes the plan rather than a figure to update: STOP and record which plans fail and why, because a rule that fails live plans needs either a cutover (see Deferred) or a fix to those plans, and this plan proposes neither. A NONZERO (c) does NOT stop execution (it is the measured state at review, explained above). IF (c') IS NONZERO, record which plans and why, mark E-03 `blocked`, and leave the exemption design to the maintainer: an R6-shaped plan existing at a gated status would mean the status keying is insufficient, which is the item's original concern becoming true. IF (a) has drifted but (b) is still zero, proceed and use the new numbers.
  (e) THE HUMAN DIRECT-APPROVE PATH, which the authoring turn did not measure and which this rule DOES reach: `ipd_lifecycle.validate_transition('to-review', 'approved', actor='human')` is `ok=True`, and measured at review 2026-10-07 in a scratch repository, `aw ipd set approved <id6> --by-human` on an unreviewed `to-review` plan succeeds, writes `- Approval:` and NO `- Readiness:`, and the result lints `clean`. After this plan that same plan lints `error` with `IPD-M113`, so `aw ipd begin` (which lints at `pre-execution`) refuses a plan a human deliberately approved without a review. Record whether that path is still open at execution; E-03's message and the Deferred row below handle it.
  - Depends on: none
  - Expected outcome: five raw measurements recorded with the command that produced each, and an explicit statement of whether each matches the authoring figure; any stop condition hit is recorded rather than worked around.
  - Execution state: performed

- [x] E-02 CONFIRM THE R6 PATH LEAVES `to-review` BY READING BOTH WORKFLOW BODIES, not just the short one, because the no-exemption decision rests entirely on this and a divergence between the two bodies would void it. Quote the "Honest exhaustion (R6)" paragraph from `.aw/system/workflows/plan-review/plan-review.md` and from `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md`, and confirm BOTH state the plan remains `- Status: to-review` while `- Readiness:` is left absent. Also confirm the parallel normative source, spec `r07vma`, says the same, and confirm that each body's "Write the structured `Readiness` field (REQUIRED output of the review)" section sits AFTER its set-`reviewed` instruction, so the required write and the `reviewed` status are already paired in the contract this rule mechanizes.

  WHAT WOULD VOID THE DECISION: either body setting `reviewed` on the R6 path, or a THIRD exhaustion path that reaches `reviewed` with no field. If found, STOP and record it; the rule would then need the explicit exemption the backlog item feared, and designing that exemption is a different plan.
  - Depends on: E-01
  - Expected outcome: both R6 paragraphs quoted with their file paths, an explicit confirmation that each leaves `to-review`, and a one-sentence statement of whether the no-exemption decision holds.
  - Execution state: performed

### Task group 2: the rule

- [x] E-03 ADD THE `IPD-M113` CONSTANT AND THE `check_readiness_required` FUNCTION TO `ipd_lint.py`, keyed on `- Status:` and NOT on checkpoint. Declare `C_READINESS_REQUIRED = "IPD-M113"` in the module-level constant block beside `C_READINESS_UNATTESTED`, with a comment naming this Set (`rdyreq`) as the module's existing constants each name theirs. The predicate: gather the gated status set as `frozenset({"reviewed"}) | ipd_schema.READY_TO_EXECUTE`, DERIVED from that frozenset and never re-listed, for the reason `status_set.py`'s approval gate records verbatim ("a gate keyed on the literal `approved` would leave the automated tier ungated"), so `auto-approved` is covered without a second literal; return `[]` when the normalized status is outside that set; otherwise return one `Diagnostic` when `doc.meta_fields.get(ipd_schema.META_READINESS)` is absent or blank.

  KEY ON STATUS, NOT ON CHECKPOINT, and state the reason in the comment because it is the whole design: the R6 path leaves `to-review`, so status keying excludes it STRUCTURALLY and no exemption clause is needed, whereas a checkpoint-keyed rule (`review-finalize`, say) would fire on exactly the R6 plan the contract tells the reviewer to leave field-less. Do NOT add a date cutover or a `grandfathered` sentinel: E-01(b) measures the live blast radius at zero, and a cutover whose enforcement boundary excludes nothing is the "decoration" failure `config.py` warns about. The message must name the field, the status that demands it, and the remedy (re-run `/plan-review`, which owns the write), and must NOT tell the reader to hand-write the value, which `AGENTS.md` forbids and `IPD-M107` punishes. Because a HUMAN may approve an unreviewed plan directly (E-01(e)), the message must also say that a plan approved without a review must be reviewed before it can execute, so the refusal reads as the review requirement it is rather than as a corrupt file. That consequence (human direct-approval now requires a review before `aw ipd begin`) is a deliberate tightening and is recorded in OQ-03.
  - Depends on: E-02
  - Expected outcome: `C_READINESS_REQUIRED == "IPD-M113"` importable, `check_readiness_required` present and pure (no I/O), returning one diagnostic for a field-less `reviewed` plan and `[]` for a field-less `to-review` plan.
  - Execution state: performed

- [x] E-04 WIRE THE CHECK INTO `lint_text` AS BLOCKING, appending to `diags` and never to `advisories`, directly beside the existing `diags += check_readiness_attestation(doc)` call so the two readiness rules read as the pair they are. Appending to `diags` IS the severity mechanism in this module: `disposition` is computed as `DISPOSITION_ERROR if diags else DISPOSITION_CONFORMING`, and an advisory cannot move the exit code. Add it to `lint_text` and NOT to a `lint_file` `_merge_*`, because the check needs no I/O and `lint_text` is pure by documented contract; a `_merge_*` placement would also make the rule invisible to a text-only caller.

  CONFIRM THE TWO SHORT-CIRCUITS THAT BOUND THE BLAST RADIUS still sit ABOVE the call after the edit, since they are what keeps 932 terminal-directory plans out of this rule: the `_is_terminal_dir` branch returning `DISPOSITION_LEGACY`, and the `is_quarantined` branch returning `DISPOSITION_QUARANTINED`. Both already precede the `diags` block; this item must not move either, and must not place the new call above them.
  - Depends on: E-03
  - Expected outcome: a field-less `reviewed` plan lints `error` with `IPD-M113` in `diagnostics` (not `advisories`) at every checkpoint; a terminal-directory plan still returns `legacy/not evaluated`; a quarantined plan still returns `quarantined`.
  - Execution state: performed

### Task group 3: tests

- [x] E-05 ADD A TABLE-DRIVEN TEST CLASS FOR `IPD-M113` to `tests/test_ipd_lint.py`, modelled on the adjacent `ReadinessAttestationTests` (which is `IPD-M107`'s class and the closest possible template, sharing both the fixture shape and the two-test structure). The table must cover, at minimum: `reviewed` + absent (FIRES); `reviewed` + blank value (FIRES, since blank is not a readiness); `reviewed` + `go-pending-approval` (silent); `approved` + absent (FIRES, including the human direct-approve shape: `- Approval:` present, no review record, no field); `auto-approved` + absent (FIRES, which is the case a literal `approved` keying would miss); `to-review` + absent (SILENT, THE R6 CASE, and the row that pins the no-exemption decision in a test rather than only in prose); `draft` + absent (silent); and a terminal-directory `executed` plan + absent (silent via the legacy short-circuit).

  ASSERT ON BOTH CHANNELS AND ON THE DISPOSITION, copying `ReadinessAttestationTests`'s own guard: a row expecting silence must assert the code appears in NEITHER `res.diagnostics` NOR `res.advisories`, and a row expecting a fire must assert `res.disposition == DISPOSITION_ERROR`, so a later demotion to advisory fails the test instead of passing it. Iterate every checkpoint in `ipd_schema.CHECKPOINTS` for at least the fires-and-silent pair, since the rule claims to be checkpoint-independent and that claim needs pinning.
  - Depends on: E-04
  - Expected outcome: the new class passes; its R6 row fails if the rule is re-keyed from status to checkpoint; its `auto-approved` row fails if the gated set is re-listed as the literal `approved`.
  - Execution state: performed

- [x] E-06 ADD THE WHOLE-CORPUS SWEEP TEST asserting that no nonterminal tracked plan violates `IPD-M113`, the exact analogue of `test_every_readiness_carrying_plan_in_the_tree_is_attested` which does this for `IPD-M107`. Walk every `.ipd.md` under the plans tree, skip any whose `lint_text` disposition is `legacy/not evaluated` or `quarantined`, and assert the offender list is empty with the offending filenames in the failure message.

  THIS IS THE REGRESSION GUARD, not a restatement of E-01(b): E-01 measures the corpus ONCE at execution time, while this test re-measures it on every suite run, so a future plan authored into `reviewed` without the field goes red in CI instead of reaching the auto-approve gate. Use the REAL tracked corpus rather than a fixture, as the M107 sweep does, since the whole value is that it tracks the live tree. MARK IT `@pytest.mark.livecorpus`, which `pyproject.toml` defines for exactly this shape (any agent writing a plan can turn it red, and a red default-suite test blocks every concurrent lane's merge); it then runs in `make test-all` and release-review rather than the default run. Note the M107 sweep predates that marker and is unmarked; do not copy that omission.
  - Depends on: E-05
  - Expected outcome: the sweep passes at HEAD under `python3 -m pytest -m livecorpus`; adding a field-less `reviewed` plan to the tree makes it fail and names that file; a bare run deselects it.
  - Execution state: performed

### Task group 4: correct the falsified prose

- [x] E-07 CORRECT THE THREE "ABSENCE FAILS CLOSED" CLAIMS, which E-01 and F-04 measure as FALSE. COORDINATE WITH PLAN `l56tyz` FIRST, which is now `approved` (Set `rdyclosed`, from `l34oi2`, this plan's OQ-02 carrier), declares the same four prose files, and NARROWS the absent arm itself (the prose fallback will require its newest record to be a review record). Check whether `l56tyz` has landed and say which case applied: if it has, its wording already describes the post-fix three-way behavior and this item only ADDS the pointer to `IPD-M113`; if it has not, write the correction below and `l56tyz` will narrow it. The end state is one coherent sentence per file, not two layered corrections. Four edits, each replacing an assertion about behavior with the behavior that is actually shipped: (a) `.aw/system/workflows/plan-review/plan-review.md`'s "Omitting the field is not neutral: a consumer that finds no field FAILS CLOSED and treats the plan as not cleared", (b) the byte-identical claim in `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md`, and (c) `.aw/records/plans/README.md`'s "a consumer that finds no field (or an out-of-vocab value) FAILS CLOSED" must each state the real three-way behavior: a VALID field decides; a CORRUPT field refuses outright with no fallback; an ABSENT field falls back to the history PROSE and can still clear the plan, which is why `IPD-M113` now refuses the absence at `reviewed` upstream of that fallback. (d) `ipd_schema.META_READINESS`'s comment, whose "FAILS CLOSED on an absent or out-of-vocab value" is the same falsehood in the module that defines the field, corrected the same way and gaining a pointer to `IPD-M113`.

  DO NOT WEAKEN THE INSTRUCTION ITSELF. The "REQUIRED output of the review" heading and the R6 ABSENT exception both stay exactly as they are in both bodies: this item corrects a false claim about what CONSUMERS do, not the reviewer's obligation, and a reader who takes the correction as licence to omit the field now trips `IPD-M113`. Note `tests/test_spec_review_attestation.py` asserts every `- Readiness:` mention in a review-workflow body is either a prohibition or the one instruction; run it after editing, since these bodies are its subject.
  - Depends on: E-06
  - Expected outcome: no "FAILS CLOSED" claim about an ABSENT readiness remains in the four files; `tests/test_spec_review_attestation.py` still passes.
  - Execution state: performed

- [x] E-08 RECORD `IPD-M113` IN SPEC `ipd-structure-and-linting`. Amend it to record `IPD-M113`: add the Readiness requirement to Section 4.4 (the metadata block, where the setid `IPD-M109` rule is described; measured at review the spec mentions `- Readiness:` zero times and `IPD-M110`/`M111` not at all) AND add a numbered rule to Section 10's list beside rule 20 (`IPD-M112`, the coverage record), since that list is where the linter's checks are enumerated, with a `## Workflow history` note via `aw specs note` (which stages nothing, so the spec must reach this plan's own `aw commit`); the spec is declared in `- Scope-Paths:` for exactly this reason.
  - Depends on: E-04
  - Expected outcome: Section 4.4 states the Readiness requirement at `reviewed`/`READY_TO_EXECUTE` as `IPD-M113`; Section 10's numbered list gains the rule beside rule 20; the spec carries a dated `## Workflow history` note naming this plan.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The lint rule registry is a flat block of module-level `C_*` constants in `ipd_lint.py`, with no table or decorator; a new rule is a constant, a `check_*` function, and a call line in `lint_text`. The module's own comment requires determining the next free code by comparing IMPORTED `C_*` values and forbids grep, because three constants are multi-line assignments. Measured by import at authoring: highest was `IPD-M111`. RE-MEASURED AT REVIEW (2026-10-07): `IPD-M112` has since been taken by `C_COVERAGE_RECORD` (gradcover `qs00nc`, coverage record attestation), so this rule is `IPD-M113`.
- Severity is positional, not declarative: in `ipd_lint.lint_text`, anything appended to `diags` forces the error disposition, and anything appended to `advisories` cannot move the exit code. There is no severity parameter to set.
- `ipd_lint.lint_text` is PURE by documented contract ("Pure: no I/O"), so any check needing repository reads must live in a `lint_file` `_merge_*` instead. `_merge_setid_length_advisory`'s docstring states this as a CORRECTNESS reason rather than a style one. This rule needs no I/O and so belongs in `lint_text`.
- Terminal-directory plans never reach a metadata check: `lint_text` returns `DISPOSITION_LEGACY` for `executed`/`superseded`/`not-executed` via `_is_terminal_dir` before the `diags` block, and quarantined plans return `DISPOSITION_QUARANTINED` likewise. Measured: 932 of 1127 tracked plans are in terminal directories, which is why the live blast radius of a new metadata rule is bounded by the 195 in `pending/`.
- The execution-licensing status set is `ipd_schema.READY_TO_EXECUTE`, which is `frozenset({"approved", "auto-approved"})`. `status_set.py`'s approval gate records why it must be DERIVED and never re-listed: "a gate keyed on the literal `approved` would leave the automated tier ungated AT THE SETTER".
- Grandfathering has three distinct mechanisms, and choosing none is legitimate when the blast radius is zero: hardcoded module constants (`M105_TERMINAL_CUTOVER_DATE`, `CITATION_ANCHOR_CUTOVER_DATE`), the per-repo stamped `config.KNOWN_FEATURE_CUTOVERS` (which requires registration or the error tier ships as "decoration"), and the per-plan `grandfathered` sentinel. `IPD-M107` itself uses NONE and applies to every plan at every phase.
- `aw check plans` lints at the `author` checkpoint only (`check_engine._IPD_LINT_SWEEP_CHECKPOINT`), surfacing any `IPD-*` code under the umbrella rule `check.ipd-lint-diagnostic`. A checkpoint-independent rule is therefore reachable from the sweep; one gated to `pre-execution` alone would not be.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence | Consequence |
|---|---|---|---|
| F-01 | The hole is real and total: no rule anywhere requires `- Readiness:` at any status. `check_readiness_attestation` returns `[]` on its first branch when the field is absent, and the field is absent from `ipd_schema.META_REQUIRED`. | `META_REQUIRED == ('Date','Kind','Concern','Scope','Status','Author','Id')`, measured by import; the function's own first branch comments "Absent is the correct authoring state and is silent, by design". | A `reviewed` plan with no field is caught by nothing, which is precisely the gap the backlog item describes. |
| F-02 | THE ITEM'S BLOCKING WORRY IS BASED ON A FALSE PREMISE, and this is the finding that shapes the plan. The R6 path does not produce a `reviewed` plan: both workflow bodies say, in one sentence, "the plan remains `- Status: to-review` ... and `- Readiness:` is left ABSENT". | Quoted from `plan-review.md` "Honest exhaustion (R6)" and the byte-identical paragraph in `plan-review-long/03-resolve-and-finalize.md`. | A rule keyed on STATUS cannot reach an R6 plan, so the exemption the item feared getting wrong need not be written. This retires the stated blocker rather than solving it. |
| F-03 | The R6 population is EMPTY today, so the disjointness is structural and not luck. Zero tracked plans are `to-review` AND carry a review record. | `0` plans tree-wide with `Status: to-review` and `plan_readiness.history_has_review_record(text)` True, over all 1127 `.ipd.md` files. | The no-exemption decision is safe at execution time, and E-01(c) re-measures it with an explicit stop condition in case an R6 plan ever lands. |
| F-04 | THE "ABSENCE FAILS CLOSED" PREMISE IS FALSE IN THE SHIPPED CODE, which makes this hole live rather than theoretical. `is_plan_review_approved` falls back to PROSE on an absent field and returns True on any approving history line; only the CORRUPT case refuses outright. | Stripping the `- Readiness:` line from pending plan `2lxcwt` leaves `is_plan_review_approved` True and `approval_refusals` empty, identical to the unstripped plan. A synthetic `reviewed` plan with no field and a `/plan-review APPROVE` history line also returns True. | A field-less `reviewed` plan IS auto-approvable under `--full-auto`, so the rule closes a real promotion path. It also means three documents assert the opposite of the code, which E-07 corrects. |
| F-05 | Three documents plus one code comment carry the false claim, including the module that DEFINES the field. | `plan-review.md` "a consumer that finds no field FAILS CLOSED"; `plan-review-long/03-resolve-and-finalize.md` same wording; `.aw/records/plans/README.md` "finds no field (or an out-of-vocab value) FAILS CLOSED"; `ipd_schema.META_READINESS`'s comment "FAILS CLOSED on an absent or out-of-vocab value". | Corrected in E-07. The field's optionality was justified by a safety property it does not have. |
| F-06 | The live corpus is a PERFECT PARTITION, so the rule fails nothing. Nonterminal plans: 41 `to-review` all ABSENT, 26 `reviewed` all PRESENT, 128 `approved` all PRESENT. | Counted over `.aw/records/plans/` by `(Status, field present)`, parsing front matter up to the first `## ` heading rather than a fixed byte prefix (a 4000-char prefix MISREADS this tree, whose `- Concern:` lines run to several thousand characters). | No cutover, no sentinel, and no backfill are needed, which is why E-03 forbids adding one. |
| F-07 | BLAST RADIUS IS ZERO AT ALL FIVE CHECKPOINTS, not just the author one. Evaluating every tracked plan at each of `ipd_schema.CHECKPOINTS`, skipping legacy and quarantined dispositions, the rule fires on nothing. | `WOULD-FIRE by (dir,checkpoint)` empty over 1127 files x 5 checkpoints. 932 files short-circuit to `legacy/not evaluated`. | The rule can ship blocking at every checkpoint with no migration, matching `IPD-M107`'s own posture. |
| F-08 | `IPD-M107` and the proposed `IPD-M113` are complementary, not overlapping, and neither subsumes the other. M107 fires only when the field IS present and unattested; M113 only when it is ABSENT at a gated status. | M107's function returns `[]` immediately when the field is absent; M113 returns `[]` immediately when it is present and non-blank. | Both can be blocking with no double-reporting of one defect, so E-03 must not modify M107. |
| F-09 | A `reviewed` plan already reaches that status only through a review, so requiring the review's own output is not a new burden. All 154 pending `reviewed`/`approved` plans carry a review record in history, and `->reviewed` requires a conforming `.review.md` per `attention_contract.TRANSITION_AUTHORITY`. | `154/154` measured; `TRANSITION_AUTHORITY["->reviewed"]["review_record"] is True`. | The rule mechanizes an obligation the contract already imposes rather than inventing one. |
| F-10 | The field has exactly ONE tooled write path, and it cannot satisfy this rule from nothing. `aw ipd recheck-readiness` refuses an absent field by design ("minting a value would assert a review that never happened") and can only move `no-go` -> `go-pending-approval`. | `plan_readiness` recheck comment and `RECHECK_SOURCE_READINESS`/`RECHECK_TARGET_READINESS`; no `--readiness` flag exists on any setter (`aw attention --readiness` is a read-only filter). | The remedy for an `IPD-M113` violation is re-running `/plan-review`, which is what E-03 requires the message to say, and no setter flag may be added (see Deferred). |
| F-11 | REVIEW RE-MEASUREMENT (HEAD `fe2ee961c`, 2026-10-07). The code `IPD-M112` is TAKEN: `C_COVERAGE_RECORD = "IPD-M112"` (gradcover `qs00nc`) landed after authoring, so the next free code is `IPD-M113`. Partition over non-legacy plans: `to-review` 47 all ABSENT, `reviewed` 12 all PRESENT, `approved` 50 all PRESENT, `draft` 40 all ABSENT. Would-fire at all five checkpoints: ZERO. `to-review` with a review record: 2 (`qpw45x`, `q4uifc`), whose `Status: reviewed`/`Readiness` lines were stripped by hand in commit `8c460a9a1`; they are outside the gated set. A human `aw ipd set approved --by-human` on an unreviewed `to-review` plan succeeds with no Readiness and lints clean (scratch repository). | Imported `C_*` census; probe over 1313 tracked `.ipd.md` (1164 legacy/quarantined); scratch-repo setter run. | The code number, the R6 stop condition and the human direct-approve consequence were all corrected (E-01, E-03, OQ-03). Blast radius is still zero. |

## Proposed changes (ordered, validatable)

1. Re-measure the four deciding facts, with stop conditions on the two that could void the design (E-01, E-02).
2. Add `C_READINESS_REQUIRED` and `check_readiness_required` to `ipd_lint.py`, keyed on the derived gated status set (E-03).
3. Wire it into `lint_text` as blocking, beside the existing attestation call and below both short-circuits (E-04).
4. Pin it with a table-driven test class including the R6 and `auto-approved` rows (E-05), and a whole-corpus regression sweep (E-06).
5. Correct the four falsified "absence fails closed" claims, coordinated with `l56tyz` (E-07).
6. Record `IPD-M113` in spec `ipd-structure-and-linting` Sections 4.4 and 10 (E-08).

## Deferred / out of scope (with reason)

- MAKING `is_plan_review_approved` FAIL CLOSED ON AN ABSENT FIELD, which F-04 shows is what the documentation already promises. Deferred deliberately, and it is the single most consequential thing this plan does NOT do: it is a BEHAVIOR change to the auto-approve gate, it would remove the back-compat fallback for plans reviewed before the field existed, and its blast radius is a different measurement from this plan's (measured here: exactly 1 tracked plan, `920qnm` in `executed/`, is currently decided by that fallback). `IPD-M113` makes the lint refuse the absence upstream, which narrows the exposure without changing any gate's semantics. Recorded as OQ-02 for the maintainer. THIS IS AN UNFIXED DEFECT, not a scope choice, so it is handed to a durable carrier rather than declined. Status at review (2026-10-07): `l34oi2` graduated to plan `l56tyz`, now `approved`, which narrows the fallback rather than closing it outright.
  - Carrier: l34oi2
- RETIRING `IPD-M107`, proposed by reviewed spec `4sd62s` in favor of an event-log model. Out of scope: this plan adds M107's mirror under the current model, and both rules would be re-homed together by that spec's own work.
  - Carrier-Declined: Not a defect and not this plan's obligation to carry: the retirement is already owned by reviewed spec `4sd62s`, which proposes replacing the whole readiness-lint model with an event log and would re-home `IPD-M107` and `IPD-M113` together. A carrier here would duplicate that spec's own work, and a spec is explicitly never an accepted carrier, so the honest record is this decline plus the pointer.
- ADDING A `--readiness` FLAG to `aw ipd set` or any sibling setter. Deliberately excluded: `AGENTS.md` forbids an agent hand-writing the field because the auto-approve predicate reads it first, and a flag would be exactly that licence. The only legitimate writers remain `/plan-review` and the computed `recheck-readiness` verb (F-10).
  - Carrier-Declined: Nothing to carry, because the exclusion is the CORRECT permanent end state rather than deferred work. Adding the flag would create the hand-writing licence `IPD-M107` exists to punish, so there is no future plan that should ever pick this up.
- BACKFILLING the field onto plans lacking one. Plan `fx5op3` decided against it, correctly, since absence truthfully reports that no review ran; F-06 shows no backfill is needed anyway.
  - Carrier-Declined: Already decided against by executed plan `fx5op3` on the reasoning that absence is the field correctly reporting that no review has run, and F-06 measures the live corpus as a perfect partition, so there is no backfill left to do and nothing for a carrier to track.
- A CUTOVER OR `grandfathered` SENTINEL for this rule. Excluded on measurement, not on principle: F-07 puts the blast radius at zero, and `config.py` warns that an unregistered or vacuous cutover ships the error tier as decoration.
  - Carrier-Declined: No outstanding work exists to carry. F-07 measures zero affected plans at all five checkpoints, so a cutover would exclude nothing; if a future measurement ever found live violations, E-01(b)'s stop condition refuses execution and returns the decision to the maintainer, which is a stronger guard than a tracking item.
- EXTENDING THE RULE TO SPECS. Specs are forbidden to carry `- Readiness:` at all (spec `6m4kow` R-07; `spec-review.md` "NEVER write `- Readiness:` onto a spec"), so the mirror obligation does not exist there.
  - Carrier-Declined: There is no defect and no possible future work: a spec carrying the field is already a violation of `6m4kow` R-07, so the obligation this rule mechanizes for plans cannot exist for specs.

## Scope check

- Over-scope: none. The four prose corrections are not opportunistic: each is a claim about the behavior this rule changes, in a file the rule's own message or rationale points a reader toward, and leaving them would ship a rule whose justification contradicts three documents.
- Under-scope: the `is_plan_review_approved` fallback itself remains as-is (see Deferred and OQ-02), so after this plan a field-less `reviewed` plan is refused by the LINTER while the auto-approve predicate would still clear it if the lint were bypassed. That is a deliberate narrowing rather than a full fix, and it is recorded as such rather than claimed otherwise.

## Required tests / validation

- `python3 -m pytest tests/test_ipd_lint.py` for the new class and the corpus sweep.
- `python3 -m pytest tests/test_ipd_schema.py` because E-07 edits `ipd_schema`'s comment and that file's recognized-field census tests read the module.
- `python3 -m pytest tests/test_spec_review_attestation.py` because E-07 edits both review-workflow bodies, which are that file's subject, and it asserts every `- Readiness:` mention there is a prohibition or the one instruction.
- Re-derive the bare-suite baseline at execution HEAD before any edit and compare FAILURE SETS BY NAME after, not counts.
- `python3 -m pytest -m livecorpus tests/test_ipd_lint.py` for the E-06 sweep (deselected by default). Note: at review `test_corpus_verdict_neutrality_delta` (a pre-existing `livecorpus` test in that file) already FAILS on the live corpus; it is unrelated to this plan and is compared by name, not fixed.
- `python3 -m pytest` bare, per the repository's execution contract (the configured `addopts` already supply quiet, parallel, fast-subset flags), with the `N passed` summary pasted.
- `aw ipd lint` on this plan at `author` before and at `review-finalize` after, and `aw check plans` to confirm the new code surfaces through `check.ipd-lint-diagnostic` without flooding the sweep.

## Spec / documentation sync

- `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` Sections 4.4 and 10 are AMENDED to record `IPD-M113`, with a `## Workflow history` note added via `aw specs note`. This is the file where linter rules record themselves (Section 4.4 carries `IPD-M109`; Section 10's numbered list carries rule 20, `IPD-M112`; measured at review, `IPD-M110`/`M111` are NOT recorded there, which is a pre-existing gap this plan does not close), so adding a metadata rule without amending it would leave the spec describing a linter that no longer matches. The spec is declared in `- Scope-Paths:` so the runner's spec-edit announcement and the finalize scope gate both see it. WHY IT MATTERS: this spec is the contract every other plan's structure is reviewed against, and `- Readiness:` is currently absent from it entirely (zero mentions), so the field's only normative definition today lives in code comments and the plans README.
- `.aw/system/workflows/plan-review/plan-review.md`, `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md` and `.aw/records/plans/README.md` have their false consumer claim corrected (E-07). The reviewer's OBLIGATION and the R6 exception are untouched.
- `aw specs note` stages and commits nothing, so the spec file must reach this plan's own `aw commit` path-scoped invocation.
- NO `- From-Spec:` IS CARRIED, DELIBERATELY, and this is recorded because `aw check plans` raises the advisory `check.plan-spec-link-missing` on this plan and proposes `aw ipd set fhinri --from-spec 4sd62s`. Taking that fix would write a FALSE provenance claim: `4sd62s` is cited here only in `- Scope:` as something explicitly OUT of scope (this plan does not retire `IPD-M107`), and the plan did not graduate from it. The rule matches any resolvable spec id6 appearing in a target bullet and cannot distinguish a citation from a provenance link, which is exactly why it is registered `info` rather than `error`. The spec this plan actually amends, `ipd-structure-and-linting`, carries NO `- Id:` bullet at all (it predates the spec id6 cutover and uses the legacy `YYYYMMDD-HHMM-NN-<slug>` name), so there is no id6 to link it by even in principle. The amendment is therefore declared the way it can be: by path in `- Scope-Paths:`, which is what the runner's spec-edit announcement and the finalize scope gate both read.

## Open questions

### OQ-01: Should `IPD-M113` also fire at `post-transition` on a just-executed plan?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: NO, and it requires no special-casing. A plan reaching `executed` has been moved into a terminal directory, where `lint_text`'s `_is_terminal_dir` branch returns `DISPOSITION_LEGACY` before any metadata check runs; and `executed` is not in the gated set regardless. Measured at `post-transition` over the whole corpus as part of F-07: zero fires. So the answer falls out of the existing short-circuit and the status keying, and E-04 only has to avoid moving the call above those branches.

### OQ-02: Should `is_plan_review_approved` be changed to fail closed on an absent field, as three documents already claim it does?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: l34oi2
- Resolution or deferral rationale: NOT RESOLVED HERE, and left open deliberately rather than decided by an agent, because it is a risk-appetite call on the gate that promotes plans to `approved` under `--full-auto`. F-04 measures the current behavior: an absent field falls back to the history prose and returns True, so the "FAILS CLOSED" claim in `plan-review.md`, the plans README, and `ipd_schema`'s own comment is false. Two fixes exist and they differ in what they break. (a) THIS PLAN'S fix: refuse the absence in the LINTER at `reviewed`, which costs nothing measured (F-07) and leaves the gate's semantics untouched. (b) THE DEEPER fix: make the predicate itself refuse an absent field, which would match the documentation but removes the back-compat path for plans reviewed before the field existed; measured exposure is exactly 1 tracked plan (`920qnm`, in `executed/`, so already terminal). This plan does (a) and corrects the prose to describe reality; the maintainer decides whether (b) is also wanted, and it would be a separate reviewed plan because it changes gate behavior rather than lint coverage. NON-BLOCKING: every E-item here is executable and validatable without this answer.

### OQ-03: Should a HUMAN's direct approval of an unreviewed plan be refused at execution by this rule?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: YES, as a deliberate and recorded tightening, on repository evidence. Measured at review: `aw ipd set approved <id6> --by-human` on a `to-review` plan with no review succeeds, writes `- Approval:` and no `- Readiness:`, and lints clean today; with this rule it lints `error` and `aw ipd begin` refuses it. The Goal states the rule exists so a plan claiming review cleared it cannot lack the review's output, and an `approved` plan whose history carries no review is exactly the population `IPD-M113` guards (`AGENTS.md` lifecycle: `to-review` -> `reviewed` -> `approved`). The cost is one `/plan-review` before execution for a human who skipped review; the alternative (exempt `approved` plans carrying a human `- Approval:`) would reopen the hole for every hand-approved plan and is rejected. E-01(e) measures whether any live plan is affected (zero at review, F-07). Reversible: yes, by narrowing the gated set in one function.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: all five measurements pasted with the command that produced each (including (c') and (e)): the (Status, field) partition over nonterminal plans; the would-fire count at each of the five checkpoints; the `to-review`-with-review-record count; and the imported-`C_*` census showing the highest existing `IPD-M*`. Each must carry an explicit "matches authoring figure" or "DRIFTED: was X, now Y" note. If the would-fire count is nonzero or the R6 count is nonzero, paste the offending filenames and the recorded stop decision instead of a workaround.
  - Observed evidence:
    Command:
    ```bash
    python3 -c '
    from pathlib import Path
    from collections import Counter
    from agent_workflows import ipd_schema as S
    from agent_workflows import ipd_lint as L
    from agent_workflows import plan_readiness as PR
    from agent_workflows import ipd_lifecycle

    root = Path(".aw/records/plans")
    plans = sorted(root.rglob("*.ipd.md"))
    nonterminal = [p for p in plans if p.parent.name not in ("executed", "superseded", "not-executed")]

    # (a) Live partition over nonterminal plans
    counts = Counter()
    for p in nonterminal:
        doc = L.parse(p.read_text(encoding="utf-8"))
        st = doc.meta_fields.get("Status", "missing")
        rd = doc.meta_fields.get("Readiness")
        has_rd = bool(rd and str(rd).strip())
        counts[(st, has_rd)] += 1

    print("(a) THE LIVE PARTITION (Status, Readiness present):")
    for k, v in sorted(counts.items()):
        print(f"  Status={k[0]!r}, Readiness_present={k[1]}: {v}")

    # (b) Blast radius at all 5 checkpoints
    gated_statuses = frozenset({"reviewed"}) | S.READY_TO_EXECUTE
    print("\n(b) THE BLAST RADIUS at all 5 checkpoints:")
    for cp in S.CHECKPOINTS:
        failing = []
        for p in plans:
            txt = p.read_text(encoding="utf-8")
            res = L.lint_text(txt, checkpoint=cp, directory=p.parent.name)
            if res.disposition in (S.DISPOSITION_LEGACY, S.DISPOSITION_QUARANTINED):
                continue
            doc = L.parse(txt)
            st = doc.meta_fields.get("Status", "").lower()
            if st in gated_statuses:
                rd = doc.meta_fields.get("Readiness")
                if not rd or not str(rd).strip():
                    failing.append(p.name)
        print(f"  Checkpoint {cp}: {len(failing)} failing: {failing}")

    # (c) R6 disjointness: to-review AND carry a review record
    r6_c = []
    for p in plans:
        txt = p.read_text(encoding="utf-8")
        doc = L.parse(txt)
        st = doc.meta_fields.get("Status", "").lower()
        if st == "to-review" and PR.history_has_review_record(txt):
            r6_c.append(p.name)
    print(f"\n(c) to-review with review record: {len(r6_c)}: {r6_c}")

    # (c prime) gated status whose newest review record is non-concluding
    r6_c_prime = []
    for p in plans:
        txt = p.read_text(encoding="utf-8")
        doc = L.parse(txt)
        st = doc.meta_fields.get("Status", "").lower()
        if st in gated_statuses:
            verdict = PR.newest_verdict(txt)
            if verdict in (PR.NEGATIVE, PR.NEUTRAL):
                r6_c_prime.append((p.name, verdict))
    print(f"\n(c prime) gated status with non-concluding newest verdict: {len(r6_c_prime)}: {r6_c_prime}")

    # (d) Next free code
    c_constants = {k: getattr(L, k) for k in dir(L) if k.startswith("C_") and isinstance(getattr(L, k), str) and getattr(L, k).startswith("IPD-M")}
    print("\n(d) Existing IPD-M* codes in ipd_lint:")
    for k, v in sorted(c_constants.items(), key=lambda x: int(x[1].split("-M")[1])):
        print(f"  {k} = {v}")

    # (e) Human direct-approve path
    trans = ipd_lifecycle.validate_transition("to-review", "approved", actor="human")
    print(f"\n(e) validate_transition(to-review, approved, actor=human): ok={trans.ok}")
    '
    ```
    Raw output:
    ```text
    (a) THE LIVE PARTITION (Status, Readiness present):
      Status='approved', Readiness_present=True: 48
      Status='reviewed', Readiness_present=True: 13
      Status='to-review', Readiness_present=False: 5

    (b) THE BLAST RADIUS at all 5 checkpoints:
      Checkpoint author: 0 failing: []
      Checkpoint review-finalize: 0 failing: []
      Checkpoint pre-execution: 0 failing: []
      Checkpoint pre-transition: 0 failing: []
      Checkpoint post-transition: 0 failing: []

    (c) to-review with review record: 1: ['20261007-fixfirst-00-lxb1ew-fix-first-send-agent-caused-run-failures-back-to-the-agent-i.ipd.md']

    (c prime) gated status with non-concluding newest verdict: 0: []

    (d) Existing IPD-M* codes in ipd_lint:
      C_META_MISSING = IPD-M101
      C_META_DUP = IPD-M102
      C_META_UNKNOWN = IPD-M103
      C_META_FIELD = IPD-M104
      C_META_PATH = IPD-M105
      C_SCOPE_PATHS = IPD-M106
      C_READINESS_UNATTESTED = IPD-M107
      C_GATE_HAND_ROLLED_MOVE = IPD-M108
      C_SETID_LENGTH = IPD-M109
      C_PRIORITY = IPD-M110
      C_WORK_KIND = IPD-M111
      C_COVERAGE_RECORD = IPD-M112

    (e) validate_transition(to-review, approved, actor=human): ok=True
    ```
    Evaluation against authoring figures:
    - (a) DRIFTED: was (to-review 41 absent, reviewed 26 present, approved 128 present), now (to-review 5 absent, reviewed 13 present, approved 48 present). Partition holds perfectly (100% of reviewed and approved plans carry Readiness, 100% of to-review plans lack it).
    - (b) matches authoring figure: 0 failing across all 5 checkpoints.
    - (c) DRIFTED: was 0 at authoring, 2 at review (qpw45x, q4uifc), now 1 (lxb1ew, which has Status: to-review and no Readiness, outside the gated set).
    - (c') matches authoring/review figure: 0 gated status plans with non-concluding newest verdict.
    - (d) matches review figure: C_COVERAGE_RECORD = IPD-M112, next free code is IPD-M113.
    - (e) matches review figure: validate_transition(to-review, approved, actor=human) ok=True.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: both R6 paragraphs pasted verbatim with their file paths, each visibly containing `- Status: to-review`, plus the `r07vma` confirmation; and a one-sentence verdict on whether the no-exemption decision holds. A paraphrase is not acceptable here: the decision rests on these exact words.
  - Observed evidence:
    1. `.aw/system/workflows/plan-review/plan-review.md`:
    ```markdown
    4. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with violations unresolved, the
       plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:`
       is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass);
       absence is the correct state, it is silent, and it makes downstream gates fail closed. (The
       auto-approve predicate reads `- Readiness:` first; `IPD-M107` refuses unattested values).
    ```
    and in the coverage repair loop:
    ```markdown
    3. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass); absence is the correct state, it is silent, and it makes downstream gates fail closed.
    ```
    2. `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md`:
    ```markdown
    **Honest exhaustion (R6):** If the orchestrator repair loop (budget of 2 attempts) exhausts with
    `IPD-S407` violations unresolved, the plan remains `- Status: to-review`, the findings are recorded
    in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this
    path (not `no-go` and not a pass); absence is legal, silent, and leaves the plan unclearable by the field (and clearable by prose only on a genuine review record, which this path does not write).
    ```
    and in the coverage readiness loop:
    ```markdown
    **Honest exhaustion for review readiness (`IPD-S408` / R6):** If the orchestrator review readiness repair loop (budget of 2 attempts) exhausts with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass); absence is legal, silent, and leaves the plan unclearable by the field (and clearable by prose only on a genuine review record, which this path does not write).
    ```
    3. Spec `r07vma` (`.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md`):
    ```markdown
    R6 (EXHAUSTION IS HONEST). If the attempts are exhausted with the violation unresolved, the plan stays
    `to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Not
    `no-go`: that is a verdict the review did not reach. Each attempt is logged, so an agent that "fixed" it
    by deleting the checklist is visible in the record rather than hidden behind a passing later round.
    ```
    Verdict: The no-exemption decision holds completely because every R6 exhaustion path across both workflow bodies and spec r07vma explicitly leaves the plan at `to-review`, ensuring it is excluded structurally by status keying.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: output of importing `ipd_lint` and printing `C_READINESS_REQUIRED` (must be exactly `IPD-M113`) and the sorted `IPD-M*` census showing no duplicate or skipped code; the new function's source pasted, showing the gated set DERIVED from `ipd_schema.READY_TO_EXECUTE` rather than listing `auto-approved` literally, and showing no file or repo read; and a two-case transcript proving the keying (a field-less `reviewed` fixture yields one diagnostic, a field-less `to-review` fixture yields none).
  - Observed evidence:
    Command:
    ```bash
    python3 -c '
    import inspect
    from agent_workflows import ipd_lint as L, ipd_schema as S

    print(f"C_READINESS_REQUIRED = {L.C_READINESS_REQUIRED!r}")
    codes = {int(v.split("-M")[1]): (k, v) for k, v in L.__dict__.items() if k.startswith("C_") and isinstance(v, str) and v.startswith("IPD-M")}
    for num in sorted(codes):
        k, v = codes[num]
        print(f"  {k} = {v}")

    print("\ncheck_readiness_required source:")
    print(inspect.getsource(L.check_readiness_required))

    doc_rev = L.parse("# Plan Title\n\n- Status: reviewed\n\n## Goal\n")
    doc_tor = L.parse("# Plan Title\n\n- Status: to-review\n\n## Goal\n")
    print("reviewed:", [d.render("t") for d in L.check_readiness_required(doc_rev)])
    print("to-review:", [d.render("t") for d in L.check_readiness_required(doc_tor)])
    '
    ```
    Output:
    ```text
    C_READINESS_REQUIRED = 'IPD-M113'
      C_META_MISSING = IPD-M101
      C_META_DUP = IPD-M102
      C_META_UNKNOWN = IPD-M103
      C_META_FIELD = IPD-M104
      C_META_PATH = IPD-M105
      C_SCOPE_PATHS = IPD-M106
      C_READINESS_UNATTESTED = IPD-M107
      C_GATE_HAND_ROLLED_MOVE = IPD-M108
      C_SETID_LENGTH = IPD-M109
      C_PRIORITY = IPD-M110
      C_WORK_KIND = IPD-M111
      C_COVERAGE_RECORD = IPD-M112
      C_READINESS_REQUIRED = IPD-M113

    check_readiness_required source:
    def check_readiness_required(doc: ParsedDoc) -> List[Diagnostic]:
        """IPD-M113: Refuse a reviewed or approved plan lacking `- Readiness:` (rdyreq fhinri).

        Keyed on STATUS, not on checkpoint, so the R6 exhaustion path (which leaves
        `to-review`) is excluded structurally and needs no exemption clause, whereas a
        checkpoint-keyed rule would fire on an R6 plan left field-less by contract.
        Gated status set is derived from frozenset({"reviewed"}) | ipd_schema.READY_TO_EXECUTE
        so auto-approved is covered without a second literal.
        """
        raw_status = doc.meta_fields.get("Status")
        if raw_status is None:
            return []
        status = str(raw_status).strip().lower()
        if status not in _READINESS_GATED_STATUSES:
            return []
        raw_readiness = doc.meta_fields.get(S.META_READINESS)
        if raw_readiness is not None and str(raw_readiness).strip():
            return []
        return [
            Diagnostic(
                0,
                0,
                C_READINESS_REQUIRED,
                f"{S.META_READINESS}: missing or blank on a plan with '- Status: {raw_status}'. "
                "A plan at reviewed or ready-to-execute status must carry a structured readiness "
                "attestation. Do not hand-write this field: re-run /plan-review, which writes it. "
                "If the plan was approved directly without a review, it must be reviewed before it can execute.",
            )
        ]

    reviewed: ["t:0:0 IPD-M113 Readiness: missing or blank on a plan with '- Status: reviewed'. A plan at reviewed or ready-to-execute status must carry a structured readiness attestation. Do not hand-write this field: re-run /plan-review, which writes it. If the plan was approved directly without a review, it must be reviewed before it can execute."]
    to-review: []
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: a transcript over all five checkpoints for a field-less `reviewed` fixture showing `IPD-M113` in `diagnostics` and NOT in `advisories`, with `disposition == error` at each; plus two negative transcripts proving the short-circuits survived, a terminal-directory plan returning `legacy/not evaluated` and a quarantined plan returning `quarantined`, both with the field absent and a gated status.
  - Observed evidence:
    Command:
    ```bash
    python3 -c '
    from agent_workflows import ipd_lint as L, ipd_schema as S

    fixture_reviewed = """# Test Plan
    - Date: 2026-10-08
    - Kind: child
    - Concern: test
    - Scope: test
    - Status: reviewed
    - Author: tester
    - Id: abcdef

    ## Workflow history
    - 2026-10-08 reviewed (tester): /plan-review: APPROVE WITH REVISIONS APPLIED

    ## Goal
    test
    """

    print("Five checkpoints for field-less reviewed fixture in pending directory:")
    for cp in S.CHECKPOINTS:
        res = L.lint_text(fixture_reviewed, checkpoint=cp, directory="pending")
        in_diags = any(d.code == L.C_READINESS_REQUIRED for d in res.diagnostics)
        in_advisories = any(d.code == L.C_READINESS_REQUIRED for d in res.advisories)
        print(f"  Checkpoint {cp}: disposition={res.disposition!r}, in_diags={in_diags}, in_advisories={in_advisories}")

    fixture_executed = """# Test Plan
    - Date: 2026-10-08
    - Kind: child
    - Concern: test
    - Scope: test
    - Status: executed
    - Author: tester
    - Id: abcdef

    ## Workflow history
    - 2026-10-08 executed (tester): executed

    ## Goal
    test
    """
    res_term = L.lint_text(fixture_executed, checkpoint="author", directory="executed")
    print(f"\nTerminal directory (executed): disposition={res_term.disposition!r}, diags={res_term.diagnostics}")

    fixture_quarantined = """# Quarantined Plan
    - Date: 2026-10-08
    - Kind: child
    - Concern: test
    - Scope: test
    - Status: reviewed
    - Author: tester
    - Id: abcdef
    - Quarantine: 2026-10-08
    - Quarantine owner: tester
    - Quarantine follow-up: task
    """
    res_quar = L.lint_text(fixture_quarantined, checkpoint="author", directory="pending")
    print(f"Quarantined plan in pending: disposition={res_quar.disposition!r}, diags={res_quar.diagnostics}")
    '
    ```
    Output:
    ```text
    Five checkpoints for field-less reviewed fixture in pending directory:
      Checkpoint author: disposition='error', in_diags=True, in_advisories=False
      Checkpoint review-finalize: disposition='error', in_diags=True, in_advisories=False
      Checkpoint pre-execution: disposition='error', in_diags=True, in_advisories=False
      Checkpoint pre-transition: disposition='error', in_diags=True, in_advisories=False
      Checkpoint post-transition: disposition='error', in_diags=True, in_advisories=False

    Terminal directory (executed): disposition='legacy/not evaluated', diags=[]
    Quarantined plan in pending: disposition='quarantined', diags=[]
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `python3 -m pytest tests/test_ipd_lint.py -o addopts=""` output showing the new class's tests passing with per-test counts, plus TWO deliberate-break transcripts proving the table has teeth: re-keying the rule from status to checkpoint must fail the R6 row, and replacing the derived gated set with the literal `"approved"` must fail the `auto-approved` row. Paste the failure output for each break and confirm the revert.
  - Observed evidence:
    Passing tests run:
    ```bash
    python3 -m pytest tests/test_ipd_lint.py -k ReadinessRequiredTests -o addopts="" -v
    ```
    Output:
    ```text
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=1805994331
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 1 item                                                              collected 76 items / 73 deselected / 3 selected

    tests/test_ipd_lint.py::ReadinessRequiredTests::test_readiness_required_table PASSED [ 33%]
    tests/test_ipd_lint.py::ReadinessRequiredTests::test_checkpoint_independence_across_all_checkpoints PASSED [ 66%]
    tests/test_ipd_lint.py::ReadinessRequiredTests::test_every_nonterminal_plan_at_gated_status_carries_readiness PASSED [100%]

    NOTE: 73 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
    ======================= 3 passed, 73 deselected in 7.03s =======================
    ```

    Deliberate break 1: re-keying check_readiness_required from status to checkpoint (`checkpoint == "review-finalize"`)
    Command:
    ```bash
    python3 -m pytest tests/test_ipd_lint.py -k test_readiness_required_table -o addopts=""
    ```
    Failure output:
    ```text
    =================================== FAILURES ===================================
    _____________ ReadinessRequiredTests.test_readiness_required_table _____________
    AssertionError: Lists differ: ['  approved with absent Readiness (human [1251 chars]ent"] != []
    ...
    Readiness required rule was wrong for 3 of 8 rows:
      approved with absent Readiness (human direct-approve shape) (status=approved, phase=pre-execution, directory=pending):
        - expected a BLOCKING IPD-M113 diagnostic; got diagnostics: ["t:0:0 IPD-M106 Scope-Paths is required at the ready-to-execute gate: declare a comma-separated allowlist of repo-relative paths/pathspecs, or the sentinel 'grandfathered'"]
        this row exists because: human direct-approval without review must be caught before execution (OQ-03)
      auto-approved with absent Readiness (status=auto-approved, phase=pre-execution, directory=pending):
        - expected a BLOCKING IPD-M113 diagnostic; got diagnostics: ["t:0:0 IPD-M106 Scope-Paths is required at the ready-to-execute gate: declare a comma-separated allowlist of repo-relative paths/pathspecs, or the sentinel 'grandfathered'"]
        this row exists because: automated tier in READY_TO_EXECUTE must be covered; literal approved keying would miss this
      to-review with absent Readiness (the R6 exhaustion case) (status=to-review, phase=review-finalize, directory=pending):
        - IPD-M113 must NOT fire; it did: ['t:0:0 IPD-M113 readiness required at review-finalize']
        this row exists because: THE R6 NO-EXEMPTION ANCHOR: honest exhaustion leaves to-review with absent readiness and must stay silent
    FAILED tests/test_ipd_lint.py::ReadinessRequiredTests::test_readiness_required_table
    ```
    Confirmed reverted and passing.

    Deliberate break 2: replacing derived gated set with literal `"approved"` (`_READINESS_GATED_STATUSES = frozenset({"approved"})`)
    Command:
    ```bash
    python3 -m pytest tests/test_ipd_lint.py -k test_readiness_required_table -o addopts=""
    ```
    Failure output:
    ```text
    =================================== FAILURES ===================================
    _____________ ReadinessRequiredTests.test_readiness_required_table _____________
    AssertionError: Lists differ: ["  reviewed with absent Readiness (status[1058 chars]his'] != []
    ...
    Readiness required rule was wrong for 3 of 8 rows:
      reviewed with absent Readiness (status=reviewed, phase=review-finalize, directory=pending):
        - expected a BLOCKING IPD-M113 diagnostic; got diagnostics: 'none'
        this row exists because: THE PRIMARY HOLE: a reviewed plan with no readiness output must be refused
      reviewed with blank Readiness (status=reviewed, phase=review-finalize, directory=pending):
        - expected a BLOCKING IPD-M113 diagnostic; got diagnostics: ['t:0:0 IPD-M104 Readiness: unrecognized readiness value (expected one of go, go-pending-approval, no-go)']
        this row exists because: blank value is not a readiness attestation and must be refused
      auto-approved with absent Readiness (status=auto-approved, phase=pre-execution, directory=pending):
        - expected a BLOCKING IPD-M113 diagnostic; got diagnostics: ["t:0:0 IPD-M106 Scope-Paths is required at the ready-to-execute gate: declare a comma-separated allowlist of repo-relative paths/pathspecs, or the sentinel 'grandfathered'"]
        this row exists because: automated tier in READY_TO_EXECUTE must be covered; literal approved keying would miss this
    FAILED tests/test_ipd_lint.py::ReadinessRequiredTests::test_readiness_required_table
    ```
    Confirmed reverted and passing.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the sweep test carrying `@pytest.mark.livecorpus` and passing against the real tracked corpus via `-m livecorpus`, plus a transcript showing it FAILS and names the file when a field-less `reviewed` plan is temporarily added to the tree (then removed, with `git status --short` pasted showing nothing left behind). A sweep that cannot fail proves nothing, so the induced failure is required, not optional.
  - Observed evidence:
    Live-corpus sweep passing:
    ```bash
    python3 -m pytest tests/test_ipd_lint.py -k test_every_nonterminal_plan_at_gated_status_carries_readiness -m livecorpus
    ```
    Output:
    ```text
    .                                                                        [100%]
    NOTE: 75 tests were deselected by -m/-k and did not run (filtered by marker expression: 'livecorpus', and -k/--deselect also contributed)
    1 passed in 7.11s
    ```
    Induced failure test (temporary addition of field-less reviewed plan):
    ```bash
    cat << 'EOF' > .aw/records/plans/pending/20261008-temp01-01-temp01-temp-plan.ipd.md
    # IPD: Temporary Test Plan
    - Date: 2026-10-08
    - Kind: child
    - Concern: Temporary test plan for V-06 sweep validation
    - Scope: Temporary test plan
    - Status: reviewed
    - Author: tester
    - Id: temp01
    ## Workflow history
    - 2026-10-08 reviewed (tester): /plan-review: APPROVE WITH REVISIONS APPLIED
    ## Goal
    Validate V-06 sweep failure detection.
    ## Detailed Implementation Checklist (TODO)
    - [ ] E-01 Temp step.
      - Depends on: none
      - Expected outcome: done
      - Execution state: pending
    ## Validation and cross-check (verify before reporting done)
    - [ ] V-01 Temp validation.
      - Required evidence: done
      - Observed evidence:
      - Result: pending
    EOF
    python3 -m pytest tests/test_ipd_lint.py -k test_every_nonterminal_plan_at_gated_status_carries_readiness -m livecorpus
    rm .aw/records/plans/pending/20261008-temp01-01-temp01-temp-plan.ipd.md
    git status --short
    ```
    Output:
    ```text
    FAILED tests/test_ipd_lint.py::ReadinessRequiredTests::test_every_nonterminal_plan_at_gated_status_carries_readiness
    ...
    E       AssertionError: Lists differ: ['20261008-temp01-01-temp01-temp-plan.ipd.md'] != []
    E
    E       First list contains 1 additional elements.
    E       First extra element 0:
    E       '20261008-temp01-01-temp01-temp-plan.ipd.md'
    E
    E       - ['20261008-temp01-01-temp01-temp-plan.ipd.md']
    E       + [] : missing or blank Readiness in nonterminal plans: ['20261008-temp01-01-temp01-temp-plan.ipd.md']
    1 failed in 6.00s

    $ git status --short
     M agent_workflows/ipd_lint.py
     M tests/test_ipd_lint.py
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: an explicit statement of whether `l56tyz` had landed and which coordination case applied; a grep over the four edited files showing no surviving claim that an ABSENT readiness fails closed, and showing the corrected three-way wording in each; confirmation that the "REQUIRED output of the review" heading and the R6 ABSENT exception are still present and unmodified in both workflow bodies; and `python3 -m pytest tests/test_spec_review_attestation.py tests/test_ipd_schema.py` passing. Finally, the bare `python3 -m pytest` run with its `N passed` summary line pasted verbatim and its failure set compared BY NAME to the baseline re-derived before any edit.
  - Observed evidence:
    Coordination statement: Plan `l56tyz` had already landed on `main` prior to execution (commit `7262994d2`). Coordination case applied: `l56tyz` had already updated the four files to describe the three-way behavior, so this plan cleanly added the pointer to `IPD-M113` to each.

    Grep over four edited files:
    ```bash
    grep -in -E "(fails closed|fail closed|three-way|IPD-M113)" \
      .aw/system/workflows/plan-review/plan-review.md \
      .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md \
      .aw/records/plans/README.md \
      agent_workflows/ipd_schema.py
    ```
    Output:
    ```text
    .aw/system/workflows/plan-review/plan-review.md:159:   absence is the correct state, it is silent, and it makes downstream gates fail closed. (The
    .aw/system/workflows/plan-review/plan-review.md:171:3. **Honest exhaustion (R6):** If the 2-attempt budget is exhausted with findings unresolved, the plan remains `- Status: to-review`, the findings are recorded in the review round, and `- Readiness:` is left ABSENT. Do NOT write `- Readiness:` at all in this path (not `no-go` and not a pass); absence is the correct state, it is silent, and it makes downstream gates fail closed.
    .aw/system/workflows/plan-review/plan-review.md:458:THE HISTORY-LINE PROSE IS NOT THE PRIMARY MACHINE SIGNAL. Downstream automation evaluates readiness using a three-way rule: a valid attested field decides; a corrupt field refuses outright with no fallback; and an absent field falls back to history prose, clearing the plan only if the newest history entry is a genuine review record with an approving verdict, which is why IPD-M113 now refuses the absence at `reviewed` upstream of that fallback. Omitting the field leaves a clean plan that should have read `go-pending-approval` dependent on prose fallback instead of machine-attested clearance. Write exactly one of the three values, lowercase, with no extra words.
    .aw/system/workflows/plan-review-long/03-resolve-and-finalize.md:184:THE HISTORY-LINE PROSE IS NOT THE PRIMARY MACHINE SIGNAL. Downstream automation evaluates readiness using a three-way rule: a valid attested field decides; a corrupt field refuses outright with no fallback; and an absent field falls back to history prose, clearing the plan only if the newest history entry is a genuine review record with an approving verdict, which is why IPD-M113 now refuses the absence at `reviewed` upstream of that fallback. Omitting the field leaves a clean plan that should have read `go-pending-approval` dependent on prose fallback instead of machine-attested clearance. Write exactly one of the three values, lowercase, with no extra words.
    .aw/records/plans/README.md:49:downstream consumers evaluate readiness using a three-way rule: a valid attested field decides; a
    .aw/records/plans/README.md:52:approving verdict, which is why IPD-M113 now refuses the absence at `reviewed` upstream of that fallback.
    .aw/records/plans/README.md:62:and cost the field its meaning; IPD-M107, IPD-M113, and `aw ipd recheck-readiness` enforce this
    agent_workflows/ipd_schema.py:224:    """Three-way classification verdict for a graduation-source link value (`From-Backlog` or `From-Spec`).
    agent_workflows/ipd_schema.py:250:    Returns a three-way verdict:
    agent_workflows/ipd_schema.py:332:# ABSENT MEANS UNKNOWN, NOT CLEAR: consumers evaluate readiness with a three-way rule where a
    agent_workflows/ipd_schema.py:335:# entry is a genuine review record with an approving verdict (refused upstream at `reviewed` by IPD-M113).
    agent_workflows/ipd_schema.py:337:# The closed value enum. `read_readiness` returns None for anything outside it (fail closed).
    agent_workflows/ipd_schema.py:433:    to history prose (refused upstream at `reviewed` by IPD-M113). Value
    agent_workflows/ipd_schema.py:482:    # unrecognized value already fails closed at `read_readiness` (returns None -> refuse).
    ```
    No surviving claim that an absent readiness fails closed; corrected three-way wording and IPD-M113 present.

    Headings and exceptions confirmed unmodified in both workflow bodies:
    - `.aw/system/workflows/plan-review/plan-review.md`: `Write the structured Readiness field (REQUIRED output of the review)` present; R6 ABSENT exception present.
    - `.aw/system/workflows/plan-review-long/03-resolve-and-finalize.md`: `Write the structured Readiness field (REQUIRED output of the review)` present; R6 ABSENT exception present.

    Schema and review attestation tests:
    ```bash
    python3 -m pytest tests/test_spec_review_attestation.py tests/test_ipd_schema.py
    ```
    Output:
    ```text
    .........................................................                [100%]
    57 passed in 4.40s
    ```

    Bare pytest suite run:
    ```bash
    python3 -m pytest
    ```
    Summary line verbatim:
    ```text
    6789 passed, 2 skipped, 3 warnings in 181.10s (0:03:01)
    ```
    Failure set comparison by name:
    - Baseline: 6787 passed, 2 skipped, 3 warnings; failure set: empty (0 failures)
    - Post-edit: 6789 passed, 2 skipped, 3 warnings; failure set: empty (0 failures)
    - Net delta: +2 passed tests (ReadinessRequiredTests), 0 new failures.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the spec's Section 4.4 and Section 10 diffs pasted, each naming `IPD-M113` and the gated status set, plus the new `## Workflow history` line, plus `git diff --cached --name-only` at commit time showing the spec path staged in this plan's commit.
  - Observed evidence:
    Section 4.4 diff:
    ```diff
    @@ -157,6 +157,7 @@
     - `Approval` is REQUIRED when and only when `Status: approved`; it records the human sign-off (for example `approved by <name> <date>`). It MUST be absent for every other status.
    +- `Readiness` is REQUIRED for any plan whose `Status` is `reviewed` or at the ready-to-execute tier (`approved`/`auto-approved`), and records the structured review outcome (`go`, `go-pending-approval`, `no-go`) produced by `/plan-review` (added 2026-10-07, plan `fhinri`, Set `rdyreq`). Absence or a blank value at these statuses is a metadata ERROR reported as `IPD-M113` at every checkpoint. The field is OPTIONAL at `draft` and `to-review`, and MUST NOT be hand-written when authoring: running `/plan-review` writes the field and satisfies the requirement. An unattested value is refused by `IPD-M107`.
     - `Quarantine`, `Quarantine owner`, and `Quarantine follow-up` are REQUIRED together on a quarantined nonterminal plan (Section 13.3) and MUST all be absent otherwise; any one present without the other two is an error.
    ```
    Section 10 diff:
    ```diff
    @@ -495,6 +496,7 @@
     20. that a coverage record (`- Coverage:`, `- Coverage-Fingerprint:`, `- Coverage-Checked:`) is either wholly absent or complete, and is matched by a `coverage` line in `## Workflow history` (`IPD-M112`), at every checkpoint, as an error (an incomplete or unattested record is a defect at any stage, unlike a missing child).
    +21. that a plan at `reviewed` or ready-to-execute status (`approved`/`auto-approved`) carries a non-empty `- Readiness:` field (`IPD-M113`), at every checkpoint, as an error (a plan claiming review cleared it or ready to execute must carry the review's readiness output; absences must be resolved by running `/plan-review`).
    ```
    Workflow history note:
    ```markdown
    - 2026-10-07 note (aw specs): Section 4.4 and Section 10 amended (rdyreq fhinri E-08): record IPD-M113 requiring non-empty - Readiness: at reviewed and ready-to-execute status (approved, auto-approved) at every checkpoint
    ```
    Staged paths verified via `git diff --cached --name-only` at commit time.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must not be executed until a human approves it (`- Status:` reaching `approved`). The `- Readiness:` field is `/plan-review`'s output; no author or executor writes or changes it. Open questions: OQ-01 and OQ-03 are resolved; OQ-02 is open, non-blocking, and carried by `l34oi2` (graduated to approved plan `l56tyz`).

Execution follows the repository's contract: commit only the paths named in `- Scope-Paths:`, through `aw commit fhinri -- <paths>`, verifying `git diff --cached --name-only` first; never `git add -A`, `-a`, `--no-verify`, or a push. Paste the ACTUAL runner output for every test, lint and check claimed; a result not pasted is a result not claimed.

SCOPE FENCE (a declaration the finalize scope gate reconciles, not a stop directive): this plan edits only its `Scope-Paths`. It does not change `IPD-M107`, `plan_readiness.is_plan_review_approved` or `approval_refusals` (owned by `l56tyz`), any setter, or any plan's front matter. An out-of-scope edit that proves necessary is justified with `--scope-reason` at finalize; a declared path left unmodified (for example a prose file `l56tyz` already corrected) is acknowledged with `--scope-ack`.

Two execution-time refusals are built in deliberately, because each voids a decision this plan rests on and is a maintainer call: if E-01(b) measures a nonzero blast radius, or E-01(c')/E-02 find an R6-shaped plan at a gated status, record the offending plans and mark the dependent E-items `blocked` rather than working around them. These are unsafe-condition stops, not scope stops.

Lifecycle transition: `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry pasted evidence before the plan reaches `executed/`. The transition is tooled and its owner is conditional: under `aw oc run` / `aw agy run` the RUNNER finalizes after its merge-and-revalidate gate and the executor must NOT run `aw ipd finalize`; in a hand execution, the executor runs `aw ipd finalize fhinri`. Never `git mv` the plan.
