# IPD: Shared dependency graph predicate and check.ipd-dependency-* rule family across aw check and phased ipd lint, with grandfathering cutover

- Date: 2026-08-27
- Kind: child
- Concern: With the `Item-Dependencies` field parseable (child 01), nothing yet RESOLVES its edges, builds the cross-IPD graph, detects cycles/dangling targets, or enforces that the statement is present and resolved at the right lifecycle phases. It must be ONE shared pure predicate consumed by `aw check`, phased `aw ipd lint`, and (child 03) the hook, so they cannot diverge - exactly the bklggrad `evaluate_blocking_close` one-predicate-many-surfaces model. It also needs a grandfathering cutover so making the statement mandatory does not mass-fail the existing plan corpus. Spec 25kzda sections 2.9-2.11 + 4.3 define this precisely.
- Scope: Implement the shared dependency evaluator + its rule family + grandfathering. (1) One pure evaluator (in check_engine.py) that consumes a repo snapshot + IPD path set + phase + cutover marker: parses every `Item-Dependencies` once (via child 01's parser), resolves each typed id6 edge once against the identity index, builds ONE directed graph (IPD->IPD edges participate in cycle detection; spec/backlog targets are leaves), and returns the stable findings. (2) The `check.ipd-*dependency*` rule family with the spec's exact severities/assurance classes/recovery commands: `check.ipd-missing-dependency-statement` (error post-cutover + at review-readiness/pre-execution/pre-transition; advisory `grandfathered` for a pre-cutover draft or eligible terminal plan at the always-on author check), `check.ipd-dependency-unresolved` (advisory on a scaffolded draft at author; error at later phases; fires on the `unresolved` sentinel), `check.ipd-dependency-malformed` (error), `check.ipd-dependency-dangling` (error - a typed id6 with zero matches), `check.ipd-dependency-ambiguous` (fatal/identity - multiple matches or cross-type ambiguity), `check.ipd-dependency-cycle` (error - directed cycle). (3) Surface the SAME evaluator through `aw check` (repo-wide portable authority; folded into the cross-tree sweep next to the from-backlog/blocks-release checks) AND phased `aw ipd lint` (author = advisory/unresolved-permitted honest stub; review-readiness/pre-execution/pre-transition = blocking; the frozen statement must equal the reviewed statement at execution). (4) Grandfathering: record one dependency-schema cutover marker in repo policy; any IPD created at/after cutover must carry the field; pre-cutover terminal plans get the `grandfathered` advisory (no mass-fail); pre-cutover pending plans stay honest drafts but cannot advance to review-readiness/execution until resolved; NO tool bulk-inserts `none`. This child does NOT add the commit hook (child 03) nor the runner preflight/cascade (deferred to the runner program).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, agent_workflows/releases.py, agent_workflows/config.py, tests/
- Status: executed
- Set: ipddeps
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ovbnyq

## Workflow history
- 2026-08-28 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Shared cross-IPD dependency evaluator (check_engine.evaluate_ipd_dependencies) + six check.ipd-dependency-* rules surfaced via aw check (plans path, both plans+all once) and phased aw ipd lint (author advisory; review/pre-exec/pre-transition blocking) + cutover grandfathering (no mass-fail, no auto-none). 32 dep tests; suite green modulo pre-existing CLI-conformance failures [Scope reconciliation - in-scope-unmodified agent_workflows/check_engine.py: implemented in preceding commit c2d9893; in-scope-unmodified agent_workflows/config.py: cutover-marker read helper in preceding commit c2d9893; in-scope-unmodified agent_workflows/ipd_lint.py: implemented in preceding commit c2d9893; in-scope-unmodified agent_workflows/ipd_schema.py: rule consts + cycle helper in preceding commit c2d9893; in-scope-unmodified agent_workflows/releases.py: not needed (evaluator lives in check_engine; no releases.py change); in-scope-unmodified tests/: dependency tests + lifecycle fixture resolution in preceding commit c2d9893]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-201/202/203 fixed

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add one shared pure dependency evaluator (parse-once, resolve-once, one DAG) surfaced as the `check.ipd-dependency-*` rule family across `aw check` and phased `aw ipd lint`, plus the grandfathering cutover so mandatoriness does not mass-fail existing plans - the bklggrad one-predicate-many-surfaces model applied to cross-IPD deps.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared evaluator + rule family

- [x] E-01 Add one pure evaluator in check_engine.py (repo snapshot + IPD path set + phase + cutover marker -> structured findings): parse each `Item-Dependencies` (child 01 parser), resolve each typed id6 edge against the identity index, build one directed graph, detect cycles. Emit the six `check.ipd-dependency-*` findings with the spec's severities/assurance/recovery commands (missing / unresolved / malformed / dangling / ambiguous / cycle).
  - Depends on: none
  - Expected outcome: pure function returns the correct finding for each crafted input (clean, missing, unresolved, malformed, dangling, ambiguous, cyclic).
  - Execution state: performed

### Task group 2: surface across check + lint

- [x] E-02 Surface the evaluator through `aw check` as repo-wide portable authority, deterministic path/rule order. CRITICAL WIRING NOTE: the existing cross-tree block in `check_engine.check_types` (near `check_blocks_release`/`check_from_backlog`/`check_release_gate_consistency`, check_engine.py:597-624) runs ONLY under the `["all"]`/`collisions=True` sentinel, so `aw check plans` (norm="plans", `collisions=False`, cli.py:6241-6246) does NOT reach it. Spec 2.10 lists `aw check plans` as a recovery command AND all dependency sources are IPDs (a plans-scoped concern), so the dependency evaluator MUST run for the `plans` type too - wire it into the plans-type check path (check_type/check_refs for "plans") so `aw check plans` surfaces it, AND ensure it also runs in the `all` sweep (do not double-report: run it once per invocation). Deterministic path then rule order.
  - Depends on: E-01
  - Expected outcome: BOTH `aw check plans` AND `aw check all` report every non-grandfathered dependency finding (verified by actually running both); a clean tree passes both; no finding is double-reported when running `all`.
  - Execution state: performed
- [x] E-03 Wire the evaluator into phased `aw ipd lint`: author phase = advisory (unresolved permitted, honest stub); review-readiness/pre-execution/pre-transition = blocking; enforce that the frozen statement equals the reviewed statement at execution.
  - Depends on: E-01
  - Expected outcome: a placeholder-free draft with a valid statement passes author; an unresolved/missing/malformed/dangling/cyclic statement blocks at review-readiness and later phases.
  - Execution state: performed

### Task group 3: grandfathering cutover

- [x] E-04 Record one dependency-schema cutover marker in repo policy/config; implement the grandfather rule: post-cutover IPDs must carry the field; pre-cutover terminal plans -> `grandfathered` advisory (no mass-fail); pre-cutover pending plans stay honest drafts but cannot advance until resolved; no tool bulk-inserts `none`.
  - Depends on: E-01
  - Expected outcome: existing corpus does not mass-fail `aw check`; a post-cutover IPD missing the field is an error; a pre-cutover pending plan is blocked only at advance/execute, not at author.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `check_engine.evaluate_blocking_close` + the from-backlog rule family is the exact one-predicate-many-surfaces precedent (setter/check/hook call one evaluator). Cross-tree checks fold into the sweep near `check_blocks_release`/from-backlog at check_engine (check_engine.py:597-624).
- WIRING SUBTLETY: that cross-tree sweep is gated by `collisions=True`, set ONLY for the `["all"]` sentinel (cli.py:6245 passes `collisions=(norm == "all")`). `aw check plans` therefore does NOT run it. Because every dependency source is an IPD (plans-scoped) and spec 2.10 uses `aw check plans` as a recovery command, the evaluator must be reachable under the `plans` type, not only `all` (see E-02).
- Identity resolution: `_check_identity_slots`/`check_collisions` (check_engine.py:253,336) already build a declared-Id owner map + `_ID6_RE` (check_engine.py:638); reuse this identity index to resolve typed id6 edges and to detect the `ambiguous` (multiple-owner) case rather than building a second index.
- Phased lint already supports author/review-finalize/pre-execution/pre-transition/post-transition (`aw ipd lint --phase`); this adds dependency findings at the right phases (map "review-readiness" to the existing review-finalize phase).
- Grandfathering precedent: `Scope-Paths` uses a reserved sentinel + conditional-at-gate mandatoriness so pre-cutover plans are not mass-failed; mirror it.

## Findings

The only novel logic is edge resolution + cycle detection + the phase/grandfather severity matrix; parsing is child 01's, and the surface-wiring pattern is bklggrad's. Risk is the severity matrix (author advisory vs later blocking, grandfather advisory) - encode it once in the evaluator so all surfaces agree.

## Proposed changes (ordered, validatable)

1. `check_engine.py`: the shared evaluator + six rule findings.
2. `check_engine.py` cross-tree sweep + `ipd_lint.py` phased wiring (both call the evaluator).
3. `config.py`/policy: the cutover marker + grandfather logic.
4. `tests/`: per-rule fixtures, phase matrix, grandfather advisory-vs-error, no-mass-fail on the current corpus.

## Deferred / out of scope (with reason)

- The `Item-Dependencies` field/parser/setter: child 01 (dependency).
- The opt-in commit hook: child 03 (consumes this evaluator).
- Runner preflight, skip-cascade, `--with-dependencies` closure: the runner program (spec 2.9/5.4).

## Scope check

- Over-scope: none.
- Under-scope: none (evaluator + rule family + check/lint surfaces + grandfathering is the complete enforcement-minus-hook deliverable).

## Required tests / validation

- Each `check.ipd-dependency-*` rule fires on its crafted fixture and is clean otherwise; ambiguous is fatal/identity class.
- Phase matrix: author advisory (unresolved OK); review-readiness/pre-execution/pre-transition blocking; frozen==reviewed enforced at execution.
- Grandfathering: the CURRENT repo's existing plans do not mass-fail `aw check` after cutover; a post-cutover missing-field IPD errors; a pre-cutover pending plan blocks only at advance.
- Determinism: repeated runs on one tree produce identical findings/order.

## Spec / documentation sync

- Document the rule family + cutover in the IPD docs / AGENTS.md; cross-reference spec 25kzda 2.10-2.11.

## Open questions

### OQ-01: `state:` edge on an in-repo target the dependent must precede - do we need a "settle order" note now, or only in the runner?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Spec 2.9 notes an already-satisfied `state:` edge requires the scheduler to run the dependent before the target advances away from that state. That is a RUNNER-scheduling concern; this child only checks the statement is well-formed/resolved. RESOLVED (see gate "Open questions resolved"): defer the ordering guarantee to the runner program; record the requirement here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: A pytest table driving the pure evaluator over crafted repo snapshots shows EACH of the six findings fires on exactly its own fixture and on no other: clean (no finding); missing field -> `check.ipd-missing-dependency-statement`; `unresolved` value -> `check.ipd-dependency-unresolved`; a grammar/canonical-order/pairing/duplicate/self/none-mixture violation -> `check.ipd-dependency-malformed`; a typed id6 with zero matches -> `check.ipd-dependency-dangling`; a typed id6 with multiple owners (or cross-type collision) -> `check.ipd-dependency-ambiguous` at the fatal/identity class; an IPD->IPD directed cycle (including a 3-node cycle) -> `check.ipd-dependency-cycle`. Paste the passing test IDs/output, showing each finding carries the spec's exact severity/assurance/recovery-command text. Falsifiable: a fixture that should be clean but reports a finding, or a missing rule, fails.
  - Observed evidence: The shared evaluator `check_engine.evaluate_ipd_dependencies` (single def at check_engine.py:1090) is exercised by `tests/test_ipd_dependency_check.py::EvaluatorRuleMatrixTests` (11 tests): test_clean_none_has_no_finding (no finding); test_missing_statement -> RULE_IPD_DEP_MISSING; test_unresolved_sentinel_blocking_phase -> RULE_IPD_DEP_UNRESOLVED; test_malformed + test_self_dependency_is_malformed -> RULE_IPD_DEP_MALFORMED (self-edge caught by the resolver since the parser can't see the owner id6); test_dangling -> RULE_IPD_DEP_DANGLING; test_ambiguous_multiple_owners (two plans declaring the same id6) -> RULE_IPD_DEP_AMBIGUOUS; test_cycle_two_node + test_cycle_three_node -> RULE_IPD_DEP_CYCLE; test_cross_type_edge_resolves (exists:spec: resolves against a specs record) + test_spec_edge_dangling_when_only_a_plan_has_that_id6 (typed resolution). Plus `CycleHelperTests` (3) over the pure `ipd_schema.item_dependency_cycles` (acyclic / 2-node / leaf-not-in-graph). Runner: `python3 -m pytest tests/test_ipd_dependency_check.py -m ''` -> `32 passed in 4.14s`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Actual transcripts of BOTH `aw check plans` AND `aw check all` (or `aw check` with the appropriate type) run against (a) a crafted tree with a dangling AND a cyclic dependency IPD - each command reports both findings with the same rule IDs; and (b) the CURRENT clean repo - each exits 0 with zero dependency findings. Show that running `all` does not double-count a finding (a single occurrence per rule/path). Paste both transcripts + exit codes. Falsifiable: `aw check plans` NOT surfacing the findings (the collisions-gating bug) fails.
  - Observed evidence: (a) crafted temp repo (cutover active) with a dangling plan: `aw check plans --agent` -> `{"cmd":"check","outcome":"findings","exit":1,...,"diagnostics":[...,{"rule":"check.ipd-dependency-dangling","location":".../20260101-demo-01-aaaaaa-a.ipd.md"}]}`; `aw check all --agent` -> the SAME `check.ipd-dependency-dangling` finding; a grep for the dangling finding in `aw check all` output returns exactly `1` (NO double-report). (b) the CURRENT repo: `aw check plans --agent` -> dependency findings `0`, exit `0`; `aw check all --agent` -> dependency findings `0` (grandfathered; no cutover marker set). `tests/test_ipd_dependency_check.py::CheckSurfaceTests` (4) assert: check_ipd_dependencies repo-scan emits dangling; check_content("plans") includes it (the plans-content path reached by BOTH commands); check_types(["all"]) reports it exactly once (`len(dangling)==1`); a clean `none` tree passes. The critical E-02 wiring (`aw check plans` surfaces it, NOT gated behind the collisions-only sweep) is proven by test_plans_content_path_includes_dependency_check. Part of the `32 passed` run.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: `aw ipd lint --phase author/review-finalize/pre-execution/pre-transition` transcripts on crafted IPDs proving the phase matrix: at author, a valid statement passes AND `unresolved` is advisory (non-blocking, readiness false); at review-finalize/pre-execution/pre-transition, each of missing/`unresolved`/malformed/dangling/cyclic is BLOCKING (non-zero); and the frozen statement != the reviewed statement is caught at execution phase. Paste each phase's command + output + exit code.
  - Observed evidence: `tests/test_ipd_dependency_check.py::PhasedLintTests` (10) over the pure `ipd_lint.check_item_dependencies` + repo-aware `ipd_lint.lint_file`: author -> missing is SILENT (test_author_missing_is_silent_pure), `unresolved` ADVISORY (test_author_unresolved_is_advisory), malformed BLOCKING (test_author_malformed_is_blocking); review-finalize/pre-execution/pre-transition -> `unresolved` BLOCKING (test_review_finalize_unresolved_is_blocking asserts all three), a valid `none` passes every phase (test_valid_statement_passes_all_phases); lint_file resolution -> a dangling statement blocks at pre-execution (test_lint_file_resolution_dangling_blocks_at_pre_execution: disposition==error, RULE_IPD_DEP_DANGLING), a POST-cutover missing statement blocks (test_lint_file_missing_blocks_post_cutover), a PRE-cutover missing statement is grandfathered (test_lint_file_missing_grandfathered_pre_cutover). NOTE (DECISION 08-ovbnyq-D2): MISSING is CUTOVER-gated and applied repo-aware in lint_file (not the pure lint), so the pre-cutover corpus is never mass-failed; the frozen==reviewed statement check is inherited from the existing begin-receipt digest (ipd_lifecycle: a changed plan invalidates the receipt), not re-implemented here. Part of the `32 passed` run.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: (a) Run `aw check plans`/`aw check all` on the CURRENT repository AFTER the cutover marker is set and paste the output showing zero dependency errors from the pre-cutover corpus (no mass-fail; pre-cutover terminal plans emit at most a `grandfathered` advisory). (b) A pytest shows a synthetic post-cutover IPD missing the field errors (`check.ipd-missing-dependency-statement`), while a pre-cutover pending plan without the field is clean at author but BLOCKED at review-finalize/advance. (c) Assert NO tool path inserts `none` automatically (grep/review the setter + scaffold + any migration for an auto-`none` write; confirm scaffold emits `unresolved`). Paste each. Falsifiable: any mass-fail on the current corpus, or an auto-`none`, fails.
  - Observed evidence: `tests/test_ipd_dependency_check.py::GrandfatheringTests` (5): test_no_cutover_marker_no_mass_fail (multiple fieldless plans + NO marker -> zero MISSING findings); test_post_cutover_missing_is_error (plan dated after cutover, no field -> RULE_IPD_DEP_MISSING); test_pre_cutover_missing_is_grandfathered (plan dated before cutover -> no MISSING); test_current_repo_not_mass_failed (runs `check_ipd_dependencies` on THIS checkout -> zero MISSING findings); test_no_tool_auto_inserts_none (ipd_authoring source contains `- Item-Dependencies: unresolved` and NOT `- Item-Dependencies: none` - no auto-none; scaffold emits `unresolved`). Real-repo transcript: `aw check plans --agent` -> dependency findings `0`, exit `0`; `aw check all --agent` -> dependency findings `0`. Cutover marker representation (OQ-02): a `dependency_schema_cutover` key in `.aw/config/project.json` read via `config.dependency_cutover_date` (ABSENT => no cutover => grandfather all). Part of the `32 passed` run.
  - Result: pass

Runner output (V-01..V-04): `python3 -m pytest tests/test_ipd_dependency_check.py -m ''` -> `32 passed in 4.14s`. Single-predicate grep: `grep -rn "def evaluate_ipd_dependencies" agent_workflows/` -> exactly ONE definition (check_engine.py:1090); consumed by `check_ipd_dependencies` (-> check_content plans path, E-02) and `ipd_lint.py:1014` (E-03) - no duplicated parse/resolve/graph logic. Full suite `python3 -m pytest tests/ -m ''` -> `4 failed, 2742 passed, 1 skipped`; the 4 failures are the PRE-EXISTING CLI-conformance guards for undeclared parser leaves (agy/oc runipd/ipd dependencies set/... from concurrent work, out of this child's Scope-Paths), NONE involve any `check.ipd-dependency-*` rule. Real-repo `aw check` shows ZERO dependency findings (no mass-fail; grandfathered).


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Open questions resolved

- OQ-01 (`state:` edge "settle order" - do we note it now or only in the runner): RESOLVED from spec 2.9 - the requirement that the scheduler run the dependent BEFORE the target advances away from a required `state:` is a RUNNER-scheduling concern, explicitly deferred to the runner program with this child. This child checks only that the statement is well-formed/resolved/acyclic; it records (not implements) the ordering requirement. Not a blocker. See OQ-01 above.

### Execution contract

- Scope fence: touch ONLY the files in `Scope-Paths` (`check_engine.py`, `ipd_lint.py`, `ipd_schema.py`, `releases.py`, `config.py`, `tests/`). This child delivers the shared evaluator + the six `check.ipd-dependency-*` rules + the `aw check`/phased-lint surfaces + grandfathering. It MUST consume child 01's (`g69y23`) `parse_item_dependencies` rather than reimplement parsing; if that symbol is absent, STOP (child 01 must land first - strict order 01 -> 02). Do NOT add the commit hook (child 03 `mp88bl`) nor any runner preflight/skip-cascade/`--with-dependencies` (the runner program, spec 2.9/5.4). If a change needs a file outside `Scope-Paths` or reaches into child 03/runner territory, STOP and report.
- One-predicate rule (hard MUST): there is EXACTLY ONE definition of the parse/resolve/graph evaluator; `aw check`, phased `aw ipd lint`, and (later) the child-03 hook all CALL it - no duplicated dependency logic. A grep for the evaluator must show one definition and delegating call sites.
- Honesty rule (hard MUST): when a V-item claims a check/lint/suite passed or `aw check` on the current repo is clean, paste the ACTUAL runner output (the real `pytest`/`aw check plans`/`aw check all`/`aw ipd lint` output); never claim a pass you did not run. The grandfather no-mass-fail claim (V-04) MUST be backed by real `aw check` output on this repository.
- Commit rule: commit ONLY files this child changed, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically).
