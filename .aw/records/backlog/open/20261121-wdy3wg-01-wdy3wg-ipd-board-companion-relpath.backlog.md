- Id: wdy3wg
- Status: open
- Set: wdy3wg
- Work-Kind: bug
- Priority: medium
- Summary: aw ipd board text mode crashes with ValueError when plans live in a companion records root
- Short-Description: aw ipd board text mode crashes with ValueError when plans live in a companion records root
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): aw ipd board text mode crashes with ValueError when plans live in a companion records root

## Symptom

In a repository configured with companion records storage (`public-target-private-companion`), `aw ipd board` in text mode raises an uncaught `ValueError: '<companion>/records/plans/pending/<plan>.ipd.md' is not in the subpath of '<target_repo>'`. The `--agent` form exits 0 because it catches the exception and falls back to the absolute path.

Reproduced 2026-11-21 with the `tests/test_companion_runner_integration.py::_provision_companion_repos` fixture and one pending plan in the companion records root, calling `cli.main(["ipd", "board", "--no-color", "--dir", <target>])`.

## Root cause

`agent_workflows/cli.py::_run_plans` prints each record with `rec.path.relative_to(root).as_posix()` in the text-mode listing loop. In companion storage `rec.path` lies under the companion records root, not under `root`, so `Path.relative_to` raises. The `--agent`/`--json` branch in the same function already wraps the same call in `try`/`except`.

Found while authoring plan `wknwwz` for backlog item `es4blt`, which names this as a related note.

## Acceptance criteria

1. `aw ipd board` in text mode lists a plan stored in a companion records root and exits 0.
2. The printed path for a companion plan is a stable display form (for example `.aw/records/<rel>` or the absolute path), and the `--agent`/`--json` path field uses the same form.
3. A regression test drives `cli.main(["ipd", "board", ...])` against a companion fixture and asserts exit 0 and the plan's filename in the output.
