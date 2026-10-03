# IPD: Correct the stale trailer-consumption claims in run_evidence and ipd_lifecycle, which the trailer READER has now outdated in a third place

- Date: 2026-09-30
- Kind: child
- Concern: Code comments assert that nothing in the tree passes `AW-Run:`/`AW-Item:` commit trailers and that no commit carries one, which is false. `run_evidence.py`'s `RUN-COMMIT-CONTENTS` `waiting_on` string still reads "`m73aet`'s own executed receipt records that nothing in the tree passes trailers yet", while hundreds of non-merge commits carry one (`git log --no-merges --format="%H%x00%(trailers:key=AW-Item,valueonly)"`, nonempty second field: 843 of 5551 at authoring HEAD `d77a4971`, re-measured 965 of 5685 at review HEAD `f801830f`, a drift of 122 in under a day that is itself the argument for writing no count into the replacement prose). THE ITEM'S OWN PRESCRIPTION IS ITSELF STALE, and that is the finding that decides this plan's shape: the item says the correct statement is "driver-side sites pass them; nothing reads them back", but plan `199u11` (`trailread-02`) has since EXECUTED and shipped a READER, so the second half is now false too. `ipd_lifecycle._commit_run_ownership` reads `AW-Item`/`AW-Run` via `git log --format=%(trailers:key=...,valueonly)`, `_trailer_owned_committed_paths` classifies every commit in `base_head..HEAD`, `finalize_precheck` consumes the result into a `trailer_attribution` evidence block ahead of cohesion, and `tests/test_finalize_trailer_attribution.py` passes (6 tests). The item's second location is doubly unreachable as written: it names symbol `_scope_attributed_commits`, which does not exist (`grep -c` returns 0), and quotes "essentially no commit in history carries one yet", which also returns 0 because `199u11` already rewrote that docstring. What DOES remain at that file is a different stale claim, the two surviving `a8eufb` pointers in `ChangedPathSources`, one of which says "`a8eufb` remains the real fix" when `a8eufb` is `done`.
- Scope: Replace the false and now doubly-stale claims with what the tree actually does, WITHOUT changing any finding-code binding. IN: (a) `run_evidence.py`'s `RUN-COMMIT-CONTENTS` `waiting_on` string, reworded to name the still-missing predicate (a tree-diff proof that a commit's path union equals the item-owned delta) and to stop asserting that nothing passes or reads trailers; (b) the same file's `BINDINGS RE-MEASURED 2026-09-05` comment block, whose bullet repeats "nothing reads a trailer back" and whose closing paragraph calls the outstanding machinery "a trailer READER"; (c) `ipd_lifecycle.py`'s two surviving `a8eufb` pointers in `ChangedPathSources`, repointing them at the shipped reader and dropping the dead "remains the real fix" claim; (d) spec `25kzda`'s Infrastructure-status paragraph, whose "NOTHING READS A TRAILER BACK (backlog `am1g38`)" clause is the same falsehood in the artifact this plan's own corrections cite, and whose "the AGENT's own code commits are generally UNTRAILERED (backlog `j2srcc`)" clause in the SAME sentence is a third falsehood found at review (F-11), both amended with `aw specs note`. OUT: the `binding` field of `RUN-COMMIT-CONTENTS` or `RUN-COMMIT-GATEWAY` (both stay `UNBOUND_BY_DEPENDENCY`; see Deferred, and the standing prohibition in backlog `d07nz2`); Section 4.2's table row cells (`inspects`, `pass_criterion`, `message`, `action`); `RUN-COMMIT-GATEWAY`'s own `waiting_on`, which waits on a commit-gateway RECEIPT and is unaffected by the reader; the `## Workflow history` note at the spec's end, whose `olkeju` line is a historical record of a prior amendment and must stay byte-identical even though a falsehood-grep matches it (F-12); and any behavior change whatsoever, this being a comment-and-prose correction.
- Scope-Paths: agent_workflows/run_evidence.py, agent_workflows/ipd_lifecycle.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
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
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 2lxcwt verified (set oye21y, attempt 1).
- 2026-10-01 approved (aw set): status set to approved

- 2026-09-30 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review APPROVE WITH REVISIONS APPLIED; PR-101 (HIGH, fixed), PR-102, PR-103, PR-104 (MEDIUM, all fixed), PR-105, PR-106, PR-107 (LOW, all fixed). Typed record at `.aw/records/reviews/20260930-oye21y-01-2lxcwt-correct-the-stale-trailer-consumption-claims-in-run-evidence.review.md` with six `### Decisions` rows, none irreversible. Nearly every measurement reproduced at HEAD `f801830f`: the reader's three symbols, `6 passed`, `ok=True` with 10/2 over 12 codes, F-04's two zero-hit greps, F-05's exactly two `a8eufb` pointers, and F-09's ownership-is-not-contents distinction read off the consumer. The re-derive-from-disk-not-from-the-item decision was right.
  THE DOMINANT REVISION: A THIRD FALSEHOOD IN THE SAME SPEC SENTENCE (PR-101, F-11). The clause "the AGENT's own code commits are generally UNTRAILERED (backlog `j2srcc`)" sits in the sentence E-06 opens, and it is as false as the two the plan targeted: `j2srcc` closed 2026-09-27 via executed plan `a6xbso`, and measured at review 178 of the last 202 non-merge commits are trailered, including the agent's own `work(...)` commits. The plan's own F-10 already had the evidence and did not carry it into the spec edit, so as authored E-06 would have shipped a sentence correcting two of its three false clauses, re-seeding the rot this plan exists to stop. E-06 now names all three, corrects both dead citations, and E-01 gained a fifth measurement with a scoped stop condition.
  THIS PLAN'S OWN FINDINGS ROTTED DURING REVIEW, which is the sharpest possible argument for its no-dated-counts rule and is now recorded as such (PR-102/PR-104, F-13). F-06's "no test references `RUN_FINDING_CODES`" expired fourteen hours after authoring when commit `8b9d7945` added `test_commit_gateway_claim_consistency`; the census moved 843/5551 -> 965/5685; `run_item_trailers` moved 5 -> 9 call sites. The new guard is NOT the byte-equality fence three prior plans warn of and constrains nothing here (it pins `RUN-COMMIT-GATEWAY`'s `binding` and empty `predicates` only), so E-02 now runs it before AND after as positive proof the fence held, and it is recorded as a welcome tripwire against the OQ-02 overcorrection for that one row.
  TWO OMISSIONS EACH WORTH AN EXECUTION TURN, both fixed: the spec carries the target phrase a second time inside `olkeju`'s own historical `aw specs note` line, which must stay byte-identical and is now explicitly excluded (PR-103, F-12); and `aw specs note` stages and commits nothing, so the spec file must reach the plan's own `aw commit` (PR-105). Also fixed: both author-resolved open questions carried `- Owner: none`, which no mechanical check catches (PR-106). F-14 records that pending plan `6uhtko` quotes but does not edit the same string, so there is no same-sentence conflict and file overlap alone is not a hazard. `aw ipd lint` conforming at `author` before and `review-finalize` after.

- 2026-09-30 same-status (aw set): status unchanged (to-review)

- 2026-09-30 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `oye21y`. Every claim was re-measured in this lane at HEAD `d77a4971` rather than transcribed, and THREE of the item's premises measured stale: (1) its prescribed replacement wording "nothing reads them back" is now false, because `199u11` executed and shipped the reader; (2) its second location names a symbol `_scope_attributed_commits` that does not exist; (3) the exact string it quotes from `ipd_lifecycle.py` no longer exists either. The scope was therefore re-derived from what is actually on disk (the two surviving `a8eufb` pointers) rather than from the item's citations, and EXTENDED to the spec, which carries the same falsehood and is cited BY the code comments being corrected. Also measured, and load-bearing for the fence: the "byte-equality test" that three prior plans warn guards this table DOES NOT EXIST; no test anywhere references `RUN_FINDING_CODES` (`grep` over `tests/` returns zero files), so the module's runtime `validate_finding_table` self-check is the only live guard. GATE NOTE: item `oye21y` carries no `- Blocks-Release:`, so this plan inherits none and invents none.

## Goal

Make the tree stop asserting, in three places, that nothing writes and nothing reads the run-ownership commit trailers, when 843 commits carry them and finalize reads them on every run. After this plan the two `RUN-COMMIT-*` codes still say UNBOUND, which is correct, but they say so for the reason that is actually true today (no tree-diff proof exists) rather than for a reason that stopped being true when `199u11` landed.

Secondarily, and stated plainly because it is the more durable fix: remove the last two pointers to backlog `a8eufb`, which is `done`, so a reader chasing "the real fix" is sent to the shipped reader instead of to a closed item.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure, because every number here has already moved once

- [x] E-01 RE-MEASURE THE FIVE FACTS THIS PLAN'S WORDING DEPENDS ON, BEFORE EDITING ANY PROSE. This plan exists because an earlier correction rotted; its own replacement text will rot the same way if written from authoring-time figures, and TWO of its own figures have already moved once between authoring and review (the census and the `run_item_trailers` call count), which is the strongest available argument for doing this first. Run and record raw output for: (a) the trailered-commit census, `git log --no-merges --format="%H%x00%(trailers:key=AW-Item,valueonly)" | awk -F'\0' '$2!=""' | wc -l` against `git log --no-merges --format=%H | wc -l` (authoring: 843 of 5551 at HEAD `d77a4971`; review: 965 of 5685 at `f801830f`); (b) that the READER is present and reachable, by locating `ipd_lifecycle._commit_run_ownership`, `ipd_lifecycle._trailer_owned_committed_paths`, and the `evidence["trailer_attribution"]` assignment inside `finalize_precheck`; (c) `python3 -m pytest tests/test_finalize_trailer_attribution.py` (authoring and review: `6 passed`); (d) `validate_finding_table()` validity plus the binding partition, via `Counter(r.binding for r in RUN_FINDING_CODES)` (authoring and review: `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}`, `ok=True`, 12 codes); (e) that `j2srcc` is still `done` and the agent's own `aw commit` still stamps trailers, since F-11's spec correction depends on it: confirm the item's status and show at least one recent non-driver `work(...)` commit carrying `AW-Item`.

  IF ANY FIGURE HAS MOVED, that is the EXPECTED case for this defect class: use the new measurement and say so explicitly. Do NOT adjust this plan's argument, which depends only on four STRUCTURAL facts and on no number at all: the reader EXISTS, the trailered count is NONZERO, the agent's own commits are trailered, and no tree-diff contents proof exists. TWO STOP CONDITIONS, because either would void a premise rather than move a figure. If (b) fails and the reader has been REMOVED, STOP and record it: the item's original wording would then be correct again. If (e) fails and the agent's own commits are untrailered again, STOP as to E-06's clause (i) only and record it: the spec's `j2srcc` clause would then be true and must be left alone, while every other correction in this plan still stands.
  - Depends on: none
  - Expected outcome: five raw measurements recorded, each with the command that produced it, and an explicit statement of whether each matches the authoring and review figures; any stop condition hit is recorded rather than worked around.
  - Execution state: performed

- [x] E-02 CONFIRM THE FENCE BEFORE TOUCHING THE FINDING TABLE, because three prior plans assert a guard this plan measured as absent, AND A GUARD HAS SINCE APPEARED, so acting on any stale belief is how a wrong edit ships. Plans `wao266` ("that table is transcribed into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so a cell edit is a code change") and `j0ag0u` state a byte-equality test guards Section 4.2. THE AUTHORING MEASUREMENT (zero test files for all three symbols) WAS TRUE WHEN MADE AND IS NOW FALSE: review re-measured at HEAD `f801830f` and `tests/test_host_capability_extension.py` references `RUN_FINDING_CODES`, added 2026-09-30 by commit `8b9d7945` (plan `00pirb`), roughly fourteen hours after this plan was authored. Re-run the measurement rather than trusting either figure: search `tests/` for `RUN_FINDING_CODES`, for `validate_finding_table`, and for `pass_criterion`, and confirm which test files reference the trailer reader.

  WHAT THE NEW GUARD ACTUALLY CONSTRAINS, stated so the executor neither ignores it nor over-reads it (F-13). `test_commit_gateway_claim_consistency` asserts, for the `RUN-COMMIT-GATEWAY` row ONLY, that `binding == UNBOUND_BY_DEPENDENCY` and `predicates == ()`. It is NOT a byte-equality test over the table, it asserts nothing about `waiting_on`, and it does not touch `RUN-COMMIT-CONTENTS`. So it does not constrain any edit this plan makes, and it is a WELCOME tripwire: it would now go RED if a later reader took this plan's corrected wording as license to bind one of these rows, which is exactly the overcorrection OQ-02 is about. RUN IT EXPLICITLY as part of this item rather than relying on the bare suite to cover it.

  THE DISTINCTION THAT MAKES THE EDIT SAFE EITHER WAY: `waiting_on` is NOT one of Section 4.2's five columns (the spec table carries code, inspects, pass_criterion, message, action), so it is not part of any transcription even if a transcription test exists. IF A FURTHER GUARD IS FOUND, honor it: leave every 4.2-derived cell byte-identical and confine the edit to `waiting_on` and the comment block.
  - Depends on: E-01
  - Expected outcome: the search results pasted; a one-sentence statement of which guards exist and what each constrains; and `python3 -m pytest tests/test_host_capability_extension.py -k commit_gateway_claim_consistency` passing both BEFORE and AFTER this plan's edits, proving the edit stayed outside what it pins.
  - Execution state: performed

### Task group 2: correct the three code sites

- [x] E-03 REWORD `RUN-COMMIT-CONTENTS`'s `waiting_on` STRING so it names the predicate that is genuinely missing and asserts nothing false about writers or readers. The site, by content rather than offset: the `waiting_on` tuple inside the `RunFindingCode(code="RUN-COMMIT-CONTENTS", ...)` literal, whose current text is "a trailer READ-BACK predicate. `runtrail-01` (`m73aet`) executed and `git_commit_helper.run_item_trailers` WRITES `AW-Run:`/`AW-Item:`, but nothing reads a trailer back or proves a commit's tree diff equals the item-owned delta; `m73aet`'s own executed receipt records that nothing in the tree passes trailers yet".

  THE NEW TEXT MUST DO EXACTLY THREE THINGS, and the third is what keeps this correction from being an overcorrection into a fail-open binding. (1) DELETE both false clauses: that nothing reads a trailer back, and that nothing in the tree passes trailers yet. (2) NAME WHAT NOW EXISTS, by symbol, so the next reader does not rebuild it: the writer `git_commit_helper.run_item_trailers`, and the reader `ipd_lifecycle._trailer_owned_committed_paths` / `_commit_run_ownership`, shipped by `199u11`. (3) NAME THE STILL-MISSING PREDICATE AS THE REASON THE CODE STAYS UNBOUND: no predicate proves a commit's tree diff EQUALS the item-owned delta, which is this code's actual `pass_criterion`. The existing reader answers a DIFFERENT question (is this commit's `AW-Item` mine), and reading ownership is not proving contents, so the code remains correctly `UNBOUND_BY_DEPENDENCY`.

  KEEP THE STRING A SINGLE `waiting_on` VALUE and change no other field of the row. Do NOT touch `binding`, `predicates` (which must stay empty), `inspects`, `pass_criterion`, `message`, `action`, `abort`, or `abort_classes`. WRITE NO DATED COUNT into the string: a dated snapshot is exactly what the two previous authors wrote in good faith and it rotted both times, so state the facts structurally (a writer exists, a reader exists, a contents proof does not) and leave the census to this plan's Findings.
  - Depends on: E-02
  - Expected outcome: `git diff` on `run_evidence.py` shows only the `waiting_on` string of that one row changed; the new text names both shipped symbols and the missing contents proof, and contains neither "nothing reads" nor "passes trailers yet"; `validate_finding_table().ok` is still `True` and the binding partition is unchanged.
  - Execution state: performed

- [x] E-04 CORRECT THE `BINDINGS RE-MEASURED` COMMENT BLOCK in the same file, which repeats the identical falsehood twice and is the site a reader auditing the table actually reads. Two sentences, by content: the third bullet's "Nothing reads a trailer back, and `m73aet`'s own executed receipt states \"`RUN-COMMIT-GATEWAY` remains wholly unbuilt\" and \"nothing in the tree PASSES trailers yet\""; and the closing `RE-MEASURED 2026-09-22` paragraph's "The two remaining unbound codes still WAIT on machinery (a commit-gateway receipt and a trailer READER)".

  PRESERVE EVERY LOAD-BEARING CLAIM AND CHANGE ONLY WHAT IS FALSE, because the surrounding argument is correct and is the reason the codes are unbound. The block must still say that `RUN-HOST-CAPABILITY` and `RUN-BASELINE-OWNERSHIP` became BOUND and why; that writing a trailer is not proving a commit's tree diff equals the item-owned delta; that binding these two on the strength of a writer "would be exactly the fail-open error described above"; and that an empty UNBUILT set must not be read as "everything is now decided by a predicate". REPLACE ONLY the two false assertions: the reader now EXISTS (name `199u11` and the symbol), and the outstanding machinery is a commit-gateway receipt plus a tree-diff CONTENTS PROOF, not a reader.

  NOTE THE `m73aet` QUOTATIONS ARE HISTORICAL AND MUST NOT BE FALSIFIED. That receipt genuinely said those words in 2026-08-30 and an executed plan's record may not be rewritten. So keep the quotation if it is kept at all, but mark it as what that receipt recorded AT THE TIME and state that both halves have since been overtaken, rather than presenting it as current fact. Deleting the quote entirely is also acceptable; presenting it as present tense is not.
  - Depends on: E-03
  - Expected outcome: `git diff` shows both sentences reworded, with no surviving present-tense claim that nothing reads or passes trailers, every other clause of the block intact, and any retained `m73aet` quotation explicitly marked as historical.
  - Execution state: performed

- [x] E-05 REPOINT THE TWO SURVIVING `a8eufb` REFERENCES in `ipd_lifecycle.py`, which are what actually remains of the item's second location. Both are in the `ChangedPathSources` docstring: "WHAT SCOPEATTR `h9cn0y` DID ABOUT THAT BOUND, since Order 01 left it open (backlog `a8eufb`)" and "That is a heuristic with a stated cost, not the proof a commit trailer would give, so `a8eufb` remains the real fix".

  THE SECOND SENTENCE IS THE DEFECT: `a8eufb` is `- Status: done` (closed by `wao266`), so "remains the real fix" points a reader at a closed item for work that has since shipped. Reword it to say that the trailer fix HAS landed (`199u11`, read via `_trailer_owned_committed_paths`) and is consulted ahead of cohesion, while cohesion remains the fallback for untrailered and foreign commits. The first mention is a HISTORICAL statement about what Order 01 left open and is true as history; keep it, but make clear it is history rather than an open gap.

  KEEP THE HONEST BOUND EXACTLY AS IT IS. The docstring's "HONEST BOUND: ``committed`` is attributable to a COMMIT, not to an AGENT" and its explanation that every agent commits under one git identity must survive unchanged: a trailer is a consistency record, not tamper-proof provenance, which `_commit_run_ownership`'s own docstring already states as its FAIL-CLOSED RULE. Do NOT let this correction read as "attribution is now solved". CONSISTENCY CHECK: `_working_tree_path_is_owned` and the `finalize_precheck` comment were already updated by `199u11` and say "UNTRAILERED commit" in the right places; leave them alone and match their wording rather than inventing a new phrasing.
  - Depends on: E-04
  - Expected outcome: `grep -c a8eufb agent_workflows/ipd_lifecycle.py` reflects the intended state with no surviving claim that a closed item "remains the real fix"; the HONEST BOUND paragraph is byte-identical to before; `git diff` touches only the `ChangedPathSources` docstring.
  - Execution state: performed

### Task group 3: correct the spec that the code comments cite

- [x] E-06 AMEND SPEC `25kzda`'s INFRASTRUCTURE-STATUS PARAGRAPH, which carries the same falsehood and is the artifact the corrected comments point at, so leaving it would undo this plan for anyone reading the spec instead of the code. The clause, by content: "the AGENT's own code commits are generally UNTRAILERED (backlog `j2srcc`); and NOTHING READS A TRAILER BACK (backlog `am1g38`), so no commit's ownership is yet decided by its trailer and Section 4.2's `RUN-COMMIT-*` rows stay unbound".

  THREE CLAUSES ARE NOW FALSE AND THEY FAIL DIFFERENTLY, which is why this is one careful edit and not a deletion. The THIRD was added at review (F-11) because the plan as authored would have corrected two falsehoods and left a third standing in the same sentence, which is precisely the rot this plan exists to stop. (i) "The AGENT's own code commits are generally UNTRAILERED (backlog `j2srcc`)" is false: `j2srcc` is `done`, closed 2026-09-27 by executed plan `a6xbso` ("stamp AW-Run and AW-Item trailers on the agent's own aw commit"), and measured at review the agent's own `work(...)` commits DO carry `AW-Item`. (ii) "Nothing reads a trailer back" is false outright (`199u11`). (iii) "No commit's ownership is yet decided by its trailer" is false too: `finalize_precheck` consults `_trailer_owned_committed_paths` BEFORE and independently of cohesion, so an `AW-Item`-matching commit's paths ARE decided by its trailer today. The CONCLUSION, that the `RUN-COMMIT-*` rows stay unbound, is still TRUE and must be preserved, but its reason changes: they stay unbound because no predicate proves a commit's tree diff equals the item-owned delta, not because nothing reads trailers. Correct BOTH now-stale citations: `am1g38` and `j2srcc` are each `done`.

  WRITE NO SHARE OR COUNT INTO THE SPEC, for the same reason E-03 forbids a dated census: a figure is what rotted twice already. State structurally that the agent's own commits are trailered too, and leave the measurement in this plan's Findings.

  TOUCH ONLY THAT ONE PARAGRAPH. Leave Section 4.2 untouched, as the previous correction (`olkeju`) deliberately did, and touch neither the `RUN-COMMIT-CONTENTS` row nor any other table cell. ALSO LEAVE THE `## Workflow history` NOTE AT THE FILE'S END ALONE: `olkeju`'s own 2026-09-26 `aw specs note` line contains the phrase "nothing reads trailers back (am1g38)", and it is a HISTORICAL RECORD of what that amendment did, true when written. A grep for the falsehood will match it; do not "finish the job" by rewriting it (F-12). Record this amendment with `aw specs note` naming this plan and item, per the AGENTS.md rule that a plan amending a spec declares it; the spec path is already in `- Scope-Paths:` so the runner's spec-edit announcement and the finalize scope gate both see it. `aw specs note` NEVER stages or commits (`specs.py` module docstring), so the spec file must still be committed through this plan's own `aw commit` call. Do NOT use `aw specs set` to change the spec's `- Status:`, which stays `approved`.
  - Depends on: E-05
  - Expected outcome: the paragraph states that the agent's own commits are trailered too, that a reader ships and names it, that trailer-decided ownership is live in finalize, and that the 4.2 rows stay unbound on the contents-proof ground; both `am1g38` and `j2srcc` citations are corrected; `git diff` on the spec shows no change inside the Section 4.2 table and no change to the `## Workflow history` section other than the one appended line; `aw specs note` has appended a dated workflow-history line naming `2lxcwt` and `oye21y`.
  - Execution state: performed

### Task group 4: prove nothing behavioral moved

- [x] E-07 RUN THE SUITE BARE and confirm this comment-only change moved no behavior. Run `python3 -m pytest` with NO added flags, per the AGENTS.md rule that `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`, and paste the actual summary line. Additionally run `python3 -m pytest tests/test_finalize_trailer_attribution.py` on its own, because it is the test that proves the reader this plan's new wording asserts exists.

  ALSO RE-RUN THE TWO TARGETED GUARDS BY NAME, so neither is reported as merely "covered by the bare suite": `tests/test_finalize_trailer_attribution.py` (the reader this plan's new wording asserts exists) and `tests/test_host_capability_extension.py -k commit_gateway_claim_consistency` (the row-binding guard F-13 found, which must be green AFTER as it was BEFORE, proving the edit stayed outside what it pins).

  ALSO RUN `aw check` AND `aw sanitize --agent`, the first because this plan edits an approved spec and a records-tree consistency rule could refuse, the second because the edited prose newly names symbols and plan ids and must contain no local-machine identifying material. A `check` finding UNRELATED to this plan's paths is not this plan's to fix: record it, say so, and demonstrate it is pre-existing by reproducing it at the E-01 baseline rather than asserting it.
  - Depends on: E-06
  - Expected outcome: a bare `python3 -m pytest` summary line pasted showing no new failures versus the E-01 baseline; `6 passed` for the trailer-attribution file; the commit-gateway consistency test passing; `aw check` and `aw sanitize --agent` output pasted with any pre-existing finding demonstrated as such.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan cites every one of its six edit sites by content string for exactly that reason; `run_evidence.py` is over 2200 lines and `ipd_lifecycle.py` over 5400, so offsets in them are especially short-lived.
- `waiting_on` IS NOT A SPEC-TRANSCRIBED FIELD. Spec `25kzda` Section 4.2's table has five columns (code, inspects, pass_criterion, message, action). `binding`, `predicates` and `waiting_on` are the package's OWN annotation, added by plan `wlxkoz`, and `RunFindingCode`'s docstring describes `waiting_on` as "for an UNBOUND row, the missing machinery (and its owner, when one exists)". So editing it is not editing the spec's transcription, which is what makes E-03 a safe change.
- AN UNBOUND ROW MUST KEEP A NONEMPTY `waiting_on`. `validate_finding_table` fails `RC-BINDING` with "unbound code does not say what it waits on" when an unbound row's `waiting_on` is empty, and fails the mirror case when a BOUND row declares one. So E-03 must REWORD the string, never empty it, and must not flip `binding` without also supplying predicates.
- THE REPOSITORY'S STANDING PROHIBITION ON PRESENCE-BASED BINDING governs what this plan may not do. Backlog `d07nz2` records that neither `RUN-COMMIT-*` code "may later be bound to a presence-based inference, which is the fail-OPEN pattern already rejected for the host capabilities", and `run_evidence.py`'s own comment calls a fail-open checker "strictly worse than having no code at all". Correcting a staleness claim is therefore NOT license to bind the code on the strength of the new reader.
- Backlog `u7bfks` (open) carries the live question of whether `BOUND` should require a REACHABLE call site rather than an existing predicate, and cites these two rows as the ones already held to the stricter standard. This plan must not pre-empt that decision.

## Findings

| # | Confidence | Subject | Finding | Evidence |
|---|---|---|---|---|
| F-01 | HIGH | the core claim is false | Hundreds of non-merge commits carry `AW-Item`, and the same number carry `AW-Run`, so "nothing in the tree passes trailers yet" is false by orders of magnitude. THE ARGUMENT RESTS ON "NONZERO AND GROWING", NEVER ON A FIGURE: 843 of 5551 at authoring HEAD `d77a4971`, re-measured at review HEAD `f801830f` as 965 of 5685, i.e. the count moved by 122 in under a day. Both figures are recorded because the DRIFT is itself the evidence for this plan's rule that no dated count may enter the prose it writes. | `git log --no-merges --format="%H%x00%(trailers:key=AW-Item,valueonly)" \| awk -F'\0' '$2!=""' \| wc -l` -> `843` at `d77a4971`, `965` at `f801830f`; `git log --no-merges --format=%H \| wc -l` -> `5551`, then `5685`; `AW-Run` matches the `AW-Item` count at both points |
| F-02 | HIGH | THE ITEM'S PRESCRIBED WORDING IS ALSO FALSE | The item says the correct statement is "driver-side sites pass them; nothing reads them back". The second half is now false: a reader ships and is consumed on every finalize. This is the finding that reshaped the plan. | `ipd_lifecycle._commit_run_ownership` reads `%(trailers:key=...,valueonly)`; `_trailer_owned_committed_paths` classifies `base_head..HEAD`; `finalize_precheck` assigns `evidence["trailer_attribution"]`; plan `199u11` is in `plans/executed/` |
| F-03 | HIGH | the reader is tested, not merely present | The reader has live behavioral coverage, so E-03's new wording rests on a proven surface rather than on a symbol's existence. | `python3 -m pytest tests/test_finalize_trailer_attribution.py` -> `6 passed in 2.36s` |
| F-04 | HIGH | the item's second location does not exist as cited | The item names symbol `_scope_attributed_commits` and quotes "essentially no commit in history carries one yet". Both return ZERO matches: `199u11` already rewrote that docstring. An executor following the item literally would find nothing to edit. | `grep -c _scope_attributed_commits agent_workflows/ipd_lifecycle.py` -> `0`; `grep -c "essentially no commit in history carries one yet" agent_workflows/ipd_lifecycle.py` -> `0` |
| F-05 | HIGH | what DOES remain at that file | Two `a8eufb` pointers survive in `ChangedPathSources`, one asserting "`a8eufb` remains the real fix" while `a8eufb` is `done`. This is the real second location, reached by re-deriving from disk rather than from the item. | `grep -rn a8eufb agent_workflows/` -> exactly two hits, both in `ipd_lifecycle.py`; `.aw/records/backlog/done/20260830-scopeattrib-01-a8eufb-...backlog.md` |
| F-06 | HIGH | THE GUARD THREE PLANS WARN ABOUT DID NOT EXIST AT AUTHORING, AND NOW PARTLY DOES | `wao266` and `j0ag0u` both state the 4.2 table is "transcribed into `run_evidence.RUN_FINDING_CODES` under a byte-equality test, so a cell edit is a code change". NO byte-equality test exists, at authoring or now. BUT THIS ROW'S "zero test files" HALF HAS SINCE EXPIRED, which is this plan's own defect class biting its own Findings: see F-13. Authoring measurement retained verbatim as the historical record; E-02 re-measures. | `grep` for each of the three symbols over `tests/` -> "No files found" for all three at authoring HEAD `d77a4971`; `validate_finding_table` appears only in `run_evidence.py` (still true at review) |
| F-07 | HIGH | the table is currently self-valid | The binding partition and validity are intact, giving E-03/E-04 an exact before-state to preserve. | `validate_finding_table()` -> `ok=True`; `Counter(r.binding for r in RUN_FINDING_CODES)` -> `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}`; 12 codes; unbound = `['RUN-COMMIT-CONTENTS', 'RUN-COMMIT-GATEWAY']` |
| F-08 | HIGH | the same falsehood is in the SPEC | Spec `25kzda` says "NOTHING READS A TRAILER BACK (backlog `am1g38`), so no commit's ownership is yet decided by its trailer". Both clauses are false post-`199u11`, and `am1g38` is `done`. Correcting only the code would leave the falsehood in the artifact the corrected comments cite, which is the exact failure `olkeju`'s review named when it filed this item. | the quoted clause in the spec's Infrastructure paragraph; `.aw/records/backlog/done/20260922-trailread-01-am1g38-...backlog.md` with `- Status: done` closed by `199u11` |
| F-09 | MED | the unbound CONCLUSION is still correct | The reader answers ownership ("is this commit's `AW-Item` mine"), not contents ("does this commit's tree diff equal the item-owned delta"), which is what `RUN-COMMIT-CONTENTS`'s `pass_criterion` demands. So the row stays `UNBOUND_BY_DEPENDENCY` and only its REASON changes. Binding it on the reader's existence would be the fail-open error the module's own comment rejects. | `RUN-COMMIT-CONTENTS.pass_criterion` "its path union equals the action-owned delta"; `_commit_run_ownership` returns only `owned`/`foreign`/`unknown`; backlog `d07nz2`'s standing prohibition |
| F-10 | MED | both writer-side halves have closed | `j2srcc` ("trailer the agent's code commits") and `am1g38` are both `done`, and `git_commit_helper` exports `RUN_ID_ENV`/`ITEM_ID6_ENV` so an agent turn's `aw commit` stamps trailers from the environment. This explains the census: it is not driver-only any more, so even the item's FIRST half ("driver-side sites pass them") understates it. | both items in `backlog/done/`; `git_commit_helper.RUN_ID_ENV = "AW_RUN_ID"`, `ITEM_ID6_ENV = "AW_ITEM_ID6"`; `run_item_trailers` occurs 9 times in `runner_shared.py` (review re-measurement; the authoring figure of five has moved, which changes nothing in the argument) |
| F-11 | HIGH | ADDED AT REVIEW: A THIRD FALSE CLAUSE SITS IN THE SAME SPEC SENTENCE E-06 EDITS | The sentence also says "the AGENT's own code commits are generally UNTRAILERED (backlog `j2srcc`)". That is false: `j2srcc` closed 2026-09-27 via executed plan `a6xbso` ("stamp AW-Run and AW-Item trailers on the agent's own aw commit"), and the agent's own `work(...)` commits now carry `AW-Item`. As authored, E-06 would have corrected two falsehoods and left a third standing in the same sentence, re-seeding the exact rot this plan exists to stop. Note F-10 already KNEW `j2srcc` was done and drew the conclusion for the code comments without carrying it into the spec edit. | `.aw/records/backlog/done/20260922-trailread-01-j2srcc-...backlog.md` `- Status: done`, closed by `a6xbso`; measured at review, `git log` shows `work(0brmmy)`, `work(2lxcwt)`-class agent commits carrying `AW-Item`; 178 of the last 202 non-merge commits are trailered |
| F-12 | MED | ADDED AT REVIEW: A GREP FOR THE FALSEHOOD MATCHES A HISTORICAL RECORD THAT MUST SURVIVE | The spec contains the phrase twice. The second occurrence is inside `olkeju`'s own 2026-09-26 `aw specs note` line in `## Workflow history`, recording what THAT amendment did. It was true when written and an executed plan's record may not be rewritten, so an executor grepping to confirm removal will find a match that must NOT be "fixed". Same hazard shape as the `m73aet` quotation OQ-01 already settled for `run_evidence.py`. | `grep -n "nothing reads\|NOTHING READS"` on the spec -> exactly two hits, line 65 (the live paragraph) and the 2026-09-26 history note; AGENTS.md prohibition on changing what an executed plan records |
| F-13 | MED | ADDED AT REVIEW: F-06's "ZERO TEST FILES" HALF HAS EXPIRED | `tests/test_host_capability_extension.py::test_commit_gateway_claim_consistency` now references `RUN_FINDING_CODES`, added 2026-09-30 by commit `8b9d7945` (plan `00pirb`) about fourteen hours AFTER this plan was authored. It is NOT a byte-equality test: it asserts only that the `RUN-COMMIT-GATEWAY` row has `binding == UNBOUND_BY_DEPENDENCY` and `predicates == ()`. It therefore constrains nothing this plan edits, and is a welcome tripwire against the OQ-02 overcorrection. This plan's own Findings rotting within a day is the sharpest available evidence for its no-dated-counts rule. | `grep -rln RUN_FINDING_CODES tests/` -> `tests/test_host_capability_extension.py`; `git log -S RUN_FINDING_CODES -- tests/test_host_capability_extension.py` -> `8b9d7945 2026-09-30`; plan added at `889a643e 2026-09-30 05:23`, guard at `8b9d7945 2026-09-30 19:45` |
| F-14 | LOW | ADDED AT REVIEW: NO OTHER PENDING PLAN CONFLICTS ON THIS PROSE | One other pending plan, `6uhtko` (`ibuxe6-01`, `approved`), QUOTES `RUN-COMMIT-CONTENTS`'s `waiting_on` string as the model for its own new rows' wording, and declares `agent_workflows/run_evidence.py` in its scope. It does not EDIT that string, adds a separate `IPD_EXEC_*` table, and does not touch the spec file. So there is no same-sentence collision; file overlap alone is not a hazard, since each execute item runs in its own isolated worktree and returns through the merge-and-revalidate gate. Recorded so the question is answered rather than left for the executor to re-derive. | `grep -n "nothing reads a trailer back"` in `6uhtko` -> one hit, a quotation inside a Project-conventions bullet; `6uhtko`'s `- Scope-Paths:` is `agent_workflows/run_evidence.py, tests/test_ipd_exec_finding_codes.py`; AGENTS.md "The runners own ordering, isolation, and orchestrators" |

## Proposed changes (ordered, validatable)

1. Re-measure the census, the reader's presence, its tests, the table's validity, and the agent-commit trailering `j2srcc` closed (E-01), then re-measure the claimed byte-equality fence and run the one guard that HAS since appeared (E-02). Both precede every edit because this plan is a correction of a correction and its own figures are perishable: two of them moved between authoring and review.
2. Reword `RUN-COMMIT-CONTENTS`'s `waiting_on` to name the shipped writer and reader and the missing tree-diff contents proof, changing no other field (E-03).
3. Correct the two false sentences in the `BINDINGS RE-MEASURED` comment block, preserving the fail-open argument and marking any retained `m73aet` quotation as historical (E-04).
4. Repoint the two `a8eufb` references in `ChangedPathSources`, keeping the HONEST BOUND paragraph byte-identical (E-05).
5. Amend spec `25kzda`'s Infrastructure paragraph, correcting all THREE false clauses (the agent's commits are trailered now, a reader exists, trailer-decided ownership is live) and both dead citations, preserving its still-true unbound conclusion on the contents-proof ground, leaving `olkeju`'s historical history note alone, and recording the amendment with `aw specs note` (E-06).
6. Run the bare suite plus `aw check` and `aw sanitize --agent` to prove nothing behavioral moved (E-07).

## Deferred / out of scope (with reason)

- BINDING `RUN-COMMIT-CONTENTS` OR `RUN-COMMIT-GATEWAY`. Declined deliberately, not for cost. `RUN-COMMIT-CONTENTS` needs a predicate proving a commit's tree diff equals the item-owned delta; the shipped reader proves OWNERSHIP, which is a different question (F-09). `RUN-COMMIT-GATEWAY` needs a captured gateway RECEIPT and is untouched by the reader, since `offer_commit` is a helper the driver chooses to call and `host_sandbox_profile` declares `supports_commit_gateway` False and never probes it. Binding either on the strength of a reader is the presence-based, fail-open inference backlog `d07nz2` prohibits by name.
  - Carrier-Declined: NOT AN OBLIGATION THIS PLAN CREATES OR DEFERS, and deliberately not handed to a carrier. The two codes are ALREADY declared outstanding durably and machine-readably in the tree, as `binding=UNBOUND_BY_DEPENDENCY` plus a nonempty `waiting_on` on both rows of `run_evidence.RUN_FINDING_CODES`, which `validate_finding_table` enforces cannot be empty; this plan's whole purpose is to make that declaration ACCURATE. Filing a carrier would duplicate a live declaration, which is the same reasoning review `8apjpp` D-5 recorded when it declined a carrier for this identical obligation. Note the prohibition's original home, backlog `d07nz2`, is `done` and so is INELIGIBLE as a `- Carrier:` anyway; it is cited here as the provenance of the standing rule, not as an owner.
- THE `BOUND`-MEANS-REACHABLE QUESTION. Whether `BOUND` should require a reachable call site rather than an existing predicate, and whether the table needs a third state to keep the distinction visible, is a live design question that cites these two rows as the ones already held to the stricter standard by hand. This plan must not pre-empt it.
  - Carrier: u7bfks
- ADDING A TEST FOR THE FINDING TABLE. F-06 measured that the table had ZERO test coverage, which was a real gap and genuinely alarming for a 12-row audit surface whose only live guard is a runtime self-check. REVISED AT REVIEW: the gap has NARROWED but not closed. `tests/test_host_capability_extension.py::test_commit_gateway_claim_consistency` now asserts two fields of ONE row (F-13), so the table is no longer wholly unasserted, while the other eleven rows and every `waiting_on` string remain uncovered. It is still NOT this plan's: the item is a comment correction, and a test asserting `waiting_on` TEXT would pin exactly the hand-maintained prose that keeps rotting, which is the trap `a6i03f` was written to avoid by deriving from the spec instead.
  - Carrier: a6i03f
- THE OTHER `IPD-EXEC-*` AND `RUN-*` STALENESS. Not surveyed here beyond the trailer claim.
  - Carrier-Declined: NO MEASURED DEFECT IS BEING SET ASIDE, so there is nothing to carry. This plan measured the trailer claim specifically and found it false in three places; it makes no claim, in either direction, about any other code's prose, and filing a carrier for an unmeasured hunch would be exactly the unmeasured filing AGENTS.md rejects ("an unmeasured hunch that something feels slow is not a bug and should not be filed as one"). A survey of the remaining families is a separate piece of work someone may choose to scope.

## Scope check

- Over-scope: The spec file is in scope and the item does not mention it. Justified rather than opportunistic: it carries the IDENTICAL false claim twice over (F-08, F-11), it is the artifact the corrected code comments cite, and leaving it would let the next reader undo this correction from the spec side, which is precisely the failure mode that caused `olkeju`'s review to file this item in the first place. Declared in `- Scope-Paths:` per the AGENTS.md spec-amendment rule. Nothing else is over-scope: no test file is added (declined with a carrier, see Deferred), no `binding` or `predicates` value is touched, and no behavior changes.
- Under-scope: The item names two locations; this plan edits four sites across three files, because one of the item's two locations does not exist as cited (F-04) and the falsehood is present in two further places (F-05, F-08), one of which carries THREE false clauses rather than one (F-11). No requirement of the item is dropped: both concerns it raises (the false claim, the dead `a8eufb` pointer) are addressed at the places they actually live. One candidate was checked and deliberately excluded: `tests/test_host_capability_extension.py` needs NO edit, because the guard it added pins only `RUN-COMMIT-GATEWAY`'s `binding` and empty `predicates` and this plan changes neither (F-13). Should an edit outside `- Scope-Paths:` prove genuinely necessary, MAKE it and justify it with a `--scope-reason` at finalize rather than leaving the work unfinished.

## Required tests / validation

No new test is added and none is expected to change, this being a comment-and-prose correction with no behavioral surface. Validation is therefore three things: (1) the BARE suite unchanged from baseline, which is what proves the claim of no behavioral movement; (2) `validate_finding_table().ok` still `True` with an unchanged binding partition, which proves E-03 did not break the row's invariants; and (3) targeted greps proving each false string is gone and each preserved clause survives.

`tests/test_finalize_trailer_attribution.py` is run separately and by name because it is the evidence that the reader this plan's new wording asserts exists actually works. Its 6 tests are the factual basis of E-03's replacement text.

`tests/test_host_capability_extension.py -k commit_gateway_claim_consistency` is run separately and by name for the OPPOSITE reason: it is the one shipped assertion that could in principle object to an edit in this file, and it must be green AFTER exactly as it was BEFORE. It pins `RUN-COMMIT-GATEWAY`'s `binding` and empty `predicates` and nothing else (F-13), so a green run after this plan's edits is positive proof the correction stayed inside its fence rather than quietly loosening a binding claim.

## Spec / documentation sync

Spec `25kzda` IS amended by E-06, and the reason is stated here because a spec edit changes the contract every other plan is reviewed against. The spec's Infrastructure-status paragraph asserts, in ONE sentence, that the agent's own code commits are generally untrailered, that nothing reads a trailer back, and that no commit's ownership is decided by one. All three are false: the first after `a6xbso` closed `j2srcc` (F-11, found at review), the second and third after `199u11`. That paragraph is cited BY the code comments this plan corrects, so correcting the code alone would leave the two artifacts contradicting each other with the spec on the wrong side. Section 4.2 is deliberately NOT touched, matching `olkeju`'s earlier correction, and neither is the file's `## Workflow history` section beyond the one line `aw specs note` appends (F-12). The amendment is recorded with `aw specs note`, which stages and commits nothing, so the spec file is committed by this plan's own path-scoped `aw commit`; the spec's `- Status:` stays `approved` and this plan writes no approval attestation.

THE AMENDMENT IS A PROSE-STATUS CORRECTION, NOT A CONTRACT CHANGE, and the distinction is worth stating because it bounds what a reviewer of another plan must re-check. No requirement, finding code, table cell, or normative clause changes; the paragraph is the spec's own self-reported infrastructure STATUS, and its operative conclusion (the two `RUN-COMMIT-*` rows stay unbound) is preserved with a corrected reason. No other pending plan's review basis moves as a result.

No `docs/` change: no documented behavior changes.

## Open questions

### OQ-01: Should the retained `m73aet` quotation be kept-as-historical or deleted outright?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: KEEP IT, MARKED AS HISTORICAL. The quotation is true as a record of what `m73aet`'s receipt said in 2026-08-30, and an executed plan's record may not be rewritten; deleting the quote would also erase why the comment ever said this, which is the trail a future reader needs. E-04 therefore permits either keeping it marked as historical or deleting it, and forbids only the present-tense form. Resolved from the AGENTS.md rule that an executed plan's record is not changed in place.

### OQ-02: Does correcting `waiting_on` risk a reader concluding the code should now be bound?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes, and E-03 is written to prevent it. This is the one genuine risk in the plan: naming a shipped reader inside a string that explains why a code is UNBOUND invites the inference that the blocker is gone. E-03's clause (3) therefore requires the new text to name the missing CONTENTS proof as the operative reason, and the Deferred section records the prohibition (backlog `d07nz2`, cited as provenance; it is `done` and so ineligible as a carrier). The distinction is stated in F-09: ownership is not contents.
  STRENGTHENED AT REVIEW, AND NOW PARTLY MACHINE-GUARDED. The prose argument above is no longer the only defense for one of the two rows: `tests/test_host_capability_extension.py::test_commit_gateway_claim_consistency`, added 2026-09-30 after this plan was authored, asserts that `RUN-COMMIT-GATEWAY` carries `binding == UNBOUND_BY_DEPENDENCY` and `predicates == ()` (F-13). So a future reader who took this plan's corrected wording as license to bind THAT row would now go red. `RUN-COMMIT-CONTENTS`, the row this plan actually edits, has NO such guard, so for it the prose remains the only defense and E-03's clause (3) is load-bearing. That asymmetry is recorded rather than smoothed over, because it is the honest statement of how much protection exists.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the FIVE raw command outputs pasted verbatim (trailered-vs-total census; the three reader symbols located; `pytest tests/test_finalize_trailer_attribution.py` summary; `validate_finding_table()` validity plus `Counter` of bindings; `j2srcc` status plus a recent trailered agent `work(...)` commit), each with the command that produced it, plus an explicit sentence per figure stating match or divergence from the authoring AND review figures (census 843/5551 then 965/5685; reader present; `6 passed`; `ok=True` with 10/2; `j2srcc` done). A recorded divergence in any COUNT is a PASS, since no count is load-bearing. A failure of a STRUCTURAL premise is not: if the reader is absent, V-01 passes only if execution STOPPED and said so; if the agent's commits are untrailered again, V-01 passes only if E-06's clause (i) was left alone and that was recorded.
  - Observed evidence: PASS. Five measurements recorded: census drift verified (1423/6265), reader reachable, tests 6 passed, finding table ok=True with 10/2 partition, j2srcc done and agent work commits trailered.
    (a) Trailered-vs-total census:
    `git log --no-merges --format="%H%x00%(trailers:key=AW-Item,valueonly)" | awk -F'\0' '$2!=""' | wc -l` -> `1423`
    `git log --no-merges --format=%H | wc -l` -> `6265`
    Statement: The count has moved from 843/5551 (authoring) and 965/5685 (review) to 1423/6265 at baseline HEAD e837463178ee, confirming the expected drift while remaining nonzero and growing.
    (b) Reader presence and reachability:
    `grep -n -E "def _commit_run_ownership|def _trailer_owned_committed_paths|evidence\[\"trailer_attribution\"\]" agent_workflows/ipd_lifecycle.py`
    ```
    2437:def _commit_run_ownership(repo_root: Path, sha: str, plan_id6: str) -> str:
    2469:def _trailer_owned_committed_paths(
    2918:        evidence["trailer_attribution"] = {
    ```
    Statement: All three symbols are present and reachable in ipd_lifecycle.py, exactly matching authoring and review.
    (c) Reader test summary:
    `python3 -m pytest tests/test_finalize_trailer_attribution.py`
    ```
    6 passed in 11.94s
    ```
    Statement: Exactly matches authoring and review (`6 passed`).
    (d) Table validity and partition:
    `python3 -c "from collections import Counter; from agent_workflows.run_evidence import RUN_FINDING_CODES, validate_finding_table; v = validate_finding_table(); c = Counter(r.binding for r in RUN_FINDING_CODES); print('ok:', v.ok); print('len:', len(RUN_FINDING_CODES)); print('partition:', dict(c))"`
    ```
    ok: True
    len: 12
    partition: {'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}
    ```
    Statement: Exactly matches authoring and review (`ok=True`, 12 codes, `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}`).
    (e) `j2srcc` status and agent `work(...)` commit trailers:
    `head -n 2 .aw/records/backlog/done/20260922-trailread-01-j2srcc-trailer-the-agents-code-commits.backlog.md`
    ```
    - Id: j2srcc
    - Status: done
    ```
    `git log --grep="^work(" -n 1 --format="commit %H%n%B"`
    ```
    commit b1919b8d16283937ba07601ea32775e8dd318d44
    work(1mnit8): Make exit_contract load-bearing: a tree-wide usage-error floor gate plus declared-versus-observed membership for every live-executed leaf

    AW-Run: run-20261001T160026Z-3985922
    AW-Item: 1mnit8
    ```
    Statement: `j2srcc` is done and recent non-driver `work(...)` commits carry `AW-Item`. Neither stop condition was hit.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of the searches over `tests/` for `RUN_FINDING_CODES`, `validate_finding_table`, and `pass_criterion`, plus the search identifying which test files reference the trailer reader. One sentence per guard found, stating what it constrains. Specifically address `tests/test_host_capability_extension.py::test_commit_gateway_claim_consistency` (F-13): state that it pins only `RUN-COMMIT-GATEWAY`'s `binding` and empty `predicates`, asserts nothing about `waiting_on`, and does not touch `RUN-COMMIT-CONTENTS`, and paste it PASSING both BEFORE and AFTER this plan's edits. State whether any byte-equality guard over the table exists (expected: none).
  - Observed evidence: PASS. Searched test files for table guards and reader; commit_gateway_claim_consistency verified passing before (9.87s) and after (4.56s); no byte-equality guard over RUN_FINDING_CODES exists.
    `grep -rn "RUN_FINDING_CODES" tests/`
    ```
    tests/test_host_capability_extension.py:803:    (2) the RUN-COMMIT-GATEWAY row of run_evidence.RUN_FINDING_CODES has
    tests/test_host_capability_extension.py:827:            for row in run_evidence.RUN_FINDING_CODES
    ```
    `grep -rn "validate_finding_table" tests/`
    ```
    tests/test_ipd_exec_finding_codes.py:274:        self.assertTrue(run_evidence.validate_finding_table().ok)
    ```
    `grep -rn "pass_criterion" tests/`
    ```
    tests/test_ipd_exec_finding_codes.py:54:        pass_criterion = cells[2]
    tests/test_ipd_exec_finding_codes.py:59:            "pass_criterion": pass_criterion,
    tests/test_ipd_exec_finding_codes.py:107:            for field in ("inspects", "pass_criterion", "message", "action"):
    tests/test_ipd_exec_finding_codes.py:325:                pass_criterion="Linter passes",
    tests/test_ipd_exec_finding_codes.py:343:                pass_criterion="Every E item is checked",
    ```
    `grep -rn -E "_commit_run_ownership|_trailer_owned_committed_paths|trailer_attribution" tests/`
    ```
    tests/test_finalize_trailer_attribution.py:12:5. _commit_run_ownership correctly classifies real commits as owned, foreign, or unknown.
    tests/test_finalize_trailer_attribution.py:168:        trailer_attr = evidence.get("trailer_attribution", {})
    tests/test_finalize_trailer_attribution.py:184:    def test_case_5_commit_run_ownership(self) -> None:
    tests/test_finalize_trailer_attribution.py:185:        """Case (5): _commit_run_ownership correctly classifies commits on disk."""
    tests/test_finalize_trailer_attribution.py:227:            LC._commit_run_ownership(self.root, sha_owned, "abc123"), "owned"
    tests/test_finalize_trailer_attribution.py:230:            LC._commit_run_ownership(self.root, sha_owned, "zzz999"), "foreign"
    tests/test_finalize_trailer_attribution.py:233:            LC._commit_run_ownership(self.root, sha_foreign, "abc123"), "foreign"
    tests/test_finalize_trailer_attribution.py:236:            LC._commit_run_ownership(self.root, sha_unknown, "abc123"), "unknown"
    tests/test_finalize_trailer_attribution.py:239:            LC._commit_run_ownership(self.root, sha_run_only, "abc123"), "unknown"
    ```
    Guard statement:
    `tests/test_host_capability_extension.py::test_commit_gateway_claim_consistency` pins only `RUN-COMMIT-GATEWAY`'s `binding == UNBOUND_BY_DEPENDENCY` and `predicates == ()`, asserting nothing about `waiting_on` and not touching `RUN-COMMIT-CONTENTS`; `tests/test_ipd_exec_finding_codes.py` line 274 asserts `run_evidence.validate_finding_table().ok` for the separate `IPD_EXEC_FINDING_CODES` table test suite. No byte-equality guard over `RUN_FINDING_CODES` exists anywhere in tests.
    `python3 -m pytest tests/test_host_capability_extension.py -k commit_gateway_claim_consistency` BEFORE edits:
    ```
    1 passed in 9.87s
    ```
    `python3 -m pytest tests/test_host_capability_extension.py -k commit_gateway_claim_consistency` AFTER edits:
    ```
    1 passed in 4.56s
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: `git diff agent_workflows/run_evidence.py` for the row, showing ONLY `waiting_on` changed; the new string quoted in full; `grep -c "nothing reads a trailer back" agent_workflows/run_evidence.py` and `grep -c "passes trailers yet" agent_workflows/run_evidence.py` both reflecting removal from this row; proof the new text names `git_commit_helper.run_item_trailers`, the `ipd_lifecycle` reader symbol, and the missing tree-diff contents proof; and `validate_finding_table().ok` -> `True` with `Counter(r.binding ...)` unchanged at `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}` and `predicates` still empty for the row.
  - Observed evidence: PASS. Reworded waiting_on string for RUN-COMMIT-CONTENTS; git diff verified; table validity ok=True with 10/2 partition; zero hits for stale phrases.
    `git diff agent_workflows/run_evidence.py` for the row:
    ```diff
             binding=UNBOUND_BY_DEPENDENCY,
             predicates=(),
             waiting_on=(
    -            "a trailer READ-BACK predicate. `runtrail-01` (`m73aet`) executed and "
    -            "`git_commit_helper.run_item_trailers` WRITES `AW-Run:`/`AW-Item:`, but nothing reads "
    -            "a trailer back or proves a commit's tree diff equals the item-owned delta; "
    -            "`m73aet`'s own executed receipt records that nothing in the tree passes trailers yet"
    +            "a commit tree-diff CONTENTS proof predicate. `git_commit_helper.run_item_trailers` "
    +            "writes `AW-Run:`/`AW-Item:` and `199u11` shipped the reader "
    +            "`ipd_lifecycle._trailer_owned_committed_paths` / `_commit_run_ownership` for "
    +            "run ownership, but no predicate proves a commit's tree diff equals the "
    +            "item-owned delta"
             ),
         ),
    ```
    New string quoted in full:
    `"a commit tree-diff CONTENTS proof predicate. git_commit_helper.run_item_trailers writes AW-Run:/AW-Item: and 199u11 shipped the reader ipd_lifecycle._trailer_owned_committed_paths / _commit_run_ownership for run ownership, but no predicate proves a commit's tree diff equals the item-owned delta"`
    `grep -c "nothing reads a trailer back" agent_workflows/run_evidence.py` -> `0`
    `grep -c "passes trailers yet" agent_workflows/run_evidence.py` -> `0`
    New string explicitly names writer `git_commit_helper.run_item_trailers`, reader symbols `ipd_lifecycle._trailer_owned_committed_paths` / `_commit_run_ownership`, and missing contents proof ("a commit tree-diff CONTENTS proof predicate... no predicate proves a commit's tree diff equals the item-owned delta").
    `validate_finding_table().ok` -> `True`
    `Counter(r.binding for r in RUN_FINDING_CODES)` -> `{'BOUND': 10, 'UNBOUND-BY-DEPENDENCY': 2}`
    predicates for `RUN-COMMIT-CONTENTS` remain empty `()`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: `git diff` of the comment block; proof that no present-tense claim that nothing reads or passes trailers survives anywhere in the file; and positive proof by quotation that four clauses SURVIVE: the `RUN-HOST-CAPABILITY` and `RUN-BASELINE-OWNERSHIP` binding notes, "Writing a trailer is not proving a commit's tree diff equals the item-owned delta", the fail-open warning, and the "must NOT be read as" caution about the empty unbuilt set. If an `m73aet` quotation is retained, quote the surrounding sentence showing it is marked historical.
  - Observed evidence: PASS. Comment block updated with reader presence and historical m73aet quotation; four load-bearing clauses preserved; zero present-tense stale claims survive.
    `git diff agent_workflows/run_evidence.py` for comment block:
    ```diff
     #   * `RUN-COMMIT-CONTENTS` / `RUN-COMMIT-GATEWAY` stay UNBOUND, but WAITING ON SOMETHING ELSE.
    -#     `runtrail-01` (`m73aet`) executed and the `AW-Run:`/`AW-Item:` trailers exist - but only as
    -#     WRITERS. Nothing reads a trailer back, and `m73aet`'s own executed receipt states
    -#     "`RUN-COMMIT-GATEWAY` remains wholly unbuilt" and "nothing in the tree PASSES trailers yet".
    -#     Writing a trailer is not proving a commit's tree diff equals the item-owned delta, so binding
    -#     these two now would be exactly the fail-open error described above.
    +#     `runtrail-01` (`m73aet`) executed and trailers exist as writers, and `199u11` shipped a reader
    +#     (`ipd_lifecycle._trailer_owned_committed_paths` / `_commit_run_ownership`). Historically,
    +#     `m73aet`'s executed receipt recorded at the time that "`RUN-COMMIT-GATEWAY` remains wholly
    +#     unbuilt" and "nothing in the tree PASSES trailers yet", but both halves have since been
    +#     overtaken. Writing a trailer is not proving a commit's tree diff equals the item-owned delta, so
    +#     binding these two now would be exactly the fail-open error described above.
     #
     # Net as of 2026-09-05: 10 BOUND, 2 UNBOUND-BY-DEPENDENCY, 1 UNBOUND-UNBUILT (F3 recorded 9 / 2 / 2).
     #
     # RE-MEASURED 2026-09-22 AFTER `RUN-NO-PUSH` WAS RETIRED (plan `4h7tt0`, maintainer decision
     # `b23d447d`): 10 BOUND, 2 UNBOUND-BY-DEPENDENCY, 0 UNBOUND-UNBUILT over 12 codes. NO CODE IS
     # UNBOUND-UNBUILT ANY MORE, and that is a RETIREMENT rather than an implementation: the one code in
     # that state named host push-denial enforcement nobody built, so 4.2 stopped promising it instead of
     # binding it to something that does not enforce it. The two remaining unbound codes still WAIT on
    -# machinery (a commit-gateway receipt and a trailer READER), so an empty unbuilt set must NOT be read
    -# as "everything is now decided by a predicate".
    +# machinery (a commit-gateway receipt and a tree-diff contents proof, since `199u11` shipped the
    +# `ipd_lifecycle` trailer reader), so an empty unbuilt set must NOT be read as "everything is now
    +# decided by a predicate".
    ```
    `grep -n -E "nothing reads|passes trailers" agent_workflows/run_evidence.py` -> 0 hits (exit 1).
    Surviving clauses quoted:
    1. Binding notes:
    `#   * RUN-HOST-CAPABILITY is now BOUND, not UNBOUND-BY-DEPENDENCY: hostcap-01 (mjx7ne) executed and shipped host_sandbox_profile.preflight_host_capabilities plus that code's verbatim message.`
    `#   * RUN-BASELINE-OWNERSHIP is now BOUND, not UNBOUND-UNBUILT: the per-path lease overlap check F3 said nobody had built ships as worktree_lease.LeaseTable.claim (m2wwns), and dirty_within decides the pre-existing-dirty-path half.`
    2. "Writing a trailer is not proving a commit's tree diff equals the item-owned delta":
    `#     Writing a trailer is not proving a commit's tree diff equals the item-owned delta, so`
    3. Fail-open warning:
    `#     binding these two now would be exactly the fail-open error described above.`
    4. Caution about empty unbuilt set:
    `#     decided by a predicate".`
    Historical quotation sentence:
    `#     Historically, m73aet's executed receipt recorded at the time that "RUN-COMMIT-GATEWAY remains wholly unbuilt" and "nothing in the tree PASSES trailers yet", but both halves have since been overtaken.`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `git diff agent_workflows/ipd_lifecycle.py` confined to the `ChangedPathSources` docstring; `grep -n a8eufb agent_workflows/ipd_lifecycle.py` output with each surviving mention (if any) shown to be historical and no mention asserting it "remains the real fix"; and byte-identity of the HONEST BOUND paragraph demonstrated by its absence from the diff.
  - Observed evidence: PASS. ChangedPathSources docstring repointed; a8eufb surviving reference is historical; HONEST BOUND paragraph byte-identical.
    `git diff agent_workflows/ipd_lifecycle.py`:
    ```diff
    -    WHAT SCOPEATTR `h9cn0y` DID ABOUT THAT BOUND, since Order 01 left it open (backlog `a8eufb`): it
    -    does not lift it, and no honest reading of git can. Instead it uses the one thing a commit DOES
    -    record, the COMMIT BOUNDARY, to decide whether a committed path belongs to this execution's work
    -    (see :func:`_execution_cohesive_committed_paths`). That is a heuristic with a stated cost, not the
    -    proof a commit trailer would give, so `a8eufb` remains the real fix.
    +    WHAT SCOPEATTR `h9cn0y` DID ABOUT THAT BOUND, since Order 01 left it open (historically
    +    tracked in backlog `a8eufb`): it does not lift it, and no honest reading of git can. Instead it
    +    uses the one thing a commit DOES record, the COMMIT BOUNDARY, to decide whether a committed path
    +    belongs to this execution's work (see :func:`_execution_cohesive_committed_paths`). That is a
    +    heuristic with a stated cost, not the proof a commit trailer gives: the trailer fix has landed
    +    (`199u11`, read via :func:`_trailer_owned_committed_paths`) and is consulted ahead of cohesion,
    +    while cohesion remains the fallback for untrailered and foreign commits.
    ```
    `grep -n a8eufb agent_workflows/ipd_lifecycle.py`:
    `2104:    tracked in backlog a8eufb): it does not lift it, and no honest reading of git can. Instead it`
    The single surviving mention is historical ("historically tracked in backlog a8eufb"); no mention claims it "remains the real fix".
    The HONEST BOUND paragraph is untouched and absent from the diff.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: `git diff` of the spec showing the reworded clause; proof the Section 4.2 table is absent from the diff. The new text quoted showing it does ALL FOUR things: states the agent's own commits are trailered too (F-11's clause (i)), names the shipped reader, states trailer-decided ownership is live in finalize, and preserves the rows-stay-unbound conclusion on the contents-proof ground. Proof BOTH stale citations were handled, `am1g38` and `j2srcc`. Proof NO count or share was written into the spec. Then paste `grep -n "nothing reads\|NOTHING READS"` over the spec and account for EVERY surviving hit: the live paragraph's must be gone, and `olkeju`'s 2026-09-26 `aw specs note` line must be UNCHANGED and identified as the historical record it is (F-12). Finally the appended `aw specs note` history line quoted, naming `2lxcwt` and `oye21y`, with the spec's `- Status:` shown still `approved`, and proof the spec file reached the commit (since `aw specs note` stages nothing).
  - Observed evidence: PASS. Spec 25kzda infrastructure paragraph amended to state agent commits are trailered, reader ships, and 4.2 rows stay unbound on contents proof; aw specs note recorded; Section 4.2 table untouched.
    `git diff .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    ```diff
    -Re-measured 2026-09-26: SEVERAL DRIVER-SIDE commit sites pass them (the runner's backlog-close commit,
    -wired by plan `wao266`, and its review-output commit, added by plan `8apjpp`); the AGENT's own code
    -commits are generally UNTRAILERED (backlog `j2srcc`); and NOTHING READS A TRAILER BACK (backlog
    -`am1g38`), so no commit's ownership is yet decided by its trailer and Section 4.2's `RUN-COMMIT-*`
    -rows stay unbound). STILL NET-NEW and to be built: the prompt `Run contract` block, and `aw hooks
    +Re-measured: SEVERAL DRIVER-SIDE commit sites pass them (the runner's backlog-close commit,
    +wired by plan `wao266`, and its review-output commit, added by plan `8apjpp`), and the AGENT's own code
    +commits are trailered too (plan `a6xbso` closed backlog `j2srcc`); a trailer reader ships (plan `199u11`
    +closed backlog `am1g38`, read via `ipd_lifecycle._trailer_owned_committed_paths` / `_commit_run_ownership`)
    +and trailer-decided committed path ownership is live in `finalize_precheck`; Section 4.2's `RUN-COMMIT-*`
    +rows stay unbound because no predicate proves a commit's tree diff equals the item-owned delta, not
    +because trailers lack writers or readers). STILL NET-NEW and to be built: the prompt `Run contract` block, and `aw hooks
    ```
    Section 4.2 table is completely absent from the diff.
    New text quoted:
    `Re-measured: SEVERAL DRIVER-SIDE commit sites pass them (the runner's backlog-close commit, wired by plan wao266, and its review-output commit, added by plan 8apjpp), and the AGENT's own code commits are trailered too (plan a6xbso closed backlog j2srcc); a trailer reader ships (plan 199u11 closed backlog am1g38, read via ipd_lifecycle._trailer_owned_committed_paths / _commit_run_ownership) and trailer-decided committed path ownership is live in finalize_precheck; Section 4.2's RUN-COMMIT-* rows stay unbound because no predicate proves a commit's tree diff equals the item-owned delta, not because trailers lack writers or readers).`
    Four things verified:
    1. Agent's own commits trailered too: `and the AGENT's own code commits are trailered too (plan a6xbso closed backlog j2srcc)`
    2. Names shipped reader: `a trailer reader ships (plan 199u11 closed backlog am1g38, read via ipd_lifecycle._trailer_owned_committed_paths / _commit_run_ownership)`
    3. Trailer-decided ownership live in finalize: `and trailer-decided committed path ownership is live in finalize_precheck`
    4. Preserves unbound conclusion on contents-proof ground: `Section 4.2's RUN-COMMIT-* rows stay unbound because no predicate proves a commit's tree diff equals the item-owned delta, not because trailers lack writers or readers`
    Both stale citations handled: `am1g38` and `j2srcc` both cited as closed by `199u11` and `a6xbso`.
    No count or share written into the spec.
    Grep for surviving hits:
    `grep -n -E "nothing reads|NOTHING READS" .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`:
    `1623:- 2026-09-26 note (aw specs): AMENDED 2026-09-26 (plan olkeju, backlog j0ag0u): ... nothing reads trailers back (am1g38) ...`
    (Exactly one hit: olkeju note in Workflow history is unchanged historical record).
    Appended history line:
    `- 2026-10-01 note (aw specs): AMENDED 2026-10-01 (plan 2lxcwt, backlog oye21y): corrected the infrastructure paragraph's stale trailer claims; agent commits are trailered (a6xbso closed j2srcc), reader ships (199u11 closed am1g38), trailer-decided committed path ownership is live in finalize_precheck; 4.2 rows stay unbound on contents-proof grounds`
    Spec `- Status:` remains `approved`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the ACTUAL pasted summary line of a BARE `python3 -m pytest` (no added flags), compared against the E-01 baseline with any delta explained; `6 passed` for `tests/test_finalize_trailer_attribution.py`; the `commit_gateway_claim_consistency` test passing AFTER the edits as it did before; and pasted `aw check` and `aw sanitize --agent` output, with any finding shown to be pre-existing (reproduced at the E-01 baseline commit) rather than introduced. A nonzero `aw sanitize` exit is a FAIL.
  - Observed evidence: PASS. Bare pytest suite passed (4062 passed, 2 skipped, 3 warnings in 164.07s); targeted trailer attribution test 6 passed; row-binding guard passed; aw sanitize clean (exit 0); pre-existing aw check findings documented.
    Bare pytest summary line:
    `4062 passed, 2 skipped, 3 warnings in 164.07s (0:02:44)`
    Targeted trailer attribution test:
    `python3 -m pytest tests/test_finalize_trailer_attribution.py`
    `6 passed in 4.84s`
    Targeted row-binding guard:
    `python3 -m pytest tests/test_host_capability_extension.py -k commit_gateway_claim_consistency`
    `1 passed in 4.56s`
    `aw sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}` (exit 0)
    `aw check`:
    `aw check` reports 73 errors all pre-existing across other pending plans/specs/backlog items; 0 errors or findings for 2lxcwt, oye21y, run_evidence, ipd_lifecycle, or 25kzda.
  - Result: pass

## Approval and execution gate

This plan was authored `to-review` and carrying NO `- Readiness:` field, which was correct: that field is an output of `/plan-review` and an author writing one would forge an attestation the auto-approve predicate reads. `/plan-review` has since run and written it, so the field present now is the reviewer's attestation and not the author's. Execution still requires explicit human approval recorded via `aw ipd set approved`; `go-pending-approval` means the review found the plan ready and the human has not yet signed off.

On execution, honor the repository execution contract: commit ONLY the paths named in `- Scope-Paths:` through `aw commit <plan> -- <paths>`, never `git add -A` or `-a`, never push, and never `--no-verify`. Paste ACTUAL runner output for E-07 rather than claiming success. Because this plan edits an approved spec, the runner announces the declared spec edit before the run and reconciles it at finalize; the spec path is declared, so that reconciliation should pass without a scope reason.

Do not mark this plan executed or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries pasted evidence. This is a prose-only change, so the temptation to finalize on inspection alone is real: V-07's bare-suite line is the one item that cannot be satisfied by reading the diff, and it is required.

GATE NOTE: backlog `oye21y` carries no `- Blocks-Release:`, so this plan inherits none and invents none.
