# IPD: Document the two match_selector narrowing sites as independent guards and pin each one from the production call shape

- Date: 2026-09-29
- Kind: child
- Concern: `status_set.match_selector` narrows by type in TWO places and a reader cannot tell from the call site whether either is load-bearing, so a test author writes a pin that passes vacuously. Backlog item `ihgjii` diagnosed the two sites as REDUNDANT belt-and-braces covering the same guarantee. MEASURED IN THIS LANE AT HEAD `54190d61`, THAT DIAGNOSIS IS WRONG, and the correction inverts the item's suggested fix: the two sites cover DISJOINT selector kinds. The FAST-PATH filter (`cands = [r for r in all_records if not target_type or r.record_type == target_type]`) is the ONLY type guard for the `id6` and `setid` kinds, which return early and never reach the resolver. The RESOLVER narrowing (`if scoped_type: record_types = (canonical,)`) is the ONLY type guard for the `status`, `stem` and `substring` kinds, which the fast path cannot see. Neither is redundant and removing either is a live cross-type defect. The item's stated remedy ("drop the redundant fast-path filter and let `scoped_type` be the single narrowing authority") would therefore SHIP A BUG: measured, with that filter removed `match_selector('<a backlog id6>', <full inventory>, root, scoped_type='plans')` returns a BACKLOG record under a plans-scoped call. Separately measured and worse than the item knew: the RESOLVER site is entirely UNPINNED. With `if scoped_type:` mutated to `if False:` the ENTIRE suite passes (3246 passed, 2 skipped), so three selector kinds have no regression test at all.
- Scope: Correct the record for `status_set.match_selector`'s two type-narrowing sites and pin the unpinned half. Write a docstring and two code comments stating WHICH selector kinds each site guards and that neither is redundant, replacing the current docstring's single-authority framing. Add tests pinning the resolver-narrowing site for the `status`, `stem` and `substring` kinds and the fast-path site for the `id6` kind plus a `setid` companion assertion (the pair is what isolates the fast path, since an `id6` test alone fails under both mutations; see F-9), each passing an UNNARROWED record list so `scoped_type` is the only filter, and each demonstrated by mutation to FAIL when its site is removed. Amend spec `2lcqno` N3, whose "ONE DOCUMENTED HOLE" paragraph names only the direct-PATH exemption and reads as though a single narrowing mechanism covers everything else. Changes NO runtime behavior: no filter is removed, no precedence changes, no public signature changes.
- Scope-Paths: agent_workflows/status_set.py, tests/test_status_set.py, .aw/records/specs/approved/20260910-2lcqno-01-2lcqno-setid-shared-topic-label-and-type-scoped-resolution.spec.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: ihgjii
- Set: selnarrow
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: jw6cm3
- Approval: 2026-09-30, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-30 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-501 (HIGH, fixed), PR-502 (MEDIUM, fixed), PR-503 (MEDIUM, fixed), PR-504 (MEDIUM, fixed), PR-505 (LOW, fixed), PR-506 (LOW, fixed). Findings recorded in `.aw/records/reviews/20260930-selnarrow-01-jw6cm3-document-the-two-match-selector-narrowing-sites-as-independe.review.md`. THIS PLAN'S CENTRAL CORRECTION OF ITS OWN BACKLOG ITEM IS RIGHT AND I RE-DERIVED EVERY LOAD-BEARING MEASUREMENT RATHER THAN READING IT. Mutating each site separately reproduces fact 1's disjointness exactly (`killFAST` breaks `setid`/`id6` only; `killRESOLVER` breaks `status`/`substring`/`stem` only). Fact 3 reproduces and is the plan's most important claim: with the resolver branch disabled the ENTIRE bare suite passes (`3346 passed, 2 skipped`), so three selector kinds have no regression test. Fact 2 reproduces verbatim through the real verb, including the exact message degradation from `No plans artifact matched 'pz34kx'` to `Selector 'pz34kx' did not resolve to a plan`. Fact 4 reproduces (`killFAST` fails exactly one test in the whole suite, `test_scoped_setid_resolution_returns_only_the_scoped_type`). Facts 5 and 6 reproduce in SHAPE. Review found one measured error and three gaps, none of which changes the deliverable. THE ERROR: E-04's `id6` pin was specified as a FAST-PATH pin, and prototyping it measured that it fails under BOTH mutations, so it cannot distinguish the two sites and V-04 as written would have been satisfied by a test that does not isolate what it claims to. The plan's own Goal fact 1 already said `id6` "breaks under BOTH" and E-04 contradicted it; E-04 and V-04 now require BOTH mutations shown and a companion `setid` assertion, which is what actually isolates the fast path. THE GAPS: fact 5's performance numbers have drifted by a factor of five (134ms measured at authoring, 680ms at review on a 2009-record corpus) so a re-derivation instruction was needed; the plan never measured `killFAST` against the FULL suite (it is 1 failure, which is the number that makes F-4's "already pinned" claim precise); and E-06 amends an APPROVED spec without saying so or naming the attestation path. I also prototyped all four tests to establish the deliverable is achievable before signing off: all four pass at HEAD and all four fail under the site each pins, and doing so surfaced a fixture constraint (`create_backlog` writes into a status-named directory, so a plans+backlog shared status token must be one both trees have, e.g. `open`, not `reviewed`) that would otherwise have cost the executor a debugging cycle. That constraint is now recorded in E-02.

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog item `ihgjii`, graduating it. EVERY claim below was measured in this lane at HEAD `54190d61` by mutating each narrowing site INDEPENDENTLY, which is the step the backlog item did not take: it mutated BOTH sites together, observed one combined effect, and concluded redundancy. Mutating them separately falsifies that. THREE FINDINGS CHANGE THE SHAPE OF THE WORK. FIRST, the two sites are NOT redundant: they cover disjoint selector kinds, the fast path owning `id6`/`setid` (which return early) and the resolver owning `status`/`stem`/`substring` (which the fast path never sees). SECOND, the item's suggested remedy is a DEFECT: dropping the fast-path filter makes a plans-scoped `id6` query return a backlog record, measured end-to-end through `aw ipd dependencies set`, where the refusal message degrades from `No plans artifact matched` to a wrong-type diagnostic. THIRD, the item believed the real coverage gap was already closed by plan `w2y5ac`'s E-01 test; measured, that test pins the FAST-PATH site only (killFAST fails it) and the RESOLVER site survives the FULL suite unmutated-detected, so the gap is larger than the item recorded and its scope is inverted. The plan's deliverable is therefore a pin plus a corrected record, NOT the refactor the item suggested.

## Goal

Make `match_selector`'s type safety legible and tested, so the next author can see from the call site which
guarantee each narrowing site provides and cannot write a pin that passes vacuously.

The backlog item asked for one of two things: a docstring stating the filters are defensive, or the removal
of the redundant one. MEASUREMENT REFUSES BOTH, because the premise both rest on (that the two sites cover
the same guarantee) is false. What is actually needed is the opposite: a record saying the two sites are
INDEPENDENT and NON-REMOVABLE, plus the missing test for the half nothing pins.

SIX FACTS ESTABLISHED AT AUTHORING, so the executor inherits measurement rather than the item's diagnosis.

1. THE TWO SITES COVER DISJOINT SELECTOR KINDS. `selectors.resolve`'s precedence is `path` -> `id6` ->
   `setid` -> `status` -> `stem` -> `substring` (stated in its own docstring). `match_selector`'s fast path
   returns EARLY for `id6` and `setid`, so those two kinds never reach the resolver and the resolver's
   narrowing cannot possibly guard them. Conversely the fast path only ever compares `r.id6` and
   `r.set_id`, so it cannot guard `status`, `stem` or `substring`. Measured, mutating each site alone,
   passing the FULL unnarrowed inventory with `scoped_type="plans"`:

   ```text
   token kind        HEAD                          killFAST                      killRESOLVER
   setid   runrecon  ['plans'] n=2                 ['backlog','plans'] n=4       ['plans'] n=2
   id6     5m43v9    [] n=0                        ['backlog'] n=1               ['backlog'] n=1
   status  approved  ['plans'] n=5                 ['plans'] n=5                 ['backlog','plans','specs'] n=22
   status  reviewed  ['plans'] n=26                ['plans'] n=26                ['backlog','plans','prompts','specs'] n=30
   substr  20260921  ['plans'] n=5                 ['plans'] n=5                 ['backlog','plans'] n=52
   stem    <backlog> [] n=0                        [] n=0                        ['backlog'] n=1
   ```

   Read the columns: `killFAST` breaks `setid` and `id6` and nothing else; `killRESOLVER` breaks `status`,
   `substring` and `stem` and nothing else. (`id6` breaks under BOTH because the fast path's early return is
   what stops the resolver being consulted at all, so removing either exposes it.)

2. THE ITEM'S SUGGESTED FIX IS A CROSS-TYPE DEFECT, NOT A SIMPLIFICATION. The item proposes dropping the
   fast-path filter "and let `scoped_type` be the single narrowing authority". Measured end-to-end through
   a real caller with that filter removed:

   ```text
   $ aw ipd dependencies set 5m43v9 none --dry-run --yes     # 5m43v9 is a BACKLOG id6
   HEAD      rc=2  FAIL  No plans artifact matched '5m43v9'.
   killFAST  rc=2  FAIL  Selector '5m43v9' did not resolve to a plan; `aw ipd dependencies set` only applies to IPDs.
   ```

   Both refuse, so no write escapes, but the refusal DEGRADES: the correct answer "no plans matched" becomes
   a wrong-type report about a record a plans-scoped resolver should never have surfaced. The reason no
   corruption follows is a SECOND, independent guard (`run_dependencies_set_command`'s
   `plan_matches = [m for m in matches if m.record_type == "plans"]`), so the item's fix would convert a
   resolver-level guarantee into a reliance on every caller's own post-filter. That is the opposite of the
   single-authority property it was reaching for.

3. THE RESOLVER-NARROWING SITE IS COMPLETELY UNPINNED. Mutating `if scoped_type:` to `if False:` and running
   the full suite bare:

   ```text
   3246 passed, 2 skipped, 3 warnings in 51.35s
   ```

   Nothing fails. So the guarantee spec `2lcqno` N3 makes normative for `status`/`stem`/`substring` selectors
   has no test. This is the plan's central deliverable and it is a BIGGER gap than the backlog item
   described, which believed the remaining hole was documentation.

4. THE FAST-PATH SITE IS ALREADY PINNED BY EXACTLY ONE TEST, AND THE ITEM MISREAD WHICH SITE ITS OWN PIN
   COVERS. With `cands = list(all_records)`, on the module and then, added at review because it is the
   number that makes this claim precise, on the FULL suite:

   ```text
   FAILED tests/test_status_set.py::SharedSetidCrossTypeResolutionTests::test_scoped_setid_resolution_returns_only_the_scoped_type
   1 failed, 81 passed in 4.17s                       # module (78 at authoring; the module has grown)
   1 failed, 3345 passed, 2 skipped in 70.04s         # FULL suite, measured at review
   ```

   `w2y5ac`'s E-01 test therefore pins the FAST PATH, not the resolver. THE FULL-SUITE NUMBER IS THE POINT
   OF THE SECOND LINE: exactly ONE test in the entire repository catches the fast-path mutation, so the
   coverage either side of `match_selector` is one test and zero tests respectively, not "some" and "none".
   The test's in-code comment says `scoped_type` must be "the ONLY thing doing the filtering here", which is
   true of the call but does not distinguish the two sites, and the item inherited that conflation. This
   plan must not weaken that test; it adds the complementary kinds beside it.

5. THE PERFORMANCE PREMISE THE ITEM CITED IS REAL AND MUCH LARGER THAN IT IMPLIED. The item says the fast
   path "exists for performance (commit `4cfa2283`)" and treats that as the only reason to keep it.

   THE RATIO IS THE DURABLE FACT; THE MILLISECONDS ARE A LIVE POPULATION AND HAVE ALREADY DRIFTED. Measured
   at authoring on a 1903-record corpus, then RE-MEASURED AT REVIEW on a 2009-record corpus, four days
   later:

   ```text
                                                authoring (1903)   review (2009)
   HEAD setid (fast path HIT):                      0.08 ms           0.28 ms
   HEAD status (fast path MISS -> resolver):      134.52 ms         680.42 ms
   HEAD substring (fast path MISS -> resolver):   133.60 ms         495.47 ms
   filter comprehension over the whole corpus:     0.053 ms          0.0866 ms
   ```

   The absolute resolver cost moved by roughly a factor of five for a 6 percent corpus growth, so NO
   MILLISECOND FIGURE HERE IS A BAR and none may be quoted as one. What is stable across both measurements
   is the RATIO and its sign: the fast path avoids a resolver walk three to four ORDERS OF MAGNITUDE more
   expensive than the filter it carries (roughly 2500x at authoring, roughly 7800x at review). So the
   filter is not a cost worth reclaiming even if it were redundant. It is not redundant (fact 1), which
   settles it twice. An executor who re-measures MUST expect different numbers and must not treat a
   mismatch with this table as a finding.

6. THE PRODUCTION CALL SHAPE DOES HIDE BOTH SITES, WHICH IS THE ONE THING THE ITEM GOT EXACTLY RIGHT. Every
   caller in `run_set_command` passes `inventory_all_artifacts(repo_root, scoped_type=scoped_type_canonical)`,
   already narrowed. Measured with that pre-narrowed list and `scoped_type="plans"`, `killFAST` is INVISIBLE
   for every kind (`setid` still `['plans']` n=2, `id6` still `[]`), because the caller already removed the
   foreign records the filter would have removed. `killRESOLVER` stays visible even pre-narrowed, because the
   resolver reads the FILESYSTEM rather than the supplied list. So a test must pass an UNNARROWED list to
   observe the fast path, and that requirement is specific to the fast path, not a general rule about this
   function. TWO CALLERS DO PASS AN UNNARROWED LIST TODAY (`run_dependencies_set_command` and
   `run_dependencies_remove_command`, both calling `inventory_all_artifacts(repo_root)` with no
   `scoped_type` and then `match_selector(..., scoped_type="plans")`), which is how fact 2 was measurable
   end-to-end; the item's claim that "every caller" pre-narrows is true of `run_set_command` only.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure before writing anything

- [ ] E-01 RE-DERIVE THE PER-SITE, PER-KIND MUTATION MATRIX in this lane before editing any file, reproducing the table in Goal fact 1 against the tree as it then stands, and RECORD THE RESULT EVEN IF IT DIFFERS from this plan's numbers. EXPECT THE `n=` COUNTS AND TOKENS TO DIFFER and do not treat that as a finding: review re-derived this matrix on a 2009-record corpus and every `n=` moved (for example `status approved` went `n=5` to `n=9` scoped and `n=22` to `n=26` under `killRESOLVER`) while the TYPE SETS, which are the actual claim, were identical in all eighteen cells. The durable assertion is the SHAPE, namely that `killFAST` changes the type set for `setid`/`id6` only and `killRESOLVER` for `status`/`substring`/`stem` only; assert on type sets, report the counts as context. MUTATE IN MEMORY IF YOU PREFER: review did this by building a monkeypatched copy of the function in a throwaway script rather than editing the file, which makes the "restore the file" step unnecessary for the matrix half and removes the risk of committing a mutation; the file edit is still required for the two SUITE runs below, which must exercise the real module. Mutate each site SEPARATELY (fast-path filter to `cands = list(all_records)`; resolver branch to `if False:`), never both at once, because mutating both together is exactly the measurement error that produced the backlog item's wrong diagnosis. Cover all six kind/token rows including the `id6` row that breaks under both. Also capture the full-suite result under the resolver mutation (Goal fact 3) as the baseline proving the gap is still open, and the `tests/test_status_set.py` result under the fast-path mutation (fact 4) proving the existing pin still covers that half. RESTORE THE FILE and prove it byte-identical (`git status --short` clean for `agent_workflows/status_set.py`) before proceeding; a mutation left in the tree would be committed.
  - Depends on: none
  - Expected outcome: the pasted per-site matrix, the pasted suite summary line under the resolver mutation, the pasted module summary under the fast-path mutation, and a pasted clean `git status` proving both mutations were reverted.
  - Execution state: pending

### Task group 2: pin the unpinned half

- [ ] E-02 PIN THE RESOLVER-NARROWING SITE FOR THE `status` KIND with a test that passes the FULL UNNARROWED inventory and `scoped_type` as the only filter, asserting the returned records are all of the scoped type. Build the corpus as a FIXTURE holding artifacts of several types that share one status token, not against this repository's live records whose statuses change under the test. Assert on the returned record TYPES, and additionally assert the fixture's foreign-type members EXIST in the corpus (the shape check `w2y5ac`'s test uses via `_research_in_corpus`), so a fixture that silently stops spanning types fails loudly rather than passing for the wrong reason. ONE FIXTURE CONSTRAINT, MEASURED AT REVIEW WHILE PROTOTYPING THIS ITEM so the executor does not spend a cycle rediscovering it: `StatusSetTestBase.create_backlog` writes to `.aw/records/backlog/<status>/<filename>` and `setUp` creates only the `open` and `done` buckets, so the shared status token must be one BOTH trees legitimately carry (`open` works; `reviewed` raises `FileNotFoundError` because no `backlog/reviewed/` directory exists). Either pick such a token or `mkdir` the bucket in the fixture, but do not pick a plans-only status and assume the helper will place it.
  - Depends on: E-01
  - Expected outcome: a passing test, plus the pasted failure of that same test under the `if False:` resolver mutation, proving it is not vacuous.
  - Execution state: pending

- [ ] E-03 PIN THE RESOLVER-NARROWING SITE FOR THE `stem` AND `substring` KINDS, which are the two remaining resolver-owned kinds and are NOT covered by E-02: a status token and a filename token travel different rungs of `selectors.resolve`'s precedence, so one does not imply the other. Use a fixture filename stem belonging to a FOREIGN type and a substring shared across types. KEY THE ASSERTION ON TYPE, NOT ON COUNT, since a count assertion over a fixture is brittle and would break for reasons unrelated to narrowing.
  - Depends on: E-01
  - Expected outcome: two passing tests, each shown FAILING under the resolver mutation, with both pasted.
  - Execution state: pending

- [ ] E-04 PIN THE `id6` KIND, whose guard is the FAST PATH but whose pin CANNOT ISOLATE that site on its own. Assert that a FOREIGN-type id6 under a `scoped_type` call returns NO match (measured HEAD answer: `[]`), passing the unnarrowed inventory. This is deliberately NOT the same assertion as `w2y5ac`'s setid test: that one proves a scoped setid returns only in-type records, while this one proves a scoped id6 belonging to another type returns nothing at all, which is the property `run_dependencies_set_command` relies on for its `No plans artifact matched` refusal (F-2). READ THIS BEFORE WRITING THE MUTATION EVIDENCE, because the obvious form of this item is wrong and review measured it wrong: an `id6` test FAILS UNDER BOTH MUTATIONS, not only under `killFAST`, exactly as Goal fact 1's table already records (`id6` breaks in both columns, because the fast path's early return is what stops the resolver being consulted at all). So a single `killFAST` failure does NOT demonstrate this test isolates the fast-path site, and no single-kind test can: the kind that isolates `killFAST` is `setid`, which is measured to survive `killRESOLVER` untouched. Therefore this item must ALSO assert the `setid` case beside the `id6` case, over the same unnarrowed inventory, so the PAIR distinguishes the sites: `setid` failing under `killFAST` while passing under `killRESOLVER` is the only fast-path-specific signal available. Do not weaken or duplicate `w2y5ac`'s existing setid test; this assertion exists to complete the mutation argument, and E-05's site comment should record that the `id6` kind alone cannot isolate either site.
  - Depends on: E-01
  - Expected outcome: a passing `id6` test and a passing `setid` companion assertion; the `id6` test shown FAILING under BOTH mutations (recorded as expected, not as a surprise); and the `setid` assertion shown FAILING under `killFAST` and PASSING under `killRESOLVER`, which is the pair that isolates the fast-path site.
  - Execution state: pending

### Task group 3: correct the record at the code site

- [ ] E-05 REWRITE `match_selector`'s DOCSTRING to state the measured division of labour, replacing the current text whose "``scoped_type`` NARROWS EVERY SELECTOR KIND EXCEPT THE DIRECT PATH" sentence describes the FUNCTION'S net contract accurately but attributes it to one mechanism, which is what lets a reader believe either site is removable. Name both sites, name WHICH KINDS each one guards, and state that neither is removable, citing the measured consequence of removing each. ADD A SHORT COMMENT AT EACH SITE too, because a reader deleting a line reads the line and not the docstring; that is the same reasoning the existing `Type mismatch` comment in `run_set_command` records for itself. Also record, at the fast-path site, that its guard is INVISIBLE from a pre-narrowed caller list (Goal fact 6), so the next test author knows to pass an unnarrowed list. Do NOT restate the performance rationale as the reason to keep the filter: correctness is now the reason, and leaving performance as the stated justification is what invited the item's proposal to trade it away.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the `git diff` of `agent_workflows/status_set.py` showing the docstring and both site comments, with no executable line changed (diff confirms comments and docstring only).
  - Execution state: pending

### Task group 4: amend the governing spec

- [ ] E-06 AMEND SPEC `2lcqno` N3, whose "ONE DOCUMENTED HOLE THAT N3 MUST NOT BE READ AS CLOSING" paragraph carves out the direct-PATH exemption and thereby implies everything else is covered by a single mechanism. Add that type-scoped resolution is delivered by TWO independent sites covering disjoint selector kinds, that removing either is a cross-type defect, and that the direct-PATH exemption is a THIRD fact rather than the only caveat. Also correct the spec's acceptance criterion 5, which reads "a REGRESSION TEST that fails when `match_selector`'s type narrowing is reverted" in the singular and was measured to be satisfiable while leaving three selector kinds untested. Cite the measurement, not this plan's prose. STATE WHY IN THE SPEC-SYNC SECTION as the plan contract requires. Write no em or en dashes in the amended spec prose. THE SPEC IS `- Status: approved`, WHICH DECIDES THE MECHANISM AND IS NOT A REASON TO SKIP THE AMENDMENT. Record the amendment with `aw specs note <spec-path> --message "<what changed and why>"`, which appends an attributed `## Workflow history` record WITHOUT touching the status; do NOT use `aw specs set` for this, because re-running a status transition on an approved spec would either re-assert an approval this plan has no authority to make or demote a contract nobody asked to reopen, and do NOT hand-edit the history block. The approval itself is untouched and must stay untouched: these are corrections of FACT inside an approved contract whose normative requirement (N3: resolution is type-scoped) this plan does not alter, which is exactly the case the repository's plan-may-amend-a-spec rule covers.
  - Depends on: E-05
  - Expected outcome: the `git diff` of the spec showing the amended N3 paragraph and the corrected criterion 5, plus the appended history record and the exact `aw specs note` invocation that produced it, and a confirmation that `- Status: approved` is byte-unchanged in the diff.
  - Execution state: pending

- [ ] E-07 RUN THE FULL REGRESSION GATE, capturing a pre-execution baseline BEFORE any edit in this plan lands and a post-change run after E-06, both with bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel and the fast subset, and a second `-q` would suppress the `N passed` line this plan requires). Then run `aw ipd lint --phase pre-transition` on this plan, `aw check` compared against its own pre-change baseline, and `aw sanitize --agent`. A pre-existing failure must be shown pre-existing by the baseline rather than argued harmless.
  - Depends on: E-06
  - Expected outcome: baseline and post-change summary lines pasted side by side, a conforming pre-transition lint, `aw check` no worse than baseline with both counts pasted, and a clean sanitizer report.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (AGENTS.md, GUIDING_PRINCIPLES P16). Every test this plan adds CALLS `match_selector` and asserts on returned records. None reads source text, counts callers, or asserts a comment survives. That constraint is load-bearing here, because the tempting shortcut for "prove the comment is present" is exactly the banned `inspect`/regex pin; E-05 is validated by its DIFF instead.
- A PLAN MAY AMEND A SPEC AND MUST DECLARE IT (AGENTS.md). The spec file is declared in `- Scope-Paths:` so the runner announces the edit before the run and reconciles it afterward.
- THE MUTATION-DEMONSTRATION CONVENTION IS ESTABLISHED IN THIS REPOSITORY AND IS THE ONLY EVIDENCE THAT REFUTES VACUITY. Spec `2lcqno` acceptance criterion 2 requires "a mutation check (break the descriptive comparison, show the pin FAILS, restore, show it passes)". Every `V-*` below demands the same, because a test that passes is not evidence it tests anything.
- `selectors.resolve`'s PRECEDENCE IS THE AUTHORITY ON WHICH KINDS EXIST, and its docstring enumerates them (`path`, `id6`, `setid`, `status`, `stem`, `substring`) with the note that kinds 2 to 5 are EXACT and only `substring` is a substring. The disjointness argument in Goal fact 1 is derived from that list plus the fast path's early return, so a kind added to `resolve` later would need re-examining against both sites.
- `run_set_command` ALREADY CARRIES A LONG COMMENT WARNING AGAINST DELETING A TYPE GUARD AS DEAD CODE (the `setidfix w2y5ac E-02` block above the `Type mismatch` refusal, which says "DO NOT DELETE IT AS DEAD CODE" and records what deleting it was measured to permit). E-05's site comments follow that established shape rather than inventing one.
- THE CALLER-SIDE POST-FILTER IS NOT A SUBSTITUTE FOR THE RESOLVER GUARANTEE. `run_dependencies_set_command` and `run_dependencies_remove_command` both re-filter with `plan_matches = [m for m in matches if m.record_type == "plans"]`. That belt is real and is why fact 2's degradation stops short of corruption, but relying on it would move the invariant into every caller, and `run_set_command`'s own `Type mismatch` comment explains why a single guarded resolver is preferred.

## Findings

| # | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-1 | The two narrowing sites cover DISJOINT selector kinds and neither is redundant | Per-site mutation matrix: `killFAST` breaks `setid`/`id6` only; `killRESOLVER` breaks `status`/`stem`/`substring` only | The backlog item's redundancy premise is false; the deliverable is a pin plus a corrected record, not a refactor (E-05) |
| F-2 | The item's suggested remedy would ship a cross-type defect | With the fast-path filter removed, a plans-scoped backlog `id6` returns a `backlog` record, and `aw ipd dependencies set 5m43v9` degrades from `No plans artifact matched` to a wrong-type diagnostic | The "drop the redundant filter" option is REFUSED and recorded as refused, not left as an open choice (Deferred section) |
| F-3 | The resolver-narrowing site is entirely unpinned | Full suite with `if scoped_type:` -> `if False:`: `3246 passed, 2 skipped` at authoring; RE-MEASURED AT REVIEW `3346 passed, 2 skipped, 3 warnings in 105.97s`, still zero failures | Three selector kinds need new tests; this is the plan's central work (E-02, E-03). Re-confirmed four days and 100 tests later, so the gap is not a transient |
| F-4 | The fast-path site is pinned by EXACTLY ONE test in the whole repository, and the item misread which site its pin covers | With `cands = list(all_records)`: `1 failed, 81 passed` on the module (78 at authoring) and, added at review, `1 failed, 3345 passed, 2 skipped` on the FULL suite, failing only `test_scoped_setid_resolution_returns_only_the_scoped_type` | That test must not be weakened; the new pins sit beside it (E-04). The full-suite count is what makes the claim precise: one test versus zero, not "some" versus "none" |
| F-5 | The fast path avoids a resolver walk three to four orders of magnitude costlier than the filter it carries | Authoring (1903 records): `setid` hit 0.08ms, `status` miss 134.52ms, filter 0.053ms. Review (2009 records): 0.28ms, 680.42ms, 0.0866ms. The RATIO is stable in sign and magnitude class (~2500x, ~7800x); the absolute figures moved ~5x for 6 percent corpus growth | Removing the filter reclaims nothing even on the item's own performance framing (E-05 must not cite performance as the reason to keep it). NO millisecond figure is a bar; an executor re-measuring must expect different numbers |
| F-9 | ADDED AT REVIEW: an `id6` test CANNOT isolate either narrowing site, so E-04 as first written could not deliver the evidence V-04 demanded | Prototyped both mutations against a foreign-type `id6` assertion: it FAILS under `killFAST` AND under `killRESOLVER`. The `setid` kind is the only one that isolates the fast path, failing `killFAST` while passing `killRESOLVER` | E-04 must assert the `setid` case BESIDE the `id6` case and V-04 must require both mutation columns; a lone `id6` killFAST failure proves nothing about which site guards. Goal fact 1's table already recorded the both-columns behavior, so E-04 contradicted its own plan |
| F-10 | ADDED AT REVIEW: the test fixture cannot place a plans-only status on a backlog item | `StatusSetTestBase.create_backlog` writes to `.aw/records/backlog/<status>/` and `setUp` creates only `open` and `done`; prototyping E-02 with a shared `reviewed` token raised `FileNotFoundError` for `backlog/reviewed/` | E-02 must pick a status BOTH trees carry (`open` measured working) or create the bucket in the fixture. Recorded so the executor does not lose a cycle to a fixture error that looks like a resolution bug |
| F-11 | ADDED AT REVIEW: all four intended tests are achievable and provably non-vacuous, prototyped before sign-off | Four prototype tests (`status`, `substring`, foreign-type `stem`, foreign-type `id6`) over an unnarrowed fixture inventory: 4 passed at HEAD; under `killRESOLVER` all 4 failed; under `killFAST` exactly the `id6` one failed | The plan's central deliverable is demonstrably buildable, which is what makes the `to-review` verdict safe to give. The prototype is a throwaway probe, NOT the deliverable: E-02 through E-04 still author the real tests in `tests/test_status_set.py` |
| F-6 | Both sites are invisible from the pre-narrowed production call shape, but only the FAST PATH is | With a pre-narrowed list, `killFAST` changes nothing for any kind; `killRESOLVER` still changes `status`/`stem`/`substring` because the resolver reads the filesystem | Every new test passes an UNNARROWED list; the "pass unnarrowed" rule is specific to the fast path and must be recorded as such (E-05) |
| F-7 | The item's "every caller pre-narrows" claim is true of one caller, not all | `run_set_command` passes `inventory_all_artifacts(repo_root, scoped_type=...)`; `run_dependencies_set_command` and `run_dependencies_remove_command` pass `inventory_all_artifacts(repo_root)` unnarrowed | An unnarrowed production path EXISTS, so the fast-path guard is reachable in production and not merely theoretical (F-2 measured through it) |
| F-8 | Spec `2lcqno` N3 documents one caveat and one regression test, both singular | N3's "ONE DOCUMENTED HOLE" names only the direct-PATH exemption; criterion 5 asks for "a REGRESSION TEST that fails when `match_selector`'s type narrowing is reverted" | The spec must be amended or it keeps licensing the single-mechanism reading that produced this item (E-06) |

## Proposed changes (ordered, validatable)

1. Re-derive the per-site, per-kind mutation matrix and the two baseline suite results, then restore the file (E-01).
2. Add a resolver-narrowing pin for the `status` kind over an unnarrowed inventory (E-02).
3. Add resolver-narrowing pins for the `stem` and `substring` kinds (E-03).
4. Add a foreign-type `id6` pin plus the `setid` companion assertion that isolates the fast-path site (E-04).
5. Rewrite the docstring and add a comment at each narrowing site, naming the kinds each guards (E-05).
6. Amend spec `2lcqno` N3 and its acceptance criterion 5 (E-06).
7. Run the regression gate against a pre-execution baseline (E-07).

## Deferred / out of scope (with reason)

- REMOVING THE FAST-PATH FILTER, which is the backlog item's own second suggestion. REFUSED ON MEASUREMENT, not deferred: F-1 shows it is the only type guard for `id6` and `setid`, and F-2 measures the resulting cross-type leak end-to-end. The item reached for it on a redundancy premise that separate-site mutation falsifies.
  - Carrier-Declined: Nothing is owed because there is no latent work here, only a proposal this plan measured and refused. Filing an item would assert the repository intends to remove the filter, which the evidence in F-1, F-2 and F-5 contradicts three ways (it guards two kinds, removing it leaks a foreign type through a real caller, and it reclaims about 0.05ms while avoiding about 134ms). The refusal and its evidence are recorded here and, after E-05, at the code site, which is where a future author considering the same removal will read it.
- CONSOLIDATING THE TWO SITES INTO ONE NARROWING AUTHORITY. Genuinely attractive and deliberately not attempted here. It is a behavior change to a hot path (F-5) requiring its own measurement, and doing it in the same change as the pins would mean the new tests are written against the new shape and could never demonstrate they catch the OLD defect.
  - Carrier-Declined: No carrier is filed because the prerequisite this plan delivers is what makes the question answerable, and filing now would guess at a design that the pins may well render unnecessary. After E-02 through E-04 land, any consolidation attempt is immediately falsifiable by tests that exist, which is the correct sequencing: pin first, refactor second. If a future author wants it, the measured matrix in E-01's evidence and the site comments from E-05 are the brief they need, and they can file the item then with the design in hand rather than as a placeholder.
- THE DIRECT-PATH TYPE EXEMPTION and the `Type mismatch` refusal that guards it. Already owned, measured and pinned by `w2y5ac` (its E-02 and `test_scoped_verb_refuses_a_foreign_type_path_and_writes_nothing`), and already documented in spec `2lcqno` N3. This plan cites it as a third fact but changes nothing about it.
  - Carrier-Declined: Nothing is owed because the work is DONE, by a plan already in `executed/` with a live test. E-06 extends the spec paragraph that describes it without altering the exemption or its guard, so there is no residual behavior to carry. An item here would misrepresent completed, tested work as outstanding.
- THE YAML-VERSUS-BULLET FRONT-MATTER DIALECT GAP that stops `read_artifact_record` parsing a research doc's `set:` field. Visible while measuring (research records carry `set_id=None` in the inventory) and explicitly owned by plan `xo3244`, Set `selfmdialect`, as recorded in `w2y5ac`'s test docstring.
  - Carrier-Declined: A carrier already EXISTS and is named (`xo3244`), so filing a second one would duplicate tracked work. This plan's fixtures must not depend on a research doc's setid resolving, for the same reason `w2y5ac`'s did not; E-02's fixture uses types whose bullet dialect parses, which keeps this plan independent of when `xo3244` lands.
- CHANGING ANY RUNTIME BEHAVIOR of `match_selector`: its precedence, its signature, which records it returns, or the caller-side post-filters. This plan adds tests, comments, a docstring and a spec amendment.
  - Carrier-Declined: A scope fence, not deferred work. No finding here measures a fault in the function's behavior; F-1 measures that its behavior is CORRECT and merely undocumented and half-untested. The fence is enforced by V-05's requirement that the `agent_workflows/status_set.py` diff change no executable line.

## Scope check

- Over-scope: none. `agent_workflows/status_set.py` carries `match_selector` and both narrowing sites; `tests/test_status_set.py` is that module's test file and already holds the `SharedSetidCrossTypeResolutionTests` class the new pins belong beside; the spec file is the normative statement E-06 must stop contradicting (F-8).
- Under-scope: `agent_workflows/selectors.py` is deliberately NOT declared. Its precedence list is the authority the disjointness argument reads FROM, and nothing about it needs changing; if the executor concludes the fix requires editing it, that is a scope change to stop and re-declare rather than to absorb. `agent_workflows/cli.py` is likewise undeclared: F-2 was measured through `aw ipd dependencies set` by monkeypatching in a throwaway script, not by editing the verb.

## Required tests / validation

- `python3 -m pytest` run BARE, with the pasted `N passed` summary line, against a pre-execution baseline captured the same way. RE-DERIVE THE BASELINE; DO NOT COMPARE TO A NUMBER IN THIS PLAN. Measured `3246 passed, 2 skipped` at authoring and `3346 passed, 2 skipped` at review four days later, so the total is a live population that grows with every merged lane and a mismatch with either figure is normal growth, not a regression. The durable bar is that the baseline is GREEN before any edit and that the FAILED set is unchanged after.
- A targeted `tests/test_status_set.py` run, since every new test lands there and the module is where F-4's existing pin lives.
- A MUTATION DEMONSTRATION FOR EVERY NEW TEST: break the site it pins, paste the failure, restore, paste the pass. A new test with no mutation evidence is exactly the vacuous pin this plan exists to prevent, so this is a hard requirement and not a nicety.
- `aw ipd lint --phase pre-transition` conforming, `aw check` no worse than a pre-change baseline with both counts pasted, and `aw sanitize --agent` clean.
- A `git status --short` after E-01 proving both exploratory mutations were reverted before any real edit landed.

## Spec / documentation sync

- SPEC `2lcqno` IS AMENDED BY THIS PLAN (declared in `- Scope-Paths:`), and the reason is that leaving it unamended keeps the repository's own approved contract licensing the misreading that produced backlog item `ihgjii`. THE SPEC IS `approved`, so the amendment is recorded with `aw specs note` and the `- Status: approved` line and its `--by-human` approval record are left byte-unchanged (see E-06). That is the correct handling rather than a loophole: the repository's rule is that a plan changing behavior a spec describes SHOULD carry the spec amendment in the same change, and the two edits here are corrections of FACT (how many mechanisms deliver N3, and that criterion 5 is satisfiable while three kinds go untested) inside a contract whose NORMATIVE requirement this plan does not touch. Nothing about N3's obligation, the direct-PATH exemption, or the `Type mismatch` guard changes. N3's "ONE DOCUMENTED HOLE THAT N3 MUST NOT BE READ AS CLOSING" paragraph names the direct-PATH exemption as the single caveat, which invites a reader to conclude that one mechanism covers every other kind; measurement (F-1) shows two independent mechanisms cover disjoint kinds. Acceptance criterion 5 compounds it by asking for "a REGRESSION TEST" in the singular, and F-3 measures that criterion as satisfiable today while three selector kinds have no test at all. Both are corrections of fact, not changes of intent: N3's normative requirement (resolution is type-scoped) is untouched.
- NO OTHER SPEC OR DOC CHANGES. `docs/` carries no statement about `match_selector`'s internals (searched), and `ipd-structure-and-linting` is cited only for the citation-anchor convention this plan follows.
- THE PRIMARY DOCUMENTATION DELIVERABLE IS THE CODE SITE ITSELF (E-05), deliberately. A reader about to delete a filter reads the filter, so a docstring alone would not have prevented this item; the same reasoning is already recorded in `run_set_command`'s `Type mismatch` comment block.

## Open questions

### OQ-01: Should the two narrowing sites eventually be consolidated into one authority, and does this plan's pin make that safe?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: This plan deliberately does NOT consolidate, for the sequencing reason in the Deferred section: tests written against a consolidated shape cannot demonstrate they catch the pre-consolidation defect, so pinning must come first. The question is whether the reviewer wants consolidation tracked now or left to a future author holding E-01's matrix and E-05's comments. NOT BLOCKING because the answer changes nothing in this plan's checklist: every item is required under either answer, and the pins are the prerequisite in both directions.
- Carrier-Declined: No carrier is owed under either answer. If the reviewer wants consolidation, the correct artifact is a new plan authored AFTER these pins exist, whose design can be measured against them; a placeholder filed now would have to guess the design and could not cite the evidence that justifies it. If the reviewer does not, there is nothing to carry. Either way the measured matrix and the site comments are the durable brief, and they land inside this plan.

### OQ-03: Does fact 3 (a normative spec guarantee with zero tests) change the `chore` classification to `bug`?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW: `chore` is CORRECT and stays. The question is worth asking because the plan's gate paragraph justifies `chore` on the item's own reasoning ("HEAD gives no wrong answer and no user waits on the difference") without testing that reasoning against fact 3, which is a strictly worse finding than the item had: a guarantee spec `2lcqno` N3 makes NORMATIVE has no test at all, and `aw check release-gates` exists because the repository does not ship known bugs. The answer is that the repository's own test is USER-PERCEPTIBLE IMPACT, and it is not met. Measured at review, HEAD returns the CORRECT answer for every one of the six kind/token rows: the type sets under `HEAD` are exactly the scoped type in every cell. The defect is entirely in the TEST COVERAGE and the RECORD, not in behavior, so no user can perceive anything today; what fact 3 measures is a missing guard against a FUTURE regression. `AGENTS.md` is explicit that inefficiency or risk a user cannot notice is not a defect, and it equally warns against over-filing (a correct-but-unpinned path is not the performance case the rule was extended to cover). Note also that a `bug` classification would be self-defeating here: it would attach `- Blocks-Release: next` to a plan that changes no runtime behavior, gating a release on a documentation-and-tests change while the thing the gate exists to prevent (a wrong answer reaching a user) is measurably absent. If a regression LATER lands because this pin was missing, that regression is the bug and this plan is its prevention.
- Carrier-Declined: Nothing is owed under the answer taken. The classification is confirmed rather than changed, so there is no follow-up work and no gate to file; the measurement that confirms it (HEAD correct in all eighteen matrix cells) is recorded in Goal fact 1 and re-derived by E-01, which is where a future reader disputing the call would look. Filing an item would record "reconsider whether an untested-but-correct path is a bug" as outstanding work, which is a policy question the repository already answers.

### OQ-02: Should the new tests join the existing `SharedSetidCrossTypeResolutionTests` class or form their own?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: The existing class carries `w2y5ac`'s four properties and a corpus-shape fixture (`_build_shared_topic`, `_research_in_corpus`) that E-02 through E-04 could reuse, which argues for joining it. Against that, its docstring is scoped to "a setid is a SHARED cross-type TOPIC label" and the new pins are about `status`/`stem`/`substring`/`id6` kinds, so joining it would widen a documented class contract. The plan leaves the choice to the executor as a recorded decision; it affects test organization only, and V-02 through V-04 demand the same mutation evidence either way.
- Carrier-Declined: NOT BLOCKING and carrying no residual work, because both branches are implemented inside E-02 through E-04 and neither leaves anything unbuilt. The executor records whichever it chose and why, and the mutation evidence each `V-*` demands proves the tests work regardless of where they live. Filing an item would imply test placement is outstanding work after this plan executes, and it is not.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the re-derived per-site, per-kind matrix PASTED, covering all six kind/token rows for HEAD, killFAST and killRESOLVER separately, with an explicit statement of whether the TYPE SETS match this plan's Goal fact 1 table and, if not, exactly which cells moved. Differing `n=` counts are EXPECTED (the corpus grows) and are not a mismatch to report as a finding; a changed TYPE SET is. Plus the pasted full-suite summary line under the resolver mutation and BOTH the module and the FULL-suite summary under the fast-path mutation, since F-4's precision rests on the full-suite count being exactly one failure. Plus a pasted `git status --short` showing `agent_workflows/status_set.py` unmodified after restoration. A matrix produced by mutating both sites together does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted PASS of the new `status`-kind test, AND pasted FAILURE of that same test with the resolver branch mutated to `if False:`, AND a pasted PASS after restoring. Plus confirmation shown by reading the test that it passes an UNNARROWED record list and that the fixture's foreign-type members are asserted present in the corpus. A pass with no paired failure does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the same mutate/fail/restore/pass triple, PASTED SEPARATELY for the `stem` test and for the `substring` test, because one passing does not imply the other (they travel different rungs of `selectors.resolve`'s precedence). Plus confirmation that each asserts on record TYPE rather than on a count.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted PASS of the foreign-type `id6` test, then its FAILURE under BOTH mutations pasted SEPARATELY (`cands = list(all_records)` and `if False:`), with an explicit statement that failing under both is the EXPECTED and measured behavior for this kind rather than a defect in the test. Then the `setid` companion assertion's PASS, its FAILURE under `killFAST`, and its PASS under `killRESOLVER`, which is the pair that actually isolates the fast-path site; a `V-04` that pastes only an `id6` killFAST failure does NOT satisfy this item, because that failure is equally produced by the resolver mutation and so proves nothing about which site is guarding. Pasted PASS after restoring. Plus evidence that `test_scoped_setid_resolution_returns_only_the_scoped_type` STILL PASSES unmodified, proving F-4's existing pin was not weakened or absorbed.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the `git diff` of `agent_workflows/status_set.py`, shown to contain ONLY docstring and comment changes with no executable line altered (state how that was confirmed from the diff, for example that every `+`/`-` line is inside a docstring or begins a comment). The diff must show, for each site, which selector kinds it guards and the measured consequence of removing it, and must show the fast-path comment recording that its guard is invisible from a pre-narrowed caller list. Confirm the performance rationale is NOT presented as the reason to keep the filter. Do NOT satisfy this item with a test that inspects source text; the diff is the evidence.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the `git diff` of the spec file showing the amended N3 paragraph and the corrected acceptance criterion 5, the pasted history record plus the exact `aw specs note` command that appended it, and a confirmation that the amended prose contains no em or en dashes. Plus a statement that N3's normative requirement was not altered, only its account of how many mechanisms deliver it. AND confirm from the diff that `- Status: approved` is byte-unchanged and that no `aw specs set` was run against this spec, since an approved contract's approval attestation is not this plan's to rewrite.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: bare `python3 -m pytest` output with the `N passed` summary line pasted, beside the pre-execution baseline captured the same way, so any failure is shown pre-existing rather than introduced. Plus `aw ipd lint --phase pre-transition` conforming, `aw check` counts before and after pasted with the after no worse, and `aw sanitize --agent` reporting zero findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, whose absence is deliberate: that field is
an output of `/plan-review` and writing it at authoring time would forge the attestation a gate reads.

The executor must: perform E-01 through E-07 in order, respecting the declared `Depends on` edges; treat
E-01 as a hard gate, since every later item rests on its matrix and a matrix produced by mutating both
sites at once would reproduce the backlog item's original error; commit only the three paths in
`- Scope-Paths:` via `aw commit <plan> -- <paths>`; never push; paste ACTUAL runner output for every claim
of a passing test, INCLUDING the paired mutation failure each new test requires; and verify each `V-*` in a
separate pass from the `E-*` that produced it. Do NOT mark this plan executed or move it to
`.aw/records/plans/executed/` until every `V-*` carries concrete pasted evidence and
`aw ipd lint --phase pre-transition` conforms.

Backlog item `ihgjii` is this plan's origin (`- From-Backlog: ihgjii`). That item carries NO
`- Blocks-Release:` gate and none is invented here, consistent with its `chore` work kind: measurement
confirms the item's own classification, since HEAD gives no wrong answer and no user waits on the
difference. What the item got wrong was its diagnosis, not its severity. THAT CLASSIFICATION WAS
RE-EXAMINED AT REVIEW AGAINST FACT 3 and confirmed; see OQ-03, which records why an untested but
provably correct path is not a `bug` under the repository's user-perceptibility test, and why gating a
release on a change that alters no runtime behavior would be self-defeating.
