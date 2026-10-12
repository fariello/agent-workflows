# Review findings: plan amt9fs

- Subject-Id: amt9fs
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `73b096f29`. The pending plan matched the sealed lane input byte for byte and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` and `--phase review-finalize` both reported `clean`. `- Kind: child`.

Evidence verified: `artifact_rename._rel_to_repo` (`agent_workflows/artifact_rename.py:49`) falls back to `path.as_posix()`; `doctor._normalize_rel_path` (`agent_workflows/doctor.py:1279`) neither resolves nor drops absolute out-of-root paths; `specs._RECORDS_SEGMENTS` and `specs.drift_location` (`agent_workflows/specs.py:318-352`); `check_engine._finding_rel_path` (`agent_workflows/check_engine.py:1125`) name-only fallback. All four modules already import `artifact_core`. Backlog `rd6ei9` exists (open). `docs/cli-output-contract.md:270` "Path Sanitization and Leak Posture" matches the quoted text. F-08's constraining tests reproduced: `62 passed`. `tests/test_repo_relative_posix.py` does not exist.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | A/D (in-root invariant) | Review run in a temp root, symlink `b.ipd.md -> a.ipd.md`: `doctor .aw/records/plans/pending/b.ipd.md`, `engine .../a.ipd.md`, `rename .../a.ipd.md`; `lnk.md -> <T>/out/tgt.md`: `doctor lnk.md`, `engine lnk.md`, `rename <T>/real/lnk.md` | E-01 step 2 said "resolve the path", which renders an in-root symlinked FILE as its target (or, for an out-of-root target, as a bare name or an absolute path). F-05's claim that in-root rendering already agrees did not hold for symlinked files, so the unified policy would have changed `doctor`'s in-root output, which the plan's own stop condition forbids. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | E-01 step 2 is now lexical-first: normalize, relativize against the lexical or resolved root, then retry with only the parent resolved, and never resolve the final component. A prototype gave the expected answer on 12 cases and matched `specs.drift_location` with no root on 7 inputs. Added F-10, the deltas in E-03 and E-04, E-06 cases and their mutation witnesses, and amended the stop condition. |
| PR-002 | MEDIUM | IN-SCOPE | E (validation safety) | V-06 `git stash push -- <paths>` then `git stash pop`; this lane is one of several worktrees of one repository, and `refs/stash` is shared across worktrees | A concurrent agent's stash operation could pop or drop the executor's stash and lose the implementation. The revert also covered only two of the three changed callers that F-10 now needs witnessed. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-06 now reverts with a scratch copy plus `git show HEAD:<path>`, includes `check_engine.py`, and requires `git diff --stat` before and after to prove the tree was restored. |
| PR-003 | LOW | UNDER-SCOPE | E (cross-platform tests) | `.github/workflows/tests.yml` matrix `os: [ubuntu-latest, macos-latest, windows-latest]` | E-06's symlink fixtures fail on Windows without privilege. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 now requires a symlink helper that raises `SkipTest` on `OSError`/`NotImplementedError`, so the non-symlink cases still run. |
| PR-004 | LOW | IN-SCOPE | G (execution contract) | Gate carried "STOP and do NOT widen into the F-09 helpers" (a scope-question stop, contrary to the 2026-09-01 ruling), no `--scope-reason`/`--scope-ack` declaration, no conditional finalize ownership, and a stale "carries NO Readiness" sentence; OQ `Owner: none`; V-06's `aw check all` count was not bound to the same session | The gate was incomplete per plan-review Step 4. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate: scope declaration, correctness-only stop conditions, honesty rule, runner versus hand finalize, backlog close by the runner. Set `Owner: plan author`. V-06 measures `aw check all` before and after in one session. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should an in-root symlinked file render as the link spelling or the resolved target? | The link spelling (lexical-first, parent-only resolution). | Fully resolve (today's `check_engine`/`artifact_rename` behavior; changes `doctor` in-root output and can leak or degrade an in-root link to a bare name). | Plan stop condition "STOP if any in-root rendering changes (F-05)"; `_core.git_mv` is given `src.relative_to(repo_root)` lexically (`agent_workflows/artifact_rename.py:876-878`); review prototype on 12 cases. | yes |
| D-2 | How should V-06 revert the helpers temporarily? | Scratch copy plus `git show HEAD:<path>`, then restore and diff. | `git stash` (worktree-shared `refs/stash`, unsafe with concurrent agents). | AGENTS.md "Shared checkout: you are not alone"; this run is one worktree of several. | yes |
