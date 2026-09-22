- Id: hdhzr2
- Status: done
- Blocks-Release: next
- Set: hdhzr2
- Priority: high
- Work-Kind: bug
- Summary: aw doctor reads a nonexistent VERSION path (.aw/VERSION, .agents/VERSION) and reports 'not installed' on a correctly installed repo

## Workflow history
- 2026-09-22 set (aw backlog): closed by aw oc run: IPD h90ij1 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260912-doctorprobe-01-h90ij1-fix-aw-doctor-s-environment-probe-it-reads-three-nonexistent.ipd.md); evidence .aw/records/plans/executed/20260912-doctorprobe-01-h90ij1-fix-aw-doctor-s-environment-probe-it-reads-three-nonexistent.ipd.md
- 2026-09-12 graduated (aw set): Design handed off to a review-ready IPD authored from repo-verified root cause
- 2026-09-12 open (aw set): status set to open
- 2026-09-12 created (aw backlog): Found by an upgrade rehearsal against a real 1.2.1 legacy repo (tools/aw_upgrade_test.py)

doctor.py reads the installed framework version from '.aw/VERSION' or '.agents/VERSION'. Neither is a real location: engine.read_installed_version probes '.aw/system/VERSION', '.aw/system/workflows/VERSION', then '.agents/workflows/VERSION' (engine.py read_installed_version). So doctor's version currency check always sees None.

MEASURED, on a rehearsal sandbox upgraded from a real 1.2.1 legacy repo (ansurv), where '.aw/system/VERSION' exists and contains 1.2.1:

    Version:     not installed (packaged: 1.3.0rc2.dev2553+g87759153) [not-installed]

and directly:

    engine.read_installed_version: 1.2.1
    doctor.installed_version: None

In THIS repo the wrong reading is masked because is_source_repo short-circuits the finding, which is why the suite never caught it. In a real target repo 'doctor.version-not-installed' fires on a correctly installed repo, so the one command a user runs to check install health misreports it.

FIX: read the version through the shared engine.read_installed_version rather than a second, divergent path list. A regression test should assert doctor reports the same version engine does, on a fixture with only '.aw/system/VERSION'.
