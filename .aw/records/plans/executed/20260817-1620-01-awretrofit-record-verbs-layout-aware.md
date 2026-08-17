# IPD: Make record writer/board/lint verbs layout-aware (plans/research/ipd-lint) + dual-layout regression tests

- Date: 2026-08-17
- Kind: child
- Concern: Post-migration record-verb regression cluster (release-review 20260817-153418 finding S2-B01 + S3-T01): the `.aw/` migration retrofit was applied to the reader/index verbs but not to the writer/board/lint verbs, which remain hardcoded to legacy `.agents/` and are blind/misleading on a migrated repo.
- Scope: Make the legacy-hardcoded record verbs layout-aware using the existing `resolve_record_path(<area>)` + legacy-read-fallback idiom (as in `plans_index._dirs`), and add falsifiable dual-layout regression tests. Verbs: `aw plans` board + `--write-index`, `aw plans set-assign`/`mv`/`archive`, `aw research new`/`new-comparison`/`set-assign`/`mv`/`check-refs`/`archive`/`promote`/`check-miscategorized`, `aw ipd lint --all`. Then regenerate the stale `.aw/records/plans/STATUS.md`. OUT: shipped docs/AGENTS.md (Order 02), install/uninstall/migration-engine (Order 04).
- Status: executed
- Set: awretrofit
- Order: 1
- Highest E allocated: 07
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: i7um6r

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): filled from release-review run 20260817-153418 findings S2-B01 + S3-T01 (Set awretrofit Order 01).
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Structural preflight conforming (author). Verified the finding citations against the real code (plans.py:155, cli.py:2824/2837, plans_refs.py:317, plans_archive.py:153, research_cmd.py:277, research_refs.py:124/260/285, research_archive.py:221, ipd_lint.py:745) and the fix idiom (plans_index._dirs:301-311, research_index._roots). PR-001 (LOW, IN-SCOPE, rubric C): the cluster's root cause is a second divergent resolver, so the plan now mandates ONE shared resolver per area (plans._resolve_area_dir, research_contract.resolve_research_root) reused by board+scan+write-index+refs. E/V bijection verified 1:1; E-06 covers every fixed verb with a fail-before/pass-after mutation probe. OQ-01 resolved (keep legacy read-fallback). No open questions; NO-GO only in the sense of pending human approval.
- 2026-08-17 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): human approved Order 01; implemented E-01..E-07 in commit 30d35dc (plans/cli/plans_refs/plans_archive/research_cmd/research_refs/research_archive/research_contract/ipd_lint + tests/test_awretrofit_layout_verbs.py + regenerated STATUS.md); V-01..V-07 verified (reproduced aw plans/ipd lint --all/research check-refs on this repo, 9 new tests pass, mutation probe RED->GREEN, full serial suite 982 passed / 1 skipped); pre-transition lint conforming; moved pending -> executed/.

## Goal

Restore the primary agent-facing record commands on migrated (`.aw/`) repos. After the awphysical
migration these verbs still read/write the vanished legacy `.agents/` tree, so they silently no-op,
false-pass a gate, or emit misleading errors (all reproduced in the release-review run). Route each
through the canonical layout-aware resolver with a legacy read-fallback, lock the behavior with
dual-layout regression tests that fail before the fix and pass after, and regenerate the stale
`STATUS.md`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

Canonical fix idiom (already proven in `plans_index._dirs`, plans_index.py:301-311 and
`research_index._roots`): resolve the area dir via
`resolve_record_path(<area>, target_repo=root)`; if that dir is absent AND the legacy
`root/.agents/<legacy-subpath>` exists, use the legacy dir (read-fallback for the retention window).
New content is created under the resolved `.aw/records/...` dir.

To avoid re-introducing a SECOND divergent resolver (the root cause of this whole cluster - rubric C),
each area gets ONE shared resolver that its board/scan/write-index/refs reuse: `plans._resolve_area_dir`
for plans+prompts (consumed by both `plans.scan` and `_run_plans`), and `research_contract.resolve_research_root`
for research (consumed by research new/refs/archive). `plans_refs`/`plans_archive`/`ipd_lint` inline the
same idiom (they are separate entry modules); the intent is a single resolution behavior per area, not
copy-pasted drift.

### Task group 1: plans board + write-index + refs/archive

- [x] E-01 Make `plans.scan()` (agent_workflows/plans.py:147-170) resolve its plans+prompts base via the layout-aware resolver instead of the hardcoded `root/.agents/{plans,prompts}`. Update the docstring. Keep the legacy dirs as read-fallback when the `.aw/records/*` dirs are absent.
  - Depends on: none
  - Expected outcome: `plans.scan(root)` returns records from `.aw/records/plans` (and `.aw/records/prompts`) on a migrated repo, and still from `.agents/*` on a legacy repo.
  - Execution state: performed

- [x] E-02 Fix `_run_plans` (agent_workflows/cli.py:2798-2846): replace the hardcoded `.agents/plans` existence gate (cli.py:2824) and the `--write-index` STATUS.md target (cli.py:2837) so the gate/board uses the resolved plans dir and STATUS.md is written next to the resolved plans dir.
  - Depends on: E-01
  - Expected outcome: `aw plans` lists the migrated plans; `aw plans --write-index` writes STATUS.md into `.aw/records/plans/` on a migrated repo.
  - Execution state: performed

- [x] E-03 Make `plans_refs._dirs` (agent_workflows/plans_refs.py:315-317) and `plans_archive._dirs` (agent_workflows/plans_archive.py:151-153) resolve the plans dir via the layout-aware resolver + legacy fallback (drop the unconditional `repo_root / PLANS_DIR`).
  - Depends on: none
  - Expected outcome: `aw plans set-assign`/`mv`/`archive` operate on `.aw/records/plans` on a migrated repo.
  - Execution state: performed

### Task group 2: research verbs

- [x] E-04 Add a shared research-root resolver mirroring `research_index._roots` (resolve_record_path("research") + legacy fallback) and route `research_cmd._research_root` (research_cmd.py:275-277), `research_refs` (research_refs.py:124/260/285), and `research_archive._roots` (research_archive.py:219-221) through it, replacing the hardcoded `repo_root / R.RESEARCH_ROOT`.
  - Depends on: none
  - Expected outcome: `aw research new`/`set-assign`/`mv`/`check-refs`/`archive`/`promote`/`check-miscategorized` read+write `.aw/records/docs/research` on a migrated repo; `aw research check-refs` no longer emits false-positive dangling id6 errors.
  - Execution state: performed

### Task group 3: ipd lint --all

- [x] E-05 Make `ipd_lint._iter_plan_files` (agent_workflows/ipd_lint.py:744-748) resolve the plans dir via the layout-aware resolver + legacy fallback instead of the hardcoded `root/.agents/plans`.
  - Depends on: none
  - Expected outcome: `aw ipd lint --all` scans `.aw/records/plans` and reports the real counts on a migrated repo (no more false conforming=0).
  - Execution state: performed

### Task group 4: regression tests + regenerate STATUS.md

- [x] E-06 Add falsifiable dual-layout regression tests (new `.aw/records/*`-only fixtures) proving each fixed verb resolves the migrated layout: plans board/scan + write-index target (tests/test_plans_board.py), plans set-assign/archive (tests/test_plans_refs.py / test_plans_archive.py), research new + check-refs (tests/test_research_*), and `ipd lint --all` (tests/test_ipd_lint.py). Each test must FAIL against the pre-fix code (mutation/verify) and PASS after.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: new tests green; a documented spot-check that at least one fails when the resolver is reverted.
  - Execution state: performed

- [x] E-07 Regenerate `.aw/records/plans/STATUS.md` via the now-fixed `aw plans --write-index` so the tracked artifact reflects reality (correct count + `.aw/records/plans` paths).
  - Depends on: E-02
  - Expected outcome: STATUS.md shows the real executed count and `.aw/records/plans/...` paths.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The layout-aware resolver is `agent_workflows.record_producers.resolve_record_path(<area>, target_repo=root)`; the proven CLI idiom (`plans_index._dirs`, plans_index.py:301-311; `research_index._roots`) resolves via it and falls back to legacy `.agents/<subpath>` only when the `.aw/records/*` dir is absent.
- Commit hook `ruff-format` reformats and aborts the first commit; re-verify + re-commit. Path-scoped commits only; never push.
- Tests are stdlib `unittest`; fixtures currently build only `.agents/*` trees (the masking gap S3-T01).

## Findings

From release-review run 20260817-153418 (all reproduced by the coordinator):

| id | verb | evidence | current behavior on migrated repo |
|---|---|---|---|
| B01a | `aw plans` board | plans.py:155, cli.py:2824 | "No plans found" (168 exist) |
| B01b | `aw plans --write-index` | cli.py:2837 | writes STATUS.md to legacy path |
| B01c | `aw plans set-assign`/`mv` | plans_refs.py:28/317 | "no plan has Id" (blind) |
| B01d | `aw plans archive` | plans_archive.py:31/153 | "no aged plans" (blind) |
| B01e | `aw research new` | research_cmd.py:277 | creates under legacy `.agents/docs/research` |
| B01f | `aw research check-refs` | research_refs.py:124 | FALSE-POSITIVE dangling id6 vs DECISIONS.md |
| B01g | `aw research archive`/`check-miscategorized` | research_archive.py:221 | "none" (blind) |
| B01h | `aw ipd lint --all` | ipd_lint.py:745 | conforming=0 (FALSE-PASSES the gate) |
| T01 | tests | .agents/* fixtures only | CI green while product broken |
| PR-001 | plan-review (arch, rubric C) | root cause = a second divergent resolver | LOW/IN-SCOPE: plan now mandates ONE shared resolver per area (plans._resolve_area_dir, research_contract.resolve_research_root) reused by board+scan+write-index+refs, not copy-pasted drift. FIXED in plan text. |

## Proposed changes (ordered, validatable)

1. E-01/E-02: plans board + scan + write-index -> resolved dir.
2. E-03: plans refs + archive -> resolved dir.
3. E-04: research new/refs/archive -> shared resolved research root.
4. E-05: ipd lint --all -> resolved plans dir.
5. E-06: dual-layout regression tests (fail-before/pass-after).
6. E-07: regenerate STATUS.md.

## Deferred / out of scope (with reason)

- Shipped workflow bodies + AGENTS.md generator .agents/ drift -> Order 02.
- RELEASING.md + Makefile version paths -> Order 03.
- install/uninstall scaffolder + migration-engine safety -> Order 04.
- Help strings/docstrings/README stubs/managed-sections/dead-code -> Order 05.

## Scope check

- Over-scope: none (each change is a mechanical resolver swap on a verb already proven broken).
- Under-scope: none within this Order's verb list; sibling concerns are explicitly deferred to Orders 02-05.

## Required tests / validation

- New dual-layout regression tests (E-06) fail before / pass after.
- `aw plans`, `aw ipd lint --all`, `aw research check-refs` reproduce correct behavior on this repo.
- Full serial suite stays green (baseline 973 passed / 1 skipped).
- `aw plans index --check`, `aw attention --check`, `aw sanitize --agent` remain clean.

## Spec / documentation sync

- CLI `--help` strings for these verbs still cite `.agents/` -> deferred to Order 05 (D04); this Order
  fixes behavior, Order 05 fixes the help prose. Note the cross-reference so they are not lost.

## Open questions

### OQ-01: Keep legacy `.agents/` read-fallback, or resolve `.aw/records/` only?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: KEEP the legacy read-fallback (mirror the existing
  `plans_index._dirs`/`research_index._roots` behavior) so the verbs work on both migrated and
  not-yet-migrated repos during the retention window. New content is always created under the
  resolved `.aw/records/...` dir. This matches the established convention and is the least-surprising,
  lowest-risk choice.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: A unit test building an `.aw/records/plans/*` + `.aw/records/prompts/*` tree (no `.agents/`) shows `plans.scan(root)` returns those records; a legacy-only fixture still works. Paste test output.
  - Observed evidence: Added `plans._resolve_area_dir` (plans.py) + made `scan` use it. `PlansBoardLayoutTests::test_scan_reads_aw_records_layout` (repository-backend `.aw/records/plans` fixture, no `.agents/`) asserts scan returns both plans with paths under `.aw/records/plans`; `LegacyFallbackTests::test_scan_falls_back_to_legacy` asserts the legacy fallback still works. `python3 -m pytest tests/test_awretrofit_layout_verbs.py` -> 9 passed.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: On this migrated repo, `aw plans` lists real plans (not "No plans found"); a test asserts `_run_plans` does not short-circuit on missing `.agents/plans` and `--write-index` targets the resolved dir. Paste `aw plans` head + test output.
  - Observed evidence: `aw plans` -> `Total: 188 plan/prompt file(s)` (was "No plans found"). `test_board_does_not_short_circuit_on_missing_agents` (asserts no "No plans found", lists the plan) and `test_write_index_targets_resolved_dir` (STATUS.md written to `.aw/records/plans`, NOT the legacy path) both pass.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `aw plans set-assign`/`archive` operate on `.aw/records/plans` (test with an aw-only fixture); reproduced behavior differs from the pre-fix "no plan has Id"/"no aged plans". Paste output.
  - Observed evidence: `plans_refs._dirs` + `plans_archive._dirs` now resolve via `resolve_record_path`+fallback. `ResearchAndRefsLayoutTests::test_plans_refs_and_archive_resolve_migrated_layout` asserts both resolve to the fixture's `.aw/records/plans`. Passed.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `aw research check-refs` on this repo no longer emits false-positive dangling id6 lines; a test shows `research new`/refs/archive resolve `.aw/records/docs/research`. Paste before/after `aw research check-refs` + test output.
  - Observed evidence: Added `research_contract.resolve_research_root` and routed research_cmd/research_refs (3 sites)/research_archive through it. BEFORE: `aw research check-refs` printed false-positive "dangling id6 'j2000q'..." lines vs DECISIONS.md. AFTER: `aw research check-refs` -> `no dangling citations`. `ResearchAndRefsLayoutTests::test_research_root_resolves_migrated_layout` asserts the resolver targets the repo-local `.aw/records/docs/research`. Passed.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `aw ipd lint --all` on this repo reports the real conforming/quarantined/legacy counts (not conforming=0); a test with an `.aw/records/plans/*` fixture confirms `_iter_plan_files` finds them. Paste `aw ipd lint --all` output + test.
  - Observed evidence: `aw ipd lint --all` -> `counts: conforming=1, quarantined=0, legacy/not evaluated=170, error=1` (was conforming=0; the single error is the pre-existing malformed historical plan `not-executed/...852jpc-...suite-error.md`, now correctly VISIBLE rather than hidden by the blind scan). `PlansBoardLayoutTests::test_ipd_lint_all_finds_migrated_plans` + `LegacyFallbackTests::test_ipd_lint_all_falls_back_to_legacy` pass.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: The new dual-layout regression tests pass; a documented fail-before/pass-after spot-check (revert one resolver -> a targeted test goes RED, restore -> GREEN). Paste both directions.
  - Observed evidence: `tests/test_awretrofit_layout_verbs.py` -> 9 passed (incl. `ResolverMutationProbe`). Documented spot-check: mutating `_resolve_area_dir` to the pre-fix `root/.agents/<area>` behavior -> `test_scan_reads_aw_records_layout` `1 failed`; restored -> `import OK` and suite green. Full serial suite: `python3 -m pytest -p no:xdist` -> `982 passed, 1 skipped in 174.87s` (was 973/1 pre-Order; +9 new tests).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: Regenerated `.aw/records/plans/STATUS.md` shows the real executed count and `.aw/records/plans/...` paths (not "Total: 61" / legacy paths). Paste head of the regenerated file.
  - Observed evidence: `aw plans --write-index` -> `OK Wrote .aw/records/plans/STATUS.md (188 entries)`; head shows `Total: 188 plan/prompt file(s).`; `grep -c '.agents/plans' STATUS.md` -> `0` (was Total: 61 with 61 legacy paths).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line.
The executor (opencode Opus 4.8) implements E-01..E-07, pastes the actual runner output (new tests +
full serial suite + the reproduced CLI behavior + the fail-before/pass-after spot-check), commits only
the explicitly scoped paths (agent_workflows/{plans,plans_refs,plans_archive,research_cmd,research_refs,
research_archive,ipd_lint}.py, agent_workflows/cli.py, the new/edited tests under tests/, and
.aw/records/plans/STATUS.md), never pushes, runs `aw ipd lint --phase pre-transition --agent` and the
full serial suite before any transition, and the orchestrator owns the terminal move to `executed/`.
This is a HIGH-priority correctness fix restoring the framework's primary agent interface post-migration.
