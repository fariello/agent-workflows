# Review findings: plan lp1zkb

- Subject-Id: lp1zkb
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `ba230c685` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review, and `--phase review-finalize` was clean after revisions.

Re-verified:
- F-01: `git log --author=test@example.com` counts 322 commits, first `80c8a93d8` (2026-10-08 01:31:49), last `e6e12c181` (2026-10-09 09:06:05). The last real-identity commit `ea16d89ac` added `ConfigGetBehaviorAndDescriptionTests` to `tests/test_config.py`; those tests sandbox `XDG_CONFIG_HOME` and run no git, so they are not an obvious writer.
- F-02/F-03: the shared config has no `user.*`/`author.*`/`committer.*` keys (exit 1), and `extensions.worktreeConfig` is unset.
- `tests/support.git` (`check=False`) and `init_repo` are as quoted. `conftest.py` loads `pytest_plugins = ["tests.deselect_notice", "tests.livecorpus_notice"]`.
- Probes run under `/tmp/opencode` only; the real config was never touched.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing | `tests/support.py` `init_repo` first statement `path.mkdir(parents=True, exist_ok=True)`; plan E-04 (e) "a regular FILE at that path" | The (e) fixture never reaches `git init`: `mkdir` raises `FileExistsError` on a file, so the test passes on the base commit too and cannot show the defect (E-04 requires it to FAIL there). A read-only existing directory does reproduce it: `git init` exits 1 and `test@example.com` lands in the enclosing repo's config. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | (e) now uses a `chmod 0o500` directory inside an enclosing tmp repo, skipped under root. Added F-07. |
| PR-002 | HIGH | UNDER-SCOPE | A. Integrity / D. Anti-regression | plan E-03 "assert `git -C <path> rev-parse --show-toplevel` resolves to `path`" | With `GIT_DIR` inherited from the environment (git hooks and some git-driven processes export it), `git init` succeeds and `--show-toplevel` reports `path`, but the identity is written to the `GIT_DIR` repo. So the planned check passes exactly the case it must refuse. Demonstrated by probe. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now scrubs `git rev-parse --local-env-vars` from `init_repo`'s git calls and checks `--absolute-git-dir` == `path/.git`. E-02 scrubs the same vars for the guard's own reads. Added case (f), F-08, and an E-05 run with inherited `GIT_DIR` in a scratch clone. |
| PR-003 | LOW | IN-SCOPE | G. Evidence | plan V-04 | The base-commit run of the new module could not load the guard plugin, which does not exist at the base commit. | Overall: Low | FIXED | V-04 now copies the plugin into the base worktree alongside the module. |
| PR-004 | LOW | IN-SCOPE | G. Execution contract | plan gate "Lifecycle" | The gate did not say the executor must not finalize under a runner, and the manual finalize command lacked `--apply`. The honesty rule was not stated as a MUST. | Overall: Low | FIXED | Added. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should `init_repo` prove it initialized `path`? | Scrub `--local-env-vars`, then compare `--absolute-git-dir` to `path/.git` | `--show-toplevel` (passes under inherited `GIT_DIR`) | review probe, F-08 | yes |
| D-2 | Change `support.git`'s default environment for every caller? | No: scrub only in `init_repo` and the guard | Scrub globally in `support.git` (wider behavior change for many tests, outside this bug's remedy) | `tests/support.py` `git` has many callers; the guard catches any other route | yes |
