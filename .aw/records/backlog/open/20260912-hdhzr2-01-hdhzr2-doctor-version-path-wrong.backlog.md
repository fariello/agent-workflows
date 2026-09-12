- Id: hdhzr2
- Status: open
- Set: hdhzr2
- Priority: high
- Work-Kind: bug
- Summary: aw doctor reads a nonexistent VERSION path (.aw/VERSION, .agents/VERSION) and reports 'not installed' on a correctly installed repo

## Workflow history
- 2026-09-12 created (aw backlog): Found by an upgrade rehearsal against a real 1.2.1 legacy repo (tools/aw_upgrade_test.py)

doctor.py reads the installed framework version from '.aw/VERSION' or '.agents/VERSION'. Neither is a real location: engine.read_installed_version probes '.aw/system/VERSION', '.aw/system/workflows/VERSION', then '.agents/workflows/VERSION' (engine.py read_installed_version). So doctor's version currency check always sees None.

MEASURED, on a rehearsal sandbox upgraded from a real 1.2.1 legacy repo (ansurv), where '.aw/system/VERSION' exists and contains 1.2.1:

    Version:     not installed (packaged: 1.3.0rc2.dev2553+g87759153) [not-installed]

and directly:

    engine.read_installed_version: 1.2.1
    doctor.installed_version: None

In THIS repo the wrong reading is masked because is_source_repo short-circuits the finding, which is why the suite never caught it. In a real target repo 'doctor.version-not-installed' fires on a correctly installed repo, so the one command a user runs to check install health misreports it.

FIX: read the version through the shared engine.read_installed_version rather than a second, divergent path list. A regression test should assert doctor reports the same version engine does, on a fixture with only '.aw/system/VERSION'.
