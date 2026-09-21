# IPD: Bound identity extraction to the metadata region so a quoted example id6 cannot claim a document

- Date: 2026-09-08
- Kind: child
- Concern: `selectors._ID_RE` is multiline and unanchored to position, so ANY `- Id: <id6>` line anywhere in a file claims that file's identity. A document that merely QUOTES an example metadata block is therefore read as ASSERTING the quoted id6, which collides with the real artifact and makes it unaddressable by the status verbs, with the refusal explicitly stating it is not overridable by `--force`. The trigger is ordinary prose (quoting the metadata format), so the documents most likely to break the tool are specs and research ABOUT `aw` itself. `_read_status` and `_read_setid` share the same whole-body scan and the same defect.
- Scope: Bound identity extraction to the artifact's METADATA REGION (the front-matter bullet block before the first `##` heading) for id6, status and setid alike; ADD a check rule reporting a metadata-shaped `- Id:` found outside that region so bounding surfaces the ambiguity rather than silently swallowing it (maintainer decision 2026-09-05: fix AND warn); and consolidate the near-duplicate `_FRONT_MATTER_ID_RE` so a fix cannot land in one reader and not the other. The fix is in the READER; the quoted example is legitimate cited content and must not be mangled.
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/check_engine.py, tests/test_selector_zero_open.py, tests/test_id_metadata_region.py
- Item-Dependencies: none
- Status: executed
- Blocks-Release: next
- Readiness: go-pending-approval
- Set: idcapture
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 76w6mq
- From-Backlog: cqytxf

## Workflow history
- 2026-09-21 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: 76w6mq verified (set idcapture, attempt 1).
- 2026-09-21 executed (opencode its_direct/pt3-claude-opus-5-1m-us): EXECUTED under `aw oc run` (run-20260921T024711Z-3450078, lane worktree). All seven E-items performed, all seven V-items verified with pasted evidence; `aw ipd lint --phase pre-transition` conforms. THE DEFECT IS FIXED AND THE FIX IS WIDER THAN THE PLAN SPECIFIED, because the CHECKER had its own copy of it: `check_engine._ID_LINE_RE`/`_SET_LINE_RE` are byte-identical twins of the selector's patterns applied to WHOLE FILE BODIES, so bounding only `selectors.py` would have left `aw check` asserting an id6 collision that no verb could any longer see - the two-surfaces-disagree shape `check_collisions`' own docstring warns about. Both are now bounded through ONE shared helper, `selectors.metadata_region`. FIVE MEASUREMENT CORRECTIONS a future reader must not inherit from this plan's earlier text, each re-measured rather than copied: (1) the corpus is 1614 tracked records, not 1136 or 1006; (2) header-exhaustion is 25 records, not 85, because `_read_header` is no longer a 4096-byte hard cap but a growing chunked read, so most previously-exhausting files now reach their `##`; (3) `check.id6-collision` went 17 -> 15, not 1 -> 0, the other 15 being pre-existing backlog-vs-`done/` duplicates this plan does not touch; (4) THE BLAST RADIUS IS THREE FILES, NOT TWO - `27rjro`, `takpys` AND the `effzzi` roadmap, which opens with a YAML fence and then carries NARRATIVE `- Set: `awoptimize`` bullets under its H1, so E-01's YAML-fence bound (rather than a "before the first `##`" bound) is what keeps prose out of the region; verified it changes no resolution answer, since `awoptimize` still resolves to the same 4 files by substring; (5) the suite baseline on this worktree is `1 failed, 7661 passed, 3 skipped, 2 xfailed`, and the single failure is the ENVIRONMENTAL `test_turn_bounds.py::test_the_permission_policy_by_contrast_IS_isolation_scoped` (it asserts `OPENCODE_CONFIG_CONTENT` is absent, and my own runner turn sets it; `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` gives `43 passed`), NOT the `test_reporting_contract.py` case review predicted, which does not occur here. AFTER: `1 failed, 7694 passed` = +33, exactly the tests added, zero regressions. ONE PREMISE OF V-04 WAS FALSIFIED AND THE EVIDENCE WAS REBUILT: there is no BEFORE "exit 2" from `aw find plans uyeko5`, because `resolve()` is scoped to ONE type and the collision was CROSS-TYPE (plans id6 vs research id6), so resolution is proven with a per-type census instead. DEFECT FOUND AND REPORTED, NOT CAUSED BY THIS CHANGE: while gathering that evidence I ran `aw ipd set reviewed uyeko5`, expecting the LIFECYCLE refusal review predicted; it did NOT refuse, and instead performed the illegal backwards `executed -> reviewed` transition, rewriting the status and `git mv`-ing an executed plan into `pending/`. I reverted it completely and verified the file is byte-identical to HEAD. `ipd_lifecycle.validate_transition('executed','reviewed')` returns `ok=False`, so the setter is not consulting a predicate it already has; reproduced in a clean throwaway repo and filed as backlog `rrvrwv` (bug, Blocks-Release: next). Also filed: `axayfn` (three identity readers outside this fence still unbounded, `_ITEM_ID_RE` measurably divergent on the same 2 docs though reached by no current call path) and `1dvtiq` (the `warning`-is-not-advisory trap, split out of the Deferred section so it has a durable carrier). Six deferred rows gained carriers: `lmjc8h`, `1dvtiq`, `05aqbj` and three `Carrier-Declined` for rows that are not obligations. NOTE FOR `xo3244`, which overlaps this file: it lands SECOND, so it must consult `metadata_region` rather than adding a second boundary parser.
- 2026-09-18 approved (aw set): status set to approved
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; readiness GO - PENDING HUMAN APPROVAL; PR-201..PR-208, all FIXED, no open questions. Reviewed at HEAD `18d7cc4c`; `aw ipd lint` conformed at `--phase author` and again at `--phase review-finalize`. THE CORE DEFECT IS REAL AND I RE-PROVED IT: `_read_id`/`_read_status`/`_read_setid` on the `27rjro` doc still return `uyeko5`/`reviewed`/`runflags` harvested from a quoted block, and `aw set reviewed uyeko5` still fails with an id6 collision at exit 2. THREE FINDINGS OF THE PLAN'S OWN WERE FALSIFIED and are now marked SUPERSEDED rather than deleted, because the plan leaned on them: F-4/F-5/F-6 claimed `aw check all` reports ZERO id6-collisions and that the repository detector had gone BLIND through retired-record masking. Re-measured, `aw check all` reports exactly ONE `check.id6-collision`, ON the `27rjro` doc, naming a SECOND live research doc (`takpys`) that quotes the same block; so both sides are scannable, nothing is masked, and check and the verbs AGREE. The retired-record mechanism is real but LATENT, and E-06 now says so instead of asserting blindness. PR-201 (HIGH) is the substantive fix: E-05 was told to register the new rule at `warning` severity so the repository would not fail its own check for documenting itself, but `warning` DOES fail the gate (`drift_exit_code` returns 1 for error AND warning, 0 only for `info`, measured), so the instruction defeated its own goal; it now says `info` and cites the two shipped `info` precedents. PR-202 (HIGH): the blast radius is TWO files, not one, so a rule or test keyed on a single doc would ship half-built; verified the region fix repairs both. Also corrected: the file census (1136 tracked, not 1006), a 4096-byte header interaction the region helper must tolerate (85 files have no `##` inside the window), the stale `status: todo` claim (it is `reference`), and E-07's precedence assertion, which as written would have asserted a substring match for a token absent from both filenames. OQ-01 and OQ-02 RESOLVED FROM EVIDENCE rather than left for the maintainer.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `cqytxf`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite being `Priority: high` / `Work-Kind: bug`. THE DEFECT IS FULLY LIVE, re-verified at HEAD `a2e0438a`: `_ID_RE` is unchanged (`selectors.py:111`), the research doc still quotes `- Id: uyeko5` at line 60, `selectors._read_id` on that file still returns `uyeko5`, and `aw set reviewed uyeko5` still FAILS with "Selector 'uyeko5' is a id6 collision matching multiple files (a data bug to fix, not overridable by --force)" naming both the real plan and the research doc, exit 2. ONE PART OF THE ITEM IS NOW MISLEADING AND MATTERS A LOT, because it would make a future reader think the bug was fixed: the item's second measured symptom, `aw check all` reporting `check.id6-collision` on the research doc, NO LONGER REPRODUCES. `aw check all` now reports ZERO id6-collision findings. THAT IS NOT A FIX; IT IS MASKING, and I traced it. `uyeko5` EXECUTED since the item was filed, so its plan moved to `.aw/records/plans/executed/`, and `check_engine._iter_type_files` skips retired records unless `include_retired` is passed (`check_engine.py:493`); measured `check_engine.is_retired(<the executed plan>, 'plans')` is True, and the executed plan is absent from the 70 plans the check scans while the research doc IS among the 76 research files scanned. So the collision has only ONE side visible to `aw check` and cannot be reported, while `selectors.resolve()` does NOT skip retired records and therefore still collides. NET EFFECT, which strictly worsens the item's severity rather than easing it: the repository-level detector is now BLIND to exactly the class of collision that still breaks the verbs. E-05 adds the warning rule the item asked for, which does not depend on both sides being scannable. THE BLAST RADIUS IS MEASURED AND TINY, which de-risks the reader change: scanning all 1006 tracked markdown files under `.aw/records/`, exactly ONE has a metadata-shaped `- Id:` line after its first `##` heading or more than one such line, and it is the `27rjro` research doc. So bounding the scan changes the resolved identity of exactly one file today. CONFIRMED the item's scope point 4: `_read_status` and `_read_setid` share the defect, measured on the same doc, returning `reviewed` and `runflags` harvested from the quoted block rather than from the doc's own YAML front matter.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a quotation a quotation. Identity should come from where an artifact DECLARES it, not from anywhere the pattern happens to match, so writing documentation about `aw`'s own metadata format cannot make a real plan unaddressable.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: bound the region, once, for all three readers

- [x] E-01 Define ONE metadata-region boundary helper in `selectors.py` and express it precisely, because every later item depends on exactly where the region ends. The region is the leading `- Key: value` bullet block BEFORE the first `##` heading; for a YAML-fenced document it is the leading `---` block. Handle the shapes actually present in the corpus rather than assuming one: bullet front matter (plans, specs, backlog, releases, reviews, prompts, walkthroughs) and YAML front matter (research, RE-MEASURED at review: 110 of 117 tracked research files are `---`-fenced, 6 start with `#`, 1 neither; the originally stated 105 of 107 is stale). A file with NO heading at all must still have a region (the whole leading bullet run), and a file whose first line is a `#` H1 title must not have its region truncated by that H1, since `##` is the boundary, not `#`.
  THE HELPER RECEIVES A TRUNCATED 4096-BYTE HEADER, NOT A WHOLE FILE, AND MUST TREAT HEADER-EXHAUSTION AS "REGION CONTINUES" RATHER THAN AS AN ERROR OR AN EMPTY REGION. This is the shape most likely to be got wrong, because it is not an edge case: MEASURED at review, 85 of 1136 tracked records have NO `## ` heading within their first `_HEADER_BYTES` (`selectors.py:317`), so for them "everything before the first `##`" legitimately means the whole window. It is harmless there (their metadata is at the top and no later `- Id:` falls inside the window), but a helper that returned empty, raised, or refused on a missing boundary would break identity extraction for 85 files while fixing 2. VERIFIED the live instance is safe: `27rjro`'s first `## ` sits at byte 1149, well inside the window, with the quoted `- Id:` AFTER it.
  - Depends on: none
  - Expected outcome: a pure helper returning the metadata region's text, correct for bullet front matter, YAML front matter, an H1-then-bullets file, a file with no `##` heading, AND a header truncated mid-region (which must yield the whole window, not empty).
  - Execution state: performed

- [x] E-02 Apply the region to `_read_id` (`selectors.py:246-248`), `_read_status` (`:251-253`) and `_read_setid` (`:304-306`) together, not just to id. The item's scope point 4 asks whether the other two share the defect; RE-MEASURED AT REVIEW (HEAD `18d7cc4c`) ON THE LIVE INSTANCE, THEY DO: on the `27rjro` research doc, `_read_status` returns `reviewed` and `_read_setid` returns `runflags`, both harvested from the QUOTED plan block rather than from the doc's own YAML front matter, whose real values are `status: reference` and `set: awmetastore` (the plan's earlier `status: todo` is stale; the doc has since been adopted). Fixing only `_read_id` would leave two readers still asserting a quoted document's status and setid, which is the same bug producing wrong `aw find <status>` and `aw find <setid>` answers instead of a collision.
  KNOW WHAT "FIXED" LOOKS LIKE HERE, because it is None rather than the doc's own value, and an executor expecting the latter will think the fix failed. A YAML region contains NO bullet-style `- Id:`/`- Status:`/`- Set:` at all (verified: `27rjro`'s `---` block carries `id: 27rjro`, not `^- Id:`), and this plan deliberately does NOT teach the readers the YAML dialect (that is `xo3244`). So the correct post-fix result for a research doc is that all three readers return None, which stops the false claim without inventing a true one.
  - Depends on: E-01
  - Expected outcome: all three readers consult only the metadata region; on the `27rjro` doc all three return None rather than a value harvested from the quoted block, and a normal bullet-front-matter plan's three values are byte-identical to before.
  - Execution state: performed

- [x] E-03 CONSOLIDATE the near-duplicate `_FRONT_MATTER_ID_RE` (`selectors.py:280`) with `_ID_RE` (`:111`) rather than fixing one and leaving the other, which is the item's scope point 3 and its stated reason is on the record: the comment block above the public readers records that both host runners previously carried private `_read_id` copies that DRIFTED, and that the public pair exists precisely so there is one definition per reader. MIND THE DELIBERATE DIFFERENCE, which must be preserved rather than flattened: `_ID_RE` requires exactly one space after the dash while `_FRONT_MATTER_ID_RE` uses `^-\s*Id:` and tolerates any whitespace, and the comment explains that widening the strict one was NOT an option because `_STATUS_RE`'s strictness is a documented MATCHING-BEHAVIOR CONTRACT that deliberately disagrees with `plans_index._META_RE` on 24 records. So consolidate the REGION-BOUNDING, not the whitespace tolerance: both readers must become region-bounded while keeping their own patterns. Also decide and record whether the PUBLIC readers (`read_front_matter_id` `:287-294`, `read_front_matter_status` `:297-304`), which both host drivers consume, should be region-bounded too; a driver reads PLAN front matter where the region is unambiguous, so bounding them is safe and consistent, but it is a change to a shared runner-facing reader and must be a stated decision rather than a side effect.
  - Depends on: E-02
  - Expected outcome: both id readers are region-bounded, their distinct whitespace patterns are unchanged, and the public readers' treatment is a recorded decision.
  - Execution state: performed

### Task group 2: warn rather than swallow

- [x] E-04 Fix the LIVE INSTANCE by the reader change alone and prove BOTH docs were left untouched. The item is explicit: "Do not mangle the quoted example (it is legitimate cited content); the fix is in the reader, not the doc." After E-02, `aw set reviewed uyeko5` must resolve the single real plan, and BOTH quoting research docs must keep their `- Id: uyeko5` lines byte-for-byte. Verify with `git diff` over `.aw/records/research/` showing no change.
  THERE ARE TWO DOCS, AND THE SECOND ALSO CLEARS THE `aw check` COLLISION. Review measured the collision `aw check all` reports today as research-to-research, `27rjro` naming `takpys` (`...takpys-...gpt56solhigh.research-report.md:141`), so the reader fix should ALSO drop that finding to zero. Assert that as part of this item rather than discovering it in E-05's before/after counts: after the fix, `check.id6-collision` should report NOTHING for either doc, because neither declares `uyeko5` in its region any more.
  MIND THAT `uyeko5`'s PLAN IS RETIRED (in `executed/`), so `aw set reviewed uyeko5` will refuse for a DIFFERENT and legitimate reason once the collision clears: `reviewed` is not a legal transition from an executed plan. Do NOT read that refusal as the collision persisting. The assertion is about RESOLUTION (exactly one file matched, and it is the plan), so prove it with a resolution-level check (`aw find plans uyeko5`, or `selectors.resolve`) and treat any transition refusal separately, naming which it is.
  - Depends on: E-02
  - Expected outcome: `uyeko5` resolves to exactly one file (the executed plan) with no collision; `check.id6-collision` reports nothing on either research doc; both docs are unmodified; any residual `aw set` refusal is identified as a lifecycle refusal rather than a resolution failure.
  - Execution state: performed

- [x] E-05 Add the CHECK RULE the maintainer required, so bounding the scan surfaces the ambiguity instead of hiding it (recorded decision 2026-09-05: fix AND warn, not fix quietly). The rule reports a metadata-shaped `- Id:` found OUTSIDE the metadata region. Register it with the existing rule machinery in `check_engine.py` alongside the identity family (`check.id6-collision`, `check.id6-identity-slot`).
  REGISTER IT AT `"info"`, NOT `"warning"`, AND THIS IS A CORRECTION RATHER THAN A PREFERENCE. The original instruction said "WARN rather than error, or the repository would fail its own check for documenting itself", and the second half is right while the label is wrong: `warning` DOES fail the gate. MEASURED by driving `artifact_core.drift_exit_code` with each value: `error` -> 1, `warning` -> 1, `info` -> 0, empty -> 1 (`artifact_core.py:405-415`, whose docstring states only `info` is advisory). So registering `"warning"` would make `aw check` exit nonzero on the two legitimate quoting documents, which is exactly the outcome OQ-01's own reasoning set out to avoid. Two shipped precedents to copy: `check.ipd-draft-ready-to-review` (`check_engine.py:262-264`) and `check.stale-index-missing` (`:333-335`), both `"info"` for the same detect-and-nudge purpose. Note also that an UNREGISTERED rule falls through to `_DEFAULT_RULESPEC` at severity `error` (documented at `:328-332`), so omitting the registry entry is not a neutral act.
  THE RULE MUST FIRE ON BOTH OFFENDING FILES, not just the one the item named. Review measured TWO: the `27rjro` research-prompt and the `takpys` research-report, which quote the same `uyeko5` block (F-7). A rule that flags only the first is half-built.
  - Depends on: E-01
  - Expected outcome: a new `"info"`-severity rule that flags BOTH offending research docs today, does not flag any conformant artifact, leaves `aw check` exit code UNCHANGED at 0-for-this-rule, and fires on the outside-the-region shape without needing a colliding counterpart.
  - Execution state: performed

- [x] E-06 REPORT, and do not fix, the retired-record scan gap in `check_collisions`, because it is a distinct defect noticed while verifying this item and fixing it is a separate scope decision. STATE IT ACCURATELY, WHICH REVIEW HAD TO CORRECT: the MECHANISM is real, but the claim that it is currently MASKING this collision is FALSE. Verified at HEAD: `check_engine.is_retired(<the executed uyeko5 plan>,'plans')` is True and `_iter_type_files` excludes it unless `include_retired=True`, so a collision between a RETIRED artifact and a live one would be invisible to `aw check` while remaining fully live for `selectors.resolve()`, which does not skip retired records. BUT `aw check all` DOES report this collision today (one `check.id6-collision`, on `27rjro`, naming `takpys`), because a SECOND live research doc quotes the same block, so both sides are scannable. Record the mechanism as a latent gap with its measurement, and explicitly retract the "detector is blind" framing so a future reader does not inherit a false premise. If the maintainer wants the gap fixed, expect a separate item rather than widening this fence: making `check_collisions` scan retired records changes what the repository-level check reports across the whole executed corpus and could surface a large batch of pre-existing findings.
  - Depends on: E-05
  - Expected outcome: the retired-record gap recorded as LATENT with a re-measurement at execution time, the "blind detector" claim explicitly retracted, and no change to `_iter_type_files`' retired filtering in this plan.
  - Execution state: performed

### Task group 3: pin it

- [x] E-07 Test the matrix, extending the module that already owns selector behavior. `tests/test_selector_zero_open.py` holds the resolver's dialect and precedence cases and is the natural home for the resolution assertions; put the region helper's own unit cases in the new module. Cover: a doc quoting `- Id: <other-id6>` in its BODY does not resolve as that id6 (the item's first required regression); `aw set <id6>` still resolves the genuine artifact; the `27rjro` doc no longer collides; the new outside-the-region `info` rule fires on BOTH offending docs (`27rjro` AND `takpys`, per F-7); `_read_status` and `_read_setid` are likewise unaffected by a quoted block; and the region helper's FIVE shapes from E-01, including the truncated-header case.
  PRESERVE THE PRECEDENCE CONTRACT, BUT ASSERT IT ON A TOKEN THAT CAN ACTUALLY MATCH. The resolver's documented order is path -> id6 -> setid -> status -> stem -> substring, and the point worth pinning is that removing an ID6 match does not silently narrow the LATER rules. As originally written this item implied asserting that the quoted id6 still matches by filename substring, which is FALSE for the live instance and would produce a failing test that looks like a regression: `uyeko5` appears in NEITHER offending filename (measured, zero matches), so after the fix it correctly resolves to ZERO research files. Assert the contract with a token that IS in the filename: measured today, `27rjro` resolves in `research` with `kind=substring` (not `id6`) and `takpys` likewise, so the correct assertion is that those still resolve by substring AFTER the change, while `uyeko5` resolves to nothing in `research` and to exactly one file in `plans`.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: all cases plus the region-shape units pass; the first regression case fails against pre-change code; the precedence assertion uses a filename-present token and does not demand a substring match for `uyeko5`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `selectors.py` is the ONE selector-to-file resolver for every verb (`rename`, `group`, `set`/`ipd set`/`spec set`/`backlog set`, `show`, `find`, `archive`, the set-assign/mv paths), so a change here reaches MUTATING verbs, not only readers. That is why the blast-radius measurement matters more than usual.
- There are deliberately TWO tiers of reader: strict internal ones for selector matching, and permissive PUBLIC ones (`read_front_matter_id`, `read_front_matter_status`) that both host drivers consume, created because the drivers previously carried private copies that drifted.
- `_STATUS_RE`'s strictness is a documented MATCHING-BEHAVIOR CONTRACT: its `(\S+)` deliberately disagrees with `plans_index._META_RE` on 24 of 469 plans carrying a multi-word `- Status:`. Do not harmonize the patterns while region-bounding them.
- The resolver reads a BOUNDED 4096-byte header (`_HEADER_BYTES`, `selectors.py:317`) for the front-matter rules, so a region boundary must be found within that window; the quoted block at line 60 of the live instance is well inside it (first `## ` at byte 1149), which is exactly why the bug bites AND why the fix works. BUT 85 of 1136 tracked records have NO `## ` inside that window at all, so a missing boundary is COMMON and must mean "region continues", never an error or an empty region.
- A `warning`-SEVERITY RULE IS NOT ADVISORY IN THIS CODEBASE. `drift_exit_code` fails on `error`, `warning` AND an empty severity, and passes ONLY on `info` (`artifact_core.py:405-415`, measured). The advisory tier is `info`, with two shipped precedents in the registry. An UNREGISTERED rule defaults to `error` (`check_engine.py:328-332`).
- A YAML-fenced region contains no bullet-style `- Key:` lines, so region-bounding the existing bullet patterns makes research metadata read as ABSENT rather than as its own values. That is the intended outcome here; teaching the YAML dialect is `xo3244`'s job.
- `check_collisions` covers all eight `SUPPORTED` types INCLUDING research, and `_iter_type_files` EXCLUDES retired records by default (measured: the executed `uyeko5` plan is absent from the 104 plans scanned). That is a LATENT gap, not the cause of anything here: `aw check all` DOES report this collision today, research-to-research between `27rjro` and `takpys`, because both quoting docs are live.
- The precedence chain and the artifacts-not-mentions rule are the resolver's published contract; a token appearing only in a body must never resolve, which is the principle this plan extends from bodies-in-general to quoted-metadata-in-particular.
- `.aw/inbox/` was deliberately sited OUTSIDE `.aw/records/` because a dropped external report that quoted an example block was harvested the same way. That placement removed the inbox exposure only; this reader bug remains live for every tracked artifact.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The pattern is unchanged and unbounded: `_ID_RE = re.compile(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$")`, applied to a whole file body. | `selectors.py:111` at `a2e0438a` |
| F-2 | THE COLLISION IS STILL LIVE: `aw set reviewed uyeko5` fails with "id6 collision matching multiple files ... not overridable by --force", naming the real plan and the research doc, exit 2. | measured at `a2e0438a` |
| F-3 | The reader still harvests the quotation: `selectors._read_id(<27rjro doc>)` returns `uyeko5`, while the doc's own front matter says `id: 27rjro`. | measured at `a2e0438a` |
| F-4 | SUPERSEDED BY REVIEW, AND THE CORRECTION MATTERS: `aw check all` DOES report a `check.id6-collision` today. Re-measured at HEAD `18d7cc4c`: exactly ONE, and it is ON the `27rjro` doc. The "zero findings" measurement no longer holds. | measured at `18d7cc4c` |
| F-5 | SUPERSEDED BY REVIEW. The retired-record mechanism is REAL (`is_retired(<the executed uyeko5 plan>,'plans')` is True, and the executed plan is absent from the 104 plans `_iter_type_files` scans by default) but it is NOT masking this collision, because a SECOND live research doc also quotes the block. Re-measured counts: 104 plans scanned (not 70), 81 research files scanned (not 76). | `check_engine.py` `is_retired`/`_iter_type_files`; measured at `18d7cc4c` |
| F-6 | SUPERSEDED BY REVIEW: the detector is NOT blind. The reported collision is research-to-research, between `27rjro` and `takpys` (`20260905-awmetastore-01-takpys-...gpt56solhigh.research-report.md:141`), BOTH live and both quoting `- Id: uyeko5`. So the collision has two scannable sides after all, and `aw check all` and `aw set uyeko5` now AGREE that something is wrong rather than diverging. The defect's severity rests on F-2/F-3 (the verbs still fail, exit 2), which is sufficient on its own. | measured: `aw check all` -> 1 id6-collision on `27rjro` naming `takpys`; `aw set uyeko5` exit 2 |
| F-15 | RE-MEASURED AT EXECUTION (2026-09-21), SUPERSEDING F-7's COUNT: THE BLAST RADIUS IS **THREE** FILES, NOT TWO. Over all **1614** tracked records under `.aw/records/` (not 1136), the region bound changes a reader answer for `27rjro`, `takpys` AND the `effzzi` roadmap. `effzzi` is the one E-01's YAML-fence bound exists for: it opens with a `---` fence and then carries NARRATIVE bullets under its H1 (`- Set: `awoptimize``, `- Plans: one orchestrator plus eight children`) BEFORE its first `##`, so a "before the first `##`" region would read prose as metadata. VERIFIED it changes no resolution answer: `awoptimize` still resolves to the same 4 research files by `substring`, because the backticked value never matched `setid` anyway (the pinned `BacktickSetValueIsPinnedTests` behavior). | measured at `5421fc10` over `git ls-files`; region differential across all 8 SUPPORTED types |
| F-16 | RE-MEASURED AT EXECUTION, SUPERSEDING F-13's COUNT: header exhaustion affects **25 of 1614** records, not 85 of 1136. The mechanism is unchanged and still load-bearing (exhaustion MUST mean "the region continues"), but the count FELL because `_read_header` is no longer a 4096-byte HARD CAP: it now reads in chunks until the metadata block is provably complete, so most files that previously exhausted the window now reach their `##`. A helper that returned empty or raised on a missing boundary would still break 25 records while fixing 3. | measured at `5421fc10`; `selectors._read_header` + `_METADATA_END_RE` over every tracked record |
| F-17 | THE CHECKER CARRIED ITS OWN COPY OF THE DEFECT, which no finding above anticipated and which is why E-02's fix had to reach `check_engine.py`. `_ID_LINE_RE` there is a byte-identical twin of `selectors._ID_RE` and `check_collisions` applied it to a WHOLE FILE BODY, so the two quoting research docs were reported as a real `check.id6-collision` with EACH OTHER. Bounding only the selector would have left `aw check` asserting a collision no verb could see. Also measured: `check_engine._ITEM_ID_RE` is divergent on the same 2 docs but is reached by no current call path (every site iterates plans/backlog/specs), so it is FILED (`axayfn`) rather than fixed inside this fence. | measured: 17 id6-collision findings before, 15 after, the 2 removed both naming `uyeko5` |
| F-7 | REVISED BY REVIEW: THE BLAST RADIUS IS **TWO** FILES, NOT ONE, and both are in the same research Set. Across all 1136 tracked markdown files under `.aw/records/` (not the 1006 originally stated), exactly two have a metadata-shaped `- Id:` after their first `##` heading: the `27rjro` research-prompt and the `takpys` research-report, which quote the same `uyeko5` block. VERIFIED that the region fix repairs BOTH: in each file the first `## ` falls inside the 4096-byte header window (byte 1149 for `27rjro`) and the quoted `- Id:` lies AFTER it, so a region-bounded read returns no id6 for either. | measured at `18d7cc4c` over `git ls-files` |
| F-12 | A `warning`-SEVERITY RULE STILL FAILS THE GATE, so E-05's severity choice as originally reasoned would not have achieved its own goal. `drift_exit_code` returns 1 for `error` AND `warning` and 0 ONLY for `info` (`artifact_core.py:405-415`, verified by driving it with each value). The non-failing advisory tier is `info`, with two shipped precedents (`check.ipd-draft-ready-to-review` and `check.stale-index-missing`, both `"info"`). | `artifact_core.py:415`; `check_engine.py:262-264`, `:333-335`; measured |
| F-13 | THE REGION BOUNDARY MUST BE FOUND INSIDE THE 4096-BYTE HEADER, AND FOR 85 TRACKED FILES IT IS NOT PRESENT THERE. Measured: 85 of 1136 tracked records have NO `## ` heading within their first 4096 bytes, so "everything before the first `##`" degenerates to the WHOLE header for them. That is harmless for those files (their metadata is at the top and no `- Id:` appears later in the window) but it means the helper MUST treat header-exhaustion as "region continues", never as an error, and E-01's "no `##` heading at all" shape is the common case rather than an edge case. | measured at `18d7cc4c` |
| F-14 | A YAML-FENCED REGION CONTAINS NO BULLET-STYLE `- Id:` AT ALL, which is why this fix leaves research id6 UNMATCHABLE rather than merely correctly-matched. Verified on `27rjro`: its `---` block has `id: 27rjro` (YAML) and no `^- Id:`. So after E-02 `_read_id` returns None for research docs, `27rjro` continues to resolve only by FILENAME SUBSTRING (measured `kind=substring` today), and `uyeko5` resolves to ZERO research files because it appears in neither filename. That is the correct outcome here and is exactly the gap plan `xo3244` exists to close. | measured at `18d7cc4c` |
| F-8 | THE ITEM'S SCOPE POINT 4 IS CONFIRMED: on the same doc `_read_status` returns `reviewed` and `_read_setid` returns `runflags`, both harvested from the quoted block instead of the doc's own `status: todo` / `set: awmetastore`. | measured at `a2e0438a` |
| F-9 | The near-duplicate reader exists and must be consolidated in the same pass, with its deliberate whitespace difference preserved. | `_ID_RE` `selectors.py:111` vs `_FRONT_MATTER_ID_RE` `:280`; the drift rationale in the comment block above the public readers |
| F-10 | The quoted content is legitimate cited material: the doc quotes a real IPD metadata block to discuss where metadata should live, which is precisely the self-documentation case the item says will keep recurring. | `.aw/records/research/20260905-awmetastore-00-27rjro-...research-prompt.md:57-61` |
| F-11 | Nothing else covers this: no pending or approved plan and no spec touches `_ID_RE`, the metadata region, or id6 over-capture. | grep over `.aw/records/plans/pending/` and `.aw/records/specs/` at `a2e0438a` |

## Proposed changes (ordered, validatable)

1. Add one metadata-region helper handling bullet and YAML front matter, tolerating a header truncated mid-region (E-01).
2. Bound `_read_id`, `_read_status` and `_read_setid` to that region (E-02).
3. Consolidate the near-duplicate id reader's region-bounding, preserving its whitespace pattern, and bound the public readers per OQ-02 (E-03).
4. Confirm the live collision is resolved by the reader change alone, both docs untouched (E-04).
5. Add the `info`-severity outside-the-region rule, firing on both offending docs (E-05).
6. Record, without fixing, the retired-record scan gap in `check_collisions`, retracting the "blind detector" claim (E-06).
7. Pin the regressions plus the region-shape units, with the precedence assertion built on a filename-present token (E-07).

## Deferred / out of scope (with reason)

- FIXING `check_collisions`' RETIRED-RECORD SCAN GAP (F-5, F-6, both now marked SUPERSEDED). The MECHANISM is real and worth its own item, but review falsified the claim that it is masking anything today, so this deferral rests on the mechanism alone rather than on an urgent symptom. Scanning retired records changes what the repository check reports across the whole executed corpus and could surface a large batch of pre-existing findings, which is a maintainer-sized decision. E-06 records it for its own item rather than widening this fence.
  - Carrier: lmjc8h
- FIXING THE `warning`-IS-NOT-ADVISORY TRAP ITSELF (F-12). Review measured that `drift_exit_code` fails on `warning`, so the codebase has an `error`/`warning`/`info` vocabulary in which only `info` is genuinely advisory, which is a latent trap for the next rule author. This plan works AROUND it by registering at `info`; changing what `warning` MEANS would re-tier every existing `warning` rule and is a separate contract decision. Worth reporting, not fixing here. FILED at execution time so this obligation outlives the plan.
  - Carrier: 1dvtiq
- EDITING THE `27rjro` RESEARCH DOC. Explicitly forbidden by the item and correct: the quotation is legitimate cited content and the fix belongs in the reader.
  - Carrier-Declined: NOT an obligation: this row records work that must NEVER be done, so there is nothing to carry forward. VERIFIED at execution: `git diff -- .aw/records/research/` is empty and both quoted `- Id: uyeko5` lines survive byte-for-byte (V-04).
- HARMONIZING `_STATUS_RE` WITH `plans_index._META_RE`. A separate documented contract change affecting 24 plans, unrelated to region bounding.
  - Carrier-Declined: NOT an obligation: this is a standing DO-NOT-DO contract, documented in `selectors._STATUS_RE`'s PARITY CONSTRAINT comment and pinned by `tests/test_selector_zero_open.py::StatusParityConstraintTests`/`RegexShapeTests`, so the decision is already durable in code and tests rather than pending in a plan. VERIFIED unchanged by this plan (V-03).
- TEACHING THE RESOLVER THE YAML DIALECT for MATCHING purposes (making research id6/status/setid resolvable via the content rules). That is backlog item `05aqbj`, already graduated to plan `xo3244` (Set `selfmdialect`, `- Status: to-review`, `From-Backlog: 05aqbj`). THE TWO INTERACT AND THE EXECUTOR MUST CHECK: `xo3244` makes the YAML block matchable, and this plan bounds WHERE a match may come from. They are complementary rather than conflicting (a region-bounded YAML read is exactly what both want), but both touch `selectors.py` and the same three readers, so whichever lands second must re-read the first's changes rather than assuming. THIS PLAN LANDED FIRST, so `xo3244` must now re-read `selectors.py`: its three readers are region-bounded and a YAML-dialect reader should consult `metadata_region` rather than adding a second boundary parser.
  - Carrier: 05aqbj
- THE `.aw/inbox/` SITING. Already done (commit `b534fee9`) and only removed the inbox exposure; nothing further here.
  - Carrier-Declined: NOT an obligation: the work is already DONE and committed, so there is no outstanding obligation to carry.

## Scope check

- Over-scope: `agent_workflows/check_engine.py` is in `Scope-Paths` for E-05's new rule, which the maintainer required as a condition of the fix ("fix AND warn"), so it is in scope by that ruling rather than by the reader defect alone. Review confirms the declared paths are sufficient and none needs adding: the region helper, all three private readers and both public readers live in `selectors.py`, and the rule plus its registry entry live in `check_engine.py`.
- Under-scope: the retired-record scan gap is reported, not fixed. No document is edited. The public runner-facing readers ARE bounded (OQ-02 resolved at review), with the call-site enumeration as E-03's evidence rather than the change being assumed.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. RE-MEASURED AT REVIEW on main (HEAD `18d7cc4c`): `1 failed, 5958 passed, 3 skipped, 2 xfailed in 57.08s`. The stated baseline `1 failed, 5648 passed` and its named `test_orchestrator_retirement` failure are BOTH WRONG: that module passes (`112 passed`), and the single real failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL because it walks the repo and trips over another party's untracked `opencode-recovery/` directory. Do NOT delete that directory to make the suite green; it is not yours. Measure your OWN before-baseline and judge on the DELTA.
- `python3 -m pytest tests/test_selector_zero_open.py tests/test_id_metadata_region.py` for the focused surface, plus any `aw find` or `check` module the change touches.
- A before/after resolution comparison over all eight `SUPPORTED` types, proving no artifact other than the TWO measured files changes its resolved id6, status or setid. TWO, not one: re-measured at review, both `27rjro` and `takpys` carry an out-of-region `- Id: uyeko5`.
- `python3 -m agent_workflows check all` before and after, with the new rule's finding shown and no OTHER rule's finding count changed EXCEPT `check.id6-collision`, which should drop from 1 to 0 because the reader fix removes the false declaration on both docs. State that expected change explicitly rather than treating it as unexplained drift.
- THE NEW RULE'S EFFECT ON THE EXIT CODE measured UNPIPED, proving an `info`-severity finding does NOT fail the gate: `aw check all` must not become nonzero BECAUSE of this rule. This is the assertion that pins OQ-01's resolution.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

No `.spec.md` file defines the metadata region or the identity-extraction boundary, so none is edited and none is declared in `Scope-Paths`. The authoritative documentation is in code and must be kept truthful: `selectors.py`'s module docstring describes the dialects and the precedence chain, and the `resolve()` docstring enumerates the six rules, so E-02/E-03 must state that the content rules read the METADATA REGION rather than the whole body. DECISIONS D140 governs the filename identity slot and is adjacent but untouched: this plan changes where a DECLARED id is read from, not what a filename slot means. If the executor concludes the region boundary deserves a written contract beyond a docstring (a reasonable position, since `aw check` will now enforce a rule about it), propose it as a follow-up rather than amending a spec inside this fence.

## Open questions

### OQ-01: Should the outside-the-region rule WARN or ERROR?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: NEITHER. REGISTER IT AT `"info"`. RESOLVED AT REVIEW BY MEASUREMENT, because the question as posed offered two options that both fail and omitted the one that works. The reasoning behind "WARN" was correct: a quoted metadata block is LEGITIMATE content this repository produces by design, so a gate that fails on it would make the repository fail its own check for correct behavior, which is the failure mode recorded in backlog `gjadwm` ("a gate that false-positives on correct behavior TRAINS agents to bypass it"). BUT `warning` DOES FAIL THE GATE. Verified by driving `artifact_core.drift_exit_code` with each value: `error` -> 1, `warning` -> 1, `info` -> 0, empty string -> 1. Its docstring is explicit that only an `info`-severity finding is advisory and that "only error/warning-class findings drive the nonzero exit" (`artifact_core.py:405-415`). So registering `"warning"` would have produced exactly the outcome the recommendation was written to prevent, on two legitimately-quoting documents, and the maintainer's fix-and-warn ruling is satisfied by `info` (the finding is reported; the gate does not fail).
  THE PRECEDENT IS ALREADY IN THIS FILE, twice, for the same detect-and-nudge purpose: `check.ipd-draft-ready-to-review` is `"info"` (`check_engine.py:262-264`) and `check.stale-index-missing` is `"info"` (`:333-335`), with the neighbouring comment recording that an UNREGISTERED rule falls through to `_DEFAULT_RULESPEC` at severity `error` and that this is why "absence could not have been made non-failing by editing a message string". So the registry entry is mandatory, not optional.
  THE COUNTER-ARGUMENT IS PRESERVED AND STILL OPEN AS A FUTURE CHOICE, not as a blocker: once the reader is bounded, an out-of-region `- Id:` is always either a quotation (harmless) or a MISPLACED DECLARATION (a real defect), and only an error-severity rule would force the second to be fixed. Distinguishing them needs a signal this plan does not build. If the maintainer later wants that, it is a severity change on a rule that by then has a clean corpus, which is the same shape as the plans-tree precedent.

### OQ-02: Should the PUBLIC runner-facing readers be region-bounded too?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, BOUND THEM. RESOLVED AT REVIEW from the code, since the question itself says it is resolvable there and the plan-review contract forbids asking a human what the repository answers. `read_front_matter_id` (`selectors.py:284-292`) and `read_front_matter_status` (`:294-302`) exist precisely BECAUSE both host runners previously carried private `_read_id`/`_read_status` copies that DRIFTED, which the comment block above them records as the reason for one definition per reader (`:276-279`). Leaving the public pair unbounded while bounding the private pair would REINSTATE that drift deliberately, in the same module, days after the comment explaining why it must not happen. A driver reads PLAN front matter, where the region boundary is unambiguous (a bullet block before `## Workflow history`), so the change is behaviour-preserving for every real driver input.
  WHAT MAKES IT SAFE IS ALSO WHAT MUST BE CHECKED, so this resolution carries an obligation rather than closing the topic: the documented failure mode of these readers is that a MISSED read silently degrades a runner to a directory-derived status, so E-03 must enumerate every driver call site and confirm each passes plan front matter rather than an arbitrary body. If any consumer legitimately needs a whole-body read, leave that one unbounded and say why in V-03. The measured header-truncation case (F-13) matters here too: a driver reading a long plan must not lose its region to the 4096-byte cap, which is why E-01's helper must treat exhaustion as "region continues".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the helper's source and its output for FIVE inputs shown individually: a bullet-front-matter plan, a YAML-fenced research doc, a file whose first line is an H1 followed by bullets, a file with no `##` heading at all, and a header TRUNCATED mid-region at `_HEADER_BYTES`. For each, show the returned region text and confirm it stops at the right boundary; for the truncated case confirm it returns the whole window rather than empty or an error. Paste the re-measured count of tracked records with no `## ` inside the header window (85 at review) so the case is shown to be common rather than hypothetical.
  - Observed evidence: all FIVE region shapes verified individually, outputs pasted below; header-exhaustion re-measured at 25 of 1614 records (review's 85 of 1136 is stale in both terms, and why is explained).
    The helper is `selectors.metadata_region` (`agent_workflows/selectors.py`). Its body, verified with `inspect.getsource`:

    ```python
    if not text:
        return text or ""
    m_open = _YAML_FENCE_OPEN_RE.match(text)
    if m_open is not None:
        m_close = _YAML_FENCE_CLOSE_RE.search(text, m_open.end())
        if m_close is None:
            return text  # fence unterminated within the input -> the region continues
        return text[: m_close.end()]
    m_end = _METADATA_END_RE.search(text)
    if m_end is None:
        return text  # no `##` in the input -> the region continues (the common 25-record case)
    return text[: m_end.start()]
    ```

    All FIVE shapes, each run individually (`region is whole input` is the header-exhaustion signal):

    ```
    === 1. bullet-front-matter plan
        input len=99  region len=65   region is whole input: False
        region ends with: ': a plan\n\n- Set: idcapture\n- Status: approved\n- Id: aaa111\n\n'
        _read_id(region-bounded) -> 'aaa111'

    === 2. YAML-fenced research doc
        input len=77  region len=53   region is whole input: False
        region ends with: '---\nid: ccc333\nset: awmetastore\nstatus: reference\n---'
        _read_id(region-bounded) -> None

    === 3. H1 then bullets
        input len=66  region len=44   region is whole input: False
        region ends with: '# A Title\n\n- Id: aaa111\n- Status: approved\n\n'
        _read_id(region-bounded) -> 'aaa111'

    === 4. NO '##' heading at all
        input len=41  region len=41   region is whole input: True
        region ends with: '# Title\n\n- Id: aaa111\n- Status: approved\n'
        _read_id(region-bounded) -> 'aaa111'

    === 5. header TRUNCATED mid-region at _HEADER_CHUNK_BYTES
        input len=4096  region len=4096   region is whole input: True
        region ends with: 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        _read_id(region-bounded) -> None
    ```

    Each stops at the right boundary: case 1 at the first `##` (keeping the H1 and every bullet), case 2 at the CLOSING `---` fence, case 3 at `## Body` with the H1 NOT truncating the region, case 4 at end-of-input. Case 5, the truncated header, returns the WHOLE 4096-byte window rather than empty or an error - exactly as required - and correctly yields no id6 because the truncation cut the input before the `- Id:` line, which is a short READ, not a wrong region.

    RE-MEASURED HEADER-EXHAUSTION COUNT, and the review figure is now STALE in both terms: **25 of 1614** tracked records under `.aw/records/` present no `## ` heading inside the bounded header window (review said 85 of 1136). The corpus grew 1136 -> 1614, and the count FELL 85 -> 25 because `_read_header` is no longer a hard 4096-byte cap: it now grows in chunks until the metadata block is provably complete, so most files that previously exhausted the window now reach their `##`. The case is therefore still common (25 records, not a hypothetical) and would still break 25 files if exhaustion were treated as an error.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the three readers' returns for the `27rjro` doc BEFORE (`uyeko5` / `reviewed` / `runflags`) and AFTER (all three None, per E-02's stated expectation, NOT the doc's own YAML values), and paste the same three readers' returns for a normal bullet-front-matter plan before and after showing them byte-identical. Do the same before/after pair for the `takpys` doc, since it carries the same quoted block. Both runs must be shown, not described. State in one sentence why None rather than `27rjro`/`reference`/`awmetastore` is the correct post-fix answer here.
  - Observed evidence: BEFORE and AFTER both actually run (via git stash of the source edits), outputs pasted; `27rjro` moves uyeko5/reviewed/runflags -> None/None/None, a normal plan is byte-identical, and one premise of this item is corrected.
    BOTH runs were actually performed: the BEFORE half by `git stash`-ing this plan's two source edits, running the readers, then `git stash pop`. Not described, measured.

    ```
    ########## BEFORE (pre-change, whole-body readers) ##########
    20260905-awmetastore-00-27rjro-where-aw-metadata-should-li
        _read_id='uyeko5'  _read_status='reviewed'  _read_setid='runflags'
        read_front_matter_id='uyeko5'  read_front_matter_status='reviewed'
    20260905-awmetastore-01-takpys-where-aw-metadata-should-li
        _read_id=None  _read_status=None  _read_setid=None
        read_front_matter_id=None  read_front_matter_status=None
    20260908-idcapture-01-76w6mq-bound-identity-extraction-to-
        _read_id='76w6mq'  _read_status='approved'  _read_setid='idcapture'
        read_front_matter_id='76w6mq'  read_front_matter_status='approved'

    ########## AFTER (region-bounded) ##########
    20260905-awmetastore-00-27rjro-where-aw-metadata-should-li
        _read_id=None  _read_status=None  _read_setid=None
        read_front_matter_id=None  read_front_matter_status=None
    20260905-awmetastore-01-takpys-where-aw-metadata-should-li
        _read_id=None  _read_status=None  _read_setid=None
        read_front_matter_id=None  read_front_matter_status=None
    20260908-idcapture-01-76w6mq-bound-identity-extraction-to-
        _read_id='76w6mq'  _read_status='approved'  _read_setid='idcapture'
        read_front_matter_id='76w6mq'  read_front_matter_status='approved'
    ```

    `27rjro` moves `uyeko5`/`reviewed`/`runflags` -> None/None/None exactly as E-02 predicted. The normal bullet-front-matter plan (`76w6mq` itself) is BYTE-IDENTICAL before and after on all five readers, which is the no-regression half.

    ONE CORRECTION TO THE PLAN'S PREMISE, worth recording because it changes WHY the `takpys` half of the fix was needed. `takpys` already read None through the SELECTOR before this change, so its before/after pair is unchanged here. That is not because it was unaffected: its quoted `- Id:` sits at line 141, past the bounded header the selector reads, so the selector never saw it. The CHECKER reads WHOLE FILES and did see it, which is why `takpys` was one side of the live `aw check` collision and why bounding the checker (not only the selector) was load-bearing. See V-04.

    WHY None IS THE CORRECT POST-FIX ANSWER, in one sentence: these three patterns speak only the BULLET dialect and a YAML-fenced region contains no `^- Id:`/`^- Status:`/`^- Set:` line at all, so None stops the FALSE claim without inventing a true one - teaching the readers the YAML dialect is plan `xo3244`'s job, not this one's.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `git diff` of both id readers showing each became region-bounded while its OWN whitespace pattern is unchanged (the strict single-space one and the `\s*` one must still differ). Paste a test proving a bullet written `-  Id: abc123` with two spaces is still read by the permissive reader and still NOT by the strict one. RECORD THE OQ-02 OUTCOME AS PERFORMED WORK, not as a decision to make: review resolved it to BOUND THEM, so paste the enumerated driver call sites for `read_front_matter_id`/`read_front_matter_status` with confirmation each passes plan front matter, and name any consumer left unbounded with its reason.
  - Observed evidence: the diff of all five reader call sites pasted, both id patterns provably still DIFFER on whitespace, the two-space bullet test pasted, and all 8 public-reader call sites enumerated with the 3 out-of-scope unbounded readers named and filed.
    `git diff -- agent_workflows/selectors.py`, filtered to the reader call lines. EVERY match site gained the region bound and NO pattern was edited:

    ```
    -    m = _ID_RE.search(text)
    +    m = _ID_RE.search(metadata_region(text))
    -    m = _STATUS_RE.search(text)
    +    m = _STATUS_RE.search(metadata_region(text))
    -    m = _FRONT_MATTER_ID_RE.search(text)
    +    m = _FRONT_MATTER_ID_RE.search(metadata_region(text))
    -    m = _FRONT_MATTER_STATUS_RE.search(text)
    +    m = _FRONT_MATTER_STATUS_RE.search(metadata_region(text))
    -    m = _SET_RE.search(text)
    +    m = _SET_RE.search(metadata_region(text))
    ```

    The two id patterns are UNCHANGED and still DIFFER, which is the consolidate-the-bound-not-the-whitespace requirement (no `_FRONT_MATTER_*_RE = ` or `_ID_RE = ` line appears in the diff at all):

    ```
    _ID_RE               = (?m)^- Id:\s*([0-9a-z]{6})\s*$      <- strict: exactly one space
    _FRONT_MATTER_ID_RE  = (?m)^-\s*Id:\s*([0-9a-z]{6})\s*$    <- permissive: any whitespace
    ```

    The two-space bullet test, pinned as `PublicReaderTests::test_the_two_tiers_still_differ_on_whitespace` (PASSED), asserting on `-  Id: aaa111` / `-  Status: approved`:

    ```
    read_front_matter_id(two_spaces)     -> 'aaa111'   (permissive: still reads it)
    read_front_matter_status(two_spaces) -> 'approved' (permissive: still reads it)
    selectors._read_id(two_spaces)       -> None       (strict: still does NOT)
    selectors._read_status(two_spaces)   -> None       (strict: still does NOT)
    ```

    OQ-02 RECORDED AS PERFORMED WORK: the public pair IS bounded. Enumerated call sites of `read_front_matter_id` / `read_front_matter_status` (`grep` over `agent_workflows/*.py`), every one passing PLAN (or spec) front matter, never an arbitrary body:

    | Call site | What it passes | Verified |
    |---|---|---|
    | `oc_runipd.py:438-439` | re-export binding only (`# noqa: F401`, required by `tests/test_runner_refork_guard.py`) | no read |
    | `oc_runipd.py:6372` | `current_plan.read_text()` via `resolve_plan_path` | plan file |
    | `oc_runipd.py:3759` | `dep_path.read_text()`, a dependency PLAN | plan file |
    | `agy_runipd.py:80-81` | re-export binding only | no read |
    | `agy_runipd.py:3005` | `current_plan.read_text()` via `resolve_plan_path` | plan file |
    | `runner_shared.py:5229-5238` | `path.read_text()` inside `parse_plan_file` | plan file |
    | `runner_shared.py:5514` | spec record text from `check_engine._iter_spec_records` | spec file |
    | `runner_shared.py:15059` | status of a run item's plan | plan file |

    NO consumer was left unbounded. Two readers OUTSIDE this plan's `Scope-Paths` remain unbounded and are NOT silently ignored: `status_set._ID_RE` (already documented as the known survivor in `artifact_core.repository_id6s`, backlog `q1ov25`) and `check_engine._ITEM_ID_RE` (10 call sites, measured LIVE-DIVERGENT on the same 2 research docs but reached by no current call path, since every site iterates plans/backlog/specs). `runner_shared.py:5514` is the one site that now pairs a BOUNDED status read with that UNBOUNDED `_ITEM_ID_RE` id6 read on the same text; measured 0 specs diverge today. All three are filed as backlog `axayfn` rather than fixed inside this fence, because `cqytxf` warns that several plans editing these readers is what recreated parser drift before.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the RESOLUTION of `uyeko5` BEFORE (collision naming two files, exit 2, measured UNPIPED) and AFTER (exactly one file, the executed plan), using `aw find plans uyeko5` or `selectors.resolve` rather than a status transition. If `aw set reviewed uyeko5` still refuses after the fix, paste the refusal and state explicitly that it is a LIFECYCLE refusal (`executed -> reviewed` is not a legal transition; verified False at review) and not a resolution failure. Paste the `check.id6-collision` count before (1) and after (0). Paste `git diff -- .aw/records/research/` showing an EMPTY diff, proving BOTH docs were left unmangled.
  - Observed evidence: resolution proven at the resolver level with a per-type census before/after, `check.id6-collision` 17 -> 15 (the 2 uyeko5 findings gone), both docs byte-for-byte unmodified, and a defect I triggered in `aw ipd set` reported and fully reverted.
    RESOLUTION, before and after, across every record type (the per-type view is what makes the fix visible; `aw find plans uyeko5` alone does NOT show it, see the correction below):

    ```
    BEFORE: which record types does `uyeko5` resolve in?
       plans         kind=id6        n=1  ['20260903-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-s']
       research      kind=id6        n=1  ['20260905-awmetastore-00-27rjro-where-aw-metadata-should-']
       reviews       kind=substring  n=1  ['20260904-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-s']
       TOTAL files claiming uyeko5 across types: 3

    AFTER: which record types does `uyeko5` resolve in?
       plans         kind=id6        n=1  ['20260903-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-s']
       reviews       kind=substring  n=1  ['20260904-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-s']
       TOTAL files claiming uyeko5 across types: 2
    ```

    The research doc's FALSE `kind=id6` claim is gone; the real plan still resolves by `id6`, and the review record still resolves by `substring` (its filename carries the id6, which is the documented convention and not a claim). `aw find plans uyeko5` AFTER, with its UNPIPED exit code:

    ```
    ✓  executed      uyeko5  runflags        .aw/records/plans/executed/20260903-runflags-01-uyeko5-wire-the-spec-2-1-run-flag-surface-onto-both-host-runners.ipd.md
    exit=0
    ```

    `selectors.resolve_for_mutation(repo, 'plans', 'uyeko5')` AFTER returns `err=None` with exactly 1 path, `kind=id6`, `is_unique=True`.

    TWO CORRECTIONS TO THIS ITEM'S PREMISE, both measured, neither weakening the fix. (1) The plan expected a BEFORE refusal at "exit 2" from `aw find plans uyeko5`/`resolve_for_mutation`. There is none: measured BEFORE, that call already returned 1 path and exit 0, because the collision was CROSS-TYPE (`plans` id6 vs `research` id6) and `resolve()` is scoped to ONE record type at a time. The review-era "exit 2" observation came from `aw set`, which sweeps types. So the correct evidence for this item is the per-type census above, which shows the duplicate claim and its removal directly. (2) `check.id6-collision` went **17 -> 15**, not 1 -> 0: the plan's figure counted only this pair, while the live tree carries 15 OTHER pre-existing collisions (14 backlog items each colliding with their own `done/` copy, plus one plan/backlog pair) that this plan does not touch. The **2** findings that disappeared are exactly the two quoting research docs:

    ```
    BEFORE total check.id6-collision: 17     BEFORE those mentioning uyeko5: 2
    AFTER  total check.id6-collision: 15     AFTER  those mentioning uyeko5: 0
    ```

    NO `aw set` TRANSITION WAS USED AS EVIDENCE HERE, deliberately, and this is reported rather than hidden: I did run `aw ipd set reviewed uyeko5` once while gathering this evidence, and it did NOT refuse. It performed the illegal backwards transition, rewriting `- Status: executed` to `reviewed` and `git mv`-ing the executed plan into `pending/`. I reverted it immediately and completely (`git restore --staged --worktree` plus removal of the stray `pending/` copy; the executed file is byte-identical to `HEAD` and `git status` over `.aw/records/plans/` is clean, verified). That is a REAL DEFECT in `aw ipd set`, not in this plan's change: `ipd_lifecycle.validate_transition('executed','reviewed')` returns `ok=False, reason="missing predecessor: backwards transition 'executed' -> 'reviewed'"`, so the setter is not consulting the predicate it already has. Reproduced in a clean throwaway repo and filed as backlog `rrvrwv` (`Work-Kind: bug`, `Blocks-Release: next`). The review's expectation that this would be a LIFECYCLE refusal was therefore correct in principle and wrong in fact - the tooling does not refuse it - which is why resolution was proven at the resolver level instead.

    BOTH DOCS LEFT UNMANGLED. `git diff -- .aw/records/research/` is EMPTY (0 files changed), and both quoted lines survive byte-for-byte:

    ```
    ...20260905-awmetastore-00-27rjro-...research-prompt.md:60:- Id: uyeko5
    ...20260905-awmetastore-01-takpys-...research-report.md:141:- Id: uyeko5
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the new rule's registration line showing severity `"info"` (NOT `warning`, per OQ-01's measured resolution), its findings on BOTH offending docs, and a full `aw check all` before/after finding-count comparison showing the new rule appears, `check.id6-collision` drops 1 -> 0, and no OTHER rule's count changed. Paste the UNPIPED exit code proving the new rule does not make the gate fail. Paste a conformant artifact NOT being flagged.
  - Observed evidence: registration line pasted at `info`, severity re-measured against drift_exit_code, both offending docs flagged, a full 11-rule before/after count table pasted, and the rule proven not to change the gate.
    The registration line, in `RULE_REGISTRY` beside the identity family, at `"info"` and NOT `warning`:

    ```python
    "check.id6-outside-metadata-region": RuleSpec(
        "info", ASSURANCE_GUIDANCE, DET_DETERMINISTIC, "I-09"
    ),
    ```

    OQ-01's severity measurement RE-CONFIRMED at execution time by driving `artifact_core.drift_exit_code` with each value, so the choice rests on a measurement and not on the label's connotation:

    ```
    severity='error'    drift_exit_code -> 1
    severity='warning'  drift_exit_code -> 1
    severity='info'     drift_exit_code -> 0
    severity=''         drift_exit_code -> 1
    ```

    Findings on BOTH offending docs (not just the one the item named), each carrying `severity: info`:

    ```
    new rule findings (default liveness): 2
       * ...takpys-where-aw-metadata-should-live.gpt56solhigh... | `- Id: uyeko5` at line 141 is outside the metadata region | sev: info
       * ...27rjro-where-aw-metadata-should-live.research-prompt | `- Id: uyeko5` at line 60  is outside the metadata region | sev: info
    ```

    Both also appear in the machine-readable surface (`aw check all --agent`), 2 diagnostics carrying `"rule": "check.id6-outside-metadata-region"`.

    FULL BEFORE/AFTER RULE-COUNT COMPARISON over `check_types(repo, ['all'])`, before measured by stashing this plan's two source edits:

    ```
    rule                                          before after delta
    check.from-backlog-dangling                       1     1    +0
    check.from-backlog-gate-mismatch                  2     2    +0
    check.id6-collision                              17    15    -2   <-- CHANGED (expected)
    check.id6-outside-metadata-region                 0     2    +2   <-- CHANGED (the new rule)
    check.identity-absent-from-name                   2     2    +0
    check.ipd-uncarried-obligation                   67    67    +0
    check.lifecycle-transition-invalid                3     3    +0
    check.live-bug-ungated                            2     2    +0
    check.name-nonconformant                          4     4    +0
    check.scope-drift                               711   719    +8   <-- NOT caused by this change
    check.system-layout-missing                       1     1    +0
    ```

    Only the two EXPECTED rules moved. `check.id6-collision` fell by 2 (17 -> 15, not the plan's predicted 1 -> 0; see V-04 for why the denominator differs). `check.scope-drift` is NOT attributable to this change and I verified rather than assuming: it counts MY OWN uncommitted files against OTHER agents' live begin receipts, and 27 of its findings name `agent_workflows/selectors.py`, `agent_workflows/check_engine.py` and `tests/test_check_engine.py` as "outside the plan's declared Scope-Paths" for those foreign receipts. It therefore grows as I edit and is deterministic within one snapshot (two consecutive calls on identical code both returned 719).

    THE NEW RULE DOES NOT FAIL THE GATE, which is the assertion pinning OQ-01's resolution:

    ```
    THIS RULE ALONE -> exit code: 0 (findings: 2)
    whole sweep WITH   this rule -> exit: 1
    whole sweep WITHOUT this rule -> exit: 1
    => the rule does NOT change the gate: True
    ```

    The sweep's exit 1 is pre-existing (67 `ipd-uncarried-obligation`, 15 `id6-collision`, etc.), unchanged by this rule. UNPIPED exit codes: `aw check all` -> 1 (pre-existing, same before and after), `aw check research` -> 0, i.e. the two flagged research docs do NOT make their own type's check fail.

    A CONFORMANT ARTIFACT IS NOT FLAGGED, pinned as `OutsideRegionRuleTests::test_a_conformant_record_is_not_flagged` (PASSED): a plan declaring `- Id: aaa111` in its region with prose-only body yields `[]`. Across the whole live tree the rule reports ONLY the 2 quoting docs out of 1614 records, so it does not mass-flag. Also pinned: `test_an_unregistered_rule_would_have_defaulted_to_error` (PASSED), proving the registry entry was mandatory rather than bookkeeping - `rule_spec('check.not-a-real-rule').severity == 'error'`.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the retired-record gap measured at execution time: `is_retired` on an executed plan, the scanned-file counts per type, and whether `aw check all` and `selectors.resolve()` AGREE or DIVERGE on the pair. State plainly whether the gap is currently latent (as review measured: `aw check all` reports the collision because both quoting docs are live) or actively masking something, and do NOT restate the retracted "detector is blind" claim. Paste `git diff -- agent_workflows/check_engine.py` limited to `_iter_type_files` showing its retired filtering was NOT changed.
  - Observed evidence: the retired-record gap re-measured at execution time and recorded as LATENT, the 'blind detector' claim explicitly retracted, the two surfaces proven to AGREE, and `_iter_type_files`' retired filtering proven unchanged.
    Measured at execution time, not inherited from the plan text:

    ```
    is_retired(<the executed uyeko5 plan>, 'plans') : True
    is the executed uyeko5 plan in the DEFAULT plans scan? False

    scanned-file counts per type (default liveness vs include_retired):
        plans          default=   85  include_retired=  702
        specs          default=   19  include_retired=   36
        backlog        default=  288  include_retired=  420
        research       default=   87  include_retired=  119
        prompts        default=    2  include_retired=   17
        walkthroughs   default=   24  include_retired=   24
        roadmaps       default=    1  include_retired=    1
        releases       default=    1  include_retired=    1
    ```

    THE MECHANISM IS REAL AND IT IS LATENT, NOT MASKING ANYTHING. `_iter_type_files` excludes a retired record unless `include_retired=True`, and the executed `uyeko5` plan is provably absent from the 85 plans the default sweep scans, while `selectors.resolve()` does NOT skip retired records. So a collision between a RETIRED artifact and a live one WOULD be invisible to a default `aw check` while remaining fully live for the verbs. That is a genuine gap worth its own item. It was NOT, however, hiding this defect: the collision `aw check all` reported was research-to-research between two LIVE docs, so both sides were always scannable.

    I EXPLICITLY RETRACT the authoring note's "the repository-level detector is now BLIND" framing (F-4/F-5/F-6, already marked SUPERSEDED). It was false when review re-measured it and it is false now. Review's own correction is itself now partly stale in its numbers, which is why this was re-measured rather than copied: review reported ONE `check.id6-collision` on the tree, and today's tree carries 17 before the fix (15 after), the extra 15 being pre-existing backlog-vs-`done/` duplicates unrelated to this plan.

    DO THE TWO SURFACES AGREE AFTER THE FIX? YES, which is the point of bounding BOTH:

    ```
    check.id6-collision findings mentioning uyeko5: 0
    selectors.resolve('plans','uyeko5'): n=1 kind=id6
    => AGREE: no collision on either surface, and the verb resolves the one real plan.
    ```

    Had only `selectors` been bounded they would have DIVERGED - `aw check` still asserting a collision no verb could see - which is the two-surfaces-disagree defect shape `check_collisions`'s own docstring warns about, and is why E-02's scope extended into the checker's readers.

    NO CHANGE TO THE RETIRED FILTERING, as required. `git diff -- agent_workflows/check_engine.py` contains ZERO `[-+]` lines touching `def _iter_type_files` or its `not include_retired and is_retired(...)` guard (grep for both over the diff returns nothing; the only `include_retired` lines in the diff are the NEW rule's own pass-through parameter). The `include_retired=True` hoist inside `check_collisions` that IPD `sk7ggr` E-05 installed is likewise untouched.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste every regression case and the region-shape units with their names and results, and the first case FAILING against pre-change code. For the precedence assertion, paste it built on a FILENAME-PRESENT token (`27rjro` and `takpys` still resolving with `kind=substring`) and paste `uyeko5` resolving to ZERO files in `research` and exactly one in `plans`; do NOT assert a substring match for `uyeko5`, which appears in neither filename. Paste the bare `python3 -m pytest` summary line and compare it to a baseline YOU measured, not to the figure this plan originally cited.
  - Observed evidence: all 33 new tests listed with results, 21 of them proven to FAIL against pre-change code, the precedence assertion built on a filename-present token, and the bare suite summary compared to my own measured baseline (+33 passed, same single environmental failure).
    EVERY case with its name and result. 33 new tests: 28 in the new `tests/test_id_metadata_region.py` plus 5 added to `tests/test_selector_zero_open.py`, which already owns selector dialect/precedence behavior.

    ```
    test_selector_zero_open.py::ContentRulesReadOnlyTheMetadataRegionTests::test_a_quoted_id6_resolves_to_the_declaring_record_only PASSED
    test_selector_zero_open.py::ContentRulesReadOnlyTheMetadataRegionTests::test_a_quoting_document_is_not_an_id6_collision PASSED
    test_selector_zero_open.py::ContentRulesReadOnlyTheMetadataRegionTests::test_the_quoting_document_still_resolves_by_its_own_identity PASSED
    test_selector_zero_open.py::ContentRulesReadOnlyTheMetadataRegionTests::test_a_quoted_setid_does_not_widen_a_set_query PASSED
    test_selector_zero_open.py::ContentRulesReadOnlyTheMetadataRegionTests::test_the_content_rules_are_bounded_while_filename_rules_are_not PASSED
    test_id_metadata_region.py::MetadataRegionShapeTests::test_bullet_front_matter_region_ends_at_the_first_h2 PASSED
    test_id_metadata_region.py::MetadataRegionShapeTests::test_an_h1_title_does_not_end_the_region PASSED
    test_id_metadata_region.py::MetadataRegionShapeTests::test_yaml_fenced_region_is_the_leading_fence_block_only PASSED
    test_id_metadata_region.py::MetadataRegionShapeTests::test_yaml_region_excludes_body_bullets_before_the_first_heading PASSED
    test_id_metadata_region.py::MetadataRegionShapeTests::test_a_file_with_no_h2_heading_at_all_still_has_a_region PASSED
    test_id_metadata_region.py::MetadataRegionShapeTests::test_a_header_truncated_mid_region_yields_the_whole_window PASSED
    test_id_metadata_region.py::MetadataRegionShapeTests::test_an_unterminated_yaml_fence_yields_the_whole_input PASSED
    test_id_metadata_region.py::MetadataRegionShapeTests::test_empty_input_is_tolerated PASSED
    test_id_metadata_region.py::BoundedReaderTests::test_a_quoted_block_does_not_override_a_real_declaration PASSED
    test_id_metadata_region.py::BoundedReaderTests::test_status_and_setid_share_the_bound_not_just_id PASSED
    test_id_metadata_region.py::BoundedReaderTests::test_a_yaml_doc_reads_as_ABSENT_rather_than_as_the_quoted_values PASSED
    test_id_metadata_region.py::PublicReaderTests::test_public_readers_are_region_bounded PASSED
    test_id_metadata_region.py::PublicReaderTests::test_the_two_tiers_still_differ_on_whitespace PASSED
    test_id_metadata_region.py::PublicReaderTests::test_a_long_plan_does_not_lose_its_region_to_truncation PASSED
    test_id_metadata_region.py::ResolutionTests::test_a_body_quoted_id6_does_not_resolve_as_that_id6 PASSED
    test_id_metadata_region.py::ResolutionTests::test_the_genuine_artifact_still_resolves_by_id6 PASSED
    test_id_metadata_region.py::ResolutionTests::test_no_collision_across_the_two_trees PASSED
    test_id_metadata_region.py::ResolutionTests::test_precedence_is_preserved_on_a_filename_present_token PASSED
    test_id_metadata_region.py::CheckerBoundTests::test_two_docs_quoting_one_block_are_not_a_collision PASSED
    test_id_metadata_region.py::CheckerBoundTests::test_a_real_duplicate_declaration_is_still_reported PASSED
    test_id_metadata_region.py::CheckerBoundTests::test_the_checker_reads_setid_from_the_region_too PASSED
    test_id_metadata_region.py::OutsideRegionRuleTests::test_it_fires_on_every_offending_file_not_just_the_first PASSED
    test_id_metadata_region.py::OutsideRegionRuleTests::test_it_is_registered_at_info_and_cannot_fail_the_gate PASSED
    test_id_metadata_region.py::OutsideRegionRuleTests::test_an_unregistered_rule_would_have_defaulted_to_error PASSED
    test_id_metadata_region.py::OutsideRegionRuleTests::test_a_conformant_record_is_not_flagged PASSED
    test_id_metadata_region.py::OutsideRegionRuleTests::test_it_fires_on_the_shape_without_needing_a_colliding_counterpart PASSED
    test_id_metadata_region.py::LiveTreeTests::test_no_live_record_declares_an_id_outside_its_region PASSED
    test_id_metadata_region.py::LiveTreeTests::test_every_records_own_id6_still_resolves_to_itself PASSED
    ```

    THE FIRST REQUIRED REGRESSION FAILS AGAINST PRE-CHANGE CODE, measured by stashing the two source edits and running that one test:

    ```
    E   AssertionError: Lists differ: [] != [PosixPath('/tmp/.../20260905-awmetastore-00-ccc333-quoting-doc.research-prompt.md')]
    E   First extra element 0:
    E   PosixPath('/tmp/.../.aw/records/research/20260905-awmetastore-00-ccc333-quoting-doc.research-prompt.md')
    tests/test_id_metadata_region.py:233: AssertionError
    FAILED tests/test_id_metadata_region.py::ResolutionTests::test_a_body_quoted_id6_does_not_resolve_as_that_id6
    1 failed in 0.18s
    ```

    21 of the 33 fail pre-change, so the suite genuinely pins the change rather than passing vacuously.

    THE PRECEDENCE ASSERTION USES A FILENAME-PRESENT TOKEN, per the review correction, and I did NOT assert a substring match for `uyeko5`. On the live tree:

    ```
    27rjro   research  kind=substring n=1   (filename-present -> still resolves AFTER)
    takpys   research  kind=substring n=1   (filename-present -> still resolves AFTER)
    uyeko5   research  kind=None      n=0   (in NEITHER filename -> correctly ZERO)
    uyeko5   plans     kind=id6       n=1   (exactly one: the executed plan)
    ```

    The synthetic twin (`test_precedence_is_preserved_on_a_filename_present_token`) asserts the same shape on a fixture so it cannot rot with the corpus, and `test_the_content_rules_are_bounded_while_filename_rules_are_not` pins the general property that bounding the CONTENT rules did not narrow the later FILENAME rules.

    BARE SUITE, `python3 -m pytest`, actual summary lines. Baseline measured BY ME on this worktree BEFORE any edit, not the figure this plan originally cited:

    ```
    BEFORE (my measured baseline):  1 failed, 7661 passed, 3 skipped, 2 xfailed, 3 warnings in 104.83s
    AFTER  (this change):           1 failed, 7694 passed, 3 skipped, 2 xfailed, 3 warnings in  99.77s
    ```

    DELTA: +33 passed, exactly the 33 tests added, and the SAME single pre-existing failure. Zero regressions.

    THE ONE FAILURE IS ENVIRONMENTAL AND IS NOT THE ONE THE PLAN PREDICTED. It is `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which asserts `OPENCODE_CONFIG_CONTENT` is ABSENT from a non-isolated turn's env; that variable is SET in my own runner turn, so the test reads my harness rather than the code. PROVEN environmental rather than assumed: `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py` gives `43 passed`. The plan's predicted failure (`test_reporting_contract.py`, blamed on an untracked `opencode-recovery/` directory) does NOT occur on this worktree, and `test_orchestrator_retirement` passes as review said. I deleted nothing to make the suite green.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan has been REVIEWED (`/plan-review`, 2026-09-10) and carries `- Readiness: go-pending-approval` as that review's attested output. It must still not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. The authoring note correctly declined to hand-write a readiness field before a review existed; the field is present now because the review happened, and its findings are recorded in `.aw/records/reviews/20260910-idcapture-01-76w6mq-...review.md`.

DO NOT INHERIT F-4 THROUGH F-6 AS WRITTEN; REVIEW FALSIFIED THEM AND THEY ARE MARKED SUPERSEDED IN PLACE. The authoring note claimed the `aw check` symptom had disappeared through MASKING and that the repository detector was now BLIND to the collision class the verbs still hit. Re-measured at HEAD `18d7cc4c`: `aw check all` reports exactly ONE `check.id6-collision`, and it is ON the `27rjro` doc, naming a SECOND live research doc (`takpys`) that quotes the same block. So both sides are scannable, nothing is masked, and check and the verbs agree that something is wrong. The retired-record mechanism is real but LATENT. E-05's rule remains worth building on its own merits (it fires on the SHAPE, needs only one side, and catches a misplaced declaration that no collision rule would), but not for the stated reason.

FOUR MEASUREMENT CORRECTIONS NOT TO INHERIT FROM THIS PLAN'S EARLIER TEXT. (1) Register the new rule at `info`, not `warning`: `warning` fails the gate exactly as `error` does (`drift_exit_code`, measured), so the original instruction defeated its own stated goal. (2) The blast radius is TWO files, not one, and the corpus is 1136 tracked records, not 1006. (3) The suite baseline is `1 failed, 5958 passed, 3 skipped, 2 xfailed`, and the failing test is the environmental `test_reporting_contract.py` case, NOT `test_orchestrator_retirement`, which passes. (4) The `27rjro` doc's own status is `reference`, not `todo`. Also: `uyeko5`'s plan is in `executed/`, so `executed -> reviewed` is an illegal transition (verified) and a post-fix `aw set` refusal is a LIFECYCLE refusal, not a resolution failure.

BOTH OPEN QUESTIONS ARE RESOLVED, so nothing blocks approval on a decision: OQ-01 to `info` by measurement, OQ-02 to BOUND THE PUBLIC READERS from the code (the comment above them records that the drift they exist to prevent is exactly what leaving them unbounded would reinstate). E-03 must still enumerate the driver call sites as evidence.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Do NOT delete the untracked `opencode-recovery/` directory that makes one suite test fail; it belongs to another party in this shared checkout. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE OVERLAP: plan `xo3244` (`selfmdialect`, `From-Backlog: 05aqbj`) also edits `selectors.py` and the same three readers, so re-read the file at execution time and compose with whatever has landed rather than assuming these coordinates; and remember this resolver serves MUTATING verbs, so a regression here misdirects a write, not merely a read. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
