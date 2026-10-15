# Review findings: plan fbdxmh

- Subject-Id: fbdxmh
- Subject-Type: ipd
- Reviewed-At: 2026-10-15
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `182cb1818` in an isolated review lane. The plan was committed and unchanged, so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review. `--phase review-finalize` was clean after revisions; its one info hit was `IPD-Z602` on E-01, which is a single function and so stays one item.

Re-verified by driving the CLI on temp fixtures with an isolated `HOME` and `AW_HOME`/`XDG_CONFIG_HOME`/`AW_CONFIG_DIR` unset:
- Bare `git init` repo: `index plans|prompts|research|all --agent` all exit 1 with a `FileNotFoundError` traceback. `plans` and `research` resolve under `$HOME/.aw/projects/<slug>-<hash>/records/<type>`, while `prompts` resolves in-repo. F-01 is reproduced. No directories were created.
- Only `.aw/records/plans/` present: `index all --agent` emits a plans `ok` line, then crashes on prompts with rc 1. F-02 is reproduced.
- `index <verb> --check --agent` on a bare repo: `outcome: conforms`, exit 0, with `check.stale-index-missing` info findings. This is the unchanged baseline.
- `aw install . -y --no-interactive` on a fresh repo creates all three records dirs, after which `index all --agent` exits 0. Re-installing after `rm -rf .aw/records/prompts` restores it.
- `aw install . -y --no-interactive` inside `<project>/sub` exits 0 and creates a NESTED project (`sub/.aw`, `sub/.agents`, `sub/AGENTS.md`, ...). `index plans --dir sub --agent` currently crashes on a home-backend path.
- `nonsurveyable_root_refusal`: for a bare git repo it gives `may_proceed=False` with `next=aw install .`. For `--dir <project>/sub` it gives `may_proceed=False` with `next=None`. For the project root it gives `may_proceed=True`.
- A hand-built `cannot-run` `CommandResult` with a normalized `.aw/projects/...` location validates under `agent_schema.validate_agent_record`. `CommandResult(status="ok", exit_code=2)` renders `outcome: "error"`.
- `python3 -m agent_workflows check all` exits 1 at base, with 37 errors in rules unrelated to this plan. `CHANGELOG.md` has no `[Unreleased]`/`### Fixed`. Fixes there are `- Fixed:` bullets under `## 2.0.0 (pending)`.
- `python3 -m pytest -o addopts="" -q tests/test_index_write_agent_records.py`: 10 passed at base.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness / F. UX (false recovery advice) | `agent_workflows/project_context.py` `nonsurveyable_root_refusal`; review probe `aw install .` in `<project>/sub` | The plan fixed `next: "aw install ."` and the human text "run 'aw install .'" for every case. For an explicit `--dir` inside a project, that advice creates a nested project, which is the class of false refusal `lmyeas` PR-001 already retired. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 derives the advice from `nonsurveyable_root_refusal`, and falls back to `aw install .` only for a real root with an incomplete tree. E-03(d) pins `next != "aw install ."` and that no `sub/.aw` appears. |
| PR-002 | MEDIUM | IN-SCOPE | F. Honest diagnostics (wrong path named) | `plans_index._dirs`, `research_index._roots` (home-backend resolution); probe | The refusal hard-coded `.aw/records/<type>` as the location. For plans/research in an unconfigured repo it would name a directory that was NOT the one checked. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The helper takes the resolved `index_dir` and stores it relative, or via `agent_schema.normalize_repo_path` (probe: `.aw/projects/x-abc123/records/plans`), so it is truthful and leak-free. Removed `default_rel_dir`. |
| PR-003 | HIGH | IN-SCOPE | E. Verification (unsatisfiable demand) / G. stale target | `check all` exit 1 at `182cb1818`; `CHANGELOG.md` heading `## 2.0.0 (pending)` | E-04/V-04 required `check all` and the suite to exit 0 and an `## [Unreleased]` -> `### Fixed` entry. The first is false at base, so a correct execution could not pass V-04, and the second names a section that does not exist. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-04 uses a base-commit comparison (no new rule id or count, no new suite failure). The entry is a `- Fixed:` bullet under the pending heading (same remedy as `7i4zba` PR-001/PR-002). |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Testing (fixture isolation) | `tests/conformance_matrix._pinned_env` copies `os.environ`; live env sets `AW_CONFIG_DIR` | E-03 said only "isolated HOME". `run_cli` inherits `AW_HOME`/`XDG_CONFIG_HOME`/`AW_CONFIG_DIR`, so the home-backend path and the "no dirs under HOME" assertion could resolve elsewhere and pass vacuously (`rlhmt9` F-07 class trap). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 and the gate require `HOME` to be a temp dir with those three variables unset. The no-creation check covers both the repo and `HOME`. |
| PR-005 | MEDIUM | OVER-SCOPE | C. Architecture (order-dependent scope) | `7i4zba` E-01 owns `aggregate_index_results`; that plan's `check=False` status formula | E-01(e) told the executor to conditionally edit a sibling-owned function "if present". That makes scope depend on run order and duplicates `7i4zba`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Removed it. Deferred to `7i4zba` with the measured interaction recorded: an exit-2 aggregate renders `outcome: "error"`, which Section 11.4 allows. E-03(b) asserts only properties that hold in either order. |
| PR-006 | MEDIUM | UNDER-SCOPE | D. Invariant map / E. tests | `quiet=True` callers; `_nv_backend_args` passes `--dir` | The plan had no invariant-to-test map, no test for the in-project `--dir` case, and no `--check`-unchanged evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the invariant-to-test map, E-03(d), and the `--check` pair in V-02. V-04 runs the existing check-path suites. |
| PR-007 | MEDIUM | UNDER-SCOPE | G. Verification checklist strength | V-01, V-02 | V-01 and V-02 demanded only diffs, which cannot show that the refusal is schema-valid or leak-free, or that dispatch reaches the guard. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-01 adds a direct helper call with schema validation and a leak check. V-02 adds a CLI write-vs-check run, with its code path named. V-03 demands `-o addopts="" -v` output, with test names as pointers only. |
| PR-008 | LOW | IN-SCOPE | G. Execution contract / evidence accuracy | `## Approval and execution gate`; Step 0 "Nine internal call sites" | The gate lacked the honesty rule, `aw ipd begin`, path-scoped `aw commit`/never-push, a scope fence, and runner-conditional finalize, and it told the executor to always finalize. The `quiet=True` caller census said nine call sites, but 13 were measured. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Rewrote the gate with all of those elements. Corrected the census, and noted that `_refresh_plans_index_fail_loud` still fails loud. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Which recovery command should the refusal advertise? | Reuse `nonsurveyable_root_refusal`'s next action; use `aw install .` only at a real root with an incomplete tree | Fixed `aw install .` (creates a nested project inside a project, measured); no `next` at all (Section 11.4 wants a recovery command where one exists) | `project_context.nonsurveyable_root_refusal`; `lmyeas` PR-001; review probe | yes |
| D-2 | Which path should the diagnostic name? | The resolved directory, made relative or normalized | Canonical `.aw/records/<type>` (names a path that was not checked) | `plans_index._dirs`; `agent_schema.normalize_repo_path` probe | yes |
| D-3 | Should this plan edit `aggregate_index_results`? | No; defer to `7i4zba` and rely on the sink | Conditional edit "if present" (order-dependent scope) | `7i4zba` E-01 ownership; `to_agent_record` probe showing `outcome: "error"` is contract-legal | yes |
| D-4 | What bar replaces `check all` exit 0? | Base-commit per-rule comparison | Keep exit 0 (unsatisfiable at base) | live `check all` exit 1 at `182cb1818` | yes |
