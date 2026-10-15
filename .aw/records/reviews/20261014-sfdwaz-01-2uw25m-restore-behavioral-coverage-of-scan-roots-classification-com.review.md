# Review: Restore behavioral coverage of SCAN_ROOTS classification completeness

- Subject-Id: 2uw25m
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `de5c53233`, clean tree, target plan committed unchanged (snapshot skipped).
`aw ipd lint --phase author` conforming before revisions; `--phase review-finalize` conforming after.

Verified TRUE: `agent_workflows/artifact_core.py` comment above `SCAN_ROOTS` still reads "no live guard
currently asserts this"; `rg classify_rel` returns empty (F-01); a one-off probe of
`attention._classify_tree` over `SCAN_ROOTS` returns `None` for exactly `DECISIONS.md`, `README.md`,
`ARCHITECTURE.md`, `.agents/docs` (F-02); `.agents/docs/specs/x.spec.md` and `.agents/docs/research/y.md`
classify to `specs`/`research`; a temp repo holding `TODO.md` + the three root docs + `.agents/docs/note.md`
yields no `TODO.md` from `iter_scan_files` and no `TODO.md` item or drift from `attention.scan`; the
deleted class content matches F-03 (`git show 19313eed7^:tests/test_artifact_core.py`); commits
`b8a40fdf4` and `19313eed7` resolve.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | A. Correctness (wrong expected outcome) | Probe at `de5c53233`: `sorted(...)` over `SCAN_ROOTS + ("TODO.md", ".aw/records/no-such-tree")` -> `['.aw/records/no-such-tree', 'TODO.md']` | E-03 Expected outcome required exactly `["TODO.md", ".aw/records/no-such-tree"]` "in sorted order"; Python sorts `.` before `T`, so an executor writing the assertion as specified gets a failing test. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Mutation test moved to new E-05 with the measured order `[".aw/records/no-such-tree", "TODO.md"]`. |
| PR-002 | MEDIUM | IN-SCOPE | G. Right-sizing | Plan E-03 (two tests, two surfaces: `iter_scan_files`/`scan` outcome vs. offender-helper mutation) | E-03 bundled two independent deliverables and test-surfaces under one E/V pair. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Split: E-03 keeps `test_todo_md_is_not_scanned`; new E-05/V-05 owns `test_the_invariant_detects_an_unclassified_root` via a module-level offender helper. Watermark 04 -> 05. |
| PR-003 | LOW | IN-SCOPE | A. Correctness (ambiguous mechanism) | `artifact_core.iter_scan_files` returns sorted file `Path`s, not roots | E-02 said each exempted name "is still yielded as a scan root" by `iter_scan_files`; it yields files, so for `.agents/docs` the observation must be a child under `<name>/`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 now states the equals-or-under-`<name>/` assertion and the fixture shape. |
| PR-004 | LOW | IN-SCOPE | E. Testing (P16 proof is noisy) | `rg "inspect\|ast\."` matches the word "inspect" and substrings like "last." | V-01's P16 grep would match ordinary prose/identifiers, making "no match" unachievable and the check uninterpretable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 now uses a word-bounded alternation over `inspect`, `import ast`, `ast.`, `getsource` and `read_text(` with a stated expectation. |
| PR-005 | LOW | IN-SCOPE | G. Live-artifact criteria convention | Plan V-01..V-03 bars on test function names and V-03 on `4 passed` | Test names and collected counts are test-organization artifacts and may not be a V bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01..V-03, V-05 now demand the pinned behavior (names are pointers); V-03 requires zero failures with the count re-derived. V-02 adds a negative demonstration that the exemption guard fails on a stale name; V-04 additionally requires the comment keep `19313eed` and the "Do not re-add `TODO.md`" instruction. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Target `classify_rel` (as the backlog names) or `attention._classify_tree`? | Keep the plan's `_classify_tree` (OQ-01 resolution confirmed). | Target `classify_rel`: rejected, symbol does not exist (`rg classify_rel` empty). | `agent_workflows/attention.py` `_classify_tree`; deleted test at `19313eed7^` calls it | yes |
| D-2 | Fix the E-03 sort-order defect by changing the expected list or by asserting a set? | Keep `sorted` list equality with the measured order. | Set equality: rejected, loses nothing material but the deleted test's precedent and the E-01 helper both produce sorted lists. | Probe output at `de5c53233` | yes |
