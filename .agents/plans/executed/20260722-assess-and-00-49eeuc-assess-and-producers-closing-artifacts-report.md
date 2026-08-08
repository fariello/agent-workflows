# IPD: producing workflows report their artifacts (created / not-created-and-why) + next steps at the end

- Date: 2026-07-22
- Concern: workflow UX / honest reporting - a user must know, at the end of a producing workflow, WHICH file(s) it created (or that it created none, and why) and what to do next
- Scope: the closing report of the IPD/artifact-PRODUCING workflows - `assess` (and the `assess-all` rollup), `incident`, `migrate`, `spec`. Prose workflow files; no product code. Standalone (not part of a Set). Item 1 of four maintainer requests (the others: aw uninstall, external install, and the already-executed overwrite-prompt D101).
- Status: executed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 49eeuc
- Set: assess-and (assess and producers closing artifacts report)
- Order: 0
- Approval: 2026-07-22, human ("approved. Go!") after /plan-review (APPROVE WITH REVISIONS APPLIED; R4/R5 fixed; OQ1/OQ2 resolved).

## Workflow history

- 2026-07-22 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): Steps 1-4. Created the canonical `.agents/workflows/assess/templates/closing-report.md` (created / none-and-why / next-steps, with both worked examples). Wired `assess.md` (Step 8 + fenced report gained a `Created:` IPD line + an always-present `Run record:` line + a not-created branch). Referenced the closing report from `assess-all`, `incident` (each action IPD), `migrate`, `spec`, each with its artifact(s) + a not-created branch. DECISIONS D102 + CHANGELOG. Validation: no em/en dashes, `aw check-local-leaks .` clean, `python -m pytest -q` green. Status approved -> executed; moved to `executed/`.
- 2026-07-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; R1-R5 (R4/R5 added). Verified the end-steps of all five producers (assess `:141-143`/`:190-211`, assess-all `:48-59`, incident `:50-54`, migrate `:43-45`, spec `:46-48`). R4 (MEDIUM, FIXED): the first-draft OQ1 lean `.agents/workflows/templates/closing-report.md` is the INSTALLER's README-stamping dir (`engine.py:2795,2835,2880`), a wrong home; corrected OQ1 to a workflow-reference home. R5 (LOW, FIXED): added the `test_dir_readmes.py`/packaging no-break guard. OQ1 resolved by human (`.agents/workflows/assess/templates/closing-report.md`); OQ2 resolved from the honest-reporting driver (run-record line always present). No open questions remain. Readiness: GO - PENDING HUMAN APPROVAL.
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
| R4 | MEDIUM | Low | maintainer | correctness (wrong home) | The first-draft OQ1 lean put the canonical convention in `.agents/workflows/templates/` - but that dir is the INSTALLER's per-bucket README-stamping SOURCE (`engine.py:2795,2835,2880`), not a workflow-reference dir; a `closing-report.md` there is a home mismatch and could be confused with a bucket README template. Raised + fixed by plan-review (PR-001): use a workflow-reference home (e.g. `assess/templates/` or an `index.md` section) instead. | `engine.py:2795,2835,2880`; `.agents/workflows/templates/` (README templates only) |
| R5 | LOW | Low | maintainer | anti-regression | A new shared file / edited workflow files must not break a content-asserting test (e.g. `tests/test_dir_readmes.py` checks a README exists per workflow dir; a new file in an existing dir is fine, but a NEW workflow dir would need a README). Confirm the chosen home does not trip such a test. Raised by plan-review (PR-002). | `tests/test_dir_readmes.py` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | R1,R2 | Define ONE canonical "Artifacts and next steps" closing-report convention (P8, single source of truth) in a shared reference the producers can point at. HOME (decide at review, OQ1; note plan-review PR-001: do NOT use `.agents/workflows/templates/` - that dir is the INSTALLER's per-bucket README-stamping source (`engine.py:2795,2835,2880`), a different purpose): candidates are (a) a shared workflow-reference file such as `.agents/workflows/assess/templates/closing-report.md` (assess is the anchor producer; matches the per-workflow `templates/` precedent like `release-review/templates/*`), or (b) a short section in `.agents/workflows/index.md`. It specifies a closing block that MUST state: CREATED - each artifact path (IPD(s), spec, post-mortem, run record) one per line, or "none"; if none, WHY (assessed and found nothing warranting a plan; user declined the write; aborted - name which); and NEXT STEPS - the concrete commands (e.g. review the IPD, `/plan-review <path>`, approve, then execute). Include a worked example of BOTH the created and the not-created case. | the chosen home (NOT `.agents/workflows/templates/`) | Low | one canonical closing-report definition exists in a workflow-reference home (not the installer README-template dir); covers created + not-created + next-steps; has both worked examples; no em/en dashes |
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
- Under-scope: the convention MUST cover the not-created-and-why case (R1, the specific ask), the run-record path for assess (R3), be referenced not restated (P8), and live in a WORKFLOW-reference home (NOT the installer README-template dir, R4/PR-001); each producer MUST end by presenting it; the chosen home MUST NOT break a content-asserting test (R5).

## Required tests / validation

- Prose only (no code): validate by review + consistency. (a) a single canonical closing-report convention exists (created paths / none-and-why / next steps) with both worked examples, in a workflow-reference home (NOT `.agents/workflows/templates/`, R4); (b) `assess` lists IPD path + run-record path + next steps and has the not-created branch; (c) `assess-all`, `incident`, `migrate`, `spec` each reference it and list their artifact(s) + next steps + not-created branch where applicable; (d) no divergent restatements of the convention (P8); (e) no em/en dashes; (f) `aw check-local-leaks .` clean; (g) `python -m pytest -q` stays green (docs; the new file must NOT trip `tests/test_dir_readmes.py` or a packaging/manifest test, R5; if a test asserts workflow-file content, update it, else expect no change) - paste actual output.

## Spec / documentation sync

- The canonical closing-report file `.agents/workflows/assess/templates/closing-report.md` (OQ1), the five producer workflow files, DECISIONS, CHANGELOG 1.3.0. The new file ships as part of the workflow tree the installer copies and needs no manifest row (templates are not commands).

## Open questions

- OQ1 (convention home): RESOLVED (human, 2026-07-22). Use a shared workflow-reference file at `.agents/workflows/assess/templates/closing-report.md` (assess is the anchor producer with an existing `templates/` dir; matches the per-workflow templates precedent). The other four producers (`assess-all`, `incident`, `migrate`, `spec`) reference it by that path. NOT `.agents/workflows/templates/` (the installer README-stamping dir, R4/PR-001).
- OQ2 (assess run-record line): RESOLVED from the honest-reporting driver (plan-review, R1/R3). The line is ALWAYS present: `Run record: <path>` when one was written, or `Run record: not written (<local-only | skipped | none>)` otherwise, so it is never silently absent (matches the not-created-and-why principle this IPD establishes).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
