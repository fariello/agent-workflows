# Review findings: plan pua92o

- Subject-Id: pua92o
- Subject-Type: ipd
- Reviewed-At: 2026-10-08
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `215224c5f`. The plan was committed and byte-identical to the lane input (sha256 `22c66d53...`), so no pre-review snapshot. `- Kind: child`. `aw ipd lint --phase author --agent`: `clean`, 0 findings. `--phase review-finalize`: `clean` (`advisory`, one `IPD-Z602` text-density note on E-01; not an error).

Verified: `cli._nv_backend_args` "`sub.dir = getattr(args, "dir", None) or os.getcwd()`"; its two callers `cli._run_noun_verb` (backend loop) and `cli._run_check` (except-fallback via `at.resolve_backend(norm, "check")`); all 23 `artifact_types.TYPE_BACKENDS` entries, whose 11 backend modules each read the dir only as `resolve_verb_repo_root(getattr(args, "dir", None))`; `resolve_verb_repo_root` explicit-no-climb rule. Re-measured F-02 at this HEAD: root `aw index research --check --agent` gives `findings, exit 1, 265`; from `docs/` it gives `conforms, exit 0, 2`. `sjsb04`'s six sites are separate from this one (`_run_record_history`, `_run_graduation`, `_run_find`, `_run_search`, `_run_check`, `doctor.run`). Sequencing: `rlhmt9` already depends on `executed:pua92o` (its F-11), and this plan depends on `sjsb04`; no cycle.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Correctness; HOW demonstrated | Plan OQ-01 and E-01 (pass `str(resolve_verb_repo_root(None))`); backend modules all use `resolve_verb_repo_root(getattr(args, "dir", None))`; `jei45f` OQ-02 and `rlhmt9` E-item pass `bool(getattr(args, "dir", None))` as the explicit flag; `project_context.no_project_message(..., explicit=...)` | OQ-01 chose the resolved string on the premise that backends read `args.dir` as a string. Measured false. A resolved string also makes every bare call indistinguishable from an explicit `--dir`, so the sibling refusals reached through `_run_check`'s fallback would print the explicit-`--dir` text for a bare call outside a project. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | OQ-01 reversed to `None` with a demonstration (in-process patch from `docs/`: `conforms, exit 0` -> `findings, exit 1`). E-01 rewritten. |
| PR-002 | MEDIUM | IN-SCOPE | Test evidence strength | `.aw/.gitignore` "records/plans/INDEX.json", "records/research/INDEX.md"; E-02(b) used `git status --porcelain` | A preview that regenerated an index would pass the no-write check because the index files are ignored. `archive` was in Scope but absent from (b). | Overall:Low | FIXED | (b) now uses a byte-and-mtime snapshot of `.aw/records/` and covers `archive`. |
| PR-003 | LOW | UNDER-SCOPE | Anti-regression | `resolve_verb_repo_root` "If no project root is found, fall through to cwd" | No control for the bare no-project case, which the change must leave as it is. | Overall:Low | FIXED | Added assertion (d) with an isolated `HOME`. |
| PR-004 | LOW | IN-SCOPE | Stakeholder visibility | `cli._run_noun_verb` self-commit resolves the root from the original args; resolver docstring hazard 3 (`$HOME`) | The approval text did not say that the commit root already climbs (so the fix makes backend and commit agree), nor that bare write verbs inherit the resolver's `$HOME` property. | Overall:Low | FIXED | Added F-05 and one sentence to WHAT APPROVAL APPROVES. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Pass `None` or the resolved string for a bare call? | `None`. | Resolved string (author's choice). Rejected: false premise, and it erases the bare/explicit distinction the Set's refusals use. | Backend census; `jei45f` OQ-02; in-process demo in OQ-01. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
