- Id: x15f0q
- Status: open
- Set: x15f0q
- Priority: high
- Work-Kind: bug
- Summary: install --to-aw leaves empty legacy directories and the whole .agents/skills tree behind, so every migrated repo reports a permanent dual-layout split-brain

## Workflow history
- 2026-09-12 created (aw backlog): Reproduced on 9 real 1.2.1 legacy repos via tools/aw_upgrade_test.py

MEASURED on nine real repos (pysyslib, veraclavis, ansurv, cscie86-scratch, emo-train, Misc-Dev, zmm, grant-data, pubrun-benchmarks), each installed at 1.2.1 in the legacy .agents/ layout, upgraded with 'aw install <repo> -y --to-aw' inside a disposable sandbox. Every one exited 0 and every one ended in the same state:

- 4 to 9 EMPTY directories remain under '.agents/workflows/' (e.g. assess/tools, verify/tools, benchmark/tools, setup-repo/tools). Zero files, directories only.
- 92 files remain under '.agents/skills/' (the entire pre-migration skills tree), while the framework now installs skills under the .aw layout. The old copies are unreferenced duplicates that a host may still discover.
- '.agents/README.md' remains.

CONSEQUENCE, and why this is not cosmetic: the leftover directories make the repo look like a split-brain layout forever. On a migrated sandbox 'aw doctor' says:

    Layout:      .aw + .agents (dual layout / split-brain)
    Warning:     Dual layouts detected (.aw/ and .agents/). Run 'aw migrate-layout' to consolidate.

The advice is unactionable, because the migration already ran and there is nothing left to move. The user is told to fix a condition that the tool itself created and that re-running the tool will not clear. The split-brain guard in the install path (_split_brain_guard) also keys off this state, so a migrated repo can be warned or refused on later installs.

Note the two leftovers are DIFFERENT defects with different fixes: empty directories are cleanup litter, whereas the orphaned skills tree is duplicated live content. Migration already has a --leftovers disposition (keep|remove|defer, defaulting to defer), so the question is whether an install-time --to-aw should default to sweeping empty dirs and whether skills should be MOVED rather than re-installed.

REPRODUCE: tools/aw_upgrade_test.py new <repo> -y -- --to-aw
