# IPD: Unified selector-to-file resolver

- Date: 2026-08-23
- Kind: child
- Concern: There are three independent selector-to-file resolvers plus a path-only outlier, so the SAME `<selector>` (a path, id6, setid, status, bare stem, or filename substring) can resolve under one `aw` verb and fail (or resolve differently) under another. `selectors.resolve_one` matches id6/status/setid/substring but NOT a direct path or an exact stem; `artifact_rename.find_target_record` wraps `resolve_one` and adds path + exact-stem; `status_set.match_selector` reimplements path/id6/setid/substring with EXACT id6/setid and no status; `aw backlog set` accepts a literal path ONLY. This is the "one unified way to FIND files" gap.
- Scope: Create ONE selector resolver and route every verb through it. Touch: agent_workflows/selectors.py (`resolve_one`, `resolve_selectors`, `record_dirs`), agent_workflows/artifact_rename.py (`find_target_record` -> thin shim), agent_workflows/status_set.py (`match_selector` -> thin shim), agent_workflows/backlog.py (`run_set` path-only branch -> use the resolver), and the per-area id6-only finders (`plans_refs._find_plan_by_id`, `research_refs._find_by_id6`, `plans_archive._find_targets`) which should delegate to the unified resolver's id6/setid path. Also the CLI call sites (`cli.py:4979,5211,5262,5304`). Depends on the Order 01 naming authority for stem/name parsing.
- Status: draft
- Set: unifyfileio
- Order: 2
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: laykok

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.

## Goal

Provide a single selector-resolution function that maps a selector to artifact file(s) using ONE well-defined, documented precedence over the FULL selector vocabulary - direct path, id6, setid, status, bare stem (via the Order 01 grammar authority), and filename substring - and route every verb (`rename`, `group`, `set`/`ipd set`/`spec set`/`backlog set`, `show`, `find`, `archive`, and the per-area set-assign/mv paths) through it. After this child, `aw <verb> <type> <selector>` accepts the same selector kinds and resolves to the same file for every verb, or reports a uniform, clear "no match / ambiguous match" error; a selector kind a specific verb intentionally rejects is rejected uniformly and documented, never a silent divergence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Characterize current resolver behavior (safety net)

- [ ] E-01 Author `tests/test_selector_resolver_matrix.py` pinning the CURRENT behavior of all three resolvers before unification: a matrix of {resolver} x {selector kind: path, id6, setid, status, exact-stem, substring} asserting exactly which kinds each resolver resolves, fails, or over-matches today (documenting the known gaps: `resolve_one` has no path/exact-stem; `match_selector` has no status/stem; `backlog set` is path-only). This baseline defines what "unified" must converge to and prevents silent behavior loss.
  - Depends on: none
  - Expected outcome: a green matrix documenting current per-resolver capabilities and gaps. (Set-level: this whole IPD executes only after Order 01 is executed.)
  - Execution state: pending

### Task group 2: Build the unified resolver

- [ ] E-02 Implement one `resolve(repo_root, artifact_type, selector, *, allow=...) -> Resolution` in `selectors.py` (the canonical home) with a single documented precedence: (1) direct path (absolute or repo-relative existing file); (2) exact id6 (`artifact_core.ID6_RE`); (3) exact setid (`- Set:` first token); (4) status token; (5) exact bare stem (parsed via the Order 01 naming authority); (6) filename substring. Return a structured result distinguishing no-match, unique-match, and ambiguous-match (multiple hits), so callers can render a uniform error. Support an `allow`/`deny` set so a verb can intentionally restrict which selector kinds it accepts - but that restriction is declared, not accidental.
  - Depends on: E-01
  - Expected outcome: one resolver covering the full vocabulary with explicit ambiguity handling and declarable per-verb restrictions.
  - Execution state: pending

### Task group 3: Route every verb through it

- [ ] E-03 Re-route callers to the unified resolver: `artifact_rename.find_target_record` becomes a thin shim (path/id6/setid/status/stem/substring via `resolve`); `status_set.match_selector` becomes a thin shim (declaring any kinds `set` intentionally restricts); `backlog.run_set` uses `resolve` instead of requiring a literal path (closing the outlier); the per-area id6 finders (`plans_refs._find_plan_by_id`, `research_refs._find_by_id6`, `plans_archive._find_targets`) delegate to `resolve`'s id6/setid path. Preserve each verb's current SUCCESSFUL resolutions exactly (the matrix E-01 pins this); only ADD the previously-missing kinds and make errors uniform.
  - Depends on: E-02
  - Expected outcome: every verb resolves selectors through the one resolver; no verb loses a resolution it had; `backlog set` now accepts id6/setid.
  - Execution state: pending

### Task group 4: Prove parity

- [ ] E-04 Add `tests/test_selector_resolver_parity.py` asserting the SAME `<selector>` of each kind resolves to the SAME file across `rename`, `group`, `set`, `show`, `find`, and `archive` in one fixture repo; assert a genuinely ambiguous selector produces the SAME uniform ambiguous-match error from every verb; and confirm `pytest -n auto` is green.
  - Depends on: E-03
  - Expected outcome: cross-verb selector parity is proven and regression-guarded.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `selectors.resolve_one` (`selectors.py:91`) fallback chain: id6 (`:98`) -> status (`:104`) -> setid (`:109`) -> filename substring (`:114`); no direct-path branch, bare-stem only via substring. `record_dirs` (`selectors.py:21`) enumerates search dirs.
- `artifact_rename.find_target_record` (`artifact_rename.py:57`): direct path (`:64-69`) -> `resolve_one` (`:72`) -> extra scan matching `selector in f.name` OR `selector == f.stem` (`:83`). The most complete resolver today; consumers `run_rename_generic` (`:343`), `run_group_generic` (`:479`).
- `status_set.match_selector` (`status_set.py:241`): direct path (`:259-271`) -> exact id6 (`:274`) -> exact setid (`:280`) -> substring (`:285`); no status, no stem. Consumer `run_set_command` (`:675`).
- Per-area id6-only finders: `plans_refs._find_plan_by_id` (`plans_refs.py:72`), `research_refs._find_by_id6` (`research_refs.py:145`), `plans_archive._find_targets` (id6 OR setid, `plans_archive.py:77-90`).
- `backlog.run_set` (`backlog.py:381-393`) requires a literal existing path - no id6/setid/substring resolution at all (the outlier).
- Call-site counts: `resolve_one` used at `artifact_rename.py:72` (+ self at `selectors.py:125`); `resolve_selectors` at `cli.py:4979,5211,5262,5304`; `find_target_record` at `artifact_rename.py:343,479`; `match_selector` at `status_set.py:675`.

## Findings

The three resolvers overlap but disagree on which selector kinds they accept, so operator muscle memory breaks between verbs: `aw group backlog <id6>` works (via `find_target_record`) while `aw backlog set <id6> ...` fails (path-only). `aw set <stem>` fails (no stem) while `aw rename <stem>` works. Unifying resolution removes this whole class of "works for one verb, not another" surprises and gives one place to fix resolution bugs.

## Proposed changes (ordered, validatable)

1. Pin current per-resolver capability matrix (E-01).
2. Build one `resolve` with a documented precedence and structured no/unique/ambiguous result (E-02).
3. Re-route `find_target_record`, `match_selector`, `backlog.run_set`, and the id6 finders to it (E-03).
4. Prove cross-verb parity and uniform ambiguity errors (E-04).

## Deferred / out of scope (with reason)

- Changing the naming grammar or the reference matcher: separate children (Orders 01, 03).
- Adding selector support to `comms` (no `TYPE_BACKENDS` verbs): out of scope; note only.

## Scope check

- Over-scope: none. Only selector resolution is unified.
- Under-scope: none. All three resolvers, the path-only backlog outlier, and the per-area id6 finders are routed through the one resolver.

## Required tests / validation

- Capability matrix `tests/test_selector_resolver_matrix.py` (E-01).
- Cross-verb parity `tests/test_selector_resolver_parity.py` (E-04).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Document the canonical selector precedence in the `resolve` docstring and in the CLI `--help` where selectors are described. Update any spec that describes selector resolution, else N/A with reason.

## Open questions

### OQ-01: When a selector matches multiple files (ambiguous), should every verb error, or should read-only verbs (`show`, `find`) list all matches while mutating verbs (`rename`, `group`, `set`) refuse?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). A single ambiguity policy is simplest (all verbs refuse ambiguous with a uniform message), but read-only verbs listing all matches is friendlier. The executor MUST get a human decision before E-02 finalizes the `Resolution` contract, since it defines the resolver's return shape.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the matrix test enumerates all three resolvers x six selector kinds and passes against the pre-refactor code, documenting each gap.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a unit test exercises `resolve` directly for every selector kind including a deliberately ambiguous one, asserting the documented precedence and the no/unique/ambiguous result shape.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: every prior successful resolution in the E-01 matrix still succeeds through the shims; `aw backlog set <id6>` now resolves (regression + new-capability shown by test).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `tests/test_selector_resolver_parity.py` passes (same selector -> same file across rename/group/set/show/find/archive; uniform ambiguous error) and `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - unify selector-to-file resolution - staged safely (matrix -> build -> re-route -> parity).

### Execution contract

1. Open questions RESOLVED: OQ-01 (ambiguity policy) MUST be resolved by a human before E-02 finalizes the resolver return contract.
2. Scope fence: unify ONLY selector resolution and route the listed callers through it. Do NOT change the grammar (Order 01) or the reference matcher (Order 03), and do NOT remove a resolution any verb has today. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
