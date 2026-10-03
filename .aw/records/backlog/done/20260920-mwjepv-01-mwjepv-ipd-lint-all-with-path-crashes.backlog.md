- Id: mwjepv
- Status: done
- Graduated-To: mwjepv
- Blocks-Release: next
- Set: mwjepv
- Priority: medium
- Work-Kind: bug
- Summary: aw ipd lint --all <path> crashes because a list is passed to Path()

## Workflow history
- 2026-10-01 set (aw backlog): closed by aw oc run: IPD gonzhl executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260929-mwjepv-01-gonzhl-make-aw-ipd-lint-all-root-resolve-a-root-instead-of-crashing.ipd.md); evidence .aw/records/plans/executed/20260929-mwjepv-01-gonzhl-make-aw-ipd-lint-all-root-resolve-a-root-instead-of-crashing.ipd.md
- 2026-09-29 set (aw backlog): graduated by run run-20260928T235941Z-1396311: gonzhl
- 2026-09-20 created (aw backlog): aw ipd lint --all <path> crashes because a list is passed to Path()

MEASURED 2026-09-20 while executing plan `9zvl2w` (encountered building a quarantine fixture).

`aw ipd lint --all <path>` fails with a TypeError surfaced as a could-not-run error:

    $ python3 -m agent_workflows ipd lint --all /tmp/somerepo
    error: lint failed to run: argument should be a str or an os.PathLike object
    where __fspath__ returns a str, not 'list'

CAUSE: `ipd_lint.run_lint` does `root = Path(getattr(args, "path", None) or ".")` (`ipd_lint.py:1573`), but `path` is declared `nargs="*"`, so it arrives as a LIST. The bare `--all` case works because the empty list is falsy and `"."` is used instead, which is why this has gone unnoticed: the documented default path is the only one exercised.

PRE-EXISTING: reproduced at HEAD `5ff889aa` before any `9zvl2w` edit (`git show HEAD:agent_workflows/ipd_lint.py` carries the identical line at :1527).

USER-PERCEPTIBLE: the `--all` help text says 'or a repo root with --all', so the one documented way to lint a repository OTHER than the cwd is broken. A human or agent linting another checkout gets a crash, not a result.

FIX SHAPE: take the FIRST element when the list is non-empty (and decide whether 2+ roots with `--all` is an error or a loop). Add a regression test covering `--all <root>`; none exists today, which is why the defect shipped.
