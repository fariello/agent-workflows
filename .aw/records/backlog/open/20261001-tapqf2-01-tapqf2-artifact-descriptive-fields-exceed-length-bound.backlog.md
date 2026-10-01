- Id: tapqf2
- Status: open
- Set: tapqf2
- Priority: low
- Work-Kind: chore
- Summary: 883 of 2820 artifact descriptive fields exceed the Section 8.8 length bound, so MAX_DESCRIPTIVE_LEN is corpus-violating at the attention renderer's input set

## Workflow history
- 2026-10-01 created (aw backlog): 883 of 2820 artifact descriptive fields exceed the Section 8.8 length bound, so MAX_DESCRIPTIVE_LEN is corpus-violating at the attention renderer's input set

FILED AS THE CARRIER for the over-length deferred row in plan `qpw45x` (Set `llnvwj`), which escapes Markdown metacharacters at the attention board and deliberately changes no length bound.

MEASURED 2026-10-01 in a lane, over the 2820 descriptive values `attention._extract_detail` actually extracts from `.aw/records/**/*.md`: 883 exceed `attention_contract.MAX_DESCRIPTIVE_LEN` (300). The longest are plan `- Scope:` values carrying several sentences.

THIS IS DISJOINT FROM THE DRIFT-DETAIL ITEMS `7stpjm` AND `0livgf`, and the distinction is the reason this is a separate record. Those two concern a COMPOSED `core.Drift.detail` string that the toolkit itself builds; this concerns the AUTHORED descriptive field of a tracked artifact, read straight out of the file. The gap has a different cause (no writer bounds a plan's `- Scope:`), a different population, and a different fix.

WHAT SECTION 8.8 REQUIRES: "Every descriptive field is a single logical line with a defined maximum length ... Over-length values are a contract violation, not silently truncated", and F10 makes such a violation a stable named `--check` failure. `attention_contract.is_safe_descriptive` already implements the predicate and `attention.unsafe-field` is already in the closed `RULE_IDS` catalog, so no new rule id is needed.

WHY IT CANNOT SIMPLY BE TURNED ON: enforcing the bound at `error` today would fail `aw check` on a clean checkout for 883 artifacts and, worse, DEADLOCK THE LIFECYCLE, because `specs.run_set` re-runs validation on the prospective text and refuses a nonconforming result, so an over-length artifact could not be transitioned to fix itself. Plan `ynhst5` E-01/E-02 measured exactly this for the 2 specs its narrower rule touched and ordered a repair-first fix; at 883 artifacts that route does not scale.

THREE ROUTES, none settled here: (a) a grandfather cutover tier keyed on the artifact's own `- Date:`, the precedent being `CARRIER_CUTOVER_DATE` in `check_engine`; (b) raise the bound to a measured percentile and enforce it, which needs a decision about what the bound is FOR, since the renderer no longer needs it for safety once `qpw45x` lands; (c) enforce at the WRITE path only, so new artifacts conform while existing ones are left alone.

NOTE THE BOUND'S SAFETY JUSTIFICATION WEAKENS once `qpw45x` ships: an over-length value is then a readability and determinism concern rather than an injection one, which argues for (b) or (c) over a hard fail.
