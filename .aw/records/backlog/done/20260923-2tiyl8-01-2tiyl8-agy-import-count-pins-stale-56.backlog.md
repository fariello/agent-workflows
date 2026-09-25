- Id: 2tiyl8
- Status: done
- Set: 2tiyl8
- Priority: medium
- Work-Kind: bug
- Summary: Two runner-layering tests assert agy imports 56 names from oc_runipd; the re-homing already reduced it to 4, so both fail at HEAD

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: moot: both pinning tests deleted in 80db6750
- 2026-09-23 created (aw backlog): Found while executing IPD iuxtjy (graduate Order 02). Both failures are PRE-EXISTING at HEAD 4c1fffde and unrelated to that plan's paths; measured in a clean stash of my own edits.

WHAT IS WRONG. Two tests pin a literal count of the names `agy_runipd` imports from `oc_runipd`, and both numbers are stale, so the suite is red at HEAD on a fact that a landed refactor already improved:

  tests/test_oc_runipd.py::AgyCardIsNotResolvableTests::test_the_shared_symbol_lives_in_runner_shared_NOT_in_oc_runipd
  tests/test_agy_runipd_cli.py::AgyCostAttributionTests::test_agy_does_not_import_the_record_builder_FROM_oc_runipd

Both assert `len(from_oc) == 56`. MEASURED at HEAD 4c1fffde by AST: the real value is 4, the names being `build_verify_and_continue_notice`, `classify_recovery_disposition`, `record_item_spec_edits`, `route_recovery_turn`.

WHY IT MATTERS RATHER THAN BEING COSMETIC. The direction of the drift is the layering IMPROVING: backlog `cnwy8g`'s re-homing work moved 52 of those names into `runner_shared`, which is exactly what the tests exist to encourage. So the tests now FAIL THE REPOSITORY FOR DOING THE RIGHT THING, and worse, they fail in the direction that trains a reader to treat a red suite as normal. Each test's REAL assertion (that a specific shared symbol is NOT imported from `oc_runipd`) still passes; only the census line is wrong.

THE FIX IS NOT SIMPLY 56 -> 4. The pattern this repository already uses elsewhere is DERIVE, NEVER PIN: assert the count did not RISE from a recorded baseline rather than equal a literal, so the next legitimate re-homing does not turn the suite red again. Plan `lyo1tz` records the same class of drift (47 -> 48) and IPD `iuxtjy`'s own E-05 was written to measure rather than pin for this reason.

NOTE A THIRD PRE-EXISTING FAILURE IS SEPARATE AND ALREADY FILED: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped fails from an ambient OPENCODE_CONFIG_CONTENT in the executing environment, which backlog `j08jky` already owns.
