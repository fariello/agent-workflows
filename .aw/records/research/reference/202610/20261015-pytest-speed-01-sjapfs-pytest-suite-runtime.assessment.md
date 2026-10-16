---
id: sjapfs
created: 20261015
set: pytest-speed
order: 01
topic: []
model: 
kind: assessment
status: reference
outcome: informational
summary: Pytest runtime and test selection on a 12-CPU host
consumed-by: []
---

## Measurement

On the 12-CPU host, `python3 -m pytest tests/ --collect-only -q -n 0 -p no:cacheprovider`
collected 8,552 default-selected tests in 511 modules and took 13.04 seconds. A
six-worker full default-selected run was still below completion after 150 seconds;
an earlier isolated clone reached 44 percent at that timeout. This was the
end-to-end cost that motivated a smaller routine gate.

After selecting representative behavioral modules through `testpaths`, the
unchanged `make test` command passed 700 tests in 24.34 seconds (`ELAPSED=24.91`)
using the existing six-worker xdist setting. After removing structure-only tests,
it passed 695 tests in 20.46 seconds (`ELAPSED=21.09`).
The final routine run, after documentation and collection-audit edits, passed
695 tests in 16.83 seconds (`ELAPSED=17.37`).

## Decision

Keep all remaining behavioral tests available through `make test-all`, which
explicitly collects `tests/` and clears the `slow` and `livecorpus` filter.
The routine gate uses a representative set of 19 test modules covering CLI,
records, plans, specs, search, sanitization, and runner behavior. Feature work
also runs its own focused test module when outside the routine set. The xdist
auto worker count is capped at six and half of available CPUs, including CI.

The complete release command collected every remaining test and reported
`13 failed, 8758 passed, 5 skipped, 18 xfailed` in 525.93 seconds. One failure
was a collection guard that still assumed bare pytest collected every module;
it now audits explicit release collection and passes (`2 passed in 5.17s`).
The other twelve failing node IDs all failed on the untouched starting commit:
the focused baseline rerun reported `12 failed in 15.83s` and its failure set
matched the modified release run exactly after excluding the fixed collection
guard. Thus no remaining release failure is introduced by this change.
