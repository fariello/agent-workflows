# IPD: Shared dependency graph predicate and check.ipd-dependency-* rule family across aw check and phased ipd lint, with grandfathering cutover

- Date: 2026-08-27
- Kind: child
- Concern: With the `Item-Dependencies` field parseable (child 01), nothing yet RESOLVES its edges, builds the cross-IPD graph, detects cycles/dangling targets, or enforces that the statement is present and resolved at the right lifecycle phases. It must be ONE shared pure predicate consumed by `aw check`, phased `aw ipd lint`, and (child 03) the hook, so they cannot diverge - exactly the bklggrad `evaluate_blocking_close` one-predicate-many-surfaces model. It also needs a grandfathering cutover so making the statement mandatory does not mass-fail the existing plan corpus. Spec 25kzda sections 2.9-2.11 + 4.3 define this precisely.
- Scope: Implement the shared dependency evaluator + its rule family + grandfathering. (1) One pure evaluator (in check_engine.py) that consumes a repo snapshot + IPD path set + phase + cutover marker: parses every `Item-Dependencies` once (via child 01's parser), resolves each typed id6 edge once against the identity index, builds ONE directed graph (IPD->IPD edges participate in cycle detection; spec/backlog targets are leaves), and returns the stable findings. (2) The `check.ipd-*dependency*` rule family with the spec's exact severities/assurance classes/recovery commands: `check.ipd-missing-dependency-statement` (error post-cutover + at review-readiness/pre-execution/pre-transition; advisory `grandfathered` for a pre-cutover draft or eligible terminal plan at the always-on author check), `check.ipd-dependency-unresolved` (advisory on a scaffolded draft at author; error at later phases; fires on the `unresolved` sentinel), `check.ipd-dependency-malformed` (error), `check.ipd-dependency-dangling` (error - a typed id6 with zero matches), `check.ipd-dependency-ambiguous` (fatal/identity - multiple matches or cross-type ambiguity), `check.ipd-dependency-cycle` (error - directed cycle). (3) Surface the SAME evaluator through `aw check` (repo-wide portable authority; folded into the cross-tree sweep next to the from-backlog/blocks-release checks) AND phased `aw ipd lint` (author = advisory/unresolved-permitted honest stub; review-readiness/pre-execution/pre-transition = blocking; the frozen statement must equal the reviewed statement at execution). (4) Grandfathering: record one dependency-schema cutover marker in repo policy; any IPD created at/after cutover must carry the field; pre-cutover terminal plans get the `grandfathered` advisory (no mass-fail); pre-cutover pending plans stay honest drafts but cannot advance to review-readiness/execution until resolved; NO tool bulk-inserts `none`. This child does NOT add the commit hook (child 03) nor the runner preflight/cascade (deferred to the runner program).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, agent_workflows/releases.py, agent_workflows/config.py, tests/
- Status: draft
- Set: ipddeps
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: ovbnyq

## Workflow history

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Add one shared pure dependency evaluator (parse-once, resolve-once, one DAG) surfaced as the `check.ipd-dependency-*` rule family across `aw check` and phased `aw ipd lint`, plus the grandfathering cutover so mandatoriness does not mass-fail existing plans - the bklggrad one-predicate-many-surfaces model applied to cross-IPD deps.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared evaluator + rule family

- [ ] E-01 Add one pure evaluator in check_engine.py (repo snapshot + IPD path set + phase + cutover marker -> structured findings): parse each `Item-Dependencies` (child 01 parser), resolve each typed id6 edge against the identity index, build one directed graph, detect cycles. Emit the six `check.ipd-dependency-*` findings with the spec's severities/assurance/recovery commands (missing / unresolved / malformed / dangling / ambiguous / cycle).
  - Depends on: none
  - Expected outcome: pure function returns the correct finding for each crafted input (clean, missing, unresolved, malformed, dangling, ambiguous, cyclic).
  - Execution state: pending

### Task group 2: surface across check + lint

- [ ] E-02 Surface the evaluator through `aw check` as repo-wide portable authority, deterministic path/rule order. CRITICAL WIRING NOTE: the existing cross-tree block in `check_engine.check_types` (near `check_blocks_release`/`check_from_backlog`/`check_release_gate_consistency`, check_engine.py:597-624) runs ONLY under the `["all"]`/`collisions=True` sentinel, so `aw check plans` (norm="plans", `collisions=False`, cli.py:6241-6246) does NOT reach it. Spec 2.10 lists `aw check plans` as a recovery command AND all dependency sources are IPDs (a plans-scoped concern), so the dependency evaluator MUST run for the `plans` type too - wire it into the plans-type check path (check_type/check_refs for "plans") so `aw check plans` surfaces it, AND ensure it also runs in the `all` sweep (do not double-report: run it once per invocation). Deterministic path then rule order.
  - Depends on: E-01
  - Expected outcome: BOTH `aw check plans` AND `aw check all` report every non-grandfathered dependency finding (verified by actually running both); a clean tree passes both; no finding is double-reported when running `all`.
  - Execution state: pending
- [ ] E-03 Wire the evaluator into phased `aw ipd lint`: author phase = advisory (unresolved permitted, honest stub); review-readiness/pre-execution/pre-transition = blocking; enforce that the frozen statement equals the reviewed statement at execution.
  - Depends on: E-01
  - Expected outcome: a placeholder-free draft with a valid statement passes author; an unresolved/missing/malformed/dangling/cyclic statement blocks at review-readiness and later phases.
  - Execution state: pending

### Task group 3: grandfathering cutover

- [ ] E-04 Record one dependency-schema cutover marker in repo policy/config; implement the grandfather rule: post-cutover IPDs must carry the field; pre-cutover terminal plans -> `grandfathered` advisory (no mass-fail); pre-cutover pending plans stay honest drafts but cannot advance until resolved; no tool bulk-inserts `none`.
  - Depends on: E-01
  - Expected outcome: existing corpus does not mass-fail `aw check`; a post-cutover IPD missing the field is an error; a pre-cutover pending plan is blocked only at advance/execute, not at author.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: A pytest table driving the pure evaluator over crafted repo snapshots shows EACH of the six findings fires on exactly its own fixture and on no other: clean (no finding); missing field -> `check.ipd-missing-dependency-statement`; `unresolved` value -> `check.ipd-dependency-unresolved`; a grammar/canonical-order/pairing/duplicate/self/none-mixture violation -> `check.ipd-dependency-malformed`; a typed id6 with zero matches -> `check.ipd-dependency-dangling`; a typed id6 with multiple owners (or cross-type collision) -> `check.ipd-dependency-ambiguous` at the fatal/identity class; an IPD->IPD directed cycle (including a 3-node cycle) -> `check.ipd-dependency-cycle`. Paste the passing test IDs/output, showing each finding carries the spec's exact severity/assurance/recovery-command text. Falsifiable: a fixture that should be clean but reports a finding, or a missing rule, fails.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Actual transcripts of BOTH `aw check plans` AND `aw check all` (or `aw check` with the appropriate type) run against (a) a crafted tree with a dangling AND a cyclic dependency IPD - each command reports both findings with the same rule IDs; and (b) the CURRENT clean repo - each exits 0 with zero dependency findings. Show that running `all` does not double-count a finding (a single occurrence per rule/path). Paste both transcripts + exit codes. Falsifiable: `aw check plans` NOT surfacing the findings (the collisions-gating bug) fails.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: `aw ipd lint --phase author/review-finalize/pre-execution/pre-transition` transcripts on crafted IPDs proving the phase matrix: at author, a valid statement passes AND `unresolved` is advisory (non-blocking, readiness false); at review-finalize/pre-execution/pre-transition, each of missing/`unresolved`/malformed/dangling/cyclic is BLOCKING (non-zero); and the frozen statement != the reviewed statement is caught at execution phase. Paste each phase's command + output + exit code.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: (a) Run `aw check plans`/`aw check all` on the CURRENT repository AFTER the cutover marker is set and paste the output showing zero dependency errors from the pre-cutover corpus (no mass-fail; pre-cutover terminal plans emit at most a `grandfathered` advisory). (b) A pytest shows a synthetic post-cutover IPD missing the field errors (`check.ipd-missing-dependency-statement`), while a pre-cutover pending plan without the field is clean at author but BLOCKED at review-finalize/advance. (c) Assert NO tool path inserts `none` automatically (grep/review the setter + scaffold + any migration for an auto-`none` write; confirm scaffold emits `unresolved`). Paste each. Falsifiable: any mass-fail on the current corpus, or an auto-`none`, fails.
  - Observed evidence:
  - Result: pending


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
