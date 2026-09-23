- Id: xelvyi
- Status: open
- Blocks-Release: next
- Set: xelvyi
- Priority: low
- Work-Kind: bug
- Summary: The sole-blocking-caller guard was a text search a docstring could trip, so it went red against a correct tree

## Workflow history
- 2026-09-22 created (aw backlog): Found while adding runner_shared.integration_lock (plan vddpml E-03).

OBSERVED 2026-09-22. `tests/test_platform_lock.py::SingleOwnerTests::test_no_blocking_mode_leaked_to_a_second_caller` searched every line of `agent_workflows/*.py` for the substring `blocking=True`, skipping only lines whose strip() starts with `#`. A DOCSTRING is neither a comment nor a call, so the guard reported `runner_shared.integration_lock` as a second blocking caller purely because its docstring explains that `platform_lock` 'reserves `blocking=True` to one caller ... this function therefore does NOT use it'.

BOTH DIRECTIONS WERE WRONG. It was RED against a tree that honors the rule exactly (a false positive that would have pressured the author into deleting a correct explanation), and it remained defeatable in the other direction by rewording the code so the literal does not appear. This repository already records the same failure mode in commit `94b00d37` (a shipped guard passing solely because its literal appeared in an explanatory comment above code that had been rewritten) and `tests/test_run_flag_surface.py`'s module docstring records deleting sixteen source-text pins for the same reason.

FIXED IN PLACE for this one guard by converting it to an `ast.walk` looking for a real `ast.keyword` (committed with plan `vddpml`, and justified as an out-of-scope edit there). `tests/test_platform_lock.py` is outside that plan's Scope-Paths, so the edit is recorded rather than hidden.

WHAT REMAINS, and why this item exists rather than being closed by that fix: the same pattern is likely present in other guards. A sweep for `assertNotIn("<literal>", source)` / `assertIn("<literal>", source)` over module source across `tests/` would find them; each hit should be judged as (a) convert to AST, (b) convert to a behavioral assertion driving the function and observing a sentinel, or (c) legitimately textual (e.g. asserting user-facing PROSE, where the text IS the subject). Known already-converted examples to follow: `tests/test_runner_telemetry_integration.py` and `tests/test_run_analytics_telemetry.py` both adopted the AST remedy and state the reasoning.
