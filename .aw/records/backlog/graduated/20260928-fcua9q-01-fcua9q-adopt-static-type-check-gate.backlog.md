- Id: fcua9q
- Status: graduated
- Graduated-To: fcua9q
- Set: fcua9q
- Priority: low
- Work-Kind: chore
- Summary: No static type checker in the toolchain, so annotation defects like g321ny fail open

## Workflow history
- 2026-09-30 set (aw backlog): graduated by run run-20260930T053053Z-3200037: m7fllj
- 2026-09-28 created (aw backlog): Filed as the named carrier for plan yifr0h's deferred toolchain decision (backlog g321ny).

Plan `yifr0h` (from backlog `g321ny`) fixed a wrong `Callable[[Any, Path], Any]` annotation on `lane_containment.bound_expiry_reaper`, whose `reap` parameter promised two positional parameters while the body calls `reaper(process, run_dir=run_dir)`. NOTHING IN THE TOOLCHAIN WOULD HAVE CAUGHT IT and nothing will catch the next one.

MEASURED at HEAD 258a1894: `pyproject.toml` declares one runtime dep (`filelock>=3`) and test extras of pytest/xdist/randomly/PyYAML; `.pre-commit-config.yaml` runs only `ruff` and `ruff-format`; `.github/workflows/tests.yml` has no type-check step. So a type error can sit in shipped code indefinitely, which is how g321ny's two errors were found by hand rather than by a gate.

WHY THIS IS NOT A ONE-LINE FIX, and why yifr0h deliberately did not do it. Adopting a checker means choosing a baseline-suppression regime first: `python3 -m mypy agent_workflows/runner_shared.py --ignore-missing-imports` reports 103 errors in that one file (mypy 2.3.1). None has been read, so it is unknown how many are real defects versus `Any`-narrowing and `Optional`-callable noise. A gate turned on without a baseline would fail every commit.

FILED AS `chore`, NOT `bug`, under the perceptibility test: no user waits on this and no user-visible output is wrong. It is a missing guard, not a defect.

DECISIONS RESERVED FOR THE MAINTAINER: which checker (mypy vs pyright/basedpyright), strictness, whether it gates pre-commit or only CI, and whether the 103 existing errors are baselined-and-suppressed or read and triaged. Risk appetite and toolchain are explicitly maintainer calls.
