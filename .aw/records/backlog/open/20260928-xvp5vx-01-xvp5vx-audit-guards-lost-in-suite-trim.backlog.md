- Id: xvp5vx
- Status: open
- Set: xvp5vx
- Priority: medium
- Work-Kind: chore
- Summary: audit what properties lost their only guard in the 19313eed suite trim

## Workflow history
- 2026-09-28 created (aw backlog): audit what properties lost their only guard in the 19313eed suite trim

Found while authoring plan t0ovw6 (backlog xw4rb7), measured at HEAD 98e3ea9a.

THE GENERAL PROBLEM. Commit 19313eed ("test: trim test suite from 9,136 to under 2,000 tests") deleted roughly 7,000 tests. Some of those tests were the ONLY guard on a property the repository still relies on and still DOCUMENTS as guarded. Nothing has audited which.

THE MEASURED INSTANCE that prompted this. Backlog xw4rb7 pointed at one symbol, `add_output_mode_flags`, and the audit of that single symbol found:

* its per-host `--help` text can be cross-contaminated with a FULL BARE SUITE STILL GREEN (2935 passed, 2 skipped) - and that exact regression already shipped once, in 63b71d8b, filed as backlog 39jkux;
* its lifted body can be RE-INLINED into a host with the full bare suite still green;
* three test files cited as its safety net (test_rununify_build_parser.py, its characterization twin, test_runner_refork_guard.py) are all gone;
* two SHIPPED COMMENTS in oc_runipd.py and agy_runipd.py still cite test_runner_refork_guard.py as a live requirement.

Plan t0ovw6 closes those two gaps for that ONE symbol. It is one sample. The deleted test_runner_refork_guard.py alone held a whole REFORK_TABLE of owned symbols, so the same question applies to every row of it.

THE WORK. Systematically diff what the deleted files ASSERTED against what survives: recover the deleted files from git (19313eed^), enumerate the properties each asserted, and for each determine whether a surviving test covers it. Produce a triage list, not necessarily a fix; each real gap becomes its own item. Prefer MUTATION as the test of coverage (the technique that found both gaps above), since a property can look covered by a test that reads its expected value from the same place the code reads it.

FILED chore AND medium: the outcome is unknown until measured, so no user-perceptible defect is claimed yet, but one sample of size one already yielded two live gaps and one shipped regression.
