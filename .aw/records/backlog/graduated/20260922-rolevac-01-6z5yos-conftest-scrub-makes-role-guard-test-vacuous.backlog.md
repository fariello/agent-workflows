- Id: 6z5yos
- Status: graduated
- Graduated-To: rolevac
- Blocks-Release: next
- Set: rolevac
- Priority: high
- Work-Kind: bug
- Summary: The root conftest scrub makes the worker-role guard's own test vacuous: test_driver_own_process_is_not_worker_role can no longer fail for any ambient value

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to IPD 8i0xa7 (rolevac Order 01). This is the LIVE member of the three-item role-masking family, and the fix for the other two is what created it: the root conftest pops AW_EXECUTION_ROLE at import time, so test_driver_own_process_is_not_worker_role (which reads os.environ) can no longer fail for ANY ambient value. PROVED at HEAD 22cf67d9: running that single test with AW_EXECUTION_ROLE=worker set on its own command line gives '1 passed'. It passes while holding the exact value it exists to forbid. The plan requires the fix be at the SEAM, not the assertion: conftest's own comment and backlog 1uq1cu both name relaxing the assertion as the wrong fix, and the conftest's stated escape hatch ('a test that needs the marking must set it ITSELF') does not cover this test, because its subject IS the ambient value. Also carried: nothing asserts the scrub itself, so deleting that one line would silently restore 31 masked failures.
- 2026-09-22 created (aw backlog): Found while executing plan e4lkv5 in lane run-20260922T023434Z-2057475.

MEASURED 2026-09-22 at HEAD 2815aa56, from inside a managed worker lane.

WHAT IS WRONG. `conftest.py:78` runs `os.environ.pop("AW_EXECUTION_ROLE", None)` at import time, before collection. `tests/test_worker_role_refusal.py:343` then asserts `os.environ.get("AW_EXECUTION_ROLE") != "worker"` about that same AMBIENT environment. Because the pop always runs first, the assertion can no longer fail for ANY ambient value: it merely confirms the pop. Evidence: `AW_EXECUTION_ROLE=worker python3 -m pytest tests/test_worker_role_refusal.py -o addopts=""` gives `7 passed`, where before the scrub it gave `1 failed, 6 passed`.

WHY IT MATTERS. That test is the guard's OWN test. Its stated purpose is "The DRIVER's own environment must never be worker-marked, or driver_begin would refuse", i.e. it is meant to catch a driver process that is wrongly worker-marked. It can no longer catch that. A safety test that cannot fail is worse than no test, because it reports green.

PROVENANCE, and why this is not a complaint about the scrub. The scrub was added deliberately in `f1a6e94c` ("fix(tests): run the suite in the coordinator role, not as a worker lane", closing 1uq1cu and xqa4hw) and it does real good: it is what gives every lane a green bare-suite baseline. Its own comment block even claims "THE GUARD WAS NOT RELAXED ... tests/test_worker_role_refusal.py still passes 7/7", which is true but is exactly the problem: it passes 7/7 because the assertion became unfalsifiable, not because the property still holds.

ALSO MEASURED: the scrub MASKS the underlying test-side defect rather than fixing it. Re-asserting the marking after the scrub (a `pytest_configure` plugin) still reddens 31 tests at 2815aa56, with the same 10/9/8/2/1/1 six-file split 770fkp recorded. Plan e4lkv5 fixed 30 of those by making the tests declare their role, so they now pass with the marking present even if the scrub were removed; this item is the remaining 31st.

THE FIX, which is already designed elsewhere: approved plan 8b9ufm declares `tests/test_worker_role_refusal.py` and its F-18 is precisely this - assert against a CONSTRUCTED env mapping rather than `os.environ`. e4lkv5 deliberately did not touch the file (8b9ufm owns it and forbids it), which is why this is filed rather than fixed.

GATED because a safety guard that cannot fail is a live defect in shipped test coverage.
