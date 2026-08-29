# IPD: runner preflight must consume the shared Item-Dependencies predicate

- Date: 2026-08-29
- Kind: child
- Concern: The runner cannot read `Item-Dependencies`. `oc_runipd._DEPS_RE` matches only the legacy `Dependencies:`/`Depends-on:` field, so 11 pending plans declare edges the queue silently ignores, every queue item is frozen with `dependencies: []`, and ordering falls back to Set/Order, which spec `25kzda` calls only a tiebreaker.
- Scope: Delete the runner's private dependency parser and consume the SHARED predicate the other four surfaces already use, then implement the runtime satisfaction semantics from spec `25kzda` sections 2.9/5.4 (wait for in-queue prerequisites, evaluate external targets from frozen state, fail closed on malformed/dangling/cyclic statements before any session starts). Excludes changes to the dependency GRAMMAR, to the four surfaces that already consume it correctly, and excludes `--with-dependencies` closure expansion.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_item_dependencies.py
- Item-Dependencies: executed:af7i6p
- Status: to-review
- Set: lanetruth
- Order: 3
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 8guhs0
- Blocks-Release: next
- From-Backlog: y9lcem

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-29 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `y9lcem`, which was filed from finding SR-001 of the `25kzda` spec review. Declares `executed:af7i6p` so the tool-identity pin lands first; this plan edits the same driver modules and its own runtime behavior would otherwise be unverifiable inside a lane running stale tooling.
- 2026-08-29 /plan-review of orchestrator y0gg8o (opencode (its_direct/pt3-claude-opus-5-1m-us)): CROSS-REFERENCE. (1) This plan's OQ-02 (`Blocking: yes`, `Owner: maintainer`), whose gate forbids execution while open, is RESOLVED in the owning orchestrator `y0gg8o` as OQ-03: ADMIT a fieldless plan with an advisory and DELEGATE the missing-statement decision to the shared evaluator plus the cutover marker; do NOT hardcode a runner-local refuse-or-admit rule in E-02. Decisive evidence: `config.dependency_cutover_date('.')` returns `None` (measured) and `config.py:275-281` documents that an absent marker grandfathers everything, so a refusing runner would be STRICTER than `aw check`/`aw ipd lint` and would recreate the very divergence this plan removes; `ipd_lint.py:895-902` already encodes the intended deferral. Also 27 of 27 pending IPDs carry the field, so nothing queued is affected. This plan's own OQ-02 MUST be updated to `Status: resolved` citing y0gg8o OQ-03 before it is executed. (2) The `executed:af7i6p` rationale above is overstated: `begin` is never lane-shadowed (see the y0gg8o child-table correction); the edge stands as edit serialization. (3) Corrected counts: 27 of 27 pending IPDs declare the field and 13 declare real edges (not 22/11), and the legacy field appears 0 times across the WHOLE plans tree, not just pending. (4) ADDED requirement now tracked by the orchestrator's completion criterion 6 and V-03: show that `dependency_status` (oc_runipd.py:1424-1450) handles each typed edge kind per spec 2.9 instead of treating a typed edge as a bare id6, and that a Set with no declared edges gates exactly as before (`dependency-blocked` at oc_runipd.py:2554/:2592 unchanged).

## Goal

Make the declared dependency graph authoritative at run time. The repository already states dependencies in a typed, id6-grounded field and checks them on four surfaces; the fifth surface, the one that actually gates execution, reads a different field name and therefore sees nothing. Close that gap by consuming the shared predicate rather than adding a second implementation of the rules.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one parser, not two

- [ ] E-01 Delete `oc_runipd._DEPS_RE` (oc_runipd.py:100) and `_read_deps` (oc_runipd.py:811-821) and read the canonical field through `ipd_schema.parse_item_dependencies`, preserving the TYPED edges (`executed:`, `exists:`, `state:`) rather than flattening them to bare id6 strings. `PlanRecord.dependencies` and the frozen queue entry must carry the typed edges, since the qualifier determines the satisfaction rule. Apply the same change symmetrically in `agy_runipd.py`.
  - Depends on: none
  - Expected outcome: neither driver defines a dependency regex; a plan declaring `executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9` yields three typed edges in the record, where today it yields `[]`.
  - Execution state: pending

- [ ] E-02 Make preflight FAIL CLOSED using the shared graph predicate before any host session starts: a malformed statement, an unresolvable or ambiguous id6, a cycle, a self-edge, or the scaffold placeholder `unresolved` refuses the run with the corresponding named rule from the existing `check.ipd-*dependency*` family. A MISSING statement must not be silently treated as `none` (spec 2.7 is explicit that absence is not an affirmative assertion); honor the existing grandfathering cutover so pre-cutover plans are not mass-failed, and state which behavior applies.
  - Depends on: E-01
  - Expected outcome: each malformed/cyclic/ambiguous case refuses before any session starts, naming the shared rule; a grandfathered pre-cutover plan is handled per the existing cutover policy rather than by an ad-hoc runner rule.
  - Execution state: pending

### Task group 2: runtime satisfaction semantics

- [ ] E-03 Implement edge satisfaction per spec `25kzda` section 2.9. `executed:<id6>` requires the target to be terminally executed with valid finalization evidence, or, if the target is in this run, to have current outcome `verified`. `exists:<type>:<id6>` is satisfied immediately from current repository state and does not wait. `state:<type>:<status>:<id6>` requires the exact status, and an already-satisfied `state:` edge is releasable but the scheduler must run the dependent BEFORE advancing the target away from that status. A target outside the queue is evaluated from frozen repository state and, absent `--with-dependencies`, an unsatisfied external target cannot be met in this run.
  - Depends on: E-01, E-02
  - Expected outcome: each edge kind behaves as specified, demonstrated per-kind; an unsatisfied in-queue `executed:` edge causes the dependent to wait rather than start.
  - Execution state: pending

- [ ] E-04 Make declared edges authoritative for queue ordering and skip-cascade, with Set/Order demoted to a tiebreaker among items whose edges are equally satisfied (spec 2.10, 5.4). When an item fails or is contained, cascade `dependency-not-met` to its dependents and continue independent work rather than stalling the queue. The existing `dependency-blocked` disposition (oc_runipd.py:78) is the natural carrier; reuse it rather than inventing a parallel state.
  - Depends on: E-03
  - Expected outcome: ordering follows declared edges; a failed item marks only its dependents blocked; independent items still run; the recorded disposition is the existing one.
  - Execution state: pending

### Task group 3: prevent recurrence

- [ ] E-05 Add `tests/test_runner_item_dependencies.py` covering: the typed-edge round trip (contrasting against today's measured `[]`); each edge kind's satisfaction rule; wait-not-start for an unsatisfied in-queue prerequisite; fail-closed preflight for malformed/cyclic/ambiguous statements; the skip-cascade; and a guard asserting NEITHER driver defines a dependency regex or a private parser, so the two implementations cannot diverge again. Include a cross-driver symmetry assertion.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the module passes; the round-trip and gating assertions are shown to FAIL against pre-fix code; the anti-divergence guard FAILS when a private regex is reintroduced.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The two parsers are measurably divergent. For the input `- Item-Dependencies: executed:a1b2c3, exists:spec:d4e5f6, state:backlog:done:g7h8j9`: `oc_runipd._read_deps` returns `[]` while `ipd_schema.parse_item_dependencies` returns three typed `ItemDependency` records. The runner's regex is `^-\s*(?:Dependencies|Depends-on):\s*(.+?)$` (oc_runipd.py:100), which never matches the canonical field name.
- `_read_deps` also strips parenthesised text and keeps only tokens matching `ID6_RE` (oc_runipd.py:818-821), so even under a matching field name the qualifiers would be discarded, which would be WORSE than reading nothing: `exists:spec:<id6>` would silently degrade toward an untyped id6.
- The live tree already relies on the canonical field: 22 pending plans declare `- Item-Dependencies:`, ZERO use the legacy field, and 11 declare real edges (`qcqhj7 -> executed:8zgybk`, `rchpms -> executed:qcqhj7`, `7p9n2v -> executed:rchpms`, `58ha43 -> executed:7p9n2v`, and the `runstop` chain). Measured in run-20260829T190308Z-4123955: every queue item has `dependencies: []` and `order: None`.
- The shared machinery already exists and is the intended consumer surface: `ipd_schema` exports `parse_item_dependencies`, `canonical_item_dependencies`, `dependency_errors`, `item_dependency_cycles`, `ITEM_DEP_TYPES`, and the rule ids `check.ipd-missing-dependency-statement`, `check.ipd-dependency-cycle`, `check.ipd-dependency-dangling`, plus malformed/unresolved/ambiguous variants. `check_engine.py`, `ipd_lint.py`, and `ipd_set_plan.py` all reference it; `oc_runipd.py` references it ZERO times.
- Spec `25kzda` section 2.10 requires "All surfaces call this evaluator; none reimplement the rules." This plan is the missing fifth caller, so the correct action is deletion plus delegation, not a new parser.
- The gap was deliberate, not an oversight: `ipddeps-00-r7xku3` recorded "EXPLICITLY DEFERRED to the runner program (not this Set): the runner's dependency-graph PREFLIGHT, skip-cascade semantics, and `--with-dependencies` closure (spec 2.9/5.4) - those live with `aw <host> run`, which does not yet exist." The premise was that a NEW verb would consume the field; `aw oc run` already exists and runs daily, so the deferral left a silent gap in a shipped verb rather than a pending one.
- A `dependency-blocked` disposition already exists in the runner's terminal states (oc_runipd.py:78) and is already used for orchestrator deferral, so the cascade has a home.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `oc_runipd.py:100`, `:811-821` | The runner's private regex reads the wrong field name, so the canonical statement is invisible. | measured: `_read_deps` returns `[]` on a valid three-edge statement |
| F2 | HIGH | pending tree | 22 plans declare `Item-Dependencies`; 0 use the legacy field; 11 declare real edges the runner cannot see. | grep counts over `.aw/records/plans/pending/` |
| F3 | HIGH | run-20260829T190308Z-4123955 | Every frozen queue item shows `dependencies: []` and `order: None`, so the declared DAG is inert and ordering came from Set/Order alone. | state.json |
| F4 | HIGH | `oc_runipd.py:818-821` | Even with a matching field name, qualifiers would be stripped and only bare id6 tokens kept, silently changing an edge's meaning. | source |
| F5 | MED | spec `25kzda` section 2.10 vs code | The spec asserts one predicate drives five surfaces; four do, the runner does not. Section 1.2 step 3 describes queue-DAG construction that does not exist. | 4 modules reference the predicate; `oc_runipd.py` references it 0 times |
| F6 | MED | consequence | A phase can be launched before its declared prerequisite is verified, with no error and no advisory: a SILENT failure where the spec requires fail-closed. | F1 + F3 together |

## Proposed changes (ordered, validatable)

1. Delete the private parser; delegate to the shared one, preserving typed edges (E-01).
2. Make preflight fail closed on malformed/dangling/cyclic/ambiguous statements before any session starts (E-02).
3. Implement per-kind runtime satisfaction (E-03).
4. Make edges authoritative for ordering and cascade, demoting Set/Order to a tiebreaker (E-04).
5. Guard against the two parsers ever diverging again (E-05).

## Deferred / out of scope (with reason)

- `--with-dependencies` transitive closure expansion (spec 2.1/2.9). It changes which items enter the frozen queue and interacts with the mixed-type gate, so it is a distinct behavior worth its own plan. This plan makes DECLARED edges authoritative for items already selected.
- The dependency GRAMMAR and the four existing consumer surfaces. Verified working; touching them would risk a regression in checks that currently pass.
- Spec text corrections (review findings SR-001/SR-002: the stale preamble and the section 2.10 five-surface claim). The spec is the maintainer's to amend; this plan makes the code match what 2.10 already asserts.
- Source-side dependency fields for specs and backlog items. Spec 2.8 scopes the v1 mandatory field to IPDs and forbids inferring the others from prose.
- The wider `25kzda` runner program (`aw hooks install`, `aw <host> prompt`, the hash-chained ledger with `AW-Run:`/`AW-Item:` trailers, the per-host capability descriptor). Genuinely unbuilt and far larger than this corrective plan.

## Scope check

- Over-scope: none. Both drivers carry the private-parser defect; the test module is new and required by E-05.
- Under-scope: `--with-dependencies`, the spec-text findings, and source-side fields for other types are named under Deferred with reasons.

## Required tests / validation

- The new `tests/test_runner_item_dependencies.py` must pass, with the typed round-trip and the wait-not-start gating shown to FAIL against pre-fix code, and the anti-divergence guard shown to FAIL when a private regex is reintroduced.
- Existing dependency tests on the other four surfaces must pass UNCHANGED, proving this plan added a consumer without altering the shared rules.
- `python3 -m pytest -n auto` and `python3 -m pytest -m "" -n auto` against the Set's recorded baseline: fast `2871 passed, 3 skipped, 4 xfailed`; full `4 failed, 3198 passed, 3 skipped, 4 xfailed`, those 4 being the PRE-EXISTING CLI-surface failures. Do not claim them as caused or fixed.
- End-to-end on real data: run a Set whose members already declare `executed:` edges (the `wtiso` or `runstop` chains both do) and paste the frozen queue showing the edges present, contrasted with the pre-fix `dependencies: []` measured in run-20260829T190308Z-4123955.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- This plan implements spec `25kzda` sections 2.9, 2.10 (fifth surface), 5.4, and section 1.2 step 3. It does NOT amend the spec.
- The spec's stale preamble and its section 2.10 five-surface claim should be corrected by the maintainer; review findings SR-001/SR-002 record the specifics. The executor should note in the plan record which spec sections are now genuinely satisfied so a later spec edit can cite this plan as evidence.

## Open questions

### OQ-01: Should the legacy `Dependencies:`/`Depends-on:` field remain accepted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NO. Measured: 0 of the plans that declare dependencies use the legacy field. Accepting two names is how the divergence arose, and keeping it would let a plan express dependencies in a form only one surface understands. E-01 removes it and E-05 guards against reintroduction. A plan that used only the legacy field will, after this change, be treated as having NO statement, which the fail-closed preflight surfaces loudly rather than silently reading as `none`; that is the correct outcome per spec 2.7.

### OQ-02: What should preflight do about a plan with NO statement at all?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Spec 2.7 is explicit that a missing field is never equivalent to `none`, and the existing rule family has `check.ipd-missing-dependency-statement`. But `ipddeps` shipped a GRANDFATHERING cutover precisely so pre-cutover plans are not mass-failed, and 11 of 22 pending plans currently declare `none` while the remainder may predate the cutover. The blocking question is whether the RUNNER should refuse a pre-cutover plan lacking the field, or admit it with an advisory. Refusing is spec-faithful but could immediately block existing queued work; admitting is pragmatic but weakens the guarantee. The executor MUST NOT choose silently: this needs the maintainer's risk call, and the answer determines E-02's behavior.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `grep -n "_DEPS_RE\|_read_deps" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returning nothing. Paste a transcript showing the three-edge sample now yielding three TYPED edges from both drivers' record-building path, contrasted with the pre-fix `[]`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste refusals for each fail-closed class (malformed, dangling/unresolvable, ambiguous id6, cycle, self-edge, `unresolved`), each naming the shared `check.ipd-*dependency*` rule, and each demonstrably occurring BEFORE any host session starts (show the absence of a session log or launch event). State explicitly which behavior was implemented for a MISSING statement and cite the OQ-02 decision.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste one demonstration per edge kind: `executed:` unsatisfied in-queue causes WAIT not start; `executed:` satisfied by a verified in-run target releases; `exists:` releases immediately without waiting; `state:` requires the exact status AND the dependent runs before the target advances away from it; an external unsatisfied target cannot be met without `--with-dependencies`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste a queue whose execution order follows declared edges rather than Set/Order, including a case where the two disagree so the tiebreaker demotion is actually exercised. Paste a failure cascade showing dependents recorded `dependency-blocked` while independent items still ran to completion.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the new module passing, then FALSIFIABILITY in three directions: the typed round-trip fails pre-fix; the gating assertion fails pre-fix; the anti-divergence guard fails when a private regex is reintroduced. Paste the cross-driver symmetry assertion and the unchanged results of the four existing consumer surfaces' dependency tests. Additionally paste the real-data end-to-end queue described under Required tests.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OQ-02 is BLOCKING and must be answered by the maintainer before execution: it determines whether preflight refuses or advises a plan with no dependency statement, and that choice can immediately block or admit existing queued work. Do not execute this plan with OQ-02 open.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. This is a SHARED CHECKOUT with concurrent agents and humans; at authoring time another session had uncommitted work in `agent_workflows/` and `tests/`. This plan and `af7i6p` both modify the two driver modules, so re-read them before editing rather than reusing a stale view, and keep both drivers symmetric.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
