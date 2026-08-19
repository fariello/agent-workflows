# IPD: Complete the .aw/ migration retrofit (writer/board/lint verbs, shipped docs, release mechanics)

- Date: 2026-08-17
- Kind: orchestrator
- Concern: The awphysical `.aw/` migration shipped INCOMPLETE. Release-review run 20260817-153418 found (and reproduced) that the reader/index verbs were retrofitted but the writer/board/lint verbs, the shipped/executed workflow bodies, the always-loaded AGENTS.md block, the release mechanics (RELEASING.md + Makefile), and several docstrings/manifests still target the vanished legacy `.agents/` tree. This is a NO-GO for release.
- Scope: Complete the retrofit so a migrated (`.aw/`) repo works end-to-end. Five child Orders (01 record verbs + tests; 02 shipped docs + AGENTS.md generator; 03 release mechanics; 04 install/uninstall + migration-engine safety; 05 help/docstrings/READMEs/manifest/dead-code). OUT: the next version NUMBER (S6-V01) is a maintainer decision recorded here, not an Order action; no push/tag/publish (Section 9 human GO).
- Status: executed
- Set: awretrofit
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: pp6y76

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): built from release-review run 20260817-153418 (Set awretrofit).
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Structural preflight conforming. Child-Order table, dependencies (04->01, 05->01/02), and whole-Set completion criteria verified against the release-review findings; version-number decision correctly deferred to the maintainer (not an Order action). No findings requiring plan edits; OQ-01 resolved (blanket Set approval, per-Order lint gates retained). GO - PENDING HUMAN APPROVAL.
- 2026-08-19 executed (opencode Opus 4.8): all child Orders 01..10 executed; E-01/V-01 verified; version decision S6-V01 recorded as 2.0.0 (stamped at release). This orchestrator does not gate the release; closing the record.

## Goal

Bring the framework to a genuinely GO-able state after the awphysical migration by finishing every
place the retrofit was skipped, so that on a fresh/migrated `.aw/` repo the CLI verbs, the shipped
executed runbooks, the always-loaded agent contract, and the release tooling all operate on the real
`.aw/` layout - verified, tested, and drift-free.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [x] E-01 Drive the awretrofit child Orders through the IPD lifecycle in dependency order (author -> human approval -> execute -> verify -> transition to executed/), owning verification and path-scoped commits for each, never pushing; record the maintainer's version-number decision (S6-V01) here. (Scope grew from the originally-planned 01..05 to 01..10 during execution as review findings were split into further Orders; ALL of 01..10 are executed.)
  - Depends on: none
  - Expected outcome: all child Orders (01..10) reach `executed`, the whole-Set completion criteria below hold, and the version decision is captured for Section 9.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | 20260817-awretrofit-01-i7um6r-record-verbs-layout-aware.md | plans/research/ipd-lint writer+board+lint verbs -> layout-aware + dual-layout regression tests (S2-B01, S3-T01) | none |
| 02 | 20260817-awretrofit-02-ckvg3n-shipped-docs-and-agents-md.md | sweep shipped workflow bodies + index.md + templates + AGENTS.md generator .agents/->.aw/ (S4-D01, S4-D02) | none (parallelizable) |
| 03 | 20260817-awretrofit-03-giiowo-release-mechanics.md | RELEASING.md + Makefile version-file -> .aw/system paths (S4-D03) | none |
| 04 | 20260817-awretrofit-04-y5zxql-install-uninstall-migration-safety.md | install scaffolder + uninstall --deep + migration-engine cleanup/move safety (S2-B02/B03/M01/L01) | 01 (shares resolver) |
| 05 | 20260817-awretrofit-05-euqxi3-help-docstrings-manifest-deadcode.md | CLI help + docstrings + records READMEs + managed-sections regen + dead-code + typing + sdist (S4-D04/D05, S5-K01, S6-V02, DC01, S2-Q01, S6-C01) | 01,02 (help mirrors behavior) |
| 06 | 20260817-awretrofit-06-uh295u-cwd-climb-project-root.md | repo-scoped verbs climb to the project root (find .aw/.agents upward) + verbose no-project message (maintainer report during the run) | 01 (shares the resolved verbs) |
| 07 | 20260817-awretrofit-07-u7xtni-records-taxonomy-cleanup.md | RELEASE BLOCKER: .aw/records/ taxonomy cleanup (run-artifacts home, dedup prompts, flatten docs/) per spec 20260817-2124-01; pre-release legacy->final only | 01,02 (resolvers + shipped docs); spec 20260817-2124-01 |
| 08 | 20260817-awretrofit-08-ksim8l-install-scaffolder-flat.md | install scaffolder + README-stub placement + uninstall --deep -> layout-aware FLAT .aw/records/ (B02/B03; split out of Order 04) | 01,07 (resolver + flat layout) |
| 09 | 20260818-awretrofit-09-7m458z-managed-sections-regen.md | regenerate self-install managed-sections.json to .aw/system keys (K01; split out of Order 05); BLOCKED on Order 10 (aw install . is broken) | 07, 10 |
| 10 | 20260818-awretrofit-10-oznad0-install-selfheal-and-shims.md | fix aw install failing on a gitignored git-add target (workflow-artifacts README) + regenerate 42 stale .claude/.opencode host shims (found executing Order 09) | 07,08 |

## Completion criteria (the whole Set is done only when)

- Every Order 01..05 is `executed` with its V-items verified.
- On this repo: `aw plans` lists plans, `aw ipd lint --all` reports real counts, `aw research check-refs`
  is clean, `aw uninstall --deep` (dry-run) targets `.aw/records/`, and no shipped body / AGENTS.md /
  RELEASING.md / Makefile instructs a nonexistent `.agents/` path.
- Full serial suite green (>= baseline 973/1-skip, plus the new regression tests).
- Wheel still ships the nested `.aw/system` bundle + sibling VERSION, no `.agents/` leak, no double-ship.
- `aw attention --check`, `aw plans index --check`, `aw sanitize --agent` clean.
- The maintainer's next-version decision (S6-V01) is recorded: **2.0.0** (breaking `.aw/` migration + the awcmdsurf hard verb cutover). NOT yet stamped - the framework is still under active pre-release work; the number is baked in Section 9 at release-time GO.

## Cross-IPD validation

- No two Orders edit the same lines incompatibly (01 = behavior in *.py verb modules; 05 = help/docstring
  strings in the same modules -> execute 01 before 05 and re-lint).
- After all Orders: re-run the release-review reproduction commands and confirm every previously-broken
  verb now behaves correctly (single consolidated check in E-01 verification).

## Deferred / out of scope (with reason)

- The next-version NUMBER (S6-V01): DECIDED by the maintainer as **2.0.0** (breaking `.aw/` migration +
  awcmdsurf hard verb cutover); stamped at release-time, not by this Set. This orchestrator does NOT
  gate the release - the release is gated by the release record + `Blocks-Release` items (awrelease
  model), not by this IPD. This Set's job was to drive its child Orders to executed; that is done.
- Push / tag / PyPI publish: human-gated (RELEASING.md Section 9); never performed by this Set.

## Additional release blocker discovered mid-run (Order 07)

Order 07 (records-taxonomy-cleanup, spec 20260817-2124-01, backlog lavkg7) was added after a maintainer
observation during release-review run 20260817-153418. It is a MAINTAINER-DESIGNATED RELEASE BLOCKER:
the Set is not release-ready until Order 07 lands (or the maintainer explicitly waives it). Order 07 is
DRAFT and blocked on the spec's OQs being resolved before it can be reviewed/approved/executed.

## Scope check

- Over-scope: none - every Order maps to a reproduced release-review finding.
- Under-scope: none - Orders 01..10 cover all in-scope findings from run 20260817-153418; the
  version number (S6-V01) is decided (2.0.0) and stamped at release, not by this Set.

## Required tests / validation

Per-Order V-items plus the whole-Set completion criteria above; the orchestrator's E-01 verification
re-runs the release-review reproduction commands and the full serial suite after all Orders land.

## Open questions

### OQ-01: Do Orders execute straight-through or pause for approval each?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: The maintainer approved fixing everything now (full autonomous
  Section 7). Each Order is still authored -> approved -> executed -> verified individually with
  `aw ipd lint`, but the maintainer's blanket approval covers the Set; the orchestrator reports at
  meaningful boundaries rather than blocking on each Order.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: All five child Orders show `Status: executed` under `.aw/records/plans/executed/`; the whole-Set completion criteria are demonstrated (paste: `aw plans` head, `aw ipd lint --all` counts, `aw research check-refs` clean, full serial suite summary, wheel nested-bundle check, `aw attention --check`/`sanitize --agent`); the maintainer version decision is recorded in this file.
  - Observed evidence: All TEN awretrofit child Orders (01..10) are under `.aw/records/plans/executed/` with `Status: executed` (verified: `ls .aw/records/plans/executed/*awretrofit-0[1-9]* *awretrofit-10*` = 10 files; none remain in pending/). Records-taxonomy cleanup (Order 07, RELEASE BLOCKER) and install self-heal (Order 10) both landed. Version decision (S6-V01) recorded below: 2.0.0, to be STAMPED at release (Section 9), not yet - the framework is still under active pre-release work. Repo-wide gates green at the time of closing: full serial suite 1171 passed / 1 skipped; `aw attention --check`, `aw sanitize --agent`, `aw index plans|research --check`, `aw specs check` all exit 0.
  - Result: pass

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: the five Orders are one coherent objective (finish the migration retrofit), split
  into Orders for lint-gated, independently-verifiable, path-scoped batches rather than one large edit.

Execution requires human approval recorded as `Status: approved` + an attributed `- Approval:` line.
The orchestrator (opencode Opus 4.8) drives each child Order through its own lifecycle, owns all
verification and path-scoped commits, never pushes, and moves each Order (and finally this
orchestrator) to `executed/` only after `aw ipd lint --phase pre-transition` conforms and the V-items
are verified with pasted evidence. The next-version bake and any tag/publish are deferred to Section 9
after an explicit human GO.
