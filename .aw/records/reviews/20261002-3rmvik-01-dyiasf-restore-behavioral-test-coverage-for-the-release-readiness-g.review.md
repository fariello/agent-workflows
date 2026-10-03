# Review: Restore behavioral test coverage for the release-readiness gates and the GO / NO-GO aggregation

- Subject-Id: dyiasf
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS

## Round 1

The plan was committed and unchanged (`883e96274`), so the pre-review snapshot was skipped. `aw ipd lint --phase author` was clean before edits, and `--phase review-finalize` was clean after them.

Re-verified at lane HEAD `3d4ad1a4d`. All probes ran outside the tracked tree, and no production file was edited.

- `rr.aggregate([]).verdict` returns `GO`. F-06 reproduces.
- On a `git init` tree under `/tmp/opencode` holding only a CHANGELOG, `versioning.resolve_version` returns `'unknown'` and `gate_changelog_versioning` returns `passed=True` with `version='unknown'`. F-05 reproduces.
- On a CHANGELOG-only tree under this worktree's gitignored `tmp/`, the gate resolves the ENCLOSING repository's version `'1.3.0rc2.dev7711+g3d4ad1a4d'`. With `GIT_CEILING_DIRECTORIES` set to the tree's parent, it returns `'unknown'` instead.
- With `subprocess.run` patched to record calls and raise, `build_report(..., run_subprocess_gates=False)` records exactly one call, `['git', 'describe', ...]`. When `.aw/system/VERSION` is present it still returns `GO`. With a CHANGELOG-only root it returns `NO-GO` with `failing_gates=['changelog_versioning']`.
- `FORBIDDEN_RELEASE_ACTIONS` is `('tag', 'publish', 'deploy', 'push', 'release', 'upload')`.
- `ThresholdPolicy().thresholds` is a dict keyed `low`/`medium`/`high`/`destructive_gated`. Assigning `dataclasses.replace(entry, max_critical_escapes=1)` yields `violations` that name `low`.
- The deleted file has 20 `def test_` functions, 9 classes and `pytestmark = pytest.mark.slow`.
- The carriers `r4a4ab`, `usggph`, `tj9dq9`, `6bolin`, `bxnhdj`, `8jeh4x` and `3rmvik` all resolve. `wix4xe` is pending and touches `gate_docs_checks`/`build_report` `doc_findings` only.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Reachability / testing (E, G) | plan E-07 and V-07 "spawns NO child process at all"; `release_readiness.gate_changelog_versioning` -> `versioning._git_describe` `subprocess.run(["git","describe",...])` | The E-07 replacement arm cannot pass on correct code. `build_report(run_subprocess_gates=False)` still spawns `git describe` through the changelog gate. Patching `subprocess.run` to raise does not abort the run, because the `OSError` is caught and the gate degrades, so a "no spawn" assertion is simply false. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with an allowlist recorder: every recorded argv must begin `git describe`. V-07 now requires the recorded list to be pasted and rejects a no-spawn assertion. Stale wording swept from proposed changes and the accounting. |
| PR-002 | MEDIUM | IN-SCOPE | Test hermeticity (E) | plan E-03 sentinel arm "non-git tree"; `versioning._git_describe` runs with `cwd=repo_root` | git walks up to any enclosing repository. Wherever `tmp_path` lands inside a checkout, the sentinel arm resolves a real version and stops exercising F-05, and the GO arm's behavior shifts with it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires `GIT_CEILING_DIRECTORIES` via `monkeypatch` for every synthetic tree in E-03, E-05 and E-07, citing the measurement. |
| PR-003 | LOW | IN-SCOPE | P16 / validation bar | plan E-01 Expected outcome "`rg -c 'release_readiness'` ... is non-zero" | A substring count over the test file is a symbol-census bar, which AGENTS.md rules out as a correctness proxy. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with per-gate pass and fail arms that assert the evidence key. |
| PR-004 | LOW | UNDER-SCOPE | Executability (G) | plan E-05 "otherwise-clean call over a synthetic `repo_root` yields GO" | The plan did not state what that root must contain. A CHANGELOG-only root gives NO-GO on `changelog_versioning` (measured). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires a CHANGELOG `##` entry plus `.aw/system/VERSION` under the E-03 ceiling. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the deleted `git tag --list` arm's intent be replaced, given the decision path does spawn `git describe`? | An allowlist recorder: every argv starts `git describe` | Stub `versioning.resolve_version` and keep the no-spawn claim (that hides the real call path); drop the arm (loses the invariant) | Measured recorder output `[['git', 'describe', ...]]` | yes |
| D-2 | How do we make "non-git" synthetic trees hermetic? | `GIT_CEILING_DIRECTORIES` via `monkeypatch` | Stub `_git_describe` (bypasses the code under test); rely on `/tmp` placement (environment-dependent) | Measured ceiling vs. no-ceiling probe | yes |

### Open questions carried

- OQ-02 (non-blocking, owner human): whether the subprocess-gate synthetic arms belong in this plan. This is a scope call that belongs to the maintainer, so it is left open. Under the 2026-09-10 ruling it does not make the plan NO-GO.
