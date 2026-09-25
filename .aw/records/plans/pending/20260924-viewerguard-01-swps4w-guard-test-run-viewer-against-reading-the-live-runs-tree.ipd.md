# IPD: Guard test_run_viewer against reading the live runs tree

- Date: 2026-09-24
- Kind: child
- Concern: `.aw/records/runs/` is GITIGNORED, box-local driver output. A test in `tests/test_run_viewer.py` that reads it passes only on a machine that has run the driver and fails in a fresh clone, in CI, and in a lane worktree. Fourteen cases did exactly that until plan `xbwq8n` moved them onto the synthetic `_build_viewer_fixture`. Nothing stops the next test from bringing the dependency back, and the author can't see the failure because it passes on their own box. Backlog `rcmbnb` carries forward the regression guard (E-03 of retired plan `utwr6y`) that was never built.
- Scope: IN: one autouse fixture plus a process audit hook, both inside `tests/test_run_viewer.py`, that fail any test in the module which lists or opens a path under the checkout's live run roots; a permanent self-test proving the hook fires; a one-shot falsification probe (not committed). OUT: a suite-wide guard in the root `conftest.py` (Deferred); any change to `agent_workflows/run_viewer.py`.
- Scope-Paths: tests/test_run_viewer.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: rcmbnb
- Set: viewerguard
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: swps4w

## Workflow history

- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog rcmbnb; re-measured that the module does zero reads under a 264-entry live runs tree (audit-hook probe, `HITS 0`, `26 passed`), and prototyped an audit-hook guard that catches a live `iterdir` while leaving cwd and missing-path scans alone.

## Goal

Make any test in `tests/test_run_viewer.py` that reads the checkout's live run roots fail on the author's own machine, where the run tree exists. That is the only place the dependency can be seen before it ships. The guard itself must be provably falsifiable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: build the guard

- [ ] E-01 Add the live-runs read guard to `tests/test_run_viewer.py`, just below the imports.
  (a) Module constant `_REPO = Path(__file__).resolve().parents[1]`. Define `_LIVE_RUN_ROOTS` as a list of `os.path.realpath` strings for the three roots `run_viewer.discover_run_dirs` scans: `runner_shared.state_root(_REPO)` (the canonical `.aw/records/runs`, resolved through the project-context authority so a non-repository records backend is covered too), `_REPO / ".aw" / "runs"` and `_REPO / ".agents" / "runs"`. Wrap the `state_root` call in `try/except Exception` and fall back to `_REPO / ".aw" / "records" / "runs"`, so the guard can never break module import.
  (b) A module-level `_hook(event, args)` registered once with `sys.addaudithook`. It does nothing unless a module flag `_ARMED[0]` is true. When armed, for the events `open`, `os.scandir` and `os.listdir` it runs `os.path.realpath(os.fsdecode(args[0]))` inside `try/except` (non-path first args such as file descriptors are ignored). It records `(event, path)` whenever the path equals a guarded root or sits under one (`p == g or p.startswith(g + os.sep)`).
  (c) An `@pytest.fixture(autouse=True)` named `_forbid_live_runs_reads` that clears the module list `_HITS`, arms, yields, disarms, and then calls `pytest.fail(...)` if anything was recorded. The failure message names the event and path, says that `.aw/records/runs/` is gitignored and box-local, and points the author at `_build_viewer_fixture`. Add `import os, sys, pytest` as needed.
  (d) A short comment block in the style of the root `conftest.py` "Home isolation" block, stating: what it catches, and why (`rcmbnb`, `xbwq8n`); that audit hooks cannot be removed, which is why it is flag-gated; that `Path.is_dir`/`stat` emit no audit event, so existence probes are deliberately allowed and only real reads (listing or opening) fail; and its reach: this module only, and only reads done in-process.
  - Depends on: none
  - Expected outcome: the module still reports every existing test passing, and a test that lists or opens a path under any guarded root fails in teardown with the explanatory message.
  - Execution state: pending

- [ ] E-02 Add a permanent self-test class `LiveRunsGuardSelfTests` in the module. `test_guard_records_a_read_under_a_guarded_root` makes a `tempfile.TemporaryDirectory()` with a `runs/run-x` child and temporarily appends its realpath to `_LIVE_RUN_ROOTS` (restoring it in `finally`). It then calls `list(Path(td, "runs").iterdir())`, asserts `_HITS` holds exactly one `os.scandir` entry for that path, and clears `_HITS` before returning so the fixture does not fail the self-test. A second test, `test_guard_ignores_unguarded_and_existence_probes`, asserts `_HITS` stays empty after `list(Path(td).iterdir())` on an unguarded temp dir and after `Path(_LIVE_RUN_ROOTS[0]).is_dir()`. Together these keep the guard falsifiable on every run, including a fresh clone that has no live tree.
  - Depends on: E-01
  - Expected outcome: both self-tests pass, and deleting the `sys.addaudithook` registration makes the first one fail.
  - Execution state: pending

### Task group 2: prove it and run the suite

- [ ] E-03 FALSIFY AGAINST THE REAL LIVE TREE, without committing the probe. In a checkout that has a populated `.aw/records/runs/` (the maintainer checkout does: 264 entries at authoring), temporarily append to `tests/test_run_viewer.py`, outside every other class:

  ```python
  class _ProbeLiveRead(TestCase):
      def test_probe(self):
          run_viewer.discover_run_dirs(_REPO)
  ```

  Run `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -p no:randomly`, which must FAIL on `test_probe` with the guard message. Then delete the probe class and rerun, which must pass. A worktree with no live tree cannot show the failure, because `discover_run_dirs` never scans an absent root. That is expected, and it is why E-02 exists. In that case also create `_REPO/.aw/records/runs/run-probe/` for the probe run and remove it afterwards.
  - Depends on: E-02
  - Expected outcome: probe present gives exactly `1 failed` (or `1 error`) with the guard message; probe removed gives zero failures; `git status --short tests/test_run_viewer.py` shows only the E-01/E-02 diff.
  - Execution state: pending

- [ ] E-04 Run the bare suite `python3 -m pytest`, with no extra flags.
  - Depends on: E-03
  - Expected outcome: zero failures; the summary line is pasted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Root `conftest.py` (commit `e2fba20d`, "Home isolation") already sets the pattern: a module-level setup that cannot be opted out of, plus an `@pytest.fixture(autouse=True)` `_restore_home_sandbox` that re-establishes it around every test. This plan copies the shape (autouse fixture plus explanatory comment block) but scopes it to one module.
- `tests/test_run_viewer.py` is `unittest.TestCase`-based, and pytest autouse fixtures still apply to TestCase methods. The probe under `/tmp/opencode/g2/probe-viewerguard/t/test_g.py` confirmed this: `ERROR test_g.py::T::test_bad - Failed: read live runs tree`, `3 passed, 1 error`.
- The suite runs under xdist (`-n auto`), so each worker installs its own hook when it imports the module. There is no cross-process state.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- F-1: THE ITEM'S "NO LIVE READ TODAY" CLAIM HOLDS. I ran the module in the maintainer checkout (264 live run dirs) under an audit-hook plugin that records any `open`/`os.scandir`/`os.listdir` under `.aw/records/runs` during a test call: `HITS 0`, `26 passed` (pytest collects 26 items; the item's "75 passed" figure counted subtests or an older layout). `Path(".")` call sites remain in `test_run_viewer.py` (for example `run_viewer.load_run_summary(run_d, Path("."))` and `_run_viewer(Path("."), ["status"])`). They are harmless today, but they are exactly the shape the item warns about. A grep guard can't tell them apart from a real read. An audit hook sees what actually gets read, so it can.
- F-2: `run_viewer.discover_run_dirs` scans `state_root(repo_root)`, `repo_root / ".aw" / "runs"` and `repo_root / ".agents" / "runs"`, and each scan is guarded by `r.is_dir()`. `is_dir` emits no audit event, while `iterdir` emits `os.scandir` (probe output `[('os.scandir', 'r/runs')]`). So the guard fires on real listing only, and a missing-path `os.scandir`/`open` still records an event (probe: `[('os.scandir', 'nope/x'), ('open', 'nope/y')]`). The guard therefore also catches a read attempt against an absent live tree, as long as the attempt gets past the `is_dir` check.
- F-3: The ALTERNATIVE, an autouse `monkeypatch.chdir(tmp_path)`, was probed and rejected: `26 passed` with it in place. It hides a `Path(".")` read rather than flagging it, and it misses a test that passes an absolute `_REPO` root. It would keep the module green in a fresh clone, but it would never tell the author anything.
- F-4: DOES THE ROOT-CONFTEST SANDBOX FIT? Partly. Its env-restore mechanism doesn't apply, because the run root comes from the repo path and not from an env var. Its placement (root conftest, suite-wide) would reach every module, but other modules have not been audited for legitimate reads of the checkout's own records, so a suite-wide version risks false positives. The module-scoped version is what the item asks for. Widening it is Deferred.

## Proposed changes (ordered, validatable)

1. E-01: the audit hook and autouse fixture in `tests/test_run_viewer.py`.
2. E-02: self-tests that keep the guard falsifiable with no live tree.
3. E-03: a one-shot falsification against the real live tree.
4. E-04: the bare suite.

## Deferred / out of scope (with reason)

- Suite-wide live-runs guard in root `conftest.py`, next to `_restore_home_sandbox`. This needs an audit of every module for legitimate reads of the checkout's own `.aw/records/` first, and it is wider than `rcmbnb` asks for.
  - Carrier-Declined: the item explicitly scopes the guard to this module ("it protects this module, not every future test"). File a backlog item only if a second module turns out to have the same hazard.
- Reads made by a subprocess (for example a test that spawns `python3 -m agent_workflows runs`) are invisible to an in-process audit hook. The module does not spawn any today; it calls `cli.main` in-process through `_run_viewer`.
  - Carrier-Declined: no current call site; the E-01 comment block records the limit.

## Scope check

- Over-scope: none.
- Under-scope: none known. The guard covers every in-process listing or open of the three roots `run_viewer.discover_run_dirs` scans.

## Required tests / validation

E-02 adds the permanent self-tests. E-03 shows the guard failing on a real live-tree read and passing once the probe is removed. E-04 runs the bare suite. Evidence is listed per item in the validation section.

## Spec / documentation sync

N/A: test-only change. No spec describes the test module's isolation. The rationale lives in the E-01 comment block.

## Open questions

### OQ-01: Fail on a live-tree read, or only warn?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Fail. A warning is invisible under `-q` and on a green run, and the item's whole complaint is that this failure mode is invisible to the author. The self-tests in E-02 keep the guard from being noisy: they show it fires only on real reads under the guarded roots.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff tests/test_run_viewer.py` showing `sys.addaudithook`, `_LIVE_RUN_ROOTS` built from `runner_shared.state_root` plus the two legacy roots, and the `_forbid_live_runs_reads` autouse fixture with `pytest.fail`. Also paste the tail of `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q` showing zero failures.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -k LiveRunsGuardSelfTests` showing `2 passed`. Then temporarily comment out the `sys.addaudithook(...)` line, rerun, and paste output showing `test_guard_records_a_read_under_a_guarded_root` FAILED. Restore the line.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the run WITH `_ProbeLiveRead` present, showing `_ProbeLiveRead::test_probe` failed (or errored) with the guard message naming a path under `.aw/records/runs`. Then paste the run WITHOUT it, showing zero failures, and `git diff --stat tests/test_run_viewer.py` showing no probe class left behind.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (for example `N passed, M skipped`) with zero failed and zero errors.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after `- Status: approved`. Commit only `tests/test_run_viewer.py` through `aw commit swps4w -- tests/test_run_viewer.py`. Never commit the E-03 probe. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and V-01..V-04 carry pasted evidence.
