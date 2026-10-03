# Review: Persist a portable close-evidence citation on both setter spellings

- Subject-Id: byzkr7
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

The target plan was committed and unchanged at lane HEAD `127464310`, so the pre-review snapshot was skipped. `aw ipd lint --phase author` and `--phase review-finalize` were both clean.

Each scratch repo was built from `tests/test_backlog_positional_close_gate._setup_repo` / `_create_item`, with `cutovers.release_gate_at_rest` resolving `20260101`, git-committed, and judged by `check_release_gate_consistency(at_rest=True)`. Results:

- **`--status` close:** wrote the Close-Evidence bullet and produced 0 findings.
- **Positional close:** wrote no bullet and produced 1 `check.blocking-item-closed-without-gate` (F-02 and F-03 confirmed).
- **Absolute citation:** stored verbatim. It read clean in place, but `False error None` after a copytree (F-05).
- **Space citation:** rc 0, bullet written, `validate_item` returned `[]`, and 1 finding (F-07).

Every cited symbol was located: `backlog.set_close_evidence_line` (single caller `backlog.run_set`), `_CLOSE_EVIDENCE_RE` `.+?` against `check_engine._META_CLOSE_EVIDENCE_RE` `\S+`, `resolve_evidence_artifact`, and `status_set.run_set_command`'s pre-flight `evaluate_blocking_close` with the verdict discarded.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Plan executability (G) | plan "Proposed changes" items 3-6 cited (E-04)..(E-07); Conventions "E-05 tests READABILITY"; Spec sync "E-07 amends"; Deferred "E-07 here"; Required tests "E-04 touches" | The cross-references used the pre-split numbering, so an executor would map reader, validator, tests and docs to the wrong E-items. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Renumbered every reference to match E-02..E-09. |
| PR-002 | MEDIUM | UNDER-SCOPE | Correctness (A) | agent_workflows/check_engine.py `evaluate_blocking_close` `_META_CLOSE_EVIDENCE_RE.search(text)`, compared with `_read_blocks_release` over `_metadata_region`; probe body-quoted -> `True ok SATISFIED`, absent -> `False error None` | E-05 widens a reader that also scans the whole file, so a quoted bullet in the body can legitimize a close at rest. Widening without bounding keeps that hole. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now bounds the reader to `_metadata_region`. Its expected outcome and V-05 each gained a bounding pair. Added F-11. |
| PR-003 | MEDIUM | IN-SCOPE | Correctness (A) | agent_workflows/backlog.py `run_set` `gate_root` / `--gate-dir`; runner_shared `close_backlog_item` | E-02 did not say which root to normalize against. On `--gate-dir` lane closes, the predicate resolves against main (`gate_root`), not `repo_root`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now names the root the predicate resolved against on each spelling. |
| PR-004 | MEDIUM | IN-SCOPE | Validation safety and live-artifact criteria (G) | V-07 "stash the non-test edits"; V-06 "893 backlog records"; Required tests "compare counts" | `git stash` in a shared checkout can capture a co-worker's work. Several bars depended on live counts. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced stash with a worktree, or with reverting only your own patch. Bars now compare same-session finding and failure sets by name and location. |
| PR-005 | MEDIUM | UNDER-SCOPE | Execution contract (G) and security (B) | plan gate; E-08 leak fixture | The gate lacked `aw ipd begin`, a scope fence, conditional finalize ownership, an id6 commit, and the `gh409m` close path. A literal `/home/<user>` string in a new test file would trip the tracked-tree `local-leaks` scan. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all gate elements. E-08 must now build the home path from runtime fragments, as `tests/test_local_leaks.py` does, with no allowlist entry. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should E-05 also bound the reader to the metadata region? | Yes. Bound it while widening. | Widen only (leaves the quoted-bullet hole); defer to b92m14 (which covers Blocks-Release only) | review probe; `check_engine._read_blocks_release` idiom | yes |
| D-2 | Which root should E-02 normalize against? | The root the predicate resolved against (`gate_root` or `repo_root`) | Always `repo_root` | `backlog.run_set` gate_root; `runner_shared.close_backlog_item` | yes |
