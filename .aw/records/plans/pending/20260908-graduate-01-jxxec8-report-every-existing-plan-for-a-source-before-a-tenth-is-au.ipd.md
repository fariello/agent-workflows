# IPD: Report every existing plan for a source before a tenth is authored, distinguishing decomposition from duplication

- Date: 2026-09-08
- Kind: child
- Concern: Nothing asks whether a spec or backlog item ALREADY has plans, so the expensive failure the maintainer named has no guard: "we need a way to make sure that the spec / backlog items have not already been addressed. We don't want multiple IPDs for the same things, especially if already implemented." VERIFIED AT HEAD `a2e0438a`: `check_engine` carries `check.from-backlog-dangling` and `check.from-spec-dangling`, both of which validate that a plan's source id6 RESOLVES to a real artifact. Neither asks the reverse question, and grepping the rule table for a duplicate or already-implemented check returns nothing.
  THE RAW MATERIAL EXISTS AND HAS GROWN, which is what makes an advisory view tractable rather than speculative. Measured across the whole plans tree at HEAD `a2e0438a`: 120 plans carry a source link (backlog `6h7y2y` recorded 71), spanning 72 distinct sources, of which 17 have MORE THAN ONE plan.
  THE "125" THIS PLAN FIRST STATED IS THE BULLET COUNT, NOT THE FILE COUNT, AND THE GAP IS AN INDEXING REQUIREMENT RATHER THAN A TYPO (review, F-8). There are 125 source-link BULLETS across 120 FILES, because FIVE plans carry BOTH a `From-Spec:` and a `From-Backlog:` bullet: `5942n7`, `pgq326`, `84j8d7` and `ueg5cf` (each `Backlog: kxkc04` + `Spec: 77tr3o`), and `h0zljh` (`Spec: 7ckptx` + `Backlog: vqv9im`). So E-01's reverse index MUST record every source bullet a plan carries; an index built with a single first-match read per file drops one edge on each of those five and under-reports the `77tr3o` and `vqv9im` clusters. Re-measured at review one day later: 166 bullets over 106 sources with 24 multi-plan clusters, which is this plan's own derive-never-pin rule demonstrating itself. The largest clusters are `From-Spec: 25kzda` x9 (8 `executed`, 1 `not-executed`), `From-Backlog: kjzlgw` x8 (all `executed`), `From-Spec: 7ckptx` x7 (4 `executed`, 3 `approved`), `From-Spec: kw5y2s` x6 (all `executed`), and `From-Backlog: 1ap48y` x4 (3 `executed`, 1 `superseded`). So someone about to graduate `25kzda` a tenth time faces eight executed siblings and nothing says so.
  THIS SET'S OWN MOTIVATING CASE IS THE STRONGEST EVIDENCE. Spec `6m4kow`, which backlog `6h7y2y` cites as having independently recorded the same measurement, ALREADY has three executed plans carrying `From-Spec: 6m4kow` (`eyh1fu`, `5slbpi`, `wpomxa`). Had this view existed, whoever filed the item would have seen those three and scoped it differently, and in fact two of the item's three premises turned out to be already-shipped work.
  THE HARD PART IS THAT MULTIPLE PLANS PER SOURCE ARE NORMAL AND CORRECT, so a naive uniqueness rule would be worse than nothing. A spec is deliberately decomposed into an ordered Set of children with distinct Orders and non-overlapping scope, and spec `25kzda`'s own graduation text says a run "may produce more than one IPD ... because a single item's design does not always decompose into exactly one plan". The nine-plan `25kzda` cluster is right, not a defect.
- Scope: Add a READ-ONLY, ADVISORY pre-graduation view that reports every existing plan carrying a given source id6 with its status and Set, so whoever graduates sees the cluster before authoring. It SHOWS; it does not decide. It must state in its own output which of the three cases it can and cannot detect. EXCLUDES any `count > 1` uniqueness rule; excludes any refusal or gate; excludes the already-implemented verdict, which is not mechanically answerable and is tracked by backlog `f1sw71`; excludes wiring the view into the graduation path (child 02 `iuxtjy`); excludes changing either forward dangling check.
- Scope-Paths: agent_workflows/check_engine.py, agent_workflows/cli.py, tests/test_graduation_view.py
- Item-Dependencies: none
- Status: to-review
- Set: graduate
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: jxxec8
- From-Backlog: 6h7y2y

## Workflow history

- 2026-09-08 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `6h7y2y` Half 2, which the item itself calls "THE ONE THAT MATTERS". The item carries no `- Blocks-Release:` so none is inherited or invented. This child is Order 01 because the item's sequencing note is explicit and gives its reason: "build the guard BEFORE or WITH the verb, not after. A working `--action plan` with no duplicate check is a machine for generating redundant plans faster than a human can."
  EVERY CLAIM RE-MEASURED at HEAD `a2e0438a` and the item held, with its numbers updated: 125 source-linked plans rather than 71, 72 distinct sources, 17 with more than one plan, and the three named clusters confirmed with their exact status breakdowns. The absence of a reverse-direction check also confirmed by grepping the rule table rather than by trusting the item.
  THE ITEM'S OWN CASE PROVED ITS POINT, and I recorded it as F-3 because it is the most persuasive argument in the plan: spec `6m4kow` already has three executed plans, and this very item was filed partly on premises that had already shipped. That is exactly the waste the view prevents.
  I IMPLEMENT THE ITEM'S "MINIMUM USEFUL VERSION" DELIBERATELY, NOT AS A SHORTCUT. The item offers a full three-way classifier and then says: "MINIMUM USEFUL VERSION, if the full classifier is too much: a PRE-GRADUATION WARNING that reports every existing plan carrying this source id6 with its status and Set ... Advisory and read-only; it does not need to decide, only to show. That alone would prevent the costly case." The full classifier is NOT chosen because one of its three cases is mechanically unanswerable: there is no per-requirement tracking, a spec carries ONE whole-artifact status with no partial-implementation state, and `implemented` requires only a resolvable citation rather than semantic verification. Backlog `f1sw71` (`graduated` to decision plan `si24ia`, which measures and recommends rather than building a requirement model; the GAP itself is unbuilt) tracks that, and the item explicitly permits shipping the plan-level guard without it provided the plan "say honestly which of the three cases above it can and cannot detect". E-03 makes that honesty part of the OUTPUT rather than only part of this document, which is the one place I went beyond the item.

## Goal

Let whoever is about to graduate a source see, before they author anything, every plan that source already has and what became of it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: read the cluster from the authority that already exists

- [ ] E-01 BUILD THE REVERSE INDEX from source id6 to the plans that cite it, reusing the enumeration the forward dangling checks already use rather than walking the tree afresh. `check.from-backlog-dangling` and `check.from-spec-dangling` already parse `From-Backlog:` and `From-Spec:` out of every plan to validate the forward direction, so the parse exists; this item inverts it.
  DO NOT ADD A SECOND PARSER FOR `From-Backlog:`/`From-Spec:`. Two readers of one field drift, and the forward checks are `error` severity, so a divergence would mean the view and the checker disagree about which plans cite a source. Locate the existing readers by symbol and reuse them.
  CARRY THE STATUS AND THE SET, because they are what makes the output actionable: the item's own example is "25kzda already has 9 plans, 7 executed" (measured today: 8 executed, 1 not-executed). A list of ids without statuses would not distinguish "already built" from "in flight".
  INCLUDE TERMINAL DIRECTORIES, NOT ONLY `pending/`. The costly case the maintainer named is re-doing landed work, so a view that reads only pending plans would miss every executed sibling and would be worst exactly where it matters most. Measured, most cluster members are `executed`.
  INDEX EVERY SOURCE BULLET A PLAN CARRIES, NOT THE FIRST MATCH, and this is a measured requirement rather than a defensive one (F-8). Five plans carry BOTH kinds of link, so a `re.search`-style first-match read per file silently drops one edge on each and under-reports two real clusters. Note the existing forward readers are single-match BY DESIGN (`find_from_backlog_plans` uses `_META_FROM_BACKLOG_RE.search`, and `check_from_spec_dangling` uses `_ITEM_FROM_SPEC_RE.search`), which is correct for their question ("does THIS plan's link resolve?") and WRONG for this one. So reuse the PATTERNS and the ITERATOR, and do the multi-match walk here; do not assume a reused reader already returns every link.
  DO NOT BUILD A SECOND TRAVERSAL OF THIS EDGE. Pending plan `bwgyum` (Set `setidhard`, Order 02, `reviewed`, `go-pending-approval`) adds the FORWARD `- Graduated-To:` link and `check.graduated-to-dangling` over the SAME `_iter_plan_ipds` in the SAME module. Whichever of the two lands second consumes the first rather than re-walking; the orchestrator (`y9s4vm`) carries that as a binding constraint and verifies it as CID-7. Check `bwgyum`'s status before writing E-01 and record which case you are in.
  - Depends on: none
  - Expected outcome: a reverse index mapping each source id6 to its plans with each plan's id6, status and Set, built by reusing the existing field readers and iterator; EVERY source bullet indexed (the five dual-link plans appear under both sources); terminal directories included; no second parser added; `bwgyum`'s status checked and the shared-traversal case recorded.
  - Execution state: pending

### Task group 2: report it without deciding

- [ ] E-02 EXPOSE IT AS A READ-ONLY SURFACE, and choose the surface deliberately (OQ-01). The item is explicit that this is "Advisory and read-only; it does not need to decide, only to show".
  DO NOT IMPLEMENT A `count > 1` RULE, and this is the single most important prohibition in the plan. Measured, 17 of 72 sources have more than one plan and the largest cluster of nine is CORRECT decomposition; spec `25kzda` says a run "may produce more than one IPD". A rule that flags count would report 17 legitimate clusters as defects and would teach people to ignore it, which is worse than having no guard.
  IF YOU CHOOSE A `check` RULE, ITS SEVERITY MUST BE `info`. `check_engine`'s `_DEFAULT_RULESPEC` exists so "a new rule is never SILENTLY unclassified", and a `warning` exits nonzero: measured, `drift_exit_code` exempts only `info`, so a `warning` would red every `aw check` run on 17 legitimate clusters. That is a real trap the repository already documents.
  MAKE IT ANSWER THE QUESTION SOMEONE ACTUALLY ASKS, which is "I am about to graduate X, what exists already?". That means accepting a source selector and reporting its cluster, not dumping all 72 clusters and leaving the reader to search.
  - Depends on: E-01
  - Expected outcome: a read-only surface that takes a source selector and reports its cluster with statuses and Sets; NO uniqueness rule; if implemented as a `check` rule, severity `info` with the `drift_exit_code` behavior verified rather than assumed.
  - Execution state: pending

- [ ] E-03 STATE THE LIMITS IN THE OUTPUT, not only in this plan. The item requires the work "say honestly which of the three cases above it can and cannot detect", and a limit recorded only in a plan file is invisible to the person reading the view.
  THE THREE CASES AND WHAT THIS VIEW CAN DO ABOUT EACH, which the output must convey: LEGITIMATE DECOMPOSITION (several children of one Set, distinct Orders, non-overlapping scope) is VISIBLE, because the view shows the Set and the reader can see one Set with many Orders; ACCIDENTAL DUPLICATION (two plans in DIFFERENT Sets covering the same requirement) is PARTLY VISIBLE, because the view shows that the Sets differ but cannot judge whether the scopes overlap; ALREADY IMPLEMENTED is NOT DETECTABLE, because there is no per-requirement tracking.
  SAY WHY THE THIRD IS UNDETECTABLE, briefly, rather than just declining it. A spec carries ONE whole-artifact status with no partial-implementation state, and `implemented` requires only a resolvable citation rather than semantic verification. Point at backlog `f1sw71`. A reader who knows WHY will not assume the view failed.
  DO NOT OVERSTATE THE SECOND CASE. The view cannot compare scopes; claiming it detects duplication would be the same kind of false confidence this whole item exists to prevent.
  - Depends on: E-02
  - Expected outcome: the view's own output states, per case, whether it is visible, partly visible, or undetectable, with the reason for the undetectable one and a pointer to `f1sw71`; no case is overstated.
  - Execution state: pending

### Task group 3: prove it against the real corpus and against over-reach

- [ ] E-04 TEST AGAINST THE LIVE CORPUS FOR THE NO-FALSE-POSITIVE PROPERTY, and against fixtures for everything else. This split is deliberate: the property "correct real work is not flagged" can only be demonstrated on the real corpus, while every behavioral case needs a fixture to be stable.
  THE LIVE ASSERTION: for `From-Spec: 25kzda` (nine plans, eight executed), the view REPORTS the cluster and flags NO defect. That is the anti-over-reach guard and it is the reason a fixture alone is insufficient, since a fixture proves only that the code does what its author expected.
  THE FIXTURE CASES: a source with zero plans; a source with one; a source with several in ONE Set (decomposition); a source with several across DIFFERENT Sets (the partly-visible case); and a source whose plans are all terminal (the already-landed case, which must be clearly visible since it is the costly one).
  DO NOT PIN THE LIVE COUNTS. The corpus grows (the item measured 71 source-linked plans, it is now 125), so a test asserting "nine plans for 25kzda" breaks on the next graduation. Assert the PROPERTY (no defect flagged, cluster reported) and derive the count.
  - Depends on: E-03
  - Expected outcome: a live-corpus assertion that the largest real cluster is reported and not flagged, with the count derived rather than pinned; five fixture cases covering zero, one, one-Set-many, many-Sets, and all-terminal.
  - Execution state: pending

- [ ] E-05 MUTATION-CHECK THE ANTI-OVER-REACH GUARD, because a test asserting "nothing was flagged" passes trivially if the view flags nothing ever.
  INTRODUCE A `count > 1` RULE deliberately, show the live-corpus assertion FAILS (it should flag 17 clusters including the correct nine-plan one), then revert and show it passes. That demonstrates the guard actually detects the failure mode the item warns about.
  ALSO MUTATE THE OTHER DIRECTION: make the view ignore terminal plans, and show the all-terminal fixture case FAILS. That is the costly case the maintainer named, so a view that silently dropped executed siblings must be caught.
  - Depends on: E-04
  - Expected outcome: two mutations, each failing the assertion it should, each passing after revert, all four outputs pasted.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE FORWARD DIRECTION IS ALREADY PARSED AND VALIDATED. `check.from-backlog-dangling` and `check.from-spec-dangling` read the same two fields at `error` severity, so the reverse index must reuse those readers rather than adding a third.
- A NEW RULE IS NEVER SILENTLY UNCLASSIFIED. `check_engine._DEFAULT_RULESPEC` exists for exactly that reason, so a new rule must be classified deliberately.
- A `warning` EXITS NONZERO; ONLY `info` DOES NOT. The repository documents this explicitly as a misreading to avoid, and it decides E-02's severity if a `check` rule is chosen: 17 legitimate clusters at `warning` would red every run.
- MULTIPLE PLANS PER SOURCE ARE CORRECT BY DESIGN. Spec `25kzda`'s graduation text says a run "may produce more than one IPD", and measured, the largest cluster is correct decomposition.
- THE ALREADY-IMPLEMENTED CASE HAS NO MECHANISM. A spec carries one whole-artifact status with no partial-implementation state, and `implemented` requires only a resolvable citation rather than semantic verification. Backlog `f1sw71` tracks it.
- THE CORPUS GROWS DURING WORK. The item measured 71 source-linked plans; it is 120 five days later (125 bullets), and 166 bullets over 106 sources one day after that at review. An executed plan in this repository's history was reviewed with a note that its own corpus count "GREW during this Set's own operation, so the count must be derived not asserted". Derive, never pin.
- THE EXISTING FORWARD READERS ARE SINGLE-MATCH BY DESIGN. `find_from_backlog_plans` and `check_from_spec_dangling` each use `.search`, which answers "does THIS plan's link resolve" correctly and cannot build a reverse index over the five dual-link plans. Reuse the patterns; do the multi-match walk here (F-8).
- Suite bare: `python3 -m pytest`. Measure the baseline in the executing worktree and compare failing NODE IDS, never totals. CORRECTED AT REVIEW: the `1 failed, 5648 passed` figure and its attribution to `tests/test_orchestrator_retirement.py` are BOTH stale. Measured at review: `1 failed, 5919 passed, 3 skipped, 2 xfailed in 51.91s`, the failing node being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which is ENVIRONMENTAL (a gitignored local `opencode-recovery/` dump in this checkout) and may be absent elsewhere; `test_orchestrator_retirement.py` now PASSES (112 passed). Measure your own and quote neither.

## Findings

| Id | Severity | Location (measured at HEAD `a2e0438a`) | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | `check_engine.py` rule table | Only the FORWARD direction is checked (`check.from-backlog-dangling`, `check.from-spec-dangling`). No reverse, duplicate, or already-implemented check exists. | grepped the rule table; no hits for duplicate/already-implemented |
| F-2 | MED | plans tree | 125 plans carry a source link across 72 sources, 17 with more than one plan. `25kzda` x9 (8 executed, 1 not-executed), `kjzlgw` x8 (all executed), `7ckptx` x7 (4 executed, 3 approved), `kw5y2s` x6 (all executed), `1ap48y` x4 (3 executed, 1 superseded). The item recorded 71 plans. | walked the tree parsing both fields plus `- Status:` |
| F-3 | HIGH | executed plans `eyh1fu`, `5slbpi`, `wpomxa` | THE ITEM'S OWN SOURCE WAS ALREADY PARTLY GRADUATED: spec `6m4kow` has three executed plans, and two of `6h7y2y`'s three premises had already shipped when it was filed. This is the waste the view prevents, demonstrated on this very Set. | grepped `From-Spec: 6m4kow` |
| F-4 | CONSTRAINT | spec `25kzda` graduation text; F-2 | A `count > 1` RULE WOULD BE WRONG: multiple plans per source is deliberate decomposition, and the nine-plan cluster is correct. Flagging it would teach readers to ignore the warning. | spec text plus measured cluster statuses |
| F-5 | CONSTRAINT | `check_engine` `drift_exit_code` and `_DEFAULT_RULESPEC` | A `warning` exits nonzero; only `info` is exempt. So a `check` rule over 17 legitimate clusters must be `info` or it reds every run. The repository documents this as a misreading to avoid. | source read |
| F-6 | BLOCKER-FOR-ONE-CASE | backlog `f1sw71`; `attention_contract` | THE ALREADY-IMPLEMENTED CASE IS NOT MECHANICALLY ANSWERABLE: one whole-artifact status, no partial-implementation state, and `implemented` needs only a resolvable citation. The item permits shipping without it if the limit is stated honestly. | the item's citation re-verified; `f1sw71` open |
| F-7 | MED | F-2 | MOST CLUSTER MEMBERS ARE TERMINAL (`executed`), so a view reading only `pending/` would miss the costly case entirely. | status breakdown per cluster |
| F-8 | MED (added at review) | plans tree; five named plans; `_META_FROM_BACKLOG_RE`, `_ITEM_FROM_SPEC_RE` | THE BULLET COUNT IS NOT THE FILE COUNT AND THE EXISTING READERS ARE SINGLE-MATCH BY DESIGN. 125 bullets over 120 files at `a2e0438a`, because `5942n7`, `pgq326`, `84j8d7`, `ueg5cf` and `h0zljh` each carry BOTH link kinds. The forward checks use `.search` (one match), which is right for "does this plan's link resolve" and wrong for building a reverse index; reusing a reader without noticing this drops one edge per dual-link plan. | re-walked a clean `a2e0438a` archive: 125 / 120; read both regex call sites |
| F-9 | HIGH (added at review) | pending plan `bwgyum` (Set `setidhard`, Order 02, `reviewed`, `go-pending-approval`) | THE OPPOSITE DIRECTION OF THIS EDGE IS BEING BUILT BY ANOTHER SET AND NEITHER PLAN MENTIONS THE OTHER. `bwgyum` adds the forward `Graduated-To` link plus its dangling check over the same `_iter_plan_ipds` in the same module. Two traversals of one relationship is the drift P8 forbids and they could disagree about what a source became. The orchestrator now carries the coordination constraint and CID-7. | grepped both Sets for cross-references (zero hits); read `bwgyum` E-01/E-03 |
| F-10 | LOW (added at review) | backlog `f1sw71` | STATUS LABEL STALE: this plan calls `f1sw71` "open" twice; it is `graduated`, to decision plan `si24ia` (`to-review`) which measures and recommends rather than building a requirement model. The GAP is unbuilt, so every exclusion resting on it is unchanged, but an executor finding it graduated with a plan attached could wrongly conclude the exclusion was overtaken. | `aw find backlog f1sw71` -> `graduated ...`; `si24ia` carries `- From-Backlog: f1sw71` |

## Proposed changes (ordered, validatable)

1. E-01 inverts the existing forward parse into a source-to-plans index carrying status and Set, including terminal directories.
2. E-02 exposes it as a read-only surface taking a source selector, with no uniqueness rule and `info` severity if it is a rule.
3. E-03 puts the three-case honesty into the OUTPUT, with the reason the third is undetectable.
4. E-04 asserts the no-false-positive property against the live corpus and the behavioral cases against fixtures.
5. E-05 mutation-checks the guard in both directions.

## Deferred / out of scope (with reason)

- THE FULL THREE-WAY CLASSIFIER. The item offers it and then offers the minimum version; the minimum is chosen because one of the three cases is mechanically unanswerable (F-6) and a classifier that guessed it would produce exactly the false confidence this item exists to prevent.
- THE ALREADY-IMPLEMENTED VERDICT. Backlog `f1sw71` (`graduated` to decision plan `si24ia`; the gap is unbuilt, so this exclusion is unchanged: F-10). The item explicitly permits shipping without it.
- ANY `count > 1` UNIQUENESS RULE, REFUSAL, OR GATE. F-4 and the item's own "advisory and read-only; it does not need to decide, only to show".
- WIRING THE VIEW INTO THE GRADUATION PATH. Child 02 (`iuxtjy`), which makes a spec or backlog selector reachable for the `plan` action and calls this view there. Split because the view is useful and testable on its own, and because the item required the guard to exist FIRST.
- SCOPE-OVERLAP DETECTION between two plans in different Sets. That would need a scope comparison the repository has no mechanism for; E-03 states the limit instead of faking it.
- CHANGING EITHER FORWARD DANGLING CHECK. They work, they are `error` severity, and this item adds a view rather than altering validation.

## Scope check

- Over-scope: `check_engine.py` is in scope ONLY to add the reverse index and, if OQ-01 chooses a rule, one `info` rule. Do NOT change either forward dangling check or any existing severity.
- Under-scope: stated rather than left as `none`. After this child the view exists but nothing CALLS it during graduation, so it helps only whoever remembers to run it; child 02 closes that. And accidental duplication is only partly visible, since scopes are not compared.

## Required tests / validation

`python3 -m pytest` bare in an isolated worktree, with the baseline measured THERE and pasted, comparing failing NODE IDS not totals. The live-corpus assertion in E-04 is deliberate and must DERIVE its counts, never pin them: this repository's long-standing `tests/test_orchestrator_retirement.py` failure is itself caused by pinning to the mutable plan corpus, and an executed plan's review record separately warns that a corpus count "GREW during this Set's own operation, so the count must be derived not asserted". Do not repeat that mistake. Run `aw check all` before and after to prove no existing rule's output changed.

## Spec / documentation sync

Spec `25kzda` (`- Status: approved`) is the authority for what graduation MEANS and its §1.3 lists graduation as a disposition of `aw <host> run`. This child adds an ADVISORY VIEW and no dispatch, so it neither implements nor contradicts that section, and no amendment is expected.
TWO THINGS TO CHECK RATHER THAN ASSUME. FIRST, whether §1.3 or the graduation text specifies a DUPLICATE CHECK as part of the graduation disposition; if it does, this child is implementing a specified behavior and that is the justification to record, and if it specifies more than this child delivers, record the remaining gap rather than amending the spec to match a partial implementation. SECOND, if OQ-01 chooses a `check` rule, the rule table is documented in the check engine's own contract and a new rule id belongs in whatever document enumerates them; grep for a rule-id enumeration outside the code before adding one.
Do NOT edit spec `25kzda`'s §4.2 finding-code table under any circumstances: it is transcribed verbatim into `run_evidence.RUN_FINDING_CODES` with a byte-equality test, so editing a cell IS a code change.

## Open questions

### OQ-01: Is the view a `check` rule, a read surface, or both?

- Blocking: no
- Status: open
- Owner: this plan's executor, escalating to the maintainer only if a new rule severity is proposed
- Resolution or deferral rationale: NOT blocking, because E-02 requires a read-only surface answering the source-selector question either way, and both shapes satisfy the item's minimum version. The considerations, measured: a `check` RULE runs on every `aw check` and in CI, so over 17 legitimate clusters it must be `info` (F-5) or it reds every run, and an `info` finding that always fires on correct work is close to noise. A READ SURFACE is consulted deliberately by whoever graduates, which matches "advisory and read-only", but only helps if someone runs it, which is precisely why child 02 wires it into the graduation path. The likely right answer is the read surface FIRST (it is what child 02 calls) with a rule only if the maintainer wants passive surfacing. Decide and record; do not add a `warning`-severity rule.

### OQ-02: Should the view report a source with ZERO plans as a distinct outcome?

- Blocking: no
- Status: open
- Owner: this plan's executor
- Resolution or deferral rationale: NOT blocking, because E-04 covers the zero case as a fixture either way and the plan completes under both answers. It matters for how the surface reads during graduation: "no existing plans for this source" is the EXPECTED and reassuring answer, and rendering it identically to an error or to empty output would make the common case look like a failure. Recommend an explicit affirmative statement, since the view's purpose is to be consulted before authoring and its most frequent honest answer is "nothing yet, proceed".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the reverse index's construction, showing it REUSES the existing `From-Backlog:`/`From-Spec:` readers and iterator (show the call, not a similar regex). Paste the index entry for `25kzda` listing every plan in the cluster with its status and Set, with the count DERIVED rather than compared against the nine measured here, and confirm terminal directories are included by showing the `executed` members. Paste a grep proving no second parser for either field was added. Paste one of the five dual-link plans (F-8) appearing under BOTH of its sources, proving every source bullet is indexed rather than the first. State `bwgyum`'s status at your execution time and which shared-traversal case applies (F-9).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the ACTUAL output of the surface for `25kzda`, and separately for a single-plan source and a zero-plan source. State OQ-01's answer. Paste a grep proving no `count > 1` comparison exists in the added code. If a `check` rule was added, paste its `RuleSpec` showing severity `info` AND paste `aw check all`'s exit code before and after, proving it did not become nonzero.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the limits statement AS IT APPEARS IN THE OUTPUT, not as a code comment or a plan quote. Confirm it addresses all three cases with the correct verdict each (visible, partly visible, undetectable), gives the reason for the undetectable one, and names `f1sw71`. Confirm it does NOT claim to detect duplication.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the live-corpus test and its actual output, showing the largest real cluster is REPORTED and NOT flagged, with the count DERIVED (paste the derivation, and confirm no literal count is asserted). Paste all five fixture cases with output: zero, one, one-Set-many, many-Sets, all-terminal. The all-terminal case is the costly one, so show it is clearly visible in the output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste BOTH mutations in full. Mutation 1: introduce a `count > 1` rule, paste the live-corpus assertion FAILING and showing it flagged the legitimate clusters, revert, paste passing. Mutation 2: make the view ignore terminal plans, paste the all-terminal fixture FAILING, revert, paste passing. Both are required; mutation 1 proves the anti-over-reach guard works and mutation 2 proves the costly case is actually covered.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Scope fence: touch ONLY the three paths in `- Scope-Paths:`. Do NOT implement a `count > 1` rule, a refusal, or any gate. Do NOT attempt the already-implemented verdict. Do NOT add a `warning`-severity rule. Do NOT add a second parser for `From-Backlog:`/`From-Spec:`. Do NOT change either forward dangling check or any existing rule severity. Do NOT pin a live corpus count in a test. Do NOT wire the view into the graduation path (child 02 owns that). Do NOT edit spec `25kzda`'s §4.2 finding-code table. If the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT, since `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`.

RE-LOCATE BY SYMBOL, NEVER BY THE LINE NUMBERS IN THIS PLAN. Find the `check.from-backlog-dangling` and `check.from-spec-dangling` implementations, `_DEFAULT_RULESPEC`, `drift_exit_code`, and the plan enumeration helpers by name.

Execution contract: commit ONLY the files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `-a`, never push. Verify the staged set with `git diff --cached --name-only` before every commit and RE-VERIFY after any failed or hook-interrupted commit, since `pre-commit` can restore another agent's paths into the index. Paste ACTUAL runner output when reporting tests passed; never claim a suite result you did not run.

Post-gate lifecycle: requires explicit human approval (`aw ipd set approved jxxec8 --by-human --message ...`) before execution. Do NOT hand-write a `Readiness:` field: that is `/plan-review`'s attested output. Transition via `aw ipd finalize` after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence. Do NOT close backlog `6h7y2y` here: its Half 1 ships in child 02, and closing it after the guard alone would claim a graduation path that is still unreachable. Child 02 (`iuxtjy`) closes it.
