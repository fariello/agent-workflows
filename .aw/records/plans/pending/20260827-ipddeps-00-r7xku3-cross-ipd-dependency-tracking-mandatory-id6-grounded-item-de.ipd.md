# IPD: Cross-IPD dependency tracking: mandatory id6-grounded Item-Dependencies statement enforced through one shared predicate

- Date: 2026-08-27
- Kind: orchestrator
- Concern: There is NO machine-readable, enforced way to state that one IPD depends on another. Today inter-IPD ordering is carried only by `Set`/`Order` (a convention, not a validated dependency) and by prose "Child IPDs, sequence, and dependencies" tables in orchestrators (not machine-readable, not checked). The intra-plan `Depends on: <E-ids>` field is a DIFFERENT layer (steps within one IPD). So nothing prevents an IPD from being run before the IPD it depends on, and dependencies cannot even be STATED in a checkable form. Spec `25kzda` (`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`, sections 2.7-2.11 + 4.3) designs the fix; build-order map `40g511` places it at Phase R3. This Set graduates JUST that mechanism from the spec, independent of the full runner program.
- Scope: Deliver first-class, id6-grounded, enforced cross-IPD dependencies via one shared predicate across many surfaces (cloning the bklggrad `From-Backlog` one-predicate-many-surfaces model). Three children: (01) the `Item-Dependencies` metadata field + typed grammar (`none` | `executed:<id6>` | `exists:<type>:<id6>` | `state:<type>:<status>:<id6>`) + `aw ipd dependencies set` setter (parse, canonical-order, self/duplicate/none-mixture rejection), mirroring `From-Backlog` (ipd_schema recognition, releases-style write primitive, status_set hoisted write); (02) one shared pure graph predicate (parse-once, resolve-once, one DAG) surfaced as the `check.ipd-*dependency*` rule family across `aw check` and phased `aw ipd lint` (author advisory; review-readiness/pre-execution/pre-transition blocking), with the grandfathering cutover so existing plans are not mass-failed and scaffold emits `unresolved` (never blank, never `none`); (03) the opt-in commit-scoped `ipd-dependency-statement-gate` hook delegating to the same predicate. EXPLICITLY DEFERRED to the runner program (not this Set): the runner's dependency-graph PREFLIGHT, skip-cascade semantics, and `--with-dependencies` closure (spec 2.9/5.4) - those live with `aw <host> run`, which does not yet exist. This Set makes dependencies STATABLE and CHECKABLE; the runner later CONSUMES them.
- Scope-Paths: agent_workflows/ipd_schema.py, agent_workflows/status_set.py, agent_workflows/cli.py, agent_workflows/releases.py, agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_authoring.py, agent_workflows/hooks/, agent_workflows/engine.py, tests/
- Status: draft
- Set: ipddeps
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: r7xku3

## Workflow history
- 2026-08-27 draft (aw set): status set to draft

- 2026-08-27 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.
- 2026-08-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (added execution contract + resolved OQ-01/OQ-02 in gate), PR-002 (replaced V-01 placeholder with concrete falsifiable evidence), PR-003 (noted shared child gate gap, out of ledger scope).

## Goal

Make cross-IPD dependencies first-class: statable in a typed, id6-grounded `Item-Dependencies` field and enforced by one shared graph predicate across `aw check`, phased `aw ipd lint`, and an opt-in commit hook, so an IPD's prerequisites are machine-tracked instead of living in prose orchestrator tables. Graduates spec 25kzda sections 2.7-2.11 (R3), deferring the runner-side preflight/cascade to the runner program.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; each child carries its executable checklist. Its only execution step is the whole-Set integration check.

### Task group 1: whole-Set integration

- [ ] E-01 After children 01-03 execute and are green, confirm one shared predicate backs the setter, the `aw check` rules, the phased lint, and the hook (single definition; grep proves no duplicated dependency logic); an IPD carrying a valid `Item-Dependencies` lints clean; a dangling/cyclic one is flagged everywhere; full suite green.
  - Depends on: none
  - Expected outcome: one predicate consumed by all surfaces; stated deps are checkable end-to-end; suite green.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | g69y23 | `Item-Dependencies` field + grammar + `aw ipd dependencies set` setter (clone From-Backlog) | none |
| 02 | ovbnyq | shared graph predicate + `check.ipd-dependency-*` family across `aw check` + phased lint + grandfathering cutover | 01 |
| 03 | mp88bl | opt-in `ipd-dependency-statement-gate` pre-commit hook delegating to the predicate | 02 |

Strict order 01 -> 02 -> 03; orchestrator integration check runs last. (This IS the prose table this Set aims to replace with a machine field; once 01 lands, this Set's own children could themselves carry `Item-Dependencies` - a natural dogfood, optional.)

## Completion criteria (the whole Set is done only when)

- An IPD may carry a well-formed `Item-Dependencies` value and lints clean; `aw ipd dependencies set` writes/canonicalizes/clears it and persists on a no-op transition (01).
- One shared predicate parses + resolves + builds the DAG and drives `check.ipd-missing-dependency-statement`/`-unresolved`/`-malformed`/`-dangling`/`-ambiguous`/`-cycle` across `aw check` and phased lint, with the grandfathering cutover and scaffold emitting `unresolved` (02).
- An opt-in commit-scoped hook refuses a staged IPD with an invalid/cyclic dependency statement, delegating to the same predicate (03).
- Full test suite green.

## Cross-IPD validation

- ONE predicate: setter (01), `aw check`/lint rules (02), and hook (03) all call the same evaluator - no duplicated parse/resolve/graph logic (grep confirms a single definition).
- The `Item-Dependencies` field (01) and the intra-plan `Depends on: <E-ids>` field never collide (an E-id is never legal in Item-Dependencies; an id6 never legal in a Depends-on row).

## Deferred / out of scope (with reason)

- Runner-side dependency PREFLIGHT, skip-cascade, and `--with-dependencies` closure (spec 2.9/5.4): they belong to `aw <host> run`, which does not exist yet; this Set makes deps statable/checkable, the runner later consumes them.
- `From-Spec` (a sibling link field): separate concern; may clone the same pattern later.
- Making `Item-Dependencies` a hard cross-tree runtime prerequisite in `aw check all` beyond the phased-lint gates: covered by the grandfathering policy in 02; no broader rollout here.

## Scope check

- Over-scope: none (runner preflight/cascade explicitly deferred).
- Under-scope: none (field + setter + predicate + rules + grandfathering + opt-in hook is the complete statable-and-checkable deliverable).

## Required tests / validation

Aggregate of children: field/grammar/setter round-trip + no-op persist (01); each `check.ipd-dependency-*` rule fires on a crafted fixture and is clean otherwise, grandfather advisory vs post-cutover error, scaffold emits `unresolved`, phased-lint blocking at review-readiness/pre-execution/pre-transition (02); hook refuses a staged invalid/cyclic statement and passes a valid one, opt-in install idempotent (03). Plus the single-predicate grep check.

## Open questions

### OQ-01: Should this Set's own children dogfood Item-Dependencies (03 declares executed:02, 02 declares executed:01)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Attractive dogfood once 01 lands the field, but it would make THIS Set's plans require their own new field mid-Set (grandfathering interaction). RESOLVED (see gate "Open questions resolved"): do NOT self-apply during this Set's execution; adopt Item-Dependencies for subsequent Sets after cutover. Revisit at 01's completion.

### OQ-02: Is the schema cutover marker a repo policy value or a fixed commit?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Spec 2.11 says "one dependency-schema cutover commit in its policy." RESOLVED (see gate "Open questions resolved"): child 02 (E-04) decides the exact representation (a policy/config value vs a recorded commit) at implementation; either satisfies the grandfathering requirement. Not an orchestrator-level or human decision.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) A grep over `agent_workflows/` shows exactly ONE definition of the dependency parse/resolve/graph evaluator (the child-02 predicate) and that the setter (01), the `aw check`/lint rules (02), and the hook (03) all call it - paste the grep command and its output showing the single definition and the delegating call sites. (b) An IPD carrying a well-formed `Item-Dependencies` value lints CONFORMING at author/review-finalize/pre-execution/pre-transition - paste the `aw ipd lint` output. (c) A crafted dangling AND a crafted cyclic statement each fire the matching `check.ipd-dependency-dangling` / `check.ipd-dependency-cycle` finding under `aw check` AND `aw ipd lint` AND the opt-in hook (same rule ID from each surface) - paste each surface's output. (d) The full test suite is green - paste the actual `pytest` (or the repo's `run_checks.py`) summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Open questions resolved

- OQ-01 (should this Set's own children dogfood `Item-Dependencies`): RESOLVED for authoring - do NOT self-apply during this Set's execution. Adopting the new field on this Set's own in-flight children would entangle them with the very grandfathering cutover they introduce (child 02). Adopt `Item-Dependencies` for subsequent Sets after the cutover lands. Not a blocker; revisit at 01's completion. See OQ-01 above.
- OQ-02 (is the schema cutover marker a policy value or a fixed commit): RESOLVED as a child-02 implementation choice, not an orchestrator-level decision. Spec 2.11 requires exactly one dependency-schema cutover commit recorded in repository policy; child 02 (E-04) selects the concrete representation (a policy/config value vs. a recorded commit hash) at implementation, and either satisfies the grandfathering requirement. Not a blocker for approving this orchestrator. See OQ-02 above.

### Execution contract

- Scope fence: this orchestrator authors NO code and edits NO source. Its ONLY execution action is E-01: the whole-Set integration check AFTER children 01 (g69y23), 02 (ovbnyq), and 03 (mp88bl) are executed and green, plus recording that verification here. Touch ONLY this orchestrator file (its own lifecycle artifact). If the integration check surfaces a gap (duplicated dependency logic, a surface that does not consume the shared predicate, a stated dependency not checkable end-to-end), STOP and report - do NOT expand scope, do NOT edit a child in place; open a corrective IPD instead. Do NOT execute any child from this plan; children are approved and executed independently in the strict order 01 -> 02 -> 03.
- Honesty rule (hard MUST): when V-01 reports the full suite green, the single-predicate grep result, or any check passed, paste the ACTUAL runner/command output (the real `pytest`/`grep`/`aw check`/`aw ipd lint` output); never claim a pass you did not run.
- Commit rule: commit ONLY this orchestrator's own changed file, path-scoped (`git commit -m <msg> -- <this plan path>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (which runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically). Because this is an ORCHESTRATOR, finalize it only after all three children are themselves executed.
