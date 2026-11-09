# IPD: Apply the repository-root path rule to the finalize scope paths and amend spec 4sd62s

- Date: 2026-11-09
- Kind: child
- Concern: Finalize records out-of-scope and widened paths that are code paths (`xexn45` F-05: 35 of 64 measured entries name `agent_workflows/` or `tests/`), but spec `4sd62s` 4.2 and `tve77h` E-03 (c) check `out_of_scope_paths` and `widened_paths` against the records root, which would refuse them (OQ-03). This is part of `8q27jt` (itself part of `xexn45`), split 2026-11-09.
- Scope: In `artifact_meta.validate_new_events`, apply the records-root containment rule to `path` only and the repository-root rule to `out_of_scope_paths` and `widened_paths`, and amend spec `4sd62s` 4.2 to say so (`8q27jt` E-03, path-root subset). EXCLUDES: writing the scope fields at finalize (`1dvb08`).
- Scope-Paths: agent_workflows/artifact_meta.py, tests/test_writers_scope_fields.py, tests/test_artifact_meta_registry.py, .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, .aw/records/plans/pending/20261109-metastore-131-9qhtrc-apply-the-repository-root-path-rule-to-the-finalize-scope-pa.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b, executed:7yr827
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 131
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9qhtrc

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 8q27jt (round 3, research nj8zdp guidance).
- 2026-11-09 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

`artifact_meta` accepts a repository-relative code path in `out_of_scope_paths` and `widened_paths` and still refuses an escaping path, and the spec says so.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: path-root rule

- [ ] E-01 In `artifact_meta.validate_new_events`, apply the records-root containment rule to `path` only, and apply "relative, no `..`, not absolute, sanitizer-scanned, inside the REPOSITORY root" to `out_of_scope_paths` and `widened_paths` (OQ-03, D-6). If `tests/test_artifact_meta_registry.py` (from `tve77h`) pins records-root containment for those two keys, change that assertion here under D-6 and name it in this plan. Create `tests/test_writers_scope_fields.py` with the OQ-03 cases: an `agent_workflows/x.py` out-of-scope path is stored and a `../x` path is refused.
  - Depends on: none
  - Expected outcome: the two OQ-03 cases pass; `tests/test_artifact_meta_registry.py` passes, with any changed assertion named.
  - Execution state: pending

- [ ] E-02 Amend spec `4sd62s` 4.2 (`.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`): the sentence saying `out_of_scope_paths` and `widened_paths` "are checked by the path rules (PATH HISTORY below)" gains "repository-relative for `out_of_scope_paths` and `widened_paths` (relative, no `..`, not absolute, inside the repository root), while `path` stays records-root-relative".
  - Depends on: E-01
  - Expected outcome: `git diff` of the spec shows only that sentence changed.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`. In phase B, `append` and `create` render through the one legacy renderer `artifact_meta.write_legacy` (file form) and `artifact_meta.render_legacy_text` (string form), both added by `7yr827`.
- UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4); atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`.
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- Finalize scope evidence is `evidence["scope_reconciliation"]` with `reasons` and `widened_paths` (`ipd_lifecycle._finalize_transaction`, `runner_shared.compute_scope_reconciliation`).
- Rollup retirement is `ipd_lifecycle.retire_orchestrator` -> `_finalize_transaction` with `evidence["transition"] == "orchestrator-rollup"`.

## Findings

| Id | Evidence (measured 2026-11-09 at `3d0ddb845`) | Finding |
|---|---|---|
| F-01 | `rg -n "checked by the path rules"` in the spec: one hit in 4.2 | One sentence to amend. |
| F-02 | `tests/test_artifact_meta_registry.py`: 21 tests | May pin the old rule; D-6 permits that one change. |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-6 (finalize path root, OQ-03). CHANGED: `out_of_scope_paths` and `widened_paths` are validated against the repository root, not the records root; `path` is unchanged. Named test: the OQ-03 cases in `tests/test_writers_scope_fields.py`, and any `tests/test_artifact_meta_registry.py` assertion that pinned the records-root rule for those two keys.

## Proposed changes (ordered, validatable)

1. Apply the path-root rule and add the OQ-03 tests (E-01).
2. Amend the spec sentence (E-02).

## Deferred / out of scope (with reason)

- Writing `scope_result`, `out_of_scope_paths` and `widened_paths` at finalize.
  - Carrier: 1dvb08
- The final merge-independence test, the AC-21 obligations test (which extends `tests/test_writers_obligations.py`), the raw-write audit (F-09), the documentation lines, and the full gates of the writer move.
  - Carrier: xexn45

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Creates `tests/test_writers_scope_fields.py` (OQ-03 cases; `1dvb08` adds the finalize cases).

## Spec / documentation sync

One spec amendment, carried with E-02: spec `4sd62s` 4.2 states that `out_of_scope_paths` and `widened_paths` are repository-relative, while `path` stays records-root-relative. Why: finalize paths are code paths that have no records-root form, so the current wording would refuse every out-of-scope code path that finalize records today (OQ-03).

## Open questions

### OQ-03: Are finalize's `out_of_scope_paths` and `widened_paths` records-root-relative?

- Blocking: no
- Status: resolved
- Owner: plan-review (round 1, decision D-2)
- Resolution or deferral rationale: No; they are repository-relative, exactly as `Scope-Paths` and `runner_shared.compute_scope_reconciliation` produce them. `xexn45` F-05 measures 35 of 64 entries as code paths (`agent_workflows/...`, `tests/...`) that have no records-root form. The 4.2 PATH HISTORY rule ("relative to the resolved records root") governs the artifact's own `path` field. `tve77h` E-03 (c) as written requires every `path`, `out_of_scope_paths` and `widened_paths` value to resolve inside the records root, and spec 4.2 says these two keys "are checked by the path rules (PATH HISTORY below)", so the approved texts and this decision disagree and 35 of 64 measured finalize paths would be refused. Resolution: `validate_new_events` applies the records-root containment rule to `path` only, and applies "relative, no `..`, not absolute, sanitizer-scanned, inside the REPOSITORY root" to `out_of_scope_paths` and `widened_paths`; the spec 4.2 sentence is amended in the same change. Recommendation strength: strong.
- Note: carried unchanged from `8q27jt` (originally `xexn45`) with its id, so the item text that cites it still resolves.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_scope_fields.py -k oq03 tests/test_artifact_meta_registry.py` with the stored `agent_workflows/x.py` case and the refused `../x` case PASSED by name, the `tests/test_artifact_meta_registry.py` PASSED count, and `git diff tests/test_artifact_meta_registry.py` (empty, or the one D-6 assertion change named).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `git diff .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` showing the one amended 4.2 sentence and nothing else.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where the Behavior decisions name it.

Honesty rule: run the named modules and the bare core gate `python3 -m pytest`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 9qhtrc -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 9qhtrc` itself.
