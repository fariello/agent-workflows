- Id: ci9kx2
- Status: open
- Blocks-Release: next
- Set: ci9kx2
- Priority: medium
- Work-Kind: bug
- Summary: aw attention --dir <non-AW-directory> prints nothing and exits 0, so an explicitly named wrong directory looks like success

## Workflow history
- 2026-09-20 created (aw backlog): aw attention --dir <non-AW-directory> prints nothing and exits 0, so an explicitly named wrong directory looks like success

MEASURED at HEAD 283b3c92 while executing IPD quqyc4 (its finding F-17), and CHARACTERIZED rather than fixed there by design.

REPRODUCTION: from an unrelated directory, `aw attention --dir /tmp/<a-git-repo-with-no-AW-layout>` prints NOTHING on either stream and exits 0. `aw ipd board --dir <same>` behaves the same way.

CAUSE: both no-project message branches are guarded by `not explicit_dir` (`attention.py`, and the `_run_plans` twin in `cli.py`), so passing --dir SKIPS the guidance entirely. The operator who was MOST explicit about where to look gets the least information, and a success exit code on top.

WHY IT IS A BUG AND NOT A NICETY: exit 0 asserts 'clean, nothing needs attention', which is a false claim about a directory the tool never surveyed. It is arguably worse than the no---dir case quqyc4 fixed, because a wrapper or CI step reading $? concludes the board is clean.

WHY quqyc4 DID NOT FIX IT: changing that guard changes WHICH INPUTS produce a cannot-run, i.e. it changes a published exit-code contract (docs/cli-output-contract.md section 3) for a flag that other callers may rely on. That deserves its own scope decision. quqyc4 PINNED today's behavior as a characterization test (tests/test_awretrofit_project_root_climb.py::NoProjectMatrixEndToEndTests::test_case_d2_explicit_dir_at_a_non_project_is_silent_and_exits_zero) so a later fix has a baseline; that test is written to be UPDATED deliberately, not to be protected.

LIKELY FIX: when --dir is given and `is_project_dir` is false, emit the same guidance (naming the DIRECTORY GIVEN, which no_project_message now accepts as a parameter) and exit 3. The --dir 'honored verbatim, no climb' rule is about RESOLUTION and need not imply silence.
