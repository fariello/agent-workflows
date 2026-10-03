- Id: gte0pd
- Status: open
- Set: gte0pd
- Priority: medium
- Work-Kind: chore
- Summary: tools/ipdrunner/ is outside testpaths, so its tests rot unnoticed (10 failures live there today)

## Workflow history
- 2026-09-30 created (aw backlog): tools/ipdrunner/ is outside testpaths, so its tests rot unnoticed (10 failures live there today)

Found while authoring plan h0zk2g (backlog s4jctz), measured at HEAD 27a80985.

WHAT IS WRONG. `pyproject.toml` sets `testpaths = ["tests"]`, and both `Makefile` targets (`test` and `test-all`) invoke `python3 -m pytest tests/` explicitly, so `tools/ipdrunner/test_runagy.py` is collected by NO standard invocation. Grepping `.github/workflows/*.yml` for `ipdrunner` or `test_runagy` returns nothing, so CI does not reach it either.

MEASURED CONSEQUENCE. Running it directly (`python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts=""`) gives `11 failed, 14 passed`. One of those failures is how backlog s4jctz was found: `AgyParserAndDiscoveryTests::test_read_deps_and_set` asserts `driver._read_id(text)` (a genuine live consumer of `agy_runipd._read_id` via the `runagy.py` shim's `vars()` copy loop) but dies one line later on `driver._read_status(text)` with `AttributeError: module 'runagy' has no attribute '_read_status'`, because `_read_status` is on NEITHER host. So the file holds the only in-tree evidence for a re-export that nothing else pins, and that evidence has been red and invisible.

THE DECISION THIS NEEDS FROM A HUMAN. Adding `tools/ipdrunner/` to `testpaths` would immediately turn 10 further pre-existing failures red in every developer run and in CI. That is a change to a SHARED gate, so the options are a judgement call: (a) add the path and fix all 11; (b) fix them first, then add the path; (c) decide the shim tests are obsolete and delete the file, accepting that the two shims then have no coverage; (d) leave it uncollected and accept the rot. Plan h0zk2g deliberately does NOT decide this (it is a low/chore plan) and mitigates only the narrow risk, by pinning its own `_read_id` guarantee inside `tests/` where collection is guaranteed.

FILED chore AND medium: nothing user-visible is broken, but an uncollected test directory is a silent coverage hole that already let one guarantee lapse.
