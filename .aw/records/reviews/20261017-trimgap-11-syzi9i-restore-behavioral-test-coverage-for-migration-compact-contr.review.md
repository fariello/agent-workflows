# Review findings: plan syzi9i

- Subject-Id: syzi9i
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (LOW, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `711302a31`. The plan was already committed and unchanged, so the pre-review snapshot was skipped. `aw ipd lint --phase author --agent`: `clean`, 0 findings. Child plan (Set `trimgap`, Order 11), test-only.

Verified in the lane (scratch test file `tests/test_zz_scratch_syzi9i.py` and scratch mutations of `agent_workflows/migration_compact.py`, all removed or restored; `git diff agent_workflows/` empty; `git status` clean apart from the plan and this record):
- `19313eed^:tests/test_migration_compact_shims.py` exists with the four classes and 22 tests the plan names, including the two `assertIs` re-export lines E-01 removes; no file at HEAD. Unchanged: `22 passed in 0.48s`.
- The 24 `b1mx2w` keys and operators match F-01. Sweep against the recovered file: 21 KILLED; `TypedContract.to_dict`, `CompactPackage.to_dict`, `CompactProjection.to_dict` (`return-none`) SURVIVED with `22 passed`.
- The planned E-02 `verify` `to_dict` test and the E-05 projection assertions, appended as a scratch class, killed all three (`1 failed, 23 passed` each).
- Every ADD expected value in E-02 to E-05 reproduced by direct call (recorded in plan F-07).

The plan's design is sound: it already targeted the three uncaught keys. What was missing was any step that proves the Goal.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | E. Testing / Goal verification | plan Goal ("Done means a `return-none`, `negate-return` or `raise` mutation ... of any of them turns a routine test red"); V-02..V-05 spot-check about 6 keys and rely on coverage | Coverage shows that code ran, not that a test would catch a change to it. The review sweep found three keys that coverage reports as executed but that no recovered test catches. The plan's additions do catch them, but nothing in the plan required showing that, so a weaker executor's version of these tests could leave them uncaught without anyone noticing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added E-06 and V-06: a sweep of all 24 keys, each with its `b1mx2w` operator. Any mutation no test catches must be fixed, not reported. V-02 and V-05 now include the three `return None` mutations. Coverage moved to V-06. Added F-07. |
| PR-002 | LOW | IN-SCOPE | Validation (command cannot produce the value) | V-01 `--collect-only -q \| rg -c test_migration_compact_shims` | `--collect-only -q` prints one `path: N` line per file, so `rg -c` prints `1` (same as `jy7439` PR-002). | all Low | FIXED | V-01 now asks for the `path: N` line, and says to report a `CORE TIER BUDGET EXCEEDED` warning instead of un-marking tests (backlog `o58dro`). |
| PR-003 | LOW | IN-SCOPE | Executability | E-01 | No rule for what to do if a recovered test fails at execution HEAD. | all Low | FIXED | Added the Set's rule: decide whether the change is intended or a regression; for a regression, use `xfail(strict=True)` plus a gated bug item. |
| PR-004 | LOW | IN-SCOPE | Execution contract | gate paragraph | The gate had no honesty rule, no staged-file check, no rule for who runs finalize, and no scope-fence wording. It also used the placeholder `aw commit <plan>`. | all Low | FIXED | Rewrote the gate as an execution contract with `aw commit syzi9i`. |

`aw ipd lint --phase review-finalize --agent`: `clean`, 0 findings.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the plan prove its Goal for all 24 keys? | A full sweep with each key's assigned `b1mx2w` operator (E-06/V-06) | Keep spot-checks plus coverage (coverage shows only that code ran; the review sweep found 3 uncaught keys) | plan Goal; `b1mx2w` `## Rollup mutation results`; F-07 | yes |
| D-2 | Keep V-01's `rg -n "assertIs\(" tests/test_migration_compact_shims.py` demand? | Keep | Drop it as a structural check | It searches the TEST file to confirm E-01 removed the identity pins; it does not test production structure, so P16 does not forbid it | yes |
| D-3 | Where may the E-06 sweep script live? | A gitignored scratch path (e.g. `.aw/state/`), never committed | Commit it as a tool (over-scope) | `.aw/.gitignore` `/state/`; Scope-Paths | yes |
