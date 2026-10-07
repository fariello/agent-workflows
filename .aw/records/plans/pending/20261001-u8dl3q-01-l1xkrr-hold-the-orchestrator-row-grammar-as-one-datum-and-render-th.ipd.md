# IPD: Hold the orchestrator row grammar as one datum and render the pattern, the canonical form, and the scaffold row from it

- Date: 2026-10-01
- Kind: child
- Concern: The typed child-tracking row grammar is stated by hand THREE TIMES and nothing fails when one copy drifts. Measured in this lane at HEAD `4fd530b8a`: `ipd_lint._ORCH_ROW_RE` states it as a regex (`^- \[[ x]\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6}) REACHED ([A-Za-z][A-Za-z-]*)$`), `ipd_lint.ORCH_ROW_CANONICAL` states it again as a rendered string (`- [ ] E-NN CONFIRM <child-id6> REACHED <status>`), and the comment block above the regex states it a third time in prose. Approved spec `r07vma` OQ-01 names exactly this decay mode and carries a PROPOSED DIRECTION rather than a decision: "hold the row GRAMMAR as data in the rule module and render the refusal message, the `aw ipd scaffold` skeleton, and the documentation from that one source". The two surfaces agree today, which is precisely why nothing is failing and why a silent divergence would ship.
- Scope: IN: introduce a single grammar DATUM in `ipd_lint` and derive `_ORCH_ROW_RE`'s pattern and `ORCH_ROW_CANONICAL`'s string from it, with ZERO change to either value's bytes; add a public renderer that emits a conforming row from typed field values; consume that renderer in `ipd_authoring`'s orchestrator skeleton so the scaffold row is rendered rather than hand-written; add tests that are SENSITIVE to the derivation (perturbing the datum must move both derived surfaces together). OUT: the rule LOGIC in `orchestrator_row_conformance`, which is correct and whose behavior must not change by one diagnostic; `_ORCH_ROW_BLOCKING_CHECKPOINTS`, owned by approved plan `zojfn6`; the refusal MESSAGE wording and its three R7 content constants, which are already held as data and already have one renderer (`render_orchestrator_row_refusal`); the DOCUMENTATION surface, which OQ-01 lists but which does not exist to render (measured: the `ipd-spec` document states the grammar nowhere) and whose creation is a separate editorial decision recorded in OQ-01 below; the child skeleton; and the pre-existing orchestrator corpus.
- Scope-Paths: agent_workflows/ipd_lint.py, agent_workflows/ipd_authoring.py, tests/test_orchestrator_row_grammar_source.py, .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
- Item-Dependencies: executed:zojfn6
- Status: approved
- Readiness: go-pending-approval
- From-Spec: r07vma
- Work-Kind: chore
- Priority: low
- From-Backlog: u8dl3q
- Set: u8dl3q
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: l1xkrr
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): plan-review APPROVE WITH REVISIONS APPLIED
- 2026-10-02 /plan-review (opencode/its_direct-pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002 (HIGH, fixed), PR-003, PR-004, PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed). The sensitivity proof could not detect a literal revert (added a binding limb and required callable derivations); `aw specs note` cannot edit OQ-01's body (retargeted to a history record, added E-06/V-06); `zojfn6` has landed so E-04's landed branch is live, and the placeholder id6 is now single-sourced too. Full record: `.aw/records/reviews/20261002-u8dl3q-01-l1xkrr-hold-the-orchestrator-row-grammar-as-one-datum-and-render-th.review.md`.
- 2026-10-01 same-status (aw set): status unchanged (to-review)
- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from open backlog item `u8dl3q`. Every finding below was MEASURED in this lane at HEAD `4fd530b8a` by running the code, and the whole refactor was PROTOTYPED in process before being written down: a six-token grammar datum reproduces the shipped regex pattern and the shipped canonical string BYTE-IDENTICALLY, renders a row that the shipped regex accepts for all nine statuses, and a one-token perturbation moves both derived surfaces together (which is the sensitivity the tests must pin). Two of the backlog item's claims were corrected by that measurement: the third hand-written copy is NOT in `ipd_authoring` as the item states (the scaffold emits `- [ ] E-01 TODO one observable action.`, no grammar statement at all), and the refusal MESSAGE is already rendered from one place, so the residual surface is the GRAMMAR alone plus two prose copies outside this plan's reach.

## Goal

Make the typed child-tracking row grammar have ONE statement in the tree, so that a future change to it cannot leave the regex that refuses an author and the canonical form that instructs them disagreeing. This applies approved spec `r07vma` OQ-01's proposed direction to the surfaces that CAN be derived mechanically, and records honestly which of OQ-01's four named surfaces cannot.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one datum, two derived surfaces

- [x] E-01 RE-MEASURE the three statements and the derivation's feasibility at execution HEAD before editing anything, and RECORD what you find. Specifically: (a) read `ipd_lint._ORCH_ROW_RE.pattern` and `ipd_lint.ORCH_ROW_CANONICAL` in process and record both values verbatim; (b) confirm the byte-identity property the whole plan rests on by building the six-token datum E-02 specifies and asserting its derived pattern equals the shipped `.pattern` string and its derived canonical equals the shipped constant; (c) record whether `ipd_authoring` emits any statement of the grammar, because F-02 says it does NOT today and `zojfn6` is the plan that introduces one. IF THE BYTE-IDENTITY FAILS, STOP AND REPORT rather than adjusting either value to make it pass: changing the shipped pattern is a change to what the rule REFUSES, which this plan has no authority to make, and changing the canonical string changes what every refusal message tells an author to write.
  - Depends on: none
  - Expected outcome: both shipped values recorded verbatim; the derived-equals-shipped property asserted in process for both; `ipd_authoring`'s current emission recorded as either "no grammar statement" (F-02's measurement) or "a hand-written row" (post-`zojfn6`), with the actual text pasted either way.
  - Execution state: performed

- [x] E-02 INTRODUCE the grammar datum in `ipd_lint` and DERIVE `_ORCH_ROW_RE` from it, changing neither the compiled pattern's bytes nor any diagnostic. Hold the grammar as an ordered tuple of tokens where each token carries BOTH its rendered form and its regex fragment, so the two can only be changed together: the six tokens are the checkbox prefix (rendered `- [ ] `, fragment `- \[[ x]\] `), the item id (rendered `E-NN`, fragment `(E-[0-9]{2,})`), the literal ` CONFIRM `, the child field (rendered `<child-id6>`, fragment `([0-9a-z]{6})`), the literal ` REACHED `, and the status field (rendered `<status>`, fragment `([A-Za-z][A-Za-z-]*)`). Compile `_ORCH_ROW_RE` from `"^" + "".join(fragments) + "$"`, computed by a PURE module-level function that takes a token sequence and returns the pattern string (for example `_orch_row_pattern(tokens)`), called with the shipped datum. THE DERIVATION MUST BE A CALLABLE OVER AN ARBITRARY DATUM and not inline module-level code, because E-05's sensitivity proof has to run the SHIPPED derivation over a PERTURBED datum; a test that re-implements the join itself would be testing its own copy, not the module. THE TWO ANCHORS MUST BE APPLIED BY THE DERIVATION AND NOT CARRIED IN A TOKEN, because the existing comment block records that both anchors are load-bearing ("Widening either anchor re-opens the place R1a exists to close") and an anchor living inside a token is an anchor a token edit can delete. KEEP THE WHOLE EXISTING COMMENT BLOCK, which records four separate decisions (both anchors, the tolerated ticked box, and the deliberate refusal to parse continuation lines); it is the reasoning the datum does not carry, and deleting it to make room for the datum would destroy the record. The three capture groups MUST stay in their current ORDER and COUNT, because `orchestrator_row_conformance` reads `m.group(1)`, `m.group(2)` and `m.group(3)` positionally.
  - Depends on: E-01
  - Expected outcome: `ipd_lint._ORCH_ROW_RE.pattern` is byte-identical to E-01's recorded value while being computed from the datum by a pure pattern-derivation function that accepts any token sequence; the comment block is intact; `orchestrator_row_conformance` is untouched.
  - Execution state: performed

- [x] E-03 DERIVE `ORCH_ROW_CANONICAL` from the same datum and ADD the public row renderer that `ipd_authoring` will consume. `ORCH_ROW_CANONICAL` becomes the concatenation of the tokens' RENDERED forms, computed by a pure canonical-derivation function over a token sequence (the twin of E-02's pattern function, for the same reason), which E-01 proved is byte-identical to the shipped string, so `render_orchestrator_row_refusal` keeps emitting the same message with no edit to it. The renderer takes the three typed field values (the `E-NN` id, the child id6, the status) plus the ticked state and returns the row; implement it by substituting into the token sequence rather than by formatting a second template string, because a second template is the third hand-written copy this plan exists to remove. UPDATE THE `ORCH_ROW_CANONICAL` COMMENT, which currently says the instruction and the rule have one source "(spec OQ-01's proposed direction, partially)"; after this item the word "partially" is wrong for the grammar and must be replaced with what is now true, naming what OQ-01 still leaves open (the two prose copies, per F-04) rather than claiming OQ-01 closed.
  - Depends on: E-02
  - Expected outcome: `ORCH_ROW_CANONICAL` byte-identical to E-01's recorded value and computed from the datum; a renderer exists whose output the shipped regex accepts for every member of `ipd_schema.RECOGNIZED_STATUS` and for both checkbox states; the stale "partially" comment corrected.
  - Execution state: performed

### Task group 2: the scaffold consumes the renderer

- [x] E-04 MAKE `ipd_authoring`'s orchestrator skeleton row RENDERED rather than hand-written, and BRANCH on what E-01(c) measured. This item's content depends on whether approved plan `zojfn6` has landed, which is why this plan declares `- Item-Dependencies: executed:zojfn6`: that plan OWNS the change that gives the orchestrator skeleton a typed row at all, and authoring a second copy of that change here would collide with it. AT REVIEW HEAD `bef6b9756` `zojfn6` HAS LANDED (it is in `executed/`), so the landed branch is expected; still confirm it from E-01(c). IN THE LANDED BRANCH, replace the hand-written `action_line` literal in `ipd_authoring._exec_placeholder_leaf` with a call to E-03's renderer, passing the same placeholder id6 the skeleton's own child table declares. That id6 is currently hand-written TWICE in `ipd_authoring` (the `c0ch01` cell of the child-table placeholder and the `c0ch01` inside the row literal), so hoist it to ONE module-private constant used by both, otherwise the row and the table it must resolve against can still drift apart, which is the same decay mode one level down, and verify the emitted bytes are UNCHANGED (this is a refactor of HOW the row is produced, not of WHAT is produced, so the byte-pinned orchestrator template must not need regenerating). IF IT HAS NOT, do NOT introduce a typed row here: record that the scaffold surface remains `zojfn6`'s to deliver, state in the plan's own evidence that this item is a no-op for that reason, and leave `ipd_authoring` untouched. DO NOT ADD A SECOND PATH: `ipd_lint` already imports `ipd_authoring` lazily inside a function body (the `check.ipd-draft-ready-to-review` nudge does exactly this), so the dependency direction for the renderer is `ipd_authoring` importing `ipd_lint`, which it ALREADY does at module scope as `LINT`; no new import and no inversion is needed.
  - Depends on: E-03
  - Expected outcome: either the scaffold's orchestrator row is produced by E-03's renderer with byte-identical output (and `tests/test_ipd_templates.py` still passes with no template regeneration), or the item is recorded as a deliberate no-op naming `zojfn6` as the owner, with the measurement that justified it.
  - Execution state: performed

- [x] E-05 ADD a new test module `tests/test_orchestrator_row_grammar_source.py` that is SENSITIVE to the derivation rather than merely asserting the current values. Four behaviors, each driving real code and asserting real outputs: (1) the derived pattern and the derived canonical both still accept and describe the same rows, proven by rendering a row for EVERY member of `ipd_schema.RECOGNIZED_STATUS` plus both checkbox states and asserting `orchestrator_row_conformance` reports each conforming inside a real orchestrator document; (2) THE SENSITIVITY PROOF, which is the test that makes this plan worth executing, in TWO LIMBS that are only meaningful together: (2a) THE BINDING limb asserts `_ORCH_ROW_RE.pattern` equals the module's pattern-derivation function applied to the shipped datum, and `ORCH_ROW_CANONICAL` equals the canonical-derivation function applied to the same datum, which is what FAILS if either surface is reverted to an independent literal that later diverges; (2b) THE PERTURBATION limb runs BOTH shipped derivation functions over a PERTURBED copy of the datum (substituting one token, as the prototype did with ` CONFIRM ` to ` VERIFY `) and asserts that both outputs changed and that the perturbed pattern accepts the perturbed rendered row, so the two functions are shown to consume the same tokens. Neither limb alone suffices: (2b) without (2a) stays green when the shipped constants are reverted to literals, because it never looks at them; (3) a row rendered by the renderer is accepted while a hand-mangled variant of it (trailing prose after the status, an over-indented row) is refused with reason `ORCH_ROW_NOT_TYPED`, which pins that the derivation did not widen either anchor; (4) the refusal message for a non-conforming row still CONTAINS the canonical form, which is what proves the message a refused author reads is the derived one. DO NOT WRITE A CODE-STRUCTURE PIN: this module must not read `ipd_lint.py`'s source text with `inspect`, `ast`, or a regex, must not count call sites, and must not assert that any comment or docstring is unchanged (AGENTS.md's test-outcomes rule and GUIDING_PRINCIPLES P16). Assert the derived VALUES and the BEHAVIOR of the rendered rows against the shipped checker.
  - Depends on: E-04
  - Expected outcome: a new test module whose four behaviors pass; the binding limb (2a) demonstrably fails when ONE surface is reverted to an independent literal that differs from the derived value (state how that was confirmed and paste the failure).
  - Execution state: performed

### Task group 3: record the partial application in the spec

- [x] E-06 APPEND ONE WORKFLOW-HISTORY RECORD TO SPEC `r07vma` WITH `aw specs note`, AND EDIT NOTHING ELSE IN IT. `aw specs note` "Append[s] a workflow-history record to a spec WITHOUT changing its status" (its `--help`); it does NOT edit an open question's rationale, so the record lands in the spec's `## Workflow history`, not in OQ-01's body. The message states three facts measured at execution: the GRAMMAR is now held as one datum in `ipd_lint` with the pattern, the canonical form and the scaffold row derived from it; the "render the refusal message" clause was ALREADY satisfied before this plan (F-03); and the residue is the prose copies (F-04, re-counted at execution) plus the absent documentation surface (F-05), so OQ-01 stays `open` with its maintainer owner. Do NOT hand-edit OQ-01, R1a's template, or the spec's `- Status:`. If the verb refuses, STOP and report.
  - Depends on: E-05
  - Expected outcome: exactly one new history line in the `r07vma` spec, written by `aw specs note`; no other line of the spec changed; `aw check` reports no new finding on it.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every anchor in this plan is a symbol or a quoted string for that reason.
- THE SUITE IS RUN BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so `python3 -m pytest` is already quiet, parallel and fast-scoped. Adding `-q` compounds into `-qq` and suppresses the `N passed` line this plan's validation requires pasted; `-n0` makes the run several times slower.
- ONE IMPLEMENTATION OF THE RULE (spec `r07vma` R3). `orchestrator_row_conformance` is the single conformance evaluator and `tests/test_orchestrator_shape_composed.py::TestOneRuleTwoConsumers` pins that both consumers reach it. This plan adds NO second regex and NO second conformance path; it reduces the number of hand-written grammar statements from two in code to one.
- TESTS ASSERT OUTCOMES, NOT CODE STRUCTURE. AGENTS.md forbids a test that reads production source with `inspect`/`ast`/regex or asserts on symbol censuses or unchanged comment text, and GUIDING_PRINCIPLES P16 allows content verification only where the text itself is the artifact under test. E-05 is written to that rule, which is why the sensitivity proof perturbs a DATUM and observes the derived values rather than grepping the module.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT. This plan declares the `r07vma` spec file in `- Scope-Paths:` because E-06 appends a partial-application record to that spec's workflow history, and an undeclared spec edit defeats the finalize scope gate. The amendment is a RECORD of partial application plus the surviving residue; it does NOT change `- Status: approved` and does NOT resolve OQ-01, whose Owner is the maintainer.

## Findings

| # | Finding | Evidence (measured in this lane at HEAD `4fd530b8a`) |
|---|---|---|
| F-01 | THE DERIVATION IS BYTE-EXACT, WHICH IS WHAT MAKES THIS A SAFE REFACTOR RATHER THAN A BEHAVIOR CHANGE. A six-token datum carrying a rendered form and a regex fragment per token reproduces `_ORCH_ROW_RE.pattern` and `ORCH_ROW_CANONICAL` byte-identically. So the whole change can be made with ZERO change to what the rule accepts and ZERO change to any refusal message, and E-01 can assert that property before any edit lands. | Prototyped in process: derived pattern `== _ORCH_ROW_RE.pattern` is True; derived canonical `== ORCH_ROW_CANONICAL` is True; a row rendered from the datum (`- [ ] E-01 CONFIRM abc123 REACHED executed`) matches the shipped regex; all nine members of `ipd_schema.RECOGNIZED_STATUS` render to a matching row; a ticked row (`- [x] E-07 CONFIRM tmp1d6 REACHED executed`) also matches. |
| F-02 | THE BACKLOG ITEM'S THIRD COPY DOES NOT EXIST YET, so this plan's scaffold half is a DEPENDENT of `zojfn6` rather than a peer of it. The item says `ipd_authoring` "emits a third hand-written copy in the skeleton"; measured, `build_skeleton(kind="orchestrator", ...)` emits the single exec row `- [ ] E-01 TODO one observable action.` and the prose placeholder `TODO: child IPD table (Order \| File \| What it does \| Depends on).`, which is no grammar statement at all. The item's own prose is consistent with this once read carefully ("after it lands"), but the summary line reads as present tense and would mislead an executor. | `A.build_skeleton(kind="orchestrator", title="T", author="a", when="2026-10-01", set_name="s", order=0, plan_id="tmp1d6")` exec rows: `['- [ ] E-01 TODO one observable action.']`. `orchestrator_row_conformance` on that skeleton: `conforming=False`, row E-01 refused `not-a-typed-child-tracking-row`, `table_reason` "no readable `## Child IPDs, sequence, and dependencies` table". Plan `zojfn6` (`- Status: approved`, Set `htce8t`) E-02 is the item that introduces the typed row. RE-MEASURED AT REVIEW HEAD `bef6b9756`: `zojfn6` is now in `executed/`, and `ipd_authoring._exec_placeholder_leaf` carries the hand-written literal `action_line = "- [ ] E-01 CONFIRM c0ch01 REACHED executed"` while `ipd_authoring`'s child-table placeholder separately hand-writes `` `c0ch01` `` in the row `"\| 01 \| `c0ch01` \| TODO child plan filename ..."`. So the third copy NOW EXISTS and E-04's LANDED branch is the live one. |
| F-03 | THE REFUSAL MESSAGE IS ALREADY SINGLE-SOURCED, so OQ-01's "render the refusal message" clause is ALREADY SATISFIED and must not be re-done. `render_orchestrator_row_refusal` is documented as "The ONLY place this message is composed", it is the only composer in the module (both refusal sites in `orchestrator_row_conformance` call it), and the three R7 content requirements are already held as the data constants `ORCH_ROW_INVARIANT`, `ORCH_ROW_NO_DELETION` and `ORCH_ROW_REMEDIES` with a comment saying they are data "so the message cannot drift from the rule". Deriving `ORCH_ROW_CANONICAL` is therefore sufficient to make the message itself derived, with no edit to the renderer. | `grep -c` for `render_orchestrator_row_refusal` in `agent_workflows/`: one definition, two call sites, all three in `ipd_lint.py`. The constants and their stated rationale are in the module beside `ORCH_ROW_CANONICAL`. |
| F-04 | TWO PROSE COPIES OF THE GRAMMAR EXIST OUTSIDE THIS PLAN'S REACH, and one of them is an approved spec, so the honest claim is PARTIAL closure and not closure. A whole-tree census of the exact canonical string over tracked files finds it in nine files; excluding terminal plans and review records, the live statements are: `agent_workflows/ipd_lint.py` (2, both collapsing to one datum here), `.aw/system/workflows/plan-review-long/02-review-and-revise.md` (1, "matching `- [ ] E-NN CONFIRM <child-id6> REACHED <status>`"), approved spec `r07vma` (1, in R1a's normative template), and pending plan `rtvdak` (1, quoting the grammar in an OQ rationale). A workflow body and a spec are PROSE a human reads, with no render step and no generator, so there is nothing to derive them from without inventing a templating mechanism for workflow bodies, which is far larger than this item. | Census run over `git ls-files`: the exact string `- [ ] E-NN CONFIRM <child-id6> REACHED <status>` appears in `ipd_lint.py` (2), `02-review-and-revise.md` (1), `r07vma` spec (1), `rtvdak` plan (1), plus 5 terminal plan records. The partial phrase `CONFIRM <child-id6> REACHED <status>` adds one more occurrence in the spec and one in plan `zojfn6`. |
| F-05 | OQ-01's DOCUMENTATION CLAUSE HAS NO TARGET, which is the backlog item's own closing note and it holds. The `ipd-spec` document states this grammar nowhere, so "render the documentation from that one source" would require first DECIDING that a documentation surface should exist. That is an editorial call about what the IPD spec documents, not a refactor, and it is the maintainer's: `r07vma` OQ-01 carries `- Owner: maintainer` and `- Status: open`. This plan therefore does not create one and records the gap in OQ-01 below. | Searching `.aw/records/specs/implemented/20260726-1340-01-ipd-spec.spec.md` for `IPD-S407`, `typed child-tracking`, and `CONFIRM` returns nothing. `r07vma` OQ-01 is `- Status: open`, `- Owner: maintainer`, `- Blocking: no` (OQ-02 and OQ-03 in the same spec are both `resolved`, so `open` here is a live state and not a stale one). |
| F-06 | THE ANCHORS AND THE GROUP ORDER ARE THE TWO WAYS THIS REFACTOR COULD SILENTLY BREAK THE RULE, which is why E-02 constrains both explicitly. The module's own comment states both anchors are deliberate ("`^` refuses an over-indented row or one that merely CONTAINS the phrase mid-line, and `$` refuses trailing prose after the status ... Widening either anchor re-opens the place R1a exists to close"), and `orchestrator_row_conformance` reads the three captures POSITIONALLY as `m.group(1)`/`m.group(2)`/`m.group(3)`, so a datum that reorders tokens or adds a capturing group would mis-assign `child_id6` and `status` while still compiling and still matching. | The comment block above `_ORCH_ROW_RE` states the anchor rationale. `orchestrator_row_conformance` body: `ident = leaf.ident or (m.group(1) if m else "")` and `child_id6, status = m.group(2), m.group(3)`. |
| F-07 | NO SUITE FAILURE IS EXPECTED, because nothing observable changes. The three test modules that exercise this area pass at HEAD and the refactor is byte-exact, so a RED test during execution is a signal the derivation drifted rather than a fixture to update. Treat any failure in `tests/test_orchestrator_shape_composed.py`, `tests/test_orchestrator_shape_gate.py`, `tests/test_ipd_templates.py` or `tests/test_orchestrator_retirement.py` as a STOP condition. | `python3 -m pytest tests/test_orchestrator_shape_composed.py tests/test_orchestrator_shape_gate.py tests/test_ipd_templates.py` reports `35 passed`. Full bare suite at authoring HEAD: `3814 passed, 2 skipped, 3 warnings in 95.47s`, with `208 tests were deselected by -m/-k`. |

## Proposed changes (ordered, validatable)

1. `agent_workflows/ipd_lint.py`: add the ordered grammar-token datum; compile `_ORCH_ROW_RE` from its fragments with the two anchors applied by the derivation; keep the existing comment block whole (E-02).
2. `agent_workflows/ipd_lint.py`: derive `ORCH_ROW_CANONICAL` from the same datum's rendered forms; add the public row renderer; correct the stale "(spec OQ-01's proposed direction, partially)" comment to state what is now true and what F-04 leaves open (E-03).
3. `agent_workflows/ipd_authoring.py`: consume the renderer for the orchestrator skeleton row IF `zojfn6` has landed, with byte-identical output; otherwise leave untouched and record why (E-04).
4. `tests/test_orchestrator_row_grammar_source.py`: four behavioral tests including the perturbation sensitivity proof (E-05).
5. `.aw/records/specs/approved/20260919-r07vma-01-r07vma-...spec.md`: append one workflow-history record via `aw specs note` stating that the GRAMMAR half is now rendered from one datum, that the refusal-message half was already satisfied, and that the prose copies (F-04) and the absent documentation surface (F-05) remain; OQ-01's body, `- Status: open`, and the spec's `- Status: approved` are untouched (E-06; see Spec / documentation sync).

## Deferred / out of scope (with reason)

- RESOLVING `r07vma` OQ-01. Its `- Owner:` is the maintainer and its documentation clause requires an editorial decision this plan cannot make (F-05). This plan applies the direction to the derivable surfaces and records the residue; it leaves OQ-01 `open`.
  - Carrier-Evidence: .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
- DERIVING THE TWO PROSE COPIES (the `plan-review-long` step body and the spec's own R1a template). F-04: a workflow body and a spec are human-read prose with no render step; adding a templating mechanism for workflow bodies is a far larger change and would need its own spec.
  - Carrier-Declined: human-readable prose surfaces in workflow and spec with no render step, outside plan scope
- CREATING A DOCUMENTATION SURFACE FOR THE GRAMMAR in the `ipd-spec` document. F-05: there is nothing to render into, and whether one should exist is the maintainer's call.
  - Carrier-Declined: maintainer editorial decision whether to create a documentation surface in the IPD spec
- `_ORCH_ROW_BLOCKING_CHECKPOINTS` and the `pre-execution` gate. Owned by approved plan `zojfn6` E-06. This plan must not touch that constant or the stale comment block above it; a collision there would make whichever plan lands second fail.
  - Carrier-Evidence: .aw/records/plans/executed/20260929-htce8t-01-zojfn6-make-the-scaffolded-orchestrator-skeleton-conform-to-the-typ.ipd.md
- THE SCAFFOLD'S CHILD TABLE and the `child` skeleton. `zojfn6` E-02 owns the table, and the `child` kind has no orchestrator rows at all (`orchestrator_row_conformance` reports `applies=False` for it).
  - Carrier-Evidence: .aw/records/plans/executed/20260929-htce8t-01-zojfn6-make-the-scaffolded-orchestrator-skeleton-conform-to-the-typ.ipd.md
- MIGRATING THE EXISTING ORCHESTRATOR CORPUS. Nothing about this plan changes what conforms, so no corpus is affected.
  - Carrier-Declined: no-op since the refactor is byte-exact and alters no conformance rules or corpus behavior

## Scope check

- Over-scope: none. The spec file is declared because E-06's residue record is written into it; without that declaration the finalize scope gate would report an undeclared spec edit.
- Under-scope: the two prose copies and the absent documentation surface are NOT closed here and are recorded in OQ-01 and in Deferred above, so `r07vma` OQ-01 remains legitimately open. An executor must not report this plan as closing OQ-01.

## Required tests / validation

- `python3 -m pytest tests/test_orchestrator_row_grammar_source.py` (the new module, all four behaviors).
- `python3 -m pytest tests/test_orchestrator_shape_composed.py tests/test_orchestrator_shape_gate.py tests/test_ipd_templates.py tests/test_orchestrator_retirement.py tests/test_ipd_authoring.py tests/test_ipd_lint.py` (every module that touches the rule, the scaffold, or the byte-pinned templates).
- A full bare `python3 -m pytest`, with the summary line pasted and the failing node-ID delta against a baseline measured IN THE EXECUTION LANE (the `3814 passed, 2 skipped` figure in F-07 is drift context, not the bar).
- `aw ipd lint --phase pre-transition` on this plan, reporting conforming.
- `aw check` over the tree, to confirm the spec amendment introduced no finding.

## Spec / documentation sync

APPROVED SPEC `r07vma` IS ANNOTATED, AND DECLARED (E-06). The annotation is ONE workflow-history record appended by `aw specs note`, which appends history and cannot edit an open question's body (corrected at review; the earlier text said the amendment went into OQ-01's rationale, which that verb cannot do), and it records three facts an executor measured: the GRAMMAR is now held as one datum and both derived surfaces come from it; the "render the refusal message" clause was ALREADY satisfied before this plan (F-03) and needed no work; and the residue is the two prose copies (F-04) plus the absent documentation surface (F-05). Record it with `aw specs note` and nothing else. DO NOT use any `aw specs set` form and DO NOT change OQ-01's `- Status: open` or its `- Owner: maintainer`: an agent has no authority to resolve a maintainer-owned question, and OQ-01's documentation clause is genuinely unanswered. DO NOT touch R1a's normative template (the spec's own statement of the grammar): it is the normative text the code implements, F-04 explains why it cannot be derived, and rewriting normative text is not what this plan is for.

NOTHING MECHANICAL ENFORCES THAT DISCIPLINE, and saying so is the point. The `status-untooled` pre-commit gate delegates to `check_engine.check_status_untooled`, which is scoped to the plans tree and never reads a `.spec.md`; `check_engine.check_spec_review_attestation` is scoped to `- Status: reviewed` and is silent on an approved spec. So use `aw specs note` because it is correct, not because something will refuse a hand-append. If the verb refuses, STOP and report rather than editing the spec by hand.

The `ipd-spec` document is NOT updated: F-05 measured that it states this grammar nowhere, and creating that surface is the maintainer's editorial call (OQ-01 below). No user-facing documentation under `docs/` describes the orchestrator row grammar either, so there is no user-facing prose to keep in step.

## Open questions

### OQ-01: Should the IPD specification document state the orchestrator row grammar at all, and if so should it be generated?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: maintainer-owned editorial open question on spec documentation; preserved in approved spec r07vma OQ-01
- Resolution or deferral rationale: NOT blocking, because every item in this plan is executable and testable without an answer: the grammar's two CODE statements collapse to one datum regardless of what the documentation does. It is recorded rather than dropped because it is the one clause of `r07vma` OQ-01 this plan cannot discharge, and leaving it unstated would make a future reader think OQ-01 was fully applied. MEASURED: the `ipd-spec` document mentions neither `IPD-S407` nor `typed child-tracking` nor `CONFIRM`, so there is no documentation copy to keep in step and therefore no drift today; the risk is the opposite one, that an author looking for the grammar in the spec finds nothing and reaches for the code. THE THREE OPTIONS, with their costs: (a) leave it absent, which is the status quo, costs nothing, and relies on the scaffold showing the shape (which is OQ-02's argument for TYPED in `r07vma` and is what `zojfn6` makes true); (b) state it in the `ipd-spec` document by hand, which re-creates the exact decay mode `r07vma` OQ-01 names and is the option this plan's whole direction argues against; (c) GENERATE that section from the datum this plan introduces, which would need a docs-render path for a `.spec.md` file, and the tree has a precedent for generated doc tables (`docs_render.py` renders registry-backed tables into `docs/`) but NONE for generating into a spec record. This plan takes (a) by inaction and does not foreclose (c). An agent should not decide this: it is a question about what a human-approved spec document contains.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the in-process measurement: `_ORCH_ROW_RE.pattern` and `ORCH_ROW_CANONICAL` verbatim as read at the execution HEAD, plus the two boolean results showing the datum-derived pattern and canonical equal them. Paste the exec rows `build_skeleton(kind="orchestrator", ...)` emits at that HEAD, so E-04's branch is decided by evidence rather than by assumption, and state which branch it selects. Name the HEAD commit. If either byte-identity is False, paste the two differing strings and STOP. (At review HEAD `bef6b9756` both were True and the skeleton row was `- [ ] E-01 CONFIRM c0ch01 REACHED executed`, selecting the landed branch; re-measure, do not copy.)
  - Observed evidence:
    HEAD commit: `ba1b81c82e9e56231cecf51b71fa8db1f405ba28`
    In-process measurement output:
    ```
    shipped_pattern: '^- \\[[ x]\\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6}) REACHED ([A-Za-z][A-Za-z-]*)$'
    shipped_canonical: '- [ ] E-NN CONFIRM <child-id6> REACHED <status>'
    derived_pattern: '^- \\[[ x]\\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6}) REACHED ([A-Za-z][A-Za-z-]*)$'
    derived_canonical: '- [ ] E-NN CONFIRM <child-id6> REACHED <status>'
    pattern equals: True
    canonical equals: True
    ipd_authoring build_skeleton exec rows:
      - [ ] E-01 CONFIRM c0ch01 REACHED executed
    ```
    Selected branch: landed branch (`zojfn6` is in `executed/` at `.aw/records/plans/executed/20260929-htce8t-01-zojfn6-make-the-scaffolded-orchestrator-skeleton-conform-to-the-typ.ipd.md`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the `git diff` of `_ORCH_ROW_RE`'s region showing the pattern is now computed from the datum, plus an in-process print of `_ORCH_ROW_RE.pattern` demonstrating it is byte-identical to V-01's recorded value. The diff must show the existing comment block RETAINED (quote its anchor-rationale sentence and its continuation-lines sentence from the post-change file to prove they survive) and must show `orchestrator_row_conformance` unchanged. Paste the capture-group proof: for one conforming row, print `m.group(1)`, `m.group(2)`, `m.group(3)` and show they are the item id, the child id6 and the status in that order.
  - Observed evidence:
    `git diff` of `_ORCH_ROW_RE` region:
    ```diff
    @@ -244,9 +244,52 @@ _CONTINUATION_SUBFIELDS: FrozenSet[str] = frozenset(
     # context and spec Section 3a limit 1 records that as an honest limit: the prose residue remains the
     # semantic probe's business (`77tr3o` R-12), and an implementer who extends this pattern into the
     # continuation lines has changed the contract and broken that division of labour.
    -_ORCH_ROW_RE = re.compile(
    -    r"^- \[[ x]\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6}) REACHED ([A-Za-z][A-Za-z-]*)$"
    +class OrchestratorRowToken(NamedTuple):
    +    """One token of the orchestrator child-tracking row grammar.
    +
    +    Carries BOTH the rendered form and the regex fragment so the two can only be changed together.
    +    """
    +
    +    rendered: str
    +    fragment: str
    +
    +
    +ORCH_ROW_GRAMMAR: Tuple[OrchestratorRowToken, ...] = (
    +    OrchestratorRowToken("- [ ] ", r"- \[[ x]\] "),
    +    OrchestratorRowToken("E-NN", r"(E-[0-9]{2,})"),
    +    OrchestratorRowToken(" CONFIRM ", r" CONFIRM "),
    +    OrchestratorRowToken("<child-id6>", r"([0-9a-z]{6})"),
    +    OrchestratorRowToken(" REACHED ", r" REACHED "),
    +    OrchestratorRowToken("<status>", r"([A-Za-z][A-Za-z-]*)"),
    +)
    +_ORCH_ROW_GRAMMAR = ORCH_ROW_GRAMMAR
    +
    +
    +def orch_row_pattern(
    +    tokens: Sequence[OrchestratorRowToken] = ORCH_ROW_GRAMMAR,
    +) -> str:
    +    """Derive the anchored regex pattern from an orchestrator row grammar token sequence.
    +
    +    THE TWO ANCHORS MUST BE APPLIED BY THE DERIVATION AND NOT CARRIED IN A TOKEN:
    +    both anchors are load-bearing ('Widening either anchor re-opens the place R1a exists
    +    to close') and an anchor living inside a token is an anchor a token edit can delete.
    +    """
    +    return "^" + "".join(t[1] for t in tokens) + "$"
    +
    +
    +_orch_row_pattern = orch_row_pattern
    +
    +
    +def orch_row_canonical(
    +    tokens: Sequence[OrchestratorRowToken] = ORCH_ROW_GRAMMAR,
    +) -> str:
    +    """Derive the canonical orchestrator row string from a grammar token sequence."""
    +    return "".join(t[0] for t in tokens)
    +
    +
    +_orch_row_canonical = orch_row_canonical
    +
    +_ORCH_ROW_RE = re.compile(orch_row_pattern())
    ```
    Retained comment block verification:
    - Anchor-rationale sentence: "FULLY ANCHORED AT BOTH ENDS ON PURPOSE. `^` refuses an over-indented row or one that merely CONTAINS the phrase mid-line, and `$` refuses trailing prose after the status, which is the shape a deliverable would take if the grammar let a row carry a second clause (\"... REACHED executed and then re-run the suite\"). Widening either anchor re-opens the place R1a exists to close."
    - Continuation-lines sentence: "CONTINUATION LINES ARE DELIBERATELY NOT MATCHED HERE. R1a leaves them unparsed as human-readable context and spec Section 3a limit 1 records that as an honest limit: the prose residue remains the semantic probe's business (`77tr3o` R-12), and an implementer who extends this pattern into the continuation lines has changed the contract and broken that division of labour."
    `orchestrator_row_conformance` unchanged: `git diff agent_workflows/ipd_lint.py` shows no edits to `orchestrator_row_conformance`.
    In-process print of `_ORCH_ROW_RE.pattern`:
    `'^- \\[[ x]\\] (E-[0-9]{2,}) CONFIRM ([0-9a-z]{6}) REACHED ([A-Za-z][A-Za-z-]*)$'` (byte-identical to V-01).
    Capture-group proof:
    For conforming row `- [ ] E-01 CONFIRM c0ch01 REACHED executed`:
    `m.group(1)`: `'E-01'` (item id)
    `m.group(2)`: `'c0ch01'` (child id6)
    `m.group(3)`: `'executed'` (status)
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste an in-process print of `ORCH_ROW_CANONICAL` showing it byte-identical to V-01's recorded value while derived from the datum. Paste a full refusal message produced by `render_orchestrator_row_refusal` for a non-conforming row and show it contains the derived canonical form, proving the message an author reads is the derived one with no edit to the renderer. Paste the renderer's output for EVERY member of `ipd_schema.RECOGNIZED_STATUS` and for both checkbox states, each shown matching `_ORCH_ROW_RE`. Paste the `git diff` of the `ORCH_ROW_CANONICAL` comment showing the word "partially" replaced by a statement that names the surviving residue.
  - Observed evidence:
    In-process print of `ORCH_ROW_CANONICAL`:
    `'- [ ] E-NN CONFIRM <child-id6> REACHED <status>'` (byte-identical to V-01).
    Full refusal message from `render_orchestrator_row_refusal`:
    `E-01 is not a typed child-tracking row (not-a-typed-child-tracking-row): the row does not match the typed grammar exactly. Write it as \`- [ ] E-NN CONFIRM <child-id6> REACHED <status>\`. WHY: an Order-0 orchestrator is retired PROGRAMMATICALLY, with the pre-transition E-*/V-* checkpoint deliberately skipped, so a step parked on a parent is performed by NOBODY and is marked complete having never run. DELETING the item is NOT an acceptable fix: the checklist is what makes a Set execute completely and in order when it is run BY HAND, so deleting it causes the lost work this rule prevents. FIX: two remedies are legitimate and this rule does not prescribe either: MOVE the step into a child plan whose \`- Item-Dependencies:\` put it in the right order, OR REMOVE it because a child already covers it (which is removal for redundancy, not deletion to silence this rule). Row as written: '- [ ] E-01 invalid'`
    Contains canonical form: True (`ORCH_ROW_CANONICAL in msg` is True).
    Renderer output for all 9 members of `ipd_schema.RECOGNIZED_STATUS` and both checkbox states matching `_ORCH_ROW_RE`:
    - `- [ ] E-01 CONFIRM abc123 REACHED draft -> matched: ('E-01', 'abc123', 'draft')`
    - `- [x] E-01 CONFIRM abc123 REACHED draft -> matched: ('E-01', 'abc123', 'draft')`
    - `- [ ] E-01 CONFIRM abc123 REACHED approved -> matched: ('E-01', 'abc123', 'approved')`
    - `- [x] E-01 CONFIRM abc123 REACHED approved -> matched: ('E-01', 'abc123', 'approved')`
    - `- [ ] E-01 CONFIRM abc123 REACHED reusable -> matched: ('E-01', 'abc123', 'reusable')`
    - `- [x] E-01 CONFIRM abc123 REACHED reusable -> matched: ('E-01', 'abc123', 'reusable')`
    - `- [ ] E-01 CONFIRM abc123 REACHED reviewed -> matched: ('E-01', 'abc123', 'reviewed')`
    - `- [x] E-01 CONFIRM abc123 REACHED reviewed -> matched: ('E-01', 'abc123', 'reviewed')`
    - `- [ ] E-01 CONFIRM abc123 REACHED executed -> matched: ('E-01', 'abc123', 'executed')`
    - `- [x] E-01 CONFIRM abc123 REACHED executed -> matched: ('E-01', 'abc123', 'executed')`
    - `- [ ] E-01 CONFIRM abc123 REACHED not-executed -> matched: ('E-01', 'abc123', 'not-executed')`
    - `- [x] E-01 CONFIRM abc123 REACHED not-executed -> matched: ('E-01', 'abc123', 'not-executed')`
    - `- [ ] E-01 CONFIRM abc123 REACHED superseded -> matched: ('E-01', 'abc123', 'superseded')`
    - `- [x] E-01 CONFIRM abc123 REACHED superseded -> matched: ('E-01', 'abc123', 'superseded')`
    - `- [ ] E-01 CONFIRM abc123 REACHED to-review -> matched: ('E-01', 'abc123', 'to-review')`
    - `- [x] E-01 CONFIRM abc123 REACHED to-review -> matched: ('E-01', 'abc123', 'to-review')`
    - `- [ ] E-01 CONFIRM abc123 REACHED auto-approved -> matched: ('E-01', 'abc123', 'auto-approved')`
    - `- [x] E-01 CONFIRM abc123 REACHED auto-approved -> matched: ('E-01', 'abc123', 'auto-approved')`
    `git diff` of the `ORCH_ROW_CANONICAL` comment:
    ```diff
    @@ -1737,9 +1780,42 @@ ORCH_ROW_REMEDIES = (
         "plan whose `- Item-Dependencies:` put it in the right order, OR REMOVE it because a child "
         "already covers it (which is removal for redundancy, not deletion to silence this rule)"
     )
    -#: The canonical form, rendered from the same grammar the check enforces, so the instruction an author
    -#: reads and the rule that refuses them have ONE source (spec OQ-01's proposed direction, partially).
    -ORCH_ROW_CANONICAL = "- [ ] E-NN CONFIRM <child-id6> REACHED <status>"
    +#: The canonical form, derived from the single grammar datum that compiles _ORCH_ROW_RE,
    +#: so the instruction an author reads, the regex that refuses them, and the scaffold
    +#: skeleton have ONE source (spec OQ-01's proposed direction applied to code; the two
    +#: prose copies in plan-review-long and spec r07vma R1a, plus the absent documentation
    +#: surface, survive outside this plan's reach).
    +ORCH_ROW_CANONICAL = orch_row_canonical()
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: EITHER (landed branch) the `git diff` of `ipd_authoring` showing the hand-written row replaced by a renderer call, PLUS proof the emitted bytes are unchanged (a before/after comparison of `build_skeleton(kind="orchestrator", ...)` output showing equality) and a passing `python3 -m pytest tests/test_ipd_templates.py` with NO template file regenerated (`git status --short` on `.aw/system/workflows/assess/templates/` must be empty), plus a search of `ipd_authoring.py` showing the placeholder child id6 is now written once; OR (not-landed branch) the measured `zojfn6` status from disk plus `git status --short agent_workflows/ipd_authoring.py` showing NO modification, with the explicit statement that the scaffold surface remains `zojfn6`'s to deliver. A claim that this item was "done" without one of those two evidence sets is not acceptable.
  - Observed evidence:
    Landed branch taken (`zojfn6` is in `executed/`):
    `git diff agent_workflows/ipd_authoring.py`:
    ```diff
    @@ -35,6 +35,9 @@ UNASSIGNED_MARKER = "E-NEW"
     # Scaffold
     # --------------------------------------------------------------------------------------

    +# The stable placeholder child id6 used in the scaffold's child table and checklist row (plan l1xkrr E-04).
    +_ORCH_PLACEHOLDER_CHILD_ID6 = "c0ch01"
    +
     # Per-heading placeholder body used in a fresh skeleton (kept minimal but conformant).
     _SECTION_BODY = {
         S.H_WORKFLOW_HISTORY: "- {date} draft ({author}): created.",
    @@ -64,7 +67,7 @@ _SECTION_BODY = {
         S.H_CHILD_IPDS: (
             "| Order | Id | File | What it does | Depends on |\n"
             "|---|---|---|---|---|\n"
    -        "| 01 | `c0ch01` | TODO child plan filename | TODO what it does. | none |"
    +        f"| 01 | `{_ORCH_PLACEHOLDER_CHILD_ID6}` | TODO child plan filename | TODO what it does. | none |"
         ),
         S.H_COMPLETION: '- TODO: each whole-Set criterion, ending with "Owner: <child-id6>" naming the child plan that performs it.',
         S.H_CROSS_IPD: "- TODO: each cross-child consistency check, naming the child plan (by id6) that performs it; a check no child performs needs a new child plan.",
    @@ -98,7 +101,11 @@ def _exec_placeholder_leaf(kind: str = "child") -> str:
         # immediately. Authors add further work as `E-NEW` leaves and run `aw ipd sync` to assign them.
         # An orchestrator emits a conforming typed child-tracking row (plan zojfn6 E-02).
         if kind == S.KIND_ORCHESTRATOR:
    -        action_line = "- [ ] E-01 CONFIRM c0ch01 REACHED executed"
    +        action_line = LINT.render_orchestrator_row(
    +            ident="E-01",
    +            child_id6=_ORCH_PLACEHOLDER_CHILD_ID6,
    +            status="executed",
    +        )
         else:
             action_line = "- [ ] E-01 TODO one observable action."
         return (
    ```
    Proof emitted bytes unchanged:
    `build_skeleton(kind="orchestrator", ...)` equality before/after confirmed (`"- [ ] E-01 CONFIRM c0ch01 REACHED executed"` in output and `| 01 | \`c0ch01\` | TODO child plan filename | TODO what it does. | none |` in output).
    `python3 -m pytest tests/test_ipd_templates.py`: `10 passed in 9.66s`.
    `git status --short .aw/system/workflows/assess/templates/`: empty (0 template files modified or regenerated).
    Search of `agent_workflows/ipd_authoring.py` for placeholder child id6:
    `grep -n "c0ch01" agent_workflows/ipd_authoring.py`:
    `39:_ORCH_PLACEHOLDER_CHILD_ID6 = "c0ch01"`
    (exactly one occurrence).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the passing output of `python3 -m pytest tests/test_orchestrator_row_grammar_source.py` with node IDs, then the broader module run named in Required tests, then a FULL bare `python3 -m pytest` summary line measured in this lane with the after-minus-before failing node-ID set (must be EMPTY) against a baseline measured in the SAME lane. THE SENSITIVITY PROOF MUST BE DEMONSTRATED, NOT ASSERTED: show that the BINDING limb (2a) discriminates: locally replace `ORCH_ROW_CANONICAL` (or the pattern) with an independent literal that differs from the derived value by one token, run the module, paste the failure naming limb (2a), restore, paste the pass. Reverting to a literal that EQUALS the derived value is not a demonstration, because no test can tell two equal strings apart. Also paste a search of the new module confirming it contains no `inspect`, `ast`, or source-reading of `agent_workflows/`, which is the code-structure-pin prohibition, and paste `aw ipd lint --phase pre-transition` on this plan reporting conforming.
  - Observed evidence:
    Passing output of `tests/test_orchestrator_row_grammar_source.py` with node IDs:
    ```
    tests/test_orchestrator_row_grammar_source.py::test_04_refusal_message_contains_canonical PASSED [ 20%]
    tests/test_orchestrator_row_grammar_source.py::test_02b_sensitivity_perturbation_limb PASSED [ 40%]
    tests/test_orchestrator_row_grammar_source.py::test_03_anchor_enforcement_and_refusal_reason PASSED [ 60%]
    tests/test_orchestrator_row_grammar_source.py::test_01_all_statuses_and_checkbox_states_conform PASSED [ 80%]
    tests/test_orchestrator_row_grammar_source.py::test_02a_sensitivity_binding_limb PASSED [100%]
    5 passed in 0.27s
    ```
    Broader module run:
    `python3 -m pytest tests/test_orchestrator_shape_composed.py tests/test_orchestrator_shape_gate.py tests/test_ipd_templates.py tests/test_orchestrator_retirement.py tests/test_ipd_authoring.py tests/test_ipd_lint.py tests/test_orchestrator_row_grammar_source.py`:
    `182 passed in 7.64s`.
    Full bare run:
    `python3 -m pytest`:
    `6340 passed, 2 skipped, 3 warnings in 269.96s (0:04:29)`
    Lane baseline before changes:
    `6335 passed, 2 skipped, 3 warnings in 736.73s (0:12:16)`
    Delta of failing node IDs: EMPTY (0 failures before, 0 failures after, delta is +5 passed tests).
    Sensitivity proof demonstration:
    Locally mutated `ORCH_ROW_CANONICAL = "- [ ] E-NN VERIFY <child-id6> REACHED <status>"`:
    ```
    tests/test_orchestrator_row_grammar_source.py::test_03_anchor_enforcement_and_refusal_reason PASSED [ 20%]
    tests/test_orchestrator_row_grammar_source.py::test_01_all_statuses_and_checkbox_states_conform PASSED [ 40%]
    tests/test_orchestrator_row_grammar_source.py::test_02b_sensitivity_perturbation_limb PASSED [ 60%]
    tests/test_orchestrator_row_grammar_source.py::test_02a_sensitivity_binding_limb FAILED [ 80%]
    tests/test_orchestrator_row_grammar_source.py::test_04_refusal_message_contains_canonical PASSED [100%]

    =================================== FAILURES ===================================
    ______________________ test_02a_sensitivity_binding_limb _______________________

        def test_02a_sensitivity_binding_limb():
            """Limb 2a: _ORCH_ROW_RE.pattern and ORCH_ROW_CANONICAL equal the module derivations from the shipped datum."""
            expected_pattern = lint.orch_row_pattern(lint.ORCH_ROW_GRAMMAR)
            expected_canonical = lint.orch_row_canonical(lint.ORCH_ROW_GRAMMAR)

            assert lint._ORCH_ROW_RE.pattern == expected_pattern
    >       assert lint.ORCH_ROW_CANONICAL == expected_canonical
    E       AssertionError: assert '- [ ] E-NN V...CHED <status>' == '- [ ] E-NN C...CHED <status>'
    E
    E         - - [ ] E-NN CONFIRM <child-id6> REACHED <status>
    E         ?            ^^^ ^^^
    E         + - [ ] E-NN VERIFY <child-id6> REACHED <status>
    E         ?            ^^^^ ^

    tests/test_orchestrator_row_grammar_source.py:66: AssertionError
    FAILED tests/test_orchestrator_row_grammar_source.py::test_02a_sensitivity_binding_limb
    1 failed, 4 passed in 0.30s
    ```
    Restored `ORCH_ROW_CANONICAL = orch_row_canonical()`: all 5 passed in 0.26s.
    Prohibition check: search for `inspect`, `ast`, `open(`, `read_text`, `Path(` in `tests/test_orchestrator_row_grammar_source.py` confirmed 0 occurrences.
    Lint check: `aw ipd lint .aw/records/plans/pending/20261001-u8dl3q-01-l1xkrr-hold-the-orchestrator-row-grammar-as-one-datum-and-render-th.ipd.md --phase pre-transition` reports conforming.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: the exact `aw specs note` command run and its output; `git diff` of the `r07vma` spec showing exactly one added history line and no other change (OQ-01 still `- Status: open`, `- Owner: maintainer`; spec still `- Status: approved`); and the `aw check` result showing no new finding naming that spec.
  - Observed evidence:
    Command run:
    `aw specs note --message "OQ-01 partially applied (plan l1xkrr): row grammar held as one datum in ipd_lint with _ORCH_ROW_RE, ORCH_ROW_CANONICAL and scaffold row derived from it; refusal message was already rendered from one place (F-03); prose copies (plan-review-long, spec r07vma R1a) and absent doc surface survive outside reach; OQ-01 remains open." .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md`
    Output:
    `aw specs note: appended a history record to .aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md`
    `git diff` of `r07vma` spec:
    ```diff
    diff --git a/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md b/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    index e50c62ea0..4c756396d 100644
    --- a/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    +++ b/.aw/records/specs/approved/20260919-r07vma-01-r07vma-orchestrator-conformance-parser-and-repair-loop.spec.md
    @@ -18,6 +18,7 @@

     ## Workflow history

    +- 2026-10-07 note (aw specs): OQ-01 partially applied (plan l1xkrr): row grammar held as one datum in ipd_lint with _ORCH_ROW_RE, ORCH_ROW_CANONICAL and scaffold row derived from it; refusal message was already rendered from one place (F-03); prose copies (plan-review-long, spec r07vma R1a) and absent doc surface survive outside reach; OQ-01 remains open.
     - 2026-10-06 note (aw specs): AMENDED 2026-10-04 (plan hm1h3l, Set gradcover): R9's probe bullet records the quoted-evidence answer and named-child credit, and both controls now feed the 25kzda 2.5d review-readiness function; Section 3a limit 1 updated; limit 5 rewritten because the omitted-final-child case is now detected by 25kzda 2.5d.
     - 2026-09-28 note (aw specs): Section 3a limit 1 noted by 3brgb6: orchestrator coverage probe now actually reads Completion criteria and Cross-IPD validation prose sections
     - 2026-09-19 approved (aw specs, --by-human): APPROVED by the human maintainer (Gabriele Fariello) 2026-09-19, recorded by the agent at their explicit instruction in session. Approval covers the design as hardened through two review rounds: R1a's typed child-tracking row as the enforcement mechanism (chosen over a prose vocabulary after the maintainer resolved OQ-02 as TYPED), R1b's rule that a cross-child check is a final child with sibling dependencies, the bounded review-time repair loop with honest exhaustion, the batch-report-then-refuse run gate, and the RETENTION of the semantic coverage probe beside the new control per 25kzda 2.5b. The maintainer is on notice of the principal cost: ZERO of 32 live orchestrator rows conform to the new grammar, so every one of the 11 pending orchestrators needs its checklist rewritten, and the migration route is the implementing plan's to choose under acceptance criterion 12. OQ-01 (keeping authoring instructions from drifting from the enforcing code) remains open and non-blocking.
    ```
    Confirmation: exactly one line added; OQ-01 remains `- Status: open`, `- Owner: maintainer`; spec remains `- Status: approved`.
    `aw check`: 0 findings for `r07vma`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution. It is `low` priority and `chore` work-kind: nothing user-visible changes, and its value is entirely in removing a drift mode.

ON EXECUTION: commit only files you changed, through `aw commit <plan> -- <paths>`, never `git add -A` and never with `--no-verify`; do not push; do not create a tag or release. Paste the ACTUAL `python3 -m pytest` output rather than a claim about it; never claim a run you did not perform.

SCOPE FENCE. `- Scope-Paths:` is a DECLARATION so the finalize scope gate can reconcile what was edited against what was declared. If an out-of-scope edit proves necessary, make it and JUSTIFY it with `--scope-reason`; a declared path left unmodified is acknowledged with `--scope-ack`.

LIFECYCLE. Every `V-*` must carry pasted evidence and `aw ipd lint --phase pre-transition` must conform before this plan reaches `executed/`. Reaching it via `aw ipd finalize` is UNCONDITIONALLY OWED, but its OWNER is CONDITIONAL: under `aw oc run` / `aw agy run` the RUNNER owns the transition, so do not invoke `aw ipd finalize` yourself in a runner-driven execution; a HAND execution invokes it. Never hand-roll a `git mv` to `executed/`. Backlog `u8dl3q` may move to `done` only once this plan is executed; its OQ-01 residue remains with spec `r07vma`.

DO NOT EXECUTE BEFORE `zojfn6` REACHES `executed`. The declared `- Item-Dependencies: executed:zojfn6` edge is load-bearing, not cosmetic: E-04's scaffold half edits the very row `zojfn6` E-02 introduces, so running first would either author a second copy of that plan's change (a collision in `ipd_authoring` and in the byte-pinned orchestrator template) or force this plan to invent a typed row that `zojfn6` would then rewrite. The runners re-check dependencies at dispatch and will mark this item `dependency-blocked` rather than run it; an agent executing by hand must honor the same order. Note the two plans touch `ipd_lint.py` for DIFFERENT reasons (that plan edits `_ORCH_ROW_BLOCKING_CHECKPOINTS` and the comment above it; this plan edits `_ORCH_ROW_RE` and `ORCH_ROW_CANONICAL`), so the overlap is a file, not a hunk.

STOP CONDITIONS, each a signal the refactor has changed behavior rather than restructured it. STOP if E-01's byte-identity assertion fails for either surface: adjusting the pattern changes what the rule REFUSES and adjusting the canonical string changes what every refusal tells an author, and neither is this plan's to change. STOP if any test in `tests/test_orchestrator_shape_composed.py`, `tests/test_orchestrator_shape_gate.py`, `tests/test_ipd_templates.py` or `tests/test_orchestrator_retirement.py` goes red: F-07 measured them green and nothing observable changes here, so a red test means the derivation drifted and the fixture is right. STOP if the byte-pinned orchestrator template needs regenerating: that means E-04 changed WHAT the scaffold emits rather than HOW, which is out of scope and is `zojfn6`'s territory. STOP if `aw specs note` refuses the annotation; do not hand-append to an approved spec.
