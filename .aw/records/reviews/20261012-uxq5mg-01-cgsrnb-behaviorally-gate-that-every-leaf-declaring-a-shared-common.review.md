# Review findings: plan cgsrnb

- Subject-Id: cgsrnb
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `a1461ccd6` in an isolated review lane. The plan was committed and unchanged (`a92c41757`), so no snapshot was needed.
`aw ipd lint --phase author --agent` was clean before semantic review (one advisory `IPD-Z602` on E-06), and `--phase review-finalize` was clean with zero findings after revisions.

Re-verified (probe scripts were placed under the gitignored `.aw/state/` and then deleted):
- `tests.test_agent_surface_conformance.UNIVERSE` has 47 leaves and `MUTATION_UNIVERSE` has 24. Both are importable module constants.
- F-02: walking `cli._build_parser()` with alias dedup gives a no-`--json` set equal to the eleven Section 1.3 forwarded leaves plus `__complete`. Every leaf declaring `--json` also declares `--fields`.
- F-03/F-04: re-ran both sweeps via `tests.conformance_matrix.run_cli`. The broken lists match the plan exactly: `config get`, `config is`, `upgrade-test env`, `upgrade-test probe`, `upgrade-test clean` under `--json`; `ipd coverage`, `partition`, `upgrade-test env/list/probe/sandboxes/clean`, `oc update-models`, `storage reattach` under `--fields`. Every leaf emitted at least one terminal record.
- F-05: `check-local-leaks --json` emits 457 bytes of JSON. With `leak_sanitizer.main` forced to `context=None`, it exits 0 with 0 stdout bytes, while `--agent --fields cmd` still projects correctly.
- `jfdk7p` and `aws1tg` resolve via `aw find backlog`, both are `bug` with `Blocks-Release: next`, and `k84fqu` resolves.
- `.github/workflows/tests.yml`: the `-m slow` step is `continue-on-error: true`, so it is advisory.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | E. Testing / CI gating | `.github/workflows/tests.yml` "Run slow-marked tests (ADVISORY ...)" `continue-on-error: true`; plan E-06 and conventions "runs `-m slow` as its own gating step" | The plan said the `-m slow` step gates and told the executor to mark the mutation half `slow` if the module costs more than 30s. That step is advisory, so the fallback would silently remove half the gate from CI. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The slow-marker fallback is removed and the conventions line is corrected. The new E-07 forbids `mark.slow`, records the times, and escalates cost to the maintainer. V-07 greps for `mark.slow`. Review measured about 24s + 11s with 8 threads. |
| PR-002 | MEDIUM | IN-SCOPE | A. Correctness of evidence demand | `command_surface.discover_parser_leaves` (aliases excluded by identity); `'sanitize' in leaves` is False | E-05, V-05 and Required tests demanded that a `sanitize` `--json` case fail. `sanitize` is an alias of `check-local-leaks` and is in neither universe, so that case cannot exist and the demand was unsatisfiable. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05, V-05, Required tests and Deferred now name only `check-local-leaks` and explain the alias. |
| PR-003 | MEDIUM | IN-SCOPE | G. Reachability | `tests/conformance_matrix.run_cli` runs `python -m agent_workflows` with `PYTHONPATH` pinned to the repo root | E-05 did not state that the mutation must be on disk. An in-process monkeypatch cannot reach the subprocess, so the mutation would appear to have no effect. E-05 also did not say which case should fail: the review measured that only `--json` breaks, while `--fields` still projects. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 now requires an on-disk edit with byte-identical restore and states the measured expected failure (`--json` only, empty stdout). |
| PR-004 | LOW | IN-SCOPE | G. Live-artifact criteria / right-sizing | V-02 "count ... equal to `len(UNIVERSE) + len(MUTATION_UNIVERSE)`"; `IPD-Z602` on E-06 | V-02 used a collected-test count as its bar. E-06 bundled the doc edit, a timing decision and the full suite run. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-02 now uses a set equality of parametrize ids against the imported universes. E-06 is split into E-06 (doc) and E-07 (measure + suite), with V-06/V-07 to match. `IPD-Z602` is cleared. |
| PR-005 | LOW | IN-SCOPE | G. Execution contract | `## Approval and execution gate`; `- Scope-Paths:` | The gate lacked the OQ status line, the scope-fence declaration (including the E-01 out-of-scope backlog filing), `aw ipd begin`, and the conditional finalize ownership. Scope-Paths omitted the plan itself, which receives evidence. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | All of those elements are added. The E-01 exemption-drift STOP is kept as a public-contract decision, not a scope stop. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | If the module is slow, move part of it to `-m slow`? | No: keep it in the gating fast suite and report the cost | Slow-mark the mutation half (makes it advisory in CI) | `.github/workflows/tests.yml` `continue-on-error: true`; review timing about 24s + 11s | yes |
| D-2 | Keep the `sanitize` sensitivity case by adding the alias to the gate? | No: assert on `check-local-leaks` only | Add alias leaves to the sweep (contradicts the universe import rule and `AliasEquivalenceTests` ownership) | `command_surface.discover_parser_leaves` docstring | yes |
| D-3 | Accept OQ-01 (test rather than `aw check` rule) and OQ-02 (no `--verbose`) as resolved? | Yes, as authored | Reopen as maintainer questions | F-07; `check_engine.RULE_REGISTRY` scope; `tests/test_verbose_flag_reach.py` | yes |
