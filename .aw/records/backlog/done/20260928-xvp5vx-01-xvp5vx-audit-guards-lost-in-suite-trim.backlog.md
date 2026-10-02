- Id: xvp5vx
- Status: done
- Graduated-To: xvp5vx
- Set: xvp5vx
- Priority: medium
- Work-Kind: chore
- Summary: audit what properties lost their only guard in the 19313eed suite trim

## Workflow history
- 2026-10-01 done (aw backlog): closed by aw agy run: IPD oyh28b executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260930-xvp5vx-01-oyh28b-build-a-reproducible-lost-guard-census-over-the-two-suite-tr.ipd.md); evidence .aw/records/plans/executed/20260930-xvp5vx-01-oyh28b-build-a-reproducible-lost-guard-census-over-the-two-suite-tr.ipd.md
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053059Z-3200713: oyh28b
- 2026-09-28 note (aw backlog): Maintainer ruling: We test outcomes and functionality, never code structure or text in a script. Zero tests that pin code. Any audit of deleted tests must strictly ignore tests that pinned code, AST, or text, and must never propose restoring them; only genuine behavioral outcomes lacking coverage may be triaged.
- 2026-09-28 set (aw backlog): Second measured instance, found while authoring plan 7dz3wv (backlog xdgorn) at HEAD beb37773: the per-host VERIFICATION FLAG dest table lost its only guard in the same trim. 7ebc2964 moved TheVerificationDestAsymmetryIsPinnedPerHost out of test_rununify_build_parser_characterization.py into test_rununify_build_parser.py, then 19313eed deleted that file too, along with test_run_flag_surface.py. Measured green-under-mutation on a full bare suite (2937 passed, 2 skipped): adding a verification flag to agy's resume parser, and removing --verify/--audit from oc's RESUME parser. Note the half-coverage shape, which is what makes this class of loss hard to see: the same removal on oc's START parser DOES fail one surviving test (test_oc_runipd.py::VerifierPromptTests::test_audit_flag_options), so a spot check on one subcommand reads as covered while the other is bare. Plan 7dz3wv closes this instance; the general audit remains open.
- 2026-09-28 created (aw backlog): audit what properties lost their only guard in the 19313eed suite trim

Found while authoring plan t0ovw6 (backlog xw4rb7), measured at HEAD 98e3ea9a.

THE GENERAL PROBLEM. Commit 19313eed ("test: trim test suite from 9,136 to under 2,000 tests") deleted roughly 7,000 tests. Some of those tests were the ONLY guard on a property the repository still relies on and still DOCUMENTS as guarded. Nothing has audited which.

THE MEASURED INSTANCE that prompted this. Backlog xw4rb7 pointed at one symbol, `add_output_mode_flags`, and the audit of that single symbol found:

* its per-host `--help` text can be cross-contaminated with a FULL BARE SUITE STILL GREEN (2935 passed, 2 skipped) - and that exact regression already shipped once, in 63b71d8b, filed as backlog 39jkux;
* its lifted body can be RE-INLINED into a host with the full bare suite still green;
* three test files cited as its safety net (test_rununify_build_parser.py, its characterization twin, test_runner_refork_guard.py) are all gone;
* two SHIPPED COMMENTS in oc_runipd.py and agy_runipd.py still cite test_runner_refork_guard.py as a live requirement.

Plan t0ovw6 closes those two gaps for that ONE symbol. It is one sample. The deleted test_runner_refork_guard.py alone held a whole REFORK_TABLE of owned symbols, so the same question applies to every row of it.

THE WORK. Systematically diff what the deleted files ASSERTED against what survives: recover the deleted files from git (19313eed^), enumerate the properties each asserted, and for each determine whether a surviving test covers it. Produce a triage list, not necessarily a fix; each real gap becomes its own item. Prefer MUTATION as the test of coverage (the technique that found both gaps above), since a property can look covered by a test that reads its expected value from the same place the code reads it. CRITICAL MAINTAINER DIRECTIVE: We test outcomes and functionality, never code structure or text in a script. Exclude all deleted tests that tried to pin code, AST, or text (e.g. refork tables, source-reading tests, line counts); only genuine behavioral outcomes lacking coverage may be triaged or restored.

FILED chore AND medium: the outcome is unknown until measured, so no user-perceptible defect is claimed yet, but one sample of size one already yielded two live gaps and one shipped regression.
