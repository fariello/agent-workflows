- Id: ovjx46
- Status: graduated
- Graduated-To: statuslayout
- Work-Kind: bug
- Blocks-Release: next
- Set: ovjx46
- Priority: low
- Summary: Audit check_engine's own layout rules for the same bare-existence split-brain false positive that doctor.probe_environment carried

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into plan 4eecvh (Set statuslayout), re-verified live at HEAD.
- 2026-09-26 same-status (aw set): Reclassified bug + Blocks-Release next on measurement (2026-09-26): the audit found check_engine clean, but aw status (cli._collect_repo_status_details) flags split-brain whenever .aw and .agents both exist, so every correctly migrated repo with .agents/skills shows a wrong orange 'run aw migrate-layout' warning while aw doctor says clean.
- 2026-09-23 created (aw backlog): Audit check_engine's own layout rules for the same bare-existence split-brain false positive that doctor.probe_environment carried

Carrier for a deliberately deferred obligation in plan z1yefm (migleftover Order 01).

WHAT IS DEFERRED
z1yefm E-06 repointed `doctor.probe_environment`'s layout classification at the shared
content-aware `engine.detect_split_brain_layout`, because the probe's bare `.is_dir()` test
reported a permanent split-brain on every correctly migrated repo (`.agents/` is a PERMANENT
resident, since `.agents/skills` is the intended skills location for BOTH layouts).

`check_engine`'s own layout rules are a SEPARATE surface with their own tests, and they are not
what a user sees in `aw doctor`, so z1yefm deliberately left them alone rather than widening its
blast radius. Whether they carry the same bare-existence assumption has NOT been checked.

WHAT TO DO
Read `check_engine`'s layout rules and determine whether any of them decides 'dual layout' or
'split-brain' from directory EXISTENCE rather than from content. If so, repoint them at
`engine.detect_split_brain_layout` as E-06 did, so `aw check`, `aw doctor`, and the install
guard cannot report this condition three different ways.

EVIDENCE THAT THE HAZARD IS REAL
Measured in z1yefm on a residue-only fixture BEFORE the fix: `engine.detect_split_brain_layout`
returned `False` while `doctor.probe_environment` returned
`.aw + .agents (dual layout / split-brain)` and advised running a migration that had already run.
Two detectors disagreeing is exactly the class of defect this audit looks for in a third.
