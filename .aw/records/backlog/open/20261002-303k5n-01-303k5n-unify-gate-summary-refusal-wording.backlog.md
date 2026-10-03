- Id: 303k5n
- Status: open
- Set: 303k5n
- Priority: low
- Work-Kind: chore
- Summary: Decide whether specs.run_set's inline --gate-summary refusal should adopt the shared descriptive-refusal vocabulary, which changes a shipped user-facing message and the non-regression test pinning it verbatim

## Workflow history
- 2026-10-02 created (aw backlog): Decide whether specs.run_set's inline --gate-summary refusal should adopt the shared descriptive-refusal vocabulary, which changes a shipped user-facing message and the non-regression test pinning it verbatim

FILED AS THE CARRIER for the one outstanding obligation in plan `685iq8` (Set `zllcnv`), which hoists the
duplicated `_refuse_unsafe_descriptive` helper into `attention_contract` but deliberately leaves this
fourth refusal alone.

THE SITUATION, measured 2026-10-02 at HEAD `adfda04dc`. `specs.run_set` refuses an unsafe
`--gate-summary` INLINE, with a bare `A.is_safe_descriptive(gs)` test and its own message,
`aw specs set: --gate-summary must be a bounded single control-char-free line`, returning 1. That is
structurally the same Section 8.8 refusal the shared helper performs, so it reads as a fourth copy.

WHY IT IS A DECISION AND NOT A CLEANUP. The two wordings are NOT interchangeable. The inline one lists
all three properties in one sentence; the shared helper names WHICH property was violated and, for the
length case, the actual length (`exceeds maximum length of 300 characters (N > 300)`). So unifying them
CHANGES A SHIPPED USER-FACING MESSAGE. It also breaks a passing test on purpose:
`tests/test_specs_releases_descriptive_safety.py::test_non_regression_already_validated_run_set_flags_preserved`
asserts that exact string verbatim and `rc_gs == 1`. Two executed plans already declined this trade for
this reason (`dtg7dz`'s Deferred section, and `uz05bl` OQ-02), so a third silent decline is not the
answer either; the point of this item is to settle it once, with the message decision made explicitly
rather than as refactor collateral.

WHAT TO DECIDE, and it is genuinely open. Either (a) adopt the shared vocabulary, accepting a changed
message and updating that non-regression test, on the argument that the shared wording is strictly more
informative and one vocabulary across trees is the goal the hoist served; or (b) keep it inline
permanently and record that `--gate-summary` has its own wording by design, in which case the
non-regression test is correct as written and should say so. Option (a) is the better end state on
message quality; option (b) is cheaper and preserves a shipped string. This is a maintainer call on
whether a clearer error message justifies changing one.

VERIFY BEFORE STARTING, do not trust this note: re-read `specs.run_set`'s gate-handling branch and
confirm the inline refusal is still spelled separately, and re-run that non-regression test to confirm
it still pins the string. If plan `685iq8` has not executed yet, the shared helper may still live in
`backlog.py` rather than `attention_contract`, which changes only where to import from, not the decision.
