# Review: Install-time layout.json and schema emission in engine.py

- Plan-Id: hauwqh
- Reviewed-At: 2026-09-04
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 6

All claims verified at HEAD `16777ccc`, working tree clean, target plan committed and unchanged, so the
pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` and again at
`--phase review-finalize`.

NO NEW FINDINGS. This is the best-evidenced plan of the four, and I could not falsify any load-bearing
claim. Recording what I checked, because "no findings" is only worth reading if the checking is visible:

- `install_into_repo` is at `engine.py:5420`, as stated.
- `_AW_GITIGNORE_TEMPLATE` at `:4207` and `_ensure_aw_gitignore` at `:5236`. This makes PR-027's
  two-places instruction correct AND it is the part a naive executor would get wrong: editing only this
  repo's checked-in `.aw/.gitignore` would change nothing for any target repo, because a target's copy
  is GENERATED from the template, and it would still pass a naive "the file contains the line" test.
- `cli.py:4226` really does call `engine.install_into_repo` directly, confirming PR-026: wiring emission
  into `engine.run()` would leave `aw setup` silently emitting nothing, and no test in the plan as
  originally written would have caught it. Putting the call inside the shared function covers all three
  callers by construction.
- `tests/test_engine_install.py` genuinely does not exist, so E-03 is correctly a CREATE.
- `.aw/.gitignore` is TRACKED in this repo, which is consistent with (not contrary to) the plan's point
  that a target's copy is generated.
- `agent_workflows/engine.py` is declared by only ONE other pending plan, its own orchestrator, so
  F-5's "no current conflict" measurement still holds at this HEAD.

Two details deserve explicit credit because they are the kind reviews usually miss: the root-`.gitignore`
assertion is correctly scoped to "carries no layout entry" rather than "has no diff" (the installer
genuinely does write an `aw:block` and a backups line there, so a no-diff assertion would fail for a
legitimate reason on first install), and the determinism requirement makes re-install a no-op rather
than a rewrite.

### Findings

No actionable finding was raised in this round, so this table is deliberately EMPTY rather than carrying
a placeholder row. A synthetic `(none)` row does not parse as a finding (its severity and decision are
not in the closed enums), which would make the record report a diagnostic and a spurious gating block -
the opposite of what an all-clear round should do.

What was checked is recorded in the round narrative above, so "no findings" remains auditable: every
cited anchor was re-measured at HEAD `16777ccc` (`install_into_repo:5420`, `_AW_GITIGNORE_TEMPLATE:4207`,
`_ensure_aw_gitignore:5236`, `cli.py:4226`), `tests/test_engine_install.py` was confirmed absent, and
`engine.py` was confirmed declared by only one other pending plan.
