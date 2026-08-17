# IPD: Complete the .aw/ migration retrofit (writer/board/lint verbs, shipped docs, release mechanics)

- Date: 2026-08-17
- Kind: orchestrator
- Concern: The awphysical `.aw/` migration shipped INCOMPLETE. Release-review run 20260817-153418 found (and reproduced) that the reader/index verbs were retrofitted but the writer/board/lint verbs, the shipped/executed workflow bodies, the always-loaded AGENTS.md block, the release mechanics (RELEASING.md + Makefile), and several docstrings/manifests still target the vanished legacy `.agents/` tree. This is a NO-GO for release.
- Scope: Complete the retrofit so a migrated (`.aw/`) repo works end-to-end. Five child Orders (01 record verbs + tests; 02 shipped docs + AGENTS.md generator; 03 release mechanics; 04 install/uninstall + migration-engine safety; 05 help/docstrings/READMEs/manifest/dead-code). OUT: the next version NUMBER (S6-V01) is a maintainer decision recorded here, not an Order action; no push/tag/publish (Section 9 human GO).
- Status: approved
- Set: awretrofit
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: pp6y76
- Approval: 2026-08-17 human maintainer (chat) - approved orchestrator 00 + Order 01 to execute; Orders 02-06 are authored and reviewed/approved individually as they are scaffolded (blanket Set approval to fix everything now, per-Order lint gates retained). Recorded by opencode Opus 4.8.

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-17 authored (opencode Opus 4.8): built from release-review run 20260817-153418 (Set awretrofit).
- 2026-08-17 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. Structural preflight conforming. Child-Order table, dependencies (04->01, 05->01/02), and whole-Set completion criteria verified against the release-review findings; version-number decision correctly deferred to the maintainer (not an Order action). No findings requiring plan edits; OQ-01 resolved (blanket Set approval, per-Order lint gates retained). GO - PENDING HUMAN APPROVAL.

## Goal

Bring the framework to a genuinely GO-able state after the awphysical migration by finishing every
place the retrofit was skipped, so that on a fresh/migrated `.aw/` repo the CLI verbs, the shipped
executed runbooks, the always-loaded agent contract, and the release tooling all operate on the real
`.aw/` layout - verified, tested, and drift-free.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..05 through the IPD lifecycle in dependency order (author -> human approval -> execute -> verify -> transition to executed/), owning verification and path-scoped commits for each, never pushing; record the maintainer's version-number decision (S6-V01) here.
  - Depends on: none
  - Expected outcome: all five child Orders reach `executed`, the whole-Set completion criteria below hold, and the version decision is captured for Section 9.
  - Execution state: pending

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

## Completion criteria (the whole Set is done only when)

- Every Order 01..05 is `executed` with its V-items verified.
- On this repo: `aw plans` lists plans, `aw ipd lint --all` reports real counts, `aw research check-refs`
  is clean, `aw uninstall --deep` (dry-run) targets `.aw/records/`, and no shipped body / AGENTS.md /
  RELEASING.md / Makefile instructs a nonexistent `.agents/` path.
- Full serial suite green (>= baseline 973/1-skip, plus the new regression tests).
- Wheel still ships the nested `.aw/system` bundle + sibling VERSION, no `.agents/` leak, no double-ship.
- `aw attention --check`, `aw plans index --check`, `aw sanitize --agent` clean.
- The maintainer's next-version decision (S6-V01) is recorded (baked in Section 9 after GO).

## Cross-IPD validation

- No two Orders edit the same lines incompatibly (01 = behavior in *.py verb modules; 05 = help/docstring
  strings in the same modules -> execute 01 before 05 and re-lint).
- After all Orders: re-run the release-review reproduction commands and confirm every previously-broken
  verb now behaves correctly (single consolidated check in E-01 verification).

## Deferred / out of scope (with reason)

- The next-version NUMBER (S6-V01): maintainer decision (breaking `.aw/` migration argues 2.0.0; tag
  line tracks 1.3.0-rc). Recorded here; reconciled + baked in Section 9 after an explicit human GO.
- Push / tag / PyPI publish: human-gated (RELEASING.md Section 9); never performed by this Set.

## Scope check

- Over-scope: none - every Order maps to a reproduced release-review finding.
- Under-scope: none - the five Orders cover all in-scope findings from run 20260817-153418; the only
  unaddressed item is the deliberately-deferred version number.

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

- [ ] V-01 validates E-01
  - Required evidence: All five child Orders show `Status: executed` under `.aw/records/plans/executed/`; the whole-Set completion criteria are demonstrated (paste: `aw plans` head, `aw ipd lint --all` counts, `aw research check-refs` clean, full serial suite summary, wheel nested-bundle check, `aw attention --check`/`sanitize --agent`); the maintainer version decision is recorded in this file.
  - Observed evidence:
  - Result: pending

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
