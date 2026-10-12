# Review findings: plan 7sy2gm

- Subject-Id: 7sy2gm
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `1bcf4518f` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `artifact_core.git_mv` and `engine._git_mv` are as F-03/F-04 state (mkdir first, then `git mv`, then `shutil.move` on any nonzero exit); `engine` call sites at the legacy-artifact relocation and the tracked-file relocation loop.
- Callers: `artifact_rename` (2), `plans_archive`, `plans_refs`, `research_refs`, `research_archive`, `status_set`, `engine` (2). All but `status_set` compute both paths with `relative_to(repo_root)`.
- `status_set._apply_transition`: `rel_src = str(rec.path.relative_to(repo_root))` with `except ValueError: rel_src = str(rec.path)`, so absolute out-of-repo paths are passed for companion/home records.
- PROBE: a scratch repo with `.aw/config/project.json` `{"records_backend": "companion"}`; `record_producers.resolve_record_path("backlog", ...)` -> `<base>/repo.aw/records/backlog` (outside the repo). `aw specs new ... --apply` then `aw set to-review <spec> --no-commit` exited 0; a spy recorded `git_mv(<repo>, "<base>/repo.aw/records/specs/draft/...", "<base>/repo.aw/records/specs/to-review/...")`.
- PROTOTYPE, authored rule (both paths must be inside): the same `aw set to-review` on a second companion spec raised an uncaught `ValueError` ("is not in the subpath of") and the spec stayed in `draft/`.
- PROTOTYPE, boundary-crossing rule: tracked `a/t.md` -> `a/../../../ESC/x.md` refused, source intact, no `ESC` directory created; untracked `a/u.md` -> `b/u.md` moved; companion `aw set to-review` exit 0, spec in `to-review/`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / D. Anti-regression | `status_set._apply_transition` `except ValueError: rel_src = str(rec.path)`; companion probe and prototype above | The authored guard (both paths must be inside the repo) would make `aw set` crash with an uncaught `ValueError` on every repository using the companion or home records backend, where the record paths legitimately sit outside `repo_root`. The plan's F-06 claimed all callers pass in-repo paths. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01, Scope and Expected outcome now refuse only a move that crosses the repository boundary (or targets the root). New F-07 records the companion path, new OQ-02 records the demonstrated decision, and new E-03 cases (c2) and (g) pin the both-outside and companion end-to-end paths. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing | E-03 "(a)-(d) fail against the pre-change helper"; V-03 | The discrimination claim did not state which cases must pass both before and after, so a test that also broke companion moves would not have been caught. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and V-03 now state that (a), (b), (c) and (d) fail before the fix while (c2), (e), (f) and (g) pass both before and after. |
| PR-003 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate was missing several contract parts (listed in the resolution). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate now covers: an OQ status line, `aw ipd begin`, the staged-set check, scope as a declaration (`--scope-reason`/`--scope-ack`), the do-not-claim-done rule, who finalizes (runner or executor) with no hand `git mv`, base-commit attribution of suite failures, and the inherited `Blocks-Release` handoff for the already-graduated item. |
| PR-004 | LOW | IN-SCOPE | G. Traceability | `aw check all` `check.ipd-uncarried-obligation` [ERROR] on this plan | Both Deferred rows lacked a `Carrier:` or `Carrier-Declined:` line. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a `Carrier-Declined` line with a rationale to each row; `aw check all` now reports only the INFO lifecycle note. |
| PR-005 | LOW | IN-SCOPE | G. Evidence accuracy | F-06 "All compute destinations under the repo" | That claim was false for `status_set` (see PR-001). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-06 corrected to name `status_set` and point at F-07. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Refuse any out-of-repo path, or only a boundary-crossing move? | Only a boundary-crossing move, or a destination equal to the root | Both-inside rule (authored; crashes companion `aw set`); constrain both-outside moves to the resolved records root (needs project-context resolution inside a stdlib-only helper) | Review probe and both prototypes; `status_set._apply_transition` absolute-path fallback | yes |
| D-2 | Should the tracked in-repo non-escape `git mv` failure get a carrier? | Carrier-Declined with rationale, surfaced in the review report | File a backlog item now | No measured harm; installer pre-checks destination existence | yes |
