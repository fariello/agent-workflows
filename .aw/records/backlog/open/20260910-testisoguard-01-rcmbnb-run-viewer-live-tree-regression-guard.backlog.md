- Id: rcmbnb
- Status: open
- Set: testisoguard
- Priority: low
- Work-Kind: chore
- Summary: test_run_viewer.py has no guard against a new test re-reading the gitignored live .aw/records/runs/ tree

## Workflow history
- 2026-09-10 created (aw backlog): test_run_viewer.py has no guard against a new test re-reading the gitignored live .aw/records/runs/ tree

CARRIED FORWARD from plan `utwr6y` (`testiso` Order 01), retired `superseded` 2026-09-10. That plan's
central premise is dead (the 14 live-tree-dependent cases were converted to a synthetic fixture by plan
`xbwq8n` on 2026-09-08), but its E-03 REGRESSION GUARD was never built and is the one piece still live.
This item exists so retiring the plan does not silently drop it.

THE DEFECT THE GUARD WOULD PREVENT, stated as the symptom rather than the remedy: `.aw/records/runs/`
is GITIGNORED, box-local driver output. A test that reads it passes only on a machine that has run the
driver and fails in a fresh clone, in CI, and in a lane worktree. That is exactly what happened: 14
cases in `tests/test_run_viewer.py` did this, and the file was unrunnable anywhere else until `xbwq8n`
fixed it. Nothing prevents the next test from reintroducing the dependency, and the failure mode is
nasty because it is INVISIBLE to the author (it passes on their box) and appears only for someone else.

CURRENT STATE, MEASURED 2026-09-10 rather than assumed. A fresh clone with zero `.aw/records/runs/`
entries reports `75 passed` for `tests/test_run_viewer.py` (`python3 -m pytest tests/test_run_viewer.py
-o addopts=""`). The fixture builder is `_build_viewer_fixture` (`:36`) and a module-level hazard
warning already exists at `:3` and `:25`. So there is NO live-tree read to fix; only the guard is
missing.

THE `dir="."` SWEEP IS ALREADY DONE, so whoever picks this up need not redo it. Five occurrences remain
and none is a live-tree read: `:25`, `:365`, `:375` and `:1910` are PROSE (the header hazard note and
two docstrings recording the history), and `:1954` is a live call in
`test_repair_without_a_target_errors_and_shows_usage`, which is SAFE because that path exits 2 on a
usage error before reading any run directory (verified passing in the fresh clone).

WHAT A GUARD MIGHT LOOK LIKE, offered as options and not as a decision: a test asserting no NEW
`dir="."` call site appears in the module beyond the one known-safe occurrence; or a fixture-scoped
check that the module never resolves a run root outside a temp dir; or running the file with the live
tree hidden. The honest limitation to weigh first: a naive grep-style guard would flag the four prose
occurrences and the one safe call, so it needs a real discriminator or it will be disabled as noisy.
Note also that any guard is only as good as its reach; it protects this module, not every future test
that might read run state.

WHY LOW PRIORITY: the live defect is fixed and the suite is green everywhere, so this is prevention
rather than repair. It is worth doing because the failure mode is invisible to the author who
reintroduces it, but nothing is broken today.
