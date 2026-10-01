# IPD: Repair the qrokie plan's fabricated filename date and the three citations the rewriter cannot reach

- Date: 2026-10-01
- Kind: child
- Concern: Exactly one record in the corpus carries a filename date that is a FABRICATED CONSTANT rather than its own date. `.aw/records/plans/executed/20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md` was renamed from `20260723-1100-07-clean-delta-and-tracking-modes-design-spec.md` by the one-off bulk migration `05c4deb1`, which discarded the real `20260723` present in the old name and substituted `plans_refs._plan_date`'s last-resort literal `20260101`. The plan's own `- Date: 2026-07-23 (fleshed 2026-07-26 from research)` is malformed against the anchored `_DATE_RE`, which is WHY the fabricator fired. The wrong date then propagated into three prose citations BY NAME, in `DECISIONS.md` D109, in spec `20260726-1239-01-clean-delta-and-tracking-modes.spec.md`, and in the research bundle `README.md`, so the name's lie is now repeated in three live records and the real date survives only in git.
- Scope: IN: correct the plan's malformed `- Date:` to the parseable `2026-07-23` so the tooled rename can read it (measured mandatory, F-04); rename the record to `20260723-instsafe-07-qrokie-...` through `aw group plans --rename --apply`; rewrite the FOUR tool-reachable live citations the preview names; HAND-correct the THREE citations the rewriter structurally cannot reach (F-06); re-key the one `tests/fixtures/derive_plan_status_baseline.json` entry, which the rewriter also cannot reach because it scans no `.json` (F-07). OUT: every code path (`plans_refs._plan_date` is `949enf`; `plans_archive._plan_date` is `dkfthf`; the lint gap is `fqcax0`/`5h8u3z`; filename-versus-metadata detection is `mt6j1p`); the facet-less-stem blindness in `artifact_refs` this plan WORKS AROUND BY HAND rather than fixes (F-06, OQ-02); any other record's name, date, or body; the `20260101` constant itself; and every citation this plan classifies LEAVE (fenced evidence transcripts and historical `.agents/` paths).
- Scope-Paths: .aw/records/plans/executed/20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md, DECISIONS.md, .aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md, .aw/records/research/20260726-0054-aw-delivery-and-clean-delta-research/README.md, tests/fixtures/derive_plan_status_baseline.json, .aw/records/backlog/done/20260901-historder-01-tk1gqo-lifecycle-history-order-mismatch.backlog.md, .aw/records/backlog/graduated/20260922-historder-01-jhrao5-oldest-first-legacy-history-misreported.backlog.md, .aw/records/backlog/graduated/20260929-5h8u3z-01-5h8u3z-malformed-date-escapes-ipd-lint.backlog.md, .aw/records/backlog/open/20260930-mt6j1p-01-mt6j1p-filename-date-disagrees-with-metadata-unreported.backlog.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: tf4jz5
- Set: tf4jz5
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: j7dsci

## Workflow history

- 2026-10-01 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-01 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `tf4jz5`, which filed the repair as a maintainer judgement call and named two candidate routes (RENAME with reference rewriting, or LEAVE as recorded history). THE DECISION IS RESOLVED FROM REPOSITORY EVIDENCE RATHER THAN DEFERRED, because the item's own stated blockers both dissolve on measurement: `.aw/records/plans/README.md` states in as many words that "Set membership/order changes on a plan already in a terminal directory are a deliberate, tool-driven, citation-safe act (the plan BODY and workflow history stay immutable; only the name/grouping is mutable via the stable `Id`)", which is the sanctioned route AGENTS.md's immutability rule leaves open, and the `ipd-executed-gate` hook was DRIVEN against a staged rename of this exact file and returned rc 0 (F-02, F-03). FOUR CORRECTIONS THE ITEM DOES NOT CONTAIN, each measured. (1) `aw rename plans` CANNOT PERFORM THIS REPAIR AT ALL and the item's assumption that it can is wrong: `run_mv` reads the date from the CURRENT filename via `_CLUSTERED_RE`, which matches, so it reproduces `20260101` and previews no rename (F-04). (2) THE MALFORMED `- Date:` MUST BE CORRECTED FIRST or no tooled route exists, measured through the real CLI on a copy carrying the production string verbatim (F-04). (3) `aw rename plans` DOES NOT REACH THE DAMAGE THE ITEM NAMES: its rewriter keys on the full filename and on the `.ipd`-bearing whole stem, and all three propagated citations cite the FACET-LESS stem, so the preview lists SEVEN files and none of them is `DECISIONS.md`, the spec, or the research README (F-06). That inverts the item's premise that `aw rename plans` "updates name-based references" for this case. (4) A FOURTH CASUALTY IS UNRECORDED: the tracked `tests/fixtures/derive_plan_status_baseline.json` is keyed by PATH, and the rewriter scans no `.json`, so a rename silently drops one baseline entry while the guard still passes at 731 against its floor of 700 (F-07).

## Goal

Make the one record in this corpus whose filename asserts a false date assert its real one, and leave every citation of it correct, so the date `20260723` stops being recoverable only from git.

The repair is performed through the tooled, sanctioned route for a terminal-plan rename, and the plan's recorded CONTENT is left untouched apart from the single malformed metadata value that caused the defect and that the tool must read to do the repair.

WHAT THIS GOAL DELIBERATELY DOES NOT CLAIM, stated so it is not read as the code fix it is not. It repairs ONE ARTIFACT and no code path, so `plans_refs._plan_date` still fabricates `20260101` for the next malformed plan (that is `949enf`, approved and unexecuted), `plans_archive._plan_date` still does too (`dkfthf`), `aw ipd lint` still reports nothing for a malformed `- Date:` (`fqcax0`), and nothing yet compares a filename date against its own metadata (`mt6j1p`). It also does NOT fix the reference-rewriter blindness that forces three of its edits to be made by hand; it works around it and records the gap as OQ-02 so the next renamer of a facet-less-cited record is not surprised by it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: baseline and the enabling metadata correction

- [ ] E-01 CAPTURE THE PRE-CHANGE BASELINE, so every later claim is a comparison and not an assertion. Save under `/tmp/opencode/tf4jz5-baseline/`: the full citation census `git grep -n '20260101-instsafe-07-qrokie'` (31 occurrences across 20 files at authoring); the rename PREVIEW `python3 -m agent_workflows group plans qrokie --set instsafe --rename --order 7` (which at HEAD prints only a Set/Order no-op line, see F-04); `python3 -m agent_workflows check plans --agent`; `python3 -m agent_workflows ipd lint` on the target file; and `python3 -m pytest -o addopts="" tests/test_history_order.py -q -k Derivation` with its `Compared N paths` line (732 at authoring).
  RECORD THE REAL DATE'S PROVENANCE IN THE SAME PASS, because it is the single fact the whole repair rests on and it lives only in git: `git log --diff-filter=R --follow --name-status -- <the target path>` shows `R099` from `.agents/plans/executed/20260723-1100-07-clean-delta-and-tracking-modes-design-spec.md` in `05c4deb1` (2026-08-08, "back-fill Id + cluster the plan corpus"). Save that output. If it does NOT show `20260723`, STOP: the premise of this plan is the old filename, and without it there is no evidence for the date to restore.
  - Depends on: none
  - Expected outcome: Baseline files written; the 31/20 citation census recorded; the `Compared N paths` number recorded; the `R099` rename record from `05c4deb1` saved showing the `20260723` source name.
  - Execution state: pending

- [ ] E-02 CORRECT THE MALFORMED `- Date:` LINE IN THE TARGET PLAN, from `- Date: 2026-07-23 (fleshed 2026-07-26 from research)` to `- Date: 2026-07-23`, and do it BEFORE any rename. This is NOT cosmetic and NOT optional: it is the step that makes a tooled repair exist at all. Measured through the real CLI on a copy carrying the production string verbatim, `aw group plans qrokie --set instsafe --rename --order 7` previews NO rename, because `_DATE_RE` is anchored (`(?m)^- Date:\s*(\d{8}|\d{4}-\d{2}-\d{2})\s*$`) and the trailing parenthetical defeats it, so `_plan_date` returns the same `20260101` the filename already has and the planned name equals the current one. With the line corrected, the identical command previews `-> 20260723-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md` (F-04, both halves driven).
  PRESERVE THE DISPLACED FACT RATHER THAN DELETING IT. The parenthetical records real history (the stub was authored 2026-07-23 and fleshed into a spec 2026-07-26) and that history is ALREADY recorded, verbatim and in more detail, in the plan's own `## Workflow history` ("2026-07-26 fleshed to a design spec from research"). So the information is not lost by this edit; confirm that history line is present before making it, and if it is absent, STOP and report rather than discarding the only copy of a fact.
  THIS IS THE ONLY BYTE OF THE EXECUTED PLAN'S BODY THIS PLAN MAY CHANGE. Do not touch its `## Workflow history`, its items, its evidence, its `- Status:`, or any other metadata value. AGENTS.md forbids changing what an executed plan RECORDS; a malformed metadata VALUE that contradicts the plan's own history is not a record of anything, and correcting it is what lets the tool read the date the plan itself states. Do not append a history line to this plan either: the record of this repair belongs in THIS plan's history, not in the repaired one's.
  - Depends on: E-01
  - Expected outcome: The target plan's `- Date:` reads exactly `- Date: 2026-07-23`; its `## Workflow history` is byte-unchanged and still carries the 2026-07-26 fleshing record; `git diff` on that file shows exactly one changed line.
  - Execution state: pending

### Task group 2: the tooled rename

- [ ] E-03 PREVIEW THE RENAME AND CLASSIFY EVERY PROPOSED REWRITE BY OPENING IT, before applying anything. Run `python3 -m agent_workflows group plans qrokie --set instsafe --rename --order 7` and save the preview. Expect it to name SEVEN citing files (measured at authoring via `plans_refs.plan_reference_rewrites_with_warnings` on the exact old/new name pair): four live records that are KEEP (`tk1gqo`, `jhrao5`, `5h8u3z`, `mt6j1p`), this repair's own backlog item `tf4jz5`, and two pending plans (`949enf`, `fqcax0`). Classify each occurrence KEEP when the text names THIS plan's file, and LEAVE when it is pasted evidence, a historical `.agents/` path, or a measurement transcript whose value was true when recorded.
  THE TWO PENDING PLANS ARE A JUDGEMENT CALL, SO MAKE IT EXPLICITLY RATHER THAN BY DEFAULT. `949enf` and `fqcax0` cite the old name as the MEASURED CASUALTY of a defect, inside findings and open-question prose. Rewriting them to the new name would make each read as if the defect produced `20260723`, which is the opposite of what each measured. Classify every occurrence in both as LEAVE and restore them after the apply. The same reasoning applies to this plan's own backlog item `tf4jz5`, whose Summary and body state the fabricated name as the defect.
  USE `--order 7` EXPLICITLY, matching the plan's existing `- Order: 7`. Omitting it also preserves the Order (`plan_set_assign` reads `None` as "preserve", per `_preserved_order`), but stating it makes the intent legible and removes any dependence on that behavior. Pass `--set instsafe`, the plan's existing terse Set id, so the Set is a no-op: `plans_index.set_terse_id` on its `- Set: instsafe (install safety and ownership)` returns `instsafe`, and `_set_metadata` will rewrite the line to the bare terse form, which is an expected and sanctioned one-line metadata change.
  - Depends on: E-02
  - Expected outcome: A saved preview showing `would rename ... -> 20260723-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md` plus its per-file rewrite lines; every occurrence classified KEEP or LEAVE in writing, with the LEAVE set naming `949enf`, `fqcax0` and `tf4jz5` and the reason for each.
  - Execution state: pending

- [ ] E-04 APPLY THE RENAME AND RESTORE EVERY LEAVE OCCURRENCE. Run `python3 -m agent_workflows group plans qrokie --set instsafe --rename --order 7 --apply --no-commit`, then immediately restore each occurrence classified LEAVE in E-03 to its pre-rename text, verified line by line against the saved preview. Use `--no-commit` so this plan's own commit is path-scoped and authored here rather than by the verb's self-commit offer.
  DO NOT USE `--no-refs` TO AVOID THE RESTORE WORK. That flag suppresses ALL rewrites, including the four KEEP records that must change, so it converts a precise repair into a dangling-citation event in four live records.
  EXPECT THE GENERATED MANIFESTS TO BE REWRITTEN AND DO NOT COMMIT THEM. `apply_renames` regenerates `.aw/records/plans/INDEX.json`/`INDEX.md`, both gitignored generated views; they are deliberately outside this plan's `- Scope-Paths:`. `STATUS.md` is likewise generated and gitignored (verified with `git check-ignore`), so its two stale `20260101-...-design-spec.md` lines need no edit and must not be hand-corrected.
  - Depends on: E-03
  - Expected outcome: The file is at `.aw/records/plans/executed/20260723-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md` with its `- Id: qrokie` unchanged; the four KEEP records cite the new name; every LEAVE occurrence is byte-identical to its pre-rename text; no manifest file is staged.
  - Execution state: pending

### Task group 3: the three citations the tool cannot reach, and the fourth it cannot see

- [ ] E-05 HAND-CORRECT THE THREE FACET-LESS CITATIONS, which are exactly the damage the backlog item names and exactly what the rewriter structurally cannot reach (F-06). In `DECISIONS.md` (D109's `**Applied:**` line, "Executed per IPD 20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec"), in `.aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md` (its `2026-08-08 migrated (aw specs)` history line, "produced by IPD `20260101-instsafe-07-qrokie-...-design-spec`"), and in `.aw/records/research/20260726-0054-aw-delivery-and-clean-delta-research/README.md` (line 5, "IPD `20260101-instsafe-07-qrokie-...-design-spec`"), replace the `20260101` date segment with `20260723`. One occurrence each, measured.
  WHY THE TOOL MISSES THESE, so the hand edit is understood as a workaround and not as sloppiness: `artifact_refs.plan_reference_rewrites_with_warnings` builds exactly two keys from the name pair, the FULL filename (`...-design-spec.ipd.md`) and the whole stem INCLUDING the type facet (`...-design-spec.ipd`). All three citations end at `-design-spec`, with no `.ipd` and no `.md`, so neither key matches and `_boundaried` finds nothing. Verified directly: the facet-less citation string contains neither key.
  CORRECTING A SPEC'S AND A DECISION'S HISTORY LINE IS THE CORRECT ACT HERE, not a violation of their immutability. Each line's claim is "this spec was produced by the IPD named X"; X is a FILENAME, the filename is changing in this same commit, and leaving it would make all three dangle. This edits an identifier, not a recorded fact or a date either record asserts about itself. Do NOT change either record's `- Status:`, and do NOT append a history line to the spec: its own history is not what this plan did.
  - Depends on: E-04
  - Expected outcome: Three files each showing exactly one changed line, `20260101` -> `20260723` inside the cited plan name; no other byte changed in any of the three; `git grep -c` confirming zero remaining facet-less `20260101-instsafe-07-qrokie` citations in them.
  - Execution state: pending

- [ ] E-06 RE-KEY THE ONE BASELINE FIXTURE ENTRY, the fourth casualty and the only one that is a TEST rather than prose. `tests/fixtures/derive_plan_status_baseline.json` is keyed by repo-relative PATH and carries `".aw/records/plans/executed/20260101-instsafe-07-qrokie-...ipd.md": "executed"`. The rewriter cannot see it: `artifact_core._REFERENCE_TEXT_SUFFIXES` is `('.md', '.txt', '.py')`, so no `.json` is ever scanned. Change that ONE key's date segment to `20260723`, leaving its value `"executed"` and every other entry byte-unchanged.
  THE FAILURE MODE THIS PREVENTS IS SILENT, WHICH IS WHY IT NEEDS ITS OWN ITEM. `tests/test_history_order.py::DerivationIsUnchangedTests` intersects the live terminal tree with the baseline keys and asserts `>= 700`. Measured: the intersection is 732 today, and after an unrepaired rename it is 731, so the guard KEEPS PASSING while silently covering one plan fewer. Nothing reports it. (Plan `rlcq7g`, approved, re-keys this fixture by id6 and would make this class of edit unnecessary in future; it is NOT a dependency here, since this plan's single-entry edit is correct against the fixture as it exists today and stays correct under either shape.)
  - Depends on: E-04
  - Expected outcome: Exactly one key changed in the fixture, JSON still parses, `len(baseline)` unchanged at its pre-change count, and the `Compared N paths` number from the Derivation test equal to E-01's baseline rather than one lower.
  - Execution state: pending

- [ ] E-07 RECONCILE THE WHOLE CITATION CENSUS AND PROVE NOTHING DANGLES, as a separate pass from the edits, because this plan touches nine paths through three different mechanisms (tooled rewrite, hand edit, fixture edit) and a missed occurrence is invisible without a whole-tree re-census. Re-run E-01's `git grep -n '20260101-instsafe-07-qrokie'` and account for EVERY surviving occurrence as a deliberate LEAVE, naming its file and reason. Also run `python3 -m agent_workflows check plans --all --agent` and `python3 -m agent_workflows sanitize --agent`, and compare the findings against E-01's baseline.
  THE EXPECTED SURVIVING SET IS NON-EMPTY AND THAT IS CORRECT, so do not drive this to zero. At authoring the deliberate LEAVE set is: `949enf` (4), `fqcax0` (2), `tf4jz5` (4), `ribg85` (3), `rlcq7g` (1), `h8e3sm` (1) and its review (1), the `wslayout` review (2), executed `63h054` (1, inside a fenced evidence block), executed `9zvl2w` (1, inside a fenced terminal-output block), and the two generated `STATUS.md` lines. Each is pasted evidence, a historical measurement, or a defect description whose subject IS the wrong name. If a count differs from this table, say so and explain which way.
  - Depends on: E-05, E-06
  - Expected outcome: A written census reconciliation accounting for every surviving occurrence; `check plans --all` showing no NEW finding versus baseline; `sanitize --agent` clean; zero dangling citations of the old name in any record that was meant to point at the file.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A TERMINAL PLAN'S NAME IS MUTABLE BY DESIGN while its body is not, and this is stated explicitly rather than inferred: `.aw/records/plans/README.md` says "Set membership/order changes on a plan already in a terminal directory are a deliberate, tool-driven, citation-safe act (the plan BODY and workflow history stay immutable; only the name/grouping is mutable via the stable `Id`)". That sentence is the authority for this plan existing at all, and it is what distinguishes this repair from the thing AGENTS.md forbids.
- CITE CODE BY SYMBOL, not by offset (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every code citation in this plan names a module function or a quoted content string: `plans_refs._plan_date`, `plans_refs._DATE_RE`, `plans_refs.plan_set_assign`, `plans_refs.run_mv`, `plans_refs._preserved_order`, `plans_refs.apply_renames`, `artifact_refs.plan_reference_rewrites_with_warnings`, `artifact_refs._whole_stem`, `artifact_refs._boundaried`, `artifact_refs._mask_fenced_code`, `artifact_core._REFERENCE_TEXT_SUFFIXES`, `artifact_naming._CLUSTERED_RE`, `plans_index.set_terse_id`, `hooks.executed_transition_gate`.
- THE GENERATED MANIFESTS ARE GITIGNORED AND MUST NOT BE COMMITTED (`idxuntrack`): `.aw/records/plans/INDEX.json`, `INDEX.md` and `STATUS.md` are all regenerated views, verified with `git check-ignore`. `apply_renames` rewrites them as a side effect, which is why this plan commits a path-scoped set rather than everything the verb touched, and why `STATUS.md`'s two stale citations are deliberately left alone.
- A RENAME LEDGER RECORD IS WRITTEN AUTOMATICALLY AND IS NOT COMMITTABLE EITHER: `apply_renames` calls `record_history.record_rename`, which appends to `.aw/records/history.jsonl`, a gitignored, non-authoritative sidecar whose emit is failure-isolated. Nothing in this plan depends on it.
- THE REFERENCE REWRITER MASKS FENCED CODE before matching (`artifact_refs._mask_fenced_code`), which is why two executed plans that cite the old name inside pasted evidence blocks are correctly absent from the rewrite set rather than needing a manual revert. Verified per file: the `63h054` occurrence is 1 raw hit and 0 after masking.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | THE DEFECT AND THE REAL DATE ARE BOTH CONFIRMED AT THIS HEAD. The target carries `- Date: 2026-07-23 (fleshed 2026-07-26 from research)` while its filename reads `20260101`, and the real date was present in the name the bulk migration discarded. | `git log --diff-filter=R --follow --name-status` on the target: `R099 .agents/plans/executed/20260723-1100-07-clean-delta-and-tracking-modes-design-spec.md -> .agents/plans/executed/20260101-instsafe-07-qrokie-...md` in `05c4deb1` (2026-08-08). It is the ONLY `20260101-` name in `.aw/records`. |
| F-02 | THE ITEM'S FIRST STATED BLOCKER DISSOLVES ON READING THE README: a terminal plan's NAME is explicitly declared mutable while its body is not, so the sanctioned route exists and AGENTS.md's immutability rule is not in tension with it. | `.aw/records/plans/README.md`, quoted verbatim in Step 0: "only the name/grouping is mutable via the stable `Id`". |
| F-03 | THE ITEM'S SECOND STATED BLOCKER IS FALSE AS A HARD BLOCK: the `ipd-executed-gate` hook does NOT refuse this rename. I staged the real `git mv` in this lane and drove the real hook. It exits 0, because its `moved_into_executed` predicate exempts a path that was ALREADY in `executed/` at HEAD under the SAME `- Id:` (the `i4c0c3` exemption), and its `gained_executed` predicate is False since the HEAD blob already had `- Status: executed`. | `git mv` to the new name, then `git diff --cached --name-status -M` showing `R100`, then `python3 -m agent_workflows ipd-executed-gate` -> `RC=0`. `ipd-status-untooled-gate` also returns 0. Both re-staged back afterwards; the tree was left clean. |
| F-04 | `aw rename plans` CANNOT DO THIS REPAIR, AND `aw group plans --rename` CANNOT EITHER UNTIL THE `- Date:` IS FIXED. This corrects the item's assumption that `aw rename plans` is the route. `run_mv` derives the new date from the CURRENT filename via `_CLUSTERED_RE`, which MATCHES this name and yields `20260101`, so the planned name equals the current one and nothing is renamed. `plan_set_assign` instead calls `_plan_date(text)`, which reads front matter, and the production `- Date:` is malformed against the anchored `_DATE_RE`, so it also returns `20260101`. Correcting that one line makes the `group` route work. | Driven in a throwaway repo seeded with the real file. Malformed: `group plans qrokie --set instsafe --rename --order 7` prints only `would set Set=instsafe Order=07`. `rename plans --id qrokie [--slug ... --set ...]` likewise prints only the Set/Order line. After correcting the `- Date:` to `2026-07-23`, the identical `group` command prints `would rename ... -> 20260723-instsafe-07-qrokie-...ipd.md`, and `--apply` performed it. `_CLUSTERED_RE.match(name).group('date')` is `'20260101'`; `_plan_date(real_text)` is `'20260101'` with `_DATE_RE.search` returning `None`. |
| F-05 | THE ORDER OF OPERATIONS IS LOAD-BEARING AND INTERACTS WITH AN APPROVED PLAN. `949enf` (approved, unexecuted) adds a FILENAME-FIRST date tier to both verbs. Prototyped against this exact name, that tier returns `20260101` from the filename and never consults the corrected front matter, so after `949enf` lands the `group --rename` route reproduces the fabricated date even WITH `- Date:` fixed, and neither verb has a `--date` flag to override it (the `research` verbs do; the `plans` verbs do not). | Prototyped `949enf` E-03's specified tiers over this name: corrected front matter yields `20260723` TODAY via `plan_set_assign` but `20260101` AFTER the fix. `rename plans --help` and `group plans --help` both show no `--date`. |
| F-06 | THE TOOL DOES NOT REACH THE DAMAGE THE ITEM NAMES. The rewriter builds exactly two keys, the full filename and the whole stem WITH the `.ipd` facet. All three propagated citations end at `-design-spec`, facet-less, so neither key matches. The preview names SEVEN files and NONE of them is `DECISIONS.md`, the spec, or the research README. This is the single most consequential correction to the item, which assumed `aw rename plans` "updates name-based references". | `plan_reference_rewrites_with_warnings` on the exact old/new pair returns edits in 7 files (`tk1gqo`, `jhrao5`, `5h8u3z`, `tf4jz5`, `mt6j1p`, `949enf`, `fqcax0`) with zero warnings; membership tests for `DECISIONS.md`, the spec and the research README are all False. `_whole_stem(old)` is `...-design-spec.ipd`; the facet-less citation contains neither it nor the full name; `_boundaried(whole_stem).search(citation)` is falsy. |
| F-07 | A FOURTH CASUALTY IS UNRECORDED ANYWHERE, AND IT FAILS SILENTLY. The tracked fixture `tests/fixtures/derive_plan_status_baseline.json` keys this plan by PATH, and the rewriter scans no `.json`, so an unrepaired rename drops one baseline entry. The guard still PASSES, because 731 clears its floor of 700. Nothing reports the lost coverage. | `artifact_core._REFERENCE_TEXT_SUFFIXES == ('.md', '.txt', '.py')`. Baseline has 777 keys, the live terminal tree 931 files, intersection 732 including this plan (value `"executed"`); simulating the rename gives 731, `>= 700` still True. `pytest -k Derivation` passes today printing `Compared 732 paths`. |
| F-08 | THE CITATION CENSUS IS 31 OCCURRENCES ACROSS 20 FILES, and most are correctly LEAVE. Four live records are KEEP; three are the facet-less hand-edit set; one is the fixture; two are generated `STATUS.md` lines needing nothing; and the remainder are defect descriptions, measurement transcripts, or fenced evidence whose subject IS the wrong name. | `git grep -n '20260101-instsafe-07-qrokie'` enumerated per occurrence with its matched token form: 13 full-name, 8 bare-prefix, 6 elided `-...`, 5 facet-less-stem, 2 `.md`-without-`.ipd`. |
| F-09 | THE TWO EXECUTED-PLAN CITATIONS NEED NO MANUAL REVERT, because fence masking already protects them. This is a negative finding that removes two files from the risk surface. | `_mask_fenced_code` on `63h054` takes its hits 1 -> 0; `9zvl2w`'s occurrence is inside an ANSI terminal-output fence and is 0 even unmasked (it cites the bare prefix, not a name key). Neither appears in the F-06 edit set. |
| F-10 | THE SET/ORDER CHANGE IS A GENUINE NO-OP AND WILL SHOW AS A ONE-LINE DIFF. `--set instsafe` matches the plan's existing terse Set id, but `_set_metadata` rewrites the `- Set:` line to the bare terse form, dropping the descriptive parenthetical. | `plans_index.set_terse_id('instsafe (install safety and ownership)')` is `'instsafe'`. In the throwaway apply the line became `- Set: instsafe` and `- Order: 7` was preserved. |

## Proposed changes (ordered, validatable)

1. Correct the single malformed `- Date:` value in the target executed plan (E-02), which is the precondition that makes any tooled rename possible (F-04).
2. Preview the rename, classify all seven citing files, apply it with `--no-commit`, and restore the LEAVE occurrences (E-03, E-04).
3. Hand-correct the three facet-less citations the rewriter cannot reach: `DECISIONS.md`, the deferred spec, the research bundle README (E-05, F-06).
4. Re-key the single affected entry in `tests/fixtures/derive_plan_status_baseline.json` (E-06, F-07).
5. Re-census every remaining occurrence and prove nothing dangles and no new check finding appeared (E-07).

## Deferred / out of scope (with reason)

- THE TWO `20260101` FABRICATORS THEMSELVES. `plans_refs._plan_date` is `949enf` (approved, unexecuted) and its copy in `plans_archive._plan_date` is `dkfthf`. This plan repairs ONE ARTIFACT and deliberately changes no behavior, exactly as `949enf` deliberately repaired no artifact. Keeping the split means each half's effect is attributable.
  - Carrier: dkfthf
- THE TWO DETECTION GAPS THAT LET THE WRONG DATE SIT UNREPORTED. A malformed `- Date:` draws no lint diagnostic (`fqcax0`, graduating `5h8u3z`), and nothing compares a filename date against the plan's own metadata (`mt6j1p`). Either would have caught this record years earlier; neither is changed here, because this plan asserts nothing about any OTHER record and a detector is a corpus-wide behavior change.
  - Carrier: mt6j1p
- FIXING THE FACET-LESS-STEM BLINDNESS in `artifact_refs.plan_reference_rewrites_with_warnings` (F-06, OQ-02). This plan works around it with three hand edits. Widening the matcher would change what EVERY rename of EVERY artifact type rewrites across the whole corpus, which is a far larger blast radius than this repair, and getting it wrong rewrites text that must not change. Filed at authoring so the gap is tracked rather than absorbed.
  - Carrier: xp6o3v
- RE-KEYING THE BASELINE FIXTURE BY id6 rather than by path. That is `rlcq7g` (approved) and it would make E-06 unnecessary in future. It is not a dependency: a one-entry path edit is correct against today's fixture and remains correct whichever way `rlcq7g` goes.
  - Carrier: rlcq7g
  - Carrier-Evidence: .aw/records/plans/executed/20260929-p0a5kr-01-rlcq7g-key-the-derive-plan-status-baseline-by-plan-id6-so-a-termina.ipd.md
- THE TWO STALE `STATUS.md` CITATIONS. It is a generated, gitignored view (`git check-ignore` confirms) that is already stale in other ways (it reports 194 plans where the tree holds over 900), and `aw index plans` regenerates it from the renamed corpus. There is nothing for a carrier to own: hand-editing a generated file would be overwritten, and the regeneration needs no tracking.
  - Carrier-Declined: a generated gitignored view, corrected by `aw index plans` from the renamed corpus; no durable work remains to hand off.
- ANY OTHER RECORD'S NAME OR DATE. 98 plans in this corpus have names whose slot token is not a real id6 and others carry oldest-first histories; none of that is this plan's business, and each already has its own item where it matters (`jhrao5` for the history order). This plan touches the ONE record whose filename date is a fabricated constant, which is a closed set of one measured at authoring.
  - Carrier-Declined: a deliberate scope boundary rather than deferred work; the one record in the class is repaired here and the other naming classes are separately owned.

## Scope check

- Over-scope: none. All nine declared paths are modified: the target plan (renamed, one metadata line), the four tool-rewritten KEEP records (`tk1gqo`, `jhrao5`, `5h8u3z`, `mt6j1p`), the three hand-corrected facet-less citers (`DECISIONS.md`, the spec, the research README), and the fixture.
- Under-scope, stated as a declaration for the finalize reconciliation rather than as a stop directive: the tool will also rewrite THREE files this plan deliberately does NOT declare, because every occurrence in them is classified LEAVE and will be restored, so their net diff is empty: `tf4jz5`'s own backlog item, pending plan `949enf`, and pending plan `fqcax0`. Do NOT add them to `- Scope-Paths:` to make a reconciliation tidier; a file whose content is restored byte-for-byte is not a scope member. The target plan's own file is renamed, so the finalize scope gate sees both a delete and an add path for it; that is the normal shape of a tooled rename and is covered by the single declared entry.
- Also deliberately undeclared and unmodified: `.aw/records/plans/INDEX.json`, `INDEX.md`, `STATUS.md` (generated, gitignored, rewritten by the verb as a side effect) and `.aw/records/history.jsonl` (gitignored ledger). None may be staged.

## Required tests / validation

- No new test is authored, and that is a deliberate choice rather than an omission: this plan changes no code, so there is no behavior to pin. A test asserting that one record's filename contains `20260723` would pin a FILENAME, which is the code-structure-pinning class GUIDING_PRINCIPLES P16 forbids, and would break the next legitimate regroup of that plan. The code-side guards belong to `949enf` (which restores the deleted date-regression coverage for both verbs) and to `fqcax0` (which adds the lint rows).
- The full suite must pass: `python3 -m pytest`, run bare. The specific guard this plan could plausibly disturb is `tests/test_history_order.py::DerivationIsUnchangedTests`, whose `Compared N paths` number must equal its pre-change value rather than being one lower (F-07), which is exactly what E-06 protects and V-06 proves.
- `python3 -m agent_workflows check plans --all --agent` must show no NEW finding against the E-01 baseline, and `python3 -m agent_workflows sanitize --agent` must be clean.
- `python3 -m agent_workflows ipd lint` on the renamed target must not regress: it returns the `legacy` disposition for a plan in `executed/` before any metadata check runs, so the `- Date:` correction cannot change its verdict; confirm that rather than assume it.

## Spec / documentation sync

No spec is amended and no `.spec.md` is declared for a CONTRACT change, because this plan changes no behavior any spec describes. The ONE spec file in `- Scope-Paths:` is `.aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md`, declared solely because E-05 corrects a stale FILENAME inside one of its history lines; its `- Status:`, its criteria and every normative statement in it are untouched. It is declared explicitly so both runners announce the spec edit before the run and the finalize reconciliation sees it, per AGENTS.md's "a plan may amend a spec, and must declare it".

`DECISIONS.md` is edited for the same reason: one stale filename inside D109's `**Applied:**` line. No new decision is recorded, because no decision is being made that is not already recorded in this plan and in the backlog item.

## Open questions

### OQ-01: Should this repair be performed at all, or should the wrong name stand as recorded history?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED IN FAVOUR OF REPAIR, from repository evidence rather than deferred back to the maintainer, because both reasons the backlog item gave for hesitating were measured and neither holds. The item's own framing was "RENAME with reference rewriting, or LEAVE it as recorded history and accept that one plan's name lies about its date". AGAINST repair, and the strongest argument: it rewrites a committed record's name. FOR repair, and decisive: `.aw/records/plans/README.md` explicitly declares a terminal plan's name mutable while its body is immutable, and names a tooled citation-safe verb as the way to do it (F-02), so this is a sanctioned operation rather than a violation; the `ipd-executed-gate` hook, which the item believed would block it, returns rc 0 on the real staged rename (F-03); and the "accept it" branch is worse than the item assumed, because the wrong date is not confined to one filename but has propagated into three live records and one tracked test fixture, all of which assert it, and the fixture one degrades a guard silently (F-07). The deciding consideration is that the record's own body states `2026-07-23`, so the name contradicts the document it names; repair makes them agree, where leaving it preserves a contradiction in four more places. NON-BLOCKING either way: nothing is broken while it stands, which is why the item is `chore`/low with no release gate, and why this plan is safe to defer or decline without consequence.

### OQ-02: Should `artifact_refs` learn the facet-less stem so a rename reaches citations like these three?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: xp6o3v
- Resolution or deferral rationale: DEFERRED TO THE MAINTAINER AND DELIBERATELY NOT ACTED ON, because it is a change to a corpus-wide matcher and not to this one record. FILED AS BACKLOG `xp6o3v` at authoring so the gap is tracked in the backlog rather than only in this plan's prose, carrying the measurement below plus the `.json`-suffix blind spot from F-07. F-06 measures that `plan_reference_rewrites_with_warnings` builds only a full-name key and a facet-BEARING whole-stem key, so a citation ending at `-design-spec` is unreachable; that is why three of this plan's edits are made by hand. Adding a facet-less key would make every future rename of every artifact type rewrite a broader set of occurrences, which cuts both ways: it would have caught these three, and it would also match prose that names a SLUG rather than a file, where a rewrite is wrong. Deciding that trade needs a corpus measurement of how often a facet-less stem appears and how often it means the file, which is a research-shaped question and not a side errand of a one-record repair. NOT BLOCKING: the three edits are small, enumerated and verifiable by hand, so this plan completes correctly whichever way the question later goes. RECORDED HERE SO THE NEXT RENAMER OF A FACET-LESS-CITED RECORD IS NOT SURPRISED BY IT, since the preview's silence looks exactly like "no citations to fix".

### OQ-03: Must this plan execute before `949enf`, and what happens if it does not?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS A SEQUENCING NOTE, NOT AS A DEPENDENCY EDGE, and `- Item-Dependencies:` is deliberately `none`. F-05 measures that `949enf`'s filename-first date tier returns `20260101` for THIS name and never consults the corrected `- Date:`, so once `949enf` lands the `aw group plans --rename` route reproduces the fabricated date and neither plans verb carries a `--date` override. So executing this plan BEFORE `949enf` is materially easier. It is NOT expressed as a dependency for two reasons. First, the grammar cannot express it: the only available edges are `executed:<id6>`, `exists:` and `state:`, all of which assert that a target IS in a state, and what is wanted here is the opposite, "not yet executed", which no edge kind encodes. Second, asserting `executed:949enf` would be false and harmful, since it would force this plan to run only AFTER the change that makes it hard. IF `949enf` LANDS FIRST, this plan is still executable: the repair becomes a plain `git mv` plus the same four reference-rewrite groups done by hand, and F-03's measurement that the executed-transition hook permits the staged rename is what makes that route safe. Say so in the execution report rather than silently switching routes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the `git log --diff-filter=R --follow --name-status` output showing the `R099` record in `05c4deb1` with `20260723-1100-07-...` as the source name, and paste the occurrence COUNT from `git grep -c` style census (expected 31 occurrences across 20 files; state both numbers as measured, not as quoted from this plan). Paste the `Compared N paths` line from the Derivation test.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste `git diff -- <target path>` showing EXACTLY ONE changed line, the `- Date:` correction, and paste `grep -c 'fleshed to a design spec from research' <target>` returning 1 to prove the displaced fact still exists in the plan's own history. Then paste, as the falsifiable proof that this edit was NECESSARY rather than cosmetic, the `group plans ... --rename` PREVIEW run twice: once on the pre-edit content showing NO rename line, and once after showing `would rename ... -> 20260723-...`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the saved preview in full, and paste the written KEEP/LEAVE classification naming all seven files. The classification must state, per file, which it is and why. Prove the LEAVE judgement on `949enf`/`fqcax0`/`tf4jz5` by quoting one occurrence from each showing the old name used AS THE DEFECT'S SUBJECT, which is what makes rewriting it falsify a measurement.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `git status --porcelain` and `git diff --cached --name-status -M` showing the `R` record for the rename to `20260723-...`, and paste `grep -n '^- Id:' <new path>` showing `qrokie` unchanged. Paste `git diff --stat` for the three LEAVE files showing ZERO lines changed in each after restoration (a nonzero stat there means a restore was missed). Paste `git check-ignore -v` for `INDEX.json`, `INDEX.md` and `STATUS.md` together with proof none is staged.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste `git diff` for each of the three hand-edited files showing exactly one changed line each, old `20260101` segment to `20260723`. Then paste `git grep -n '20260101-instsafe-07-qrokie' -- DECISIONS.md '.aw/records/specs' '.aw/records/research'` returning NOTHING, which is the falsifiable proof the facet-less class is cleared. Confirm the spec's `- Status:` line is unchanged by pasting it.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the one-line fixture diff. Paste `python3 -c` output showing the baseline still parses and `len()` is unchanged from E-01's number. Then paste `python3 -m pytest -o addopts="" tests/test_history_order.py -q -k Derivation` PASSING with its `Compared N paths` line, and state explicitly that N EQUALS E-01's baseline N rather than being one lower. N being one lower is the exact silent failure this item exists to prevent and must be reported as a failure, not accepted because the test still passes.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste the final census reconciliation accounting for every surviving occurrence by file with its LEAVE reason, and state any divergence from F-08's table in either direction. Paste `check plans --all --agent` and `sanitize --agent` outputs compared against the E-01 baseline, naming any new finding. Paste the BARE `python3 -m pytest` summary line showing the `N passed` count.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY the paths this plan declares, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push, and never `--no-verify`. Verify the staged set with `git diff --cached --name-only` before every commit, and re-verify after any failed raw commit attempt, since a rejected hook can leave paths in the index that you never staged. This lane is a shared checkout: do not revert, stage or clean any change you did not make.

HOOKS MUST RUN AND ARE EXPECTED TO PASS. F-03 measured `ipd-executed-gate` returning rc 0 on the real staged rename of this file, and `ipd-status-untooled-gate` likewise. If either REFUSES during execution, STOP and report: a refusal means a premise of this plan is wrong, and the remedy is never `--no-verify`.

DO NOT WIDEN THE REPAIR. Specifically: do not change `plans_refs`, `plans_archive`, `artifact_refs`, `check_engine` or any other module (the code halves are `949enf`, `dkfthf`, `fqcax0`, `mt6j1p`); do not rename any other record; do not edit the `20260101` constant; do not add a facet-less key to the reference matcher (OQ-02); do not hand-edit a generated manifest; do not author a test that asserts a filename (GUIDING_PRINCIPLES P16); and do not touch the target plan's `## Workflow history`, items, evidence or `- Status:`. An out-of-scope edit that proves NECESSARY is to be MADE and then JUSTIFIED (`aw ipd finalize` takes a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path); it is not a reason to stop.

POST-GATE LIFECYCLE. Execution requires explicit human approval recorded through `aw ipd set approved <id6>`. On completion, every `V-*` must carry pasted evidence and `aw ipd lint --phase pre-transition` must report conforming before `aw ipd finalize` moves this plan to `.aw/records/plans/executed/`. Do not claim done while any `V-*` is pending.
