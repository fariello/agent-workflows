# IPD: Reconcile the long-form Live-artifact rubric bullet to the verbatim-copy parity shape

- Date: 2026-10-11
- Kind: child
- Concern: The `Live-artifact success criteria vs. stable code facts (re-derivation convention)` bullet in `review-rubric.md` `## A. Plan completeness` is the ONLY bullet in that section carried as a one-sentence POINTER, while its four siblings are byte-identical VERBATIM copies of the single-file `plan-review.md` rubric G bullets, so the two plan-review variants silently disagree on how a rubric bullet is kept in parity.
- Scope: Replace the long-form pointer bullet with a byte-identical copy of the single-file bullet, and convert its pointer-shape test into a byte-identity parity test. No other bullet, workflow body, spec, or production code changes.
- Scope-Paths: .aw/system/workflows/plan-review-long/review-rubric.md, tests/test_v_item_evidence_durability.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: vbz06g
- Set: vbz06g
- Order: 1
- Highest E allocated: 03
- Author: opencode/claude-opus
- Id: xl1iko

## Workflow history

- 2026-10-12 draft (opencode/claude-opus): created.
- 2026-10-12 to-review (opencode/claude-opus): authored from backlog vbz06g; findings measured at HEAD 1feee61ca; review-ready.

## Goal

Make the long-form rubric carry the `Live-artifact` re-derivation bullet in the same verbatim-copy shape every other bullet in `## A. Plan completeness` uses, and pin that shape with a byte-identity parity test, so the two plan-review variants follow ONE parity convention for rubric bullets and any future drift in this bullet fails the suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reconcile the bullet shape

- [ ] E-01 In `.aw/system/workflows/plan-review-long/review-rubric.md` `## A. Plan completeness`, replace the single line beginning `- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**` (the pointer bullet, which contains `(see ../plan-review/plan-review.md per the parity note in plan-review-long.md)`) with the EXACT bullet text from `.aw/system/workflows/plan-review/plan-review.md` `### G. Plan executability` that begins with the same bold prefix, copied byte-for-byte as it stands AT EXECUTION TIME (re-read it; do not paste the text quoted in this plan). Keep its position: it stays first among the bold rubric bullets, immediately before `- **Canonical no-error-added proof shape`. Touch no other line.
  - Depends on: none
  - Expected outcome: the long-form bullet, sliced from its bold prefix to the next `\n- **`, is byte-identical to the single-file bullet sliced the same way; the bullet no longer contains the pointer parenthetical; the other four bullets in `## A. Plan completeness` are unchanged.
  - Execution state: pending

### Task group 2: pin the reconciled shape

- [ ] E-02 In `tests/test_v_item_evidence_durability.py`, rewrite `TestVItemEvidenceDurability.test_long_form_plan_review_evidence_durability_parity` so it asserts the VERBATIM-COPY shape instead of the pointer shape: slice the `Live-artifact` bullet out of `review-rubric.md` `## A. Plan completeness` and out of `plan-review.md` `### G. Plan executability` (both via `support.section(..., bullet_prefix, "\n- **", anchored=False)`, the same slicing the module already uses) and `assertEqual` the two slices, plus assert every entry of `SINGLE_FILE_ANCHORS` is present in the long-form slice. Remove the now-false `assertNotIn("Criteria counting **stable code facts**", ...)` "must remain a pointer" assertion and the `LONG_FORM_POINTER_ANCHORS` constant (no other module references it; re-derive that by search at execution). Update the test's docstring and the module docstring's parity wording to say the long-form carries a verbatim copy. Keep the module's existing P16 exemption paragraph, which still applies (it reads workflow bodies, not `agent_workflows/*.py`).
  - Depends on: E-01
  - Expected outcome: the test passes against the reconciled files and FAILS if either copy of the bullet is edited without the other, if the long-form bullet is deleted, or if the long-form bullet reverts to the pointer form.
  - Execution state: pending

### Task group 3: validate

- [ ] E-03 Take a bare `python3 -m pytest` baseline in this lane BEFORE E-01, then after E-02 run the targeted modules and a bare full suite, and perform the three source-file mutation proofs named in `## Required tests / validation`, restoring each with an empty `git diff --stat` for the mutated path.
  - Depends on: E-02
  - Expected outcome: targeted modules pass; each mutation makes the parity test fail and is restored; the full-suite set of failing node ids after the change is a subset of the baseline set.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE TWO PLAN-REVIEW VARIANTS ARE KEPT IN DELIBERATE PARITY. `plan-review-long.md` says `the two are kept in deliberate parity`; `plan-review.md` says `The two variants are otherwise kept in deliberate parity.`
- THE MEASURED PARITY SHAPE FOR A RUBRIC BULLET IN THIS PAIR IS A VERBATIM COPY. Measured at HEAD 1feee61ca by slicing each `- **<name>:**` bullet in `review-rubric.md` `## A. Plan completeness` and comparing it to the same-named bullet in `plan-review.md` `### G. Plan executability`: `Canonical no-error-added proof shape ...`, `Runtime-demonstration reachability ...`, `Right-sizing and conceptual density (per E-item)`, and `Maintainer sizing signals` are byte-identical; `Live-artifact success criteria ...` is NOT (1150 characters in the single-file body versus 355 in the long-form pointer). Both sections list the same five bullets in the same order.
- SPEC `ipd-structure-and-linting` Section 3 (`## 3. Normative language and canonical source of truth`) states `Duplicated rubric or template content MUST have a parity test.` A verbatim copy therefore obliges a parity test, which E-02 supplies.
- WORKFLOW-BODY CONTENT TESTS sit inside GUIDING_PRINCIPLES P16's narrow exception (the text is the artifact under test); precedent: `tests/test_plan_review_feasibility_rule.py`, `tests/test_v_item_demonstration_reachability.py`, and `tests/test_v_item_evidence_durability.py` itself, whose module docstring records that exemption.
- The two rubric surfaces DO NOT share section letters: in `review-rubric.md`, `## G.` is UX and accessibility and the plan-executability bullets live in `## A. Plan completeness` (recorded in `tests/test_v_item_demonstration_reachability.py` `test_long_form_review_rubric_reachability_rule_parity` docstring). Tests must slice `## A. Plan completeness`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | The divergence this backlog item tracks is real and isolated to ONE bullet. Of the five bold rubric bullets in `review-rubric.md` `## A. Plan completeness`, four are byte-identical copies of their `plan-review.md` rubric G counterparts and one, `Live-artifact ...`, is a 355-character pointer whose single-file counterpart is 1150 characters. | slice comparison measured at HEAD 1feee61ca over `.aw/system/workflows/plan-review/plan-review.md` and `.aw/system/workflows/plan-review-long/review-rubric.md` |
| F-02 | The two shapes came from two plans that each believed they were following convention. `vtup6x` (executed, commit `b3afea162`) wrote the pointer, reasoning that `tests/test_plan_review_feasibility_rule.py` enforces a pointer for this pair. `9aprci` (executed, commit `70266f371`) measured verbatim copy as the house style, followed it, and filed this backlog item for the divergence. `9aprci`'s review (F-11) recorded that `vtup6x`'s claim is wrong about the FILES: the feasibility test's long-form target is `03-resolve-and-finalize.md`, which carries the full text AND adds a pointer sentence; no shipped test enforced pointer-only for `review-rubric.md`. | `.aw/records/plans/executed/20260929-nos070-01-vtup6x-*.ipd.md` E-02 and OQ-03; `.aw/records/plans/executed/20260929-vreach-01-9aprci-*.ipd.md` F-06, F-11, OQ-02, and V-02 observed evidence naming `vbz06g` |
| F-03 | The pointer shape is currently pinned by a test, so the reconciliation must change that test, not just the prose. `test_long_form_plan_review_evidence_durability_parity` asserts the pointer literals (`LONG_FORM_POINTER_ANCHORS`) and `assertNotIn("Criteria counting **stable code facts**", ...)`, i.e. it FAILS on a verbatim copy. | `tests/test_v_item_evidence_durability.py` `TestVItemEvidenceDurability.test_long_form_plan_review_evidence_durability_parity` |
| F-04 | No existing test compares the full text of ANY review-rubric bullet to its single-file twin; the sibling parity tests assert only anchor phrases in `## A. Plan completeness`. So the four verbatim bullets can already drift beyond their anchors undetected; this plan closes that only for the bullet it touches (see Deferred). | `tests/test_plan_review_feasibility_rule.py` `test_no_error_added_proof_shape_in_rubrics`; `tests/test_v_item_demonstration_reachability.py` `test_long_form_review_rubric_reachability_rule_parity` |
| F-05 | No pending plan declares either path this plan edits, so there is no sequencing edge to declare. | search of `.aw/records/plans/pending/` for `review-rubric.md` and `test_v_item_evidence_durability` at HEAD 1feee61ca returned only this plan |

## Proposed changes (ordered, validatable)

1. Replace the long-form pointer bullet with a byte-identical copy of the single-file bullet (E-01, F-01).
2. Rewrite the long-form parity test to assert byte identity and the single-file anchors, removing the pointer-only assertions that would fail on the copy (E-02, F-03).
3. Validate with a same-lane baseline, targeted tests, mutation proofs, and the full suite (E-03).

## Deferred / out of scope (with reason)

- Full-text byte-identity parity tests for the OTHER four `## A. Plan completeness` bullets (F-04). Out of scope: those bullets are already in the verbatim shape, so they are not part of the divergence this item reconciles, and their parity tests belong to modules owned by other plans (`tests/test_plan_review_feasibility_rule.py`, `tests/test_v_item_demonstration_reachability.py`). Widening this plan to rewrite them is opportunistic scope.
  - Carrier-Declined: No obligation is left outstanding by this plan. Their anchor-level parity tests exist and satisfy the spec's "MUST have a parity test"; strengthening them to byte identity is an optional improvement nobody has requested, and filing it here would assert a gap this item does not define.
- Converting the four verbatim bullets to pointers instead (the opposite reconciliation). Rejected, not deferred; see OQ-01.
  - Carrier-Declined: A rejected alternative carries no outstanding work.

## Scope check

- Over-scope: none. One workflow body bullet and one test function (plus its module's docstring and one constant), both paths declared in `- Scope-Paths:`.
- Under-scope: no `CHANGELOG.md` entry, deliberately: the change aligns internal reviewer-facing prose and adds no behaviour a CLI user observes, matching `9aprci` (`70266f371`), which edited this same file without a CHANGELOG line. No spec is amended (see Spec sync).

## Required tests / validation

- Baseline: a bare `python3 -m pytest` in this lane BEFORE the first edit, recording the set of failing node ids (no suite total is written here; a plan-recorded figure cannot distinguish an added test from a merge).
- `python3 -m pytest tests/test_v_item_evidence_durability.py tests/test_v_item_demonstration_reachability.py tests/test_plan_review_feasibility_rule.py` after E-02, all passing.
- Three SOURCE-FILE mutation proofs, each restored with an empty `git diff --stat -- <path>`: (a) revert the long-form bullet to its pre-E-01 pointer text; (b) change one word in the long-form bullet only; (c) change one word in the single-file `plan-review.md` bullet only. Each must make `test_long_form_plan_review_evidence_durability_parity` FAIL. Mutation (c) touches an undeclared path TEMPORARILY and leaves no diff; it is not a scope edit.
- A bare `python3 -m pytest` after E-02, judged on the delta of failing node ids against the baseline.

## Spec / documentation sync

- N/A, no spec amended. Spec `ipd-structure-and-linting` Section 3 already requires a parity test for duplicated rubric content; this plan conforms to it (E-02) rather than changing it. Spec `20260726-1340-01-ipd-spec` only points at plan-review Rubric G for this convention (history line `2026-09-24 amended (tgop8e)`), which is the single-file body this plan does not change.
- `review-rubric.md` is a workflow body shipped verbatim by the installer; no managed block restates its bullets, so nothing generated needs regeneration.

## Open questions

### OQ-01: Reconcile toward the verbatim copy, or convert the siblings to pointers?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM REPOSITORY EVIDENCE: verbatim copy. (1) Four of five bullets in the section are already byte-identical copies (F-01), so changing one bullet is the least disruptive reconciliation. (2) The opposite direction would break shipped tests: `test_no_error_added_proof_shape_in_rubrics` and `test_long_form_review_rubric_reachability_rule_parity` assert full-rule anchor phrases (`drift_exit_code`, `check_engine.rule_spec`, `unsatisfiable`, `name the code path`, `UNDER-SCOPE`) inside `review-rubric.md` `## A. Plan completeness`, which a one-sentence pointer would not carry. (3) `vtup6x`'s premise for the pointer, that a shipped test enforced a pointer for this pair, was measured wrong by `9aprci` F-11 (F-02). (4) The single-source-of-truth objection to duplication is answered the way spec `ipd-structure-and-linting` Section 3 prescribes, by a parity test, and E-02's byte-identity test is stronger than the pointer test it replaces. Reversible: yes.

### OQ-02: Should the parity test assert byte identity or only anchor phrases?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED: byte identity, plus the anchors. Anchor-only parity (the sibling modules' shape) lets the two copies drift outside their anchors (F-04), which is the silent drift the duplication rule exists to prevent; byte identity is the precise statement of "verbatim copy". The anchor assertions are kept so a failure message names which load-bearing phrase is missing. The cost, that any wording edit must touch both files, is the intended parity obligation.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff -- .aw/system/workflows/plan-review-long/review-rubric.md` showing exactly one removed line (the pointer bullet) and one added line (the full bullet), and paste the output of a one-off `python3 -c` (or heredoc) that slices the `- **Live-artifact` bullet to the next `\n- **` from both `review-rubric.md` and `plan-review.md` and prints `True` for equality, plus the list of bold bullet names in `review-rubric.md` `## A. Plan completeness` showing the same five names in the same order as before. All reachable by construction (diff, file content).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff -- tests/test_v_item_evidence_durability.py` showing the rewritten test with an equality assertion between the two slices and the removed pointer-only assertions, and paste the output of `rg -n LONG_FORM_POINTER_ANCHORS` across the repo showing no remaining reference. Then paste the ACTUAL output of `python3 -m pytest tests/test_v_item_evidence_durability.py tests/test_v_item_demonstration_reachability.py tests/test_plan_review_feasibility_rule.py` showing them passing. Reachable by construction (diff, search, test result).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste, for EACH of mutation proofs (a), (b), (c), the failing pytest output of `python3 -m pytest tests/test_v_item_evidence_durability.py` naming `test_long_form_plan_review_evidence_durability_parity`, followed by an empty `git diff --stat -- <mutated path>` after restoring. Paste the summary line and the failing node ids (if any) of the pre-edit baseline and of the post-change bare `python3 -m pytest`, and state that the post-change failing set is a subset of the baseline set. Reachable by construction (test results, diff).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING. One rubric bullet in the long-form `review-rubric.md` changes from a one-sentence pointer to a byte-identical copy of its single-file twin, matching the four sibling bullets, and its test changes from pinning the pointer to pinning byte identity. No production Python, spec, or other workflow body changes.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Two paths, both in `- Scope-Paths:`. Do NOT edit `.aw/system/workflows/plan-review/plan-review.md` (it is the source of the copy; mutation proof (c) touches it only temporarily and must leave an empty diff), do NOT change the other four bullets in `review-rubric.md`, and do NOT edit any plan under `.aw/records/plans/executed/`. If the work genuinely requires a path outside the fence, make the edit and justify it: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

HONESTY RULE, HARD MUST. When you report that tests passed, paste the ACTUAL runner output. Do not claim a run you did not perform.

COMMIT AND PUSH. Commit ONLY the declared paths, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set before committing.

LIFECYCLE TRANSITION. This plan MUST reach a terminal state. When executed by `aw oc run` or `aw agy run`, the RUNNER owns the transition and self-finalizes; when executed by hand, the EXECUTOR runs `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries `Result: pass` with concrete pasted evidence. Do NOT hand-roll a `git mv` into `.aw/records/plans/executed/`.
