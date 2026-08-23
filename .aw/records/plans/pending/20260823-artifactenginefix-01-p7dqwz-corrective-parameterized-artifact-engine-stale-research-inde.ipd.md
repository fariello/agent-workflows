# IPD: Corrective: stale research index and aw group releases/UX fixes

- Date: 2026-08-23
- Kind: child
- Concern: Three executed plans (autoindex hszr72, grouptypes o2ygf3, renametypes 53yczi) left three SAFE, self-contained post-execution gaps: the research manifest index is stale; aw group carries an untested/undocumented releases route; and aw group --apply prints no success confirmation. (The larger parameterized-engine design-debt is deliberately split into a SEPARATE follow-up IPD - see Deferred - because it is risky internal churn against already-shipped, passing plans/research paths with no user-visible payoff, and must be planned deliberately rather than ride along with these small fixes.)
- Scope: agent_workflows/artifact_types.py, agent_workflows/artifact_rename.py (aw group --apply output only), the research manifest index, CLI --help/docs for the releases group route, and tests/test_artifact_group.py. Does NOT reopen or edit the three executed IPDs, and does NOT refactor the rename/group engine or re-route plans/research.
- Status: reviewed
- Set: artifactenginefix
- Order: 1
- Highest E allocated: 03
- Author: Gabriele Fariello
- Id: p7dqwz

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (OQ-01 resolved by human: keep `aw group releases`, add test+doc); PR-002 (human-decided scope split: deferred the risky parameterized-engine refactor + plans/research unification to a separate follow-up IPD, dropped E-01/E-02/E-03, renumbered the three safe fixes to E-01/E-02/E-03); PR-003 (removed E-02's self-authorizing "split if unsafe" escape hatch by removing that E-item); PR-004 (replaced non-falsifiable "no regex ladder remains" evidence with checkable index/test evidence); PR-005 (tightened E-item wording and validation mapping). Range-shorthand (former E-03) confirmed near-no-op for the free-form types (range cites exist only for plans/research).

## Goal

Close the three SAFE, self-contained post-execution gaps left by the executed sibling plans (`hszr72`, `o2ygf3`, `53yczi`) without editing those executed IPDs: (1) re-seat the stale research manifest index and confirm `aw check all` reports zero `stale-index`; (2) close the untested/undocumented `aw group releases` route by adding a test and documenting it (OQ-01 resolved: keep); and (3) emit a success confirmation line from `aw group --apply` so a set-injection is not silent. The larger parameterized-engine refactor and `plans`/`research` unification the siblings mandated is intentionally NOT in this IPD (see Deferred).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Stale research manifest index

- [ ] E-01 Re-seat the stale research manifest index. On the current tree `aw index research --check` reports `stale-index` on both `INDEX.json` and `INDEX.md` (pre-existing debt, not introduced by the three siblings, but it means the repo is not in the zero-drift state their narrative implies). Run `aw index research` to regenerate, verify the regenerated index is deterministic (re-running produces no diff), and commit the refreshed index path-scoped.
  - Depends on: none
  - Expected outcome: `aw index research --check` is clean and `aw check all` reports zero `stale-index` findings.
  - Execution state: pending

### Task group 2: aw group releases coverage + UX

- [ ] E-02 Close the untested `aw group releases` gap (OQ-01 resolved: KEEP). `releases` was registered as a `group` route in `agent_workflows/artifact_types.py` by the grouptypes commit but has no test and no doc. Add `test_group_releases` to `tests/test_artifact_group.py` covering preview, `--apply`, and `- Set:` injection/update on a `releases` record, and document `releases` as an in-scope `group` type in the relevant CLI `--help`/docs. Do not leave an untested, undocumented route.
  - Depends on: none
  - Expected outcome: `aw group releases` is covered by a passing test and documented as in-scope; no untested route remains.
  - Execution state: pending

- [ ] E-03 Emit a success confirmation line from `aw group <type> --apply`. Today a successful `--apply` that only injects `- Set:` (no rename) prints nothing on the apply path (`agent_workflows/artifact_rename.py:524-539`), while the dry-run path does print `--- would set metadata Set: ... ---`. Print a concrete confirmation on apply (e.g. `set metadata Set: <id> in <path>`) consistent with how `aw rename --apply` reports, and cover it with a test assertion. Do NOT change the group engine's structure beyond adding this output.
  - Depends on: none
  - Expected outcome: `aw group --apply` prints a clear per-artifact confirmation line; a test asserts it.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AGENTS.md agent execution contract: "Do NOT add commits to a plan already in `.aw/records/plans/executed/`; close a post-execution gap with a new corrective IPD, not an in-place edit." This IPD is that corrective instrument for the SAFE gaps found verifying `hszr72`, `o2ygf3`, `53yczi`.
- `aw index research` regenerates the research manifest (`INDEX.json`/`INDEX.md`); `aw index research --check` fails on drift. Re-running the regenerate must be deterministic (no diff on a second run).
- Range-shorthand citations (`<stem>..NN`) exist ONLY for `plans` and `research` (e.g. `20260802-1944-00..06`); the free-form types `aw group`/`aw rename` handle here (backlog, specs, prompts, roadmaps, walkthroughs, releases) carry NO range citations. This is why the "third citation form" work is not needed for these types and why it was moved to the follow-up engine IPD.
- `aw group <type> --apply`'s metadata-only path prints nothing (`agent_workflows/artifact_rename.py:524-539`); the dry-run path prints `--- would set metadata Set: ... ---` (line 511). E-03 aligns the apply path.

## Findings

Verification of the three executed sibling plans (2026-08-23) found five gaps. This IPD addresses the three SAFE ones; the two engine-design gaps are split to a follow-up IPD (see Deferred):
- SAFE (this IPD): `aw check all` reports `stale-index` on the research `INDEX.json`/`INDEX.md` (bisected to pre-date the three siblings at commit 152211e; pre-existing debt, not a regression). -> E-01.
- SAFE (this IPD): `aw group` registered a `releases` route (grouptypes commit) that is outside grouptypes' OQ-02 scope and has no test/doc. -> E-02.
- SAFE (this IPD): `aw group <type> --apply` prints no confirmation on a successful set-injection. -> E-03.
- DEFERRED to follow-up IPD: the mandated parameterized per-type engine was not built (`artifact_rename.py` is a monolithic regex-switch; `plans`/`research` still route to their old `plans_refs`/`research_refs` backends = two parallel implementations).
- DEFERRED to follow-up IPD (and re-evaluate): the generic reference-rewriter does full-name + bare-stem only, not range shorthand - but range shorthand only occurs for plans/research (which the generic engine does not currently handle), so this is likely a no-op and only becomes relevant IF the follow-up IPD re-routes plans/research through the generic engine.
- All three siblings otherwise executed faithfully: named tests exist and pass, `pytest -n auto` is green (2094 passed, 1 skipped), lifecycle moves were path-scoped git renames, and no pushes occurred. This corrective IPD does NOT dispute their executed status.

## Proposed changes (ordered, validatable)

1. Regenerate and re-seat the research manifest index; confirm zero drift (E-01).
2. Add `test_group_releases` and document `releases` as an in-scope group type (E-02).
3. Align `aw group --apply` to print a success confirmation, with a test (E-03).

## Deferred / out of scope (with reason)

- The parameterized per-type engine refactor and `plans`/`research` unification the siblings mandated: DEFERRED to a SEPARATE follow-up IPD (human decision, 2026-08-23 /plan-review). Rationale: it is risky internal churn (Remediation Risk - Functionality: re-routing the most-used, already-shipped, already-tested `plans`/`research` rename/group paths through a new engine) with no user-visible payoff (it is design-contract fidelity, not a bug fix), so it must be planned and reviewed deliberately, not bundled with these small safe fixes. The follow-up IPD must also re-evaluate whether the "third citation form" work is needed at all, since range shorthand only exists for plans/research.
- Editing the three executed IPDs (`hszr72`, `o2ygf3`, `53yczi`): out of scope by the AGENTS.md rule against amending executed plans.
- The `hszr72` silent `except Exception: pass` around auto-index and its duplicated workflow-history line: cosmetic; deferred (low value, no user impact); can be folded into the follow-up engine IPD if it touches that code.

## Scope check

- Over-scope: none. This IPD does not refactor the engine, re-route plans/research, or edit the executed IPDs.
- Under-scope: none. The three E-items fully cover the three SAFE gaps; the engine-design gap is explicitly deferred to a named follow-up IPD rather than silently dropped.

## Required tests / validation

- `aw index research --check` clean and `aw check all` reporting zero `stale-index` (paste actual output) (E-01).
- `tests/test_artifact_group.py` extended with `test_group_releases` (preview + `--apply` + `- Set:` injection) and a `--apply` confirmation-output assertion, all green (E-02, E-03).
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Document `releases` as an in-scope `aw group` type in the relevant CLI `--help`/docs (E-02, OQ-01 resolved: keep).

## Open questions

### OQ-01: Is `aw group releases` intended to be supported?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): KEEP `aw group releases`. `releases` records carry `Id`/`Set`/`Order` frontmatter, so grouping them is semantically meaningful. E-05 therefore adds `test_group_releases` (preview/apply/set-injection) and documents `releases` as in-scope for `group`; it does NOT remove the route.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw index research --check` clean output and `aw check all` showing zero `stale-index`; regenerated index is deterministic on re-run (second `aw index research` produces no diff).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: `test_group_releases` passes (preview + `--apply` + `- Set:` injection on a `releases` record) and `releases` is documented as an in-scope `group` type in CLI `--help`/docs.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a test asserts `aw group <type> --apply` prints a concrete per-artifact confirmation line on the metadata-only (no-rename) path.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: three small, independent, low-risk corrective fixes (research index freshness, `aw group releases` coverage+doc, `aw group --apply` output) left by the sibling Set; the risky engine refactor was deliberately split out.

### Execution contract

1. Open questions RESOLVED: OQ-01 (keep `aw group releases`) resolved by human (2026-08-23).
2. Scope fence: touch ONLY `agent_workflows/artifact_types.py` (if needed for the releases route/doc), the `aw group --apply` output in `agent_workflows/artifact_rename.py` (output only - do NOT refactor the engine or re-route `plans`/`research`), the research manifest index (regenerate via `aw index research`), CLI `--help`/docs for the releases group type, and `tests/test_artifact_group.py`. Do NOT edit the three executed IPDs. Do NOT change manifest index schema/format. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
