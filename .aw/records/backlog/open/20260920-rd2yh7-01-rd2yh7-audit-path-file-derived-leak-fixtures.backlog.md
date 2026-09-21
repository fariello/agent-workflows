- Id: rd2yh7
- Status: open
- Set: rd2yh7
- Priority: low
- Work-Kind: chore
- Summary: Audit tests that derive leak-detector fixture input from Path(__file__) so no other test asserts a property of its own checkout location

## Workflow history
- 2026-09-20 created (aw backlog): Deferred from plan zx9dkq (its second Deferred/out-of-scope row); filed so the obligation survives that plan reaching executed.

DEFERRED BY plan `zx9dkq`, whose "Deferred / out of scope" section reads: "AUDITING EVERY TEST THAT DERIVES A FIXTURE FROM `Path(__file__)`. Plausibly the same shape exists elsewhere, but a repo-wide sweep is its own plan with its own measurement."

WHY IT IS WORTH DOING. `zx9dkq` fixed one instance of a general shape: a test that interpolates the LIVE CHECKOUT PATH into a value it then asserts a leak rule matches. That test passed in the maintainer home tree and failed in a hand-made worktree elsewhere, and it cost a false alarm mid-merge (a baseline run showed two failures that did not occur on `main`, which had to be ruled out as a merge regression first). Any other test with the same shape carries the same trap.

WHAT `zx9dkq` ALREADY CHECKED, so the sweep does not start from zero: during its E-01 it recorded "none encountered" for tests that plant a `Path(__file__)`-derived value as leak-detector INPUT. `Path(__file__)` is used widely and legitimately (reading source text, locating `pyproject.toml`; e.g. `tests/test_run_analytics_spa.py:2723` and `:2745`), and those uses are NOT this defect. So the sweep is looking specifically for: a checkout-derived path that is passed to `leak_sanitizer.scan_text` (or any detector) and asserted to match or not match.

SUGGESTED METHOD, cheap and decisive: grep for `Path(__file__)` and `build_ruleset`/`scan_text` co-occurring in one test class, then run the suite from a checkout OUTSIDE the home tree (a temp-directory copy of the tracked files is sufficient, which is how `zx9dkq` measured) and compare failures against the same-tree baseline. That is a MEASUREMENT, not a read-through, which is the point of filing it separately rather than asserting it is clean.

THE FIX PATTERN IS ESTABLISHED by `zx9dkq`: plant a FIXED synthetic literal, never a `Path.home()`-derived or checkout-derived value, and note that the account name must not be one of the placeholders the `home-path` rule deliberately allows (`u`, `alice`, `user`, `USER`, `<...>`) or the plant yields zero findings and the test passes vacuously. Spell the literal as a concatenation so the source file stays clean under the repository leak gate.
