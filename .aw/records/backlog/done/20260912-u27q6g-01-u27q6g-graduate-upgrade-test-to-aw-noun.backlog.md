- Id: u27q6g
- Status: done
- Graduated-To: upgrehearse
- Set: u27q6g
- Priority: low
- Work-Kind: feature
- Summary: Graduate tools/aw_upgrade_test.py to a first-class aw noun once the rehearsal workflow has proven itself

## Workflow history
- 2026-09-26 set (aw backlog): closed by aw oc run: IPD 8ud1is executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20260925-upgrehearse-01-8ud1is-restore-the-upgrade-rehearsal-safety-tests-and-graduate-the.ipd.md); evidence .aw/records/plans/executed/20260925-upgrehearse-01-8ud1is-restore-the-upgrade-rehearsal-safety-tests-and-graduate-the.ipd.md
- 2026-09-25 graduated (aw set): graduated into upgrehearse (plan 8ud1is); verified live at 8e74dcac
- 2026-09-12 created (aw backlog): Deliberate follow-up: shipped as a maintainer script first, per the maintainer's script-now-promote-later decision

tools/aw_upgrade_test.py currently lives in tools/ as a maintainer rehearsal rig. It is arguably useful to END USERS too, who would want to rehearse an upgrade against a copy of their own repo before running it for real.

PROMOTION WORK, if and when the workflow proves itself:
1. Move the logic into the package (e.g. agent_workflows/upgrade_test.py) and leave tools/aw_upgrade_test.py as a thin delegating shim, matching how pwatch and agy_run were graduated.
2. Register an 'aw upgrade-test' noun with sub-verbs (list/new/sandboxes/probe/env/clean) in cli._build_parser, dispatch in main().
3. Declare every leaf in command_surface.COMMAND_INVENTORY, or tests/test_command_surface_declarations.py and tests/test_cli_conformance_matrix.py fail CI on the undeclared leaves.
4. Adopt the dual-audience output contract (--agent JSONL, --json, exit 0 clean / 1 findings / 2 cannot-run). The tool already has a --json path to build on.
5. Decide the DEFAULT SANDBOX ROOT for a non-maintainer: the harness currently derives it from the operator's first configured search root (a 'tmp/aw-upgrade-tests' subdirectory, chosen to sit outside the discovery scan) with an AW_UPGRADE_TEST_ROOT override. That is right for a maintainer but assumes a search root exists, so a shipped version should prefer the state root or a temp dir.

DEFER RATIONALE: the surface obligations are real, and the rehearsal workflow should earn them by being used first. The four safety invariants (never mutate the source, never push, never pollute the real inventory, never delete a non-sandbox) are already covered by tests/test_aw_upgrade_test.py, so promotion is mostly wiring, not re-establishing safety.

A SYNTHETIC BASELINE is the other half of this, tracked here so it is not lost: the harness currently rehearses only from a real repo's CURRENT state, which on this server is a single data point (1.2.1, legacy layout). Installing an OLD git tag into a throwaway repo and then upgrading it with the current code would give arbitrary version pairs and a CI-runnable upgrade test. The internals were kept source-agnostic so this can be added without rework.
