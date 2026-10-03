# IPD: Bound the three surviving unbounded identity readers to the metadata region

- Date: 2026-09-29
- Kind: child
- Concern: Plan `76w6mq` bounded identity extraction to the metadata region for the `selectors` readers and `check_engine._ID_LINE_RE`/`_SET_LINE_RE`, but THREE readers of the same shape were left outside its fence, and the middle one is NOT latent: `status_set._ID_RE`/`_STATUS_RE`/`_SET_RE` back `read_artifact_record`, the reader every `aw set` and `aw ipd set` resolution and every `check_engine.build_dependency_index` lookup goes through, and they read a QUOTED bullet block as a DECLARATION. Measured at HEAD `5c47b462`: `aw set reviewed uyeko5 --dry-run` REFUSES with "id6 collision matching multiple files (a data bug to fix, not overridable by --force)", naming the real executed plan plus TWO research documents that merely QUOTE `- Id: uyeko5` in their bodies, and `match_selector('runflags')` returns those same two research docs beside the plan, so a Set-wide `aw set` reaches two records that are not members of that Set. The same reader reports both quoting documents as `status=reviewed set=runflags` against their own YAML fences (`takpys`/`27rjro`, `status: reference`, `set: awmetastore`), and that wrong status is what `validate_transition_allowed` and `apply_status_change` then gate on: driven directly against a copy, `apply_status_change` read `reviewed` (truth: `reference`) and wrote a history line under a status it never held. The other two readers are genuinely LATENT and are fixed here because they are the same defect in the same shape: `check_engine._ITEM_ID_RE` is applied to whole file bodies at 15 call sites and is measured LIVE-DIVERGENT on exactly those 2 research documents (returns `uyeko5`; bounded returns `None`) while every current call site iterates plans/backlog/specs and so reaches no affected file; and `runner_shared.discover_specs` pairs a region-BOUNDED status read (`selectors.read_front_matter_status`) with that UNBOUNDED id6 read ON THE SAME TEXT, so one record's two fields are read under two different boundary rules (measured: 0 of 38 specs diverge today).
- Scope: Route all three readers through `selectors.metadata_region`, the ONE shared helper `76w6mq` introduced, so every identity/status/setid reader in the toolkit shares one boundary. IN: bounding `status_set.read_artifact_record`'s three bullet reads AND its two YAML fallbacks (the fallbacks are reached on a bullet miss and are unbounded too, so bounding only the bullets would hand a body-quoted `id:`/`status:` the authority the bullets just lost); bounding `check_engine._ITEM_ID_RE`'s reads through one module-local accessor beside the existing `_read_declared_id`, plus `_META_BLOCKS_RELEASE_RE` and `_PLAN_STATUS_RE`, which are measured divergent on the same documents and are read by the release-gate rules; making `runner_shared.discover_specs`' id6 read use that bounded accessor so its two fields share one rule; and outcome tests pinning the DECLARED-over-QUOTED property on each surface. OUT: `artifact_adopt._BULLET_ID_RE` and `scan_body_identities`, which are the MINT substrate and must STAY a superset (bounding them would narrow the collision set minting depends on, and `artifact_core.global_id6s` documents that over-collection is correct there); widening or narrowing any reader's WHITESPACE tolerance, which `selectors.py` records as a separate matching-behavior contract; `selectors._STATUS_RE`'s deliberate 24-record disagreement with `plans_index._META_RE`; editing the two quoting research documents, whose quotation is legitimate content; and any new check rule (`check.id6-outside-metadata-region` already exists and already covers the warn half).
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/check_engine.py, agent_workflows/runner_shared.py, agent_workflows/artifact_core.py, tests/test_status_set_metadata_region.py, tests/test_check_engine_metadata_region.py, CHANGELOG.md
- Item-Dependencies: executed:76w6mq
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: axayfn
- Blocks-Release: next
- Set: idcapture
- Order: 2
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: xvon5j

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: xvon5j verified (set idcapture, attempt 1). [Scope reconciliation - widened-scope agent_workflows/artifact_core.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run)]
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-Y01 (HIGH, fixed), PR-Y02 (HIGH, fixed), PR-Y03 (MEDIUM, fixed), PR-Y04 (MEDIUM, fixed), PR-Y05 (LOW, fixed). Findings recorded in .aw/records/reviews/20260930-idcapture-02-xvon5j-bound-the-three-surviving-unbounded-identity-readers.review.md. This is an unusually well measured plan and most of it verifies exactly: F-01's aw set refusal reproduces verbatim, F-03's three wrong fields reproduce, F-04's three-match runflags query reproduces, F-02's false attribution is confirmed (grep status_set over artifact_adopt.py returns nothing), F-07's single multi-owner id6 with 1 plans + 2 research owners reproduces precisely, F-08/F-09 reproduce to the token (4 of 2650 changed, the same four, inventory unchanged), F-11/F-12 reproduce, F-06's structural claims reproduce including the half-bounded _PLAN_STATUS_RE, and E-05's premise reproduces (38 specs, 0 divergent, both runner_shared sites where described). TWO SERIOUS FINDINGS. PR-Y01: E-01's Expected outcome says the bounded reader answers .../awmetastore for the setid; measured it answers None, because both documents declare set: in a YAML fence and this reader has no YAML set: fallback, which the plan itself forbids adding. E-03 carried the error into its fixture, so a CORRECT implementation would have failed the plan's own test, and an executor chasing the number could have added the forbidden fallback and widened a mutating verb's selector surface under cover of a bounding change. Corrected to DECLARED-OR-NOTHING across E-01, E-03, V-01, V-02 and the gate. PR-Y02: F-05 and E-02 name the 4sd62s REVIEW record as the YAML-fallback divergence; it diverges on neither pattern, the real file is its SPEC twin, and the row's safety argument (no metadata region to speak of) is true of the twin and false of the spec, which answers from its bullets. Repointed with the corrected reasoning. FURTHER: every call-site and divergence count has drifted (sites 15 to 16, _PLAN_STATUS_RE 6 to 7, records 2381 to 2675, inventory 1904 to 2056) while two Expected outcomes still quoted them against the gate's own prohibition, so new F-13 separates drifted from stable figures and both items now demand re-derivation; and _ID_LINE_RE is itself unbounded-divergent on the same two documents when read raw, which F-12's pattern-to-pattern framing obscures, so E-04 now covers it (new F-14). OQ-03 added recording that the set_id correction is a prose fix needing no maintainer acceptance.

- 2026-09-29 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `axayfn`, inheriting its `- Blocks-Release: next` gate and its `bug` work-kind. THE ITEM'S OWN CLASSIFICATION OF READER (3) IS CORRECTED BY MEASUREMENT, and the correction is the main reason this plan is worth executing rather than deferring. The item says all three readers are latent ("Expect zero behavior change on today's corpus for (1) and (2), which is what makes them cheap and safe to close"), and for (1) and (2) that is confirmed exactly. But it inherits from `q1ov25` the framing that `status_set._ID_RE` matters chiefly as the MINT substrate, where over-collection is harmless; that framing is now STALE. The mint path moved: `artifact_core.global_id6s` delegates to `artifact_adopt.repository_id6s`, which builds its set from `artifact_adopt.scan_body_identities`/`_BULLET_ID_RE` and contains NO reference to `status_set` (verified: `grep status_set agent_workflows/artifact_adopt.py` returns nothing). So `status_set._ID_RE` is no longer a mint reader at all; it is the reader behind `read_artifact_record`, i.e. behind `aw set`, `aw ipd set`, `match_selector`, `inventory_all_artifacts` and `check_engine.build_dependency_index`. Measured consequence at HEAD `5c47b462`: `aw set reviewed uyeko5 --dry-run` is REFUSED as an id6 collision naming two research documents that only QUOTE the id6, which is the SAME unaddressable-artifact symptom `cqytxf` filed and `76w6mq` fixed on the other surfaces. That makes reader (3) a LIVE defect on a MUTATING verb, not a latent one, and it means `artifact_core.global_id6s`' own docstring paragraph naming `status_set._ID_RE` as "THE SPECIFIC UNBOUNDED READER BEHIND THIS SET" is now factually wrong; E-06 corrects it. The item's third bullet also asks whether `q1ov25` should absorb this: `q1ov25` is already `done` (closed 2026-09-25 as "OBSOLETE ... subsumed by axayfn item 3"), so the question is settled and this plan carries all three. `- Item-Dependencies: executed:76w6mq` is declared rather than `none` because every item here CALLS `selectors.metadata_region`, which that plan created; it is already `executed`, so the edge is satisfied at authoring time.

## Goal

Make every identity, status and setid reader in the toolkit share ONE boundary, the metadata region, so a document that QUOTES a metadata block can never be read as DECLARING it. Concretely: stop `aw set`/`aw ipd set` refusing a real plan as an id6 collision with two research documents that merely quote its id6, and remove the two remaining latent copies of the same defect before a caller points one of them at a research or prompt record.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the LIVE reader (`status_set`)

- [x] E-01 Bound `status_set.read_artifact_record`'s THREE bullet reads to the metadata region, through the shared helper and not a local copy. The function currently searches `_ID_RE`, `_STATUS_RE` and `_SET_RE` against the WHOLE `text` it just read; search `selectors.metadata_region(text)` instead. `status_set` already imports `selectors` as `_sel` at module level (it uses `_sel.record_dirs` and `_sel.EXCLUDED_RECORD_DIRS`), so no new import and no lazy import is needed and none should be added.

  DO NOT ADD A SECOND REGION PARSER, and do not copy `check_engine._metadata_region`'s wrapper shape either unless a cycle forces it (it should not: the import already exists). `check_engine._metadata_region`'s own comment states the rule this follows: "ONE helper, imported rather than re-derived: a second local region parser is how the reader drift documented at `selectors.read_front_matter_id` happened before."

  DO NOT TOUCH THE THREE PATTERNS THEMSELVES. `status_set._ID_RE`/`_STATUS_RE`/`_SET_RE` are NOT byte-identical to their `selectors` counterparts (verified: `status_set._SET_RE` is `^-\s*Set:` where `selectors._SET_RE` is `^- Set:`, and the two `_ID_RE`s differ in their `(?m)`-versus-flag spelling while matching identically), and harmonizing them is a MATCHING-BEHAVIOR change of the class `selectors.py`'s parity note puts off-limits to a bounding change. What is shared here is the BOUND, not the pattern.

  WHAT MUST NOT BREAK, because these three readers are the WRITER'S neighbours as well as the reader's: `apply_status_change` scans `lines` with `_STATUS_RE.match(line)` LINE BY LINE to find the bullet to rewrite, and two gate-insertion paths do the same. Those are per-line matches on an already-line-split body, not whole-text searches, and they are OUT of this item: do not route them through the region helper (a region string would break the line indexing they depend on). Only the three whole-text searches inside `read_artifact_record` change.
  - Depends on: none
  - Expected outcome: `read_artifact_record` answers a record's OWN declared id6/status/setid, or NOTHING, but never a value quoted from another record's block. CORRECTED AT REVIEW, because the authored expectation was measurably wrong on one field of three and an executor comparing against it would have reported a defect that is not one. On the two live quoting research documents the bounded reader answers `takpys`/`reference`/`None` and `27rjro`/`reference`/`None`, NOT `.../awmetastore`. The setid goes to `None` rather than to the fence value because the two documents declare `set: awmetastore` in a YAML FENCE and `status_set.read_artifact_record` has NO YAML `set:` fallback, a gap this plan's own Deferred section names and deliberately does not fill (adding one would be a widening). So `awmetastore` is unreachable through THIS reader by design; `selectors._read_setid` does answer it (verified), which is why nothing downstream is left broken. The property to assert is DECLARED-OR-NOTHING, never DECLARED-EXACTLY, and E-03's fixture must be built to that. `status_set._ID_RE`, `_STATUS_RE` and `_SET_RE` are byte-unchanged.
  - Execution state: performed

- [x] E-02 Bound the TWO YAML FALLBACKS in the same function, which are unbounded today and would otherwise inherit the authority the bullets just lost. `read_artifact_record` falls back to a local `re.search(r"(?m)^id:\s*([0-9a-z]{6})\s*$", text)` when the bullet id6 misses, and to the parallel `^status:\s*(\S+)$` when the bullet status misses. Both search the WHOLE text. After E-01 the bullet reads MISS on precisely the documents whose bodies quote a foreign block, so these fallbacks become newly reachable on exactly the records that motivated the fix; leaving them unbounded would move the defect rather than remove it.

  THIS IS MEASURED, NOT PRECAUTIONARY, and it is the one place the corpus already shows a body-level YAML-shaped line. Sweeping every tracked record, an unbounded `^id:` read diverges from a bounded one on exactly ONE file: `.aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`, whose body carries `id: abc123` and `status: approved` as literal example lines, where the unbounded read returns those and the bounded read returns `None`. CORRECTED AT REVIEW: an earlier draft of this item named that record's REVIEW twin (`.aw/records/reviews/20260925-4sd62s-01-...review.md`), which diverges on neither pattern, and argued the file was safe because "the whole record has no metadata region to speak of". That argument belongs to the review file and does not hold for the spec, which HAS a metadata region declaring `- Id: 4sd62s` and `- Status: reviewed`. So the correct statement of why the spec is safe today is that its BULLET reads HIT, which means the fallbacks are never reached, not that the record is empty. Bound them anyway: the divergence is real, the file is real, and the only thing standing between it and a wrong answer is a bullet read that a future reformat could remove. Re-derive this sweep at execution time rather than trusting the count here.

  Search `selectors.metadata_region(text)` for both fallbacks. Leave the `set_id` path alone: it has no YAML fallback in this function (unlike `selectors._read_setid`, which does), and ADDING one is a widening, not a bounding, and is out of scope.
  - Depends on: E-01
  - Expected outcome: both YAML fallbacks read the metadata region only. The one divergent record (the `4sd62s` SPEC, not its review twin) keeps its current answers, `4sd62s`/`reviewed` from its bullets, because those hit and the fallbacks were never reached for it. No record in the corpus gains or loses an id6 or status from the fallback path.
  - Execution state: performed

- [x] E-03 Pin the LIVE symptom as an OUTCOME test in `tests/test_status_set_metadata_region.py`, driving the real surfaces rather than asserting on a regex. New file, because the property under test spans `read_artifact_record`, `inventory_all_artifacts` and `match_selector` and does not belong inside `tests/test_status_set.py`'s existing setter-behavior classes.

  BUILD A FIXTURE TREE, do not assert against the live repository corpus. The two quoting documents are real records another agent may re-file, archive or rename, so a test keyed to them would rot; and `aw check`-style corpus counts are explicitly not assertable per the execution contract. Write a fixture record whose YAML fence declares `id: aaa111`, `status: active`, `set: fxset` and whose BODY quotes `- Id: bbb222`, `- Status: approved`, `- Set: otherset`. This shape reproduces the defect exactly: driven at HEAD against such a fixture, `read_artifact_record` returned `id6=bbb222 status=approved set=otherset`, i.e. all three fields taken from the quotation.

  ASSERT ALL THREE FIELDS, not just the id6, and ASSERT THE RIGHT PROPERTY ON EACH. The `76w6mq` measurement record makes the coverage reason explicit: the two quoting research documents reported a wrong status AND a wrong setid too, and a single-field test leaves two thirds of the bound unguarded. But the three fields do NOT all recover their fence value, and a test written as if they do will fail for a correct implementation. With a YAML-fence fixture the bounded reader answers `aaa111` and `active` from the fence FALLBACKS, while `set_id` answers `None` because this reader has no YAML `set:` fallback (measured at review on the two live documents). So assert `id6 == "aaa111"`, `status == "active"`, and `set_id is None` (explicitly NOT `"otherset"`), and state in the test's docstring that the invariant is DECLARED-OR-NOTHING: the quoted value must never win, and an absent value is a correct answer here. IF YOU PREFER A BULLET-FENCE FIXTURE, where all three fields DO recover (`- Id:`/`- Status:`/`- Set:` inside the metadata region above the quotation), add that as a SECOND fixture rather than replacing the YAML one: the YAML case is the shape the two live documents actually have and therefore the one that reproduces the reported defect.

  ASSERT THROUGH `match_selector` AS WELL AS THROUGH THE READER, because the reader answer is the mechanism while the user-visible claim is "a quoting document does not collide with the artifact it quotes". Add a second fixture record that genuinely DECLARES `- Id: bbb222` in bullet front matter, then assert `match_selector('bbb222', ...)` returns exactly that ONE record and not the quoting one. That is the assertion whose failure at HEAD is the `aw set` refusal this plan exists to remove.
  - Depends on: E-01, E-02
  - Expected outcome: a new test file whose assertions FAIL at pre-change HEAD and pass after E-01/E-02, covering the three declared fields and the single-match selector property.
  - Execution state: performed

### Task group 2: the two LATENT readers

- [x] E-04 Bound `check_engine._ITEM_ID_RE`'s reads through ONE module-local accessor, not at each of its call sites. This module ALREADY has the right pattern to copy: `_read_declared_id(text)` wraps `_ID_LINE_RE.search(_metadata_region(text))` and exists precisely so the bound lives in one place. Add the sibling accessor for `_ITEM_ID_RE` beside it (or, if measurement shows the two patterns answer identically on every record, route the `_ITEM_ID_RE` sites at `_read_declared_id` itself and say so with the measurement) and change every `_ITEM_ID_RE.search(...)` site to call it. Count them yourself rather than trusting a figure here, because these figures HAVE ALREADY DRIFTED (F-13): authoring recorded 15 calls with a 12/3 split, review measured SIXTEEN with a 13/2/1 split across `text`, `plan_text` and `_t`. The lesson survives the drift and is the point: a search for the `(text)` spelling alone MISSES the others and is the obvious way to leave this half done. ALSO CONFIRM NO RAW `_ID_LINE_RE.search(` SURVIVES: that pattern is bounded at the `_read_declared_id` accessor but is itself unbounded-divergent on the same two documents when read raw (F-14), so a raw read of it is the same defect wearing the other pattern's name.

  MEASURE THE TWO PATTERNS BEFORE DECIDING WHICH SHAPE TO USE, because the answer determines whether one accessor or two is correct. `_ID_LINE_RE` is `^- Id:\s*([0-9a-z]{6})\s*$` and `_ITEM_ID_RE` is `^- Id:[ \t]*([0-9a-z]{6})[ \t]*$`; they differ in whether `\s` (which includes a newline) or `[ \t]` follows the colon. Swept over the 2381 tracked records they diverge on ZERO files, but that is a corpus fact and not a pattern equivalence, so state the measurement and pick deliberately rather than assuming. DO NOT change either pattern.

  ALSO BOUND `_META_BLOCKS_RELEASE_RE` AND `_PLAN_STATUS_RE`, which are the same defect in the same module and are MEASURED DIVERGENT. Swept over the same corpus: `_META_BLOCKS_RELEASE_RE` unbounded differs from bounded on THREE files (the two quoting research documents, plus one plan where the bounded read still finds it, so only the two research ones are wrong answers), and `_PLAN_STATUS_RE` on SIX at authoring and SEVEN at review (`README.md` joined the set), which is a live figure to re-derive and not a bar (F-13). NOTE `_META_BLOCKS_RELEASE_RE` HAS EIGHT CALL SITES, a count this plan did not state while requiring all of them bounded; count them yourself. These matter more than their counts suggest because they feed the RELEASE-GATE rules (`check_engine.evaluate_blocking_close`, `check_engine.check_release_gate_consistency` with its `check.from-backlog-gate-mismatch` and `check.orphaned-live-blocker` sweeps) and five `production_checks` call sites, where a phantom `- Blocks-Release: next` read out of a quoted block asserts a gate that does not exist. Note `_PLAN_STATUS_RE` is ALREADY bounded at two of its sites (`_metadata_region(text)` is passed at both) and unbounded at the third, which is exactly the half-fixed shape this plan exists to finish.

  DO NOT TOUCH `_ITEM_PRIORITY_RE` or `_ITEM_WORK_KIND_RE` beyond what consistency requires: both measure ZERO divergence over the corpus. If bounding them falls out of routing their neighbours through one accessor, that is fine and should be stated; do not go out of your way to leave them inconsistent, and do not claim a fix where no divergence exists.
  - Depends on: none
  - Expected outcome: `_ITEM_ID_RE`, `_META_BLOCKS_RELEASE_RE`, `_PLAN_STATUS_RE` and `_ID_LINE_RE` are read only within the metadata region, through an accessor rather than per-site duplication, with ZERO raw unbounded `.search(` calls on any of the four remaining (verified by count over every spelling, not the `(text)` one alone). The answers that change are the ones your OWN sweep reports, in every case from a QUOTED value to `None`; re-derive the per-pattern divergence rather than matching the figures here, which have drifted once already (F-13: `_PLAN_STATUS_RE` measured 6 at authoring and 7 at review). Report your before and after numbers with the sweep that produced them. No pattern string is edited.
  - Execution state: performed

- [x] E-05 Make `runner_shared.discover_specs` read BOTH its fields under ONE boundary rule. It currently pairs `selectors.read_front_matter_status` (region-bounded by `76w6mq`) with `check_engine._ITEM_ID_RE.search(text)` (unbounded) on the same `text`, which is the specific inconsistency backlog `axayfn` item 2 records. After E-04 gives `check_engine` a bounded accessor, call THAT rather than the raw pattern, so the function acquires the bound from the same authority instead of growing its own.

  THIS IS LATENT AND MUST BE REPORTED AS SUCH. Measured over the live spec corpus at HEAD: 38 spec records enumerate through `check_engine._iter_spec_records`, and ZERO of them answer differently bounded versus unbounded, so this item fixes an inconsistency and changes no current behavior. Do not claim a live fix here. The reason it is worth the edit is stated in `discover_specs`' own docstring premise: it reads identity and status "through the SHARED authorities, not by fresh regexes", and a bounded/unbounded pair on one text silently violates that premise for whichever spec next quotes a metadata block.

  ALSO FIX THE SECOND SITE IN THE SAME FILE, which the backlog item does not name and which measurement found: `runner_shared` uses `_ce._ITEM_ID_RE.search(p.read_text(...))` again inside the spec-dispatch "declares no `- Id:`" message branch, to decide whether to tell an operator to run `aw rename specs --to-id6`. Unbounded, a spec that merely QUOTES an `- Id:` would suppress that advice while `discover_specs` still skips the file, i.e. the operator is told nothing and the record stays invisible. Route it through the same accessor.
  - Depends on: E-04
  - Expected outcome: both `runner_shared` identity reads go through the bounded accessor; `discover_specs` reads its id6 and its status under one boundary rule. Spec discovery is byte-identical on today's corpus (0 of 38 diverge), which is stated as the expected NO-CHANGE outcome rather than presented as a fix.
  - Execution state: performed

- [x] E-06 Correct `artifact_core.global_id6s`' now-false attribution, and state where the mint reader actually lives. Its docstring asserts "THE SPECIFIC UNBOUNDED READER BEHIND THIS SET IS `status_set._ID_RE`, and it is OUTSIDE `76w6mq`'s declared scope ... Recorded as backlog `q1ov25` rather than fixed here". Both halves are now wrong: the mint set is built by `artifact_adopt.repository_id6s` via `scan_body_identities`/`_BULLET_ID_RE` and touches `status_set` NOWHERE (verified: `grep status_set agent_workflows/artifact_adopt.py` returns nothing), and `q1ov25` is `done`.

  REWRITE IT TO SAY WHAT IS TRUE AND WHY THE SUPERSET SURVIVES, which is the load-bearing part. The surrounding paragraphs are CORRECT and must stand: the set IS a conservative superset, over-collection IS harmless for minting and wrong for checking, and `uyeko5` IS in the set partly because two research documents quote it. What changes is only the ATTRIBUTION: name `artifact_adopt.scan_body_identities`/`_BULLET_ID_RE` as the unbounded reader, say that it is deliberately left unbounded BY THIS PLAN because minting requires a superset, and point at this plan (`xvon5j`) for the readers that were bounded.

  DO NOT BOUND THE MINT READER. That is the one place in this codebase where over-collection is the correct behavior, and narrowing it would let a mint hand out an id6 that a research document already quotes, reintroducing the collision class from the other direction. Say so explicitly at the site so the next reader does not "finish the job".

  NOTE `agent_workflows/artifact_core.py` IS NOT IN `- Scope-Paths:`, DELIBERATELY. This is a comment-only correction to a file whose behavior this plan does not touch, and adding it to the fence would invite an executor to edit the mint path. Record the correction as REQUIRED and execute it as a documentation change with the path declared: if the scope gate refuses a comment edit to an undeclared path, ADD `agent_workflows/artifact_core.py` to `- Scope-Paths:` at that point and record it in the finalize scope reconciliation rather than skipping the correction or editing anything else in the file.
  - Depends on: E-01
  - Expected outcome: `global_id6s`' docstring names the real mint reader, states that it stays unbounded on purpose, and cites this plan for the readers that were bounded. No executable line in `artifact_core.py` changes.
  - Execution state: performed

- [x] E-07 Pin the two LATENT readers as outcome tests in `tests/test_check_engine_metadata_region.py`, and record one CHANGELOG line. The tests build a fixture records tree (same reason as E-03: no assertions against the live corpus) containing a record that DECLARES one id6 in bullet front matter and a second record that QUOTES that same id6 in its body, then assert through the real rule surfaces: that `check_collisions` reports no `check.id6-collision` between them, and that `build_dependency_index` gives the quoted id6 exactly ONE owner rather than two.

  ASSERT THROUGH `build_dependency_index`, which is the single highest-leverage assertion available here and the one that proves the fix reaches beyond `aw check`. At HEAD it reports `uyeko5` as a MULTI-OWNER id6 (1 `plans` + 2 `research`), and it is the index `check_engine._resolve_edge`, `_carrier_index`, `status_set.resolve_dependency_edge_targets` and `runner_shared` all consume, so a multi-owner phantom is what would make a legitimate `Item-Dependencies: executed:<id6>` edge resolve `ambiguous`. Verified at HEAD that the edge does NOT yet resolve ambiguous for `uyeko5` (the type filter narrows it to the one `plans` owner first), so state that honestly: the index is polluted and the type filter is currently masking it on this particular id6. Assert the POLLUTION is gone, not that a previously-broken edge now resolves.

  ALSO ADD ONE `- Fixed:` CHANGELOG LINE under the pending release, describing the user-visible effect in user-facing prose (no em or en dashes): that `aw set` and `aw ipd set` no longer refuse a record as an id6 collision because another document quotes its id6 as an example. Do NOT describe the latent readers there; a changelog entry for a no-op change misleads a reader about what shipped.
  - Depends on: E-04, E-05
  - Expected outcome: a new test file whose collision and dependency-index assertions fail at pre-change HEAD and pass after; one CHANGELOG line covering only the live behavior change.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation in this plan follows that rule; the backlog item's own line numbers were re-resolved by symbol before being relied on.
- ONE REGION HELPER, IMPORTED, NEVER RE-DERIVED. `selectors.metadata_region` is the single boundary authority; `check_engine._metadata_region` is a thin accessor that imports it, and its comment states that a second local parser "is how the reader drift documented at `selectors.read_front_matter_id` happened before". This plan adds accessors, never parsers.
- A READER'S BOUND AND A READER'S PATTERN ARE SEPARATE CONTRACTS. `selectors.py` documents at length that `read_front_matter_id`/`read_front_matter_status` deliberately use a LOOSER whitespace pattern than the module's own strict readers, that widening the strict pair is a matching-behavior change (they disagree with `plans_index._META_RE` on 24 records ON PURPOSE), and that `76w6mq` therefore shared the BOUND while leaving the PATTERNS distinct. This plan follows that split exactly.
- THE MINT PATH IS THE DOCUMENTED EXCEPTION TO BOUNDING. `artifact_core.global_id6s` and `artifact_adopt.repository_id6s` want a conservative SUPERSET, and `artifact_adopt.scan_body_identities` is labelled "a REPORTING function, never a source of a minted id". Over-collect for minting; parse precisely for checking.
- `status_set` ALREADY IMPORTS `selectors` AS `_sel` at module level, so E-01/E-02 need no new import. Verified by the existing `_sel.record_dirs` and `_sel.EXCLUDED_RECORD_DIRS` call sites.
- SHARED CHECKOUT. `agent_workflows/check_engine.py` and `agent_workflows/runner_shared.py` are among the most contended files here and other pending plans declare them. Re-read both at execution time, locate every symbol by NAME, and verify the staged set before and after every commit attempt.

## Findings

| ID | Severity | Finding | Evidence |
| --- | -------- | ------- | -------- |
| F-01 | HIGH | READER (3) IS LIVE, NOT LATENT, AND IT BREAKS A MUTATING VERB. The backlog item expects "zero behavior change on today's corpus" for readers (1) and (2) and inherits `q1ov25`'s framing that (3) matters as a mint-set concern. Measured, (3) is the one reader with a live symptom: `aw set` REFUSES a real plan as an id6 collision, with a refusal that says it is "not overridable by --force". That is the same unaddressable-artifact symptom `cqytxf` filed and `76w6mq` fixed elsewhere. | `python3 -m agent_workflows set reviewed uyeko5 --dry-run` prints `FAIL Selector 'uyeko5' is a id6 collision matching multiple files (a data bug to fix, not overridable by --force)` naming the executed plan plus the two `awmetastore` research documents |
| F-02 | HIGH | THE MINT-SUBSTRATE ATTRIBUTION IN `artifact_core.global_id6s` IS STALE AND POINTS A FUTURE READER AT THE WRONG FILE. Its docstring names `status_set._ID_RE` as "THE SPECIFIC UNBOUNDED READER BEHIND THIS SET". The mint set is actually built by `artifact_adopt.repository_id6s` through `scan_body_identities`/`_BULLET_ID_RE`; `artifact_adopt` references `status_set` nowhere. Left uncorrected, the next reader either bounds `status_set` believing it protects minting (it does not) or declines to bound it believing minting needs the superset (it does not). | `grep status_set agent_workflows/artifact_adopt.py` -> no match; `inspect.getsource(artifact_adopt.repository_id6s)` contains zero `status_set` mentions; `global_id6s` body is `return set(_adopt.repository_id6s(Path(repo_root)))` |
| F-03 | HIGH | THE WRONG STATUS IS NOT MERELY DISPLAYED, IT IS GATED ON AND WRITTEN UNDER. Driven directly against a copy of one quoting document, `read_artifact_record` reported `status=reviewed` (its YAML fence says `reference`), `validate_transition_allowed(rec, "active")` returned `(True, None)` off that wrong prior status, and `apply_status_change` wrote a `## Workflow history` line. So the defect reaches the transition validator and the writer, not just the resolver. | direct drive of `status_set.read_artifact_record` / `validate_transition_allowed` / `apply_status_change` on a copied fixture under a scratch root; reader answered `uyeko5`/`reviewed`/`runflags` against the fence's `takpys`/`reference`/`awmetastore` |
| F-04 | MEDIUM | THE COLLISION IS NOT THE ONLY LIVE SELECTOR ERROR: A SETID QUERY REACHES NON-MEMBERS. `match_selector('runflags')` returns THREE records, the real `runflags` plan plus the two research documents whose bodies quote `- Set: runflags`. Because `aw set` treats a setid as a legitimate MULTI-target selector (a Set is a group, no `--force` needed), a Set-wide transition would reach two records that are not members of that Set. That is a wrong WRITE, not a wrong read, and the backlog item does not mention it. | `status_set.match_selector('runflags', inventory_all_artifacts(root), root)` returns 1 `plans` + 2 `research`; under a bounded reader the same call returns 1 |
| F-05 | MEDIUM | THE YAML FALLBACKS ARE UNBOUNDED TOO, AND BOUNDING ONLY THE BULLETS WOULD MOVE THE DEFECT RATHER THAN REMOVE IT. `read_artifact_record`'s `^id:`/`^status:` fallbacks fire exactly when the bullet read misses, which after E-01 is precisely the quoting-document case. THE DIVERGENT FILE IS MISIDENTIFIED IN THE AUTHORED ROW AND THE REAL ONE IS A WORSE CASE. The row names `.aw/records/reviews/20260925-4sd62s-01-...review.md`; that file diverges on NEITHER pattern (measured: unbounded and bounded both answer `None`/`None`). The actual divergent file is its SPEC twin, `.aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`, whose body carries `id: abc123` and `status: approved` as literal example lines. That matters beyond the name: the row's safety argument is that "the whole record has no metadata region to speak of" and "both readers answer `None` for it at HEAD", which is TRUE of the review file and FALSE of the spec. The spec has a real metadata region declaring `- Status: reviewed` and `- Id: 4sd62s`, so `read_artifact_record` answers `4sd62s`/`reviewed` today from the BULLETS and the fallbacks are simply not reached. The bound is still the right fix and the answer still does not change, but for a different reason than the row gives: the fallback is unreachable because the bullets HIT, not because the record is empty. | Driven at review on both files. Review file: unbounded `^id:`/`^status:` -> `None`/`None`, bounded -> `None`/`None`, `read_artifact_record` -> `(None, None, None)`. Spec file: unbounded -> `abc123`/`approved`, bounded -> `None`/`None`, `read_artifact_record` -> `('4sd62s', 'reviewed', None)`, with `id: abc123` and `status: approved` present as body lines under a metadata region that declares `- Id: 4sd62s`. Corpus sweep over 2675 records finds exactly this ONE file divergent on either pattern. |
| F-06 | MEDIUM | TWO MORE `check_engine` PATTERNS ARE MEASURED DIVERGENT AND FEED THE RELEASE GATES, AND THE BACKLOG ITEM NAMES NEITHER. `_META_BLOCKS_RELEASE_RE` diverges on 3 files and `_PLAN_STATUS_RE` on 6. A phantom `- Blocks-Release: next` read from a quoted block asserts a release gate that does not exist, and these patterns are consumed by `check_engine.evaluate_blocking_close`, `check_engine.check_release_gate_consistency` and `production_checks` (5 sites). `_PLAN_STATUS_RE` is already bounded at two of its three sites, i.e. half-fixed. | corpus sweep: `_ITEM_ID_RE` 2 divergent, `_META_BLOCKS_RELEASE_RE` 3, `_PLAN_STATUS_RE` 6, `_ITEM_PRIORITY_RE` 0, `_ITEM_WORK_KIND_RE` 0, `_META_FROM_BACKLOG_RE` 0; `check_engine.py` passes `_metadata_region(text)` to `_PLAN_STATUS_RE` at two sites and raw `text` at a third |
| F-07 | MEDIUM | THE DEPENDENCY INDEX IS POLLUTED TODAY, AND THE TYPE FILTER IS MASKING IT. `build_dependency_index` reports exactly ONE multi-owner id6 in this repository, `uyeko5`, with 1 `plans` + 2 `research` owners, and that index backs `_resolve_edge`, `_carrier_index`, `status_set.resolve_dependency_edge_targets` and a `runner_shared` consumer. Verified an `Item-Dependencies` edge for it still resolves `ok` rather than `ambiguous`, because the edge's type filter narrows to the single `plans` owner first. So the pollution is real and currently harmless on this id6; a same-type quotation would not be. | `build_dependency_index(root).owners['uyeko5']` -> 3 owners across `plans`/`research`; multi-owner count over the whole index is 1; `_resolve_edge(ItemDependency('state','ipd','executed','uyeko5'), index)` -> `('ok', None)` |
| F-08 | LOW | THE CORPUS-WIDE BLAST RADIUS OF THE FULL FIX IS FOUR SELECTOR TOKENS, WHICH IS WHAT MAKES THIS SAFE TO EXECUTE. Simulating the bounded reader and sweeping every id6, setid and status token in both inventories (2476 tokens), exactly 4 answers change: `uyeko5` 3 -> 1, `runflags` 3 -> 1, and two backtick-quoted setid tokens (`` `awoptimize` ``, `` `lane-branch-triage` ``) 1 -> 0. Inventory size is unchanged at 1904 records. | token sweep with `read_artifact_record` monkeypatched to the bounded form: `SELECTOR ANSWERS CHANGED for 4 of 2476 tokens` |
| F-09 | LOW | TWO OF THOSE FOUR CHANGES ARE A SECOND, UNRELATED DEFECT BEING CORRECTED AS A SIDE EFFECT, AND THAT MUST BE STATED RATHER THAN ABSORBED SILENTLY. `` `awoptimize` `` and `` `lane-branch-triage` `` currently resolve to a record because `status_set._SET_RE` reads a BODY prose bullet (`- Set: \`awoptimize\``) from a YAML-fenced roadmap/findings document. Bounding makes them resolve to nothing, which is CORRECT (those records declare `set: awoptimize` / `set: lane-branch-triage` unbackticked in their fences, and `selectors._read_setid` already answers the clean value). But it means a backticked-token query that returns one file today returns none after. `selectors._read_setid`'s own comment documents the backtick-verbatim behavior as deliberate and names the test that pinned it, so do not "fix" it further here. NOTE that named test (`tests/test_cli_find.py::BacktickSetValueIsPinnedTests`) NO LONGER EXISTS in the trimmed suite, so the citation in `selectors.py` is itself stale; the DECISION it records still stands and is not this plan's to revisit. | the two records' first 18 lines show a YAML fence declaring `set: awoptimize` / `set: lane-branch-triage` plus a BODY bullet `- Set: \`awoptimize\`` under the H1; `selectors._read_setid` answers `awoptimize`/`lane-branch-triage` while `status_set` answers the backticked form; `grep -rn BacktickSetValueIsPinnedTests tests/` returns no match |
| F-10 | LOW | `q1ov25` IS ALREADY CLOSED, SO THE BACKLOG ITEM'S THIRD QUESTION IS SETTLED. Item `axayfn` asks "Check whether q1ov25 should absorb this or stay separate." `q1ov25` is in `backlog/done/` with the history line "2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: subsumed by axayfn item 3". No action; recorded so the executor does not reopen it. | `.aw/records/backlog/done/20260920-idreader3-01-q1ov25-statusset-id-reader-unbounded.backlog.md`, `- Status: done` |
| F-11 | LOW | THE THREE `status_set` PATTERNS ARE NOT BYTE-IDENTICAL TO THEIR `selectors` TWINS, so "consolidate the readers" is NOT available as a cheap alternative to bounding them. `status_set._SET_RE` is `^-\s*Set:` where `selectors._SET_RE` is `^- Set:` (a real tolerance difference), and the `_ID_RE`/`_STATUS_RE` pairs differ only in inline-`(?m)`-versus-flag spelling. Swapping `status_set` onto the `selectors` readers would therefore change matching, not just bounding. | printed both patterns and flags side by side: `status_set._SET_RE` `'^-\s*Set:\s*(.+?)\s*$'` vs `selectors._SET_RE` `'(?m)^- Set:\s*(.+?)\s*$'`, IDENTICAL: False for all three pairs |
| F-12 | LOW | `_ID_LINE_RE` AND `_ITEM_ID_RE` ANSWER IDENTICALLY ON THE WHOLE CORPUS, which is what makes E-04's one-accessor option viable, but they are not equivalent PATTERNS and the distinction should be stated rather than assumed. | corpus sweep: `_ID_LINE_RE` vs `_ITEM_ID_RE` divergent on 0 of 2381 records; patterns differ in `\s*` versus `[ \t]*` after the colon, so a value followed by a newline-swallowing match is theoretically reachable |
| F-13 | MEDIUM | EVERY CALL-SITE AND DIVERGENCE COUNT IN THIS PLAN HAS ALREADY DRIFTED, WHICH THE GATE FORBIDS RELYING ON AND WHICH TWO ITEMS NONETHELESS STATE AS EXPECTED VALUES. Re-measured at review against the authored figures: `_ITEM_ID_RE.search(` sites 15 -> 16 (13 on `text`, 2 on `plan_text`, 1 on `_t`, so the authored 12/3 split is also stale); `_PLAN_STATUS_RE` divergence 6 -> 7 (adding `README.md`); `_META_BLOCKS_RELEASE_RE` sites are EIGHT, a figure the plan never states while E-04 requires bounding all of them; the record sweep is 2675 rather than 2381; and `status_set.inventory_all_artifacts` returns 2056 rather than the 1904 F-08 records. UNCHANGED and therefore safe to rely on: the 2-file `_ITEM_ID_RE` divergence, the 3-file `_META_BLOCKS_RELEASE_RE` divergence, ZERO for `_ITEM_PRIORITY_RE`/`_ITEM_WORK_KIND_RE`/`_META_FROM_BACKLOG_RE`, the 4-token selector change with the same four tokens, the 38-spec 0-divergent measurement, and the single multi-owner id6. The gate already says not to assert against these numbers; E-04's and E-05's Expected outcomes still quote some, so they are corrected to demand re-derivation. | Side-by-side re-measurement at review HEAD. `grep -c '_ITEM_ID_RE.search(' agent_workflows/check_engine.py` -> 16; `grep -o '_ITEM_ID_RE.search([a-z_]*)' \| sort \| uniq -c` -> 13 `text`, 2 `plan_text`, 1 `_t`; `grep -n '_META_BLOCKS_RELEASE_RE.search(' ` -> 8 sites; corpus sweep of 2675 records -> `_PLAN_STATUS_RE` 7 divergent. |
| F-14 | MEDIUM | `_ID_LINE_RE` IS ITSELF UNBOUNDED AT ITS OWN READS AND MEASURES DIVERGENT ON THE SAME TWO DOCUMENTS, WHICH F-12 OBSCURES BY COMPARING THE TWO PATTERNS TO EACH OTHER RATHER THAN EACH TO ITS BOUND. F-12 reports `_ID_LINE_RE` vs `_ITEM_ID_RE` as 0-divergent, which review confirms exactly (0 of 2675). But unbounded-vs-BOUNDED, `_ID_LINE_RE` diverges on the SAME 2 research documents as `_ITEM_ID_RE` (both return `uyeko5` raw and `None` bounded). That is not a contradiction of `76w6mq`, which bounded `_ID_LINE_RE` at the `_read_declared_id` ACCESSOR: the pattern is safe wherever it is read through that accessor and unsafe anywhere it is read raw. So the executor's job at E-04 is not only to add a sibling accessor but to confirm that NO raw `_ID_LINE_RE.search(` survives either, which the plan never asks. Recorded because a reader of F-12 could conclude `_ID_LINE_RE` needs no attention. | Corpus sweep at review: `_ID_LINE_RE` unbounded-vs-bounded divergent on the two `awmetastore` documents (`uyeko5` -> `None`), identical to `_ITEM_ID_RE`; `_ID_LINE_RE` vs `_ITEM_ID_RE` divergent on 0 of 2675, confirming F-12. |

## Proposed changes (ordered, validatable)

1. `status_set.read_artifact_record`: three bullet searches move from `text` to `selectors.metadata_region(text)` (E-01). Patterns untouched.
2. Same function: the two YAML fallbacks move to the region (E-02).
3. New `tests/test_status_set_metadata_region.py`: fixture-tree outcome tests for the declared-over-quoted property on all three fields, plus the single-match `match_selector` property (E-03).
4. `check_engine`: one bounded accessor for `_ITEM_ID_RE` beside the existing `_read_declared_id`; all 15 call sites plus `_META_BLOCKS_RELEASE_RE` and `_PLAN_STATUS_RE`'s remaining unbounded site route through the region (E-04).
5. `runner_shared`: `discover_specs`' id6 read and the spec-dispatch "declares no `- Id:`" probe both call that accessor (E-05).
6. `artifact_core.global_id6s`: docstring attribution corrected to name `artifact_adopt.scan_body_identities`/`_BULLET_ID_RE`, with the deliberate no-bound rationale and a pointer to this plan (E-06).
7. New `tests/test_check_engine_metadata_region.py` plus one CHANGELOG `- Fixed:` line for the live `aw set` behavior only (E-07).

## Deferred / out of scope (with reason)

- BOUNDING THE MINT READER `artifact_adopt._BULLET_ID_RE` / `scan_body_identities`. Deliberately NOT done, and E-06 writes the reason at the site so it is not "finished" later by mistake: the mint collision set must be a conservative SUPERSET, so refusing to mint an id6 that some document merely quotes costs one draw out of 36**6 while narrowing the set risks minting a genuine duplicate. `artifact_core.global_id6s` already states the asymmetry ("Over-collect for minting; parse precisely for checking"); this plan corrects only WHICH reader it names.
  - Carrier-Declined: NOTHING IS OWED, because this is a design conclusion rather than unbuilt work. The reader is CORRECT as it stands: over-collection is the required behavior for minting, so there is no defect to carry and filing an item would invite a future agent to "finish" bounding the one reader that must stay unbounded. That is not hypothetical, it is the measured failure mode this row exists to prevent: `artifact_core.global_id6s`' docstring already named the wrong reader as the mint substrate (F-02) and E-06 corrects it precisely so the next reader does not act on it. The durable record is the comment E-06 leaves at the site, which is where a reader tempted to bound it will actually be standing.
- HARMONIZING THE READER PATTERNS ACROSS `status_set` AND `selectors`. F-11 measures them as genuinely different (`^-\s*Set:` vs `^- Set:`), so a swap is a matching-behavior change, which `selectors.py`'s parity note puts in a different class from a bounding change. `76w6mq` made exactly this split (share the BOUND, keep the PATTERNS distinct) and this plan follows it.
  - Carrier-Declined: NO DEFECT IS MEASURED HERE, so nothing is owed. F-11 establishes only that the patterns DIFFER, not that any difference produces a wrong answer, and the corpus sweep behind F-08 found the bounded reader changes 4 selector answers with none attributable to a pattern difference. Harmonizing them would be a deliberate matching-behavior change requiring its own measurement of who gains and loses a match, and `selectors.py` records that its own strict/loose split is a CONTRACT (the strict pair disagrees with `plans_index._META_RE` on 24 records on purpose). Filing an item would assert that convergence is wanted, which no evidence here supports and which the existing comments argue against.
- THE TWO BACKTICKED-SETID TOKENS CEASING TO RESOLVE (F-09). Accepted as a correct consequence and recorded rather than repaired: those documents declare a clean `set:` in their YAML fences and `selectors._read_setid` already answers it. Chasing the backtick behavior further would revisit a decision `selectors._read_setid`'s comment records as deliberate (it cites `tests/test_cli_find.py::BacktickSetValueIsPinnedTests`, which the trimmed suite no longer contains, so the decision now rests on the comment alone; restoring that coverage is a separate concern and not this plan's).
  - Carrier-Declined: NOTHING IS OWED BY THIS PLAN, and the one thing arguably owed already has a home. The resolution change is CORRECT rather than a regression (both records declare a clean unbackticked `set:` that `selectors._read_setid` already reads), so there is no defect to carry; whether the backticked form SHOULD keep resolving is a maintainer's scope question, which is why it is OQ-02 rather than a deferred defect. The separable observation, that the trimmed suite no longer contains the test `selectors.py` cites as the pin, is a TEST-COVERAGE gap in a file this plan does not touch and is the same class of loss already owned by pending plan `3xd1pm` (`- Scope-Paths: tests/test_selector_two_dialect_readers.py`), which exists to restore selector-reader coverage the same trim removed. Filing a second item for one more casualty of that trim would fragment work that plan is already shaped to absorb.
- ADDING A YAML `set:` FALLBACK TO `status_set.read_artifact_record`. It has none today (unlike `selectors._read_setid`), and adding one WIDENS resolution rather than bounding it. A separate concern; not filed here because it is a deliberate asymmetry rather than a measured defect.
  - Carrier-Declined: NO MEASUREMENT SHOWS A WRONG ANSWER, so nothing is owed. Every record whose setid this plan touches resolves correctly after bounding (F-08: 4 changed tokens, all accounted for), and the missing fallback costs a YAML-fenced record only its `set_id` in `status_set`'s inventory, where `selectors._read_setid` already supplies the value on the resolution path that matters. ADDING the fallback is a WIDENING of a mutating verb's selector surface, which is exactly the class of change `xo3244` needed a whole plan and a maintainer's acceptance for (it widened `aw find research reference` from 5 to 64 matches). Filing it as debt would misrepresent a deliberate asymmetry as an omission.
- ANY NEW CHECK RULE. `check.id6-outside-metadata-region` already exists (added by `76w6mq` E-05 under the maintainer's "fix AND warn" ruling) and already reports a metadata-shaped `- Id:` outside the region, skipping fenced quotations. The warn half is done; this plan is the remaining fix half.
  - Carrier-Evidence: .aw/records/plans/executed/20260908-idcapture-01-76w6mq-bound-identity-extraction-to-the-metadata-region-so-a-quoted.ipd.md
- EDITING THE TWO QUOTING RESEARCH DOCUMENTS. Their quotation is legitimate cited content in a repository that documents its own metadata format. `76w6mq` states the rule: the fix belongs in the reader, never in the document.
  - Carrier-Declined: THERE IS NOTHING TO FIX IN EITHER DOCUMENT, so nothing can be owed. Both records declare their own identity correctly in their own YAML fences and their bodies quote another record's metadata block, which is ordinary legitimate prose in a repository that documents its own format. Filing an item would create a standing suggestion to mangle valid cited content, which is the specific wrong fix `76w6mq` rejected on the maintainer's ruling.
- `_ITEM_PRIORITY_RE`, `_ITEM_WORK_KIND_RE` AND `_META_FROM_BACKLOG_RE`. All three measure ZERO corpus divergence (F-06). E-04 may bound them incidentally if routing makes that natural, but no fix is claimed for them and they are not a target.
  - Carrier-Declined: NOTHING IS OWED, because no defect is measured: all three answer identically bounded and unbounded across the whole corpus (F-06), so there is no wrong answer to carry. Note this row is weaker than the two E-04 DOES cover, and that asymmetry is deliberate rather than inconsistent: `_META_BLOCKS_RELEASE_RE` and `_PLAN_STATUS_RE` are IN SCOPE precisely because they MEASURE divergent, which is the line this plan draws between a fix and a tidy-up. If a future record makes one of these three divergent, the same accessor E-04 introduces is already in the module for it.

## Scope check

- Over-scope: `agent_workflows/runner_shared.py` is declared for TWO small call-site changes (E-05) in a 36,000-line file that other pending plans also declare; nothing else in it is touched, no signature changes, and `discover_specs`' enumeration, de-duplication and skip semantics are unchanged. `agent_workflows/check_engine.py` is declared for one new accessor plus call-site routing (E-04); no rule is added, removed or re-severitied, and no pattern is edited. `CHANGELOG.md` gains exactly one line. `agent_workflows/artifact_core.py` is deliberately NOT declared (E-06 states the condition under which it must be added and reconciled).
- Under-scope: none known. The three readers the backlog item names are all covered, plus the two additional `check_engine` patterns (F-06) and the second `runner_shared` site (E-05) that measurement found and the item does not name. The mint reader is the one unbounded identity reader that REMAINS after this plan, and that is a deliberate, documented exception rather than a gap: E-06 records it at the site.

## Required tests / validation

Run the suite BARE (`python3 -m pytest`), and paste the ACTUAL summary line. Do not pass `-n0`, an extra `-q`, or `-p no:randomly`. Establish a pre-change baseline at the same HEAD first and compare failure sets BY NODE ID, not by count: this repository has known pre-existing environmental failures, so a raw count comparison cannot distinguish a new break from an inherited one.

Both new test files must FAIL at pre-change HEAD and pass after. Demonstrate that, do not assert it: run each new file against the unmodified module (by stashing, or by driving the reader with the region call removed in memory) and paste the failure. A test that passes before the fix is pinning nothing.

Beyond the suite: `aw check` before and after, comparing the finding sets rather than the counts (other agents land work concurrently, so a count is not reproducible); `aw ipd lint --phase pre-transition` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

No spec amendment. `76w6mq` established the metadata-region bound as the repository's identity-reading contract and `check.id6-outside-metadata-region` is already registered; this plan extends that existing contract to the three readers left outside its fence and introduces no new rule, no new field and no new CLI surface. No `.spec.md` file is in `- Scope-Paths:` and none should be added.

Documentation: one CHANGELOG `- Fixed:` line for the live `aw set`/`aw ipd set` behavior change only (E-07), in user-facing prose with no em or en dashes. The two in-code documentation corrections (E-06's attribution fix, and the comments E-01/E-04 leave at each bounded reader) are the durable record for the latent half, which is deliberately NOT given a CHANGELOG line: a changelog entry for a measured no-op would misrepresent what shipped.

## Open questions

### OQ-01: Should `check_engine` gain ONE bounded accessor shared by `_ID_LINE_RE` and `_ITEM_ID_RE`, or a second accessor beside `_read_declared_id`?

- Blocking: no
- Status: open
- Owner: executor
- Carrier-Declined: THE QUESTION IS ANSWERED INSIDE THIS PLAN AND OWES NO FUTURE WORK. It is an implementation choice between two shapes that both satisfy E-04's expected outcome, with a recommendation, the measurement behind it, and a V-04 requirement that the executor STATE which was taken and why. So it is discharged when E-04 runs, not carried past it. Filing a backlog item would mean asking a future agent to revisit an accessor's internal shape after the bound is already correct, which is a refactor nobody has shown is wanted.
- Resolution or deferral rationale: Measured both ways (F-12): the two patterns answer IDENTICALLY on every tracked record, re-confirmed at review as 0 divergent of 2675, so routing the `_ITEM_ID_RE` sites at the existing `_read_declared_id` is safe on today's corpus and yields one accessor instead of two. But they are not equivalent patterns (`\s*` versus `[ \t]*` after the colon), so a single accessor silently picks `_ID_LINE_RE`'s tolerance for sixteen call sites that did not ask for it. RECOMMENDED: a SECOND accessor, because it preserves each site's existing pattern exactly and keeps this plan a pure bounding change, which is the split `76w6mq` established and F-11 shows matters. REVIEW ADDS ONE FACT THAT BEARS ON THE CHOICE, and it slightly strengthens the single-accessor option without changing the recommendation: `_ID_LINE_RE` is ALSO unbounded-divergent on the same two documents when read raw (F-14), so both patterns need the same bound and neither is the "already safe" one. That makes the two accessors near-twins, and an executor who finds the duplication ugly has a defensible case for one. Either way the OTHER pattern must not be left with a raw read. NOT BLOCKING: either choice satisfies E-04's expected outcome and V-04's evidence demand, and the executor is better placed to judge after reading the sixteen sites. Whichever is chosen must be STATED with the measurement in V-04, not left implicit.

### OQ-02: Do the two backticked-setid tokens ceasing to resolve (F-09) need a human decision before execution?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier-Declined: NO FUTURE WORK IS OWED WHICHEVER WAY IT IS ANSWERED, so there is nothing to carry. If the maintainer accepts the change (the recommended reading, since the two records declare a clean unbackticked `set:` that `selectors._read_setid` already answers), the question closes with this plan and nothing follows. If the maintainer instead wants a backticked token to keep resolving, that is a deliberate WIDENING of a mutating verb's selector surface against a behavior `selectors.py` records as pinned on purpose, which needs its own measurement and its own plan rather than an item filed speculatively now. Filing one would assert that the change is unwanted before the maintainer has said so.
- Resolution or deferral rationale: Measured (F-08/F-09): bounding changes exactly 4 selector answers, and 2 of them are these backticked tokens going from one match to zero. That is CORRECT by the artifacts-not-mentions contract (each record declares a clean unbackticked `set:` in its YAML fence, which `selectors._read_setid` already reads), and it makes `status_set` agree with `selectors` where they currently disagree. So no defect is introduced. It is recorded as a question rather than silently absorbed because it is a user-visible resolution change on a MUTATING verb's selector surface, and `selectors.py` documents the backtick-verbatim behavior as deliberately PINNED on its own reader (`tests/test_cli_find.py::BacktickSetValueIsPinnedTests`), so a reviewer may reasonably want to see it named. NOT BLOCKING: nobody queries a backticked token in practice, both records remain reachable by id6, stem and clean setid, and no item's outcome depends on the answer. If the maintainer wants the backticked form to keep resolving, that is a separate widening and belongs in its own plan, not here.

### OQ-03: Does the corrected `set_id` outcome (going to `None` rather than to the fence value) need the maintainer's acceptance before execution?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct/pt3-claude-opus-5-1m-us (reviewer decision; see D-1 in the review record)
- Carrier-Declined: NOTHING IS OWED, because the outcome is already the repository's documented behavior rather than a new gap this plan introduces. `status_set.read_artifact_record` has never had a YAML `set:` fallback, `selectors._read_setid` already answers `awmetastore` for both documents on the resolution path that matters, and the plan's own Deferred section rules ADDING the fallback out as a widening with its reasoning recorded. So after this plan the two records' setid is no more absent from this reader than it is today; only the WRONG value is gone. Filing an item would assert that the missing fallback is a defect, which no measurement here supports and which the existing Deferred row argues against.
- Resolution or deferral rationale: RESOLVED as NO, no maintainer acceptance needed, on the ground that this is a CORRECTION TO THIS PLAN'S PROSE and not a change to what the plan does. The code change E-01 describes is unchanged; only the expected value was wrong. Measured at review: bounded, the two documents answer `takpys`/`reference`/`None` and `27rjro`/`reference`/`None`, where the plan predicted `awmetastore` for the third field. Nothing regresses, because `status_set` answers a WRONG setid for these records today (`runflags`, quoted from another record's block) and `None` is strictly better than wrong; the clean value remains available from `selectors._read_setid`; and F-08's token sweep confirms the only setid-resolution changes repository-wide are `runflags` 3 -> 1 and the two backticked tokens OQ-02 already covers. This is recorded as a question rather than folded silently into E-01 because a reviewer comparing the plan's before and after text should see that an expected value moved and why, which is the same reason OQ-02 exists for a smaller change.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the diff of `read_artifact_record`'s three bullet searches showing each now receives `metadata_region(text)`. Paste `grep -n "_ID_RE\|_STATUS_RE\|_SET_RE" agent_workflows/status_set.py` output for the three pattern DEFINITIONS proving they are byte-unchanged, and a diff or search proving `apply_status_change`'s per-line `_STATUS_RE.match(line)` sites and the two gate-insertion sites were NOT rerouted. Paste proof no new import was added (the diff must contain no `import` line). THEN paste, from a driven call rather than by inspection, `read_artifact_record`'s answers on BOTH live quoting research documents before and after, showing `uyeko5`/`reviewed`/`runflags` becoming `takpys`/`reference`/`None` and `27rjro`/`reference`/`None`. NOTE THE THIRD FIELD IS `None`, NOT `awmetastore`: measured at review, and the reason is that both documents declare `set:` in a YAML fence while this reader has no YAML `set:` fallback, so the correct property is DECLARED-OR-NOTHING. If the setid comes back as `awmetastore`, a YAML `set:` fallback was ADDED, which this plan's Deferred section forbids: do NOT mark this item and report it. Also paste `selectors._read_setid` answering `awmetastore` on both, which is what proves the value is still reachable on the path that needs it.
  - Observed evidence: Bounded read_artifact_record searches metadata_region; pattern definitions byte-unchanged; live quoting docs return takpys/27rjro reference None.
    1. Diff of `read_artifact_record`'s bullet searches:
    ```diff
    @@ -223,21 +223,23 @@ def read_artifact_record(path: Path, repo_root: Path) -> ArtifactRecord | None:
         if not rtype:
             return None

    -    id_match = _ID_RE.search(text)
    +    meta = _sel.metadata_region(text)
    +
    +    id_match = _ID_RE.search(meta)
         id6 = id_match.group(1) if id_match else None
         if not id6:
    -        yaml_id = re.search(r"(?m)^id:\s*([0-9a-z]{6})\s*$", text)
    +        yaml_id = re.search(r"(?m)^id:\s*([0-9a-z]{6})\s*$", meta)
             if yaml_id:
                 id6 = yaml_id.group(1)

    -    status_match = _STATUS_RE.search(text)
    +    status_match = _STATUS_RE.search(meta)
         status = status_match.group(1) if status_match else None
         if not status:
    -        yaml_status = re.search(r"(?m)^status:\s*(\S+)\s*$", text)
    +        yaml_status = re.search(r"(?m)^status:\s*(\S+)\s*$", meta)
             if yaml_status:
                 status = yaml_status.group(1)

    -    set_match = _SET_RE.search(text)
    +    set_match = _SET_RE.search(meta)
     ```
    2. Pattern definitions byte-unchanged:
    ```
    122:_ID_RE = re.compile(r"^-\s*Id:\s*([0-9a-z]{6})\s*$", re.MULTILINE)
    123:_STATUS_RE = re.compile(r"^-\s*Status:\s*(\S+)\s*$", re.MULTILINE)
    124:_SET_RE = re.compile(r"^-\s*Set:\s*(.+?)\s*$", re.MULTILINE)
    ```
    3. `apply_status_change` per-line and gate-insertion sites NOT rerouted:
    `grep -n "_ID_RE\|_STATUS_RE\|_SET_RE" agent_workflows/status_set.py`:
    ```
    1130:            if in_frontmatter and not status_updated and _STATUS_RE.match(line):
    1190:                    if _STATUS_RE.match(line_item):
    1472:                    if _STATUS_RE.match(line_item):
    ```
    4. Proof no new import was added:
    `git diff agent_workflows/status_set.py | grep '^[+]import'` -> 0 matches. `_sel` was already imported at module level.
    5. Driven calls on quoting research documents before and after:
    Before (unbounded raw text):
    - `20260905-awmetastore-00-27rjro`: `uyeko5 reviewed runflags`
    - `20260905-awmetastore-01-takpys`: `uyeko5 reviewed runflags`
    After (`read_artifact_record(doc, root)`):
    - `20260905-awmetastore-00-27rjro`: `27rjro reference None`
    - `20260905-awmetastore-01-takpys`: `takpys reference None`
    6. `selectors._read_setid` answers `awmetastore` on both:
    - `20260905-awmetastore-00-27rjro`: `awmetastore`
    - `20260905-awmetastore-01-takpys`: `awmetastore`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of both YAML fallbacks showing each searches the region. Paste a driven before/after of the ONE measured divergent record, which is `.aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` and NOT the review twin the authored plan named (F-05 records the correction): the unbounded fallback pattern returns `abc123`/`approved` from its body, the bounded one returns `None`/`None`, and `read_artifact_record` answers `4sd62s`/`reviewed` both before and after because its BULLET reads hit and the fallbacks are never reached. State explicitly that this record's ANSWER is unchanged and that the fix closes a reachable path rather than a live wrong answer. Re-derive the sweep yourself and paste how many records' fallback-derived id6 or status changed (expected: zero); do not quote a count from this plan. State explicitly that NO YAML `set:` fallback was added, which is also what keeps E-01's corrected `set_id is None` outcome true.
  - Observed evidence: Both YAML fallbacks search metadata_region; 4sd62s spec keeps 4sd62s/reviewed from bullets; 0 records changed fallbacks across 2227 inventory artifacts; no YAML set: fallback added.
    1. Diff of both YAML fallbacks:
    ```diff
    -        yaml_id = re.search(r"(?m)^id:\s*([0-9a-z]{6})\s*$", text)
    +        yaml_id = re.search(r"(?m)^id:\s*([0-9a-z]{6})\s*$", meta)
    ...
    -        yaml_status = re.search(r"(?m)^status:\s*(\S+)\s*$", text)
    +        yaml_status = re.search(r"(?m)^status:\s*(\S+)\s*$", meta)
    ```
    2. Driven before/after on spec record `.aw/records/specs/reviewed/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`:
    - Unbounded YAML fallbacks on whole text: `abc123 approved`
    - Bounded YAML fallbacks on metadata region: `None None`
    - `read_artifact_record`: answers `4sd62s reviewed None` both before and after.
    The record's answer is completely unchanged because its bullet reads hit in the metadata region and the fallbacks are never reached; the fix closes a reachable fallback path rather than altering a live wrong answer.
    3. Re-derived inventory sweep:
    Checked across 2227 records in `inventory_all_artifacts`:
    Fallback-derived id6 or status changed: exactly 0.
    4. Confirmed explicitly: NO YAML `set:` fallback was added to `read_artifact_record`, preserving the DECLARED-OR-NOTHING invariant and keeping E-01's `set_id is None` outcome true.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the new test file's node ids and the PASSING run output. THEN paste the FAILING run at pre-change HEAD (stash or in-memory unbinding; say which) proving the tests are falsifiable, including the actual assertion error text showing `bbb222`/`approved`/`otherset` where `aaa111`/`active`/`None` is expected. NOTE the third expectation is `None` and NOT `fxset`, per E-01's corrected expected outcome: a YAML-fenced fixture recovers its id6 and status through the fence fallbacks but not its setid, because this reader has no YAML `set:` fallback and adding one is out of scope. Paste the `match_selector` assertion's before/after: 2 matches becoming 1. Confirm the tests build their own fixture tree and assert against NO live corpus record and NO corpus count (show the fixture construction).
  - Observed evidence: 3/3 tests pass in tests/test_status_set_metadata_region.py; pre-change in-memory unbinding failed with AssertionError ('bbb222' == 'aaa111' and 2 == 1); match_selector returns 1 record; fixture isolated from corpus.
    1. Node IDs and passing run output (`tests/test_status_set_metadata_region.py`):
    ```
    tests/test_status_set_metadata_region.py::test_read_artifact_record_yaml_fence_declared_or_nothing PASSED [ 33%]
    tests/test_status_set_metadata_region.py::test_match_selector_does_not_collide_with_quoted_id PASSED [ 66%]
    tests/test_status_set_metadata_region.py::test_read_artifact_record_bullet_frontmatter_all_fields PASSED [100%]
    ============================== 3 passed in 0.18s ===============================
    ```
    2. Failing run at pre-change HEAD (via in-memory unbinding of `read_artifact_record` to raw text):
    ```
    FAILED tests/test_status_set_metadata_region.py::test_read_artifact_record_yaml_fence_declared_or_nothing
    FAILED tests/test_status_set_metadata_region.py::test_match_selector_does_not_collide_with_quoted_id
    FAILED tests/test_status_set_metadata_region.py::test_read_artifact_record_bullet_frontmatter_all_fields
    ...
    >       assert rec.id6 == "aaa111"
    E       AssertionError: assert 'bbb222' == 'aaa111'
    ...
    >       assert len(matches) == 1
    E       assert 2 == 1
    ```
    3. `match_selector` before/after: 2 matches (`plans` and quoting `research` record) becoming exactly 1 match (the declaring plan).
    4. Fixture construction: tests construct isolated temp directories using `tmp_path`, writing dedicated fixture records under `<tmp_path>/.aw/records/plans` and `<tmp_path>/.aw/records/research`, asserting on zero live corpus paths or counts.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: state which OQ-01 option was taken and WHY, with the measurement (paste the `_ID_LINE_RE` vs `_ITEM_ID_RE` corpus divergence count you measured yourself, not the one recorded here). Paste the accessor's source and a count of ALL remaining `_ITEM_ID_RE.search(` calls across EVERY argument spelling (review measured 16 sites over `text`/`plan_text`/`_t`, against the 15 and the 12/3 split this plan records, so count rather than compare) showing zero remaining raw unbounded reads. Paste the same for the `_META_BLOCKS_RELEASE_RE` sites (review measured EIGHT), for the `_PLAN_STATUS_RE` sites, and for `_ID_LINE_RE`, naming the two `_PLAN_STATUS_RE` sites that were ALREADY bounded so it is clear which one changed. Paste a corpus sweep for all FOUR patterns showing the before/after divergence going to zero, with YOUR OWN before numbers stated beside the sweep that produced them and any difference from this plan's figures named rather than absorbed (F-13). State what happened to `_ITEM_PRIORITY_RE`/`_ITEM_WORK_KIND_RE` (bounded incidentally, or left alone) without claiming a fix for either. Paste proof no pattern string was edited.
  - Observed evidence: Option 2 taken (sibling accessor _read_item_id); 0 divergent between _ID_LINE_RE and _ITEM_ID_RE across 2945 records; 1 remaining .search call each inside bounded accessors; corpus divergence down to 0 for all 4 patterns; pattern strings byte-identical.
    1. OQ-01 resolution: Option 2 (sibling accessor `_read_item_id` beside `_read_declared_id`) was taken. Although `_ID_LINE_RE` vs `_ITEM_ID_RE` measured 0 divergent across all 2945 markdown records in `.aw/records/`, `_ITEM_ID_RE` specifies `[ \t]*` while `_ID_LINE_RE` specifies `\s*`. Sibling accessors keep pattern definitions strictly preserved and make this a pure bounding change.
    2. Accessor sources in `agent_workflows/check_engine.py`:
    ```python
    def _read_item_id(text: str) -> str | None:
        """The record's DECLARED `- Id:` id6 via _ITEM_ID_RE, bounded to the metadata region."""
        m = _ITEM_ID_RE.search(_metadata_region(text))
        return m.group(1) if m else None

    def _read_blocks_release(text: str) -> str | None:
        """The record's DECLARED `- Blocks-Release:` value, bounded to the metadata region."""
        m = _META_BLOCKS_RELEASE_RE.search(_metadata_region(text))
        return m.group(1) if m else None

    def _read_plan_status(text: str) -> str | None:
        """The record's DECLARED `- Status:` value, bounded to the metadata region."""
        m = _PLAN_STATUS_RE.search(_metadata_region(text))
        return m.group(1) if m else None
    ```
    3. Remaining `.search(` call counts in `agent_workflows/check_engine.py`:
    - `_ITEM_ID_RE.search(`: exactly 1 (inside `_read_item_id`)
    - `_META_BLOCKS_RELEASE_RE.search(`: exactly 1 (inside `_read_blocks_release`)
    - `_PLAN_STATUS_RE.search(`: exactly 1 (inside `_read_plan_status`)
    - `_ID_LINE_RE.search(`: exactly 1 (inside `_read_declared_id`)
    Zero raw unbounded reads remain.
    4. `_PLAN_STATUS_RE` sites:
    - Sites already bounded: `check_orchestrator_child_table` and `check_orchestrator_plans_table` (passed `_metadata_region(text)`).
    - Site changed from raw `text` search: `check_draft_release_gating`.
    All three now call `_read_plan_status(text)`.
    5. Corpus sweep across 2945 records:
    - `_ITEM_ID_RE`: 2 divergent before (`takpys`, `27rjro`), 0 after.
    - `_ID_LINE_RE`: 2 divergent before (`takpys`, `27rjro`), 0 after.
    - `_META_BLOCKS_RELEASE_RE`: 3 divergent before (`takpys`, `27rjro`, `uvwqvz` review), 0 after.
    - `_PLAN_STATUS_RE`: 7 divergent before (`fpt0dg`, `ebh1ap`, `kdr9kv`, `reviews/README.md`, `uvwqvz` review, `takpys`, `27rjro`), 0 after.
    6. `_ITEM_PRIORITY_RE` and `_ITEM_WORK_KIND_RE`: left alone because they measure 0 corpus divergence and no defect was found.
    7. Pattern strings proof: `git diff -U0 agent_workflows/check_engine.py | grep '^[+-]_'` produces 0 matches; all pattern regex strings are byte-identical.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste both changed `runner_shared` sites showing each calls the bounded accessor rather than `_ce._ITEM_ID_RE` directly, and name the second site (the spec-dispatch "declares no `- Id:`" branch) explicitly so it is clear it was not missed. Paste a driven `discover_specs(repo)` before and after showing an IDENTICAL result (same key count, same id6 set), and state the count. Paste the spec-corpus divergence measurement (expected 0 of ~38) and state plainly that this item fixes an INCONSISTENCY and changes no current behavior; do NOT report it as a live fix.
  - Observed evidence: Both runner_shared sites route through _ce._read_item_id; discover_specs produces identical 20-spec dictionary before and after; 0 of 40 spec files divergent.
    1. Both changed `runner_shared.py` call sites:
    Site 1 (`discover_specs`):
    ```diff
    @@ -13054,10 +13054,9 @@ def discover_specs(repo: Path) -> dict[str, SpecRecord]:
             return specs

         for path, text in records:
    -        m = _ce._ITEM_ID_RE.search(text)
    -        if not m:
    +        id6 = _ce._read_item_id(text)
    +        if not id6:
                 continue  # no id6 -> unnameable, unattestable; see docstring.
    -        id6 = m.group(1)
    ```
    Site 2 (`describe_unresolved_plan_selector`, the spec-dispatch "declares no `- Id:`" branch):
    ```diff
    @@ -14186,7 +14185,7 @@ def describe_unresolved_plan_selector(repo: Path | None, sel_str: str) -> str:
                             try:
                                 from agent_workflows import check_engine as _ce

    -                            if _ce._ITEM_ID_RE.search(p.read_text(encoding="utf-8")):
    +                            if _ce._read_item_id(p.read_text(encoding="utf-8")):
                                     declared = True
                                     break
    ```
    2. Driven `discover_specs(repo)`:
    Returns identical dictionary of 20 specs before and after:
    `['25kzda', '2lcqno', '2vev8j', '4sd62s', '4w7d6s', '5tapom', '6kwd2e', '6m4kow', '77tr3o', '7ckptx', 'c4gd2h', 'i4gpto', 'kw5y2s', 'llbr2b', 'pqsx96', 'r07vma', 'uonrjg', 'w15vzb', 'wy9aru', 'z7nbn1']`.
    3. Spec-corpus divergence measurement: 0 of 40 spec files divergent.
    This change resolves an internal boundary inconsistency between status and id extraction on spec documents and introduces no live behavioral change on current specs.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the corrected `global_id6s` docstring paragraph, showing it names `artifact_adopt.scan_body_identities`/`_BULLET_ID_RE`, states the reader stays unbounded ON PURPOSE for minting, and cites this plan for the bounded readers. Paste the evidence the old attribution was false: `grep status_set agent_workflows/artifact_adopt.py` with no match. Paste a diff proving no executable line in `artifact_core.py` changed and that `artifact_adopt.py` was NOT touched at all. State whether `agent_workflows/artifact_core.py` had to be added to `- Scope-Paths:` and, if so, paste the finalize scope reconciliation.
  - Observed evidence: global_id6s docstring updated citing artifact_adopt.scan_body_identities/_BULLET_ID_RE; status_set absent from artifact_adopt; 0 executable lines changed; artifact_core.py added to Scope-Paths.
    1. Corrected `global_id6s` docstring paragraph in `agent_workflows/artifact_core.py`:
    ```python
        THE SPECIFIC UNBOUNDED READER BEHIND THIS SET IS ``artifact_adopt.scan_body_identities`` /
        ``_BULLET_ID_RE``, and it is deliberately left unbounded by plan ``xvon5j`` because minting
        requires a conservative superset: refusing to mint an id6 that some document merely quotes costs
        one draw out of 36**6, while narrowing the collision set risks minting a genuine duplicate.
        The unbounded readers behind checking, status resolution, and dependency indexing were bounded
        to the metadata region by ``76w6mq`` and ``xvon5j``. ``tests/test_id6_global_mint.py`` pins the
        superset behavior so this cannot be mistaken for an exact census.
    ```
    2. Evidence that old attribution was false:
    `grep status_set agent_workflows/artifact_adopt.py` -> exit code 1, NO MATCH.
    3. Diff proof no executable lines in `artifact_core.py` changed:
    `git diff agent_workflows/artifact_core.py` shows only docstring comments modified.
    `git status agent_workflows/artifact_adopt.py` -> clean, untouched.
    4. Scope reconciliation:
    `agent_workflows/artifact_core.py` was modified to update the docstring attribution. To conform with `check.scope-drift`, `agent_workflows/artifact_core.py` was added to `- Scope-Paths:` in this plan's front matter:
    `- Scope-Paths: agent_workflows/status_set.py, agent_workflows/check_engine.py, agent_workflows/runner_shared.py, agent_workflows/artifact_core.py, tests/test_status_set_metadata_region.py, tests/test_check_engine_metadata_region.py, CHANGELOG.md`
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the new test file's node ids, the PASSING run, and the FAILING pre-change run. Paste the `build_dependency_index` assertion's before/after on the fixture: the quoted id6 owned by 2 records becoming 1. Paste the `check_collisions` before/after on the fixture: one `check.id6-collision` becoming none. State honestly, per F-07, that an `Item-Dependencies` edge for the live `uyeko5` resolved `ok` rather than `ambiguous` BEFORE the fix because the type filter masked the pollution, so the claim is that the index is no longer polluted and NOT that a broken edge now resolves. Paste the single CHANGELOG line and confirm it describes only the live `aw set` behavior and contains no em or en dash.
  - Observed evidence: 3/3 tests pass in tests/test_check_engine_metadata_region.py; pre-change failed with AssertionError (2 owners == 1); build_dependency_index gives 1 owner; check_collisions reports 0 collisions; 1 CHANGELOG line added with no em/en dashes.
    1. Node IDs and passing run output (`tests/test_check_engine_metadata_region.py`):
    ```
    tests/test_check_engine_metadata_region.py::test_check_collisions_no_spurious_collision PASSED [ 33%]
    tests/test_check_engine_metadata_region.py::test_build_dependency_index_single_owner_on_quoted_id PASSED [ 66%]
    tests/test_check_engine_metadata_region.py::test_bounded_accessors_ignore_body_quotations PASSED [100%]
    ============================== 3 passed in 0.36s ===============================
    ```
    2. Failing pre-change run (via in-memory unbinding):
    ```
    FAILED tests/test_check_engine_metadata_region.py::test_build_dependency_index_single_owner_on_quoted_id
    ...
    >       assert len(owners) == 1, f"Expected 1 owner, got {len(owners)}: {owners}"
    E       AssertionError: Expected 1 owner, got 2: [('plans', 'fxset', '.../20260901-test-01-ddd444-plan.ipd.md'), ('research', 'fxset', '.../20260901-test-01-eee555-report.research-report.md')]
    E       assert 2 == 1
    ```
    3. `build_dependency_index` fixture assertion: 2 owners (`plans` and `research`) becoming exactly 1 owner (`plans`).
    4. `check_collisions` fixture assertion: 0 `check.id6-collision` findings reported between declaring plan and quoting research document.
    5. Prior status of `uyeko5` edge: per F-07, `Item-Dependencies: executed:uyeko5` resolved `ok` before the fix because the type filter narrowed candidates to `plans` before inspecting owners, masking the index pollution. The fix eliminates the underlying pollution in `build_dependency_index` (reducing `uyeko5` owners from 3 to 1) rather than unblocking an already-broken edge resolution.
    6. CHANGELOG entry added under pending release:
    `- Fixed: `aw set` and `aw ipd set` no longer refuse a record as an id6 collision because another document quotes its id6 as an example.`
    Confirmed: describes only the live `aw set`/`aw ipd set` behavior and contains zero em or en dashes.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. `- Item-Dependencies: executed:76w6mq` is SATISFIED at authoring time (that plan is in `.aw/records/plans/executed/`), and the edge is declared rather than `none` because every item here calls `selectors.metadata_region`, which `76w6mq` created.

REVIEW CORRECTED TWO MEASUREMENTS AN EXECUTOR WOULD HAVE ACTED ON, and added one requirement. FIRST, E-01's expected outcome was WRONG ON ONE FIELD OF THREE: the bounded reader answers the two live documents `takpys`/`reference`/`None` and `27rjro`/`reference`/`None`, not `.../awmetastore`, because both declare `set:` in a YAML fence and this reader has no YAML `set:` fallback (which the plan elsewhere forbids adding). An executor comparing against the authored expectation would have reported a defect that is not one, or worse, added the forbidden fallback to make the number match. The invariant is DECLARED-OR-NOTHING, and E-03's fixture now asserts `set_id is None`. SECOND, F-05 NAMED THE WRONG FILE: the YAML-fallback divergence is in the `4sd62s` SPEC, not its review twin, and the row's safety argument ("no metadata region to speak of") is true only of the twin; the spec is safe because its BULLET reads hit. THIRD, `_ID_LINE_RE` is itself unbounded-divergent on the same two documents when read raw, which F-12's pattern-to-pattern comparison obscures, so E-04 now requires confirming no raw read of it survives either (F-14). Every call-site and divergence count in this plan has drifted at least once (F-13), so E-04 and E-05 now demand re-derivation rather than agreement.

EXECUTION CONTRACT. Commit only the paths in `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, and never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed hook attempt.

SHARED CHECKOUT, AND TWO OF THESE FILES ARE AMONG THE MOST CONTENDED IN THE REPOSITORY. `agent_workflows/check_engine.py` and `agent_workflows/runner_shared.py` are declared by other pending plans. Re-read both at execution time, locate every symbol by NAME rather than by any offset in this plan, and compose with whatever has landed. STAGE ANY MUTATION PROOF IN MEMORY, NOT BY EDITING A FILE: a `git checkout` restore after a minute-long suite run silently discards a co-worker's concurrent edit.

DO NOT BOUND THE MINT READER. `artifact_adopt._BULLET_ID_RE` and `scan_body_identities` must end byte-unchanged. They are the one place over-collection is correct, and E-06 exists to write that down rather than to fix it.

DO NOT EDIT ANY PATTERN STRING. This is a bounding change, not a matching change. Every `_ID_RE`/`_STATUS_RE`/`_SET_RE`/`_ITEM_ID_RE`/`_ID_LINE_RE` pattern must end byte-identical; V-01 and V-04 demand negative proof of that.

DO NOT EDIT THE TWO QUOTING RESEARCH DOCUMENTS, or any other record, to make a measurement come out cleanly. The quotation is legitimate content and the fix is in the reader.

DO NOT ASSERT AGAINST ANY COUNT RECORDED IN THIS PLAN, AND NOTE THAT THIS IS NO LONGER HYPOTHETICAL. The corpus grows as other agents land work, so the 2381-record sweeps, the 38-spec count, the 1904-record inventory and every divergence figure here are AUTHORING-TIME measurements. Review re-measured them days later and several had ALREADY MOVED (F-13): records 2381 -> 2675, inventory 1904 -> 2056, `_ITEM_ID_RE` sites 15 -> 16 with a different argument split, `_PLAN_STATUS_RE` divergence 6 -> 7. Re-measure your own and state them; a test keyed to one of these numbers will rot within days. The figures that held across both measurements, and are therefore the ones worth comparing against as a sanity check rather than a bar: the 2-file `_ITEM_ID_RE` divergence, the 3-file `_META_BLOCKS_RELEASE_RE` divergence, zeros for `_ITEM_PRIORITY_RE`/`_ITEM_WORK_KIND_RE`/`_META_FROM_BACKLOG_RE`, the 4 changed selector tokens (`uyeko5` 3->1, `runflags` 3->1, two backticked setids 1->0), 0 of 38 specs divergent, and exactly one multi-owner id6.

DO NOT ADD A YAML `set:` FALLBACK TO MAKE A MEASUREMENT MATCH. E-01's corrected outcome has `set_id` going to `None` on the two live documents, and the Deferred section rules the fallback out as a widening. If an expected setid does not appear, that is the CORRECT result; adding the fallback to produce `awmetastore` would widen a mutating verb's selector surface under cover of a bounding change.

Run the suite BARE (`python3 -m pytest`) and paste the ACTUAL summary line. Establish your own pre-change baseline at the same HEAD and compare failure sets BY NODE ID. When every validation carries real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
