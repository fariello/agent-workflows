# IPD: run_checks.py npm-script execution on Windows

- Date: 2026-07-08
- Concern: cross-platform correctness (tooling)
- Scope: `run_checks.py`'s execution of npm/package.json checks on Windows only. NOT the
  CLI/distribution (IPD-2), which is verified green cross-OS.
- Status: EXECUTED 2026-07-09
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Make `run_checks.py` run detected npm `scripts` correctly on Windows so the two
node-runner end-to-end self-tests pass there, instead of being skipped.

## Context (how this surfaced)

IPD-2 Batch F added a Windows CI matrix. It revealed that
`tests.test_run_checks.RunChecksEndToEndTests.test_passing_check_exit_zero` and
`test_failing_check_exit_one` fail on Windows: a passing npm `test` script reports
`all_ran_passed: False` and a failing one exits 0 instead of 1. The tests are currently
SKIPPED on Windows (`@unittest.skipIf(os.name == "nt", ...)`) with that reason recorded,
so the suite is green on all OSes. This IPD tracks the real fix.

This is a PRE-EXISTING `run_checks.py` gap (the tool predates IPD-2 and was never
Windows-verified), surfaced by the new CI matrix - not a regression from IPD-2.

## Likely cause (to confirm)

`run_checks.py` runs the package-manager check via a subprocess. On Windows the npm
executable is `npm.cmd` (not `npm`), and `subprocess.run([...], shell=False)` will not
find/execute a `.cmd` the same way, and/or exit codes are not propagated as expected.
Candidates to inspect: how the check command is built and invoked (shell vs list form,
`shutil.which("npm")` resolution, `.cmd`/`.bat` handling, and returncode capture).

## Proposed approach (draft; refine during execution)

1. Reproduce on a Windows runner (or Windows VM); capture the actual command and exit
   code `run_checks.py` produces for a trivial passing and failing npm script.
2. Fix the invocation so it is Windows-correct:
   * Resolve the command executable path using `shutil.which`.
   * On Windows (`os.name == "nt"`), if the resolved executable ends with a batch/command script extension (such as `.cmd` or `.bat`), prepend `["cmd.exe", "/c"]` to the command list while keeping `shell=False`.
   * This ensures safe, parameter-safe execution without command injection or shell escaping vulnerabilities associated with `shell=True`.
   * Ensure POSIX behavior is completely unchanged.
3. Remove the `skipIf(os.name == "nt")` guard on `RunChecksEndToEndTests` so both tests
   run and pass on Windows.
4. Keep zero runtime dependencies; add a DECISIONS entry if the invocation contract
   changes.

## Required tests / validation

- The two `RunChecksEndToEndTests` pass on the Windows CI matrix with the skip guard
  removed; still green on Linux/macOS.
- Run the full test suite on Linux/macOS to guarantee zero regressions.
- Full suite green on all three OSes.

## Open questions (Resolved)

1. Is there a Windows runner available to iterate against, or is this fixed blind and
   verified via CI on push? (CI-verified is acceptable but slower.)
   * *Resolution*: Confirmed that no Windows runner is available on this system; changes must be verified via the Windows CI matrix on push.

## Approval and execution gate

Approved by user and executed. Remote validation is triggered via the GitHub Actions Windows CI runner on push.

## Execution record (2026-07-09)

Executed successfully:
- Imported `os` and `shutil` in `.agents/workflows/verify/tools/run_checks.py`.
- Updated `run_check` to resolve target executable path via `shutil.which`. If running on Windows (`os.name == "nt"`) and the resolved executable is a batch file (`.cmd`/`.bat`), it prepends `["cmd.exe", "/c"]` to execute it safely with `shell=False`.
- Removed the class-level `skipIf(os.name == "nt", ...)` decorator from `RunChecksEndToEndTests` in `tests/test_run_checks.py` to enable E2E check validation on Windows.
- Verified that all 128 tests are green on local POSIX/Linux environment.
- Pushed changes to main branch to trigger Windows CI execution.
