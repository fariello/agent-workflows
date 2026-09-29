# IPD: Make every mutating artifact verb accept the one universal selector

- Date: 2026-09-29
- Kind: orchestrator
- Concern: THE PLANS TREE'S MUTATING VERBS DO NOT SPEAK THE SELECTOR VOCABULARY THE REST OF THE TOOLKIT SPEAKS, AND THE MOST NATURAL FIX FOR THAT OPENS A CROSS-TYPE WRITE, so the two must be sequenced rather than shipped independently. Measured in this lane: `aw rename plans <a filename>` and `aw group plans <a filename>` both exit 2 with `no plan has Id '<filename>'` while `aw find plans <the same filename>` exits 0 and prints the path; `aw archive plans <a filename>` is worse still, printing a `✓ CLEAN` success banner at exit 0 having archived nothing. Against that, `aw rename specs <a PLAN path> --apply` exits 0 and RENAMES THE PLAN, because `selectors.resolve`'s first precedence rule matches an existing file regardless of the type requested and the generic rename engine applies no type check. So the plans backends are too NARROW and the generic one is too WIDE, and closing the first by routing plans onto the shared resolver would inherit the second: measured, `resolve_for_mutation(repo,'plans',<a spec path>)` returns that SPEC with no error.
- Scope: Orchestrate four children that together make the plans tree's mutating verbs accept the same selectors every reader already accepts, while making a resolved path type-safe for every mutating verb first. This plan holds ORCHESTRATION ONLY: every deliverable belongs to a child (`eby93o` the containment guard, `87m438` the plans `rename`/`group` routing, `1x4tdo` the `archive plans` matcher and its exit status, `3qxuw1` the derived rename hint), and this file contributes no code, no test, and no record of its own. EXCLUDES, in every child without exception: changing `selectors.resolve`'s read-side precedence, merging the plans rename engine into the generic one, and deciding which records tree owns a `.roadmap.md`.
- Scope-Paths: .aw/records/plans/pending/20260929-awrenamesel-00-95jk4s-make-every-mutating-artifact-verb-accept-the-one-universal-s.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Work-Kind: bug
- Priority: medium
- From-Backlog: gyv9tf
- Blocks-Release: next
- Set: awrenamesel
- Order: 0
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 95jk4s

## Workflow history
- 2026-09-29 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): plan-review: APPROVE WITH REVISIONS APPLIED; PR-501 (MEDIUM), PR-502 (MEDIUM), PR-503 (MEDIUM), PR-504 (LOW), all FIXED. All ten findings reproduced; IPD-S407 conforms with no repair loop. Cross-plan findings fixed in owning child eby93o.

- 2026-09-29 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501 (MEDIUM), PR-502 (MEDIUM), PR-503 (MEDIUM), PR-504 (LOW), all FIXED. Findings recorded in `.aw/records/reviews/20260929-awrenamesel-00-95jk4s-make-every-mutating-artifact-verb-accept-the-one-universal-s.review.md`. EVERY ONE OF THIS PLAN'S TEN FINDINGS WAS INDEPENDENTLY REPRODUCED and every one holds, including the load-bearing F-03 sequencing measurement (`resolve_for_mutation(repo,'plans',<a spec path>)` returns the SPEC with `err=None`) and the F-04 cross-type rename (a real `cli.main` run in a throwaway repo renamed the plan at exit 0). `aw ipd lint` conforms at `author` and `review-finalize`, so `IPD-S407`'s orchestrator child-row check passes with no repair loop needed, and the coverage premise holds by inspection: all four deliverables are owned by children (5+6+5+4 E-items) and this file carries only confirmation rows. THE THREE SUBSTANTIVE FINDINGS ALL WIDEN OR SCOPE THE SET RATHER THAN FAULTING ITS DESIGN: the cross-type rename is reachable through SIX type verbs rather than the one demonstrated, all through a single shared call site, so one guard still suffices but Order 01 must prove it for all six (PR-501); a confinement precedent already exists in `research_archive` that chose the OPPOSITE shape to Order 01's "refuse, never silently drop" for a legitimate reason, and neither plan cited it, so Order 01 must reconcile rather than appear to overrule a shipped sibling (PR-502); and completion criterion 2 was an unrestricted universal over "every mutating verb" that the Set does not deliver, since only three production call sites route through the guarded resolver (PR-503). Cross-plan findings were fixed in the OWNING child (`eby93o` gains F-13/F-14 and obligations on E-03, E-05, V-03, V-05) and cross-referenced here per the plan-review cross-plan rule.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `gyv9tf` as a Set rather than one plan, because authoring measured that the item's one-line request cannot be implemented safely on its own. THE SEQUENCING IS THE REASON THIS ORCHESTRATOR EXISTS: `87m438` implements the item's literal ask by routing the plans backends onto `selectors.resolve_for_mutation`, and that resolver returns a SPEC when asked for a `plans` artifact and given a spec path, so shipping it first would import a cross-type write into the one backend currently immune to it (its id-directed scan cannot leave `plans_dir`). `eby93o` therefore goes first and `87m438` declares `executed:eby93o`. THE ITEM ALSO UNDER-REPORTS AND MIS-DIAGNOSES: it names `rename` but not `group` (identical defect, same module), does not know about `archive plans` (a silent no-op at exit 0, plus a terse setid that fails for 77 setids covering 136 plans), and asserts "the roadmaps type has no rename route of its own" when it has one that works. Each correction is recorded in the child that owns it rather than here. The four children were sized so each is one focused pass with its own failing-first evidence.

## Goal

Make a selector that resolves for a reader resolve identically for a mutating verb, without letting the widened vocabulary reach outside the type the operator named.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the children

- [ ] E-01 CONFIRM eby93o REACHED executed
  - Depends on: none
  - Expected outcome: `eby93o` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 01 adds the containment guard to `selectors.resolve_for_mutation`, so a resolved path outside the requested type's own `record_dirs` is refused. It MUST be first, and this is measured rather than stylistic: Order 02 routes the plans backends onto that same resolver, and `resolve_for_mutation(repo,'plans',<a spec path>)` returns the SPEC with no error, so running Order 02 first would make `aw rename plans <a spec path>` rename a spec. Order 03 depends on it for the same reason.

- [ ] E-02 CONFIRM 87m438 REACHED executed
  - Depends on: E-01
  - Expected outcome: `87m438` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 02 is the backlog item's literal subject: it routes `plans_refs.run_mv` and `plans_refs.plan_set_assign` through the shared resolver so `rename`/`group` accept a filename, stem, path and setid. It declares `executed:eby93o` in its own front matter. Its second half is the one an executor is most likely to miss: the target's id6 must be re-read from the resolved file, because the current code reuses the selector string in the filename's `<id6>` slot.

- [ ] E-03 CONFIRM 1x4tdo REACHED executed
  - Depends on: E-01
  - Expected outcome: `1x4tdo` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 03 fixes the third private matcher, `plans_archive._find_targets`: it accepts the shared vocabulary, compares a setid against the TERSE token instead of the raw `- Set:` line, and makes an explicit target that matched nothing refuse instead of printing a success banner. It declares `executed:eby93o` for path type-safety. It is INDEPENDENT of Order 02 (different module, different function) and may run before or after it.

- [ ] E-04 CONFIRM 3qxuw1 REACHED executed
  - Depends on: none
  - Expected outcome: `3qxuw1` reads `- Status: executed` on disk.
  - Execution state: pending
  Order 04 makes `check_engine._identity_rename_hint` derive its type noun from where the record lives, so the remediation command it prints for a roadmap resolves in either tree. It is INDEPENDENT of all three siblings: it changes a suggested string, touches no resolver, and is correct in any order. Sequenced last because its population is currently zero, so it is the lowest-urgency member.

## Child IPDs, sequence, and dependencies

| Order | Id | Title | Depends on | Why this order |
|---|---|---|---|---|
| 01 | `eby93o` | Confine a path selector to the requested type tree so a mutating verb cannot rename a foreign artifact | none | Must precede 02 and 03: both route a backend onto `resolve_for_mutation`, which today hands back a foreign-type file for a path selector. |
| 02 | `87m438` | Route the plans rename and group backends through the shared selector resolver | `executed:eby93o` | The backlog item's own defect. Needs 01 or it imports a cross-type write into the only immune backend. |
| 03 | `1x4tdo` | Give the archive plans matcher the shared selector vocabulary and make an unmatched target refuse | `executed:eby93o` | Third private matcher, separate module; independent of 02. Also changes an exit status, which a reviewer may want to judge alone. |
| 04 | `3qxuw1` | Derive the rename hint type from where the record lives so the suggested command resolves | none | Independent of all siblings; latent (population zero today), so lowest urgency. |

THE ONLY REQUIRED EDGE IS `eby93o` BEFORE `87m438` AND `1x4tdo`. Orders 02, 03 and 04 are mutually independent and may execute in parallel lanes once 01 has executed. They touch DISJOINT production files by deliberate choice (`selectors.py`, `plans_refs.py`, `plans_archive.py`, `check_engine.py`) and disjoint test files, so no two children contend for a path.

## Completion criteria (the whole Set is done only when)

1. A selector that resolves for a READER resolves identically for the plans tree's MUTATING verbs: `aw rename plans`, `aw group plans` and `aw archive plans` each accept a filename, a filename stem, a repo-relative path, an id6 and a terse setid, with the id6 form still working.
2. No mutating verb THAT ROUTES THROUGH `selectors.resolve_for_mutation` acts on an artifact outside the type the operator named. Concretely: each of the SIX types whose rename reaches `artifact_rename.run_rename_generic` (`specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps`, `releases`) refuses a foreign-type path, and so do the plans backends once Orders 02 and 03 route them there. SCOPED AT REVIEW (F-13): the earlier wording was an unrestricted universal over every mutating verb, which Order 01 does not deliver, because a backend with its own private matcher never reaches the guard. `research` already refuses a path by DENYING `MATCH_PATH` before containment is consulted (F-12), so it is out of the guard's reach by a different and pre-existing mechanism, not by this Set's work.
3. A rename driven by a NON-id6 selector writes a filename whose `<id6>` segment is the record's DECLARED `- Id:`, never the selector string. This is the correctness half that a resolver-only fix would silently break.
4. An EXPLICIT archive target that matched nothing archivable exits NONZERO, while a bare sweep with nothing due still exits 0.
5. A terse setid addresses its Set regardless of whether the record's `- Set:` value carries a descriptive parenthetical, so the 77 setids measured unaddressable today become addressable.
6. Every remediation command the identity checker prints RESOLVES when run, for a record in either tree, or it prints no command at all.
7. `python3 -m pytest` is green, with the baseline re-derived by each child at execution rather than taken from this plan.

## Cross-IPD validation

- ORDER MATTERS AND IS DECLARED, ONCE: `87m438` and `1x4tdo` each declare `executed:eby93o`, because the resolver they route onto hands back a foreign-type file for a path selector (F-03). `3qxuw1` declares no dependency and is genuinely independent, so it may execute in any position and may be approved alone.
- THE SEQUENCING IS PINNED FROM THE CHILDREN'S SIDE, not only by this table. `87m438` E-06(e) and `1x4tdo` E-05(e) each assert that a foreign-type path is REFUSED through their newly routed backend, which can only pass with Order 01 in the tree. So a violated ordering surfaces as a failing child test rather than as a date comparison nobody runs.
- NO CHILD MAY CHANGE `selectors.resolve`'s READ-SIDE PRECEDENCE. This is the Set's one standing exclusion and it is repeated in all four children. Order 01 changes only the MUTATION wrapper; a child that finds the read side genuinely wrong should report it, not fix it here.
- NO CHILD MAY TOUCH `status_set.py`. Its `Type mismatch` refusal guards a different surface, is pinned by its own test, and carries an explicit do-not-delete rationale. Order 01 adds a second guard alongside it and must not be read as replacing it.
- ORDER 01's GUARD COVERS SIX TYPE VERBS, NOT ONE, AND MUST BE SHOWN TO (F-11, added at review). All six reach `resolve_for_mutation` through the single `artifact_rename.run_rename_generic` call site, so the guard closes all six at once and no child gains a deliverable; Order 01's E-05/V-05 now require the six-type refusal matrix rather than the one `specs` case. TWO TYPES DO NOT REACH IT and must not be miscredited to it: `research` refuses a path earlier by DENYING `MATCH_PATH`, and `plans` refuses only because its private matcher cannot resolve a path until Order 02 routes it.
- ORDER 01 MUST RECONCILE WITH `research_archive`'s CONFINEMENT PRECEDENT rather than appear to overrule it (F-12, added at review). That helper DROPS out-of-tree paths and refuses only when all were dropped, the opposite of Order 01's "refuse, never silently drop"; both are correct because one filters a possible multi-match and the other rejects a single named foreign path. Order 01's E-03 now carries that distinction as a required comment, and is forbidden from adopting the sibling's deny-`MATCH_PATH` shape, which would refuse the legitimate same-type path selectors this Set exists to enable.

### Set-level findings (carried from authoring)

- F-A THE SET EXISTS BECAUSE THE ITEM'S ONE-LINE REQUEST CANNOT BE IMPLEMENTED ALONE. Routing the plans backends onto the shared resolver is the fix the item asks for, and that resolver is measurably too wide (F-03, F-04), so the guard must precede it. A single plan would hide that ordering inside one checklist where neither a reviewer nor a runner could enforce it.
- F-B THE ITEM UNDER-REPORTS THE SURFACE BY MORE THAN HALF. It names `rename` only; `group` carries the identical defect in the same module, and `archive plans` carries two worse ones that are SILENT (F-05, F-06). Each correction is recorded in the child that owns it, with its own measurement, rather than asserted here.
- F-C THE ITEM'S ROADMAPS DIAGNOSIS IS WRONG AND ITS WORKAROUND IS BROKEN (F-07), so Order 04 carries a corrected diagnosis rather than the item's text. It is also LATENT (population zero today), which is why it is `Priority: low` while its siblings are `medium`.

### Conventions this Set was authored against

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN. Every row in this plan's checklist is a child confirmation; the reasoning lives on the continuation lines. The runner RETIRES a parent once every child is `executed` and deliberately SKIPS the pre-transition E/V checkpoint, so a step parked here would be marked complete having never run (AGENTS.md).
- THE ORCHESTRATOR COVERAGE GATE asks a model whether a parent carries work no child covers and refuses a run unattended when it does. This parent was authored to pass it by construction: each of the four deliverables is owned by exactly one child and named in the table above.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Project conventions discovered (Step 0)

- An orchestrator carries orchestration and NOT work of its own. This plan's four `E-*` items are child-confirmation rows only; it contributes no code, no test and no record, so the runner's orchestrator coverage gate should pass it by construction (AGENTS.md).
- Retirement SKIPS the pre-transition E/V checkpoint, on the premise that a parent's own items are performed by nobody. That premise is TRUE here by construction, which is why no deliverable was parked on this file (AGENTS.md).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'` (AGENTS.md).
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`; verify the staged set, since this checkout is shared (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE BACKLOG ITEM'S DEFECT RE-REPRODUCES AT THIS HEAD, for `rename` and also for `group`, which the item does not mention. | `aw rename plans 20260808-0004-06-migrate-existing-plans.ipd.md --to-id6` -> `error: no plan has Id '<filename>'`, EXIT 2; `aw group plans <the same filename> --set zz` -> the identical message, EXIT 2; `aw rename plans 7qx7ys --to-id6` -> EXIT 0. |
| F-02 | THE READ SIDE ALREADY ACCEPTS WHAT THE MUTATING SIDE REFUSES, which is what makes this an inconsistency rather than a policy. | `aw find plans 20260808-0004-06-migrate-existing-plans.ipd.md --paths` -> EXIT 0 and the path. Measured resolver kinds for `plans`, all five REPRODUCED at review: filename and stem -> `substring`, repo-relative path -> `path`, id6 -> `id6`, `findtier` -> `setid` (**4** plans at review, 3 when authored; a live count that drifts and is context only). |
| F-03 | THE SEQUENCING IS FORCED BY MEASUREMENT, WHICH IS THIS ORCHESTRATOR'S REASON TO EXIST: the shared resolver returns a SPEC when asked for a `plans` artifact and handed a spec path, while the current plans scan cannot leave `plans_dir`. | `selectors.resolve_for_mutation(repo,'plans','.aw/records/specs/implemented/20260817-2147-01-uniform-artifact-naming-grammar.spec.md')` -> `err=None`, one path, the SPEC. `plans_refs._find_plan_by_id` iterates `plans_dir.rglob("*.md")` only. |
| F-04 | THE GENERIC ENGINE ALREADY PERFORMS A CROSS-TYPE RENAME TODAY, independently of anything this Set changes, which is why Order 01 is a fix and not merely a precaution. **WIDENED AT REVIEW: it is SIX types, not one, and the two that refuse do so for TWO DIFFERENT reasons, one of which is a precedent Order 01 must reconcile with (see F-11, F-12).** | Throwaway git repo: `cli.main(["--no-interactive","rename","specs",<a plan path>,"--slug","zzz","--apply","--dir",d])` -> EXIT 0, `renamed .aw/records/plans/pending/20260929-demo-01-ab12cd-a-demo-plan.ipd.md -> ...-zzz.ipd.md`; the original path no longer existed. RE-MEASURED AT REVIEW across all eight renameable types, each against the SAME plan path in a fresh throwaway repo: `specs`, `prompts`, `backlog`, `walkthroughs`, `roadmaps` and `releases` each EXIT 0 and RENAME THE PLAN; `research` EXITs 2 with `this verb does not accept a path selector`; `plans` EXITs 2 with `no plan has Id '<path>'`. |
| F-11 | REVIEW FINDING (PR-501), RECORDED HERE BECAUSE IT WIDENS THIS SET'S JUSTIFICATION RATHER THAN ITS SCOPE: the cross-type rename is reachable through SIX type verbs, not the one `specs` case F-04 demonstrates. Order 01's guard sits in `selectors.resolve_for_mutation`, which `artifact_rename.run_rename_generic` calls for ALL of them through one site, so ONE guard closes all six and no child gains work. What changes is the STAKES and the blast radius Order 01's own E-05 sweep must cover. | Re-measured at review, per F-04's evidence row. The single shared call site is `artifact_rename.run_rename_generic`'s `selectors.resolve_for_mutation(repo_root, artifact_type, selector, force=...)`, so the six types are one code path taking `artifact_type` as a parameter. |
| F-12 | REVIEW FINDING (PR-502): A CONFINEMENT PRECEDENT ALREADY EXISTS IN THIS CODEBASE AND NEITHER THIS PLAN NOR ORDER 01 CITES IT, AND IT CHOSE THE OPPOSITE OF ORDER 01's PRESCRIBED SHAPE. `research_archive._resolve_research_for_mutation` solves the same problem (confine a resolved set to one type's tree) by DENYING `MATCH_PATH` up front and then DROPPING out-of-root paths, refusing only when every path was dropped. Order 01's E-03 mandates "REFUSE, NEVER SILENTLY DROP" and does not mention that a sibling does the opposite for a legitimate reason (it accepts a setid multi-match, where dropping non-members is correct). Order 01 must reconcile with it rather than appear to contradict it; recorded here so the reconciliation is not lost, and carried onto Order 01 in its own findings. | `agent_workflows/research_archive.py` `_resolve_research_for_mutation` passes `deny=frozenset({selectors.MATCH_PATH})` then iterates `for p in paths:` skipping any failing `p.resolve().relative_to(rroot_resolved)`, and returns `selector '<s>' matched no research files within the research root` only `if paths and not confined`. Its docstring attributes the design to IPD `me227c` E-04. The `research` EXIT 2 in F-04 comes from the DENY, not from any containment check. |
| F-13 | REVIEW FINDING (PR-503): COMPLETION CRITERION 2 AS ORIGINALLY WORDED CLAIMED MORE THAN THE SET DELIVERS. It read "No mutating verb acts on an artifact outside the type the operator named", an unrestricted universal over every mutating verb. Order 01 guards `resolve_for_mutation`, so it covers exactly the verbs that ROUTE through it, and measured there are only THREE production call sites (`artifact_rename.run_rename_generic`, `research_archive`, and `selectors.resolve_one`'s shim). Verbs that do NOT route through it, notably `aw group` for the non-plans types and every backend with its own private matcher, are unaffected, and the plans backends only become covered because Order 02 and Order 03 route them there. The criterion is now scoped to what the Set proves. | `grep -n 'resolve_for_mutation' agent_workflows/*.py` returns the definition plus exactly two production callers (`artifact_rename.py`, `research_archive.py`) and two comment mentions in `cli.py`. |
| F-05 | A THIRD PRIVATE MATCHER EXISTS THAT THE ITEM DOES NOT KNOW ABOUT, and its failures are SILENT, which is worse than a refusal. | `aw archive plans <a filename>` -> `✓ CLEAN  no terminal-root plan or Set matches '<filename>'`, EXIT 0, nothing archived, while `aw archive plans 7qx7ys` archives that same plan. `aw archive plans nonexistent-token-xyz` -> the same banner at EXIT 0, so a typo is indistinguishable from a clean tree. |
| F-06 | THE SAME MATCHER ALSO BREAKS TERSE SETIDS AT SCALE, because it compares the RAW `- Set:` line. THE CENSUS DRIFTS AND IS CONTEXT, NOT A BAR (re-measured at review): the counts below moved within a day, so Order 03 must re-derive them rather than assert them. | `aw archive plans researchorg` -> `✓ CLEAN no terminal-root plan or Set matches 'researchorg'`; `aw archive plans 'researchorg (research-org)'` -> **8** plans (the plan said 3). Corpus re-measured at review: **965** plans declare a Set (the plan said 908), 136 carry a descriptive parenthetical (unchanged), **549** distinct setids of which **77** are unaddressable (unchanged) against **472** addressable (the plan said 423). The 77/136 figures the Set's argument rests on are STABLE; the totals are not. |
| F-07 | THE ITEM'S ROADMAPS DIAGNOSIS IS WRONG AND ITS OWN WORKAROUND IS BROKEN, so that half is carried with a corrected diagnosis rather than as described. | `artifact_types.TYPE_BACKENDS['roadmaps']['rename']` is `artifact_rename.run_rename_roadmaps` and `aw rename roadmaps 7ny1bg --slug x` -> EXIT 0. Meanwhile `check_engine._identity_rename_hint('roadmaps','7ny1bg','Id',False)` -> `aw rename research 7ny1bg --to-id6 --apply`, and running it -> `error: no research artifact matched '7ny1bg'`, EXIT 2. |
| F-08 | THE FOUR CHILDREN TOUCH DISJOINT PRODUCTION FILES, so Orders 02, 03 and 04 can run in parallel lanes after 01 with no contention. | Declared `Scope-Paths`: `selectors.py` (01), `plans_refs.py` (02), `plans_archive.py` (03), `check_engine.py` (04), each with its own new test file. |
| F-09 | A SPEC ALREADY REQUIRES WHAT THIS SET IMPLEMENTS, so the Set closes a gap against a written contract rather than introducing a preference. | Spec `z7nbn1` 1.1: "A selector that resolves for one verb MUST resolve identically for every other verb"; its Section 2.1 records the selector as satisfied "largely... FOR READERS" and flags the surviving non-shared fallbacks as the remaining work. |
| F-10 | Baseline is clean in this lane, so any failure in any child is attributable to that child. THE ABSOLUTE COUNT DRIFTS AND IS NOT A BAR: each child re-derives it. | `python3 -m pytest` -> `3246 passed, 2 skipped, 3 warnings in 51.44s`. REPRODUCED at review HEAD `7b91f150`: `3246 passed, 2 skipped, 3 warnings in 49.40s`, plus the 207-test deselect notice. |

## Proposed changes (ordered, validatable)

1. Execute `eby93o` (Order 01): containment guard in `selectors.resolve_for_mutation`.
2. Execute `87m438` (Order 02): route `plans_refs` `rename`/`group` through the shared resolver, reading the id6 from the resolved file.
3. Execute `1x4tdo` (Order 03): route `plans_archive._find_targets`, fix the terse-setid comparison, and refuse an unmatched explicit target.
4. Execute `3qxuw1` (Order 04): derive the rename hint's type noun from the record's location.

This plan itself changes no source. Each numbered step is a child's whole deliverable, and the evidence lives in that child's `V-*` items.

## Deferred / out of scope (with reason)

- MERGING `plans_refs` INTO `artifact_rename.run_rename_generic` so there is literally one rename engine. Declined for the whole Set: the plans backend carries four distinct documented guarantees the generic engine does not (`vf03z3` Order/date preservation, `e3hzyc` Order semantics, `5rzupk` slug derivation, the three-form plan citation rewriter), and folding them in would risk all four in a change whose purpose is to fix a selector.
  - Carrier-Declined: an unmeasured behavioral merge of two engines with at least four documented guarantees; disproportionate to the defect and would obscure the source of any regression.
- NARROWING `selectors.resolve` ITSELF so no reader can address a foreign-type path. Declined: the read side is deliberately permissive, spec `z7nbn1` 2.1 counts seventeen importing modules, and the harm requires a MUTATION, which `resolve_for_mutation` already chokepoints.
  - Carrier-Declined: unmeasured blast radius across seventeen importers for no safety gain, since only a mutation can damage anything.
- DECIDING WHICH RECORDS TREE OWNS A `.roadmap.md` (both existing ones parse as research with `kind=roadmap`, yet one is filed under `roadmaps/`). Declined for the whole Set: deciding means MOVING tracked records and rewriting their citations, a data migration with its own review. Order 04 is deliberately correct under either answer.
  - Carrier-Declined: a records migration rather than a code defect; the hint derivation is correct under either filing, so nothing waits on it.
- WIRING `archive` FOR THE SEVEN TYPES THAT LACK IT. Declined: no type other than `plans` and `research` has a shelving convention to implement, so adding the verb means inventing sharding policy.
  - Carrier-Declined: there is no convention to implement; inventing one is a feature decision needing its own review.
- MAKING THE PLANS BACKEND HONOR `--to-id6`, which it silently ignores. Declined: implementing minting changes what the verb WRITES rather than what it ACCEPTS, and every plan in this repository already declares an id6, so it would have nothing to do today.
  - Carrier-Declined: a no-op flag is a separate defect from a refused selector; minting needs its own fence and an id6-allocation decision.

## Scope check

- Over-scope: none. This plan's single `Scope-Paths` entry is its own file, which is correct for a plan contributing no code: every production path is declared by the child that owns it, and no path is declared twice across the Set.
- Under-scope: after this Set, mutating verbs for the plans tree are consistent with readers, but `selectors.resolve` remains permissive for READERS by design, and the roadmap filing ambiguity remains. Both are recorded above with reasons. A reviewer who wants either in scope should say so, accepting that the first changes what seventeen modules see and the second is a records migration.

## Required tests / validation

This plan performs no work and therefore runs no tests of its own; each child owns its own failing-first evidence and its own suite runs. What this plan requires before it may be considered complete:

- All four children read `- Status: executed` on disk, each with its `V-*` items carrying inspected evidence.
- THE SEQUENCING WAS HONORED, which is this plan's one substantive claim: `eby93o` executed BEFORE `87m438` and `1x4tdo`. Both children pin this from their side with a test asserting a foreign-type path is refused through their newly routed backend, so a violation shows up as a failing child test rather than only as a date ordering.
- The end-state consistency check, run once after all four: `aw rename plans <a filename>`, `aw group plans <a filename>` and `aw archive plans <a filename>` all resolve, and `aw rename plans <a spec path>` refuses.

## Spec / documentation sync

No spec amendment is required by this Set and no `.spec.md` file appears in any child's `Scope-Paths`, and that conclusion rests on reading the three specs that govern selectors rather than on a grep miss.
- Spec `z7nbn1` (`Status: implementing`) 1.1 is what the Set IMPLEMENTS: a selector that resolves for one verb must resolve identically for every other. Its own Section 2.1 already names the surviving non-shared fallbacks as the remaining work, so no text needs changing.
- Approved spec `2lcqno` N3 documents the path-kind hole Order 01 closes ("type-safe for every selector kind EXCEPT a direct PATH") and requires the existing `status_set` refusal be "PINNED, never retired as dead code"; Order 01 adds a second guard on a second surface and leaves that refusal byte-unchanged, which is what N3 contemplates.
- The uniform naming spec defines the `<id6>` filename segment as "the artifact's `- Id:`", which is the contract Order 02's id6 re-read protects, and states the singleton-set convention Order 02 asserts for a Set-less plan.
IF ANY CHILD'S EXECUTOR FINDS a spec sentence asserting that the plans tree deliberately accepts only an id6, that a mutating verb may act outside its type's tree, or that an unmatched archive target should exit 0, that discovery changes this section: stop, add the file to that child's `Scope-Paths`, amend it in the same change, and say why, per the plan-may-amend-a-spec rule.

## Open questions

### OQ-01: Should this have been one plan rather than a Set of four?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, A SET, on two grounds that are measured rather than stylistic. FIRST, a REQUIRED ORDERING exists inside the work: the shared resolver hands back a foreign-type file for a path selector (F-03), so the routing change and the guard cannot land in either order, and a single plan would hide that ordering inside one checklist where a reviewer could not judge it or a runner enforce it. SECOND, the four changes touch four DISJOINT production modules with disjoint test surfaces (F-08), and three of them are mutually independent, so a Set lets Orders 02, 03 and 04 execute in parallel lanes after Order 01 while a single plan would serialize them. The children are also separately reviewable in a way that matters: Order 03 changes a user-visible EXIT STATUS and Order 01 changes a shared resolver's refusal policy, and a reviewer may legitimately approve one and question the other.

### OQ-02: Should the backlog item be closed `done` once this Set executes?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, NO, `graduated` NOW AND THE GATE TRAVELS WITH THE CHILDREN. Per AGENTS.md, `graduated` means the design is handed off while `done` means the code is written and validated, so the authoring flow sets `graduated` and does not close it. The item carries `- Blocks-Release: next`, and every child inherits that gate plus `- From-Backlog: gyv9tf`, so the release blocker is provably preserved across the handoff rather than dropped: the close-legitimacy predicate is satisfied by an EXECUTED plan carrying the same gate and the same `From-Backlog`. Note the item's `Work-Kind: bug` also makes the gate mandatory while it is live, so removing it from any child would be a policy violation and not a tidy-up.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `eby93o` reads `- Status: executed` on disk and sits in `.aw/records/plans/executed/`; paste the path and the status line. Plus a statement that its own `V-*` items carry inspected evidence, since this Set's safety rests on that guard actually being in force.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `87m438` reads `- Status: executed` on disk; paste the path and the status line. Plus confirmation that it executed AFTER `eby93o`, evidenced by its own foreign-type-path test passing (which can only pass with the guard in place), not merely by commit dates.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `1x4tdo` reads `- Status: executed` on disk; paste the path and the status line. Plus confirmation it executed after `eby93o`, on the same basis as V-02.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `3qxuw1` reads `- Status: executed` on disk; paste the path and the status line. Plus the end-state consistency check for the whole Set, pasted: `aw rename plans <a filename>`, `aw group plans <a filename>` and `aw archive plans <a filename>` each resolving, and `aw rename plans <a spec path>` refusing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was authored `to-review` with no `- Readiness:` field, correctly, since that value is an output of review rather than of authoring. It must not be executed on the strength of the authoring turn.

THIS PLAN CARRIES NO WORK OF ITS OWN, WHICH IS DELIBERATE AND IS WHAT MAKES ITS RETIREMENT HONEST. Every deliverable belongs to a child; this file contributes no code, no test and no record. That matters mechanically: a runner RETIRES an orchestrator once every child is `executed` and SKIPS the pre-transition E/V checkpoint, on the premise that the parent's items are performed by nobody. Any work parked here would therefore be marked complete having never been performed or verified. If a reviewer believes this Set needs a step no child covers, ADD A CHILD for it; do not move it onto this file, and do not delete the child checklist to make the coverage gate pass.

EXECUTION CONTRACT. In a managed lane the runner owns this plan's transition and retires it as bookkeeping once all four children are `executed`; no agent turn is spent on it. An agent executing this Set BY HAND must honor the one required edge (`eby93o` before `87m438` and `1x4tdo`), may run Orders 02, 03 and 04 in any order or in parallel after that, and must execute each child under that child's own execution contract and fence. Do not change any child's requirements to make it easier. Commit through `aw commit <plan> -- <paths>` with the staged set verified (the checkout is shared); never `git add -A`, never push, never `--no-verify`.
POST-GATE LIFECYCLE. Move this plan to `.aw/records/plans/executed/` only once all four children are there and `aw ipd lint --phase pre-transition` conforms. Backlog item `gyv9tf` is set `graduated`, not `done`, by the authoring flow; do not close it here, and do not strip `- Blocks-Release: next` from any child, since the item's `Work-Kind: bug` makes that gate mandatory while the work is live (OQ-02).
