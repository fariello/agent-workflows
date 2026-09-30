- Id: ikxtkj
- Status: graduated
- Graduated-To: ikxtkj
- Set: ikxtkj
- Priority: medium
- Work-Kind: chore
- Summary: Four published docs cite five test files the 2026-09-24 suite trim deleted, so each names a guard that no longer exists and a reader cannot verify the claim

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053024Z-3198670: 1jg2m2
- 2026-09-28 created (aw backlog): Found while graduating backlog bar5t8 (the FORCE_COLOR section 1.1 row 2 wording defect).

MEASURED 2026-09-28 at HEAD c763a2fa by extracting every `tests/test_*.py` citation from `docs/*.md` and testing each for existence. Five citations resolve to no file, all five deleted by commit 19313eed ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24):

    docs/cli-output-contract.md:91    tests/test_flag_surface_uniformity.py
    docs/recovery.md:56               tests/test_release_readiness.py
    docs/security.md:6                tests/test_security_hardening.py
    docs/wtiso-state-taxonomy.md:11   tests/test_wtiso_taxonomy_freeze.py
    docs/wtiso-state-taxonomy.md:105  tests/test_wtiso_characterization.py

WHY THIS IS A DEFECT AND NOT UNTIDINESS. Each citation is load-bearing prose: the doc states a property and names the test that enforces it, which is what lets a reader verify the claim rather than trust it. docs/cli-output-contract.md:91 is the sharpest case, reading "tests/test_flag_surface_uniformity.py enforces both halves" and then describing that file's two named skip lists (EXEMPT_SUBCOMMANDS, FORWARDED_SUBCOMMANDS) in detail; neither symbol exists anywhere in the tree now. A reader following it finds nothing, and cannot tell whether the enforcement moved or was dropped.

WHY THIS IS A CHORE RATHER THAN A BUG, stated so a reviewer can dispute the judgement: the underlying BEHAVIOR is intact. The flag-uniformity property docs/cli-output-contract.md section 1.2 describes still measures exactly as written (re-measured 2026-09-28 by walking cli._build_parser(): 249 leaf parser nodes, 29 missing either color flag, and all 29 are the documented verbatim-forwarding driver leaves plus the hidden __complete). So a script author acting on the doc gets correct behavior; only the verification route is broken. That is not user-perceptible impact under the repository's own test, so it does not gate a release.

FIX SHAPE, per citation, since they are not one decision. For each: (a) if an equivalent guard survives under another name, re-point the citation to it; (b) if the property is now unguarded, either re-point to the nearest real coverage and say plainly that it is partial, or drop the citation and keep the claim; (c) never leave a name that resolves to nothing. docs/cli-output-contract.md:55's citation of the same deleted file is EXCLUDED from this item: it sits inside the sentence plan mj18mi (backlog bar5t8) rewrites, and is fixed there.

A DURABLE GUARD IS WORTH CONSIDERING but is a separate judgement this item does not prejudge: a test asserting every tests/test_*.py path cited in docs/ exists would stop the next deletion silently orphaning a citation. It would be a repository-CONTENT check (docs prose against the filesystem), not a production-source-text pin, so the 2026-09-26 no-source-pin ruling does not exclude it.
