- Id: x15f0q
- Status: done
- Blocks-Release: next
- Set: x15f0q
- Priority: high
- Work-Kind: bug
- Summary: install --to-aw leaves empty legacy directories and .agents/README.md behind, so every migrated repo permanently reports a dual-layout split-brain and doctor advises a migration that already ran

## Workflow history
- 2026-09-23 set (aw backlog): closed by aw oc run: IPD z1yefm executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260912-migleftover-01-z1yefm-stop-install-to-aw-leaving-a-permanent-split-brain-classify.ipd.md); evidence .aw/records/plans/executed/20260912-migleftover-01-z1yefm-stop-install-to-aw-leaving-a-permanent-split-brain-classify.ipd.md
- 2026-09-12 graduated (aw set): Design handed off to a review-ready IPD authored from repo-verified root cause
- 2026-09-12 open (aw set): status set to open
- 2026-09-12 created (aw backlog): Reproduced on 9 real 1.2.1 legacy repos via tools/aw_upgrade_test.py

MEASURED on nine real repos (pysyslib, veraclavis, ansurv, cscie86-scratch, emo-train, Misc-Dev, zmm, grant-data, pubrun-benchmarks), each installed at 1.2.1 in the legacy .agents/ layout, upgraded with 'aw install <repo> -y --to-aw' inside a disposable sandbox. Every one exited 0 and every one ended in the same state:

- 4 to 9 EMPTY directories remain under '.agents/workflows/' (e.g. assess/tools, verify/tools, benchmark/tools, setup-repo/tools). Zero files, directories only.
- 92 files remain under '.agents/skills/'. CORRECTION (2026-09-12, verified after filing): these are NOT leftovers and NOT a defect. '.agents/skills' is the INTENDED location for BOTH layouts by deliberate design: engine.SKILLS_DIR = '.agents/skills' (engine.py:171) and resolve_skills_dir() returns it for the aw layout too (engine.py:174-183), because a skill package is DISCOVERED by a host tool scanning a fixed host-facing directory, exactly like the .opencode/.claude command shims. Verified on a fresh --to-aw run: all 92 files are present as CURRENT manifest rows, all exist on disk, and their mtimes match the install that just ran, i.e. the installer WROTE them there. The original 'unreferenced duplicates' claim in this item was wrong.
- '.agents/README.md' remains.

CONSEQUENCE, and why this is not cosmetic: the leftover directories make the repo look like a split-brain layout forever. On a migrated sandbox 'aw doctor' says:

    Layout:      .aw + .agents (dual layout / split-brain)
    Warning:     Dual layouts detected (.aw/ and .agents/). Run 'aw migrate-layout' to consolidate.

The advice is unactionable, because the migration already ran and there is nothing left to move. The user is told to fix a condition that the tool itself created and that re-running the tool will not clear. The split-brain guard in the install path (_split_brain_guard) also keys off this state, so a migrated repo can be warned or refused on later installs.

ROOT CAUSE (repo-verified, not inferred): cli._handle_legacy_migration hardcodes leftover_disposition='defer' when it drives the migration for --to-aw (cli.py:5241, and again on the interactive path at cli.py:5265-5267). 'defer' RECORDS leftovers for a later cleanup and deliberately deletes nothing (layout_migration._handle_leftovers, layout_migration.py:527-541). No install-time flag can reach any other disposition, so an install-driven migration can never clean up after itself. Precedent for the fix already exists in the codebase: engine.migrate_legacy_layout removes a now-empty legacy dir after moving its contents (engine.py:2624-2636).

The REAL residue after --to-aw is therefore: empty directories under .agents/workflows/ plus .agents/README.md, and NOT the skills tree. That is enough on its own to trip the dual-layout detector, because the detector keys off directory EXISTENCE rather than live content.

REPRODUCE: tools/aw_upgrade_test.py new <repo> -y -- --to-aw
