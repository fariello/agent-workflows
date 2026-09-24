# IPD: Give aw backlog new a near-duplicate guard so one defect cannot be filed twenty-four times

- Date: 2026-09-23
- Kind: child
- Concern: ONE DEFECT HAS TWENTY-THREE OPEN BACKLOG ITEMS AND THE COUNT IS STILL RISING, BECAUSE NOTHING WARNS A FILER THAT THE ITEM ALREADY EXISTS. Backlog `uj5g58` records "18 items independently filed the same `turn_bounds` ambient-env defect". MEASURED AT HEAD `22cf67d9` it is now 23 (plus `uj5g58` itself), so SIX more were filed after the item that counted them: `06ngnx`, `1ixbnr`, `3q0fcm`, `4vn040`, `7p08pw`, `8dp3zp`, `cfgj8s`, `hco0mk`, `j08jky`, `j8gcyq`, `mepbmp`, `ph0wlt`, `pmmnuw`, `pzbcto`, `q8s57d`, `r67fl1`, `rfu7mk`, `se8vsp`, `tem4g9`, `tng9xf`, `to77re`, `wx72g3`, `zgndje`. That rising count IS the finding: the cost is ongoing and measurable, not historical.
  VERIFIED THERE IS NO GUARD: `aw backlog new --help` exposes no duplicate, similarity, or near-match option, and nothing in the creation path consults existing items. So a filer with an honest intention ("record this defect") gets no signal that twenty-three siblings exist, and the cheapest correct action (check first) requires knowing to search and guessing the right words.
  THE COST IS NOT MERELY UNTIDINESS, WHICH IS WHY THIS IS WORTH BUILDING. Every duplicate is an item a human must triage, a row in `aw attention` competing for the same attention the board exists to direct, and a separate `Blocks-Release: next` gate: all twenty-three carry it, so a single test defect is currently presented as twenty-three release blockers. It also corrodes the board's usefulness, which is the same "trains people to ignore the rule" failure `4y7nzh` records for a gate that stayed red for two days.
  THE HARD PART IS THAT NEAR-DUPLICATE DETECTION MUST NOT BECOME A REFUSAL, and this is the constraint that shapes the whole design. Legitimately similar items exist: two genuinely distinct defects in one module often share most of their vocabulary, and the `graduate` Set's own guard (`aw graduation`, shipped by `jxxec8`) is deliberately ADVISORY for exactly this reason, reporting a cluster and stating which cases it "can detect", "can only partly detect", and "cannot detect at all". That precedent is directly applicable and should be followed rather than re-litigated: SHOW the filer the candidates and let them decide.
  A SECOND, CHEAPER SIGNAL IS ALSO MISSING AND IS WORTH MORE THAN SIMILARITY SCORING. Twenty-three items name the SAME TEST NODE (`test_turn_bounds`) and mostly the same environment variable. An exact-token overlap on a distinctive identifier (a test node id, a symbol name, an error string) would have caught nearly all of them with no fuzzy matching and no false-positive risk, which makes it the higher-value half of this plan.
- Scope: Make filing a duplicate harder than filing a new item, without refusing anything. IN: (a) at `aw backlog new`, report existing OPEN items that plausibly describe the same defect, advisory-only, following `aw graduation`'s precedent of stating its own limits; (b) prefer distinctive-token overlap (test node ids, symbol names, error strings) over prose similarity, per OQ-01; (c) a test proving the twenty-three-item corpus would have been caught. OUT: refusing or blocking a filing; auto-merging or auto-closing existing duplicates; retroactively consolidating the twenty-three (that is a records act, and `uj5g58` plus this plan record the reasoning, but a bulk close is deliberately a separate human-approved change); and any change to `aw attention`'s ranking.
- Scope-Paths: agent_workflows/backlog.py, tests/test_backlog_duplicate_guard.py
- Item-Dependencies: none
- Status: to-review
- Set: envhermet
- Order: 2
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: fwgq2u
- From-Backlog: uj5g58
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `uj5g58`, whose `- Blocks-Release: next` is INHERITED. RE-MEASURED its central number rather than repeating it: the item says 18, the live count is 23, so six were filed after it was written. The rising count is the argument.
  THE DESIGN IS CONSTRAINED BY A SHIPPED PRECEDENT rather than invented here: `aw graduation` (from `jxxec8`) solves the structurally identical problem for sources and plans by SHOWING a cluster and stating its own detection limits, never refusing. This plan follows it deliberately, which also means the honest-limits wording is a requirement and not a nicety.
  MY STRONGEST RECOMMENDATION IS THE CHEAP HALF: twenty-three of these items name the same test node, so distinctive-token overlap would have caught almost all of them with no fuzzy matching. Prose similarity is the part most likely to produce false positives and least likely to be needed.

## Goal

Tell someone filing a backlog item that the defect may already be filed, at the moment they file it, without ever refusing the filing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure the corpus the guard must catch

- [ ] E-01 RE-MEASURE THE DUPLICATE CORPUS AND DERIVE THE DISCRIMINATOR FROM IT, before designing anything. The corpus is the specification: a guard that would not have caught these twenty-three is not worth shipping.
  RE-COUNT rather than trusting this plan: enumerate open items describing the turn-bounds ambient-env defect and report the number. At authoring it was 23 against `uj5g58`'s recorded 18. If it has risen again, say so; that number is the plan's justification.
  FIND WHAT THEY SHARE THAT NOTHING ELSE DOES. Measure candidate signals across the corpus: the test node id (`test_turn_bounds`), the environment variable name, and any shared error text. For each, report how many of the 23 carry it AND how many UNRELATED open items also carry it. The second number is the false-positive rate and it decides OQ-01.
  DO NOT DESIGN A SIMILARITY SCORE BEFORE THIS MEASUREMENT. If a distinctive token catches 23 of 23 with no unrelated matches, prose similarity is unnecessary complexity and must not be built.
  ALSO CHECK A NEGATIVE CONTROL: find two genuinely DISTINCT open items that share most of their vocabulary, and confirm your proposed signal does NOT flag them as the same defect. The `check.scope-drift` and turn-bounds families are good hunting grounds.
  - Depends on: none
  - Expected outcome: the live duplicate count, a per-signal table of true matches and unrelated matches across the whole open corpus, and a negative-control pair that must not be flagged; OQ-01 answered from those numbers.
  - Execution state: pending

### Task group 2: build the advisory

- [ ] E-02 REPORT CANDIDATE DUPLICATES AT FILING TIME, ADVISORY ONLY, per OQ-01's answer.
  IT MUST NEVER REFUSE, AND THIS IS THE LOAD-BEARING CONSTRAINT. Follow `aw graduation`'s shipped precedent: show the candidates with their id6, status and summary, and let the filer decide. A refusal would block legitimate filings and would train filers to work around the tool, which is worse than the duplicates.
  IT MUST STATE ITS OWN LIMITS IN ITS OUTPUT, as `aw graduation` does ("which of the three cases it can detect, can only partly detect, and cannot detect at all"). A filer who sees "no candidates" must understand that means "nothing matched the signal", never "this is definitely new".
  SEARCH THE RIGHT POPULATION. A duplicate of an item already `done` or `graduated` is still worth showing (the defect may be fixed, which is more useful than filing again), so do not restrict the search to `open` without saying why. This is a genuine design choice: state it.
  IT MUST NOT SLOW FILING NOTICEABLY. `59t9x5` establishes in this repository that a user-perceptible delay is itself a defect, and it measures the corpus read at roughly 530ms for ~620 records; a guard that re-walks everything with a fuzzy comparison could exceed that. Measure the added latency and report it.
  - Depends on: E-01
  - Expected outcome: `aw backlog new` reports plausible existing items with id6, status and summary; it never refuses; its output states what its silence does and does not prove; the added latency is measured and reported.
  - Execution state: pending

### Task group 3: prove it against the real corpus

- [ ] E-03 PROVE THE GUARD WOULD HAVE CAUGHT THE TWENTY-THREE, AND WOULD NOT FLAG THE NEGATIVE CONTROL.
  TEST AGAINST FIXTURES DERIVED FROM THE REAL ITEMS, not invented text. The filings' actual wording is the input the guard must handle, and it varies more than a synthetic fixture would.
  ASSERT THE NEGATIVE CONTROL EXPLICITLY. A guard that flags everything is useless and will be disabled; E-01's distinct-but-similar pair must be shown NOT flagged.
  DO NOT PIN THE LIVE CORPUS. Tests in this repository that assert against live records are a known hazard (`jb0sc1`, `caf5ed`, `agrlvw` all record versions of it), so build fixtures rather than asserting "23 items match" against the tree, which will change the moment this plan's own siblings close them.
  - Depends on: E-02
  - Expected outcome: a test showing representative filings from the 23 are flagged as candidates of one another, and the negative-control pair is not; no assertion against the live records tree.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE ADVISORY-NOT-REFUSAL PATTERN IS ALREADY SHIPPED AND IS THE MODEL HERE: `aw graduation` reports every plan/spec already citing a source, "read-only and ADVISORY: it shows and never refuses, and it adds no uniqueness rule, because a source decomposing into several children of one Set is correct".
- STATING DETECTION LIMITS IN THE OUTPUT is part of that precedent, not decoration: `aw graduation` enumerates what it can, partly can, and cannot detect, so a clean answer is not misread as a guarantee.
- A USER-PERCEPTIBLE DELAY IS A DEFECT in this repository (`59t9x5`, reclassified `bug` by the maintainer for costing ~128ms of a ~530ms command), which bounds how expensive this guard may be.
- TESTS MUST NOT ASSERT AGAINST THE LIVE RECORDS TREE (`jb0sc1`, `caf5ed`, `agrlvw`), which is why E-03 requires fixtures.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `aw backlog new` | No duplicate/similarity guard exists, so nothing tells a filer that 23 siblings already exist. | `--help` exposes no such option; no consultation of existing items in the creation path |
| F-2 | HIGH | the live corpus | `uj5g58` recorded 18 duplicates; the live count is 23, so SIX were filed after the counting item. The cost is ongoing. | enumerated: `06ngnx`, `1ixbnr`, `3q0fcm`, `4vn040`, `7p08pw`, `8dp3zp`, `cfgj8s`, `hco0mk`, `j08jky`, `j8gcyq`, `mepbmp`, `ph0wlt`, `pmmnuw`, `pzbcto`, `q8s57d`, `r67fl1`, `rfu7mk`, `se8vsp`, `tem4g9`, `tng9xf`, `to77re`, `wx72g3`, `zgndje` |
| F-3 | MED | release gating | All 23 carry `Blocks-Release: next`, so ONE test defect is presented to the release gate as 23 blockers, distorting the outstanding-blocker set `aw attention` reports. | each item's front matter |
| F-4 | MED (design) | `aw graduation` | The structurally identical problem is already solved advisory-only, with stated limits. Re-deciding refuse-versus-advise would discard a shipped, reviewed precedent. | `aw graduation --help`: "Read-only and ADVISORY: it shows and never refuses" |
| F-5 | MED (design) | the corpus's shared vocabulary | 23 items name the same test node and mostly the same env var, so exact distinctive-token overlap likely catches nearly all with no fuzzy matching; prose similarity carries the false-positive risk and may be unnecessary. | the enumerated summaries |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the corpus and derives the discriminator, including a false-positive count and a negative control.
2. E-02 reports candidates at filing time, advisory-only, with stated limits and measured latency.
3. E-03 proves the guard catches representatives of the 23 and spares the negative control, using fixtures.

## Deferred / out of scope (with reason)

- REFUSING A FILING. F-4: the shipped precedent is advisory, and a refusal would block legitimate items and invite workarounds.
- RETROACTIVELY CONSOLIDATING THE TWENTY-THREE. A records act needing human judgement about which filing survives; it should be a separate, human-approved change rather than a side effect of building a guard. Note child 01 (`heglfv`) fixes the underlying defect, which is what makes consolidation safe to do later.
- AUTO-MERGING OR AUTO-CLOSING. Strictly worse than advising: an automatic close on a similarity heuristic would destroy a real report whenever the heuristic is wrong.
- EXTENDING THE GUARD TO OTHER RECORD TYPES (specs, plans). Plausible and out of scope; the measured corpus is backlog items. If E-01 shows the same pattern elsewhere, that is a SUCCESSOR PLAN rather than a backlog item, since the design would already be proven here.

## Scope check

- Over-scope: `agent_workflows/backlog.py` is in scope ONLY for the advisory at creation time. Do not change `aw attention`'s ranking, the item schema, or any status semantics.
- Under-scope: if the candidate search needs a shared corpus reader that does not exist, declare the file before adding it rather than widening at finalize; and prefer an existing enumeration over a new walk, per the `59t9x5` latency constraint.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: the new duplicate-guard test module.
- E-03 MUST use fixtures, not the live tree (`jb0sc1`, `caf5ed`, `agrlvw`), and MUST include the negative-control pair.
- E-02's latency measurement must be pasted, since a slow filing path is itself a defect by this repository's standard (`59t9x5`).

## Spec / documentation sync

- `aw backlog new`'s documented behavior changes (it now reports candidates), so its help text and any backlog README describing the filing flow should record it, including that the advisory never refuses.
- No `.spec.md` edit is anticipated. If the backlog contract is specified in a spec, declare that file in `- Scope-Paths:` before editing, per the spec-amendment rule.

## Open questions

### OQ-01: Distinctive-token overlap, prose similarity, or both?

- Blocking: no
- Status: open
- Owner: this plan's executor, decided by E-01's measured false-positive counts
- Resolution or deferral rationale: NOT blocking, because E-01 produces the numbers that decide it and E-02 is implementable under any answer. DISTINCTIVE-TOKEN OVERLAP (a shared test node id, symbol name, or error string) is recommended and should be measured FIRST: it is cheap, explainable to the filer ("these items also mention `test_turn_bounds`"), and carries almost no false-positive risk, and F-5 suggests it alone would have caught nearly all 23. PROSE SIMILARITY catches paraphrases a token match misses, but it is where false positives live, and a noisy advisory is one filers learn to skip past, which returns us to the current state with extra latency. If token overlap catches 23 of 23 with no unrelated matches, DO NOT build similarity scoring; record that as the answer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the live duplicate count pasted; a per-signal table giving true matches and UNRELATED matches across the whole open corpus; the named negative-control pair; and OQ-01's answer derived from those numbers rather than asserted.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `aw backlog new` output showing candidate items with id6, status and summary; proof it exits successfully and files the item anyway (never refuses); the stated-limits text quoted from its own output; and the measured added latency.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the test pasted showing representative filings from the 23 flagged as candidates of one another AND the negative-control pair not flagged; confirmation by inspection that no assertion reads the live records tree; plus the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
