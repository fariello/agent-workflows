# Review findings: plan 1ue3kr

- Subject-Id: 1ue3kr
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed in an isolated review lane at HEAD `a178320e9`. The plan was committed and unchanged (last touched by `1864cc9d2`), so no snapshot was needed. `aw ipd lint --phase author --agent` was clean before semantic review.

Re-verified:
- `agent_workflows/cli.py::_run_migrate_layout` (line 16576): `--config` not-found and invalid-JSON both `return 1`; precedence `cli_backend or config_backend or "repository"` and `cli_leftovers or config_leftovers or "defer"`; wizard gate `_term_mod.is_interactive() or isinstance(sys.stdin, io.StringIO)`; decline on `conf not in ("y", "yes")` returns 1; non-interactive unconfirmed returns 1 with "Non-interactive migration requires explicit confirmation".
- `cli._dispatch` calls `_run_migrate_layout(args, term)` through the module global (`if args.command == "migrate-layout":`), so rebinding the attribute reaches the dispatch.
- Scratch probe under `.aw/state/` (deleted): `RES wizard 0 True False`, `RES override 0 repository False`, `RES badjson 1 False`, `RES nonint 1 False`, `RES plan 0 False True`, `RES cfg 0 True keep`, `RES ovr 0 False remove`.
- E-04 mechanism demonstrated with a scratch two-test module and both plugins (deleted): unmutated `2 passed`; return-none `2 failed`; confirm-bypass `1 failed, 1 passed` (decline only).
- `.github/workflows/tests.yml` "Run self-tests (parallel)": `python -m pytest tests/ -n auto -rfEs` collects every non-slow module under `tests/`.
- `tests/support.py::init_repo` / `clean_git_env` scrub inherited git env vars.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | E. Test soundness | `cli._run_migrate_layout` `selected_leftovers = cli_leftovers or config_leftovers or "defer"` | E-02 asserted precedence only for `target_backend`; a mutation dropping `--leftovers` precedence or config `leftovers` parsing would survive, though the plan's Goal names flag precedence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 (a)/(b) now also assert transaction disposition `keep`/`remove` and `.agents/README.md` present/absent (probe `RES cfg 0 True keep`, `RES ovr 0 False remove`); V-02 demands those lines. |
| PR-002 | MEDIUM | IN-SCOPE | B/C. Test isolation | `tests/support.py::clean_git_env`, `init_repo` | E-01 fixture ran raw `git` without scrubbing inherited `GIT_DIR`/`GIT_INDEX_FILE`; run from a hook or lane it can write to the outer repo. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 now uses `tests.support.init_repo` and `clean_git_env()` for add/commit. |
| PR-003 | MEDIUM | IN-SCOPE | G. Execution contract | `## Approval and execution gate` | Gate lacked OQ status, scope-fence declaration wording, the hard-MUST paste rule, and conditional runner/executor finalize ownership; it said "move the plan" without naming the tool. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten with all elements; `aw ipd finalize` only when executed by hand. |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Load-bearing guard | `pyproject.toml` `testpaths`; `.github/workflows/tests.yml` `python -m pytest tests/ -n auto -rfEs` | The module is outside `testpaths`, so its guard depends on CI's full-directory step and on carrying no `slow` mark; the plan did not say so or check it. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Deferred row states the CI path and forbids a `slow`/`livecorpus` mark; V-05 demands a `--collect-only -m 'not slow and not livecorpus'` proof. |
| PR-005 | LOW | IN-SCOPE | E. Evidence | E-04 / V-04 | Expected outcome said "most tests" though `None` equals neither 0 nor 1, so every test should fail; V-04 did not demand the plugin source or unmutated baseline; HOW was undemonstrated. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Outcome tightened; V-04 demands baseline, plugin source and summaries; mechanism demonstrated at review and cited in E-04; `finally` restore and `-p no:cacheprovider` added. |
| PR-006 | LOW | IN-SCOPE | Records conformance | `## Workflow history`; E-01(c); E-05 | History was oldest-first; E-01(c) said "both" of three seeded files; E-05 used `<plan>` placeholder. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reordered newest-first; "all three ... with seeded content"; `aw commit 1ue3kr`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Must the module be added to `testpaths` to be a real guard? | No; rely on CI full-directory step, forbid `slow` mark, prove collection in V-05 | Add to `testpaths` (changes routine gate, maintainer decision) | `.github/workflows/tests.yml` "Run self-tests (parallel)"; plan Deferred row | yes |
| D-2 | Is the in-memory plugin mutation mechanism sound (HOW question)? | Yes | Source-edit mutation with restore (riskier in a shared checkout) | Review demonstration: `2 passed` / `2 failed` / `1 failed, 1 passed` | yes |
| D-3 | Should leftovers precedence be pinned in this plan? | Yes, in E-02 | Leave to a follow-up (would leave named Goal property unguarded) | plan `## Goal` "flag precedence"; probe `RES ovr 0 False remove` | yes |
