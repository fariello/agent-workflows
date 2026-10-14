- Id: rd6ei9
- Status: graduated
- Graduated-To: rd6ei9
- Set: rd6ei9
- Priority: low
- Work-Kind: chore
- Summary: Decide whether the remaining repo-relative path renderers (ipd_lifecycle._repo_relative, attention._rel_posix, layout_inventory._repo_relative, doctor's inline Drift-location relativization in probe_artifacts) should adopt the shared artifact_core renderer that qv0fi1's plan amt9fs introduces

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 61lsze
- 2026-10-12 created (aw backlog): Filed while authoring amt9fs (graduating qv0fi1), which unifies exactly the four renderers qv0fi1 names. These further sites were found by grep and are OUT of that plan's scope because their contracts differ on purpose: ipd_lifecycle._repo_relative falls back to the resolved ABSOLUTE path (receipt plan_path), attention._rel_posix RAISES ValueError outside the root, layout_inventory._repo_relative returns None as a signal and deliberately does not resolve symlinks, and doctor.probe_artifacts relativizes with os.sep-joined str(). Each needs its own behavior argument. Not user-perceptible (inputs are always under the root in normal operation), so chore.
