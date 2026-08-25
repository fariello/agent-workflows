# IPD: Fix aw rename order slug mangle preserve slug when order changes

- Date: 2026-08-24
- Kind: child
- Concern: `aw rename plans <id6> --order <NN>` without an explicit `--slug` corrupts the slug: it injects the OLD cluster segment (`<setid>-NN-`) into the new slug instead of changing only the NN facet. Observed 2026-08-23 renumbering the ipdgates Set: `aw rename plans wezhxg --order 07` proposed a target with `ipdgates-06-` embedded in the slug. Root cause: `_slug_of(old_name, id6)` (`plans_refs.py:156-165`) re-derives the slug by splitting the filename and dropping only leading pure-digit tokens and the id6, so it strips the date but leaves the `<setid>` and `NN` tokens in the slug; `run_mv` (`plans_refs.py:379-418`) then feeds that mangled slug back into `clustered_name`. This is silent filename corruption on a common regroup/renumber operation. Backlog item dcla4g (release-blocker for 2.0.0 / f33nrj).
- Scope: Fix `_slug_of` in `agent_workflows/plans_refs.py` so renaming with `--order` alone preserves the true slug, by parsing the clustered name with the canonical parser (`artifact_naming.parse_clustered` / `_CLUSTERED_RE`) and returning its `slug` group rather than the digit-stripping heuristic. Add a regression test asserting `rename --order` alone preserves the slug. Single-child plan for the awrenamebug Set.
- Scope-Paths: agent_workflows/plans_refs.py, tests/test_plans_refs.py
- Status: to-review
- Set: awrenamebug
- Order: 1
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 5rzupk

## Workflow history
- 2026-08-24 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): Completed drafting: fully authored, lint-conforming, ready to critique

- 2026-08-24 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created; single-child plan for backlog item dcla4g (rename --order slug mangle). NOTE: release-blocker intent (`Blocks-Release: next`, gates 2.0.0 / f33nrj) is DEFERRED from front matter until the vwios6ipd Set makes plans able to carry the field without failing `aw ipd lint` (IPD-M103). Interim intent is tracked on backlog item dcla4g and the f33nrj release record; re-mark via `aw ipd set --blocks-release next` once that Set lands.

## Goal

Make `aw rename plans <id6> --order <NN>` (without `--slug`) preserve the plan's real slug and change only the Order facet, eliminating the silent injection of the old `<setid>-NN-` cluster prefix into the new slug.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Fix the slug derivation

- [ ] E-01 Replace the heuristic body of `_slug_of(old_name, id6)` in `agent_workflows/plans_refs.py` (`plans_refs.py:156-165`) so it parses `old_name` with the canonical clustered-name parser (`artifact_naming.parse_clustered` / `_CLUSTERED_RE`, `artifact_naming.py:157-164`, groups `date/set/nn/id6/slug`) and returns the `slug` group directly. Keep a safe fallback (return `"plan"` or the current heuristic result) only when the name does not match the clustered grammar (e.g. legacy names). This mirrors the already-correct generic path `compute_target_name` (`artifact_rename.py:81-90`) which reads `m_uni.group("slug")`.
  - Depends on: none
  - Expected outcome: for `20260823-ipdgates-06-wezhxg-remove-raw-x.ipd.md`, `_slug_of(...)` returns `remove-raw-x` (not `ipdgates-06-remove-raw-x`); `run_mv --order 07` proposes a target with only the NN facet changed.
  - Execution state: pending

### Task group 2: Regression test

- [ ] E-02 In `tests/test_plans_refs.py`, add a regression test that runs the `run_mv` path (or `_slug_of` directly) on a clustered plan name with `--order <newNN>` and NO `--slug`, and asserts the resulting target name preserves the original slug and changes only the Order facet (no `<setid>-NN-` injected into the slug). Include the exact ipdgates repro shape from the backlog item.
  - Depends on: E-01
  - Expected outcome: the test fails on pre-fix code (mangled slug) and passes after the fix.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw rename plans` routes to `plans_refs.run_mv` (`plans_refs.py:379-418`; registered `artifact_types.py:78`). When `--slug` is omitted, the slug comes from `_slug_of(src.name, id6)` (`plans_refs.py:410`, defined `plans_refs.py:156-165`).
- The canonical naming authority is `agent_workflows/artifact_naming.py` (`_CLUSTERED_RE` at `artifact_naming.py:83-86`, `parse_clustered`/groups at `artifact_naming.py:157-164`). The generic rename path `artifact_rename.compute_target_name` already parses correctly; the plans `run_mv` path is the outlier with the bug.
- Rename tests: `tests/test_plans_refs.py` (the buggy path), plus `tests/test_artifact_rename.py`, `tests/test_naming_authority_golden.py`. Run with `python3 -m pytest tests/test_plans_refs.py`.
- Contributor contract: path-scoped commits only, no push, no em/en dashes in user-facing prose.

## Findings

| ID | Severity | Persona | Finding |
|---|---|---|---|
| F-01 | High | Toolkit user | `_slug_of` (`plans_refs.py:156-165`) strips only leading pure-digit tokens + id6, leaving `<setid>` and `NN` in the derived slug; verified it returns `awrenamebug-01-rename-order-slug-mangle` for this very plan's name instead of `rename-order-slug-mangle`. `run_mv` then embeds the old cluster prefix in the new name. |
| F-02 | Med | Maintainer | The generic `compute_target_name` (`artifact_rename.py:81-90`) parses the slug correctly via the canonical regex; the plans path duplicates a broken heuristic instead of reusing the authority. |

## Proposed changes (ordered, validatable)

1. Rewrite `_slug_of` to parse via the canonical clustered-name regex and return the `slug` group, with a legacy fallback.
2. Add a regression test for `rename --order` alone preserving the slug (ipdgates repro).

## Deferred / out of scope (with reason)

- Folding the plans rename path into the unifyfileio unified rename engine is out of scope; that is a larger refactor tracked by the unifyfileio Set. This IPD fixes the specific defect in place (the backlog item explicitly allows "fix here or fold into that Set"; fixing here is the smaller, release-blocking change).
- No change to `run_mv`'s Order handling (`plans_refs.py:393-399`); only the slug derivation.

## Scope check

- Over-scope: none. Two files only.
- Under-scope: none. Fixing `_slug_of` addresses the documented root cause; the regression test guards it.

## Required tests / validation

- `python3 -m pytest tests/test_plans_refs.py` green, including the new regression test.
- Manual: on a clustered plan, run `aw rename plans <id6> --order <NN>` (no `--slug`) and confirm the dry-run target changes only the Order facet and preserves the slug (no `<setid>-NN-` injected).
- `pre-commit run --files agent_workflows/plans_refs.py tests/test_plans_refs.py`.

## Spec / documentation sync

- No spec change expected; this is a bug fix restoring documented behavior. N/A unless the naming-authority golden fixtures need a new case (add if the golden test enumerates rename cases).

## Open questions

### OQ-01: On a legacy (non-clustered) plan name that does not match `_CLUSTERED_RE`, what slug should `_slug_of` return?

- Blocking: no
- Status: deferred
- Owner: author
- Resolution or deferral rationale: DEFERRED to a safe fallback in E-01: when the name does not match the clustered grammar, keep the pre-existing heuristic result (or `"plan"`) so legacy behavior is unchanged. The bug only manifests for clustered names, which the canonical parser handles; non-blocking.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted dry-run output of `aw rename plans <id6> --order <NN>` (no `--slug`) on a clustered plan showing the target changes only the Order facet and preserves the slug; and/or a snippet showing `_slug_of` now returns the parser's `slug` group.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `python3 -m pytest tests/test_plans_refs.py` output showing the new regression test passing (and, if captured, failing on the pre-fix code).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one small, cohesive concern (fix the plans rename slug derivation) plus its regression guard, confined to one module and its test.

### Execution contract

1. Open questions RESOLVED: OQ-01 is non-blocking and resolved (safe legacy fallback). No blocking open question remains.
2. Scope fence: touch ONLY `agent_workflows/plans_refs.py` and `tests/test_plans_refs.py`. Reuse the canonical `artifact_naming` parser; do NOT introduce a new regex or refactor `run_mv` beyond the slug source. Do NOT touch the unifyfileio engine. If a fix seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests/checks passed, paste the ACTUAL runner output (`python3 -m pytest tests/test_plans_refs.py` and the `aw rename` dry-run); never claim a pass from narration or an unchecked box.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit (via the lifecycle workflow).
