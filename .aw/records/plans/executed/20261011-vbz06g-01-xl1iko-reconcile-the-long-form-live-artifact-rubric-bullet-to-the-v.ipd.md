# IPD: Reconcile the long-form Live-artifact rubric bullet to the verbatim-copy parity shape

- Date: 2026-10-11
- Kind: child
- Concern: The `Live-artifact success criteria vs. stable code facts (re-derivation convention)` bullet in `review-rubric.md` `## A. Plan completeness` is the ONLY bullet in that section carried as a one-sentence POINTER, while its four siblings are byte-identical VERBATIM copies of the single-file `plan-review.md` rubric G bullets, so the two plan-review variants silently disagree on how a rubric bullet is kept in parity.
- Scope: Replace the long-form pointer bullet with a byte-identical copy of the single-file bullet, and convert its pointer-shape test into a byte-identity parity test. No other bullet, workflow body, spec, or production code changes.
- Scope-Paths: .aw/system/workflows/plan-review-long/review-rubric.md, tests/test_v_item_evidence_durability.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: vbz06g
- Set: vbz06g
- Order: 1
- Highest E allocated: 03
- Author: opencode/claude-opus
- Id: xl1iko

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: xl1iko verified (set vbz06g, attempt 1).
- 2026-10-12 approved (aw set): status set to approved

- 2026-10-12 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003. Reviewed at HEAD f8d99c044. Byte-identity test and all mutation proofs demonstrated on in-memory copies (deleted bullet raises SectionBoundError, noted); mutation word pinned to a once-per-copy token; narrowed pytest runs use -o addopts=""; manifest-hash staleness and unrelated pointer recorded (F-06, F-07). Record: .aw/records/reviews/20261011-vbz06g-01-xl1iko-reconcile-the-long-form-live-artifact-rubric-bullet-to-the-v.review.md.
- 2026-10-12 draft (opencode/claude-opus): created.
- 2026-10-12 to-review (opencode/claude-opus): authored from backlog vbz06g; findings measured at HEAD 1feee61ca; review-ready.

## Goal

Make the long-form rubric carry the `Live-artifact` re-derivation bullet in the same verbatim-copy shape every other bullet in `## A. Plan completeness` uses, and pin that shape with a byte-identity parity test, so the two plan-review variants follow ONE parity convention for rubric bullets and any future drift in this bullet fails the suite.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: reconcile the bullet shape

- [x] E-01 In `.aw/system/workflows/plan-review-long/review-rubric.md` `## A. Plan completeness`, replace the single line beginning `- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**` (the pointer bullet, which contains `(see ../plan-review/plan-review.md per the parity note in plan-review-long.md)`) with the EXACT bullet text from `.aw/system/workflows/plan-review/plan-review.md` `### G. Plan executability` that begins with the same bold prefix, copied byte-for-byte as it stands AT EXECUTION TIME (re-read it; do not paste the text quoted in this plan). Keep its position: it stays first among the bold rubric bullets, immediately before `- **Canonical no-error-added proof shape`. Touch no other line.
  - Depends on: none
  - Expected outcome: the long-form bullet, sliced from its bold prefix to the next `\n- **`, is byte-identical to the single-file bullet sliced the same way; the bullet no longer contains the pointer parenthetical; the other four bullets in `## A. Plan completeness` are unchanged.
  - Execution state: performed

### Task group 2: pin the reconciled shape

- [x] E-02 In `tests/test_v_item_evidence_durability.py`, rewrite `TestVItemEvidenceDurability.test_long_form_plan_review_evidence_durability_parity` so it asserts the VERBATIM-COPY shape instead of the pointer shape: slice the `Live-artifact` bullet out of `review-rubric.md` `## A. Plan completeness` and out of `plan-review.md` `### G. Plan executability` (both via `support.section(..., bullet_prefix, "\n- **", anchored=False)`, the same slicing the module already uses) and `assertEqual` the two slices, plus assert every entry of `SINGLE_FILE_ANCHORS` is present in the long-form slice. Remove the now-false `assertNotIn("Criteria counting **stable code facts**", ...)` "must remain a pointer" assertion and the `LONG_FORM_POINTER_ANCHORS` constant (no other module references it; re-derive that by search at execution). Update the test's docstring and the module docstring's parity wording to say the long-form carries a verbatim copy. Keep the module's existing P16 exemption paragraph, which still applies (it reads workflow bodies, not `agent_workflows/*.py`).
  - Depends on: E-01
  - Expected outcome: the test passes against the reconciled files and FAILS if either copy of the bullet is edited without the other, if the long-form bullet is deleted (the slice then raises `support.SectionBoundError`, an error rather than an assertion failure, which still fails the test), or if the long-form bullet reverts to the pointer form. Demonstrated at review on in-memory copies with the same `support.section` slicing and assertions: HEAD pointer -> FAIL (6 anchors missing, unequal); reconciled -> PASS; one-word edit to the long-form copy only -> FAIL (unequal); one-word edit to the single-file copy only -> FAIL (unequal); long-form bullet deleted -> `SectionBoundError`.
  - Execution state: performed

### Task group 3: validate

- [x] E-03 Take a bare `python3 -m pytest` baseline in this lane BEFORE E-01, then after E-02 run the targeted modules and a bare full suite, and perform the three source-file mutation proofs named in `## Required tests / validation`, restoring each with an empty `git diff --stat` for the mutated path.
  - Depends on: E-02
  - Expected outcome: targeted modules pass; each mutation makes the parity test fail and is restored; the full-suite set of failing node ids after the change is a subset of the baseline set.
  - Execution state: performed

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
| F-05 | No pending plan declares either path this plan edits, so there is no sequencing edge to declare. | search of `.aw/records/plans/pending/` for `review-rubric.md` and `test_v_item_evidence_durability` at HEAD 1feee61ca returned only this plan; re-checked at review HEAD f8d99c044, same result |
| F-06 | The `.aw/system/managed-sections.json` `sha256` for `review-rubric.md` (and for `plan-review.md`) ALREADY differs from the file on disk, so earlier edits to these bodies (`9aprci`, `vtup6x`, `k6t24p`) also did not refresh it. This plan inherits that state and does not change it. | Review: manifest `d7fae7f1...` vs `sha256sum` `ec407cac...` for `review-rubric.md`; `7c986280...` vs `e9723a9e...` for `plan-review.md`, at HEAD f8d99c044 |
| F-07 | The other pointer in `plan-review-long.md` ("per the parity note above", the `Readiness` bullet) is about a different rule, so this reconciliation does not touch it. No generated command copy (`.opencode/`, `.claude/`) embeds the bullet. | Review search of `plan-review-long.md` for "parity note" and of `.opencode .claude .agents` for "Live-artifact success criteria" (no hits) |

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
- `python3 -m pytest -o addopts="" tests/test_v_item_evidence_durability.py tests/test_v_item_demonstration_reachability.py tests/test_plan_review_feasibility_rule.py` after E-02, all passing. This is a narrowed per-test view, so the repo contract's `-o addopts=""` form is used; the bare-suite rule governs the full runs below.
- Three SOURCE-FILE mutation proofs, each restored with an empty `git diff --stat -- <path>`: (a) revert the long-form bullet to its pre-E-01 pointer text; (b) change one word in the long-form bullet only; (c) change one word in the single-file `plan-review.md` bullet only. Use a word that occurs exactly once in each copy, such as `permitted` in "a test function name is permitted only as a non-binding pointer" (it occurred once in each copy at review), so the mutation cannot land outside the bullet. Each must make `test_long_form_plan_review_evidence_durability_parity` FAIL. Mutation (c) touches an undeclared path TEMPORARILY and leaves no diff; it is not a scope edit.
- A bare `python3 -m pytest` after E-02, judged on the delta of failing node ids against the baseline.

## Spec / documentation sync

- N/A, no spec amended. Spec `ipd-structure-and-linting` Section 3 already requires a parity test for duplicated rubric content; this plan conforms to it (E-02) rather than changing it. Spec `20260726-1340-01-ipd-spec` only points at plan-review Rubric G for this convention (history line `2026-09-24 amended (tgop8e)`), which is the single-file body this plan does not change.
- `review-rubric.md` is a workflow body shipped verbatim by the installer; no managed block restates its bullets, so nothing generated needs regeneration. The manifest hash is already stale for this file (F-06), and refreshing it is not this plan's concern.

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

- [x] V-01 validates E-01
  - Required evidence: paste `git diff -- .aw/system/workflows/plan-review-long/review-rubric.md` showing exactly one removed line (the pointer bullet) and one added line (the full bullet), and paste the output of a one-off `python3 -c` (or heredoc) that slices the `- **Live-artifact` bullet to the next `\n- **` from both `review-rubric.md` and `plan-review.md` and prints `True` for equality, plus the list of bold bullet names in `review-rubric.md` `## A. Plan completeness` showing the same five names in the same order as before. All reachable by construction (diff, file content).
  - Observed evidence:
    `git diff -- .aw/system/workflows/plan-review-long/review-rubric.md`:
    ```diff
    diff --git a/.aw/system/workflows/plan-review-long/review-rubric.md b/.aw/system/workflows/plan-review-long/review-rubric.md
    index f621a2f51..11f4895b0 100755
    --- a/.aw/system/workflows/plan-review-long/review-rubric.md
    +++ b/.aw/system/workflows/plan-review-long/review-rubric.md
    @@ -35,7 +35,7 @@ For an agent-executable plan (an IPD or similar with actionable steps), it must
     verification/cross-check checklist that maps 1:1 with concrete per-item evidence; a weak or
     absent verification checklist (one that could let an agent claim completion without doing every
     step) is an UNDER-SCOPE finding.
    -- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** A V-item demands the behaviour pinned plus the mechanism that pins it (re-derived at execution time); a collected test count is never the bar; a test name is a non-binding pointer only (see `../plan-review/plan-review.md` per the parity note in `plan-review-long.md`).
    +- **Live-artifact success criteria vs. stable code facts (re-derivation convention):** An `Expected outcome` or acceptance criterion that counts **live artifacts** (such as pending plans, open review findings, or stranded repository state) MUST state the required property and require re-derivation at execution time; a count measured at authoring belongs in the item's prose as context, never as the bar. Criteria counting **stable code facts** (schema keys, enum members) or an orchestrator counting its own declared children are EXEMPT, because these are fixed authored facts rather than drifting live populations. In contrast, a collected test count and a test function name are ARTIFACTS OF TEST ORGANIZATION, not stable authored facts; neither may serve as a V-item's bar (a test function name is permitted only as a non-binding pointer). A V-item must instead demand the behaviour pinned plus the mechanism that pins it, and must require re-derivation at execution time. (Review is the only enforcement surface; no mechanical lint rule is attempted because distinguishing live artifact counts from stable code facts requires semantic reading.)
     - **Canonical no-error-added proof shape vs. unsatisfiable exit-0 demands (evidence-feasibility convention):** When a plan demands proof that an advisory rule adds no error, the author must demand evidence that can actually be produced. The canonical proof requires two limbs:
       (a) a **registry severity assertion**, showing the rule id resolves through `check_engine.rule_spec` to the intended severity; and
       (b) a **gate-consequence measurement**, driving `artifact_core.drift_exit_code` with the finding list and pasting its return value as a contrastive pair--asserting the real finding list exits 1 (e.g. `drift_exit_code(drift) == 1` for `warning` or `error`) AND that the same finding list with its severity swapped to `info` exits 0 (e.g. `drift_exit_code([d._replace(severity="info") for d in drift]) == 0`). The pair is what localizes the exit code to the severity under test.
    ```
    One-off equality and ordered bold bullet check output:
    ```text
    $ python3 -c '
    from pathlib import Path
    import re
    from tests import support

    p_long = Path(".aw/system/workflows/plan-review-long/review-rubric.md").read_text(encoding="utf-8")
    p_single = Path(".aw/system/workflows/plan-review/plan-review.md").read_text(encoding="utf-8")

    sec_long = support.section(p_long, "## A. Plan completeness", "## ")
    sec_single = support.section(p_single, "### G. Plan executability", "## ")

    bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
    b_long = support.section(sec_long, bullet_prefix, "\n- **", anchored=False)
    b_single = support.section(sec_single, bullet_prefix, "\n- **", anchored=False)

    print("Equality:", b_long == b_single)

    bullets_long = re.findall(r"^- \*\*([^*]+)\*\*", sec_long, re.MULTILINE)
    print("Bullets in review-rubric.md ## A. Plan completeness:")
    for b in bullets_long:
        print(" -", b)
    '
    Equality: True
    Bullets in review-rubric.md ## A. Plan completeness:
     - Live-artifact success criteria vs. stable code facts (re-derivation convention):
     - Canonical no-error-added proof shape vs. unsatisfiable exit-0 demands (evidence-feasibility convention):
     - Runtime-demonstration reachability vs. unsatisfiable observation demands (reachability convention):
     - Right-sizing and conceptual density (per E-item):
     - Maintainer sizing signals:
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `git diff -- tests/test_v_item_evidence_durability.py` showing the rewritten test with an equality assertion between the two slices and the removed pointer-only assertions, and paste the output of `rg -n LONG_FORM_POINTER_ANCHORS` across the repo showing no remaining reference. Then paste the ACTUAL output of `python3 -m pytest -o addopts="" tests/test_v_item_evidence_durability.py tests/test_v_item_demonstration_reachability.py tests/test_plan_review_feasibility_rule.py` showing them passing. Reachable by construction (diff, search, test result).
  - Observed evidence:
    `git diff -- tests/test_v_item_evidence_durability.py`:
    ```diff
    diff --git a/tests/test_v_item_evidence_durability.py b/tests/test_v_item_evidence_durability.py
    index bbebdfdf1..ae305128f 100644
    --- a/tests/test_v_item_evidence_durability.py
    +++ b/tests/test_v_item_evidence_durability.py
    @@ -1,4 +1,7 @@
    -"""Tests for V-item evidence durability and parity rules (IPD vtup6x, set nos070; IPD 5q9a6a, set ezv744).
    +"""Tests for V-item evidence durability and verbatim-copy parity rules (IPD vtup6x, set nos070; IPD 5q9a6a, set ezv744; IPD xl1iko, set vbz06g).
    +
    +The long-form review-rubric.md carries a byte-identical verbatim copy of the
    +re-derivation convention bullet from plan-review.md.

     Exemption from source-text-pin prohibition:
     This module reads WORKFLOW BODIES and a SPEC, the artifacts under change, and no
    @@ -64,16 +67,6 @@ SINGLE_FILE_ANCHORS = [
         "Review is the only enforcement surface",
     ]

    -# Pointer anchors for the long-form parity rule:
    -LONG_FORM_POINTER_ANCHORS = [
    -    "Live-artifact success criteria vs. stable code facts (re-derivation convention):",
    -    "behaviour pinned plus the mechanism that pins it",
    -    "collected test count is never the bar",
    -    "../plan-review/plan-review.md",
    -    "per the parity note in `plan-review-long.md`",
    -]
    -
    -
     class TestVItemEvidenceDurability(unittest.TestCase):
         def test_single_file_plan_review_evidence_durability(self) -> None:
             """Assert single-file plan-review.md narrows the exemption and requires behaviour plus mechanism."""
    @@ -114,31 +107,36 @@ class TestVItemEvidenceDurability(unittest.TestCase):
             )

         def test_long_form_plan_review_evidence_durability_parity(self) -> None:
    -        """Assert review-rubric.md carries the parity pointer without duplicating the paragraph."""
    -        content = REVIEW_RUBRIC_FILE.read_text(encoding="utf-8")
    -        section_a = support.section(content, "## A. Plan completeness", "## ")
    +        """Assert review-rubric.md carries a byte-identical verbatim copy of the plan-review.md bullet."""
    +        content_long = REVIEW_RUBRIC_FILE.read_text(encoding="utf-8")
    +        section_a = support.section(content_long, "## A. Plan completeness", "## ")
    +
    +        content_single = PLAN_REVIEW_FILE.read_text(encoding="utf-8")
    +        section_g = support.section(content_single, "### G. Plan executability", "## ")

    -        # Locate the pointer bullet
             bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
    -        bullet_text = support.section(
    +        bullet_long = support.section(
                 section_a, bullet_prefix, "\n- **", anchored=False
             )
    +        bullet_single = support.section(
    +            section_g, bullet_prefix, "\n- **", anchored=False
    +        )
    +
    +        # 1. Assert byte-identical verbatim copy between long-form and single-file
    +        self.assertEqual(
    +            bullet_long,
    +            bullet_single,
    +            f"{REVIEW_RUBRIC_REL} bullet must be a byte-identical verbatim copy of {PLAN_REVIEW_REL}",
    +        )

    -        # Assert pointer trio and summary anchors are present in the long-form bullet
    -        for anchor in LONG_FORM_POINTER_ANCHORS:
    +        # 2. Assert semantic anchors are present in the long-form copy
    +        for anchor in SINGLE_FILE_ANCHORS:
                 self.assertIn(
                     anchor,
    -                bullet_text,
    -                f"Anchor '{anchor}' not found in pointer bullet of {REVIEW_RUBRIC_REL}",
    +                bullet_long,
    +                f"Anchor '{anchor}' not found in long-form bullet of {REVIEW_RUBRIC_REL}",
                 )

    -        # Confirm the long-form does NOT duplicate the full paragraph (remains a pointer)
    -        self.assertNotIn(
    -            "Criteria counting **stable code facts**",
    -            bullet_text,
    -            f"{REVIEW_RUBRIC_REL} must not duplicate the full normative paragraph from plan-review.md",
    -        )
    -
         def test_spec_section_5_4_evidence_reachability(self) -> None:
             """Assert spec Section 5.4 carries reachability rule and preserves linter boundary.
     ```
    Output of `rg -n LONG_FORM_POINTER_ANCHORS` across the repo:
    ```text
    $ rg -n LONG_FORM_POINTER_ANCHORS
    (exit code 1, 0 matches found)
    ```
    ACTUAL output of targeted pytest:
    ```text
    $ python3 -m pytest -o addopts="" tests/test_v_item_evidence_durability.py tests/test_v_item_demonstration_reachability.py tests/test_plan_review_feasibility_rule.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=280523531
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/xl1iko
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items

    tests/test_plan_review_feasibility_rule.py ....                          [ 40%]
    tests/test_v_item_evidence_durability.py ...                             [ 70%]
    tests/test_v_item_demonstration_reachability.py ...                      [100%]

    ============================== 10 passed in 0.34s ==============================
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste, for EACH of mutation proofs (a), (b), (c), the failing pytest output of `python3 -m pytest -o addopts="" tests/test_v_item_evidence_durability.py` naming `test_long_form_plan_review_evidence_durability_parity`, followed by an empty `git diff --stat -- <mutated path>` after restoring. Paste the summary line and the failing node ids (if any) of the pre-edit baseline and of the post-change bare `python3 -m pytest`, and state that the post-change failing set is a subset of the baseline set. Reachable by construction (test results, diff).
  - Observed evidence:
    Mutation proof (a) [revert long-form bullet to pre-E-01 pointer text]:
    ```text
    $ python3 -m pytest -o addopts="" tests/test_v_item_evidence_durability.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=1847836474
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/xl1iko
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_v_item_evidence_durability.py .F.                             [100%]

    =================================== FAILURES ===================================
    _ TestVItemEvidenceDurability.test_long_form_plan_review_evidence_durability_parity _

    self = <tests.test_v_item_evidence_durability.TestVItemEvidenceDurability testMethod=test_long_form_plan_review_evidence_durability_parity>

        def test_long_form_plan_review_evidence_durability_parity(self) -> None:
            """Assert review-rubric.md carries a byte-identical verbatim copy of the plan-review.md bullet."""
            content_long = REVIEW_RUBRIC_FILE.read_text(encoding="utf-8")
            section_a = support.section(content_long, "## A. Plan completeness", "## ")

            content_single = PLAN_REVIEW_FILE.read_text(encoding="utf-8")
            section_g = support.section(content_single, "### G. Plan executability", "## ")

            bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
            bullet_long = support.section(
                section_a, bullet_prefix, "\n- **", anchored=False
            )
            bullet_single = support.section(
                section_g, bullet_prefix, "\n- **", anchored=False
            )

            # 1. Assert byte-identical verbatim copy between long-form and single-file
    >       self.assertEqual(
                bullet_long,
                bullet_single,
                f"{REVIEW_RUBRIC_REL} bullet must be a byte-identical verbatim copy of {PLAN_REVIEW_REL}",
            )
    E       AssertionError: '- **Live-artifact success criteria vs. s[311 chars]d`).' != "- **Live-artifact success criteria vs. s[1106 chars]ng.)"
    E       Diff is 1512 characters long. Set self.maxDiff to None to see it. : .aw/system/workflows/plan-review-long/review-rubric.md bullet must be a byte-identical verbatim copy of .aw/system/workflows/plan-review/plan-review.md

    tests/test_v_item_evidence_durability.py:126: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity
    ========================= 1 failed, 2 passed in 0.14s ==========================

    $ git checkout -- .aw/system/workflows/plan-review-long/review-rubric.md && git diff --stat -- .aw/system/workflows/plan-review-long/review-rubric.md
    (empty output)
    ```

    Mutation proof (b) [change 'permitted' to 'allowed' in long-form bullet only]:
    ```text
    $ python3 -m pytest -o addopts="" tests/test_v_item_evidence_durability.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=2266771238
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/xl1iko
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_v_item_evidence_durability.py .F.                             [100%]

    =================================== FAILURES ===================================
    _ TestVItemEvidenceDurability.test_long_form_plan_review_evidence_durability_parity _

    self = <tests.test_v_item_evidence_durability.TestVItemEvidenceDurability testMethod=test_long_form_plan_review_evidence_durability_parity>

        def test_long_form_plan_review_evidence_durability_parity(self) -> None:
            """Assert review-rubric.md carries a byte-identical verbatim copy of the plan-review.md bullet."""
            content_long = REVIEW_RUBRIC_FILE.read_text(encoding="utf-8")
            section_a = support.section(content_long, "## A. Plan completeness", "## ")

            content_single = PLAN_REVIEW_FILE.read_text(encoding="utf-8")
            section_g = support.section(content_single, "### G. Plan executability", "## ")

            bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
            bullet_long = support.section(
                section_a, bullet_prefix, "\n- **", anchored=False
            )
            bullet_single = support.section(
                section_g, bullet_prefix, "\n- **", anchored=False
            )

            # 1. Assert byte-identical verbatim copy between long-form and single-file
    >       self.assertEqual(
                bullet_long,
                bullet_single,
                f"{REVIEW_RUBRIC_REL} bullet must be a byte-identical verbatim copy of {PLAN_REVIEW_REL}",
            )
    E       AssertionError: "- **[794 chars]e is allowed only as a non-binding pointer). A[300 chars]ng.)" != "- **[794 chars]e is permitted only as a non-binding pointer).[302 chars]ng.)"
    E       Diff is 3933 characters long. Set self.maxDiff to None to see it. : .aw/system/workflows/plan-review-long/review-rubric.md bullet must be a byte-identical verbatim copy of .aw/system/workflows/plan-review/plan-review.md

    tests/test_v_item_evidence_durability.py:126: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity
    ========================= 1 failed, 2 passed in 0.14s ==========================

    $ git checkout -- .aw/system/workflows/plan-review-long/review-rubric.md && git diff --stat -- .aw/system/workflows/plan-review-long/review-rubric.md
    (empty output)
    ```

    Mutation proof (c) [change 'permitted' to 'allowed' in single-file plan-review.md bullet only]:
    ```text
    $ python3 -m pytest -o addopts="" tests/test_v_item_evidence_durability.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=681954192
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/xl1iko
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 3 items

    tests/test_v_item_evidence_durability.py ..F                             [100%]

    =================================== FAILURES ===================================
    _ TestVItemEvidenceDurability.test_long_form_plan_review_evidence_durability_parity _

    self = <tests.test_v_item_evidence_durability.TestVItemEvidenceDurability testMethod=test_long_form_plan_review_evidence_durability_parity>

        def test_long_form_plan_review_evidence_durability_parity(self) -> None:
            """Assert review-rubric.md carries a byte-identical verbatim copy of the plan-review.md bullet."""
            content_long = REVIEW_RUBRIC_FILE.read_text(encoding="utf-8")
            section_a = support.section(content_long, "## A. Plan completeness", "## ")

            content_single = PLAN_REVIEW_FILE.read_text(encoding="utf-8")
            section_g = support.section(content_single, "### G. Plan executability", "## ")

            bullet_prefix = "- **Live-artifact success criteria vs. stable code facts (re-derivation convention):**"
            bullet_long = support.section(
                section_a, bullet_prefix, "\n- **", anchored=False
            )
            bullet_single = support.section(
                section_g, bullet_prefix, "\n- **", anchored=False
            )

            # 1. Assert byte-identical verbatim copy between long-form and single-file
    >       self.assertEqual(
                bullet_long,
                bullet_single,
                f"{REVIEW_RUBRIC_REL} bullet must be a byte-identical verbatim copy of {PLAN_REVIEW_REL}",
            )
    E       AssertionError: "- **[794 chars]e is permitted only as a non-binding pointer).[302 chars]ng.)" != "- **[794 chars]e is allowed only as a non-binding pointer). A[300 chars]ng.)"
    E       Diff is 3933 characters long. Set self.maxDiff to None to see it. : .aw/system/workflows/plan-review-long/review-rubric.md bullet must be a byte-identical verbatim copy of .aw/system/workflows/plan-review/plan-review.md

    tests/test_v_item_evidence_durability.py:126: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_long_form_plan_review_evidence_durability_parity
    ========================= 1 failed, 2 passed in 0.16s ==========================

    $ git checkout -- .aw/system/workflows/plan-review/plan-review.md && git diff --stat -- .aw/system/workflows/plan-review/plan-review.md
    (empty output)
    ```

    Pre-edit baseline:
    `8396 passed, 5 skipped, 18 xfailed, 3 warnings in 459.77s (0:07:39)`
    Failing node ids: none

    Post-change bare `python3 -m pytest`:
    `8396 passed, 5 skipped, 18 xfailed, 3 warnings in 375.09s (0:06:15)`
    Failing node ids: none

    The post-change failing set is a subset of the baseline set (both empty).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING. One rubric bullet in the long-form `review-rubric.md` changes from a one-sentence pointer to a byte-identical copy of its single-file twin, matching the four sibling bullets, and its test changes from pinning the pointer to pinning byte identity. No production Python, spec, or other workflow body changes.

SCOPE FENCE, DECLARED SO THE RUNNER CAN RECONCILE IT AFTERWARDS (not an instruction to stop). Two paths, both in `- Scope-Paths:`. Do NOT edit `.aw/system/workflows/plan-review/plan-review.md` (it is the source of the copy; mutation proof (c) touches it only temporarily and must leave an empty diff), do NOT change the other four bullets in `review-rubric.md`, and do NOT edit any plan under `.aw/records/plans/executed/`. If the work genuinely requires a path outside the fence, make the edit and justify it: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

HONESTY RULE, HARD MUST. When you report that tests passed, paste the ACTUAL runner output. Do not claim a run you did not perform.

COMMIT AND PUSH. Commit ONLY the declared paths, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set before committing.

LIFECYCLE TRANSITION. This plan MUST reach a terminal state. When executed by `aw oc run` or `aw agy run`, the RUNNER owns the transition and self-finalizes; when executed by hand, the EXECUTOR runs `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries `Result: pass` with concrete pasted evidence. Do NOT hand-roll a `git mv` into `.aw/records/plans/executed/`.
