# Review: retarget the installer and stop creating a repo-root run-scratch directory, child gzhd7t (Set wfartifacts)

- Subject-Id: gzhd7t
- Subject-Type: ipd
- Reviewed-At: 2026-09-12
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Readiness: go-pending-approval

## Round 1

Reviewed at HEAD `14b09376`. `aw ipd lint --phase author` CONFORMED with zero findings before semantic
review, and `--phase review-finalize` conformed after every revision.

SELF-REVIEW DISCLOSURE: the same agent and model authored this Set minutes earlier, so this is close to
a self-review and is worth less than an independent one. Its value therefore rests on what was
EXECUTED rather than reasoned: every numeric claim in every plan was re-measured against the
repository, which is what produced the findings below.

VERIFIED BY EXECUTION, not by reading. All four cited sites resolve: `ARTIFACTS_DIR = "workflow-artifacts/"`
at `:237`, the proposed-file entry at `:3292`, the repo-root path construction at `:5141`, and the
fallback literal beginning at `:5153`. The actual `mkdir` is at `:5168`, and the plan's prose says
"`:5141`, `:5168`" in F-1, so the citation is accurate. `check_gitignore`'s two branches at
`:2664-2676` read as quoted. The 42-references-across-10-files count re-verified exactly.

ONE FINDING, FIXED. PR-003 (register in the orchestrator's record): the plan said some tests "assert the
defect" without naming them, which is a real executability gap on a change that will break tests by
design. All five sites are now named in F-7 and in E-03, including the one that must be re-pointed
rather than deleted.

THE PLAN'S BEST FEATURE is that it makes the maintainer's report into a single assertion:
`(repo / "workflow-artifacts").exists()` is FALSE after a fresh install. That is falsifiable, cheap, and
exactly the reported symptom.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-003 | LOW | IN-SCOPE | G. Plan executability | `tests/test_installer.py:394`, `:406`, `:409-410`; `tests/test_awretrofit_install_selfheal.py:69`, `:78` | The plan asserted that some existing tests assert the defect but named none, leaving the executor to locate them on a change guaranteed to break tests. Verified true and located. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-7 naming all five sites; E-03 now names them inline and flags `test_installer.py:409` (a re-run preserving a user's CUSTOMIZED README) as correct behavior to re-point rather than delete. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | The plan leaves "retarget or remove `check_gitignore`" to the executor. Is an unresolved choice acceptable in an approved plan? | ACCEPTABLE, because the plan states the CONSTRAINT that matters and both options satisfy it. | Decide it here (rejected: both are defensible, the removal is a small API change needing a caller check that is cheaper to do while editing, and choosing arbitrarily would remove information the executor has and I do not); mark it blocking (rejected: nothing downstream depends on the answer). | E-02 forbids leaving a branch that can advise about a directory the installer no longer creates, and V-02 demands evidence for whichever path is taken. | yes |
