# Review findings: plan mtdxiu

- Subject-Id: mtdxiu
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `5188004da` in an isolated review lane. The plan was committed and unchanged (lane input sha256 `a8c5fef3...` matches the tracked file), so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review and `--phase review-finalize` was clean after revisions.

Re-verified in a scratch target (`aw install . -y --preset private-target`, `AW_NO_REEXEC=1`, isolated `HOME`, worktree package on `PYTHONPATH`):
- F-01: `<stem>.data/notes.md` with YAML front matter -> `aw research index` "notes.md: name-invalid: name must include a '.<kind>' suffix before '.md'", exit 1. With bullet-style (non-YAML) front matter it is skipped quietly (exit 0).
- F-04: `aw attention --all --format json` -> `valid False`, `attention.missing-status` for both `<stem>.data/notes.md` and `<stem>.data/r.txt`.
- NEW F-10: a copy of the doc under its conformant name inside `<stem>.data/` -> `aw research index` "wrote ... (2 docs)" exit 0, and `aw find 5b1tk3` lists both files with "id6 5b1tk3 is claimed by 2 files of the SAME type, in different lifecycle directories".
- Code anchors: every `rglob("*.md")` walk the plan lists in `research_index`, `research_archive`, `research_refs`, `research_cmd` (4) and `artifact_adopt` resolves. `research_refs._refuse_uncontained_destination`, `research_refs._apply_renames`, `research_archive.apply_moves` (`RF._git_mv` on `m.old_path` only), `artifact_refs._boundaried`, `artifact_core.git_mv` (shutil fallback, parent mkdir), `engine.RETIRED_RESEARCH_README_HASHES`, `engine.classify_records_root_readme`, `check_engine.enrich_drift`, and `check_engine` delegation to `research_index.check_drift` all resolve. Spec sections 5.2, 5.6 and 5.7 exist. CHANGELOG has a "2.0.0 (pending)" section. All the listed regression test files exist.
- Type-agnostic walks that also enumerate research: `selectors._iter_md`, `check_engine._iter_type_files`, `cli.py` `for p in sorted(base.rglob("*.md"))` over `selectors.record_dirs`, `completion.py` and `artifact_refs` `for p in d.rglob("*.md")`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | UNDER-SCOPE | C. Architecture / A. Correctness | `selectors._iter_md` ("Walk `base` yielding *.md files"); `check_engine._iter_type_files`; scratch `aw find 5b1tk3` "claimed by 2 files of the SAME type" | E-02 made only the research-module walks companion-blind. The type-agnostic record walks behind `aw find`, every selector resolve, `aw check`, completion and the cross-type reference name set still see a `.md` inside a companion as a research record. So a doc copy kept as companion data duplicates the id6 and makes selectors ambiguous, which undermines the convention's goal. | C:Medium; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | Added E-10/V-10 (prune companion dirs in `selectors._iter_md`, filter the other listed walks through the same E-02 helper, re-grep at execution). Added F-10, test case (j), and the three modules to `- Scope-Paths:`. E-09 now depends on E-10. |
| PR-002 | LOW | IN-SCOPE | E. Testing | F-04 (`r.txt` flagged); E-09 (h) | Case (h) did not require a non-Markdown companion file, although attention flags those too. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Case (h) now includes `r.txt`. |
| PR-003 | LOW | IN-SCOPE | G. Live-artifact criteria | F-08 `find ... -name '*.data'` prints nothing | The "no migration needed" claim rests on a live count measured at authoring. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now re-runs the `find` at execution. |
| PR-004 | LOW | IN-SCOPE | Step 3 decision recording | OQ-01/OQ-02 `- Owner: none` | The resolved questions recorded no owner although the author made the choice. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Owner set to `plan author`. D-1 and D-2 are recorded below. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | The gate lacked an explicit human-approval line, and "in order" was ambiguous once E-10 was added. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added "Execute only after explicit human approval" and "dependency order (E-10 after E-02)". |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What shape should a companion take? | Sibling `<doc-stem>.data/` (the plan author's choice, kept). | `<id6>.data/`: survives a rename but sorts away from its doc and breaks the field workaround. | backlog `bh1cy5` body ("sibling directory named <report-stem>.data/"); spec `20260730-2152-01` clustering by name | yes |
| D-2 | Should an orphaned companion fail `--check`? | `warning` (fails). | `info` (advisory only): it would not satisfy the backlog's "--check flags orphans". | backlog `bh1cy5`; `artifact_core.drift_exit_code` exempts only `info` | yes |
| D-3 | Should the type-agnostic walks be fixed in this plan or in a separate child? | This plan (E-10), through the same helper. | A separate plan: that would ship a convention that `aw find` breaks, which contradicts the cohesion rationale. | F-10 scratch measurement; plan cohesion rationale | yes |
