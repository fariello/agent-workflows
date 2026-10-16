# Review findings: plan fxbm7j

- Subject-Id: fxbm7j
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane after commit `9a37f42c8`. The plan was committed and unchanged, so no pre-review snapshot was taken. `aw ipd lint --phase author --agent`: `clean` (info `IPD-Z602`). Child plan. Dependencies `s07f73` (reviewed this sweep) and `6u755v` (approved, pending) are not executed, so `placement_switch.py` does not exist at HEAD; E-01's stop condition covers it.

Verified:
- Preset value mapping in E-03 matches `install_wizard.get_preset_defaults` (`private-target` records `target-tracked`/`target-git`; clean-target `home-untracked`/`untracked`) and `ProjectPolicy.__post_init__` (`repository-untracked` -> `target-ignored`/`ignored`); enum values in `project_schema`.
- F-02 precedence: `project_context.resolve_project_context` reads `merged_local_binding.get("records_backend")` before `project_policy_data.get("records_backend")`.
- F-03 reproduced: after the backlog bug, `project.json` read `home target-tracked target-git`.
- A `private-target --records-backend home` install writes 41 scaffold files under the home records root, 0 in-tree, and `.aw/.gitignore` already exists (so `records-to-target` needs no gitignore creation in the common case).
- `.aw/.gitignore` ignores `records/runs/`, supporting the fixture's ignored `runs/r1/state.json`.
- `6u755v` copy rule "refuse if the destination exists and is not hash-identical" and rollback "(3) ... delete every destination this transaction copied".

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | Rubric A (data integrity, rollback) | E-01 `destination-not-empty` "ignoring scaffold `.gitkeep`/`README.md` that the installer already wrote there"; `6u755v` E-03 copy "refuse if the destination exists and is not hash-identical"; review probe: after the bug, `<AW_HOME>/projects/repo-793064/records` held 41 pre-existing scaffold files | The planner exempted pre-existing scaffold destinations from the blocker but said nothing about what the copy and rollback do with them. A differing scaffold would refuse mid-copy despite a clean plan, and an identical pre-existing one, if journaled as copied, would be deleted by rollback, leaving the destination side changed after a "byte-identical" rollback. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01: a scaffold source whose destination pre-exists is a `discard` item; E-02: hash-identical pre-existing destinations are journaled `preexisting`, never `copied`, so rollback cannot delete them; E-05 adds case (10) and adjusts (9); V-05 demands its evidence; F-06 added. |
| PR-002 | LOW | IN-SCOPE | Rubric G (dead branch) | E-01 warning "for `repository` -> `repository-untracked`"; `project_context.resolve_project_context` maps both to `<repo>/.aw/records`; `s07f73` E-02 "that pair is `None` here" | That warning can never fire: Order 01 returns `None` for the pair, which this planner maps to `not-a-records-switch`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Warning scoped to `records-to-home`, with the reason stated. |
| PR-003 | LOW | IN-SCOPE | Rubric E (test precision) | E-05 case (8) "on a separate `local-only` request" | "Separate" could be read as a separate repository, whose project id and control dir differ, so the two journals would not collide and the test would not prove mutual blocking. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (8) now names the SAME repo and the shared control dir. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean` (info `IPD-Z602` only).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What happens to a scaffold source whose destination already exists? | `discard` the source; keep the destination untouched. | Overwrite (REJECTED: destroys bytes the transaction did not write, contradicts no-overwrite copy rule). Block (REJECTED: every home-placed project already has scaffold, so every switch-back would block). | `6u755v` E-03 copy rule; review probe of the home scaffold. | yes |
| D-2 | How does rollback avoid deleting pre-existing destinations? | Journal them `preexisting`; rollback deletes only `copied`. | Snapshot the destination tree (REJECTED: heavier, duplicates the journal). | `6u755v` rollback step (3) "every destination this transaction copied". | yes |
