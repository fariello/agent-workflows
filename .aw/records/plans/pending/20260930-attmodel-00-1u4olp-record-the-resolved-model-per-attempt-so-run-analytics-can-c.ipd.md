# IPD: Record the resolved model per attempt so run analytics can compare models

- Date: 2026-09-30
- Kind: orchestrator
- Concern: A MODEL COMPARISON CANNOT BE DRAWN OVER THIS REPOSITORY'S OWN RUNS, and the reason is three separable defects that must be fixed in order rather than together. Backlog `7yz545` measured the symptom: about 100 of 298 `state.json` files carry `options.model` or `options.cost_attribution.model`, so two thirds of the corpus is unattributable and the `runsdash` dashboard (`97i0ao`) labels those rows `(unrecorded)`. Authoring measured the three causes. NO ATTEMPT RECORD CARRIES A MODEL AT ALL, so even a fully-attributed run cannot distinguish an executor turn from a verifier turn under a second model; the DASHBOARD MIS-ATTRIBUTES EVERY VERIFIER ROW because it computes one model per run and stamps it onto every row (executed: a run with `model: provA/executor-model` and `verify_model: provB/verifier-model` reported `role=main model=provA` AND `role=verify model=provA`); and THE COMPARISON IS FED AN EMPTY LIST by its only production caller (`stats_mod.model_comparison([])` in `run_analytics_cli`), which returns `Verdict.REFUSED` with "coverage 0.0000" for want of any input, while the same function fed 30 attempts each carrying a model returns `Verdict.COMPUTED`. That last one matters most for sequencing: fixing only the producer would deliver the field and still no answer.
- Scope: Orchestrate three children that together make a model attributable per attempt and make the consumers read it. This plan holds ORCHESTRATION ONLY: every deliverable belongs to a child (`czut8j` the frozen per-attempt producer, `ov2c9n` the host-observed model, `r5fk4k` the three consumers), and this file contributes no code, no test, no doc and no record of its own. EXCLUDES, in every child without exception: back-filling history, moving `MODEL_COVERAGE_THRESHOLD` from its declared 0.80, editing the retained `CORPUS_BASELINE` snapshot, adding a new CLI flag (which would require amending spec `25kzda` Section 2.1), and making anything GATE or REFUSE on a model value.
- Scope-Paths: .aw/records/plans/pending/20260930-attmodel-00-1u4olp-record-the-resolved-model-per-attempt-so-run-analytics-can-c.ipd.md
- Item-Dependencies: none
- Status: to-review
- Coverage: pass
- Coverage-Fingerprint: 6c18c8fb8839c7b9635d1a0688e154e3630d410f9c24dc1521852a87a8161853
- Coverage-Checked: 2026-10-07 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: feature
- Priority: medium
- From-Backlog: 7yz545
- Set: attmodel
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 1u4olp

## Workflow history
- 2026-10-07 to-review (aw set): returned to review: every child executed; each completion criterion leads with its owning child; coverage pass recorded
- 2026-10-07 coverage pass (aw oc run): fingerprint 6c18c8fb8839, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 coverage fail (aw oc run): fingerprint b325498c257e, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): every child is executed; each Set-level obligation now names the child that performed it.
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: The Set-level obligations are: the three children's test files all present and green

- 2026-10-06 coverage fail (aw oc run): fingerprint 628403857f36, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `7yz545` as a Set of three rather than one plan, because authoring measured that the item's one-line request decomposes into a producer, a host observation and three consumers with different risk profiles and different failure modes. TWO CORRECTIONS TO THE ITEM ARE RECORDED IN THE CHILDREN THAT OWN THEM RATHER THAN HERE. (1) The item says the OpenCode model comes "from the session's assistant message modelID"; the `--format json` stream carries NO model id (measured: a complete turn emitted `step_start`, `text`, `step_finish` and nothing naming a model), so `ov2c9n` takes a different and executed route, `opencode export`. (2) The item under-reports the defect: it frames the problem as missing coverage, and coverage is only two thirds of it, since the dashboard mis-attributes every verifier row even on a fully-attributed run, and the comparison arm is fed an empty list regardless of coverage. Both are owned by `r5fk4k`.
- 2026-09-30 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make every attempt in a future run name the model it ran under, and make the three consumers that report a
model read that field, so the comparison backlog `7yz545` asks for receives a real population.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the children

- [ ] E-01 CONFIRM czut8j REACHED executed
  - Depends on: none
  - Expected outcome: `czut8j` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 01 writes the FROZEN per-attempt model at the one seam both hosts reach (`runner_shared.execute_item_core`). It MUST be first, and the reason is structural rather than stylistic: both siblings read a field that does not exist until it lands. `ov2c9n` records an OBSERVATION beside the frozen value, so without the frozen value its disagreement case is inexpressible; `r5fk4k`'s whole fallback chain is anchored on `attempt["model"]`, so without it the per-row resolution has nothing new to read. Both siblings declare `executed:czut8j` in their own front matter.

- [ ] E-02 CONFIRM ov2c9n REACHED executed
  - Depends on: E-01
  - Expected outcome: `ov2c9n` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 02 adds the HOST-OBSERVED model, which is what closes the coverage gap on the default configuration where no `--model` is passed at all. Its route was executed at authoring rather than assumed (`opencode export <sessionID>` reports `info.model.id`, found at byte offset 263 of a 284 MB export, readable in 1.3 to 4.7 seconds with a 4 KiB bounded read). It is INDEPENDENT of Order 03 and may run before it, after it, or in a parallel lane.

- [ ] E-03 CONFIRM r5fk4k REACHED executed
  - Depends on: E-01
  - Expected outcome: `r5fk4k` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 03 repoints the three consumers and is the plan that actually delivers the item's ask. It is INDEPENDENT of Order 02 by design (its precedence chain reads the observed tier when present and skips it when absent, the same tolerance it already applies to a pre-`w33lrl` run's missing `cost_attribution`), so it declares `executed:czut8j` only. Sequenced last in the table because it is the plan whose output a human will judge the Set by.

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Depends on | Why this order |
|---|---|---|---|---|
| 01 | `czut8j` | Record the frozen launch model on every attempt so a per-attempt model exists at all | none | Must precede both siblings: each reads `attempt["model"]`, which nothing writes today. Needs no host cooperation, so it is the reliable floor the others build on. |
| 02 | `ov2c9n` | Observe the model the OpenCode host actually used for a turn and record it beside the frozen one | `executed:czut8j` | Records an observation BESIDE the frozen value, so the frozen value must exist first. Independent of 03. |
| 03 | `r5fk4k` | Read the per-attempt model in analytics and the dashboard so coverage reaches the consumers | `executed:czut8j` | The item's actual ask. Independent of 02: reads the observed tier opportunistically, requires only the frozen one. |

THE ONLY REQUIRED EDGE IS `czut8j` BEFORE `ov2c9n` AND `r5fk4k`. Orders 02 and 03 are mutually independent
and may execute in parallel lanes once 01 has executed. Their production files OVERLAP on
`runner_shared.py` (02 adds one injected call at an existing seam; 01 already changed that function), which
is an author-time note and not a runtime hazard: each execute item runs in its own isolated worktree and
returns through the merge-and-revalidate gate. Order 03's files (`run_dashboard.py`, `run_analytics.py`,
`run_analytics_statistics.py`, `run_analytics_cli.py`) are disjoint from both siblings'.

## Completion criteria (the whole Set is done only when)

Every criterion below names, as its first words, the child plan that performs it. All three children
are `executed`.

1. [Owner: czut8j] Every attempt record written by either host names the model it was launched under, on every path an
   attempt can take: the happy path, the two early refusals (scope-target-stale, host-capability), and an
   interrupted attempt after its post-fill accounting has run.
2. [Owner: r5fk4k] A run that used TWO models (a `--verify-with` run) records both, and every consumer reports both: the
   dashboard's verify row reports the verifier's model rather than the executor's, which is the defect
   measured at authoring and the sharpest test of the whole Set.
3. [Owner: ov2c9n] A turn launched with NO `--model` flag at all still ends with a concrete model on its attempt record,
   sourced from the host's own report rather than from a config read.
4. [Owner: r5fk4k] `run_analytics_statistics.model_comparison` is fed a REAL attempt population by its production caller and
   reports the coverage it actually achieves. A REFUSAL IS AN ACCEPTABLE OUTCOME HERE and must not be
   engineered away: `MODEL_COVERAGE_THRESHOLD` stays 0.80 and the corpus is not back-filled, so a corpus
   dominated by pre-Set runs may legitimately keep refusing with a real number in place of today's
   fabricated 0.0000.
5. [Owner: r5fk4k] A run carrying NO per-attempt fields (every run that already exists) produces output identical to today's
   from every consumer, including the `(unrecorded, <host>)` per-host label.
6. [Owner: ov2c9n] Nothing gates, refuses, warns-to-failure or changes a disposition on a model value, and an unreachable
   host costs a run nothing: a failed observation leaves the turn's exit code, disposition and item status
   byte-identical.
7. [Owner: czut8j, ov2c9n and r5fk4k] No spec is amended (none describes these surfaces, measured) and no new CLI flag is added, so spec
   `25kzda` Section 2.1's flag grammar and `tests/test_run_flag_surface.py` are untouched.
8. [Owner: czut8j, ov2c9n and r5fk4k] `python3 -m pytest` is green, with the baseline re-derived by each child at execution rather than taken
   from any plan in this Set.
9. [Owner: ov2c9n and czut8j] TWO RESIDUES ARE NAMED RATHER THAN CLAIMED. The Antigravity host gains no OBSERVED model in this Set
   (its stream already carries one at `event["init"]["model"]`, parsed and discarded today, so it needs a
   cheap persist rather than a subprocess interrogation, and `ov2c9n` defers it with that reason). The
   `audit` verb keeps no per-attempt model (it writes its own `state.json` and its own lean attempt dict
   without passing through `execute_item_core`). Each must be filed as its own backlog item at execution,
   and the Set must NOT be reported as delivering either.

## Cross-IPD validation

- ORDER MATTERS AND IS DECLARED, ONCE: `ov2c9n` and `r5fk4k` each declare `executed:czut8j`. `r5fk4k`
  deliberately does NOT declare `ov2c9n`, and its OQ-03 records why; do not add that edge without reading it.
- THE SEQUENCING IS PINNED FROM THE CHILDREN'S SIDE, not only by this table. `ov2c9n`'s E-05 case (e) asserts
  that a frozen model and an observed model can DISAGREE and both be recorded, and `r5fk4k`'s E-06 case (b)
  asserts an attempt-grain fact takes the ATTEMPT's model: neither can pass without Order 01 in the tree, so a
  violated ordering surfaces as a failing child test rather than as a date comparison nobody runs.
- ONE PRECEDENCE, NOT THREE. Order 01 defines the PRODUCER-side resolution (which frozen option key this turn
  was launched from) and Order 03 defines the CONSUMER-side chain (which recorded field a reader prefers).
  Those are different questions and both are defined ONCE in their own plan. No child may hand-write a second
  if-chain answering either; `r5fk4k` E-01 states this obligation for the consumer side, and the reason is the
  measured disagreement at authoring, where `run_dashboard` and `run_analytics` gave different answers about
  the same run's verify phase.
- A REQUEST AND AN OBSERVATION ARE SEPARATE KEYS AND NEITHER MAY OVERWRITE THE OTHER. `ov2c9n` OQ-01 records
  the ruling with its reasoning; collapsing them would make a substituted model undetectable, which is one of
  the two reasons that plan exists. Order 03 decides the READER's precedence between them and is the only
  plan that may.
- NO CHILD MAY BACK-FILL HISTORY. `w33lrl` (executed) set this precedent for `cost_attribution` and recorded
  it explicitly; inventing a model for a past attempt fabricates provenance, and a past session's export is
  not guaranteed to exist.
- NO CHILD MAY WIDEN `run_analytics_privacy`'S ALLOWLIST SPECULATIVELY. Measured at authoring: `model` and
  `model_variant` are admitted, `model_source` is REFUSED as a key. `r5fk4k` E-05 must decide on evidence and
  PREFER not widening; if it widens, the module's own rule applies (a new key ships with a test proving it
  cannot carry a path, a transcript or a command line).
- NO CHILD MAY ADD A CLI FLAG. Spec `25kzda` Section 2.1 declares the flag grammar and
  `tests/test_run_flag_surface.py` reads that spec AS A FILE and fails in both directions, so a flag added
  without a declared spec amendment turns the suite red. `ov2c9n` E-04 is shaped to reach its opt-out through
  the existing configuration surface for exactly this reason, and is required to STOP and report rather than
  add a flag.
- EACH CHILD WRITES ITS TESTS IN A NEW FILE, checked against the pending tree at authoring: `czut8j` uses
  `tests/test_attempt_model_identity.py`, `ov2c9n` uses `tests/test_attempt_host_model_observation.py`,
  `r5fk4k` uses `tests/test_attempt_model_consumers.py` plus an addition to `tests/test_run_dashboard.py`.
  None of the three new paths is declared by any other pending plan, while `tests/test_runner_shared.py` and
  `tests/test_run_analytics.py` are each declared by several, which is why neither is used.
- THE THREE SHIPPED DASHBOARD MODEL TESTS MUST PASS UNEDITED. `test_one_row_per_session_with_roles`,
  `test_unrecorded_model_is_labeled_per_host` and `test_antigravity_run` each pin a fallback tier the Set
  preserves, so an edit to any of them signals a tier was broken rather than extended. `r5fk4k` F-05 carries
  this and V-06 requires the no-edit claim be verified rather than asserted.

## Deferred / out of scope (with reason)

- THE ANTIGRAVITY OBSERVED MODEL, deferred by `ov2c9n` with its reason (the value is already parsed in that
  host's stream loop and merely discarded, so it needs a persist and not an interrogation, and bundling it
  would make a cheap change wait on a subprocess design). Named in completion criterion 9 so the Set cannot
  claim it.
- THE `audit` VERB'S SEPARATE STATE WRITER, excluded by both `czut8j` and `ov2c9n` because it bypasses
  `execute_item_core` entirely and fixing it means editing a host file neither plan needs to touch. Named in
  completion criterion 9.
- SPEC `w15vzb`'S R-6 CASE B AND CRITERION A-8 ("an unprovidable-at-launch model WARNS, falls back, and
  RECORDS the fallback in run state"), recorded OUTSTANDING in that approved spec. This Set does NOT implement
  it and must not be read as doing so: it records the RESOLVED model, not a fallback EVENT. What it does
  supply is the per-attempt place such a record would live, so a later plan implementing A-8 has a home for
  it. Stated here because the adjacency is close enough to be miscredited.
- PRODUCER-SIDE MODEL NORMALIZATION (stripping `uri/`, `google/`, `anthropic/`, `openai/`), which stays at
  the display boundary in `run_dashboard._normalize_model`. `7hek98`'s gate paragraph names producer-side
  normalization as a deferred alternative; changing what is RECORDED is a different decision from changing
  what is DISPLAYED, and this Set takes neither.
- ANY REFUSAL OR GATE ON A REQUESTED-VERSUS-ACTUAL DISAGREEMENT. The Set makes a divergence VISIBLE; deciding
  what to do about one has a real false-positive cost (a provider alias, a version suffix or a normalization
  difference would all read as divergence) and spec `25kzda` Section 5.3a's "NEVER A GATE" posture for derived
  observations is the precedent for leaving it out.
- READING THE OPENCODE SQLITE STORE DIRECTLY, refused by `ov2c9n` with three reasons (an undocumented internal
  schema with no compatibility promise, a correctness and locking hazard in another application's live
  database, and a machine-local absolute path of exactly the kind the leak sanitizer exists to keep out of
  tracked output). The host's own `opencode export` is used instead.

## Scope check

- Over-scope: none. This file declares only itself and contributes no deliverable.
- Under-scope: the two residues in completion criterion 9 (the Antigravity observed model and the `audit`
  verb), each to be filed as its own backlog item at execution rather than absorbed silently.

## Required tests / validation

This plan runs no tests of its own; each child carries its own validation surface and each must be green on
its own terms. Every child is executed. Owners of the Set-level obligations: each child's own test file is
present and green in that child's V-items (`czut8j`, `ov2c9n`, `r5fk4k`); the three shipped dashboard model
tests green and UNEDITED is `r5fk4k`'s V-06 (it is the child that touches the dashboard); and each child ran
a bare `python3 -m pytest` against its own re-derived baseline at its boundary, `r5fk4k`'s being the last.

## Open questions

### OQ-01: Should the Set have been two plans rather than three, folding the observation into the producer?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: THREE, because the frozen field and the observed field have different failure modes and a reviewer should be able to judge them separately. The frozen field is a pure write from a mapping already in memory: it cannot fail, needs no host, and is testable without a subprocess. The observation spawns a child process per turn, depends on a host CLI surface that this repository does not control (authoring measured 1.18.33 while the `tools/ipdrunner/` runbook documents runs under 1.18.21), and needs a timeout and an opt-out. Folding them would put an unfailable write and a host-dependent interrogation behind one approval, so a maintainer who wanted the first and doubted the second would have to reject both. It would also make the FLOOR wait on the ceiling: the frozen field alone already fixes the two-model mis-attribution, which is the sharpest defect in the Set.

### OQ-02: Should the backlog item be closed `done` when this Set retires?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NOT BY AN AUTHORING TURN, and the handoff is already recorded in the mechanism rather than in prose. The item moves to `graduated` when the design is handed off, which is what this Set is; `done` requires the code written and validated, which is Order 03's execution. All four plans in the Set carry `- From-Backlog: 7yz545`, so the graduation link is machine-readable and `aw check`'s `check.from-backlog-dangling` rule can resolve it. The item carries no `- Blocks-Release:` gate (its `- Work-Kind:` is `feature`, not `bug`, so the auto-gating rule does not apply), so there is no gate to inherit and none was invented: the plans deliberately declare no `Blocks-Release`.

### OQ-03: Does an orchestrator carrying only confirmation rows risk the coverage gate?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: NO, AND THE SET WAS AUTHORED TO THAT RULE DELIBERATELY. The repository's orchestrator-coverage gate refuses to retire a parent that carries work no child covers, because retirement skips the pre-transition E/V checkpoint on the premise that a parent's own items are performed by nobody. Every E-item in this file is a CONFIRMATION that a named child reached `executed`, and every deliverable in the Concern and Goal is owned by one of the three children: the producer by `czut8j`, the observation by `ov2c9n`, all three consumers plus the doc by `r5fk4k`. The two residues in completion criterion 9 are explicitly NOT deliverables of this Set (they are named as filed-elsewhere), which is the honest treatment rather than parking them on the parent where they would be marked complete having never been performed.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the `- Status:` line of `czut8j` read from disk showing `executed`, and its file present under `.aw/records/plans/executed/`. Both, because a status line and a location can disagree and the location is what the lifecycle treats as authoritative.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the `- Status:` line of `ov2c9n` read from disk showing `executed`, and its file present under `.aw/records/plans/executed/`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the `- Status:` line of `r5fk4k` read from disk showing `executed`, and its file present under `.aw/records/plans/executed/`. Plus, because this is the child that delivers the item's ask, the pasted `model_comparison` result its V-04 produced, so the Set's own closing report names the coverage actually achieved rather than asserting improvement.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires `/plan-review` followed by explicit human approval before execution;
an executing agent must not self-approve, and must not hand-write a `- Readiness:` value, which is an output
of review.

An agent told to "execute `attmodel`" must run the children in Order, honoring the declared edges: `czut8j`
first, then `ov2c9n` and `r5fk4k` in either order or in parallel lanes. This file itself contributes no code
and is retired once all three children read `executed` on disk.

At execution, follow the repository execution contract: this plan declares only its own path, so any commit
it makes is limited to that file through `aw commit <plan> -- <path>`, never `git add -A`, never push. Do not
report the Set complete until all three children are `executed`, every completion criterion above is met or
explicitly reported as not met, and the two residues in criterion 9 have been filed as their own backlog
items.
