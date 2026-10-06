# Review findings: plan sbiv1j

- Subject-Id: sbiv1j
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (BLOCKER, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (LOW, fixed), PR-009 (LOW, fixed)

## Round 1

Reviewed in lane `review-sweep-run-20261006T040814Z-944` at HEAD `ce21f6e43`. The plan was committed and byte-identical
to the sealed lane input (rev-11); no snapshot needed. `- Kind: child`. `aw ipd lint --phase author` clean before;
`review-finalize` clean after.

Re-measured: `check_engine.evaluate_blocking_close` (the `graduated` branch), `find_from_backlog_artifacts` /
`_from_backlog_carrier_index` and the single-item contract test; `config.resolve_cutover_date`, `KNOWN_FEATURE_CUTOVERS`,
`.aw/config/project.json` `cutovers`, and the `release_gate_at_rest` at-rest arm; `.aw/records/backlog/README.md`
`Graduated-To`; `attention_contract.SPEC_TRANSITIONS`; the production setter argv in `execute_item_core`; CI's fail-closed
`aw check backlog` step.

Corpus scan: 189 `graduated` items; 88 have no active `From-Backlog` handoff (42 with only terminal plans, 40 with only a
resolving `Graduated-To` Set, 6 with nothing); `bmhoxe` has a `draft` handoff plan (`yqv6b7`); specs `c4gd2h` and `z7nbn1`
are `implementing` (`z7nbn1` has only terminal plans). Lint at `author` on the 124 active linked plans takes about 1.1 s
warm; the carrier index about 0.5 s.

Setter spy (a `sitecustomize` wrapper on `evaluate_blocking_close`, bare suite: `3 failed, 5080 passed, 2 skipped`; the 3
failures did not involve this predicate): 24 tests in 9 files move an item to `graduated` with zero carriers.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | BLOCKER | IN-SCOPE | A / CI | corpus scan; `tests.yml` "aw check backlog (backlog conformance; fail closed)" | An ungrandfathered `error` rule reports about 46 to 89 existing `graduated` items whose plans Order 09 never touches (it reopens only orchestrator-backed items), so CI goes red when it lands. E-04 left grandfathering optional. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | New stamped cutover `graduation_ready`; judge only graduations dated on or after it; completed handoffs are ready. |
| PR-002 | HIGH | IN-SCOPE | E verification | E-04 Expected outcome | "On the real tree after Order 09, it reports nothing" was false for the measured population. | Overall:Low | FIXED | Restated against the grandfathered population, with re-derived counts. |
| PR-003 | HIGH | UNDER-SCOPE | E regression | setter spy (24 tests, 9 files) | Existing tests graduate items with no handoff and would be refused; none were in scope. | Overall:Low | FIXED | New E-06/V-06 adds a ready fixture plan to each and keeps every assertion; files declared. |
| PR-004 | HIGH | IN-SCOPE | A correctness | 42 terminal-only items; 40 `Graduated-To`-only items; backlog README | "No handoff at all" misread a completed handoff and the source-side `Graduated-To` link as missing. | Overall:Low | FIXED | Both are handoff evidence in E-01. |
| PR-005 | MEDIUM | IN-SCOPE | G executability | `backlog.run_set` / `status_set` `evaluate_blocking_close` call sites | Refusal point, output shape and renderer unspecified; a refusal after the directory move would leave the file moved. | Overall:Low | FIXED | Before any write, the same output shape, the shared renderer. |
| PR-006 | MEDIUM | IN-SCOPE | E regression | `test_case5b_agent_sets_graduated_before_handoff_commit` asserts `BACKLOG-GRADUATE-LEGITIMACY` | The agent's early `graduated` call is now refused, so this test's outcome changes; F-02 claimed no production change. | Overall:Low | FIXED | Named in E-06, with before and after assertions in V-06. |
| PR-007 | MEDIUM | IN-SCOPE | A correctness | `--gate-dir` semantics (`runner_shared` notes) | An isolated runner call evaluates gates against main, where the produced plans do not yet exist. | Overall:Low | FIXED | The handoff check reads the `--dir` tree; lane production test case added. |
| PR-008 | LOW | IN-SCOPE | G sequencing | `review_readiness` needs `qs00nc`; the production regression needs `r2wa38`; the remedy uses `26m1nb` edges | Dependencies were reached only transitively (`52opph` -> `24qw39` ...). | Overall:Low | FIXED | Declared `26m1nb`, `r2wa38`; `1f4faf` synced. |
| PR-009 | LOW | IN-SCOPE | G contract | gate | Incomplete execution contract. | Overall:Low | FIXED | Completed. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How is the existing corpus kept green? | New stamped cutover on the graduation date | reopen all 88 items (sweeping records change outside scope); warning severity (contradicts the maintainer's "must report" and R-13) | `release_gate_at_rest` precedent; corpus scan | yes |
| D-2 | Is an all-terminal handoff ready? | Yes, when at least one plan is `executed` | require an active plan (flags every finished item) | `graduated` semantics in the backlog README; `done` close rules | yes |
| D-3 | Which tree does an isolated call evaluate? | The `--dir` (lane) tree | the gate tree (plans absent there) | `--gate-dir` documentation in `runner_shared` | yes |
