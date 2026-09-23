- Id: izfscm
- Status: open
- Blocks-Release: next
- Set: izfscm
- Priority: medium
- Work-Kind: bug
- Summary: aw_upgrade_test.py probe reports .agents/skills as 'orphaned-skills ... unreferenced duplicates' but that directory is the INTENDED skills location for both layouts, so the harness advises deleting live install output

## Workflow history
- 2026-09-23 created (aw backlog): aw_upgrade_test.py probe reports .agents/skills as 'orphaned-skills ... unreferenced duplicates' but that directory is the INTENDED skills location for both layouts, so the harness advises deleting live install output

Found while executing plan z1yefm (migleftover Order 01).

WHAT IS WRONG
The rehearsal harness emits this observation after a MIGRATING run:

  [orphaned-skills] 92 file(s) remain under .agents/skills/ while the framework now installs
  skills under the .aw layout, so the old copies are unreferenced duplicates a host may still
  discover.

Both clauses are false. The framework does NOT install skills 'under the .aw layout':
`engine.SKILLS_DIR = ".agents/skills"` and `engine.resolve_skills_dir()` returns that SAME path
for the `aw` layout as for the legacy one, deliberately, because a skill package is discovered by
a host tool scanning a fixed directory (exactly like the `.opencode/` and `.claude/` command
shims). So the files are not duplicates and not unreferenced; they are the live, current install
output. Verified in the z1yefm rehearsal: all 92 files survive a `--leftovers remove` migration
and are CURRENT manifest rows.

WHY IT MATTERS
This is the harness whose whole purpose is to produce evidence a human or agent then judges, and
this observation actively misleads that judgement toward deleting working install output. It has
already done so once: it is the origin of the incorrect 'unreferenced duplicates' claim in backlog
item x15f0q, which plan z1yefm had to correct (recorded as F-06 in that plan). An observation that
has already propagated one wrong conclusion into a tracked record will do it again.

SCOPE NOTE
Not fixed in z1yefm because `tools/aw_upgrade_test.py` is outside its Scope-Paths.

SUGGESTED FIX
Drop the `orphaned-skills` observation, or invert it: `.agents/skills` SURVIVING a migration is
the correct outcome, and its DISAPPEARANCE is the reportable defect. Read the expected path from
`engine.resolve_skills_dir` so the harness cannot drift from the installer again.
