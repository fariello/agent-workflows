# Review: Retire dangling citations of deleted code-pin tests in runner comments

- Subject-Id: 65d5zf
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Verified at HEAD `e857562e1`. `aw ipd lint --phase author` clean with one advisory (`IPD-Z602` on E-04).
Re-measured E-01: the `rg` sweep reproduces F-01..F-03 exactly (runner_shared `13564`, `23696`, `28229`;
agy `460`, `1841`, `1888`, `4104`, `4109`; oc `5240`, `5260`; `tests/test_agy_runipd_cli.py:1875`); all three
cited test files absent; `git log -S` confirms `19313eed7` for `SharedPredicateTests`,
`TheRowWalkIsSharedWithTheRetirementGate`, `_shim_set`, and `d27e5eac8` for `test_no_runner_to_runner_import`;
AST read shows both `main` `subcommands` sets equal (`--help, -h, audit, integrate, report, resume, start,
status, stop`). Backlogs `2ohbkj` (open), `iosmvn`, `046nys`, plan `dtelfb` all resolve.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | D. Honest documentation | `tests/test_oc_runipd.py` `driver.main(["integrate", "mm6wuz"])`; `tests/test_agy_runipd_cli.py` `agy_runipd.main(["integrate", "agi001", ...])`; `oc_runipd.main` comment "A test asserts the bare form is not rewritten, in both drivers, and a third assertion pins this set ..." | E-05/E-06 would rewrite all bare-form claims as dead, but `integrate` is still driven through the real `main` in both drivers, so the rewrite would trade one false statement for another. E-06 also omitted the oc `integpath-04` sentence from its quoted list. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-06; E-05/E-06 now distinguish surviving `integrate` coverage from absent `stop`/`audit`/set-equality coverage and list the oc `integpath-04` sentence. |
| PR-002 | LOW | IN-SCOPE | E. Testing (baseline) | E-02, V-02, V-07 | Suite parity compared summary counts; counts vary with load-sensitive nodes (`wc5c5e`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Baseline and parity now compare FAILED node-id sets, with single re-run for a post-only failure. |
| PR-003 | LOW | IN-SCOPE | E. Testing (proof) | V-06 "`git show HEAD:<path>`" | After a commit HEAD contains the edit, so an AST comparison against HEAD would trivially print EQUAL. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | V-06 compares against the E-02 recorded base commit. |
| PR-004 | LOW | IN-SCOPE | G. Right-sizing | lint `IPD-Z602` on E-04 | E-03/E-04 enumerate three sites each with no recorded cohesion rationale. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Cohesion rationale recorded: one rule, one file, prose only, one V-item; split adds no independent test surface. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Split E-03/E-04 per site? | Keep, with cohesion rationale | One E-item per site | Each site is a single-file prose edit under one rule; V-03/V-04 quote all passages | yes |
| D-2 | How should the rewritten shim comments treat `integrate`? | State it is still exercised via real `main` | Declare all bare-form coverage gone | `rg 'main\(\["integrate"' tests/` hits in both driver test files | yes |
