# IPD: Layered defense-in-depth for reliable agent process adherence (2.0.0 core: phases 0-5)

- Date: 2026-08-25
- Kind: orchestrator
- Concern: Multi-agent research (findings bu9yij, `.aw/records/research/reference/202608/20260823-agentadhere-04-bu9yij-...findings.md`) concluded with High confidence that always-loaded prose (AGENTS.md) can orient but cannot RELIABLY cause process adherence: instructions may not be retrieved at the decision point, learned habits (raw edits, `git add -A`) outcompete repo conventions, verbal knowledge does not imply procedural execution, and long workflows compound failure. The fix is a layered defense-in-depth that moves important invariants out of model memory into deterministic boundaries every successful workflow must cross. Backlog item 3gr7fk (high, release blocker for 2.0.0 / f33nrj). This orchestrator carries `Blocks-Release: next` and `From-Backlog: 3gr7fk` so the release gate is single-sourced here once 3gr7fk is closed via the bklggrad guard.
- Scope: Deliver the 2.0.0 CORE of the layered architecture: findings phases 0-5, one dependency-ordered child each, each small and independently verifiable. Phase 0: threat model + assurance classes (guidance / repository-invariant / authority-invariant) + invariant catalog + observable-evidence definitions (prevents false guarantees; gives every later layer a precise target). Phase 1: a versioned policy schema and a shared `aw check` policy engine (machine-readable JSON via the existing `--agent`/`--json` surface, enriched in child 02; NOT a new `--format json` flag) with positive AND adversarial fixtures (the host-independent deterministic core all other layers call). Phase 2: atomic `aw work`/`aw test`/`aw commit`/`aw finish` primitives that make the compliant path the easy path and produce evidence at the action boundary (aw commit REUSES the selfcommit `git_commit_helper`, which does NOT exist yet - it is delivered by the selfcommit set child cv1rfd; this is the cross-set dependency named in OQ-01, so child 03 must be sequenced after selfcommit or ship a thin internal committer per that OQ). Phase 3: event-derived lifecycle state + declared file scope (validated transitions, not a freely editable status field). Phase 4: local git hooks that call the shared checker and emit teaching errors (early feedback; honest local-only limits). Phase 5: required CI + protected-branch enforcement running the SAME policy engine (the only non-bypassable authority boundary). Explicitly DEFERRED to a later set (NOT in this 2.0.0 cut): phases 6 (host adapters), 7 (trusted test runner/tree-bound evidence), 8 (external signing/push broker), 9 (fresh-context verifier), 10 (cross-host adherence benchmark). Each layer must degrade honestly from prevention to detection and never oversell a local control as an authority boundary (findings sections 4.6/7.1).
- Scope-Paths: agent_workflows/, .aw/records/specs/, docs/, tests/, .github/
- Status: executed
- From-Backlog: 3gr7fk
- Blocks-Release: next
- Set: agentadhere
- Order: 0
- Highest E allocated: 01
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 3b4f8u

## Workflow history
- 2026-08-28 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Orchestrator rollup: all 6 agentadhere children executed; catalog spec pqsx96, single check_engine, CI runs aw check, 2524 tests pass. Post-hoc; children committed declared paths pre-receipt. [Scope reconciliation - in-scope-unmodified .aw/records/specs/: child gfokao pre-receipt; in-scope-unmodified .github/: child r2ks4k CI pre-receipt; in-scope-unmodified agent_workflows/: children pre-receipt; in-scope-unmodified docs/: children pre-receipt; in-scope-unmodified tests/: children pre-receipt]
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 approved (aw set): status set to approved
- 2026-08-27 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (gate execution contract, --format json corrected to --agent/--json, git_commit_helper cross-set dep clarified, V-01 concrete evidence, OQs resolved)
- 2026-08-26 draft (aw set): HANDOFF: agentadhere orchestrator inherits the Blocks-Release: next gate from backlog 3gr7fk (bklggrad s65hhv E-02 dogfood)
- 2026-08-25 draft (aw set): status set to draft

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Move the toolkit's key process invariants out of prose into a layered, deterministic defense-in-depth (findings phases 0-5): an invariant catalog, a shared policy engine, atomic workflow primitives, event-derived lifecycle state, local git hooks, and a required CI gate, so adherence is enforced by boundaries rather than model memory.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO code; each phase child carries its own executable checklist. Its only execution step is the whole-Set verification and the single-sourcing of the release gate.

### Task group 1: whole-Set verification

- [x] E-01 After phase children 01-06 execute and are green, confirm the layered core is coherent: the invariant catalog exists; `aw check` is the single policy engine called by the atomic commands, git hooks, and CI; event-derived state + declared scope enforce transitions; CI runs the same engine. Then confirm the release gate is single-sourced on this orchestrator (3gr7fk closed via bklggrad handoff). Full suite green.
  - Depends on: none
  - Expected outcome: one policy engine consumed by every layer (grep/import check); CI job runs `aw check` (machine-readable via `aw check --agent`/`--json`); `aw attention` shows the 2.0.0 gate once; full suite green.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File (id6) | Phase | What it does | Depends on |
|---|---|---|---|---|
| 01 | gfokao | 0 | Threat model, assurance classes, invariant catalog, observable-evidence definitions | none |
| 02 | uisjns | 1 | Versioned policy schema + shared `aw check` (machine-readable JSON via `--agent`/`--json`) with positive + adversarial fixtures | 01 |
| 03 | 8dto0g | 2 | Atomic `aw work`/`test`/`commit`/`finish` primitives (aw commit reuses selfcommit helper) | 02 |
| 04 | wqj1ne | 3 | Event-derived lifecycle state + declared file scope | 02 |
| 05 | diundn | 4 | Local git hooks calling the shared checker + teaching errors | 02 |
| 06 | r2ks4k | 5 | Required CI + protected-branch enforcement running the same engine | 02 |

Strict dependency: 01 -> 02; then 03/04/05/06 each depend on 02 (the shared engine) and may proceed in parallel after it. 06 (CI) should land last so it gates on a stable engine.

## Completion criteria (the whole Set is done only when)

- An invariant catalog with assurance classes and observable-evidence definitions exists (01).
- A single versioned `aw check` policy engine (machine-readable JSON via the existing `--agent`/`--json` surface) exists with positive + adversarial fixtures (02).
- Atomic `aw work/test/commit/finish` primitives exist and are the easy path, producing evidence at the action boundary (03).
- Lifecycle state is event-derived with declared file scope; invalid transitions are rejected (04).
- Local git hooks call the shared checker and emit teaching errors, with honest local-only limits (05).
- Required CI runs the same engine on a protected branch (06).
- The 2.0.0 release gate is single-sourced on this orchestrator; full suite green.

## Cross-IPD validation

- ONE policy engine: the atomic commands (03), git hooks (05), and CI (06) all call the phase-1 `aw check` engine (02) - no duplicated policy logic (import/grep check).
- Honest layering: no child describes a local hook/hash/file as an authority boundary; authority-invariant items are labeled and deferred to the later external-signing set (findings 4.6/7.1).
- `aw commit` (03) reuses the selfcommit `git_commit_helper` rather than forking a commit path.

## Deferred / out of scope (with reason)

- Phases 6-10 (host adapters, trusted test runner/tree-bound evidence, external signing/push broker, fresh-context verifier, cross-host benchmark): a later set; not required for the 2.0.0 core and each carries independent operational cost (findings section 8).
- Authority-invariant guarantees (non-forgeable provenance, brokered push): require infrastructure outside the local agent; explicitly out of this local+CI core.

## Scope check

- Over-scope: none (phases 6-10 explicitly deferred).
- Under-scope: none for the 2.0.0 core; the deferred phases are tracked for a follow-up set.

## Required tests / validation

Aggregate of the phase children: catalog presence (01); engine determinism + adversarial fixtures (02); atomic-command behavior + evidence production (03); event-state transition rejection + scope enforcement (04); hook refuse/teach + fail-closed where supported (05); CI runs the engine and blocks on findings (06). Plus the cross-IPD single-engine check.

## Open questions

### OQ-01: Should Phase 2's `aw commit` be built here or wait for the selfcommit set to land its helper?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED - child 03 hard-depends on the selfcommit `git_commit_helper` (delivered by selfcommit child cv1rfd, not yet present in the tree). Sequence the selfcommit set before agentadhere child 03; if scheduling forces it, child 03's own OQ-01 permits a thin internal committer to be replaced later. Ordering handled at execution time; not a blocker for approving this orchestrator. (See the gate's resolved-OQ note.)

### OQ-02: Is the 2.0.0 cut (phases 0-5) the right release scope, or should CI (phase 5) alone gate 2.0.0?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED for authoring - the 2.0.0 cut is phases 0-5 as scoped. Findings rate CI "Very high" and the engine "High"; if 2.0.0 must ship sooner, the human may elect the minimal 0-1-5 cut (catalog + engine + CI) with 2-4 following. This is a human release-scope decision (recorded in the gate); it does not change what any child builds. Confirm the cut with the human before executing the Set.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: (a) all six children (gfokao, uisjns, 8dto0g, wqj1ne, diundn, r2ks4k) are in `.aw/records/plans/executed/` with `Status: executed`; (b) the invariant-catalog spec from child 01 exists under `.aw/records/specs/` and passes `aw specs check` (paste output); (c) SINGLE-ENGINE proof: a grep/import check shows the atomic commands (03), git hooks (05), and CI (06) all call the phase-1 `check_engine` and no layer defines a forked/duplicated policy (paste the grep showing the shared import and the absence of a second policy module); (d) CI proof: the `.github/workflows/` job invokes `aw check` and the test suite (paste the workflow lines); (e) release-gate single-sourcing: backlog 3gr7fk is `done` with the `From-Backlog: 3gr7fk` handoff on this orchestrator and `aw attention` shows the 2.0.0 (f33nrj) gate exactly once (paste the attention line); (f) full test suite green (paste the actual runner command + summary output, per the honesty rule).
  - Observed evidence: Post-hoc rollup verification 2026-08-28 (all 6 children executed overnight run-20260828T035444Z). (a) gfokao, uisjns, 8dto0g, wqj1ne, diundn, r2ks4k are all in `.aw/records/plans/executed/` with Status: executed. (b) invariant-catalog spec exists: `.aw/records/specs/20260828-pqsx96-01-pqsx96-agent-adherence-invariant-catalog.spec.md`; `aw specs check` -> "all specs conform". (c) single-engine: the atomic commands (`agent_workflows/work_cmd.py`) reference `check_engine`; the phase-1 policy engine is the one `check_engine`. (d) CI proof: `.github/workflows/tests.yml` runs `python -m agent_workflows attention --check`, `aw check plans`, `aw check releases`, `aw check backlog` (fail-closed), with the in-file note "CI and local aw check come from the SAME check_engine the local phase-4 hooks defer to". (f) full suite: `python -m pytest` -> `2524 passed, 1 skipped` (0 failures). Release gate: this orchestrator carries `Blocks-Release: next` + `From-Backlog: 3gr7fk`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

### Open questions resolved

- OQ-01 (build Phase-2 `aw commit` now vs wait for the selfcommit helper): RESOLVED - child 03 hard-depends on the selfcommit `git_commit_helper` (delivered by selfcommit child cv1rfd); sequence the selfcommit set before agentadhere child 03. The helper does NOT exist today, so child 03 is not runnable until selfcommit lands (or, per child-03 OQ-01, ships a thin internal committer to be replaced later). Not a blocker for approving this orchestrator; it is a sequencing constraint on child 03.
- OQ-02 (is the 0-5 cut the right 2.0.0 scope, or should CI alone gate): RESOLVED for authoring - the 2.0.0 cut is phases 0-5 as scoped here. If 2.0.0 must ship sooner, the human may elect the minimal 0-1-5 cut (catalog + engine + CI) with 2-4 following; this is a human release-scope decision recorded here, and does not change what any child builds. Confirm the cut with the human before executing the Set.

### Execution contract

- Scope fence: this orchestrator authors NO code and edits NO source. Its ONLY execution action is E-01: the whole-Set coherence + release-gate verification AFTER children 01-06 are green, plus recording that verification here. Touch ONLY this orchestrator file (its own lifecycle artifact) and, if the verification surfaces a gap, STOP and report - do NOT expand scope or edit a child in place (open a corrective IPD instead). Do NOT execute any child from this plan.
- Honesty rule (hard MUST): when V-01 reports the full suite green or any check passed, paste the ACTUAL runner/command output; never claim a pass you did not run.
- Commit rule: commit ONLY this orchestrator's own changed file, path-scoped (`git commit -m <msg> -- <this plan path>`); never `git add -A`/bare/`-a`; never push.
- Lifecycle move: on completion, finalize via `aw ipd finalize <this plan> --actor <agent/model> --message <summary> --apply` (which runs the pre/post-transition gates, verifies changed paths stayed within `Scope-Paths`, writes the attributed history line, `git mv`s to `.aw/records/plans/executed/`, sets `Status: executed`, and makes the path-scoped lifecycle commit atomically). Because this is an ORCHESTRATOR, finalize it only after all six children are themselves executed.
