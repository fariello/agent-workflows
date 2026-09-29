# IPD: Derive the rename hint type from where the record lives so the suggested command resolves

- Date: 2026-09-29
- Kind: child
- Concern: `check_engine._IDENT_RENAME_TYPE` maps `roadmaps -> research` as a STATIC constant, so the remediation command it emits for a roadmap is wrong for whichever of the two possible locations the record is NOT in. The map's own comment justifies the entry with "a `.roadmap.md` lives in the research tree and `aw rename roadmaps <id6>` reports 'no roadmaps artifact matched' while `aw rename research <id6>` resolves it", and that premise is only TRUE OF SOME ROADMAPS. Measured in this lane: of three `.roadmap.md` files, one is under `.aw/records/roadmaps/` and is resolvable ONLY as `aw rename roadmaps 7ny1bg`, while `aw rename research 7ny1bg` exits 2 with `no research artifact matched '7ny1bg'`. So for that file the hint emits exactly the refusing command its own docstring says is "worse than no suggestion".
  THE BACKLOG ITEM'S DIAGNOSIS IS WRONG HERE AND THE CORRECTION MATTERS, because it points at a fix that would not work. The item says "the roadmaps type has no rename route of its own". It does: `artifact_types.TYPE_BACKENDS` maps `roadmaps` `rename` to `artifact_rename.run_rename_roadmaps`, which delegates to the generic engine, and measured, `aw rename roadmaps 7ny1bg --slug x` resolves and previews the rename plus four citation rewrites. The real cause is DIRECTORY SCOPING: `selectors.resolve` searches only the requested type's own `record_dirs`, so a `.roadmap.md` filed in the research tree is reachable as `research` and not as `roadmaps`, and one filed under `roadmaps/` is the reverse. A record's addressable TYPE depends on WHICH DIRECTORY it was filed in, and the static map cannot express that.
  THIS IS LATENT, NOT LIVE, AND THE PLAN SAYS SO RATHER THAN OVERSTATING IT. Measured: `check_name_identity` with `include_retired=True` currently reports ZERO findings on any `.roadmap.md`, so the wrong hint is not being printed to anyone today. What makes it worth fixing anyway is that it is a CORRECTNESS TRAP WITH A TRIGGER OUTSIDE ANYONE'S CONTROL: the branch fires the first time a roadmap's declared `- Id:` or `- Set:` stops matching its filename, and at that moment the tool confidently prints a command that exits 2. A latent defect whose remedy is a one-line derivation is cheaper to fix than to rediscover.
- Scope: Replace the static `roadmaps -> research` entry's effect with a DERIVATION: pick the rename type noun by asking which type actually resolves the record at its real path, so the emitted command is runnable for a roadmap in either tree. Keep the map for every type whose noun is unambiguous, keep the existing id6-over-filename selector preference, and add the outcome tests this branch has none of. EXCLUDES: changing where roadmaps are FILED or which tree owns them (a records-taxonomy decision, not a hint defect); changing `selectors.py` type scoping; adding `rename` routes for `comms`/`reviews`, which have none; and the `plans`/`archive` selector defects carried by the siblings.
- Scope-Paths: agent_workflows/check_engine.py, tests/test_identity_rename_hint.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: gyv9tf
- Blocks-Release: next
- Set: awrenamesel
- Order: 4
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 3qxuw1

## Workflow history

- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `gyv9tf`. THIS PLAN CORRECTS THE BACKLOG ITEM RATHER THAN IMPLEMENTING IT. The item asserts "the roadmaps type has no rename route of its own"; measured, it HAS one (`artifact_rename.run_rename_roadmaps`) and `aw rename roadmaps 7ny1bg --slug x` resolves, so a fix that added a route would have been work with no defect behind it (F-02). The real defect is directory-scoped resolution, and the discovery that matters is that the item's own WORKAROUND is broken: the `roadmaps -> research` mapping it describes as the fix emits a REFUSING command for the one roadmap actually filed under `roadmaps/` (F-03). PRIORITY IS `low`, DELIBERATELY BELOW ITS SIBLINGS, because the branch's current population is ZERO (F-04) and nothing is being mis-advised today; it is filed as a bug rather than a chore because when it does fire it prints a command that exits 2, which is a wrong answer and not an inefficiency. It carries the item's `Blocks-Release: next` gate per the repository's every-live-bug rule. It declares no dependency on the siblings: it changes a hint string, touches no resolver, and is correct in any order.

## Goal

Make the remediation command a roadmap's identity finding prints actually resolve, by deriving the type noun from where the record lives instead of asserting one statically.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the wrong hint

- [ ] E-01 REPRODUCE THE WRONG HINT AS A FAILING TEST, and make the test's oracle be that the command RUNS, not that it matches a string. Create `tests/test_identity_rename_hint.py` and add a case that seeds a roadmap under `.aw/records/roadmaps/` whose declared `- Id:` is ABSENT from its filename (which is what makes the identity branch fire), obtains the finding's recovery command, and asserts that RUNNING that command resolves rather than refusing. At HEAD this must FAIL: the emitted command is `aw rename research <id6> --to-id6 --apply` and `aw rename research 7ny1bg --to-id6` exits 2 with `no research artifact matched '7ny1bg'`.
  THE ORACLE IS EXECUTABILITY, WHICH IS THE WHOLE POINT AND ALSO WHAT KEEPS THIS TEST HONEST. Asserting the hint equals the literal string `aw rename roadmaps ...` would pin an implementation detail and would pass for a command that still refused. Drive the emitted command through `cli.main` in the fixture repo and assert a non-refusal, so the test measures the property the docstring claims ("a suggested command that refuses is worse than no suggestion").
  ADD THE MIRROR CASE, a `.roadmap.md` filed in the RESEARCH tree, whose correct noun is `research`. Both cases must pass after the fix; at HEAD this one already passes, and that asymmetry is exactly why a static map is wrong. Keep it as a control so a fix that merely flipped the constant to `roadmaps` would FAIL it.
  DRIVE IT IN-PROCESS VIA `cli.main` UNDER `redirect_stdout`, NOT AS A SUBPROCESS. Measured hazard rather than style: an editable install can make a subprocess `python3 -m agent_workflows` in a lane import the MAIN checkout, so a subprocess assertion can pass while the tree under test is unfixed (filed as `ccbe60`).
  MAKE THE FINDING ACTUALLY FIRE, WHICH TAKES CARE. `check_name_identity` skips a record whose name matches NO grammar (that is `check.name-nonconformant`'s subject), skips the `Id` half of a MODERN id6-clustered name, and reads the declaration only from the METADATA REGION so a quoted example is not treated as a claim. So the fixture must be a legitimately SHAPED but pre-id6 name carrying a real metadata `- Id:` bullet. Verify the finding appears before asserting anything about its recovery text; a fixture that produces no finding would make a broken test pass vacuously.
  - Depends on: none
  - Expected outcome: Two tests, the `roadmaps/`-tree case FAILING at HEAD because its suggested command exits 2, and the research-tree case passing as a control.
  - Execution state: pending

### Task group 2: derive the noun

- [ ] E-02 DERIVE THE RENAME TYPE FROM WHERE THE RECORD LIVES. In `check_engine._identity_rename_hint`, choose the type noun by asking which type actually resolves this record at its real path, rather than reading a static map entry. Keep the map for the unambiguous types and use the derivation where the record's type is positional.
  PASS THE PATH IN, WHICH IS THE SIGNATURE CHANGE THIS NEEDS. `_identity_rename_hint(record_type, selector, field, modern)` currently receives no path, which is precisely why it cannot answer the question; its caller `_identity_finding` HAS the path. Thread it through rather than re-deriving anything from the selector.
  DERIVE BY CONTAINMENT IN `selectors.record_dirs`, NOT BY `status_set.detect_artifact_type`. This is the measured trap in this area (Order 01 hit the same one): `detect_artifact_type` types ANY `.roadmap.md` as `roadmaps` via its facet-first branch, including the one in the research tree that only `aw rename research` resolves, so using it would emit the refusing command for the OTHER file. Ask instead which type's `record_dirs` CONTAIN the record's path; that is the same question `selectors.resolve` answers when it scopes a search, so the hint and the resolver cannot disagree.
  FALL BACK TO SILENCE, NEVER TO A GUESS. The function already returns `""` when it has no usable type or selector, and `_identity_finding` already substitutes a prose remedy in that case. If no type's directories contain the record, emit no command rather than a plausible-looking one: the docstring's own standard is that a refusing suggestion is worse than none.
  DO NOT CHANGE THE SELECTOR PREFERENCE. Preferring the declared id6 over the filename is CORRECT and is the other half of why this helper exists; it is also what makes the emitted command work for the plans tree, whose resolver is id-directed until `87m438` lands. Leave that logic exactly as it is.
  - Depends on: E-01
  - Expected outcome: The emitted command names a type noun that resolves the record, for a roadmap in either tree, and stays silent rather than guessing when no type owns the path.
  - Execution state: pending

### Task group 3: prove the other types did not regress

- [ ] E-03 PIN EVERY OTHER TYPE'S HINT AS STILL CORRECT AND STILL RUNNABLE. Add cases covering each type the map serves (`plans`, `specs`, `backlog`, `prompts`, `walkthroughs`, `releases`, `research`) that seed a record of that type with a declared identity absent from its filename and assert the emitted command RESOLVES. This is the regression surface of E-02's change: the derivation must not alter a noun that was already right.
  ASSERT EXECUTABILITY PER TYPE, not equality with a string, for the same reason as E-01. A type whose derived noun differs from its old static entry is a finding to REPORT, not to paper over: it would mean the static map and the directory layout disagree for a type nobody has checked.
  NOTE THE `plans` CASE IS THE ONE TO WATCH, because its resolver accepts only an id6 until `87m438` lands. The hint already prefers the declared id6, so it should pass both before and after that plan; if it passes only after, say so, since that would mean this plan's test depends on a sibling and the dependency should be declared.
  - Depends on: E-02
  - Expected outcome: Every mapped type's hint still resolves; any type whose derived noun differs from its static entry is reported rather than silently accepted.
  - Execution state: pending

- [ ] E-04 STATE THE REMAINING HOLE HONESTLY IN THE CODE, so the next reader is not misled the way this map's comment misled. Replace the stale justification comment (which asserts a `.roadmap.md` "lives in the research tree") with the measured truth: a `.roadmap.md` may live in EITHER tree, its addressable type follows its DIRECTORY, and the noun is therefore derived. Name the types that have NO `rename` route at all (`comms`, `reviews`) so the absence stays deliberate rather than looking like an oversight.
  DO NOT CLAIM THE UNDERLYING TAXONOMY QUESTION IS FIXED. This plan makes the HINT correct; it does not decide whether a roadmap-kind research document should live under `roadmaps/`, and that ambiguity remains. Say so in the comment and record it in the Deferred section, so a later reader does not read a working hint as evidence that the filing question was settled.
  - Depends on: E-02
  - Expected outcome: The comment describes measured behavior, names the routeless types, and does not overstate what was fixed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The suite is run BARE (`python3 -m pytest`); `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q`, or `-p no:randomly` (AGENTS.md).
- Tests must assert OBSERVABLE BEHAVIOR, never code structure: no `inspect`/`ast`/regex reads of production source, no symbol censuses (AGENTS.md, GUIDING_PRINCIPLES P16). Every test this plan adds RUNS the suggested command and asserts it resolves, which is the strongest available oracle for a remediation hint.
- `check_name_identity` is ADVISORY (`warning`) and scope-filtered: it honors `include_retired`, skips names matching no grammar at all (owned by `check.name-nonconformant`), skips the `Id` half of a modern clustered name (owned by `check.id6-identity-slot`), and reads declarations only from the metadata region. A fixture must thread all four filters to make the branch fire.
- `selectors.record_dirs` returns only EXISTING directories and `[]` for an unknown type, so a containment derivation must handle the empty case (which is the silence path here).
- Commit through `aw commit <plan> -- <paths>`, never `git add -A`; verify the staged set, since this checkout is shared (AGENTS.md).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | THE HINT EMITS A REFUSING COMMAND for the one roadmap filed under `roadmaps/`, which is exactly what its own docstring calls worse than no suggestion. | `check_engine._identity_rename_hint('roadmaps','7ny1bg','Id',False)` -> `aw rename research 7ny1bg --to-id6 --apply`; running `aw rename research 7ny1bg --to-id6` -> `error: no research artifact matched '7ny1bg'`, EXIT 2. |
| F-02 | THE BACKLOG ITEM'S DIAGNOSIS IS WRONG: `roadmaps` HAS a rename route of its own and it works. | `artifact_types.TYPE_BACKENDS['roadmaps']['rename'] == 'artifact_rename.run_rename_roadmaps'`; `aw rename roadmaps 7ny1bg --slug x` -> EXIT 0, previews the rename plus 4 citation rewrites in 2 backlog records. |
| F-03 | THE REAL CAUSE IS DIRECTORY-SCOPED RESOLUTION, so a record's addressable type follows its FILING LOCATION and no static map can be right for both cases. | `selectors.resolve(repo,'roadmaps','effzzi')` -> 0 paths; `selectors.resolve(repo,'research','effzzi')` -> 1 path, `kind=id6`. `selectors.resolve(repo,'roadmaps','7ny1bg')` -> 1 path; `selectors.resolve(repo,'research','7ny1bg')` -> 0 paths. The two `.roadmap.md` files need OPPOSITE nouns. |
| F-04 | IT IS LATENT TODAY, POPULATION ZERO, which is why the priority is `low` and why this plan does not overstate the harm. | `check_engine.check_name_identity(repo, include_retired=True)` -> 11 findings, NONE on a `.roadmap.md` and none under `.aw/records/roadmaps/`. |
| F-05 | THE MAP'S JUSTIFICATION COMMENT IS FACTUALLY WRONG, which is how the defect survived: it asserts "a `.roadmap.md` lives in the research tree", true of 2 of 3 such files and false of the one the hint then mis-advises. | The comment above `_IDENT_RENAME_TYPE`; corpus: `.aw/records/roadmaps/...7ny1bg...roadmap.md`, `.aw/records/research/reference/202608/...effzzi...roadmap.md`, `.aw/records/research/archive/202607/...3rpcmu...roadmap.md`. |
| F-06 | THE OBVIOUS DERIVATION IS ALSO WRONG, measured: `status_set.detect_artifact_type` types BOTH files `roadmaps` via its facet-first branch, so using it would emit the refusing `roadmaps` noun for the research-tree file. | `detect_artifact_type(<research-tree .roadmap.md>)` -> `'roadmaps'` while only `resolve(repo,'research',...)` finds it. `artifact_naming.TYPE_FACET['roadmaps'] == 'roadmap'`. |
| F-07 | CONTAINMENT IN `record_dirs` GIVES THE RIGHT ANSWER FOR BOTH FILES, which is why E-02 uses it: it is the same question the resolver answers when scoping a search. | Containment check: `('roadmaps', <roadmaps-tree file>)` -> True, `('research', <roadmaps-tree file>)` -> False; `('research', <research-tree .roadmap.md>)` -> True, `('roadmaps', <that file>)` -> False. |
| F-08 | BOTH FILES PARSE AS RESEARCH DOCUMENTS with `kind=roadmap`, which is why the taxonomy question is genuinely open and must NOT be presented as settled by this plan. | `research_contract.parse_name` on both names -> `kind='roadmap'` (`set=awoptimize id=effzzi`, `set=7ny1bg id=7ny1bg`). `research_contract.KINDS` includes `roadmap`. |
| F-09 | THE HELPER CANNOT ANSWER THE QUESTION TODAY BECAUSE IT NEVER RECEIVES THE PATH, so E-02's signature change is required rather than cosmetic. Its caller has the path. | `_identity_rename_hint(record_type, selector, field, modern)` takes no path; `_identity_finding(record_type, path, field, value, in_region, modern, selector)` takes one and calls it. |
| F-10 | THE SELECTOR PREFERENCE IS CORRECT AND MUST SURVIVE: preferring a declared id6 over a filename is what makes the emitted command work for the plans tree, whose resolver is id-directed. | `_identity_rename_hint` docstring: "THE SELECTOR IS THE DECLARED id6 WHEREVER ONE EXISTS, not the filename"; measured, `aw rename plans <legacy filename> --to-id6` exits 2 while `aw rename plans 7qx7ys --to-id6` exits 0. |
| F-11 | THE `--to-id6` SUFFIX IS A SEPARATE PRE-EXISTING WART on the plans branch of this hint, worth knowing so it is not mistaken for this plan's regression: the plans backend ignores the flag entirely. | `aw rename plans 7qx7ys` and `aw rename plans 7qx7ys --to-id6` print IDENTICAL target names; `to_id6` appears 0 times in `plans_refs.py`. |
| F-12 | Baseline is clean in this lane, so any failure after the change is attributable to it. THE ABSOLUTE COUNT DRIFTS AND IS NOT A BAR: re-derive it on your own clean tree. | `python3 -m pytest` -> `3246 passed, 2 skipped, 3 warnings in 51.44s`. |
| F-13 | NO TEST ASSERTS A HINT IS RUNNABLE. The one adjacent test asserts the printed advisory STRING only, so a hint that refuses passes the suite today. | `tests/test_doctor.py` asserts on the printed remediation text; no test executes an emitted `aw rename` command. |

## Proposed changes (ordered, validatable)

1. Add `tests/test_identity_rename_hint.py` with a failing case proving the `roadmaps/`-tree hint emits a command that exits 2, plus the research-tree control (E-01).
2. Thread the record's path into `_identity_rename_hint` and derive the type noun by containment in `selectors.record_dirs`, falling back to silence (E-02).
3. Add per-type executability cases for every mapped type, reporting any type whose derived noun differs from its static entry (E-03).
4. Replace the stale justification comment with the measured truth, name the routeless types, and state that the filing-taxonomy question remains open (E-04).

## Deferred / out of scope (with reason)

- THE PLANS `rename`/`group` SELECTOR DEFECT, the backlog item's own subject.
  - Carrier: 87m438
- THE CROSS-TYPE PATH GUARD on mutating verbs.
  - Carrier: eby93o
- THE `archive plans` SILENT NO-OP AND RAW-SETID DEFECTS.
  - Carrier: 1x4tdo
- THE RECORDS-TAXONOMY QUESTION: whether a document that parses as research with `kind=roadmap` (F-08) should live under `.aw/records/roadmaps/` or under the research tree, and therefore which noun SHOULD address it. This plan deliberately makes the hint correct for BOTH filings instead of deciding, because deciding means MOVING tracked records and rewriting their citations, which is a records migration needing its own review. If the answer were later "roadmaps own all `.roadmap.md` files", this plan's derivation would still be correct, which is the point of deriving.
  - Carrier-Declined: deciding it means moving tracked records and rewriting citations, a data migration with its own review; the derivation is correct under either answer, so the hint need not wait for it.
- ADDING `rename` ROUTES FOR `comms` AND `reviews`, which have none, so `_IDENT_RENAME_TYPE` has no entry and the hint correctly stays silent. Out of fence: giving them a route means deciding their naming grammar and citation semantics, not fixing a hint.
  - Carrier-Declined: no rename route exists to correct; creating one is a feature with its own grammar and citation decisions.
- THE `--to-id6` NO-OP ON THE PLANS BRANCH of this hint (F-11). Pre-existing, unrelated to type derivation, and carried in the sibling's Deferred list; mentioning it here only so an executor does not read it as a regression introduced by this change.
  - Carrier-Declined: a separate pre-existing defect in a different module; fixing it changes what `rename plans` WRITES, not which noun the hint names.

## Scope check

- Over-scope: none. The two declared paths are the module holding the wrong map and a new test file dedicated to the hint. `agent_workflows/selectors.py` is deliberately NOT in scope: E-02 CALLS `record_dirs` and must not change type scoping. `status_set.py` is not in scope and is deliberately NOT used (F-06).
- Under-scope: the hint becomes correct while the underlying ambiguity (which tree owns a roadmap-kind document) remains, so two records of the same apparent kind still need different nouns. That is accepted deliberately and stated in code by E-04, so the next reader is not misled the way F-05's comment misled.

## Required tests / validation

- The new cases in `tests/test_identity_rename_hint.py`: the `roadmaps/`-tree roadmap, the research-tree `.roadmap.md` control, and one executability case per mapped type.
- EVERY CASE'S ORACLE MUST BE THAT THE EMITTED COMMAND RESOLVES, run through `cli.main`, not that it equals a string. A string-equality test would pass for a refusing command and would pin an implementation detail; F-13 records that the only adjacent test today asserts printed text and therefore cannot catch this class of defect.
- FAILING-FIRST CONTRAST IS MANDATORY: run E-01's `roadmaps/`-tree case against UNFIXED source and paste the failure, showing the emitted command and its exit 2, then against the fixed tree and paste the pass. Also paste the research-tree control PASSING at HEAD, since the asymmetry is the evidence that a static map cannot serve both.
- STATE THE POPULATION HONESTLY in the evidence: `check_name_identity` reports zero `.roadmap.md` findings on this repository today (F-04), so the fixture is what makes the branch fire. Confirm the finding actually appeared before asserting on its recovery text; a vacuous fixture would make a broken test pass.
- Bare `python3 -m pytest` before and after, with both summary lines pasted. MEASURE YOUR OWN BASELINE ON A CLEAN TREE and compare against that, not against F-12's `3246`, which drifts with every intervening commit. The bar is ZERO FAILURES and a passed-count delta of exactly the new cases.
- Negative proof that the fence held: `git diff --stat` shows no change to `agent_workflows/selectors.py`, `agent_workflows/status_set.py`, `agent_workflows/plans_refs.py` or `agent_workflows/artifact_rename.py`.
- `aw sanitize --agent` clean (no maintainer/machine identifiers in anything authored).

## Spec / documentation sync

No spec amendment is required and no `.spec.md` file is in `Scope-Paths`, and that conclusion rests on reading the specs that govern resolution rather than on a grep miss.
- Approved spec `2lcqno` N3 requires type-scoped resolution ("Every verb that accepts a setid MUST resolve it WITHIN the requested type's tree when a type is known"). This plan does not change that scoping; it makes a SUGGESTED COMMAND agree with it, which is a defect fix toward the approved contract rather than a change to it.
- Spec `z7nbn1` 1.1 ("a selector that resolves for one verb MUST resolve identically for every other verb") is about selector kinds, not type nouns, and is untouched here; the siblings carry its plans-tree violation.
- The uniform naming spec's type-token table lists `Roadmap | .roadmap.md` with no note about which tree owns it, which is the documentation gap behind F-08. This plan does NOT close it, because closing it is a filing decision, and writing a rule into the spec would commit the repository to a migration this plan does not perform. E-04 records the ambiguity in code instead.
IF THE EXECUTOR FINDS a spec or README sentence stating which tree owns a `.roadmap.md`, that changes this section and possibly the fix: a documented owner would make one of the two filings WRONG, which is a records defect to report rather than something to accommodate. Stop and report rather than silently encoding a rule the specs do not state.

## Open questions

### OQ-01: Derive the type noun, or fix the filing so a static map is right?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, DERIVE. Fixing the filing means MOVING tracked records between `.aw/records/research/` and `.aw/records/roadmaps/` and rewriting their citations, which is a records migration with its own review, and it would still leave the hint asserting a rule rather than observing reality. Deriving is a one-line question ("which type's directories contain this path") that is correct under EITHER answer to the filing question, so it does not block on a taxonomy decision and does not have to be revisited if that decision is later made. The filing question is recorded in Deferred with the reason (F-08 shows both files parse as research with `kind=roadmap`, so it is genuinely ambiguous and not an obvious mistake).

### OQ-02: Why not reuse `status_set.detect_artifact_type`, which already types a path?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT: IT GIVES THE WRONG ANSWER HERE. `detect_artifact_type` is facet-first and returns the first type whose `TYPE_FACET` suffix the filename ends with, so it types BOTH `.roadmap.md` files as `roadmaps`, including the research-tree one that ONLY `aw rename research` resolves (F-06). Using it would fix one file and break the other, which is the current defect with the sides swapped. Containment in `selectors.record_dirs` asks the same question the RESOLVER asks when it scopes a search (F-07), so the hint and the resolver cannot disagree by construction, which is the property that matters for a suggested command. Order 01 (`eby93o`) hit and recorded the identical trap on a different surface, so this is a repeated measurement rather than a one-off.

### OQ-03: Should a type with no resolvable owner emit a best-guess command or nothing?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED, NOTHING, following the function's existing contract. It already returns `""` when it has no type or no selector, and `_identity_finding` already substitutes prose ("reconcile the filename with the declared metadata" / "converting this name to the id6 grammar is optional"), so silence has a well-formed presentation and needs no new code path. The docstring's standard is explicit that "a suggested command that refuses is worse than no suggestion", and a best guess is precisely a command that may refuse. This also makes the empty-`record_dirs` case (a type whose directory does not exist) fall out correctly without special handling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The pytest output for the `roadmaps/`-tree case run against UNFIXED source, pasted verbatim, showing it FAILING, together with the EXACT emitted command and the EXACT refusal and exit code observed when it was run. Plus the research-tree control PASSING at HEAD, pasted, since the asymmetry is the evidence a static map cannot serve both. Plus explicit confirmation that the seeded fixture actually PRODUCED an identity finding (state how many findings and on which file), because a fixture that threads none of the four scope filters would make a broken test pass vacuously.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Both E-01 cases now PASSING, pasted; plus the `git diff` of `check_engine.py` showing the path threaded into `_identity_rename_hint`, the containment-based derivation, and the silence fallback. Plus explicit confirmation that `status_set.detect_artifact_type` was NOT used, with the measured reason restated (F-06), since that is the substitution a later reader is most likely to make. Plus confirmation the id6-over-filename selector preference is unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pytest output for the per-type executability cases, pasted, naming each of the seven mapped types and the command emitted for it, with the observed exit status of RUNNING each. Any type whose derived noun differs from its old static entry must be named explicitly and REPORTED as a finding, not silently accepted. For `plans`, state whether the case passes before `87m438` lands as well as after, and if it passes only after, declare that this plan needs an `Item-Dependencies` edge it currently lacks.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: The new comment text pasted in full, showing it states that a `.roadmap.md` may live in either tree, that addressability follows the directory, that the noun is derived, and that `comms`/`reviews` have no rename route. Plus confirmation that it does NOT claim the filing-taxonomy question is resolved. Plus the bare `python3 -m pytest` summary after the change compared against the baseline YOU measured before editing (not F-12's number), with the delta shown to be exactly the new cases and zero failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan was authored `to-review` with no `- Readiness:` field, correctly, since that value is an output of review rather than of authoring. It must not be executed on the strength of the authoring turn.

EXECUTION CONTRACT. Stay inside `Scope-Paths`: `agent_workflows/check_engine.py` and `tests/test_identity_rename_hint.py`. Call `selectors.record_dirs`; do NOT modify `selectors.py`, and leave `status_set.py`, `plans_refs.py` and `artifact_rename.py` byte-unchanged. Do NOT derive the noun with `status_set.detect_artifact_type`: F-06 measures that it returns `roadmaps` for BOTH files and would break the research-tree case. Do NOT change the id6-over-filename selector preference (F-10). Do NOT move any record or decide which tree owns a `.roadmap.md`. Commit through `aw commit <plan> -- <paths>` with the staged set verified (the checkout is shared); never `git add -A`, never push, never `--no-verify`.
EVIDENCE CONTRACT. The failing-first contrast in V-01 is the gate, and it has a second half unique to this plan: you must also show the fixture PRODUCED a finding, because the branch's real-world population is zero (F-04) and a fixture that fires nothing would make a broken test pass. Every oracle must be that the emitted command RUNS, never that it matches a string. Paste actual runner output for every `V-*`; never record a pass not run. Be aware of the measured hazard behind E-01's in-process requirement: an editable install can make a subprocess `python3 -m agent_workflows` import the MAIN checkout rather than this lane (`ccbe60`), so a subprocess assertion can pass against unfixed source.
POST-GATE LIFECYCLE. On completion move this plan to `.aw/records/plans/executed/` only once `aw ipd lint --phase pre-transition` conforms and every `V-*` carries inspected evidence. The runner owns the transition in a managed lane (`aw ipd begin` refuses with `AW-LIFECYCLE-ROLE-001` there). Backlog item `gyv9tf` is set `graduated`, not `done`, by the authoring flow; do not close it here.
