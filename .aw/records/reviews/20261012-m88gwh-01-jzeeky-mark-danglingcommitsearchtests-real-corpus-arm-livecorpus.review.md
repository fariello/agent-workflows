# Review findings: plan jzeeky

- Subject-Id: jzeeky
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `d795acb85` in an isolated review lane; plan committed and unchanged, no snapshot needed.
`aw ipd lint --phase author --agent` clean before semantic review; `--phase review-finalize` clean after.

Re-verified:
- `test_07_real_corpus_arm_conditional` body: `pathlib.Path.cwd()`, `git cat-file -e 0abc01d9`,
  `git merge-base --is-ancestor 0abc01d9 main`, then `find_dangling_commits_by_subject(repo_path, "8u6770")`.
- `tests/test_runner_shared.py` imports `unittest` but not `pytest`; no `pytest.mark` in the file.
- `git cat-file -t 0abc01d9` -> `commit` (`lifecycle(8u6770): finalize 8u6770 -> executed`); not an ancestor of
  `main` (exit 1); `git for-each-ref --contains` empty. Test currently passes: `1 passed` (1.18s call).
- Tests 01-06 build a synthetic repo via `_make_repo`: `7 passed` for the class.
- With `-m livecorpus` on the unmarked test today: `136 deselected`, exit 5, so V-02's "1 deselected" probe
  is only meaningful after E-01.
- Backlog `m88gwh` is `bug`, `Blocks-Release: next`, graduated to `jzeeky`; the plan inherits the gate.
- Sibling `vzk1iw` (to-review) also declares `tests/test_runner_shared.py` at a disjoint site.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Missing: OQ status, scope-as-declaration/`--scope-reason`, MUST-paste honesty rule, `aw ipd begin`, staged-set check, conditional runner/executor finalize ownership, and the inherited `Blocks-Release: next` handoff. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements. |
| PR-002 | MEDIUM | IN-SCOPE | E. Testing / baseline | E-02, V-02 "`N passed` summary with no failures" | Required a fully green bare suite with no baseline, so another party's failure would block a correct execution, and a passed-count drop of one (the deselected test) was not anticipated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02/V-02 now take a pre-edit bare baseline and require an identical failing-test set by name; V-02 states the expected exit 5 for the deselection probe. |
| PR-003 | LOW | IN-SCOPE | Project conventions | `pyproject.toml` `livecorpus` marker text ("asserts a property over EVERY artifact in this repository's own .aw/records/ tree") | Test 07 reads git objects and refs, not `.aw/records/`; the plan did not acknowledge the marker-description mismatch. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added a MARKER FIT convention note: the marker's operational reason applies, the backlog prescribes it, and the marker text is deliberately not amended. |
| PR-004 | LOW | IN-SCOPE | Evidence | F2 | F2 asserted the test "can flip" without the mechanism. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F2 now states the skip/fail conditions and the review re-measurement. |
| PR-005 | LOW | IN-SCOPE | Conventions | E-01 "beside `import unittest`" | Placing a third-party import inside the stdlib group departs from the precedent file's grouping. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now places `import pytest` as its own group before the first-party imports, and forbids touching the test body. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Use `livecorpus` despite its `.aw/records/`-specific description, or add a new marker / amend the text? | Use `livecorpus` unchanged | New marker (expands `addopts` and Makefile contract); amend marker text (shared contract, out of scope) | backlog `m88gwh` summary prescribes `livecorpus`; marker's stated operational reason (lane gate blocking) | yes |
| D-2 | Does overlap with `vzk1iw` on `tests/test_runner_shared.py` need a dependency edge? | No | Add an edge | disjoint sites; runner isolates worktrees (AGENTS.md runner section) | yes |
