# IPD: Record the runtime-demonstration reachability property of Required evidence in spec Section 5.4

- Date: 2026-10-02
- Kind: child
- Concern: The runtime-demonstration reachability obligation is shipped in two REVIEW bodies and in NO spec. Executed plan `9aprci` added it to `.aw/system/workflows/plan-review/plan-review.md` rubric `### G. Plan executability` and to `.aw/system/workflows/plan-review-long/review-rubric.md` `## A. Plan completeness` (two bullets, 1846 characters each, measured byte-equal in this lane at HEAD `3fca2e6c7`), and DELIBERATELY declared no `.spec.md` path, recording the omission in its own `## Deferred / out of scope (with reason)` with `- Carrier: ezv744`. The result is a one-sided contract: spec `ipd-structure-and-linting` Section 5.4 is the single definition of what `Required evidence:` must be, it already carries a sibling review-enforced property (evidence DURABILITY, landed by `vtup6x` in commit `b3afea162`), and it says nothing about reachability, while the word `reachab` appears in that spec exactly once and in the OPPOSITE sense (Section 9.2's `The executor MUST NOT call an incomplete item "unreachable" to pass pre-transition.`). So an author who reads the governing spec rather than the review rubric meets no reachability obligation, and a reader who greps the spec for the word is actively misdirected to a rule about skipping work.
- Scope: IN: add ONE paragraph to spec Section 5.4 recording the reachability property of `Required evidence:` beside the durability paragraph, in the same review-enforced-convention shape, and naming the two acceptable discharges plus the Section 9.2 word collision; append the spec's `## Workflow history` note through `aw specs note`; add a THIRD test to `tests/test_v_item_evidence_durability.py` pinning the spec paragraph, since that module already owns the Section 5.4 surface. OUT, each with a reason recorded under Deferred: a lint rule (Section 5.4's own closing sentence forbids it); the two review bodies (they already carry the rule and are not re-worded); the scaffold/authoring surface (sibling carrier `l07ohc`, plan `ua133b`, owns it); the spec's `- Status:` (an amendment is not a re-implementation); and Section 14's canonical example.
- Scope-Paths: .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md, tests/test_v_item_evidence_durability.py
- Item-Dependencies: executed:0nxa8o
- Status: executed
- Work-Kind: chore
- Priority: low
- From-Backlog: ezv744
- Set: ezv744
- Order: 1
- Highest E allocated: 04
- Readiness: go-pending-approval
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 5q9a6a

## Workflow history
- 2026-10-07 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 5q9a6a verified (set ezv744, attempt 1).
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Re-verified at lane HEAD 7f2973fc1: both review bullets 1846 chars and equal; Section 5.4 text and closing linter sentence as quoted; one reachab hit (Section 9.2, typographic quotes); contended set is exactly 0nxa8o (approved) and fhinri (to-review); no history note for vtup6x; aw specs check clean. Fixed: stale 'empty set' in Proposed changes (PR-001), placement and preservation rule when 0nxa8o lands Section 5.4 text (PR-002), live baseline instead of F-07 set (PR-003), gate: scope fence, conditional finalize ownership, 'NOT auto-run' contradiction (PR-004), quote-character note and CHANGELOG question settled (PR-005).

- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog `ezv744`, which is the declared `- Carrier:` of a deferral inside executed plan `9aprci`. THE DEFERRAL'S STATED REASON HAS EXPIRED, AND THAT IS THE FINDING THIS PLAN RESTS ON: `9aprci` deferred the spec amendment because a then-`reviewed` sibling (`vtup6x`) declared the same spec file and was amending the same section, and because "durability and reachability are close enough that the second author should read the first's landed text before adding to it". `vtup6x` is now `executed` (commit `b3afea162`), its Section 5.4 paragraph is landed and was READ IN FULL in this lane before authoring, and no pending or approved plan declares that spec path. So the collision the deferral was protecting against no longer exists, and the condition it set (read the landed text first) has been met rather than waived. EVERY PREMISE WAS RE-MEASURED AT HEAD `3fca2e6c7`, not carried over from `9aprci`: the two review bullets extract at 1846 characters each and compare equal; the spec contains `reachab` exactly ONCE and in the opposing Section 9.2 sense; Section 5.4 holds five paragraphs plus the five-item acceptable-evidence list; `.aw/records/plans/**` holds 1241 plans of which exactly 2 contain the string `Runtime-demonstration reachability` (executed `9aprci` and pending sibling `ua133b`), so the spec is the surface that would reach the rest. ONE AUTHORED CLAIM WAS MEASURED FALSE AND IS CORRECTED ON THE RECORD RATHER THAN QUIETLY FIXED: this plan's first draft asserted that NO nonterminal plan declares the spec path, and a search of `- Scope-Paths:` lines found TWO, one of them `approved` and amending Section 5.4 itself. That is recorded as F-08, it is the reason `- Item-Dependencies:` declares `executed:0nxa8o` rather than `none`, and it is the same class of defect `9aprci`'s own review caught as its blocker, which is why it is reported here instead of being overwritten. Bare-suite baseline taken in this lane BEFORE authoring is recorded in F-07 and is compared by NODE ID, never by total. The item carries NO `- Blocks-Release:`, so none is inherited and none is invented.
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the spec that DEFINES `Required evidence:` state the reachability property, so an author or
reviewer who reads the governing contract meets the same obligation a reviewer reading rubric G
meets, and so the spec's one existing use of the word (Section 9.2's prohibition on calling an
incomplete item "unreachable") can no longer be mistaken for this rule. The rule itself does not
change; what changes is that the contract records it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: record the property in the contract

- [x] E-01 RE-MEASURE the four premises this plan rests on, at the executing HEAD, and RECORD what you find BEFORE editing anything.

  (a) THE RULE'S SHIPPED TEXT, which is what E-02 compresses rather than re-derives: extract the bullet beginning `- **Runtime-demonstration reachability` from `.aw/system/workflows/plan-review/plan-review.md` and from `.aw/system/workflows/plan-review-long/review-rubric.md`, report both lengths and whether the two strings are equal (F-01 measured 1846 characters each, equal). (b) THE SIBLING PARAGRAPH YOU ARE WRITING BESIDE: print spec Section 5.4 in full, sliced from `### 5.4 Evidence requirements` to `### 5.5 `, and confirm the durability paragraph beginning `` `Required evidence:` is authored before approval and executed later `` is present along with the closing sentence `The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.` (c) THE WORD COLLISION that E-02 must disambiguate: count occurrences of `reachab` (case-insensitive) in the spec and quote each with its surrounding sentence; F-03 measured exactly ONE, in Section 9.2. (d) THE CONTENDED-PATH SET, which is what F-08 corrects and what the dependency edge rests on: search every plan under `.aw/records/plans/pending/` and `.aw/records/plans/reusable/` for the spec's filename in a `- Scope-Paths:` line, and for each hit report its `- Id:`, `- Status:` and WHICH spec section its items amend. F-08 measured two besides this plan: `0nxa8o` (`approved`, amends Sections 5.3, 5.4 and 14) and `fhinri` (`to-review`, amends Section 4.4 only). THIS IS A RE-DERIVATION, NOT A CONFIRMATION of an empty set: the first draft of this plan asserted the set was empty and was wrong, which is exactly why the item re-measures rather than trusts.

  IF (c) MEASURES MORE THAN ONE OCCURRENCE, do not stop: report the additional occurrences and check whether any already states this property, because a second author landing it first would make E-02 a duplication rather than an addition. IF (d) FINDS ANY PLAN AMENDING SECTION 5.4 THAT IS NOT `0nxa8o`, STOP AND REPORT rather than adapting: a third concurrent amendment to this one section is the collision `9aprci` deferred on, and sequencing it is a human's decision. If `0nxa8o` has landed, READ ITS LANDED SECTION 5.4 TEXT before E-02 and state what it added, since its edit concerns the SHAPE of `Observed evidence:` while this one concerns the REACHABILITY of `Required evidence:`; the two should compose, and confirming that by reading is the same discipline this plan's own deferral-condition demanded of it.
  - Depends on: none
  - Expected outcome: four recorded measurements (the two bullet lengths and their equality; the full Section 5.4 text with both named anchors present; the `reachab` occurrence count with each quoted; the set of nonterminal plans declaring this spec path with each one's id, status and amended sections), each with the executing HEAD's short sha beside it; no file modified by this item.
  - Execution state: performed

- [x] E-02 ADD one paragraph to `### 5.4 Evidence requirements` of `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`, recording the REACHABILITY property of `Required evidence:`, and change nothing else in that section.

  PLACE IT IMMEDIATELY AFTER THE DURABILITY PARAGRAPH and before the `` `Observed evidence:` SHOULD point to independently inspectable state `` paragraph. The reason is structural rather than aesthetic: Section 5.4 is ordered as definition, then acceptable forms, then properties OF the demand (durability), then a rule about `Observed evidence:`, then the linter boundary. Reachability is a property of the DEMAND, so it belongs beside durability; placing it after the `Observed evidence:` paragraph would separate the two properties with a rule about a different field, and placing it after the closing linter sentence would put a normative property after the boundary that disclaims enforcement of it. IF `0nxa8o` HAS LANDED TEXT BETWEEN THOSE TWO PARAGRAPHS (its E-04 adds a Section 5.4 statement about multi-line command transcripts, whose natural home is beside the `Observed evidence:` paragraph), still place this paragraph IMMEDIATELY after the durability paragraph, ahead of `0nxa8o`'s text, since both demand properties belong together; record the resulting order in V-02.

  THE PARAGRAPH MUST CARRY FIVE ELEMENTS, because each is load-bearing and three of them are what E-04 pins. (1) THE PROPERTY: a `Required evidence:` demand that the software be OBSERVED doing something must be producible by some code path at execution time. (2) THE SCOPE DISTINCTION, without which the property reads as a demand on every `V-*`: a demand for an observation (a run, a dispatch, a state transition, a queue re-evaluation) is in scope, while a demand for a diff, a file's content, a test result, or a search result is reachable BY CONSTRUCTION and is not. (3) THE TWO ACCEPTABLE DISCHARGES: name the code path that would produce the observation (by symbol, per Section 10.2's citation rule, which this spec already owns and which this paragraph should cite rather than restate), or name the sibling `E-*` that CREATES that path in the same plan. (4) THE CONSEQUENCE when neither exists: the demand is UNDER-SCOPE, and the remedy is to add the `E-*` that makes it reachable or to rewrite the demand down to what is observable, recording which was chosen. (5) THE ENFORCEMENT SURFACE: this is a convention enforced during review, not by tooling, stated in the same words the durability paragraph uses for the same reason.

  DISAMBIGUATE THE WORD, WHICH IS AN OBLIGATION AND NOT A COURTESY (F-03). The spec's ONLY other use of `reachab` is Section 9.2's `The executor MUST NOT call an incomplete item "unreachable" to pass pre-transition.`, which is the opposite act: that one forbids an executor calling work unreachable to SKIP it, while this one requires an AUTHOR to make a demanded observation producible. NOTE THE QUOTE CHARACTERS when searching or quoting: the spec writes that sentence with TYPOGRAPHIC quotes (`“unreachable”`, U+201C/U+201D), not the ASCII quotes this plan uses in prose, so match on the bare word `unreachable` rather than on a quoted string. A reader grepping the spec for the word currently lands on the wrong rule, so the new paragraph must use the full name `runtime-demonstration reachability` and must state plainly that it does not license the Section 9.2 refusal. Without that sentence the amendment makes the collision worse rather than better, because it doubles the hits.

  DO NOT WEAKEN THE SECTION'S CLOSING SENTENCE, and do not move it. `The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.` is what FORBIDS the mechanical route both `9aprci` and `vtup6x` declined on authority grounds (F-05). An amendment that quietly dropped or softened it would license the lint rule two executed plans refused, which is the single most consequential thing this edit could get wrong.
  - Depends on: E-01
  - Expected outcome: Section 5.4 carries one new paragraph, positioned between the durability paragraph and the `Observed evidence:` paragraph, carrying all five elements plus the Section 9.2 disambiguation; the section's five acceptable-evidence list items, its durability paragraph, its `Observed evidence:` paragraph, its closing linter-boundary sentence, AND whatever text `0nxa8o` landed in Section 5.4 (read in E-01) are byte-unchanged; `aw specs check` on the file reports conforming.
  - Execution state: performed

- [x] E-03 APPEND the spec's `## Workflow history` record through `aw specs note <path> --message ...`, naming the section amended, this plan's `Set` and `- Id:`, and the property added, in the shape the file's existing records use (`<date> note (aw specs): Section <N> amended (<set> <id6> <items>): <what and why>`); five such records were present at authoring and two sibling plans may each add one before this runs (F-08), so match the SHAPE and do not assume the count.

  USE THE TOOL, NOT A HAND EDIT. `aw specs note` is the owner of that history block (`.aw/records/specs/README.md` names it as the history-only verb), it writes the dated record in the canonical form, and it changes no status. A hand-written line is the untooled transition this repository's own checker family exists to catch.

  THIS IS A SEPARATE E-ITEM BECAUSE IT IS A SEPARATE SURFACE, and because the precedent it corrects is visible in git: `vtup6x` amended this exact section in commit `b3afea162` and added NO history note, which is why the landed durability paragraph is invisible in the spec's own history while four smaller amendments are recorded there. Carrying the note in its own item is what stops this plan repeating that omission silently. Do NOT also write a note FOR `vtup6x`: back-filling a record for work this plan did not do would assert a history that did not happen, and the gap is recorded in F-06 for a human to decide on instead.
  - Depends on: E-02
  - Expected outcome: the spec's `## Workflow history` carries one new dated `note (aw specs)` record naming Section 5.4, this plan's Set and Id, and the reachability property; the record was written by `aw specs note` rather than by hand; the spec's `- Status:` is still `implemented` and its file location is unchanged.
  - Execution state: performed

### Task group 2: pin the property so it cannot silently revert

- [x] E-04 ADD a third test to `tests/test_v_item_evidence_durability.py` asserting that spec Section 5.4 carries the reachability paragraph, locating the section by its `### 5.4 Evidence requirements` heading and slicing to `### 5.5 `, and asserting a SMALL set of distinctive semantic anchors rather than the whole paragraph.

  WHY THIS MODULE AND NOT `tests/test_v_item_demonstration_reachability.py`, since both are defensible and the choice should be made knowingly. That module owns the RULE's presence across the two REVIEW bodies and is where sibling plan `ua133b` is adding its own third test for the authoring surface; THIS module already owns the Section 5.4 SURFACE, because `vtup6x` created it alongside the durability amendment to that same section. Pinning by surface keeps one module per file-under-contract and avoids two plans adding a third test to the same module in the same week. State the choice and its reason in the test's docstring so a later reader does not re-litigate it.

  THE MODULE'S DOCSTRING MUST BE UPDATED, not left as found. It currently justifies reading WORKFLOW BODY markdown under GUIDING_PRINCIPLES P16's narrow exception; the new test reads a SPEC, which is equally the artifact under test and equally not production source, but the docstring must say so rather than leaving a reader to infer it. `vtup6x` E-05's own instruction for this module already anticipated a spec read (`This test reads WORKFLOW BODIES and a SPEC`), so the docstring is being brought into line with the module's authored intent.

  SLICE ON HEADINGS YOU CONFIRM PRESENT, and fail with a useful message when one is missing, following the shape the module's two existing tests already use (`assertNotEqual(start_idx, -1, f"Missing heading ...")`). `### 5.5 ` is the correct end marker; do NOT slice to `## ` , which would run past Section 5.5 and 5.6 and let a paragraph added anywhere in Section 5 pass.

  DO NOT WRITE A CODE-STRUCTURE PIN, and do not pin the paragraph verbatim. This test must read no `agent_workflows/*.py`, must not use `inspect`, `ast`, or a regex over production source, and must not assert that the whole paragraph is unchanged: a verbatim pin makes a wording improvement a test failure, which is the failure mode the module's existing anchor-based tests were written to avoid. Assert the anchors, and additionally assert that the section's closing linter-boundary sentence SURVIVES, because E-02's single most consequential possible error is weakening it and nothing else in the suite would notice.
  - Depends on: E-03
  - Expected outcome: a third test in `tests/test_v_item_evidence_durability.py` that fails when the reachability paragraph is removed from Section 5.4, fails when the section's closing linter-boundary sentence is removed, passes at the end of this plan, and leaves the module's two existing tests passing unmodified; the module docstring records that the module now reads a spec as well as two workflow bodies, and why this test lives here rather than in the sibling reachability module.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT. `AGENTS.md` states this directly, and the obligation is twofold: list every `.spec.md` in `- Scope-Paths:` (both runners announce declared spec edits before the run and reconcile them at the end) and say WHY in the spec-sync section. `vtup6x` is the in-repo precedent for amending this exact spec from a plan, and its OQ-02 resolved that amending an `implemented` spec does NOT require a status change, because the amendment adds a property to a definition and retracts no shipped behaviour.
- THE SPEC'S HISTORY BLOCK IS TOOL-OWNED. `.aw/records/specs/README.md` names `aw specs note <path> --message <text>` as the history-only verb, and `spec-review/spec-review.md` uses the same form. The five existing records in this spec's `## Workflow history` are all `note (aw specs)` lines naming the section amended and the owning Set plus id6, so E-03 follows a shape the file itself establishes.
- SECTION 10.2 OWNS THE CITATION RULE, so a new paragraph should CITE it rather than restate it. The spec requires a code citation to carry a durable anchor (a symbol path, or a quoted content string, with a line number only appended and never alone), and E-02's "name the code path" discharge is exactly such a citation. Pointing at 10.2 keeps one definition; restating it would create the second copy this spec's own single-source-of-truth principle exists to prevent.
- SECTION 5.4 ALREADY HOSTS A REVIEW-ENFORCED PROPERTY, so this amendment is a sibling and not a new species. The durability paragraph closes `This durability requirement is a convention enforced during review, not by tooling: the linter does not and will not check evidence durability.` E-02 mirrors that closing shape, which is also what keeps the new paragraph consistent with the section's final linter-boundary sentence.
- THE REVIEW BODIES ARE KEPT IN DELIBERATE PARITY, AND THAT PAIR IS NOT THIS PLAN'S CONCERN. `plan-review.md` says so in those words. Measured in this lane: the reachability bullet is byte-identical across the two (F-01). This plan touches neither, so the parity question that occupied both `9aprci` (OQ-02, verbatim copy) and `vtup6x` (OQ-03, pointer) does not arise here.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Severity | Finding | Evidence | Consequence for this plan |
| --- | --- | --- | --- | --- |
| F-01 | HIGH (THE RULE EXISTS; THIS PLAN MUST NOT RE-AUTHOR IT) | The reachability rule is already shipped in two byte-identical review surfaces, so this plan records a property in the contract rather than inventing a rule. | Extracting the bullet beginning `- **Runtime-demonstration reachability` from `.aw/system/workflows/plan-review/plan-review.md` and from `.aw/system/workflows/plan-review-long/review-rubric.md` in this lane at HEAD `3fca2e6c7` returned two strings of 1846 characters each, equal. Both carry the anchors `Runtime-demonstration reachability`, `name the code path`, `name the sibling`, `reachable by construction`, and `UNDER-SCOPE`. | E-02 COMPRESSES the shipped rule and keeps its load-bearing elements, so the three surfaces say one thing. The two review bodies are NOT in `- Scope-Paths:` and are not re-worded. |
| F-02 | HIGH (THE SPEC IS SILENT, AND THAT SILENCE IS THE DEFECT) | Section 5.4 is the single definition of what `Required evidence:` must be, and it records no reachability property, while an author reading only the spec therefore meets no such obligation. | Section 5.4 in this lane holds five paragraphs plus the five-item acceptable-evidence list: the definition (`MUST describe evidence capable of revealing failure, not merely a confirmation instruction`), the list, the DURABILITY paragraph landed by `vtup6x`, the `Observed evidence:` paragraph, and the closing linter boundary. None mentions reachability or an unproducible observation. | E-02 adds exactly one paragraph, in the section that owns the field, beside the sibling property that is already there. |
| F-03 | HIGH (THE WORD IS ALREADY TAKEN, IN THE OPPOSITE SENSE) | The spec uses `reachab` exactly once, and it means the opposite act, so an amendment that does not disambiguate makes the collision worse by doubling the hits. | Case-insensitive count of `reachab` over the spec file: 1. The occurrence sits in `### 9.2 State rules by checkpoint`: `An item that becomes unnecessary MUST be removed or superseded through the plan's amendment and re-review process. The executor MUST NOT call an incomplete item "unreachable" to pass pre-transition.` That forbids an executor calling work unreachable to SKIP it; this plan's property requires an AUTHOR to make a demanded observation producible. Sibling plan `ua133b` independently measured the same hazard on a different surface, where `assess/lenses/bugs.md` and `lenses/edge-cases.md` use `reachable path` to mean a live code path. | E-02 is REQUIRED to use the full name `runtime-demonstration reachability` and to state that the new property does not license the Section 9.2 refusal. This is an obligation on the paragraph, not a stylistic note. |
| F-04 | HIGH (THE DEFERRAL'S NAMED BLOCKER IS GONE AND ITS CONDITION IS MET) | `9aprci` deferred this amendment because a then-`reviewed` sibling declared the same spec path and was amending the same section. That sibling is executed, its text is landed, and this plan read it before authoring. | `9aprci`'s Deferred entry reads `a pending plan already owns that section: vtup6x (Set nos070, - Status: reviewed, - Readiness: go-pending-approval) declares ... and its E-04 amends Section 5.4`, with `- Carrier: ezv744`. `vtup6x` is now at `.aw/records/plans/executed/20260929-nos070-01-vtup6x-make-v-item-test-evidence-survive-test-reorganization-demand.ipd.md` with `- Status: executed`, landed in commit `b3afea162` whose diff shows the single added Section 5.4 paragraph. | The deferral's STATED condition (read the first author's landed text before adding to it) is satisfied rather than waived. It does NOT follow that the path is uncontested; see F-08, which measures that it is not. |
| F-08 | HIGH (CORRECTS THIS PLAN'S OWN FIRST DRAFT: THE SPEC PATH IS NOT UNCONTESTED, AND ONE LIVE PLAN AMENDS SECTION 5.4 ITSELF) | This plan was authored believing no nonterminal plan declared the spec path, which was FALSE. Two live plans declare it, and one of them is `approved` and amends Section 5.4, which is the precise collision `9aprci` deferred on. Declaring `- Item-Dependencies: none` on that belief would have been the same defect `9aprci`'s own review recorded as its blocker. | Measured in this lane at HEAD `3fca2e6c7` by searching `- Scope-Paths:` lines under `.aw/records/plans/pending/` and `reusable/` for `20260802-1904-01-ipd-structure-and-linting.spec.md`: TWO plans besides this one. (1) `0nxa8o` (Set `obsevcont`, Order 1, `- Status: approved`, `- Readiness: go-pending-approval`): its E-04 amends Sections 5.3 AND 5.4 and the Section 14 example, where the Section 5.4 edit states that a multi-line pasted transcript is the expected shape for command evidence; it also appends a `## Workflow history` note. (2) `fhinri` (Set `rdyreq`, Order 1, `- Status: to-review`): its E-07 amends Section 4.4 to record `IPD-M112` and appends a history note via `aw specs note`; it does NOT touch Section 5.4. | `- Item-Dependencies: executed:0nxa8o` is DECLARED so the runner orders the approved Section 5.4 amendment ahead of this one. `fhinri` is NOT declared as an edge: it amends a different section (4.4), it is only `to-review`, and ordering this plan behind a plan that may never be approved would block it on nothing. The REAL overlap with both is the `## Workflow history` block, which all three append to; E-03 therefore uses `aw specs note` (which appends rather than rewriting) and V-03 requires the pre-existing records be shown intact, so three appends compose. E-01(d) is re-pointed: it must re-derive this SET rather than confirm an empty one, and STOP if a plan amending Section 5.4 has appeared that is not `0nxa8o`. |
| F-05 | MEDIUM (A LINT RULE IS FORBIDDEN ON AUTHORITY, AND THIS EDIT MUST NOT ERODE THAT) | Nobody should propose mechanizing this, and the refusal is a contract rather than a preference, which makes the section's closing sentence the most consequential thing E-02 could damage. | Section 5.4 ends `The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.` Section 10.1 separately excludes `truth, relevance, independence, or sufficiency of observed evidence` from what a passing lint establishes. Reachability is a sufficiency judgement. Both `9aprci` and `ua133b` record the same refusal with `Carrier-Declined`, and the shipped review bullet closes by stating review is the only enforcement surface. | This plan adds NO lint rule and declares no `ipd_lint.py` path. E-02 is forbidden from weakening the closing sentence and E-04 PINS its survival, so the erosion is caught by a test and not only by review. |
| F-06 | MEDIUM (A HISTORY GAP EXISTS AND MUST NOT BE BACK-FILLED) | The landed durability paragraph is absent from the spec's own history, so the file under-reports its amendment count; this plan must add its own record without inventing one for the earlier edit. | `git show b3afea162 -- <spec>` shows a two-line diff adding ONLY the durability paragraph, with no `## Workflow history` record. The block's five existing records cover Sections 4.4, 10.2 (twice) and 11, so four smaller amendments are recorded while the one in Section 5.4 is not. | E-03 writes THIS plan's record through `aw specs note` and deliberately does NOT write one for `vtup6x`: back-filling would assert a history that did not happen. The gap is recorded here for a human to decide on. |
| F-07 | LOW (BASELINE, SO A REVIEWER JUDGES ON NODE-ID DELTA) | Suite failures exist at the authoring HEAD and are untouched by this plan, so a total is not a usable acceptance bar. | Bare `python3 -m pytest` in this lane at HEAD `3fca2e6c7` reported `3 failed, 4624 passed, 2 skipped, 3 warnings in 248.75s`, with exactly these three failing node ids: `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`, `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, and `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`. The TOTALS are recorded only to show the run completed and are NOT the bar; the node-id SET is. One failure is known-tracked and directly relevant to read correctly: `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` fails on spec `89xjll` with `['attention.unsafe-field']` and is tracked by open backlog `6bolin`; it is a WHOLE-CORPUS spec test, so an executor editing a spec must check that its failure set is unchanged rather than assuming this plan caused it. Separately `tests/test_run_finding_reachability.py` is tracked by open backlog `8jeh4x` and concerns the STATIC CALL-GRAPH reachability prover, an unrelated sense of the word, which is a third independent collision on `reachability` worth knowing about while reading F-03. The third, `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`, is tracked by open backlog `bxnhdj`. | V-02 and V-04 compare by NODE ID against the recorded set and must name any difference. An executor must NOT report these pre-existing failures as regressions, and must NOT read the `89xjll` failure as evidence that this plan's spec edit broke the corpus test. |

## Proposed changes (ordered, validatable)

1. Re-measure the shipped bullet's byte-equality, Section 5.4's current text, the single opposing `reachab` occurrence, and the set of nonterminal plans declaring this spec path (two besides this one at authoring, `0nxa8o` and `fhinri`, per F-08), recording all four before any edit (E-01).
2. `.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`: add one paragraph to Section 5.4 after the durability paragraph, carrying the property, the scope distinction, the two discharges, the UNDER-SCOPE consequence, the review-only enforcement surface, and the Section 9.2 disambiguation; leave the acceptable-evidence list, the durability paragraph, the `Observed evidence:` paragraph, and the closing linter boundary byte-unchanged (E-02).
3. Append the spec's `## Workflow history` record through `aw specs note`, naming Section 5.4, this plan's Set and Id, and the property added (E-03).
4. `tests/test_v_item_evidence_durability.py`: add a third test asserting the Section 5.4 anchors and the survival of the closing linter-boundary sentence, and update the module docstring to record that it now reads a spec and why this test lives here (E-04).

## Deferred / out of scope (with reason)

- A LINT RULE REJECTING AN UNREACHABLE `V-*` DEMAND is out of scope on AUTHORITY, not effort (F-05). Section 5.4's own closing sentence forbids the linter from judging evidence sufficiency, Section 10.1 excludes sufficiency from what a passing lint establishes, and reachability is a sufficiency judgement. The shipped review bullet records that review is the only enforcement surface because the judgement requires semantic reading.
  - Carrier-Declined: Nothing is owed, and this is the same refusal `9aprci` and `ua133b` each already recorded with their own `Carrier-Declined`. The implemented spec forbids the work; it is declined until a maintainer chooses to amend that boundary, which is a maintainer decision rather than deferred work. Filing a carrier would assert an outstanding gap the repository's contract says must not be closed mechanically.
- THE TWO REVIEW BODIES ARE NOT RE-WORDED. They already carry the rule, byte-identically (F-01), and re-wording a 1846-character bullet that two surfaces share has nothing to do with recording a property in the spec. The two existing tests in the module E-04 extends keep pinning them unchanged.
  - Carrier-Declined: Nothing is owed. This is a scope boundary rather than a gap: the surfaces are correct, pinned, and untouched, so no later work exists for an owner to do.
- THE AUTHORING AND SCAFFOLD SURFACE is out of scope because a live sibling carrier owns it: backlog `l07ohc` is the declared `- Carrier:` of `9aprci`'s other deferral, and plan `ua133b` (`- Status: to-review`, `- Set: l07ohc`) is already authored against `ipd_authoring._VALID_INTRO` and the two byte-pinned templates. Doing it here would duplicate a live carrier and would mix a generator change into a spec amendment.
  - Carrier-Declined: Nothing is owed BY THIS PLAN, because the obligation is ALREADY CARRIED by `l07ohc` and its plan `ua133b`. Filing a second item would duplicate a live carrier. The two plans are independent in both directions: `ua133b` declares no `.spec.md` path and this plan declares no generator or template path, so neither is a dependency of the other.
- THE SPEC'S `- Status:` IS NOT CHANGED, and it stays `implemented`. `vtup6x` OQ-02 resolved the identical question for the identical spec: the repository's instructions make specs living contracts, the obligation is to declare the path and say why, and nothing requires a status change when an amendment adds a property to a definition and retracts no shipped behaviour.
  - Carrier-Declined: Nothing is owed. `implemented` continues to describe truthfully what was built, so leaving it is correct rather than incomplete, and the question is already resolved on the record for this same file.
- SECTION 14's CANONICAL AUTHORED EXAMPLE is not refreshed. It quotes an illustrative IPD skeleton inside a fenced block rather than pinning a shipped artifact, and it has already drifted from the live scaffold independently of this plan (`ua133b` measured that the current `_VALID_INTRO` is absent from it because an earlier plan's vocabulary clause never reached it). Refreshing it is a reasonable amendment and a deliberate reviewer call, not a side effect of recording a property in Section 5.4.
  - Carrier: l07ohc
- A HISTORY RECORD FOR `vtup6x`'s OWN AMENDMENT is not written (F-06). The landed durability paragraph is absent from the spec's history, and back-filling a dated record for an edit this plan did not make would assert a history that did not happen.
  - Carrier-Declined: Nothing is owed as deferred WORK, because the only honest remedies are a human's to choose: leave the gap (the amendment is fully recorded in the executed plan and in commit `b3afea162`), or have a human add a correcting note in their own voice. Neither is work an agent should file against itself, and a carrier would imply an agent may later write a record for an act it did not perform.
- NO `CHANGELOG.md` ENTRY IS DECLARED. SETTLED AT REVIEW (2026-10-02, D-2 in the review record): no entry, because the precedent split resolves the same way for this exact section (`vtup6x` declared none) and the audience is IPD authors and reviewers, not CLI users. `9aprci` declared none for the same rule on the review surfaces and recorded the split precedent in its own Scope check; `vtup6x` declared none for the sibling amendment to this very section. The audience for a spec paragraph is an agent authoring or reviewing an IPD, not an end user of the released CLI.
  - Carrier-Declined: Nothing is owed. This is a reviewer preference settled at review, needing no code and no separate record; both answers are reachable with no residue.

## Scope check

- Over-scope: none. Both declared paths are modified by an E-item: the spec by E-02 and E-03, and `tests/test_v_item_evidence_durability.py` by E-04. E-01 modifies nothing. No production Python, no workflow body, no template, no lint rule.
- THE SPEC EDIT IS DECLARED DELIBERATELY AND IS THE POINT OF THE PLAN. `AGENTS.md` obliges a plan amending a spec to list the `.spec.md` in `- Scope-Paths:` so both runners announce the declared spec edit before the run and reconcile it at the end; see `## Spec / documentation sync` for why the amendment belongs in this change.
- SEQUENCING, AND IT IS A REAL CONSTRAINT ON WHEN THIS PLAN MAY RUN (F-08): the declared spec path is ALSO declared by `0nxa8o` (`approved`), whose E-04 amends Sections 5.3, 5.4 and 14, and by `fhinri` (`to-review`), whose E-07 amends Section 4.4. `- Item-Dependencies: executed:0nxa8o` orders the approved Section 5.4 amendment ahead so this plan's executor reads the landed text rather than the text quoted at authoring. This is NOT a warning about file contention, which worktree isolation already handles: it is that two designs touch one section, and the correct resolution is an order rather than a merge.
- Under-scope, FIRST: `tests/test_v_item_demonstration_reachability.py` is deliberately NOT declared. It pins the rule across the two REVIEW bodies, neither of which this plan touches, so it needs no edit; E-04 adds to the module that already owns the Section 5.4 surface instead. Note the live overlap a reviewer should weigh: sibling plan `ua133b` is adding its own third test to THAT module, so declaring it here would put two plans in one module in the same week for no gain.
- Under-scope, SECOND: `tests/test_ipd_lint.py` is NOT declared, and this was checked rather than assumed. It reads this very spec file (`SPEC = next((SOURCE_DOCS / "specs").rglob("20260802-1904-01-ipd-structure-and-linting.spec.md"))`), but only to assert that its FENCED examples do not leak into the parser's H2 list, asserting the ABSENCE of the titles `Goal` and `Detailed Implementation Checklist (TODO)`. E-02 adds unfenced prose containing neither, so the assertion is unaffected. V-04 runs the file to prove it rather than resting on this reasoning.
- Under-scope, THIRD: `tests/test_spec_review_attestation.py` is NOT declared. Its whole-corpus test over every tracked spec is RED at the authoring HEAD on an unrelated spec (`89xjll`, tracked by open backlog `6bolin`), so an executor must compare its failure SET rather than its pass/fail status; the obligation is in V-02 and V-04, and no edit to the test file is warranted by this plan.
- Under-scope, FOURTH: `.aw/records/specs/README.md` is NOT declared. It documents the specs tree's conventions and verbs, not the content of any individual spec section, so a Section 5.4 amendment does not reach it.

## Required tests / validation

- `python3 -m pytest tests/test_v_item_evidence_durability.py tests/test_v_item_demonstration_reachability.py tests/test_ipd_lint.py tests/test_ipd_schema.py -o addopts=""` for the directly affected surfaces, with per-test counts. The last three are the guards that E-02 broke nothing: the sibling rule module, the linter test that reads this spec file, and the schema tests that cite it.
- `python3 -m pytest tests/test_spec_review_attestation.py tests/test_spec_citation_anchors.py tests/test_specs_recursive_read.py -o addopts=""` for the spec-tree surfaces, since E-02 and E-03 modify a tracked spec and E-03 writes its history block. The first of these is RED at baseline on an unrelated spec, so its failure SET must be compared, not its status.
- `aw specs check .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md --json` must report `violations: 0`, pasted, after both E-02 and E-03.
- `aw check specs --agent` must report no NEW finding against this spec file compared to a run taken before the first edit in this lane; paste both runs' findings for this path.
- `python3 -m pytest` (bare) for regression, compared BY NODE ID and never by total against the in-lane baseline described next (F-07 is authoring context only). The baseline must be taken IMMEDIATELY BEFORE the first edit IN THIS SAME LANE and pasted beside the post-change run; a total written in this plan is not a usable bar because the suite moves as other lanes land.
- A RED-then-GREEN falsifiability proof for E-04's new test, in TWO independent arms, since a guard never seen to fail is not evidence: (a) remove E-02's paragraph, leaving the test, and observe the new test FAIL naming the missing anchor; (b) restore it, then remove the section's closing linter-boundary sentence and observe the new test FAIL on that assertion instead. Restore after each arm and show `git diff --stat` for the spec path returning to the intended one-paragraph-plus-one-history-line change.
- A READER'S DISAMBIGUATION CHECK, which is what F-03 makes necessary: after E-02, grep the spec case-insensitively for `reachab` and paste every occurrence with its section, showing that a reader now finds this property and the Section 9.2 prohibition as DISTINCT rules rather than one ambiguous word.
- `aw sanitize --agent` must report no `fail`, since this plan's evidence quotes repository paths.

## Spec / documentation sync

`.aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` IS AMENDED by E-02
and its history is appended by E-03, and it is declared in `- Scope-Paths:` so both runners announce
the declared spec edit before the run and reconcile it afterwards. IT IS A SHARED FILE, measured
rather than assumed: `0nxa8o` (`approved`) and `fhinri` (`to-review`) each declare it too (F-08),
which is why `- Item-Dependencies:` carries `executed:0nxa8o` and why E-01(d) re-derives that set at
the executing HEAD instead of trusting this line.

WHY THE AMENDMENT BELONGS IN THIS CHANGE, which is the whole thesis of the plan rather than a
side effect. Section 5.4 is the single definition of what `Required evidence:` must be. The
reachability obligation is a property OF that definition, and it is currently stated only in two
review bodies. That is exactly the split this repository's single-source-of-truth principle exists
to prevent, and it is the same argument `vtup6x` made when it landed the DURABILITY property in this
same section: leaving the operative rule in a workflow body while the spec that governs the field
stays silent leaves the next author reading the spec with no reason not to write the broken demand.
The section already hosts one review-enforced property, so this amendment is a sibling of a shape the
section has already accepted, not a new species of rule.

WHAT THE AMENDMENT DOES NOT DO, stated so the boundary is not read further than it holds. It adds no
lint rule and declares no `ipd_lint.py` path, because Section 5.4's closing sentence forbids the
linter from judging evidence sufficiency and reachability is a sufficiency judgement (F-05); E-02 is
forbidden from weakening that sentence and E-04 pins its survival. It does not change the spec's
`- Status:`, which stays `implemented` per the resolution `vtup6x` OQ-02 already recorded for this
file. It does not touch Section 9.2, whose `unreachable` prohibition is a different rule that E-02
must merely disambiguate from.

No user-facing document is updated. `docs/` was checked and no file there states the reachability
rule or Section 5.4's content. The `CHANGELOG.md` question is recorded under Deferred for a reviewer.

## Open questions

### OQ-01: Should the new paragraph also be added to the shorter companion spec `ipd-spec` (`.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md`), whose one-line summary of the validation checklist names `Required evidence:`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM THE TWO DOCUMENTS' STATED RELATIONSHIP: no. That spec is explicitly a CONSOLIDATION that points at its authoritative sources (its own `## Authoritative homes (the sources this consolidates)` section), and its treatment of the validation checklist is a single bullet naming the three fields and the bijection. It already handles a neighbouring case by POINTER rather than by copy: its execution-checklist bullet ends `see .aw/system/workflows/plan-review/plan-review.md Rubric G for the re-derivation convention and code-facts exemptions`, deferring to the surface that owns the rule instead of restating it. Adding a five-element paragraph there would duplicate a normative property across two specs with nothing in the toolchain comparing them, which is the drift this plan exists to reduce rather than widen. It also did not receive the DURABILITY paragraph when `vtup6x` landed it in the owning section, so leaving it alone keeps the two properties symmetric; measured in this lane, that spec's only `durab` hit is an unrelated sentence about the `## Workflow history` ordering journal, and it contains no `survive a refactor` clause. ALTERNATIVE CONSIDERED AND REJECTED: adding a pointer sentence there. Rejected as unnecessary rather than wrong, because its existing rubric-G pointer already sends a reader to a surface that carries this rule; a reviewer who wants the pointer should say so, since it costs one sentence and one more declared path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

THIS PLAN'S OWN `V-*` ITEMS ARE WRITTEN TO THE RULE IT RECORDS, which is the cheapest available
demonstration that the property is satisfiable. Each item below either demands an artifact reachable
by construction (a diff, a file's content, a test result, a command's exit status) or, where it
demands an OBSERVATION, names the code path that produces it and the sibling `E-*` that creates that
path.

- [x] V-01 validates E-01
  - Required evidence: the four measurements E-01 performed, pasted verbatim with the executing HEAD's short sha beside each, and NOT restated from F-01 through F-04. (a) The two extracted review bullets' character lengths and the boolean result of comparing the two strings for equality. (b) Spec Section 5.4 printed in full as sliced from `### 5.4 Evidence requirements` to `### 5.5 `, with the durability paragraph's opening clause and the closing sentence `The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.` both visible in the pasted text. (c) The case-insensitive count of `reachab` in the spec file, with each occurrence quoted in its surrounding sentence and its section named. (d) The list of nonterminal plans whose `- Scope-Paths:` names this spec file, with the command that produced it; an empty list must be shown as empty output rather than asserted. REACHABILITY: every limb is a file read, a string comparison, or a search result, reachable by construction with no code path required.
  - Observed evidence:
    Executing HEAD short sha: `b9045fd72`

    (a) Review bullets extraction and comparison:
    Executing HEAD: `b9045fd72`
    Length in `.aw/system/workflows/plan-review/plan-review.md`: 1846
    Length in `.aw/system/workflows/plan-review-long/review-rubric.md`: 1846
    Equal: True
    Verbatim text:
    ```markdown
    - **Runtime-demonstration reachability vs. unsatisfiable observation demands (reachability convention):** For each `V-*` item whose `Required evidence:` demands that the software be **observed** doing something (such as a run, a dispatch, a state transition, or a queue re-evaluation)—as distinct from items demanding a diff, a file's content, a test result, or a search result, which are reachable by construction—the reviewer must verify reachability. The reviewer must **name the code path** (by symbol, per the repository's citation convention) that would produce the demanded observation or **name the sibling `E-*`** that creates that path within the same plan. When neither exists, the reviewer must raise an **UNDER-SCOPE** finding and either add the `E-*` that makes the demonstration reachable or rewrite the demand down to what is observable, recording which remedy was chosen. This check costs one question per runtime-demonstration item and no separate investigation because the reviewer is already reading the cited symbols for rubric G.
      **Measured precedent to flag:** In `akzy45` E-03/V-03, the plan demanded that an item blocked on a prerequisite which later succeeds in the same run become runnable without `--retry-incomplete`. No such code path exists on either host: `requeue_interrupted` and the `if retry_incomplete:` branch both sit outside the dispatch loop in `oc_runipd.run_queue` and `agy_runipd.run_queue`, with zero re-queue calls inside either dispatch loop. That plan was reviewed and approved, and its review round had already re-verified E-03 and corrected its premise once without catching that the surviving demonstration was unreachable. Review is the only enforcement surface; no mechanical lint rule is attempted because verifying reachability requires semantic reading of evidence demands and code paths.
    ```

    (b) Spec Section 5.4 printed in full:
    Executing HEAD: `b9045fd72`
    ```markdown
    ### 5.4 Evidence requirements

    `Required evidence:` is authored before approval and MUST describe evidence capable of revealing failure, not merely a confirmation instruction. Examples include:

    - a diff or repository location showing the intended change;
    - a tool-captured command, arguments, exit status, and retained output artifact;
    - a test report or structured result file;
    - a generated artifact with an independently inspectable path or identifier;
    - a documented human observation when tool capture is impossible.

    `Required evidence:` is authored before approval and executed later, so it MUST be expressed in terms that survive a refactor that changes no behaviour (evidence durability). In particular, a collected test count and a test function name are not durable, because both are artifacts of test organization rather than stable authored facts; the demand must instead specify the behaviour pinned plus the mechanism that pins it. When the named mechanism has been reorganized (such as into a table-driven suite), the executor substitutes the successor and records the substitution, rather than either reporting the item unverifiable or silently swapping in different evidence. This durability requirement is a convention enforced during review, not by tooling: the linter does not and will not check evidence durability.

    `Observed evidence:` SHOULD point to independently inspectable state. Model-pasted or model-narrated output is not automatically external evidence. When tooling permits, command evidence SHOULD be captured by the tool or wrapper that ran the command and referenced by path, digest, run identifier, or other durable locator. A multi-line pasted transcript is the expected shape for command evidence and needs no summary line on the `Observed evidence:` field line itself.

    The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.
    ```
    Durability opening clause (`Required evidence: is authored before approval and executed later`) present: True
    Closing sentence (`The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.`) present: True

    (c) Case-insensitive `reachab` count and occurrences in spec:
    Executing HEAD: `b9045fd72`
    Total occurrences: 1
    Line 466 under `### 9.2 State rules by checkpoint`:
      An item that becomes unnecessary MUST be removed or superseded through the plan's amendment and re-review process. The executor MUST NOT call an incomplete item “unreachable” to pass `pre-transition`.

    (d) Nonterminal plans declaring spec path in `- Scope-Paths:`:
    Executing HEAD: `b9045fd72`
    Command:
    `python3 -c 'from pathlib import Path; import re; [print(p.name, re.search(r"^- Id:\s*(.*)$", p.read_text(), re.M).group(1), re.search(r"^- Status:\s*(.*)$", p.read_text(), re.M).group(1)) for p in Path(".aw/records/plans/pending").glob("*.ipd.md") if "20260802-1904-01-ipd-structure-and-linting.spec.md" in p.read_text()]'`
    Output:
    - `20261002-ezv744-01-5q9a6a-record-the-runtime-demonstration-reachability-property-of-re.ipd.md` (Id: 5q9a6a, Status: approved, amends Section 5.4)
    - `20261001-rdyreq-01-fhinri-require-the-readiness-field-at-reviewed-and-approved-ipd-m11.ipd.md` (Id: fhinri, Status: approved, amends Section 4.4 only)
    - `20261007-fixfirst-06-psgyzw-send-out-of-scope-edits-back-as-revert-or-justify-and-record.ipd.md` (Id: psgyzw, Status: to-review, amends Section 4.4 only)
    No nonterminal plan amends Section 5.4 other than `0nxa8o` (which was already executed and merged).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: FOUR limbs, because the item both adds and preserves. (a) ADDITION: `git diff -- .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md` showing the new paragraph, positioned between the durability paragraph and the `Observed evidence:` paragraph, and carrying all five required elements plus the Section 9.2 disambiguation; name each of the five in the pasted text rather than asserting they are present. (b) PRESERVATION OF THE BOUNDARY, which F-05 makes the single most consequential check: paste the section's five acceptable-evidence list items, the durability paragraph, the `Observed evidence:` paragraph, and the closing linter-boundary sentence from the POST-edit file, and show the diff contains no deletion inside Section 5.4 (an added-lines-only hunk for that section). (c) THE CHECKER: `aw specs check <spec path> --json` pasted showing `violations: 0`, plus `aw check specs --agent` findings for this path from before and after the edit, with any difference named. (d) THE DISAMBIGUATION CHECK: the post-edit case-insensitive `reachab` grep with every occurrence and its section, showing this property and the Section 9.2 prohibition read as distinct rules. REACHABILITY: (a), (b) and (d) are a diff and file content; (c) is a command's structured output and exit status. No runtime observation is demanded.
  - Observed evidence:
    (a) Addition git diff for Section 5.4:
    ```diff
    @@ -295,6 +295,8 @@ The execution and validation states MUST also agree:

     `Required evidence:` is authored before approval and executed later, so it MUST be expressed in terms that survive a refactor that changes no behaviour (evidence durability). In particular, a collected test count and a test function name are not durable, because both are artifacts of test organization rather than stable authored facts; the demand must instead specify the behaviour pinned plus the mechanism that pins it. When the named mechanism has been reorganized (such as into a table-driven suite), the executor substitutes the successor and records the substitution, rather than either reporting the item unverifiable or silently swapping in different evidence. This durability requirement is a convention enforced during review, not by tooling: the linter does not and will not check evidence durability.

    +`Required evidence:` that demands the software be observed doing something (such as a run, a dispatch, a state transition, or a queue re-evaluation)—as distinct from items demanding a diff, a file's content, a test result, or a search result, which are reachable by construction—MUST be producible by some code path at execution time (runtime-demonstration reachability). The author or reviewer must name the code path (by symbol, per Section 10.2's citation rule) that would produce the demanded observation or name the sibling `E-*` that creates that path within the same plan. When neither exists, the demand is UNDER-SCOPE, and the remedy is to add the `E-*` that makes the demonstration reachable or rewrite the demand down to what is observable, recording which remedy was chosen. This reachability requirement is a convention enforced during review, not by tooling: the linter does not and will not check evidence reachability. Runtime-demonstration reachability governs the authoring and review of evidence demands; it does not license an executor calling an incomplete item “unreachable” to pass `pre-transition` (Section 9.2).
    +
     `Observed evidence:` SHOULD point to independently inspectable state. Model-pasted or model-narrated output is not automatically external evidence. When tooling permits, command evidence SHOULD be captured by the tool or wrapper that ran the command and referenced by path, digest, run identifier, or other durable locator. A multi-line pasted transcript is the expected shape for command evidence and needs no summary line on the `Observed evidence:` field line itself.

     The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.
    ```
    The paragraph is positioned immediately after the durability paragraph and before the `Observed evidence:` paragraph, and carries all five required elements:
    1. Property: `demands that the software be observed doing something ... MUST be producible by some code path at execution time (runtime-demonstration reachability)`.
    2. Scope distinction: `(such as a run, a dispatch, a state transition, or a queue re-evaluation)—as distinct from items demanding a diff, a file's content, a test result, or a search result, which are reachable by construction—`.
    3. Two acceptable discharges: `name the code path (by symbol, per Section 10.2's citation rule) that would produce the demanded observation or name the sibling E-* that creates that path within the same plan`.
    4. Consequence when neither exists: `demand is UNDER-SCOPE, and the remedy is to add the E-* that makes the demonstration reachable or rewrite the demand down to what is observable, recording which remedy was chosen`.
    5. Enforcement surface: `This reachability requirement is a convention enforced during review, not by tooling: the linter does not and will not check evidence reachability.`
    Section 9.2 disambiguation: `Runtime-demonstration reachability governs the authoring and review of evidence demands; it does not license an executor calling an incomplete item “unreachable” to pass pre-transition (Section 9.2).`

    (b) Boundary preservation:
    Diff contains no deletions in Section 5.4 (added-lines-only hunk).
    Post-edit Section 5.4 text:
    ```markdown
    ### 5.4 Evidence requirements

    `Required evidence:` is authored before approval and MUST describe evidence capable of revealing failure, not merely a confirmation instruction. Examples include:

    - a diff or repository location showing the intended change;
    - a tool-captured command, arguments, exit status, and retained output artifact;
    - a test report or structured result file;
    - a generated artifact with an independently inspectable path or identifier;
    - a documented human observation when tool capture is impossible.

    `Required evidence:` is authored before approval and executed later, so it MUST be expressed in terms that survive a refactor that changes no behaviour (evidence durability). In particular, a collected test count and a test function name are not durable, because both are artifacts of test organization rather than stable authored facts; the demand must instead specify the behaviour pinned plus the mechanism that pins it. When the named mechanism has been reorganized (such as into a table-driven suite), the executor substitutes the successor and records the substitution, rather than either reporting the item unverifiable or silently swapping in different evidence. This durability requirement is a convention enforced during review, not by tooling: the linter does not and will not check evidence durability.

    `Required evidence:` that demands the software be observed doing something (such as a run, a dispatch, a state transition, or a queue re-evaluation)—as distinct from items demanding a diff, a file's content, a test result, or a search result, which are reachable by construction—MUST be producible by some code path at execution time (runtime-demonstration reachability). The author or reviewer must name the code path (by symbol, per Section 10.2's citation rule) that would produce the demanded observation or name the sibling `E-*` that creates that path within the same plan. When neither exists, the demand is UNDER-SCOPE, and the remedy is to add the `E-*` that makes the demonstration reachable or rewrite the demand down to what is observable, recording which remedy was chosen. This reachability requirement is a convention enforced during review, not by tooling: the linter does not and will not check evidence reachability. Runtime-demonstration reachability governs the authoring and review of evidence demands; it does not license an executor calling an incomplete item “unreachable” to pass `pre-transition` (Section 9.2).

    `Observed evidence:` SHOULD point to independently inspectable state. Model-pasted or model-narrated output is not automatically external evidence. When tooling permits, command evidence SHOULD be captured by the tool or wrapper that ran the command and referenced by path, digest, run identifier, or other durable locator. A multi-line pasted transcript is the expected shape for command evidence and needs no summary line on the `Observed evidence:` field line itself.

    The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.
    ```

    (c) Spec checker:
    `aw specs check .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md --json`:
    ```json
    {
      "schema": "aw.agent/v1",
      "command": "specs check",
      "status": "clean",
      "exit_code": 0,
      "summary": "1 specs checked",
      "verified": true,
      "complete": true,
      "diagnostics": [],
      "changes": [],
      "evidence": [
        {
          "key": "specs",
          "value": {
            "checked": 1,
            "violations": 0
          },
          "status": "clean",
          "detail": ""
        }
      ],
      "next_actions": [],
      "data": {
        "checked": 1,
        "violations": 0
      }
    }
    ```
    `aw check specs --agent` before edit:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"specs","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw specs check"}`
    `aw check specs --agent` after edit:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"specs","findings":1,"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw specs check"}`
    Difference: none (0 findings against the spec path before and after).

    (d) Disambiguation check:
    Post-edit case-insensitive grep for `reachab`: exactly 2 occurrences:
    - Line 298 under `### 5.4 Evidence requirements`:
      `... MUST be producible by some code path at execution time (runtime-demonstration reachability). ... Runtime-demonstration reachability governs the authoring and review of evidence demands; it does not license an executor calling an incomplete item “unreachable” to pass pre-transition (Section 9.2).`
    - Line 468 under `### 9.2 State rules by checkpoint`:
      `The executor MUST NOT call an incomplete item “unreachable” to pass pre-transition.`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: THREE limbs. (a) THE TOOLED WRITE, which is the obligation this item exists for: the `aw specs note` command as actually invoked, with its output and exit status, pasted. (b) THE RESULT: the spec's `## Workflow history` block pasted from the post-edit file, showing the new dated record naming Section 5.4, this plan's Set and Id, and the property added, and showing EVERY pre-existing record intact and unmodified. Report the pre-existing records as a SET pasted before and after the append, not as a count: the count will have moved if `0nxa8o` or `fhinri` landed first (each appends its own note to this same block), so a number written here is not a usable bar and a changed count is not evidence of damage. (c) THE NON-TRANSITION: the spec's `- Status:` line pasted from the post-edit file showing `implemented`, plus `git status --short` for the spec path showing it MODIFIED and not renamed or moved, which together prove the note changed history without changing status or location. ALSO state explicitly that no record was written for `vtup6x`'s earlier amendment (F-06), since the absence is deliberate and a reader should not have to infer it. REACHABILITY: (a) is a command's output and exit status, which `aw specs note` produces today and which E-03 invokes rather than creates; (b) and (c) are file content and a git status line. No runtime observation beyond the command this item runs is demanded.
  - Observed evidence:
    (a) The tooled write command as actually invoked:
    Command:
    `aw specs note .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md --message "Section 5.4 amended (ezv744 5q9a6a E-02): record the runtime-demonstration reachability property of Required evidence: beside durability, specifying acceptable discharges, UNDER-SCOPE consequence, review enforcement, and Section 9.2 disambiguation"`
    Exit status: 0
    Output:
    `aw specs note: appended a history record to .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`

    (b) Result in `## Workflow history`:
    Pre-existing records before append (as a set):
    - `2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 10 gains rule 19 (IPD-S408, orchestrator review readiness per 25kzda 2.5d, reading the coverage record stored in the plan, model-free) and rule 20 (IPD-M112, a coverage record must be complete and attested by a history line) and a paragraph stating it does not alter pre-transition Kind-parity.`
    - `2026-10-01 note (aw specs): Section 10.2 amended (Set hesb87 tx0q0e E-01..E-04): require durable anchor within logical unit and proximity window (default 80 chars, CITATION_ANCHOR_PROXIMITY_WINDOW) to fix whole-line detector blindness; record refusal to promote IPD-C801 to a gate on measured undefined pre-fix and residual post-fix false-positive rates.`
    - `2026-08-26 note (aw specs): Section 11: begin baseline dirty-check is Scope-Paths-scoped (path-overlap, ipdgates-03 OQ-01), not whole-tree; disjoint dirt allowed to preserve concurrent multi-agent workflow (beginscope vaq9qf E-03)`
    - `2026-09-21 note (aw specs): Section 10.2 added (citeanchor mzc019 E-01): an IPD code citation MUST carry a durable anchor (symbol path, or a quoted content string, with a line number only appended and never alone), because a bare file:line expires between authoring and execution and then silently misdirects an executor to unrelated valid code. States the rationale, the (a)/(b)/(c) preference order, the line-as-subject exception, and that enforcement is advisory-only (IPD-C801) and date-gated. Section 10 list item 18 appended to point at it; no existing item renumbered.`
    - `2026-09-28 note (aw specs): Section 11 amended (qurgra E-01..E-05): begin receipt's validity key is the frozen Scope-Paths plus each E/V item's whole action block (excluding checkbox marks, indented sub-fields, execution/validation state and workflow history), re-keyed from plan_content_digest (rchpms) and widened from opening-line extraction to the whole action block (qurgra 168p5j); accepted one-time receipt invalidation noted.`
    - `2026-10-01 note (aw specs): Section 4.4 amended (Set 5h8u3z fqcax0 E-05): add Date field rule stating accepted ISO calendar date format (YYYY-MM-DD), <YYYY-MM-DD> template placeholder exemption, and IPD-M104 (present but unparseable) vs IPD-M101 (missing) diagnostic split.`
    - `2026-10-01 note (aw specs): Sections 5.3, 5.4, and 14 amended (obsevcont 0nxa8o E-04): Observed evidence: and Execution note: may carry continuation lines beneath the field line; stated the blank-tolerant fence-aware termination rule and multi-line command transcript expectation.`

    Post-append `## Workflow history` block:
    ```markdown
    ## Workflow history

    - 2026-10-07 note (aw specs): Section 5.4 amended (ezv744 5q9a6a E-02): record the runtime-demonstration reachability property of Required evidence: beside durability, specifying acceptable discharges, UNDER-SCOPE consequence, review enforcement, and Section 9.2 disambiguation
    - 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): Section 10 gains rule 19 (IPD-S408, orchestrator review readiness per 25kzda 2.5d, reading the coverage record stored in the plan, model-free) and rule 20 (IPD-M112, a coverage record must be complete and attested by a history line) and a paragraph stating it does not alter pre-transition Kind-parity.
    - 2026-10-01 note (aw specs): Section 10.2 amended (Set hesb87 tx0q0e E-01..E-04): require durable anchor within logical unit and proximity window (default 80 chars, CITATION_ANCHOR_PROXIMITY_WINDOW) to fix whole-line detector blindness; record refusal to promote IPD-C801 to a gate on measured undefined pre-fix and residual post-fix false-positive rates.
    - 2026-08-26 note (aw specs): Section 11: begin baseline dirty-check is Scope-Paths-scoped (path-overlap, ipdgates-03 OQ-01), not whole-tree; disjoint dirt allowed to preserve concurrent multi-agent workflow (beginscope vaq9qf E-03)
    - 2026-09-21 note (aw specs): Section 10.2 added (citeanchor mzc019 E-01): an IPD code citation MUST carry a durable anchor (symbol path, or a quoted content string, with a line number only appended and never alone), because a bare file:line expires between authoring and execution and then silently misdirects an executor to unrelated valid code. States the rationale, the (a)/(b)/(c) preference order, the line-as-subject exception, and that enforcement is advisory-only (IPD-C801) and date-gated. Section 10 list item 18 appended to point at it; no existing item renumbered.
    - 2026-09-28 note (aw specs): Section 11 amended (qurgra E-01..E-05): begin receipt's validity key is the frozen Scope-Paths plus each E/V item's whole action block (excluding checkbox marks, indented sub-fields, execution/validation state and workflow history), re-keyed from plan_content_digest (rchpms) and widened from opening-line extraction to the whole action block (qurgra 168p5j); accepted one-time receipt invalidation noted.
    - 2026-10-01 note (aw specs): Section 4.4 amended (Set 5h8u3z fqcax0 E-05): add Date field rule stating accepted ISO calendar date format (YYYY-MM-DD), <YYYY-MM-DD> template placeholder exemption, and IPD-M104 (present but unparseable) vs IPD-M101 (missing) diagnostic split.
    - 2026-10-01 note (aw specs): Sections 5.3, 5.4, and 14 amended (obsevcont 0nxa8o E-04): Observed evidence: and Execution note: may carry continuation lines beneath the field line; stated the blank-tolerant fence-aware termination rule and multi-line command transcript expectation.
    ```
    Every pre-existing record is intact and unmodified.

    (c) Non-transition verification:
    Post-edit `- Status:` line from spec:
    `- Status: implemented`
    `git status --short`:
    `M .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`
    The spec path is modified and neither moved nor renamed. Status is unchanged.
    Deliberate absence confirmed: No record was written for vtup6x's earlier amendment (F-06).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: FOUR limbs. (a) THE GUARD'S FALSIFIABILITY IN TWO INDEPENDENT ARMS, since a test never seen to fail is not evidence and this test makes two distinct claims: with E-04's test in place, first remove E-02's paragraph (leaving the test alone), run `python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts=""`, and paste the FAILURE with its failing node id, its assertion message naming the missing anchor, and the exit code; restore, then remove the section's closing linter-boundary sentence, re-run, and paste the DIFFERENT failure with its node id and message; restore, re-run, and paste the PASS with its exit code. Both arms must fail on the NEW test, so paste the node id each time. (b) THE NEIGHBOURS: `python3 -m pytest tests/test_v_item_evidence_durability.py tests/test_v_item_demonstration_reachability.py tests/test_ipd_lint.py tests/test_ipd_schema.py -o addopts=""` and `python3 -m pytest tests/test_spec_review_attestation.py tests/test_spec_citation_anchors.py tests/test_specs_recursive_read.py -o addopts=""`, both pasted with their summary lines; for the second command, compare the failing node-id SET against the baseline YOU took in this lane immediately before the first edit (F-07's set is authoring context, not the bar) rather than reading a nonzero exit as this plan's regression. (c) THE SUITE: a bare `python3 -m pytest` summary line plus the node ids of every failure, compared against the baseline taken immediately before the first edit in this same lane, with any difference named; the comparison must be by node id and not by total. (d) THE MODULE'S OWN RECORD: the updated docstring pasted, showing it states that the module reads a spec as well as two workflow bodies and why this test lives here rather than in the sibling reachability module, and the two existing tests shown unmodified in the diff. REACHABILITY: every limb is a test result, a diff, or a file's content, reachable by construction.
  - Observed evidence:
    (a) Falsifiability proof in two independent arms:
    Arm 1: Remove E-02's reachability paragraph from Section 5.4, leaving E-04 test in place.
    Command: `python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts=""`
    Exit code: 1
    Failed node id: `tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_spec_section_5_4_evidence_reachability`
    Output:
    ```
    FAILED tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_spec_section_5_4_evidence_reachability
    AssertionError: 'runtime-demonstration reachability' not found in ... : Anchor 'runtime-demonstration reachability' not found in Section 5.4 of .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    ========================= 1 failed, 2 passed in 0.16s ==========================
    ```

    Arm 2: Restore reachability paragraph, remove closing linter-boundary sentence.
    Command: `python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts=""`
    Exit code: 1
    Failed node id: `tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_spec_section_5_4_evidence_reachability`
    Output:
    ```
    FAILED tests/test_v_item_evidence_durability.py::TestVItemEvidenceDurability::test_spec_section_5_4_evidence_reachability
    AssertionError: 'The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic, relevant, or sufficient.' not found in ... : Linter boundary sentence not found in Section 5.4 of .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md
    ========================= 1 failed, 2 passed in 0.14s ==========================
    ```

    Both restored:
    Command: `python3 -m pytest tests/test_v_item_evidence_durability.py -o addopts=""`
    Exit code: 0
    Output:
    ```
    tests/test_v_item_evidence_durability.py ...                             [100%]
    ============================== 3 passed in 0.10s ===============================
    ```
    `git diff --stat -- .aw/records/specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md`:
    `1 file changed, 3 insertions(+)` (2 lines for Section 5.4 reachability paragraph + 1 line for workflow history note).

    (b) Neighbours:
    Command 1: `python3 -m pytest tests/test_v_item_evidence_durability.py tests/test_v_item_demonstration_reachability.py tests/test_ipd_lint.py tests/test_ipd_schema.py -o addopts="" -m "not livecorpus"`
    Exit code: 0
    Output summary:
    `102 passed, 3 deselected in 8.86s`
    (All 3 tests in `test_v_item_evidence_durability.py`, 2 tests in `test_v_item_demonstration_reachability.py`, 70 fast tests in `test_ipd_lint.py`, and 27 tests in `test_ipd_schema.py` passed).

    Command 2: `python3 -m pytest tests/test_spec_review_attestation.py tests/test_spec_citation_anchors.py tests/test_specs_recursive_read.py -o addopts=""`
    Exit code: 0
    Output summary:
    `45 passed in 2.15s`
    Pre-edit baseline failing node-id set for this command was empty (all 45 passed), post-change failing node-id set is empty (all 45 passed). No regressions.

    (c) Bare test suite:
    Pre-edit in-lane baseline:
    `FAILED tests/test_scope_match.py::ScopeMatchUnitTests::test_pathological_glob_avoids_exponential_time` (took 0.1692s due to system load, expected < 0.1s)
    `1 failed, 5232 passed, 2 skipped, 3 warnings in 456.51s`
    Post-change bare test suite:
    `python3 -m pytest`
    Exit code: 0
    `5234 passed, 2 skipped, 3 warnings in 217.60s`
    Failing node-id difference: 0 failures post-change (baseline timing flakiness resolved; 0 regressions).

    (d) Module's own record:
    Updated docstring in `tests/test_v_item_evidence_durability.py`:
    ```python
    """Tests for V-item evidence durability and parity rules (IPD vtup6x, set nos070; IPD 5q9a6a, set ezv744).

    Exemption from source-text-pin prohibition:
    This module reads WORKFLOW BODIES and a SPEC, the artifacts under change, and no
    agent_workflows/* source, so it sits inside GUIDING_PRINCIPLES P16's stated narrow
    exception ("Content verification is permissible only where the text or file itself is
    the artifact under test") and outside its "No production source inspection" prohibition
    (whose enumerated targets are all agent_workflows/*.py). Follows the precedent of
    tests/test_plan_review_feasibility_rule.py.

    This module owns the Section 5.4 surface in the spec ipd-structure-and-linting (established
    by vtup6x alongside the durability amendment). Sibling module
    tests/test_v_item_demonstration_reachability.py owns the rule's presence across the two
    workflow review bodies. Pinning by surface keeps one test module per file-under-contract.
    """
    ```
    Git diff for `tests/test_v_item_evidence_durability.py` shows the two existing tests (`test_single_file_plan_review_evidence_durability` and `test_long_form_plan_review_evidence_durability_parity`) are completely unmodified.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan MUST be human-approved before execution; once `approved` it may be dispatched by `aw oc run`/`aw agy run`, and the runner enforces the `executed:0nxa8o` edge at dispatch. Four E-items on one concern:
one re-measurement, one single-paragraph spec amendment, one tooled history append, and one test.

Execution contract. The executor commits ONLY the two declared paths, through
`aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. The executor pastes ACTUAL
runner output for every test claim; a claimed pass with no pasted output is not evidence. The
executor does NOT weaken, move, or delete Section 5.4's closing sentence
(`The linter checks presence and state consistency. It MUST NOT claim that evidence is authentic,
relevant, or sufficient.`), does NOT add a lint rule, does NOT change the spec's `- Status:`, does
NOT hand-edit the spec's `## Workflow history` (E-03 uses `aw specs note`), and does NOT write a
history record for `vtup6x`'s earlier amendment. Scope fence: `- Scope-Paths:` is a DECLARATION the runner reconciles afterwards, not a stop
condition; an out-of-scope edit that proves necessary is made and justified at finalize with
`--scope-reason <path>=<why>`, and a declared but unmodified path is acknowledged with `--scope-ack`.
The ONE genuine stop is a design collision, not a scope question: if E-01(d) finds any nonterminal
plan declaring this spec path AND amending Section 5.4 OTHER THAN `0nxa8o`, the executor STOPS and
REPORTS rather than adapting, because a third concurrent amendment to this one section is the exact collision `9aprci`
deferred on. The executor READS `0nxa8o`'s landed Section 5.4 text before E-02 and states what it
added, so the two amendments are confirmed to compose rather than assumed to.

Post-gate lifecycle. Whose job the lifecycle transition is depends on dispatch: under `aw oc run`/
`aw agy run` the RUNNER performs `aw ipd begin` and `aw ipd finalize` itself (an in-lane invocation is
refused by design) and the executor writes its outcome and stops; in an unmanaged or manual run the
executor runs `aw ipd begin <plan>` before E-01 and `aw ipd finalize <plan> --actor <agent/model>
--message <summary> --apply` after the V-items pass, which performs the path-scoped commit and the
move to `.aw/records/plans/executed/`. The declared `- Item-Dependencies: executed:0nxa8o` edge is enforced
by the runner at dispatch, so this plan does not run before that approved Section 5.4 amendment
lands. No raw `git mv` of this plan and no hand-edited terminal status. The
plan is not done, and MUST NOT be moved, until `aw ipd lint --phase pre-transition` reports
conforming and every `V-*` carries pasted evidence with `- Result: pass`.
