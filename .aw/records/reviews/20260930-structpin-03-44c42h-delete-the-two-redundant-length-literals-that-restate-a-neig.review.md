# Review findings: plan 44c42h

- Subject-Id: 44c42h
- Subject-Type: ipd
- Reviewed-At: 2026-09-30
- Reviewer: opencode/its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-401 (HIGH, fixed), PR-402 (HIGH, fixed), PR-403 (MEDIUM, fixed), PR-404 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `b48bb220`. The plan file is committed and unmodified
(`git status --short` empty before edits), so no pre-review snapshot was needed. Structural preflight
`aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE semantic
review. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator
child-row check does not apply.

All probe work was done under the gitignored `tmp/` and removed afterwards. No production file and no
test was modified by this review.

THE DIAGNOSIS IS CORRECT AND MOST OF THE PLAN IS WELL MEASURED. Re-derived independently:

- F-1 REPRODUCES EXACTLY. I re-implemented the AST scan from the plan's own description and got 17
  rows at the same line numbers, including `tests/test_reaskscore_composed.py:98
  len(runner_shared.TERMINAL_STATES)==24` and `tests/test_term.py:915 len(T.STAGE_COLOR_16)==20`.
- F-2 REPRODUCES: `len(TERMINAL_STATES)` 24, `len(STAGE_COLOR_16)` 20, `len(ALL_STAGES)` 20,
  set-equality True, `len(TERMINAL_STATES_CANONICAL)` 14.
- F-3 REPRODUCES: `test_terminal_states_union` asserts `runner_shared.TERMINAL_STATES ==
  frozenset(EXPECTED_CANONICAL_STATES | set(EXPECTED_LEGACY_ALIASES.keys()))` with both operands
  hand-written in that file (14 and 10). A name-level pin, as claimed.
- F-5 REPRODUCES: both test bodies read in full; no other assertion depends on either literal.
- F-8 REPRODUCES: the comment `# 23 + \`retired\` ...` sits immediately above the `== 24` assertion.
- F-9 REPRODUCES: `validate_16_color_palette()` is called at module level in `term.py` and raises
  naming missing/unknown stages.
- F-10 REPRODUCES: `55 passed in 7.47s` for the three files with `-o addopts=""`.
- F-11 REPRODUCES: `b02ohu` declares five unrelated `Scope-Paths`, `76ic0k` declares
  `tests/test_no_code_structure_pins.py, CONTRIBUTING.md`; neither collides. Both are `approved`.
- The `b02ohu` deferral rows ending `- Carrier: aaoapo` exist for both cases, and the `aaoapo` item
  text matches what the plan quotes, including its SUGGESTED FIX.
- `GUIDING_PRINCIPLES.md` P16's "No count or census pins" and "Verify test sensitivity with mutation"
  bullets are quoted accurately, as is `term.validate_16_color_palette`'s "second table that rots"
  docstring.

TWO HIGH FINDINGS DEMOLISH E-02's JUSTIFICATION, and with it the plan's central authored judgement
that the two cases are asymmetric. The plan's own gate warned an executor NOT to simplify E-02 into a
deletion; that warning was built on measurements that do not hold.

PR-402 (HIGH) is the decisive one. F-6 claimed the stage vocabulary has no absolute pin anywhere in
the suite, concluding that deleting Case 2's literal loses coverage and that a hand-transcribed
20-name frozenset must replace it. THE PIN EXISTS. `tests/test_lifecycle_style.py::StageTableTests::
test_stage_table_and_glyphs_progression` calls `_parse_spec_section5()`, which READS the spec file
and extracts Section 5's table, then asserts `module_rows == spec_rows` across all 20 rows and 5
fields. F-6's `rg ALL_STAGES` search missed it because the assertion never mentions `ALL_STAGES`.
That pin is strictly STRONGER than the transcription E-02 proposed, and its own helper docstring says
so: "Parsing rather than transcribing is the whole point: a transcription slip in any of 20 rows
times 4 fields fails here instead of being read past." Measured by patching `_STAGE_ROWS`, `STAGES`,
`STAGE_ORDER` and `ALL_STAGES` together: dropping ANY one of the 20 stages turns that test RED,
including all three stages the edited `test_term` misses. It carries no `slow`/`livecorpus` marker and
runs in the default suite (`1 passed in 0.14s`).

PR-401 (HIGH). F-4's counterexample is also wrong, in a way that matters because it is the single
measurement E-02's shape rested on. The probe compared the two SETS in isolation and never ran the
test. Re-measured by extracting the real test body, deleting the `len` line (exactly what the backlog
item's suggested fix produces) and running it under a coordinated shrink of each stage in turn: 17 of
20 go RED with `KeyError: '<stage>'`, raised by `color_16_for_stage` inside the test's OWN separation
and collapse assertions. `abandoned`, F-4's chosen victim, is among the 17: it is a member of the gray
collapse group. Only `authority-queued`, `reusable` and `review-queued` escape, and F-6's pin covers
those. So the residual gap was 3 stages, not 20, and after PR-402 it is zero.

NEW FINDING F-12 records why the replacement would have been actively harmful rather than merely
unnecessary. Simulating a fully coordinated, deliberate vocabulary removal (the spec's Section 5 row
deleted too), the parsed pin legitimately AGREES (`module_rows == spec_rows` True at 19 rows), because
the spec is the normative source and it was amended. A hand-written 20-name frozenset would go RED
there, i.e. exactly when the change is correct and approved. That is the "tax on correct changes"
backlog `aaoapo` and `5zyuc8` exist to remove, so adding the list would have made this plan
reintroduce its own Set's defect in a new place. `lifecycle_style` additionally exposes each stage as
a named constant specifically "so a consumer never spells one as a bare literal", a further reason not
to write 20 bare literals into a test.

CONSEQUENT EDITS. E-02 is now a plain one-line deletion matching E-01, so the diff is SMALLER than
authored. OQ-01's answer is REVERSED from "pin it by name" to "delete it outright", with the reversal
and its measurements recorded in place rather than the question being rewritten. V-02 now demands a
coverage-PRESERVATION demonstration (the surviving cross-file pin shown RED under a coordinated
shrink, for one of the three stages `test_term` does not name plus one it does) instead of a
RED-then-GREEN on a new assertion, and makes the pin a stop condition exactly as V-01 already did for
Case 1. Task group 2's heading, E-01's "and is NOT safe for Case 2" parenthetical, the P16 convention
bullet, proposed change 2, the validation paragraph and all three gate paragraphs were swept.

PR-403 (MEDIUM). The Goal claimed both tests would assert "strictly MORE" afterwards. For E-01 that
was never true (a pure deletion) and after PR-402 it is not true for E-02 either. Overclaiming the
benefit of a deletion is how a later reader concludes coverage was added when it was not. FIXED: the
Goal now states both cases assert exactly as much with one fewer thing to update, and Under-scope
records the one genuinely accepted residue (a fully coordinated, spec-amended vocabulary removal is
detected by no test, deliberately, because failing on it would be the tax).

PR-404 (LOW). The Deferred row for the third scan instance explicitly said "FILING THE ITEM IS THE
REVIEWER'S CALL". Taking that call: FILED as backlog `rdtme9`
(`.aw/records/backlog/open/20260930-structpin-01-rdtme9-redundant-canonical-count-literal.backlog.md`,
`chore`/`low`, Set `structpin`), with the measurement and the one-line fix direction. The row now
carries `- Carrier: rdtme9` and `- Carrier-Evidence:` instead of a declination, and Under-scope no
longer says "unfiled". `aw backlog check` reports all items conform.

NOTHING WAS DEFERRED and no finding is left OPEN, so no escalation to a `- Blocking: yes` question is
required by Step 4's gate threshold (`review_findings_gate.block_at`, default `HIGH`).

`aw ipd lint --phase review-finalize --agent` reports `conforming` after the revisions.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Given that the stage vocabulary IS pinned by a spec-parsing test, should E-02 delete the literal or keep a replacement anyway as defence in depth? | Delete it outright; add nothing. | (a) Keep the authored hand-transcribed 20-name frozenset as a second line of defence, rejected because F-12 measures it firing only on CORRECT spec-approved changes, which is the tax this Set removes, and because it duplicates a table a shipped test already parses (P8, and the "second table that rots" docstring); (b) assert `set(STAGE_COLOR_16) == set(ALL_STAGES)` plus a count derived from the spec at test time, rejected as a more complex restatement of what the spec-parsing test already does in a better place. | `tests/test_lifecycle_style.py` `_parse_spec_section5` + `assertEqual(module_rows, spec_rows)`; probe showing that test RED for all 20 stages and for the 3 `test_term` misses; F-12's spec-amended probe (`module_rows == spec_rows: True` at 19 rows); `agent_workflows/term.py` `validate_16_color_palette` docstring. | yes |
| D-2 | Was F-4's falsification enough on its own to make E-02 a deletion, or was F-6 needed too? | Both were needed, and both are recorded; F-6 is the decisive one. | Treating F-4 alone as sufficient, rejected because F-4 corrected leaves a real 3-stage gap (`authority-queued`, `reusable`, `review-queued`) which, absent F-6, would have justified a narrow replacement. Recording only F-6, rejected because F-4's probe method (comparing two sets instead of running the test) is the reusable lesson. | Probe output `17 ERROR (KeyError)` / `3 PASS (UNDETECTED)`; the spec-parse probe RED for those same 3. | yes |
| D-3 | Should the third scan instance be filed, which the plan's Deferred row left to the reviewer? | Yes, file it as a backlog item. | Leaving it as a `Carrier-Declined` observation in the plan, rejected because the row itself says filing is the reviewer's call and the plan reaches `executed/` soon after, at which point an unfiled observation stops being visible in `aw attention`; filing it as a `bug`, rejected because the literal is correct today and no user waits on it. | The plan's own Deferred row text; measured `len(TERMINAL_STATES_CANONICAL) == 14` matching a 14-member `EXPECTED_CANONICAL_STATES` on the preceding line; `aw backlog new ... --apply` wrote `rdtme9`. | yes |
| D-4 | OQ-01 was `Status: resolved` with an answer review has now inverted. Reopen it, or rewrite it? | Keep it `resolved`, replace the rationale with the corrected one, and state plainly that the answer was REVERSED at review with the measurements that reversed it. | Reopening as `open`, rejected because the question is genuinely settled (more firmly than before) and an open non-blocking question adds noise without a decision pending; silently rewriting as if the original answer never existed, rejected because it would destroy the record of a measured correction that a future reader needs in order not to re-derive the transcription idea. | Workflow guidance that a resolved question's reasoning must be corrected where falsified (the same treatment applied to `1dcl10` OQ-02 earlier in this sweep); F-4, F-6 and F-12 as the reversing evidence. | yes |
