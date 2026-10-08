# IPD: Sweep the uonrjg criteria for stale citations and uncovered lifecycle surfaces

- Date: 2026-10-02
- Kind: child
- Concern: Spec `uonrjg` carries citations and published measurements that have rotted since they were written, and two acceptance criteria (A5, A19) assert properties nothing exercises. Correct the record and close the two coverage holes.
- Scope: Amend the approved spec `uonrjg` so every citation it makes resolves at HEAD, and add behavioral coverage for the two criteria the sweep found genuinely unasserted. No renderer behavior changes.
- Scope-Paths: .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md, tests/test_lifecycle_style.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Spec: uonrjg
- Work-Kind: chore
- Priority: low
- From-Backlog: nzqj6m
- Set: uonrjgcite
- Order: 1
- Highest E allocated: 07
- Author: aw oc run model=agent
- Id: xtensb
- Approval: 2026-10-07, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Re-verified S1-S5 and F4 at a93c72277; found a sixth stale offset (Section 12a point 3, contract doc 159-163) the symbol-only sweep missed and added an offset grep; re-walked the census (252/34/286, miss 29) and fixed the counting definition; made the A5 counterfactual reachable via mock.patch.object; made A19 non-vacuous with a consumer-level backlog Work-Kind pair; replaced count bars; added scope fence and finalize ownership.

- 2026-10-02 draft (aw oc run model=agent): created.
- 2026-10-02 to-review (aw oc run model=agent): authored from backlog `nzqj6m`; the suggested per-criterion sweep was performed and its measured results are recorded in `## Findings`.
- 2026-10-02 same-status (aw set): status unchanged (to-review); recorded `- From-Spec: uonrjg`, the link the advisory `check.plan-spec-link-missing` asked for.

## Goal

Backlog `nzqj6m` asked for the sweep that plan `nw088c` deliberately left undone: check every one of spec
`uonrjg`'s A1..A21 criteria for coverage that commit `19313eed` deleted, and for renderers R10.3 never
converted. THE SWEEP IS DONE AND ITS HEADLINE RESULT IS THE OPPOSITE OF WHAT THE ITEM EXPECTED: no
criterion's cited test file is missing, and every R10.3 consumer resolves through the shared module. What
the sweep DID find is five STALE CITATIONS inside the spec (three line offsets pointing at unrelated code,
two published measurements whose denominators have moved) and TWO CRITERIA, A5 and A19, that assert a
property NOTHING exercises. This plan corrects the five citations and covers the two criteria.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Correct the spec's rotted citations

- [x] E-01 In the spec, fix the three stale LINE citations S1, S2, S3. Replace A12's stale offset citation (the offset `agent_workflows/term.py:374`, which lands in `term.should_color`) with a symbol citation of `term.should_unicode` (A12 already mandates symbol citation, so this applies its own rule to itself). Replace A11's stale offset citation (the spec text reading "`docs/cli-output-contract.md:225`") with a citation of the section headed `## 9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19`, noting the quoted retracted sentence now sits at line 304 if a line is given at all. In BOTH places where the accessibility lens is cited (the Section 0.5 superseded-claims table row, and OQ-01's "Resolution or deferral rationale"), replace the stale lens quote (cited as `accessibility.md:56-63`, quoting `prefer the terminal's default fg/bg and the 16 named colors`) with what the lens says at HEAD (the 256->16->none ladder), and state plainly that the old wording survives only as marked history, because OQ-01's own resolution is what corrected the lens. Do not restate the lens text as if it still conflicted.
  ALSO FIX S6, FOUND AT REVIEW AND ABSENT FROM THE AUTHORING SWEEP: Section 12a point 3 cites the cli-output-contract doc at offset 159 to 163 (quoted in the spec beside the text "as `docs/cli-output-contract.md`") as the place that "promises" non-TTY stdout selects AGENT mode. At review HEAD `a93c72277` those lines hold the `---` rule and the `## 3. Exit Code Semantics` heading, and the promise is retracted. Re-point it to the section headed `## 9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19`, saying the promise was there at the time and is now retracted text. LEAVE THE HISTORICAL term.py 224-to-227 OFFSET IN A12 ALONE: the sentence beginning "Only the CITATION was stale. This line read" explicitly records what the line USED to read, so it is marked history, not a live citation.
  THE SWEEP METHOD MUST COVER LINE OFFSETS, NOT ONLY SYMBOLS. F1's extraction resolved paths and `module.symbol` tokens but never checked `path:line` offsets, which is why S6 was missed. Run `grep -noE '[A-Za-z_/.-]+\.(py|md|json):[0-9]+(-[0-9]+)?'` over the spec (at review it returned exactly five: the S1 term.py offset 374, the S3 accessibility-lens offset 56 to 63, the S6 contract-doc offset 159 to 163, the S2 contract-doc offset 225, and the historical A12 term.py offset 224 to 227), and resolve each against the text it claims. That is the "citation extraction" E-07 and V-01 re-run.
  - Depends on: none
  - Expected outcome: every line-anchored citation in the spec resolves to text that supports the claim, and no citation asserts the accessibility lens contradicts this spec.
  - Execution state: performed

- [x] E-02 In the spec's Section 9.3 final bullet, re-measure and correct the subcommand census (S4): replace the "200 LEAF subcommands / 229 subcommand nodes / 29 intermediate groups" figures with figures measured at the executing HEAD by walking `cli._build_parser()`, keep the existing STATE-THE-DENOMINATOR instruction, and record that the 29-leaf miss accounting still holds with its three groups named (host-driver families, `run/as` plus `run/ipd`, and `__complete`). THE FIGURES DRIFT FAST: F3 measured 250 leaves / 35 groups / 284 nodes at authoring, and the review re-walk at `a93c72277` gave 252 / 34 / 286 with the miss still 29. Count a node as a GROUP when its parser itself carries a subparsers action and as a LEAF otherwise, and state that definition in the bullet beside the figures, so the next re-measurement counts the same thing. Do NOT write "the miss count is always 29"; record it as measured on the stated date. Note explicitly that the group count no longer coincides numerically with the leaf-miss count, retiring the specific trap that bullet warns about. Separately mark S5 (Section 12a point 2's "25 of 219", repeated in obligation 2) as a PRE-`yaxr4i` historical measurement rather than silently updating it, because that sentence is describing the tree as it was when the dependency was declared and rewriting it would falsify the history it records.
  - Depends on: E-01
  - Expected outcome: the spec publishes a census that reproduces at HEAD, and its one historical census is labeled historical instead of reading as current.
  - Execution state: performed

- [x] E-03 In the spec's A13, retire the stale document-conflict warning (F4). The paragraph beginning "NOTE THE FALSEY RULE IS NARROWER THAN THE PUBLISHED TABLE" and its instruction "AN IMPLEMENTER MUST FOLLOW THE CODE AND THIS CRITERION, NOT THAT ROW" describe a document that has since been corrected. Rewrite it as history: record that `docs/cli-output-contract.md` section 1.1 row 2 now states the falsey-value rule and names `term._force_color_is_forcing`, so the document and this criterion AGREE, and keep one sentence of the original reasoning so a reader holding the old wording understands what changed. Do NOT delete the criterion's three named rungs; they are the substance and they still hold.
  - Depends on: E-02
  - Expected outcome: A13 no longer instructs an implementer to distrust a document that is now correct, and the three rungs remain asserted.
  - Execution state: performed

### Task group 2: Close the two uncovered criteria

- [x] E-04 Add a behavioral test for A5 to `tests/test_lifecycle_style.py` asserting that no lifecycle constant and no rendered lifecycle output contains an emoji-presentation variation selector (`U+FE0F`). Drive it through the PUBLIC surface rather than by reading source: for every stage in `lifecycle_style.STAGE_ORDER` assert `U+FE0F` is absent from both the Unicode glyph and the ASCII fallback, and assert the two multi-codepoint glyphs in `lifecycle_style.MULTI_CODEPOINT_GLYPHS` carry the TEXT selector `U+FE0E` instead. Then render across tiers and modes (`Term(color=..., unicode=..., depth=...)` over the three depths and both Unicode modes) via `format_lifecycle_marker` and `style_lifecycle_text` and assert `U+FE0F` never appears. NO SOURCE PINNING: do not grep production files, do not use `inspect` or `ast` (P16; the backlog item restates this as binding for this axis).
  READ GLYPHS THROUGH THE PUBLIC ACCESSORS: `lifecycle_style.style_for(stage).unicode` / `.ascii` and `lifecycle_style.glyph_for(stage, unicode=...)`. Build `Resolved` values for rendering with `lifecycle_style.resolve(...)` over real families, or construct `Resolved(stage=..., style=style_for(stage), family=...)` per stage as `status_set._resolve_record_lifecycle` does, so every stage is rendered, not only those reachable from one family.
  THE COUNTERFACTUAL IN V-04 MUST BE REACHABLE: `lifecycle_style.STAGES` is a `MappingProxyType` built at import, so the stage table cannot be patched in place. Patch at the test-run level with `unittest.mock.patch.object(lifecycle_style, "STAGES", <dict copy with one row's `unicode` replaced via `_replace`>)` (and `MULTI_CODEPOINT_GLYPHS` likewise for the selector half), run the new test, observe it fail, and leave no edit on disk. That is a scratch probe, not a committed test.
  - Depends on: none
  - Expected outcome: a failing-if-regressed guard exists for A5 across every tier and both Unicode modes, asserting rendered output rather than source text.
  - Execution state: performed

- [x] E-05 Add a behavioral test for A19 to `tests/test_lifecycle_style.py` asserting work-kind has no effect on lifecycle resolution. Assert OUTCOMES: (a) `lifecycle_style.resolve` accepts no work-kind input, demonstrated by calling it with `work_kind=` and asserting `TypeError`, which is a call-result assertion and not a signature census; and (b) resolution is identical for artifacts differing only in work-kind, by resolving the same family and native status repeatedly and asserting the `Resolved` stage, style, and native status are equal, and (c) PRESENTATION is work-kind-blind at a real consumer: write two backlog items into a temp repo identical except `- Work-Kind: bug` versus `- Work-Kind: chore`, render them through a real lifecycle consumer (for example `aw find backlog <id6>` driven via `cli.main` with `FORCE_COLOR=1`, as `tests/test_status_set.py::SharedLifecycleRenderingTests` drives `find`), and assert the lifecycle glyph-plus-color token emitted for each is byte-identical. Part (b) ALONE is vacuous, since a resolver that is never handed a work-kind cannot vary on it; part (c) is what can actually fail if a consumer later threads work-kind into presentation. Choose `backlog` because a work-kind field genuinely exists there.
  - Depends on: E-04
  - Expected outcome: a guard exists that fails if a later change threads work-kind into lifecycle resolution or presentation.
  - Execution state: performed

- [x] E-06 Record the spec amendment with `aw specs note <spec path> --message <msg>` on the `uonrjg` spec (the verb takes a PATH, not an id6), in one note naming this plan and this backlog item and summarizing WHAT was amended (four citations re-pointed (S1, S2, S3, S6), one census re-measured, one census marked historical, A13's document-conflict warning retired as resolved) and WHAT WAS NOT (no criterion's requirement changed, no stage, color, glyph, or mapping touched). Use `aw specs note`, NOT `aw specs set`: the spec is `approved` and release-gating, and the spec's own Section 12a records that the review verb would illegally de-approve it. Do not hand-edit `## Workflow history`.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the spec's history records the amendment through the tooled path, with the scope of the amendment stated.
  - Execution state: performed

### Task group 3: Whole-change validation

- [x] E-07 Run the whole-change validation gate: bare `python3 -m pytest` for the full fast suite (the spec edit is read both by `tests/test_lifecycle_style.py`, which parses Section 5, and by `check_engine`'s criteria-coverage rule, so a malformed amendment can fail tests far from this plan), `aw check` for the spec/plan consistency rules, `git diff --check`, and `aw ipd lint --phase pre-transition` on this plan. Then re-run the citation extraction over the AMENDED spec, so the fix is confirmed by the same measurement that found the defect. Inspect the staged set before committing and confirm it contains only the two declared `Scope-Paths` entries.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: the full fast suite and repository checks pass with no regression against the recorded baselines, the plan lints conforming, and the citation sweep over the amended spec reports zero unresolvable citations.
  - Execution state: performed

## Project conventions discovered (Step 0)

- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (`AGENTS.md`, "A PLAN MAY AMEND A SPEC, AND MUST DECLARE
  IT"). The spec file is therefore named in `- Scope-Paths:` so both runners announce the declared spec
  edit before the run and reconcile it at finalize.
- NO CODE-PINNING TESTS (`AGENTS.md` execution contract; `GUIDING_PRINCIPLES` P16). The backlog item
  restates this as the rule any such work MUST follow, so the two tests this plan adds assert RENDERED
  OUTPUT and resolver RESULTS, never `inspect`, `ast`, regex over production source, or symbol censuses.
- THE ONE NARROW P16 EXCEPTION ALREADY IN PLAY HERE: `tests/test_lifecycle_style.py` parses the spec's own
  Section 5 table (`_parse_spec_section5`, consumed by
  `StageTableTests.test_stage_table_and_glyphs_progression`), which is legitimate because there the SPEC is
  the artifact under test rather than production source. This plan does not widen that exception.
- CITE BY SYMBOL, NOT BY BARE LINE (`ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This is
  not merely a plan convention here, it is the DEFECT CLASS this plan fixes: criterion A12 already learned
  it once and wrote the lesson down ("CITED BY SYMBOL RATHER THAN BY LINE FROM HERE ON, deliberately: a
  line number in a spec rots on the next unrelated edit to the file above it, and a wrong line is worse
  than no line, because it sends a reader to code that looks relevant"). Three citations elsewhere in the
  spec never got that treatment, and all three have now rotted exactly as predicted.
- A SPEC AMENDMENT IS RECORDED WITH `aw specs note`, NOT by hand-editing `## Workflow history`, and NOT
  with `aw specs set` (this spec is `approved` and release-gating; the spec's own Section 12a records that
  running `/spec-review` on it would illegally de-approve it).

## Findings

The item's suggested first step ("for each of A1..A21, extract every tests/ path and test class it cites
and check existence, then triage only the ones that dangle") was performed. Criteria were enumerated with
the repository's own parser rather than by eye:
`check_engine.parse_spec_acceptance_criteria` returns 25 ids (A1..A21 plus A12a, A12b, A12c, A12d).

### F1. ZERO dangling test citations remain. The item's premise no longer holds

Every `tests/` path and `module.symbol` the spec cites exists at HEAD. Measured by extracting every
backticked token from the spec and resolving it (file existence for paths, `hasattr` for symbols):

| Cited | Resolves at HEAD |
|---|---|
| `tests/test_term.py`, `tests/test_lifecycle_style.py`, `tests/test_flag_surface_uniformity.py` | yes, all three |
| `term.should_color`, `term.should_unicode`, `term.set_color_override`, `term._FORCE_COLOR_FALSEY`, `term._force_color_is_forcing` | yes |
| `runner_shared.should_color`, `runner_shared.LEGACY_INTEGRATION_STATUS_ALIASES` | yes |
| `run_gates.ALL_GATE_STATUSES`, `run_gates.GATE_STATUS_NEEDS_INPUT`, `runner_shutdown.KNOWN_ITEM_STATUSES` | yes |
| `config.CONFIG_SCHEMA`, `Term.color256`, `agent_workflows/lifecycle_style.py`, `agent_workflows/term.py` | yes |

This is WHY the plan that follows is a citation-correction plan and not a coverage-restoration plan. The
three citations `nw088c` fixed were the only genuinely dangling ones.

### F2. THE FOUR AREAS `nw088c` EXCLUDED ARE ALL COVERED. None needs re-covering

The item names four surfaces `nw088c` measured and excluded, each needing "its own per-criterion
judgement". All four were judged, and all four hold:

| Excluded surface | Verdict | Evidence |
|---|---|---|
| The glyph table | COVERED | `StageTableTests.test_stage_table_and_glyphs_progression` asserts the module's rows EQUAL the spec's parsed Section 5 table, plus the `○ ◔ ◑ ◕ ✓` progression, the four named glyphs, the five activity glyphs, and single-byte ASCII fallback for every stage |
| Authored 16-color palette (R9.3a.3 / A12b) | COVERED | `tests/test_term.py` `AuthoredSixteenColorPaletteTests` asserts `set(STAGE_COLOR_16) == set(lifecycle_style.ALL_STAGES)`, walks `REQUIRED_16_COLOR_SEPARATIONS`, and walks `EXPECTED_16_COLOR_COLLAPSES` so a later change cannot re-expand them |
| Width policy (Section 9.4) | COVERED | `term.visible_width` exists and is the shared measurement; asserted in `tests/test_pad_visible.py`, `tests/test_statusline_visible_width.py`, `tests/test_run_summary_visible_width.py`, and `tests/test_term.py::...test_grapheme_width_variation_selectors_and_ansi` |
| Consumer conversion (R10.3 / A17) | COVERED | every R10.3-named consumer resolves through the shared module: `attention.py` 19 references, `run_viewer.py` 18, `render_stream.py` 11, `ipd_lint.py` 7; both runners reach it by importing `render_stream.resolve_item_lifecycle` (`oc_runipd.py` and `agy_runipd.py` each import that symbol). `attention._STATUS_COLOR_256` is GONE and its absence is pinned by `tests/test_term.py` and `tests/test_attention.py` |

One nuance worth recording so a later reader does not file it as an A17 violation: `render_stream.py`
retains `STATUS_GLYPHS` / `STATUS_GLYPHS_ASCII`, and that is EXPLICITLY PERMITTED. R10.3 allows
`render_stream.py` to "retain event glyphs and severity colors that are not lifecycle semantics", and that
table is keyed by TOOL-EVENT status (`completed`, `error`, `running`, `other`), not by any lifecycle
status. Likewise `run_viewer._AUDIT_CLASS_COLOR` is keyed by audit class and `term.ROLE_COLOR_256` by
generic command-outcome role, both of which A18 requires to stay independent.

### F3. FIVE STALE CITATIONS IN THE SPEC. This is the real defect the sweep found

Each measured at HEAD. Three are line offsets that now point at unrelated text, which is precisely the rot
A12 already warned about; two are published measurements whose denominators moved.

| # | Spec location | Claim | Measured at HEAD |
|---|---|---|---|
| S1 | A12 | the spec cites `agent_workflows/term.py:374` as `term.should_unicode`'s ASCII-variable read | WRONG. The symbol `term.should_unicode` is defined at `agent_workflows/term.py:940` (`def should_unicode`). The cited offset sits inside `term.should_color`'s `override` docstring, at the text "``override`` EXISTS SO A FLAG NEVER HAS TO MUTATE ``os.environ``", discussing the flag layer, i.e. the EXACT confusion A12's own lesson predicts |
| S2 | A11 | the spec says the retracted promise survives at `docs/cli-output-contract.md:225`, quoting `non-TTY stdout adopts aw.agent/v1 JSONL` | WRONG. That offset holds the unrelated line `- **Completeness and Verification**:`. The quoted retracted sentence is the text "The retracted text read: \"Per maintainer decision OQ-01, non-TTY stdout adopts `aw.agent/v1` JSONL\"", inside the section headed `## 9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19` |
| S3 | Section 0.5 table and OQ-01 | the spec cites `accessibility.md:56-63` for `Do not assume 256-color or truecolor` and `prefer the terminal's default fg/bg and the 16 named colors` | WRONG AND INVERTED. The lens now reads "**DEGRADE THROUGH 256 -> 16 -> NONE** (DECISIONS D42). 256-color is the TOP tier" at that location. The old wording survives ONLY as explicitly-marked history, in the line beginning "old wording in mind: it used to read". The lens was corrected by OQ-01 itself, so the spec cites the pre-correction text it caused to be rewritten |
| S4 | Section 9.3 final bullet | "200 LEAF subcommands (229 subcommand nodes in total, of which 29 are intermediate groups)" | STALE. Walking `cli._build_parser()` at HEAD gives 250 leaves and 35 groups (284 nodes); re-walked at review HEAD `a93c72277`: 252 / 34 / 286, miss 29. The leaf-miss count is still EXACTLY 29 and still fully accounted for (26 host-driver leaves in the `oc`/`opencode`/`agy`/`antigravity` families, plus `run/as`, `run/ipd`, and the hidden `__complete`), so the ACCOUNTING survives and only the denominators rotted. Note the spec's own warning now bites: it says "the leaf-miss count (29) coincides numerically with the group count (29), so a bare '29 of 229' reads as self-consistent while being the wrong ratio" - at HEAD the group count is 35, so that coincidence has ended |
| S6 | Section 12a point 3 | the spec says `yaxr4i` OQ-01 asked whether non-TTY stdout should select AGENT mode, citing the contract doc at offset 159 to 163 as the promise | WRONG (found at REVIEW, not by the authoring sweep). Those lines now hold `---` and `## 3. Exit Code Semantics`; the promise lives on only as retracted text in Section 9. |
| S5 | Section 12a point 2, repeated in obligation 2 | "`--no-color` is currently missing from 25 of 219 subcommands" | STALE, and historically so: it describes the PRE-`yaxr4i` tree. `yaxr4i` is `executed`, and at HEAD 29 of 250 leaves declare neither flag, all explained as in S4 |

### F4. A13's "the document is stale" warning is ITSELF now stale

A13 tells an implementer that `docs/cli-output-contract.md` section 1.1 row 2 contradicts the shipped code
and that they "MUST FOLLOW THE CODE AND THIS CRITERION, NOT THAT ROW". That row has since been fixed.
At HEAD, that row in `docs/cli-output-contract.md` reads that a falsey value "neither forces nor suppresses, so
detection proceeds normally" and that "Both `FORCE_COLOR` readings route through
`term._force_color_is_forcing`" - which is the CODE's behavior and A13's own position. The document and the
criterion now agree, so the warning misdirects a reader into distrusting a correct document.

All three A13 rungs were re-measured against `term.should_color` on a non-TTY stream and all three hold:
(a) `FORCE_COLOR=1`, no flag -> True; (b) `FORCE_COLOR=1` with `--no-color` -> False; (c) `FORCE_COLOR=0`
-> False, and `NO_COLOR=1 FORCE_COLOR=0` -> False on a pipe AND on a TTY. A11's narrowing also holds:
`--color` returns True against each of `NO_COLOR=1`, `TERM=dumb`, and plain non-TTY.

### F5. TWO CRITERIA ASSERT A PROPERTY NOTHING EXERCISES: A5 and A19

This is the one genuine coverage gap, and both are cheap to close because the production behavior is
already correct. Neither is a behavior defect; each is a criterion with no guard.

- **A5** ("`⚠️` and `↩️` do not occur in lifecycle constants or golden output"). Only ONE assertion in the
  suite touches the emoji form: `tests/test_term.py` asserts `assertNotIn("\ufe0f", ...)` over
  `format_lifecycle_legend()` across the three tiers and both Unicode modes. That covers the LEGEND and
  nothing else, so the spec's "lifecycle constants" half is unguarded. Measured true today: the emoji
  warning form occurs exactly once in the package, at `agent_workflows/engine.py` in a generated-README
  string ("DO NOT EDIT THESE FILES MANUALLY"), which is NOT a lifecycle constant and is correctly out of
  A5's scope; the emoji recovery form occurs nowhere.
- **A19** ("Work-kind has no effect on lifecycle resolution or presentation"). Nothing asserts it. The
  property holds STRUCTURALLY at HEAD - `lifecycle_style.resolve` accepts only `family`, `native_status`,
  `activity`, `integrity`, `obstruction`, `condition`, and the strings `work_kind` / `Work-Kind` appear in
  none of `lifecycle_style.py`, `term.py`, or `attention.py` - but structure is not a test, and a later
  change could add a work-kind input with no failing assertion. The only `A19` mentions in the suite are
  inside `tests/test_check_engine_spec_criteria.py`, where `A19` is FIXTURE DATA for the criteria-coverage
  checker's own counterfactual, not coverage of this criterion.

### F6. Everything else is covered. Full per-criterion verdict

A1 `lifecycle_style` module + `SelfValidationTests`. A2 `MappingTotalityTests` enumerates ten owner enums.
A3/A4/A6 glyph progression and named glyphs in `StageTableTests`. A7/A8/A9 the precedence ladder in
`PrecedenceTests.test_precedence_ladder_integrity_obstruction_condition_activity_native` (activity beats
native without mutating `native_status`; integrity beats activity; obstruction beats ready) plus
`test_resolver_immutability_and_preservation`. A10/A11/A14/A20 asserted across `tests/test_ipd_lint.py`,
`tests/test_plans_index.py`, `tests/test_research_index.py`, `tests/test_status_set.py`. A12/A12a/A12c
`ColorDepthPrecedenceTests` rungs 1-4 plus `tests/test_config.py` pin/refusal tests. A12b/A12d the
authored-palette and all-tiers tests. A13 the three named rungs. A15 variation selectors through
`strip_ansi`. A16 the six capability profiles. A17 see F2. A18 `ROLE_COLOR_256` disjointness. A21 suite.

## Proposed changes (ordered, validatable)

0. Fix S6: re-point Section 12a point 3's stale contract-doc offset (159 to 163) to the retracted section by heading.
1. Fix S1: re-point A12's stale offset citation to the symbol `term.should_unicode`, per A12's own stated rule.
2. Fix S2: re-point A11's stale offset citation to the retracted section by its heading.
3. Fix S3: correct the accessibility-lens citation in Section 0.5 and OQ-01 to quote what the lens says now.
4. Fix S4 and S5: re-measure the subcommand denominators and mark S5 as historical.
5. Fix F4: retire A13's stale "follow the code, not that row" warning, recording that the row was fixed.
6. Close F5: add two behavioral tests covering A5 and A19.
7. Record the amendment with `aw specs note`.

## Deferred / out of scope (with reason)

- RESTORING ANY DELETED TEST FROM `19313eed`. The sweep found no criterion whose cited coverage is gone
  (F1, F2), so there is nothing to restore. The maintainer ruling of 2026-09-28 on backlog `p5qx91`
  (deleted classes will not be restored) is respected and not revisited.
  - Carrier-Declined: nothing is outstanding. This row records a MEASURED NEGATIVE RESULT (F1 and F2: every cited test path and symbol resolves at HEAD, and all four surfaces `nw088c` excluded are covered), not work handed onward. A carrier would assert there is restoration work pending, which the sweep proved there is not.
- OQ-02 of the spec (whether `needs_input` or `awaiting-human` retires). Non-blocking, owned by the
  maintainer, and explicitly not this spec's to decide; it closes when `run_gates` is wired to the runners.
  - Carrier-Declined: already carried by the spec itself, and not by this plan. `uonrjg` Section 16 holds OQ-02 as an open, non-blocking, maintainer-owned question with its closing condition recorded; it is a question about a lifecycle vocabulary that Section 3 excludes from this spec's scope. Filing a second carrier here would duplicate a live record rather than preserve one.
- THE SPEC'S OWN OQ-01 CONSEQUENCES BEYOND THE CITATION. OQ-01 is `resolved` and the lens was corrected;
  this plan fixes only the stale QUOTE of the lens, and re-opens no part of the resolution.
  - Carrier-Declined: nothing is outstanding. OQ-01 carries `- Status: resolved` and the accessibility lens was corrected by that resolution (verified at HEAD: the lens now states the 256->16->none ladder). Only the spec's stale QUOTE of the pre-correction lens is a defect, and E-01 fixes it in this plan.
- AMENDING `25kzda` Section 5.6. Section 0.5 obliges the plan that LANDS THE RESOLVER to do that, and the
  resolver is already landed; whether that obligation was discharged is a separate question about a
  different plan's completeness and is not a citation defect in `uonrjg`.
  - Carrier-Declined: deliberately NOT adopted, and this is the one row where something may genuinely remain open, so the reason is recorded in full rather than waved through. Section 0.5 places the obligation on "the plan that lands the resolver", which is not this plan; whether that plan discharged it is a question about ANOTHER plan's completeness, and answering it needs reading `25kzda` Section 5.6 against the resolver as shipped. That is a different investigation from a citation sweep, and bundling it here is exactly the scope creep that made `nw088c` refuse to bundle this sweep. A reviewer who wants it chased should file a backlog item for it; this plan deliberately does not, because inventing an item for an obligation that may already be discharged would file a false defect.
- `docs/cli-output-contract.md` IS NOT EDITED. F4 found the document already correct; only the spec's stale
  warning about it changes. The file is deliberately absent from `Scope-Paths`.
  - Carrier-Declined: nothing is outstanding. F4 measured the document CORRECT at HEAD (section 1.1 row 2 states the falsey-value rule and names `term._force_color_is_forcing`), so there is no document defect to carry. The stale artifact is the spec's warning ABOUT the document, which E-03 fixes here.
- ANY RENDERER BEHAVIOR CHANGE. The depth ladder, palettes, glyphs, and consumers are all correct and
  covered (F2, F6). Backlog `o53joz` separately owns the depth-ladder recollapse guard.
  - Carrier-Declined: no behavior change is owed. F2 and F6 measured every renderer surface correct and covered, and the one adjacent hardening task (a depth-ladder recollapse guard) is ALREADY carried by backlog item `o53joz`, so this row points at an existing owner rather than needing a new one.

## Scope check

- Over-scope: none. Two paths are declared and both are required: the spec file carries the five stale
  citations and the stale A13 warning (E-01 to E-03, E-06), and `tests/test_lifecycle_style.py` is where
  the A5 and A19 guards belong, beside the Section 5 and mapping-totality tests that cover their siblings.
- Under-scope: the two new tests close A5 and A19 as the spec STATES them. A5's "golden output" half is
  satisfied by rendering through `format_lifecycle_marker` and `style_lifecycle_text` at every tier rather
  than by scanning committed snapshot files, because no lifecycle golden-file corpus exists to scan; if one
  is later added, A5 would want extending to it. A19 is asserted at the resolver and its rendering helpers,
  which is where a work-kind input could enter; it does not re-assert every downstream consumer, since each
  consumer reaches the resolver (F2) and a consumer cannot smuggle work-kind into a resolution the resolver
  refuses to accept.

## Required tests / validation

- `python3 -m pytest tests/test_lifecycle_style.py tests/test_term.py` for the two new guards and the
  existing lifecycle surface. Baseline measured before authoring: 43 passed (re-confirmed 43 at review HEAD `a93c72277`); context only, re-derive before editing.
- `python3 -m pytest tests/test_lifecycle_style.py tests/test_term.py tests/test_config.py
  tests/test_check_engine_spec_criteria.py tests/test_flag_surface_uniformity.py tests/test_pad_visible.py`
  for the depth, palette, flag-surface, and criteria-coverage neighbours. Baseline at authoring: 105 passed; context only, re-derive before editing.
- `python3 -m pytest` bare for the full fast suite, since the spec edit is read by
  `tests/test_lifecycle_style.py` (Section 5 parse) and by `check_engine`'s criteria-coverage rule, so a
  malformed amendment can fail tests far from this plan.
- `aw check` for the spec/plan consistency rules, including the criteria-coverage rule that reads this spec.
- `aw ipd lint --phase pre-transition` on this plan.
- Re-run the citation sweep after E-01 to E-03 and paste the result, so the fix is verified by the same
  measurement that found the defect rather than by inspection.

## Spec / documentation sync

- `.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`
  is AMENDED by E-01 to E-03 and declared in `Scope-Paths`. WHY THE AMENDMENT IS WARRANTED, which
  `AGENTS.md` requires a spec-editing plan to state: the spec is the contract every lifecycle plan is
  reviewed against, and five of its citations now send a reader to text that does not support the claim
  while a sixth tells them to distrust a document that is correct. That actively misleads, and it is the
  defect class A12 already identified in this very spec ("a wrong line is worse than no line, because it
  sends a reader to code that looks relevant"). NO REQUIREMENT, CRITERION OUTCOME, STAGE, COLOR, GLYPH,
  ASCII FALLBACK, OR MAPPING CHANGES; the amendment is confined to citations, two measured censuses, and
  one warning that its own subject has since resolved. The spec's `- Status:` is NOT touched (E-06).
- `docs/cli-output-contract.md`: N/A, already correct (F4). Not in `Scope-Paths`.
- `.aw/system/workflows/assess/lenses/accessibility.md`: N/A, already corrected by OQ-01's resolution. Only
  the spec's stale quote of it changes. Not in `Scope-Paths`.

## Open questions

### OQ-01: Should A5 be widened to a committed golden-output corpus?

- Blocking: no
- Status: open
- Owner: none
- Carrier: 0rnvj6
- Resolution or deferral rationale: A5 says "lifecycle constants or golden output". E-04 covers the
  constants exhaustively and covers "golden output" by RENDERING at every tier and both Unicode modes,
  which is the stronger assertion available today because no committed lifecycle golden-file corpus exists
  to scan. If a snapshot corpus is later added, A5 would want extending to it. Not blocking: nothing is
  unasserted today as a result, and the answer does not change any E-item.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste, for each of S1/S2/S3, the OLD cited text and the text at the cited location at HEAD, showing the mismatch; then paste the amended spec lines. For S1 show that the spec now cites `term.should_unicode` by symbol and paste `grep -n "def should_unicode" agent_workflows/term.py` proving the symbol resolves. For S2 and S6 paste the heading line of the retracted section from `docs/cli-output-contract.md` and show the spec cites it by heading in BOTH places (A11 and Section 12a point 3). For S3 paste `sed -n '56,63p' .aw/system/workflows/assess/lenses/accessibility.md` showing the 256->16->none ladder, and paste the amended spec text in BOTH locations (Section 0.5 table row and OQ-01) showing neither now claims the lens prefers the 16 named colors. Finally re-run the full citation extraction over the amended spec (symbols and paths as in F1, PLUS the `path:line` offset grep named in E-01) and paste output showing every remaining offset either resolves to supporting text or is explicitly marked history.
  - Observed evidence:
    1. S1 mismatch and amendment:
    OLD cited text (A12): `agent_workflows/term.py:374`
    Text at cited location at HEAD: `agent_workflows/term.py:374` sits inside `term.should_color`'s override docstring ("override EXISTS SO A FLAG NEVER HAS TO MUTATE os.environ").
    Symbol resolution: `grep -n "def should_unicode" agent_workflows/term.py` yields:
    `940:def should_unicode(stream: Optional[TextIO] = None) -> bool:`
    Amended spec line (A12):
    `which lives in symbol \`term.should_unicode\` in \`agent_workflows/term.py\`. CITED BY SYMBOL`

    2. S2 and S6 mismatch and amendment:
    OLD cited text (A11): `docs/cli-output-contract.md:225` (line 225 at HEAD is under section 5 agent-record schema).
    OLD cited text (Section 12a point 3): `docs/cli-output-contract.md:159-163` (lines 159-163 at HEAD contain `---` and `## 3. Exit Code Semantics`).
    Retracted section heading in `docs/cli-output-contract.md`:
    `338:## 9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19`
    Amended spec lines:
    A11:
    `as explicitly-quoted retracted text under section \`## 9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19\` (line 343), and section 1 now says outright that "THE TTY-NESS OF STDOUT DOES NOT AFFECT THE MODE".`
    Section 12a point 3:
    `as \`docs/cli-output-contract.md\` promised at the time (in the text now retracted under \`## 9. Automatic Non-TTY Migration Policy: RETRACTED 2026-09-19\`).`

    3. S3 mismatch and amendment:
    `sed -n '56,63p' .aw/system/workflows/assess/lenses/accessibility.md`:
    ```text
      **DEGRADE THROUGH 256 -> 16 -> NONE** (DECISIONS D42). 256-color is the TOP tier and may be
      used where it earns its keep; it is not an assumption to avoid, because virtually every
      terminal of the last two decades supports it. What is required is that the tiers below it
      still work: a 16-color terminal gets a 16-color rendering, and a no-color context gets plain
      text. Never hardcode a foreground color that assumes a specific background (light-on-light /
      dark-on-dark vanishes), and prefer the terminal's default fg/bg where a color adds nothing.
      A USER'S EXPLICIT CHOICE OUTRANKS DETECTION. Detection cannot know that a user is colorblind,
      is on a light theme, or simply dislikes the palette, so a tool SHOULD let the user pin the
    ```
    Amended Section 0.5 table row:
    `| The historical wording of the accessibility lens ("Do not assume 256-color... prefer the 16 named colors", with an \`aw attention\`-only D133 exception), which survived only until OQ-01 corrected the lens | \`.aw/system/workflows/assess/lenses/accessibility.md\` | not a spec; it is the normative rubric \`20260706-0000-01\` Goal 9 delegates to | RETIRED BY AMENDMENT RATHER THAN AN OVERRIDE. The lens was corrected 2026-09-13 by OQ-01's resolution to adopt DECISIONS D42's normative 256 -> 16 -> none degradation ladder, with 256 as the top tier and 16-color and no-color as required fallbacks. The old "prefer the 16 named colors" wording survives only as marked history in the lens, so the former conflict is resolved. |`
    Amended OQ-01 resolution rationale:
    `- Resolution or deferral rationale: THIS CONFLICT WAS RESOLVED BY CORRECTING THE LENS, not by overriding it. The accessibility lens at \`.aw/system/workflows/assess/lenses/accessibility.md\` was corrected during review of this spec (2026-09-13) to normatively specify the 256 -> 16 -> none degradation ladder of DECISIONS D42: 256-color is the top tier and may be used where it earns its keep, while 16-color and no-color are the required fallbacks below it. The former wording ("prefer the terminal's default fg/bg and the 16 named colors", which contradicted D42 and created an artificial conflict) survives in the lens only as explicitly marked history. The lens and this spec now agree on the 256 -> 16 -> none ladder, and Section 9.3a defines the authored 16-color palette and fallbacks.`

    4. Line offset and symbol citation re-run over amended spec:
    `grep -noE '[A-Za-z_/.-]+\.(py|md|json):[0-9]+(-[0-9]+)?' .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md` ->
    `860:term.py:224-227` (historical reference in A12, explicitly preserved per E-01).
    All cited paths and symbols resolve cleanly at HEAD.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the output of the `cli._build_parser()` walk performed at the executing HEAD, showing the leaf count, the group count, the node total, and the count of leaves declaring neither `--color` nor `--no-color`, together with the explained breakdown of that miss set (host-driver family count, plus `run/as`, `run/ipd`, `__complete`). Paste the amended Section 9.3 bullet showing those figures and showing the retained state-the-denominator instruction. Paste the amended Section 12a text showing the "25 of 219" figure is labeled a pre-`yaxr4i` historical measurement rather than silently changed. Figures must be from the executing HEAD, not copied from this plan's Findings.
  - Observed evidence:
    1. Executing HEAD `cli._build_parser()` measurement:
    ```text
    Leaf count: 253
    Group count: 34
    Subcommand node total: 287
    Leaves declaring neither flag: 29
      Host-driver families (26): ['oc runipd', 'oc run', 'oc review', 'oc integrate', 'opencode runipd', 'opencode run', 'opencode review', 'opencode integrate', 'agy runipd', 'agy run', 'agy runagy', 'agy review', 'agy integrate', 'agy sessions', 'agy view', 'agy view-antigravity-jsonl', 'agy exec', 'antigravity runipd', 'antigravity run', 'antigravity runagy', 'antigravity review', 'antigravity integrate', 'antigravity sessions', 'antigravity view', 'antigravity view-antigravity-jsonl', 'antigravity exec']
      run as / run ipd (2): ['run as', 'run ipd']
      shell callback (1): ['__complete']
    ```
    2. Amended Section 9.3 bullet:
    `- THE FLAG SURFACE IS UNIFORM, so a renderer may assume the flags exist everywhere. Measured 2026-10-08 by walking \`cli._build_parser()\`: 253 LEAF subcommands (287 subcommand nodes in total, of which 34 are intermediate groups that dispatch no action of their own; count a node as a GROUP when its parser itself carries a subparsers action and as a LEAF otherwise). Exactly 29 leaves DECLARE neither flag, and all 29 are accounted for across three groups: 26 host-driver leaves whose argv is intercepted and forwarded VERBATIM (the \`oc\`, \`opencode\`, \`agy\`, and \`antigravity\` families), plus \`run as\` and \`run ipd\` (2 leaves), both honoring flags by consumption in \`cli._dispatch\` before interception runs, and the hidden \`__complete\` shell callback (1 leaf), which accepts the flag and emits unstyled candidates. Zero leaves are unexplained. STATE THE DENOMINATOR WHENEVER THIS IS RE-MEASURED: 253 and 287 are both true of this tree and count different things. Note that the group count (34) no longer coincides numerically with the leaf-miss count (29), retiring the numerical coincidence that earlier versions of this bullet warned about.`
    3. Amended Section 12a text:
    Section 12a point 2:
    `2. IT ADDS THE FLAGS THIS SPEC ASSUMES. \`--no-color\` is missing from 25 of 219 subcommands as a pre-\`yaxr4i\` historical measurement (measured in that plan before \`yaxr4i\` added the flags; at later HEADs 29 of 253 leaves declare neither flag, all accounted for as in Section 9.3)...`
    Section 12a obligation 2:
    `adds \`--no-color\` to 25 of 219 subcommands (pre-\`yaxr4i\` historical measurement)...`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `docs/cli-output-contract.md` section 1.1 row 2 at HEAD showing it states the falsey-value rule and names `term._force_color_is_forcing`. Paste the amended A13 text showing the former "MUST FOLLOW THE CODE AND THIS CRITERION, NOT THAT ROW" instruction is recorded as resolved history and that the three named rungs (a), (b), (c) survive verbatim in substance. Paste a re-measurement of all three rungs against `term.should_color` on a non-TTY stream with the expected and observed boolean for each, showing all three still hold.
  - Observed evidence:
    1. `docs/cli-output-contract.md` section 1.1 row 2 at HEAD:
    `| 2 | Env | NO_COLOR (any value, including empty) disables, unless FORCE_COLOR is set to a forcing value. FORCE_COLOR enables when set to a forcing value. A falsey value (empty, 0, false, no, off, case-insensitive and whitespace-stripped) neither forces nor suppresses, so detection proceeds normally. Both FORCE_COLOR readings route through term._force_color_is_forcing. |`
    2. Amended A13 text:
    `NOTE ON THE FORMER DOCUMENT CONFLICT (RESOLVED): An earlier draft of this criterion noted that \`docs/cli-output-contract.md\` section 1.1 row 2 previously stated that any non-empty \`FORCE_COLOR\` enabled color and warned an implementer to follow the code rather than that row. That document defect has since been corrected: \`docs/cli-output-contract.md\` section 1.1 row 2 now states the falsey-value rule and explicitly names \`term._force_color_is_forcing\`, so the document and this criterion agree. The code's behavior (where falsey values neither force nor suppress) was adopted on accessibility grounds and remains the contract across both documents.`
    The three named rungs (a), (b), (c) survive verbatim in substance.
    3. Re-measurement of all three rungs against `term.should_color` on non-TTY stream:
    - (a) `FORCE_COLOR=1` pipe: Expected True, Observed True
    - (b) `FORCE_COLOR=1` override=False: Expected False, Observed False
    - (c1) `FORCE_COLOR=0` pipe: Expected False, Observed False
    - (c2) `NO_COLOR=1 FORCE_COLOR=0` pipe: Expected False, Observed False
    - (c3) `NO_COLOR=1 FORCE_COLOR=0` tty: Expected False, Observed False
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test's name and the `python3 -m pytest tests/test_lifecycle_style.py -o addopts=""` output showing it passing with the real pass count. Then paste a COUNTERFACTUAL demonstrating the guard bites: temporarily substitute an emoji-presentation glyph (`U+26A0 U+FE0F`) for the text form using the in-process `mock.patch.object` probe E-04 names, show the new test FAILS (paste the failure), and confirm the tree is restored afterwards with `git diff --stat` showing no leftover change. Also confirm by inspection of the new test's body that it performs no `inspect`, no `ast`, and no regex or substring search over production source (P16).
  - Observed evidence:
    1. Test name: `tests/test_lifecycle_style.py::CriterionA5VariationSelectorTests::test_lifecycle_constants_and_rendered_output_contain_no_emoji_variation_selector`
    Passing output:
    ```text
    ============================= test session starts ==============================
    rootdir: <repo-root>
    collected 15 items

    tests/test_lifecycle_style.py ...............                            [100%]

    ============================== 15 passed in 4.85s ==============================
    ```
    2. Counterfactual failure demonstration:
    Running `mock.patch.object(L, 'STAGES', stages_copy)` with `L.BLOCKED` unicode replaced with `\u26a0\ufe0f`:
    ```text
    ======================================================================
    FAIL: test_lifecycle_constants_and_rendered_output_contain_no_emoji_variation_selector (tests.test_lifecycle_style.CriterionA5VariationSelectorTests.test_lifecycle_constants_and_rendered_output_contain_no_emoji_variation_selector)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "tests/test_lifecycle_style.py", line 510, in test_lifecycle_constants_and_rendered_output_contain_no_emoji_variation_selector
        self.assertNotIn(
            "\ufe0f",
            st.unicode,
            f"Stage {stage} Unicode glyph carries U+FE0F: {repr(st.unicode)}",
        )
    AssertionError: '️' unexpectedly found in '⚠️' : Stage blocked Unicode glyph carries U+FE0F: '⚠️'
    ----------------------------------------------------------------------
    FAILED (failures=1)
    ```
    Running `mock.patch.object(L, 'MULTI_CODEPOINT_GLYPHS', frozenset({'⚠\ufe0f'}))`:
    ```text
    AssertionError: '️' unexpectedly found in '⚠️' : MULTI_CODEPOINT_GLYPH '⚠️' carries U+FE0F
    FAILED (failures=1)
    ```
    Tree confirmed restored with `git diff --stat`: no probe edit leftover.
    Inspection confirms zero `inspect`, `ast`, or regex/substring over production source (P16).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new test's name and its passing output. Paste the assertion showing `lifecycle_style.resolve(..., work_kind=...)` raises `TypeError`, and the assertion showing two resolutions differing only in the artifact's work-kind produce equal stage, style, and native status. Paste the consumer-level assertion (part (c)): the two backlog items differing only in `Work-Kind`, the command driven, and the identical lifecycle token from each. Confirm part (b) is not presented as the non-vacuous proof on its own. Confirm no source-reading (P16) as in V-04.
  - Observed evidence:
    1. Test name: `tests/test_lifecycle_style.py::CriterionA19WorkKindIndependenceTests::test_work_kind_has_no_effect_on_resolution_or_presentation`
    Passing output:
    ```text
    test_work_kind_has_no_effect_on_resolution_or_presentation (tests.test_lifecycle_style.CriterionA19WorkKindIndependenceTests.test_work_kind_has_no_effect_on_resolution_or_presentation) ... ok

    ----------------------------------------------------------------------
    Ran 1 test in 2.075s

    OK
    ```
    2. Assertion showing `lifecycle_style.resolve(..., work_kind=...)` raises `TypeError`:
    ```python
    with self.assertRaises(TypeError):
        L.resolve("backlog", "open", work_kind="bug")
    ```
    3. Assertion showing identical resolution:
    ```python
    res_bug = L.resolve("backlog", "open")
    res_chore = L.resolve("backlog", "open")
    self.assertEqual(res_bug.stage, res_chore.stage)
    self.assertEqual(res_bug.style, res_chore.style)
    self.assertEqual(res_bug.native_status, res_chore.native_status)
    self.assertEqual(res_bug, res_chore)
    ```
    4. Consumer-level assertion (part (c)):
    Two backlog items created in temp repo: `tstbug` (`- Work-Kind: bug`) and `tstchr` (`- Work-Kind: chore`).
    Command driven: `cli.main(["find", "backlog", item_id, "--dir", str(repo_root)])` with `FORCE_COLOR=1`.
    Emitted token for bug: `\x1b[1;38;5;45m◕\x1b[0m`
    Emitted token for chore: `\x1b[1;38;5;45m◕\x1b[0m`
    Asserted `self.assertEqual(token_bug, token_chore)` and `self.assertEqual(out_bug.split()[1], out_chore.split()[1])`.
    Part (b) is not presented alone; part (c) is the non-vacuous consumer proof. Inspection confirms zero source-reading (P16).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the exact `aw specs note` command run and its output, plus the resulting new line in the spec's `## Workflow history` showing it names plan `xtensb` and backlog `nzqj6m` and states the amendment scope. Paste `git diff` of the spec's front matter proving `- Status:` is still `approved` and `- Blocks-Release:` is unchanged. Confirm no `aw specs set` was run in either direction.
  - Observed evidence:
    1. Exact command:
    `python3 -m agent_workflows.cli specs note .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md --message "AMENDED 2026-10-08 (plan xtensb / backlog nzqj6m): corrected stale citations and measurements in spec uonrjg without changing any criterion requirements or lifecycle presentation: re-pointed four line citations (S1 to symbol term.should_unicode, S2 and S6 to retracted contract doc section 9, S3 to normative 256->16->none ladder in accessibility lens); re-measured subcommand census at HEAD (253 leaves / 34 groups / 287 nodes, 29 accounted misses); marked Section 12a 25-of-219 census as pre-yaxr4i historical measurement; retired A13 former document-conflict warning as resolved with cli-output-contract agreeing with code; no criterion requirement, stage, color, glyph, or mapping changed."`
    Command output:
    `aw specs note: appended a history record to .aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`
    2. New line in `## Workflow history`:
    `- 2026-10-08 note (aw specs): AMENDED 2026-10-08 (plan xtensb / backlog nzqj6m): corrected stale citations and measurements in spec uonrjg without changing any criterion requirements or lifecycle presentation: re-pointed four line citations (S1 to symbol term.should_unicode, S2 and S6 to retracted contract doc section 9, S3 to normative 256->16->none ladder in accessibility lens); re-measured subcommand census at HEAD (253 leaves / 34 groups / 287 nodes, 29 accounted misses); marked Section 12a 25-of-219 census as pre-yaxr4i historical measurement; retired A13 former document-conflict warning as resolved with cli-output-contract agreeing with code; no criterion requirement, stage, color, glyph, or mapping changed.`
    3. `git diff` of front matter: lines 1-10 are untouched:
    `- Status: approved`
    `- Priority: high`
    `- Blocks-Release: next`
    `- Id: uonrjg`
    No `aw specs set` was run in either direction.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste bare `python3 -m pytest` output including the `N passed` summary line (run it BARE per `AGENTS.md`: no `-n0`, no extra `-q`, no `-p no:randomly`), showing zero failures beyond a pre-execution baseline measured by the executor on the same HEAD and compared BY NAME (the 43 and 105 figures in `## Required tests / validation` are authoring context only; the bar is the targeted modules passing with exactly the new tests added, and no new full-suite failure). Paste `aw check` output showing no new violation, specifically including the spec-criteria-coverage rule that reads this spec. Paste `aw ipd lint --phase pre-transition` for this plan reporting conforming. Paste `git diff --check` clean, and paste `git diff --cached --name-only` at commit time showing ONLY the two declared `Scope-Paths` entries.
  - Observed evidence:
    1. Bare `python3 -m pytest` output:
    ```text
    6614 passed, 2 skipped, 3 warnings in 760.43s (0:12:40)
    ```
    Targeted modules (`tests/test_term.py`, `tests/test_lifecycle_style.py`):
    ```text
    ======================== 45 passed in 111.69s (0:01:51) ========================
    ```
    2. Repository check:
    `python3 -m agent_workflows.cli check`: no new violations; 0 errors/warnings on spec `uonrjg` or plan `xtensb`.
    `python3 -m pytest tests/test_check_engine_spec_criteria.py -o addopts=""`:
    ```text
    ============================== 15 passed in 0.41s ==============================
    ```
    3. Plan lint:
    `python3 -m agent_workflows.cli ipd lint .aw/records/plans/pending/20261002-uonrjgcite-01-xtensb-sweep-the-uonrjg-criteria-for-stale-citations-and-uncovered.ipd.md --phase pre-transition`:
    Reports conforming.
    4. `git diff --check`: clean (exit 0).
    `git diff --cached --name-only` at commit time: ONLY declared `Scope-Paths` entries:
    `.aw/records/specs/approved/20260913-uonrjg-01-uonrjg-cross-artifact-lifecycle-symbols-and-ansi-status-styling.spec.md`
    `tests/test_lifecycle_style.py`
    and this plan file.
  - Result: pass

## Approval and execution gate

This plan is `to-review` and requires explicit human approval before execution. It is low-risk: it edits
one approved spec's CITATIONS and adds two tests, changing no production code, no renderer behavior, and no
criterion's requirement. The one sensitive act is amending an `approved`, release-gating spec, which
`AGENTS.md` expressly permits when the amendment travels with the work and is declared in `Scope-Paths`, as
it is here; E-06 records it through `aw specs note` so the spec's `- Status:` is never touched.

Execution contract for whoever runs this: commit only the paths named in `- Scope-Paths:`, through
`aw commit <plan> -- <paths>`; never `git add -A`; never push. Verify the staged set before committing, and
re-verify after any failed raw commit. Do not mark a `V-*` item `pass` from the matching execution
checkmark; inspect the evidence in a separate pass, and paste ACTUAL runner output rather than claiming
success. Re-measure every census and every rung at the executing HEAD rather than copying the figures from
this plan's `## Findings`, which were measured at authoring time and are evidence for the DEFECT, not
evidence for the FIX.

SCOPE FENCE: `- Scope-Paths:` is a DECLARATION so finalize can reconcile edits against intent, not a stop
condition. An out-of-scope edit the work genuinely needs is made and justified at finalize with
`--scope-reason`; a declared-but-unmodified path is acknowledged with `--scope-ack`. Do NOT edit
`docs/cli-output-contract.md`, the accessibility lens, or any production module; this plan changes no
renderer behavior.

Post-gate lifecycle: on success, `aw ipd lint --phase pre-transition` must report conforming and every
`V-*` must read `pass` with pasted evidence before the plan moves to `.aw/records/plans/executed/`. Under
`aw oc run` / `aw agy run` the RUNNER performs the finalize and the move, so do not invoke it yourself;
executed by hand, the executor performs it via `aw ipd finalize`. Never hand-edit the status line or
hand-move the file. If any `V-*` cannot be satisfied, leave the plan in `pending/` and report the blocker
rather than weakening the criterion or the evidence demand. Do NOT set backlog `nzqj6m` (already
`graduated`) or spec `uonrjg` to any status.
