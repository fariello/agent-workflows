- Id: 5st6e5
- Status: done
- Blocks-Release: next
- Set: cihealth
- Priority: high
- Work-Kind: bug
- Summary: CI has failed on every push since 2026-09-27 (about 1,600 main commits) and nothing on this machine shows it

## Workflow history
- 2026-10-15 done (aw backlog): status set to done
- 2026-10-13 created (aw backlog): filed during /plan-review of Set gradfix; graduated to Set cihealth

Measured 2026-10-12 with gh run list: last green tests.yml run 2026-09-27 (f69ad318a); 1623 first-parent commits since. Root causes in run 38168033704: test extra pins filelock>=4 (requires Python >=3.10) while CI tests 3.9, so every 3.9 leg fails at install; tests use typing.Self and contextlib.chdir (3.11+); tests need the agy binary or a sandbox; mypy gate reports 15 errors; aw check plans exits 1 on 15 findings. Maintainer ruling 2026-10-12: fix CI, run a periodic checkup every 100 commits, show it in aw attention and aw doctor, add an overridable hard stop, and gate stale spec pointers at the runner merge check. Graduated to Set cihealth.
