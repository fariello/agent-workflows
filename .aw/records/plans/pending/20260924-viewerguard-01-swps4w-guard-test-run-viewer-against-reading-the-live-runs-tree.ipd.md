# IPD: Guard test_run_viewer against reading the live runs tree

- Date: 2026-09-24
- Kind: child
- Concern: `.aw/records/runs/` is GITIGNORED, box-local driver output. A test in `tests/test_run_viewer.py` that reads it passes only on a machine that has run the driver and fails in a fresh clone, in CI, and in a lane worktree. Fourteen cases did exactly that until plan `xbwq8n` moved them onto the synthetic `_build_viewer_fixture`. Nothing stops the next test from bringing the dependency back, and the author can't see the failure because it passes on their own box. Backlog `rcmbnb` carries forward the regression guard (E-03 of retired plan `utwr6y`) that was never built.
- Scope: IN: one autouse fixture plus a process audit hook, both inside `tests/test_run_viewer.py`, that fail any test in the module which lists or opens a path under the checkout's live run roots; permanent self-tests proving BOTH that the hook records and that the fixture actually FAILS (the latter via a subprocess, because an in-process test cannot assert its own fixture failed); a one-shot falsification probe against the real live tree (not committed). OUT: a suite-wide guard in the root `conftest.py` (Deferred); any change to `agent_workflows/run_viewer.py`.
- Scope-Paths: tests/test_run_viewer.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: rcmbnb
- Set: viewerguard
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: swps4w
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (aw set): plan-review complete: PR-601..PR-606 all fixed; added E-03 (subprocess self-test proving the fixture actually fails, measured falsifiable) and E-05 (xdist plus random-order stability); recorded the guard's honest reach (inert with no live tree); 6 items, 6:6 E/V bijection; findings and 4 decisions in .aw/records/reviews/20260924-viewerguard-01-swps4w-...review.md

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-601..PR-606, all FIXED. Reproduced every author claim (`HITS 0`, `26 passed` under a synthesized live tree; `is_dir`/`exists`/`stat` emit no audit event while `iterdir` emits `os.scandir`; `os.fsdecode(int)` raises so the `try/except` is load-bearing). The dominant finding: the E-02 self-tests CLEAR `_HITS` before returning, so they never exercise the fixture's `pytest.fail` - measured by gutting `pytest.fail` and watching both self-tests stay GREEN, leaving the guard's only real proof in the uncommitted E-03 probe. Added E-03 (a subprocess self-test that asserts a nonzero exit and the guard message, verified falsifiable). Also recorded the guard's HONEST REACH as a measured limit rather than an aside: with the live tree ABSENT a genuine `discover_run_dirs(_REPO)` call passes silently, so the guard is inert in CI and in a lane worktree and works only on a box that has run the driver - which is the author's box, and is exactly where the plan's Goal aims it.
- 2026-09-24 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog rcmbnb; re-measured that the module does zero reads under a 264-entry live runs tree (audit-hook probe, `HITS 0`, `26 passed`), and prototyped an audit-hook guard that catches a live `iterdir` while leaving cwd and missing-path scans alone.

## Goal

Make any test in `tests/test_run_viewer.py` that reads the checkout's live run roots fail on the author's own machine, where the run tree exists. That is the only place the dependency can be seen before it ships. The guard itself must be provably falsifiable.

HONEST REACH, stated here because it bounds what this plan delivers and was measured at review (F-5). The guard fires only when a read actually reaches the filesystem, and `run_viewer.discover_run_dirs` gates every scan behind `r.is_dir()`, which emits no audit event. So on a machine with NO live runs tree - a fresh clone, CI, or a lane worktree - a genuine `discover_run_dirs(_REPO)` call is a silent no-op and the guard correctly reports nothing. That is not a defect to fix: it is the same condition that makes the underlying bug harmless there. The consequence to be clear-eyed about is that this guard does NOT make CI catch the regression; it makes the AUTHOR catch it, on the one box where the bug is both reproducible and invisible. E-02 and E-03 exist so the guard is still proven to work where it cannot fire.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: build the guard

- [x] E-01 Add the live-runs read guard to `tests/test_run_viewer.py`, just below the imports.
  (a) Module constant `_REPO = Path(__file__).resolve().parents[1]`. Define `_LIVE_RUN_ROOTS` as a list of `os.path.realpath` strings for the three roots `run_viewer.discover_run_dirs` scans: `runner_shared.state_root(_REPO)` (the canonical `.aw/records/runs`, resolved through the project-context authority so a non-repository records backend is covered too), `_REPO / ".aw" / "runs"` and `_REPO / ".agents" / "runs"`. Wrap the `state_root` call in `try/except Exception` and fall back to `_REPO / ".aw" / "records" / "runs"`, so the guard can never break module import.
  (b) A module-level `_hook(event, args)` registered once with `sys.addaudithook`. It does nothing unless a module flag `_ARMED[0]` is true. When armed, for the events `open`, `os.scandir` and `os.listdir` it runs `os.path.realpath(os.fsdecode(args[0]))` inside `try/except` (non-path first args such as file descriptors are ignored). The `try/except` is LOAD-BEARING, not defensive decoration: measured at review, `os.fsdecode(3)` raises `TypeError`, and an fd-based `open(fd, 'w')` does reach the hook with an int first arg, so without the guard a legitimate fd write would raise from inside the hook. It records `(event, path)` whenever the path equals a guarded root or sits under one (`p == g or p.startswith(g + os.sep)`). Re-entrancy is bounded: `os.path.realpath` inside the hook does not itself emit a guarded event (measured max re-entry depth 1).
  (c) An `@pytest.fixture(autouse=True)` named `_forbid_live_runs_reads` that clears the module list `_HITS`, arms, yields, disarms, and then calls `pytest.fail(...)` if anything was recorded. CLEAR `_HITS` BEFORE CALLING `pytest.fail`, not after, or the recorded hit leaks into the next test in the same worker and fails it too, reporting the wrong test as the offender. The failure message names the event and path, says that `.aw/records/runs/` is gitignored and box-local, and points the author at `_build_viewer_fixture`. Add `import os`, `import sys` and `import pytest` - measured at review, the module currently imports NONE of the three (it has `argparse`, `io`, `json`, `tempfile`, `contextlib`, `datetime`, `pathlib`, `typing`, `unittest`), so all three are new; `pytest` is already an established import in sibling test modules (`tests/test_cli.py`, `tests/test_installer.py` and others), so it introduces no new dependency.
  (d) A short comment block in the style of the root `conftest.py` "Home isolation" block, stating: what it catches, and why (`rcmbnb`, `xbwq8n`); that audit hooks cannot be removed, which is why it is flag-gated; that `Path.is_dir`/`exists`/`stat` emit no audit event (verified at review: all three record nothing, while `iterdir` emits `os.scandir` and a MISSING-path `open`/`iterdir` still emits its event), so existence probes are deliberately allowed and only real reads fail; and its reach - this module only, only in-process reads, and ONLY on a box where the live tree exists, since an absent root is never scanned past `is_dir` (F-5). State that last limit explicitly in the comment: a future reader who assumes CI enforces this guard would be wrong.
  - Depends on: none
  - Expected outcome: the module still reports every existing test passing, and a test that lists or opens a path under any guarded root fails in teardown with the explanatory message.
  - Execution state: performed

- [x] E-02 Add a permanent self-test class `LiveRunsGuardSelfTests` in the module, covering what the HOOK records. `test_guard_records_a_read_under_a_guarded_root` makes a `tempfile.TemporaryDirectory()` with a `runs/run-x` child and temporarily appends its realpath to `_LIVE_RUN_ROOTS` (restoring it in `finally`). It then calls `list(Path(td, "runs").iterdir())`, asserts `_HITS` holds exactly one `os.scandir` entry for that path, and clears `_HITS` before returning so the fixture does not fail the self-test. A second test, `test_guard_ignores_unguarded_and_existence_probes`, asserts `_HITS` stays empty after `list(Path(td).iterdir())` on an unguarded temp dir and after `Path(_LIVE_RUN_ROOTS[0]).is_dir()`. NOTE WHAT THESE DO NOT PROVE, and do not let the item's own clearing of `_HITS` read as sufficient: because they clear `_HITS`, the autouse fixture never fails, so the `pytest.fail` branch - the entire enforcement mechanism - is NOT exercised. Measured at review by replacing the `pytest.fail(...)` call with `pass`: both of these self-tests still PASSED. E-03 is what closes that hole; do not merge E-03 into this item, because its mechanism (a subprocess) is unrelated to these two in-process assertions. Also make the second test robust when `_LIVE_RUN_ROOTS[0]` does not exist (the fresh-clone case): `Path(absent).is_dir()` is `False` and emits no event, so the assertion holds, but state that this is deliberate rather than accidental so a later reader does not "strengthen" it into requiring the path to exist.
  - Depends on: E-01
  - Expected outcome: both self-tests pass, and deleting the `sys.addaudithook` registration makes the first one fail.
  - Execution state: performed

- [x] E-03 Add the permanent self-test that the FIXTURE ACTUALLY FAILS, which is the one assertion E-02 structurally cannot make: a test cannot assert that its own teardown fixture failed it. Add `test_fixture_fails_a_test_that_reads_a_guarded_root` to `LiveRunsGuardSelfTests`, which writes a tiny throwaway test module into a `tempfile.TemporaryDirectory()` containing a COPY of the hook plus autouse fixture (guarding one fake root passed via an env var) and one test that lists that root, then runs it with `subprocess.run([sys.executable, "-m", "pytest", <mod>, "-o", "addopts=", "-q", "-p", "no:randomly"], capture_output=True, text=True, cwd=td)` and asserts a NONZERO returncode and the guard message substring in stdout. Prototyped at review: it passes as written, and when the inner `pytest.fail(...)` is replaced with `pass` it FAILS (`AssertionError`, inner run reported `1 passed`), so it is genuinely falsifiable. Use `-o addopts=` so the parent suite's `-n auto` does not nest, and `cwd=td` so the inner run cannot pick up this repository's `conftest.py`. It needs NO live tree, so unlike E-04 it protects the guard in CI and in a lane worktree too.
  - Depends on: E-02
  - Expected outcome: the subprocess self-test passes; replacing the copied `pytest.fail` with `pass` makes it fail.
  - Execution state: performed

### Task group 2: prove it and run the suite

- [x] E-04 FALSIFY AGAINST THE REAL LIVE TREE, without committing the probe. In a checkout that has a populated `.aw/records/runs/` (the maintainer checkout does: 264 entries at authoring), temporarily append to `tests/test_run_viewer.py`, outside every other class:

  ```python
  class _ProbeLiveRead(TestCase):
      def test_probe(self):
          run_viewer.discover_run_dirs(_REPO)
  ```

  Run `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -p no:randomly`, which must FAIL on `test_probe` with the guard message. Then delete the probe class and rerun, which must pass. A worktree with no live tree cannot show the failure, because `discover_run_dirs` never scans an absent root - CONFIRMED at review: with the tree moved aside, the same probe passed silently and the hook recorded nothing. That is expected, and it is why E-02 and E-03 exist. IF THIS EXECUTES IN A LANE WORKTREE OR ANY CHECKOUT WITH NO LIVE TREE, synthesize one first: create `_REPO/.aw/records/runs/run-probe/` with a `state.json`, run the probe, then remove the directory you created and confirm with `git status --short` that nothing remains (the path is gitignored by `.aw/.gitignore`'s `records/runs/`, verified at review, so it will not appear as untracked - check the filesystem, not only git).
  - Depends on: E-03
  - Expected outcome: probe present gives exactly `1 failed` (or `1 error`) with the guard message naming a path under the runs root; probe removed gives zero failures; `git status --short tests/test_run_viewer.py` shows only the E-01..E-03 diff and no synthesized run directory remains on disk.
  - Execution state: performed

- [x] E-05 Confirm the guard does not change the module's cost or its result under the REAL suite conditions, which are xdist plus random ordering and are not what E-02's targeted runs exercise. Run `python3 -m pytest tests/test_run_viewer.py` (bare, so the configured `-n auto --dist=worksteal` and `pytest-randomly` both apply) three times and confirm the same pass count each time with no ordering-dependent failure. Rationale, measured at review: the hook is installed process-wide and fires on every `open`/`os.scandir`/`os.listdir` in the worker, and `_HITS`/`_ARMED` are module-level mutable state shared by every test in the worker; the prototype was stable across xdist and five random seeds, but the plan should demonstrate that on the real module rather than inherit the prototype's result. Review also measured the overhead as negligible (a disarmed hook cost 1.00x on a 3,000-file write-and-read loop, 320.5ms against 319.6ms), so a large slowdown would indicate a mistake rather than an inherent cost.
  - Depends on: E-04
  - Expected outcome: three bare runs of the module report the same pass count with zero failures and no order-dependent flake.
  - Execution state: performed

- [x] E-06 Run the bare suite `python3 -m pytest`, with no extra flags.
  - Depends on: E-05
  - Expected outcome: zero failures; the summary line is pasted.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Root `conftest.py` (commit `e2fba20d`, "Home isolation") already sets the pattern: a module-level setup that cannot be opted out of, plus an `@pytest.fixture(autouse=True)` `_restore_home_sandbox` that re-establishes it around every test. This plan copies the shape (autouse fixture plus explanatory comment block) but scopes it to one module.
- `tests/test_run_viewer.py` is `unittest.TestCase`-based, and pytest autouse fixtures still apply to TestCase methods. The probe under `/tmp/opencode/g2/probe-viewerguard/t/test_g.py` confirmed this: `ERROR test_g.py::T::test_bad - Failed: read live runs tree`, `3 passed, 1 error`.
- The suite runs under xdist (`-n auto`), so each worker installs its own hook when it imports the module. There is no cross-process state.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- F-1: THE ITEM'S "NO LIVE READ TODAY" CLAIM HOLDS. I ran the module in the maintainer checkout (264 live run dirs) under an audit-hook plugin that records any `open`/`os.scandir`/`os.listdir` under `.aw/records/runs` during a test call: `HITS 0`, `26 passed` (pytest collects 26 items; the item's "75 passed" figure counted subtests or an older layout). `Path(".")` call sites remain in `test_run_viewer.py` (for example `run_viewer.load_run_summary(run_d, Path("."))` and `_run_viewer(Path("."), ["status"])`). They are harmless today, but they are exactly the shape the item warns about. A grep guard can't tell them apart from a real read. An audit hook sees what actually gets read, so it can.
- F-2: `run_viewer.discover_run_dirs` scans `state_root(repo_root)`, `repo_root / ".aw" / "runs"` and `repo_root / ".agents" / "runs"`, and each scan is guarded by `r.is_dir()`. `is_dir` emits no audit event, while `iterdir` emits `os.scandir` (probe output `[('os.scandir', 'r/runs')]`). So the guard fires on real listing only, and a missing-path `os.scandir`/`open` still records an event (probe: `[('os.scandir', 'nope/x'), ('open', 'nope/y')]`). The guard therefore also catches a read attempt against an absent live tree, as long as the attempt gets past the `is_dir` check.
- F-3: The ALTERNATIVE, an autouse `monkeypatch.chdir(tmp_path)`, was probed and rejected: `26 passed` with it in place. It hides a `Path(".")` read rather than flagging it, and it misses a test that passes an absolute `_REPO` root. It would keep the module green in a fresh clone, but it would never tell the author anything.
- F-4: DOES THE ROOT-CONFTEST SANDBOX FIT? Partly. Its env-restore mechanism doesn't apply, because the run root comes from the repo path and not from an env var. Its placement (root conftest, suite-wide) would reach every module, but other modules have not been audited for legitimate reads of the checkout's own records, so a suite-wide version risks false positives. The module-scoped version is what the item asks for. Widening it is Deferred. WORTH KNOWING, confirmed at review: the root conftest's OWN "Home isolation" defect was found with an audit hook (its comment block records catching `DeclarativeAllowedValuesTests` rewriting the real user config), so this technique has direct in-repo precedent rather than being novel here.
- F-5 (measured at review; the guard's honest reach): WITH THE LIVE TREE ABSENT, A REAL LIVE-TREE READ PASSES SILENTLY. I moved `.aw/records/runs/` aside and reran a probe calling `run_viewer.discover_run_dirs(_REPO)` under the guard: `3 passed`, hook recorded nothing, because every scan sits behind `r.is_dir()` and `is_dir` emits no audit event. Directly: `discover_run_dirs` returned `[]` with zero guarded hits. So the guard is INERT in CI (a fresh `actions/checkout@v4` with no runs tree) and in a lane worktree, and fires only on a box that has run the driver. This does not defeat the plan - the Goal correctly aims at the author's machine, and that is the only place the bug is both live and invisible - but it must be stated rather than implied, because a reader who believes CI enforces this will stop looking.
- F-6 (measured at review; the dominant finding): THE E-02 SELF-TESTS DO NOT PROVE THE GUARD ENFORCES ANYTHING. Because each clears `_HITS` before returning, the autouse fixture finds nothing and never calls `pytest.fail`. I replaced the prototype's `pytest.fail(...)` with `pass` and reran: both self-tests PASSED (`2 passed`), and the full prototype went from `3 passed, 1 error` to `3 passed`. The only thing that caught the gutted enforcement was the E-04 probe, which is deleted after one run. A guard whose enforcement branch has no permanent test is one refactor away from being decorative. E-03 closes this with a subprocess self-test, prototyped and confirmed falsifiable at review.
- F-7 (measured at review): `_LIVE_RUN_ROOTS` DEPENDS ON AMBIENT CONFIG, which is fine but should be understood. `runner_shared.state_root` resolves through `resolve_project_context`, so under a `home` records backend it returns a path under the developer's real `~/.aw/projects/<id>/records/runs` - OUTSIDE the checkout - while `repository` returns `<repo>/.aw/records/runs` and `companion` returns `<repo>.aw/records/runs`. Guarding the external path is arguably MORE valuable (a test reading the developer's home run tree is at least as bad), and the root conftest's `AW_HOME` sandbox does not perturb it because the backend comes from the repo's own `project.json` (verified: `state_root` returned the same in-repo path before and after sandboxing `AW_HOME`). One-off cost at import: 23.1ms first call, 2.8ms thereafter.

## Proposed changes (ordered, validatable)

1. E-01: the audit hook and autouse fixture in `tests/test_run_viewer.py`.
2. E-02: in-process self-tests covering what the hook RECORDS.
3. E-03: a subprocess self-test covering that the fixture actually FAILS (F-6).
4. E-04: a one-shot falsification against the real live tree.
5. E-05: stability under the real suite conditions (xdist plus random order).
6. E-06: the bare suite.

## Deferred / out of scope (with reason)

- Suite-wide live-runs guard in root `conftest.py`, next to `_restore_home_sandbox`. This needs an audit of every module for legitimate reads of the checkout's own `.aw/records/` first, and it is wider than `rcmbnb` asks for.
  - Carrier-Declined: the item explicitly scopes the guard to this module ("it protects this module, not every future test"). File a backlog item only if a second module turns out to have the same hazard.
- Reads made by a subprocess (for example a test that spawns `python3 -m agent_workflows runs`) are invisible to an in-process audit hook. The module does not spawn any today; it calls `cli.main` in-process through `_run_viewer`.
  - Carrier-Declined: no current call site; the E-01 comment block records the limit.

## Scope check

- Over-scope: none.
- Under-scope (both added at review): the original plan had NO permanent test of the guard's enforcement branch, so gutting `pytest.fail` left the suite green (F-6); E-03 closes that. And stability under the suite's real conditions (xdist plus `pytest-randomly`, which the targeted `-p no:randomly` runs in E-02/E-04 deliberately disable) was inherited from a prototype rather than shown on the real module; E-05 closes that. The guard still covers every in-process listing or open of the three roots `run_viewer.discover_run_dirs` scans, subject to the reach limit in F-5.

## Required tests / validation

E-02 adds the in-process self-tests covering what the hook RECORDS. E-03 adds the subprocess self-test covering that the fixture actually FAILS, which is the assertion E-02 structurally cannot make and the one the review found missing. E-04 shows the guard failing on a real live-tree read and passing once the probe is removed. E-05 confirms stability under xdist plus random ordering. E-06 runs the bare suite. Evidence is listed per item in the validation section.

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

- [x] V-01 validates E-01
  - Required evidence: paste `git diff tests/test_run_viewer.py` showing `sys.addaudithook`, `_LIVE_RUN_ROOTS` built from `runner_shared.state_root` plus the two legacy roots, the `try/except` around the `state_root` call, and the `_forbid_live_runs_reads` autouse fixture with `pytest.fail` AND with `_HITS` cleared BEFORE the `pytest.fail` call. Also paste the tail of `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q` showing zero failures, and quote the comment block's reach sentence (the one stating the guard is inert where no live tree exists), since that limit is the review's F-5 and must not be dropped.
  - Observed evidence: Guard diff, test passing output, and reach sentence verified:
```diff
@@ -9,6 +9,9 @@
 import argparse
 import io
 import json
+import os
+import subprocess
+import sys
 import tempfile
 from contextlib import redirect_stderr, redirect_stdout
 from datetime import datetime, timezone
@@ -15,10 +15,91 @@
 from typing import Any
 from unittest import TestCase

-from agent_workflows import cli, run_viewer
+import pytest
+
+from agent_workflows import cli, run_viewer, runner_shared
 from agent_workflows.term import Term

+# --------------------------------------------------------------------------------------------------
+# Live-runs isolation: no test in this module may read the checkout's live runs tree.
+# --------------------------------------------------------------------------------------------------
+#
+# WHAT IT CATCHES, AND WHY (`rcmbnb`, `xbwq8n`). `.aw/records/runs/` is gitignored, box-local driver
+# output. A test that reads it passes on a machine that has run the driver and fails in a fresh clone,
+# in CI, and in a lane worktree. Fourteen cases did that until plan `xbwq8n` moved them onto
+# `_build_viewer_fixture`. This guard catches regression reads under `.aw/records/runs/` (and legacy
+# run roots) during test execution.
+#
+# AUDIT HOOK MECHANISM AND SCOPE. Python audit hooks (`sys.addaudithook`) cannot be removed once
+# registered. The hook is therefore flag-gated via `_ARMED[0]` so it is active only while a test in
+# this module executes, and inert for any other tests sharing the worker process.
+#
+# EXISTENCE PROBES VS REAL READS. `Path.is_dir()`, `exists()`, and `stat()` emit no audit event in
+# Python, whereas `iterdir()` emits `os.scandir`, `os.listdir()` emits `os.listdir`, and file reading
+# emits `open`. Existence probes are deliberately allowed, while directory listings and file opens
+# under the guarded roots fail.
+#
+# HONEST REACH AND LIMITATIONS (F-5). This guard protects this module only, for in-process reads, and
+# ONLY on a box where the live tree exists, since `run_viewer.discover_run_dirs` checks `r.is_dir()`
+# before scanning and an absent root is never scanned past `is_dir`. On a machine with no live runs
+# tree (such as a fresh clone, CI, or a lane worktree), an unisolated call to `discover_run_dirs`
+# returns an empty list without emitting an audit event; the guard is inert where no live tree exists.
+# CI does not enforce this guard; it is designed to catch regressions on the author's machine where
+# live run records actually exist.
+_REPO = Path(__file__).resolve().parents[1]
+try:
+    _canonical_runs = runner_shared.state_root(_REPO)
+except Exception:
+    _canonical_runs = _REPO / ".aw" / "records" / "runs"
+
+_LIVE_RUN_ROOTS: list[str] = [
+    os.path.realpath(str(_canonical_runs)),
+    os.path.realpath(str(_REPO / ".aw" / "runs")),
+    os.path.realpath(str(_REPO / ".agents" / "runs")),
+]
+
+_ARMED: list[bool] = [False]
+_HITS: list[tuple[str, str]] = []
+
+
+def _hook(event: str, args: tuple[Any, ...]) -> None:
+    if not _ARMED[0]:
+        return
+    if event in ("open", "os.scandir", "os.listdir"):
+        try:
+            p = os.path.realpath(os.fsdecode(args[0]))
+        except Exception:
+            return
+        for g in _LIVE_RUN_ROOTS:
+            if p == g or p.startswith(g + os.sep):
+                _HITS.append((event, p))
+                break
+
+
+sys.addaudithook(_hook)
+
+
+@pytest.fixture(autouse=True)
+def _forbid_live_runs_reads():
+    _HITS.clear()
+    _ARMED[0] = True
+    try:
+        yield
+    finally:
+        _ARMED[0] = False
+    if _HITS:
+        hits = list(_HITS)
+        _HITS.clear()
+        first_event, first_path = hits[0]
+        pytest.fail(
+            f"Test performed live runs read ({first_event} on {first_path!r}). "
+            ".aw/records/runs/ is gitignored and box-local; "
+            "use _build_viewer_fixture instead. "
+            f"Total hits: {hits}"
+        )
```
Tail of `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q`:
```
.............................                                            [100%]
29 passed in 9.08s
```
Quoted reach sentence:
> "On a machine with no live runs tree (such as a fresh clone, CI, or a lane worktree), an unisolated call to `discover_run_dirs` returns an empty list without emitting an audit event; the guard is inert where no live tree exists. CI does not enforce this guard; it is designed to catch regressions on the author's machine where live run records actually exist."
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -k LiveRunsGuardSelfTests` showing the self-tests passing. Then temporarily comment out the `sys.addaudithook(...)` line, rerun, and paste output showing `test_guard_records_a_read_under_a_guarded_root` FAILED. Restore the line and paste an empty `git diff --stat tests/test_run_viewer.py`-relative confirmation that only the intended diff remains.
  - Observed evidence: Self-tests passing, hook falsification failure, and line restored:
1. Self-tests passing:
```
$ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -k LiveRunsGuardSelfTests
...                                                                      [100%]
3 passed, 26 deselected in 1.43s
```
2. With `sys.addaudithook` commented out:
```
$ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -k LiveRunsGuardSelfTests
F..                                                                      [100%]
=================================== FAILURES ===================================
____ LiveRunsGuardSelfTests.test_guard_records_a_read_under_a_guarded_root _____

self = <tests.test_run_viewer.LiveRunsGuardSelfTests testMethod=test_guard_records_a_read_under_a_guarded_root>

    def test_guard_records_a_read_under_a_guarded_root(self):
        with tempfile.TemporaryDirectory() as td:
            runs_dir = Path(td) / "runs"
            (runs_dir / "run-x").mkdir(parents=True)
            guarded_path = os.path.realpath(str(runs_dir))
            _LIVE_RUN_ROOTS.append(guarded_path)
            try:
                list(Path(td, "runs").iterdir())
>               self.assertEqual(len(_HITS), 1)
E               AssertionError: 0 != 1

tests/test_run_viewer.py:2065: AssertionError
=========================== short test summary info ============================
FAILED tests/test_run_viewer.py::LiveRunsGuardSelfTests::test_guard_records_a_read_under_a_guarded_root
1 failed, 2 passed, 26 deselected in 0.78s
```
3. Line restored and diff confirmed:
```
$ git diff --stat tests/test_run_viewer.py
 tests/test_run_viewer.py | 199 ++++++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 198 insertions(+), 1 deletion(-)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the subprocess self-test PASSING. Then perform the falsification that E-02 cannot: replace the `pytest.fail(...)` call INSIDE the generated inner module with `pass`, rerun, and paste the output showing the self-test FAILING (the review's prototype reported `AssertionError` with the inner run's `1 passed`). Restore it. This is the plan's single most important piece of evidence, because F-6 measured that without it the entire enforcement branch is untested; a passing run alone does not satisfy this item.
  - Observed evidence: Subprocess self-test passing, gutted inner fail falsified, and restored test passing:
1. Subprocess self-test passing:
```
$ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -k test_fixture_fails_a_test_that_reads_a_guarded_root
.                                                                        [100%]
1 passed, 28 deselected in 0.75s
```
2. Falsification with `pytest.fail(...)` replaced with `pass` in inner module:
```
$ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -k test_fixture_fails_a_test_that_reads_a_guarded_root
F                                                                        [100%]
=================================== FAILURES ===================================
__ LiveRunsGuardSelfTests.test_fixture_fails_a_test_that_reads_a_guarded_root __

self = <tests.test_run_viewer.LiveRunsGuardSelfTests testMethod=test_fixture_fails_a_test_that_reads_a_guarded_root>

        def test_fixture_fails_a_test_that_reads_a_guarded_root(self):
...
>               self.assertNotEqual(res.returncode, 0)
E               AssertionError: 0 == 0

tests/test_run_viewer.py:2154: AssertionError
=========================== short test summary info ============================
FAILED tests/test_run_viewer.py::LiveRunsGuardSelfTests::test_fixture_fails_a_test_that_reads_a_guarded_root
1 failed, 28 deselected in 0.78s
```
3. Restored `pytest.fail(...)` and re-verified pass:
```
$ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -k test_fixture_fails_a_test_that_reads_a_guarded_root
.                                                                        [100%]
1 passed, 28 deselected in 0.78s
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the run WITH `_ProbeLiveRead` present, showing `_ProbeLiveRead::test_probe` failed (or errored) with the guard message naming a path under the runs root. Then paste the run WITHOUT it, showing zero failures, and `git diff --stat tests/test_run_viewer.py` showing no probe class left behind. If you synthesized a runs tree because this checkout had none, say so explicitly and paste the filesystem check (for example `ls .aw/records/runs`) proving you removed it; `git status` alone is NOT sufficient evidence here, because the path is gitignored and would look clean either way.
  - Observed evidence: Synthesized runs tree in lane worktree (.aw/records/runs/run-probe/state.json created); probe failed, probe removed passed, tree removed verified:
Synthesized runs tree in lane worktree: `.aw/records/runs/run-probe/state.json` created.
1. Run with `_ProbeLiveRead` present:
```
$ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -p no:randomly
..............................E                                          [100%]
==================================== ERRORS ====================================
________________ ERROR at teardown of _ProbeLiveRead.test_probe ________________

    @pytest.fixture(autouse=True)
    def _forbid_live_runs_reads():
        _HITS.clear()
        _ARMED[0] = True
        try:
            yield
        finally:
            _ARMED[0] = False
        if _HITS:
            hits = list(_HITS)
            _HITS.clear()
            first_event, first_path = hits[0]
>           pytest.fail(
                f"Test performed live runs read ({first_event} on {first_path!r}). "
                ".aw/records/runs/ is gitignored and box-local; "
                "use _build_viewer_fixture instead. "
                f"Total hits: {hits}"
            )
E           Failed: Test performed live runs read (os.scandir on '/home/user/VC/agent-workflows/.aw/worktrees/swps4w/.aw/records/runs'). .aw/records/runs/ is gitignored and box-local; use _build_viewer_fixture instead. Total hits: [('os.scandir', '/home/user/VC/agent-workflows/.aw/worktrees/swps4w/.aw/records/runs')]

tests/test_run_viewer.py:98: Failed
=========================== short test summary info ============================
ERROR tests/test_run_viewer.py::_ProbeLiveRead::test_probe - Failed: Test per...
30 passed, 1 error in 6.06s
```
2. Run with `_ProbeLiveRead` removed:
```
$ python3 -m pytest tests/test_run_viewer.py -o addopts="" -q -p no:randomly
.............................                                            [100%]
29 passed in 9.36s
```
3. Synthesized runs tree removed; filesystem check confirming it no longer exists:
```
$ rm -rf .aw/records/runs
$ ls .aw/records/runs
ls: cannot access '.aw/records/runs': No such file or directory
```
4. Git status and diff stat confirming probe class removed:
```
$ git status --short
 M tests/test_run_viewer.py
$ git diff --stat tests/test_run_viewer.py
 tests/test_run_viewer.py | 199 ++++++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 198 insertions(+), 1 deletion(-)
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the summary line of all THREE bare `python3 -m pytest tests/test_run_viewer.py` runs, showing the same pass count and zero failures each time. State the pass count explicitly; review measured 26 collected items in this module, so a materially different number is worth explaining rather than glossing.
  - Observed evidence: Three consecutive bare runs stable with 29 passed across xdist and random ordering:
Three consecutive bare runs (xdist parallel + randomized test order):
- Bare run 1: `29 passed in 7.22s`
- Bare run 2: `29 passed in 7.03s`
- Bare run 3: `29 passed in 3.76s`
Pass count is 29 (26 pre-existing tests + 3 new tests in `LiveRunsGuardSelfTests`). Zero failures across all three runs with stable execution under xdist and random ordering.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the final summary line of bare `python3 -m pytest` (for example `N passed, M skipped`) with zero failed and zero errors. Bare per AGENTS.md: no `-n0`, no extra `-q`, no `-p no:randomly`.
  - Observed evidence: Bare full suite run completed with 2253 passed, 1 skipped, 0 failed, 0 errors:
```
$ python3 -m pytest
2253 passed, 1 skipped, 3 warnings in 42.74s
```
Zero failed, zero errors.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Six items, one concern: a falsifiable live-runs read guard for one test module. The count grew from four at review because the original E-02's self-tests were measured NOT to exercise the guard's enforcement branch (F-6), which needed a separate item with a different mechanism (a subprocess, E-03), and because stability under the suite's real xdist-plus-random conditions was asserted rather than shown (E-05). No item introduces a second concern, and the whole change remains confined to one test file.

WHAT A HUMAN IS APPROVING. A test-only change to `tests/test_run_viewer.py` that installs a process-wide `sys.addaudithook` when that module is imported. Two things deserve a second look even though the diff is small and touches no production code. FIRST, an audit hook cannot be uninstalled once registered, so it remains present for the rest of that pytest worker's life; it is flag-gated (`_ARMED`) so it is inert outside this module's tests, and review measured its cost as indistinguishable from zero (1.00x on a 3,000-file write-and-read loop), but "cannot be removed" is a property worth knowing you are accepting. SECOND, the guard's REACH is narrower than the title suggests: it is inert on any machine with no live runs tree, which includes CI and every lane worktree (F-5), so this buys author-side detection and not a CI gate.

SCOPE FENCE (a DECLARATION for reconciliation, not a stop directive). The only file to change is `tests/test_run_viewer.py`, and within it: three new imports (`os`, `sys`, `pytest`), the `_REPO`/`_LIVE_RUN_ROOTS`/`_HITS`/`_ARMED` module constants, the `_hook` function and its single `sys.addaudithook` registration, the `_forbid_live_runs_reads` autouse fixture, the explanatory comment block, and the `LiveRunsGuardSelfTests` class with three tests. EXPLICITLY NOT IN SCOPE: any change to `agent_workflows/run_viewer.py` or `agent_workflows/runner_shared.py`; the root `conftest.py`; the existing six `Path(".")` call sites in this module (they are safe today per F-1 and rewriting them is not this plan's job); and any suite-wide widening of the guard (Deferred). An out-of-scope edit is made and then JUSTIFIED (`aw ipd finalize` requires a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

HONESTY RULE (hard MUST). Paste the ACTUAL runner output for every `V-*`; never claim a test passed that you did not run. This plan is most exposed to faking on V-03 and V-02, because each requires PRODUCING A FAILURE by temporarily breaking the guard and then restoring it - the easiest evidence in this plan to assert without performing, and the only evidence that distinguishes a working guard from a decorative one. V-04's cleanup claim is the second: the runs path is gitignored, so a false "nothing left behind" would not be caught by `git status`.

STOP CONDITIONS (genuinely unsafe, distinct from the scope fence). Stop and report if: `run_viewer.discover_run_dirs` no longer scans the three roots E-01 enumerates (the guarded set would then be wrong rather than incomplete); or `tests/test_run_viewer.py` has gained a test that legitimately reads the checkout's own runs tree, since the guard would then be refusing correct behavior and the design question returns to the maintainer.

Execute only after `- Status: approved`. Commit only `tests/test_run_viewer.py` through `aw commit swps4w -- tests/test_run_viewer.py`. Never commit the E-04 probe class, and never commit a synthesized `.aw/records/runs/` directory. LIFECYCLE TRANSITION: reaching `executed/` via `aw ipd finalize` is UNCONDITIONALLY owed, but under `aw oc run`/`aw agy run` the RUNNER owns that transition, so do not invoke it yourself in a runner-driven execution; a hand execution invokes it. Never hand-roll a `git mv` to `executed/`. Transition only after `aw ipd lint --phase pre-transition` conforms and V-01..V-06 carry pasted evidence. Backlog `rcmbnb` is already `graduated` and carries no `- Blocks-Release:`, so no gate handoff is owed.
