# Review findings: plan 8d0qsg

- Subject-Id: 8d0qsg
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (LOW, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `550035bde`. The plan was committed and byte-identical to the lane
input, so no pre-review snapshot was needed. `aw ipd lint --phase author --agent`: `clean` before review;
`--phase review-finalize`: `clean` after revision. Not an orchestrator (`- Kind: child`), so S407/S408 do not apply.
The three instruments (`1ub8ex`, `nzzu8n`, `sk2rbf`) are `reviewed`, not yet built (`tools/` holds only
`lost_guard_census.py`), so their interfaces were taken from their reviewed plan text.

Demonstrations (temp dirs only, worktrees removed):
- `python3 tools/lost_guard_census.py --summary 19313eed`: `Uncited deleted files: 209 files holding 3585 removed functions`, 9.6s.
- Detached worktree of HEAD with the `19313eed^` blob of `tests/test_wtiso_taxonomy_freeze.py`, run with `nzzu8n`'s
  pytest flags: `2 failed, 5 passed`; both junit messages `ImportError: cannot import name 'wtiso_gate' from 'agent_workflows'`.
- `ast.walk` over the 209 uncited blobs for `tests.*` imports: `tests.test_run_analytics_export` (2, absent; itself in
  the uncited set), `tests.fixtures.run_analytics` (1, absent as module), `tests.support` (46, present).
- `aw research new ... --set uncitedaudit` dry run accepted the setid (would write `20261012-uncitedaudit-01-<id6>-uncited-trim-audit.findings.md`).
- `aw research index` / `--check` both exit 1 at this HEAD on pre-existing `7so8uz` `frontmatter-invalid`; INDEX files are gitignored (`.aw/.gitignore:50-51`).
- F-03 prefix cluster re-derived: 34 files, 993 functions, 27,316 lines; total 102,815 lines.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness (classification) | E-03 original; `nzzu8n` E-01 Classify; review replay of `tests/test_wtiso_taxonomy_freeze.py` | The mechanical rules keyed on replay `error-import`, but a function-local import of a vanished module reports `fail` with other tests passing, so known `subject-retired` cases would land in `fail-investigate` and flood Order 06 with false regressions. The verdicts also overlapped (e.g. a recreated file that passes) with no precedence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now applies five ordered rules; rule 2 reads failing-test junit messages, distinguishes file-wide from partial import failures, and keeps a partial file's passing-test reach. Scope verdict definitions aligned. |
| PR-002 | MEDIUM | UNDER-SCOPE | A correctness (environment vs product) | Review `ast.walk` over the 209 blobs (F-06) | Imports of `tests.*` helpers deleted by the same trim were unclassified; they are environment causes and would otherwise read as `subject-retired` or `fail-investigate`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rule 2 routes them to `replay-env-limited`; F-06 added. |
| PR-003 | MEDIUM | IN-SCOPE | C operability (index) | `.aw/.gitignore:50-51`; `aw research index --check` exit 1 at `550035bde` | E-04 committed "the doc and index" and demanded `index --check` conform; the index is gitignored and `--check` already fails on unrelated corpus diagnostics, so V-04 was unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Commit the doc only; evidence is `aw research find --id` plus no `--check` diagnostic naming the doc. Gate and Required tests swept. F-07 added. |
| PR-004 | MEDIUM | IN-SCOPE | A data integrity (same-tree) | `sk2rbf` E-04 stale-baseline refusal | Nothing pinned baseline, diff and replay to one HEAD; a commit in between makes `diff` refuse or line data incomparable. Coverage replays each file a second time, so verdicts can disagree. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 captures HEAD/status/worktrees; E-02 forbids intervening commits, makes `replay.json` authoritative and records the mismatch count; V-02 pastes `baseline.json` `head`. |
| PR-005 | MEDIUM | UNDER-SCOPE | G executability (evidence) | V-01..V-03 original | V-01 never ran the inventory JSON it compared; V-02 compared counts not path sets; V-03 did not check "exactly once" or function totals. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-items now demand pasted one-liners over the JSON and the doc table, path-set equality, and function-sum reconciliation; live counts re-derived, not the bar. |
| PR-006 | LOW | IN-SCOPE | G (traceability) | E-04 original; `sk2rbf` E-04 output shape; `anzu8q` E-01 | E-04 asked for "test names that reach" a function, which `diff.json` cannot supply (reach is per file). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Candidates grouped by function with files and exclusive counts; Order 06 reads test bodies itself. |
| PR-007 | LOW | IN-SCOPE | Evidence accuracy / gate | F-02 vs `1ub8ex` Concern; gate text; OQ-01 Owner | F-02 said 16 files import nothing and "1 imports only a vanished module" (reviewed `1ub8ex`: 13 and 3); gate lacked the paste-actual-output rule and fence wording; OQ-01 owner `none`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-02 corrected, F-05..F-07 added; gate itemized; owner set to `plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to classify a file where some tests fail on an import and others pass? | Treat import-failing tests as explained and classify by the rest. | Whole file `subject-retired`, rejected because it discards passing-test exclusive reach; whole file `fail-investigate`, rejected because the failure is explained. | Review replay (F-05). | yes |
| D-2 | Commit the research index? | No; commit the doc only. | Force-add the index, rejected because it is gitignored by design. | `.aw/records/research/README.md` "The index". | yes |
| D-3 | Which replay data decides verdicts when plain and coverage runs disagree? | `replay.json`; record mismatches. | Coverage run, rejected because coverage overhead can change timeouts. | `sk2rbf` E-01 (~1.8x overhead). | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
