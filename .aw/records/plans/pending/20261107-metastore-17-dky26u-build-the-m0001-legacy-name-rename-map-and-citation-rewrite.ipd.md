# IPD: Build the m0001 legacy-name rename map and citation rewrite

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` 5.2 step 3 renames every legacy-timestamp record and rewrites every citation of it. Measured 2026-11-07: 35 tracked records outside comms match `artifact_naming._LEGACY_TIMESTAMP_RE` (34 after the OQ-02 template exclusion), and `dcerjg` F-05 measured 2,035 citation hits in 457 files over the widened scan roots. Plan `dcerjg` owned this step; it was split 2026-11-07 per the maintainer's step-complexity rule.
- Scope: Create `agent_workflows/migrations/m0001_renames.py` with `classify_name`, `build_rename_map` (`dcerjg` E-07) and `plan_citation_rewrites` (`dcerjg` E-08), and its test module (subset of `dcerjg` E-14). The citation step is ONE call to `artifact_refs.plan_reference_rewrites_with_warnings` over the scratch copy; the executor writes no per-citation edit by hand, so the 2,035 hits are the tool's output, not hidden manual steps. EXCLUDES: preflight, journal and sidecar (`vxevph`); conversion (`ghhzb6`, `hpedmn`); census, round trip and the end-to-end clone proof (`dcerjg`).
- Scope-Paths: agent_workflows/migrations/m0001_renames.py, agent_workflows/migrations/m0001_metadata_v2.py, tests/test_m0001_renames.py, .aw/records/plans/pending/20261107-metastore-17-dky26u-build-the-m0001-legacy-name-rename-map-and-citation-rewrite.ipd.md
- Item-Dependencies: executed:tve77h, executed:vxevph
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 17
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: dky26u

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from dcerjg per maintainer step-complexity rule (no single E/V item hides hundreds of steps).
- 2026-11-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`m0001` can compute, on a scratch copy, the full legacy-name rename map and the citation rewrite with its per-location report, proven on fixtures; the clone dry-run evidence is pasted by `dcerjg` V-15.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: rename map and citations

- [ ] E-01 Create `agent_workflows/migrations/m0001_renames.py` with `classify_name(name)`, which tests `artifact_naming._LEGACY_TIMESTAMP_RE` BEFORE `artifact_naming.parse_clustered` (so `20260712-1033-01-assess-bugs-...` is legacy, not `set=1033, id6=assess`), and `build_rename_map(repo, journal)` for every tracked artifact, walkthrough and roadmap with a legacy name, excluding comms, `.data/` files, READMEs and the six templates named in OQ-02: mint a repository-unique `id6` with `artifact_core.mint_id6` for each id-less record and journal it; keep an existing `- Id:`; `set` is the existing `- Set:` or else the record's `id6`; `order` is the logged `- Order:` when present, otherwise the filename `NN` (OQ-26 correction); emit `YYYYMMDD-<set>-<NN>-<id6>-<slug>.<type>.md` with the original date, slug and facet. Do not call `artifact_rename.compute_target_name`, which hard-codes `set_id=mint_id6, order=1`. Refuse the map when two plans would share a Set and order.
  - Depends on: none
  - Expected outcome: on this repository (measured at authoring and re-checked at review: 35 legacy-timestamp files outside comms, minus the one OQ-02 template) the map has 34 entries: 28 minted (17 specs, 11 walkthroughs) and 6 preserved; the BAR is re-derived at execution time as "every `_LEGACY_TIMESTAMP_RE` record outside comms and the OQ-02 exclusions is mapped, each id-less one minted, each `- Id:` one preserved", and the fixed rows below are stable code facts of terminal records, with `wvlk84` mapped to `20260817-awphysical-17-wvlk84-assess-bugs-leftover-remove-dataloss.ipd.md`, `lus9ou`/`7qx7ys`/`8q6yr9` to `plans-adopter` orders 00, 06, 07, and `4o5lt9`/`4w7d6s` to Sets equal to their own `id6`.
  - Execution state: pending

- [ ] E-02 In `m0001_renames.py`, add `plan_citation_rewrites(repo, rename_map)` calling `artifact_refs.plan_reference_rewrites_with_warnings` with `scan_roots=artifact_core.REFERENCE_SCAN_ROOTS + ("agent_workflows", "docs", ".aw/system", "CHANGELOG.md")` (passed as an argument; `REFERENCE_SCAN_ROOTS` itself is unchanged so `aw rename` keeps its roots), then drop every edit that falls inside text that step 4 imports byte for byte (each `## Workflow history` line, sidecar objects, legacy `- Verdict:` values) and every entry of a named exemption list (deliberate old-format examples: the legacy-name fixture in `tests/test_plans_rename_selectors.py` and code comments in `artifact_naming`, `artifact_refs`, `plans_refs`, `artifact_rename` that describe the old grammar). The step captures each history line BEFORE any rewrite, applies the remaining edits in the scratch copy, and reports hits per location (top-level directory, or records type) plus every citation left unchanged with its reason.
  - Depends on: E-01
  - Expected outcome: the dry-run report on the clone shows per-location counts that sum to the planned edits, 0 ambiguity warnings, a non-empty "left unchanged" list naming the history-line and exemption reasons, and no edit inside any `## Workflow history` section.
  - Execution state: pending

### Task group 2: tests

- [ ] E-03 Add `tests/test_m0001_renames.py`, moved here from `dcerjg` E-14 (subset), on `tmp_path` fixture repositories built with real `git init`, calling the real functions and asserting on outputs (no source reading): AC-41 cases 2 and 3 on fixtures, the logged-Order rule, the Set-and-order collision refusal, citation exemptions and history-line protection. Mark it `core`, or `slow` if its slowest test exceeds 2 s in `--durations=10`, named in V-03.
  - Depends on: E-01, E-02
  - Expected outcome: the module passes under `python3 -m pytest -o addopts="" -v tests/test_m0001_renames.py`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Transactional migrations reuse `layout_migration.MigrationManager` (`_acquire_lock`, `_save_transaction`, `_load_transaction`, `resume_migration`, `rollback_migration`); spec 5.1 forbids new journal or lock components (carried from `dcerjg` Step 0).
- Path roots come from `project_context.resolve_project_context` (`config_project`, `state_durable`, `records`), never `<repo>/.aw/...` literals (spec 4.5, 5.1).
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); new modules set `pytestmark = pytest.mark.core` unless the `--durations=10` rule of `dcerjg` E-14 moves one to `slow`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- Naming authority is `artifact_naming` (`_LEGACY_TIMESTAMP_RE`, `parse_clustered`); citations go through `artifact_refs.plan_reference_rewrites_with_warnings`, whose `scan_roots` is a parameter; ids are minted by `artifact_core.mint_id6` (repository-wide collision check) (carried from `dcerjg` Step 0).

## Findings

| Id | Evidence (measured 2026-11-07 in this worktree) | Finding |
|---|---|---|
| F-01 | `git ls-files .aw/records` filtered by `artifact_naming._LEGACY_TIMESTAMP_RE`, comms excluded: 35 | E-01 hidden work: 1 classifier, 1 map builder, 34 mapped records produced by code (not by hand), 4 rules (mint, keep Id, Set, logged Order), 1 collision refusal: about 8 code units. |
| F-02 | `artifact_core.REFERENCE_SCAN_ROOTS` holds 19 roots; `artifact_refs.plan_reference_rewrites_with_warnings(repo_root, name_map, scan_roots=...)` takes them as an argument | E-02 hidden work: 1 call, 4 added roots, 3 protected text classes, 1 exemption list of 5 entries (`tests/test_plans_rename_selectors.py`, `artifact_naming`, `artifact_refs`, `plans_refs`, `artifact_rename` comments), 1 report: about 11 units; the 2,035 edits are applied by the tool in scratch. |
| F-03 | `rg -n "def compute_target_name" agent_workflows/artifact_rename.py`: builds `set_id=mint_id6, order=1` | It cannot be reused for the OQ-26 rule (carried from `dcerjg` F-13). |

## Proposed changes (ordered, validatable)

1. E-01: classifier and rename map.
2. E-02: citation plan and report.
3. E-03: tests.

## Deferred / out of scope (with reason)

- The end-to-end clone proof with apply, commit and second apply, and its rename and citation sections.
  - Carrier: dcerjg

## Scope check

- Over-scope: none. `m0001_metadata_v2.py` is touched only to call the step-3 functions in the journaled run.
- Under-scope: none for `dcerjg` E-07 and E-08 on fixtures (AC-41 cases 2 and 3); AC-41 cases 1 and 5 on the clone are pasted by `dcerjg` V-15.

## Required tests / validation

New module: `tests/test_m0001_renames.py` (`core`). Existing: `tests/test_plans_rename_selectors.py`. Gate: bare `python3 -m pytest`.

## Spec / documentation sync

No spec change; implements `4sd62s` 5.2 step 3, OQ-26, OQ-27 and OQ-28.

## Open questions

### OQ-02: How are roadmaps, prompt-library files, research templates, reference packages and READMEs handled (spec 4.1 "the plan must also decide, by name")?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Carried from `dcerjg` OQ-02 (resolved there; the full decision text stays in `dcerjg`). For this part: the six templates named there are excluded from the rename map, the legacy-named research template stays the one `_LEGACY_TIMESTAMP_RE` match, and READMEs, comms and `.data/` files are never renamed.

- Note: carried unchanged from `dcerjg` with its id, so item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_renames.py -k "classify or order or collision"` all PASSED. (The clone dry-run rename-map section, with the `wvlk84` and `plans-adopter` rows, moved to `dcerjg` V-15, because the clone proof runs after every part.)
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_renames.py -k citation` all PASSED, including the test that a `## Workflow history` line citing an old name is not edited. (The clone dry-run citation section moved to `dcerjg` V-15.)
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_renames.py --durations=10` with every test PASSED, naming the slug-starts-with-a-6-letter-word classification test, the logged-Order test, the collision-refusal test, the exemption test and the history-line-protection test; and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: this plan NEVER runs `aw migrate metadata --apply` (or bare `aw migrate --apply`) in this checkout. Every apply is on a `tmp_path` fixture repository. If an apply would touch this checkout's records, stop and report: that is a genuinely unsafe condition, not a scope question.

Honesty rule: run the named test modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit dky26u -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize dky26u` itself.
