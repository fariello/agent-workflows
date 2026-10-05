# Review findings: plan qs00nc

- Subject-Id: qs00nc
- Subject-Type: ipd
- Reviewed-At: 2026-10-04
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: REVIEWED - OPEN QUESTIONS
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed)

## Round 1

Reviewed in the isolated review lane `review-sweep-run-20261004T134544Z-4052083` at HEAD `ed94410dd`. The plan was
committed and byte-identical to the sealed lane input (rev-4, sha256 `06794481...`), so no snapshot was needed. First
`- Kind:` bullet is `child`, so `IPD-S407` does not apply. `aw ipd lint --phase author --agent` was clean before review;
after revision `review-finalize` reports only `IPD-Q501` (the intended effect of blocking OQ-03), and the `IPD-Z602`
density advisory that the first revision of E-04 raised was cleared by splitting it into E-04 and E-06.

Re-measured: `runner_shared.find_unauthored_child_rows` (returns `(tokens, parsed)`), `read_set_membership`
(`SetMember.status`; a second Order-0 plan is filed as a child), `read_probe_verdict(repo_root, digest, *, model=...)`,
`probe_cache_digest`, `probe_orchestrator(state, target, *, repo, host, retry_budget, asker, runner, counter)`,
`ProbeTarget`, `ProbeOutcome(cached, calls)`, `probe_argv` reading `state["options"]`, `_assert_probe_spawn_is_permitted`,
`resolve_retry_budget`, `enforce_freeze_time_refusal` and its call order in `initialize_run_core`;
`ipd_lint.orchestrator_row_conformance`, `lint_file`, `LintResult.passing`, `C_ORCH_ROW`; `ipd_schema.PASSING_DISPOSITIONS`;
`check_engine.RULE_REGISTRY`/`rule_spec`; `command_surface.find_undeclared_leaves`; `tests/test_agent_surface_conformance.py`
universe; `.github/workflows/tests.yml` step "aw check plans (plan conformance; fail closed)". Measured: an executed plan
lints `legacy/not evaluated`; `read_set_membership` 0.30 to 0.48 s warm per Set (cProfile: `selectors.resolve`); bare
`aw ipd lint` 2.27 s; 17 pending orchestrators, three `approved` (`95jk4s`, `9wzlou`, `l4vw9o`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | C/E feasibility | `agent_workflows/runner_shared.py:19548` `enforce_freeze_time_refusal` "`\"pre-execution\" if status in (\"approved\", \"auto-approved\")`"; its call at `:29257` precedes `probe_decision = enforce_orchestrator_probe_gate(` at `:29522`; `probe_verdict_store_path` (gitignored); qs00nc E-04 "error diagnostic" at `pre-execution` | Same root as `hm1h3l`/`1f4faf` PR-006 (absent verdict as `error` turns CI red permanently), PLUS a mechanism neither earlier review named: an absent-verdict error at `pre-execution` refuses every un-probed approved orchestrator in the freeze gate, before the run-start probe that would ask. The severity is a published-gate guarantee the maintainer must choose. | C:Medium; U:High; S:Low; F:High; Overall:High | FIXED | RESOLVED 2026-10-04 by maintainer ruling, recorded in the plan's OQ-03 (now `Blocking: no`, `Status: resolved`): the coverage answer is STORED IN THE PLAN (new `25kzda` 2.5e: `Coverage`, `Coverage-Fingerprint`, `Coverage-Checked`, `## Coverage findings`), written only by the tool with a matching history line and refused otherwise by new lint rule `IPD-M112`, excluded from the execution-receipt fingerprint, retiring the gitignored 30-day cache. Every clone and CI read the same record, so an absent or out-of-date record is an error in `aw ipd lint` and `aw check` without CI or freeze-gate breakage. Applied in hm1h3l (A.2, A.3, A.6, 2.5e, B.2, D.1, rule 20), 8mabmu (E-03, E-06, E-07) and qs00nc (E-01, E-04, E-06). Previously: Escalated as qs00nc OQ-03 (`Blocking: yes`, `Finding: PR-001`); E-04/E-06/V-04/V-06 now take the severity from OQ-03; freeze-gate context added to `hm1h3l` and `1f4faf` OQ-03. |
| PR-002 | HIGH | IN-SCOPE | A correctness | `ipd_lint.lint_file` on the newest `.aw/records/plans/executed/*.ipd.md` returned `legacy/not evaluated`; `ipd_schema.PASSING_DISPOSITIONS = frozenset((DISPOSITION_CONFORMING,))`; OQ-02 "`executed` is included" | Condition 2 as written lints every child, so every executed child fails and any orchestrator with executed children is never ready, contradicting OQ-02. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01: a terminal-directory child with `Status: executed` is ready without lint; E-05/V-01 add an executed-child case. |
| PR-003 | MEDIUM | IN-SCOPE | A correctness | `read_set_membership` docstring "A Set with two Order-0 plans is malformed; keep the FIRST ... treat the rest as children" | Linting children through `lint_file` with `IPD-S408` active recurses on a malformed Set (the second Order-0 child calls `review_readiness` again). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 requires `IPD-S408` suppressed when linting children; V-01 demands the malformed-Set fixture. |
| PR-004 | HIGH | UNDER-SCOPE | D anti-regression | `tests/test_command_surface_declarations.py` `test_zero_undeclared_parser_leaves`; `tests/test_agent_surface_conformance.py` runs every `check`/`read` `result` leaf with no args in a bare repo | A new `ipd coverage` parser leaf with no `CommandDeclaration` fails the suite, and `command_surface.py` was not in Scope-Paths; the conformance universe would also run it bare. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Scope-Paths gains `agent_workflows/command_surface.py`; E-03 specifies the declaration and the no-arg exit-2 record; tests list and V-03 extended; diff check counts six paths. |
| PR-005 | MEDIUM | IN-SCOPE | G executability / reachability | `probe_orchestrator(state, target, *, repo, host, retry_budget, ...)`; `probe_argv` reads `state["options"]`; `ProbeOutcome.cached`/`.calls`; V-03 "the record's cache field or timing shows it" | E-03 did not say how to call the probe (state, target, retry budget), and V-03's cache demand named no field the record would carry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 specifies the state/target/retry-budget composition, `--host`/`--model`, and per-orchestrator `cached`/`calls` in the record; V-03 demands `cached: true`, `calls: 0`. |
| PR-006 | MEDIUM | UNDER-SCOPE | C operability / user-perceptible cost | `read_set_membership` 0.30 to 0.48 s warm per Set (cProfile `selectors.resolve`); 17 pending orchestrators; bare `aw ipd lint` 2.27 s | Bare `aw ipd lint` (author, advisory) and `aw check plans` would call `read_set_membership` per orchestrator, adding several seconds to commands humans wait on. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 accepts precomputed `membership`; E-04/E-06 require one plans-tree read per invocation and a 1 s warm budget; baseline and after timings demanded. |
| PR-007 | LOW | IN-SCOPE | E evidence / G gate | E-05 parity via subprocess cannot inject an asker; `find_unauthored_child_rows` `parsed=False`; OQ-01 cites the pinning test without its file; gate lacked scope fence and paste-actual-output rule; E-04 bundled two deliverables (`IPD-Z602`) | Parity fixture mechanism unspecified; unusable table not covered; citation incomplete; gate contract incomplete; E-04 multi-concern. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Parity fixture pre-records verdicts; unusable-table case added; OQ-01 cites `tests/test_lost_guard_census.py`; gate gains fence and honesty rule; check rule split into E-06/V-06. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Lint executed children or treat them as ready? | Ready without lint when under `executed/` with `Status: executed` | lint with `legacy=True` (still not `conforming`); drop `executed` from OQ-02 (blocks re-review of partly run Sets) | `lint_file` disposition measured; OQ-02 | yes |
| D-2 | Where does `ipd coverage` get its model/host? | `runner_profiles.resolve` composed into `state["options"]`, plus `--host`/`--model` | a new probe-only resolver (second path) | `probe_argv` reads `state["options"]`; plan text already named `runner_profiles.resolve` | yes |
| D-3 | Bound the sweep cost how? | One plans-tree read per invocation, 1 s warm budget, measured | cache across invocations (stale risk); accept per-orchestrator reads | measured 0.3 to 0.48 s per Set x 17; AGENTS.md perceptibility rule | yes |
| D-4 | Command class for `ipd coverage`? | `check`, `result`, exit `(0,1,2)` | `mutation` (it writes only the gitignored verdict store, like `ipd begin`'s local receipt) | `command_surface` `ipd begin` declaration comment | yes |
