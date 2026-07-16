# Section 3 - Tests / regression

Verdict: sound. Suite 258 passed / 1 skipped (skip is a justified conditional release-tag assertion).
- D85 regression tests (InstallCorrectnessTests, test_install_all_isolates_systemexit, short-secret redaction) genuinely test the fixes.
- No residual date/tmpdir/order flakiness (D78 lesson held). Tests meaningful, not vacuous. Resource hygiene clean.
Gap noted: no regression test for the engine.run() multi-repo SystemExit path (ties to REL-001; the corrective IPD adds one).
