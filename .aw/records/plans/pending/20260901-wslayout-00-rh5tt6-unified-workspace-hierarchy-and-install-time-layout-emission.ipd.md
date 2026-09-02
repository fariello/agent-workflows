# IPD: Unified Workspace Hierarchy and Install-Time Layout Emission Orchestrator

- Date: 2026-09-01
- Kind: orchestrator
- Concern: Workspace layout definitions are currently fragmented across 5 Python modules and inaccessible to non-Python tooling. Spec kw5y2s establishes a single-source Python layout model in layout.py and install-time emission of .aw/system/layout.json and schema for non-Python tools.
- Scope: Coordinate execution of the 5-plan child set wslayout implementing Spec kw5y2s across core modeling, internal module consolidation, install-time emission, and CLI surface.
- Scope-Paths: agent_workflows/layout.py, agent_workflows/artifact_types.py, agent_workflows/selectors.py, agent_workflows/record_producers.py, agent_workflows/project_schema.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/check_engine.py, tests/
- Item-Dependencies: none
- Status: reviewed
- Set: wslayout
- Order: 0
- Highest E allocated: 02
- Author: antigravity
- Id: rh5tt6
- From-Spec: kw5y2s

## Workflow history
- 2026-09-02 reviewed (aw set): plan-review round 2 (orchestrator): APPROVE WITH REVISIONS APPLIED; PR-010..PR-014 fixed; spec kw5y2s now approved so the round-1 external gate is cleared

- 2026-09-01 draft (antigravity): created orchestrator.
- 2026-09-01 to-review (antigravity): authored complete orchestrator plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001..PR-008. Author-phase lint conforming for all six plans; every finding is semantic. Review record: .aw/records/reviews/20260901-wslayout-00-rh5tt6-unified-workspace-hierarchy-and-install-time-layout-emission.review.md
- 2026-09-01 /plan-review question loop (maintainer): OQ-1 and OQ-2 asked interactively and ANSWERED, so neither remains blocking. OQ-1 = UNION vocabulary (keep `roadmaps`, add `reviews`/`backlog`/`other`). OQ-2 = emitted layout files GITIGNORED via the framework-owned `.aw/.gitignore`. Verdict unchanged (the remaining findings still require a replan).
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all eight findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review ROUND 2 at HEAD `12159af5`, scoped to the ORCHESTRATOR: APPROVE WITH REVISIONS APPLIED; PR-010..PR-014 all FIXED. THE ROUND-1 BLOCKER IS CLEARED: spec `kw5y2s` is now `approved` `--by-human`, so `ipd-lifecycle.md:16` is satisfied and readiness moves NO-GO -> GO - PENDING HUMAN APPROVAL. Round 1's fixes were VERIFIED against the children rather than trusted (dependencies reconciled, union vocabulary pinned, the two missing test files now created by their owners, `test_setup_repo_cli.py` dropped), and the union claim was re-measured against live code (10 + 9 -> 12 = eleven classes plus the `records` carve-out; exclusions exactly seven). PR-010 HIGH: the orchestrator had NO execution contract; added ten clauses including a scope fence, the honesty rule, path-scoped commits, and the expected-`tk1gqo`-diagnostic note, plus the two MEASURED live scope collisions (`e32j35` on `selectors.py`, `6knsrx` on `engine.py`) with per-child re-measurement required. PR-011 HIGH: both V-items were unfalsifiable one-liners; V-01 now demands per-child executed-path, status, lint and NON-EMPTY child evidence, and V-02 demands the end-to-end install/gitignore/read/absent proof that no child owns. PR-012 MEDIUM: completion criteria still asserted `aw setup-repo` bakes files, contradicting round 1's own PR-003 fix. PR-013 MEDIUM: cross-IPD validation was four vague bullets, now five falsifiable cross-cutting assertions with measured baselines. PR-014 LOW: prose-bullet Findings converted to the evidence table the template expects. Status to-review -> reviewed. Review record round 2 appended.

## Goal

Coordinate the implementation of Spec kw5y2s across 5 child plans, ensuring zero regression to existing Python callers and deterministic emission of .aw/system/layout.json during install.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Child Set Execution & Integration

- [ ] E-01 Track and coordinate execution of child plans wpu5zu (Order 01), zvk796 (Order 02), rodj06 (Order 03), hauwqh (Order 04), and 30jug9 (Order 05).
  - Depends on: none
  - Expected outcome: All 5 child plans executed, verified, and finalized into executed/.
  - Execution state: pending
  - SERIAL, IN TABLE ORDER, and gated on the predecessor reaching `executed`: 02, 03 and 04 each import `layout.py` and declare `executed:wpu5zu`; 05 declares `executed:hauwqh`. The metadata was reconciled with the table at round 1 (PR-007), so do not re-derive the sequence from prose.
  - BEFORE EACH CHILD, re-measure concurrent scope collisions per execution-contract item 4. This is a per-child action, not a one-time Set-start check, because the colliding work (`e32j35` on `selectors.py`, `6knsrx` on `engine.py`) may land mid-Set.
  - Coordination only: this item performs NO product edit and writes no code.

### Task group 2: End-to-End Release Gate & Conformance

- [ ] E-02 Execute repository-wide test suite and leak sanitization across all integrated layout changes.
  - Depends on: E-01
  - Expected outcome: Full pytest test suite passes bare, aw check passes, aw sanitize passes clean.
  - Execution state: pending
  - AND PERFORM THE END-TO-END BEHAVIORAL PROOF, which is the part no child owns: in a temporary target repo, run a real install, confirm both layout files were emitted, confirm both are gitignored through the framework-owned `.aw/.gitignore` with the root `.gitignore` untouched, confirm the layout surface reads the emitted file, and confirm it degrades gracefully when the file is absent (the fresh-clone case the GITIGNORED ruling creates).
  - Also run the cross-IPD vocabulary-parity assertion (see Cross-IPD validation): the combined result of Orders 02 and 03 is the shipping state, and no single child observes it.
  - Run the suite BARE, `python3 -m pytest`, from the PRIMARY checkout. Do not add `-n0`, a second `-q`, or `-p no:randomly`; `pyproject.toml` `addopts` already supplies the intended flags.

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Set dependencies |
|---:|---|---|---|
| 01 | `wpu5zu` | Core Layout Model and JSON Schema in layout.py | approved spec |
| 02 | `zvk796` | Consolidate artifact_types.py and selectors.py into layout model | 01 |
| 03 | `rodj06` | Consolidate record_producers.py and project_schema.py into layout model | 01 |
| 04 | `hauwqh` | Install-time layout.json and schema emission in engine.py | 01 |
| 05 | `30jug9` | Add aw layout CLI command and workspace health check rule | 04 |

## Completion criteria (the whole Set is done only when)

- `agent_workflows/layout.py` exists as the single source of truth for workspace layout definitions, carrying the UNION vocabulary (eleven record classes plus the `records` root carve-out) per the maintainer ruling.
- `artifact_types.py`, `record_producers.py`, `selectors.py`, and `project_schema.py` re-export from `layout.py` with backward compatibility PROVEN, not asserted: every public name each module exported before still exists with an identical value, and the bare full suite passes.
- `engine.install()` bakes `.aw/system/layout.json` and `.aw/system/layout.schema.json` during installation, as the SOLE emission site. CORRECTED at round 1 (PR-003) and restated here because the original wording survives in other sections: `aw setup-repo` is NOT a CLI verb, it is an agent slash-command backed by a workflow body, and it inherits emission transitively from `aw install` with no code of its own.
- Both emitted files are GITIGNORED via the framework-owned `.aw/.gitignore`, with the user's root `.gitignore` untouched.
- The layout surface (`aw layout` or whatever `30jug9` OQ-01 settles on) and `aw check` verify layout presence and validity, and both behave correctly when the file is ABSENT (the fresh-clone case).
- All 5 child plans are finalized in `executed/` with every `V-*` carrying non-empty pasted evidence.
- Full pytest suite passes bare, `aw sanitize` is clean, and no NEW `aw check` diagnostic class appeared (the six pre-existing `check.lifecycle-transition-invalid` reports are expected; backlog `tk1gqo`).

## Cross-IPD validation

These are the checks NO single child can perform, which is the orchestrator's reason to exist.

- THE VOCABULARY DID NOT NARROW END TO END. After all children, assert the model's `record_classes` is still a superset of both live source vocabularies. Measured at round 2 as the baseline to beat: `ARTIFACT_TYPES` has 10 members (`backlog, comms, other, plans, prompts, releases, research, roadmaps, specs, walkthroughs`), `RecordClass` has 9 (`comms, plans, prompts, records, releases, research, reviews, specs, walkthroughs`), whose union is 12 names, which is the eleven modeled classes PLUS the `records` root carve-out held separately. `roadmaps` must still be present and `aw rename roadmaps` / `aw group roadmaps` must still work.
- THE EMITTED FILE MATCHES THE MODEL. Compare the schema `layout.py` generates against the emitted `.aw/system/layout.json`, in a temporary repo, after a real install.
- BACKWARD COMPATIBILITY ACROSS THE WHOLE SUITE, not per child. Each consolidating child validates its own two files plus the bare suite; only here is the COMBINED result of Orders 02 and 03 observed, which is the state that actually ships.
- THE NET-NEW CLI BEHAVIOR WORKS. `aw check reviews` errors today (measured at round 2: `outcome: error, exit 2, target: reviews`). If the union vocabulary makes `reviews` a CLI noun, that command must succeed after the Set, and `aw check roadmaps` must not have regressed. Assert both.
- THE FRESH-CLONE CASE. Because emission is gitignored, a fresh clone has no `layout.json` until an install runs. Assert every reader tolerates its absence rather than crashing, and that `aw check` reports the absence as the distinguished non-failing state the spec's ruling requires.

## Project conventions discovered (Step 0)

- `agent_workflows/`: Core framework modules.
- `Spec kw5y2s`: Unified Workspace Hierarchy Specification and Machine-Readable Install-Time Layout Emission, now `approved` (F-2).
- A lifecycle transition is a POST-gate step performed with `aw ipd finalize`, never an E-item (`ipd-lifecycle` workflow).
- Execution against an unapproved controlling spec is forbidden (`ipd-lifecycle.md:16`); that gate is now satisfied.
- `.aw/.gitignore` is the FRAMEWORK-OWNED ignore file and already carries this convention for other generated paths; the user's root `.gitignore` is never touched (`.aw/.gitignore:1-15`).
- `engine.install()` is the sole install entry point in Python; `/aw setup-repo` is an agent slash-command backed by a workflow body with no Python call site, and `aw install` RECOMMENDS it as a follow-up (`engine.py:3581-3597`). There is no `aw update` verb.
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies the intended flags.

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **The decomposition is sound and survived two review rounds.** Pure new code first (Order 01), isolated refactor of legacy modules second (02 and 03), install emission third (04), user-facing surface last (05). Round 1's own REPLAN call was withdrawn on exactly this basis: the sequence was never the problem. | Round 1 review record, D-6. |
| F-2 | **The external spec gate that made round 1 NO-GO IS NOW CLEARED.** Controlling spec `kw5y2s` is `- Status: approved`, approved `--by-human` with the maintainer's verbatim attestation, and it carries both maintainer rulings. `ipd-lifecycle.md:16`'s precondition is therefore satisfied and readiness turns on ordinary plan approval alone. | `.aw/records/specs/20260901-kw5y2s-01-kw5y2s-...spec.md:4` and its workflow history; commit `6db54f8b`. |
| F-3 | **Round 1's fixes are REAL, verified by re-reading the children rather than trusting the record.** `Item-Dependencies` now match the sequence table on all five children (`zvk796`/`rodj06`/`hauwqh` -> `executed:wpu5zu`, `30jug9` -> `executed:hauwqh`); `wpu5zu` E-01 carries the union vocabulary with the `records` carve-out and pinned exclusions; `rodj06` E-02 and `hauwqh` E-03 now CREATE the previously-missing test files; `tests/test_setup_repo_cli.py` is gone from scope. | `grep` of `- Item-Dependencies:` across the Set; `wpu5zu:39-59`; `rodj06:60,107-109`; `hauwqh:71-76,109-112`. |
| F-4 | **The union vocabulary claim CHECKS OUT against live code.** Measured: `ARTIFACT_TYPES` = 10 members, `RecordClass` = 9, union = 12 names, which is exactly the eleven modeled record classes plus `records` held separately as the empty-subpath carve-out (`_RECORD_CLASS_SUBPATHS[RecordClass.RECORDS] == ""`). `EXCLUDED_RECORD_DIRS` is exactly the seven the plans pin. The aliases include `roadmap -> roadmaps` and `misc`/`others -> other` as `wpu5zu` E-01 requires. | Live import at HEAD `12159af5`; `record_producers.py:136`; `artifact_types.py:12-39`; `selectors.EXCLUDED_RECORD_DIRS`. |
| F-5 | **Two premises the Set relies on are still true at round 2, so its work is not already done.** `aw layout` does not exist (invalid choice), and `aw check reviews` still errors (`outcome: error, exit 2`), which is the net-new behavior `30jug9` owns. | `python3 -m agent_workflows layout`; `aw check reviews --agent`. |
| F-6 | **PR-009's tooling defect is unresolved and will fire during execution.** `check.lifecycle-transition-invalid` still reports on all six wslayout plans and on 3 unrelated ones (9 repo-wide), and backlog `tk1gqo` is still `open`. The executor must expect it and must NOT "fix" it by reordering histories. | `aw check plans --agent` at round 2; `.aw/records/backlog/open/20260901-historder-01-tk1gqo-...backlog.md:2`. |
| F-7 | **REVIEW FINDING (round 2): the orchestrator had NO execution contract at all**, while its own children and comparable orchestrators in this repo carry one (compare `3m0urk`'s eight-clause contract). Added, including the scope fence, the honesty rule, path-scoped commits, and the lifecycle-transition-is-not-an-E-item rule. | Round 2 diff of this file; `3m0urk` gate section. |
| F-9 | **REVIEW FINDING (round 2, ADVISORY, not fixed here): the five CHILDREN are still `Status: to-review`, and the sole stated reason has expired.** Round 1's D-4 deliberately held them there because "`ipd-lifecycle.md:16` gates execution on approval of controlling spec `kw5y2s`, which remains `draft`". That spec is now `approved` (F-2), so the rationale no longer holds, yet the children still read `to-review` while this orchestrator reads `reviewed`. Round 2's ledger was the ORCHESTRATOR only, so advancing five plans this round did not re-review would overstate the review performed; they are left as-is deliberately. RECOMMENDED NEXT STEP: either re-run `/plan-review` over the five children (which would also let their two `open` executor questions be re-confirmed), or advance them on round 1's recorded authority with `aw ipd set reviewed`, before seeking approval. Until then the Set's own plans disagree about their pipeline position. | Round 1 record D-4; `grep '^- Status:'` across the Set at round 2; spec status at `...kw5y2s...spec.md:4`. |
| F-8 | **REVIEW FINDING (round 2): live concurrent scope collisions on two of the Set's modules.** APPROVED plan `e32j35` (Set `findidx`) declares `agent_workflows/selectors.py`, which `zvk796` rewrites; REVIEWED plan `6knsrx` declares `agent_workflows/engine.py`, which `hauwqh` edits and which lands a stack of unmerged lane branches. Across pending plans `cli.py` is declared by 13 and `engine.py` by 3. | Measured `grep -l` over `.aw/records/plans/pending/*.ipd.md` with each plan's `- Status:`. |

## Proposed changes (ordered, validatable)

1. Execute Plan 01 (wpu5zu): Core Layout Model & JSON Schema in layout.py.
2. Execute Plan 02 (zvk796): Consolidate artifact_types.py and selectors.py.
3. Execute Plan 03 (rodj06): Consolidate record_producers.py and project_schema.py.
4. Execute Plan 04 (hauwqh): Install-time layout.json and schema emission in engine.py.
5. Execute Plan 05 (30jug9): Add aw layout CLI command and workspace health check rule.
6. Verify orchestrator end-to-end integration (E-02).

## Deferred / out of scope (with reason)

- Out of scope: changing on-disk layout paths of existing records (spec maintains exact path compatibility).

## Scope check

- Over-scope: none. This orchestrator's `Scope-Paths` is the UNION of what the children edit; the orchestrator's own commits touch only this plan file. Recorded so the breadth is understood as delegation, not as an intent to edit nine modules from here.
- Under-scope: none in this plan. Note the children own two test files that DO NOT EXIST yet and must be CREATED, not edited (round 1 PR-002, verified still absent at round 2): `tests/test_record_producers.py` (created by `rodj06` E-02) and `tests/test_engine_install.py` (created by `hauwqh` E-03). `tests/test_layout.py` is likewise new (`wpu5zu` E-02). `tests/test_setup_repo_cli.py` was correctly DROPPED from scope, since no such CLI surface exists.
- Concurrent-scope collision, recorded rather than resolved (PR-010): `agent_workflows/selectors.py` is also declared by APPROVED plan `e32j35`, and `agent_workflows/engine.py` by REVIEWED plan `6knsrx`. See execution-contract item 4; the mitigation is re-measurement immediately before each child, not a change to this plan's scope.

## Required tests / validation

- Every child's own validation suite passing, with actual pasted output per child.
- Bare full repository `python3 -m pytest` from the PRIMARY checkout, baseline re-measured on unmodified HEAD at execution time (round 1 observed `4004 passed, 3 skipped, 4 xfailed`; treat that as historical, not as the target).
- `aw check --agent` showing no NEW diagnostic class versus the pre-execution baseline; the six `check.lifecycle-transition-invalid` reports are expected (backlog `tk1gqo`).
- `aw sanitize --agent` passing clean.
- The end-to-end install-and-read proof described in V-02, performed in a temporary target repo, which is the only evidence that the Set's actual purpose was achieved.

## Spec / documentation sync

- Aligned with spec `kw5y2s`, which is now `approved` (F-2). Its factual defects were corrected in place during round 1 (vocabulary tables, traversal exclusions, the non-existent `aw setup-repo`/`aw update` verbs) and the two maintainer rulings are encoded in its Sections 2.3, 3.2 and 3.2.1. Do NOT edit the spec further during execution: it is approved, and a plan-time edit to an approved spec would invalidate the attestation.
- If execution discovers a further factual defect in the spec, do not silently diverge and do not edit it: record the discrepancy and report it, since only the maintainer may re-approve.
- No user-facing documentation is named by this orchestrator. The user-visible surface (`aw layout` or its chosen alternative) is `30jug9`'s, and its own plan owns any docs and completion wiring that surface needs.

## Open questions

### OQ-01: What is the true unified record-class vocabulary?

- Blocking: no
- Status: resolved
- Finding: PR-001
- Resolution or deferral rationale: RESOLVED 2026-09-01 by the maintainer, asked interactively: the
  vocabulary is the UNION. Keep every type that exists today, INCLUDING `roadmaps`, and ADD the missing
  ones (`reviews`, `backlog`, `other`) where a module lacks them. The model DOCUMENTS reality rather
  than redefining it, so the consolidation deletes nothing and breaks nothing.
  WHY THE QUESTION EXISTED: draft spec `kw5y2s:59-73` presented a `record_classes` table as the single
  source of truth, but it matched NEITHER existing vocabulary. Measured at HEAD: `ARTIFACT_TYPES`
  (`agent_workflows/artifact_types.py:12-23`) contains `roadmaps`, which the spec omitted; `RecordClass`
  (`agent_workflows/record_producers.py:85-101`) contains `records` (empty subpath, `:136`), which the
  spec omitted; the spec added `reviews` (not an accepted CLI noun: `aw check reviews` errored) and
  `backlog`/`other` (absent from `RecordClass`). `roadmaps` is live in 12 modules with working verbs
  `run_rename_roadmaps`/`run_group_roadmaps` (`agent_workflows/artifact_rename.py:827-828,855-856`) and
  5 artifacts on disk, so deriving from the spec's list would have deleted a shipped CLI surface.
  WHERE IT IS NOW ENCODED: spec Section 3.2 (eleven classes with per-row provenance) and Section 3.2.1
  (the `records` empty-subpath carve-out); `wpu5zu` E-01/E-02 and V-01; `zvk796` E-01 and V-01;
  `rodj06` E-01 and V-01; `30jug9` E-03 and V-03.
  CONSEQUENCES CARRIED: `roadmaps` must survive every derivation; `records` needs an explicit carve-out
  rather than an ordinary subpath entry; and `reviews` becoming a CLI noun is net-new behavior that
  `aw check reviews` must now accept, tested rather than assumed.

### OQ-02: Is the emitted `.aw/system/layout.json` git-tracked or gitignored?

- Blocking: no
- Status: resolved
- Finding: PR-004
- Resolution or deferral rationale: RESOLVED 2026-09-01 by the maintainer, asked interactively:
  GITIGNORED, via a `.gitignore` INSIDE the `.aw/` directory (the framework-owned file), never the
  user's root `.gitignore`.
  WHY THE QUESTION EXISTED: the spec's own rationale for install-time emission is to eliminate git drift
  (`kw5y2s:40-43`), yet the plans never stated trackedness, and the two in-repo precedents point in
  OPPOSITE directions. `.aw/system/` is tracked here (156 files) and the sibling generated marker
  `.aw/system/VERSION` is tracked, while one day earlier the maintainer decided the analogous case the
  other way in backlog `ila6vl` (stop tracking the generated INDEX manifests, 328 commits in 14 days).
  Guessing would have either recreated that churn or contradicted the spec's stated purpose.
  WHY THE CHOSEN MECHANISM IS NOT NEW: `.aw/.gitignore` already exists and already carries this exact
  convention for four other generated or box-local paths, and its header states it "lives inside the
  framework-owned `.aw/` tree; it is NOT the user's root `.gitignore`" (`.aw/.gitignore:1-15`).
  WHERE IT IS NOW ENCODED: spec Section 2.3 (the ruling, its reasoning, and the consequence) and the
  updated Sections 6.1/7/8; `hauwqh` E-02 (add `system/layout.json` and `system/layout.schema.json`,
  idempotently) with V-02 requiring `git check-ignore -v` evidence and proof the root `.gitignore` is
  untouched; `30jug9` E-01 (the command must work with no emitted file) and E-02 (the presence/drift
  rule is the loud-failure backstop).
  CONSEQUENCE CARRIED: a fresh clone has NO layout.json until an install runs, so every non-Python
  reader must tolerate absence, CI reading it needs an install step first, and git will never show a
  diff for a stale emitted file, which is precisely why the `aw check` rule became required rather than
  optional.

### OQ-03: Which install entry point receives the emission wiring?

- Blocking: no
- Status: resolved
- Finding: PR-003
- Resolution or deferral rationale: RESOLVED 2026-09-01 (measured from the repository, then the spelling
  corrected by the maintainer): `engine.install()`, reached by `aw install`, is the SOLE emission site.
  The draft spec and two plans named `aw setup-repo` and `aw update` as install entry points; neither is
  a CLI verb. The correct spelling is `/aw setup-repo` (alias `/setup-repo`), an AGENT SLASH-COMMAND
  backed by a workflow BODY (`.aw/system/workflows/setup-repo/setup-repo.md`, shim
  `.opencode/commands/setup-repo.md`; see `.aw/system/workflows/index.md:108,121`), so it has no Python
  call site into which file emission could be wired.
  THE RELATIONSHIP IS THE REVERSE OF THE PLANS' ASSUMPTION: `aw install` runs FIRST and then RECOMMENDS
  `/setup-repo` as a follow-up conformance pass (`agent_workflows/engine.py:3581-3597`, "NEXT STEP ...
  run /setup-repo"). `/aw setup-repo` therefore inherits emission transitively at zero cost, and no
  emission code belongs in the workflow body. There is likewise no `aw update` verb; `aw install` is
  idempotent and is itself the update path.
  WHERE IT IS NOW ENCODED: spec Section 6.1 (rewritten, with the four install-time steps and an explicit
  paragraph on why the slash-command needs no code) plus Sections 7.1 and 8.2; `hauwqh` E-01 (sole
  emission site) with V-01 requiring evidence that the workflow body is untouched, `Scope` and
  `Scope-Paths` corrected, and `tests/test_setup_repo_cli.py` dropped from scope because there is no
  such CLI surface to test.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste, for EACH of the five children (`wpu5zu`, `zvk796`, `rodj06`, `hauwqh`, `30jug9`), its resolved path under `.aw/records/plans/executed/`, its `- Status: executed` line, and the `aw ipd lint --phase pre-transition --agent` result showing `conforming`. Then paste a per-child confirmation that every one of its `V-*` items carries NON-EMPTY observed evidence and `Result: pass`, because a child can be moved to `executed/` with blank evidence and this is the orchestrator's only chance to catch that. Also paste the resolved `Item-Dependencies` of each child alongside the sequence table, proving metadata and table still agree at completion time (they were reconciled at round 1; a later edit could desync them).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the COMPLETE bare `python3 -m pytest` summary line run from the PRIMARY checkout, with the baseline RE-MEASURED on unmodified HEAD at execution time and any delta explained change-by-change (do not reuse round 1's `4004 passed, 3 skipped, 4 xfailed`, which predates later commits). Paste `aw check --agent` output for the artifact types this Set touches and confirm no NEW diagnostic class appeared; the six pre-existing `check.lifecycle-transition-invalid` diagnostics are EXPECTED and are not a regression (backlog `tk1gqo`). Paste `aw sanitize --agent` showing `outcome: clean`. Finally paste the END-TO-END behavioral proof this Set exists for, which no child owns alone: in a temporary target repo, run an install, show `.aw/system/layout.json` and `.aw/system/layout.schema.json` were emitted, show `git check-ignore -v` reports both ignored via the framework-owned `.aw/.gitignore` with the root `.gitignore` untouched, show `aw layout` (or whatever surface `30jug9` OQ-01 settled on) reads it, and show the same command degrades gracefully when the file is absent.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THE EXTERNAL SPEC GATE IS NOW CLEARED (round 2, 2026-09-01). Round 1 reported readiness NO-GO solely because controlling spec `kw5y2s` was `draft` and `ipd-lifecycle.md:16` forbids executing against an unapproved spec. Measured at round 2: that spec is now `- Status: approved` (`.aw/records/specs/20260901-kw5y2s-01-kw5y2s-unified-workspace-hierarchy-spec-and-install-time-layout-emi.spec.md:4`), approved `--by-human` with the maintainer's verbatim attestation recorded in its workflow history, and it carries both maintainer rulings (UNION vocabulary, GITIGNORED emission). The remaining gate is ordinary human approval of these six plans.

Execution contract:

1. Human approval of the plans is required. There are no unresolved BLOCKING questions: this orchestrator's three open questions are all `Status: resolved`, and the two remaining `open` questions (`zvk796` OQ-01 traversal exclusions, `30jug9` OQ-01 CLI naming) are non-blocking, assigned to the EXECUTOR, each with a stated safe default and a V-item that FAILS if the choice is made without being recorded.
2. Execute children SERIALLY in the table order. The metadata now matches the table (`Item-Dependencies` written at round 1), so a scheduler and a human read the same sequence. Do not start Order 02, 03, or 04 before `wpu5zu` is `executed`, because they import `layout.py`.
3. The orchestrator itself authors NO product code and touches only its own file. Product changes, tests, and commits belong to the children.
4. RE-MEASURE CONCURRENT SCOPE COLLISIONS IMMEDIATELY BEFORE EACH CHILD, not once at Set start (round 2, PR-010). Measured at round 2 across pending plans: `cli.py` is declared by 13, `engine.py` by 3, `selectors.py`/`artifact_types.py`/`record_producers.py` by 3 each, `check_engine.py`/`project_schema.py` by 2 each. Two specific live conflicts: APPROVED plan `e32j35` (Set `findidx`) declares `agent_workflows/selectors.py`, which `zvk796` rewrites; and REVIEWED plan `6knsrx` (Set `wtisoland`) declares `agent_workflows/engine.py`, which `hauwqh` edits, and is itself the lander for a stack of unmerged lane branches. A child editing those files while such work is in flight is writing into a file about to receive a large merge.
5. Validation requires ACTUAL pasted commands, exit codes, and file contents. A clean structural lint is not evidence of behavior, and this Set has already been bitten by that: round 1 found the orchestrator's open-question section had never been PARSED by the linter (prose bullets instead of `### OQ-NN:` headings), so an earlier "lint conforming" was a false negative on that section.
6. Commit only files the executing plan changed, path-scoped. Other agents and runs are ACTIVE in this shared checkout, so before every commit verify the staged set with `git diff --cached --name-only` and `git restore --staged` anything not yours. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
7. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
8. Scope fence (a DECLARATION so the runner can reconcile afterwards): this orchestrator's declared Scope-Paths are the union the children edit; the orchestrator's OWN commits touch only this plan file. An out-of-scope edit is permitted but must be JUSTIFIED with a per-path `aw ipd finalize --scope-reason`, and a declared-but-unmodified path needs a `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a file you must edit is being changed concurrently and the two sets of changes cannot be safely combined (this is the item-4 case).
9. `check.lifecycle-transition-invalid` fires on all six of these plans and is a KNOWN TOOLING DEFECT, not a plan defect (round 1 PR-009, filed as backlog `tk1gqo`, still `open` and still firing on 9 plans repo-wide including approved ones). Do NOT "fix" it by reordering these histories to newest-first: that would contradict the oldest-first convention every other plan follows. Expect the diagnostic and leave it alone.
10. After all children and both orchestrator E/V items pass, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`. The lifecycle transition is a POST-gate step, never an E-item.
