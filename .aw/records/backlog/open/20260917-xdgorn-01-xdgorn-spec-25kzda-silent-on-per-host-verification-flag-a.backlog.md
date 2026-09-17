- Id: xdgorn
- Status: open
- Set: xdgorn
- Priority: medium
- Work-Kind: bug
- Summary: Spec 25kzda does not document that --no-verify means different things on the two run hosts

## Workflow history
- 2026-09-17 created (aw backlog): Spec 25kzda does not document that --no-verify means different things on the two run hosts

Measured live at 4a1bb873 by plan s16omw (rununify Order 10, E-01/E-04).

WHAT IS WRONG. The two run hosts ship an INCOMPATIBLE verification-flag contract, and the spec that governs the run flag surface does not mention it.

  spelling        oc dest (start)   agy dest (start)
  --validate      validate          validate
  --no-validate   validate          validate
  --verify        validate          ABSENT
  --no-verify     validate          no_verify
  --audit         validate          ABSENT
  --no-audit      validate          no_verify

On agy `resume`, NONE of the six is registered. So `--no-verify` is an alias of `--no-validate`'s tri-state on oc and a SEPARATE store-true dest on agy.

WHY THE EXISTING CONTRACT TEST CANNOT CATCH IT. tests/test_run_flag_surface.py reads spec 25kzda 2.1's grammar block as a FILE and checks it in both directions, but that grammar declares neither `--validate` nor `--verify` nor `--no-verify`; only the twelve `RUN_POLICY_FLAGS` rows are spec-governed. The spec mentions the runner `--no-verify` only in Section 2.1's 2026-09-05 amendment note and the RUN-COMMIT-GATEWAY rows, and there only to separate the RUNNER sense from the GIT sense. Nothing states the per-host difference.

WHY IT MATTERS. The asymmetry is deliberate and defended in code by a build-time guard (agent_workflows/agy_runipd.py:2034, `assert_verification_flags_are_distinct`), whose docstring records that registering oc's alias list on agy would make BooleanOptionalAction steal agy's shipped spellings. Both branches of that hazard were executed and confirmed by s16omw. So the design is sound; the DOCUMENTATION of it is missing, which means an operator reading the spec cannot learn that the same flag differs by host, and a future de-duplication has no spec sentence to check itself against.

SUGGESTED FIX: amend spec 25kzda 2.1 to declare the verification flags per host, with the reason for the asymmetry, and extend the contract test's coverage to them. The asymmetry itself is now pinned in tests/test_rununify_build_parser_characterization.py::TheVerificationDestAsymmetryIsPinnedPerHost.
