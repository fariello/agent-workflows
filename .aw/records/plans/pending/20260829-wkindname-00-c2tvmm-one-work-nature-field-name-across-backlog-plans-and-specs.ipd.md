# IPD: one work-nature field name across backlog, plans, and specs

- Date: 2026-08-29
- Kind: orchestrator
- Concern: Only backlog records the NATURE of work (bug, feature, chore, security, followup). Plans and specs do not, so that classification is lost the moment a backlog item graduates into a plan, and nothing can ask for all bug work across the trees. The maintainer decided the field must carry ONE name everywhere, which makes this two genuinely different jobs: a migration that renames backlog's existing field across 88 tracked items, and a feature that adds the field to two more contracts. This orchestrator exists because those jobs have different failure modes and are independently executable, and because the superseded single plan `a6cej0` bundled them.
- Scope: ORCHESTRATOR - authors NO product code. Its own execution work is (E-01) whole-Set verification only. Child 01 carries the rename plus migration; child 02 carries the field addition. This plan owns the child sequence, the one-vocabulary rule both children inherit, the Set completion criteria, and the cross-plan checks. Excludes adding the field to research, excludes any attention-board wiring or sort change, and excludes deriving the value from `From-Backlog`.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: to-review
- Set: wkindname
- Order: 0
- Highest E allocated: 01
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: c2tvmm
- Blocks-Release: next
- From-Backlog: 1ap48y

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): created by SPLITTING the approved plan `a6cej0` at the maintainer's direction. `a6cej0` began as "add an optional field", then absorbed the maintainer's rename-first decision, which turned it into a migration bundled with a feature. It stayed under the size thresholds (8 leaves, 3 groups against limits of 18 and 5), so this split is NOT a size split; it is the spec's other criterion, that work mixing distinct concerns with independently-executable phases should be split. The dependency graph in `a6cej0` proved the phases were already independent: its field-addition items declared `Depends on: none` and nothing in them depended on the rename items. `a6cej0` is retired as superseded by this Set, and the maintainer's four recorded decisions carry over verbatim (one shared vocabulary; store rather than derive; rename first; recognized-but-optional mechanics per the `Priority` precedent).

## Goal

Give plans and specs the same work-nature field backlog already has, under a single field name, without letting a mechanical 88-file migration and a two-contract feature share one blast radius.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO product code. Its only execution step is the whole-Set verification.

### Task group 1: whole-Set verification

- [ ] E-01 After both children execute, confirm the Set delivered one field name on one vocabulary: backlog, plans, and specs all use `- Work-Kind:`; every consumer reads the SAME vocabulary symbol with no forked copy anywhere; the field is optional on all three so an artifact without it still validates; `aw check` flags an out-of-vocabulary value on each type; and the distinct `- Gate-Kind:` field is intact. Then confirm the honest limit is stated rather than oversold: nothing yet CONSUMES the field for filtering, so the Set must not be reported as delivering cross-tree search.
  - Depends on: none
  - Expected outcome: one field name across three types on one shared vocabulary; absent stays valid everywhere; `aw check` catches a bad value on each type; `Gate-Kind` unaffected; the no-filtering limit recorded; full suite green.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | File (id6) | What it does | Depends on |
|---|---|---|---|
| 01 | 9trlc3 | Rename backlog's on-disk `- Kind:` field to `- Work-Kind:` in `backlog.py`, and migrate the 88 existing items behind a dual-read window. A pure migration: mechanical, one module, many tracked files. | none |
| 02 | ng2blv | Add the recognized-but-optional `Work-Kind` field to the IPD schema and the spec contract, with setter support and an `aw check` enum rule, reusing the one shared vocabulary. | 01 executed |

Children are SEQUENTIAL. Child 02 declares `executed:9trlc3` because the field name it recognizes must already be the name backlog writes; adding the field first and renaming after would put two spellings in the tree at once, which is the confusion this Set exists to remove.

Hard constraints both children inherit, stated once here:
- ONE vocabulary. `backlog.KINDS` is the single source and no child may fork, subset, or duplicate it. The `xprio` Set's completion criteria demand exactly this ("no forked copies", provable by grep) and this Set follows it.
- The field is RECOGNIZED-BUT-OPTIONAL on every type. Absent means unclassified, with no forced default, so no existing artifact is mass-failed.
- The enum check lives in the `aw check` surface, never in a schema or contract layer. This is the layering rule the schema states for `Priority`, `Scope-Paths`, `Blocks-Release`, and `From-Backlog`.
- Never anchor a rename or a search on the bare token `Kind`. Three other fields collide with it: an IPD's structural `Kind` (orchestrator or child), research's document-type kind, and backlog's own `Gate-Kind`.

## Completion criteria (the whole Set is done only when)

- Backlog, plans, and specs all carry the work-nature field under the name `- Work-Kind:`.
- Exactly one vocabulary definition exists, consumed by every reader (provable by grep for the member tokens).
- An artifact with no `Work-Kind` validates on all three types.
- `aw check` reports an out-of-vocabulary value on a backlog item, a plan, and a spec.
- The 88 migrated backlog items validate, and `- Gate-Kind:` still appears on exactly 2 items and still parses.
- Full suite green, and the record states that filtering is NOT delivered.

## Cross-IPD validation

- CID-1: one vocabulary symbol, no forked member list anywhere in `agent_workflows/`.
- CID-2: one field name across all three types; no module still reads the old backlog spelling once child 01 is executed.
- CID-3: the field is absent from every REQUIRED-field set, so absence never fails an artifact.
- CID-4: `Gate-Kind` is untouched by the migration, verified by count and by parsing an item that carries it.

## Project conventions discovered (Step 0)

- The pattern for this exact shape of change is ALREADY EXECUTED and should be copied rather than reinvented: the `xprio` Set added a uniform recognized-but-optional `Priority` across plans, specs, and research as an orchestrator plus three per-type children. Its rules are the ones this Set inherits: optional not required, absent means unset, one shared vocabulary.
- Test precedents exist for a field of exactly this kind: `tests/test_ipd_priority.py` and `tests/test_spec_priority.py`. Child 02 mirrors them instead of inventing a test shape.
- The `check.priority-invalid` rule is the template for the enum check: registered as error severity, repository assurance class, deterministic.
- `backlog.py` is the ONLY module that reads backlog's work-nature field, which is what keeps child 01 small in code terms even though it rewrites many files.
- The superseded `a6cej0` carries the full evidence base for all four maintainer decisions and its findings remain valid; children should cite it rather than re-deriving.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | MED | `a6cej0` structure | The split criterion is CONCERN MIXING, not size. `a6cej0` had 8 executable leaves across 3 task groups against thresholds of 18 and 5, so it was never oversized; the spec separately directs splitting work that mixes distinct concerns or has independently-executable phases, and after the rename decision it did both. | `ipd_schema.MAX_E_LEAVES = 18`; the ipd-spec size-threshold paragraph naming "mixes distinct concerns, or has independently-executable phases" |
| F2 | MED | `a6cej0` dependency graph | The phases were ALREADY independent, which is why splitting costs nothing structurally. Its field-addition item declared `Depends on: none` and no field-addition item depended on either rename item, so the rename could ship and be verified entirely on its own. | `a6cej0` E-item `Depends on:` lines |
| F3 | MED | `a6cej0` gate | A REAL DEFECT in the approved plan, which the split resolves: its cohesion rationale still read "6 E-leaves across 2 task groups" after the rename decision took it to 8 across 3. The stale count was introduced when the rename items were added and would have misled a reviewer about the plan's shape. | `a6cej0` "Cohesion rationale" line versus its measured leaf and group counts |
| F4 | HIGH | `backlog.py`; `.aw/records/backlog/` | The migration's blast radius is the reason to isolate it: 88 tracked items carry the field, in a checkout where other agents commit concurrently. The code change is small (one module) but the file count is not, so a conflict in the migration should not be able to block the unrelated feature work. | `grep -rl '^- Kind:' .aw/records/backlog/` = 88; the only work-nature reads live in `backlog.py` |
| F5 | HIGH | `backlog.py` | The corruption hazard child 01 must own: `backlog.py` also parses a DISTINCT `- Gate-Kind:` field that 2 items carry, so any substring-based rename silently produces `Gate-Work-Kind` and breaks the gate contract. | `grep -rl '^- Gate-Kind:' .aw/records/backlog/` = 2 |
| F6 | MED | `attention.py`, `check_engine.py` | The honest limit, carried over from `a6cej0` and still true: NOTHING consumes a work-nature field today, not even on backlog. This Set makes the classification recorded and validated on two more types; it does NOT deliver cross-tree filtering, and no child may claim it does. | the attention item record carries priority and release-blocker fields but no work-nature field; no reader of the vocabulary outside backlog's own validation and creation paths |

## Proposed changes (ordered, validatable)

1. Retire `a6cej0` as superseded by this Set (done as part of creating it).
2. Child 01: rename in code, then migrate 88 items behind a dual-read window.
3. Child 02: add the field to the IPD schema and spec contract, with setter and check rule.
4. Verify the whole Set: one name, one vocabulary, optional everywhere, `Gate-Kind` intact (E-01).

## Deferred / out of scope (with reason)

- Adding the field to RESEARCH. A research document's nature is already carried by its mandatory document-type facet drawn from an 18-member vocabulary, so a second kind axis there would confuse rather than clarify. This is where this Set deliberately differs from `xprio`, which did include research because priority is orthogonal to document type.
- DERIVING the value from a plan's `From-Backlog` link. Decided against in `a6cej0` and unchanged: a derived value is undefined for the majority of artifacts that carry no such link, and would let a plan's classification change silently when someone edits the source item. Because the field is optional, a later derivation pass can populate absent values without contradicting this Set.
- ATTENTION-BOARD wiring, labelling, or sort changes, and cross-tree FILTERING. Per F6 nothing consumes the field yet; delivering search is separate work.
- BACKFILLING the field onto existing plans and specs. Absent means unclassified by design.

## Scope check

- Over-scope: none. This orchestrator writes only its own record and declares no product path, which is correct for an orchestrator that authors no code.
- Under-scope: none. Both children exist, are authored, and are listed with their dependency; unlike the `rununify` orchestrator this Set's seams were already known, so nothing is deferred to a measurement step.
- The children declare the product paths: child 01 takes `backlog.py` plus the backlog records tree; child 02 takes the schema, spec contract, check engine, CLI, setter module, and its test file.

## Required tests / validation

- Each child must pass its own validation independently, since the point of the split is that they are separately verifiable. Child 01's evidence stands without child 02 existing.
- `aw check` and `aw backlog check` must be clean after EACH child, not only at the end of the Set. A migration that leaves the tree failing until a later child lands would defeat the split.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""` (or `make test` / `make test-all`). Do NOT add `-n auto` or a second `-q`.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite during this sweep at `df731f1`: `2880 passed, 3 skipped, 4 xfailed`. Take your own readings with the HEAD they were taken at; several sessions are committing concurrently.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming for this plan and both children.

## Spec / documentation sync

- No spec text change is forced. This Set follows the already-executed `Priority` pattern and changes no contract a spec pins.
- Child 01 owns updating any documentation that names backlog's old field spelling, since leaving a doc describing the old name reintroduces the confusion the rename removes.
- Child 02 should check whether the `ipd-spec` document enumerates recognized metadata fields and whether `Priority` was added there when `xprio` landed, then follow that precedent exactly rather than inventing a new documentation obligation.

## Open questions

### OQ-01: Should child 02 wait for child 01, or can they run in parallel?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: SEQUENTIAL, child 01 first. Child 02 declares `executed:9trlc3`. The reason is not a code dependency, since the two touch disjoint modules, but a naming one: child 02 teaches plans and specs to recognize `Work-Kind`, and if it landed while backlog still wrote `Kind`, the tree would briefly carry two spellings for one concept, which is exactly the confusion this Set removes. Running the rename first also front-loads the riskiest work, so a migration conflict surfaces before any feature work is invested.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a backlog item, a plan, and a spec each carrying `- Work-Kind:` and validating. Paste a grep for the vocabulary member tokens showing exactly ONE definition in `agent_workflows/`. Paste one artifact of each type with NO `Work-Kind` still validating. Paste `aw check` flagging an out-of-vocabulary value on each of the three types. Paste the `- Gate-Kind:` count still at 2 with one such item parsing. Paste the full suite result with its HEAD. Finally, state in writing that cross-tree filtering is NOT delivered by this Set; claiming otherwise fails this item.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 1 E-leaf in 1 task group, which is correct for an orchestrator that authors no code and verifies the Set. The SET's right-sizing is enforced through the two children, each of which is one concern with its own falsifiable surface.

Open questions: ALL RESOLVED. The four decisions this Set implements were made by the maintainer and are recorded in the superseded `a6cej0` and carried into the children: one shared vocabulary rather than a per-type set; store the value rather than derive it; rename backlog's field first; and recognized-but-optional mechanics following the `Priority` precedent. OQ-01 fixes the child order.

Scope fence: this plan writes only its own record. Author NO product code and touch neither child's files. Both children already exist, so if executing this orchestrator seems to require writing one, STOP and report.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Specific to this Set: do NOT describe the outcome as enabling cross-tree filtering or search (F6).

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. Before every commit run `git diff --cached --name-only` and unstage anything not modified by this plan. Several sessions are committing to this checkout concurrently and at least one had unrelated files STAGED while this Set was authored, so verify the staged set rather than trusting a path-scoped command.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
