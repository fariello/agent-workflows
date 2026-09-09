- Id: dbslfm
- Status: open
- Set: m105rev
- Priority: medium
- Work-Kind: bug
- Summary: IPD-M105 cannot see a terminal directory holding a non-terminal status, because the whole executed tree returns legacy before the metadata check runs

## Workflow history
- 2026-09-08 created (aw backlog): FOUND 2026-09-08 while measuring, at the maintainer's challenge, whether a tracked-only status-versus-directory audit already existed (during the review of 6ltz1y OQ-03). The maintainer approved filing this separately rather than widening that plan. THE PREDICATE IS CORRECT AND LIVE: ipd_schema._check_path_status (:432-456) is pure and tracked-only, covers all five dispositions, and surfaces as IPD-M105; verified that a pending/ file carrying Status: executed yields it at ERROR. THE GAP IS ONE-DIRECTIONAL: ipd_lint.py:1023-1025 returns DISPOSITION_LEGACY with an EMPTY diagnostic list for any file in a terminal directory before check_metadata runs, so a file in executed/ whose own Status says to-review produces NOTHING, measured, including under a date shard. The exemption is BY DIRECTORY rather than by age or format version, so it exempts a plan written today exactly as much as one written in June. k9awrq (lintreach-01) would make IPD-M105 reachable from aw check but CANNOT fix this and says so, its scope excluding 'CHANGING ANY LINT RULE, or adding one. This plan changes REACHABILITY only'. Filed as a DECISION item because the honest fix is choosing what replaces a directory-shaped exemption (a date/format cutover, the mechanism config.dependency_cutover_date already provides, or a severity split), and because the blast radius across the three terminal directories must be counted before a severity is chosen. No Blocks-Release: this is a latent enforcement gap, not a live defect in shipped behavior.

/tmp/opencode/b1.md
