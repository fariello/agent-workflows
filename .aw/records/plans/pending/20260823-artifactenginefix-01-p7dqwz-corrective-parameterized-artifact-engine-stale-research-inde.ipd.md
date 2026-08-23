# IPD: Corrective: parameterized artifact engine, stale research index, and group scope/UX fixes

- Date: 2026-08-23
- Kind: child
- Concern: Three executed plans (autoindex hszr72, grouptypes o2ygf3, renametypes 53yczi) left post-execution gaps: the mandated parameterized per-type engine was not built (a monolithic regex-switch module was built instead, and plans/research were not unified onto it); the research manifest index is stale; and aw group carries a scope-creep releases route with no test plus a silent-success UX gap.
- Scope: agent_workflows/artifact_rename.py, agent_workflows/plans_refs.py, agent_workflows/research_refs.py, agent_workflows/artifact_core.py, agent_workflows/artifact_types.py, agent_workflows/status_set.py, the research manifest index, and the rename/group test suites. Does NOT reopen or edit the three executed IPDs.
- Status: draft
- Set: artifactenginefix
- Order: 1
- Highest E allocated: 06
- Author: Gabriele Fariello
- Id: p7dqwz

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.

## Goal

Close the post-execution gaps left by the three executed sibling plans (`hszr72`, `o2ygf3`, `53yczi`) without editing those executed IPDs: (1) replace the monolithic regex-switch `artifact_rename.py` engine with the parameterized per-type engine those plans mandated (inject per-type name-builder, reference-rewriter, metadata-writer) and unify `plans`/`research` onto it so there is a single rename/group backend rather than two parallel implementations; (2) restore the mandated third citation form (range shorthand) in reference rewriting; (3) re-seat the stale research manifest index and confirm `aw check all` reports zero `stale-index`; (4) resolve the `aw group releases` scope question (either cover it with a test and document it as in-scope, or remove the route); and (5) emit a success confirmation line from `aw group --apply`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Parameterized per-type engine (replaces the monolithic regex-switch)

- [ ] E-01 Refactor `agent_workflows/artifact_rename.py` from the current monolithic `run_rename_generic`/`run_group_generic` (which switch on a fixed set of filename regexes) into the PARAMETERIZED per-type engine the three sibling plans mandated: a single core apply-path that is injected, per artifact type, with a name-builder, a reference-rewriter, and a metadata-writer. Prefer extending `agent_workflows/artifact_core.py` for any newly-shared primitive; keep the per-type handler surface small. Do NOT regress any behavior currently covered by `tests/test_artifact_rename.py` / `tests/test_artifact_group.py`.
  - Depends on: none
  - Expected outcome: rename/group for every in-scope type dispatches through one parameterized engine with per-type injected handlers, not a regex ladder.
  - Execution state: pending

- [ ] E-02 Unify `plans` and `research` onto the parameterized engine from E-01 by expressing each type's divergent behavior as an injected handler rather than a separate module, preserving all existing behavior and the `hszr72` auto-index hook. Divergence to encode per handler: plans edits in-file `- Set:`/`- Order:` and uses the clustered grammar; research encodes set/order in the filename, requires `--date`, and reads extra `--kind`/`--model` facets. If full unification proves unsafe in one pass, split the residual into a follow-up E-item rather than leaving two parallel engines.
  - Depends on: E-01
  - Expected outcome: `plans`/`research` rename and group route through the single parameterized engine with no behavior change and the auto-index hook intact.
  - Execution state: pending

- [ ] E-03 Restore the third citation form in reference rewriting. The mandated plans behavior rewrites full name + bare stem + range shorthand; the current generic engine (`plan_reference_rewrites`) rewrites only full-name and bare-stem. Add range-shorthand rewriting to the parameterized reference-rewriter (at least for the clustered-grammar types) so a rename does not orphan range-shorthand citations.
  - Depends on: E-01
  - Expected outcome: renames rewrite all three citation forms; no orphaned range-shorthand references remain.
  - Execution state: pending

### Task group 2: Stale research manifest index

- [ ] E-04 Re-seat the stale research manifest index. On the current tree `aw index research --check` reports `stale-index` on both `INDEX.json` and `INDEX.md` (pre-existing debt, not introduced by the three siblings, but it means the repo is not in the zero-drift state their narrative implies). Run `aw index research` to regenerate, verify the regenerated index is deterministic (re-running produces no diff), and commit the refreshed index path-scoped. Investigate briefly whether any research mutation path still bypasses the `hszr72` auto-index hook; if one is found, record it as a follow-up E-item.
  - Depends on: none
  - Expected outcome: `aw index research --check` is clean and `aw check all` reports zero `stale-index` findings.
  - Execution state: pending

### Task group 3: aw group releases scope + UX

- [ ] E-05 Resolve the `aw group releases` scope creep. `releases` was registered as a `group` route in `agent_workflows/artifact_types.py` by the grouptypes commit, but `releases` was NOT in grouptypes' OQ-02 scope and has no test. Per OQ-01 below, either (a) keep it, add `test_group_releases` covering set-injection/preview/apply, and document releases as in-scope for group; or (b) remove the `run_group_releases` route. Do not leave an untested, undocumented route.
  - Depends on: none
  - Expected outcome: the `releases` group capability is either tested + documented or removed; no untested route remains.
  - Execution state: pending

- [ ] E-06 Emit a success confirmation line from `aw group <type> --apply`. Today a successful `--apply` that injects `- Set:` prints nothing (it does mutate, so it is not a silent no-op, but it gives no operator feedback). Print a concrete confirmation (e.g. the injected/updated `- Set:` and any rename) consistent with how `aw rename --apply` reports, and cover it in a test.
  - Depends on: none
  - Expected outcome: `aw group --apply` prints a clear per-artifact confirmation line; a test asserts it.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AGENTS.md agent execution contract: "Do NOT add commits to a plan already in `.aw/records/plans/executed/`; close a post-execution gap with a new corrective IPD, not an in-place edit." This IPD is that corrective instrument for the gaps found verifying `hszr72`, `o2ygf3`, `53yczi`.
- `agent_workflows/artifact_core.py` owns the shared primitives (`iter_scan_files`, `atomic_write`, `git_mv`, id6/kebab helpers) and deliberately keeps filename-grammar and reference-rewriting per-area; it is the preferred home for any newly-shared primitive.
- `plans_refs`/`research_refs` genuinely diverge (frontmatter-vs-filename set/order encoding, three-vs-one citation forms, extra `--kind`/`--model` facets on research), which is exactly why the sibling plans mandated a parameterized engine rather than a copy-paste.
- The `hszr72` auto-index hook lives in `status_set.py::_auto_index_types` and in the `plans`/`research` branches of `artifact_rename.run_rename_generic`/`run_group_generic`; it must be preserved through the refactor.

## Findings

Verification of the three executed sibling plans (2026-08-23) found:
- The mandated parameterized per-type engine was not built. `agent_workflows/artifact_rename.py` is a monolithic regex-switch (`run_rename_generic`/`run_group_generic`) with thin per-type string wrappers; `plans`/`research` still route to their old `plans_refs`/`research_refs` backends, so there are two parallel implementations rather than one shared engine.
- Reference rewriting drops the third citation form: `plan_reference_rewrites` handles full-name + bare-stem only, not the range shorthand the clustered grammar uses.
- `aw check all` reports `stale-index` on the research `INDEX.json`/`INDEX.md` (bisected to pre-date the three siblings at commit 152211e; pre-existing debt, not a regression from these plans).
- `aw group` registered a `releases` route (grouptypes commit) that is outside grouptypes' OQ-02 scope and has no test.
- `aw group <type> --apply` prints no confirmation on a successful set-injection.
- All three siblings otherwise executed faithfully: named tests exist and pass, `pytest -n auto` is green (2094 passed, 1 skipped), lifecycle moves were path-scoped git renames, and no pushes occurred. This corrective IPD does NOT dispute their executed status; it closes the residual gaps.

## Proposed changes (ordered, validatable)

1. Build the parameterized per-type rename/group engine and route all in-scope types through it (E-01).
2. Unify `plans`/`research` onto that engine, preserving divergent behavior and the auto-index hook (E-02).
3. Restore range-shorthand reference rewriting (E-03).
4. Regenerate and re-seat the research manifest index; confirm zero drift (E-04).
5. Resolve `aw group releases` (test+document or remove) (E-05).
6. Add `aw group --apply` success output + test (E-06).

## Deferred / out of scope (with reason)

- Editing the three executed IPDs (`hszr72`, `o2ygf3`, `53yczi`): out of scope by the AGENTS.md rule against amending executed plans.
- The `hszr72` silent `except Exception: pass` around auto-index and its duplicated workflow-history line: cosmetic; note only, fix opportunistically if E-02 touches that code, otherwise defer.
- Roadmap legacy-`HHMM` component being dropped on rename: roadmap names are free-form; deferred unless E-01's per-type roadmap handler makes it trivial to preserve.

## Scope check

- Over-scope: none. The three executed IPDs are not edited.
- Under-scope: none, given the E-item set covers engine unification, citation fidelity, index freshness, and the two group defects.

## Required tests / validation

- `tests/test_artifact_rename.py` and `tests/test_artifact_group.py` extended and still green (including new range-shorthand and group-confirmation assertions, and `test_group_releases` if E-05 keeps the route).
- A regression test proving `plans`/`research` rename and group behavior is unchanged after E-02 unification and that the auto-index hook still fires.
- `aw index research --check` clean and `aw check all` reporting zero `stale-index` (paste actual output).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- If E-05 keeps `releases` in group scope, note it in the relevant CLI `--help`/docs. Otherwise N/A.

## Open questions

### OQ-01: Is `aw group releases` intended to be supported?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO. If yes, E-05 keeps the route, adds `test_group_releases`, and documents it. If no, E-05 removes the `run_group_releases` route. The executor MUST resolve this before implementing E-05.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: rename/group tests pass and the engine dispatches through one parameterized core with per-type injected handlers (no regex ladder remains); `tests/test_artifact_rename.py` + `tests/test_artifact_group.py` green.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a regression test proves `plans`/`research` rename+group behavior is unchanged after unification and the `hszr72` auto-index hook still fires; suite green.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a test asserts a rename rewrites the range-shorthand citation form (not just full-name/bare-stem) with no orphaned references.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `aw index research --check` clean output and `aw check all` showing zero `stale-index`; regenerated index is deterministic on re-run.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: per OQ-01 resolution, either `test_group_releases` passes and releases-in-group is documented, or the `run_group_releases` route is removed and a test asserts `aw group releases` is unsupported.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: a test asserts `aw group <type> --apply` prints a concrete per-artifact confirmation line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: single cohesive theme (make the artifact rename/group engine match the design contract the three siblings were approved on, and clear the residual index/scope/UX gaps they left).

### Execution contract

1. Open questions RESOLVED: OQ-01 (releases-in-group) MUST be resolved by the human before executing E-05.
2. Scope fence: refactor and unify the rename/group engine and clear the named residual gaps WITHOUT editing the three executed IPDs and without changing manifest index schema/format contracts.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
