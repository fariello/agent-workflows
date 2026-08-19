# IPD: global history sidecar and inline-metadata slimming

- Date: 2026-08-18
- Kind: orchestrator
- Concern: Implement spec 20260818-1525-02 (sidecar administrative metadata, RELEASE BLOCKER). Every record type carries a `## Workflow history` narrative that grows unbounded; agents that consume these files fully read + cache the whole body, so the history burns tokens on administrative narrative that adds little value to the task at hand (the maintainer specifically flagged history). Adopt the DECIDED middle path: keep the small high-value fields (Status/Set/Id/Order/gate) inline, and move the bulky low-per-read-value history to ONE GLOBAL append-only `.aw/records/history.jsonl` keyed by id6 (line = {id6,date,tree,workflow,actor,message}); records keep inline state + a `- Managed-by:` directive + the LATEST-ONE history line, while the full chronological log lives only in the sidecar.
- Scope: A new `record_history.py` owning `.aw/records/history.jsonl` (append + read-by-id6) and its schema; routing the SPECS + BACKLOG status-transition writers (specs.run_set/run_note, backlog.run_set) to append a sidecar line and slim their inline history to latest-one; the `- Managed-by:` directive added to record templates + the generator; an idempotent migration folding existing inline `## Workflow history` blocks into the sidecar; and a `history` read verb (or `aw show --history`). IN: the sidecar store/writer, specs+backlog writer routing, template/generator directive, migration + read verb. OUT: the front-matter PARSERS (plans_index, specs, backlog, research_contract keep reading inline Status/Set/Id/Order UNCHANGED); manifest/index/attention/validators untouched by design (only history moves); PLANS/IPD history slimming (IPD-S405 requires the inline `executed` line - plans keep full inline history); IPD-transition + research writer routing (a documented IPD-safe FOLLOW-UP, not this Set).
- Status: to-review
- Set: awhistory
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: x97z83

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): high-level skeleton from spec 20260818-1525-02 (global .aw/records/history.jsonl, RELEASE BLOCKER); children to be fleshed out.
- 2026-08-18 to-review (opencode Opus 4.8): authored + lint-conforming; advanced draft->to-review (readiness, not a review).
- 2026-08-18 /plan-review (opencode Opus 4.8, RIGOROUS): APPROVE WITH REVISIONS APPLIED. PR-001 (HIGH): orchestrator Scope + child-02 + completion claimed IPD-transition + research writer routing, but child awhistory-02 delivers only specs+backlog -> unsatisfiable completion criterion, and routing an IPD writer to slim history would break IPD-S405 (ipd_lint.py:666 requires the inline `executed` entry). Narrowed the orchestrator to specs+backlog, excluded plans/IPD slimming explicitly, and moved IPD/research routing to a documented follow-up. Conforms at review-finalize. GO - PENDING HUMAN APPROVAL.

## Goal

Cut the token cost of consuming records by moving unbounded workflow-history narrative out of every record
body into ONE GLOBAL append-only `.aw/records/history.jsonl` keyed by id6, while keeping the small
high-value state fields (Status/Set/Id/Order/gate) inline plus a `- Managed-by:` directive and the
latest-one history line, so agents still reason about a file at a glance but no longer read/cache the full log.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..03 through the IPD lifecycle in dependency order (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing. Sequence so the store/writer (01) lands before the writer routing (02) and the migration + read verb (03) land last. On completion, confirm the sidecar is the single source of the full log, the SPECS + BACKLOG writers append exactly one line and keep only the latest-one inline (plans/IPD history untouched - IPD-S405 needs its inline `executed` line), the front-matter parsers/attention/index still pass unchanged, the migration is idempotent, and spec 20260818-1525-02 is advanced to implemented. (IPD/research writer routing is a documented follow-up outside this Set.)
  - Depends on: none
  - Expected outcome: Orders 01..03 executed; `.aw/records/history.jsonl` is the authoritative full log; inline history slimmed to latest-one + `- Managed-by:` directive present on new records; migration idempotent; full suite + `aw attention --check`/index checks green; spec 20260818-1525-02 advanced to implemented.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Split by layer so each intermediate state is runnable (store first, then route writers into it, migration + read verb last):

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | (to scaffold) awhistory-store-and-writer | New `record_history.py` owning `.aw/records/history.jsonl`: the JSONL schema (`{id6, date, tree, workflow, actor, message}`, keyed by id6 via `artifact_core.ID6_RE`), an append primitive, and a read-by-id6 reader. Add the `- Managed-by: aw (do not hand-edit status/history; use aw)` directive to record templates + the generator so new files carry it. + tests. | none |
| 02 | (to scaffold) awhistory-route-writers | Route the specs + backlog status-transition writers to ALSO append a sidecar line and slim their inline `## Workflow history` to the latest-one record: specs.run_set/run_note (specs.py) + backlog.run_set (backlog.py). Front-matter parsers (plans_index, specs, backlog, research_contract) stay UNCHANGED. CRITICAL EXCLUSION: PLANS/IPD `## Workflow history` is NEVER slimmed - `ipd_lint` IPD-S405 (ipd_lint.py:666) REQUIRES an inline `executed` history entry at post-transition, so slimming an IPD would break every plan transition. IPD-transition + research writer routing are therefore a DOCUMENTED FOLLOW-UP (a separate IPD-safe design), NOT part of this Set. + tests. | 01 |
| 03 | (to scaffold) awhistory-migration | Idempotent migration folding existing inline `## Workflow history` blocks into `.aw/records/history.jsonl`, preserving dates/actors (re-running adds nothing); a `history` read verb (or `aw show --history`) that returns a record's full chronological history by id6. + tests. | 01, 02 |

## Completion criteria (the whole Set is done only when)

- Orders 01..03 executed.
- `.aw/records/history.jsonl` exists and is the single authoritative full log; `record_history.py` appends and reads-by-id6 with the decided schema.
- The specs + backlog status-transition writers (specs set/note, backlog set) each append exactly one sidecar line per transition and slim their inline history to latest-one; AC1 holds. (PLANS/IPD history is NOT slimmed - IPD-S405 needs the inline `executed` line; IPD + research writer routing is a documented follow-up, out of this Set.)
- The `history` read verb returns a record's full chronological history by id6 (AC2); the migration is idempotent with no loss (AC3).
- The `- Managed-by:` directive is present on record templates + generated files.
- Front-matter parsers/attention/index unchanged: `aw attention --check`, `aw specs check`, `aw backlog check`, `aw index ... --check` still pass reading inline state (AC4); a measurable token reduction on a representative record (AC5).
- Full serial suite green; `aw sanitize --agent` clean; spec 20260818-1525-02 -> implemented.

## Cross-IPD validation

- Order 02 (writer routing) MUST land after Order 01 (the store exists) and Order 03 (migration + read verb) MUST land last so it folds the already-slimmed corpus; re-run the full suite after each Order.
- No-drift: the front-matter parsers (plans_index, specs, backlog, research_contract) and `aw attention`/index/validators must remain byte-behavior-equivalent on inline state - only history moves. Prove via the unchanged `--check` verbs still passing after each Order.
- id6 join key is `artifact_core.ID6_RE` and follows the shared Drift convention (artifact_core.py:247-266); every sidecar line and the migration MUST key on it consistently.

## Deferred / out of scope (with reason)

- Moving Status/Set/Id/Order/disposition out of the file (they stay inline per spec G1/Non-goals).
- Changing the naming grammar or directory taxonomy (spec Non-goals).
- A networked/remote store; the sidecar is a local repo file (spec Non-goals).
- Modifying the front-matter parsers or manifest/index/attention/validators (spec R6 - they keep reading inline state unchanged).

## Scope check

- Over-scope: none - every Order maps to spec 20260818-1525-02 requirements R1-R5; R6 (parsers unchanged) is explicitly out of scope.
- Under-scope: none - the three Orders cover the store/schema/writer (R1), the writer routing + inline slimming (R2), the read verb (R3), the migration (R4), and the template/generator directive (R5).

## Required tests / validation

Per-Order V-items plus the whole-Set completion criteria and the spec's acceptance criteria AC1-AC5. E-01's
verification re-runs the full serial suite, demonstrates one-line-per-transition + latest-one-inline, runs
the migration twice to prove idempotency, reads history back by id6, and re-runs the unchanged `--check`
verbs to prove no drift, after all Orders land.

## Open questions

### OQ-01: does the `history` read surface land as a standalone `aw history <id6>` verb or `aw show --history`?

- Blocking: no
- Status: open
- Owner: maintainer (resolve at Order 03)
- Resolution or deferral rationale: Spec R3 permits either. Recommendation: a dedicated `aw history <id6>` verb for discoverability, with `aw show --history` as an alias if `aw show` exists. Non-blocking - the sidecar is the source of truth either way and the read path is a thin reader over `record_history.py`.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all three child Orders show `Status: executed` under `.aw/records/plans/executed/`; paste a smoke run showing a status transition appending exactly one line to `.aw/records/history.jsonl` while the record body keeps only the latest-one inline; the `history` read verb returning a record's full chronological history by id6; the migration run twice with the second run adding nothing (idempotent); `aw attention --check`, `aw specs check`, `aw backlog check`, and the relevant `index --check` still green (parsers unchanged); a before/after token count on a representative record showing the reduction; the full serial suite tail and `aw sanitize --agent` clean; spec 20260818-1525-02 is `implemented`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: three Orders for one coherent objective (move history to a global sidecar and slim inline metadata), split by layer (store/schema/writer -> route the transition writers + slim inline -> migration + read verb) so each is independently reviewable/executable and every intermediate state stays runnable (the store lands before writers route into it; the migration folds the already-slimmed corpus last).

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The orchestrator
(opencode Opus 4.8) drives each child Order through its own lifecycle, owns all verification + path-scoped
commits (`git commit -m msg -- <path>`, never `git add -A`/`-a`), never pushes, and moves each Order (and
finally this orchestrator) to `executed/` only after `aw ipd lint --phase pre-transition` conforms and the
V-items are verified with pasted evidence. Large mechanical Orders (e.g. the migration) may be handed to
Gemini via `agy` (blocking), but the orchestrator OWNS verification and commits and never trusts a report on
faith. On completion, advance spec 20260818-1525-02 to implemented. RELEASE BLOCKER per spec 20260818-1525-02
(must land before the first `.aw/`-layout release).
