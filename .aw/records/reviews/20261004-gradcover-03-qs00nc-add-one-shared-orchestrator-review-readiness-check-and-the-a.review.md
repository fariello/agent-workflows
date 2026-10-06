# Review findings: plan qs00nc

- Subject-Id: qs00nc
- Subject-Type: ipd
- Reviewed-At: 2026-10-06
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (MEDIUM, fixed), PR-004 (HIGH, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (LOW, fixed), PR-008 (HIGH, fixed), PR-009 (MEDIUM, fixed), PR-010 (LOW, fixed), PR-011 (LOW, fixed), PR-012 (LOW, fixed)

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

## Round 2

Re-review in isolated lane `review-sweep-run-20261006T040814Z-944` at HEAD `c950886a8`, after the
2026-10-04 maintainer ruling (coverage answer stored in the plan) and the round-2 revision of Order 02
(`8mabmu`, now committing the record at write). The plan was byte-identical to the sealed lane input
(rev-4); no snapshot needed. `Kind: child`. Both lint phases `clean` before and after, each with one
pre-existing `IPD-Z602` (info) on E-03. OQ-03 is `Blocking: no`, `resolved`, `Owner: maintainer`,
confirming round 1's PR-001 as fixed.

MEASURED: a temporary pytest plugin (written under the gitignored `.aw/state/`, removed afterwards)
wrapped `ipd_lint.lint_file` across the bare `python3 -m pytest` run (5082 passed, 1 failed, unrelated:
`test_readiness_absence_invariant` flags four `to-review` gradcover plans carrying `Readiness:` in this
lane, a live-corpus artifact of the in-flight Set) and recorded every test in which an
`orchestrator` plan PASSED lint at `review-finalize` or `pre-execution`. Four tests, all at
`pre-execution`: `tests/test_orchestrator_retirement.py` (2), `tests/test_orchestrator_shape_gate.py`
(1), `tests/test_action_table_runner_parity.py` (1). Each depends on that pass today and none of their
fixtures carries a coverage record. Symbols confirmed: `read_set_membership`,
`find_unauthored_child_rows`, `SetMember`, `resolve_retry_budget` in `runner_shared`;
`orchestrator_row_conformance`, `check_readiness_attestation`, `C_ORCH_ROW` in `ipd_lint`;
`is_in_terminal_directory` in `run_selection_policy`; `CommandDeclaration` fields in `command_surface`;
the conformance sweep's universe is `check`/`read`/`bare` + `result` leaves run with no extra argv
(`tests/test_agent_surface_conformance.py` `compute_conformance_universe`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-008 | HIGH | UNDER-SCOPE | D (anti-regression) | lint-spy measurement above; `runner_shared.enforce_freeze_time_refusal` (`pre-execution` for `approved`); `ipd_lifecycle.begin_plan` pre-execution gate; qs00nc E-04 (absent record is an error at `pre-execution`); qs00nc Scope-Paths (six paths, no existing test file) | After E-04, every synthetic `approved` orchestrator without a coverage record is refused at freeze time and at `aw ipd begin`, so four existing runner tests turn red, in files the plan did not declare. The plan's bare-suite reconciliation would surface it only at execution, with no step to fix it. | C:Low; U:Low; S:Low; F:Medium; Overall:Medium | FIXED | New E-08/V-08: re-derive the list, add a tool-written `coverage_record.write` pass to each failing fixture, change no assertion. Three files added to Scope-Paths; E-05 now depends on E-08. |
| PR-009 | MEDIUM | IN-SCOPE | C (one mechanism) | qs00nc E-03 "`--commit` flag ... without it the edited plans are left for the operator"; `8mabmu` E-07 (round 2) "`coverage_record.write` takes `commit=True` from `probe_orchestrator` and makes one path-scoped commit" | Two contradictory commit behaviors for the same write: Order 02 commits at write, Order 03 left it uncommitted by default. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 defers to Order 02's commit-at-write and adds `--no-commit` (mirroring `aw ipd set`), reporting written/committed per plan. |
| PR-010 | LOW | IN-SCOPE | E (evidence feasibility) | qs00nc Required tests and V-03 "restore `axozpe` with `git checkout -- <path>`" | Under commit-at-write the record is committed, so `git checkout` restores nothing. | all Low | FIXED | Real-tree run uses `--no-commit` then `git checkout`; V-03 names the revert alternative. |
| PR-011 | LOW | IN-SCOPE | C (interface) | qs00nc E-01 signature lacks `retry_budget`; `5etev3` E-02 "passing `retry_budget=frozen_retry_budget(state)` through to the probe"; `probe_orchestrator(..., retry_budget: int, ...)` | Order 04 passes a parameter the shared function does not declare. | all Low | FIXED | E-01 adds `retry_budget`, defaulting to `resolve_retry_budget(None, repo=repo)`. |
| PR-012 | LOW | IN-SCOPE | G (accuracy) | V-02 "both remedies" vs E-02's five; Scope check "one test file"; V-05 "six declared paths" | Wording and counts stale after revision. | all Low | FIXED | Corrected. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-5 | Fix the four broken fixtures, or exempt synthetic plans / downgrade the absent-record finding at `pre-execution`? | Fix the fixtures with a tool-written record | exempt fixtures (a test-only path in production); make absent-record advisory at `pre-execution` (contradicts maintainer's OQ-03 ruling and `hm1h3l` D.1) | maintainer ruling recorded in OQ-03; P16 (tests drive real behavior) | yes |
| D-6 | Who commits the record written by `aw ipd coverage`? | Order 02's commit-at-write, with `--no-commit` to suppress | a second commit path in the verb | `8mabmu` E-07 / D-4 | yes |
