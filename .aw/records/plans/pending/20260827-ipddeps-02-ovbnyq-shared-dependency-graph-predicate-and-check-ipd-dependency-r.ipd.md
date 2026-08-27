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

- [ ] E-02 Fold the evaluator into the cross-tree `aw check` sweep (next to the from-backlog/blocks-release checks) as repo-wide portable authority, deterministic path/rule order.
  - Depends on: E-01
  - Expected outcome: `aw check` (and `aw check plans`) report every non-grandfathered dependency finding; clean tree passes.
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

- `check_engine.evaluate_blocking_close` + the from-backlog rule family is the exact one-predicate-many-surfaces precedent (setter/check/hook call one evaluator). Cross-tree checks fold into the sweep near `check_blocks_release`/from-backlog at check_engine.
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
- Status: open
- Owner: none
- Resolution or deferral rationale: Spec 2.9 notes an already-satisfied `state:` edge requires the scheduler to run the dependent before the target advances away from that state. That is a RUNNER-scheduling concern; this child only checks the statement is well-formed/resolved. Defer the ordering guarantee to the runner program; record the requirement here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: TODO falsifiable evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

TODO: approval + execution gate prose (execution contract, post-gate lifecycle move).
