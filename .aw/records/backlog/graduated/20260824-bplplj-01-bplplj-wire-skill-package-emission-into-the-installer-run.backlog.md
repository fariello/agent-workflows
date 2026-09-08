- Id: bplplj
- Status: graduated
- Set: bplplj
- Priority: medium
- Work-Kind: followup
- Summary: Wire skill-package emission into the installer run() path across hosts

## Workflow history
- 2026-09-08 graduated (aw set): MOSTLY OBSOLETE, NARROWED. The installerskill Set (rldro6 / kvfsak) shipped in 5af28bbb, so this item's central claim that install_all writes only body+shim members is FALSE of the run path: install_into_repo merges skill members at engine.py:5697-5704 via _build_skill_members:5595 -> generate_adapter_bundle:5616. Verified by RUNNING kvfsak's tests (tests/test_installer_skill_emission.py: 10 passed), which cover resolver, namespace, prune scan, fresh install, idempotency, both orphan cases and manifest uninstall. The 'across hosts' clause was resolved to one shared .agents/skills dir by kvfsak D2/OQ-03. ONE gap survives: aw install --diff never calls _build_skill_members (engine.py:5856-5862), so the preview under-reports 90 files (measured: 52 shim, 90 skill, 0 overlap). kvfsak E-05's own text scopes itself to prune_stale, never the diff renderer, which is why the gap is real. Graduated to plan at61gc for that gap plus a preview/apply parity test.
- 2026-08-24 created (aw backlog): Wire skill-package emission into the installer run() path across hosts

MOSTLY OBSOLETE 2026-09-08, NARROWED TO ONE SURVIVING GAP. Read this before acting on the text below:
its central factual claim is no longer true.

WHAT LANDED. The `installerskill` Set (orchestrator `rldro6`, child `kvfsak`) shipped in `5af28bbb`
"feat(installer): emit generated skill packages in the install run path". So the claim that
`engine.install_all` "today writes only `body_members` + `shim_members`" is FALSE of the run path:
`install_into_repo` now builds `skill_members = _build_skill_members(...)` (`engine.py:5697`), merges
`generated_members = {**shim_members, **skill_members}` (`:5700`), and passes that merged map to both
`install_all` (`:5703`) and `prune_stale` (`:5704`). `_build_skill_members` (`:5595`) calls the
canonical `host_adapters.generate_adapter_bundle` (`:5616`) and returns `bundle.skill_files()` (`:5625`).

I DID NOT TAKE THE PLAN RECORD'S WORD FOR IT. Running `kvfsak`'s test file directly,
`python3 -m pytest tests/test_installer_skill_emission.py -o addopts=""`, gives `10 passed in 21.73s`,
covering the skills-dir resolver, the framework-namespace predicate, the prune scan,
fresh install plus manifest, an idempotent re-install, orphan prune (tracked AND untracked), and
manifest-driven uninstall. So every clause of this item except one is genuinely delivered and under
test, and re-planning any of it would be pure waste.

ALSO ALREADY RESOLVED: the "across hosts" clause. `kvfsak` (D2/OQ-03) ruled that skills land in ONE
shared host-consumption directory for BOTH layouts, `.agents/skills` (`host_adapters.py:60`,
`engine.resolve_skills_dir:174`), so there is no per-host emission left to wire. And uninstall needed no
separate member set: `uninstall_repo` is manifest-driven, so skill files are removed because
`write_file` recorded each one.

THE ONE SURVIVING GAP: `aw install --diff` DOES NOT SHOW SKILL MEMBERS. `show_install_diffs`
(`engine.py:3270`) has exactly ONE call site, `engine.py:5862`, and that branch builds only
`body_members` and `shim_members` and never calls `_build_skill_members`. Measured by calling the
production generators against this repository's own manifest: `shim members: 52`, `skill members: 90`,
`overlap: 0`. So the dry run that exists to show what an apply will write UNDER-REPORTS 90 files.

WHY THAT GAP IS REAL AND NOT SOMETHING I MISSED: this item named "install-diff tests" in scope and
`kvfsak` E-05 mentions install-diff, but E-05's stated deliverable is only "passing `generated_members`
(shim + skill) to `prune_stale`", and its V-05 evidence is re-install and orphan-prune output. The diff
RENDERER is named in neither. So the covering plan's own text shows it did not close this.

GRADUATED TO plan `at61gc` (`.aw/records/plans/pending/20260908-instdiff-01-at61gc-...ipd.md`, carrying
`- From-Backlog: bplplj`), scoped to that one gap plus a preview/apply parity test. Set `graduated`
rather than `done` because the code is not yet written; when `at61gc` executes, this item may close
`done`.

ORIGINAL ITEM TEXT FOLLOWS, uncorrected.

execset Order 05 (2h7777) proved skill/shim generation at the library level (build_skill_package digest parity + generate_shim_members drift-free) and exposed /exec-set via the existing shim path, but did NOT wire skill-package emission (host_adapters.generate_adapter_bundle / build_skill_package .to_files()) into engine.install_all (which today writes only body_members + shim_members). Wiring skill emission into the installer is a cross-cutting installer-output change touching all hosts + uninstall + idempotency + install-diff tests; it was deliberately kept out of the packaging Order's scope (D21-2h7777-D2). Follow-up: wire it and extend the installer tests.
