# IPD: Phase 1: versioned policy schema and shared aw check (machine-readable JSON) with positive and adversarial fixtures

- Date: 2026-08-25
- Kind: child
- Concern: Findings bu9yij Phase 1 (the "host-independent deterministic core" all other layers must call): a single policy engine, surfaced through the EXISTING `aw check` machine-readable output (`--agent` = `aw.agent/v1` JSONL, `--json` = structured JSON; there is NO `--format json` flag - enrich the existing surface, do NOT add a new flag or a forked output path), where each finding carries a stable rule id, severity + assurance class, affected artifact/location, observed-vs-required state, the exact recovery command, and whether the result is deterministic/heuristic/externally-attested. The toolkit already has a unified `check_engine` (check_engine.py) producing a `Drift` list, but it is not yet organized as a versioned policy schema with the full finding shape, and it lacks a systematic positive+adversarial fixture corpus. Phases 2-5 (atomic commands, hooks, CI) must all call THIS engine so results never diverge by host.
- Scope: Formalize the shared policy engine on top of the existing `check_engine`: (1) a VERSIONED policy schema (a schema_version + a registry of rules, each with stable id, severity, assurance class from the Phase-0 catalog, and determinism/heuristic/attested tag); (2) enrich the `Drift`/finding shape and the existing `aw check` machine-readable output (`--agent`/`--json`) to include observed-vs-required, the exact recovery command, and the determinism/assurance tags; (3) a fixture corpus with POSITIVE cases (clean artifacts pass) and ADVERSARIAL cases (each cataloged invariant's violation is detected) drawn from the Phase-0 catalog and findings section 9 (code-before-IPD, hand-edited status, terminal transition without evidence, out-of-scope staged tree, claimed-but-unrun tests, stale-tree evidence, missing/disabled/malformed hook, etc.). This child does NOT add the atomic commands/hooks/CI; it makes the engine the single, versioned, well-shaped source of truth they will all call. Reuse the existing per-type validators (check_engine composes them); do not fork. Also includes the first concrete authoring-lifecycle rule (detect-and-nudge): a `draft` IPD whose authoring placeholders are all resolved is flagged with the `aw ipd set to-review` recovery command, fixing the recurring miss where a finished draft is never advanced to `to-review` (scaffold correctly emits `draft` for a stub at ipd_authoring.py:131; nothing advances it when authoring completes).
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/artifact_core.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_authoring.py, agent_workflows/cli.py, tests/
- Status: reviewed
- Set: agentadhere
- Order: 2
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: uisjns

## Workflow history
- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001 --format json corrected to --agent/--json (x6), PR-002 gate execution contract, PR-003 backward-compat characterization test added (HIGH under-scope), PR-004 V-01..V-03 concrete evidence, OQ-01/OQ-02 resolved

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Formalize the existing `check_engine` into a versioned policy engine surfaced through the existing `aw check` machine-readable output (`--agent`/`--json`; no new `--format json` flag), with each finding carrying rule id, severity, assurance class, observed-vs-required, exact recovery command, and determinism tag, plus a positive + adversarial fixture corpus, so every later layer calls one source of truth.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: versioned schema + finding shape

- [ ] E-01 Add a versioned policy schema over `check_engine`: a rule registry keyed by stable rule id, each with severity, assurance class (from Phase-0 catalog), and a determinism/heuristic/attested tag; enrich the finding/`Drift` shape (artifact_core.py:245) + the existing `aw check --agent`/`--json` output to include observed-vs-required, the exact recovery command, and the tags. Enrich the existing `Drift` (or a superset) WITHOUT breaking existing `aw check <type>` callers, `render_agent_drift`/`drift_exit_code`, or the two installed hooks that delegate to `check_engine` rules (backward-compatible: existing consumers keep working; see V-01).
  - Depends on: none
  - Expected outcome: `aw check --agent`/`--json` emits findings with the full documented shape and a schema_version; existing `aw check <type>` output/exit-code behavior is preserved.
  - Execution state: pending

### Task group 2: fixture corpus

- [ ] E-02 Build a positive + adversarial fixture corpus (from the Phase-0 catalog and findings section 9): clean artifacts pass; each cataloged invariant's violation is detected with the right rule id and recovery command.
  - Depends on: E-01
  - Expected outcome: a test suite where every positive fixture is clean and every adversarial fixture triggers exactly the expected rule.
  - Execution state: pending

### Task group 3: draft-readiness detect-and-nudge rule

- [ ] E-03 Add a shared `authoring_placeholders_resolved(plan_text) -> bool` predicate (detects remaining authoring placeholders: `Concern: TODO.`/`Scope: TODO.`/`Scope-Paths: TODO`/`Goal` TODO / `TODO.` E-V bodies from the scaffold at ipd_authoring.py:120-160) and a policy rule `check.ipd-draft-ready-to-review`: a plan at `Status: draft` with NO remaining placeholders is flagged (severity info/advisory) with the exact recovery command `aw ipd set to-review <id6>`; a draft that still has placeholders is silent (correctly still a stub). Surface the SAME rule as a passing-nudge line from `aw ipd lint --phase author` when it passes on a placeholder-free draft. DETECT-AND-NUDGE only: never auto-flip the status (keeps `to-review` an explicit, tool-authored transition).
  - Depends on: E-01
  - Expected outcome: `aw check`/`aw ipd lint --phase author` on a placeholder-free `draft` emits the advance nudge with the `aw ipd set to-review` command; a draft with placeholders emits nothing; no status is auto-changed.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `check_engine` (check_engine.py) already composes the per-type validators into a `Drift` list and is consumed by `aw check <type>` - EXTEND it, do not fork; reuse `check_names`/`check_content`/`check_refs`/`check_collisions` and the release/backlog rules.
- `_core.Drift` (artifact_core) is the current finding type; enrich it (or wrap it) rather than introducing a parallel finding type.
- Findings section 9 enumerates the adversarial cases to encode as fixtures.

## Findings

The engine exists; Phase 1 is about GIVING IT A CONTRACT (versioned schema + rich finding shape) and PROVING IT (adversarial fixtures), so downstream layers can depend on stable rule ids and recovery commands.

## Proposed changes (ordered, validatable)

1. `check_engine.py`/`artifact_core.py`: versioned rule registry + enriched finding shape.
2. `cli.py`: the existing `aw check --agent`/`--json` output emits the full shape + schema_version (extend the current `aw.agent/v1`/structured-JSON surface; no new `--format json` flag).
3. `check_engine.py`/`ipd_lint.py`/`ipd_authoring.py`: shared `authoring_placeholders_resolved` predicate + `check.ipd-draft-ready-to-review` detect-and-nudge rule; `aw ipd lint --phase author` prints the advance hint on a placeholder-free draft.
4. `tests/`: positive + adversarial fixture corpus + draft-readiness detect/nudge/no-auto-flip cases.

## Deferred / out of scope (with reason)

- Atomic commands (phase 2), event-state (phase 3), hooks (phase 4), CI (phase 5): they CALL this engine but are separate children.

## Scope check

- Over-scope: none.
- Under-scope: none (schema + finding shape + fixtures is the phase-1 deliverable).

## Required tests / validation

- `aw check --agent`/`--json` output conforms to the documented finding shape (schema_version, rule id, severity, assurance class, observed-vs-required, recovery command, determinism tag).
- Backward compatibility (anti-regression, rubric D): existing `aw check <type>` callers, `render_agent_drift`/`drift_exit_code`, and the two installed hooks (`status_untooled_gate`, `executed_transition_gate`) that delegate to `check_engine` rules continue to work unchanged - a characterization test pins the pre-change `aw check` output/exit codes and confirms they are preserved after the `Drift` enrichment.
- Every positive fixture passes clean; every adversarial fixture triggers exactly its expected rule id and recovery command.
- Determinism: repeated runs on the same tree produce identical findings.
- Draft-readiness: `aw check`/`aw ipd lint --phase author` on a placeholder-free `draft` emits `check.ipd-draft-ready-to-review` with the `aw ipd set to-review <id6>` recovery command; a draft that still has authoring placeholders emits nothing; the status is NEVER auto-changed (detect-and-nudge, not auto-flip).

## Spec / documentation sync

- Document the policy schema + finding shape (a spec or docs page); reference the Phase-0 catalog.

## Open questions

### OQ-01: Version the schema separately from the existing check output, or bump a shared schema_version?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED - use a dedicated policy `schema_version` for the rule registry so hooks/CI can assert compatibility independently, AND reconcile it with the existing `SCHEMA_VERSION` already emitted at cli.py:6641 (do not introduce a conflicting second versioning scheme). Concretely: add the policy schema_version to the enriched `aw check` machine-readable output and keep it consistent with the established `aw.agent/v1` envelope. Not a blocker.

### OQ-02: What exactly counts as an "authoring placeholder" for the draft-readiness predicate?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED - the predicate matches the LITERAL scaffold placeholder tokens emitted at ipd_authoring.py:120-160 (verified in-tree: `- Concern: TODO.` at :120, `- Scope: TODO.` at :121, `- Scope-Paths: TODO` at :129, the `## Goal` TODO body, and `TODO`-bearing E/V leaves). Conservative rule: presence of ANY known scaffold placeholder means still-drafting (silent); absence of ALL means ready-to-nudge. Match the anchored scaffold strings (not a bare substring `TODO`) so legitimate prose containing "TODO" does not false-positive; V-03(d) asserts this. Not a blocker.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: (a) `aw check --agent` (and `--json`) on a fixture with findings emits each finding with the full documented shape - schema_version, stable rule id, severity, assurance class, observed-vs-required, exact recovery command, determinism/heuristic/attested tag (paste one JSONL/JSON finding record showing every field); (b) the rule registry is versioned (a `schema_version`/`SCHEMA_VERSION` value is present and reconciled with the existing one at cli.py:6641); (c) DETERMINISM: two consecutive `aw check` runs on the same tree produce byte-identical machine-readable output (paste a diff showing no difference); (d) BACKWARD COMPATIBILITY (anti-regression): a characterization test captures the pre-change `aw check <type>` output + exit codes, and after enrichment the existing `aw check <type>` callers, `render_agent_drift`/`drift_exit_code`, and both installed hooks (`status_untooled_gate`, `executed_transition_gate`) still pass - paste the test run showing the pinned behavior is unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a test suite where EVERY positive fixture yields zero findings (clean) and EVERY adversarial fixture (drawn from the Phase-0 catalog + findings section 9: code-before-IPD, hand-edited status, terminal transition without evidence, out-of-scope staged tree, claimed-but-unrun tests, stale-tree evidence, missing/disabled/malformed hook) triggers EXACTLY its expected rule id and recovery command (paste the test run; the assertion is per-fixture rule-id equality, not merely "some finding fired"). Each catalog invariant has at least one adversarial fixture (coverage confirmed against the Phase-0 catalog).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: (a) `aw check` / `aw ipd lint --phase author` on a placeholder-free `draft` IPD emits `check.ipd-draft-ready-to-review` with the exact recovery command `aw ipd set to-review <id6>` (paste output); (b) the SAME plan while it still contains a scaffold authoring placeholder (e.g. `Concern: TODO.`) emits NOTHING for that rule (paste output); (c) the status is NEVER auto-changed by the rule (assert the file's `Status:` is unchanged after the check runs - detect-and-nudge, not auto-flip); (d) the `authoring_placeholders_resolved` predicate does not false-positive on legitimate prose containing the word "TODO" (a fixture with narrative "TODO" that is not a scaffold placeholder is treated as ready) per OQ-02.
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: three E-items, each one focused pass with its own verification surface - E-01 (versioned registry + `Drift` enrichment + `aw check` output, one cohesive engine-shape change), E-02 (fixture corpus), E-03 (draft-readiness detect-and-nudge rule). Kept as one child because all three center on the same shared engine (`check_engine`) and share the Phase-0 catalog as input; they do not warrant separate child IPDs.

### Open questions resolved

- OQ-01 (schema versioning): RESOLVED - dedicated policy `schema_version`, reconciled with the existing `SCHEMA_VERSION` (cli.py:6641); no conflicting second scheme.
- OQ-02 (what is an authoring placeholder): RESOLVED - match the anchored literal scaffold tokens at ipd_authoring.py:120-160, not a bare `TODO` substring; V-03(d) guards against false positives on legitimate prose.

### Execution contract

- Scope fence: touch ONLY the files in `Scope-Paths` - `agent_workflows/check_engine.py`, `agent_workflows/artifact_core.py`, `agent_workflows/ipd_lint.py`, `agent_workflows/ipd_authoring.py`, `agent_workflows/cli.py`, and `tests/`. EXTEND `check_engine` and enrich `Drift`; do NOT fork a parallel finding type or a new output path, and do NOT add the atomic commands (phase 2), event-state (phase 3), hooks (phase 4), or CI (phase 5). Depends on the Phase-0 catalog (child gfokao) being available to source assurance classes. If the work seems to need files outside this fence, STOP and report.
- Anti-regression MUST: preserve existing `aw check <type>` output/exit-code behavior and the two installed hooks; the V-01(d) characterization test is a hard requirement, not optional.
- Honesty rule (hard MUST): when a V-item reports a test/`aw check` run passed, paste the ACTUAL runner output; never claim a pass you did not run.
- Commit rule: commit ONLY this child's own changed files, path-scoped (`git commit -m <msg> -- <paths>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically).
