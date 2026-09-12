- Id: ygtykn
- Status: open
- Set: ygtykn
- Priority: medium
- Work-Kind: bug
- Summary: An upgrade stamps the SOURCE tree's baked VERSION file, so every install from a dev checkout writes a stale version and the manifest agrees

## Workflow history
- 2026-09-12 created (aw backlog): Found by an upgrade rehearsal against real 1.2.1 legacy repos (tools/aw_upgrade_test.py)

MEASURED on nine real repos upgraded from 1.2.1 with the current checkout (packaged version 1.3.0rc2.dev2553+g87759153):

    installed VERSION after upgrade: 1.2.1
    manifest installed_version:      1.2.1
    packaged/running version:        1.3.0rc2.dev2553+g87759153

The installed VERSION is copied from the source tree's baked '.aw/system/VERSION' file, which in this checkout still reads 1.2.1 because 'make version-file' has not been re-run since the last release. So an install performed from a dev checkout stamps a version that does not describe the code it just installed, and the manifest records the same wrong number.

WHY IT MATTERS BEYOND COSMETICS: versioning.status() compares installed against packaged to classify a repo as current/stale/ahead, and that classification drives 'aw list-repos', 'aw status', doctor's currency check, and the would-downgrade preflight warning. A wrong stamp therefore makes a freshly upgraded repo report STALE, which is exactly what 'aw list-repos' shows for all 31 repos here. Re-running the installer will not clear it.

Note this is arguably correct for a RELEASE install (bake-then-tag means a tagged tree's VERSION equals its tag), so the fix is a judgement about what a dev-checkout install should stamp: the resolved running version, or the baked file with a loud warning that they disagree. Worth deciding rather than leaving implicit, since it is the difference between 'stale' being meaningful and being noise.

REPRODUCE: tools/aw_upgrade_test.py new <repo> -y -- --to-aw, then read the version-unchanged and manifest-version-unchanged observations.
