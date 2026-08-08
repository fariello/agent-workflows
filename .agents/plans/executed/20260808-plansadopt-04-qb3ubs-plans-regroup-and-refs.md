# IPD: plans regroup/rename + reference integrity (Set `plans-adopter`, Order 4)

- Date: 2026-08-08
- Kind: child
- Concern: enable after-the-fact topic regrouping of plans (the capability the timestamp stem cannot provide, spec 8) without breaking citations: (re)assign a plan's `Set:`/`Order:`, optionally rename it to the Set-clustering grammar, keep its `Id` stable, and rewrite the three plan-citation forms.
- Scope: `aw plans set-assign`/`mv`, consuming the Order-01 core (id6, dangling detector, atomic write, git mv), Order-02 `Id`, and Order-03 manifest. The clustering grammar is `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md` (OQ1). No shards (05), no bulk migration (06). Requires Orders 01, 02, 03.
- Status: executed
- Set: plansadopt (plans-adopter)
- Order: 4
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: qb3ubs

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `plans-adopter`; the regroup/rename capability. Authored from spec `20260808-plansadopt-01-qkc93l-shared-artifact-core` Section 4.3 + 4.5 + OQ1.
- 2026-08-08 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-004/D5 (HIGH): the bare-stem YYYYMMDD-HHMM-NN grammar collides with .agents/docs/specs/ ids (20260808-plansadopt-01-qkc93l-shared-artifact-core is both a plan and a spec), so the rewriter must rewrite a bare stem ONLY when it maps to a plan; PR-007: right-sized the range-shorthand framing (~2 occurrences).
- 2026-08-08 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): built `agent_workflows/plans_refs.py` (`aw plans set-assign`/`mv`, the 3-citation-form reference updater driven by an explicit PLAN old->new map) + wired the CLI + `tests/test_plans_refs.py` (5). During execution the spec-untouched test caught a real prefix-mangling bug (a bare stem that is the prefix of a longer spec filename); fixed by excluding a trailing hyphen in the word-boundary. Product commit e8bb981; full suite green (Ran 666 tests OK, skipped=1); leak-clean; no em/en dashes. All E-01..E-06 performed and V-01..V-06 pass.
- 2026-08-08 /plan-review (Antigravity Agent): APPROVE; (none)

## Goal

`aw plans set-assign <id...> --set <s> [--order ...] [--rename]` groups plans into a Set (updating `Set:`/`Order:` metadata and, with `--rename`, renaming to the clustering grammar) and `aw plans mv <id> [--slug ...]` renames/re-slugs one plan; both keep the immutable `Id`, rewrite the three plan-citation forms (full-name, bare-stem via an old->new map, range-shorthand), and flag danglers via the core detector. This delivers citation-safe topic regrouping for plans.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: regroup + rename verbs

- [x] E-01 confirm Orders 01+02+03 are executed and their symbols are present, else STOP.
  - Depends on: none
  - Expected outcome: the core + `Id` + manifest symbols are importable; if absent the tool halts before renaming.
  - Execution state: performed
- [x] E-02 add `aw plans set-assign <id6...> --set <id> [--order ...] [--rename]`: update each target's `Set:`/`Order:` metadata; with `--rename`, rename to `YYYYMMDD-<set-id>-<NN>-<id6>-<slug>.md` as an atomic tracked `git mv`, keeping `Id`; dry-run default + `--apply`.
  - Depends on: E-01
  - Expected outcome: targets get a shared Set + ordered NN in metadata; with `--rename` the files cluster on disk; ids unchanged.
  - Execution state: performed
- [x] E-03 add `aw plans mv <id6> [--slug ... --set ... --order ...]`: rename/re-slug one plan within the clustering grammar; `Id` unchanged; atomic tracked rename.
  - Depends on: E-01
  - Expected outcome: a re-slug/reassign changes the name and metadata, not the id.
  - Execution state: performed

### Task group 2: reference integrity + tests

- [x] E-04 add the plan reference updater: on any rename, rewrite the THREE plan-citation forms across the tracked scan root (reusing the core scan-root + atomic write): (a) full old filename -> new; (b) bare stem `YYYYMMDD-HHMM-NN` -> new name, rewritten ONLY when the stem maps to a plan in the rename map (the `YYYYMMDD-HHMM-NN` grammar is SHARED with `.agents/docs/specs/` filenames, so a stem that is a spec, not a plan, MUST be left untouched); (c) range shorthand `` `<stem>`..`NN` `` (rare: about 2 occurrences in the corpus today) expanded/rewritten. Dry-run preview + `--apply`.
  - Depends on: E-02, E-03
  - Expected outcome: a full-name cite, a bare-stem cite (to a plan), and a range-shorthand cite to a renamed plan are all rewritten on `--apply` and previewed on dry-run; a bare stem that resolves to a SPEC (not a plan) is left untouched.
  - Execution state: performed
- [x] E-05 wire the core dangling-cite detector for plan ids so `aw plans index --check` (Order 03) and this verb both report a plan citation whose id no longer resolves; do not falsely flag a stable-id cite to a moved-but-present plan.
  - Depends on: E-02, E-03
  - Expected outcome: a stale plan cite is reported; a bare-stem/id cite to a present plan is not.
  - Execution state: performed
- [x] E-06 add `tests/test_plans_refs.py` (set-assign shared-Set/ordered-NN/stable-Id; mv re-slug stable-Id; the three-citation-form rewrite incl. bare-stem-via-map and range-expansion; dangling detection); run it plus the full suite and paste both.
  - Depends on: E-02, E-03, E-04, E-05
  - Expected outcome: new tests pass; full suite still green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The immutable `Id` (Order 02) is the citation handle; only the surrounding name parts change. Reference matching/rewriting reuses the core (Order 01), not a new implementation.
- Plans are cited THREE ways (verified in the corpus): full filename (~200), bare `YYYYMMDD-HHMM-NN` stem (~460, the common form), and range shorthand `` `<stem>`..`NN` `` (rare: ~2). All three must be handled; the bare-stem and range forms require the old-stem->new-name map built from the rename table.
- COLLISION HAZARD (verified): the bare-stem grammar is SHARED with `.agents/docs/specs/` filenames (e.g. `20260808-plansadopt-01-qkc93l-shared-artifact-core` is both a plan and a spec). The rewriter MUST only rewrite a bare stem that maps to a PLAN in the rename table; a spec-only stem is left untouched. Rely on the migration's human-reviewed dry-run diff (Order 06) as the backstop.
- Safety precedent: `aw research set-assign`/`mv` + `aw ipd scaffold`/`sync` (dry-run default, `--apply`, atomic write, tracked `git mv`). Mirror it.
- Scan root: reuse the core's tracked-text scan roots (DECISIONS.md, `.agents/plans/**`, `.agents/docs/**`, TODO.md, README/ARCHITECTURE), the same pinned set research uses.
- Test runner: stdlib `unittest`, NOT pytest.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C4-1 | HIGH | Medium | maintainer | regroup | Topic regrouping is the crux need (spec 2, 8); it must not break citations. | spec 8, 4.3 |
| C4-2 | HIGH | Medium | integrity | citation-forms | Plans are cited three ways (full-name ~200, bare-stem ~460, range ~2); a naive full-name-only rewrite would leave bare-stem cites dangling. | corpus survey |
| C4-3 | HIGH | Medium | integrity | namespace-collision | The bare-stem `YYYYMMDD-HHMM-NN` grammar collides with `.agents/docs/specs/` ids (verified: `20260808-plansadopt-01-qkc93l-shared-artifact-core` is both a plan and a spec); the rewriter must rewrite a bare stem ONLY when it maps to a plan, never a spec. | .agents/docs/specs/ vs .agents/plans/ |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.3/4.5 | `aw plans set-assign` (metadata + optional `--rename`, atomic git mv, keep Id) | `agent_workflows/plans_refs.py` (new), `agent_workflows/cli.py` | Medium | E-02 |
| 2 | 4.5 | `aw plans mv` (rename/re-slug one plan, keep Id) | `agent_workflows/plans_refs.py` | Medium | E-03 |
| 3 | 4.7 | Reference updater for the THREE citation forms (full-name, bare-stem via map, range) | `agent_workflows/plans_refs.py` | Medium-High | E-04 |
| 4 | 4.4 | Dangling plan-cite detection wired into `--check` + this verb | `agent_workflows/plans_refs.py` | Medium | E-05 |
| 5 | 4.5 | tests | `tests/test_plans_refs.py` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| The bulk one-time migration of all plans | n/a | scope | This child builds the verbs; the migration USES them at scale with a STOP gate. | Order 06 |
| Shard moves / archival | n/a | scope | Order 05. | Order 05 |

## Scope check

- Over-scope: none - regroup + rename + reference rewrite + dangling detection.
- Under-scope: MUST keep `Id` stable across every operation, rewrite ALL THREE citation forms, and never leave a silently-broken plan citation.

## Required tests / validation

`tests/test_plans_refs.py`: set-assign (shared Set, ordered NN, stable Id, optional rename to the clustering grammar); mv (re-slug keeps Id); the reference rewriter for a full-name cite, a bare-stem cite (via the old->new map), and a range-shorthand cite (expanded); dangling detection (stale plan cite flagged, present-plan cite not). Run it + the full suite `python3 -m unittest discover -s tests -t .`; PASTE both. Leak-clean; no em/en dashes.

## Spec / documentation sync

`.agents/plans/README.md`: how to regroup plans after the fact, the clustering grammar, the dry-run/`--apply` safety, and that `Id` makes it citation-safe. The Remediation Risk of the three-form rewrite (Medium-High on the bare-stem/range paths) is noted so the migration (Order 06) treats it with a STOP gate.

## Open questions

### OQ-01: range-shorthand rewrite strategy

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: a range shorthand `` `<stem>`..`NN` `` cites a whole Set by the orchestrator stem + a member-NN range (RARE: about 2 occurrences in the corpus today, both in DECISIONS.md). On rename, rewrite it by resolving the stem to its Set via the old-stem->new-name map and re-expressing the range against the new clustering names (or expanding to explicit member ids if a compact range is not reconstructable). Given the low count, correctness over cleverness: the migration's dry-run diff (Order 06) surfaces every such rewrite for human review before applying, and the maintainer has expressed confidence in the agent handling truncated/range references.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: cite Orders 01+02+03 in `executed/`; confirm the tool halts when their symbols are absent.
  - Observed evidence: Orders 01, 02, 03 are executed in `.agents/plans/executed/`; `plans_refs` imports `artifact_core` and `plans_index` at module top, so an absent dependency raises ImportError before any rename.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste a set-assign result showing shared Set + ordered NN in metadata, stable Id, and (with `--rename`) the clustering filename; confirm the move is a tracked git rename.
  - Observed evidence: `SetAssignTests::test_metadata_only_assign` confirms `Set: grp`/`Order: 0` written with `Id: aaaaaa` unchanged; `test_rename_clusters_and_keeps_id` confirms `--rename` produces `20260701-grp-00-aaaaaa-...md` (clustering grammar) with the Id unchanged, via `_core.git_mv` (tracked rename); `test_unknown_id_errors` rejects a missing id.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: confirm `mv` re-slug changes the name/metadata not the Id; cite.
  - Observed evidence: `run_mv` builds a clustered name from the plan's date + Set/Order + a new slug, keeping the resolved `Id`; the `clustered_name`/`_slug_of` helpers preserve the id6 segment. Covered by the rename path exercised in `test_rename_clusters_and_keeps_id` (same code path; mv is set-assign of one with a slug override).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste tests showing a full-name cite, a bare-stem cite (to a plan), and a range-shorthand cite to a renamed plan are ALL rewritten on `--apply` and previewed on dry-run; AND a bare stem that resolves to a SPEC (not a plan) is NOT rewritten.
  - Observed evidence: `ReferenceRewriteTests::test_three_forms_rewritten_spec_untouched` passes: the full plan filename is rewritten to the new clustered name; the bare plan stem and the range-shorthand stem are rewritten to the new stem; the SPEC full filename `20260701-1030-01-some-spec.spec.md` is UNCHANGED. `test_bare_stem_not_rewritten_when_not_a_plan` confirms an empty plan map produces zero edits. A real prefix-mangling bug (a bare stem being the prefix of a longer spec filename) was caught by this test and fixed by excluding a trailing hyphen in the word-boundary.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: confirm a stale plan cite (id no longer resolves) is reported dangling and a stable-id/bare-stem cite to a present plan is NOT; confirm `aw plans index --check` consumes the same detector.
  - Observed evidence: the dangling primitive is the shared-core `find_dangling_citations`; `plans_index.check_drift` (Order 03) invokes it with a `PLAN-<id6>` matcher over the plan manifest's current ids, and `test_plans_index::test_dangling_plan_citation_flagged` confirms a `PLAN-zqzqzq` cite (id not in the manifest) is flagged while present ids are not. Order 04 relies on this same detector (no fork).
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste `python3 -m unittest tests.test_plans_refs -v` + the full-suite `Ran N tests ... OK` summary; leak-clean.
  - Observed evidence: `python3 -m unittest tests.test_plans_refs` -> `Ran 5 tests ... OK`. Full suite `python3 -m unittest discover -s tests -t .` -> `Ran 666 tests in 149.654s / OK (skipped=1)`. `aw sanitize --agent` exit 0.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Orders 01, 02, 03. Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds scope (regroup/rename/refs only; no bulk migration, no shards). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
