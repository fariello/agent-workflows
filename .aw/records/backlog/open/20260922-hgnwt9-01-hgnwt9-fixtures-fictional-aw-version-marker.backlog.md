- Id: hgnwt9
- Status: open
- Set: hgnwt9
- Priority: low
- Work-Kind: chore
- Summary: Two test fixtures still seed the install marker at the fictional .aw/VERSION, so they silently assert against an uninstalled repo

## Workflow history
- 2026-09-22 created (aw backlog): Two test fixtures still seed the install marker at the fictional .aw/VERSION, so they silently assert against an uninstalled repo

Found while executing IPD h90ij1 (which fixed `aw doctor`'s probe and the two fixtures that the fix made FAIL).

TWO MORE FIXTURES seed the framework install marker at `.aw/VERSION`, a path NO supported layout creates (the real ones are `.aw/system/VERSION`, `.aw/system/workflows/VERSION`, `.agents/workflows/VERSION`; see `engine.read_installed_version`). They do not FAIL today, which is why h90ij1 did not have to touch them, but each silently exercises a weaker condition than it reads as asserting:

1. `tests/test_doctor_and_marker.py::VersionDriftSourceRepoTests::test_installed_target_stale_flagged`
   Its comment says 'an installed target with a VERSION that does not match packaged' and it writes `.aw/VERSION = 0.0.1`. Measured post-h90ij1: the drift emitted is `doctor.version-not-installed`, NOT a stale finding. The test passes only because its assertion is the loose `d.rule.startswith('doctor.version-')`, which `not-installed` also satisfies. So the STALE path it exists to cover is never exercised.

2. `tests/test_check_recipe.py::CheckRecipeUnitTests` setUp writes `.aw/VERSION = 0.1.0`.
   Measured: `engine.read_installed_version` returns None for that fixture, so `check_engine.check_system_layout` takes its case (a) 'not an installed AW workspace' early return and emits nothing. Any layout-presence behavior the suite believes it covers on an installed workspace is skipped.

REMEDY: move the marker to `.aw/system/VERSION` in both, and in (1) tighten the assertion to the specific `doctor.version-stale` rule it means to pin. Note that making a fixture genuinely installed may also require `engine.emit_layout_artifacts(root)`, since `check_system_layout` correctly requires the emitted layout document of an installed workspace; that is exactly what h90ij1 did for the two fixtures it had to fix.

Low priority and `chore` rather than `bug`: no shipped behavior is wrong and no user is affected, the cost is test COVERAGE that is weaker than it appears.
