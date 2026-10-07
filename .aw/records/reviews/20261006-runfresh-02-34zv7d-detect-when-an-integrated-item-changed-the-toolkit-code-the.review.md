# Review findings: plan 34zv7d

- Subject-Id: 34zv7d
- Subject-Type: ipd
- Reviewed-At: 2026-10-07
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261007T030816Z-4078927` at HEAD `bf7ed9ad1`. The plan was
committed and byte-identical to the sealed lane input (rev-3); no snapshot needed. `- Kind: child`, so `IPD-S407`
and `IPD-S408` do not apply. `aw ipd lint --phase author` clean before review; `review-finalize` clean after.

Re-measured: `git diff --name-only 3f4763b56 f723865c6 -- agent_workflows` lists 18 files (F-02 holds);
`runner_shared.initialize_run_core` writes the `"driver": {"id", "path", "sha256"}` block before `run-created`;
`runner_shared.runner_package_root` is `Path(__file__).resolve().parent.parent`; `agent_workflows/loaded_code.py`
and `tests/test_loaded_code.py` do not exist; the package has 188 `.py` files including the `agent_workflows/hooks/`
subpackage, hashed in about 0.1s by a review probe; 17 test files drive `initialize_run`; no test asserts an exact
`state["driver"]` key set. Order 03 (`re15ol`) calls `loaded_code.code_changed` from a process started by `resume`,
which never calls `initialize_run_core`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A correctness | E-01 "later calls return the stored record unchanged" including `is_target_checkout`; 17 test files call `initialize_run` for distinct fixture repos in one xdist worker | Memoizing the whole record freezes `is_target_checkout` to the first `repo` seen, so a later run in the same process gets another repository's classification. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Memoize only root, fingerprint, per-file map and time; compute `is_target_checkout` per call; test added; `_reset_for_tests()`. |
| PR-002 | HIGH | UNDER-SCOPE | A correctness / cross-child | re15ol Scope "calls `loaded_code.code_changed`" after a restart; `resume` never calls `initialize_run_core`; E-02 undefined with no memoized record | A resumed process would compare against nothing; behavior undefined, risking a restart loop or a crash. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | `code_changed` establishes the record on first call and returns `changed=False`; test and V-02 case added. |
| PR-003 | MEDIUM | IN-SCOPE | E testing | E-04 "building a fixture package tree" while E-01's API reads only `runner_shared.runner_package_root()` | The tests had no seam to point the detector at a fixture; the only route was editing the real package. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Keyword `package_root` on `loaded_code_record` and `code_changed`; E-04 uses it. |
| PR-004 | MEDIUM | IN-SCOPE | A correctness / interface | Scope "(c) `code_changed(state)`" vs E-02 "`code_changed(repo: Path)`" | Contradictory signatures inside the plan that Order 03 implements against. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope now says `code_changed(repo)`. |
| PR-005 | LOW | IN-SCOPE | D anti-regression / E | E-01 "hashing ... each path and its bytes"; E-03 makes every existing `initialize_run` test a non-target run | Undelimited path+bytes concatenation can collide; the suite-wide side effect and subpackage coverage were unstated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Per-file digest lines with separators; subpackage edit case; convention note on non-target side effect; `tests/test_hostdedup_third_host.py` added to the test command. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What does `code_changed` do with no memoized record? | Establish it and report unchanged | raise; report changed (restart loop risk) | re15ol resume path; `initialize_run_core` not called on resume | yes |
| D-2 | How should tests reach a fixture package? | `package_root` keyword | monkeypatch `runner_package_root` (still global); edit real package (forbidden) | E-04; P16 | yes |
