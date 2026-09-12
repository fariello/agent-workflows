# Review: ignore .aw/workflow-artifacts from the framework-owned gitignore, child vh14ku (Set wfartifacts)

- Subject-Id: vh14ku
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

VERIFIED BY EXECUTION. `'workflow-artifacts' in _AW_GITIGNORE_TEMPLATE` returns False, confirming the
central claim. The `/inbox/` precedent the plan leans on is present in the template, and its comment
records the measured reason a bare pattern is unsafe. `_ensure_aw_gitignore` is the only path reaching
an already-installed repo, and every prior pattern addition in that function carries a comment saying
so, which is exactly the shape this plan follows.

NO FINDINGS. This is the smallest and best-specified child in the Set: one anchored line in two places,
a re-sync that an existing guard test enforces, and four `git check-ignore` proofs including an
anchoring guard. The dependency ordering it asserts (this must precede Orders 01 and 03) is correct and
is the Set's load-bearing constraint.

WORTH NOTING FOR THE EXECUTOR, not a finding: this repo's ROOT `.gitignore:68` already ignores
`.aw/workflow-artifacts/`, so a `git check-ignore` run HERE can pass for the wrong reason. The plan
already anticipates this by requiring attribution to `.aw/.gitignore` via `-v`, which is the correct
guard and is why no finding is raised.

### Findings

NO ACTIONABLE FINDING. The table is deliberately EMPTY rather than carrying a `(none)` placeholder row:
`Severity` and `Decision` are typed enums, so a row using `-` for them parses as a malformed artifact
(`REV-P002`/`REV-P003`) and `approval_refusals` then reports an unresolved gating finding, which would
refuse this plan for a clerical reason. Measured at review: the placeholder row produced exactly that
refusal, and removing it cleared it.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should this child also ignore the legacy repo-root path? | NO, as the plan's own OQ-01 resolves. | Ignore both (rejected on mechanics: `.aw/.gitignore` patterns are `.aw/`-relative and CANNOT express a repo-root path, and reaching outside `.aw/` would mean editing the user's root `.gitignore`, which `engine.py`'s module docstring explicitly forbids). | The template's relative-path semantics; the installer's stated non-interference with user gitignores. | yes |
