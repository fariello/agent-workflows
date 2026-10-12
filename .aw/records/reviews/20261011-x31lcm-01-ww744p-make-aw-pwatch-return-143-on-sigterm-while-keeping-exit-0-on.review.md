# Review findings: plan ww744p

- Subject-Id: ww744p
- Subject-Type: ipd
- Reviewed-At: 2026-10-12
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated lane at HEAD `47538dba5`. The pending plan matched the sealed lane input (sha256 `1050d9ef...`) and was committed, so no snapshot commit was needed. `aw ipd lint --phase author --agent` reported `clean`. `- Kind: child`.

Re-measured: subprocess probe `SIGINT rc= 0 first= True`, `SIGTERM rc= 0 first= True` (F-01); in-process sentinels after `--once`: `int restored: False term restored: False` (F-04 leak confirmed); patched-`sleep` in-process SIGTERM returns `0` today (test shape is feasible); `--once` exits 0; bare `aw pwatch` exits 2. Survey reproduces: in-process callers `cli.py` (`return pwatch.main(list(argv_list[1:]))` and the `pwatch_args` arm), `runners_monitor.py` `return pwatch.main(pwatch_argv)`; wrappers `tools/pwatch.py`, `tools/watch-agy.py`; no signal supervisor. Both quoted stale texts exist (`command_surface.py` point 3, `test_exit_contract_conformance.py` "verbs like pwatch return 0 on signals"). D162 is the last decision. `uu4rfe` exists and is `open`; `evaluate_durable_carrier` returns `[]`. `x31lcm` is `chore` with no `Blocks-Release`, so no release gate is owed.

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | UNDER-SCOPE | F (honest documentation) | `agent_workflows/pwatch.py:970` `pwatch.main` first branch `return runners_monitor.run_table_dashboard(args)` | `aw pwatch --runners --table` returns before any handler is installed, so this plan does not change it, yet E-06's README note would have said `pwatch` exits 143 on SIGTERM unqualified. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added F-07. E-02 states the branch is untouched, and E-06 and V-06 now require the README note to name the `--runners --table` exception (carried by `uu4rfe`). |
| PR-002 | MEDIUM | IN-SCOPE | E (test robustness / coverage) | Plan E-04 "A fourth in-process test is recommended"; V-03 "if the fourth test exists" | The only test that can observe handler restoration after a SIGTERM was optional, and as specified it would HANG on a regression: with a no-op sentinel installed and no `pwatch` handler, the patched `sleep` loop never exits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Test (4) is now REQUIRED and bounded (the patched `sleep` raises on its second call). E-04 now asks for four tests, and V-03 demands it. Added F-08. |
| PR-003 | LOW | IN-SCOPE | E (evidence feasibility) | Plan V-04 `grep -nE "inspect|ast\.|..."`; review run `printf 'last.x\nfast.y' | grep -nE "inspect|ast\."` matched both | The source-read check pattern `ast\.` false-positives on ordinary identifiers, so a clean test file could fail V-04's "no hits". | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The pattern is now word-bounded (`\binspect\b|\bast\.`). |
| PR-004 | LOW | IN-SCOPE | A (concurrency between plans) | Pending plan `n8we3u` E-11 also targets "D163 at authoring" | Two pending plans target the same decision number. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 now says to use the next free number and to re-read the last `### D<n>` heading just before writing. |
| PR-005 | LOW | IN-SCOPE | Project rule (OQ owner) | OQ-01 `- Owner: none`; plan-review Step 3.1 rule 5 | A question the author resolved recorded no owner. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Now `Owner: plan author`. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|---|---|---|---|---|---|
| D-1 | Should `--runners --table` be brought into this plan so `aw pwatch` is uniform? | No; document the exception and leave it to `uu4rfe`. | Route the table branch through the new handling here. | Plan Scope OUT names `run_table_dashboard`; `uu4rfe` (open) carries exactly that handler; `runners_monitor.py` is outside Scope-Paths. | yes |
