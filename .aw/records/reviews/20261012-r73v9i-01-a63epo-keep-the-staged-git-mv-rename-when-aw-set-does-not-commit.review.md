# Review findings: plan a63epo

- Subject-Id: a63epo
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `e5ab6af3d` in an isolated review lane. The plan was committed and unchanged (`d937df46b`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- `status_set._offer_self_commit` runs `_gch._git(repo_root, ["reset", "--quiet", "HEAD", "--", *paths])` before `offer_commit` under the "jgcm68 D2" comment (F-02).
- `status_set.apply_status_change` relocates with `_core.git_mv`, then `_core.atomic_write`s the destination (hence `RM`, F-04).
- `git_commit_helper.offer_commit` returns `skipped` for `no_commit` and for the non-interactive branch before any staging; its `add_paths` filter uses `_in_index` (F-03).
- Scratch-repo reproduction (probe under gitignored `.aw/state/`): pre-fix backlog `--no-commit` and no-flag both give ` D open/...` plus `?? done/`; with the reset suppressed both give `RM open/... -> done/...`; `--commit` commits cleanly either way (F-01, F-04 confirmed).
- `tests/test_set_dispatch_parity.py::test_backlog_relocation_porcelain_shape_agreement` asserts the defect shape (F-05). The only other ` D`/`??` porcelain assert in `tests/test_git_commit_helper.py` builds its fixture by hand, not via `aw set`.
- Spec `wy9aru` AC-5 and Section 4.2 exist as cited.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing | `status_set.apply_status_change` (shared by plans); review probe: `aw ipd set superseded <plan> --no-commit` and `aw set not-executed <plan> --no-commit` leave ` D pending/...` plus `?? superseded/` pre-fix, `RM` after | The Concern and the E-05 CHANGELOG line name `aw ipd set`, but E-04 tested only backlog and specs, so a user-facing claim had no test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-07 and E-04 (c) (plan relocation via `aw ipd set`); Scope and Scope check say three record types. |
| PR-002 | MEDIUM | UNDER-SCOPE | D. Anti-regression | `runner_shared.close_backlog_item` appends `--no-commit`; `runner_shared.commit_backlog_close` parses `git status --porcelain -uall` and returns None on fewer than two paths | The fix changes the porcelain shape seen by the non-isolated runner close, an in-repo consumer the plan did not name. Measured at review that it handles `RM` (commits `R075`), but nothing pinned it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-08, E-06 and V-06: outcome test driving `aw backlog set --no-commit` then `commit_backlog_close`, asserting a single `R` commit. |
| PR-003 | MEDIUM | IN-SCOPE | E. Testing precision | `status_set._offer_self_commit` maps bare `--yes` to `assume_yes=True`; `git_commit_helper._is_interactive`; existing test passes `--yes` | E-04 (a) said "NO commit flag" but did not forbid `--yes`, which the sibling test passes and which would make the "non-interactive" test commit instead of skip, so it would not exercise the defect path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 (a) now requires no `--yes` and forcing `AW_NONINTERACTIVE=1` via `mock.patch.dict`; V-04 demands the diff shows both. |
| PR-004 | LOW | IN-SCOPE | E. Testing precision | review probe: `?? .aw/records/history.jsonl` remains after every `--commit` in the parity fixture | E-04's "no remaining entry" porcelain assertion would fail on the untracked history sidecar the fixture leaves (no `.gitignore`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 (d) now asserts no TRACKED entry for either half and excludes the sidecar explicitly. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked the OQ status line, a scope-fence declaration, the MUST-paste honesty rule, `aw ipd begin`, and the conditional runner/executor finalize ownership. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All elements added; the fence is a declaration with `--scope-reason`/`--scope-ack`, not a stop. E-01 also now says probe scripts go under gitignored `.aw/state/`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Cover plan relocations, or drop `aw ipd set` from the CHANGELOG claim? | Cover them (E-04 (c)) | Narrow the CHANGELOG to backlog and specs (understates a real fix) | review probe F-07; `status_set.apply_status_change` is shared by all three types | yes |
| D-2 | Pin the runner consumer, or rely on the existing runner tests? | Add one outcome test (E-06) | Rely on `tests/test_backlog_close_host_label.py` (it fakes `commit_backlog_close`, so it never sees real porcelain) | `tests/test_backlog_close_host_label.py` monkeypatches `commit_backlog_close`; review probe F-08 | yes |
| D-3 | Keep the deferral of the same pre-reset in `cli._offer_records_commit`, `plans_archive`, `research_archive`? | Keep deferred as the author wrote it | Fold them in (unmeasured, other verbs, outside the backlog item) | backlog `r73v9i` names `aw set` only; plan Deferred section | yes |
