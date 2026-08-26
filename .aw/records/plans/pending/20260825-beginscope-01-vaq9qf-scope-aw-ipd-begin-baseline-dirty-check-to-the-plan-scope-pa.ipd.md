# IPD: Scope aw ipd begin baseline dirty-check to the plan Scope-Paths (honor the approved path-overlap multi-agent rule)

- Date: 2026-08-25
- Kind: child
- Concern: `aw ipd begin` (agent_workflows/ipd_lifecycle.py:460) refuses to issue a receipt whenever the WHOLE worktree is dirty (`get_git_dirty_digest(repo) != "clean"`), forcing every downstream execution to start from a globally-clean tree. This directly contradicts the design that was human-approved for this very gate. The originating IPD `ipdgates-03` (`xjbvu2`, executed 2026-08-24) resolved OQ-01/PR-003 after an explicit human challenge ("why the anchor? won't it thrash my multi-agent workflow?"): the agreed rule is PATH-OVERLAP-scoped, NOT HEAD-identity- or whole-tree-scoped - "this execution's changes" is defined as the diff restricted to the plan's `Scope-Paths`, and the receipt was made to persist across unrelated intervening commits on DISJOINT paths precisely to "preserve the concurrent multi-agent workflow." That path-overlap principle was correctly applied to receipt LIFETIME but was NOT applied to the initial baseline dirty-check, which stayed a blunt whole-tree check. The consequence is the exact multi-agent thrash the resolution promised to avoid: the maintainer routinely runs several agents at once (executing one IPD while `/plan-review`-ing another or editing backlogs), and any unrelated uncommitted work anywhere in the tree now blocks `begin` for an in-scope, otherwise-clean plan. Concrete failure: overnight run `run-20260826T000928Z-1641359` (Set bklggrad) implemented + committed all three children green, but NONE could complete the terminal `begin`/`finalize` transition because pre-existing unrelated dirty files (awrenamebug/INDEX/agentadhere) tripped the whole-tree check, and each turn was correctly forbidden from committing/stashing them. Origin: incident review 2026-08-26.
- Scope: Narrow ONLY the baseline dirty-check in `aw ipd begin` so it refuses on uncommitted changes to paths INSIDE the plan's frozen `Scope-Paths`, and IGNORES uncommitted work on disjoint paths - matching the path-overlap rule the `ipdgates-03` OQ-01/PR-003 resolution already approved. This does not weaken the anti-scope-creep guarantee: `finalize` (`ipdgates-04`/`-05`) still performs the two-way scope reconciliation against the frozen base, so an in-scope collision or an out-of-scope change is still caught there; `begin` merely stops false-positive-refusing on disjoint dirt. Reorder `begin` so the `Scope-Paths` freeze (currently step 5) runs BEFORE the baseline check (currently step 4), because the scoped check needs the frozen paths. Add a scoped dirty helper (a path-filtered variant of `get_git_dirty_digest`, or a new `dirty_within(repo, paths)` in run_evidence.py) that treats staged, unstaged, and untracked entries matching any `Scope-Paths` prefix/pathspec as in-scope-dirty. Keep the unversioned/ambiguous-HEAD refusal unchanged. Update the E-01 contract prose and the fail-closed tests in tests/test_ipd_lifecycle_cli.py that currently assert whole-tree refusal, and add tests proving: (a) disjoint dirt no longer blocks begin, (b) in-scope dirt still refuses, (c) the diagnostic names the offending in-scope path(s). Sync the `ipd-structure` spec Section 11 and the `ipd-lifecycle` workflow doc text that describe the "clean baseline" so they state the path-overlap rule. This is a corrective IPD for a gap in an already-executed plan (`ipdgates-03`), per the AGENTS.md rule that a post-execution gap is closed by a NEW IPD, not an in-place edit of the executed plan.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, agent_workflows/run_evidence.py, tests/, .aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md, .aw/records/specs/
- Status: approved
- Set: beginscope
- Order: 1
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: vaq9qf
- Approval: 2026-08-26, human ("approved"): Human approved execution now as absolute top priority (unblocks concurrent multi-agent workflow); behavior is the already-approved ipdgates-03 OQ-01 path-overlap rule

## Workflow history
- 2026-08-26 approved (opencode its_direct/pt3-claude-opus-4.8-1m-us, --by-human): Human approved execution now as absolute top priority (unblocks concurrent multi-agent workflow); behavior is the already-approved ipdgates-03 OQ-01 path-overlap rule
- 2026-08-26 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): status set to to-review

- 2026-08-25 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Make `aw ipd begin` honor the path-overlap baseline rule that `ipdgates-03` (`xjbvu2`) already approved: refuse on uncommitted changes INSIDE the plan's frozen `Scope-Paths`, ignore disjoint dirt elsewhere. This restores the maintainer's concurrent multi-agent workflow (execute one IPD while others are being reviewed/edited) without weakening the anti-scope-creep guarantee, which `finalize`'s scope reconciliation still enforces against the frozen base.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Scoped baseline dirty-check in aw ipd begin

- [ ] E-01 In agent_workflows/run_evidence.py, add a path-scoped dirty helper (e.g. `dirty_within(repo_dir, scope_paths) -> "clean" | <digest>`) that runs `git status --porcelain` and returns non-clean ONLY when a staged, unstaged, or untracked entry matches any of `scope_paths` (repo-relative prefix / pathspec, matching the same normalization `finalize` uses for its Scope-Paths comparison). Leave the existing whole-tree `get_git_dirty_digest` unchanged (other callers rely on it).
  - Depends on: none
  - Expected outcome: a unit-testable function that reports clean when only disjoint paths are dirty and non-clean (naming the offending path) when an in-scope path is dirty.
  - Execution state: pending

- [ ] E-02 In agent_workflows/ipd_lifecycle.py `begin`, reorder so the `Scope-Paths` freeze (current step 5) runs BEFORE the baseline check (current step 4), then replace the whole-tree `get_git_dirty_digest(repo) != "clean"` refusal (ipd_lifecycle.py:460) with a call to the E-01 scoped helper over the frozen `Scope-Paths`. Keep the unversioned / ambiguous-HEAD refusal unchanged. Make the refusal diagnostic name the specific in-scope dirty path(s) and cite that disjoint work is intentionally allowed. Update the docstring's ordered fail-closed list (ipd_lifecycle.py:380-387).
  - Depends on: E-01
  - Expected outcome: `begin` issues a receipt when only disjoint paths are dirty; still refuses (exit 2) when an in-scope path is dirty or HEAD is ambiguous; the receipt binding is otherwise unchanged.
  - Execution state: pending

- [ ] E-03 Update the `ipd-structure` spec Section 11 and the `ipd-lifecycle` workflow doc text that describe the "clean/unambiguous baseline" so they state the PATH-OVERLAP rule (in-scope dirt refuses; disjoint dirt is allowed to preserve the concurrent multi-agent workflow), consistent with the `ipdgates-03` OQ-01 resolution. Use the managed verbs (`aw specs note`) for the spec.
  - Depends on: E-02
  - Expected outcome: the primary docs no longer claim a globally-clean tree is required; they describe the scoped rule.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `aw ipd begin`/`finalize` are the tooled terminal-transition surface; hand-editing the transition is forbidden (AGENTS.md).
- A post-execution gap in an executed plan is closed by a NEW corrective IPD, never an in-place edit of the executed plan (AGENTS.md; the executed plan is `ipdgates-03` / `xjbvu2`).
- `get_git_dirty_digest` (run_evidence.py:156) is the existing whole-tree porcelain digest; `finalize` already computes this-execution's changed paths restricted to `Scope-Paths` since the frozen base (ipd_lifecycle.py `_changed_paths_since_base` / scope reconciliation), which is the normalization the E-01 helper should mirror.
- User-facing prose avoids em/en dashes; this IPD is an internal artifact where that constraint does not apply.

## Findings

The path-overlap rule is not new policy - it is the ALREADY-APPROVED contract from `ipdgates-03`:

- OQ-01 resolution (executed IPD `20260823-ipdgates-03-xjbvu2-...`, line 99): "The validity rule is PATH-OVERLAP-scoped, not HEAD-identity-scoped ... 'this execution's changes' = the diff restricted to this plan's `Scope-Paths` since base."
- PR-003 / plan-review (same IPD, line 21): resolved by the human after the challenge "won't it thrash my multi-agent workflow?"; the agreed behavior "preserves the concurrent multi-agent workflow" (multiple agents committing on the same branch on DISJOINT file sets).
- The gap: E-01 of that plan (line 34) inlined an unqualified "refusing a dirty ... worktree" clause; the implementation (ipd_lifecycle.py:460) made it a whole-tree check, contradicting the resolution above. `finalize` remained correctly scope-aware, so only `begin`'s baseline check is wrong.
- Incident: `run-20260826T000928Z-1641359` (Set bklggrad) - three children committed green (d9166fe, 596dd9a, 81d9acb) but could not `begin`/`finalize` because unrelated disjoint dirt tripped the whole-tree check. (Those three were subsequently finalized post-hoc by hand-supplied `--scope-ack`s once the tree was made clean; this IPD removes the need for that workaround.)

## Proposed changes (ordered, validatable)

1. `run_evidence.py`: add `dirty_within(repo_dir, scope_paths)` (path-scoped porcelain check). (E-01)
2. `ipd_lifecycle.py::begin`: freeze Scope-Paths first, then call `dirty_within` over the frozen paths in place of the whole-tree refusal; keep unversioned/ambiguous-HEAD refusal; improve the diagnostic; update the docstring. (E-02)
3. Spec Section 11 + `ipd-lifecycle.md`: state the path-overlap baseline rule. (E-03)
4. Tests: rewrite the whole-tree fail-closed assertions to the scoped rule, and add disjoint-allowed / in-scope-refused / diagnostic-names-path cases. (validation)

## Deferred / out of scope (with reason)

- No change to `finalize` or its scope reconciliation - it is already path-scoped and remains the enforcement point for scope creep; touching it would widen blast radius without need.
- No change to `get_git_dirty_digest` itself - other callers (doctor, run evidence) legitimately want the whole-tree digest; the scoped behavior is an additive helper.
- The recurring "driver bundles agent-owned cli.py edits into unrelated commits" anomaly (decisions 03-orb9zb-D2, 04-f1dhht-D2) is a separate runner concern, tracked elsewhere; not in this IPD.

## Scope check

- Over-scope: none.
- Under-scope: none. The four Scope-Paths (`ipd_lifecycle.py`, `run_evidence.py`, `tests/`, the workflow doc, the specs tree) cover the code change, the helper, the tests, and the two doc surfaces; no other module reads the begin baseline check.

## Required tests / validation

`python -m pytest tests/test_ipd_lifecycle_cli.py -p no:randomly` green with the rewritten + new baseline cases; full suite `python -m pytest -p no:randomly` green; `aw ipd lint` on this plan clean; a manual repro proving `aw ipd begin` succeeds on a tree dirtied only on disjoint paths and still refuses on an in-scope dirty path; `aw sanitize --agent` clean.

## Spec / documentation sync

Update `ipd-structure` spec Section 11 (via `aw specs note`) and `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md` to describe the path-overlap baseline rule, replacing any "clean worktree/baseline" wording that implies a globally-clean tree.

## Open questions

### OQ-01: Untracked file matching semantics for in-scope detection

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: An untracked NEW file created under a declared `Scope-Paths` directory (e.g. a new `tests/test_x.py` when `tests/` is in scope) should count as in-scope-dirty at `begin`. Recommended: `dirty_within` treats an untracked entry as in-scope when its path is under any scope directory prefix or matches a scope pathspec, mirroring how `finalize` attributes new files. Confirm this matches `finalize`'s existing changed-path normalization during E-01 so begin and finalize agree; if they diverge, prefer finalize's semantics as the source of truth. Non-blocking: the recommended approach is clear and testable.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a unit test showing `dirty_within` returns "clean" when only a disjoint path is dirty and non-clean (naming the path) when an in-scope path is dirty (staged, unstaged, and untracked-new cases). Paste the runner output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: rewritten/added tests in tests/test_ipd_lifecycle_cli.py proving `begin` (a) issues a receipt when only disjoint paths are dirty, (b) still refuses (exit 2) on an in-scope dirty path with a diagnostic that names it, (c) still refuses on ambiguous/unversioned HEAD; plus a manual `aw ipd begin` repro on a disjoint-dirty tree (receipt written) vs an in-scope-dirty tree (refused). Paste both. Full suite `python -m pytest -p no:randomly` green.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the updated spec Section 11 text and `ipd-lifecycle.md` excerpt showing the path-overlap baseline rule; `aw specs check` / `aw ipd lint` clean; `aw sanitize --agent` clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: touch ONLY the declared `Scope-Paths` plus this plan's own file. This is a corrective IPD for a gap in the executed plan `ipdgates-03` (`xjbvu2`); do NOT edit that executed plan in place. Honesty rule (hard MUST): when reporting tests/validation passed, paste the ACTUAL runner output; never claim success not run. Commit only files this plan changes, path-scoped; never `git add -A`; never push. On completion perform the terminal transition via `aw ipd begin <plan> --actor <agent/model>` then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply` (which, once this IPD lands, will itself only require the tree to be clean within this plan's Scope-Paths); do NOT hand-edit the terminal transition. All target work is human-approved before execution; this plan awaits `/plan-review` and explicit human approval (`Status: approved`) before it may be executed.
