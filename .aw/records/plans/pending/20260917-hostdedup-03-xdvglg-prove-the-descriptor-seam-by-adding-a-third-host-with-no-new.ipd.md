# IPD: Prove the descriptor seam by adding a third host with no new runner

- Date: 2026-09-17
- Kind: child
- Concern: Nothing currently PROVES that adding a host does not mean writing another runner. The claim rests on `HostLabels` existing, but both of its instances were written by extracting from two runners that already existed, so the descriptor has never been exercised in the direction it will actually be used: adding a NEW host that has no runner module of its own. Until that is demonstrated, 'add a descriptor, not a runner' is an assertion. The measured risk is concrete: `oc_runipd.py` is 9588 lines and `agy_runipd.py` 5784, so if the seam is insufficient the third host arrives as several thousand more duplicated lines, and the fourth and fifth after it.
- Scope: Add a THIRD host end to end without adding a runner module, and let the attempt find whatever the seam is missing. The deliverable is either a working third host reached through `HostLabels` plus a thin entry point, or a precise, evidenced list of what the descriptor cannot express. Both outcomes are valuable; only an unexamined assumption is not.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_hostdedup_third_host.py, .aw/records/research
- Item-Dependencies: executed:nmlx47
- Status: draft
- Set: hostdedup
- Order: 3
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: xdvglg

## Workflow history

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Turn "a new host is a descriptor, not a runner" from a claim into a demonstrated property, before the
codex/claude/hermes work starts and the cost of being wrong is multiplied by three.

WHY A THIRD HOST IS THE ONLY HONEST TEST. Orders 01 and 02 reduce duplication between two EXISTING
runners. That is necessary but it does not answer the question the maintainer actually asked, which is
about hosts that do not exist yet. A seam extracted from two instances is fitted to those two instances;
the third is where an over-fitted abstraction reveals itself. Doing this as a DELIBERATE experiment, whose
acceptable outcome includes "the descriptor is insufficient, here is exactly how", is much cheaper than
discovering the same thing halfway through a real host integration.

SCOPE DISCIPLINE: this plan does not need a working AI host. A third host that is real enough to exercise
every seam the runners touch (a scripted or dry-run host) answers the structural question completely, and
does so without depending on a vendor CLI, credentials, or spend.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Enumerate what a host must supply

- [ ] E-01 Derive, from the code rather than from intuition, the COMPLETE set of things a host must supply to the shared runner: every `HostLabels` field, every host-specific `options` key, the driver-identity contract (`state['driver']['path']`, whose BASENAME two analytics consumers key on), the argv/launch shape, the permission-posture inputs, and any remaining host-specific branch in shared code. Produce it as a checklist a new host integrator could work through.
  - Depends on: none
  - Expected outcome: an enumerated host contract with each entry citing the consumer that reads it. `orziju`'s review measured 23 `options` keys (10 shared, 7 oc-only, 6 agy-only) and named the `__file__`/driver-identity hazard; both must appear.
  - Execution state: pending

### Task group 2: Add the third host and let it find the gaps

- [ ] E-02 Implement the maintainer's OQ-02 ruling: add an explicit host-id field to `HostLabels`, have a run record that identity, and re-point `run_analytics_sources.driver_generation` and `run_viewer` at the id. MUST include the fallback for PRE-CUTOVER records, which hold a module path and cannot be rewritten, so historical runs keep attributing correctly.
  - Depends on: E-01
  - Expected outcome: a runner-less host is attributable by id, and an existing run record recorded before this change still resolves to its host rather than `unknown`.
  - Execution state: pending

- [ ] E-03 Add a third host defined ONLY by a `HostLabels` instance plus the thinnest possible entry point, with NO new runner module, and drive one real IPD execution through it end to end. Use a scripted/dry-run host so the test needs no vendor CLI, credentials or spend. Record every place the attempt required a change to shared code.
  - Depends on: E-02
  - Expected outcome: either a completed execution, or a precise failure list. Each required change to shared code is recorded with the reason, because that list IS the measurement of how good the seam is.
  - Execution state: pending

- [ ] E-04 Classify each gap E-03 found as (a) a missing `HostLabels` field, (b) a genuine host CAPABILITY needing a switch rather than a label, or (c) a structural limit meaning the seam is insufficient as designed. For (c), state what a sufficient seam would look like; do not paper over it.
  - Depends on: E-03
  - Expected outcome: a per-gap classification with a recommendation. An empty gap list is a valid and excellent outcome, but must be stated as a measured result rather than an assumption.
  - Execution state: pending

### Task group 3: Make the answer durable

- [ ] E-05 Immortalize the host contract from E-01 and the gap analysis from E-04 to `.aw/records/research/` via `aw research new`, so the codex/claude/hermes work starts from a measured contract rather than re-deriving it.
  - Depends on: E-04
  - Expected outcome: a committed research record containing the enumerated contract, the third-host result, and the gap classification.
  - Execution state: pending

- [ ] E-06 Add `tests/test_hostdedup_third_host.py` keeping the third host alive as a PERMANENT guard, so a future change that reintroduces a host-specific assumption into shared code fails a test instead of being discovered by the next host integrator. Assert the third host needs no runner module, AND pin host attribution in BOTH directions per the OQ-02 ruling: a runner-less host attributes by id, and a pre-cutover path-only record still attributes correctly.
  - Depends on: E-05
  - Expected outcome: a guard proving the seam still admits a runner-less host, which is the property Orders 01-03 exist to establish.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `runner_shared.HostLabels` requires every field explicitly (NO DEFAULTS) so a missing value raises at
  construction rather than reading as empty. A third host must therefore supply all eight fields, which is
  exactly the enumeration E-01 needs.
- `HostLabels` models ONE capability flag (`emits_launch_identity`) alongside its strings, establishing the
  precedent that a genuine capability may be a switch rather than a label. E-03's classification uses that
  distinction.
- THE DRIVER-IDENTITY CONTRACT IS A REAL TRAP FOR A NEW HOST: `initialize_run` writes
  `state['driver']['path']` from `__file__`, and `run_analytics_sources.driver_generation` plus
  `run_viewer` key on its BASENAME to attribute a run to a host. A host with no runner module of its own
  has no natural basename, so E-01 must state what it supplies instead. `orziju` found both consumers
  would silently return `unknown` with no test failing.
- `aw host capabilities` already exists as the surface describing what a host can guarantee; a third host
  should be legible to it rather than bypassing it.
- Durable analysis belongs in `.aw/records/research/` via `aw research new`, never hand-named (AGENTS.md).
- The execution contract forbids `git add -A` and pushing; commit only declared `Scope-Paths`.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | `HostLabels` exists and carries 8 host-varying values, with both instances bound by their host's wrappers | `runner_shared.py:8530` onwards, `OC_HOST_LABELS` and the agy equivalent |
| F-2 | The descriptor has never been exercised by a host WITHOUT its own runner module, which is the actual N-host use case | both instances were extracted from pre-existing runners by `rununify` 04 (`tx6q0h`) |
| F-3 | Host-specific state is not confined to labels: 23 `options` keys split 10 shared / 7 oc-only / 6 agy-only | `orziju` review measurement, reproduced at that HEAD |
| F-4 | Driver identity is derived from `__file__`'s basename by two analytics consumers, so a runner-less host has no obvious identity | `run_analytics_sources.driver_generation`, `run_viewer.py:858-870`; `orziju` F-9 |
| F-5 | The cost of an insufficient seam is measured in thousands of lines per host | `oc_runipd.py` 9588 lines, `agy_runipd.py` 5784 |
| F-6 | A vendor CLI is NOT needed to answer the structural question | the repository already tests hosts with injected runner doubles (`host_runner` spawns via an injectable runner; `host_launchers` uses doubles, "No live models are launched in tests") |

## Proposed changes (ordered, validatable)

1. Derive the complete host contract from code, with a consumer cited per entry (E-01).
2. Add a third host as a descriptor plus a thin entry point, no runner module, and drive a real execution
   through it, recording every shared-code change it forced (E-02).
3. Classify each gap as missing-label / genuine-capability / structural-limit, with a recommendation (E-03).
4. Immortalize the contract and the gap analysis to `.aw/records/research/` (E-04).
5. Keep the third host as a permanent guard (E-05).

## Deferred / out of scope (with reason)

- Integrating a REAL codex / claude / hermes host is out of scope. This plan establishes the seam is
  sufficient; each real host is its own work with its own vendor specifics, spend and credentials.
- The five large functions remain forked; a third host that needs them will reach them through whatever
  wrappers exist. If E-02 finds that the remaining fork BLOCKS a third host, that is a finding for E-03 and
  a strong argument for resolving those five, not licence to split them here.
- No new public `aw` verb for host registration. If E-03 concludes one is needed, it recommends it.

## Scope check

- Over-scope: none. Every item serves the single question of whether a host can be added without a runner.
- Under-scope: this plan does not deliver a usable third AI host, only the proof that the seam admits one.
  That is deliberate: the structural question is answerable without vendor dependencies, and coupling it to
  one would make the answer hostage to an unrelated integration.

## Required tests / validation

- `python3 -m pytest` bare and green with the summary line pasted.
- Evidence the third host completed a real IPD execution, with its run record showing correct host
  attribution rather than `unknown` (F-4's trap).
- The explicit list of shared-code changes the third host required, or a statement that it required none.
- `tests/test_hostdedup_third_host.py` green, and shown to FAIL if a host-specific assumption is
  reintroduced into shared code.

## Spec / documentation sync

No `.spec.md` is declared. Spec `25kzda` is written for two hosts in places and speaks of "which host is
running"; if E-03 finds the spec ASSUMES exactly two hosts anywhere, record it as a finding and file a spec
amendment separately rather than editing a shipped contract inside an experiment. Backlog `xdgorn` already
notes the spec is silent on a per-host flag asymmetry, so this area is known to need attention.

## Open questions

### OQ-01: Should the third host be a real vendor CLI or a scripted double?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A SCRIPTED/DRY-RUN HOST. The question this plan answers is structural
  (can a host exist without a runner module), and a scripted host exercises every seam the runners touch
  while needing no credentials, no vendor CLI and no spend. The repository already establishes this pattern:
  `host_runner` takes an injectable runner and `host_launchers`' own docstring records "No live models are
  launched in tests (doubles only)". Using a real vendor host would make a structural result hostage to an
  unrelated integration, and would not strengthen the finding.

### OQ-02: What identity does a host with no runner module report as its driver?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-17: THE DESCRIPTOR CARRIES AN
  EXPLICIT HOST ID, and a run records that identity rather than deriving it from a module filename. The
  question was put to the maintainer with three alternatives priced (explicit id; a per-host identity-only
  stub module; recording both during a transition) and this was chosen directly.

  WHY IT WAS THE MAINTAINER'S CALL, not an executor's: `state['driver']['path']` reaches PERMANENT run
  records, and `run_analytics_sources.driver_generation` plus `run_viewer` currently attribute a run to a
  host by string-matching the BASENAME of that path. Changing what the field means changes durable history
  and the analytics that read it.

  WHAT THIS COMMITS THE SET TO, and E-01/E-02 must carry all four. (1) `HostLabels` gains an explicit host
  id field, justified by named consumers exactly as every other field is. (2) The two analytics consumers
  read the ID rather than the basename, so a runner-less host is attributable. (3) HISTORICAL RECORDS STILL
  HOLD PATHS and must keep resolving: existing runs recorded `oc_runipd.py` / `agy_runipd.py` and cannot be
  rewritten, so the consumers need a documented fallback from id to basename for pre-cutover records. This
  is the part most likely to be missed and it must not be. (4) The identity must be pinned by a test in BOTH
  directions: a runner-less host attributes correctly, and a pre-cutover record still attributes correctly.
  The rejected stub-module option is recorded here so a later reader knows it was considered and why it lost:
  it would have preserved both consumers with zero migration, at the cost of conceding one module per host
  forever, which is the very shape this Set exists to eliminate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the enumerated host contract, each entry citing the consumer that reads it, and
    explicitly covering the 8 `HostLabels` fields, the host-specific `options` keys, and the driver-identity
    contract. A contract with an entry whose consumer is not named fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the host-id field with its named consumers; evidence a runner-less host attributes by
    id; AND evidence a PRE-CUTOVER run record (one holding only a module path, taken from an existing run in
    `.aw/records/runs/`) still attributes to its host rather than `unknown`. The historical case is the one
    most likely to be skipped, so a verdict without it fails this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the third host's run record from a real execution, showing correct host attribution
    (NOT `unknown`), plus the complete list of shared-code changes the attempt required, or an explicit
    statement that it required none. Confirm no new runner module was added.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the per-gap classification with a recommendation for each, or an explicit "no gaps
    found" stated as a measured result. Any structural-limit gap must say what a sufficient seam looks like.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the committed research record path, containing the contract and the gap analysis.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest tests/test_hostdedup_third_host.py` green, AND shown to fail when
    a host-specific assumption is reintroduced into shared code (make the edit, paste the failure, revert).
    Plus `python3 -m pytest` bare and green with the summary line pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, AND it carries a blocking open question
(OQ-02, the driver identity of a runner-less host) that the maintainer must answer before E-02 can settle
its approach. An executor must not resolve OQ-02 unilaterally: it changes the meaning of a field in every
durable run record and governs whether analytics can attribute a run to a host.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, never push. Paste ACTUAL runner output for every V-item.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. Note that a
finding of "the seam is insufficient, here is how" is a SUCCESSFUL outcome for this plan, provided E-03
classifies each gap; it does not require the third host to work.
