# IPD: Correct the stale trailer-consumption claims in run_evidence and ipd_lifecycle, which the trailer READER has now outdated in a third place

- Date: 2026-09-30
- Kind: child
- Concern: Code comments assert that nothing in the tree passes `AW-Run:`/`AW-Item:` commit trailers and that no commit carries one, which is false. `run_evidence.py`'s `RUN-COMMIT-CONTENTS` `waiting_on` string still reads "`m73aet`'s own executed receipt records that nothing in the tree passes trailers yet", while MEASURED in this lane at HEAD `d77a4971` there are 843 trailered non-merge commits of 5551 (`git log --no-merges --format="%H%x00%(trailers:key=AW-Item,valueonly)"`, nonempty second field). THE ITEM'S OWN PRESCRIPTION IS ITSELF STALE, and that is the finding that decides this plan's shape: the item says the correct statement is "driver-side sites pass them; nothing reads them back", but plan `199u11` (`trailread-02`) has since EXECUTED and shipped a READER, so the second half is now false too. `ipd_lifecycle._commit_run_ownership` reads `AW-Item`/`AW-Run` via `git log --format=%(trailers:key=...,valueonly)`, `_trailer_owned_committed_paths` classifies every commit in `base_head..HEAD`, `finalize_precheck` consumes the result into a `trailer_attribution` evidence block ahead of cohesion, and `tests/test_finalize_trailer_attribution.py` passes (6 tests). The item's second location is doubly unreachable as written: it names symbol `_scope_attributed_commits`, which does not exist (`grep -c` returns 0), and quotes "essentially no commit in history carries one yet", which also returns 0 because `199u11` already rewrote that docstring. What DOES remain at that file is a different stale claim, the two surviving `a8eufb` pointers in `ChangedPathSources`, one of which says "`a8eufb` remains the real fix" when `a8eufb` is `done`.
- Scope: Replace the false and now doubly-stale claims with what the tree actually does, WITHOUT changing any finding-code binding. IN: (a) `run_evidence.py`'s `RUN-COMMIT-CONTENTS` `waiting_on` string, reworded to name the still-missing predicate (a tree-diff proof that a commit's path union equals the item-owned delta) and to stop asserting that nothing passes or reads trailers; (b) the same file's `BINDINGS RE-MEASURED 2026-09-05` comment block, whose bullet repeats "nothing reads a trailer back" and whose closing paragraph calls the outstanding machinery "a trailer READER"; (c) `ipd_lifecycle.py`'s two surviving `a8eufb` pointers in `ChangedPathSources`, repointing them at the shipped reader and dropping the dead "remains the real fix" claim; (d) spec `25kzda`'s Infrastructure-status paragraph, whose "NOTHING READS A TRAILER BACK (backlog `am1g38`)" clause is the same falsehood in the artifact this plan's own corrections cite, amended with `aw specs note`. OUT: the `binding` field of `RUN-COMMIT-CONTENTS` or `RUN-COMMIT-GATEWAY` (both stay `UNBOUND_BY_DEPENDENCY`; see Deferred, and the standing prohibition in backlog `d07nz2`); Section 4.2's table row cells (`inspects`, `pass_criterion`, `message`, `action`); `RUN-COMMIT-GATEWAY`'s own `waiting_on`, which waits on a commit-gateway RECEIPT and is unaffected by the reader; and any behavior change whatsoever, this being a comment-and-prose correction.
- Scope-Paths: agent_workflows/run_evidence.py, agent_workflows/ipd_lifecycle.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- From-Spec: 25kzda
- Work-Kind: chore
- Priority: low
- From-Backlog: oye21y
- Set: oye21y
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 2lxcwt

## Workflow history
- 2026-09-30 same-status (aw set): status unchanged (to-review)

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `oye21y`. Every claim was re-measured in this lane at HEAD `d77a4971` rather than transcribed, and THREE of the item's premises measured stale: (1) its prescribed replacement wording "nothing reads them back" is now false, because `199u11` executed and shipped the reader; (2) its second location names a symbol `_scope_attributed_commits` that does not exist; (3) the exact string it quotes from `ipd_lifecycle.py` no longer exists either. The scope was therefore re-derived from what is actually on disk (the two surviving `a8eufb` pointers) rather than from the item's citations, and EXTENDED to the spec, which carries the same falsehood and is cited BY the code comments being corrected. Also measured, and load-bearing for the fence: the "byte-equality test" that three prior plans warn guards this table DOES NOT EXIST; no test anywhere references `RUN_FINDING_CODES` (`grep` over `tests/` returns zero files), so the module's runtime `validate_finding_table` self-check is the only live guard. GATE NOTE: item `oye21y` carries no `- Blocks-Release:`, so this plan inherits none and invents none.

## Goal

Make the tree stop asserting, in three places, that nothing writes and nothing reads the run-ownership commit trailers, when 843 commits carry them and finalize reads them on every run. After this plan the two `RUN-COMMIT-*` codes still say UNBOUND, which is correct, but they say so for the reason that is actually true today (no tree-diff proof exists) rather than for a reason that stopped being true when `199u11` landed.

Secondarily, and stated plainly because it is the more durable fix: remove the last two pointers to backlog `a8eufb`, which is `done`, so a reader chasing "the real fix" is sent to the shipped reader instead of to a closed item.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure, because every number here has already moved once

- [ ] E-01 RE-MEASURE THE FOUR FACTS THIS PLAN'S WORDING DEPENDS ON, BEFORE EDITING ANY PROSE. This plan exists because an earlier correction rotted; its own replacement text will rot the same way if written from authoring-time figures. Run and record raw output for: (a) the trailered-commit census, `git log --no-merges --format="%H%x00%(trailers:key=AW-Item,valueonly)" | awk -F'\0' '$2!=""' | wc -l` against `git log --no-merges --format=%H | wc -l` (authoring: 843 of 5551 at HEAD `d77a4971`); (b) that the READER is present and reachable, by locating `ipd_lifecycle._commit_run_ownership`, `ipd_lifecycle._trailer_owned_committed_paths`, and the `evidence["trailer_attribution"]` assignment inside `finalize_precheck`; (c) `python3 -m pytest tests/test_finalize_trailer_attribution.py` (authoring: `6 passed`); (d) `validate_finding_table()` validity plus the binding partition, via `Counter(r.binding for r in RUN_FINDING_CODES)` (authoring: `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}`, `ok=True`, 12 codes).

  IF ANY FIGURE HAS MOVED, that is the EXPECTED case for this defect class: use the new measurement and say so explicitly. Do NOT adjust this plan's argument, which depends only on the reader EXISTING and on the trailered count being nonzero, not on any particular number. IF THE READER HAS BEEN REMOVED (b fails), STOP and record it: the item's original wording would then be correct again and this plan's premise is void.
  - Depends on: none
  - Expected outcome: four raw measurements recorded, each with the command that produced it, and an explicit statement of whether each matches the authoring figure.
  - Execution state: pending

- [ ] E-02 CONFIRM THE FENCE BEFORE TOUCHING THE FINDING TABLE, because three prior plans assert a guard that this plan measured as absent and acting on either belief without checking is how a wrong edit ships. Plans `wao266` ("that table is transcribed into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so a cell edit is a code change") and `j0ag0u` state a byte-equality test guards Section 4.2. Re-run the measurement: search `tests/` for `RUN_FINDING_CODES`, for `validate_finding_table`, and for `pass_criterion` (authoring: ZERO files for all three), and confirm `tests/test_finalize_trailer_attribution.py` is the only test file referencing the trailer reader.

  RECORD WHICH BELIEF THE MEASUREMENT SUPPORTS, and note the distinction that makes this edit safe either way: `waiting_on` is NOT one of Section 4.2's five columns (the spec table carries code, inspects, pass_criterion, message, action), so it is not part of any transcription even if a transcription test exists. IF A GUARD IS FOUND that did not exist at authoring, honor it: leave every 4.2-derived cell byte-identical and confine the edit to `waiting_on` and the comment block.
  - Depends on: E-01
  - Expected outcome: the search results pasted, and a one-sentence statement of whether a byte-equality test exists, with the consequence for this plan's fence.
  - Execution state: pending

### Task group 2: correct the three code sites

- [ ] E-03 REWORD `RUN-COMMIT-CONTENTS`'s `waiting_on` STRING so it names the predicate that is genuinely missing and asserts nothing false about writers or readers. The site, by content rather than offset: the `waiting_on` tuple inside the `RunFindingCode(code="RUN-COMMIT-CONTENTS", ...)` literal, whose current text is "a trailer READ-BACK predicate. `runtrail-01` (`m73aet`) executed and `git_commit_helper.run_item_trailers` WRITES `AW-Run:`/`AW-Item:`, but nothing reads a trailer back or proves a commit's tree diff equals the item-owned delta; `m73aet`'s own executed receipt records that nothing in the tree passes trailers yet".

  THE NEW TEXT MUST DO EXACTLY THREE THINGS, and the third is what keeps this correction from being an overcorrection into a fail-open binding. (1) DELETE both false clauses: that nothing reads a trailer back, and that nothing in the tree passes trailers yet. (2) NAME WHAT NOW EXISTS, by symbol, so the next reader does not rebuild it: the writer `git_commit_helper.run_item_trailers`, and the reader `ipd_lifecycle._trailer_owned_committed_paths` / `_commit_run_ownership`, shipped by `199u11`. (3) NAME THE STILL-MISSING PREDICATE AS THE REASON THE CODE STAYS UNBOUND: no predicate proves a commit's tree diff EQUALS the item-owned delta, which is this code's actual `pass_criterion`. The existing reader answers a DIFFERENT question (is this commit's `AW-Item` mine), and reading ownership is not proving contents, so the code remains correctly `UNBOUND_BY_DEPENDENCY`.

  KEEP THE STRING A SINGLE `waiting_on` VALUE and change no other field of the row. Do NOT touch `binding`, `predicates` (which must stay empty), `inspects`, `pass_criterion`, `message`, `action`, `abort`, or `abort_classes`. WRITE NO DATED COUNT into the string: a dated snapshot is exactly what the two previous authors wrote in good faith and it rotted both times, so state the facts structurally (a writer exists, a reader exists, a contents proof does not) and leave the census to this plan's Findings.
  - Depends on: E-02
  - Expected outcome: `git diff` on `run_evidence.py` shows only the `waiting_on` string of that one row changed; the new text names both shipped symbols and the missing contents proof, and contains neither "nothing reads" nor "passes trailers yet"; `validate_finding_table().ok` is still `True` and the binding partition is unchanged.
  - Execution state: pending

- [ ] E-04 CORRECT THE `BINDINGS RE-MEASURED` COMMENT BLOCK in the same file, which repeats the identical falsehood twice and is the site a reader auditing the table actually reads. Two sentences, by content: the third bullet's "Nothing reads a trailer back, and `m73aet`'s own executed receipt states \"`RUN-COMMIT-GATEWAY` remains wholly unbuilt\" and \"nothing in the tree PASSES trailers yet\""; and the closing `RE-MEASURED 2026-09-22` paragraph's "The two remaining unbound codes still WAIT on machinery (a commit-gateway receipt and a trailer READER)".

  PRESERVE EVERY LOAD-BEARING CLAIM AND CHANGE ONLY WHAT IS FALSE, because the surrounding argument is correct and is the reason the codes are unbound. The block must still say that `RUN-HOST-CAPABILITY` and `RUN-BASELINE-OWNERSHIP` became BOUND and why; that writing a trailer is not proving a commit's tree diff equals the item-owned delta; that binding these two on the strength of a writer "would be exactly the fail-open error described above"; and that an empty UNBUILT set must not be read as "everything is now decided by a predicate". REPLACE ONLY the two false assertions: the reader now EXISTS (name `199u11` and the symbol), and the outstanding machinery is a commit-gateway receipt plus a tree-diff CONTENTS PROOF, not a reader.

  NOTE THE `m73aet` QUOTATIONS ARE HISTORICAL AND MUST NOT BE FALSIFIED. That receipt genuinely said those words in 2026-08-30 and an executed plan's record may not be rewritten. So keep the quotation if it is kept at all, but mark it as what that receipt recorded AT THE TIME and state that both halves have since been overtaken, rather than presenting it as current fact. Deleting the quote entirely is also acceptable; presenting it as present tense is not.
  - Depends on: E-03
  - Expected outcome: `git diff` shows both sentences reworded, with no surviving present-tense claim that nothing reads or passes trailers, every other clause of the block intact, and any retained `m73aet` quotation explicitly marked as historical.
  - Execution state: pending

- [ ] E-05 REPOINT THE TWO SURVIVING `a8eufb` REFERENCES in `ipd_lifecycle.py`, which are what actually remains of the item's second location. Both are in the `ChangedPathSources` docstring: "WHAT SCOPEATTR `h9cn0y` DID ABOUT THAT BOUND, since Order 01 left it open (backlog `a8eufb`)" and "That is a heuristic with a stated cost, not the proof a commit trailer would give, so `a8eufb` remains the real fix".

  THE SECOND SENTENCE IS THE DEFECT: `a8eufb` is `- Status: done` (closed by `wao266`), so "remains the real fix" points a reader at a closed item for work that has since shipped. Reword it to say that the trailer fix HAS landed (`199u11`, read via `_trailer_owned_committed_paths`) and is consulted ahead of cohesion, while cohesion remains the fallback for untrailered and foreign commits. The first mention is a HISTORICAL statement about what Order 01 left open and is true as history; keep it, but make clear it is history rather than an open gap.

  KEEP THE HONEST BOUND EXACTLY AS IT IS. The docstring's "HONEST BOUND: ``committed`` is attributable to a COMMIT, not to an AGENT" and its explanation that every agent commits under one git identity must survive unchanged: a trailer is a consistency record, not tamper-proof provenance, which `_commit_run_ownership`'s own docstring already states as its FAIL-CLOSED RULE. Do NOT let this correction read as "attribution is now solved". CONSISTENCY CHECK: `_working_tree_path_is_owned` and the `finalize_precheck` comment were already updated by `199u11` and say "UNTRAILERED commit" in the right places; leave them alone and match their wording rather than inventing a new phrasing.
  - Depends on: E-04
  - Expected outcome: `grep -c a8eufb agent_workflows/ipd_lifecycle.py` reflects the intended state with no surviving claim that a closed item "remains the real fix"; the HONEST BOUND paragraph is byte-identical to before; `git diff` touches only the `ChangedPathSources` docstring.
  - Execution state: pending

### Task group 3: correct the spec that the code comments cite

- [ ] E-06 AMEND SPEC `25kzda`'s INFRASTRUCTURE-STATUS PARAGRAPH, which carries the same falsehood and is the artifact the corrected comments point at, so leaving it would undo this plan for anyone reading the spec instead of the code. The clause, by content: "and NOTHING READS A TRAILER BACK (backlog `am1g38`), so no commit's ownership is yet decided by its trailer and Section 4.2's `RUN-COMMIT-*` rows stay unbound".

  BOTH HALVES ARE NOW FALSE AND THEY FAIL DIFFERENTLY, which is why this is one careful edit and not a deletion. "Nothing reads a trailer back" is false outright (`199u11`). "No commit's ownership is yet decided by its trailer" is false too: `finalize_precheck` consults `_trailer_owned_committed_paths` BEFORE and independently of cohesion, so an `AW-Item`-matching commit's paths ARE decided by its trailer today. The CONCLUSION, that the `RUN-COMMIT-*` rows stay unbound, is still TRUE and must be preserved, but its reason changes: they stay unbound because no predicate proves a commit's tree diff equals the item-owned delta, not because nothing reads trailers. Also correct the now-stale `am1g38` citation: that item is `done`, closed by `199u11`.

  LEAVE SECTION 4.2 UNTOUCHED, as the previous correction (`olkeju`) deliberately did, and touch neither the `RUN-COMMIT-CONTENTS` row nor any other table cell. Record the amendment with `aw specs note` naming this plan and item, per the AGENTS.md rule that a plan amending a spec declares it; the spec path is already in `- Scope-Paths:` so the runner's spec-edit announcement and the finalize scope gate both see it. Do NOT use `aw specs set` to change the spec's `- Status:`, which stays `approved`.
  - Depends on: E-05
  - Expected outcome: the paragraph states that a reader ships and names it, that trailer-decided ownership is live in finalize, and that the 4.2 rows stay unbound on the contents-proof ground; `git diff` on the spec shows no change inside the Section 4.2 table; `aw specs note` has appended a dated workflow-history line naming `2lxcwt` and `oye21y`.
  - Execution state: pending

### Task group 4: prove nothing behavioral moved

- [ ] E-07 RUN THE SUITE BARE and confirm this comment-only change moved no behavior. Run `python3 -m pytest` with NO added flags, per the AGENTS.md rule that `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, and paste the actual summary line. Additionally run `python3 -m pytest tests/test_finalize_trailer_attribution.py` on its own, because it is the test that proves the reader this plan's new wording asserts exists.

  ALSO RUN `aw check` AND `aw sanitize --agent`, the first because this plan edits an approved spec and a records-tree consistency rule could refuse, the second because the edited prose newly names symbols and plan ids and must contain no local-machine identifying material. A `check` finding UNRELATED to this plan's paths is not this plan's to fix: record it and say so.
  - Depends on: E-06
  - Expected outcome: a bare `python3 -m pytest` summary line pasted showing no new failures versus the E-01 baseline; `6 passed` for the trailer-attribution file; `aw check` and `aw sanitize --agent` output pasted with any pre-existing finding identified as such.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan cites every one of its six edit sites by content string for exactly that reason; `run_evidence.py` is over 2200 lines and `ipd_lifecycle.py` over 5400, so offsets in them are especially short-lived.
- `waiting_on` IS NOT A SPEC-TRANSCRIBED FIELD. Spec `25kzda` Section 4.2's table has five columns (code, inspects, pass_criterion, message, action). `binding`, `predicates` and `waiting_on` are the package's OWN annotation, added by plan `wlxkoz`, and `RunFindingCode`'s docstring describes `waiting_on` as "for an UNBOUND row, the missing machinery (and its owner, when one exists)". So editing it is not editing the spec's transcription, which is what makes E-03 a safe change.
- AN UNBOUND ROW MUST KEEP A NONEMPTY `waiting_on`. `validate_finding_table` fails `RC-BINDING` with "unbound code does not say what it waits on" when an unbound row's `waiting_on` is empty, and fails the mirror case when a BOUND row declares one. So E-03 must REWORD the string, never empty it, and must not flip `binding` without also supplying predicates.
- THE REPOSITORY'S STANDING PROHIBITION ON PRESENCE-BASED BINDING governs what this plan may not do. Backlog `d07nz2` records that neither `RUN-COMMIT-*` code "may later be bound to a presence-based inference, which is the fail-OPEN pattern already rejected for the host capabilities", and `run_evidence.py`'s own comment calls a fail-open checker "strictly worse than having no code at all". Correcting a staleness claim is therefore NOT license to bind the code on the strength of the new reader.
- Backlog `u7bfks` (open) carries the live question of whether `BOUND` should require a REACHABLE call site rather than an existing predicate, and cites these two rows as the ones already held to the stricter standard. This plan must not pre-empt that decision.

## Findings

| # | Confidence | Subject | Finding | Evidence |
|---|---|---|---|---|
| F-01 | HIGH | the core claim is false | 843 of 5551 non-merge commits carry `AW-Item`, and the same count carry `AW-Run`, so "nothing in the tree passes trailers yet" is false by three orders of magnitude. | `git log --no-merges --format="%H%x00%(trailers:key=AW-Item,valueonly)" \| awk -F'\0' '$2!=""' \| wc -l` -> `843`; `git log --no-merges --format=%H \| wc -l` -> `5551`; measured at HEAD `d77a4971` |
| F-02 | HIGH | THE ITEM'S PRESCRIBED WORDING IS ALSO FALSE | The item says the correct statement is "driver-side sites pass them; nothing reads them back". The second half is now false: a reader ships and is consumed on every finalize. This is the finding that reshaped the plan. | `ipd_lifecycle._commit_run_ownership` reads `%(trailers:key=...,valueonly)`; `_trailer_owned_committed_paths` classifies `base_head..HEAD`; `finalize_precheck` assigns `evidence["trailer_attribution"]`; plan `199u11` is in `plans/executed/` |
| F-03 | HIGH | the reader is tested, not merely present | The reader has live behavioral coverage, so E-03's new wording rests on a proven surface rather than on a symbol's existence. | `python3 -m pytest tests/test_finalize_trailer_attribution.py` -> `6 passed in 2.36s` |
| F-04 | HIGH | the item's second location does not exist as cited | The item names symbol `_scope_attributed_commits` and quotes "essentially no commit in history carries one yet". Both return ZERO matches: `199u11` already rewrote that docstring. An executor following the item literally would find nothing to edit. | `grep -c _scope_attributed_commits agent_workflows/ipd_lifecycle.py` -> `0`; `grep -c "essentially no commit in history carries one yet" agent_workflows/ipd_lifecycle.py` -> `0` |
| F-05 | HIGH | what DOES remain at that file | Two `a8eufb` pointers survive in `ChangedPathSources`, one asserting "`a8eufb` remains the real fix" while `a8eufb` is `done`. This is the real second location, reached by re-deriving from disk rather than from the item. | `grep -rn a8eufb agent_workflows/` -> exactly two hits, both in `ipd_lifecycle.py`; `.aw/records/backlog/done/20260830-scopeattrib-01-a8eufb-...backlog.md` |
| F-06 | HIGH | THE GUARD THREE PLANS WARN ABOUT DOES NOT EXIST | `wao266` and `j0ag0u` both state the 4.2 table is "transcribed into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so a cell edit is a code change". No such test exists: NO test file references `RUN_FINDING_CODES`, `validate_finding_table`, or `pass_criterion`. The runtime self-check is the only live guard. E-02 re-measures rather than trusting either belief. | `grep` for each of the three symbols over `tests/` -> "No files found" for all three; `validate_finding_table` appears only in `run_evidence.py` |
| F-07 | HIGH | the table is currently self-valid | The binding partition and validity are intact, giving E-03/E-04 an exact before-state to preserve. | `validate_finding_table()` -> `ok=True`; `Counter(r.binding for r in RUN_FINDING_CODES)` -> `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}`; 12 codes; unbound = `['RUN-COMMIT-CONTENTS', 'RUN-COMMIT-GATEWAY']` |
| F-08 | HIGH | the same falsehood is in the SPEC | Spec `25kzda` says "NOTHING READS A TRAILER BACK (backlog `am1g38`), so no commit's ownership is yet decided by its trailer". Both clauses are false post-`199u11`, and `am1g38` is `done`. Correcting only the code would leave the falsehood in the artifact the corrected comments cite, which is the exact failure `olkeju`'s review named when it filed this item. | the quoted clause in the spec's Infrastructure paragraph; `.aw/records/backlog/done/20260922-trailread-01-am1g38-...backlog.md` with `- Status: done` closed by `199u11` |
| F-09 | MED | the unbound CONCLUSION is still correct | The reader answers ownership ("is this commit's `AW-Item` mine"), not contents ("does this commit's tree diff equal the item-owned delta"), which is what `RUN-COMMIT-CONTENTS`'s `pass_criterion` demands. So the row stays `UNBOUND_BY_DEPENDENCY` and only its REASON changes. Binding it on the reader's existence would be the fail-open error the module's own comment rejects. | `RUN-COMMIT-CONTENTS.pass_criterion` "its path union equals the action-owned delta"; `_commit_run_ownership` returns only `owned`/`foreign`/`unknown`; backlog `d07nz2`'s standing prohibition |
| F-10 | MED | both writer-side halves have closed | `j2srcc` ("trailer the agent's code commits") and `am1g38` are both `done`, and `git_commit_helper` exports `RUN_ID_ENV`/`ITEM_ID6_ENV` so an agent turn's `aw commit` stamps trailers from the environment. This explains the 843: it is not driver-only any more, so even the item's FIRST half ("driver-side sites pass them") understates it. | both items in `backlog/done/`; `git_commit_helper.RUN_ID_ENV = "AW_RUN_ID"`, `ITEM_ID6_ENV = "AW_ITEM_ID6"`; five `run_item_trailers` call sites in `runner_shared.py` |

## Proposed changes (ordered, validatable)

1. Re-measure the census, the reader's presence, its tests, and the table's validity (E-01), then re-measure the claimed byte-equality fence (E-02). Both precede every edit because this plan is a correction of a correction and its own figures are perishable.
2. Reword `RUN-COMMIT-CONTENTS`'s `waiting_on` to name the shipped writer and reader and the missing tree-diff contents proof, changing no other field (E-03).
3. Correct the two false sentences in the `BINDINGS RE-MEASURED` comment block, preserving the fail-open argument and marking any retained `m73aet` quotation as historical (E-04).
4. Repoint the two `a8eufb` references in `ChangedPathSources`, keeping the HONEST BOUND paragraph byte-identical (E-05).
5. Amend spec `25kzda`'s Infrastructure paragraph, preserving its still-true conclusion while correcting its reason and its dead citation, and record it with `aw specs note` (E-06).
6. Run the bare suite plus `aw check` and `aw sanitize --agent` to prove nothing behavioral moved (E-07).

## Deferred / out of scope (with reason)

- BINDING `RUN-COMMIT-CONTENTS` OR `RUN-COMMIT-GATEWAY`. Declined deliberately, not for cost. `RUN-COMMIT-CONTENTS` needs a predicate proving a commit's tree diff equals the item-owned delta; the shipped reader proves OWNERSHIP, which is a different question (F-09). `RUN-COMMIT-GATEWAY` needs a captured gateway RECEIPT and is untouched by the reader, since `offer_commit` is a helper the driver chooses to call and `host_sandbox_profile` declares `supports_commit_gateway` False and never probes it. Binding either on the strength of a reader is the presence-based, fail-open inference backlog `d07nz2` prohibits by name.
  - Carrier-Declined: NOT AN OBLIGATION THIS PLAN CREATES OR DEFERS, and deliberately not handed to a carrier. The two codes are ALREADY declared outstanding durably and machine-readably in the tree, as `binding=UNBOUND_BY_DEPENDENCY` plus a nonempty `waiting_on` on both rows of `run_evidence.RUN_FINDING_CODES`, which `validate_finding_table` enforces cannot be empty; this plan's whole purpose is to make that declaration ACCURATE. Filing a carrier would duplicate a live declaration, which is the same reasoning review `8apjpp` D-5 recorded when it declined a carrier for this identical obligation. Note the prohibition's original home, backlog `d07nz2`, is `done` and so is INELIGIBLE as a `- Carrier:` anyway; it is cited here as the provenance of the standing rule, not as an owner.
- THE `BOUND`-MEANS-REACHABLE QUESTION. Whether `BOUND` should require a reachable call site rather than an existing predicate, and whether the table needs a third state to keep the distinction visible, is a live design question that cites these two rows as the ones already held to the stricter standard by hand. This plan must not pre-empt it.
  - Carrier: u7bfks
- ADDING A TEST FOR THE FINDING TABLE. F-06 measures that the table has ZERO test coverage, which is a real gap and is genuinely alarming for a 12-row audit surface whose only live guard is a runtime self-check. It is NOT this plan's: the item is a comment correction, and a test asserting `waiting_on` text would pin exactly the hand-maintained prose that keeps rotting.
  - Carrier: a6i03f
- THE OTHER `IPD-EXEC-*` AND `RUN-*` STALENESS. Not surveyed here beyond the trailer claim.
  - Carrier-Declined: NO MEASURED DEFECT IS BEING SET ASIDE, so there is nothing to carry. This plan measured the trailer claim specifically and found it false in three places; it makes no claim, in either direction, about any other code's prose, and filing a carrier for an unmeasured hunch would be exactly the unmeasured filing AGENTS.md rejects ("an unmeasured hunch that something feels slow is not a bug and should not be filed as one"). A survey of the remaining families is a separate piece of work someone may choose to scope.

## Scope check

- Over-scope: The spec file is in scope and the item does not mention it. Justified rather than opportunistic: it carries the IDENTICAL false claim (F-08), it is the artifact the corrected code comments cite, and leaving it would let the next reader undo this correction from the spec side, which is precisely the failure mode that caused `olkeju`'s review to file this item in the first place. Declared in `- Scope-Paths:` per the AGENTS.md spec-amendment rule.
- Under-scope: The item names two locations; this plan edits four sites across three files, because one of the item's two locations does not exist as cited (F-04) and the falsehood is present in two further places (F-05, F-08). No requirement of the item is dropped: both concerns it raises (the false claim, the dead `a8eufb` pointer) are addressed at the places they actually live.

## Required tests / validation

No new test is added and none is expected to change, this being a comment-and-prose correction with no behavioral surface. Validation is therefore three things: (1) the BARE suite unchanged from baseline, which is what proves the claim of no behavioral movement; (2) `validate_finding_table().ok` still `True` with an unchanged binding partition, which proves E-03 did not break the row's invariants; and (3) targeted greps proving each false string is gone and each preserved clause survives.

`tests/test_finalize_trailer_attribution.py` is run separately and by name because it is the evidence that the reader this plan's new wording asserts exists actually works. Its 6 tests are the factual basis of E-03's replacement text.

## Spec / documentation sync

Spec `25kzda` IS amended by E-06, and the reason is stated here because a spec edit changes the contract every other plan is reviewed against. The spec's Infrastructure-status paragraph asserts that nothing reads a trailer back and that no commit's ownership is decided by one; after `199u11` both are false, and that paragraph is cited BY the code comments this plan corrects, so correcting the code alone would leave the two artifacts contradicting each other with the spec on the wrong side. Section 4.2 is deliberately NOT touched, matching `olkeju`'s earlier correction. The amendment is recorded with `aw specs note`; the spec's `- Status:` stays `approved` and this plan writes no approval attestation.

No `docs/` change: no documented behavior changes.

## Open questions

### OQ-01: Should the retained `m73aet` quotation be kept-as-historical or deleted outright?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: KEEP IT, MARKED AS HISTORICAL. The quotation is true as a record of what `m73aet`'s receipt said in 2026-08-30, and an executed plan's record may not be rewritten; deleting the quote would also erase why the comment ever said this, which is the trail a future reader needs. E-04 therefore permits either keeping it marked as historical or deleting it, and forbids only the present-tense form. Resolved from the AGENTS.md rule that an executed plan's record is not changed in place.

### OQ-02: Does correcting `waiting_on` risk a reader concluding the code should now be bound?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, and E-03 is written to prevent it. This is the one genuine risk in the plan: naming a shipped reader inside a string that explains why a code is UNBOUND invites the inference that the blocker is gone. E-03's clause (3) therefore requires the new text to name the missing CONTENTS proof as the operative reason, and the Deferred section records the prohibition with its carrier (`d07nz2`). The distinction is stated in F-09: ownership is not contents.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the four raw command outputs pasted verbatim (trailered-vs-total census; the three reader symbols located; `pytest tests/test_finalize_trailer_attribution.py` summary; `validate_finding_table()` validity plus `Counter` of bindings), each with the command that produced it, plus an explicit sentence per figure stating match or divergence from authoring (843/5551, reader present, `6 passed`, `ok=True` with 10/2). A recorded divergence is a PASS provided the plan's premise (reader exists, census nonzero) still holds; if the reader is absent, V-01 passes only if execution STOPPED and said so.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of the searches over `tests/` for `RUN_FINDING_CODES`, `validate_finding_table`, and `pass_criterion`, plus the search identifying which test files reference the trailer reader; and one sentence stating whether a byte-equality guard exists. If one IS found, paste its name and state what it constrains and how E-03/E-04 stayed inside it.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff agent_workflows/run_evidence.py` for the row, showing ONLY `waiting_on` changed; the new string quoted in full; `grep -c "nothing reads a trailer back" agent_workflows/run_evidence.py` and `grep -c "passes trailers yet" agent_workflows/run_evidence.py` both reflecting removal from this row; proof the new text names `git_commit_helper.run_item_trailers`, the `ipd_lifecycle` reader symbol, and the missing tree-diff contents proof; and `validate_finding_table().ok` -> `True` with `Counter(r.binding ...)` unchanged at `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}` and `predicates` still empty for the row.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff` of the comment block; proof that no present-tense claim that nothing reads or passes trailers survives anywhere in the file; and positive proof by quotation that four clauses SURVIVE: the `RUN-HOST-CAPABILITY` and `RUN-BASELINE-OWNERSHIP` binding notes, "Writing a trailer is not proving a commit's tree diff equals the item-owned delta", the fail-open warning, and the "must NOT be read as" caution about the empty unbuilt set. If an `m73aet` quotation is retained, quote the surrounding sentence showing it is marked historical.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff agent_workflows/ipd_lifecycle.py` confined to the `ChangedPathSources` docstring; `grep -n a8eufb agent_workflows/ipd_lifecycle.py` output with each surviving mention (if any) shown to be historical and no mention asserting it "remains the real fix"; and byte-identity of the HONEST BOUND paragraph demonstrated by its absence from the diff.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `git diff` of the spec showing the reworded clause; proof the Section 4.2 table is absent from the diff; the new text quoted showing it names the shipped reader, states trailer-decided ownership is live in finalize, preserves the rows-stay-unbound conclusion, and drops or corrects the `am1g38` citation; and the appended `aw specs note` history line quoted, naming `2lxcwt` and `oye21y`, with the spec's `- Status:` shown still `approved`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the ACTUAL pasted summary line of a BARE `python3 -m pytest` (no added flags), compared against the E-01 baseline with any delta explained; `6 passed` for `tests/test_finalize_trailer_attribution.py`; and pasted `aw check` and `aw sanitize --agent` output, with any finding shown to be pre-existing (reproduced at the E-01 baseline commit) rather than introduced. A nonzero `aw sanitize` exit is a FAIL.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

This plan is `to-review` and carries no `- Readiness:` field: that field is an output of `/plan-review` and writing one here would forge an attestation the auto-approve predicate reads. Execution requires explicit human approval recorded via `aw ipd set approved`.

On execution, honor the repository execution contract: commit ONLY the paths named in `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` or `-a`, never push, and never `--no-verify`. Paste ACTUAL runner output for E-07 rather than claiming success. Because this plan edits an approved spec, the runner announces the declared spec edit before the run and reconciles it at finalize; the spec path is declared, so that reconciliation should pass without a scope reason.

Do not mark this plan executed or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence. This is a prose-only change, so the temptation to finalize on inspection alone is real: V-07's bare-suite line is the one item that cannot be satisfied by reading the diff, and it is required.

GATE NOTE: backlog `oye21y` carries no `- Blocks-Release:`, so this plan inherits none and invents none.
