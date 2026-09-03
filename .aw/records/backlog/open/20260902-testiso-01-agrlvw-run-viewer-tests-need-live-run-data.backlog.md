- Id: agrlvw
- Status: open
- Blocks-Release: next
- Set: testiso
- Priority: high
- Work-Kind: bug
- Summary: 15 tests in tests/test_run_viewer.py depend on gitignored live run data under .aw/records/runs/, so they pass only on a machine that has run the driver and fail in every fresh clone and in CI

## Workflow history
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

FOUND 2026-09-02 while deciding whether the crashed runs lane work (97df1z) was safe to merge. The
lane looked like it broke 15 tests. It did not. Chasing that produced a real, separate defect.

THE SYMPTOM. A bare `python3 -m pytest` in a FRESH CLONE reports:

    15 failed, 4028 passed, 3 skipped, 4 xfailed
    FAILED tests/test_run_viewer.py::RunViewerTests::test_aw_cli_entry_points
    FAILED tests/test_run_viewer.py::RunViewerTests::test_discover_run_dirs
    FAILED tests/test_run_viewer.py::RunViewerTests::test_format_run_human
    FAILED tests/test_run_viewer.py::RunViewerTests::test_load_run_summary_state_json
    FAILED tests/test_run_viewer.py::RunViewerTests::test_multi_run_cli_json_summary
    FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_latest_only
    FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_latest_only_single_run
    FAILED tests/test_run_viewer.py::RunViewerTests::test_run_viewer_cli_short
    ... (15 total, all in this one file)

THE FAILURE MESSAGE NAMES THE CAUSE:

    >   self.assertIn("run-", buf.getvalue())
    E   AssertionError: run- not found in no matching runs found\\n

The test invokes the real CLI (`cli.main(["runs", "--last", "--no-color"])`) and asserts the output
mentions a run. In a tree with no run directories the CLI is CORRECT to say "no matching runs found",
so the test fails on a correct program.

THE ROOT CAUSE, measured. These tests read the LIVE `.aw/records/runs/` tree instead of a fixture, and
that directory is GITIGNORED (it is box-local driver state: per-run queue, session logs, prompts,
outcomes, locks; see the `.aw/.gitignore` entry for `records/runs/`). So the tests depend on data that
by design never arrives with the repository:

    primary checkout (has run the driver):  89 run dirs  -> 36 passed
    fresh clone (never run the driver):      0 run dirs  -> 15 failed, 21 passed

VERIFIED NOT CAUSED BY THE LANE, three ways, because that was the original question:
1. The same 15 fail on plain `main` in a fresh clone with the lane NOT merged.
2. All 36 pass in the primary checkout, both before and after merging the lane
   (post-merge full suite: 4052 passed, 3 skipped, 4 xfailed, zero failures).
3. `git show 209227d5 --stat` confirms the lane never touches `tests/test_run_viewer.py`.

THIS IS NOT THE `dh0uno` WORKTREE PHANTOM, and conflating them would send a reader down the wrong path.
The standing note in the maintainers checklist says "a detached worktree fails about 15
`test_run_viewer.py` tests that PASS in the primary tree", which describes the same FILE and a similar
COUNT, so the two are easy to mistake for one another. They are different: `dh0uno` is about an inner
`aw` resolving state against a lane worktree, while this reproduces in a PLAIN CLONE with no worktree
involved at all. The shared symptom is that both are invisible in the one tree where developers
actually run the suite.

WHY HIGH. Three compounding costs:
1. CI CANNOT TRUST THE SUITE. Any clean checkout (CI runner, new contributor, release verification)
   sees 15 failures on a healthy tree, which is exactly the "gate that false-positives on correct
   behavior TRAINS agents to bypass it" failure mode already recorded in backlog `gjadwm`.
2. IT NEARLY GOT GOOD WORK DISCARDED. The 15 failures appeared while validating a merge and looked like
   the merges fault. It took three separate experiments to establish they were not.
3. IT HIDES REAL BREAKAGE. With 15 known-failing tests in the file, a 16th real failure would be
   invisible in the noise.

WHAT TO FIX, not prescribed. The tests need to own their data instead of borrowing the machines:
- Point them at a TEMPORARY run tree (tmp_path with a couple of synthetic run dirs) rather than the
  repos live `.aw/records/runs/`. The file already builds fixtures for some cases, so the pattern
  exists; the 15 failures are the cases that skipped it.
- If any case genuinely needs a real corpus, mark it so it SKIPS (not fails) when no run data is
  present, and say why in the skip reason. A skip is honest; a failure on a healthy tree is not.
- Add a guard so this cannot regress: a test that asserts the suite does not read
  `.aw/records/runs/`, or CI that runs the suite in a fresh clone (which is what would have caught this
  the day it landed).

ADJACENT, worth checking in the same pass: whether any other test reads gitignored box-local state
(`.aw/records/history.jsonl`, `.aw/worktrees/`, `.aw/state/runtime/`). The same defect class would
produce the same fresh-clone-only failures elsewhere.
