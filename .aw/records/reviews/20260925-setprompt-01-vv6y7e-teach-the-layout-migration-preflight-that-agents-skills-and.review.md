# Review: Teach the layout migration preflight that .agents/skills and the installer-written .aw files are known

- Subject-Id: vv6y7e
- Subject-Type: ipd
- Reviewed-At: 2026-09-25
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

All claims verified at HEAD `dd9e7e62`. The plan was committed and unchanged (last touched by
`f1eb09da`), so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent` reported
clean (exit 0) before review, and `--phase review-finalize --agent` reports clean (exit 0) after.

THE DIAGNOSIS IS CORRECT AND WAS REPRODUCED. On four committed scratch repos with `AW_HOME`
isolated: BASE dry-runs OK; BASE + `.agents/skills/assess/SKILL.md`, BASE + `.aw/.gitignore`, and
BASE + `.aw/setup-repo-needed.md` each raise `PreflightGateError` naming exactly
`agents:skills`, `partial-aw:.gitignore`, and `partial-aw:setup-repo-needed.md`. The `.aw/.gitignore`
case also fails with the REAL content `engine._ensure_aw_gitignore` writes, not only a stub.

THE DESIGN WAS PROTOTYPED, NOT JUST READ. On a scratch copy of the package with the E-02 branch
(`host-adapter-in-place` / `preserve`) and the E-03 branches (`skip`) applied, a combined shape
carrying all three triggers dry-runs, APPLIES with `leftover_disposition="remove"`, and ROLLS BACK
via `MigrationManager.rollback_migration()`, with all three paths byte-identical throughout and
`.aw/system/` created; `.agents/mystery.txt` still classifies `block-unknown`. The reasoning the
plan relies on holds in code: `execute_migration` skips any mapping whose `destination_root_class`
is `host-adapter-in-place` ("they are NEVER moved"), the map builder drops `skip` items before the
transaction, and `_handle_leftovers` walks only `_LEGACY_LEFTOVER_ROOTS = (".agents",
"workflow-artifacts")` with `_is_removable_leftover` already guarding the skills prefix.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Scope fence | plan `- Scope-Paths:`; `.aw/records/backlog/graduated/20260923-72qlya-01-...backlog.md` | Scope-Paths named the backlog item under `open/`, but it is already in `graduated/`, so finalize's scope reconciliation would treat the real path as out of scope. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Path corrected to `graduated/`. |
| PR-002 | MEDIUM | IN-SCOPE | Executability | `72qlya` history: 2026-09-25 note + `graduated` record naming `vv6y7e`; `aw backlog note --help` (`--message MESSAGE`) | E-05 instructed writing a note that is already written, with a `-m` flag the verb does not accept, which would fail or duplicate the record. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now confirms and pastes the existing records, adds a note only if missing, using `--message`. V-05 updated. |
| PR-003 | LOW | IN-SCOPE | Correctness | `layout_inventory._walk` yields `skills`, `skills/assess`, `skills/assess/SKILL.md` (probe) | E-02 described matching files under `skills/`, but the walker also yields the bare directory entries, all three of which fall to `block-unknown`. The `first == "skills"` test covers them, but the plan did not say so, so an executor could write a narrower match. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 states the branch covers the directory entries too. |
| PR-004 | LOW | UNDER-SCOPE | Testing | `rollback_migration` probe; `git log --diff-filter=D -- tests/test_layout_inventory_gitignore.py` -> `19313eed` | E-04 did not cover rollback, the other path that touches in-place items; and it described the existing coverage incompletely (a walker test was deleted by the trim). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added case (6) rollback; E-04, V-04 and the tests section updated; the deleted test is named. |
| PR-005 | LOW | IN-SCOPE | Plan executability | `layout_inventory._legacy_class`; its only use sets the informational `legacy_class` field; the preflight error pass reads `ownership`/`disposition` only | E-02 left "update the coarse root classifier only if it gates the preflight" to the executor. The repository answers it: it does not gate. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now says do not change `_legacy_class`, with the reason. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `_legacy_class` also learn `skills`? | No | Add a `skills` case returning a host-adapter class | `layout_inventory._legacy_class` feeds only the `legacy_class` item field; the unknown-owner error reads `ownership`/`disposition` | yes |
| D-2 | Is the plan's `skip` disposition for the two `.aw/` files safe on apply and rollback? | Yes, keep `skip` | `preserve` + `host-adapter-in-place` | scratch prototype: apply + rollback leave both byte-identical; map builder drops `skip` items; leftovers roots exclude `.aw` | yes |
