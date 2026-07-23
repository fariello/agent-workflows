# IPD: producing workflows report their artifacts (created / not-created-and-why) + next steps at the end

- Date: 2026-07-22
- Concern: workflow UX / honest reporting - a user must know, at the end of a producing workflow, WHICH file(s) it created (or that it created none, and why) and what to do next
- Scope: the closing report of the IPD/artifact-PRODUCING workflows - `assess` (and the `assess-all` rollup), `incident`, `migrate`, `spec`. Prose workflow files; no product code. Standalone (not part of a Set). Item 1 of four maintainer requests (the others: aw uninstall, external install, and the already-executed overwrite-prompt D101).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-22 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer request - "the /assess * workflows need to tell the user AT THE END which files (IPDs) were created (or not, and why), and suggested next steps." Generalized to the sibling producers for consistency (incident/migrate/spec), since they share the gap.

## Goal

Every workflow that PRODUCES a durable artifact (an IPD, a spec, a post-mortem + action IPDs) ends with a clear, uniform closing report that states: (a) exactly which file(s) it created, with paths; OR (b) that it created NONE, and why; plus (c) the concrete suggested next steps. A user must never be left guessing what was written or what to do next.

Why it matters: today `assess` prints `IPD written: <path>` + a `Next step:` line (good), but has NO branch for "assessed and proposed nothing" (so on a clean assessment the user sees a verdict but no explicit "no IPD was created because ..."), and the sibling producers are inconsistent - `incident` lists emitted IPDs, `migrate`/`spec` give next-steps prose, none define the not-created case, and none share one closing convention. This is an honest-reporting and self-documenting gap (P2/P3): the artifact set and the next action should be unambiguous at the end of every producing run.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` P2 (honest documentation over aspirational), P3 (self-documenting), P8 (single source of truth), P12 (self-contained interaction). No em/en dashes.
- Producers and their current closing state (verified):
  - `assess` (`.agents/workflows/assess/assess.md`): Step 8 "Report and stop" (`:141-143`) says to present the report with IPD + run-record paths; the fenced report template (`:190-211`) has `IPD written: <path>` and `Next step: ...` but (a) has NO "created none, and why" branch, and (b) the RUN-RECORD path is mentioned in Step 8 prose yet is NOT a line in the fenced template.
  - `assess-all` (`.agents/workflows/assess-all/assess-all.md`): emits ONE consolidated IPD (`:48-59`) + a rollup run record; should likewise state the single IPD path + next steps + the not-created case (e.g. all concerns clean).
  - `incident` (`.agents/workflows/incident/incident.md`): Step 7 (`:50-54`) "list the emitted action IPDs" - MULTIPLE files; no not-created branch, no fenced closing block.
  - `migrate` (`.agents/workflows/migrate/migrate.md`): Step 6 (`:43-45`) writes one IPD + recommends plan-review; no explicit "IPD written: <path>" closing line, no not-created branch.
  - `spec` (`.agents/workflows/spec/spec.md`): Step 5 (`:46-48`) writes the file + points at next steps; no not-created branch, no fenced closing block.
- The `assess` fenced report template (`:190-211`) is the strongest existing model to mirror/extend.
- These are prose runbooks; there is no shared include mechanism, so a shared convention means a short canonical block referenced from each (P8: define once, reference, do not restate divergently).

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| R1 | MEDIUM | Low | any user | honest reporting | Producers do not define the "created NO artifact, and why" case; a clean/aborted run leaves the user unsure whether an IPD exists. | `assess.md:190-211` (no none-branch); `incident.md:50-54`; `migrate.md:43-45`; `spec.md:46-48` |
| R2 | MEDIUM | Low | any user | consistency / self-documenting | The "what did I create + next steps" closing varies per workflow (assess has a fenced template; incident lists files; migrate/spec are prose); no uniform block. | the four files above |
| R3 | LOW | Low | any user | completeness | `assess` Step 8 says to report the run-record path, but the fenced template only prints `IPD written:`; the run-record path is not in the literal output. | `assess.md:141-143` vs `:190-211` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | R1,R2 | Define ONE canonical "Artifacts and next steps" closing-report convention (P8, single source of truth) in a shared reference the producers can point at. Candidate home: a short section in `.agents/workflows/index.md` OR a small `.agents/workflows/templates/closing-report.md` (decide at review, OQ1). It specifies a closing block that MUST state: CREATED - each artifact path (IPD(s), spec, post-mortem, run record) one per line, or "none"; if none, WHY (assessed and found nothing warranting a plan; user declined the write; aborted - name which); and NEXT STEPS - the concrete commands (e.g. review the IPD, `/plan-review <path>`, approve, then execute). Include a worked example of BOTH the created and the not-created case. | `.agents/workflows/templates/closing-report.md` (new) or `index.md` | Low | one canonical closing-report definition exists; covers created + not-created + next-steps; has both worked examples; no em/en dashes |
| 2 | R1,R3 | Update `assess` to reference the canonical closing report: extend its fenced template (`:190-211`) to add a `Run record: <path>` line (R3) and a `Created:`/`Next step:` structure per the convention, AND add the explicit NOT-CREATED branch (a clean assessment that proposes no IPD says so and why). Do not remove the existing verdict/top-findings/plan-summary content. | `.agents/workflows/assess/assess.md` | Low | assess report lists IPD path + run-record path + next steps; a no-IPD run prints the not-created block with a reason; existing report content preserved |
| 3 | R1,R2 | Update `assess-all`, `incident`, `migrate`, `spec` to each end by presenting the canonical closing report: the artifact path(s) they wrote (assess-all: the one consolidated IPD + rollup; incident: the post-mortem + each action IPD; migrate: the IPD; spec: the spec file), the not-created branch where it applies (e.g. spec/assess-all abandoned, incident with no follow-ups), and next steps. Reference the Step 1 convention; do not restate it divergently. | `.agents/workflows/assess-all/assess-all.md`, `.agents/workflows/incident/incident.md`, `.agents/workflows/migrate/migrate.md`, `.agents/workflows/spec/spec.md` | Low | each producer references the closing convention and lists its artifact(s) + next steps + not-created branch where applicable |
| 4 | R1,R2 | Docs/decision sync: a DECISIONS entry (pin at execution) recording the uniform closing-report convention (artifacts created / not-created-and-why / next steps) across the producing workflows; CHANGELOG 1.3.0. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; links resolve; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| Non-producing / dialogue workflows (`advise` session summary, `getting-started`, `whatnext`, `list-workflows`, the review workflows) | Low | scope | They do not PRODUCE a lifecycle artifact the same way (advise saves a session summary; whatnext/plan-review already have their own required final report). Out of scope; this is about IPD/artifact producers. | Only if a gap appears there. |
| A programmatic check that the closing report was emitted | High | functionality | The report is runtime agent output, not a tracked artifact, so nothing static to lint; enforced by instruction like the other conventions. | n/a. |

## Scope check

- Over-scope: none. One canonical closing-report convention + references from the five producing workflows + docs. No code; no change to WHAT the workflows produce, only to how they REPORT it at the end.
- Under-scope: the convention MUST cover the not-created-and-why case (R1, the specific ask), the run-record path for assess (R3), and be referenced not restated (P8); each producer MUST end by presenting it.

## Required tests / validation

- Prose only (no code): validate by review + consistency. (a) a single canonical closing-report convention exists (created paths / none-and-why / next steps) with both worked examples; (b) `assess` lists IPD path + run-record path + next steps and has the not-created branch; (c) `assess-all`, `incident`, `migrate`, `spec` each reference it and list their artifact(s) + next steps + not-created branch where applicable; (d) no divergent restatements of the convention (P8); (e) no em/en dashes; (f) `aw check-local-leaks .` clean; (g) `python -m pytest -q` stays green (docs; if a test asserts workflow-file content, e.g. a dir-README or manifest test, update it, else expect no change) - paste actual output.

## Spec / documentation sync

- The canonical closing-report location (new template or index section), the five producer workflow files, DECISIONS, CHANGELOG 1.3.0. If a new file under `.agents/workflows/templates/` is added, confirm it ships (it is part of the workflow tree the installer copies) and does not need a manifest row (templates are not commands).

## Open questions

- OQ1 (convention home): a new `.agents/workflows/templates/closing-report.md` (a dedicated, referenceable file, consistent with the other `templates/`), or a short section in `.agents/workflows/index.md`? Lean: a `templates/closing-report.md` file (clean single source, matches the existing template convention, easy to reference); confirm at review.
- OQ2 (assess run-record line): include the `Run record: <path>` line always, or only when a run record was written (a local-only or skipped run might not have one)? Lean: print it when written, and say "run record: not written (local-only / skipped)" otherwise, so the line is never silently absent. Confirm at review.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
