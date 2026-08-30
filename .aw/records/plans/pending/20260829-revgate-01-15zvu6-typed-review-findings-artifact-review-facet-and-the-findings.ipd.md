# IPD: Typed review findings artifact, review facet, and the findings-gate config key

- Date: 2026-08-29
- Kind: child
- Concern: Review findings (severity + decision) exist only in prose, so no gate, check, or report can see them; severity appears zero times in `ipd_lint.py` and `check_engine.py`.
- Scope: Introduce a machine-readable `.review.md` findings artifact under `.aw/records/reviews/`, add `review` to the closed artifact-type facet enum, add the `review_findings_gate` project-config key (default threshold `high`), and a dangling-reference check. The artifact carries a decisions section as well as findings, so `c621h9` (Order 04) can populate it. This plan does NOT gate anything: enforcement is `plqjt7` (Order 02) and dependency cascade is `7nkcgp` (Order 03).
- Scope-Paths: agent_workflows/artifact_naming.py, agent_workflows/config.py, agent_workflows/review_findings.py, agent_workflows/check_engine.py, .aw/records/reviews/README.md, tests/test_review_findings.py
- Item-Dependencies: none
- Status: to-review
- Set: revgate
- Order: 1
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 15zvu6
- Blocks-Release: next

## Workflow history

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-08-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from a maintainer-directed investigation into whether plan-review's High/Blocker findings are ever left unresolved; the measurement gap is the subject of this plan.

## Goal

Make a review's findings durable, typed, and machine-readable, so a High or Blocker left unfixed
becomes a fact the tooling can act on instead of prose buried in a workflow-history line. This plan
lays the data foundation only; the two sibling plans enforce on top of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the artifact and its name

- [ ] E-01 Add `review` to `ARTIFACT_TYPE_FACETS` in `agent_workflows/artifact_naming.py:59` (a CLOSED
      enum, so a dotted slug is never mis-parsed as a facet) and add the `reviews` -> `review` entry to
      `TYPE_FACET` (`artifact_naming.py:73`). A review file therefore takes the uniform clustered name
      `YYYYMMDD-<setid>-NN-<id6>-<slug>.review.md`, where `<id6>` is the REVIEWED PLAN's id6, which is
      the stable join key.
  - Depends on: none
  - Expected outcome: the naming grammar accepts and round-trips a `.review.md` name; existing facets
    are unchanged.
  - Execution state: pending

- [ ] E-02 Create `agent_workflows/review_findings.py` with a pure parser and writer for the findings
      table. One file per reviewed plan at `.aw/records/reviews/<clustered-name>.review.md`, holding a
      metadata block (`- Plan-Id:`, `- Reviewed-At:`, `- Reviewer:`, `- Verdict:`) and the findings
      table whose columns are the ones plan-review already writes: `ID | Severity | Scope | Area |
      Finding | Remediation Risk | Decision | Resolution`. Severity is the closed set
      `blocker|high|medium|low`; Decision is `fixed|deferred|open|replan`. The parser MUST be pure and
      never raise on a malformed row: it returns typed findings plus diagnostics, mirroring
      `ipd_lint`'s parse-then-diagnose shape.
  - Depends on: E-01
  - Expected outcome: a `.review.md` round-trips through writer -> parser with identical findings, and a
    malformed row yields a diagnostic rather than an exception.
  - Execution state: pending

- [ ] E-03 Support MULTIPLE review rounds per plan by appending rounds within the one file (a repeated
      `## Round <N>` section), because plans are demonstrably re-reviewed: the corpus has 863
      `/plan-review` history lines across 352 plans. The parser MUST expose which round is CURRENT
      (the last one), since the gate in `plqjt7` acts on current findings only, not on a finding that a
      later round already fixed.
  - Depends on: E-02
  - Expected outcome: a two-round file parses to two rounds, and `current_findings()` returns only the
    latest round's rows.
  - Execution state: pending

- [ ] E-08 Give the artifact a `## Decisions` section alongside its findings table, so a reviewer's
      SELF-RESOLVED judgement calls are recorded in the same file as its findings. Columns:
      `ID | Question | Chosen | Alternatives considered | Basis | Reversible`. The parser exposes them
      as typed decisions (same pure, never-raise contract as E-02). This plan only defines and parses
      the section; `c621h9` (Order 04) owns making reviewers WRITE it and surfacing it for audit. The
      section is OPTIONAL so a review with no autonomous decisions is still valid.
  - Depends on: E-02
  - Expected outcome: a `## Decisions` section round-trips through writer -> parser; a file without one
    parses cleanly with zero decisions.
  - Execution state: pending

- [ ] E-04 Write `.aw/records/reviews/README.md` documenting the tree: the flat layout (reviews do NOT
      move when a plan moves `pending/` -> `executed/`, so `aw ipd finalize` stays a single-file
      transaction), the id6 join key, the round convention, and the severity/decision enums.
  - Depends on: E-02
  - Expected outcome: the convention is documented where a future agent will look.
  - Execution state: pending

### Task group 2: the configurable threshold

- [ ] E-05 Add the `review_findings_gate` key to `agent_workflows/config.py`, read from
      `.aw/config/project.json`, following the EXISTING precedent of `dependency_schema_cutover`
      (`config.py:282-316`): read directly from project.json (NOT via the XDG user config, which drops
      unknown keys), tolerate a bare string for convenience, and never raise. Shape:
      `{"block_at": "high"}` with `block_at` in `medium|high|blocker|off`. DEFAULT WHEN ABSENT IS
      `high` (maintainer decision, 2026-08-29). Note this default is deliberately NOT fail-open, unlike
      the cutover marker: an absent key means the gate is ACTIVE at `high`. Provide a
      `findings_gate_threshold(repo_root) -> str` accessor and an `is_gating(severity, threshold)`
      predicate so both sibling plans share ONE comparison and cannot diverge.
  - Depends on: none
  - Expected outcome: threshold resolves to `high` on a repo with no key set, honors an explicit value,
    and `off` disables gating.
  - Execution state: pending

- [ ] E-06 Add `check.review-dangling` to `agent_workflows/check_engine.py`: a `.review.md` whose
      `Plan-Id:` resolves to no plan is a finding, mirroring the existing `check.from-backlog-dangling`
      treatment of an unresolvable cross-tree reference. Advisory severity, because a review of a
      superseded plan is untidy rather than dangerous.
  - Depends on: E-01, E-02
  - Expected outcome: a review file pointing at a nonexistent id6 is reported; a valid one is not.
  - Execution state: pending

### Task group 3: prove the foundation

- [ ] E-07 Write `tests/test_review_findings.py` covering: the naming round-trip; writer/parser
      fidelity; a malformed row producing a diagnostic and NOT an exception; multi-round parsing with
      `current_findings()`; threshold resolution including the absent-key default of `high` and the
      `off` case; `is_gating` at each severity/threshold combination; the `## Decisions` section
      round-trip plus the no-decisions case from E-08; and the dangling check firing and not
      over-firing. Include the adversarial case for the closed enum: a plan slug containing a dot
      (e.g. `foo.bar`) must NOT be mis-parsed as a facet.
  - Depends on: E-01, E-02, E-03, E-05, E-06, E-08
  - Expected outcome: the whole foundation is covered by tests that fail if any piece regresses.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ARTIFACT_TYPE_FACETS` (`artifact_naming.py:59`) is explicitly a CLOSED enum, with the stated reason
  that a dotted slug must never be mis-parsed as a facet. Adding `review` must preserve that property,
  hence the adversarial dotted-slug test in E-07.
- `dependency_schema_cutover` (`config.py:282-316`) is the precedent for a project-config key: read
  straight from `.aw/config/project.json`, tolerate a bare string, never raise. Reuse that shape rather
  than inventing a second config-reading style. NOTE the deliberate divergence: that marker is
  fail-OPEN (absent means no cutover); this key's absent-default is `high` (gate active).
- `ipd_lint` parses open questions into `List[Dict[str, str]]` (`ipd_lint.py:162`, `:258`) and then
  diagnoses them separately (`check_open_questions`, `:597`). The findings parser should mirror that
  parse-then-diagnose split so `plqjt7` can compare findings to open questions with both already
  parsed.
- `aw attention` knows five trees (`backlog`, `plans`, `releases`, `research`, `specs` via
  `attention_contract.CLASS_MAPS`). Reviews are deliberately NOT added as a sixth attention tree in
  this plan; surfacing is deferred (see Deferred) because an attention mapping needs its own
  status-class semantics.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | Severity is invisible to every deterministic gate. | `grep -c` for `BLOCKER`, `HIGH`, `Severity`, `Remediation Risk` in `agent_workflows/ipd_lint.py` + `check_engine.py` returns `0` for all four |
| F-2 | There is no findings artifact anywhere today. | No `.aw/records/reviews/` tree exists; no `*review*.json` under `.aw/records/` |
| F-3 | Findings live only in prose, in two places. | The plan's `## Workflow history` line and the session transcript under `.aw/records/runs/*/sessions/` |
| F-4 | Because of F-3, the corpus cannot be measured reliably. | An attempt to count findings by scraping transcripts yielded 55 severity+decision rows, and 33 of 278 session files contain a verbatim copy of `plan-review.md` (which itself contains the literal text `` `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW` ``), so scraped totals conflate instructions with findings |
| F-5 | Re-review is normal, so a findings file needs rounds. | 863 `/plan-review` history lines across 352 distinct plans |
| F-6 | Reviews reaching an open-questions verdict are common. | 48 history lines record `REVIEWED - OPEN QUESTIONS`; 49 plans contain that verdict, of which 44 are now `executed` |
| F-7 | Plans move between lifecycle directories, so a co-located review file would couple finalize to two files. | `aw ipd finalize` moves a plan `pending/` -> `executed/`; the repo already has a live class of bug from lifecycle state coupled across locations |

## Proposed changes (ordered, validatable)

1. Add the `review` facet to the closed naming enum (E-01).
2. Add the pure findings parser/writer and the flat `reviews/` tree (E-02, E-04).
3. Support multiple rounds with an explicit current round (E-03).
4. Add the configurable threshold with a shared `is_gating` predicate (E-05).
5. Add the dangling-reference check (E-06).
6. Cover all of it with tests, including the closed-enum adversarial case (E-07).

## Deferred / out of scope (with reason)

- **Any gating or blocking behavior.** Deferred to `plqjt7` (Order 02) by design: this plan must be
  landable without changing whether anything executes, so the data layer can be verified in isolation.
- **The dependency cascade.** Deferred to `7nkcgp` (Order 03).
- **Backfilling the 352 existing reviewed plans.** Deliberately out of scope. Their findings exist only
  in prose and transcripts, and F-4 shows scraping them is unreliable; manufacturing a typed record
  from an unreliable scrape would put false precision into the tree. New reviews get records going
  forward, exactly as the spec-id6 cutover grandfathered pre-cutover names.
- **Adding `reviews` as a sixth `aw attention` tree.** Deferred: it needs its own native-status ->
  attention-class mapping in `attention_contract.CLASS_MAPS`, which is a separate design question
  (a review is not "ready/active/blocked" in the same sense a plan is).
- **Changing the plan-review workflow to EMIT the artifact.** Deferred to `plqjt7`, which owns the
  enforcement and therefore the instruction change; splitting the emitter from the format would leave
  this plan unverifiable on its own.

## Scope check

- Over-scope: none. Every E-item is data-layer only.
- Under-scope: acknowledged. After this plan NOTHING is gated: a High left `open` still blocks nothing,
  because the enforcement lives in `plqjt7`. The honest claim is "findings can now be recorded and read
  by machine", not "unfixed findings are now caught".

## Required tests / validation

1. `python3 -m pytest tests/test_review_findings.py` green, run BARE (the repo's `addopts` supplies
   `-q -n auto --dist=worksteal -m 'not slow'`; do not pass `-n0` or a second `-q`).
2. Full default suite green with counts pasted, compared against the baseline at execution time.
3. Naming safety demonstrated: the closed-enum property still holds for a dotted slug.
4. Threshold default demonstrated on a repo with NO `review_findings_gate` key, showing it resolves to
   `high`.

## Spec / documentation sync

- `.aw/records/reviews/README.md` is a deliverable (E-04).
- The `review` facet joins a documented closed enum; `artifact_naming.py`'s module docstring lists the
  facet types and must be updated in the same edit as E-01.
- No spec governs review findings today. If this Set lands, the plan-review workflow body becomes the
  natural place to document the artifact, which `plqjt7` owns.

## Open questions

### OQ-01: Should a review file be named by the plan's id6 or get its own id6?

- Blocking: no
- Status: resolved
- Owner: resolved from repository evidence during authoring
- Resolution or deferral rationale: RESOLVED - use the REVIEWED PLAN's id6. The join must survive a
  plan rename or a `pending/` -> `executed/` move, and the id6 is the repo's stable cross-tree handle
  (the same role it plays in `From-Backlog`, `From-Spec`, and `Item-Dependencies`). A separate id6 would
  add a second identity with no join value and would need its own dangling check in both directions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session showing a `.review.md` clustered name parsed by
    `artifact_naming` and round-tripped, plus the ADVERSARIAL case: a slug containing a dot is NOT
    parsed as a facet. Paste the diff of `ARTIFACT_TYPE_FACETS` proving no existing facet changed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a written `.review.md` and the parser's output for it, showing every column
    recovered. Then paste the malformed-row case showing a DIAGNOSTIC and no traceback (a parser that
    raises fails this item).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a two-round file and the parsed result, showing `current_findings()`
    returns ONLY round 2. Include a case where round 1 has a `HIGH/open` finding that round 2 marks
    `fixed`, proving a superseded finding is not reported as current.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the README, and confirm it states the three load-bearing conventions
    (flat/no-move, id6 join key, round semantics) plus both enums.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste threshold resolution in four conditions: no key present (MUST be `high`),
    explicit `medium`, explicit `blocker`, explicit `off`. Paste the `is_gating` truth table for all
    severity x threshold combinations. Also paste a malformed-key case proving it does not raise.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `aw check` reporting `check.review-dangling` for a review whose `Plan-Id:`
    resolves to nothing, AND paste a run with a valid review showing the rule does NOT fire (proving it
    is not vacuous or over-firing).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste a `.review.md` containing a `## Decisions` section and the parser's typed
    output for it, showing every column recovered. Then paste a review file with NO decisions section
    parsing cleanly with zero decisions (proving the section is optional, not silently required).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the full test file result with counts, and the full default suite result
    with counts. Every V-item above must have a corresponding test; name which test covers which.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

RESOLVE-BEFORE-REFUSING (maintainer instruction, 2026-08-29): if you hit an obstacle while executing
this plan, you MUST first do the work of finding a strong recommended path from repository evidence.
Throwing up your hands and reporting "cannot proceed" is a LAST resort, and it is only acceptable when
you can state (a) what you tried, (b) the specific evidence that blocks each candidate approach, and
(c) a concrete recommended option with its trade-offs for the maintainer to choose. A bare refusal, or
an open question that merely restates the obstacle without a recommendation, is not an acceptable
outcome for this plan.

Execution contract: commit only the files changed for this plan, path-scoped
(`git commit -m msg -- <path>`), never `git add -A` and never push. Other agents and runs are ACTIVE in
this checkout; verify the staged set before every commit with `git diff --cached --name-only` and never
stage, revert, or discard another party's work. Run the suite BARE. When every `V-*` item carries
pasted evidence and `aw ipd lint --phase pre-transition` conforms, move this plan to
`.aw/records/plans/executed/` via `aw ipd finalize`.
