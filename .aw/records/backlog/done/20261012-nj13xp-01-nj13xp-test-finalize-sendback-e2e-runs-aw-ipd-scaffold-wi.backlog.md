- Id: nj13xp
- Status: done
- Graduated-To: nj13xp
- Blocks-Release: next
- Set: nj13xp
- Priority: medium
- Work-Kind: bug
- Summary: test_finalize_sendback e2e runs aw ipd scaffold without --dir, so it climbs out of its temp repo and writes plans into any enclosing AW project (source of the polluted /tmp/.aw that fails ~39 non-project tests)

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD ivq0nr executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-nj13xp-01-ivq0nr-pass-dir-in-test-finalize-sendback-e2e-scaffold-and-bound-fi.ipd.md); evidence .aw/records/plans/executed/20261014-nj13xp-01-ivq0nr-pass-dir-in-test-finalize-sendback-e2e-scaffold-and-bound-fi.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: ivq0nr
- 2026-10-12 created (aw backlog): test_finalize_sendback e2e runs aw ipd scaffold without --dir, so it climbs out of its temp repo and writes plans into any enclosing AW project (source of the polluted /tmp/.aw that fails ~39 non-project tests)

Observed 2026-10-12 in lane 69pxm5: /tmp/.aw/records/plans/pending held 44 leaked 20261012-testset-01-*-e2e-test-plan.ipd.md files; with it present the bare suite fails 39 tests (test_no_project_exit_is_cannot_run, test_explicit_dir_non_project, test_validator_nonsurveyable_dir, ...) with 'the specified directory is inside an AW project' instead of 'no AW project found'. Same failures on an unmodified HEAD export; TMPDIR=/var/tmp gives 7222 passed. Setting TMPDIR inside a checkout reproduced the leak into that checkout's .aw/records/plans/pending. Fix: pass --dir to the scaffold subprocess in tests/test_finalize_sendback.py (E2E Test Plan), and consider whether project discovery should stop at the enclosing git root.
