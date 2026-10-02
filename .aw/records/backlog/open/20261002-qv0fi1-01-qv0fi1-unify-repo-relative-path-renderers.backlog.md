- Id: qv0fi1
- Status: open
- Set: qv0fi1
- Priority: low
- Work-Kind: chore
- Summary: Unify the four repo-relative path renderers (artifact_rename._rel_to_repo, specs.drift_location, doctor._normalize_rel_path, and check_engine's new 2eubdn helper) behind one fallback policy

## Workflow history
- 2026-10-02 created (aw backlog): Filed at /plan-review of 2eubdn (2026-10-02): that plan deferred this P8 duplication to carrier w38q54, which is its OWN source item and closes when 2eubdn executes, so the deferral would vanish. The four helpers differ in fallback on purpose (raw posix, records-segment truncation, normalize, name-only), so unifying needs a behavior argument about which fallback wins; 2eubdn adopts specs.drift_location's name-only fallback as the leak-free choice. Not user-perceptible, so chore.
